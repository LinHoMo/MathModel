#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diagram_gen.py — 科学图表生成 CLI（V3 P2）

用法:
    python src/modeling_harness/cli/diagram_gen.py flowchart --nodes "A,B,C" --edges "A->B,B->C" -o fig.svg
    python src/modeling_harness/cli/diagram_gen.py bar --data "类别A:10,类别B:25" -o bar.svg

零第三方依赖，输出 SVG。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

# 以「脚本路径」方式直接运行时（py -3.12 src/modeling_harness/cli/diagram_gen.py ...）
# 仍需能导入 modeling_harness.viz 包；以 mh / -m 方式运行时该插入为无害幂等。
_SRC = Path(__file__).resolve().parents[2]
if (_SRC / "modeling_harness").is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ROOT = Path(__file__).resolve().parents[3]

if TYPE_CHECKING:
    from modeling_harness.viz.ir import DiagramIR


def _svg_header(w: int, h: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'
        f'<rect width="100%" height="100%" fill="white"/>\n'
    )


def _svg_footer() -> str:
    return "</svg>\n"


def flowchart(nodes_str: str, edges_str: str, title: str = "") -> str:
    """简单的自上而下流程图。"""
    nodes = [n.strip() for n in nodes_str.split(",") if n.strip()]
    edges = [e.strip() for e in edges_str.split(",") if e.strip()]

    node_w, node_h = 120, 40
    gap_y = 30
    start_y = 60
    x_center = 200

    h = start_y + len(nodes) * (node_h + gap_y) + 40
    w = x_center * 2

    svg = _svg_header(w, h)
    if title:
        svg += f'<text x="{x_center}" y="30" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>\n'

    positions = {}
    for i, node in enumerate(nodes):
        y = start_y + i * (node_h + gap_y)
        positions[node] = (x_center, y + node_h // 2)
        svg += (
            f'<rect x="{x_center - node_w // 2}" y="{y}" '
            f'width="{node_w}" height="{node_h}" '
            f'rx="5" fill="#E3F2FD" stroke="#1565C0" stroke-width="1.5"/>\n'
        )
        svg += (
            f'<text x="{x_center}" y="{y + node_h // 2 + 5}" '
            f'text-anchor="middle" font-size="12">{node}</text>\n'
        )

    for edge in edges:
        parts = edge.split("->")
        if len(parts) != 2:
            continue
        src, dst = parts[0].strip(), parts[1].strip()
        if src in positions and dst in positions:
            x1, y1 = positions[src]
            x2, y2 = positions[dst]
            y1_top = y1 + node_h // 2
            y2_top = y2 - node_h // 2
            svg += (
                f'<line x1="{x1}" y1="{y1_top}" x2="{x2}" y2="{y2_top}" '
                f'stroke="#1565C0" stroke-width="1.5" marker-end="url(#arrow)"/>\n'
            )

    svg += (
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#1565C0"/></marker></defs>\n'
    )
    svg += _svg_footer()
    return svg


def bar_chart(data_str: str, title: str = "") -> str:
    """简单的竖向柱状图。"""
    items: List[Tuple[str, float]] = []
    for pair in data_str.split(","):
        if ":" in pair:
            label, raw = pair.split(":", 1)
            try:
                items.append((label.strip(), float(raw.strip())))
            except ValueError:
                continue

    if not items:
        return _svg_header(400, 200) + '<text x="200" y="100" text-anchor="middle">无数据</text>\n' + _svg_footer()

    max_val = max(v for _, v in items) or 1
    bar_w = 60
    gap = 20
    chart_h = 250
    start_x = 60
    start_y = 50
    w = start_x + len(items) * (bar_w + gap) + 20
    h = chart_h + 100

    svg = _svg_header(w, h)
    if title:
        svg += f'<text x="{w // 2}" y="30" text-anchor="middle" font-size="14" font-weight="bold">{title}</text>\n'

    for i, (label, val) in enumerate(items):
        x = start_x + i * (bar_w + gap)
        bar_h = (val / max_val) * chart_h * 0.8
        y = start_y + chart_h - bar_h
        svg += (
            f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" '
            f'fill="#42A5F5" stroke="#1565C0" stroke-width="1"/>\n'
        )
        svg += (
            f'<text x="{x + bar_w // 2}" y="{y - 5}" '
            f'text-anchor="middle" font-size="11">{val}</text>\n'
        )
        svg += (
            f'<text x="{x + bar_w // 2}" y="{start_y + chart_h + 20}" '
            f'text-anchor="middle" font-size="10">{label}</text>\n'
        )

    svg += _svg_footer()
    return svg


def _build_from_ir(args) -> int:
    """DiagramIR(JSON) → .svg/.html。fail-closed：破损 IR 不留半成品。"""
    from modeling_harness.viz.html import render_html
    from modeling_harness.viz.ir import DiagramIR, DiagramIRError
    from modeling_harness.viz.svg import render_svg

    try:
        ir = DiagramIR.load(args.ir)
    except (DiagramIRError, OSError) as exc:
        print(f"[FAIL] DiagramIR 破损: {exc}", file=sys.stderr)
        return 2
    if args.title:
        ir.title = args.title

    out = Path(args.output)
    suffix = out.suffix.lower()
    if suffix == ".svg":
        content = render_svg(ir)
    elif suffix in (".html", ".htm"):
        content = render_html(ir)
    else:
        print("[FAIL] 输出后缀须为 .svg 或 .html", file=sys.stderr)
        return 2

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"[OK] 图表已生成: {args.output}（kind={ir.kind}，"
          f"{len(ir.nodes)} 节点 / {len(ir.edges)} 边）")
    return 0


def _write_figure(ir: "DiagramIR", out_dir: Path, stem: str) -> List[Path]:
    """把 DiagramIR 落成 .ir.json（可 diff 源）+ .svg + .html 三件套。"""
    from modeling_harness.viz.html import render_html
    from modeling_harness.viz.svg import render_svg

    out_dir.mkdir(parents=True, exist_ok=True)
    ir_path = out_dir / f"{stem}.ir.json"
    ir_path.write_text(ir.to_json(), encoding="utf-8")
    svg_path = out_dir / f"{stem}.svg"
    svg_path.write_text(render_svg(ir), encoding="utf-8")
    html_path = out_dir / f"{stem}.html"
    html_path.write_text(render_html(ir), encoding="utf-8")
    return [ir_path, svg_path, html_path]


def _render_project(args) -> int:
    """projects/<name> → artifacts/figures/{model-map,evidence-graph}.*"""
    from modeling_harness.viz.extract import from_evidence_graph, from_model_ir
    from modeling_harness.viz.ir import DiagramIRError

    proj = ROOT / "projects" / args.name
    if not proj.is_dir():
        print(f"[FAIL] 项目不存在: {proj}", file=sys.stderr)
        return 2
    mir = proj / "model_ir.json"
    if not mir.is_file():
        print(f"[FAIL] 缺 model_ir.json: {mir}", file=sys.stderr)
        return 2

    fig_dir = proj / "artifacts" / "figures"
    try:
        written = _write_figure(from_model_ir(mir), fig_dir, "model-map")
        eg_path = proj / "state" / "evidence_graph.json"
        if not args.no_evidence and eg_path.is_file():
            written += _write_figure(from_evidence_graph(eg_path), fig_dir, "evidence-graph")
    except DiagramIRError as exc:
        print(f"[FAIL] 图表派生失败: {exc}", file=sys.stderr)
        return 2

    for path in written:
        print(f"[OK] 生成: {path.relative_to(ROOT).as_posix()}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="科学图表生成（SVG 输出）")
    sub = parser.add_subparsers(dest="chart_type", required=True)

    p_fc = sub.add_parser("flowchart", help="流程图")
    p_fc.add_argument("--nodes", required=True, help="节点列表，逗号分隔")
    p_fc.add_argument("--edges", required=True, help="边列表，逗号分隔（A->B 格式）")
    p_fc.add_argument("--title", default="", help="标题")
    p_fc.add_argument("-o", "--output", help="输出文件路径")

    p_bar = sub.add_parser("bar", help="柱状图")
    p_bar.add_argument("--data", required=True, help="数据（类别:值,类别:值）")
    p_bar.add_argument("--title", default="", help="标题")
    p_bar.add_argument("-o", "--output", help="输出文件路径")

    p_build = sub.add_parser("build", help="由 DiagramIR(JSON) 确定性渲染 SVG/HTML")
    p_build.add_argument("ir", help="DiagramIR JSON 路径")
    p_build.add_argument("-o", "--output", required=True, help="输出路径（.svg 或 .html）")
    p_build.add_argument("--title", default="", help="覆盖标题")

    p_proj = sub.add_parser("project", help="生成项目模型图（写 artifacts/figures/）")
    p_proj.add_argument("name", help="projects/<name> 项目名")
    p_proj.add_argument("--no-evidence", action="store_true", help="跳过 Evidence Graph")

    args = parser.parse_args(argv)

    if args.chart_type == "build":
        return _build_from_ir(args)
    if args.chart_type == "project":
        return _render_project(args)

    if args.chart_type == "flowchart":
        content = flowchart(args.nodes, args.edges, title=args.title)
    elif args.chart_type == "bar":
        content = bar_chart(args.data, title=args.title)
    else:
        parser.print_help()
        return 1

    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(f"[OK] 图表已生成: {args.output}")
    else:
        print(content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
