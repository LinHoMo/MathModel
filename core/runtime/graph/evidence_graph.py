"""Evidence Graph — Artifact 之间的 typed relation 集合 + 失效传播。

回答两个问题:
    1. 哪些证据支撑哪些 Claim（coverage / traceability）
    2. 上游失效时，下游哪些 Artifact 被波及（invalidation propagation）

设计（与 docs/architecture/V3.1_ARCHITECTURE.md §1.3 / §1.12 一致）:
    * 节点 = Stable ID（必须已在 ArtifactRegistry 注册）
    * 边   = 14 种 typed relation，全部单向、语义固定
    * 强边（上游死了下游也死）: solved_by / implemented_by / validated_by /
      uses / assumes / produces / visualized_by / supports / selects / based_on
    * 弱边（上游死了下游只需复查）: appears_in / derived_from
    * 传播分级: invalidated / requires_revalidation / dirty / unaffected
    * 传播用不动点迭代（图小，性能无虞），绝不全删——只标记，不删除。

持久化: projects/<p>/state/evidence_graph.json（graph_version 每次保存 +1）。
与 Registry 的关系: Graph 负责关系推导，Registry 负责对象落地——
传播判定结果通过 Registry 的 mark_* 方法写回 Artifact contract。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

GRAPH_VERSION = 3

# ---------------------------------------------------------------- 关系类型

# relation -> (允许的 from 类型集合, 允许的 to 类型集合)；None 表示任意类型
RELATION_TYPES: dict[str, tuple] = {
    "motivates":      ({"problem"}, {"question"}),
    "solved_by":      ({"question"}, {"model"}),
    "assumes":        ({"model"}, {"assumption"}),
    "implemented_by": ({"model"}, {"code"}),
    "validated_by":   ({"model"}, {"experiment"}),
    "tests":          ({"experiment"}, {"model"}),
    "uses":           ({"experiment"}, {"dataset", "code"}),
    "produces":       ({"experiment"}, {"result"}),
    "visualized_by":  ({"result"}, {"figure", "table"}),
    "supports":       ({"result"}, {"claim"}),
    "appears_in":     ({"claim"}, {"paper_section"}),
    "selects":        ({"decision"}, {"model"}),
    "based_on":       ({"decision"}, None),
    "derived_from":   (None, None),
}

STRONG_RELATIONS = frozenset({
    "solved_by", "implemented_by", "validated_by", "uses", "assumes",
    "produces", "visualized_by", "supports", "selects", "based_on",
})
WEAK_RELATIONS = frozenset({"appears_in", "derived_from"})

# ------------------------------------------------------------- 传播语义
#
# 失效传播不是"沿所有边无脑洪水填充"。每条 relation 按方向分档:
#   kill  : 上游死 → 下游判死（若下游的全部 kill 支撑都死了）
#   reval : 上游死 → 下游只需复查（requires_revalidation）
#   None  : 不传播（如 tests——实验死了模型不受影响）
#
# (forward_tier, reverse_tier):
#   forward = from 死时 to 受影响；reverse = to 死时 from 受影响
_PROPAGATION: dict[str, tuple] = {
    "motivates":      ("kill", None),      # 问题死了，子问题失去存在依据
    "solved_by":      ("kill", None),      # 问题死了，求解它的模型 moot
    "assumes":        (None, "reval"),     # 假设死了 → 模型需重推导（可修补，不直接判死）
    "implemented_by": ("kill", None),      # 模型死了，实现它的代码 moot
    "validated_by":   ("kill", None),      # 模型死了，验证它的实验 moot
    "tests":          (None, None),        # 实验死了，被测模型不受影响
    "uses":           (None, "kill"),      # 数据/代码死了，使用它的实验判死
    "produces":       ("kill", None),      # 实验死了，其产出结果判死
    "visualized_by":  ("kill", None),      # 结果死了，其图表判死
    "supports":       ("kill", None),      # 结果死了，其支撑的 claim 受影响
    "appears_in":     ("reval", None),     # claim 死了，出现的章节只需复查
    "selects":        (None, None),        # 决策死了，被选模型不受影响
    "based_on":       (None, "reval"),     # 证据死了，基于它的决策需复查
    "derived_from":   ("reval", "reval"),  # 通用派生：一律弱传播
}


def propagation_tiers(relation: str) -> tuple:
    """返回 (forward_tier, reverse_tier)；tier ∈ {"kill", "reval", None}。"""
    return _PROPAGATION.get(relation, (None, None))

# 传播判定类别
INVALIDATED = "invalidated"
REQUIRES_REVALIDATION = "requires_revalidation"
DIRTY = "dirty"


class GraphError(ValueError):
    """Evidence Graph 操作非法。"""


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class EvidenceGraph:
    """Typed relation 图 + invalidation 传播引擎。

    用法:
        graph = EvidenceGraph(registry, path=proj/"state/evidence_graph.json")
        graph.add_relation("Q001", "solved_by", "M001")
        report = graph.invalidate("DATA003", reason="数据源勘误")
    """

    def __init__(self, registry, path: str | Path | None = None):
        self.registry = registry
        self.path = Path(path) if path else None
        self.relations: list[dict] = []   # [{from, relation, to, at}]
        self.graph_version: int = 0
        # P7 并发契约：并行节点同时登记关系/剪边必须互斥
        import threading
        self._lock = threading.RLock()
        if self.path and self.path.exists():
            self.load()

    # ------------------------------------------------------------ 持久化

    def load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if raw.get("graph_schema_version") != GRAPH_VERSION:
            raise GraphError(
                f"evidence_graph.json 版本不兼容: {raw.get('graph_schema_version')!r}")
        self.graph_version = int(raw.get("graph_version", 0))
        self.relations = list(raw.get("relations", []))

    def save(self) -> None:
        if not self.path:
            raise GraphError("未配置持久化路径，无法 save()")
        self.graph_version += 1
        payload = {
            "graph_schema_version": GRAPH_VERSION,
            "graph_version": self.graph_version,
            "project": self.registry.project,
            "updated_at": _utcnow(),
            "relations": self.relations,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # ------------------------------------------------------------ 关系操作

    def _type_of(self, artifact_id: str) -> str:
        art = self.registry.get(artifact_id)   # ArtifactNotFound 向上抛
        return art.type

    def add_relation(self, from_id: str, relation: str, to_id: str,
                     *, check_types: bool = True) -> dict:
        """登记 typed relation（fail-closed：ID 不存在 / 类型不匹配 / 自环 / 重复 均拒绝）。"""
        with self._lock:
            return self._add_relation_locked(from_id, relation, to_id,
                                             check_types=check_types)

    def _add_relation_locked(self, from_id, relation, to_id,
                             *, check_types=True) -> dict:
        if relation not in RELATION_TYPES:
            raise GraphError(f"未知 relation 类型: {relation!r}（合法: {sorted(RELATION_TYPES)}）")
        if from_id == to_id:
            raise GraphError(f"不允许自环: {from_id} -{relation}-> {from_id}")
        # ID 必须已注册（同时校验存在性）
        from_type = self._type_of(from_id)
        to_type = self._type_of(to_id)
        if check_types:
            ft, tt = RELATION_TYPES[relation]
            if ft is not None and from_type not in ft:
                raise GraphError(
                    f"relation {relation!r} 的 from 必须是 {sorted(ft)}，"
                    f"实际 {from_id} 是 {from_type}")
            if tt is not None and to_type not in tt:
                raise GraphError(
                    f"relation {relation!r} 的 to 必须是 {sorted(tt)}，"
                    f"实际 {to_id} 是 {to_type}")
        for rel in self.relations:
            if (rel["from"], rel["relation"], rel["to"]) == (from_id, relation, to_id):
                raise GraphError(f"关系已存在: {from_id} -{relation}-> {to_id}")
        edge = {"from": from_id, "relation": relation, "to": to_id, "at": _utcnow()}
        self.relations.append(edge)
        self._sync_artifact_view(from_id)
        self._sync_artifact_view(to_id)
        return edge

    def remove_relation(self, from_id: str, relation: str, to_id: str) -> None:
        before = len(self.relations)
        self.relations = [r for r in self.relations
                          if not (r["from"] == from_id and r["relation"] == relation
                                  and r["to"] == to_id)]
        if len(self.relations) == before:
            raise GraphError(f"关系不存在: {from_id} -{relation}-> {to_id}")
        self._sync_artifact_view(from_id)
        self._sync_artifact_view(to_id)

    # ------------------------------------------------------------ 查询

    def out_edges(self, artifact_id: str) -> list[dict]:
        return [r for r in self.relations if r["from"] == artifact_id]

    def in_edges(self, artifact_id: str) -> list[dict]:
        return [r for r in self.relations if r["to"] == artifact_id]

    def relations_of(self, artifact_id: str) -> list[dict]:
        return self.out_edges(artifact_id) + self.in_edges(artifact_id)

    def downstream(self, artifact_id: str) -> set[str]:
        """失效会波及的所有下游节点（沿传播方向遍历，不含自身）。

        传播方向 = forward tier 的出边 + reverse tier 的入边。
        """
        seen: set[str] = set()
        frontier = [artifact_id]
        while frontier:
            cur = frontier.pop()
            for e in self.out_edges(cur):
                if _PROPAGATION.get(e["relation"], (None, None))[0] \
                        and e["to"] not in seen:
                    seen.add(e["to"])
                    frontier.append(e["to"])
            for e in self.in_edges(cur):
                if _PROPAGATION.get(e["relation"], (None, None))[1] \
                        and e["from"] not in seen:
                    seen.add(e["from"])
                    frontier.append(e["from"])
        return seen

    def upstream(self, artifact_id: str) -> set[str]:
        """失效会波及本节点的所有上游节点（downstream 的反向，不含自身）。"""
        seen: set[str] = set()
        frontier = [artifact_id]
        while frontier:
            cur = frontier.pop()
            for e in self.in_edges(cur):
                if _PROPAGATION.get(e["relation"], (None, None))[0] \
                        and e["from"] not in seen:
                    seen.add(e["from"])
                    frontier.append(e["from"])
            for e in self.out_edges(cur):
                if _PROPAGATION.get(e["relation"], (None, None))[1] \
                        and e["to"] not in seen:
                    seen.add(e["to"])
                    frontier.append(e["to"])
        return seen

    def killer_supports(self, artifact_id: str) -> set[str]:
        """会判死该节点的 kill 级支撑集合。

        来源有二:
          * 入边的 forward tier = kill（如 experiment produces result）
          * 出边的 reverse tier = kill（如 experiment uses dataset——数据死了实验判死）
        判死条件: killer_supports 非空且全部死亡。部分死亡 → requires_revalidation。
        """
        sups: set[str] = set()
        for e in self.in_edges(artifact_id):
            if _PROPAGATION.get(e["relation"], (None, None))[0] == "kill":
                sups.add(e["from"])
        for e in self.out_edges(artifact_id):
            if _PROPAGATION.get(e["relation"], (None, None))[1] == "kill":
                sups.add(e["to"])
        return sups

    def coverage(self) -> dict:
        """Claim 支撑覆盖率（Evidence Gate 的核心指标）。"""
        terminal = {"invalidated", "superseded", "deprecated"}
        claims = [a.artifact_id for a in self.registry.list_by_type("claim")
                  if a.status not in terminal]
        supported = [c for c in claims
                     if any(e["relation"] == "supports" and e["to"] == c
                            for e in self.relations)]
        return {
            "claims_total": len(claims),
            "claims_supported": len(supported),
            "claims_unsupported": len(claims) - len(supported),
            "coverage_ratio": round(len(supported) / len(claims), 4) if claims else None,
        }

    def retract_invalidated(self) -> int:
        """剪除触及终态产物（invalidated/superseded/deprecated）的关系边。

        invalidate() 只标记不删除（审计语义）；但失效传播完成后，健康链重建
        需要剪掉死边，否则 Evidence Gate 的 E3（链含失效产物）永远 FAIL。
        剪边不回滚已登记的失效标记；返回剪除条数（0 = 无死边，幂等）。
        """
        with self._lock:
            terminal = {"invalidated", "superseded", "deprecated"}
            dead = {a.artifact_id for a in self.registry.all()
                    if a.status in terminal}
            before = len(self.relations)
            self.relations = [e for e in self.relations
                              if e["from"] not in dead and e["to"] not in dead]
            removed = before - len(self.relations)
            if removed:
                self.graph_version += 1
            return removed

    def evidence_chain(self, claim_id: str) -> list[dict]:
        """返回支撑某 Claim 的完整证据链（claim ← result ← experiment ← model/data）。"""
        chain: list[dict] = []
        seen: set[str] = set()
        frontier = [claim_id]
        while frontier:
            cur = frontier.pop()
            for e in self.in_edges(cur):
                if e["from"] in seen:
                    continue
                seen.add(e["from"])
                chain.append(e)
                frontier.append(e["from"])
        return chain

    # ------------------------------------------------------ 失效传播

    def invalidate(self, artifact_id: str, reason: str = "",
                   invalidated_by: str = "") -> dict:
        """失效传播：标记，不删除。

        规则（V3.1 §1.12 + _PROPAGATION 边档位表）:
            * 根节点 → invalidated
            * kill 边下游：全部 kill 支撑都死 → invalidated；仅部分死 → requires_revalidation
            * reval 边下游 → requires_revalidation（证据本体未死，内容需复查）
            * reval 来源节点继续传播，但只传播 reval 档
            * 与死/需复查节点同 Question 但无边关系 → dirty
            * 其余 → unaffected（不写任何标记）
        不动点迭代：后死亡的支撑可以把先标记为 reval 的节点升级为 invalidated。
        返回分类报告；判定通过 Registry 写回各 Artifact contract。
        """
        root = self.registry.get(artifact_id)
        root.mark_invalidation(INVALIDATED, reason or "invalidated by propagation",
                               invalidated_by, by="graph.invalidate")

        dead: set[str] = {artifact_id}
        reval: set[str] = set()

        def _affected(src: str):
            """受 src 失效影响的邻居: [(neighbor, tier)]。"""
            out = []
            for e in self.out_edges(src):
                tier = _PROPAGATION.get(e["relation"], (None, None))[0]
                if tier:
                    out.append((e["to"], tier))
            for e in self.in_edges(src):
                tier = _PROPAGATION.get(e["relation"], (None, None))[1]
                if tier:
                    out.append((e["from"], tier))
            return out

        changed = True
        while changed:
            changed = False
            for src in sorted(dead | reval):
                src_dead = src in dead
                for cand, tier in _affected(src):
                    if cand in dead or self._is_terminal(cand):
                        continue
                    if tier == "reval" or not src_dead:
                        # reval 档，或来源只是 reval → 一律复查
                        if cand not in reval:
                            reval.add(cand)
                            changed = True
                    else:
                        # kill 档 + 来源已死：看 cand 的 kill 支撑是否全死
                        supports = self.killer_supports(cand)
                        if supports and supports <= dead:
                            reval.discard(cand)
                            dead.add(cand)
                            changed = True
                        elif cand not in reval:
                            reval.add(cand)
                            changed = True

        # 同 Question 旁染：dirty
        dirty: set[str] = set()
        for aid in dead | reval:
            art = self.registry.get(aid)
            if not art.question:
                continue
            for other in self.registry.by_question(art.question):
                oid = other.artifact_id
                if oid in dead or oid in reval or oid in dirty:
                    continue
                if self._is_terminal(oid) or self._has_invalidation(oid):
                    continue
                if aid in self.downstream(oid) or oid in self.downstream(aid):
                    continue   # 有直接/间接边关系的已按上面规则处理
                dirty.add(oid)

        # 写回 Registry
        for aid in sorted(dead - {artifact_id}):
            self.registry.invalidate(aid, reason or f"上游 {artifact_id} 失效",
                                     invalidated_by=artifact_id)
        for aid in sorted(reval):
            self.registry.mark_revalidation_needed(
                aid, f"上游 {artifact_id} 失效，需复查", invalidated_by=artifact_id)
        for aid in sorted(dirty):
            self.registry.mark_dirty(aid, f"同问旁染：{artifact_id} 失效")

        report = {
            "root": artifact_id,
            "reason": reason,
            "invalidated": sorted(dead),
            "requires_revalidation": sorted(reval),
            "dirty": sorted(dirty),
            "unaffected": sorted(
                a.artifact_id for a in self.registry.all()
                if a.artifact_id not in dead and a.artifact_id not in reval
                and a.artifact_id not in dirty),
        }
        return report

    def _is_terminal(self, artifact_id: str) -> bool:
        try:
            return self.registry.get(artifact_id).status in ("invalidated", "superseded", "deprecated")
        except KeyError:
            return True

    def _has_invalidation(self, artifact_id: str) -> bool:
        try:
            return bool(self.registry.get(artifact_id).invalidation)
        except KeyError:
            return False

    # ------------------------------------------------------ Registry 视图

    def _sync_artifact_view(self, artifact_id: str) -> None:
        """把 graph 关系同步为 Artifact contract 的只读 relations 视图。"""
        try:
            self.registry.set_relations_view(artifact_id, self.relations_of(artifact_id))
        except KeyError:
            pass

    def sync_all_views(self) -> None:
        for art in self.registry.all():
            self._sync_artifact_view(art.artifact_id)

    # ------------------------------------------------------------ 审计

    def integrity_check(self) -> list[str]:
        """Graph 级完整性检查（最终审计 / 回归测试消费）。"""
        problems: list[str] = []
        seen = set()
        for e in self.relations:
            key = (e["from"], e["relation"], e["to"])
            if key in seen:
                problems.append(f"重复关系: {key}")
            seen.add(key)
            if e["relation"] not in RELATION_TYPES:
                problems.append(f"未知 relation: {e['relation']!r}")
                continue
            for end in ("from", "to"):
                if not self.registry.exists(e[end]):
                    problems.append(f"悬空关系: {e[end]} ({end} of {key})")
            ft, tt = RELATION_TYPES[e["relation"]]
            if self.registry.exists(e["from"]) and ft is not None:
                if self._type_of(e["from"]) not in ft:
                    problems.append(f"类型不匹配(from): {key}")
            if self.registry.exists(e["to"]) and tt is not None:
                if self._type_of(e["to"]) not in tt:
                    problems.append(f"类型不匹配(to): {key}")
        return problems
