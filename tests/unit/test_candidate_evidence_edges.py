"""audit FIX-2.4：Evidence Graph evaluated_by / selected_from 边。

- RELATION_TYPES 含 evaluated_by（candidate → VR/EXEC）与 selected_from
  （selected_model → candidate）
- 均属弱边（不传播失效）
- 候选竞技场选型后 graph 含完整边

运行: python -m pytest tests/unit/test_candidate_evidence_edges.py -q
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import pytest

from modeling_harness.runtime.graph.evidence_graph import (
    RELATION_TYPES,
    WEAK_RELATIONS,
    EvidenceGraph,
)


@pytest.fixture
def graph(tmp_path):
    from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
    reg = ArtifactRegistry(tmp_path / "registry.json",
                           allow_legacy_unverified=True)
    reg.create("question", artifact_id="Q001", title="Q001", activate=True)
    reg.create("model", title="M1", question="Q001", activate=True)
    reg.create("model", title="M2", question="Q001", activate=True)
    reg.create("execution_result", title="VR1", question="Q001", activate=True,
               data={"status": "success", "code_hash": "a" * 16,
                     "outputs": {"x": 1},
                     "legacy_unverified": True})
    g = EvidenceGraph(reg, tmp_path / "eg.json")
    return g, reg


def test_relation_types_declared():
    assert "evaluated_by" in RELATION_TYPES
    assert "selected_from" in RELATION_TYPES


def test_weak_edges_no_invalidation_propagation(graph):
    g, reg = graph
    models = reg.list_by_type("model")
    m1, m2 = models[0].artifact_id, models[1].artifact_id
    vr = reg.list_by_type("execution_result")[0].artifact_id
    # 弱边：上游失效不沿 evaluated_by/selected_from 传播
    assert "evaluated_by" in WEAK_RELATIONS
    assert "selected_from" in WEAK_RELATIONS
    g.add_relation(m1, "evaluated_by", vr)
    g.add_relation(m2, "selected_from", m1)
    g.invalidate(m1, reason="test")
    assert vr not in g.downstream(m1)
    g.invalidate(m2, reason="test")
    assert m1 not in g.downstream(m2)
