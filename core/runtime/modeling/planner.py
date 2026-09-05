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
class DecisionRule:
    """P8-9：实验判定规则——实验结果必须落在四态之一，不允许"看起来不错"。"""
    metric: str                     # 判定指标
    accept_if: str                  # 如 "improvement >= 3% and robustness_pass"
    reject_if: str                  # 如 "improvement < 3%"
    refine_if: str = ""             # 介于两者之间 → REFINE
    def as_dict(self) -> dict:
        return {"metric": self.metric, "accept_if": self.accept_if,
                "reject_if": self.reject_if, "refine_if": self.refine_if}


@dataclass
class ExperimentEntry:
    """P8-7：单条实验的结构化定义——每条都能回答"为什么必须做"。"""
    experiment_id: str
    purpose: str                     # 为什么做（来自 evidence_requirements）
    hypothesis: str                  # 预期主张
    method: str                      # 验证手段
    baseline: str                    # 对照物
    metrics: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    required_artifacts: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    failure_detection: str = ""
    decision_rule: DecisionRule | None = None
    priority: int = 2                # 1=must 2=should 3=nice
    cost: int = 1                    # 相对成本（1-10）
    expected_information_gain: float = 0.5   # 0-1（P8-14 时间预算基础）

    def as_dict(self) -> dict:
        return {"experiment_id": self.experiment_id, "purpose": self.purpose,
                "hypothesis": self.hypothesis, "method": self.method,
                "baseline": self.baseline, "metrics": self.metrics,
                "controls": self.controls,
                "required_artifacts": self.required_artifacts,
                "required_evidence": self.required_evidence,
                "failure_detection": self.failure_detection,
                "decision_rule": self.decision_rule.as_dict()
                if self.decision_rule else None,
                "priority": self.priority, "cost": self.cost,
                "expected_information_gain": self.expected_information_gain}


@dataclass
class ExperimentPlan:
    question: str
    methods: list[str]                       # 主方法 + 组合方法 card_id
    required_checks: list[str] = field(default_factory=list)
    preflight_guards: list[str] = field(default_factory=list)
    failure_watchlist: list[dict] = field(default_factory=list)
    baseline_comparison: list[str] = field(default_factory=list)
    sensitivity: list[str] = field(default_factory=list)
    # ---- P8-7 结构化实验条目 ----
    entries: list[ExperimentEntry] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "question": self.question,
            "methods": self.methods,
            "required_checks": self.required_checks,
            "preflight_guards": self.preflight_guards,
            "failure_watchlist": self.failure_watchlist,
            "baseline_comparison": self.baseline_comparison,
            "sensitivity": self.sensitivity,
            "entries": [e.as_dict() for e in self.entries],
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

        # ---- P8-7：结构化实验条目（每条回答"为什么必须做"）
        plan.entries = self._build_entries(plan, card_ids, baseline_card_id)
        return plan

    def plan_from_candidate(self, candidate, question: str = "Q001") -> ExperimentPlan:
        """Candidate（P8-4）→ ExperimentPlan（P8-7）：候选的创新候选与
        required_experiments 全部落进结构化条目（无证据的创新只是 hypothesis）。"""
        card_ids = [candidate.base_card] + [
            c for c in candidate.composition
            if c in self.retriever.cards and c != candidate.base_card]
        plan = self.plan(question, card_ids)
        seen = {e.purpose for e in plan.entries}
        for req in candidate.required_experiments:
            if req in seen:
                continue
            seen.add(req)
            plan.entries.append(ExperimentEntry(
                experiment_id=f"E-{plan.question}-{len(plan.entries) + 1:02d}",
                purpose=f"候选方案要求: {req}",
                hypothesis=f"{req} 验证通过",
                method=req, baseline=plan.baseline_comparison[0],
                priority=2, cost=2, expected_information_gain=0.5,
                decision_rule=DecisionRule(
                    metric=req, accept_if="criteria_pass",
                    reject_if="criteria_fail", refine_if="borderline")))
        for inno in candidate.innovations:
            for req in inno.to_experiment_requirements():
                if req in seen:
                    continue
                seen.add(req)
                plan.entries.append(ExperimentEntry(
                    experiment_id=f"E-{plan.question}-{len(plan.entries) + 1:02d}",
                    purpose=f"创新验证[{inno.pattern_id}]: {req}",
                    hypothesis=f"{inno.name} 产生正收益（{inno.expected_benefit[:40]}）",
                    method=req, baseline=f"未采用创新的 {candidate.base_card} 基线",
                    priority=2, cost=3, expected_information_gain=0.6,
                    failure_detection=inno.risk[0] if inno.risk else "",
                    decision_rule=DecisionRule(
                        metric="innovation_gain",
                        accept_if="gain > cost", reject_if="gain <= 0",
                        refine_if="gain 微弱")))
        return plan

    def _build_entries(self, plan: ExperimentPlan, card_ids: list[str],
                       baseline_card_id: str | None) -> list[ExperimentEntry]:
        """从 Method Card 的 evidence_requirements + 失败记忆反向生成实验。

        成本/信息增益为确定性启发值（证据成本低的必做项优先；high 级失败
        防线信息增益最高）。decision_rule 为四态结构（P8-9）。
        """
        entries: list[ExperimentEntry] = []
        seq = {"n": 0}

        def _entry(**kw) -> ExperimentEntry:
            seq["n"] += 1
            kw.setdefault("experiment_id", f"E-{plan.question}-{seq['n']:02d}")
            kw.setdefault("baseline", plan.baseline_comparison[0])
            return ExperimentEntry(**kw)

        main = self.retriever.cards[card_ids[0]]

        # 1) 基线对照（永远第一条，priority=1）
        entries.append(_entry(
            purpose="方法学对照：主方法必须战胜朴素基线才有意义",
            hypothesis=f"{main.name} 优于朴素基线",
            method="同口径基线对比实验", priority=1, cost=1,
            expected_information_gain=0.9,
            metrics=main.typical_metrics or ["primary_metric"],
            controls=["相同数据划分", "相同评价指标"],
            decision_rule=DecisionRule(
                metric="primary_metric",
                accept_if="improvement >= 3%",
                reject_if="improvement < 0%",
                refine_if="0% <= improvement < 3%")))

        # 2) evidence_requirements.minimum（priority=1）
        for req in main.evidence_minimum:
            entries.append(_entry(
                purpose=f"方法卡最低证据要求: {req}",
                hypothesis=f"{main.name} 在 {req} 上可复现且达标",
                method=req, priority=1, cost=2,
                expected_information_gain=0.7,
                metrics=main.typical_metrics,
                decision_rule=DecisionRule(
                    metric=req, accept_if="criteria_pass",
                    reject_if="criteria_fail", refine_if="borderline")))

        # 3) 失败记忆防线（P8-5 → P8-7 通道：high 级失败的恢复动作变成实验）
        for fm in self.retriever.failures_for(card_ids[0]):
            if fm.severity != "high":
                continue
            recovery = ", ".join(fm.recovery[:2]) if fm.recovery else fm.fix
            entries.append(_entry(
                purpose=f"失败防线: {fm.title}（severity=high）",
                hypothesis=f"按 recovery 执行后 {fm.failure_id} 不复现",
                method=recovery or "针对性验证",
                baseline="未采取防线的主方法", priority=1, cost=2,
                expected_information_gain=0.8,
                failure_detection=fm.detection_signal or fm.detection,
                decision_rule=DecisionRule(
                    metric="failure_recurrence",
                    accept_if="信号未触发", reject_if="信号触发且复现",
                    refine_if="信号触发但可归因为外部因素")))

        # 4) recommended 证据（priority=2）
        for req in main.evidence_recommended:
            entries.append(_entry(
                purpose=f"方法卡推荐增强证据: {req}",
                hypothesis=f"{req} 提升结论稳健性",
                method=req, priority=2, cost=3,
                expected_information_gain=0.4,
                decision_rule=DecisionRule(
                    metric=req, accept_if="criteria_pass",
                    reject_if="criteria_fail", refine_if="borderline")))

        # 5) 组合方法的消融对照
        if len(card_ids) > 1:
            entries.append(_entry(
                purpose=f"消融对照: 组合方法 {card_ids[1]} 的边际贡献",
                hypothesis="组合优于单一主方法",
                method=f"仅用 {card_ids[1]} 同口径对照", priority=2, cost=2,
                expected_information_gain=0.5,
                decision_rule=DecisionRule(
                    metric="marginal_gain",
                    accept_if="marginal_gain > 0", reject_if="marginal_gain <= 0",
                    refine_if="量级不显著")))
        return entries
