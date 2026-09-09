"""P12-3-lite Cross-Question Context 边界性质测试。

运行: python -m pytest tests/integration/test_cross_question_context.py -q
只测边界性质：派生纯度（只读）/ 确定性 / 准入门（三条件）/ absent 标注 /
state_version 展示。不追求测试数量。
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.synthesis.context import (  # noqa: E402
    ContextError, _evidence_independent, build_cross_question_context)
from runtime.writing.findings import Finding  # noqa: E402


def _session(tmp_path, questions=("Q001", "Q002"), run=True, name="proj", **kw):
    from _real_session import make_real_session
    return make_real_session(tmp_path, questions=questions, run=run,
                             name=name, **kw)


def _linked_pair(tmp_path, dep_type="evidential", name="proj"):
    """已声明 Q001→Q002 科学依赖的双问题会话。返回 (s, q1, q2)。"""
    s = _session(tmp_path, run=True, name=name)
    q1 = next(a.artifact_id for a in s.registry.list_by_type("question")
              if a.title == "Q001")
    q2 = next(a.artifact_id for a in s.registry.list_by_type("question")
              if a.title == "Q002")
    s.declare_dependency(q1, q2, dep_type, "测试依赖")
    return s, q1, q2


def _strip_fids(obj):
    """剥离 finding_id（FindingGraph batch 序号不跨重建稳定，非本层产物）。"""
    if isinstance(obj, dict):
        return {k: _strip_fids(v) for k, v in obj.items()
                if k != "finding_id"}
    if isinstance(obj, list):
        return [_strip_fids(v) for v in obj]
    return obj


def _build(s):
    return build_cross_question_context(s.registry, s.graph, s.state)


class TestDerivedPurity:
    def test_build_is_read_only(self, tmp_path):
        """派生纯度：构建前后 State / Registry / 磁盘文件零变化。"""
        s, q1, q2 = _linked_pair(tmp_path)
        before_state = json.dumps(s.state.data, sort_keys=True,
                                  ensure_ascii=False)
        before_arts = [(a.artifact_id, a.status, a.tags, a.depends_on)
                       for a in s.registry.all()]
        before_files = sorted(p.name for p in s.project_dir.rglob("*"))
        _build(s)
        _build(s)
        assert json.dumps(s.state.data, sort_keys=True,
                          ensure_ascii=False) == before_state
        assert [(a.artifact_id, a.status, a.tags, a.depends_on)
                for a in s.registry.all()] == before_arts
        assert sorted(p.name for p in s.project_dir.rglob("*")) == before_files

    def test_deterministic_rebuild(self, tmp_path):
        """确定性：同一状态两次重建，导出一致（finding_id 除外）。"""
        s, q1, q2 = _linked_pair(tmp_path)
        c1, c2 = _build(s), _build(s)
        assert _strip_fids(c1.as_dict()) == _strip_fids(c2.as_dict())
        assert c1.to_context_block() == c2.to_context_block()

    def test_unknown_question_rejected(self, tmp_path):
        s = _session(tmp_path, run=False, name="p-unknown")
        with pytest.raises(ContextError, match="不存在"):
            build_cross_question_context(s.registry, s.graph, s.state,
                                         ["Q001", "QX"])

    def test_session_accessor_matches_direct_build(self, tmp_path):
        """会话入口与直接构建等价（同一派生函数）。"""
        s, q1, q2 = _linked_pair(tmp_path)
        assert _strip_fids(s.cross_question_context().as_dict()) == \
            _strip_fids(_build(s).as_dict())


class TestAdmissionGate:
    def test_supported_conclusion_with_provenance(self, tmp_path):
        """默认管线（results 含稳健性标签）+ evidential 依赖 → supported，
        provenance 含审计 §Q12 最小集。"""
        s, q1, q2 = _linked_pair(tmp_path)
        ctx = _build(s)
        assert len(ctx.conclusions) == 1
        c = ctx.conclusions[0]
        assert c["level"] == "supported"
        assert c["question_refs"] == [q1, q2]
        assert c["dependency_refs"][0]["dependency_type"] == "evidential"
        assert c["claim_refs"] == ["C001", "C002"]
        assert c["decision_rule"]["rule"] == "discrete-bottleneck"
        assert c["decision_rule"]["bottleneck"] == "PASS"
        assert set(c["decision_rule"]["admission"]) == {
            "declared-dependency", "status-admissible",
            "evidence-independent"}
        assert c["state_version"] == ctx.state_version
        # 门 2：UNKNOWN comparative 占位永不入组合
        assert all(f["status"] in ("PASS", "WEAK")
                   for f in c["finding_refs"])
        assert {f["results"][0] for f in c["finding_refs"]} == {"R001", "R002"}

    def test_qualified_when_weak_bottleneck(self, tmp_path):
        """瓶颈规则：一侧 finding 降为 WEAK → qualified + 局限记录。"""
        s, q1, q2 = _linked_pair(tmp_path)
        s.registry.get("R001").tags.clear()
        ctx = _build(s)
        assert len(ctx.conclusions) == 1
        c = ctx.conclusions[0]
        assert c["level"] == "qualified"
        assert c["decision_rule"]["bottleneck"] == "WEAK"
        assert any("WEAK" in lim for lim in c["limitations"])

    def test_status_gate_excludes_fail(self, tmp_path):
        """门 2：一侧只有 FAIL finding（无 producer）→ 不得组合 → hypothesis。"""
        s, q1, q2 = _linked_pair(tmp_path)
        q3 = s.registry.create("question", title="Q3-only-fail",
                               activate=True).artifact_id
        s.declare_dependency(q1, q3, "evidential", "测试依赖")
        s.registry.create("result", title="孤儿结果", question=q3,
                          activate=True)   # 无 produces 边 → descriptive FAIL
        ctx = _build(s)
        assert all(q3 not in c["question_refs"] for c in ctx.conclusions)
        assert any("无非 FAIL/UNKNOWN" in h["reason"]
                   and q3 in h["question_refs"] for h in ctx.hypotheses)

    def test_execution_dependency_not_synthesized(self, tmp_path):
        """门 1（参与矩阵）：execution 依赖声明存在但不参与 synthesis。"""
        s, q1, q2 = _linked_pair(tmp_path, dep_type="execution")
        ctx = _build(s)
        assert ctx.conclusions == []
        assert any("不参与 synthesis" in h["reason"]
                   for h in ctx.hypotheses)

    def test_evidence_independence_rule(self):
        """门 3：共享支撑 result 的两侧不得组合（同源不因数量升级）。"""
        f1 = Finding("F1", "descriptive", "s1", supported_by=["R001"],
                     status="PASS", question="Q001")
        f2 = Finding("F2", "descriptive", "s2", supported_by=["R001"],
                     status="PASS", question="Q002")
        f3 = Finding("F3", "descriptive", "s3", supported_by=["R002"],
                     status="PASS", question="Q002")
        assert not _evidence_independent([f1], [f2])
        assert _evidence_independent([f1], [f3])

    def test_hypothesis_without_declared_dependency(self, tmp_path):
        """P12-0 Q10：无依赖声明但结构可比 → hypothesis（非 conclusion）。"""
        s = _session(tmp_path, name="p-nodep")
        ctx = _build(s)
        assert ctx.conclusions == []
        assert any("无显式依赖声明" in h["reason"]
                   for h in ctx.hypotheses)

    def test_no_hypothesis_without_comparability(self, tmp_path):
        """结构不可比（一侧无可入组 finding）→ 不产生 hypothesis 噪声。"""
        s = _session(tmp_path, name="p-incomp")
        q1 = next(a.artifact_id for a in s.registry.list_by_type("question")
                  if a.title == "Q001")
        q2 = next(a.artifact_id for a in s.registry.list_by_type("question")
                  if a.title == "Q002")
        q3 = s.registry.create("question", title="Q3-bare",
                               activate=True).artifact_id
        s.registry.create("result", title="孤儿结果", question=q3,
                          activate=True)   # Q3 仅 FAIL/UNKNOWN
        ctx = _build(s)
        assert any(h["question_refs"] == [q1, q2] for h in ctx.hypotheses)
        assert all(q3 not in h["question_refs"] for h in ctx.hypotheses)


class TestContextBlock:
    def test_block_sections_and_absent_marker(self, tmp_path):
        """块结构：per-question / 链路 / 结论 或 synthesis: absent。"""
        s = _session(tmp_path, name="p-absent")
        block = _build(s).to_context_block()
        assert "## 跨问题综合上下文" in block
        assert "state_version:" in block
        assert "### Q001 · status=" in block
        assert "### 跨问题链路" in block
        assert "synthesis: absent" in block

    def test_block_with_conclusion(self, tmp_path):
        s, q1, q2 = _linked_pair(tmp_path, name="p-concl")
        block = _build(s).to_context_block()
        assert "### 结论（准入）" in block
        assert "[supported]" in block
        assert "--evidential-->" in block
        assert "discrete-bottleneck" in block
        assert "synthesis: absent" not in block
        assert "### 假设" not in block   # 双问题全准入：无假设噪声

    def test_state_version_reflects_mutations(self, tmp_path):
        """state_version 随状态变化（deps/relations 计数入版本）。"""
        s = _session(tmp_path, name="p-sv")
        v0 = _build(s).state_version
        q1 = next(a.artifact_id for a in s.registry.list_by_type("question")
                  if a.title == "Q001")
        q2 = next(a.artifact_id for a in s.registry.list_by_type("question")
                  if a.title == "Q002")
        s.declare_dependency(q1, q2, "evidential", "版本对账")
        v1 = _build(s).state_version
        assert v1["dependency_records"] == v0["dependency_records"] + 1
        assert v1 != v0
