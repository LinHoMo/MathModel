#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Research Quality Contract（P9-1）—— 质量判定统一契约。

设计要点（P9 硬约束）:
* **不是分数**：QualityReport 不产生 0.82 式黑箱总分，只产生可追溯 findings。
* **四态复用**：PASS / WEAK / FAIL / UNKNOWN——与 Evidence Gate / JudgeCritic
  同一状态集合，不创造第五种状态（P9-1 红线）。
* **全量可追溯**：每条 finding 必须携带 subject（对象类型+ID）与 refs
  （evidence / artifact / knowledge / decision），能回答"为什么、依据什么"。
* **确定性**：全部规则为显式确定性检查，零 LLM（P9 原则 9）。
* **反馈动作**：finding 携带 recommended_action，映射到 P7 已冻结的
  rerun / recompute / reset_question / retry 语义，不新造 rerun 语义。

配套文档: docs/architecture/RESEARCH_QUALITY_CONTRACT.md
权威消费方: core/validators/quality/evaluators.py + aggregator.py
"""

from __future__ import annotations

from dataclasses import dataclass, field

# P9-1：状态集合（冻结，禁止扩充）
QUALITY_STATUSES = ("PASS", "WEAK", "FAIL", "UNKNOWN")
PASS, WEAK, FAIL, UNKNOWN = QUALITY_STATUSES

# 七维（P9-2）：每维产生 findings，不是七个固定分数
DIMENSIONS = (
    "problem",           # Q1 Problem Validity
    "model",             # Q2 Model Validity
    "experiment",        # Q3 Experiment Validity
    "evidence",          # Q4 Evidence Sufficiency
    "decision",          # Q5 Decision Validity
    "innovation",        # Q6 Innovation Validity
    "reproducibility",   # Q7 Reproducibility
)

# finding 严重度（与 Gate 的 fail/weak 对齐 + unknown）
SEVERITIES = ("fail", "weak", "unknown", "info")

# subject 类型（七类对象 + 计划）
SUBJECT_TYPES = ("problem", "question", "model", "experiment", "evidence",
                 "claim", "decision", "innovation", "experiment_plan",
                 "reproducibility", "quality")

# recommended_action 的合法动作域（映射 P7 已冻结语义，禁止新造）
ACTIONS = ("none", "rerun_model_selection", "refine_experiment_plan",
           "rerun_experiment", "rebuild_evidence", "request_evidence",
           "recompute", "reset_question", "record_failure", "review_decision")

_STATUS_RANK = {PASS: 0, UNKNOWN: 1, WEAK: 2, FAIL: 3}


def worst_status(a: str, b: str) -> str:
    """四态合并：FAIL > WEAK > UNKNOWN > PASS。"""
    return a if _STATUS_RANK.get(a, 0) >= _STATUS_RANK.get(b, 0) else b


@dataclass
class QualityFinding:
    """单条质量发现——最小可追溯单元。"""
    dimension: str                       # DIMENSIONS 之一
    severity: str                        # fail / weak / unknown / info
    status: str                          # PASS / WEAK / FAIL / UNKNOWN
    subject_type: str                    # SUBJECT_TYPES 之一
    subject_id: str                      # 对象 ID（artifact id / decision id / …）
    reason: str                          # 为什么（人可读）
    evidence_refs: list[str] = field(default_factory=list)   # evidence 关系/闭包 ids
    artifact_refs: list[str] = field(default_factory=list)   # 关联 artifact ids
    knowledge_refs: list[dict] = field(default_factory=list) # [{id, version}]
    decision_refs: list[str] = field(default_factory=list)
    recommended_action: str = "none"     # ACTIONS 之一
    check_id: str = ""                   # 规则编号（M1/E5/I3/D2…，审计用）

    def __post_init__(self):
        if self.dimension not in DIMENSIONS:
            raise ValueError(f"finding.dimension 非法: {self.dimension!r}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"finding.severity 非法: {self.severity!r}")
        if self.status not in QUALITY_STATUSES:
            raise ValueError(f"finding.status 非法: {self.status!r}")
        if self.subject_type not in SUBJECT_TYPES:
            raise ValueError(f"finding.subject_type 非法: {self.subject_type!r}")
        if self.recommended_action not in ACTIONS:
            raise ValueError(f"finding.recommended_action 非法: "
                             f"{self.recommended_action!r}（合法: {ACTIONS}）")

    @property
    def is_blocker(self) -> bool:
        return self.severity == "fail"

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "dimension", "severity", "status", "subject_type", "subject_id",
            "reason", "evidence_refs", "artifact_refs", "knowledge_refs",
            "decision_refs", "recommended_action", "check_id")}


@dataclass
class QualityDimensionReport:
    """单维度报告：该维度的状态由其 findings 推导（无独立分数）。"""
    dimension: str
    findings: list[QualityFinding] = field(default_factory=list)

    @property
    def status(self) -> str:
        st = PASS
        for f in self.findings:
            if f.severity == "fail":
                st = worst_status(st, FAIL)
            elif f.severity == "weak":
                st = worst_status(st, WEAK)
            elif f.severity == "unknown":
                st = worst_status(st, UNKNOWN)
        return st

    def as_dict(self) -> dict:
        return {"dimension": self.dimension, "status": self.status,
                "findings": [f.as_dict() for f in self.findings]}


@dataclass
class QualityReport:
    """聚合报告（P9-9）：overall_status 由维度推导，无黑箱总分。"""
    dimensions: dict[str, QualityDimensionReport] = field(default_factory=dict)
    subject: str = ""                    # 评估对象（项目名/问题域）

    # ------------------------------------------------------------ 派生

    @property
    def findings(self) -> list[QualityFinding]:
        return [f for d in self.dimensions.values() for f in d.findings]

    @property
    def overall_status(self) -> str:
        st = PASS
        for d in self.dimensions.values():
            st = worst_status(st, d.status)
        return st

    @property
    def blockers(self) -> list[QualityFinding]:
        return [f for f in self.findings if f.is_blocker]

    @property
    def warnings(self) -> list[QualityFinding]:
        return [f for f in self.findings if f.severity == "weak"]

    @property
    def unknowns(self) -> list[QualityFinding]:
        return [f for f in self.findings if f.severity == "unknown"]

    @property
    def recommended_actions(self) -> list[dict]:
        """去重后的行动清单（FAIL/WEAK finding 的动作 + subject）。"""
        seen, actions = set(), []
        for f in self.findings:
            if f.recommended_action == "none" or not f.is_blocker and \
                    f.severity != "weak":
                continue
            key = (f.recommended_action, f.subject_type, f.subject_id)
            if key not in seen:
                seen.add(key)
                actions.append({"action": f.recommended_action,
                                "subject_type": f.subject_type,
                                "subject_id": f.subject_id,
                                "reason": f.reason,
                                "check_id": f.check_id})
        return actions

    def as_dict(self) -> dict:
        return {
            "subject": self.subject,
            "overall_status": self.overall_status,
            "dimensions": {k: v.as_dict() for k, v in self.dimensions.items()},
            "blockers": [f.as_dict() for f in self.blockers],
            "warnings": [f.as_dict() for f in self.warnings],
            "unknowns": [f.as_dict() for f in self.unknowns],
            "recommended_actions": self.recommended_actions,
        }
