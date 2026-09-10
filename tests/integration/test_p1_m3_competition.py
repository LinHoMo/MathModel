# -*- coding: utf-8 -*-
"""P1-M3 Candidate Competition e2e — 7 条验收逐条断言。

场景：2024_A Q1 双候选（M1 故意错误：ell_body=1.925；M2 修正：1.65），
每候选独立 MIR-i→CODE-i→EXEC-i→R-i→VR-i 链，evidence-based 选型选 M2。

验收映射：
  ① ≥2 候选真 subprocess 执行 + 数值验证（独立 EXEC-i/VR-i，status 来自真实退出码）
  ② decision 含 alternatives/criteria/evidence_ids/chosen，criteria 机械可算，
     chosen 与证据排序一致（VR 约束违反最小者当选）
  ③ decision -selects-> model 边存在，reasoning/evidence_ids 可溯源到真实 VR
  ④ 新增测试 + 全量 pytest 不回归（≥890 passed）、catalog OK、validate 57/0
  ⑤ LLM-free：候选 MODEL_IR/Code 外部注入（fixture），core 只登记/校验/执行/验证/选型
  ⑥ 禁越界：不新增 Agent/Skill/知识库/论文模块/无关 schema（见 commit 清单）
  ⑦ 按序 commit（feat(p1-m3):）+ P1_M3_REPORT.md（不 push）

运行: py -3.12 -m pytest tests/integration/test_p1_m3_competition.py -q
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

from m3_driver import (LOOP_NODES, artifact_ids, decisions_of,  # noqa: E402
                       inject_candidates, make_session, relation_pairs,
                       replay_report, step_all)
from m3_fixtures import CANDIDATES, EXPECTED_CHOSEN_MODEL_ID  # noqa: E402


@pytest.fixture()
def session(tmp_path):
    s = make_session(tmp_path / "project")
    inject_candidates(s, workdir=str(tmp_path / "work"))
    return s


def run_all(session):
    return step_all(session)


def test_01_two_candidates_independent_chains(session):
    """验收①：≥2 候选全部真 subprocess 执行 + 数值验证，链独立互不覆盖。"""
    results = run_all(session)
    for nid in LOOP_NODES:
        assert results[nid].status == "pass", f"{nid} -> {results[nid].status}"

    mirs = artifact_ids(session, "model_ir")
    codes = artifact_ids(session, "code")
    execs = artifact_ids(session, "execution_result")
    results_art = artifact_ids(session, "result")
    vrs = artifact_ids(session, "verification_result")

    assert len(mirs) == 2 and len(codes) == 2 and len(execs) == 2 \
        and len(results_art) == 2 and len(vrs) == 2, \
        (f"候选链应各 2 条：MIR={mirs} CODE={codes} EXEC={execs} "
         f"R={results_art} VR={vrs}")

    # 链独立：MIR001→CODE001→EXEC001→VR001 / MIR002→CODE002→EXEC002→VR002
    pairs = relation_pairs(session)
    chain1 = {("MIR001", "implemented_by", "CODE001"),
              ("CODE001", "executed_by", "EXEC001"),
              ("EXEC001", "verified_by", "VR001")}
    chain2 = {("MIR002", "implemented_by", "CODE002"),
              ("CODE002", "executed_by", "EXEC002"),
              ("EXEC002", "verified_by", "VR002")}
    assert chain1 <= pairs, chain1 - pairs
    assert chain2 <= pairs, chain2 - pairs

    # status 来自真实退出码（禁硬编码）：returncode=0 → success
    for xid in execs:
        xd = session.registry.get(xid).data or {}
        assert xd.get("returncode") == 0, f"{xid} returncode != 0"
        assert xd.get("status") == "success", f"{xid} status 应来自真实退出码"
        assert (xd.get("outputs") or {}), f"{xid} 必须有真实数值输出"


def test_02_decision_fields_and_ranking(session):
    """验收②：decision 字段齐全，criteria 机械可算，chosen 与证据排序一致。"""
    run_all(session)
    decisions = decisions_of(session)
    assert len(decisions) == 1, decisions
    d = decisions[0]["data"]

    alt_ids = {a["model_ir"] for a in d["alternatives"]}
    assert alt_ids >= {"MIR001", "MIR002"}, alt_ids
    assert d["criteria"] == ["mathematical_valid", "constraint_violation_max",
                             "execution_valid", "variable_domain_violation",
                             "empirical_valid"]
    assert set(d["evidence_ids"]) == {"VR001", "VR002"}
    assert d["chosen"] == "MIR002", d["chosen"]
    assert d["confidence"] > 0

    # 机械排序：mathematical_valid 优先 + constraint_violation_max 升序
    assert d["ranked"] == ["MIR002", "MIR001"], d["ranked"]
    cv = {a["model_ir"]: a["constraint_violation_max"]
          for a in d["alternatives"]}
    assert cv["MIR001"] == 0.275 and cv["MIR002"] == 0.0
    # chosen 与证据排序一致：约束违反最小者当选
    assert d["chosen"] == min(cv, key=cv.get)


def test_03_selects_edge_and_traceability(session):
    """验收③：decision -selects-> model 边 + reasoning/evidence_ids 溯源。"""
    run_all(session)
    pairs = relation_pairs(session)
    decisions = decisions_of(session)
    d = decisions[0]
    ddata = d["data"]

    selects = [p for p in pairs if p[1] == "selects"]
    assert selects, "必须存在 decision -selects-> model 边"
    assert selects[0][0] == d["artifact_id"] and selects[0][2] == "M001"

    # evidence_ids 指向真实 artifact
    for vr_id in ddata["evidence_ids"]:
        assert session.registry.get(vr_id) is not None, f"{vr_id} 不存在"

    # reasoning 引用真实 VR id + 数值
    rsn = ddata["reasoning"]
    assert "VR002" in rsn and "VR001" in rsn
    assert "0.0" in rsn and "0.275" in rsn
    assert "chosen=MIR002" in rsn


def test_04_bad_candidate_real_fail(session):
    """验收①补充：坏候选 VR 真实 FAIL（数值判，非伪造）。"""
    run_all(session)
    vr1 = session.registry.get("VR001")
    v1 = vr1.data or {}
    assert v1["status"] == "failed"
    assert v1["mathematical_valid"] is False
    assert v1["execution_valid"] is True      # 执行本身成功（returncode=0）
    assert v1["constraint_violation_max"] == pytest.approx(0.275, abs=1e-6)
    assert v1["variable_domain_violation"] == 0   # 域合规，FAIL 纯来自约束违反
    # 实测数值（EXEC001 体板间距 1.925 vs 声明 1.65）
    x1 = session.registry.get("EXEC001").data or {}
    spacing = (x1["outputs"]["pair_distances"]["0"] or [None, None])[1]
    assert spacing == pytest.approx(1.925, abs=1e-6)


def test_05_unselected_when_no_evidence(session):
    """验收④（P0-4 修订）：无执行/验证证据时如实不选型（消除 recs[0]）。

    零执行/零验证 ≠ PASS：无 validation_spec → 无 VR 证据 →
    model_execution/model_validation/model_selection_decision 级联
    blocked（BLOCKED 依赖传播：上游阻塞时下游如实传播，不执行 executor
    不假装完成），且不产生任何 decision artifact。
    """
    # 不注入 validation_specs → 无 VR 证据
    shared = session.executor_impl.shared
    shared.pop("validation_specs", None)
    results = {}
    for nid in LOOP_NODES:
        results[nid] = session.engine.step(nid)
    # 候选带代码 → 执行真实发生（pass）；无 validation_spec → 零验证
    assert results["model_execution"].status == "pass"         # 有执行
    assert results["model_validation"].status == "blocked"     # 零验证 ≠ PASS
    assert results["model_selection_decision"].status == "blocked"  # 级联传播

    decisions = decisions_of(session)
    assert len(decisions) == 0, "无证据不得制造任何 decision artifact"
    # 容器 model 的 selection_status 保持 pending（未假装选型）
    m = session.registry.get("M001")
    assert (m.data or {}).get("selection_status") == "pending_evidence"



def test_full_loop_disk_recovery(tmp_path):
    """验收⑥⑦：全链产物落盘后可从磁盘复原（registry/graph/replay）。"""
    project = tmp_path / "project"
    s = make_session(project)
    inject_candidates(s, workdir=str(tmp_path / "work"))
    results = run_all(s)
    for nid in LOOP_NODES:
        assert results[nid].status == "pass"
    s.checkpoint()

    # 磁盘复原
    registry = json.loads(
        (project / "state" / "registry.json").read_text(encoding="utf-8"))
    graph = json.loads(
        (project / "state" / "evidence_graph.json").read_text(encoding="utf-8"))
    artifacts = registry["artifacts"]
    for aid in ("P001", "M001", "MIR001", "MIR002", "CODE001", "CODE002",
                "EXEC001", "EXEC002", "R001", "R002", "VR001", "VR002"):
        assert aid in artifacts, aid
    pairs = {(r["from"], r["relation"], r["to"]) for r in graph["relations"]}
    assert ("D002", "selects", "M001") in pairs

    # replay 可从磁盘重放 RUN1/RUN2 且输出一致
    for xid in ("EXEC001", "EXEC002"):
        rep = replay_report(str(project), xid)
        assert rep.get("ok") is True, rep
        assert rep.get("outputs_match") is True, rep
        assert rep.get("deviation") == [], rep

    # VR 数值从磁盘可见
    vr2 = artifacts["VR002"]["data"]
    assert vr2["status"] == "passed" and vr2["mathematical_valid"] is True
    vr1 = artifacts["VR001"]["data"]
    assert vr1["status"] == "failed" and vr1["mathematical_valid"] is False


def test_llm_free_boundary(session):
    """验收⑤：候选 MODEL_IR/Code 全部来自外部注入（fixture），core 无 LLM。"""
    # 注入发生在任何节点执行之前（fixture 已注入）
    shared = session.executor_impl.shared
    cands = shared.get("external_candidates", {}).get("Q001", [])
    assert len(cands) == 2
    for c in cands:
        assert isinstance(c["model_ir"], dict) and isinstance(c["code"], str)
        assert "def solve(inputs)" in c["code"]
    # 执行链由真实 subprocess 完成：EXEC provenance 指向 local_python
    run_all(session)
    x = session.registry.get("EXEC001").data or {}
    assert (x.get("provenance") or {}).get("adapter") == "local_python"
