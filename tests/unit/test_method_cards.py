"""P2 Method Cards 测试：加载契约 / 交叉引用 / KnowledgeRetriever 打分与建议包。

运行: python -m pytest tests/unit/test_method_cards.py -q
覆盖任务书 Knowledge 层要求: Method Cards 结构化 + 检索 API 输出
「候选方法 + 适用条件 + 风险 + 验证方式 + 历史失败案例」。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.knowledge.cards import CardError, load_knowledge
from runtime.knowledge.retriever import KnowledgeRetriever

KNOWLEDGE_ROOT = REPO / "core" / "knowledge"


@pytest.fixture(scope="module")
def retriever():
    return KnowledgeRetriever(KNOWLEDGE_ROOT)


class TestCardLibrary:
    """真实知识库加载与契约校验（fail-closed）。"""

    def test_library_loads(self, retriever):
        assert len(retriever.cards) >= 12, "首批方法卡应 ≥12 张"
        assert len(retriever.failures) >= 8, "首批失败记忆应 ≥8 条"
        assert len(retriever.patterns) >= 6, "首批创新模式应 ≥6 个"

    def test_all_cards_have_core_fields(self, retriever):
        for card in retriever.cards.values():
            assert card.card_id.startswith("mc-")
            assert card.name and card.family
            assert card.problem_types and card.good_for
            assert card.validation, f"{card.card_id} 缺 validation（必做验证）"
            assert card.risks, f"{card.card_id} 缺 risks"

    def test_expected_high_freq_cards_present(self, retriever):
        expected = {"mc-topsis", "mc-entropy-weight", "mc-ahp", "mc-ga",
                    "mc-sa", "mc-grey-gm11", "mc-arima", "mc-nsga2",
                    "mc-monte-carlo", "mc-pca"}
        assert expected <= set(retriever.cards)

    def test_schema_files_exist(self):
        for name in ("method_card", "failure", "pattern"):
            p = REPO / "core" / "schemas" / "v3" / "knowledge" / f"{name}.schema.json"
            assert p.is_file(), f"缺少 schema: {p}"


class TestCardContract:
    """契约违反 → CardError（fail-closed）。"""

    def _write(self, tmp_path, content, name="bad.yaml"):
        cards = tmp_path / "methods" / "cards"
        cards.mkdir(parents=True)
        # 最小合法卡做底，再写坏卡
        (cards / "mc-ok.yaml").write_text(
            "card_id: mc-ok\nname: 合法卡\nfamily: f\nversion: 1\n"
            "problem_types: [evaluation]\ngood_for: [x]\nvalidation: [v]\n",
            encoding="utf-8")
        (cards / name).write_text(content, encoding="utf-8")

    def test_missing_required_field(self, tmp_path):
        self._write(tmp_path,
                    "card_id: mc-bad\nname: 缺 good_for\nfamily: f\n"
                    "problem_types: [evaluation]\n")
        with pytest.raises(CardError, match="good_for"):
            load_knowledge(tmp_path)

    def test_bad_card_id(self, tmp_path):
        self._write(tmp_path,
                    "card_id: bad-id\nname: x\nfamily: f\nproblem_types: [a]\n"
                    "good_for: [x]\nvalidation: [v]\n")
        with pytest.raises(CardError, match="mc-"):
            load_knowledge(tmp_path)

    def test_dangling_known_failure(self, tmp_path):
        self._write(tmp_path,
                    "card_id: mc-bad\nname: x\nfamily: f\nproblem_types: [a]\n"
                    "good_for: [x]\nvalidation: [v]\nknown_failures: [fm-nope]\n")
        with pytest.raises(CardError, match="fm-nope"):
            load_knowledge(tmp_path)

    def test_dangling_combined_with(self, tmp_path):
        self._write(tmp_path,
                    "card_id: mc-bad\nname: x\nfamily: f\nproblem_types: [a]\n"
                    "good_for: [x]\nvalidation: [v]\noften_combined_with: [mc-ghost]\n")
        with pytest.raises(CardError, match="mc-ghost"):
            load_knowledge(tmp_path)

    def test_duplicate_card_id(self, tmp_path):
        cards = tmp_path / "methods" / "cards"
        cards.mkdir(parents=True)
        body = ("card_id: mc-dup\nname: x\nfamily: f\nversion: 1\n"
                "problem_types: [a]\ngood_for: [x]\nvalidation: [v]\n")
        (cards / "a.yaml").write_text(body, encoding="utf-8")
        (cards / "b.yaml").write_text(body, encoding="utf-8")
        with pytest.raises(CardError, match="重复"):
            load_knowledge(tmp_path)


class TestRetrieverScoring:
    """打分规则逐项验证。"""

    def test_evaluation_features_rank_evaluation_cards(self, retriever):
        recs = retriever.recommend({"problem_types": ["evaluation", "ranking"],
                                    "has_data": True})
        assert recs, "评价类特征应命中方法"
        ids = [r.card.card_id for r in recs]
        assert "mc-topsis" in ids
        assert recs[0].score >= 3
        assert any("问题类型命中" in m for r in recs for m in r.matched)

    def test_no_data_excludes_data_cards(self, retriever):
        recs = retriever.recommend({"problem_types": ["evaluation", "ranking"],
                                    "has_data": False})
        ids = {r.card.card_id for r in recs}
        assert "mc-topsis" not in ids, "requires_data 卡在无数据时应排除"
        assert "mc-ahp" in ids or "mc-fuzzy-evaluation" in ids, \
            "无数据评价应推荐主观方法"

    def test_small_sample_excludes_large_only_cards(self, retriever):
        recs = retriever.recommend({"problem_types": ["prediction", "timeseries"],
                                    "has_data": True, "sample_size": "small",
                                    "time_series": True})
        ids = {r.card.card_id for r in recs}
        assert "mc-lstm" not in ids, "小样本应排除 large-only 卡"
        assert "mc-grey-gm11" in ids, "小样本时序应推荐灰色预测"
        assert "mc-arima" not in ids, "ARIMA 要求 medium+ 样本"

    def test_large_sample_timeseries(self, retriever):
        recs = retriever.recommend({"problem_types": ["prediction", "timeseries"],
                                    "has_data": True, "sample_size": "large",
                                    "time_series": True})
        ids = {r.card.card_id for r in recs}
        assert "mc-lstm" in ids
        assert "mc-grey-gm11" not in ids, "灰色预测样本档不含 large"

    def test_multi_objective_boost(self, retriever):
        recs = retriever.recommend({"problem_types": ["optimization"],
                                    "objectives": 3})
        ids = [r.card.card_id for r in recs]
        assert ids[0] == "mc-nsga2", "多目标特征下 NSGA-II 应排第一"

    def test_uncertainty_boost(self, retriever):
        recs = retriever.recommend({"problem_types": ["uncertainty"],
                                    "uncertainty": True})
        ids = {r.card.card_id for r in recs}
        assert "mc-monte-carlo" in ids
        assert any("不确定性" in m for r in recs for m in r.matched
                   if r.card.card_id == "mc-monte-carlo")

    def test_time_series_mismatch_penalty(self, retriever):
        recs_ts = retriever.recommend({"problem_types": ["prediction"],
                                       "has_data": True, "time_series": True,
                                       "sample_size": "medium"})
        recs_flat = retriever.recommend({"problem_types": ["prediction"],
                                         "has_data": True, "time_series": False,
                                         "sample_size": "medium"})
        ts_ids = {r.card.card_id for r in recs_ts}
        flat_ids = {r.card.card_id for r in recs_flat}
        assert "mc-arima" in ts_ids
        # 非时序特征下纯时序卡被 -4 压出（单标签命中 +3 不足以存活）
        assert "mc-arima" not in flat_ids
        assert "mc-grey-gm11" not in flat_ids

    def test_top_k_limit_and_ordering(self, retriever):
        recs = retriever.recommend({"problem_types": ["evaluation"]}, top_k=2)
        assert len(recs) <= 2
        scores = [r.score for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_unknown_problem_type_returns_empty(self, retriever):
        assert retriever.recommend({"problem_types": ["nonexistent-type"]}) == []


class TestRecommendationPackage:
    """建议包完整性：风险 + 验证 + 失败案例 + 创新模式。"""

    def test_topsis_rec_includes_failures_and_patterns(self, retriever):
        recs = retriever.recommend({"problem_types": ["evaluation", "ranking"],
                                    "has_data": True})
        rec = next(r for r in recs if r.card.card_id == "mc-topsis")
        fids = [f.failure_id for f in rec.related_failures]
        assert "fm-topsis-no-normalization" in fids, "TOPSIS 卡应附未标准化失败案例"
        pids = [p.pattern_id for p in rec.related_patterns]
        assert "ip-combined-weighting" in pids or "ip-two-stage-evaluation" in pids

    def test_as_dict_shape(self, retriever):
        recs = retriever.recommend({"problem_types": ["optimization"],
                                    "objectives": 2})
        d = recs[0].as_dict()
        for key in ("card_id", "name", "score", "matched", "warnings",
                    "validation", "related_failures", "related_patterns"):
            assert key in d

    def test_metaheuristics_family_failures(self, retriever):
        failures = retriever.failures_for("mc-ga")
        fids = [f.failure_id for f in failures]
        assert "fm-heuristic-global-optimum-claim" in fids

    def test_patterns_for_problem_type(self, retriever):
        pats = retriever.patterns_for(["optimization", "multi-objective"])
        assert pats, "优化类应命中创新模式"
        assert pats[0].pattern_id == "ip-pareto-select"

    def test_metaheuristic_cards_share_overclaim_failure(self, retriever):
        """元启发式方法族共享"全局最优"失败记忆（家族级关联）。"""
        for cid in ("mc-ga", "mc-sa", "mc-pso"):
            assert any(f.failure_id == "fm-heuristic-global-optimum-claim"
                       for f in retriever.failures_for(cid)), cid
