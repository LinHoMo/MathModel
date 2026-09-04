"""P1 V3 State Model 测试：状态转换 / Per-Qi / blocked / recovery / 派生视图。

运行: python -m pytest tests/unit/test_state_v3.py -q
覆盖任务书 §36 State Tests: state transition / partial state / blocked state / recovery。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.artifacts.registry import ArtifactRegistry
from runtime.graph.evidence_graph import EvidenceGraph
from runtime.state.model import (
    ProjectState, StateError, can_question_transition,
)


@pytest.fixture
def state(tmp_path):
    return ProjectState(tmp_path / "status.json")


class TestQuestionStateMachine:
    def test_forward_path(self):
        assert can_question_transition("pending", "analyzing")
        assert can_question_transition("analyzing", "modeled")
        assert can_question_transition("modeled", "experimenting")
        assert can_question_transition("experimenting", "validated")
        assert can_question_transition("validated", "complete")

    def test_failure_and_retry(self):
        assert can_question_transition("experimenting", "failed")
        assert can_question_transition("failed", "experimenting")
        assert can_question_transition("failed", "analyzing")

    def test_illegal_transition_rejected(self):
        assert not can_question_transition("pending", "complete")   # 不许跳级
        assert not can_question_transition("pending", "validated")

    def test_blocked_and_recovery(self):
        assert can_question_transition("experimenting", "blocked")
        assert can_question_transition("blocked", "experimenting")

    def test_complete_can_be_invalidated(self):
        assert can_question_transition("complete", "failed")


class TestProjectState:
    def test_ensure_question_idempotent(self, state):
        state.ensure_question("Q001")
        state.ensure_question("Q001")
        assert list(state.data["state"]["questions"]) == ["Q001"]

    def test_set_question_status(self, state):
        state.ensure_question("Q001")
        state.set_question_status("Q001", "analyzing")
        state.set_question_status("Q001", "modeled")
        assert state.question_status("Q001") == "modeled"

    def test_set_question_status_illegal(self, state):
        state.ensure_question("Q001")
        with pytest.raises(StateError):
            state.set_question_status("Q001", "complete")

    def test_failure_records_reason_and_retry(self, state):
        state.ensure_question("Q001")
        state.set_question_status("Q001", "analyzing")
        state.set_question_status("Q001", "modeled")
        state.set_question_status("Q001", "experimenting")
        state.set_question_status("Q001", "failed", failure_reason="灵敏度分析未通过")
        q = state.data["state"]["questions"]["Q001"]
        assert q["failure_reason"] == "灵敏度分析未通过"
        assert q["retry_count"] == 1
        # 恢复
        state.set_question_status("Q001", "experimenting")
        assert q["failure_reason"] is None

    def test_attach_artifacts(self, state):
        state.ensure_question("Q001")
        state.attach("Q001", "models", "M001")
        state.attach("Q001", "models", "M001")   # 幂等
        state.attach("Q001", "claims", "C001")
        q = state.data["state"]["questions"]["Q001"]
        assert q["models"] == ["M001"]
        assert q["claims"] == ["C001"]

    def test_attach_invalid_kind(self, state):
        state.ensure_question("Q001")
        with pytest.raises(StateError):
            state.attach("Q001", "papers", "S001")

    def test_dependencies_blocking(self, state):
        state.ensure_question("Q001")
        state.ensure_question("Q002", dependencies=["Q001"])
        # Q001 未完成 → Q002 被依赖阻塞
        assert state.blocked_by_dependencies("Q002") == ["Q001"]
        state.set_question_status("Q001", "analyzing")
        state.set_question_status("Q001", "modeled")
        state.set_question_status("Q001", "experimenting")
        state.set_question_status("Q001", "validated")
        assert state.blocked_by_dependencies("Q002") == []

    def test_partial_state_multiple_questions(self, state):
        """多维 partial: Q1 complete / Q2 experimenting / Q3 pending。"""
        for qid in ("Q001", "Q002", "Q003"):
            state.ensure_question(qid)
        for st in ("analyzing", "modeled", "experimenting", "validated", "complete"):
            state.set_question_status("Q001", st)
        for st in ("analyzing", "modeled", "experimenting"):
            state.set_question_status("Q002", st)
        assert state.question_status("Q001") == "complete"
        assert state.question_status("Q002") == "experimenting"
        assert state.question_status("Q003") == "pending"


class TestDimensions:
    def test_set_dimension(self, state):
        state.set_dimension("problem", "complete")
        assert state.dimension("problem")["status"] == "complete"

    def test_set_dimension_fields(self, state):
        state.set_dimension("paper", "in_progress", sections_written=3, sections_total=8)
        assert state.dimension("paper")["sections_written"] == 3

    def test_unknown_dimension(self, state):
        with pytest.raises(StateError):
            state.set_dimension("galaxy", "complete")
        with pytest.raises(StateError):
            state.dimension("galaxy")

    def test_invalid_dimension_status(self, state):
        with pytest.raises(StateError):
            state.set_dimension("problem", "almost-done")


class TestWorkflowView:
    def test_complete_block_reset(self, state):
        state.workflow_set_current(["a", "b"])
        state.workflow_complete("a")
        assert "a" not in state.data["workflow"]["current_nodes"]
        assert "a" in state.data["workflow"]["completed_nodes"]
        state.workflow_block("b", "依赖未满足")
        assert state.data["workflow"]["blocked_nodes"] == ["b"]
        state.workflow_reset(["a", "b"])
        assert state.data["workflow"]["completed_nodes"] == []
        assert state.data["workflow"]["blocked_nodes"] == []

    def test_waiting_approval(self, state):
        state.workflow_set_current(["x"])
        state.workflow_waiting("x")
        assert state.data["workflow"]["waiting_approval"] == ["x"]
        state.workflow_approve("x")
        assert state.data["workflow"]["waiting_approval"] == []

    def test_retry_recording(self, state):
        assert state.workflow_record_retry("node1") == 1
        assert state.workflow_record_retry("node1") == 2


class TestPersistence:
    def test_roundtrip(self, state, tmp_path):
        state.data["project"] = "t"
        state.ensure_question("Q001")
        state.set_question_status("Q001", "analyzing")
        state.set_dimension("problem", "complete")
        state.save()
        s2 = ProjectState(tmp_path / "status.json")
        assert s2.question_status("Q001") == "analyzing"
        assert s2.dimension("problem")["status"] == "complete"

    def test_version_incompatible(self, tmp_path):
        import json
        p = tmp_path / "status.json"
        p.write_text(json.dumps({"schema_version": 2}), encoding="utf-8")
        with pytest.raises(StateError):
            ProjectState(p)


class TestDerivation:
    def test_refresh_from_registry_and_graph(self, tmp_path):
        reg = ArtifactRegistry(tmp_path / "r.json")
        reg.project = "t"
        reg.create("question", title="Q1", activate=True)
        reg.create("model", title="m", question="Q001", activate=True)
        reg.create("experiment", title="e", question="Q001", activate=True)
        reg.create("result", title="r", question="Q001", activate=True)
        reg.create("claim", title="c", question="Q001", activate=True)
        g = EvidenceGraph(reg, path=tmp_path / "g.json")
        g.add_relation("E001", "produces", "R001")
        g.add_relation("R001", "supports", "C001")
        g.save()

        state = ProjectState(tmp_path / "status.json")
        state.data["project"] = "t"
        for st in ("analyzing", "modeled", "experimenting"):
            state.set_question_status("Q001", st)
        summary = state.refresh_from(reg, g)
        # Q001 拿到 claim 且被支撑 → 自动晋级 validated
        assert state.question_status("Q001") == "validated"
        assert summary["evidence"]["claims_supported"] == 1
        assert summary["evidence"]["claims_total"] == 1
        assert state.data["state"]["questions"]["Q001"]["experiments"] == ["E001"]

    def test_refresh_syncs_question_list(self, tmp_path):
        reg = ArtifactRegistry(tmp_path / "r.json")
        reg.project = "t"
        reg.create("question", title="Q1", activate=True)
        reg.create("question", title="Q2", activate=True)
        state = ProjectState(tmp_path / "status.json")
        state.refresh_from(reg, None)
        assert set(state.data["state"]["questions"]) == {"Q001", "Q002"}
