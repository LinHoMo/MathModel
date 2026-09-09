# -*- coding: utf-8 -*-
"""P1-M3 演示：2024_A 双候选真实跑通候选竞技场 + evidence-based 选型。

落盘（research/P15/m3_run/project/）：
- state/registry.json + evidence_graph.json + status.json（等）
- artifacts/exec/{input.json,output.json}（真实 subprocess 工件）
- replay_report.json（RUN1/RUN2 重放零偏差）
- demo_summary.json（闭环数值摘要）

运行：py -3.12 research/P15/m3_run/run_m3_demo.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_HERE = Path(__file__).resolve().parent
if str(_REPO / "core") not in sys.path:
    sys.path.insert(0, str(_REPO / "core"))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from m3_driver import (artifact_ids, decisions_of, make_session,  # noqa: E402
                       relation_pairs, replay_report, run_competition)

PROJECT_DIR = _HERE / "project"


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2),
                    encoding="utf-8")


def main() -> dict:
    # 清理本演示自产目录（可复现：同一命令 → 同一落盘）
    import shutil
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    workdir = PROJECT_DIR / "artifacts" / "exec"
    t0 = time.perf_counter()
    session, results = run_competition(make_session(PROJECT_DIR), workdir)
    elapsed = round(time.perf_counter() - t0, 2)

    mirs = artifact_ids(session, "model_ir")
    codes = artifact_ids(session, "code")
    execs = artifact_ids(session, "execution_result")
    vrs = artifact_ids(session, "verification_result")
    decisions = decisions_of(session)
    pairs = relation_pairs(session)

    # 决策明细
    decision = decisions[0]
    ddata = decision["data"]
    chosen = ddata["chosen"]
    evidence_ids = ddata["evidence_ids"]
    selects = [p for p in pairs if p[1] == "selects"]

    # VR 数值摘要
    vr_summary = {}
    for vr_id in vrs:
        a = session.registry.get(vr_id)
        d = a.data or {}
        vr_summary[vr_id] = {
            "execution_id": d.get("execution_id"),
            "status": d.get("status"),
            "mathematical_valid": d.get("mathematical_valid"),
            "constraint_violation_max": d.get("constraint_violation_max"),
            "objective_value": d.get("objective_value"),
            "robustness": d.get("robustness"),
        }
    exec_summary = {}
    for xid in execs:
        a = session.registry.get(xid)
        d = a.data or {}
        outs = d.get("outputs") or {}
        pd = outs.get("pair_distances") or {}
        hs = outs.get("head_speeds") or {}
        exec_summary[xid] = {
            "status": d.get("status"), "returncode": d.get("returncode"),
            "body_spacing": (pd.get("0") or [None, None])[1]
            if pd.get("0") else None,
            "head_speed_60": hs.get("60"),
        }

    # Replay 验证
    replay = {}
    for xid in execs:
        replay[xid] = replay_report(str(PROJECT_DIR), xid)

    summary = {
        "scenario": "P1-M3 candidate competition (2024_A Q1)",
        "elapsed_sec": elapsed,
        "artifacts": {
            "model": artifact_ids(session, "model"),
            "model_ir": mirs, "code": codes,
            "execution_result": execs, "result": artifact_ids(session, "result"),
            "verification_result": vrs,
        },
        "selection": {
            "decision_id": decision["artifact_id"],
            "chosen": chosen,
            "alternatives": ddata.get("alternatives"),
            "criteria": ddata.get("criteria"),
            "evidence_ids": evidence_ids,
            "confidence": ddata.get("confidence"),
            "reasoning": ddata.get("reasoning"),
            "ranked": ddata.get("ranked"),
            "selects_edges": [list(p) for p in selects],
        },
        "vr_summary": vr_summary,
        "exec_summary": exec_summary,
        "replay": replay,
        "node_results": {k: v.status for k, v in results.items()},
    }

    # 落盘
    dump_json(PROJECT_DIR / "state" / "registry.json",
              {"artifacts": {a.artifact_id: a.to_dict()
                             for a in session.registry.all()}})
    dump_json(PROJECT_DIR / "state" / "evidence_graph.json",
              {"relations": [dict(r) for r in session.graph.relations]})
    dump_json(PROJECT_DIR / "state" / "status.json",
              {"scenario": summary["scenario"],
               "selection": summary["selection"],
               "node_results": summary["node_results"]})
    dump_json(PROJECT_DIR / "replay_report.json", replay)
    dump_json(_HERE / "demo_summary.json", summary)

    # 校验闭环关键断言（与 e2e 同源）
    assert len(mirs) == 2 and len(codes) == 2 and len(execs) == 2 \
        and len(vrs) == 2, "候选/执行/验证链必须各 2 条"
    assert chosen == "MIR002", f"chosen 应为 MIR002，实际 {chosen}"
    assert "MIR001" in [a["model_ir"] for a in ddata["alternatives"]]
    assert set(evidence_ids) == set(vrs), "evidence_ids 应指向全部候选 VR"
    assert selects and selects[0][1] == "selects"
    for xid, rep in replay.items():
        assert rep.get("ok") is True and rep.get("outputs_match") is True, \
            f"{xid} replay 不一致: {rep}"

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n演示完成：{PROJECT_DIR}（replay 零偏差）")
    return summary


if __name__ == "__main__":
    main()
