#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Writing Patterns（P11-6）—— 优秀论文的论证模式蒸馏（非 style-RAG）。

每类模式只描述"论证结构"：preconditions / structure / required_evidence /
failure_mode / competition_fit。只能影响 Narrative/Expression，
**不能改变 Research Truth**（P11 硬约束）。
purpose 与 ParagraphPurpose 对齐（patterns_for 按段落 purpose 选择）。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WritingPattern:
    pattern_id: str
    name: str
    purpose: str                              # ParagraphPurpose 之一
    preconditions: list[str]                  # 触发前提（事实层条件）
    structure: list[str]                    # 段内论证顺序（ArgumentUnit 槽位）
    required_evidence: list[str]
    failure_mode: str
    competition_fit: list[str] = field(default_factory=list)
    good_example_summary: str = ""


WRITING_PATTERNS: dict[str, WritingPattern] = {
    p.pattern_id: p for p in [
        WritingPattern(
            pattern_id="WP-001", name="problem_to_model_transition",
            purpose="method_choice",
            preconditions=["选型决策已登记"],
            structure=["赛题约束的抽象化说明", "为什么该类模型适配该约束",
                       "模型选择的一句话依据（引用选型决策）"],
            required_evidence=["selection_decision"],
            failure_mode="模型介绍与问题脱节（堆背景）",
            competition_fit=["cumcm", "mcm"],
            good_example_summary="先讲问题本质结构，再讲模型为何匹配，一段完成过渡"),
        WritingPattern(
            pattern_id="WP-002", name="baseline_limitation_improvement",
            purpose="comparison",
            preconditions=["baseline_comparison", "improvement 数值"],
            structure=["基线方法与结果", "基线局限（数据支撑）",
                       "改进点与改进量", "改进的适用边界"],
            required_evidence=["baseline_comparison"],
            failure_mode="只报改进量不讲基线局限，显得无对比意义",
            competition_fit=["cumcm", "mcm"],
            good_example_summary="改进永远相对于被指明局限的基线陈述"),
        WritingPattern(
            pattern_id="WP-003", name="result_interpretation",
            purpose="interpretation",
            preconditions=["实验结果", "decision_rule 判定"],
            structure=["观察到的结果", "与假设的关系",
                       "可能的机制解释（标记为解释）", "实际含义"],
            required_evidence=["experiment_result"],
            failure_mode="有数字无解释，或把推测写成事实",
            competition_fit=["cumcm", "mcm"],
            good_example_summary="结果→含义→机制（标注 possible explanation）"),
        WritingPattern(
            pattern_id="WP-004", name="sensitivity_narrative",
            purpose="sensitivity",
            preconditions=["sensitivity 证据"],
            structure=["扰动设计", "关键参数与结论稳定性", "不稳定区间的坦承"],
            required_evidence=["sensitivity"],
            failure_mode="灵敏度变成表格堆砌，无结论稳定性陈述",
            competition_fit=["cumcm"],
            good_example_summary="灵敏度回答'结论稳不稳'，不是'我做了扰动'"),
        WritingPattern(
            pattern_id="WP-005", name="multi_question_bridge",
            purpose="transition",
            preconditions=["跨问题依赖（DAG depends_on）"],
            structure=["上一问给出的可复用产物", "本问如何消费该产物",
                       "边界差异"],
            required_evidence=["question_dependency"],
            failure_mode="'下面研究问题二'式无信息过渡",
            competition_fit=["cumcm", "mcm"],
            good_example_summary="过渡句必须携带产物继承关系"),
        WritingPattern(
            pattern_id="WP-006", name="innovation_claim",
            purpose="summary",
            preconditions=["InnovationCandidate", "validated finding"],
            structure=["基线做法", "本研究的修改点", "改进证据",
                       "未声称的部分"],
            required_evidence=["validated_finding"],
            failure_mode="把'用了新方法'当创新，无改进证据",
            competition_fit=["mcm"],
            good_example_summary="创新=修改点+可测改进+边界声明"),
        WritingPattern(
            pattern_id="WP-007", name="limitation_calibration",
            purpose="limitation",
            preconditions=["assumption 清单"],
            structure=["假设的适用边界", "证据不支持的推广", "后续改进方向"],
            required_evidence=["assumptions"],
            failure_mode="模板化'本文仍有不足'，无具体边界",
            competition_fit=["cumcm", "mcm"],
            good_example_summary="局限必须指明哪条证据不支撑哪种推广"),
    ]}


def patterns_for(purpose: str, competition: str | None = None,
                 evidence_ready: dict | None = None) -> list[WritingPattern]:
    """按段落 purpose 与竞赛过滤可用模式（确定性）。"""
    out = []
    for p in WRITING_PATTERNS.values():
        if p.purpose != purpose:
            continue
        if competition and p.competition_fit and \
                competition not in p.competition_fit:
            continue
        ev = evidence_ready or {}
        if any(not ev.get(k) for k in p.required_evidence):
            continue
        out.append(p)
    return out
