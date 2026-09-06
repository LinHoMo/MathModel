"""P12-2 Cross-Question Relation Contract 对抗测试。

运行: python -m pytest tests/integration/test_cross_question_relations.py -q
对照任务书 §⑤ 防污染清单 + 身份冻结（label ≠ Artifact ID）。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.state.dependencies import DependencyError  # noqa: E402
from runtime.state.relations import (  # noqa: E402
    CROSS_RELATION_TYPES, RelationError, resolve_question_id)
from runtime.writing.paragraphs import question_dependencies  # noqa: E402

TERMINAL = ("invalidated", "superseded", "deprecated")


def _session(tmp_path, questions=("Q001", "Q002"), run=True, name="proj"):
    s = RuntimeSession(tmp_path / name, list(questions))
    if run:
        s.run()
    return s


def _linked_pair(tmp_path, dep_type="evidential", name="proj"):
    """已声明 Q001→Q002 科学依赖的双问题会话。返回 (s, q1, q2 真实 ID)。"""
    s = _session(tmp_path, run=True, name=name)
    q1 = next(a.artifact_id for a in s.registry.list_by_type("question")
              if a.title == "Q001")
    q2 = next(a.artifact_id for a in s.registry.list_by_type("question")
              if a.title == "Q002")
    s.declare_dependency(q1, q2, dep_type, "测试依赖")
    return s, q1, q2


class TestIdentityFreeze:
    def test_label_is_not_artifact_id(self, tmp_path):
        """身份冻结：label ≠ Artifact ID，位置推断被拒绝。"""
        s = _session(tmp_path, questions=("Q001",), run=False)
        assert resolve_question_id(s.registry, "Q001") == "Q001"
        # 单问题会话：第二个 label 必须无法解析（不存在按位置推断的 Q002）
        with pytest.raises(RelationError):
            resolve_question_id(s.registry, "Q002")
        with pytest.raises(RelationError):
            resolve_question_id(s.registry, "Q-not-created")

    def test_reordered_labels_resolve_by_identity(self, tmp_path):
        """questions 列表任意命名：解析走 Registry identity 而非位置。"""
        s = _session(tmp_path, questions=("QX", "QY"), run=False, name="p2")
        assert resolve_question_id(s.registry, "QX").startswith("Q0")


class TestCreationGates:
    def test_no_dependency_refs_rejected(self, tmp_path):
        """跨问题 compares 无 dependency_refs → invalid。"""
        s, q1, q2 = _linked_pair(tmp_path)
        r1 = s.registry.list_by_type("result")[0]
        with pytest.raises(RelationError, match="dependency_refs"):
            s.declare_cross_relation(r1.artifact_id, q2, "compares", [])

    def test_wrong_dependency_type_rejected(self, tmp_path):
        """compares 不接受 execution 依赖（D3 延伸）。"""
        s, q1, q2 = _linked_pair(tmp_path, dep_type="execution")
        r1 = s.registry.list_by_type("result")[0]
        with pytest.raises(RelationError, match="不接受"):
            s.declare_cross_relation(
                r1.artifact_id, q2, "compares",
                [{"source_question": q1, "target_question": q2,
                  "dependency_type": "execution"}])

    def test_dependency_pointing_wrong_questions_rejected(self, tmp_path):
        """dependency 指向错误问题 → FAIL。"""
        s, q1, q2 = _linked_pair(tmp_path)
        s.registry.create("question", title="Q3-outside", activate=True)
        q3 = next(a.artifact_id for a in s.registry.list_by_type("question")
                  if a.title == "Q3-outside")
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == q1)
        with pytest.raises(RelationError, match="指向错误"):
            s.declare_cross_relation(
                r1.artifact_id, q2, "extends",
                [{"source_question": q3, "target_question": q2,
                  "dependency_type": "evidential"}])

    def test_forged_dependency_ref_rejected(self, tmp_path):
        """CQ-01 Dependency Forgery：回指不存在的 P12-1 记录 → 拒绝。"""
        s, q1, q2 = _linked_pair(tmp_path)
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == q1)
        # 真实记录匹配 → extends 合法
        rec = s.declare_cross_relation(
            r1.artifact_id, q2, "extends",
            [{"source_question": q1, "target_question": q2,
              "dependency_type": "evidential"}])
        assert rec["status"] == "active"
        # 伪造：类型组合不在 records 中 → 拒绝
        with pytest.raises(RelationError, match="不存在"):
            s.declare_cross_relation(
                r1.artifact_id, q2, "derived_from",
                [{"source_question": q1, "target_question": q2,
                  "dependency_type": "comparative"}])

    def test_same_question_relation_rejected_here(self, tmp_path):
        """同问题关系不走 Cross-Question 契约（保持既有语义）。"""
        s = _session(tmp_path, questions=("Q001",), run=True)
        q1 = s.registry.list_by_type("question")[0].artifact_id
        r1 = s.registry.list_by_type("result")[0]
        with pytest.raises(RelationError, match="同问题"):
            s.declare_cross_relation(r1.artifact_id, q1, "derived_from",
                                     [{"source_question": q1,
                                       "target_question": q1,
                                       "dependency_type": "evidential"}])


class TestLegalRelations:
    def test_extends_with_evidential_dependency(self, tmp_path):
        s, q1, q2 = _linked_pair(tmp_path)
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == q1)
        rec = s.declare_cross_relation(
            r1.artifact_id, q2, "extends",
            [{"source_question": q1, "target_question": q2,
              "dependency_type": "evidential"}], created_by="t")
        assert rec["status"] == "active"
        assert rec["source_question"] == q1
        assert rec["target_question"] == q2
        # 持久化
        s2 = RuntimeSession(s.project_dir, ["Q001", "Q002"])
        recs = s2.cross_relations()
        assert len(recs) == 1 and recs[0]["relation_id"] == rec["relation_id"]

    def test_compares_with_comparative_dependency(self, tmp_path):
        s, q1, q2 = _linked_pair(tmp_path, dep_type="comparative")
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == q1)
        rec = s.declare_cross_relation(
            r1.artifact_id, q2, "compares",
            [{"source_question": q1, "target_question": q2,
              "dependency_type": "comparative"}])
        assert rec["relation_type"] == "compares"

    def test_relation_types_frozen(self):
        assert set(CROSS_RELATION_TYPES) == {"compares", "extends",
                                             "derived_from"}


class TestInvalidationSemantics:
    def test_upstream_death_marks_revalidation_not_invalidation(self, tmp_path):
        """④：上游失效 → 关系 requires_revalidation（reval ≠ invalidation）。"""
        s, q1, q2 = _linked_pair(tmp_path)
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == q1)
        rec = s.declare_cross_relation(
            r1.artifact_id, q2, "extends",
            [{"source_question": q1, "target_question": q2,
              "dependency_type": "evidential"}])
        r_art = s.registry.get(r1.artifact_id)
        s.invalidate(r1.artifact_id, reason="勘误")
        rels = s.cross_relations()
        assert rels[0]["status"] == "requires_revalidation"
        # reval ≠ invalidation：关系没有终态，且可重派生
        assert rels[0]["status"] not in TERMINAL

    def test_execution_dependency_no_scientific_relation(self, tmp_path):
        """execution 依赖不能建立科学关系 → 无失效面（D3 延伸）。"""
        s, q1, q2 = _linked_pair(tmp_path, dep_type="execution")
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == q1)
        with pytest.raises(RelationError):
            s.declare_cross_relation(
                r1.artifact_id, q2, "extends",
                [{"source_question": q1, "target_question": q2,
                  "dependency_type": "execution"}])
        assert s.cross_relations() == []

    def test_superseded_relation_never_reactivates(self, tmp_path):
        """reval 后的关系不得静默回到 active——只能重派生产生新记录。"""
        s, q1, q2 = _linked_pair(tmp_path)
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == q1)
        s.declare_cross_relation(
            r1.artifact_id, q2, "extends",
            [{"source_question": q1, "target_question": q2,
              "dependency_type": "evidential"}])
        s.invalidate(r1.artifact_id, reason="勘误")
        assert s.cross_relations()[0]["status"] == "requires_revalidation"
        # 没有"复活"API：状态只能由新关系记录取代
        s.run()
        assert s.cross_relations()[0]["status"] == "requires_revalidation"


class TestAuditRetention:
    def test_rerun_keeps_old_relations_new_point_to_new_lineage(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        q1 = next(a.artifact_id for a in s.registry.list_by_type("question")
                  if a.title == "Q001")
        q2 = s.registry.create("question", title="Q2b", activate=True)
        s.declare_dependency(q1, q2.artifact_id, "evidential", "扩展")
        old_result = next(a for a in s.registry.list_by_type("result")
                          if a.status == "active")
        rec = s.declare_cross_relation(
            old_result.artifact_id, q2.artifact_id, "extends",
            [{"source_question": q1, "target_question": q2.artifact_id,
              "dependency_type": "evidential"}])
        s.rerun("experiment@Q001")
        s.run()
        # 旧关系保持审计态；新谱系的关系另立记录
        recs = s.cross_relations()
        assert recs[-1]["relation_id"] == rec["relation_id"]
        new_results = [a.artifact_id for a in s.registry.list_by_type("result")
                       if a.status == "active"]
        # 新 active result 可建立新关系（旧记录不阻碍）
        new_rec = s.declare_cross_relation(
            new_results[-1], q2.artifact_id, "extends",
            [{"source_question": q1, "target_question": q2.artifact_id,
              "dependency_type": "evidential"}])
        assert new_rec["relation_id"] != rec["relation_id"]

    def test_crash_resume_provenance_preserved(self, tmp_path):
        s, q1, q2 = _linked_pair(tmp_path)
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == q1)
        rec = s.declare_cross_relation(
            r1.artifact_id, q2, "extends",
            [{"source_question": q1, "target_question": q2,
              "dependency_type": "evidential"}])
        s2 = RuntimeSession(s.project_dir, ["Q001", "Q002"])
        s2.resume()
        rels = s2.cross_relations()
        assert len(rels) == 1
        assert rels[0]["dependency_refs"] == rec["dependency_refs"]
        assert rels[0]["created_by"] == rec["created_by"]

    def test_question_dependencies_reader_reflects_declaration(
            self, tmp_path):
        """依赖声明 → 叙事层过渡段派生（显式依赖的合法消费）。"""
        s, q1, q2 = _linked_pair(tmp_path)
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == q1)
        s.declare_cross_relation(
            r1.artifact_id, q2, "extends",
            [{"source_question": q1, "target_question": q2,
              "dependency_type": "evidential"}])
        deps = question_dependencies(s.registry, s.graph)
        assert {"from": q1, "to": q2,
                "relation": "provides_products_for"} in deps
