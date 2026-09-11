#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""viz.html — DiagramIR → 自包含 HTML（内联 SVG + 语义 CSS，明暗双主题）。

单文件、零外链依赖（除 SVG 命名空间），无时间戳 → byte-stable。
携带「源真源」脚注，提醒读者产物为派生生成物、真源在 IR。
"""
from __future__ import annotations

from typing import Optional
from xml.sax.saxutils import escape

from modeling_harness.viz.ir import DiagramIR
from modeling_harness.viz.svg import render_svg

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


def render_html(ir: DiagramIR, *, svg: Optional[str] = None,
                source_note: str = "") -> str:
    """把 DiagramIR 渲染为自包含 HTML 文档（确定性）。"""
    ir.validate()
    body_svg = render_svg(ir) if svg is None else svg
    head = ir.title or ir.kind
    foot = source_note or (
        "本页为<a>生成物</a>——由 <code>mh diagram build</code> 从 DiagramIR 确定性渲染；"
        "真源在 IR（catalog / model_ir.json / evidence_graph.json）。"
    )
    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(head)}</title>\n"
        f"<style>{_HTML_STYLE}</style>\n</head>\n<body>\n"
        "<header>\n"
        f"<h1>{escape(head)}</h1>\n"
        f'<p class="meta">kind = {escape(ir.kind)} · {len(ir.nodes)} 节点 / '
        f"{len(ir.edges)} 边</p>\n</header>\n"
        f'<div class="canvas">{body_svg}</div>\n'
        f"<footer>{foot}</footer>\n"
        "</body>\n</html>\n"
    )


__all__ = ["render_html"]
