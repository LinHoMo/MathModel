"""KnowledgeRetriever — 知识检索 API（V3 P2）。

输入问题特征向量（problem_types / has_data / sample_size / time_series /
objectives / uncertainty），输出排序后的决策建议包：候选方法卡 + 打分理由 +
必做验证 + 关联失败记忆 + 关联创新模式。

打分规则（全部显式、可测试）:
    problem_types 交集     每命中 +3
    requires_data 矛盾     无数据却要数据 → 排除
    sample_size 不兼容     样本档不在卡兼容集 → 排除（未知样本档不排除）
    time_series 匹配       相同 +1 / 相反 -4（纯时序方法不得进入非时序问题；null 卡不参与）
    objectives >= 2        multi_objective 卡 +2 / 单目标卡 -1
    uncertainty            handles_uncertainty 卡 +2
只返回 score > 0 的建议，按分数降序；并列按 card_id 字典序稳定排序。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .cards import FailureMemory, MethodCard, Pattern, load_knowledge


@dataclass
class RecommendationScore:
    """维度化推荐分（P8-3）：total 必须可拆解，每个维度可解释。"""
    fit: int = 0                 # 问题类型/能力匹配（0-40）
    data: int = 0                # 数据条件匹配（0-15）
    interpretability: int = 0    # 可解释性（0-10）
    robustness: int = 0          # 稳健性（0-10）
    complexity: int = 0          # 复杂度适配（0-5，越简单越高）
    innovation: int = 0          # 创新潜力（0-10）
    competition: int = 0         # 竞赛适配（0-10）
    evidence_cost: int = 0       # 证据成本（0-5，越低越高）
    risk_penalty: int = 0        # 风险罚分（≤0，来自 risk 字段 + 失败记忆）

    @property
    def total(self) -> int:
        d = self.as_dict()
        return sum(v for k, v in d.items() if k != "risk_penalty")             + self.risk_penalty

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "fit", "data", "interpretability", "robustness", "complexity",
            "innovation", "competition", "evidence_cost", "risk_penalty")}


@dataclass
class Recommendation:
    card: MethodCard
    score: int
    matched: list[str] = field(default_factory=list)       # 命中理由（人可读）
    warnings: list[str] = field(default_factory=list)      # 风险提示
    related_failures: list[FailureMemory] = field(default_factory=list)
    related_patterns: list[Pattern] = field(default_factory=list)
    # ---- P8 决策扩展 ----
    score_detail: RecommendationScore = field(default_factory=RecommendationScore)
    matched_capabilities: list[str] = field(default_factory=list)
    missing_capabilities: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)        # 结构化风险（含来源）
    required_experiments: list[str] = field(default_factory=list)
    knowledge_refs: list[dict] = field(default_factory=list)  # [{id, version}]

    def as_dict(self) -> dict:
        return {
            "card_id": self.card.card_id,
            "name": self.card.name,
            "family": self.card.family,
            "score": self.score,
            "matched": self.matched,
            "good_for": self.card.good_for,
            "requires": self.card.requires,
            "warnings": self.warnings or self.card.risks,
            "validation": self.card.validation,
            "often_combined_with": self.card.often_combined_with,
            "related_failures": [
                {"failure_id": f.failure_id, "title": f.title,
                 "avoidance": f.avoidance} for f in self.related_failures],
            "related_patterns": [
                {"pattern_id": p.pattern_id, "title": p.title,
                 "innovation": p.innovation} for p in self.related_patterns],
            "score_detail": self.score_detail.as_dict()
            | {"total": self.score_detail.total},
            "matched_capabilities": self.matched_capabilities,
            "missing_capabilities": self.missing_capabilities,
            "violations": self.violations,
            "risks": self.risks,
            "required_experiments": self.required_experiments,
            "knowledge_refs": self.knowledge_refs,
            "reasoning": self.reasoning(),
        }

    def reasoning(self) -> str:
        """P8 可解释性：为什么推荐 / 为什么不靠前 / 依据是什么。"""
        sd = self.score_detail
        parts = [f"total={self.score}（fit={sd.fit} data={sd.data} "
                 f"interpretable={sd.interpretability} robust={sd.robustness} "
                 f"innovation={sd.innovation} competition={sd.competition} "
                 f"risk_penalty={sd.risk_penalty}）"]
        if self.matched_capabilities:
            parts.append("命中: " + ", ".join(self.matched_capabilities))
        if self.missing_capabilities:
            parts.append("缺失: " + ", ".join(self.missing_capabilities))
        if self.violations:
            parts.append("违反: " + ", ".join(self.violations))
        if self.required_experiments:
            parts.append("必做实验: " + ", ".join(self.required_experiments))
        return "；".join(parts)


class KnowledgeRetriever:
    """检索器。构造时加载知识库（fail-closed，契约违反抛 CardError）。"""

    def __init__(self, knowledge_root: str | Path):
        self.root = Path(knowledge_root)
        self.cards, self.failures, self.patterns = load_knowledge(self.root)

    # ------------------------------------------------------------ 查询

    def card(self, card_id: str) -> MethodCard:
        return self.cards[card_id]

    def failure(self, failure_id: str) -> FailureMemory:
        return self.failures[failure_id]

    def pattern(self, pattern_id: str) -> Pattern:
        return self.patterns[pattern_id]

    def failures_for(self, card_id: str) -> list[FailureMemory]:
        """方法卡的关联失败：known_failures 显式引用 + method_family 匹配 + applies_to 反向引用。"""
        card = self.cards[card_id]
        out = []
        seen: set[str] = set()
        for fid in card.known_failures:
            if fid not in seen:
                out.append(self.failures[fid])
                seen.add(fid)
        for fm in self.failures.values():
            if fm.failure_id in seen:
                continue
            if fm.method_family == card.family or card_id in fm.applies_to:
                out.append(fm)
                seen.add(fm.failure_id)
        return out

    def patterns_for(self, problem_types: list[str]) -> list[Pattern]:
        """按问题类型交集推荐创新模式（交集大小降序）。"""
        scored = []
        for pat in self.patterns.values():
            overlap = set(pat.problem_types) & set(problem_types)
            if overlap:
                scored.append((-len(overlap), pat.pattern_id, pat))
        scored.sort(key=lambda t: (t[0], t[1]))
        return [p for _, _, p in scored]

    # ------------------------------------------------------------ 检索

    def recommend(self, features: dict, top_k: int = 5) -> list[Recommendation]:
        """输入问题特征，输出排序建议包。

        features 键（均可选，缺省不参与打分/过滤）:
            problem_types: list[str]  问题类型标签
            has_data: bool            是否有题给数据
            sample_size: str          small(<200) / medium(200-1000) / large(>=1000)
            time_series: bool         是否时间演化
            objectives: int           目标数
            uncertainty: bool         是否含不确定性
        """
        pts = set(features.get("problem_types") or [])
        has_data = features.get("has_data")
        sample_size = features.get("sample_size")
        time_series = features.get("time_series")
        objectives = features.get("objectives")
        uncertainty = features.get("uncertainty")

        recs: list[Recommendation] = []
        for card in self.cards.values():
            score = 0
            matched: list[str] = []

            overlap = pts & set(card.problem_types)
            if overlap:
                score += 3 * len(overlap)
                matched.append(f"问题类型命中: {', '.join(sorted(overlap))}")

            if card.requires_data and has_data is False:
                continue  # 无数据却要数据 → 排除
            if sample_size in SAMPLE_ORDER and card.sample_size and \
                    sample_size not in card.sample_size:
                continue  # 样本档不兼容 → 排除
            if card.requires_data and has_data is None and pts:
                matched.append("需确认数据可得性（该卡要求题给数据）")

            if time_series is not None and card.time_series is not None:
                if card.time_series == time_series:
                    score += 1
                    matched.append("时序特征匹配" if time_series else "非时序特征匹配")
                else:
                    score -= 4

            if isinstance(objectives, int) and objectives >= 2:
                if card.multi_objective:
                    score += 2
                    matched.append("多目标适配")
                else:
                    score -= 1

            if uncertainty and card.handles_uncertainty:
                score += 2
                matched.append("不确定性处理能力")

            if score > 0:
                related = self.failures_for(card.card_id)
                sd, caps, missing, violations, risks, req_exp =                     self._capability_match(card, features, related, pts)
                sd.fit += score          # legacy 标签分并入 fit（拆解恒等）
                rec = Recommendation(
                    card=card, score=sd.total, matched=matched,
                    warnings=list(card.risks), related_failures=related,
                    related_patterns=[p for p in self.patterns_for(list(pts))
                                      if card.card_id in p.cards],
                    score_detail=sd, matched_capabilities=caps,
                    missing_capabilities=missing, violations=violations,
                    risks=risks, required_experiments=req_exp,
                    knowledge_refs=[{"id": card.card_id,
                                     "version": card.version}])
                recs.append(rec)

        recs.sort(key=lambda r: (-r.score, r.card.card_id))
        return recs[:top_k]

    # ------------------------------------------------------------ P8-3 Capability Matching

    def _capability_match(self, card, features, related_failures, pts):
        """结构化适用条件 → 维度分 + 命中/缺失/违反 + 结构化风险 + 必做实验。

        全部确定性规则（P8 硬约束 7：不为"看起来智能"堆规则）。
        """
        sd = RecommendationScore()
        caps: list[str] = []
        missing: list[str] = []
        violations: list[str] = []
        risks: list[dict] = []
        req_exp: list[str] = list(card.evidence_minimum)

        # ---- fit：applicability 命中/缺失/违反 ----
        sd.fit = min(40, 20 + 4 * len(card.applicability_positive))
        for cond in card.applicability_positive:
            key = _cond_key(cond)
            if key and _cond_satisfied(key, features):
                caps.append(key)
                sd.fit = min(40, sd.fit + 4)
            else:
                missing.append(key or cond)
        for cond in card.applicability_negative:
            key = _cond_key(cond)
            if key and _cond_satisfied(key, features):
                violations.append(f"命中否定条件: {cond}")
                sd.fit = max(0, sd.fit - 10)
        for cond in card.required_conditions:
            key = _cond_key(cond)
            if key and not _cond_satisfied(key, features):
                violations.append(f"硬前提未满足: {cond}")
                sd.fit = max(0, sd.fit - 15)

        # ---- data：成本与可得性 ----
        cost_data = card.costs.get("data", "medium")
        sd.data = {"low": 15, "medium": 10, "high": 5}.get(cost_data, 10)
        if features.get("has_data") is False and card.requires_data:
            violations.append("需要题给数据但无数据")
            sd.data = 0
        if features.get("sample_size") in SAMPLE_ORDER                 and card.sample_size                 and features["sample_size"] not in card.sample_size:
            violations.append(
                f"样本档 {features['sample_size']} 不在兼容档 {card.sample_size}")
            sd.data = max(0, sd.data - 8)

        # ---- interpretability / robustness / complexity / innovation ----
        sd.interpretability = {"high": 10, "medium": 6, "low": 2}.get(
            card.interpretability, 5)
        sd.robustness = {"high": 10, "medium": 6, "low": 2}.get(
            card.robustness, 5)
        sd.complexity = {"low": 5, "medium": 3, "high": 1}.get(
            card.costs.get("compute", "medium"), 3)
        sd.innovation = {"high": 10, "medium": 6, "low": 2}.get(
            card.innovation_potential, 4)
        sd.competition = {"high": 10, "medium": 6, "low": 2}.get(
            card.competition_suitability, 5)
        sd.evidence_cost = {"low": 5, "medium": 3, "high": 1}.get(
            "high" if len(card.evidence_minimum) >= 2 else
            "medium" if card.evidence_minimum else "low", 3)

        # ---- risk_penalty：卡片结构化 risk + 失败记忆（P8-5 决策闭环）----
        _SEV = {"low": -1, "medium": -3, "high": -6}
        for dim, level in card.risk.items():
            if level in _LEVELS:
                sd.risk_penalty += _SEV[level]
                if level != "low":
                    risks.append({"source": "card", "dim": dim,
                                  "level": level})
        for fm in related_failures:
            sev = fm.severity if fm.severity in _LEVELS else "medium"
            sd.risk_penalty += _SEV[sev]
            risks.append({"source": "failure_memory", "id": fm.failure_id,
                          "level": sev, "title": fm.title})
            # high 级失败 → 强制验证（失败记忆改变实验需求，而非删除知识）
            if sev == "high" and fm.recovery:
                req_exp.append(f"failure-guard[{fm.failure_id}]:" +
                               ",".join(fm.recovery[:2]))
            elif sev == "high":
                req_exp.append(f"failure-guard[{fm.failure_id}]:"
                               "加强该失败对应的验证并复现对照")
        return sd, caps, missing, violations, risks, req_exp


_LEVELS = {"low", "medium", "high"}


def _cond_key(cond: str) -> str:
    """能力条件 → 可判定键（snake_case 首段），无法判定返回空。"""
    key = cond.strip().lower().replace(" ", "_").replace("-", "_")
    return key


_KNOWN_CONDITIONS = {
    "temporal_dependency": lambda f: bool(f.get("time_series")),
    "time_series": lambda f: bool(f.get("time_series")),
    "stationary_or_transformable": lambda f: bool(f.get("time_series")),
    "small_sample": lambda f: f.get("sample_size") == "small",
    "small_sample_friendly": lambda f: f.get("sample_size") == "small",
    "large_sample": lambda f: f.get("sample_size") == "large",
    "medium_sample": lambda f: f.get("sample_size") in ("medium", "large"),
    "has_data": lambda f: f.get("has_data") is True,
    "data_available": lambda f: f.get("has_data") is True,
    "high_dimensional_features": lambda f: bool(f.get("high_dimensional")),
    "strong_non_linear_interaction": lambda f: bool(f.get("nonlinear")),
    "nonlinearity": lambda f: bool(f.get("nonlinear")),
    "multi_objective": lambda f: f.get("objectives", 1) >= 2,
    "uncertainty": lambda f: bool(f.get("uncertainty")),
    "interpretability_required": lambda f: bool(f.get("interpretability_required")),
    "mechanism_known": lambda f: bool(f.get("mechanism_known")),
}


def _cond_satisfied(key: str, features: dict) -> bool:
    fn = _KNOWN_CONDITIONS.get(key)
    return bool(fn(features)) if fn else False


SAMPLE_ORDER = {"small", "medium", "large"}
