"""P0-E5 Validation Primitive — 三状态铁律的机械落地。

铁律（THREE_LAYER_ARCHITECTURE v3 §2.6）：execution_status=success 绝不推出
model_status=correct。本模块提供第一扇门（Execution → Validation）的确定性原语：

    ExecutionResult(EXEC)
        → 一组确定性检查（output 字段/数值范围/等式）
        → VerificationResult(VR, 一等 artifact)
        → verified_by 边绑定溯源

状态语义（与用户裁决一致）：
    * VR.status = passed  ⟺  execution success 且全部检查通过
    * VR.status = failed  ⟺  execution success 但至少一项检查失败（可归因到具体 check）
    * VR.status = invalid ⟺  execution 非 success（无输出可验证，不得 passed）

检查全部确定性执行（无 LLM、无随机）：verification 不是评价，是校验。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VERIFICATION_FIELDS = (
    "verification_id", "execution_id", "status", "checks",
    "evidence_refs", "started_at", "finished_at", "provenance",
)


@dataclass
class VerificationResultData:
    verification_id: str = ""
    execution_id: str = ""
    status: str = "invalid"          # passed / failed / invalid
    checks: list[dict] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in VERIFICATION_FIELDS}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "VerificationResultData":
        return cls(**{k: d.get(k) for k in VERIFICATION_FIELDS})


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _num(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _get_path(outputs: dict, path: str) -> Any:
    """'a.b.0' 形式取嵌套值；空路径返回整体。"""
    cur: Any = outputs
    for part in path.split(".") if path else []:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None
    return cur


# ---------------------------------------------------------------- checks

def run_check(kind: str, outputs: dict, spec: dict) -> dict:
    """执行单条确定性检查，返回 {name, kind, passed, detail}。"""
    name = spec.get("name") or kind
    path = spec.get("path", "")
    detail = spec.get("expect", "")
    value = _get_path(outputs, path)

    if kind == "output_field_exists":
        ok = value is not None
        return {"name": name, "kind": kind, "passed": ok,
                "detail": (f"存在 {path}={value!r}" if ok
                           else f"缺失字段 {path!r}")}

    if kind == "output_numeric":
        num = _num(value)
        ok = num is not None
        return {"name": name, "kind": kind, "passed": ok,
                "detail": (f"{path}={num!r} 为数值" if ok
                           else f"{path}={value!r} 非数值")}

    if kind == "output_range":
        num = _num(value)
        lo, hi = spec.get("min"), spec.get("max")
        ok = num is not None and (lo is None or num >= lo) \
            and (hi is None or num <= hi)
        return {"name": name, "kind": kind, "passed": ok,
                "detail": (f"{path}={num!r} 在 [{lo}, {hi}]"
                           if ok else f"{path}={num!r} 超出 [{lo}, {hi}]")}

    if kind == "output_equals":
        ok = value == spec.get("expect")
        return {"name": name, "kind": kind, "passed": ok,
                "detail": (f"{path}={value!r} 等于期望 {spec.get('expect')!r}"
                           if ok else f"{path}={value!r} != {spec.get('expect')!r}")}

    return {"name": name, "kind": kind, "passed": False,
            "detail": f"未知检查类型 {kind!r}"}


def run_checks(execution_data: dict, checks: list[dict]) -> tuple[str, list[dict]]:
    """对执行结果跑检查集，返回 (status, checks)。

    铁律：execution 非 success → invalid，不执行任何检查。
    """
    if execution_data.get("status") != "success":
        return "invalid", [{
            "name": "__execution_status__", "kind": "precondition",
            "passed": False,
            "detail": (f"execution status={execution_data.get('status')}，"
                       "无输出可验证（铁律：不得 passed）"),
        }]
    results = [run_check(c.get("kind"), execution_data.get("outputs") or {},
                         c) for c in checks]
    status = "passed" if all(r["passed"] for r in results) else "failed"
    return status, results


# ------------------------------------------------------------ registration

def validate_execution(project_dir: str | Path, exec_id: str,
                       checks: list[dict],
                       provenance: dict | None = None) -> VerificationResultData:
    """从 registry 取 execution_result，跑检查，注册 VR artifact + verified_by 边。

    返回 VerificationResultData；调用方可通过 data.verification_id 引用。
    """
    from runtime.artifacts.registry import ArtifactRegistry, ArtifactNotFound
    from runtime.graph.evidence_graph import EvidenceGraph

    project_dir = Path(project_dir)
    reg_path = project_dir / "state" / "registry.json"
    if not reg_path.exists():
        raise FileNotFoundError(f"Registry 不存在: {reg_path}")
    reg = ArtifactRegistry(reg_path)
    reg.load()

    try:
        art = reg.get(exec_id)
    except ArtifactNotFound:
        raise ValueError(f"execution_result 不存在: {exec_id}") from None
    exec_data = dict(art.data or {})

    started = _now()
    status, check_results = run_checks(exec_data, checks)
    finished = _now()

    vdata = VerificationResultData(
        verification_id="", execution_id=exec_id, status=status,
        checks=check_results,
        evidence_refs=[exec_id],
        started_at=started, finished_at=finished,
        provenance=provenance or {"engine": "execution.validation",
                                  "check_count": len(checks)},
    )
    created = reg.create("verification_result",
                         title=f"验证 {exec_id}（{status}）",
                         created_by="execution.validation",
                         data=vdata.to_dict(), activate=True)
    vdata.verification_id = created.artifact_id
    reg.save()

    g = EvidenceGraph(reg, project_dir / "state" / "evidence_graph.json")
    g.load()
    g.add_relation(exec_id, "verified_by", vdata.verification_id)
    g.save()

    return vdata


def main(argv: list[str] | None = None) -> int:
    """CLI：python -m runtime.execution.validation <项目> <exec_id> <checks.json>"""
    import argparse
    ap = argparse.ArgumentParser(description="对 execution_result 跑确定性验证")
    ap.add_argument("project")
    ap.add_argument("exec_id")
    ap.add_argument("checks", help="检查清单 JSON 文件路径")
    args = ap.parse_args(argv)

    checks = json.loads(Path(args.checks).read_text(encoding="utf-8"))
    vr = validate_execution(args.project, args.exec_id, checks)
    print(json.dumps(vr.to_dict(), ensure_ascii=False, indent=2))
    print(f"[validation] {vr.verification_id} status={vr.status} "
          f"checks={len(vr.checks)}")
    return 0 if vr.status == "passed" else 1
