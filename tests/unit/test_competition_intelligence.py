"""P8 Competition Intelligence 测试：CI-01~CI-10 不变量 + A1/A2/A3 场景。

运行: python -m pytest tests/unit/test_competition_intelligence.py -q
对照任务书 P8-16（API 可测试 10 项）与 P8-17（不变量 CI-01~CI-10），
以及最终成功标准：同一题目改变三个约束 → 推荐合理变化且每次变化可解释。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.decisions.log import DecisionLog  # noqa: E402
from runtime.knowledge.intelligence import CompetitionIntelligence, \
    ProblemProfile  # noqa: E402
from runtime.knowledge.packs import detect_knowledge_conflicts  # noqa: E402

KNOW = REPO / "core" / "knowledge"


def _ci(tmp_path, competition_type="cumcm"):
    dlog = DecisionLog(tmp_path / "decision_log.json")
    return CompetitionIntelligence(KNOW, decisions=dlog,
                                   competition_type=competition_type)


def _base_profile() -> ProblemProfile:
    return ProblemProfile(problem_types=["evaluation"], has_data=True,
                          sample_size="medium", competition_type="cumcm")


# ============================================================
# API 基础行为
# ============================================================

class TestAPIBasics:
    def test_recommend_deterministic(self, tmp_path):
        """P8-16-1 / CI-10：同 Profile → 确定性推荐。"""
        ci = _ci(tmp_path)
        r1 = [(r.card.card_id, r.score) for r in ci.recommend_methods(
            _base_profile())]
        r2 = [(r.card.card_id, r.score) for r in ci.recommend_methods(
            _base_profile())]
        assert r1 == r2 and r1

    def test_every_recommendation_explainable(self, tmp_path):
        """CI-01：每条推荐可解释（分数可拆解 + reasoning 非空）。"""
        ci = _ci(tmp_path)
        for rec in ci.recommend_methods(_base_profile()):
            assert rec.reasoning(), "推荐必须带解释"
            sd = rec.score_detail.as_dict()
            assert sum(sd.values()) == rec.score, \
                f"{rec.card.card_id} 分数不可拆解: {sd} vs {rec.score}"
            assert rec.knowledge_refs, "必须引用知识（id+version）"

    def test_no_recommendation_references_missing_card(self, tmp_path):
        """CI-02：推荐不得引用缺失的 MethodCard（knowledge_refs 全部存在）。"""
        ci = _ci(tmp_path)
        for rec in ci.recommend_methods(_base_profile()):
            for ref in rec.knowledge_refs:
                assert ref["id"] in ci.retriever.cards \
                    or ref["id"] in ci.retriever.patterns

    def test_candidates_generated_and_ranked(self, tmp_path):
        """P8-21-G：生成候选方案而非单模型；排序确定。"""
        ci = _ci(tmp_path)
        cands = ci.rank_candidates(ci.generate_candidates(_base_profile()))
        assert len(cands) >= 3
        kinds = {c.kind for c in cands}
        assert "baseline" in kinds
        assert [c.score for c in cands] == \
            sorted((c.score for c in cands), reverse=True)

    def test_experiment_plan_complete(self, tmp_path):
        """P8-21-H/I/J/K：每条实验有 purpose/hypothesis/baseline/decision_rule。"""
        ci = _ci(tmp_path)
        sug = ci.build_experiment_plan(_base_profile())
        assert sug.plan.entries
        for e in sug.plan.entries:
            assert e.purpose, "实验必须回答为什么做"
            assert e.hypothesis
            assert e.baseline
            assert e.decision_rule is not None
        # 信息增益 + 成本存在（时间预算基础）
        assert all(0 <= e.expected_information_gain <= 1 for e in sug.plan.entries)
        assert all(e.cost >= 1 for e in sug.plan.entries)

    def test_decision_trace_and_explain(self, tmp_path):
        """P8-21-M：Decision 绑定知识版本；explain_decision 可重现。"""
        ci = _ci(tmp_path)
        outcome = ci.select_and_record(_base_profile(), "Q001")
        assert outcome.decision_id
        exp = ci.explain_decision(outcome.decision_id)
        assert exp["chosen"] == outcome.chosen
        assert exp["knowledge_refs"], "决策必须绑定知识"
        for ref in exp["knowledge_refs"]:
            assert ref["reproducible"], \
                "登记时的知识版本必须与当前一致（历史可重现）"
        assert exp["score_breakdown"], "决策必须携带分数拆解"


# ============================================================
# 决策改变的三个约束场景（P8 成功标准）
# ============================================================

class TestConstraintScenarios:
    def test_A1_to_A2_small_sample_changes_ranking(self, tmp_path):
        """A1 普通数据 → A2 小样本：推荐顺序合理变化且可解释。"""
        ci = _ci(tmp_path)
        a1 = ci.recommend_methods(_base_profile())
        a2 = ci.recommend_methods(
            ProblemProfile(problem_types=["evaluation"], has_data=True,
                           sample_size="small"))
        assert [(r.card.card_id, r.score) for r in a1] != \
            [(r.card.card_id, r.score) for r in a2], "小样本约束应改变推荐"
        # 变化可解释：小样本正条件命中（small_sample_friendly）或否定条件违反
        explained = any(
            "small_sample_friendly" in r.matched_capabilities or r.violations
            for r in a2)
        assert explained, "变化必须能解释（正条件命中或否定条件违反）"

    def test_A2_to_A3_competition_pack_changes_ranking(self, tmp_path):
        """A2 → A3 竞赛约束：pack 的 high_risk_methods 改变推荐并可解释。"""
        ci_cumcm = _ci(tmp_path, "cumcm")
        profile = ProblemProfile(problem_types=["prediction"], has_data=True,
                                 sample_size="medium")
        with_pack = ci_cumcm.recommend_methods(profile)
        scores_with = {r.card.card_id: r.score for r in with_pack}
        # 无 pack 参照
        from runtime.knowledge.retriever import KnowledgeRetriever
        bare = KnowledgeRetriever(KNOW).recommend(profile.as_features(),
                                                  top_k=10)
        for rec in bare:
            if rec.card.family in (ci_cumcm.pack.high_risk_methods or []):
                assert scores_with.get(rec.card.card_id, 0) \
                    < rec.score, "high_risk 方法在 pack 下必须降权且可解释"
                hit = [r for r in with_pack
                       if r.card.card_id == rec.card.card_id]
                if hit:
                    assert any(rk["source"] == "competition_pack"
                               or "competition" in json.dumps(rk)
                               for rk in hit[0].risks) or \
                        hit[0].score_detail.risk_penalty < 0

    def test_failure_memory_affects_recommendation(self, tmp_path):
        """P8-16-2 / CI-04：Failure Memory 改变打分与实验需求。"""
        ci = _ci(tmp_path)
        recs = ci.recommend_methods(_base_profile())
        penalized = [r for r in recs if r.score_detail.risk_penalty < 0]
        assert penalized, "存在失败记忆的方法必须被罚分"
        for r in penalized:
            assert any(rk["source"] == "failure_memory" for rk in r.risks)
            high = [f for f in r.related_failures if f.severity == "high"]
            if high:
                assert any(e.startswith("failure-guard")
                           for e in r.required_experiments), \
                    "high 级失败必须注入强制验证"

    def test_data_constraint_downgrades_method(self, tmp_path):
        """P8-16-4：数据限制 → 依赖数据的方法被降权/违反。"""
        ci = _ci(tmp_path)
        with_data = {r.card.card_id: r.score for r in ci.recommend_methods(
            ProblemProfile(problem_types=["prediction"], has_data=True))}
        without = {r.card.card_id: (r.score, r.violations)
                   for r in ci.recommend_methods(
                       ProblemProfile(problem_types=["prediction"],
                                      has_data=False))}
        excluded = set(with_data) - set(without)      # 被硬过滤排除的方法
        downgraded = [cid for cid in without
                      if cid in with_data and without[cid][0] < with_data[cid]]
        assert excluded or downgraded, \
            "无数据时依赖数据的方法应被排除（最强降权）或降分"


# ============================================================
# 失效 / 版本 / 冲突 / 只读不变量
# ============================================================

class TestLifecycleInvariants:
    def test_ci03_innovation_without_evidence_is_hypothesis(self, tmp_path):
        """CI-03：无证据的创新只能是 hypothesis。"""
        ci = _ci(tmp_path)
        cands = ci.generate_candidates(_base_profile())
        innovations = [i for c in cands for i in c.innovations]
        assert innovations, "评价类问题应命中至少一个创新模式"
        for i in innovations:
            assert i.status == "hypothesis"
            assert i.required_evidence or i.validation_protocol, \
                "创新候选必须绑定证据要求"

    def test_ci06_invalidated_evidence_not_supporting_decision(self, tmp_path):
        """CI-06：失效证据不得支撑 active 决策（Registry 级验证，P7 契约）。"""
        import tempfile
        from runtime.artifacts.registry import ArtifactRegistry
        from runtime.graph.evidence_graph import EvidenceGraph
        with tempfile.TemporaryDirectory() as td:
            reg = ArtifactRegistry(Path(td) / "r.json")
            reg.project = "t"
            reg.create("question", title="q", activate=True)
            reg.create("model", title="m", activate=True)
            reg.create("result", title="r", activate=True)
            g = EvidenceGraph(reg)
            g.add_relation("E001", "produces", "R001")
            g.add_relation("R001", "supports", "C001")
            g.invalidate("R001", reason="结果失效")
            # 支撑链上的 claim 被传播判死 → 不得继续支撑决策（P7 契约）
            assert reg.get("R001").status == "invalidated"
            assert reg.get("C001").status == "invalidated"

    def test_ci07_knowledge_version_change_keeps_history(self, tmp_path):
        """CI-07：知识版本升级不改写历史决策（决策存的是登记时版本）。"""
        ci = _ci(tmp_path)
        outcome = ci.select_and_record(_base_profile(), "Q001")
        exp_before = ci.explain_decision(outcome.decision_id)
        # 模拟卡片升级
        card = ci.retriever.cards[outcome.chosen]
        card.version += 1
        exp_after = ci.explain_decision(outcome.decision_id)
        # 决策记录的是登记时版本 → 不被当前版本改写（历史可追溯）
        v_before = [(r["id"], r["version"]) for r in exp_before["knowledge_refs"]]
        v_after = [(r["id"], r["version"]) for r in exp_after["knowledge_refs"]]
        assert v_before == v_after
        # 当前版本已变 → reproducible 标志显式翻转（不静默）
        ref_after = exp_after["knowledge_refs"][0]
        assert ref_after["current_version"] == 2
        assert ref_after["reproducible"] is False
        assert exp_after["chosen"] == exp_before["chosen"]

    def test_ci08_pack_readonly_on_runtime_state(self, tmp_path):
        """CI-08：Competition Pack 不直接改 Runtime 状态（只影响打分）。"""
        ci = _ci(tmp_path)
        before = ci.pack.__dict__.copy()
        ci.recommend_methods(_base_profile())
        ci.generate_candidates(_base_profile())
        assert ci.pack.__dict__ == before, "pack 被打分过程改写 = 违反只读契约"

    def test_ci09_side_effect_controlled(self, tmp_path):
        """CI-09：知识层 side-effect 受控——除 DecisionLog 外零写入。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            dlog = DecisionLog(Path(td) / "d.json")
            ci = CompetitionIntelligence(KNOW, decisions=dlog)
            ci.recommend_methods(_base_profile())
            ci.generate_candidates(_base_profile())
            ci.build_experiment_plan(_base_profile())
            assert list(Path(td).iterdir()) == [Path(td) / "d.json"] or \
                not list(Path(td).iterdir()), \
                "知识 API 不得在工作目录产生其他写入"


# ============================================================
# 冲突检测
# ============================================================

class TestConflictDetection:
    def test_conflicting_knowledge_detected(self, tmp_path):
        """P8-16-8 / CI 冲突：compatible×incompatible 矛盾必须被发现。"""
        from runtime.knowledge.cards import MethodCard
        a = MethodCard.from_dict({
            "card_id": "mc-test-a", "name": "A", "family": "t",
            "problem_types": ["evaluation"], "good_for": ["x"],
            "incompatible_methods": ["mc-test-b"]}, "test")
        b = MethodCard.from_dict({
            "card_id": "mc-test-b", "name": "B", "family": "t",
            "problem_types": ["evaluation"], "good_for": ["x"],
            "compatible_methods": ["mc-test-a"]}, "test")
        conflicts = detect_knowledge_conflicts(
            {"mc-test-a": a, "mc-test-b": b}, {}, {})
        assert any(c.severity == "high" and c.field == "compatible_incompatible"
                   for c in conflicts)

    def test_real_knowledge_conflict_report_clean_or_open(self, tmp_path):
        """真实知识库：冲突要么为空，要么每条可记录（open 状态显式）。"""
        ci = _ci(tmp_path)
        for c in ci.conflict_report():
            assert c["resolution_status"] in ("open", "acknowledged", "resolved")
            assert c["severity"] in ("low", "medium", "high")
