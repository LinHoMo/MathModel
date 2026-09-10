# -*- coding: utf-8 -*-
"""P2-3 验收：检索命中率（检索失败 vs 知识无用 判别）+ 元数据修复。

验收标准（ROADMAP P2-3）：
1. 8 题 ground-truth 卡 hit@3 ≥ 75%（检索链路可靠）
2. 2017_B（词表错位）与 2022_C（sample_size 元数据）修复后命中
3. 检索修复不破坏既有知识检索语义（KnowledgeRetriever 回归）
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "research" / "P15" / "analysis"))

from p2_3_retrieval_hitrate import PROBLEM_FEATURES, PROBLEM_GT, main  # noqa: E402
from runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402


@pytest.fixture(scope="module")
def hit_result():
    return main()


class TestP23RetrievalHitrate:
    def test_hit_at_3_above_threshold(self, hit_result):
        assert hit_result["hit@3"] / hit_result["n_problems"] >= 0.75

    def test_vocabulary_fix_2017B(self, hit_result):
        r = next(r_ for r_ in hit_result["rows"] if r_["problem"] == "2017_B")
        assert r["gt_rank"] == 1, "mc-ols 应经 regression 词表命中 rank=1"

    def test_sample_size_fix_2022C(self, hit_result):
        r = next(r_ for r_ in hit_result["rows"] if r_["problem"] == "2022_C")
        assert r["gt_rank"] == 1, "mc-kmeans 应支持 small 样本命中 rank=1"

    def test_coverage_gap_2024A_recorded(self, hit_result):
        r = next(r_ for r_ in hit_result["rows"] if r_["problem"] == "2024_A")
        assert r["gt_rank"] is None, "2024_A 为卡池覆盖缺口（非检索 bug）"

    def test_retriever_regression(self):
        """修复后知识检索语义不回归：DP/排队/数值 PDE 卡仍可按题型命中。"""
        kr = KnowledgeRetriever(str(REPO / "core" / "knowledge"))
        cases = [
            ({"problem_types": ["sequential_decision"]}, "mc-dp"),
            ({"problem_types": ["random_service_system"]}, "mc-queuing-theory"),
            ({"problem_types": ["heat_transfer"]}, "mc-numerical-pde"),
            ({"problem_types": ["clustering"], "has_data": True,
              "sample_size": "small"}, "mc-kmeans"),
        ]
        for feats, expect in cases:
            top = [rec.card.card_id for rec in kr.recommend(feats, top_k=5)]
            assert expect in top, f"{expect} not in {top}"
