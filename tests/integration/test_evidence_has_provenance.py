# -*- coding: utf-8 -*-
"""audit FIX-4.1（P0-01/P0-07）：Evidence 必须携带边级 execution provenance。

supports 边必须携带 exec_ref（指向真实 EXEC artifact）；无 EXEC 引用的
evidence 不被 gate 认可。旧数据形态（仅 result.data.execution_ref）降级 weak。

运行: python -m pytest tests/integration/test_evidence_has_provenance.py -q
"""

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
for p in (_REPO / "src", _REPO / "research" / "P15" / "vs001_run"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from vs001_driver import (LOOP_NODES, artifact_ids, make_session,  # noqa: E402
                          relation_pairs, run_m1, run_m2, step_all)
from modeling_harness.validators.evidence.evidence_gate import evaluate as gate_evaluate  # noqa: E402


@pytest.fixture()
def session(tmp_path):
    return make_session(tmp_path / "proj")


def _run_full_loop(session, workdir):
    """M1（验证 FAIL）→ M2（验证 PASS）→ 拓扑补齐至 evidence_build/evidence_gate。

    只有 M2 存活后下游节点才不被 model_validation 阻塞，evidence 链才能产生。
    """
    run_m1(session, workdir)
    mir1 = artifact_ids(session, "model_ir")[0]
    run_m2(session, mir1, workdir)
    session.engine.run()
    return session


def test_supports_edge_carries_exec_ref(session, tmp_path):
    """真实闭环：supports 边必须携带 exec_ref，指向 success 的真实 EXEC。"""
    _run_full_loop(session, tmp_path / "exec")
    execs = artifact_ids(session, "execution_result")
    assert execs, "必须有真实 EXEC"
    ex = session.registry.get(execs[0])
    assert ex.data["status"] == "success"
    claims = artifact_ids(session, "claim")
    assert claims
    supp = [e for e in relation_pairs(session)
            if e[1] == "supports" and e[2] in claims]
    assert supp, "claim 必须有 supports 边"
    # 边级 exec_ref 必须存在且指向成功 EXEC
    edges = session.graph.relations
    for e in edges:
        if e["relation"] == "supports" and e["to"] in claims:
            ref = e.get("exec_ref")
            assert ref, f"supports 边必须携带 exec_ref: {e}"
            x = session.registry.get(ref)
            assert (x.data or {}).get("status") == "success", \
                f"exec_ref {ref} 必须指向 success EXEC"
    # gate 认可该证据链
    rep = gate_evaluate(session.registry, session.graph)
    assert not any(f.code == "E9" and f.severity == "fail"
                   for f in rep.findings), rep.summary()


def test_gate_weak_when_edge_missing_but_data_has(tmp_path):
    """旧数据形态：supports 边无 exec_ref，仅 result.data.execution_ref →
    E9 降级 weak（不 FAIL，但要求补齐边级 provenance）。"""
    from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
    from modeling_harness.runtime.graph.evidence_graph import EvidenceGraph
    reg = ArtifactRegistry(tmp_path / "registry.json")
    reg.project = "t"
    reg.create("question", title="Q", activate=True)
    reg.create("execution_result", title="exec", question="Q001",
               activate=True,
               data={"status": "success", "outputs": {"y": 1.0},
                     "code_hash": "b" * 64, "returncode": 0,
                     "legacy_unverified": True})
    reg.create("result", title="result", question="Q001", activate=True,
               data={"execution_ref": "EXEC001"})
    reg.create("claim", title="claim", question="Q001", activate=True)
    g = EvidenceGraph(reg, path=tmp_path / "g.json")
    g.add_relation("EXEC001", "produces", "R001")
    g.add_relation("R001", "supports", "C001")   # 边无 exec_ref
    rep = gate_evaluate(reg, g)
    assert rep.verdict == "WEAK", rep.summary()
    assert any(f.code == "E9" and f.severity == "weak"
               for f in rep.findings), rep.summary()


def test_gate_fails_without_any_exec(tmp_path):
    """无任何执行引用：supports 边无 exec_ref 且 result.data 也无 → E9 FAIL。"""
    from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
    from modeling_harness.runtime.graph.evidence_graph import EvidenceGraph
    reg = ArtifactRegistry(tmp_path / "registry.json")
    reg.project = "t"
    reg.create("question", title="Q", activate=True)
    reg.create("result", title="result", question="Q001", activate=True)
    reg.create("claim", title="claim", question="Q001", activate=True)
    g = EvidenceGraph(reg, path=tmp_path / "g.json")
    g.add_relation("R001", "supports", "C001")
    rep = gate_evaluate(reg, g)
    assert any(f.code == "E9" and f.severity == "fail"
               for f in rep.findings), rep.summary()
