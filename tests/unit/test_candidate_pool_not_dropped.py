#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADR-0016 Step 2 守卫测试：落选候选不得静默丢弃。

缺口（机器核验）：`handlers.py:1876-1879` 的 `do_experiment_design` 只取 `cands[0]`，
其余候选（含全部 innovation 候选）被直接丢弃 —— 它们的 `required_experiments` 与
创新验证要求**从不进入实验计划**，等于「探索出来的候选静默消失」。

本测试锁：**落选候选的验证义务必须进入计划**（以 `候选方案要求[<cand_id>]` 标注），
且创新候选的 `创新验证[<pattern_id>]` 要求同样保留。

刻意**不**锁「落选候选被执行」：core 是 LLM-free，方法组合候选没有 MODEL_IR，
`skeleton_mir` 明确不编造 variables/equations（construction_status=pending_model_spec，
不可执行）。为凑「多候选」而硬造 MIR 只会得到一批执行必 FAIL 的假候选 ——
ADR-0016 决策 4 已禁止。能否真执行，取决于候选是否携带可执行 MIR。

运行: python -m pytest tests/unit/test_candidate_pool_not_dropped.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import pytest  # noqa: E402

from modeling_harness.runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402
from modeling_harness.runtime.modeling.candidates import (  # noqa: E402
    Candidate,
    InnovationCandidate,
)
from modeling_harness.runtime.modeling.planner import ExperimentPlanner  # noqa: E402

KNOWLEDGE_ROOT = REPO / "src" / "modeling_harness" / "knowledge"
BASE_CARD = "mc-topsis"


@pytest.fixture
def planner():
    return ExperimentPlanner(KnowledgeRetriever(KNOWLEDGE_ROOT))


def _baseline_cand() -> Candidate:
    return Candidate(
        candidate_id="CA001-A", kind="baseline", composition=[BASE_CARD],
        base_card=BASE_CARD, rationale="top1 方法学基线", score=7,
        required_experiments=["必做对照 A"])


def _improved_cand() -> Candidate:
    return Candidate(
        candidate_id="CA001-B", kind="improved",
        composition=[BASE_CARD, "mc-entropy-weight"],
        base_card=BASE_CARD, rationale="主方法 + 推荐增强", score=9,
        required_experiments=["必做对照 B"])


def _innovation_cand() -> Candidate:
    inno = InnovationCandidate(
        pattern_id="ip-pareto-select", name="帕累托前沿选型",
        base_method=BASE_CARD, modification="保留帕累托前沿",
        expected_benefit="折衷可见", risk=["前沿过宽"],
        required_evidence=["前沿 vs 单点的对照"],
        validation_protocol=["同 seeds 配对比较"],
        novelty_level="high", implementation_cost="medium",
        competition_fit="high", status="hypothesis")
    return Candidate(
        candidate_id="CA001-D", kind="innovation",
        composition=[BASE_CARD, "+innovation:ip-pareto-select"],
        base_card=BASE_CARD, rationale="主方法 + 创新模式", score=8,
        required_experiments=["必做对照 D"], innovations=[inno])


def test_losing_candidates_contribute_entries(planner):
    """核心 RED：落选候选的 required_experiments 必须进计划，而不是消失。"""
    top, *rest = _baseline_cand(), _improved_cand(), _innovation_cand()
    plan = planner.plan_from_candidate(top, "Q001")
    extra = planner.extra_entries_from_candidates(rest, plan)
    purposes = [e.purpose for e in extra]
    assert any("CA001-B" in p and "必做对照 B" in p for p in purposes), purposes
    assert any("CA001-D" in p and "必做对照 D" in p for p in purposes), purposes


def test_losing_innovation_requirements_survive(planner):
    """落选的**创新**候选：其创新验证要求不得湮没。"""
    top = _baseline_cand()
    plan = planner.plan_from_candidate(top, "Q001")
    extra = planner.extra_entries_from_candidates([_innovation_cand()], plan)
    joined = " | ".join(e.purpose for e in extra)
    assert "ip-pareto-select" in joined, joined
    assert "前沿 vs 单点的对照" in joined, joined


def test_no_duplicate_against_main_plan(planner):
    """与主计划已计入的 purpose 不得重复。"""
    top = _baseline_cand()
    plan = planner.plan_from_candidate(top, "Q001")
    extra_first = planner.extra_entries_from_candidates([_improved_cand()], plan)
    plan.entries.extend(extra_first)
    extra_again = planner.extra_entries_from_candidates([_improved_cand()], plan)
    assert extra_again == [], "重复调用产生了重复条目"


def test_empty_candidate_list_is_noop(planner):
    plan = planner.plan_from_candidate(_baseline_cand(), "Q001")
    assert planner.extra_entries_from_candidates([], plan) == []
