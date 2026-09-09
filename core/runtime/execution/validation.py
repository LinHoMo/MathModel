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


def _norm_key(key: str) -> str:
    """小写 + 去下划线/空格：'total_cost' == 'TotalCost' == 'total cost'。"""
    return "".join(ch for ch in key.lower() if ch.isalnum())


def resolve_output_key(outputs: dict, *names: str) -> str | None:
    """按候选名（name/symbol/别名）解析执行输出中的字段 key。

    精确匹配优先；其次小写归一匹配。返回命中的 key 或 None。
    """
    for n in names:
        if not n:
            continue
        if n in outputs:
            return n
    normed = {_norm_key(k): k for k in outputs}
    for n in names:
        if not n:
            continue
        hit = normed.get(_norm_key(n))
        if hit is not None:
            return hit
    return None


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

    if kind == "output_key_exists":
        # Fidelity 专用：按候选名（name/symbol/别名）解析输出字段
        hit = resolve_output_key(outputs, *(spec.get("names") or []))
        detail = (f"输出字段 {hit!r} 存在（声明 {spec.get('declared')!r}）"
                  if hit else
                  f"缺失声明 {spec.get('declared')!r}（候选 "
                  f"{spec.get('names') or []} 均未命中输出 key）")
        return {"name": name, "kind": kind, "passed": hit is not None,
                "detail": detail, "resolved_key": hit}

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


# ---------------------------------------------------------------- P1-VS-001 数值验证（C8）

NUMERIC_VALIDATION_FIELDS = (
    "execution_valid", "mathematical_valid", "empirical_valid", "robustness",
    "constraint_violation_max", "objective_value", "objective_sane",
    "variable_domain_violation", "checks", "detail",
)


def run_numeric_validation(outputs: dict, spec: dict,
                           execution_status: str = "success") -> dict:
    """基于真实数值判 FAIL（P1-VS-001 C8，ValidationResult 四字段）。

    通用路径（audit FIX-5.2 前置）：spec 提供 "checks"（run_check 支持的类型：
    output_field_exists / output_numeric / output_range / output_equals /
    output_key_exists）时，走通用确定性检查集——不绑定任何特定题目。
    其余保持 2024_A 硬编码路径（P1-VS-001 向后兼容）。

    检查（全部确定性，零 LLM）：
      1. constraint_violation_max —— outputs["pair_distances"][t][i] 与
         spec.constraints[].reference 之差的绝对最大值（pair_index 0=头板，
         "1+"=全部体板）；> tolerance → mathematical_valid=False
      2. objective_sanity —— outputs["head_speeds"] 均值 vs spec.objective
         .expected ± tolerance → empirical_valid
      3. variable_domain_violation —— outputs["positions"] 全部坐标落在
         spec.domain [min,max] 内
      4. robustness —— 约束余量归一（1 − violation/最坏参考，clip [0,1]）
    判 FAIL 独立于 evidence_gate（evidence_gate 只查边不查数值）。
    """
    if execution_status != "success":
        return {
            "execution_valid": False, "mathematical_valid": False,
            "empirical_valid": False, "robustness": 0.0,
            "constraint_violation_max": None, "objective_value": None,
            "objective_sane": False, "variable_domain_violation": True,
            "status": "invalid", "detail": f"execution status={execution_status}",
            "checks": [{"name": "__execution_status__", "kind": "precondition",
                        "passed": False,
                        "detail": f"execution status={execution_status}，"
                                  "无输出可验证（铁律：不得 passed）"}],
        }

    # FIX-1.2/audit D-010：通用检查集路径（docstring 承诺但此前未实现）。
    # spec["checks"]（run_check 支持类型）存在时优先走确定性通用检查集，
    # 不再硬编码 2024_A 的 pair_distances/head_speeds 字段。
    checks_spec = spec.get("checks") or []
    if checks_spec:
        cstatus, results = run_checks(
            {"status": execution_status, "outputs": outputs}, checks_spec)
        n_pass = sum(1 for r in results if r.get("passed"))
        return {
            "execution_valid": True, "mathematical_valid": cstatus == "passed",
            "empirical_valid": cstatus == "passed",
            "robustness": 1.0 if cstatus == "passed" else 0.0,
            "constraint_violation_max": 0.0,
            "objective_value": None,
            "objective_sane": cstatus == "passed",
            "variable_domain_violation": False,
            "status": cstatus, "checks": results,
            "detail": f"通用检查集: {n_pass}/{len(results)} 通过",
        }

    # ---- 通用检查集（不绑定具体题目；spec.checks 由外部验证规格注入）
    if spec.get("checks"):
        status, checks = run_checks(
            {"status": execution_status, "outputs": outputs},
            spec["checks"])
        passed = status == "passed"
        return {
            "execution_valid": execution_status == "success",
            "mathematical_valid": passed,
            "empirical_valid": passed,
            "robustness": 1.0 if passed else 0.0,
            "constraint_violation_max": None,
            "objective_value": None,
            "objective_sane": passed,
            "variable_domain_violation": not any(
                not c["passed"] for c in checks if c["kind"] == "domain"),
            "status": status,
            "detail": (f"通用检查: {sum(1 for c in checks if c['passed'])}/"
                       f"{len(checks)} 通过"),
            "checks": checks,
        }

    checks: list[dict] = []
    pair_distances = outputs.get("pair_distances") or {}
    constraints = spec.get("constraints") or []
    constraint_violation_max = 0.0
    for c in constraints:
        ref = float(c.get("reference"))
        tol = float(c.get("tolerance", 1e-6))
        pi = c.get("pair_index")
        viol = 0.0
        n_checked = 0
        for t, ds in pair_distances.items():
            for i, d in enumerate(ds):
                if pi == "1+" and i < 1:
                    continue
                if pi != "1+" and i != pi:
                    continue
                n_checked += 1
                viol = max(viol, abs(float(d) - ref))
        ok = viol <= tol
        constraint_violation_max = max(constraint_violation_max, viol)
        checks.append({"name": c.get("name"), "kind": "constraint",
                       "passed": ok, "reference": ref, "max_violation": viol,
                       "checked_pairs": n_checked,
                       "detail": (f"max|d-ref|={viol:.6g}（≤{tol}）"
                                  if ok else
                                  f"max|d-ref|={viol:.6g} > tol={tol}")})

    obj = spec.get("objective") or {}
    exp = obj.get("expected")
    otol = float(obj.get("tolerance", 0.05))
    speeds = [float(v) for v in (outputs.get("head_speeds") or {}).values()
              if v is not None]
    objective_value = (sum(speeds) / len(speeds)) if speeds else None
    objective_sane = (objective_value is not None and exp is not None
                      and abs(objective_value - exp) <= otol)
    # FIX-1.2：执行失败/无输出时 objective_value=None，detail 不得格式化 None
    measured_desc = (f"{objective_value:.6g} m/s" if objective_value is not None
                     else "N/A（无输出）")
    exp_desc = (f"{exp}" if exp is not None else "N/A")
    checks.append({"name": obj.get("name", "objective_sanity"),
                   "kind": "objective", "passed": objective_sane,
                   "expected": exp, "measured": objective_value,
                   "detail": (f"mean head speed={measured_desc}"
                              f"（期望 {exp_desc}±{otol}）")})

    dom = spec.get("domain") or {}
    dmin, dmax = dom.get("min"), dom.get("max")
    domain_ok = True
    if dmin is not None and dmax is not None:
        for frame in outputs.get("positions") or []:
            for pt in frame.get("points") or []:
                for coord in pt:
                    if not (dmin <= coord <= dmax):
                        domain_ok = False
                        break
                if not domain_ok:
                    break
            if not domain_ok:
                break
    variable_domain_violation = not domain_ok
    if not domain_ok:
        checks.append({"name": "variable_domain", "kind": "domain",
                       "passed": False, "range": [dmin, dmax],
                       "detail": f"存在坐标超出 [{dmin}, {dmax}]"})

    constraint_tolerance = float(spec.get("constraint_tolerance", 1e-6))
    mathematical_valid = (constraint_violation_max <= constraint_tolerance
                          and domain_ok)
    empirical_valid = objective_sane
    if constraint_violation_max <= 1e-12:
        robustness = 1.0
    else:
        worst_ref = max((float(c.get("reference") or 1.0)) for c in constraints)
        robustness = max(0.0, 1.0 - constraint_violation_max / worst_ref)
    status = "passed" if (mathematical_valid and empirical_valid) else "failed"

    return {
        "execution_valid": True, "mathematical_valid": mathematical_valid,
        "empirical_valid": empirical_valid, "robustness": round(robustness, 6),
        "constraint_violation_max": round(constraint_violation_max, 9),
        "objective_value": objective_value,
        "objective_sane": objective_sane,
        "variable_domain_violation": variable_domain_violation,
        "status": status, "checks": checks,
        "detail": (f"constraint_violation_max={constraint_violation_max:.6g}，"
                   f"objective="
                   + (f"{objective_value:.6g}" if objective_value is not None else "N/A")
                   + f"，domain_ok={domain_ok}"),
    }


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
