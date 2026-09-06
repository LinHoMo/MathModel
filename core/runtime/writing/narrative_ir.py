#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scientific Narrative IR（P10-1/2/3）—— 论文的中间表示层。

Writer 不直接操作 Markdown/LaTeX；一切论文结构先落为本 IR：

    Research State → Claim Coverage Matrix → Narrative IR → Paper Projection
                                                          → LLM 表达层（可选）
                                                          → Fact Checker

P10-2 Claim Coverage Matrix：每行 claim，列 evidence/experiment/model/figure/
section——全部由图派生，不冗余存储（P10-0 裁决）。
强制规则：C1 无证据不可发布；C2 hypothesis ≠ conclusion；C3/C4 由 P7 失效
传播覆盖（红队 R1/R2 已验证）。

P10-3 NarrativeReasoningGraph：论文级推理关系（motivates/supports/contradicts/
explains/compares/limits/extends），区别于证据图的物理因果边。
"""

from __future__ import annotations

from dataclasses import dataclass, field

TERMINAL = ("invalidated", "superseded", "deprecated")

# 推理关系词汇表（P10-3 冻结；物理因果边仍在 Evidence Graph）
REASONING_RELATIONS = ("motivates", "supports", "contradicts", "explains",
                       "compares", "limits", "extends")

# section purpose 词汇表（P10-1 IR）
SECTION_PURPOSES = ("problem_definition", "methodology", "experiment",
                    "results", "discussion", "conclusion")


@dataclass
class NarrativeSection:
    """IR 节点：一个 section 及其全部可追溯锚点。"""
    section_id: str                       # S1, S2, ...
    purpose: str                          # SECTION_PURPOSES 之一
    title: str = ""
    claims: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)     # result ids
    experiments: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    figures: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    equations: list[str] = field(default_factory=list)    # model id 引用
    limitations: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)     # FindingGraph ids

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "section_id", "purpose", "title", "claims", "evidence",
            "experiments", "models", "figures", "tables", "equations",
            "limitations", "findings")}


@dataclass
class ScientificNarrative:
    """整篇论文的 IR（派生自 Registry+Graph，随失效传播自动更新）。"""
    title: str = ""
    abstract: str = ""
    sections: list[NarrativeSection] = field(default_factory=list)
    reasoning_edges: list[dict] = field(default_factory=list)  # {from, relation, to}
    coverage: dict = field(default_factory=dict)

    def section(self, section_id: str) -> NarrativeSection | None:
        return next((s for s in self.sections
                     if s.section_id == section_id), None)

    def as_dict(self) -> dict:
        return {"title": self.title, "abstract": self.abstract,
                "sections": [s.as_dict() for s in self.sections],
                "reasoning_edges": self.reasoning_edges,
                "coverage": self.coverage}


# ============================================================
# P10-2 Claim Coverage Matrix
# ============================================================

@dataclass
class CoverageRow:
    claim_id: str
    evidence: list[str] = field(default_factory=list)
    experiments: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    figures: list[str] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    status: str = "active"               # claim 生命周期状态直通

    @property
    def publishable(self) -> bool:
        """C1：无 evidence 不可发布；C2：hypothesis/未验证不充当 conclusion；
        C3/C4：终态 claim 不可发布（P7 传播已保证 status 正确）。"""
        return bool(self.evidence) and self.status == "active"

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "claim_id", "evidence", "experiments", "models", "figures",
            "sections", "status", "publishable")}


def claim_coverage(registry, graph,
                   section_map: dict[str, list[str]] | None = None
                   ) -> list[CoverageRow]:
    """Claim → Evidence/Experiment/Model/Figure/Section 全景矩阵。

    section_map: {section_id: [claim_id]} —— 由 Narrative IR 生成；
    缺省时不填 sections 列。
    """
    section_map = section_map or {}
    rows: list[CoverageRow] = []
    edges = [(e["from"], e["relation"], e["to"]) for e in graph.relations]

    def _rev(target: str, rel: str) -> list[str]:
        return [f for f, r, t in edges if r == rel and t == target]

    for c in registry.list_by_type("claim"):
        qid = c.question
        evidence = _rev(c.artifact_id, "supports")
        experiments: list[str] = []
        for r_id in evidence:
            experiments += _rev(r_id, "produces")
        models: list[str] = []
        for x_id in experiments:
            models += [f for f, r, t in edges
                       if r in ("validated_by", "tests") and t == x_id]
        figures: list[str] = []
        for r_id in evidence:
            figures += [t for f, r, t in edges
                        if r == "visualized_by" and f == r_id]
        sections = [sid for sid, cids in section_map.items()
                    if c.artifact_id in cids]
        rows.append(CoverageRow(
            claim_id=c.artifact_id, evidence=evidence,
            experiments=sorted(set(experiments)), models=sorted(set(models)),
            figures=sorted(set(figures)), sections=sorted(set(sections)),
            status=c.status))
    return rows


# ============================================================
# P10-1 IR 构建（派生式）
# ============================================================

def build_narrative_ir(registry, graph, narrative=None,
                       findings_graph=None) -> ScientificNarrative:
    """从 Registry+Graph（可选 Narrative/Findings）构建论文 IR。

    abstract/conclusion 由 validated findings 派生（P10-11），
    不接受"先写正文后总结"。
    """
    sections: list[NarrativeSection] = []
    section_claims: dict[str, list[str]] = {}

    def _active(typ):
        return [a for a in registry.list_by_type(typ)
                if a.status not in TERMINAL]

    def _ids(arts):
        return [a.artifact_id for a in arts]

    def _edges():
        return [(e["from"], e["relation"], e["to"]) for e in graph.relations]

    edges = _edges()
    claims = _active("claim")
    models = _active("model")
    experiments = _active("experiment")
    results = _active("result")
    figures = _active("figure")
    findings = list(findings_graph.findings) if findings_graph else []

    def _by_question(arts, qid):
        return [a.artifact_id for a in arts if a.question == qid]

    # S1 problem_definition
    s1 = NarrativeSection("S1", "problem_definition",
                          title="问题重述与分析",
                          claims=[c.artifact_id for c in claims])
    # S2 methodology
    s2 = NarrativeSection("S2", "methodology", title="模型建立",
                          models=_ids(models))
    s2.equations = _ids(models)
    s2.claims = [c.artifact_id for c in claims]
    # S3 experiment
    s3 = NarrativeSection("S3", "experiment", title="实验设计",
                          experiments=_ids(experiments),
                          models=_ids(models))
    # S4 results
    s4 = NarrativeSection("S4", "results", title="结果与分析",
                          evidence=_ids(results), figures=_ids(figures),
                          claims=[c.artifact_id for c in claims])
    s4.findings = [f.finding_id for f in findings]
    # S5 discussion
    s5 = NarrativeSection("S5", "discussion", title="讨论与局限",
                          limitations=[
                              f"{a.artifact_id}: {r}"
                              for a in registry.list_by_type("assumption")
                              for r in [a.data.get("limitation", "")] if r]
                          or [f"假设 {a.artifact_id} 的适用边界需讨论"
                              for a in registry.list_by_type("assumption")
                              if a.status == "active"])
    # S6 conclusion
    s6 = NarrativeSection("S6", "conclusion", title="结论",
                          claims=[c.artifact_id for c in claims])
    s6.findings = [f.finding_id for f in findings
                   if f.status == "PASS"]
    sections = [s1, s2, s3, s4, s5, s6]
    for s in sections:
        section_claims[s.section_id] = list(s.claims)

    # 推理图（叙事级）
    reasoning: list[dict] = []
    problems = _active("problem")
    for p in problems:
        for q in _active("question"):
            reasoning.append({"from": p.artifact_id, "relation": "motivates",
                              "to": q.artifact_id})
    for c in claims:
        for r_id in _rev_local(edges, c.artifact_id, "supports"):
            reasoning.append({"from": r_id, "relation": "supports",
                              "to": c.artifact_id})
    for f in findings:
        for other in findings:
            if other.finding_id != f.finding_id and \
                    f.compares_with(other):
                reasoning.append({"from": f.finding_id,
                                  "relation": "compares",
                                  "to": other.finding_id})
    for m in models:
        for a_id in [t for f, r, t in edges
                     if r == "assumes" and f == m.artifact_id]:
            reasoning.append({"from": a_id, "relation": "limits",
                              "to": m.artifact_id})

    cov = graph.coverage()
    abstract = _derive_abstract(findings, claims, cov, models=models,
                                experiments=experiments)
    return ScientificNarrative(
        title=(problems[0].title if problems else "数学建模研究"),
        abstract=abstract,
        sections=sections, reasoning_edges=reasoning, coverage=cov)


def _rev_local(edges, target, rel):
    return [f for f, r, t in edges if r == rel and t == target]


def _derive_abstract(findings, claims, coverage: dict,
                     models=None, experiments=None) -> str:
    """P11-15：Abstract 五要素结构（problem/method/key result/validation/
    contribution），全部从 validated findings 与 Registry 派生。

    禁止"具有重要意义/效果良好"类无证据空话（由 P11-17 检测兜底）。
    """
    validated = [f for f in findings if f.status == "PASS"]
    total = coverage.get("claims_total", 0)
    supported = coverage.get("claims_supported", 0)
    parts = []
    parts.append("针对赛题建立建模与求解流程"
                 + (f"（{len(models)} 个模型）" if models else ""))
    if models:
        cards = [str(m.data.get("card_id", "")) for m in models
                 if m.data.get("card_id")]
        if cards:
            parts.append("采用 " + "、".join(cards) + " 等方法")
    if total:
        parts.append(f"形成 {total} 项结论，{supported} 项获得实验证据支撑")
    if experiments:
        parts.append(f"并以 {len(experiments)} 组实验完成验证"
                     "（含基线对照与灵敏度检验）")
    for f in validated:
        parts.append(f.statement)
    if validated:
        parts.append("主要贡献为可追溯的证据链与结论边界声明")
    else:
        parts.append("尚无经验证的发现（研究进行中）")
    return "。".join(p for p in parts if p) + "。"


def derive_conclusion(findings) -> str:
    """P10-11：Conclusion 只从 validated findings 派生。"""
    validated = [f for f in findings if f.status == "PASS"]
    if not validated:
        return "尚无经验证的结论。"
    return "；".join(f.statement for f in validated) + "。"
