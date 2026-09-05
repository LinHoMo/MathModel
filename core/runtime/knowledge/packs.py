#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Competition Pack 加载 + 知识冲突检测（P8-2 / P8-9）。

Competition Pack 是结构化竞赛画像（schema: v3/knowledge/competition_pack.schema.json），
消费方为 ModelArena / ExperimentPlanner / JudgeCritic。
CI-08 不变量：Pack 对 Runtime 只读——它只参与打分与计划，不直接改状态。

Conflict Detection（P8-9 最小实现）：能发现、能记录、能阻止 silent contradiction；
不要求自动解决。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .cards import CardError, _opt_level, _require_str, _require_str_list

PACK_ID_RE_PREFIX = "cp-"


@dataclass
class CompetitionPack:
    pack_id: str
    competition_type: str
    evaluation_dimensions: list[str]
    version: int = 1
    status: str = "active"
    problem_characteristics: list[str] = field(default_factory=list)
    common_problem_patterns: list[str] = field(default_factory=list)
    recommended_methods: list[str] = field(default_factory=list)   # family 或 card_id
    high_risk_methods: list[str] = field(default_factory=list)
    typical_model_combinations: list[str] = field(default_factory=list)
    typical_experiments: list[str] = field(default_factory=list)
    common_failure_modes: list[str] = field(default_factory=list)
    innovation_patterns: list[str] = field(default_factory=list)
    judging_preferences: list[str] = field(default_factory=list)
    paper_structure_expectations: list[str] = field(default_factory=list)
    time_constraints: dict = field(default_factory=dict)
    data_constraints: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    source_type: str = ""

    @classmethod
    def from_dict(cls, d: dict, where: str) -> "CompetitionPack":
        pack_id = _require_str(d, "pack_id", where)
        if not pack_id.startswith(PACK_ID_RE_PREFIX):
            raise CardError(f"{where}: pack_id 须以 cp- 开头: {pack_id!r}")
        tc = d.get("time_constraints", {})
        if tc and not isinstance(tc, dict):
            raise CardError(f"{where}: time_constraints 须为映射")
        return cls(
            pack_id=pack_id,
            competition_type=_require_str(d, "competition_type", where),
            evaluation_dimensions=_require_str_list(
                d, "evaluation_dimensions", where, min_items=1),
            version=d.get("version", 1) or 1,
            status=d.get("status", "active") or "active",
            problem_characteristics=_require_str_list(
                d, "problem_characteristics", where),
            common_problem_patterns=_require_str_list(
                d, "common_problem_patterns", where),
            recommended_methods=_require_str_list(d, "recommended_methods", where),
            high_risk_methods=_require_str_list(d, "high_risk_methods", where),
            typical_model_combinations=_require_str_list(
                d, "typical_model_combinations", where),
            typical_experiments=_require_str_list(d, "typical_experiments", where),
            common_failure_modes=_require_str_list(d, "common_failure_modes", where),
            innovation_patterns=_require_str_list(d, "innovation_patterns", where),
            judging_preferences=_require_str_list(d, "judging_preferences", where),
            paper_structure_expectations=_require_str_list(
                d, "paper_structure_expectations", where),
            time_constraints=dict(tc),
            data_constraints=_require_str_list(d, "data_constraints", where),
            source_refs=_require_str_list(d, "source_refs", where),
            source_type=d.get("source_type", "") or "",
        )


def load_competition_packs(knowledge_root: str | Path) -> dict[str, CompetitionPack]:
    """加载 core/knowledge/competition/cp-*.yaml（目录缺省 → 空，向后兼容）。"""
    root = Path(knowledge_root) / "competition"
    packs: dict[str, CompetitionPack] = {}
    if not root.is_dir():
        return packs
    for f in sorted(root.glob("cp-*.yaml")):
        from runtime.execution.yamlio import load_file  # 零依赖解析器
        data = load_file(f)
        pack = CompetitionPack.from_dict(data, str(f))
        if pack.pack_id in packs:
            raise CardError(f"{f}: pack_id 重复: {pack.pack_id}")
        packs[pack.pack_id] = pack
    return packs


# ============================================================
# P8-9 Knowledge Conflict Detection（能发现、能记录、能报告）
# ============================================================

@dataclass
class KnowledgeConflict:
    entity: str            # 冲突涉及的知识实体（card/failure/pattern id 或组合）
    field: str             # 冲突字段语义（compatible_incompatible / recommend_risk ...）
    source_a: str          # 甲方（id + 摘要）
    source_b: str          # 乙方
    severity: str          # low / medium / high
    detail: str = ""
    resolution_status: str = "open"    # open / acknowledged / resolved


def detect_knowledge_conflicts(cards, failures, patterns) -> list[KnowledgeConflict]:
    """最小冲突检测（规则显式可测试，不做黑盒）：

    C1 compatible × incompatible 交集     → high
    C2 recommended × high_risk（同族/同卡）→ medium
    C3 卡互斥组合 vs pattern.cards 共存   → medium
    """
    conflicts: list[KnowledgeConflict] = []
    by_id = cards

    # C1: 一张卡声称与 X compatible，另一张声明 X incompatible（含反向）
    for cid, card in by_id.items():
        for other in card.incompatible_methods:
            other_card = by_id.get(other)
            if other_card and cid in other_card.incompatible_methods:
                continue  # 双向互斥：一致，无冲突
            if other_card and other in card.incompatible_methods:
                continue
            if other_card and cid in other_card.compatible_methods \
                    and other in card.compatible_methods:
                continue
            # A 说和 B incompatible，B 却说和 A compatible → 矛盾
            if other_card and cid in other_card.compatible_methods:
                conflicts.append(KnowledgeConflict(
                    entity=f"{cid}×{other}", field="compatible_incompatible",
                    source_a=f"{cid}.incompatible_methods 含 {other}",
                    source_b=f"{other}.compatible_methods 含 {cid}",
                    severity="high",
                    detail="单侧互斥 + 单侧兼容 → silent contradiction"))
        # 自身 compatible/incompatible 交集
        inter = set(card.compatible_methods) & set(card.incompatible_methods)
        if inter:
            conflicts.append(KnowledgeConflict(
                entity=cid, field="compatible_incompatible",
                source_a=f"{cid}.compatible_methods",
                source_b=f"{cid}.incompatible_methods",
                severity="high",
                detail=f"同卡内同时兼容与互斥: {sorted(inter)}"))

    # C2: 卡推荐的问题类型被高严重度失败记忆命中（applies_to 反指）
    for cid, card in by_id.items():
        for fm in failures.values():
            if cid in fm.applies_to and fm.severity == "high" \
                    and card.status == "active":
                conflicts.append(KnowledgeConflict(
                    entity=f"{cid}×{fm.failure_id}", field="recommend_vs_high_risk",
                    source_a=f"{cid} 推荐 {card.problem_types}",
                    source_b=f"{fm.failure_id} severity=high applies_to {cid}",
                    severity="medium",
                    detail="推荐方法存在 high 级失败记忆：需在打分中体现 risk "
                           "penalty + required validation（P8-5 消费，非删除知识）"))

    # C3: pattern 引用不存在的卡
    for pid, pat in patterns.items():
        for cid in pat.cards:
            if cid not in by_id:
                conflicts.append(KnowledgeConflict(
                    entity=f"{pid}×{cid}", field="pattern_card_missing",
                    source_a=f"{pid}.cards 含 {cid}",
                    source_b="cards 集合无此 id",
                    severity="medium",
                    detail="创新模式引用不存在的方法卡"))
    return conflicts
