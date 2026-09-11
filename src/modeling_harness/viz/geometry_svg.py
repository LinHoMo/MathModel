#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""viz.geometry_svg — GeometryIR → 确定性 SVG / 自包含 HTML。

纯标准库、零第三方依赖；输出 byte-stable（无时间戳、无集合迭代序、坐标统一 1 位小数），
同一 IR 重复渲染字节相等，可直接 git diff。

世界坐标 → 画布坐标：由 IR 的 viewport（缺省时由 items 的包围盒自动取界）线性映射，
``equal_aspect`` 为真时保持等比，避免把圆画成椭圆。y 轴翻转（数学坐标向上为正）。
配色与明暗主题全部走 ``<style>`` 语义 class（含 ``prefers-color-scheme: dark``）。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple
from xml.sax.saxutils import escape

from modeling_harness.viz.geometry import GeometryIR, Item

CANVAS_W = 960.0
MARGIN = 44.0
TITLE_H = 46.0
LEGEND_H = 34.0
PAD_RATIO = 0.06

_STYLE = """\
:root{color-scheme:light dark}
text{font-family:-apple-system,'Segoe UI','Microsoft YaHei',Roboto,Helvetica,Arial,sans-serif}
.geom-bg{fill:#ffffff}
.geom-title{fill:#1a237e;font-size:17px;font-weight:700}
.geom-sub{fill:#78909c;font-size:11px}
.geom-frame{fill:none;stroke:#e0e6ec;stroke-width:1}
.tick{stroke:#eceff1;stroke-width:1}
.geom-axis{stroke:#b0bec5;stroke-width:1.2}
.geom-axis-label{fill:#90a4ae;font-size:10px}
.geom-label{fill:#102027;font-size:11px}
.geom-legend text{fill:#37474f;font-size:11px}
.item{stroke-width:1.8}
.item.default{fill:#e3f2fd;stroke:#1565c0}
.item.accent{fill:#e8f5e9;stroke:#2e7d32}
.item.emphasis{fill:#fff3e0;stroke:#ef6c00;stroke-width:2.6}
.item.danger{fill:#ffebee;stroke:#c62828;stroke-width:2.6}
.item.muted{fill:none;stroke:#b0bec5;stroke-dasharray:5 4}
.item.dashed{fill:none;stroke:#7e57c2;stroke-dasharray:7 5}
.seg{stroke-width:1.8;fill:none}
.seg.default{stroke:#1565c0}
.seg.accent{stroke:#2e7d32}
.seg.emphasis{stroke:#ef6c00;stroke-width:2.6}
.seg.danger{stroke:#c62828;stroke-width:2.6}
.seg.muted{stroke:#b0bec5;stroke-dasharray:5 4}
.seg.dashed{stroke:#7e57c2;stroke-dasharray:7 5}
.pt{stroke-width:1.4}
.pt.default{fill:#1565c0;stroke:#ffffff}
.pt.accent{fill:#2e7d32;stroke:#ffffff}
.pt.emphasis{fill:#ef6c00;stroke:#ffffff;stroke-width:2.2}
.pt.danger{fill:#c62828;stroke:#ffffff;stroke-width:2.2}
.pt.muted{fill:#b0bec5;stroke:#ffffff}
.pt.dashed{fill:#7e57c2;stroke:#ffffff}
.arrow-head{stroke:none}
.arrow-head.default{fill:#1565c0}
.arrow-head.accent{fill:#2e7d32}
.arrow-head.emphasis{fill:#ef6c00}
.arrow-head.danger{fill:#c62828}
.arrow-head.muted{fill:#b0bec5}
.arrow-head.dashed{fill:#7e57c2}
@media (prefers-color-scheme:dark){
.geom-bg{fill:#0f1419}
.geom-title{fill:#90caf9}
.geom-sub{fill:#90a4ae}
.geom-frame{stroke:#22303c}
.tick{stroke:#1b232b}
.geom-axis{stroke:#546e7a}
.geom-axis-label{fill:#78909c}
.geom-label{fill:#eceff1}
.geom-legend text{fill:#cfd8dc}
.item.default{fill:#102a43;stroke:#4a90d9}
.item.accent{fill:#10331f;stroke:#4caf50}
.item.emphasis{fill:#3a2a12;stroke:#ffa726}
.item.danger{fill:#33161a;stroke:#ef5350}
.item.muted{stroke:#546e7a}
.item.dashed{stroke:#ab47bc}
.seg.default{stroke:#4a90d9}
.seg.accent{stroke:#4caf50}
.seg.emphasis{stroke:#ffa726}
.seg.danger{stroke:#ef5350}
.seg.muted{stroke:#546e7a}
.seg.dashed{stroke:#ab47bc}
.pt.default{stroke:#0f1419}
.pt.accent{stroke:#0f1419}
.pt.emphasis{stroke:#0f1419}
.pt.danger{stroke:#0f1419}
.pt.muted{stroke:#0f1419}
.pt.dashed{stroke:#0f1419}
.arrow-head.default{fill:#4a90d9}
.arrow-head.accent{fill:#4caf50}
.arrow-head.emphasis{fill:#ffa726}
.arrow-head.danger{fill:#ef5350}
.arrow-head.muted{fill:#546e7a}
.arrow-head.dashed{fill:#ab47bc}
}
"""


def _num(value: float) -> str:
    """统一 1 位小数并去尾零 → 确定性且紧凑。"""
    return f"{round(float(value), 1):g}"


def _attr(value: object) -> str:
    return escape(str(value), {'"': "&quot;"})


def _est_width(text: str, font_px: float) -> float:
    total = 0.0
    for ch in text:
        total += font_px * (1.0 if ord(ch) > 0x2E80 else 0.56)
    return total


def _content_bounds(ir: GeometryIR) -> Tuple[float, float, float, float]:
    boxes = [b for b in (i.bounds() for i in ir.items) if b is not None]
    if not boxes:
        raise ValueError("GeometryIR 无可用坐标包围盒")
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes)
    y1 = max(b[3] for b in boxes)
    return x0, y0, x1, y1


class _Projector:
    """世界坐标 → 画布坐标的等比线性映射（y 轴翻转）。"""

    def __init__(self, ir: GeometryIR) -> None:
        bx0, by0, bx1, by1 = _content_bounds(ir)
        vp = ir.viewport
        if vp.xlim is not None:
            bx0, bx1 = float(vp.xlim[0]), float(vp.xlim[1])
        if vp.ylim is not None:
            by0, by1 = float(vp.ylim[0]), float(vp.ylim[1])
        dx = max(bx1 - bx0, 1e-9)
        dy = max(by1 - by0, 1e-9)
        pad = PAD_RATIO * max(dx, dy)
        if vp.xlim is None:
            bx0, bx1 = bx0 - pad, bx1 + pad
        if vp.ylim is None:
            by0, by1 = by0 - pad, by1 + pad
        dx, dy = max(bx1 - bx0, 1e-9), max(by1 - by0, 1e-9)

        inner_w = CANVAS_W - 2 * MARGIN
        kx = inner_w / dx
        ky = (inner_w / dy) if dy > 0 else kx
        self.k = min(kx, ky) if vp.equal_aspect else ky
        self.x0, self.y1 = bx0, by1
        self.top = TITLE_H + MARGIN
        self.height = (by1 - by0) * self.k + 2 * MARGIN + TITLE_H + LEGEND_H
        self.y0 = by0

    def xy(self, x: float, y: float) -> Tuple[float, float]:
        return (MARGIN + (float(x) - self.x0) * self.k,
                self.top + (self.y1 - float(y)) * self.k)


def _arrowhead(px: float, py: float, angle: float, variant: str, size: float = 8.0) -> str:
    a1 = angle + math.radians(155.0)
    a2 = angle - math.radians(155.0)
    pts = [
        (px, py),
        (px + size * math.cos(a1), py + size * math.sin(a1)),
        (px + size * math.cos(a2), py + size * math.sin(a2)),
    ]
    d = " ".join(f"{_num(p[0])},{_num(p[1])}" for p in pts)
    return f'<polygon class="arrow-head {_attr(variant)}" points="{d}"/>'


def _item_svg(item: Item, pr: _Projector) -> List[str]:
    v = item.variant
    out: List[str] = []
    if item.kind == "point":
        sx, sy = pr.xy(*item.points[0])
        out.append(f'<circle class="pt {_attr(v)}" cx="{_num(sx)}" cy="{_num(sy)}" r="3.6"/>')
        anchor = (sx + 7, sy - 7)
    elif item.kind == "segment":
        (x1, y1), (x2, y2) = item.points
        a, b = pr.xy(x1, y1), pr.xy(x2, y2)
        out.append(
            f'<line class="seg {_attr(v)}" x1="{_num(a[0])}" y1="{_num(a[1])}" '
            f'x2="{_num(b[0])}" y2="{_num(b[1])}"/>'
        )
        anchor = ((a[0] + b[0]) / 2 + 6, (a[1] + b[1]) / 2 - 6)
    elif item.kind == "ray":
        if item.at is None or item.bearing_deg is None or item.length is None:  # validate() 已保证
            return out
        sx, sy = pr.xy(*item.at)
        ang = math.radians(float(item.bearing_deg))
        ex_w = item.at[0] + float(item.length) * math.cos(ang)
        ey_w = item.at[1] + float(item.length) * math.sin(ang)
        ex, ey = pr.xy(ex_w, ey_w)
        out.append(
            f'<line class="seg {_attr(v)}" x1="{_num(sx)}" y1="{_num(sy)}" '
            f'x2="{_num(ex)}" y2="{_num(ey)}"/>'
        )
        # 画布 y 向下，世界方位角逆时针 → 屏幕角取负
        out.append(_arrowhead(ex, ey, -ang, v))
        anchor = (sx + 6, sy + 14)
    elif item.kind == "polygon":
        pts = " ".join(
            f"{_num(a)},{_num(b)}" for a, b in (pr.xy(x, y) for x, y in item.points)
        )
        out.append(f'<polygon class="item {_attr(v)}" points="{pts}"/>')
        cxs = [pr.xy(x, y)[0] for x, y in item.points]
        cys = [pr.xy(x, y)[1] for x, y in item.points]
        anchor = (sum(cxs) / len(cxs), sum(cys) / len(cys))
    elif item.kind == "polyline":
        pts = " ".join(
            f"{_num(a)},{_num(b)}" for a, b in (pr.xy(x, y) for x, y in item.points)
        )
        out.append(f'<polyline class="seg {_attr(v)}" points="{pts}"/>')
        if item.arrow:
            (x1, y1), (x2, y2) = item.points[-2], item.points[-1]
            a, b = pr.xy(x1, y1), pr.xy(x2, y2)
            out.append(_arrowhead(b[0], b[1], math.atan2(b[1] - a[1], b[0] - a[0]), v))
        lx, ly = pr.xy(*item.points[-1])
        anchor = (lx + 7, ly - 7)
    elif item.kind == "circle":
        if item.center is None or item.radius is None:  # validate() 已保证
            return out
        sx, sy = pr.xy(*item.center)
        r_px = float(item.radius) * pr.k
        out.append(
            f'<circle class="item {_attr(v)}" cx="{_num(sx)}" cy="{_num(sy)}" '
            f'r="{_num(r_px)}"/>'
        )
        anchor = (sx, sy + r_px + 13)
    elif item.kind == "label":
        if item.at is None:  # validate() 已保证
            return out
        sx, sy = pr.xy(*item.at)
        out.append(
            f'<text class="geom-label" x="{_num(sx)}" y="{_num(sy)}" '
            f'text-anchor="middle">{escape(item.text)}</text>'
        )
        return out
    else:  # pragma: no cover - validate() 已拦
        return out

    if item.label:
        out.append(
            f'<text class="geom-label" x="{_num(anchor[0])}" y="{_num(anchor[1])}">'
            f"{escape(item.label)}</text>"
        )
    return out


def render_geometry_svg(ir: GeometryIR, *, subtitle: str = "") -> str:
    """把 GeometryIR 渲染为自包含 SVG 文本（确定性）。"""
    ir.validate()
    pr = _Projector(ir)
    h = pr.height
    body: List[str] = []

    body.append(f'<rect class="geom-bg" x="0" y="0" width="{_num(CANVAS_W)}" height="{_num(h)}"/>')
    body.append(
        f'<rect class="geom-frame" x="{_num(MARGIN / 2)}" y="{_num(TITLE_H + MARGIN / 2)}" '
        f'width="{_num(CANVAS_W - MARGIN)}" height="{_num(h - TITLE_H - LEGEND_H - MARGIN)}"/>'
    )
    if ir.title:
        body.append(
            f'<text class="geom-title" x="{_num(MARGIN / 2 + 6)}" y="24">'
            f"{escape(ir.title)}</text>"
        )
    sub = subtitle or f"kind = {ir.kind} · {len(ir.items)} 图元"
    body.append(f'<text class="geom-sub" x="{_num(MARGIN / 2 + 6)}" y="40">{escape(sub)}</text>')

    for item in ir.items:
        body.extend(_item_svg(item, pr))

    if ir.legend:
        ly = h - LEGEND_H + 8
        lx = MARGIN / 2 + 6
        for entry in ir.legend:
            body.append(
                f'<text class="geom-legend" x="{_num(lx)}" y="{_num(ly)}">'
                f"• {escape(entry)}</text>"
            )
            lx += _est_width(entry, 11.0) + 22

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'viewBox="0 0 {_num(CANVAS_W)} {_num(h)}" width="{_num(CANVAS_W)}" height="{_num(h)}">\n'
        f"<style>{_STYLE}</style>\n" + "\n".join(body) + "\n</svg>\n"
    )


_HTML_STYLE = """\
:root{color-scheme:light dark}
*{box-sizing:border-box}
body{margin:0;padding:24px;
  font-family:-apple-system,'Segoe UI','Microsoft YaHei',Roboto,Helvetica,Arial,sans-serif;
  background:#ffffff;color:#102027}
header h1{margin:0 0 4px;font-size:20px;color:#1a237e}
header .meta{margin:0;font-size:12px;color:#607d8b}
.canvas{margin:16px 0;overflow:auto;border:1px solid #e0e6ec;border-radius:10px;background:#fff}
footer{margin-top:16px;font-size:11px;color:#90a4ae}
footer code{background:#f4f7fa;padding:1px 5px;border-radius:4px}
@media (prefers-color-scheme:dark){
body{background:#0f1419;color:#eceff1}
header h1{color:#90caf9}
header .meta{color:#90a4ae}
.canvas{background:#0f1419;border-color:#22303c}
footer{color:#78909c}
footer code{background:#1b232b}
}
"""


def render_geometry_html(ir: GeometryIR, *, svg: Optional[str] = None,
                         source_note: str = "") -> str:
    """把 GeometryIR 渲染为自包含 HTML 文档（确定性）。"""
    ir.validate()
    body_svg = render_geometry_svg(ir) if svg is None else svg
    head = ir.title or ir.kind
    foot = source_note or (
        "本页为生成物——由 <code>mh diagram geometry</code> 从 GeometryIR 确定性渲染；"
        "真源在 IR（其数值应可追溯到模型定义与结果台账）。"
    )
    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(head)}</title>\n"
        f"<style>{_HTML_STYLE}</style>\n</head>\n<body>\n"
        "<header>\n"
        f"<h1>{escape(head)}</h1>\n"
        f'<p class="meta">kind = {escape(ir.kind)} · {len(ir.items)} 图元</p>\n</header>\n'
        f'<div class="canvas">{body_svg}</div>\n'
        f"<footer>{foot}</footer>\n"
        "</body>\n</html>\n"
    )


__all__ = ["render_geometry_svg", "render_geometry_html", "CANVAS_W"]
