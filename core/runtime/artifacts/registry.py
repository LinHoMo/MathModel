"""Artifact Registry — Artifact 登记簿（单一事实源）。

持久化: projects/<p>/state/registry.json（原子写）。
职责: ID 分配 / 版本历史 / 生命周期推进 / 引用完整性 / 查询。
不做: Evidence Graph 的关系推导（core/runtime/graph 职责）——本层只在
Artifact contract 的 relations 字段维护 graph 同步过来的只读视图。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .artifact import Artifact, ContractError, utcnow
from .ids import ARTIFACT_TYPES, IDFormatError, format_id, is_valid_id
from .lifecycle import LifecycleError, assert_transition, is_terminal

REGISTRY_VERSION = 3


class RegistryError(ValueError):
    """Registry 操作非法。"""


class ArtifactNotFound(KeyError):
    """Artifact 不存在。"""


class ArtifactRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.artifacts: dict[str, Artifact] = {}   # id → 最新版本
        self.history: dict[str, dict[int, dict]] = {}  # id → {version: snapshot}
        self.counters: dict[str, int] = {}         # type → 已发放数量
        self.project: str = ""
        self._dirty = False
        if self.path.exists():
            self.load()
        else:
            self.project = self._infer_project()

    # ------------------------------------------------------------ 持久化

    def _infer_project(self) -> str:
        # projects/<p>/state/registry.json → <p>
        parts = self.path.parts
        if "state" in parts:
            i = parts.index("state")
            if i >= 1 and parts[i - 1]:
                return parts[i - 1]
        return ""

    def load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("registry_version") != REGISTRY_VERSION:
            raise RegistryError(f"registry.json 版本不兼容: {raw.get('registry_version')!r}")
        self.project = raw.get("project", "")
        self.counters = {k: int(v) for k, v in raw.get("counters", {}).items()}
        self.artifacts = {}
        self.history = {}
        for aid, adict in raw.get("artifacts", {}).items():
            self.artifacts[aid] = Artifact.from_dict(adict)
        for aid, versions in raw.get("history", {}).items():
            self.history[aid] = {int(v): snap for v, snap in versions.items()}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "registry_version": REGISTRY_VERSION,
            "project": self.project,
            "updated_at": utcnow(),
            "counters": self.counters,
            "artifacts": {aid: a.to_dict() for aid, a in sorted(self.artifacts.items())},
            "history": {aid: {str(v): s for v, s in vers.items()}
                        for aid, vers in self.history.items()},
        }
        # 原子写：临时文件 + replace
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self._dirty = False

    # ------------------------------------------------------------- ID 分配

    def next_id(self, artifact_type: str) -> str:
        if artifact_type not in ARTIFACT_TYPES:
            raise IDFormatError(f"未知 artifact 类型: {artifact_type!r}")
        n = self.counters.get(artifact_type, 0) + 1
        candidate = format_id(ARTIFACT_TYPES[artifact_type], n)
        # 防御：ID 永不复用（即使人为删除过）
        while candidate in self.artifacts:
            n += 1
            candidate = format_id(ARTIFACT_TYPES[artifact_type], n)
        return candidate

    # ---------------------------------------------------------------- 创建

    def create(self, artifact_type: str, *, title: str = "", payload=None,
               created_by: str = "", question: str = "", depends_on=None,
               parent=None, provenance=None, data=None, tags=None,
               activate: bool = False) -> Artifact:
        """登记新 Artifact（状态 draft；activate=True 直接进入 active）。"""
        aid = self.next_id(artifact_type)
        art = Artifact(
            artifact_id=aid, type=artifact_type, title=title or aid,
            payload=list(payload or []), created_by=created_by, question=question,
            depends_on=list(depends_on or []), parent=list(parent or []),
            provenance=dict(provenance or {}), data=dict(data or {}),
            tags=list(tags or []),
        )
        problems = art.validate()
        if problems:
            raise ContractError("; ".join(problems))
        self._assert_refs_exist(art)
        if activate:
            art.transition("active", by=created_by, reason="registered with payload")
        art.lifecycle_history.insert(0, {"from": None, "to": art.status,
                                         "at": utcnow(), "by": created_by,
                                         "reason": "created"})
        self.artifacts[aid] = art
        self.counters[artifact_type] = self.counters.get(artifact_type, 0) + 1
        self._dirty = True
        return art

    # ---------------------------------------------------------------- 查询

    def get(self, artifact_id: str, version: int | None = None) -> Artifact:
        if artifact_id not in self.artifacts:
            raise ArtifactNotFound(artifact_id)
        if version is None:
            return self.artifacts[artifact_id]
        if version == self.artifacts[artifact_id].version:
            return self.artifacts[artifact_id]
        snap = self.history.get(artifact_id, {}).get(version)
        if snap is None:
            raise RegistryError(f"{artifact_id} 无版本 {version}（当前 {self.artifacts[artifact_id].version}）")
        return Artifact.from_dict(snap)

    def latest(self, artifact_id: str) -> Artifact:
        return self.get(artifact_id)

    def exists(self, artifact_id: str) -> bool:
        return artifact_id in self.artifacts

    def list_by_type(self, artifact_type: str) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.type == artifact_type]

    def list_by_status(self, status: str) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.status == status]

    def by_question(self, question_id: str) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.question == question_id]

    def all(self) -> list[Artifact]:
        return list(self.artifacts.values())

    def __len__(self) -> int:
        return len(self.artifacts)

    # ------------------------------------------------------------ 生命周期

    def transition(self, artifact_id: str, target: str, *, by: str = "",
                   reason: str = "") -> Artifact:
        art = self.get(artifact_id)
        art.transition(target, by=by, reason=reason)
        self._dirty = True
        return art

    def activate(self, artifact_id: str, by: str = "") -> Artifact:
        return self.transition(artifact_id, "active", by=by, reason="activated")

    def mark_validated(self, artifact_id: str, validator: str,
                       report: dict | None = None) -> Artifact:
        art = self.get(artifact_id)
        art.mark_validated(validator, report)
        self._dirty = True
        return art

    def publish(self, artifact_id: str, by: str = "") -> Artifact:
        return self.transition(artifact_id, "published", by=by, reason="published")

    def block(self, artifact_id: str, reason: str = "", by: str = "") -> Artifact:
        return self.transition(artifact_id, "blocked", by=by, reason=reason)

    def deprecate(self, artifact_id: str, reason: str = "", by: str = "") -> Artifact:
        return self.transition(artifact_id, "deprecated", by=by, reason=reason)

    def invalidate(self, artifact_id: str, reason: str,
                   invalidated_by: str = "") -> Artifact:
        """直接失效（invalidation 传播由 graph 层调用此方法逐个落地）。"""
        art = self.get(artifact_id)
        art.mark_invalidation("invalidated", reason, invalidated_by)
        self._dirty = True
        return art

    def mark_revalidation_needed(self, artifact_id: str, reason: str,
                                 invalidated_by: str = "") -> Artifact:
        art = self.get(artifact_id)
        art.mark_invalidation("requires_revalidation", reason, invalidated_by)
        self._dirty = True
        return art

    def mark_dirty(self, artifact_id: str, reason: str) -> Artifact:
        art = self.get(artifact_id)
        art.mark_invalidation("dirty", reason)
        self._dirty = True
        return art

    def clear_invalidation(self, artifact_id: str) -> Artifact:
        art = self.get(artifact_id)
        art.clear_invalidation()
        self._dirty = True
        return art

    # ---------------------------------------------------------------- 版本

    def update(self, artifact_id: str, **fields) -> Artifact:
        """更新 Artifact：旧版本快照进 history，version +1。

        触及内容字段（payload/depends_on/parent/question/data）时状态重置为
        draft（validation 失效）；纯元数据更新（title/tags/provenance）保留状态。
        终态 Artifact 拒绝更新（需新建替代并 supersede）。
        """
        art = self.get(artifact_id)
        if is_terminal(art.status):
            raise LifecycleError(
                f"{artifact_id} 处于终态 {art.status}，不能更新；请新建 Artifact 并 supersede")
        if not fields:
            raise RegistryError("update 需要至少一个字段")
        unknown = set(fields) - {"title", "tags", "provenance", "payload", "depends_on",
                                 "parent", "question", "data", "created_by"}
        if unknown:
            raise RegistryError(f"不允许通过 update 修改: {sorted(unknown)}"
                                "（状态请用 transition/生命周期方法）")
        # 快照当前版本
        self.history.setdefault(artifact_id, {})[art.version] = art.to_dict()
        # 应用变更
        for key, value in fields.items():
            setattr(art, key, value)
        art.version += 1
        content_touched = any(k in fields for k in
                              ("payload", "depends_on", "parent", "question", "data"))
        if content_touched and art.status in ("validated", "published", "active"):
            # 内容变更 → validation 失效，回 draft（合法转换：validated→draft 不在表中，
            # 因此这里显式作为"版本重置"记录，而非普通 transition）
            art.lifecycle_history.append({
                "from": art.status, "to": "draft", "at": utcnow(),
                "by": "registry.update", "reason": "content changed → new version",
            })
            art.status = "draft"
            art.validation = {}
        art.updated_at = utcnow()
        problems = art.validate()
        if problems:
            # 回滚内存态（磁盘未动）
            raise ContractError("; ".join(problems))
        self._assert_refs_exist(art)
        self._dirty = True
        return art

    def supersede(self, artifact_id: str, reason: str,
                  replacement: str = "", by: str = "") -> Artifact:
        """标记被替代。replacement 可指向新 Artifact ID。"""
        if replacement and not self.exists(replacement):
            raise ArtifactNotFound(replacement)
        art = self.get(artifact_id)
        art.transition("superseded", by=by, reason=reason)
        if replacement:
            art.invalidation = {"status": "superseded", "reason": reason,
                                "invalidated_by": replacement, "at": utcnow()}
        self._dirty = True
        return art

    def versions(self, artifact_id: str) -> list[int]:
        """返回全部可用版本号（含当前）。"""
        art = self.get(artifact_id)
        vers = list(self.history.get(artifact_id, {}).keys()) + [art.version]
        return sorted(vers)

    # ------------------------------------------------------------ 关系视图

    def set_relations_view(self, artifact_id: str, relations: list[dict]) -> None:
        """由 Evidence Graph 层调用，同步只读关系视图。"""
        art = self.get(artifact_id)
        art.relations = list(relations)
        art.updated_at = utcnow()
        self._dirty = True

    # -------------------------------------------------------------- 完整性

    def _assert_refs_exist(self, art: Artifact) -> None:
        for ref in art.depends_on + art.parent:
            if not self.exists(ref) and ref != art.artifact_id:
                raise RegistryError(f"{art.artifact_id} 引用了不存在的 Artifact: {ref}")
        if art.question and not self.exists(art.question):
            raise RegistryError(f"{art.artifact_id} 引用了不存在的 Question: {art.question}")

    def integrity_check(self) -> list[str]:
        """Registry 级完整性检查（最终审计 / 回归测试消费）。"""
        problems: list[str] = []
        seen_ids = set()
        for aid, art in self.artifacts.items():
            if aid in seen_ids:
                problems.append(f"ID 重复: {aid}")
            seen_ids.add(aid)
            problems += [f"{aid}: {p}" for p in art.validate()]
            for ref in art.depends_on + art.parent:
                if ref not in self.artifacts:
                    problems.append(f"{aid} 悬空引用: {ref}")
            if art.question and art.question not in self.artifacts:
                problems.append(f"{aid} 悬空 question 引用: {art.question}")
            # 计数器一致性
            expected = sum(1 for a in self.artifacts.values() if a.type == art.type)
        for atype, prefix in ARTIFACT_TYPES.items():
            n = sum(1 for a in self.artifacts.values() if a.type == atype)
            if self.counters.get(atype, 0) < n:
                problems.append(f"counters[{atype}]={self.counters.get(atype)} < 实际数 {n}")
        return problems

    # ---------------------------------------------------------------- 导出

    def summary(self) -> dict:
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for a in self.artifacts.values():
            by_type[a.type] = by_type.get(a.type, 0) + 1
            by_status[a.status] = by_status.get(a.status, 0) + 1
        return {
            "project": self.project, "total": len(self.artifacts),
            "by_type": by_type, "by_status": by_status,
            "graph_pending_dirty": self._dirty,
        }
