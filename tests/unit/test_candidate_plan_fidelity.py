#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADR-0016 守卫测试：候选序列化必须保真 —— 创新候选不得在重建处静默降级。

缺口（机器核验，见 ADR-0016 Context）：
  handlers.py:1880-1885 重建 Candidate(...) 时未传 innovations，而该字段默认 []，
  导致 planner.py:184 的创新专用分支恒空转 —— decision_rule=gain > cost /
  failure_detection=inno.risk[0] / baseline="未采用创新的 <card> 基线" 永不生成，
  创新要求只以普通字符串残留在 required_experiments 里（降级为「候选方案要求」）。

本测试锁两件事：
  1. `Candidate.as_dict()` / `Candidate.from_dict()` 往返**不丢字段**
     （innovations / validations / dependencies / assumptions / risks / score_detail）；
  2. 经 from_dict 重建的候选，其创新要求**真的**变成 plan 里的「创新验证[…]」条目。

运行: python -m pytest tests/unit/test_candidate_plan_fidelity.py -q
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


def _innovation_candidate() -> Candidate:
    """构造一个「创新候选」，字段填满以便往返比对。"""
    inno = InnovationCandidate(
        pattern_id="ip-pareto-select",
        name="帕累托前沿选型",
        base_method=BASE_CARD,
        modification="在选型阶段保留帕累托前沿而非单点最优",
        expected_benefit="在效率与稳健性之间给出可选折衷",
        risk=["前沿过宽导致结论不锐利"],
        required_evidence=["帕累托前沿 vs 单点最优的对照实验"],
        validation_protocol=["同一组 seeds 下逐对比较"],
        novelty_level="high",
        implementation_cost="medium",
        competition_fit="high",
        knowledge_version=2,
        source_refs=["case-2023B"],
        status="hypothesis")
    return Candidate(
        candidate_id="CA001-D",
        kind="innovation",
        composition=[BASE_CARD, "+innovation:ip-pareto-select"],
        base_card=BASE_CARD,
        rationale="主方法 + 创新模式「帕累托前沿选型」",
        score=9,
        score_detail={"innovation": 8, "evidence_cost": 3},
        risks=[{"source": "knowledge_card", "id": BASE_CARD,
                "level": "medium", "title": "归一化缺失"}],
        required_experiments=["必做对照 1"],
        innovations=[inno],
        knowledge_refs=[{"id": BASE_CARD, "version": 1}],
        validations=[{"obligation": "归一化检查", "source_card": BASE_CARD}],
        dependencies=["scipy"],
        assumptions=[{"assumption": "指标可比", "source_card": BASE_CARD}])


# --------------------------------------------------------------- 往返保真
def test_roundtrip_preserves_innovations():
    """核心 RED：重建后 innovations 必须还在（否则 planner 的创新分支恒空转）。"""
    src = _innovation_candidate()
    rebuilt = Candidate.from_dict(src.as_dict())
    assert rebuilt.innovations, "重建丢失 innovations —— 创新分支将永不触发"
    assert rebuilt.innovations[0].pattern_id == "ip-pareto-select"
    assert rebuilt.innovations[0].required_evidence == [
        "帕累托前沿 vs 单点最优的对照实验"]
    assert rebuilt.innovations[0].validation_protocol == [
        "同一组 seeds 下逐对比较"]
    assert rebuilt.innovations[0].risk == ["前沿过宽导致结论不锐利"]
    assert rebuilt.innovations[0].novelty_level == "high"


def test_roundtrip_preserves_obligations_and_meta():
    """validations / dependencies / assumptions / risks / score_detail 同样不得丢。"""
    src = _innovation_candidate()
    rebuilt = Candidate.from_dict(src.as_dict())
    assert rebuilt.candidate_id == src.candidate_id
    assert rebuilt.kind == src.kind
    assert rebuilt.composition == src.composition
    assert rebuilt.base_card == src.base_card
    assert rebuilt.score == src.score
    assert rebuilt.score_detail == src.score_detail
    assert rebuilt.risks == src.risks
    assert rebuilt.required_experiments == src.required_experiments
    assert rebuilt.validations == src.validations
    assert rebuilt.dependencies == src.dependencies
    assert rebuilt.assumptions == src.assumptions
    assert rebuilt.knowledge_refs == src.knowledge_refs


def test_from_dict_ignores_derived_reasoning_key():
    """as_dict() 里的 reasoning 是派生展示字段，from_dict 必须容忍它（不炸）。"""
    d = _innovation_candidate().as_dict()
    assert "reasoning" in d
    rebuilt = Candidate.from_dict(d)
    assert rebuilt.candidate_id == d["candidate_id"]


def test_from_dict_tolerates_missing_optional_fields():
    """最小 dict（仅必填）也能重建，可选字段回落默认值。"""
    rebuilt = Candidate.from_dict({
        "candidate_id": "CA009-A", "kind": "baseline",
        "composition": [BASE_CARD], "base_card": BASE_CARD,
        "rationale": "最小候选"})
    assert rebuilt.innovations == []
    assert rebuilt.validations == []
    assert rebuilt.assumptions == []
    assert rebuilt.dependencies == []


# ------------------------------------------------- 创新条目真的进 plan（行为）
@pytest.fixture
def planner():
    return ExperimentPlanner(KnowledgeRetriever(KNOWLEDGE_ROOT))


def test_innovation_requirements_become_plan_entries(planner):
    """重建后的候选，其创新要求必须变成「创新验证[…]」条目（不是普通候选要求）。"""
    rebuilt = Candidate.from_dict(_innovation_candidate().as_dict())
    plan = planner.plan_from_candidate(rebuilt, "Q001")
    purposes = [e.purpose for e in plan.entries]
    assert any(p.startswith("创新验证[ip-pareto-select]") for p in purposes), \
        f"未生成创新验证条目；实际条目={purposes}"
    inno_entries = [e for e in plan.entries
                    if e.purpose.startswith("创新验证[")]
    assert inno_entries, "创新条件条目缺失（重建丢 innovations 时必然如此）"
    assert all(e.decision_rule.metric == "innovation_gain"
               for e in inno_entries)
    assert any(e.failure_detection == "前沿过宽导致结论不锐利"
               for e in inno_entries), "创新风险未落进 failure_detection"
