"""MethodArena — 方法选型竞技场（V3 P3，model_selection 节点核心）。

流程:
    1. KnowledgeRetriever.recommend(features) 拿排序候选（含风险/验证/失败案例）
    2. DecisionLog 查同类问题的历史决策（含被推翻记录——不重蹈覆辙）
    3. 历史 active 决策若与当前首选冲突 → 提示先处理旧决策（invalidate 或沿用）
    4. 产出 shortlist 并把选型登记为 Decision（reversible，供后续推翻）

Arena 语义: 候选并列展示（适用条件/风险/验证代价），选型必须留下
alternatives 与 criteria——评委追问"为什么不用 X"时直接有答案。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..decisions.log import DecisionLog
from ..knowledge.retriever import KnowledgeRetriever, Recommendation


class SelectionError(ValueError):
    """选型失败（无候选 / 与历史决策冲突未处理）。"""


@dataclass
class SelectionOutcome:
    question: str
    features: dict
    shortlist: list[dict]                    # 排序候选（Recommendation.as_dict）
    chosen: str                              # card_id
    decision_id: str = ""
    prior_decisions: list[dict] = field(default_factory=list)  # 历史决策视图
    notes: list[str] = field(default_factory=list)

    @property
    def chosen_card(self) -> dict:
        return next(c for c in self.shortlist if c["card_id"] == self.chosen)


class MethodArena:
    def __init__(self, retriever: KnowledgeRetriever,
                 decisions: DecisionLog | None = None):
        self.retriever = retriever
        self.decisions = decisions

    def select(self, question: str, features: dict, top_k: int = 3,
               created_by: str = "model_selection",
               record: bool = True) -> SelectionOutcome:
        """按问题特征选型。question 如 'Q001' 或自由文本描述。"""
        recs: list[Recommendation] = self.retriever.recommend(features, top_k=top_k)
        if not recs:
            raise SelectionError(
                f"无匹配方法卡: features={features}；"
                f"检查问题类型标签或先扩充知识库")

        outcome = SelectionOutcome(
            question=question,
            features=dict(features),
            shortlist=[r.as_dict() for r in recs],
            chosen=recs[0].card.card_id,
        )

        # ---- 历史决策交叉检查（同类问题的 active 决策不可静默覆盖）
        if self.decisions is not None:
            qt = features.get("problem_types") or []
            outcome.prior_decisions = self.decisions.query(
                question_type=qt[0] if qt else None, active_only=False) \
                if qt else self.decisions.query(active_only=False)
            active_same_chosen = [
                d for d in outcome.prior_decisions
                if d.get("status") == "active" and d.get("chosen") == outcome.chosen
                and str(d.get("question", "")).startswith(question)]
            active_conflict = [
                d for d in outcome.prior_decisions
                if d.get("status") == "active" and d.get("chosen") != outcome.chosen
                and str(d.get("question", "")).startswith(question)]
            if active_conflict:
                outcome.notes.append(
                    f"与 active 决策 {active_conflict[0]['decision_id']}（"
                    f"{active_conflict[0]['chosen']}）冲突；"
                    f"确认后应先 invalidate 旧决策再登记新选型")
            if active_same_chosen:
                outcome.notes.append(
                    f"沿用历史决策 {active_same_chosen[0]['decision_id']} 的选型")

        # ---- 登记决策（选型即决策，alternatives 保留落选理由）
        if record and self.decisions is not None:
            top = recs[0]
            dec = self.decisions.add(
                question=f"{question} 方法选型",
                chosen=outcome.chosen,
                alternatives=[
                    f"{r.card.card_id}（score={r.score}，"
                    f"{'；'.join(r.matched) or '次优'}）"
                    for r in recs[1:]],
                criteria=["检索得分", "适用条件匹配", "验证代价",
                          "历史决策一致性"],
                reasoning=top.reasoning() or
                          f"{top.card.name} 在候选中得分最高",
                confidence=min(0.5 + 0.1 * top.score, 0.95),
                reversible=True,
                created_by=created_by,
                evidence_ids=[],
                question_type=(features.get("problem_types") or [""])[0],
                knowledge_refs=top.knowledge_refs,
                failure_refs=[f.failure_id for f in top.related_failures],
                required_validation=list(top.required_experiments),
                score_breakdown=top.score_detail.as_dict(),
            )
            outcome.decision_id = dec.decision_id
        return outcome
