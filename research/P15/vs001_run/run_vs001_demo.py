# -*- coding: utf-8 -*-
"""P1-VS-001 演示运行：2024_A 垂直切片闭环，产物落盘到 research/P15/vs001_run/project/。

用法：
    cd C:\\Users\\Lin\\Desktop\\Programs\\MathModel
    py -3.12 research/P15/vs001_run/run_vs001_demo.py

落盘产物：
    project/state/registry.json          # P001/M1/C1/R1/V1/M2/C2/R2/V2 …
    project/state/evidence_graph.json    # 完整谱系边（instantiates/implemented_by/
                                         #   executed_by/produces/verified_by/
                                         #   revision_of/supersedes）
    project/state/status.json            # 流程状态投影
    replay_report.json                   # RUN1/RUN2 重放偏差报告（输出一致）
    demo_summary.json                    # 闭环数值与边摘要
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
for p in (REPO / "core", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from vs001_driver import (  # noqa: E402
    artifact_ids, make_session, relation_pairs, replay_report, run_m1, run_m2,
)

PROJECT_DIR = HERE / "project"


def main() -> dict:
    import shutil
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    workdir = PROJECT_DIR / "artifacts" / "exec"
    session = make_session(PROJECT_DIR)
    summary = {"project_dir": str(PROJECT_DIR), "problem": "2024_A Q1"}

    # ---- M1 → RUN1 → VALIDATION FAIL
    session, _ = run_m1(session, workdir)
    exec1 = artifact_ids(session, "execution_result")[0]
    vr1 = artifact_ids(session, "verification_result")[0]
    ex1 = session.registry.get(exec1)
    v1 = session.registry.get(vr1)
    summary["m1_run"] = {
        "execution_id": exec1,
        "exit_code": ex1.data["returncode"],
        "status": ex1.data["status"],
        "body_spacing_measured": ex1.data["outputs"]["pair_distances"]["0"][1],
        "head_speed_60": ex1.data["outputs"]["head_speeds"]["60"],
        "verification_id": vr1,
        "verdict": v1.data["status"],
        "mathematical_valid": v1.data["mathematical_valid"],
        "constraint_violation_max": v1.data["constraint_violation_max"],
    }

    # ---- REVISION → M2 → RUN2 → VALIDATION PASS
    mir1 = artifact_ids(session, "model_ir")[0]
    session, _ = run_m2(session, mir1, workdir)
    execs = artifact_ids(session, "execution_result")
    exec2 = [e for e in execs if e != exec1][0]
    vrs = artifact_ids(session, "verification_result")
    vr2 = [v for v in vrs if v != vr1][0]
    ex2 = session.registry.get(exec2)
    v2 = session.registry.get(vr2)
    summary["m2_run"] = {
        "execution_id": exec2,
        "exit_code": ex2.data["returncode"],
        "status": ex2.data["status"],
        "body_spacing_measured": ex2.data["outputs"]["pair_distances"]["0"][1],
        "head_speed_60": ex2.data["outputs"]["head_speeds"]["60"],
        "verification_id": vr2,
        "verdict": v2.data["status"],
        "mathematical_valid": v2.data["mathematical_valid"],
        "empirical_valid": v2.data["empirical_valid"],
        "robustness": v2.data["robustness"],
        "constraint_violation_max": v2.data["constraint_violation_max"],
    }

    # ---- 谱系边
    rels = sorted(relation_pairs(session))
    summary["relations"] = [{"from": f, "relation": r, "to": t}
                            for f, r, t in rels]

    # ---- Replay 验证（验收 7）
    replay_report_r1 = replay_report(PROJECT_DIR, exec1)
    replay_report_r2 = replay_report(PROJECT_DIR, exec2)
    summary["replay"] = {
        "run1": {"ok": replay_report_r1["ok"],
                 "outputs_match": replay_report_r1["outputs_match"],
                 "replayed_status": replay_report_r1["replayed_status"]},
        "run2": {"ok": replay_report_r2["ok"],
                 "outputs_match": replay_report_r2["outputs_match"],
                 "replayed_status": replay_report_r2["replayed_status"]},
    }
    (HERE / "replay_report.json").write_text(
        json.dumps({"run1": replay_report_r1, "run2": replay_report_r2},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "demo_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    main()
