# -*- coding: utf-8 -*-
"""Candidate Arena benchmark — 固化 P1-M3 候选竞技场为正式可复现 benchmark。

候选池：外部 Agent 真实产物（P15-K003 正式 runs：model_ir + run_model.py +
output_mapping），harness 重跑 真实执行 → 数值验证 → evidence-based 选型。
全链机械（LLM-free）。

铁律：
- 选型只依据机械证据（exec_status / VR valid / constraint_violation_max /
  fidelity_score），禁止 recs[0]/first()/硬编码默认；
- 无候选满足 → 如实 UNSELECTED（不硬选）；
- 执行全部真实 subprocess 重跑（run_code_pipeline，不读旧 execution_result，
  保证可复现）；
- 验证用通用检查集（derive_checks_from_mir + output_mapping 输出键解析），
  不绑定任何题目的特制参考值（FIX-5.2 通用路径）。

契约说明（治理记录）：K003 实验 register 与 runtime registry 的 MODEL_IR
契约当前并存（实验侧宽松、runtime 侧模板对齐严格）；arena 作为 benchmark 工具
走 run_code_pipeline 轻量执行路径（不注入 runtime registry schema），候选
MODEL_IR 只要求 fidelity 可读结构（variables/objectives 等），执行/验证由
harness 完成。契约统一是独立治理项（STATUS.md「统一节点标准」待办）。

用法：
    py -3.12 research/P15/benchmark/arena/arena_runner.py            # 全池
    py -3.12 research/P15/benchmark/arena/arena_runner.py --problems 2011_B 2019_C
输出：{workdir}/arena_report.json + ARENA_BENCHMARK_REPORT.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]  # arena/benchmark/P15/research/<repo>
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from modeling_harness.runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from modeling_harness.runtime.execution.codegen import run_code_pipeline  # noqa: E402
from modeling_harness.runtime.execution.validation import (  # noqa: E402
    derive_checks_from_mir,
    run_numeric_validation,
    validate_against_gt,
)

DEFAULT_POOL = _REPO / "research" / "P15" / "experiments" / "P15-K003" / "runs"
DEFAULT_WORKDIR = _REPO / "research" / "P15" / "benchmark" / "arena" / "runs"


# ---------------------------------------------------------------- 候选池加载

def load_pool(pool_root: Path) -> dict[str, list[dict]]:
    """从候选池目录加载真实候选：{problem_id: [Candidate]}。

    Candidate = {run_id, arm, problem_id, model_ir, code, output_mapping,
                 inputs, validation_plan}。只加载有 model_ir+code+output_mapping
    的 run（缺任一契约文件的 run 不入池，报告中披露）。
    """
    pool: dict[str, list[dict]] = {}
    skipped: list[dict] = []
    for run_dir in sorted(pool_root.iterdir()):
        if not run_dir.is_dir():
            continue
        mir_f, code_f, om_f, man_f = (run_dir / "model_ir.json",
                                      run_dir / "run_model.py",
                                      run_dir / "output_mapping.json",
                                      run_dir / "manifest.json")
        if not man_f.exists():
            skipped.append({"run_id": run_dir.name, "reason": "缺 manifest.json"})
            continue
        manifest = json.loads(man_f.read_text(encoding="utf-8"))
        pid = manifest.get("problem_id")
        if not pid:
            skipped.append({"run_id": run_dir.name, "reason": "manifest 无 problem_id"})
            continue
        if not mir_f.exists():
            # K003 设计：F 臂（自由文本输入）不产生 MODEL_IR，不入 arena 池
            skipped.append({"run_id": run_dir.name, "reason": "F 臂无 model_ir"
                           if manifest.get("arm") == "F" else "缺 model_ir.json"})
            continue
        if not all(f.exists() for f in (code_f, om_f)):
            skipped.append({"run_id": run_dir.name,
                            "reason": "缺 run_model.py 或 output_mapping.json"})
            continue
        cand = {
            "run_id": run_dir.name,
            "arm": manifest.get("arm"),
            "problem_id": pid,
            "model_ir": json.loads(mir_f.read_text(encoding="utf-8")),
            "code": code_f.read_text(encoding="utf-8"),
            "output_mapping": json.loads(om_f.read_text(encoding="utf-8")),
        }
        pool.setdefault(pid, []).append(cand)
    return pool, skipped


def _nonneg_variable_names(mir: dict) -> list[str]:
    """从 MODEL_IR 声明提取非负变量输出名（用于 L6
    output_nonnegative 的 paths 派生）：

    domain.lower >= 0 或状态/决策/观测变量且无负下界声明。
    保守原则：只对明确非负的变量下断言，不误伤
    合法可负值（回归系数/坐标/收益差等）。
    """
    out: list[str] = []
    for v in mir.get("variables") or []:
        dom = v.get("domain") or {}
        lower = None
        if isinstance(dom, dict):
            lower = dom.get("lower")
        if lower is not None and lower >= 0:
            sym = v.get("symbol") or v.get("name")
            if sym:
                out.append(sym)
        elif v.get("type") in ("state", "decision", "observation", "constant"):
            sym = v.get("symbol") or v.get("name")
            if sym and not (isinstance(lower, (int, float)) and lower < 0):
                out.append(sym)
    return out


def _with_derived_paths(gt_assertions: dict | None, cand: dict) -> dict | None:
    """为 output_nonnegative 断言派生 paths（从 MODEL_IR 非负变量）。"""
    if not gt_assertions:
        return None
    g = dict(gt_assertions)
    g["checks"] = []
    for c in gt_assertions.get("checks") or []:
        c = dict(c)
        if c.get("kind") == "output_nonnegative" and not c.get("paths"):
            paths = _nonneg_variable_names(cand.get("model_ir") or {})
            if not paths:
                continue  # 无非负声明变量：该断言不可派生，不判输
            c["paths"] = paths
        g["checks"].append(c)
    return g


def build_spec(cand: dict) -> dict:
    """通用验证规格：MODEL_IR 派生检查 + output_mapping 输出键解析。

    不做任何题目特制数值参考（通用最小真实验证，FIX-5.2 路径）。
    """
    checks = derive_checks_from_mir(cand["model_ir"])
    om = cand.get("output_mapping") or {}
    for c in checks:
        c["path"] = om.get(c["path"], c["path"])
    return {"checks": checks}


# ---------------------------------------------------------------- 竞技场执行

def run_candidate(cand: dict, workdir: Path) -> dict:
    """单个候选：真实执行 + fidelity（全机械，可复现）。

    数值验证（VR）在 run_arena 统一做（用该候选真实 EXEC outputs）。
    返回 {run_id, arm, model_id, exec_status, fidelity_score, execution_id}。
    """
    mir = cand["model_ir"]
    model_id = mir.get("model_id") or cand["run_id"]
    pipeline = run_code_pipeline(
        workdir, mir, cand["code"], model_id=model_id,
        output_mapping=cand.get("output_mapping"),
        adapter=LocalPythonAdapter())
    return {"run_id": cand["run_id"], "arm": cand["arm"],
            "model_id": model_id,
            "exec_status": pipeline.get("exec_status"),
            "fidelity_score": pipeline.get("fidelity_score"),
            "execution_id": pipeline.get("exec_id")}


def _fetch_outputs(cand: dict, workdir: Path) -> dict:
    """从该候选最近 EXEC artifact 读取真实 outputs（供 VR 数值验证）。"""
    from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
    reg = ArtifactRegistry(workdir / "state" / "registry.json")
    execs = [a for a in reg.list_by_type("execution_result")]
    if not execs:
        return {}
    x = execs[-1]
    return (x.data or {}).get("outputs") or {}


def select_by_evidence(rows: list[dict]) -> dict:
    """机械选型：只看机械证据（exec_status→valid→cvm→fidelity）。

    排序键（严格序）：exec_status=success > valid=True > cvm 小 > fidelity 高。
    无 success → UNSELECTED（如实，不硬选）。返回 {selected, chosen, basis, rows}。
    """
    alive = [r for r in rows if r.get("exec_status") == "success"]
    if not alive:
        return {"selected": False, "chosen": None,
                "basis": ["无候选执行成功（exec_status≠success），如实不选型"]}
    valid = [r for r in alive if r.get("valid") is True]
    pool = valid if valid else alive
    pool = sorted(pool, key=lambda r: (
        0 if r.get("valid") is True else 1,
        0 if (r.get("l6_status") or "unverifiable") == "passed" else 1,
        r.get("constraint_violation_max") if r.get("constraint_violation_max")
        is not None else float("inf"),
        -(r.get("fidelity_score") or 0.0),
    ))
    best = pool[0]
    basis = [
        f"exec_status={best['exec_status']}",
        f"valid={best.get('valid')}",
        f"l6={best.get('l6_status')}",
        f"cvm={best.get('constraint_violation_max')}",
        f"fidelity={best.get('fidelity_score')}",
    ]
    if not valid:
        basis.append("（无候选通过数值验证，在存活候选中选择约束违反最小者——"
                     "如实标注降级选型）")
    return {"selected": True, "chosen": best["model_id"], "basis": basis,
            "evidence": [r.get("execution_id") for r in pool]}


# ---------------------------------------------------------------- 报告

def render_markdown(report: dict) -> str:
    lines = [
        "# Candidate Arena Benchmark 报告",
        "",
        f"> 候选池：`{report['pool']}` ｜ 生成：{report['generated_at']} ｜ "
        f"模式：`{report['mode']}`（真实 subprocess 重跑，机械选型）",
        "",
        "## 汇总",
        "",
        f"- 题目数：{report['summary']['problems']}",
        f"- 候选总数：{report['summary']['candidates']}",
        f"- 有选型决策：{report['summary']['selected']}",
        f"- 如实不选型（UNSELECTED）：{report['summary']['unselected']}",
        "",
        "## 逐题结果",
        "",
    ]
    for p in report["problems"]:
        lines += [f"### {p['problem_id']}", ""]
        lines += ["| 候选 | 臂 | exec_status | valid | cvm | l6 | fidelity | 选型 |",
                  "|---|---|---|---|---|---|---|---|"]
        for c in p["candidates"]:
            sel = "✓" if c["model_id"] == p["decision"].get("chosen") else ""
            lines.append(f"| {c['run_id'][:8]} | {c['arm']} | "
                         f"{c['exec_status']} | {c['valid']} | "
                         f"{c['constraint_violation_max']} | "
                         f"{c.get('l6_status')} | "
                         f"{c['fidelity_score']} | {sel} |")
        d = p["decision"]
        lines += ["", "**决策**："
                  f"{'选择 ' + str(d['chosen']) if d['selected'] else 'UNSELECTED（无候选满足验证）'}"]
        for b in (d.get("basis") or []):
            lines += [f"- 依据：{b}"]
        lines += [""]
    lines += [
        "## 验证语义说明",
        "",
        "- `valid` = 通用确定性检查（FIX-5.2：MODEL_IR 声明变量/目标键出现在真实",
        "  执行输出 + output_mapping 输出键解析）——**结构级检查，不是数值正确性**；",
        "- `cvm`（constraint_violation_max）与 `fidelity_score` 为机械判定（VR/",
        "  fidelity 管线）；",
        "- `l6` = ground-truth 断言判定（`problem_cards/*/gt.json#l6_assertions`：",
        "  feasibility / objective_finite / 输出非负等数学必然与题面客观边界，",
        "  非答案数值）；无断言 → `unverifiable`（不编造分数）；",
        "- 选型决策只基于上表机械证据，无证据不选型（UNSELECTED 如实报告）。",
        "",
    ]
    return "\n".join(lines)


def run_arena(pool_root: Path, workdir: Path,
              problems: list[str] | None = None) -> dict:
    pool, skipped = load_pool(pool_root)
    if problems:
        pool = {p: pool[p] for p in problems if p in pool}
    workdir.mkdir(parents=True, exist_ok=True)

    report = {
        "mode": "arena_benchmark",
        "pool": str(pool_root),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "skipped_runs": skipped,
        "l6_assertions": "problem_cards/*/gt.json#l6_assertions（v1.0，"
                         "mathematical_necessity + problem_statement 客观边界）",
        "problems": [],
        "summary": {"problems": 0, "candidates": 0,
                    "selected": 0, "unselected": 0},
    }
    for pid, candidates in sorted(pool.items()):
        # P2-1 L6：加载该题的 ground-truth 断言（无断言 → unverifiable）
        gt_path = _REPO / "research" / "P15" / "benchmark" / "problem_cards" \
            / pid / "gt.json"
        gt_assertions = None
        if gt_path.exists():
            gt_assertions = (json.loads(gt_path.read_text(encoding="utf-8"))
                             .get("l6_assertions"))
        rows = []
        for cand in candidates:
            row = run_candidate(cand, workdir)
            # VR 数值验证：用该候选自己的真实 outputs（EXEC artifact）
            if row["exec_status"] == "success":
                outputs = _fetch_outputs(cand, workdir)
                cand["_outputs"] = outputs
                spec = build_spec(cand)
                vd = run_numeric_validation(outputs, spec)
                row.update({"valid": vd.get("mathematical_valid"),
                            "constraint_violation_max": vd.get(
                                "constraint_violation_max"),
                            "status": vd.get("status"),
                            "checks": vd.get("checks")})
                # P2-1 L6：ground-truth 断言判定（机械；无断言如实 unverifiable）
                l6 = validate_against_gt(
                    {"status": row["exec_status"], "outputs": outputs,
                     "constraint_violation_max": vd.get(
                         "constraint_violation_max"),
                     "objective_value": vd.get("objective_value"),
                     "objective_sane": vd.get("objective_sane")},
                    _with_derived_paths(gt_assertions, cand))
                row.update({"l6_status": l6.get("status"),
                            "l6_score": l6.get("l6_score"),
                            "l6_checks": l6.get("checks")})
            rows.append(row)
        decision = select_by_evidence(rows)
        report["problems"].append({"problem_id": pid, "candidates": rows,
                                   "decision": decision})
        report["summary"]["problems"] += 1
        report["summary"]["candidates"] += len(rows)
        report["summary"]["selected" if decision["selected"] else "unselected"] += 1

    (workdir / "arena_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (workdir / "ARENA_BENCHMARK_REPORT.md").write_text(
        render_markdown(report), encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="Candidate Arena benchmark")
    ap.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    ap.add_argument("--workdir", type=Path, default=DEFAULT_WORKDIR)
    ap.add_argument("--problems", nargs="*", default=None)
    args = ap.parse_args()
    report = run_arena(args.pool, args.workdir, args.problems)
    print(render_markdown(report))


if __name__ == "__main__":
    main()
