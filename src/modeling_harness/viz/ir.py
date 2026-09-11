#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""viz.ir — DiagramIR：类型化图表中间表示 + fail-closed 契约校验。

范式来源（受限借鉴）：archify「Agent 产出类型化 JSON IR → 确定性渲染器编译为
自包含 SVG/HTML」。本仓只取「类型化 IR + 确定性渲染」这一内核，纯标准库实现，
零第三方依赖（ADR-0004）。

契约（schema_version 1.0）::

    {
      "schema_version": "1.0",
      "kind": "architecture|model_map|evidence_graph|matrix",
      "title": "...",
      "nodes": [{"id", "label", "group?", "variant?", "detail?"}],
      "edges": [{"from", "to", "label?", "kind?"}],
      "legend": ["..."]
    }

契约破损（重复 id / 悬空边 / 非法词表 / 空图）一律抛 :class:`DiagramIRError`
—— fail-closed，绝不放行半成品。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

SCHEMA_VERSION = "1.0"

# 受控词表（对齐 archify authoring-contract 的 componentType/variant 思路）
KINDS = ("architecture", "model_map", "evidence_graph", "matrix")
NODE_VARIANTS = ("default", "emphasis", "muted", "dashed")
EDGE_KINDS = ("flow", "dependency", "evidence", "reference")


class DiagramIRError(ValueError):
    """DiagramIR 契约破损 —— fail-closed。"""


def _require_nonempty(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DiagramIRError(f"{what} 必须为非空字符串，得到 {value!r}")
    return value


@dataclass
class Node:
    """图节点：id 唯一；group 决定分层；variant 决定视觉。"""

    id: str
    label: str
    group: str = ""
    variant: str = "default"
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"id": self.id, "label": self.label}
        if self.group:
            out["group"] = self.group
        if self.variant and self.variant != "default":
            out["variant"] = self.variant
        if self.detail:
            out["detail"] = self.detail
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        return cls(
            id=str(data.get("id") or ""),
            label=str(data.get("label") or ""),
            group=str(data.get("group") or ""),
            variant=str(data.get("variant") or "default"),
            detail=str(data.get("detail") or ""),
        )


@dataclass
class Edge:
    """图边：source/target 须指向已存在的 node；kind 受控词表。"""

    source: str
    target: str
    label: str = ""
    kind: str = "flow"

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"from": self.source, "to": self.target}
        if self.label:
            out["label"] = self.label
        if self.kind and self.kind != "flow":
            out["kind"] = self.kind
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Edge":
        source = str(data.get("from", data.get("source")) or "")
        target = str(data.get("to", data.get("target")) or "")
        return cls(
            source=source,
            target=target,
            label=str(data.get("label") or ""),
            kind=str(data.get("kind") or "flow"),
        )


@dataclass
class DiagramIR:
    """类型化图表中间表示。构建后须 :meth:`validate` 通过方可渲染。"""

    kind: str
    title: str = ""
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    legend: List[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    # ---- 契约校验 --------------------------------------------------------

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise DiagramIRError(
                f"schema_version 必须为 {SCHEMA_VERSION!r}，得到 {self.schema_version!r}"
            )
        if self.kind not in KINDS:
            raise DiagramIRError(f"非法 kind={self.kind!r}；允许 {KINDS}")
        if not self.nodes:
            raise DiagramIRError("DiagramIR 至少需要一个 node（空图无意义）")

        seen = set()
        for node in self.nodes:
            _require_nonempty(node.id, "node.id")
            if node.id in seen:
                raise DiagramIRError(f"node id 重复：{node.id!r}")
            seen.add(node.id)
            _require_nonempty(node.label, f"node {node.id!r} 的 label")
            if node.variant not in NODE_VARIANTS:
                raise DiagramIRError(
                    f"node {node.id!r} 非法 variant={node.variant!r}；允许 {NODE_VARIANTS}"
                )

        for edge in self.edges:
            if edge.kind not in EDGE_KINDS:
                raise DiagramIRError(
                    f"edge {edge.source!r}->{edge.target!r} 非法 kind={edge.kind!r}；"
                    f"允许 {EDGE_KINDS}"
                )
            for endpoint, role in ((edge.source, "from"), (edge.target, "to")):
                if endpoint not in seen:
                    raise DiagramIRError(
                        f"edge {edge.source!r}->{edge.target!r} 的 {role}={endpoint!r} "
                        f"引用的节点不存在"
                    )

    # ---- 确定性序列化 ----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "title": self.title,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "legend": list(self.legend),
        }

    def to_json(self) -> str:
        # sort_keys + 固定缩进 + 末尾换行 → byte-stable，可 git diff
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagramIR":
        if not isinstance(data, dict):
            raise DiagramIRError("IR 顶层必须为对象")
        try:
            nodes = [Node.from_dict(n) for n in data.get("nodes", [])]
            edges = [Edge.from_dict(e) for e in data.get("edges", [])]
        except (TypeError, AttributeError) as exc:
            raise DiagramIRError(f"IR 结构破损：{exc}") from exc
        ir = cls(
            kind=data.get("kind", ""),
            title=data.get("title", "") or "",
            nodes=nodes,
            edges=edges,
            legend=[str(x) for x in data.get("legend", [])],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )
        ir.validate()
        return ir

    @classmethod
    def from_json(cls, text: str) -> "DiagramIR":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DiagramIRError(f"IR 非合法 JSON：{exc}") from exc
        return cls.from_dict(data)

    @classmethod
    def load(cls, path: "str | Path") -> "DiagramIR":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


__all__ = [
    "SCHEMA_VERSION",
    "KINDS",
    "NODE_VARIANTS",
    "EDGE_KINDS",
    "DiagramIRError",
    "Node",
    "Edge",
    "DiagramIR",
]
