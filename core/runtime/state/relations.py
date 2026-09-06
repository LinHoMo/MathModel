#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-Question Relation Contract（P12-2）—— 跨问题科学关系的唯一语义源。

冻结（任务书 §①–④）:
* 跨问题合法关系类型: compares / extends / derived_from（其余类型跨问题一律拒绝）;
* 跨问题关系必须携带 dependency_refs，且能回指 P12-1 的 QuestionDependency
  记录——没有 dependency provenance 的关系 = invalid（不允许"先建后猜"）;
* 同问题 derived_from 保持现有语义（直接走 EvidenceGraph 边，不经本契约）;
* Question label ≠ Artifact ID（身份冻结）：所有关系经 Registry 真实 identity
  建立，不得按 questions 数组位置推断 ID;
* 失效语义: 上游失效 → 关系 status = requires_revalidation（可逆的记账标记，
  reval ≠ invalidation）；关系永远不进入 P7 终态（派生记录，重派生即更新）。

依赖类型配对（冻结）:
    compares     ← comparative | evidential
    extends      ← evidential | extension
    derived_from  ← evidential | extension
execution 依赖不能支撑任何跨问题科学关系（D3 延伸）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

CROSS_RELATION_TYPES = ("compares", "extends", "derived_from")

# 关系类型 → 允许的 dependency_type（P12-2 冻结）
ALLOWED_DEPENDENCY_TYPES: dict[str, tuple[str, ...]] = {
    "compares": ("comparative", "evidential"),
    "extends": ("evidential", "extension"),
    "derived_from": ("evidential", "extension"),
}

RELATION_STATUSES = ("active", "requires_revalidation")


class RelationError(ValueError):
    """跨问题关系声明非法。"""


@dataclass
class CrossQuestionRelation:
    relation_id: str
    source: str                    # artifact id（Registry 真实 identity）
    target: str
    relation_type: str              # CROSS_RELATION_TYPES 之一
    source_question: str
    target_question: str
    dependency_refs: list[dict] = field(default_factory=list)  # P12-1 records
    created_by: str = ""
    at: str = ""
    status: str = "active"          # active / requires_revalidation（无终态）

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "relation_id", "source", "target", "relation_type",
            "source_question", "target_question", "dependency_refs",
            "created_by", "at", "status")}


# ============================================================
# 身份规则（P12-2 冻结）：label ≠ Artifact ID
# ============================================================

def resolve_question_id(registry, label_or_id: str) -> str:
    """只按 Registry 真实 identity 解析 question：
    artifact_id 精确匹配，或 title 精确匹配；二者皆无 → RelationError。
    禁止按 questions 数组位置推断。"""
    for a in registry.list_by_type("question"):
        if a.artifact_id == label_or_id:
            return a.artifact_id
    for a in registry.list_by_type("question"):
        if a.title == label_or_id:
            return a.artifact_id
    raise RelationError(f"question 无法解析（label ≠ Artifact ID）: {label_or_id!r}")


def _question_of(registry, artifact_id: str) -> str:
    a = registry.get(artifact_id)
    if a.type == "question":
        return a.artifact_id
    return a.question or ""


# ============================================================
# 声明
# ============================================================

def cross_relations(state) -> list[dict]:
    return list(state.data.get("cross_question_relations") or [])


def declare_cross_relation(state, registry, source: str, target: str,
                           relation_type: str, dependency_refs: list[dict],
                           created_by: str = "", at: str = "") -> dict:
    """声明并持久化一条跨问题关系。验证全部 fail-closed：

    R-a 类型合法; R-b 双方 artifact 存在且分属不同 question;
    R-c dependency_refs 必须回指 P12-1 records 且类型配对合法;
    R-d derived_from 额外写入 EvidenceGraph 边（同问题 derived_from 不走此契约）。
    """
    from .model import _utcnow
    from .dependencies import dependency_records

    if relation_type not in CROSS_RELATION_TYPES:
        raise RelationError(f"relation_type 非法: {relation_type!r}（合法: "
                            f"{list(CROSS_RELATION_TYPES)}）")
    src_q = _question_of(registry, source)
    tgt_q = _question_of(registry, target)
    if not src_q or not tgt_q:
        raise RelationError("关系端点必须归属 question")
    if src_q == tgt_q:
        raise RelationError(
            "同问题关系不经 Cross-Question 契约（使用 EvidenceGraph 边）")

    # R-c: dependency_refs 回指校验（无 provenance = invalid）
    records = dependency_records(state)
    if not dependency_refs:
        raise RelationError(
            f"跨问题 {relation_type} 缺少 dependency_refs（无 provenance = "
            "invalid，P12-2 冻结）")
    for ref in dependency_refs:
        # 指向校验前置：依赖必须连接关系两端的问题（无向匹配）
        pair = {ref.get("source_question"), ref.get("target_question")}
        if pair != {src_q, tgt_q}:
            raise RelationError(
                f"dependency 指向错误问题: {pair} ≠ {{{src_q}, {tgt_q}}}")
        match = [r for r in records
                 if r["source_question"] == ref.get("source_question")
                 and r["target_question"] == ref.get("target_question")
                 and r["dependency_type"] == ref.get("dependency_type")]
        if not match:
            raise RelationError(
                f"dependency_ref 不存在: {ref}（必须回指 P12-1 记录）")
        if ref.get("dependency_type") not in \
                ALLOWED_DEPENDENCY_TYPES[relation_type]:
            raise RelationError(
                f"{relation_type} 不接受 dependency_type="
                f"{ref.get('dependency_type')!r}（合法: "
                f"{ALLOWED_DEPENDENCY_TYPES[relation_type]}）")

    seq = len(cross_relations(state)) + 1
    rec = CrossQuestionRelation(
        relation_id=f"CQR-{seq:03d}", source=source, target=target,
        relation_type=relation_type, source_question=src_q,
        target_question=tgt_q,
        dependency_refs=[dict(r) for r in dependency_refs],
        created_by=created_by, at=at or _utcnow())
    state.data.setdefault("cross_question_relations", []).append(rec.as_dict())

    # R-d: derived_from 落物理边（同问题边已由既有语义覆盖）
    if relation_type == "derived_from":
        self_edge = any(e["from"] == source and e["to"] == target
                        and e["relation"] == "derived_from"
                        for e in self_graph_edges(state))
        if not self_edge:
            try:
                registry.get(source)  # 存在性（fail-closed）
                state.data.setdefault("cross_question_derived_edges",
                                      []).append({"from": source,
                                                  "relation": "derived_from",
                                                  "to": target})
            except Exception as e:  # pragma: no cover
                raise RelationError(f"derived_from 边写入失败: {e}")
    return rec.as_dict()


def self_graph_edges(state) -> list[dict]:
    """跨问题 derived_from 的物理边登记（State 层审计副本，不进 EvidenceGraph:
    compares/extends 无物理边类型，derived_from 的边登记保持派生层一致性）。"""
    return list(state.data.get("cross_question_derived_edges") or [])


# ============================================================
# 失效语义（④）：上游失效 → requires_revalidation（可逆记账）
# ============================================================

def mark_relations_for_revalidation(state, dead_question: str,
                                    reason: str) -> list[str]:
    """dead_question 参与的跨问题关系 → requires_revalidation。

    执行依赖从不进入本契约（构造期已拒绝），因此 D3 语义自动保持。
    reval ≠ invalidation：状态可逆，不产生 P7 终态。
    """
    changed = []
    for r in state.data.get("cross_question_relations") or []:
        if r["status"] == "active" and dead_question in (
                r["source_question"], r["target_question"]):
            r["status"] = "requires_revalidation"
            changed.append(r["relation_id"])
    return changed
