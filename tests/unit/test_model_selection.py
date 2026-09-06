"""P3 Modeling 层测试：MethodArena 选型 + ExperimentPlanner 规划。

运行: python -m pytest tests/unit/test_model_selection.py -q
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.decisions.log import DecisionLog
from runtime.knowledge.retriever import KnowledgeRetriever
from runtime.modeling.planner import ExperimentPlanner, PlannerError
from runtime.modeling.selection import MethodArena, SelectionError

KNOWLEDGE_ROOT = REPO / "core" / "knowledge"


@pytest.fixture
def retriever():
    return KnowledgeRetriever(KNOWLEDGE_ROOT)


@pytest.fixture
def decisions(tmp_path):
    return DecisionLog(tmp_path / "decisions.json")


class TestMethodArena:
    def test_select_returns_shortlist(self, retriever, decisions):
        arena = MethodArena(retriever, decisions)
        out = arena.select("Q001", {"problem_types": ["evaluation", "ranking"],
                                    "has_data": True})
        assert out.chosen.startswith("mc-")
        assert len(out.shortlist) >= 2
        assert out.decision_id == "D001"
        # alternatives 保留了落选者（评委问"为什么不用 X"有答案）
        dec = decisions.get("D001")
        assert len(dec.alternatives) >= 1
        assert dec.criteria
        assert dec.reversible

    def test_decision_recorded_in_log(self, retriever, decisions):
        arena = MethodArena(retriever, decisions)
        arena.select("Q001", {"problem_types": ["optimization"],
                              "objectives": 2})
        rows = decisions.query(question_type="optimization")
        assert len(rows) == 1
        assert rows[0]["chosen"].startswith("mc-")

    def test_no_candidates_raises(self, retriever, decisions):
        arena = MethodArena(retriever, decisions)
        with pytest.raises(SelectionError, match="无匹配"):
            arena.select("Q001", {"problem_types": ["nonexistent"]})

    def test_prior_active_decision_consistency_note(self, retriever, decisions):
        arena = MethodArena(retriever, decisions)
        arena.select("Q001", {"problem_types": ["optimization"], "objectives": 2})
        # 同 question 重新选型且换了方法 → 冲突提示
        out2 = MethodArena(retriever, decisions).select(
            "Q001", {"problem_types": ["optimization"]})
        assert any("冲突" in n for n in out2.notes)

    def test_prior_invalidated_decision_not_conflicting(self, retriever, decisions):
        arena = MethodArena(retriever, decisions)
        out1 = arena.select("Q001", {"problem_types": ["optimization"],
                                     "objectives": 2})
        out2 = MethodArena(retriever, decisions).select(
            "Q001", {"problem_types": ["optimization"]})
        # P9.5 R3 修复后：重选型自动失效旧决策（无需手动 invalidate）
        assert decisions.decisions[out1.decision_id].status == "invalidated"
        out3 = MethodArena(retriever, decisions).select(
            "Q001", {"problem_types": ["optimization"]})
        assert not any("冲突" in n for n in out3.notes)
        # 历史决策视图包含被推翻记录（superseded_note）
        assert any("superseded_note" in d for d in out3.prior_decisions)

    def test_no_decision_log_still_selects(self, retriever):
        arena = MethodArena(retriever, None)
        out = arena.select("Q001", {"problem_types": ["evaluation"]})
        assert out.chosen
        assert out.decision_id == ""


class TestExperimentPlanner:
    def test_plan_contains_validation_checks(self, retriever):
        planner = ExperimentPlanner(retriever)
        plan = planner.plan("Q001", ["mc-topsis", "mc-entropy-weight"])
        # 两张卡各有 validation 条目 → required_checks 合并
        assert any("mc-topsis" in c for c in plan.required_checks)
        assert any("mc-entropy-weight" in c for c in plan.required_checks)
        assert any("Spearman" in c or "敏感性" in c for c in plan.required_checks)

    def test_plan_contains_failure_guards(self, retriever):
        planner = ExperimentPlanner(retriever)
        plan = planner.plan("Q001", ["mc-topsis"])
        # TOPSIS 的关联失败记忆进入防线
        assert any("归一" in g for g in plan.preflight_guards)
        assert any(f["failure_id"] == "fm-topsis-no-normalization"
                   for f in plan.failure_watchlist)
        # watchlist 带 detection（实验后自检动作）
        assert all(f["detection"] for f in plan.failure_watchlist)

    def test_plan_baseline_always_present(self, retriever):
        planner = ExperimentPlanner(retriever)
        plan = planner.plan("Q001", ["mc-ga"])
        assert plan.has_baseline
        assert any("朴素基线" in b for b in plan.baseline_comparison)

    def test_plan_with_explicit_baseline_card(self, retriever):
        planner = ExperimentPlanner(retriever)
        plan = planner.plan("Q001", ["mc-ga"], baseline_card_id="mc-sa")
        assert any("mc-sa" in b for b in plan.baseline_comparison)

    def test_plan_sensitivity_default(self, retriever):
        planner = ExperimentPlanner(retriever)
        plan = planner.plan("Q001", ["mc-pca"])
        assert plan.has_sensitivity

    def test_plan_unknown_card_raises(self, retriever):
        planner = ExperimentPlanner(retriever)
        with pytest.raises(PlannerError, match="不存在"):
            planner.plan("Q001", ["mc-ghost"])

    def test_plan_empty_cards_raises(self, retriever):
        with pytest.raises(PlannerError, match="为空"):
            ExperimentPlanner(retriever).plan("Q001", [])

    def test_plan_as_dict_machine_readable(self, retriever):
        plan = ExperimentPlanner(retriever).plan(
            "Q001", ["mc-topsis"], baseline_card_id="mc-ahp")
        d = plan.as_dict()
        for key in ("question", "methods", "required_checks",
                    "preflight_guards", "failure_watchlist",
                    "baseline_comparison", "sensitivity"):
            assert key in d
        assert d["methods"] == ["mc-topsis"]


class TestArenaPlannerIntegration:
    def test_arena_output_feeds_planner(self, retriever, decisions):
        """选型 → 规划 的端到端链路（model_selection → experiment_design）。"""
        arena = MethodArena(retriever, decisions)
        out = arena.select("Q001", {"problem_types": ["evaluation", "ranking"],
                                    "has_data": True}, top_k=3)
        methods = [out.chosen] + out.chosen_card.get("often_combined_with", [])[:1]
        methods = [m for m in methods if m in retriever.cards]
        plan = ExperimentPlanner(retriever).plan(
            "Q001", methods,
            baseline_card_id=out.shortlist[1]["card_id"] if len(out.shortlist) > 1 else None)
        assert plan.methods[0] == out.chosen
        assert plan.required_checks
