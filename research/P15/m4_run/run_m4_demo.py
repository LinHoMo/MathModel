# -*- coding: utf-8 -*-
"""P1-M4 演示：2024_A 知识引导 vs 无引导候选对比（完整 M3 管线）。

落盘（research/P15/m4_run/project/，自清理可复现）：
- state/registry.json + evidence_graph.json + status.json
- artifacts/exec/{input.json,output.json}（真实 subprocess 工件）
- replay_report.json（EXEC 重放零偏差）
- m4_summary.json（义务完备度对比表 + EXEC/VR 数值）

运行：py -3.12 research/P15/m4_run/run_m4_demo.py
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_HERE = Path(__file__).resolve().parent
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent / "m3_run") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "m3_run"))

from m3_driver import (artifact_ids, decisions_of, make_session,  # noqa: E402
                       relation_pairs, replay_report, run_competition)
from m4_fixtures import (CANDIDATES, GUIDED_MODEL_ID,  # noqa: E402
                         UNGUIDED_MODEL_ID, bzd_cards)

PROJECT_DIR = _HERE / "project"


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2),
                    encoding="utf-8")


def obligations_summary(session, mir_ids: list[str]) -> dict:
    """义务完备度：每个候选 MODEL_IR 的 validations/assumptions/risks/dependencies 项数。"""
    out = {}
    for mir_id in mir_ids:
        a = session.registry.get(mir_id)
        d = a.data or {}
        vals = d.get("validations") or []
        assum = d.get("assumptions") or []
        risks = d.get("risks") or []
        deps = d.get("dependencies") or []
        out[mir_id] = {
            "model_id": d.get("model_id"),
            "n_validations": len(vals),
            "n_assumptions": len(assum),
            "n_risks": len(risks),
            "n_dependencies": len(deps),
            "obligation_total": len(vals) + len(assum) + len(risks),
            "source_cards": sorted({v.get("source_card")
                                    for v in vals + assum + risks
                                    if v.get("source_card")}),
            "knowledge_refs": d.get("knowledge_refs") or [],
        }
    return out


def exec_summary(session, exec_ids: list[str]) -> dict:
    out = {}
    for eid in exec_ids:
        a = session.registry.get(eid)
        d = a.data or {}
        diag = (d.get("outputs") or {}).get("diagnostics") or {}
        out[eid] = {
            "status": d.get("status"),
            "returncode": d.get("returncode"),
            "body_spacing": diag.get("ell_body"),
        }
    return out


def vr_summary(session, vr_ids: list[str]) -> dict:
    out = {}
    for vid in vr_ids:
        a = session.registry.get(vid)
        d = a.data or {}
        out[vid] = {
            "execution_id": d.get("execution_id"),
            "status": d.get("status"),
            "mathematical_valid": d.get("mathematical_valid"),
            "execution_valid": d.get("execution_valid"),
            "constraint_violation_max": d.get("constraint_violation_max"),
            "domain_violation": d.get("domain_violation"),
            "robustness": d.get("robustness"),
        }
    return out


def main() -> dict:
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    workdir = PROJECT_DIR / "artifacts" / "exec"
    t0 = time.perf_counter()
    session, results = run_competition(make_session(PROJECT_DIR), workdir,
                                       candidates=CANDIDATES)
    elapsed = round(time.perf_counter() - t0, 2)

    mirs = artifact_ids(session, "model_ir")
    codes = artifact_ids(session, "code")
    execs = artifact_ids(session, "execution_result")
    vrs = artifact_ids(session, "verification_result")
    decisions = decisions_of(session)
    pairs = relation_pairs(session)

    decision = decisions[0]
    ddata = decision["data"]
    selects = [p for p in pairs if p[1] == "selects"]

    summary = {
        "scenario": "P1-M4 知识引导 vs 无引导（2024_A Q1）",
        "elapsed_sec": elapsed,
        "guide_cards": [{"id": c.card_id, "version": c.version,
                         "source_type": c.source_type}
                        for c in bzd_cards()],
        "obligations": obligations_summary(session, mirs),
        "exec_summary": exec_summary(session, execs),
        "vr_summary": vr_summary(session, vrs),
        "selection": {
            "chosen": ddata.get("chosen"),
            "confidence": ddata.get("confidence"),
            "alternatives": ddata.get("alternatives"),
            "criteria": ddata.get("criteria"),
            "evidence_ids": ddata.get("evidence_ids"),
            "reasoning": ddata.get("reasoning"),
            "selects_edges": sorted(selects),
        },
        "node_results": {k: v.status for k, v in results.items()},
    }

    # 重放：两个 EXEC 各自重放并断言输出一致
    replay = {}
    for eid in execs:
        rep = replay_report(PROJECT_DIR, eid)
        replay[eid] = {k: rep.get(k) for k in
                       ("ok", "outputs_match", "deviation", "original_id")}
    summary["replay"] = replay

    session.checkpoint()
    dump_json(PROJECT_DIR / "state" / "registry.json",
              [{"artifact_id": a.artifact_id, "artifact_type": a.type,
                "question": a.question, "title": a.title, "data": a.data,
                "payload": a.payload} for a in session.registry.all()])
    dump_json(PROJECT_DIR / "state" / "evidence_graph.json",
              {"relations": session.graph.relations})
    dump_json(PROJECT_DIR / "state" / "status.json",
              {"project": "vs001-m4-demo", "status": "completed",
               "node_results": summary["node_results"]})
    dump_json(PROJECT_DIR / "replay_report.json", replay)
    dump_json(_HERE / "m4_summary.json", summary)
    print("P1-M4 demo done:", PROJECT_DIR)
    print(json.dumps(summary, ensure_ascii=False, indent=1)[:1200])
    return summary


if __name__ == "__main__":
    main()
