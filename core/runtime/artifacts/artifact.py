"""Artifact Contract — 统一对象契约（V3 单一对象模型）。

Contract 必备维度: identity / type / version / status / provenance /
dependency / validation / relations / lifecycle / invalidation。
本模块同时提供零依赖的结构化校验（对应 core/schemas/v3/artifact/artifact.schema.json）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from .ids import ARTIFACT_TYPES, IDFormatError, id_matches_type, is_valid_id
from .lifecycle import STATES, LifecycleError, assert_transition

CONTRACT_VERSION = "3.1"

# 状态与 ID 之外的保留字段
RESERVED_FIELDS = frozenset({
    "schema_version", "artifact_id", "type", "version", "status",
    "created_at", "updated_at", "lifecycle_history",
})

# 触发"内容变更"的字段：更新这些字段会把状态重置回 draft（validation 失效）
CONTENT_FIELDS = ("payload", "depends_on", "parent", "question", "data")


class ContractError(ValueError):
    """Contract 校验失败。"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Artifact:
    """可引用、可追踪、可验证、可版本化的研究对象。"""

    artifact_id: str
    type: str
    version: int = 1
    status: str = "draft"
    title: str = ""
    created_by: str = ""            # 产生者（node / role / agent 名）
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)
    payload: list[str] = field(default_factory=list)   # 相对项目根的文件路径（可为空）
    parent: list[str] = field(default_factory=list)     # 同型派生来源（可选）
    depends_on: list[str] = field(default_factory=list) # 硬依赖的上游 Artifact ID
    relations: list[dict] = field(default_factory=list) # Evidence Graph 同步的 typed relations（只读视图）
    provenance: dict = field(default_factory=dict)      # {node, session, tool, prompt_ref, ...}
    validation: dict = field(default_factory=dict)      # {validators: [], passed, report: {}}
    lifecycle_history: list[dict] = field(default_factory=list)
    invalidation: dict = field(default_factory=dict)    # {status, reason, invalidated_by, at}
    question: str = ""              # 所属 Question ID（Qi 类型 Artifact 专用）
    tags: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)            # 轻量内联数据（如 result 数值快照）

    # ------------------------------------------------------------------ 校验

    def validate(self) -> list[str]:
        """结构化校验，返回问题列表（空列表 = 通过）。"""
        problems: list[str] = []
        if not is_valid_id(self.artifact_id):
            problems.append(f"artifact_id 非法: {self.artifact_id!r}")
            return problems
        if self.type not in ARTIFACT_TYPES:
            problems.append(f"未知 artifact 类型: {self.type!r}")
        elif not id_matches_type(self.artifact_id, self.type):
            problems.append(f"ID {self.artifact_id} 前缀与类型 {self.type!r} 不匹配")
        if not isinstance(self.version, int) or self.version < 1:
            problems.append(f"version 必须为 ≥1 的整数: {self.version!r}")
        if self.status not in STATES:
            problems.append(f"status 非法: {self.status!r}")
        for ref in self.depends_on + self.parent:
            if not is_valid_id(ref):
                problems.append(f"依赖/父引用非法: {ref!r}")
        if self.question and not is_valid_id(self.question):
            problems.append(f"question 引用非法: {self.question!r}")
        if self.question and not self.question.startswith("Q"):
            problems.append(f"question 必须是 Q 类型 ID: {self.question!r}")
        if self.artifact_id in self.depends_on or self.artifact_id in self.parent:
            problems.append("Artifact 不能依赖/派生自自身")
        if self.question == self.artifact_id:
            problems.append("question 不能指向自身")
        return problems

    # ------------------------------------------------------------- 生命周期

    def transition(self, target: str, by: str = "", reason: str = "") -> "Artifact":
        """状态转换（fail-closed；幂等转换允许重放）。"""
        assert_transition(self.status, target)
        if target != self.status:
            self.lifecycle_history.append({
                "from": self.status, "to": target, "at": utcnow(),
                "by": by, "reason": reason,
            })
            self.status = target
        self.updated_at = utcnow()
        return self

    def mark_validated(self, validator: str, report: dict | None = None,
                       by: str = "") -> "Artifact":
        """active → validated，并记录验证证据。"""
        self.transition("validated", by=by or validator,
                        reason=f"validated by {validator}")
        self.validation = {
            "validators": sorted(set(self.validation.get("validators", []) + [validator])),
            "passed": True,
            "report": report or {},
            "at": utcnow(),
        }
        return self

    def mark_invalidation(self, status: str, reason: str, invalidated_by: str = "",
                          by: str = "graph") -> "Artifact":
        """记录 invalidation 传播判定（invalidated / requires_revalidation / dirty）。"""
        if status not in ("invalidated", "requires_revalidation", "dirty"):
            raise ContractError(f"非法 invalidation 状态: {status!r}")
        if status == "invalidated":
            # 从任意非终态进入 invalidated；已是终态则保持（幂等，不覆盖原终态）
            if self.status not in ("invalidated", "superseded", "deprecated"):
                self.lifecycle_history.append({
                    "from": self.status, "to": "invalidated", "at": utcnow(),
                    "by": by, "reason": reason,
                })
                self.status = "invalidated"
        self.invalidation = {
            "status": status, "reason": reason,
            "invalidated_by": invalidated_by, "at": utcnow(),
        }
        self.updated_at = utcnow()
        return self

    def clear_invalidation(self) -> "Artifact":
        """失效修复后清除标记（仅非终态可清）。"""
        if self.status in ("invalidated", "superseded", "deprecated"):
            raise LifecycleError(f"{self.status} 为终态，不可清除 invalidation；请创建新版本")
        self.invalidation = {}
        self.updated_at = utcnow()
        return self

    # ---------------------------------------------------------------- 序列化

    def to_dict(self) -> dict:
        d = asdict(self)
        d["schema_version"] = CONTRACT_VERSION
        # 保持字段顺序可读
        ordered = {"schema_version": CONTRACT_VERSION}
        for key in ("artifact_id", "type", "version", "status", "title", "question",
                    "created_by", "created_at", "updated_at", "payload", "parent",
                    "depends_on", "relations", "provenance", "validation",
                    "lifecycle_history", "invalidation", "tags", "data"):
            ordered[key] = d.get(key)
        return ordered

    @classmethod
    def from_dict(cls, d: dict) -> "Artifact":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in d.items() if k in known}
        art = cls(**kwargs)
        problems = art.validate()
        if problems:
            raise ContractError(f"反序列化失败: {'; '.join(problems)}")
        return art

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def validate_contract_dict(d: dict) -> list[str]:
    """零依赖契约校验（供 schema 门禁 / 测试使用）。"""
    try:
        Artifact.from_dict(d)
        return []
    except (ContractError, IDFormatError, LifecycleError, TypeError) as exc:
        return [str(exc)]
