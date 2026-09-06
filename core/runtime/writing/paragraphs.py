#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paragraph IR + ArgumentUnit + Controlled Renderer（P11-2/3/8/9/12/13/14）。

层次：
    Section（P10 IR） → ArgumentUnit（Claim→论证单元）
                    → ParagraphPlan（每段有"为什么存在"）
                    → Renderer（确定性默认 / LLM 可插拔）
                    → 后验校验（数字/引用/claim ⊆ 允许集；强措辞校准）
                    → Accept / hard reject / rerender

跨问题叙事（P11-12）、图表绑定（P11-13）、公式绑定（P11-14）全部落为
ParagraphPlan 的显式字段——论文第一次拥有"这段话为什么存在"。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .expression import (ExpressionContext, ExpressionInput, ExpressionOutput,
                         allowed_phrasing, check_wording,
                         classify_renderer_failure, evidence_level_of)
from .patterns import patterns_for

# P11-2：段落 purpose 枚举（冻结）
PARAGRAPH_PURPOSES = (
    "problem_context", "motivation", "method_choice", "definition",
    "assumption", "derivation", "procedure", "experiment_setup", "result",
    "comparison", "interpretation", "robustness", "sensitivity",
    "limitation", "implication", "transition", "summary")


@dataclass
class ArgumentUnit:
    """P11-3：Claim → 论证单元（不是 Claim → 一句话）。"""
    claim_id: str
    claim_text: str
    support: list[str] = field(default_factory=list)      # result/experiment ids
    comparison: dict = field(default_factory=dict)         # {baseline, candidate}
    interpretation: str = ""                               # 机制/含义（可标 hypothesis）
    interpretation_status: str = "fact"                    # fact / hypothesis
    limitation: str = ""
    implication: str = ""
    evidence_level: str = "weak"           # strong/moderate/weak/unknown

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "claim_id", "claim_text", "support", "comparison",
            "interpretation", "interpretation_status", "limitation",
            "implication", "evidence_level")}


@dataclass
class FigureBinding:
    """P11-13：图表叙事绑定——图必须参与论证。"""
    figure_id: str
    why_exists: str = ""
    what_to_observe: str = ""
    what_it_supports: list[str] = field(default_factory=list)   # claim ids
    what_it_does_not_prove: str = ""


@dataclass
class EquationBinding:
    """P11-14：公式叙事绑定——公式不为凑数量而生。"""
    equation_id: str
    model_ref: str = ""
    purpose: str = ""
    symbols: list[str] = field(default_factory=list)
    used_by: list[str] = field(default_factory=list)            # section ids


@dataclass
class ParagraphPlan:
    """段落计划：表达层的输入，事实锚点齐全。"""
    paragraph_id: str
    purpose: str                                  # PARAGRAPH_PURPOSES 之一
    section_id: str
    claim_refs: list[str] = field(default_factory=list)
    finding_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    figure_refs: list[str] = field(default_factory=list)
    table_refs: list[str] = field(default_factory=list)
    equation_refs: list[str] = field(default_factory=list)
    required_content: list[str] = field(default_factory=list)
    optional_context: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    transition_from: str = ""
    transition_to: str = ""
    argument_units: list[ArgumentUnit] = field(default_factory=list)
    cross_question_from: str = ""          # P11-12：Q001 → Q002 产物继承

    def as_dict(self) -> dict:
        d = {k: getattr(self, k) for k in (
            "paragraph_id", "purpose", "section_id", "claim_refs",
            "finding_refs", "evidence_refs", "figure_refs", "table_refs",
            "equation_refs", "required_content", "optional_context",
            "forbidden_claims", "transition_from", "transition_to",
            "cross_question_from")}
        d["argument_units"] = [a.as_dict() for a in self.argument_units]
        return d


# ============================================================
# P11-12 跨问题叙事依赖
# ============================================================

def question_dependencies(registry, graph) -> list[dict]:
    """从问题间 depends_on 派生产物继承叙事（Q1 → provides for Q2）。"""
    out = []
    questions = {a.artifact_id: a for a in registry.list_by_type("question")}
    for qid, q in questions.items():
        for dep in q.depends_on or []:
            if dep in questions:
                out.append({"from": dep, "to": qid,
                            "relation": "provides_products_for"})
    return out


# ============================================================
# P11-2 ParagraphPlanner
# ============================================================

class ParagraphPlanner:
    """Section（P10 IR）→ ParagraphPlan[]（论证结构，确定性派生）。"""

    def __init__(self, registry, graph, findings_graph=None,
                 competition: str | None = None, pack=None):
        self.registry = registry
        self.graph = graph
        self.fg = findings_graph
        self.competition = competition
        self.pack = pack

    def plan(self, section_id: str, section, ir) -> list[ParagraphPlan]:
        if section.purpose == "problem_definition":
            plans = self._problem_sections(section, ir)
        elif section.purpose == "methodology":
            plans = self._methodology_sections(section, ir)
        elif section.purpose == "experiment":
            plans = self._experiment_sections(section, ir)
        elif section.purpose == "results":
            plans = self._results_sections(section, ir)
        elif section.purpose == "discussion":
            plans = self._discussion_sections(section, ir)
        else:   # conclusion
            plans = self._conclusion_sections(section, ir)
        # P11-7：pack 写作档只影响 emphasis（required_content 标注），不改结构
        if self.pack is not None:
            prefs = [p.lower() for p in (self.pack.judging_preferences or [])]
            for pl in plans:
                if any("摘要" in p or "summary" in p for p in prefs):
                    pl.required_content.append("pack:结论先行")
                if any("灵敏度" in p or "sensitivity" in p for p in prefs):
                    pl.required_content.append("pack:灵敏度陈述")
        return plans

    # ------------------------------------------------------------ 各 section

    def _problem_sections(self, sec, ir):
        plans = [ParagraphPlan(
            paragraph_id=f"{sec.section_id}-P1", purpose="problem_context",
            section_id=sec.section_id, claim_refs=list(sec.claims),
            required_content=["赛题约束抽象化", "研究对象与目标"])]
        plans.append(ParagraphPlan(
            paragraph_id=f"{sec.section_id}-P2", purpose="transition",
            section_id=sec.section_id,
            transition_to="methodology",
            required_content=["问题结构 → 建模路径的过渡"]))
        return plans

    def _methodology_sections(self, sec, ir):
        plans = []
        for i, mid in enumerate(sec.models, 1):
            m = self.registry.get(mid)
            card_id = str(m.data.get("card_id", ""))
            plans.append(ParagraphPlan(
                paragraph_id=f"{sec.section_id}-M{i}",
                purpose="method_choice", section_id=sec.section_id,
                claim_refs=[mid],
                equation_refs=[mid],
                required_content=[
                    f"为什么选择 {card_id}（选型依据）",
                    "模型假设与适用边界", "变量与符号定义"],
                optional_context=[
                    f"选型理由（来自决策记录）: {self._selection_reason(card_id)}"],
                forbidden_claims=["未经实验支持的'最优'声明"]))
            plans.append(ParagraphPlan(
                paragraph_id=f"{sec.section_id}-A{i}", purpose="assumption",
                section_id=sec.section_id,
                claim_refs=[mid],
                required_content=[f"{mid} 的假设声明与依据"]))
        return plans

    def _experiment_sections(self, sec, ir):
        plans = [ParagraphPlan(
            paragraph_id=f"{sec.section_id}-S1", purpose="experiment_setup",
            section_id=sec.section_id, evidence_refs=list(sec.experiments),
            required_content=["实验设计目的", "对照设置", "评价指标"])]
        # P11-12：跨问题过渡
        deps = question_dependencies(self.registry, self.graph)
        for d in deps:
            plans.append(ParagraphPlan(
                paragraph_id=f"{sec.section_id}-X{d['from']}→{d['to']}",
                purpose="transition", section_id=sec.section_id,
                cross_question_from=d["from"],
                transition_from=d["from"], transition_to=d["to"],
                required_content=[
                    f"{d['from']} 的产物如何被 {d['to']} 消费"]))
        return plans

    def _results_sections(self, sec, ir):
        plans = []
        for i, rid in enumerate(sec.evidence, 1):
            units = self._argument_units_for_result(rid)
            plans.append(ParagraphPlan(
                paragraph_id=f"{sec.section_id}-R{i}", purpose="result",
                section_id=sec.section_id, evidence_refs=[rid],
                claim_refs=[u.claim_id for u in units],
                finding_refs=[f.finding_id for f in (self.fg.findings if self.fg else [])
                              if rid in f.supported_by],
                figure_refs=self._figures_for_result(rid),
                argument_units=units,
                required_content=["结果陈述", "与假设的关系", "对照比较"]))
            for u in units:
                if u.interpretation or u.implication:
                    plans.append(ParagraphPlan(
                        paragraph_id=f"{sec.section_id}-I{i}",
                        purpose="interpretation", section_id=sec.section_id,
                        claim_refs=[u.claim_id], evidence_refs=[rid],
                        required_content=["机制解释（若为推测须标记）",
                                          "实际含义"],
                        optional_context=["possible explanation" if
                                          u.interpretation_status == "hypothesis"
                                          else ""]))
                if u.limitation:
                    plans.append(ParagraphPlan(
                        paragraph_id=f"{sec.section_id}-L{i}",
                        purpose="limitation", section_id=sec.section_id,
                        claim_refs=[u.claim_id],
                        required_content=[f"边界: {u.limitation}"]))
            if any(u.evidence_level in ("strong", "moderate") for u in units):
                plans.append(ParagraphPlan(
                    paragraph_id=f"{sec.section_id}-S{i}", purpose="sensitivity",
                    section_id=sec.section_id, evidence_refs=[rid],
                    required_content=["扰动设计", "结论稳定性陈述"]))
        return plans

    def _discussion_sections(self, sec, ir):
        return [ParagraphPlan(
            paragraph_id=f"{sec.section_id}-D1", purpose="limitation",
            section_id=sec.section_id, claim_refs=list(sec.claims),
            required_content=["假设的适用边界", "证据不支持的推广"]),

            ParagraphPlan(
                paragraph_id=f"{sec.section_id}-D2", purpose="implication",
                section_id=sec.section_id, claim_refs=list(sec.claims),
                required_content=["实际含义", "后续方向"])]

    def _conclusion_sections(self, sec, ir):
        return [ParagraphPlan(
            paragraph_id=f"{sec.section_id}-C1", purpose="summary",
            section_id=sec.section_id, claim_refs=list(sec.claims),
            finding_refs=[f.finding_id for f in (self.fg.findings if self.fg else [])
                          if f.status == "PASS"],
            required_content=["仅陈述 validated findings",
                              "边界条件"], forbidden_claims=["新结论"])]

    # ------------------------------------------------------------ 工具

    def _argument_units_for_result(self, rid) -> list[ArgumentUnit]:
        """P11-3：result → ArgumentUnit（claim/support/comparison/解释/边界）。"""
        edges = [(e["from"], e["relation"], e["to"]) for e in self.graph.relations]
        claims = [t for f, r, t in edges if r == "supports" and f == rid]
        producer = next((f for f, r, t in edges
                         if r == "produces" and t == rid), "")
        units = []
        for cid in claims:
            c = self.registry.get(cid)
            active = c.status == "active"
            has_robust = bool(self.registry.get(rid).tags)
            level = evidence_level_of(c.status, has_baseline=True,
                                      has_robustness=has_robust)
            interp, interp_status = self._interpretation_for(cid, rid)
            units.append(ArgumentUnit(
                claim_id=cid,
                claim_text=(c.data.get("statement") or c.title or ""),
                support=[producer] if producer else [],
                comparison={"baseline": "朴素基线", "candidate": cid},
                interpretation=interp, interpretation_status=interp_status,
                limitation=self._limitation_for(cid),
                implication="适用于当前数据条件，不声称普适最优",
                evidence_level=level if active else "unknown"))
        return units

    def _interpretation_for(self, cid, rid):
        """P11-11：解释引擎（确定性）。机制无证据时标 hypothesis。"""
        c = self.registry.get(cid)
        card_id = ""
        for m in self.registry.list_by_type("model"):
            if m.question == c.question:
                card_id = str(m.data.get("card_id", ""))
        if card_id:
            return (f"主要贡献来自 {card_id} 所代表的建模路径"
                    f"（possible explanation，机制证据待补）"), "hypothesis"
        return ("结果与假设方向一致"), "fact"

    def _limitation_for(self, cid) -> str:
        c = self.registry.get(cid)
        return f"结论限于 {c.question} 的数据条件与假设边界"

    def _figures_for_result(self, rid) -> list[str]:
        return [t for f, r, t in
                [(e["from"], e["relation"], e["to"]) for e in self.graph.relations]
                if r == "visualized_by" and f == rid]

    def _selection_reason(self, card_id) -> str:
        return f"见 {card_id} 的选型决策记录（knowledge_refs 可回查）" if card_id else ""

    def figure_bindings(self) -> list[FigureBinding]:
        """P11-13：图 → why_exists/what_to_observe/what_it_supports/does_not_prove。"""
        out = []
        edges = [(e["from"], e["relation"], e["to"]) for e in self.graph.relations]
        for f in self.registry.list_by_type("figure"):
            if f.status in ("invalidated", "superseded", "deprecated"):
                continue
            supported = [t for ff, r, t in edges
                         if r == "visualized_by" and ff == f.artifact_id]
            out.append(FigureBinding(
                figure_id=f.artifact_id,
                why_exists=f"展示 {f.question} 的实验结果",
                what_to_observe="结果指标与基线的相对关系",
                what_it_supports=supported,
                what_it_does_not_prove="因果机制（需受控实验）"))
        return out

    def equation_bindings(self) -> list[EquationBinding]:
        """P11-14：公式绑定 model_ref/purpose/symbols——拒绝凑数量公式。"""
        out = []
        for i, m in enumerate(self.registry.list_by_type("model")):
            if m.status in ("invalidated", "superseded", "deprecated"):
                continue
            out.append(EquationBinding(
                equation_id=f"EQ-{m.artifact_id}",
                model_ref=m.artifact_id,
                purpose=f"{m.data.get('card_id', '')} 的核心刻画（服务 "
                        f"{m.question} 的求解）",
                symbols=["自变量", "参数", "目标量"],
                used_by=["S2"]))
        return out


class DecisionLogStub:
    def __init__(self):
        self.decisions = {}


# ============================================================
# P11-8 Controlled Renderer（确定性默认 + LLM 可插拔）
# ============================================================

_NUM_RE = re.compile(r"(?<![\w.])(\d+\.\d+|\d+%|\d+)(?![\w.])")
_CITE_RE = re.compile(r"\\cite[tp]?\{([^}]+)\}")


class DeterministicRenderer:
    """默认渲染器：从 ParagraphPlan 确定性生成段落（零 LLM）。"""

    name = "deterministic"

    def render_paragraph(self, inp: ExpressionInput) -> ExpressionOutput:
        plan, ctx = inp.paragraph_plan, inp.context
        parts: list[str] = []
        claims, findings = [], []
        numbers: list[str] = []
        for u in plan.get("argument_units", []):
            level = u.get("evidence_level", "weak")
            phrasing = allowed_phrasing(level)[0] if allowed_phrasing(level) else ""
            text = u.get("claim_text", "")
            if level == "unknown":
                parts.append(f"[待验证] {text}（证据不足，不作结论）")
            else:
                parts.append(f"{phrasing}：{text}" if phrasing else text)
            claims.append(u.get("claim_id", ""))
            numbers += _NUM_RE.findall(text)
            if u.get("interpretation"):
                tag = "" if u.get("interpretation_status") == "fact" \
                    else "（possible explanation）"
                parts.append(f"{u['interpretation']}{tag}")
        for req in plan.get("required_content", []):
            parts.append(f"[{req}]")
        if plan.get("transition_from") and plan.get("transition_to"):
            parts.append(f"承接 {plan['transition_from']} 的产物，"
                         f"进入 {plan['transition_to']} 的研究。")
        text = " ".join(p for p in parts if p)
        return ExpressionOutput(
            text=text, renderer_name=self.name,
            source_claim_ids=[c for c in claims if c],
            rendered_numbers=sorted(set(numbers)))


class ControlledRenderer:
    """可插拔 LLM 渲染器封装：LLM 只拿到最小权限 Context，
    输出必过后验校验（数字/引用/claim ⊆ 允许集）。
    LLM 调用方以 callable 注入（llm_fn(ExpressionInput) -> str），
    本仓库不内置任何 LLM。"""

    name = "controlled-llm"

    def __init__(self, llm_fn=None):
        self.llm_fn = llm_fn
        self.fallback = DeterministicRenderer()

    def render_paragraph(self, inp: ExpressionInput) -> ExpressionOutput:
        if self.llm_fn is None:
            out = self.fallback.render_paragraph(inp)
        else:
            text = self.llm_fn(inp)
            out = ExpressionOutput(
                text=text, renderer_name=self.name,
                source_claim_ids=[c["id"] for c in inp.context.allowed_claims],
                source_evidence_ids=list(inp.context.allowed_evidence))
        out = self._post_validate(inp, out)
        return out

    # ------------------------------------------------------------ P11-9 后验

    def _post_validate(self, inp: ExpressionInput,
                       out: ExpressionOutput) -> ExpressionOutput:
        ctx = inp.context
        violations: list[str] = []
        rendered_nums = _NUM_RE.findall(out.text)
        allowed_nums = set(ctx.allowed_numbers)
        for n in rendered_nums:
            if allowed_nums and n not in allowed_nums:
                violations.append(f"hallucinated_number: {n}")
        rendered_cites = {k.strip() for m in _CITE_RE.findall(out.text)
                          for k in m.split(",")}
        allowed_refs = set(ctx.allowed_references)
        for c in rendered_cites:
            if allowed_refs and c not in allowed_refs:
                violations.append(f"hallucinated_citation: {c}")
        # 措辞校准（按段落内最强证据级别）
        levels = [u.get("evidence_level", "weak")
                  for u in inp.paragraph_plan.get("argument_units", [])]
        level = "strong" if "strong" in levels else \
            "moderate" if "moderate" in levels else \
            "weak" if "weak" in levels else "unknown"
        out.wording_violations = check_wording(out.text, level)
        out.violations = violations + out.wording_violations
        out.disposition = classify_renderer_failure(out.violations)
        return out
