#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Expression Contract（P11-1）—— Research Layer 与 Expression Layer 的分界。

铁律（P11 硬约束 5–12）:
    LLM 可以改变: wording / 句式 / 段序（IR 允许内）/ transition / 解释措辞 /
                  详略 / 术语一致性
    LLM 不可以改变: claim 含义 / 数值 / 证据关系 / 模型身份 / 实验结果 /
                    决策结论 / 引用身份 / finding 状态

ExpressionInput 携带**最小权限**的 ExpressionContext（P11-10）：只给当前段落
需要的事实，不给全项目、不给 invalidated 历史。ExpressionOutput 必须可反查来源。
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 表达层可变更 / 不可变更清单（契约冻结）
LLM_MAY_CHANGE = ("wording", "sentence_structure", "paragraph_ordering",
                  "transition", "explanation_phrasing", "concision",
                  "terminology_consistency")
LLM_MAY_NOT_CHANGE = ("claim_meaning", "numeric_value", "evidence_relation",
                      "model_identity", "experiment_result", "decision_outcome",
                      "citation_identity", "finding_status")


@dataclass
class ExpressionContext:
    """最小权限上下文：渲染一段话所能知道的全部。"""
    paragraph_purpose: str
    section_purpose: str
    allowed_claims: list[dict] = field(default_factory=list)    # [{id, text, status}]
    allowed_findings: list[dict] = field(default_factory=list)
    allowed_evidence: list[str] = field(default_factory=list)   # result ids
    allowed_numbers: list[str] = field(default_factory=list)   # 可出现的数字全集
    allowed_references: list[str] = field(default_factory=list)  # bib keys
    permitted_metrics: list[str] = field(default_factory=list)
    figure_bindings: list[dict] = field(default_factory=list)
    competition_context: dict = field(default_factory=dict)
    style_constraints: dict = field(default_factory=dict)   # {forbidden_terms, ...}
    forbidden_inferences: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "paragraph_purpose", "section_purpose", "allowed_claims",
            "allowed_findings", "allowed_evidence", "allowed_numbers",
            "allowed_references", "permitted_metrics", "figure_bindings",
            "competition_context", "style_constraints", "forbidden_inferences")}


@dataclass
class ExpressionInput:
    """一次受控表达请求：ParagraphPlan + 裁剪后的 Context。"""
    paragraph_plan: dict                                   # ParagraphPlan.as_dict()
    context: ExpressionContext
    renderer_name: str = "deterministic"     # deterministic / llm:<model>

    def as_dict(self) -> dict:
        return {"paragraph_plan": self.paragraph_plan,
                "context": self.context.as_dict(),
                "renderer_name": self.renderer_name}


@dataclass
class ExpressionOutput:
    """渲染结果 + 可反查来源（FactChecker/后验校验消费）。"""
    text: str
    renderer_name: str
    source_claim_ids: list[str] = field(default_factory=list)
    source_finding_ids: list[str] = field(default_factory=list)
    source_evidence_ids: list[str] = field(default_factory=list)
    rendered_numbers: list[str] = field(default_factory=list)
    rendered_citations: list[str] = field(default_factory=list)
    wording_violations: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    disposition: str = "accept"            # accept / hard_reject / deterministic_repair / rerender

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "text", "renderer_name", "source_claim_ids", "source_finding_ids",
            "source_evidence_ids", "rendered_numbers", "rendered_citations",
            "wording_violations", "violations", "disposition")}


# ============================================================
# P11-10 措辞校准：证据强度 → 允许措辞（禁止无证据强词）
# ============================================================

EVIDENCE_LEVELS = ("strong", "moderate", "weak", "unknown")

_ALLOWED_PHRASING = {
    "strong": ["结果表明", "实验证据支持"],
    "moderate": ["结果显示", "在当前实验设置下表现更好"],
    "weak": ["提示", "可能", "初步表明"],
    "unknown": [],
}

# 禁止无条件出现的强断言词（除非 evidence_level=strong 且对应条件成立）
FORBIDDEN_SUPERLATIVES = ("optimal", "best", "proves", "generalizable",
                          "显著", "最优", "完胜", "证明")


def evidence_level_of(claim_status: str, has_baseline: bool,
                      has_robustness: bool) -> str:
    """claim 生命周期状态 + 对照/稳健性证据 → 证据强度。"""
    if claim_status != "active":
        return "unknown"
    if has_baseline and has_robustness:
        return "strong"
    if has_baseline:
        return "moderate"
    return "weak"


def allowed_phrasing(level: str) -> list[str]:
    if level not in EVIDENCE_LEVELS:
        raise ValueError(f"evidence level 非法: {level!r}")
    return list(_ALLOWED_PHRASING[level])


def check_wording(text: str, level: str, significance: bool = False) -> list[str]:
    """P11-10 校准检查：返回违规词列表（空 = 通过）。

    unknown 证据不得写成结论；"显著/最优/证明/best/optimal" 属硬禁词——
    仅 level=strong 且存在真实显著性检验（significance=True）时允许"显著"；
    strong 本身也只解锁"结果表明"，不解锁 best/证明。
    """
    violations = []
    if level == "unknown":
        if text.strip():
            violations.append("unknown 证据不得写成结论")
        return violations
    hard = ("optimal", "best", "proves", "generalizable", "最优", "完胜",
            "证明")
    for w in hard:
        if w in text:
            violations.append(f"硬禁强断言词（无真实检验支撑）: {w}")
    if "显著" in text and not (level == "strong" and significance):
        violations.append("'显著'需真实显著性检验支撑")
    if level == "weak" and not any(p in text for p in allowed_phrasing(level)) \
            and text.strip():
        violations.append("weak 级证据须使用限定措辞（提示/可能/初步）")
    return violations


# ============================================================
# P11-19 Renderer 失败语义（不是所有错误都重调模型）
# ============================================================

RENDERER_FAILURES = ("hallucinated_number", "hallucinated_citation",
                     "unsupported_claim", "format_failure", "style_failure")


def classify_renderer_failure(violations: list[str]) -> str:
    """后验违规 → 处置语义：
    幻觉数字/引用/无据断言 → hard reject；格式 → 确定性修复；风格 → rerender。
    """
    joined = ";".join(violations)
    if "number" in joined or "citation" in joined or "claim" in joined:
        return "hard_reject"
    if "format" in joined:
        return "deterministic_repair"
    return "rerender"
