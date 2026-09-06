#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把基线校准跑（2000_C）的真实实验/结果/声明注册进 V3 证据链。

确定性管线产出的骨架产物（M/E/R/C 编号）之外，本脚本补登记 agent 真实
解题产生的实验与结果（真实数值来自 figures/all_results.json），使
experiment validity / validation reliability 指标度量真实工作而非占位产物。
已知缺口（记入 P13 backlog）：agent 产物目前只能事后注册，handlers 尚未
提供 agent 结果的正式接入节点。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]        # 仓库根（sys.path → core）
PROJECT = Path(__file__).resolve().parents[1]     # 项目目录
sys.path.insert(0, str(ROOT / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402

QUESTIONS = ["Q001", "Q002", "Q003", "Q004"]


def main() -> int:
    results = json.loads(
        (PROJECT / "figures" / "all_results.json").read_text(encoding="utf-8"))
    s = RuntimeSession(PROJECT, QUESTIONS)       # 载入既有状态（不重跑）
    qids = {a.title: a.artifact_id
            for a in s.registry.list_by_type("question")}

    specs = [
        # (title, question, metrics, tags, runs)
        ("真实实验: 分段生存率估计与稳定年龄结构", "Q001",
         [{"metric": "S_adult", "value": results["Q1_survival_age_structure"]
           ["segment_survival_S"]["adult_2_50"], "unit": "1/yr"},
          {"metric": "calf_share_pct", "value":
           results["Q1_survival_age_structure"]
           ["age_structure_11000"]["calf_share_pct"], "unit": "%"}],
         ["baseline"], 1),
        ("真实实验: Leslie 矩阵避孕配额（双情景 + bootstrap）", "Q002",
         [{"metric": "cows_darted_per_year", "value":
           results["Q2_darting_quota"]
           ["scenario_B_culling_calibrated"]["cows_per_year"], "unit": "cows/yr"},
          {"metric": "relocation_eq_per_year", "value":
           results["Q2_darting_quota"]
           ["scenario_B_culling_calibrated"]["relocation_eq_per_year"],
           "unit": "heads/yr"}],
         ["baseline", "sensitivity", "multi_run"],
         results["n_runs"]),
        ("真实实验: 灾难恢复模拟（30/50/70% × 双情景）", "Q003",
         [{"metric": "recovery_50pct_years", "value":
           results["Q3_catastrophe_recovery"]
           ["B_calibrated_kill_50pct_recovery_years"], "unit": "yr"}],
         ["baseline", "sensitivity"], 1),
        ("真实实验: 规模泛化方案表（5 规模 × 3 生存档）", "Q004",
         [{"metric": "plan_rows", "value":
           len(results["Q4_generalization"]["plan_table"]), "unit": "rows"}],
         ["baseline", "sensitivity"], 1),
    ]
    created = []
    for title, qlabel, metrics, tags, runs in specs:
        qid = qids[qlabel]
        model = next((a for a in s.registry.list_by_type("model")
                      if a.question == qid), None)
        exp = s.registry.create("experiment", title=title, question=qid,
                                depends_on=[model.artifact_id]
                                if model else [],
                                data={"runs": runs, "seed": results["seed"],
                                      "source": "agent-run main.py"},
                                created_by="agent-baseline", activate=True)
        res = s.registry.create(
            "result", title=f"{title} — 结果", question=qid,
            depends_on=[exp.artifact_id], data={"metrics": metrics,
                                                "runs": runs},
            tags=tags, created_by="agent-baseline", activate=True)
        claim = s.registry.create(
            "claim", title=f"{title.split(':')[-1].strip()} 的结论成立",
            question=qid, depends_on=[res.artifact_id],
            created_by="agent-baseline", activate=True)
        s.graph.add_relation(exp.artifact_id, "produces", res.artifact_id)
        s.graph.add_relation(res.artifact_id, "supports", claim.artifact_id)
        created.append((exp.artifact_id, res.artifact_id, claim.artifact_id))

    s.checkpoint()
    for exp_id, res_id, claim_id in created:
        print(f"[OK] {exp_id} → {res_id} → {claim_id}")
    cov = s.graph.coverage()
    print(f"[OK] claims {cov.get('claims_supported')}/"
          f"{cov.get('claims_total')} · registry {len(s.registry)} artifacts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
