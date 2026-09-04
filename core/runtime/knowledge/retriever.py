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
class Recommendation:
    card: MethodCard
    score: int
    matched: list[str] = field(default_factory=list)       # 命中理由（人可读）
    warnings: list[str] = field(default_factory=list)      # 风险提示
    related_failures: list[FailureMemory] = field(default_factory=list)
    related_patterns: list[Pattern] = field(default_factory=list)

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
        }


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
                rec = Recommendation(card=card, score=score, matched=matched,
                                     warnings=list(card.risks),
                                     related_failures=self.failures_for(card.card_id),
                                     related_patterns=[
                                         p for p in self.patterns_for(list(pts))
                                         if card.card_id in p.cards])
                recs.append(rec)

        recs.sort(key=lambda r: (-r.score, r.card.card_id))
        return recs[:top_k]


SAMPLE_ORDER = {"small", "medium", "large"}
