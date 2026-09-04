"""ExperimentPlanner — 实验规划器（V3 P3，experiment_design 节点核心）。

从选中方法卡生成实验计划:
    * required_checks: 方法卡 validation 条目（必做验证，缺一不可进 evidence）
    * preflight_guards: 关联失败记忆的 avoidance（实验前防线，防重蹈覆辙）
    * failure_watchlist: 关联失败记忆的 symptom+detection（实验中/后自检）
    * baseline_comparison: 朴素基线 + 次优方法卡（Arena 落选者作为对照）
    * sensitivity: 灵敏度方案（从 validation 中含"敏感"的条目提取）

计划是机器可读的（experiment_Qi 节点消费），evidence_gate 反向核对
required_checks 是否被实验结果覆盖。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..knowledge.retriever import KnowledgeRetriever


class PlannerError(ValueError):
    """实验规划失败。"""


@dataclass
class ExperimentPlan:
    question: str
    methods: list[str]                       # 主方法 + 组合方法 card_id
    required_checks: list[str] = field(default_factory=list)
    preflight_guards: list[str] = field(default_factory=list)
    failure_watchlist: list[dict] = field(default_factory=list)
    baseline_comparison: list[str] = field(default_factory=list)
    sensitivity: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "question": self.question,
            "methods": self.methods,
            "required_checks": self.required_checks,
            "preflight_guards": self.preflight_guards,
            "failure_watchlist": self.failure_watchlist,
            "baseline_comparison": self.baseline_comparison,
            "sensitivity": self.sensitivity,
        }

    @property
    def has_baseline(self) -> bool:
        return bool(self.baseline_comparison)

    @property
    def has_sensitivity(self) -> bool:
        return bool(self.sensitivity)


class ExperimentPlanner:
    def __init__(self, retriever: KnowledgeRetriever):
        self.retriever = retriever

    def plan(self, question: str, card_ids: list[str],
             baseline_card_id: str | None = None) -> ExperimentPlan:
        """为问题（如 Q001）的选中方法生成实验计划。

        card_ids: 主方法 + 常组合方法（Arena shortlist 头部）
        baseline_card_id: 对照方法（缺省取 shortlist 次优，由调用方传入）
        """
        if not card_ids:
            raise PlannerError("card_ids 为空：无方法可规划")
        for cid in card_ids:
            if cid not in self.retriever.cards:
                raise PlannerError(f"方法卡不存在: {cid}")

        plan = ExperimentPlan(question=question, methods=list(card_ids))

        # ---- 必做检查（validation 条目去重合并）+ 灵敏度提取
        seen_checks: set[str] = set()
        for cid in card_ids:
            card = self.retriever.cards[cid]
            for v in card.validation:
                if v not in seen_checks:
                    plan.required_checks.append(f"[{cid}] {v}")
                    seen_checks.add(v)
                if "敏感" in v or "sensitivity" in v.lower():
                    plan.sensitivity.append(f"[{cid}] {v}")
            if not any("敏感" in v for v in card.validation):
                plan.sensitivity.append(
                    f"[{cid}] 默认: 关键参数 ±10% 扰动对结论的影响")

        # ---- 失败防线（关联失败记忆，主方法优先）
        seen_guards: set[str] = set()
        for cid in card_ids:
            for fm in self.retriever.failures_for(cid):
                if fm.avoidance not in seen_guards:
                    plan.preflight_guards.append(fm.avoidance)
                    seen_guards.add(fm.avoidance)
                plan.failure_watchlist.append({
                    "failure_id": fm.failure_id,
                    "method": fm.method,
                    "symptom": fm.symptom,
                    "detection": fm.detection,
                })

        # ---- 基线对比（朴素基线永远在场 + 显式对照方法）
        plan.baseline_comparison.append("朴素基线（均值/最近值/穷举小规模等同口径对照）")
        if baseline_card_id:
            if baseline_card_id not in self.retriever.cards:
                raise PlannerError(f"对照方法卡不存在: {baseline_card_id}")
            plan.baseline_comparison.append(
                f"方法对照: {baseline_card_id}（{self.retriever.cards[baseline_card_id].name}）")
        return plan
