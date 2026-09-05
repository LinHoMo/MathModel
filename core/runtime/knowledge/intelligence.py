#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Competition Intelligence API（P8-15）—— 知识层的稳定程序接口。

其他模块**不得直接读 YAML**；一切知识消费走本 API。
输出全部为结构化对象（dataclass / dict），可测试、可解释、可追溯。

P8 最终审计问题 #10：去掉所有 LLM，本 API 仍然完整工作——
它是纯确定性计算层（规则 + 结构化知识），不含任何 Agent。

CI-08：Knowledge 层 side-effect 受控——除 DecisionLog 显式登记外，
本 API 不写任何状态（API 只读知识 + 打分 + 规划，不执行研究）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .cards import FailureMemory, MethodCard, Pattern
from .packs import CompetitionPack, detect_knowledge_conflicts, \
    load_competition_packs
from .retriever import KnowledgeRetriever, Recommendation


@dataclass
class ProblemProfile:
    """结构化问题画像（P8-21 验收 A：真实问题 → Profile）。"""
    problem_types: list[str] = field(default_factory=list)
    objective_types: list[str] = field(default_factory=list)
    has_data: bool = True
    sample_size: str = "medium"          # small / medium / large
    time_series: bool = False
    multi_objective: bool = False
    uncertainty: bool = False
    high_dimensional: bool = False
    nonlinear: bool = False
    interpretability_required: bool = False
    mechanism_known: bool = False
    competition_type: str = "cumcm"
    time_budget_hours: float | None = None

    def as_features(self) -> dict:
        """→ retriever.recommend 的 features dict（含派生键）。"""
        return {
            "problem_types": list(self.problem_types),
            "has_data": self.has_data,
            "sample_size": self.sample_size,
            "time_series": self.time_series,
            "objectives": 2 if self.multi_objective else 1,
            "uncertainty": self.uncertainty,
            "high_dimensional": self.high_dimensional,
            "nonlinear": self.nonlinear,
            "interpretability_required": self.interpretability_required,
            "mechanism_known": self.mechanism_known,
        }


@dataclass
class ExperimentSuggestion:
    candidate_id: str
    question: str
    plan: object                          # ExperimentPlan
    explanation: str

    def as_dict(self) -> dict:
        return {"candidate_id": self.candidate_id, "question": self.question,
                "plan": self.plan.as_dict(), "explanation": self.explanation}


class CompetitionIntelligence:
    """知识 → 决策的计算层。构造一次，全 API 复用（确定性、无隐藏状态）。"""

    def __init__(self, knowledge_root: str | Path,
                 decisions=None, competition_type: str = "cumcm"):
        self.root = Path(knowledge_root)
        self.retriever = KnowledgeRetriever(self.root)
        self.packs = load_competition_packs(self.root)
        self.pack = self.packs.get(f"cp-{competition_type}") or next(
            iter(self.packs.values()), None)
        self.decisions = decisions
        from ..modeling.candidates import CandidateArena
        from ..modeling.planner import ExperimentPlanner
        self.candidate_arena = CandidateArena(self.retriever, self.pack)
        self.planner = ExperimentPlanner(self.retriever)
        self._conflicts = detect_knowledge_conflicts(
            self.retriever.cards, self.retriever.failures,
            self.retriever.patterns)

    # ------------------------------------------------------------ P8-15 API

    def search_methods(self, profile: ProblemProfile,
                       top_k: int = 10) -> list[Recommendation]:
        """全量候选检索（排序后），供上层做进一步筛选。"""
        return self.retriever.recommend(profile.as_features(), top_k=top_k)

    def recommend_methods(self, profile: ProblemProfile,
                          top_k: int = 3) -> list[Recommendation]:
        """带维度分与解释的方法推荐（每条可回答为什么）。"""
        recs = self.search_methods(profile, top_k=top_k)
        if self.pack:
            for rec in recs:
                if rec.card.family in self.pack.recommended_methods \
                        or rec.card.card_id in self.pack.recommended_methods:
                    rec.score += 5
                    rec.score_detail.competition += 5
                if rec.card.family in self.pack.high_risk_methods \
                        or rec.card.card_id in self.pack.high_risk_methods:
                    rec.score -= 8
                    rec.score_detail.risk_penalty -= 8
        recs.sort(key=lambda r: (-r.score, r.card.card_id))
        return recs

    def generate_candidates(self, profile: ProblemProfile) -> list:
        """候选方案生成（baseline/improved/hybrid/innovation）。"""
        recs = self.recommend_methods(profile, top_k=3)
        return self.candidate_arena.generate_candidates(
            question="Q001", features=profile.as_features(), recs=recs)

    def rank_candidates(self, candidates: list) -> list:
        """确定性候选排序（CI-10）。"""
        return self.candidate_arena.rank(candidates)

    def find_failure_risks(self, candidate, context: dict | None = None
                           ) -> list[FailureMemory]:
        """候选方案的失败风险（主方法 + 组合方法全覆盖）。"""
        risks: list[FailureMemory] = []
        seen: set[str] = set()
        for cid in candidate.composition:
            if cid in self.retriever.cards:
                for fm in self.retriever.failures_for(cid):
                    if fm.failure_id not in seen:
                        risks.append(fm)
                        seen.add(fm.failure_id)
        return risks

    def suggest_experiments(self, candidate, question: str = "Q001"
                            ) -> ExperimentSuggestion:
        """候选 → 结构化实验计划（每条含 purpose/hypothesis/decision_rule）。"""
        plan = self.planner.plan_from_candidate(candidate, question)
        return ExperimentSuggestion(
            candidate_id=candidate.candidate_id, question=question,
            plan=plan,
            explanation=candidate.reasoning())

    def find_innovation_patterns(self, profile: ProblemProfile,
                                 candidate=None) -> list[Pattern]:
        pats = self.retriever.patterns_for(list(profile.problem_types))
        if candidate is not None:
            pats = [p for p in pats
                    if p.pattern_id not in
                    {i.pattern_id for i in candidate.innovations}]
        return pats

    def build_experiment_plan(self, profile: ProblemProfile,
                              question: str = "Q001") -> ExperimentSuggestion:
        """端到端：Profile → 推荐 → 候选 → 最优候选的实验计划。"""
        cands = self.rank_candidates(self.generate_candidates(profile))
        if not cands:
            raise ValueError("无可用候选方案（知识库为空或 profile 过滤全拒）")
        return self.suggest_experiments(cands[0], question)

    def explain_decision(self, decision_id: str) -> dict:
        """Decision Trace（P8-10/P8-16）：决策 → 知识版本 → 失败记忆 → 验证。"""
        if self.decisions is None:
            raise ValueError("未接入 DecisionLog，无法解释决策")
        dec = self.decisions.decisions.get(decision_id)
        if dec is None:
            raise KeyError(f"决策不存在: {decision_id}")
        knowledge = []
        for ref in dec.knowledge_refs:
            card = self.retriever.cards.get(ref.get("id", ""))
            knowledge.append({
                **ref,
                "current_version": card.version if card else None,
                "reproducible": bool(card and card.version == ref.get("version")),
                "name": card.name if card else None,
            })
        failures = [{"failure_id": fid,
                     "title": self.retriever.failures[fid].title,
                     "severity": self.retriever.failures[fid].severity}
                    for fid in dec.failure_refs
                    if fid in self.retriever.failures]
        return {
            "decision_id": dec.decision_id,
            "chosen": dec.chosen,
            "status": dec.status,
            "reasoning": dec.reasoning,
            "score_breakdown": dec.score_breakdown,
            "knowledge_refs": knowledge,
            "failure_refs": failures,
            "required_validation": dec.required_validation,
            "conflict_report": self.conflict_report(),
        }

    def get_competition_pack(self, profile: ProblemProfile | None = None
                             ) -> CompetitionPack | None:
        return self.pack

    def conflict_report(self) -> list[dict]:
        """P8-12/16：知识冲突报告（能发现、能记录；resolution_status 显式）。"""
        return [{"entity": c.entity, "field": c.field,
                 "source_a": c.source_a, "source_b": c.source_b,
                 "severity": c.severity,
                 "resolution_status": c.resolution_status,
                 "detail": c.detail}
                for c in self._conflicts]

    def select_and_record(self, profile: ProblemProfile, question: str,
                          record: bool = True):
        """推荐 + 登记 DecisionLog（唯一有副作用的入口，显式命名）。"""
        from ..modeling.selection import MethodArena
        arena = MethodArena(self.retriever, self.decisions)
        return arena.select(question, profile.as_features(), record=record)
