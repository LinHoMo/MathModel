"""P0 Artifact Layer 测试：Stable ID / Contract / Lifecycle / Registry / Versioning。

运行: python -m pytest tests/unit/test_artifacts.py -q
零第三方依赖（与 core/tools 惯例一致）。
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.artifacts.ids import (
    IDFormatError, format_id, id_matches_type, id_type, is_valid_id, parse_id,
)
from runtime.artifacts.artifact import Artifact, ContractError
from runtime.artifacts.lifecycle import (
    LifecycleError, assert_transition, can_transition, is_terminal, next_forward,
)
from runtime.artifacts.registry import (
    ArtifactNotFound, ArtifactRegistry, RegistryError,
)


# ------------------------------------------------------------------- IDs

class TestStableIDs:
    def test_valid_ids(self):
        for aid, typ in [("P001", "problem"), ("Q012", "question"), ("M003", "model"),
                         ("DATA007", "dataset"), ("CODE021", "code"), ("E009", "experiment"),
                         ("R002", "result"), ("F001", "figure"), ("T004", "table"),
                         ("C008", "claim"), ("D001", "decision"), ("N002", "narrative"),
                         ("S004", "paper_section"), ("DELIV001", "deliverable")]:
            assert is_valid_id(aid)
            assert id_type(aid) == typ
            assert id_matches_type(aid, typ)

    def test_invalid_ids(self):
        for bad in ["", "X001", "M", "model01", "M-01", "M01a", "q001", None, "M0"]:
            assert not is_valid_id(bad), bad

    def test_parse_errors(self):
        with pytest.raises(IDFormatError):
            parse_id("bogus")

    def test_format_id_pads_to_three(self):
        assert format_id("M", 2) == "M002"
        assert format_id("DATA", 3) == "DATA003"
        assert format_id("DELIV", 1) == "DELIV001"

    def test_format_id_no_pad_over_999(self):
        assert format_id("M", 1000) == "M1000"

    def test_type_prefix_mismatch_rejected(self):
        assert not id_matches_type("M001", "question")


# -------------------------------------------------------------- Lifecycle

class TestLifecycle:
    def test_forward_path(self):
        assert can_transition("draft", "active")
        assert can_transition("active", "validated")
        assert can_transition("validated", "published")

    def test_next_forward(self):
        assert next_forward("draft") == "active"
        assert next_forward("published") is None
        assert next_forward("invalidated") is None

    def test_blocked_recovery(self):
        assert can_transition("active", "blocked")
        assert can_transition("validated", "blocked")
        assert can_transition("blocked", "active")

    def test_any_to_terminal(self):
        for s in ("draft", "active", "validated", "published", "blocked"):
            for t in ("invalidated", "superseded", "deprecated"):
                assert can_transition(s, t), (s, t)

    def test_terminal_is_absorbing(self):
        for t in ("invalidated", "superseded", "deprecated"):
            assert is_terminal(t)
            with pytest.raises(LifecycleError):
                assert_transition(t, "active")
            with pytest.raises(LifecycleError):
                assert_transition(t, "invalidated")

    def test_illegal_jumps_rejected(self):
        for frm, to in [("draft", "validated"), ("draft", "published"),
                        ("active", "published"), ("blocked", "validated"),
                        ("published", "active"), ("deprecated", "draft")]:
            assert not can_transition(frm, to), (frm, to)
            with pytest.raises(LifecycleError):
                assert_transition(frm, to)

    def test_unknown_states(self):
        with pytest.raises(LifecycleError):
            assert_transition("step_01", "active")   # V2 的 29-step 不是合法状态
        assert not can_transition("active", "step_01")

    def test_idempotent_replay(self):
        assert can_transition("active", "active")   # 重放安全
        assert can_transition("draft", "draft")


# ---------------------------------------------------------------- Contract

class TestArtifactContract:
    def make(self, **kw):
        base = dict(artifact_id="M001", type="model", title="TOPSIS 模型",
                    payload=["work/model_draft.md"], created_by="modeler/model-builder")
        base.update(kw)
        return Artifact(**base)

    def test_valid_contract(self):
        assert self.make().validate() == []

    def test_id_type_mismatch(self):
        assert any("前缀与类型" in p for p in self.make(artifact_id="Q001").validate())

    def test_bad_status_rejected(self):
        assert any("status 非法" in p for p in self.make(status="step_07").validate())

    def test_self_dependency_rejected(self):
        assert any("自身" in p for p in self.make(depends_on=["M001"]).validate())

    def test_bad_question_ref(self):
        assert any("question 引用非法" in p
                   for p in self.make(question="bogus").validate())
        assert any("必须是 Q 类型" in p
                   for p in self.make(question="M001").validate())

    def test_roundtrip_serialization(self):
        art = self.make(depends_on=["Q001", "A001"])
        d = art.to_dict()
        assert d["schema_version"] == "3.1"
        art2 = Artifact.from_dict(json.loads(art.to_json()))
        assert art2.artifact_id == "M001"
        assert art2.validate() == []

    def test_transition_records_history(self):
        art = self.make()
        art.transition("active", by="t", reason="r")
        art.transition("validated", by="t", reason="r")
        assert [h["to"] for h in art.lifecycle_history] == ["active", "validated"]
        assert art.status == "validated"

    def test_mark_validated_stamps_evidence(self):
        art = self.make().transition("active")
        art.mark_validated("model-critic", report={"score": "WEAK→PASS"})
        assert art.validation["passed"] is True
        assert "model-critic" in art.validation["validators"]

    def test_invalidation_levels(self):
        art = self.make().transition("active")
        art.mark_invalidation("requires_revalidation", "上游数据失效", invalidated_by="DATA001")
        assert art.invalidation["status"] == "requires_revalidation"
        assert art.status == "active"   # 弱失效不改变生命周期
        art.mark_invalidation("invalidated", "直接依赖失效", invalidated_by="DATA001")
        assert art.status == "invalidated"
        with pytest.raises(LifecycleError):
            art.clear_invalidation()   # 终态不可清


# ---------------------------------------------------------------- Registry

@pytest.fixture()
def reg(tmp_path):
    return ArtifactRegistry(tmp_path / "state" / "registry.json")


class TestRegistry:
    def test_create_assigns_sequential_ids(self, reg):
        m1 = reg.create("model", title="模型一")
        m2 = reg.create("model", title="模型二")
        assert (m1.artifact_id, m2.artifact_id) == ("M001", "M002")

    def test_create_with_activate(self, reg):
        a = reg.create("question", title="Q1", activate=True)
        assert a.status == "active"

    def test_id_never_reused(self, reg):
        q = reg.create("question", title="Q")
        del reg.artifacts[q.artifact_id]     # 模拟人为删除
        q2 = reg.create("question", title="Q again")
        assert q2.artifact_id == "Q002"      # 计数器不回退

    def test_dangling_ref_rejected(self, reg):
        with pytest.raises(RegistryError):
            reg.create("model", depends_on=["M999"])   # 引用不存在

    def test_question_ref_must_exist(self, reg):
        reg.create("question", title="Q1")
        m = reg.create("model", question="Q001")
        assert m.question == "Q001"
        with pytest.raises(RegistryError):
            reg.create("model", question="Q099")

    def test_persistence_roundtrip(self, tmp_path):
        path = tmp_path / "state" / "registry.json"
        reg = ArtifactRegistry(path)
        reg.create("question", title="Q1", activate=True)
        m = reg.create("model", title="M", question="Q001", activate=True)
        reg.mark_validated(m.artifact_id, "model-critic")
        reg.save()
        reg2 = ArtifactRegistry(path)
        assert len(reg2) == 2
        assert reg2.get("M001").status == "validated"
        assert reg2.counters["model"] == 1

    def test_versioning_snapshots_and_reset(self, reg):
        reg.create("question", title="Q1", activate=True)
        m = reg.create("model", title="v1 内容", payload=["work/m_v1.md"], activate=True)
        reg.mark_validated(m.artifact_id, "model-critic")
        # 内容更新 → v2，状态重置 draft，v1 快照进 history
        m2 = reg.update(m.artifact_id, payload=["work/m_v2.md"], title="v2 内容")
        assert m2.version == 2
        assert m2.status == "draft"
        assert m2.validation == {}
        assert reg.versions("M001") == [1, 2]
        v1 = reg.get("M001", version=1)
        assert v1.status == "validated"
        assert v1.payload == ["work/m_v1.md"]
        # 元数据更新保留状态
        m3 = reg.update("M001", tags=["baseline"])
        assert m3.version == 3
        assert m3.status == "draft"      # v2 本来就是 draft，保持

    def test_update_terminal_rejected(self, reg):
        m = reg.create("model", title="x")
        reg.invalidate(m.artifact_id, "数据造假")
        with pytest.raises(Exception):
            reg.update(m.artifact_id, title="y")

    def test_supersede_with_replacement(self, reg):
        old = reg.create("model", title="旧", activate=True)
        new = reg.create("model", title="新", activate=True)
        reg.supersede(old.artifact_id, "被更好模型替代", replacement=new.artifact_id)
        assert reg.get(old.artifact_id).status == "superseded"
        assert reg.get(old.artifact_id).invalidation["invalidated_by"] == new.artifact_id

    def test_blocked_flow(self, reg):
        m = reg.create("model", title="x", activate=True)
        reg.block(m.artifact_id, reason="等待数据")
        assert m.status == "blocked"
        reg.transition(m.artifact_id, "active", reason="数据恢复")
        assert m.status == "active"

    def test_integrity_check_clean(self, reg):
        reg.create("question", title="Q1", activate=True)
        reg.create("model", title="m", question="Q001", depends_on=["Q001"])
        assert reg.integrity_check() == []

    def test_integrity_check_detects_dangling(self, reg):
        reg.create("question", title="Q1", activate=True)
        m = reg.create("model", title="m", depends_on=["Q001"])
        reg.artifacts["Q001"].status = "invalidated"
        # 人为制造悬空引用
        m.depends_on = ["Q099"]
        problems = reg.integrity_check()
        assert any("悬空引用" in p for p in problems)

    def test_relations_view_sync(self, reg):
        q = reg.create("question", title="Q1", activate=True)
        m = reg.create("model", title="m", question="Q001", activate=True)
        reg.set_relations_view(m.artifact_id, [{"type": "solved_by", "to": "Q001"}])
        assert reg.get(m.artifact_id).relations == [{"type": "solved_by", "to": "Q001"}]

    def test_summary(self, reg):
        reg.create("question", title="Q1", activate=True)
        reg.create("model", title="m", question="Q001")
        s = reg.summary()
        assert s["total"] == 2
        assert s["by_type"]["model"] == 1
        assert s["by_status"]["active"] == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
