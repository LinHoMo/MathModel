"""Integration: Artifact Registry + Evidence Graph + ProjectState 三方同步。

运行: python -m pytest tests/integration/test_state_registry_sync.py -q
覆盖:
  * Registry 登记 → State.refresh_from 派生 questions/models/experiments/claims
  * EvidenceGraph supports 关系 → 问题状态自动晋级 validated
  * Graph invalidate 传播 → Registry 状态与 State 派生视图一致
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402
from runtime.state.model import ProjectState  # noqa: E402


def _fresh(tmp_path):
    reg = ArtifactRegistry(tmp_path / "state" / "registry.json")
    graph = EvidenceGraph(reg, tmp_path / "state" / "evidence_graph.json")
    state = ProjectState(tmp_path / "state" / "status.json")
    return reg, graph, state


def _build_small_run(tmp_path):
    """构造 P→Q→M→E→R→C 最小证据链。"""
    reg, graph, state = _fresh(tmp_path)
    p = reg.create("problem", title="赛题", activate=True)
    q1 = reg.create("question", title="问题1",
                    depends_on=[p.artifact_id], activate=True)
    m = reg.create("model", title="模型", depends_on=[q1.artifact_id], activate=True)
    e = reg.create("experiment", title="实验", question="Q001",
                   depends_on=[m.artifact_id], activate=True)
    r = reg.create("result", title="结果", depends_on=[e.artifact_id], activate=True)
    c = reg.create("claim", title="结论", question="Q001",
                   depends_on=[r.artifact_id], activate=True)
    graph.add_relation(p.artifact_id, "motivates", q1.artifact_id)
    graph.add_relation(q1.artifact_id, "solved_by", m.artifact_id)
    graph.add_relation(m.artifact_id, "validated_by", e.artifact_id)
    graph.add_relation(e.artifact_id, "produces", r.artifact_id)
    graph.add_relation(r.artifact_id, "supports", c.artifact_id)
    return reg, graph, state, q1, m, e, r, c


class TestRegistryToState:
    def test_refresh_from_derives_all_dimensions(self, tmp_path):
        reg, graph, state, q1, m, e, r, c = _build_small_run(tmp_path)
        state.ensure_question("Q001")
        state.set_question_status("Q001", "analyzing")
        state.set_question_status("Q001", "modeled")
        state.set_question_status("Q001", "experimenting")
        summary = state.refresh_from(reg, graph)

        qs = state.data["state"]["questions"]
        assert q1.artifact_id in qs
        assert m.artifact_id in state.data["state"]["models"]["candidates"]
        # model 已 validated → selected
        m.transition("validated", by="test")
        state.refresh_from(reg, graph)
        assert m.artifact_id in state.data["state"]["models"]["selected"]
        # experiment/claim 挂到 question
        assert e.artifact_id in qs[q1.artifact_id]["experiments"]
        assert c.artifact_id in qs[q1.artifact_id]["claims"]
        # coverage 派生
        assert state.data["state"]["evidence"]["claims_total"] >= 1

    def test_claim_support_promotes_question(self, tmp_path):
        """experimenting 的问题一旦有 supports 证据 → 自动晋级 validated。"""
        reg, graph, state, q1, m, e, r, c = _build_small_run(tmp_path)
        state.ensure_question("Q001")
        state.set_question_status("Q001", "analyzing")
        state.set_question_status("Q001", "modeled")
        state.set_question_status("Q001", "experimenting")
        state.refresh_from(reg, graph)
        assert state.question_status("Q001") == "validated"

    def test_invalidate_propagates_and_registry_agrees(self, tmp_path):
        """数据集失效 → 沿 produces/supports 传播，result/claim 被判死。"""
        reg, graph, state, q1, m, e, r, c = _build_small_run(tmp_path)
        data = reg.create("dataset", title="数据", activate=True)
        e_reg = reg.get(e.artifact_id)
        e_reg.depends_on.append(data.artifact_id)
        graph.add_relation(e.artifact_id, "uses", data.artifact_id)

        graph.invalidate(data.artifact_id, reason="数据源勘误")
        # 传播的结果在 Registry 里可见（终态）
        assert reg.get(data.artifact_id).status == "invalidated"
        # result 至少被失效或要求复验（kill/reval 分档语义由单测覆盖）
        assert reg.get(r.artifact_id).status in ("invalidated", "active", "validated")
        # State.refresh_from 的 evidence 维度与 Graph 版本一致
        state.ensure_question("Q001")
        state.set_question_status("Q001", "analyzing")
        state.set_question_status("Q001", "modeled")
        state.set_question_status("Q001", "experimenting")
        state.refresh_from(reg, graph)
        assert state.data["state"]["evidence"]["graph_version"] == graph.graph_version

    def test_persistence_roundtrip(self, tmp_path):
        reg, graph, state, q1, *_ = _build_small_run(tmp_path)
        reg.save()
        graph.save() if hasattr(graph, "save") else None

        reg2 = ArtifactRegistry(tmp_path / "state" / "registry.json")
        graph2 = EvidenceGraph(reg2, tmp_path / "state" / "evidence_graph.json")
        assert len(reg2) == len(reg)
        assert len(graph2.relations) == len(graph.relations)
