#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Question Dependency Contract（P12-1）—— 科学问题间依赖的唯一语义源。

冻结（任务书 §三）:
* dependency_type 五枚举，禁止自由文本;
* 双写一致性: State（dependency_records + 调度镜像）与 Registry（question
  artifact depends_on）必须一致，否则 integrity FAIL（D1）;
* 依赖必须显式声明（D2）——composer 的 `*` 展开只是问题集合展开，
  不产生 dependency；问题顺序不隐含科学依赖;
* 参与矩阵: 哪些类型参与 scheduling / invalidation / synthesis / aggregation;
* 科学依赖图必须无环（D6，检测到 cycle 直接 FAIL）;
* provenance: who → depends on whom → why → type → when（D8）。

参与矩阵（冻结）:
    type          | scheduling | invalidation(reval) | synthesis | aggregation
    execution      | yes        | no                  | no        | no
    methodological | no         | no                  | reference | no
    evidential     | yes        | yes                 | yes       | yes
    comparative    | no         | no                   | comparison| no
    extension      | no         | yes                 | yes       | yes
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEPENDENCY_TYPES = ("execution", "methodological", "evidential",
                    "comparative", "extension")

# 参与矩阵（P12-1 冻结；变更须改此处 + CROSS_QUESTION_SYNTHESIS_CONTRACT.md）
PARTICIPATION: dict[str, dict[str, bool]] = {
    "execution":      {"scheduling": True,  "invalidation": False,
                      "synthesis": False, "aggregation": False},
    "methodological": {"scheduling": False, "invalidation": False,
                      "synthesis": False, "aggregation": False},
    "evidential":     {"scheduling": True,  "invalidation": True,
                      "synthesis": True,  "aggregation": True},
    "comparative":    {"scheduling": False, "invalidation": False,
                      "synthesis": True,  "aggregation": False},
    "extension":      {"scheduling": False, "invalidation": True,
                      "synthesis": True,  "aggregation": True},
}

# 跨问题失效传播只允许 reval 档（D3/D4）：execution 永不传播（D3 钉死）
PROPAGATING_TYPES = tuple(t for t in DEPENDENCY_TYPES
                          if PARTICIPATION[t]["invalidation"])

_SCHEDULING_TYPES = tuple(t for t in DEPENDENCY_TYPES
                          if PARTICIPATION[t]["scheduling"])

_TERMINAL = ("invalidated", "superseded", "deprecated")


class DependencyError(ValueError):
    """依赖声明非法（未知类型 / 环 / 自依赖 / 缺失 question）。"""


@dataclass
class QuestionDependency:
    """一条科学依赖的完整 provenance（D8）。"""
    source_question: str          # 被依赖方（提供产物/证据）
    target_question: str          # 依赖方
    dependency_type: str          # DEPENDENCY_TYPES 之一
    reason: str
    created_by: str = ""
    at: str = ""

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "source_question", "target_question", "dependency_type",
            "reason", "created_by", "at")}


# ============================================================
# 声明（双写：State records + 调度镜像；Registry 镜像由调用方持 registry 完成）
# ============================================================

def dependency_records(state) -> list[dict]:
    return list(state.data.get("dependencies") or [])


def declare_dependency(state, registry, source_question: str,
                       target_question: str, dependency_type: str,
                       reason: str, created_by: str = "",
                       at: str = "") -> dict:
    """声明一条依赖并双写。返回 QuestionDependency dict。

    D2: 必须显式调用本函数（无任何隐式推导）；D6: 环检测 FAIL；
    D1: Registry 镜像（evidential/extension → target artifact depends_on）
    与 State records 同步落地。
    """
    from .model import _utcnow

    _validate_decl(state, registry, source_question, target_question,
                   dependency_type)
    rec = QuestionDependency(
        source_question=source_question, target_question=target_question,
        dependency_type=dependency_type, reason=reason,
        created_by=created_by, at=at or _utcnow())
    # State: 全量 provenance records
    state.data.setdefault("dependencies", []).append(rec.as_dict())
    # State: 调度镜像（scheduling 类型 → target 的 dependencies 列表，
    # 供 blocked_by_dependencies 消费）
    if PARTICIPATION[dependency_type]["scheduling"]:
        q = state.ensure_question(target_question)
        if source_question not in q["dependencies"]:
            q["dependencies"].append(source_question)
    # Registry: 科学传播类依赖镜像到 question artifact depends_on
    if dependency_type in ("evidential", "extension"):
        art = registry.get(target_question)
        if source_question not in (art.depends_on or []):
            art.depends_on.append(source_question)
    return rec.as_dict()


def _validate_decl(state, registry, source_question, target_question,
                   dependency_type):
    if dependency_type not in DEPENDENCY_TYPES:
        raise DependencyError(
            f"dependency_type 非法: {dependency_type!r}（合法: "
            f"{list(DEPENDENCY_TYPES)}）")
    if source_question == target_question:
        raise DependencyError(f"自依赖: {source_question}")
    qids = {a.artifact_id for a in registry.list_by_type("question")}
    for q in (source_question, target_question):
        if q not in qids:
            raise DependencyError(f"question 不存在: {q}")
    # D6: 环检测（source→target 加入后不得出现循环）
    records = dependency_records(state)
    edges: dict[str, set[str]] = {}
    for r in records:
        edges.setdefault(r["target_question"], set()).add(r["source_question"])
    edges.setdefault(target_question, set()).add(source_question)
    _assert_acyclic(edges, target_question)


def _assert_acyclic(edges: dict[str, set[str]], start: str) -> None:
    """D6: 从 start 出发沿"依赖方→被依赖方"走，回到起点即环。"""
    stack, seen = [start], set()
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        for nxt in edges.get(cur, ()):
            if nxt == start:
                raise DependencyError(
                    f"科学依赖图出现循环: {start} → … → {start}（P12-1 冻结："
                    "runtime 不猜测科学循环的解法，直接 FAIL）")
            stack.append(nxt)


# ============================================================
# 一致性（D1）
# ============================================================

def dependency_integrity_problems(registry, state) -> list[str]:
    """D1 双写一致性检查：Registry 镜像 vs State records。"""
    problems = []
    records = dependency_records(state)
    declared: dict[str, set[str]] = {}
    for r in records:
        # Registry 镜像只记录 evidence/extension（科学传播类），
        # execution 等其他类型走 State（调度）——见 declare_dependency
        if r["dependency_type"] in ("evidential", "extension"):
            declared.setdefault(r["target_question"], set()).add(
                r["source_question"])
    for a in registry.list_by_type("question"):
        mirror = set(a.depends_on or [])
        expected = declared.get(a.artifact_id, set())
        if mirror != expected:
            problems.append(
                f"{a.artifact_id}: Registry depends_on {sorted(mirror)} "
                f"≠ State 声明 {sorted(expected)}")
    # State 中声明了 evidential/extension 但 Registry 缺 question artifact
    qids = {a.artifact_id for a in registry.list_by_type("question")}
    for r in records:
        if r["target_question"] not in qids:
            problems.append(f"State 依赖的 question 不在 Registry: "
                            f"{r['target_question']}")
    return problems


# ============================================================
# 跨问题失效传播（D3/D4/D5）—— 只沿 evidential/extension 传播 reval
# ============================================================

def propagate_to_dependents(registry, state, source_question: str,
                            reason: str) -> list[dict]:
    """source question 证据失效 → 按 PARTICIPATION 向依赖方传播 requires_revalidation。

    * 只沿 PROPAGATING_TYPES 传播（D3: execution 永不传播）;
    * 只打 reval 标记，不判死（P7: superseded ≠ invalidated）;
    * 终态产物跳过（D5: terminal 不因 dependency 复活或变化）;
    * 返回 [{target_question, artifact_id}] 审计清单。
    """
    affected: list[dict] = []
    records = [r for r in dependency_records(state)
               if r["source_question"] == source_question
               and r["dependency_type"] in PROPAGATING_TYPES]
    for r in records:
        target = r["target_question"]
        for a in registry.all():
            if a.question != target or a.status in _TERMINAL:
                continue
            if a.type in ("question",):
                continue
            try:
                a.mark_invalidation("requires_revalidation",
                                    reason=f"[{r['dependency_type']}] {reason}",
                                    by="cross-question-propagation")
            except Exception:
                continue   # 终态等守卫
            affected.append({"target_question": target,
                             "artifact_id": a.artifact_id,
                             "dependency_type": r["dependency_type"]})
    return affected
