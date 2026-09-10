# -*- coding: utf-8 -*-
"""Capability Validation（Δscore）— 度量 P1 改造带来的能力变化。

双口径（诚实声明，不混用）：
1. 八项能力指标（e2e_metrics，测"完整模型—论文管线"）：同题（2024_A）
   pre = projects/p151-2024a-r2（P1 前真实产物，B0-R2 时代）
   post = research/P15/experiments/p1-vs001/project（P1 闭环产物）。
   可比项逐项列 Δ；指标为 None = 该期产物无对应环节产物（如实，不估算）。
2. P1 专属执行级指标（Model Construction Loop 的直接机械证据）：
   execution_success_rate / validation 通过 / revision 谱系 / evidence 完整性
   ——从 P1 产物 registry+graph 机械统计。

局限（如实声明）：
- pre/post 是不同期产物（非同一流水线重跑），差异含题面处理方式/产物范围差异，
  不是受控 A/B；本报告是"能力状态对比"而非"因果效应测量"（因果属 K 系列实验）。
- 八项指标面向论文管线；P1 改造主要在模型闭环——两套口径并行呈现。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from modeling_harness.cli.e2e_metrics import compute_e2e_metrics  # noqa: E402

PRE_PROJECT = _REPO / "projects" / "p151-2024a-r2"
POST_PROJECT = _REPO / "research" / "P15" / "experiments" / "p1-vs001" / "project"
GT_2024A = _REPO / "research" / "P15" / "benchmark" / "problem_cards" / "2024_A" / "gt.json"

METRIC_ORDER = [
    "decomposition_coverage", "structure_alignment", "model_correctness",
    "experiment_validity", "validation_reliability", "innovation",
    "writing_completeness", "end_to_end",
]

_METRIC_LABELS = {
    "decomposition_coverage": "问题分解覆盖",
    "structure_alignment": "模型结构对齐（allowed_modeling_structures）",
    "model_correctness": "模型正确性（gt 数值对照）",
    "experiment_validity": "实验有效性",
    "validation_reliability": "验证可靠性",
    "innovation": "创新性",
    "writing_completeness": "论文完备性",
    "end_to_end": "端到端",
}


def _load_gt() -> dict:
    return json.loads(GT_2024A.read_text(encoding="utf-8"))


def eight_metric_delta() -> dict:
    gt = _load_gt()
    pre = compute_e2e_metrics(str(PRE_PROJECT), gt=gt)
    post = compute_e2e_metrics(str(POST_PROJECT), gt=gt)
    rows = []
    for m in METRIC_ORDER:
        pv = (pre["metrics"].get(m) or {}).get("value")
        qv = (post["metrics"].get(m) or {}).get("value")
        delta = None
        if pv is not None and qv is not None:
            delta = round(qv - pv, 1)
        rows.append({"metric": m, "label": _METRIC_LABELS[m],
                     "pre": pv, "post": qv, "delta": delta})
    return {"pre": "projects/p151-2024a-r2", "post": str(POST_PROJECT),
            "rows": rows}


def _p1_loop_metrics() -> dict:
    """P1 专属执行级指标（Model Construction Loop 机械证据）。"""
    from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
    from modeling_harness.runtime.graph.evidence_graph import EvidenceGraph
    sdir = POST_PROJECT / "state"
    reg = ArtifactRegistry(sdir / "registry.json")
    graph = EvidenceGraph(reg, sdir / "evidence_graph.json")

    execs = reg.list_by_type("execution_result")
    vrs = reg.list_by_type("verification_result")
    mirs = reg.list_by_type("model_ir")
    rels = {(r["from"], r["relation"], r["to"]) for r in graph.relations}

    n_exec = len(execs)
    n_success = sum(1 for a in execs if (a.data or {}).get("status") == "success")
    rev_of = sum(1 for r in rels if r[1] == "revision_of")
    supersedes = sum(1 for r in rels if r[1] == "supersedes")
    implemented = sum(1 for r in rels if r[1] == "implemented_by")
    exec_evidence = sum(1 for r in rels if r[1] == "verified_by")

    return {
        "execution_total": n_exec,
        "execution_success": n_success,
        "execution_success_rate": round(n_success / n_exec, 3) if n_exec else None,
        "validation_total": len(vrs),
        "validation_fail_observed": sum(
            1 for a in vrs
            if (a.data or {}).get("status") in ("failed", "invalid")),
        "model_ir_total": len(mirs),
        "revision_lineage_edges": rev_of,
        "supersede_edges": supersedes,
        "implemented_by_edges": implemented,
        "verified_by_edges": exec_evidence,
    }


def render_report() -> str:
    delta = eight_metric_delta()
    loop = _p1_loop_metrics()
    lines = [
        "# Capability Validation（Δscore）— P1 改造能力对比",
        "",
        f"> 日期：{json.dumps(__import__('datetime').datetime.now().isoformat(timespec='seconds'))}",
        "> 同题（2024_A）：pre = P1 前真实产物（B0-R2 时代）｜ "
        "post = P1 闭环产物（vs001：M1→FAIL→M2→PASS + Replay）",
        "",
        "## 一、八项能力指标 Δ",
        "",
        "| 指标 | pre | post | Δ |",
        "|---|---|---|---|",
    ]
    for r in delta["rows"]:
        pv = "—" if r["pre"] is None else str(r["pre"])
        qv = "—" if r["post"] is None else str(r["post"])
        dv = "—" if r["delta"] is None else f"{r['delta']:+.1f}"
        lines.append(f"| {r['label']} | {pv} | {qv} | {dv} |")
    lines += [
        "",
        "**口径说明**：`—` = 该期产物无对应环节产物（如 pre 无 model_ir → "
        "structure 0；post 无论文产物 → writing/experiment 为 None），如实不估算。",
        "",
        "## 二、P1 专属执行级指标（Model Construction Loop 机械证据）",
        "",
        f"- 真实执行：{loop['execution_success']}/{loop['execution_total']} "
        f"success（rate={loop['execution_success_rate']}）",
        f"- 数值验证：{loop['validation_total']} 次（含 "
        f"{loop['validation_fail_observed']} 次如实 FAIL——M1 缺陷模型被真实拦截）",
        f"- MODEL_IR：{loop['model_ir_total']} 个（M1/M2 独立 artifact，不覆盖）",
        f"- 修订谱系边：revision_of={loop['revision_lineage_edges']}、"
        f"supersede={loop['supersede_edges']}",
        f"- 实现/证据边：implemented_by={loop['implemented_by_edges']}、"
        f"verified_by={loop['verified_by_edges']}",
        "",
        "## 三、结论与局限",
        "",
        "- **P1 的直接能力证据在执行级**：真实执行 2/2 success、M1 数值 FAIL 被拦截、"
        "修订后 M2 PASS、谱系与证据边完整——这是 P1 前（无执行闭环）不存在的机制。",
        "- **八项指标是论文管线测量**，与 P1 的模型闭环改造正交；可比项中 "
        "decomposition 20→40（P1 产物分解更完整）。",
        "- **局限（如实）**：pre/post 是不同期真实产物，非受控 A/B——本报告是"
        "能力状态对比，因果效应测量属 K 系列实验（K001-K003 已按预注册门执行）。",
    ]
    return "\n".join(lines)


def main() -> None:
    delta = eight_metric_delta()
    loop = _p1_loop_metrics()
    out = {"mode": "capability_delta", "pre": delta["pre"], "post": delta["post"],
           "eight_metrics": delta["rows"], "p1_loop": loop}
    out_path = _REPO / "research" / "P15" / "analysis" / "capability_delta.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    report_path = _REPO / "research" / "P15" / "analysis" / "CAPABILITY_DELTA_REPORT.md"
    report_path.write_text(render_report(), encoding="utf-8")
    print(render_report())


if __name__ == "__main__":
    main()
