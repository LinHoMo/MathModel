#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""modeling_harness.viz — 确定性图表渲染（Archify 范式，零第三方依赖）。

三层分离：源 IR（catalog / model_ir.json / evidence_graph.json）→ 确定性渲染器
（``ir`` / ``extract`` / ``svg`` / ``html``）→ 人看产物（``.svg`` / ``.html``）。

只服务本项目定位（可信建模 + 证据）的「给人看」环节：不引入 Node 运行时、
不做通用可视化框架、不新增第三方依赖（ADR-0004）。
"""
from __future__ import annotations

from modeling_harness.viz.ir import (
    EDGE_KINDS,
    KINDS,
    NODE_VARIANTS,
    SCHEMA_VERSION,
    DiagramIR,
    DiagramIRError,
    Edge,
    Node,
)

__all__ = [
    "SCHEMA_VERSION",
    "KINDS",
    "NODE_VARIANTS",
    "EDGE_KINDS",
    "DiagramIR",
    "DiagramIRError",
    "Edge",
    "Node",
]
