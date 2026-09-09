"""P0-E6 Model-to-Execution Fidelity — 第二扇门（Model → Code 语义保真）。

用户裁决（THREE_LAYER_ARCHITECTURE v3 §2.7 / §3）：
    * L2 Fidelity 是 LinHoMo 独有核心指标：执行代码必须执行 MODEL_IR 声明的模型。
    * execution success=1 但 fidelity=0 完全可能（声明的目标/约束/变量 ≠ 代码跑的）。
    * K002 起 model_fidelity 进入测量。

本模块把 MODEL_IR 声明转成**确定性映射检查**（复用 VR 框架，不扩 schema）：
    MODEL_IR（variables/objectives/constraints/equations 的 name/symbol）
        → output_key_exists / output_numeric / output_range checks
        → fidelity_score = passed/total（0-1）

铁律：fidelity 是结构映射校验（LLM-free、确定性、可归因到具体声明项）；
不是"看起来像"的 LLM 判断。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .validation import run_checks, run_check, resolve_output_key

FIDELITY_ENGINE = "execution.fidelity"


# ------------------------------------------------------------ checks 生成

def _candidate_names(decl: dict, extra: list[str] | None = None) -> list[str]:
    """从声明项提取候选输出名：name / symbol / 其他别名。"""
    names: list[str] = []
    for key in ("name", "symbol"):
        v = decl.get(key)
        if isinstance(v, str) and v.strip():
            names.append(v.strip())
    for v in extra or []:
        if v and v not in names:
            names.append(v)
    return names


def fidelity_checks_from_ir(model_ir: dict, experiment_idx: int = 0) -> list[dict]:
    """把 MODEL_IR 声明转成确定性检查清单（K002 的 model_fidelity 以此测量）。

    检查族（每项独立、可归因）：
      F1 variables   —— 每个变量的 name/symbol 必须能在执行输出中解析
      F2 objectives  —— 每个目标的 expression 引用的变量（variables_refs → name/symbol）可观测
      F3 constraints —— 每个约束的 variables_refs 引用的变量可观测
      F4 equations   —— 每个方程的 variables_refs 引用的变量可观测
      F5 ranges      —— variable.value_range（min/max）与输出值比对
    """
    checks: list[dict] = []
    by_id: dict[str, dict] = {}

    def _reg(name: str, kind: str, declared: str, names: list[str],
             extra: dict | None = None) -> None:
        spec: dict[str, Any] = {"name": name, "kind": kind,
                                "declared": declared, "names": names}
        if extra:
            spec.update(extra)
        checks.append(spec)

    for v in model_ir.get("variables") or []:
        by_id[v.get("variable_id")] = v
        names = _candidate_names(v)
        if not names:
            continue
        _reg(f"F1 变量可观测: {v.get('name') or v.get('symbol')}",
             "output_key_exists", v.get("name") or v.get("symbol"), names)
        vr = v.get("value_range") or {}
        lo, hi = vr.get("min"), vr.get("max")
        if lo is not None or hi is not None:
            _reg(f"F5 变量范围: {v.get('name') or v.get('symbol')} ∈ "
                 f"[{lo}, {hi}]", "output_range",
                 v.get("name") or v.get("symbol"), names,
                 {"path": "", "min": lo, "max": hi})

    def _refs_checks(kind_label: str, items: list[dict], prefix: str) -> None:
        for it in items:
            refs = []
            for rid in it.get("variables_refs") or []:
                v = by_id.get(rid) or next(
                    (x for x in model_ir.get("variables") or []
                     if x.get("variable_id") == rid), None)
                if v:
                    refs.extend(_candidate_names(v))
            if refs:
                _reg(f"{prefix} {kind_label}: {it.get('expression') or it.get('name')}",
                     "output_key_exists",
                     it.get("expression") or it.get("name"), list(dict.fromkeys(refs)))

    _refs_checks("目标", model_ir.get("objectives") or [], "F2")
    _refs_checks("约束", model_ir.get("constraints") or [], "F3")
    _refs_checks("方程", model_ir.get("equations") or [], "F4")
    return checks


# ---------------------------------------------------------------- 计算

def check_fidelity(model_ir: dict, execution_data: dict,
                   experiment_idx: int = 0) -> dict:
    """对 execution 跑 MODEL_IR 派生的 fidelity 检查。

    返回 {status, fidelity_score, passed, total, checks}：
      status = aligned（score==1）/ misaligned（0<score<1）/
               unverifiable（execution 非 success 或 MODEL_IR 无可用声明）
    """
    if execution_data.get("status") != "success":
        return {"status": "unverifiable", "fidelity_score": None,
                "passed": 0, "total": 0,
                "checks": [{"name": "__execution_status__", "kind": "precondition",
                            "passed": False,
                            "detail": f"execution status={execution_data.get('status')}，"
                                      "无输出可做 fidelity 映射"}]}
    checks = fidelity_checks_from_ir(model_ir, experiment_idx)
    if not checks:
        return {"status": "unverifiable", "fidelity_score": None,
                "passed": 0, "total": 0,
                "checks": [{"name": "__no_declarations__", "kind": "precondition",
                            "passed": False,
                            "detail": "MODEL_IR 无可用变量/目标/约束/方程声明"}],
                "reason": "no_declarations"}
    # output_key_exists 的 range 检查需要 path 指向解析后的 key：
    # 先做一次 key 解析，把 F5 的 path 回填到实际 key
    results = []
    for c in checks:
        if c["kind"] == "output_range" and not c.get("path"):
            hit = resolve_output_key(execution_data.get("outputs") or {},
                                     *(c.get("names") or []))
            c = {**c, "path": hit or ""}
        results.append(run_check(c["kind"], execution_data.get("outputs") or {}, c))
    passed = sum(1 for r in results if r["passed"])
    score = round(passed / len(results), 4) if results else None
    status = "aligned" if score == 1.0 else "misaligned"
    return {"status": status, "fidelity_score": score,
            "passed": passed, "total": len(results), "checks": results}


def verify_fidelity(project_dir: str | Path, model_ir: dict, exec_id: str,
                    experiment_idx: int = 0) -> dict:
    """端到端：从 registry 取 execution_result，做 fidelity 检查，
    注册 VR（provenance 标 execution.fidelity）+ 写 fidelity 报告文件。

    返回 {verification_id, fidelity_status, fidelity_score, passed, total,
          checks, report_path}。
    """
    from runtime.artifacts.registry import ArtifactRegistry
    from runtime.execution.validation import validate_execution

    project_dir = Path(project_dir)
    reg = ArtifactRegistry(project_dir / "state" / "registry.json")
    reg.load()
    art = reg.get(exec_id)
    if art is None:
        raise ValueError(f"execution_result 不存在: {exec_id}")
    exec_data = dict(art.data or {})

    fid = check_fidelity(model_ir, exec_data, experiment_idx)
    checks = fid["checks"]
    # 复用 VR 框架注册验证产物
    vr = validate_execution(project_dir, exec_id, checks,
                            provenance={"engine": FIDELITY_ENGINE,
                                        "experiment_idx": experiment_idx,
                                        "fidelity_status": fid["status"]})
    # fidelity 报告文件（与 execution 同目录系，K002 测量层直接消费）
    rep_dir = project_dir / "state" / "fidelity"
    rep_dir.mkdir(parents=True, exist_ok=True)
    rep_path = rep_dir / f"{exec_id}.json"
    report = {
        "execution_id": exec_id,
        "verification_id": vr.verification_id,
        "fidelity_status": fid["status"],
        "fidelity_score": fid["fidelity_score"],
        "passed": fid["passed"],
        "total": fid["total"],
        "checks": fid["checks"],
        "engine": FIDELITY_ENGINE,
    }
    rep_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return {"verification_id": vr.verification_id,
            "fidelity_status": fid["status"],
            "fidelity_score": report["fidelity_score"],
            "passed": fid["passed"], "total": fid["total"],
            "checks": fid["checks"], "report_path": str(rep_path)}


def main(argv: list[str] | None = None) -> int:
    """CLI：python -m runtime.execution.fidelity <项目> <exec_id> <model_ir.json>"""
    import argparse
    ap = argparse.ArgumentParser(description="MODEL_IR → 执行结果的 fidelity 校验")
    ap.add_argument("project")
    ap.add_argument("exec_id")
    ap.add_argument("model_ir", help="MODEL_IR JSON 文件路径")
    args = ap.parse_args(argv)
    model_ir = json.loads(Path(args.model_ir).read_text(encoding="utf-8"))
    out = verify_fidelity(args.project, model_ir, args.exec_id)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["fidelity_status"] == "aligned" else 1
