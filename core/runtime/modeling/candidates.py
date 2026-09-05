#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Candidate Arena（P8-4 / P8-6）—— 候选方案生成、排序与解释。

竞赛建模的真实形态不是"单方法 vs 单方法"，而是：
    Baseline + Improved Model + Hybrid Model + Innovation + Sensitivity

本模块只负责 candidate generation / ranking / explanation（P8 硬约束），
**不执行模型**——执行交给 Modeling Runtime（handlers / planner）。

Innovation Candidate（P8-6）必须绑定 required_evidence + validation_protocol：
没有证据支撑的创新只能是 hypothesis，不能进入 Research State（CI-03）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..knowledge.cards import Pattern
from ..knowledge.packs import CompetitionPack
from ..knowledge.retriever import KnowledgeRetriever, Recommendation

_CANDIDATE_SEQ = {"n": 0}


@dataclass
class InnovationCandidate:
    """结构化创新候选（P8-6）：由 InnovationPattern + 命中上下文生成。"""
    pattern_id: str
    name: str
    base_method: str                    # card_id
    modification: str
    expected_benefit: str
    risk: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    validation_protocol: list[str] = field(default_factory=list)
    novelty_level: str = ""             # incremental/notable/high
    implementation_cost: str = ""       # low/medium/high
    competition_fit: str = ""
    knowledge_version: int = 1
    source_refs: list[str] = field(default_factory=list)
    status: str = "hypothesis"          # hypothesis → (evidence) → accepted

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "pattern_id", "name", "base_method", "modification",
            "expected_benefit", "risk", "required_evidence",
            "validation_protocol", "novelty_level", "implementation_cost",
            "competition_fit", "knowledge_version", "source_refs", "status")}

    def to_experiment_requirements(self) -> list[str]:
        """创新候选 → 反向实验需求（P8-6→P8-7 通道）。"""
        reqs = list(self.required_evidence)
        reqs += [f"validation_protocol: {v}" for v in self.validation_protocol]
        return reqs or ["创新有效性对照实验（vs 未采用该创新的基线）"]


@dataclass
class Candidate:
    """候选方案（P8-4）：baseline / improved / hybrid / innovation。"""
    candidate_id: str
    kind: str                            # baseline/improved/hybrid/innovation
    composition: list[str]               # 方法/组件描述序列
    base_card: str                       # 主方法 card_id
    rationale: str                       # 为什么是它（可解释）
    score: int = 0
    score_detail: dict = field(default_factory=dict)
    risks: list[dict] = field(default_factory=list)
    required_experiments: list[str] = field(default_factory=list)
    innovations: list[InnovationCandidate] = field(default_factory=list)
    knowledge_refs: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "kind": self.kind,
            "composition": self.composition,
            "base_card": self.base_card,
            "rationale": self.rationale,
            "score": self.score,
            "score_detail": self.score_detail,
            "risks": self.risks,
            "required_experiments": self.required_experiments,
            "innovations": [i.as_dict() for i in self.innovations],
            "knowledge_refs": self.knowledge_refs,
            "reasoning": self.reasoning(),
        }

    def reasoning(self) -> str:
        parts = [f"{self.candidate_id}[{self.kind}] {self.rationale}"]
        if self.innovations:
            parts.append("创新: " + "; ".join(
                f"{i.name}（{i.novelty_level or 'incremental'}, {i.status}）"
                for i in self.innovations))
        if self.required_experiments:
            parts.append("必做: " + ", ".join(self.required_experiments))
        return "；".join(parts)


class CandidateArena:
    """从 shortlist 生成候选方案并排序（确定性，可解释）。"""

    def __init__(self, retriever: KnowledgeRetriever,
                 pack: CompetitionPack | None = None):
        self.retriever = retriever
        self.pack = pack

    # ------------------------------------------------------------ 生成

    def generate_candidates(self, question: str, features: dict,
                            recs: list[Recommendation] | None = None,
                            top_cards: int = 2) -> list[Candidate]:
        recs = recs or self.retriever.recommend(features, top_k=top_cards + 1)
        if not recs:
            return []
        cands: list[Candidate] = []
        main = recs[0]
        _CANDIDATE_SEQ["n"] += 1
        batch = _CANDIDATE_SEQ["n"]

        # 1) Baseline：主方法单独成案（朴素对照之外的方法学基线）
        cands.append(Candidate(
            candidate_id=f"CA{batch:03d}-A", kind="baseline",
            composition=[main.card.card_id], base_card=main.card.card_id,
            rationale=f"top1 {main.card.name}（total={main.score}），"
                      f"作为方法学基线", score=main.score,
            score_detail=main.score_detail.as_dict(),
            risks=main.risks,
            required_experiments=main.required_experiments,
            knowledge_refs=main.knowledge_refs))

        # 2) Improved：主方法 + 卡片 recommended 证据/组合增强
        improved_parts = [main.card.card_id]
        boost = main.card.evidence_recommended[:2]
        if main.card.compatible_methods:
            partner = next((c for c in main.card.compatible_methods
                            if c in self.retriever.cards
                            and c != main.card.card_id), None)
            if partner:
                improved_parts.append(partner)
        cands.append(Candidate(
            candidate_id=f"CA{batch:03d}-B", kind="improved",
            composition=improved_parts + [f"+{b}" for b in boost],
            base_card=main.card.card_id,
            rationale="主方法 + 推荐增强"
                      + ("（组合兼容方法）" if len(improved_parts) > 1 else ""),
            score=main.score + (2 if boost else 0),
            score_detail=main.score_detail.as_dict(),
            risks=main.risks,
            required_experiments=main.required_experiments
            + [f"recommended: {b}" for b in boost],
            knowledge_refs=main.knowledge_refs))

        # 3) Hybrid：主方法 × 次优方法（方法对照型组合）
        if len(recs) > 1:
            alt = recs[1]
            cands.append(Candidate(
                candidate_id=f"CA{batch:03d}-C", kind="hybrid",
                composition=[main.card.card_id, alt.card.card_id],
                base_card=main.card.card_id,
                rationale=f"top1×top2 对照混合（{main.card.name} × {alt.card.name}），"
                          "提供方法层面的稳健性对照",
                score=max(main.score, alt.score) - 2,
                score_detail=alt.score_detail.as_dict(),
                risks=main.risks + alt.risks,
                required_experiments=main.required_experiments
                + [f"ablation: 仅用 {alt.card.card_id} 对照"],
                knowledge_refs=main.knowledge_refs
                + [{"id": alt.card.card_id, "version": alt.card.version}]))

        # 4) Innovation：pattern 命中主方法 → InnovationCandidate（hypothesis）
        for pat in self.retriever.patterns_for(list(features.get(
                "problem_types") or [])):
            if main.card.card_id in pat.cards or pat.baseline_method \
                    and main.card.card_id in pat.cards:
                inno = self._innovation_from_pattern(pat, main.card)
                cands.append(Candidate(
                    candidate_id=f"CA{batch:03d}-D", kind="innovation",
                    composition=[main.card.card_id,
                                 f"+innovation:{pat.pattern_id}"],
                    base_card=main.card.card_id,
                    rationale=f"主方法 + 创新模式「{pat.title}」"
                              f"（预期收益: {pat.expected_benefit or pat.innovation[:40]}）",
                    score=main.score + {"high": 6, "medium": 4,
                                        "incremental": 2}.get(
                        pat.novelty_level, 3)
                    + {"high": 2, "medium": 0, "low": -2}.get(
                        pat.competition_fit, 0)
                    - {"high": 4, "medium": 2, "low": 0}.get(
                        pat.implementation_cost, 1),
                    score_detail=main.score_detail.as_dict(),
                    risks=main.risks + [{"source": "pattern",
                                         "id": pat.pattern_id,
                                         "level": "medium",
                                         "title": r} for r in pat.risks[:2]],
                    required_experiments=main.required_experiments
                    + inno.to_experiment_requirements(),
                    innovations=[inno],
                    knowledge_refs=main.knowledge_refs
                    + [{"id": pat.pattern_id, "version": pat.version}]))
                break   # 每个 batch 只带一个创新候选（竞赛时间约束）

        # Competition Pack 修饰（CI-08：只读参与打分，不改状态）
        if self.pack:
            for c in cands:
                bonus = 0
                if main.card.family in self.pack.recommended_methods \
                        or main.card.card_id in self.pack.recommended_methods:
                    bonus += 5
                if main.card.family in self.pack.high_risk_methods \
                        or main.card.card_id in self.pack.high_risk_methods:
                    bonus -= 8
                    c.risks.append({"source": "competition_pack",
                                    "id": self.pack.pack_id, "level": "high",
                                    "title": "该竞赛评委对这类方法持保守态度"})
                c.score += bonus
        return cands

    def _innovation_from_pattern(self, pat: Pattern, card: MethodCard
                                 ) -> InnovationCandidate:
        return InnovationCandidate(
            pattern_id=pat.pattern_id, name=pat.title,
            base_method=card.card_id,
            modification=pat.innovation,
            expected_benefit=pat.expected_benefit or pat.innovation,
            risk=list(pat.risks), required_evidence=list(pat.required_evidence),
            validation_protocol=list(pat.validation_protocol),
            novelty_level=pat.novelty_level,
            implementation_cost=pat.implementation_cost,
            competition_fit=pat.competition_fit,
            knowledge_version=pat.version,
            source_refs=list(pat.examples),
            status="hypothesis")

    # ------------------------------------------------------------ 排序

    def rank(self, candidates: list[Candidate]) -> list[Candidate]:
        """确定性排序：score 降序 → id 升序（同分可复现，CI-10）。"""
        return sorted(candidates, key=lambda c: (-c.score, c.candidate_id))
