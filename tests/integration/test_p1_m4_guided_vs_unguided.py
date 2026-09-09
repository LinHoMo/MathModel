# -*- coding: utf-8 -*-
"""P1-M4 知识引导 vs 无引导 e2e — 对比可测量，如实展示不预设"知识必胜"。

场景：2024_A Q1，两个候选共用同一正确求解器（C2_CODE）：
- GUIDED（M2024A-Q1-GUIDED）：MODEL_IR 义务由 BZD 试点卡机械映射
  （validations/assumptions/risks 带 source_card，knowledge_refs 指向卡 id）
- UNGUIDED（M2024A-Q1-UNGUIDED）：义务极少（1 验证 + 1 假设，无知识来源）

断言：
  ① 知识卡→候选义务映射真实可跑（validations 来自方法卡 validation，溯源 card_id）
  ② BZD 试点卡可被检索（source_type=BZD）
  ③ 对比 demo 真实跑通（两候选各真 subprocess + 数值验证），差异可测量
  ④ 全量 pytest 不回归（基线 897+）
  ⑤ LLM-free：候选 MODEL_IR/Code 外部注入，provenance.adapter=local_python
  ⑥ 禁越界（见 commit 清单）
  ⑦ 按序 commit + P1_M4_REPORT.md（不 push）

运行: py -3.12 -m pytest tests/integration/test_p1_m4_guided_vs_unguided.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "core") not in sys.path:
    sys.path.insert(0, str(_REPO / "core"))
if str(_REPO / "research" / "P15" / "m3_run") not in sys.path:
    sys.path.insert(0, str(_REPO / "research" / "P15" / "m3_run"))
if str(_REPO / "research" / "P15" / "m4_run") not in sys.path:
    sys.path.insert(0, str(_REPO / "research" / "P15" / "m4_run"))

from m3_driver import (artifact_ids, decisions_of,  # noqa: E402
                       make_session, relation_pairs, replay_report,
                       run_competition)
from m4_fixtures import (CANDIDATES, GUIDE_CARD_IDS,  # noqa: E402
                         GUIDED_MODEL_ID, UNGUIDED_MODEL_ID, bzd_cards)


@pytest.fixture()
def session(tmp_path):
    s = make_session(tmp_path / "project")
    return s


def _mir_data(session, mir_id: str) -> dict:
    return dict((session.registry.get(mir_id).data or {}))


def test_01_guided_obligations_from_bzd_cards(session):
    """验收①：知识引导候选义务映射真实可跑，validations 来自方法卡并溯源。"""
    session, results = run_competition(session, tmp_workdir(session), candidates=CANDIDATES)

    mirs = artifact_ids(session, "model_ir")
    assert len(mirs) == 2, mirs

    guided = _mir_data(session, "MIR001")
    unguided = _mir_data(session, "MIR002")
    assert guided["model_id"] == GUIDED_MODEL_ID
    assert unguided["model_id"] == UNGUIDED_MODEL_ID

    # 引导候选：BZD 映射义务带 source_card（M2 自身声明 VAL001 无 source_card，跳过）
    assert guided["validations"], "引导候选必须有验证义务"
    cards = {c.card_id: c for c in bzd_cards()}
    sourced = [v for v in guided["validations"] if "source_card" in v]
    assert sourced, "引导候选必须有来自方法卡的验证义务"
    for v in sourced:
        assert v["source_card"] in cards, v
        assert v["obligation"] in [x["obligation"] for x in
                                   _all_mapped_obligations(cards)["validations"]]
    # assumptions/risks：BZD 映射项带 source_card（M2 自身声明项无 source_card，跳过）
    for a in guided["assumptions"]:
        if "source_card" in a:
            assert a["source_card"] in cards
    for r in guided["risks"]:
        if "source_card" in r:
            assert r["source_card"] in cards
    # knowledge_refs 可溯源到 card_id
    assert {ref["id"] for ref in guided["knowledge_refs"]} == set(GUIDE_CARD_IDS)
    # 无引导候选：义务极少且无知识来源
    assert len(unguided["validations"]) == 1
    assert not any(v.get("source_card") for v in unguided["validations"])
    assert not (unguided.get("knowledge_refs") or [])


def _all_mapped_obligations(cards: dict) -> dict:
    from runtime.modeling.candidates import _merge_obligations, \
        map_card_obligations
    oblig = {"validations": [], "assumptions": [], "risks": [], "dependencies": []}
    for c in cards.values():
        oblig = _merge_obligations(oblig, map_card_obligations(c))
    return oblig


def tmp_workdir(session) -> Path:
    wd = Path(session.project_dir) / "work"
    wd.mkdir(parents=True, exist_ok=True)
    return wd


def test_02_obligation_completeness_measurable(session):
    """验收③：义务完备度差异可测量（引导 19 vs 无引导 2，项数明确）。"""
    session, _ = run_competition(session, tmp_workdir(session), candidates=CANDIDATES)
    guided = _mir_data(session, "MIR001")
    unguided = _mir_data(session, "MIR002")

    def total(d: dict) -> int:
        return len(d.get("validations") or []) \
            + len(d.get("assumptions") or []) + len(d.get("risks") or [])

    g, u = total(guided), total(unguided)
    assert g > u, f"引导义务完备度应显著高于无引导: {g} vs {u}"
    assert u >= 1  # MODEL_IR 契约要求 validations/assumptions 非空（极少形态）


def test_03_both_candidates_real_execution_and_validation(session):
    """验收③：两候选各真 subprocess 执行 + 数值验证，独立 EXEC/VR。"""
    session, results = run_competition(session, tmp_workdir(session), candidates=CANDIDATES)
    for nid, r in results.items():
        assert r.status == "pass", f"{nid} -> {r.status}"

    execs = artifact_ids(session, "execution_result")
    vrs = artifact_ids(session, "verification_result")
    assert len(execs) == 2 and len(vrs) == 2, (execs, vrs)

    # 共享同一 code（对比义务而非代码），但 EXEC/VR 每候选独立
    codes = artifact_ids(session, "code")
    assert len(codes) == 1, codes
    pairs = relation_pairs(session)
    assert {("MIR001", "implemented_by", codes[0]),
            ("MIR002", "implemented_by", codes[0])} <= pairs
    assert {("CODE001", "executed_by", "EXEC001"),
            ("CODE001", "executed_by", "EXEC002"),
            ("EXEC001", "verified_by", "VR001"),
            ("EXEC002", "verified_by", "VR002")} <= pairs

    # status 来自真实退出码
    for xid in execs:
        xd = session.registry.get(xid).data or {}
        assert xd.get("returncode") == 0, xid
        assert xd.get("status") == "success", xid
        assert (xd.get("outputs") or {}), xid
    for vid in vrs:
        vd = session.registry.get(vid).data or {}
        assert vd["status"] == "passed"
        assert vd["mathematical_valid"] is True
        assert vd["constraint_violation_max"] == 0.0


def test_04_selection_runs_with_evidence(session):
    """验收③：选型基于真实 VR 证据；无引导候选"碰巧也 PASS"时如实呈现平局。"""
    session, _ = run_competition(session, tmp_workdir(session), candidates=CANDIDATES)
    decisions = decisions_of(session)
    assert len(decisions) == 1
    d = decisions[0]["data"]
    assert set(d["evidence_ids"]) == {"VR001", "VR002"}
    assert d["chosen"] in ("MIR001", "MIR002")
    # 两个候选 cv=0.0 平局 → 确定性 tie-break（如实，不伪造差异）
    cv = {a["model_ir"]: a["constraint_violation_max"]
          for a in d["alternatives"]}
    assert cv == {"MIR001": 0.0, "MIR002": 0.0}
    pairs = relation_pairs(session)
    selects = [p for p in pairs if p[1] == "selects"]
    assert selects and selects[0][0] == decisions[0]["artifact_id"]


def test_05_replay_consistent(session):
    """验收③：两个 EXEC 均可从磁盘重放且输出一致。"""
    project = session.project_dir
    session, _ = run_competition(session, tmp_workdir(session), candidates=CANDIDATES)
    session.checkpoint()
    for xid in ("EXEC001", "EXEC002"):
        rep = replay_report(str(project), xid)
        assert rep.get("ok") is True, rep
        assert rep.get("outputs_match") is True, rep
        assert rep.get("deviation") == [], rep


def test_06_llm_free_boundary(session):
    """验收⑤：候选 MODEL_IR/Code 外部注入；EXEC provenance 指向 local_python。"""
    shared = session.executor_impl.shared
    assert len(CANDIDATES) == 2
    for c in CANDIDATES:
        assert isinstance(c["model_ir"], dict) and isinstance(c["code"], str)
        assert "def solve(inputs)" in c["code"]
    session, _ = run_competition(session, tmp_workdir(session), candidates=CANDIDATES)
    for xid in ("EXEC001", "EXEC002"):
        xd = session.registry.get(xid).data or {}
        assert (xd.get("provenance") or {}).get("adapter") == "local_python"


def test_full_loop_disk_artifacts(tmp_path):
    """验收⑥⑦：全链产物落盘 + 对比表字段可从磁盘复原。"""
    project = tmp_path / "project"
    s = make_session(project)
    wd = project / "work"
    wd.mkdir(parents=True, exist_ok=True)
    s, _ = run_competition(s, wd, candidates=CANDIDATES)
    s.checkpoint()

    registry = json.loads(
        (project / "state" / "registry.json").read_text(encoding="utf-8"))
    artifacts = registry["artifacts"]
    for aid in ("P001", "M001", "MIR001", "MIR002", "CODE001",
                "EXEC001", "EXEC002", "VR001", "VR002"):
        assert aid in artifacts, aid
    guided = artifacts["MIR001"]["data"]
    unguided = artifacts["MIR002"]["data"]
    assert len(guided["validations"]) > len(unguided["validations"])
    assert {v["source_card"] for v in guided["validations"]
               if "source_card" in v} == set(GUIDE_CARD_IDS)
