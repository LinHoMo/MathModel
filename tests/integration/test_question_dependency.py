"""P12-1 Question Dependency Contract 不变量测试（D1–D10）。

运行: python -m pytest tests/integration/test_question_dependency.py -q
对照任务书 P12-1 验收表。scope 冻结：不做 synthesis / 不做跨问题聚合 /
不做 confidence 加权 / 不改 P7 契约。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.state.dependencies import (  # noqa: E402
    DEPENDENCY_TYPES, PARTICIPATION, PROPAGATING_TYPES, DependencyError,
    declare_dependency, dependency_integrity_problems, dependency_records,
    propagate_to_dependents)
from runtime.writing.paragraphs import question_dependencies  # noqa: E402

TERMINAL = ("invalidated", "superseded", "deprecated")


def _session(tmp_path, questions=("Q001", "Q002"), run=True, name="proj"):
    s = RuntimeSession(tmp_path / name, list(questions))
    if run:
        s.run()
    return s


# ============================================================
# D1 双写一致 + D8 provenance
# ============================================================

class TestD1DualWrite:
    def test_declare_dual_writes_state_and_registry(self, tmp_path):
        s = _session(tmp_path)
        rec = s.declare_dependency("Q001", "Q002", "evidential",
                                   "Q2 复用 Q1 的预测结果", "test")
        # State records
        recs = dependency_records(s.state)
        assert len(recs) == 1 and recs[0]["dependency_type"] == "evidential"
        # Registry 镜像（evidential → depends_on）
        assert "Q001" in s.registry.get("Q002").depends_on
        # D1: 一致性检查通过
        assert s.dependency_integrity() == []

    def test_D1_mismatch_detected(self, tmp_path):
        s = _session(tmp_path)
        s.declare_dependency("Q001", "Q002", "evidential", "r")
        # 篡改 Registry 镜像（模拟漂移）
        s.registry.get("Q002").depends_on.remove("Q001")
        problems = s.dependency_integrity()
        assert problems and "≠" in problems[0]

    def test_D8_provenance_complete(self, tmp_path):
        s = _session(tmp_path)
        rec = s.declare_dependency("Q001", "Q002", "evidential",
                                   "预测结果复用", created_by="tester")
        for key in ("source_question", "target_question", "dependency_type",
                    "reason", "created_by", "at"):
            assert rec.get(key), f"provenance 缺 {key}"
        assert rec["source_question"] == "Q001"
        assert rec["target_question"] == "Q002"


# ============================================================
# D2 显式声明（无隐式依赖）
# ============================================================

class TestD2ExplicitOnly:
    def test_no_implicit_dependency_from_question_order(self, tmp_path):
        s = _session(tmp_path)
        assert dependency_records(s.state) == []
        assert question_dependencies(s.registry, s.graph) == []
        assert s.dependency_integrity() == []

    def test_invalid_type_rejected(self, tmp_path):
        s = _session(tmp_path, run=False)
        with pytest.raises(DependencyError):
            declare_dependency(s.state, s.registry, "Q001", "Q002",
                               "scientific", "自由文本类型")
        with pytest.raises(DependencyError):
            declare_dependency(s.state, s.registry, "Q001", "Q002",
                               "unknown-kind", "r")

    def test_missing_question_rejected(self, tmp_path):
        s = _session(tmp_path, run=False)
        with pytest.raises(DependencyError):
            declare_dependency(s.state, s.registry, "Q001", "Q999",
                               "evidential", "r")
        with pytest.raises(DependencyError):
            declare_dependency(s.state, s.registry, "Q001", "Q001",
                               "evidential", "自依赖")


# ============================================================
# D3/D4 传播参与矩阵（钉死 D3）
# ============================================================

class TestD3D4Propagation:
    def _invalidate_q1(self, s):
        r = next(a for a in s.registry.list_by_type("result")
                 if a.question == "Q001")
        s.invalidate(r.artifact_id, reason="Q1 证据勘误")

    def _q2_marks(self, s):
        return [a for a in s.registry.all()
                if a.question == "Q002" and a.status not in TERMINAL
                and a.invalidation.get("status") == "requires_revalidation"]

    def test_D3_execution_dependency_never_propagates(self, tmp_path):
        """D3（钉死）：execution 依赖不产生任何科学失效传播。"""
        s = _session(tmp_path)
        s.declare_dependency("Q001", "Q002", "execution", "调度顺序")
        self._invalidate_q1(s)
        assert self._q2_marks(s) == [], \
            "execution 依赖不得打 requires_revalidation"
        # Q002 的证据链完全不受影响
        for a in s.registry.all():
            if a.question == "Q002":
                assert a.status not in ("invalidated",)

    def test_D4_evidential_dependency_propagates_reval(self, tmp_path):
        s = _session(tmp_path)
        s.declare_dependency("Q001", "Q002", "evidential", "结果复用")
        self._invalidate_q1(s)
        marks = self._q2_marks(s)
        assert marks, "evidential 依赖必须传播 requires_revalidation"
        # D7: 只是 reval 标记，不判死（superseded ≠ invalidated 不混淆）
        for a in marks:
            assert a.status not in TERMINAL

    def test_D4_extension_propagates(self, tmp_path):
        s = _session(tmp_path)
        s.declare_dependency("Q001", "Q002", "extension", "扩展研究")
        self._invalidate_q1(s)
        assert self._q2_marks(s)

    def test_comparative_and_methodological_do_not_propagate(self, tmp_path):
        s = _session(tmp_path)
        s.declare_dependency("Q001", "Q002", "comparative", "横向对比")
        self._invalidate_q1(s)
        assert self._q2_marks(s) == []
        # participitation 矩阵本身冻结
        assert PROPAGATING_TYPES == ("evidential", "extension")
        assert PARTICIPATION["execution"]["invalidation"] is False


# ============================================================
# D5 terminal 不被复活/不被标记
# ============================================================

class TestD5Terminal:
    def test_terminal_artifacts_skipped_by_propagation(self, tmp_path):
        s = _session(tmp_path, run=False)
        # 目标问题 = Q002 的实际 artifact id（标签↔ID 以 Registry 为准）
        q2 = next(a for a in s.registry.list_by_type("question")
                  if a.title == "Q002").artifact_id
        r = s.registry.create("result", title="死结果", question=q2,
                              activate=True)
        r.transition("invalidated", by="t", reason="test")
        q1 = s.registry.list_by_type("question")[0].artifact_id
        s.declare_dependency(q1, q2, "evidential", "r")
        affected = propagate_to_dependents(s.registry, s.state, q1, "勘误")
        targets = {x["artifact_id"] for x in affected}
        assert r.artifact_id not in targets, "终态产物不得被传播标记"
        assert s.registry.get(r.artifact_id).status == "invalidated"


# ============================================================
# D6 环检测
# ============================================================

class TestD6Acyclic:
    def test_cycle_rejected(self, tmp_path):
        s = _session(tmp_path, questions=("Q001", "Q002"), run=False)
        s.declare_dependency("Q001", "Q002", "evidential", "r")
        with pytest.raises(DependencyError, match="循环"):
            declare_dependency(s.state, s.registry, "Q002", "Q001",
                               "evidential", "反向依赖")

    def test_diamond_is_legal(self, tmp_path):
        s = _session(tmp_path, questions=("Q001", "Q002", "Q003"), run=False)
        s.declare_dependency("Q001", "Q003", "evidential", "r1")
        s.declare_dependency("Q002", "Q003", "evidential", "r2")
        assert s.dependency_integrity() == []


# ============================================================
# D9 crash/resume：依赖不依赖内存态
# ============================================================

class TestD9Resume:
    def test_dependency_survives_crash_resume(self, tmp_path):
        s = _session(tmp_path, run=True)
        s.declare_dependency("Q001", "Q002", "evidential", "r")
        # 新会话（零内存）下：records / 镜像 / 一致性全部还在
        s2 = RuntimeSession(s.project_dir, ["Q001", "Q002"])
        recs = dependency_records(s2.state)
        assert len(recs) == 1
        assert "Q001" in s2.registry.get("Q002").depends_on
        assert s2.dependency_integrity() == []
        # 传播在新会话下同样工作
        r = next(a for a in s2.registry.list_by_type("result")
                 if a.question == "Q001")
        s2.invalidate(r.artifact_id, reason="勘误")
        assert any(a.question == "Q002" and a.invalidation.get("status")
                   == "requires_revalidation" for a in s2.registry.all())


# ============================================================
# D10 不改变既有单问题语义（由全量回归背书）+ 调度语义
# ============================================================

class TestD10Scheduling:
    def test_scheduling_mirror_and_blocking(self, tmp_path):
        """execution/evidential → State 调度镜像 → blocked_by_dependencies。"""
        s = _session(tmp_path, run=False)
        s.declare_dependency("Q001", "Q002", "execution", "调度顺序")
        # Q001 未完成 → Q002 被阻塞
        assert s.state.blocked_by_dependencies("Q002") == ["Q001"]
        # comparative 不参与调度（Q003 → Q002）
        s.registry.create("question", title="Q3", activate=True)
        q3 = [a.artifact_id for a in s.registry.list_by_type("question")
              if a.title == "Q3"][0]
        s.declare_dependency(q3, "Q002", "comparative", "对比")
        assert s.state.blocked_by_dependencies("Q002") == ["Q001"]

    def test_participation_matrix_frozen(self):
        assert set(DEPENDENCY_TYPES) == {"execution", "methodological",
                                         "evidential", "comparative",
                                         "extension"}
        assert PARTICIPATION["evidential"] == {
            "scheduling": True, "invalidation": True, "synthesis": True,
            "aggregation": True}
