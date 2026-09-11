#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""viz.svg — DiagramIR → 确定性 SVG（分层布局 + 正交连线 + 图例）。

纯标准库、零第三方依赖；输出 byte-stable（无时间戳、无集合迭代序），
同一 IR 重复渲染字节相等，可直接 git diff。

布局：IR 的 ``group`` 决定层（按首次出现顺序自上而下），层内节点按插入序
横向排列；正向边（目标层在下）走竖直折线，反馈/同层边走右侧沟槽。
配色与明暗主题全部走 ``<style>`` 语义 class（含 ``prefers-color-scheme: dark``），
不散落内联颜色。
"""
from __future__ import annotations

from typing import Dict, List, Tuple
from xml.sax.saxutils import escape

from modeling_harness.viz.ir import DiagramIR, Edge, Node

NODE_W = 184
NODE_H = 52
GAP_X = 36
GAP_Y = 64
MARGIN = 32
TITLE_H = 46
LEGEND_H = 34
PALETTE = 6

_STYLE = """\
:root{color-scheme:light dark}
text{font-family:-apple-system,'Segoe UI','Microsoft YaHei',Roboto,Helvetica,Arial,sans-serif}
.bg{fill:#ffffff}
.title{fill:#1a237e;font-size:18px;font-weight:700}
.subtitle{fill:#78909c;font-size:11px}
.layer-band{fill:#f4f7fa}
.layer-band.alt{fill:#eaeff5}
.layer-title{fill:#546e7a;font-size:12px;font-weight:600}
.shape{stroke-width:1.6}
.shape.layer-0{fill:#e3f2fd;stroke:#1565c0}
.shape.layer-1{fill:#e8f5e9;stroke:#2e7d32}
.shape.layer-2{fill:#fff3e0;stroke:#ef6c00}
.shape.layer-3{fill:#f3e5f5;stroke:#6a1b9a}
.shape.layer-4{fill:#e0f7fa;stroke:#00838f}
.shape.layer-5{fill:#fbe9e7;stroke:#bf360c}
.node .label{fill:#102027;font-size:12px}
.node .detail{fill:#607d8b;font-size:10px}
.node.emphasis .shape{stroke-width:2.8;stroke:#c62828}
.node.muted .shape{opacity:.5}
.node.dashed .shape{stroke-dasharray:5 3}
.edge{fill:none;stroke:#90a4ae;stroke-width:1.4}
.edge.dependency{stroke:#7e57c2;stroke-dasharray:4 3}
.edge.evidence{stroke:#2e7d32}
.edge.reference{stroke:#b0bec5;stroke-dasharray:2 4}
.edge-label{fill:#607d8b;font-size:9px}
.arrow-head{fill:#90a4ae}
.legend text{fill:#37474f;font-size:11px}
@media (prefers-color-scheme:dark){
.bg{fill:#0f1419}
.title{fill:#90caf9}
.subtitle{fill:#90a4ae}
.layer-band{fill:#161c22}
.layer-band.alt{fill:#1b232b}
.layer-title{fill:#90a4ae}
.node .label{fill:#eceff1}
.node .detail{fill:#90a4ae}
.edge{stroke:#546e7a}
.edge-label{fill:#90a4ae}
.arrow-head{fill:#546e7a}
.legend text{fill:#cfd8dc}
.shape.layer-0{fill:#102a43;stroke:#4a90d9}
.shape.layer-1{fill:#10331f;stroke:#4caf50}
.shape.layer-2{fill:#3a2a12;stroke:#ffa726}
.shape.layer-3{fill:#2a1633;stroke:#ab47bc}
.shape.layer-4{fill:#0f2d31;stroke:#26c6da}
.shape.layer-5{fill:#331613;stroke:#ff7043}
}
"""


def _attr(value: object) -> str:
    return escape(str(value), {'"': "&quot;"})


def _num(value: float) -> str:
    # 统一 1 位小数并去尾零 → 确定性且紧凑
    return f"{round(float(value), 1):g}"


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def _layout(ir: DiagramIR) -> Tuple[List[str], Dict[str, List[Node]], Dict[str, Tuple[float, float]]]:
    """返回 (层序, 层→节点, 节点 id→(x, y))。"""
    order: List[str] = []
    layers: Dict[str, List[Node]] = {}
    for node in ir.nodes:
        key = node.group or ""
        if key not in layers:
            layers[key] = []
            order.append(key)
        layers[key].append(node)

    ncols = max(len(v) for v in layers.values())
    base_w = MARGIN * 2 + ncols * NODE_W + (ncols - 1) * GAP_X
    top = TITLE_H + MARGIN

    pos: Dict[str, Tuple[float, float]] = {}
    for i, key in enumerate(order):
        row = layers[key]
        row_w = len(row) * NODE_W + (len(row) - 1) * GAP_X
        start_x = MARGIN + (base_w - MARGIN * 2 - row_w) / 2.0
        y = top + i * (NODE_H + GAP_Y)
        for j, node in enumerate(row):
            pos[node.id] = (start_x + j * (NODE_W + GAP_X), float(y))
    return order, layers, pos


def render_svg(ir: DiagramIR, *, title: str = "") -> str:
    """把 DiagramIR 渲染为自包含 SVG 文本（确定性）。"""
    ir.validate()

    order, layers, pos = _layout(ir)
    layer_index = {g: i for i, g in enumerate(order)}
    group_of = {n.id: (n.group or "") for n in ir.nodes}

    forward: List[Edge] = []
    feedback: List[Edge] = []
    for edge in ir.edges:
        if layer_index[group_of[edge.target]] > layer_index[group_of[edge.source]]:
            forward.append(edge)
        else:
            feedback.append(edge)

    ncols = max(len(v) for v in layers.values())
    base_w = MARGIN * 2 + ncols * NODE_W + (ncols - 1) * GAP_X
    gutter = (44 + 16 * len(feedback)) if feedback else 0
    canvas_w = base_w + gutter
    content_bottom = TITLE_H + MARGIN + (len(order) - 1) * (NODE_H + GAP_Y) + NODE_H
    canvas_h = content_bottom + MARGIN + (LEGEND_H if ir.legend else 0)

    head = title or ir.title
    parts: List[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_num(canvas_w)} '
        f'{_num(canvas_h)}" width="{_num(canvas_w)}" height="{_num(canvas_h)}" '
        f'role="img" aria-label="{_attr(head or ir.kind)}">'
    )
    parts.append(f"<style>{_STYLE}</style>")
    parts.append("<defs>")
    parts.append(
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse">'
        '<path class="arrow-head" d="M 0 0 L 10 5 L 0 10 z"/></marker>'
    )
    parts.append("</defs>")
    parts.append('<rect class="bg" width="100%" height="100%"/>')

    if head:
        parts.append(f'<text class="title" x="{_num(MARGIN)}" y="30">{_attr(head)}</text>')
    parts.append(
        f'<text class="subtitle" x="{_num(MARGIN)}" y="{_num(TITLE_H - 8)}">'
        f'kind={_attr(ir.kind)} · {len(ir.nodes)} 节点 / {len(ir.edges)} 边</text>'
    )

    # 层带 + 层标题
    for i, key in enumerate(order):
        band_y = TITLE_H + MARGIN + i * (NODE_H + GAP_Y)
        band_cls = "layer-band alt" if i % 2 else "layer-band"
        parts.append(
            f'<rect class="{band_cls}" x="{_num(MARGIN / 2)}" y="{_num(band_y - 12)}" '
            f'width="{_num(base_w - MARGIN)}" height="{NODE_H + 24}" rx="10"/>'
        )
        if key:
            parts.append(
                f'<text class="layer-title" x="{_num(MARGIN / 2 + 12)}" y="{_num(band_y + 16)}">'
                f"{_attr(key)}</text>"
            )

    # 边（先画，节点压在上层）
    lane_x = base_w - MARGIN / 2 + 20
    for k, edge in enumerate(feedback):
        lane = lane_x + k * 16
        parts.append(_edge_svg(edge, pos, lane=lane, forward=False))
    for edge in forward:
        parts.append(_edge_svg(edge, pos, lane=0.0, forward=True))

    # 节点
    for node in ir.nodes:
        x, y = pos[node.id]
        parts.append(_node_svg(node, x, y, layer_index[node.group or ""]))

    # 图例
    if ir.legend:
        ly = content_bottom + MARGIN
        parts.append('<g class="legend">')
        lx = MARGIN
        for i, item in enumerate(ir.legend):
            parts.append(
                f'<rect class="shape layer-{i % PALETTE}" x="{_num(lx)}" y="{_num(ly - 10)}" '
                f'width="12" height="12" rx="3"/>'
            )
            parts.append(f'<text x="{_num(lx + 18)}" y="{_num(ly)}">{_attr(item)}</text>')
            lx += 18 + 11 * len(item) + 22
        parts.append("</g>")

    parts.append("</svg>")
    return "".join(parts) + "\n"


def _node_svg(node: Node, x: float, y: float, layer_idx: int) -> str:
    cls = f"node layer-{layer_idx % PALETTE}"
    if node.variant and node.variant != "default":
        cls += f" {node.variant}"
    cx = x + NODE_W / 2.0
    has_detail = bool(node.detail)
    label_y = y + (NODE_H / 2.0 - 2 if has_detail else NODE_H / 2.0 + 4)
    out = [
        f'<g class="{cls}" data-node-id="{_attr(node.id)}" data-layer="{_attr(node.group or "")}">',
        f"<title>{_attr(node.label)}</title>",
        f'<rect class="shape layer-{layer_idx % PALETTE}" x="{_num(x)}" y="{_num(y)}" '
        f'width="{NODE_W}" height="{NODE_H}" rx="6"/>',
        f'<text class="label" x="{_num(cx)}" y="{_num(label_y)}" text-anchor="middle">'
        f"{_attr(_truncate(node.label, 20))}</text>",
    ]
    if has_detail:
        out.append(
            f'<text class="detail" x="{_num(cx)}" y="{_num(y + NODE_H / 2.0 + 13)}" '
            f'text-anchor="middle">{_attr(_truncate(node.detail, 26))}</text>'
        )
    out.append("</g>")
    return "".join(out)


def _edge_svg(edge: Edge, pos: Dict[str, Tuple[float, float]], *, lane: float, forward: bool) -> str:
    sx, sy = pos[edge.source]
    tx, ty = pos[edge.target]
    if forward:
        s_bottom = sy + NODE_H
        t_top = ty
        sx_c = sx + NODE_W / 2.0
        tx_c = tx + NODE_W / 2.0
        mid_y = (s_bottom + t_top) / 2.0
        pts = [(sx_c, s_bottom), (sx_c, mid_y), (tx_c, mid_y), (tx_c, t_top)]
        label_x, label_y = (sx_c + tx_c) / 2.0, mid_y - 4
    else:
        s_right = sx + NODE_W
        t_right = tx + NODE_W
        sy_c = sy + NODE_H / 2.0
        ty_c = ty + NODE_H / 2.0
        pts = [(s_right, sy_c), (lane, sy_c), (lane, ty_c), (t_right, ty_c)]
        label_x, label_y = lane + 4, (sy_c + ty_c) / 2.0

    poly = " ".join(f"{_num(px)},{_num(py)}" for px, py in pts)
    out = [
        f'<g class="edge-group" data-edge-from="{_attr(edge.source)}" '
        f'data-edge-to="{_attr(edge.target)}">',
        f'<polyline class="edge {edge.kind}" points="{poly}" marker-end="url(#arrow)"/>',
    ]
    if edge.label:
        out.append(
            f'<text class="edge-label" x="{_num(label_x)}" y="{_num(label_y)}" '
            f'text-anchor="middle">{_attr(_truncate(edge.label, 12))}</text>'
        )
    out.append("</g>")
    return "".join(out)


__all__ = ["render_svg"]
