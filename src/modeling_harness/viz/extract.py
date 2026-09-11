#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""viz.extract — 由源真源派生 DiagramIR（MODEL_IR / Evidence Graph / catalog）。

源真源始终是 IR 本身（``model_ir.json`` / ``state/evidence_graph.json`` /
``catalog/*.yaml``）；本模块只做**确定性**的「IR → DiagramIR」投影，不引入
任何新事实。缺失/破损即抛错（fail-closed）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from modeling_harness.viz.ir import DiagramIR, DiagramIRError, Edge, Node

# MODEL_IR model_graph 节点 type → 语义层（与 model.md 的 L1/L2/L3 分层一致）
MODEL_LAYER: Dict[str, str] = {
    "problem": "L1 语义层",
    "assumption": "L1 语义层",
    "parameter": "L1 语义层",
    "variable": "L1 语义层",
    "mechanism": "L2 数学层",
    "equation": "L2 数学层",
    "constraint": "L2 数学层",
    "objective": "L2 数学层",
    "solver": "L3 计算层",
    "experiment": "L3 计算层",
    "validation": "L3 计算层",
    "claim": "L3 计算层",
}
MODEL_LAYER_ORDER = ["L1 语义层", "L2 数学层", "L3 计算层"]
MODEL_OTHER = "其他"

# Artifact 前缀 → 证据图分层（与 V3.1 架构 14 种 artifact 类型对齐）
EVIDENCE_LAYER: Dict[str, str] = {
    "PROBLEM": "problem",
    "Q": "question",
    "ASSUMPTION": "assumption",
    "MODEL": "model",
    "CODE": "code",
    "EXPERIMENT": "experiment",
    "RESULT": "result",
    "FIGURE": "figure",
    "TABLE": "table",
    "CLAIM": "claim",
    "DECISION": "decision",
    "NARRATIVE": "narrative",
    "DELIVERABLE": "deliverable",
}
EVIDENCE_LAYER_ORDER = [
    "problem", "question", "assumption", "model", "code", "experiment",
    "result", "figure", "table", "claim", "decision", "narrative", "deliverable",
]


def _read_json(path: "str | Path") -> Dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise DiagramIRError(f"源 IR 不存在：{p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DiagramIRError(f"源 IR 非合法 JSON：{p}：{exc}") from exc
    if not isinstance(data, dict):
        raise DiagramIRError(f"源 IR 顶层必须为对象：{p}")
    return data


def from_model_ir(path: "str | Path") -> DiagramIR:
    """MODEL_IR（``model_ir.json``）→ ``kind=model_map`` 的 DiagramIR。

    节点/边直接取自 ``model_graph``（真源），按 ``type`` 归入 L1/L2/L3；
    节点顺序与边顺序保持 IR 原序（确定性）。
    """
    data = _read_json(path)
    graph = data.get("model_graph")
    if not isinstance(graph, dict):
        raise DiagramIRError(f"{path}: 缺 model_graph，无法生成模型图")
    raw_nodes = graph.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise DiagramIRError(f"{path}: model_graph.nodes 为空，无法生成模型图")

    nodes: List[Node] = []
    seen: Set[str] = set()
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            continue
        nid = str(raw.get("id") or "").strip()
        if not nid or nid in seen:
            continue
        seen.add(nid)
        ntype = str(raw.get("type") or "")
        nodes.append(
            Node(
                id=nid,
                label=str(raw.get("label") or nid),
                group=MODEL_LAYER.get(ntype, MODEL_OTHER),
                detail=ntype,
            )
        )

    edges: List[Edge] = []
    for raw in graph.get("edges") or []:
        if not isinstance(raw, dict):
            continue
        src = str(raw.get("from") or "").strip()
        dst = str(raw.get("to") or "").strip()
        if src in seen and dst in seen:
            edges.append(Edge(source=src, target=dst,
                              label=str(raw.get("relation") or ""), kind="flow"))

    present = [g for g in MODEL_LAYER_ORDER if any(n.group == g for n in nodes)]
    if any(n.group == MODEL_OTHER for n in nodes):
        present.append(MODEL_OTHER)

    ir = DiagramIR(
        kind="model_map",
        title=str(data.get("title") or data.get("model_id") or "MODEL_IR"),
        nodes=nodes,
        edges=edges,
        legend=present,
    )
    ir.validate()
    return ir


def _artifact_layer(artifact_id: str) -> str:
    core = artifact_id[3:] if artifact_id.startswith("MH-") else artifact_id
    alpha = ""
    for ch in core:
        if ch.isalpha():
            alpha += ch
        elif alpha:
            break
    return EVIDENCE_LAYER.get(alpha.upper(), alpha.lower() or "other")


def _layer_rank(layer: str) -> int:
    return EVIDENCE_LAYER_ORDER.index(layer) if layer in EVIDENCE_LAYER_ORDER else len(
        EVIDENCE_LAYER_ORDER
    )


def from_evidence_graph(path: "str | Path") -> DiagramIR:
    """Evidence Graph（``state/evidence_graph.json``）→ ``kind=evidence_graph`` 的 IR。"""
    data = _read_json(path)
    relations = data.get("relations")
    if not isinstance(relations, list) or not relations:
        raise DiagramIRError(f"{path}: relations 为空，无法生成证据图")

    layer_of: Dict[str, str] = {}
    raw_edges: List[Tuple[str, str, str]] = []
    for rel in relations:
        if not isinstance(rel, dict):
            continue
        src = str(rel.get("from") or "").strip()
        dst = str(rel.get("to") or "").strip()
        if not src or not dst:
            continue
        layer_of.setdefault(src, _artifact_layer(src))
        layer_of.setdefault(dst, _artifact_layer(dst))
        raw_edges.append((src, dst, str(rel.get("relation") or "")))

    # 按（层规范序，id）排序 → 确定性且分层可读
    ordered_ids = sorted(layer_of, key=lambda a: (_layer_rank(layer_of[a]), a))
    nodes = [Node(id=a, label=a, group=layer_of[a], detail=layer_of[a]) for a in ordered_ids]
    ids = set(ordered_ids)
    edges = [Edge(source=s, target=t, label=label, kind="evidence")
             for s, t, label in raw_edges if s in ids and t in ids]

    present = [g for g in EVIDENCE_LAYER_ORDER if any(n.group == g for n in nodes)]
    extra = [g for g in dict.fromkeys(layer_of.values()) if g not in present]
    ir = DiagramIR(
        kind="evidence_graph",
        title=f"{data.get('project', 'project')} · Evidence Graph",
        nodes=nodes,
        edges=edges,
        legend=present + extra,
    )
    ir.validate()
    return ir


def from_catalog(v3: Dict[str, Any]) -> DiagramIR:
    """catalog ``v3.yaml``（roles/nodes/validators）→ ``kind=architecture`` 的 IR。

    入参为已解析的 ``v3`` 子字典（YAML 解析留在 CLI 层，保持 viz 包零依赖）。
    分层：Roles → 各 stage（DAG 节点按 stage 归组）→ Validators；边为
    ``节点 --validator--> validator``。
    """
    roles = v3.get("roles") or []
    nodes = v3.get("nodes") or []
    validators = v3.get("validators") or []
    if not isinstance(nodes, list) or not nodes:
        raise DiagramIRError("catalog v3 视图缺 nodes，无法生成架构图")

    out: List[Node] = []
    for role in roles:
        name = str(role.get("name") or "").strip()
        if name:
            out.append(Node(id=f"role:{name}", label=name, group="Roles",
                            detail=str(role.get("capabilities") or "")[:24]))
    stages: List[str] = []
    for node in nodes:
        name = str(node.get("name") or "").strip()
        if not name:
            continue
        stage = str(node.get("stage") or "其他")
        if stage not in stages:
            stages.append(stage)
        out.append(Node(id=f"node:{name}", label=name, group=stage,
                        detail=str(node.get("role") or "")))
    for val in validators:
        name = str(val.get("name") or "").strip()
        if name:
            out.append(Node(id=f"val:{name}", label=name, group="Validators",
                            detail=str(val.get("kind") or "")))

    node_ids = {f"node:{str(n.get('name'))}" for n in nodes}
    edges: List[Edge] = []
    for node in nodes:
        val = node.get("validator")
        if val and f"node:{node.get('name')}" in node_ids:
            edges.append(Edge(source=f"node:{node.get('name')}", target=f"val:{val}",
                              kind="dependency"))

    legend = ["Roles"] + stages + ["Validators"]
    ir = DiagramIR(
        kind="architecture",
        title="Modeling-Harness · 架构总览（catalog 真源派生）",
        nodes=out,
        edges=edges,
        legend=legend,
    )
    ir.validate()
    return ir


__all__ = ["from_model_ir", "from_evidence_graph", "from_catalog",
           "MODEL_LAYER", "EVIDENCE_LAYER"]
