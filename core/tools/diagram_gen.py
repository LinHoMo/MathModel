#!/usr/bin/env python3
"""Scientific diagram generation tool for math modeling papers.

Supports: flowcharts, DAG visualization, result plots, comparison charts.
Output: SVG/PNG with publication-quality defaults.

Usage:
    python core/tools/diagram_gen.py flowchart --nodes "A,B,C" --edges "A->B,B->C" -o figures/flow.svg
    python core/tools/diagram_gen.py dag --spec work/model_dag.json -o figures/dag.svg
    python core/tools/diagram_gen.py result --data figures/all_results.json --type line -o figures/result.svg
    python core/tools/diagram_gen.py compare --data figures/all_results.json --metric accuracy -o figures/compare.svg
"""

import argparse
import json
import os
import sys
from pathlib import Path


def check_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return True
    except ImportError:
        print("ERROR: matplotlib not installed. Run: pip install matplotlib", file=sys.stderr)
        return False


def setup_style():
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    plt.rcParams.update({
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.figsize": (6, 4),
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def cmd_flowchart(args):
    """Generate a simple flowchart from node/edge specification."""
    if not check_matplotlib():
        return 1
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    setup_style()

    nodes = [n.strip() for n in args.nodes.split(",")]
    edges = []
    if args.edges:
        for e in args.edges.split(","):
            src, dst = e.strip().split("->")
            edges.append((src.strip(), dst.strip()))

    fig, ax = plt.subplots(figsize=(max(6, len(nodes) * 1.5), 4))
    ax.set_xlim(-0.5, len(nodes) + 0.5)
    ax.set_ylim(-1, 3)
    ax.axis("off")

    node_positions = {}
    box_width, box_height = 1.2, 0.8
    for i, node in enumerate(nodes):
        x = i * 1.5
        y = 1
        node_positions[node] = (x, y)
        box = FancyBboxPatch(
            (x - box_width / 2, y - box_height / 2),
            box_width, box_height,
            boxstyle="round,pad=0.1",
            facecolor="#E8F4FD",
            edgecolor="#2196F3",
            linewidth=1.5,
        )
        ax.add_patch(box)
        ax.text(x, y, node, ha="center", va="center", fontsize=9, fontweight="bold")

    for src, dst in edges:
        if src in node_positions and dst in node_positions:
            x1, y1 = node_positions[src]
            x2, y2 = node_positions[dst]
            arrow = FancyArrowPatch(
                (x1 + box_width / 2, y1),
                (x2 - box_width / 2, y2),
                arrowstyle="-|>",
                mutation_scale=15,
                color="#666666",
                linewidth=1.2,
            )
            ax.add_patch(arrow)

    output_path = args.output
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fig.savefig(output_path, format=os.path.splitext(output_path)[1].lstrip(".") or "svg")
    plt.close(fig)
    print(f"Flowchart saved to {output_path}")
    return 0


def _svg_escape(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def cmd_dag(args):
    """Generate DAG visualization from model_dag.json (pure SVG, zero third-party deps)."""
    with open(args.spec, "r", encoding="utf-8") as f:
        dag = json.load(f)

    nodes = dag.get("nodes", [])
    edges = dag.get("edges", [])

    if not nodes:
        print("WARNING: No nodes in DAG spec", file=sys.stderr)
        return 0

    # 层级：优先 topological_order（每层可并行），否则按 stage_order 聚合
    topo = dag.get("topological_order")
    node_ids = {nd["id"] for nd in nodes}
    if topo:
        levels = [[nid for nid in layer if nid in node_ids] for layer in topo]
    else:
        by_stage = {}
        for node in nodes:
            by_stage.setdefault(node.get("stage_order", node.get("level", 0)), []).append(node["id"])
        levels = [by_stage[k] for k in sorted(by_stage)]
    levels = [lv for lv in levels if lv]

    critical = set(dag.get("critical_path", []))
    node_by_id = {nd["id"]: nd for nd in nodes}

    box_w, box_h = 190, 46
    level_gap_x = 250
    node_gap_y = 72
    x0, y0 = 10, 20

    pos = {}
    for li, layer in enumerate(levels):
        x = x0 + li * level_gap_x
        n = len(layer)
        for i, nid in enumerate(layer):
            y = y0 + (n - 1) * node_gap_y / 2 - i * node_gap_y + node_gap_y
            pos[nid] = (x, y)

    max_nodes = max((len(lv) for lv in levels), default=1)
    width = x0 + len(levels) * level_gap_x + 30
    height = y0 + max_nodes * node_gap_y + node_gap_y + 20

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" font-family="sans-serif">']
    parts.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
                 'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                 '<path d="M 0 0 L 10 5 L 0 10 z" fill="#666"/></marker></defs>')

    for edge in edges:
        src = edge.get("source", edge.get("from", ""))
        dst = edge.get("target", edge.get("to", ""))
        if src not in pos or dst not in pos:
            continue
        x1, y1 = pos[src]
        x2, y2 = pos[dst]
        mx = (x1 + x2) / 2
        d = (f"M {x1 + box_w / 2} {y1 + box_h / 2} "
             f"C {mx} {y1 + box_h / 2}, {mx} {y2 + box_h / 2}, "
             f"{x2 - box_w / 2} {y2 + box_h / 2}")
        color = "#E65100" if edge.get("critical") else "#78909C"
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6" '
                     f'marker-end="url(#arrow)"/>')

    for node in nodes:
        nid = node["id"]
        if nid not in pos:
            continue
        x, y = pos[nid]
        is_crit = nid in critical
        fill = "#FFF3E0" if is_crit else "#E3F2FD"
        stroke = "#EF6C00" if is_crit else "#1E88E5"
        label = node.get("label", nid)
        if len(label) > 22:
            label = label[:21] + "…"
        parts.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        parts.append(f'<text x="{x + box_w / 2}" y="{y + box_h / 2 - 6}" text-anchor="middle" '
                     f'font-size="12" font-weight="bold">{_svg_escape(nid)}</text>')
        parts.append(f'<text x="{x + box_w / 2}" y="{y + box_h / 2 + 11}" text-anchor="middle" '
                     f'font-size="9" fill="#555">{_svg_escape(label)}</text>')

    parts.append('</svg>')
    svg_text = "\n".join(parts)

    output_path = args.output
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_text + "\n")
    print(f"DAG saved to {output_path} ({len(nodes)} nodes, {len(edges)} edges, pure SVG)")
    return 0


def cmd_result(args):
    """Generate result plot from all_results.json."""
    if not check_matplotlib():
        return 1
    import matplotlib.pyplot as plt

    setup_style()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    fig, ax = plt.subplots(figsize=(7, 4.5))

    plot_type = args.type or "bar"

    if plot_type == "line":
        results = data.get("results", data)
        if isinstance(results, dict):
            keys = list(results.keys())
            values = []
            for k in keys:
                v = results[k]
                if isinstance(v, dict):
                    values.append(v.get("value", v.get("mean", 0)))
                else:
                    values.append(float(v) if v else 0)
            ax.plot(range(len(keys)), values, "o-", color="#2196F3", linewidth=1.5, markersize=5)
            ax.set_xticks(range(len(keys)))
            ax.set_xticklabels(keys, rotation=45, ha="right")
        elif isinstance(results, list):
            x_vals = list(range(len(results)))
            y_vals = [r.get("value", 0) if isinstance(r, dict) else float(r) for r in results]
            ax.plot(x_vals, y_vals, "o-", color="#2196F3", linewidth=1.5, markersize=5)

    elif plot_type == "bar":
        results = data.get("results", data)
        if isinstance(results, dict):
            keys = list(results.keys())
            values = []
            for k in keys:
                v = results[k]
                if isinstance(v, dict):
                    values.append(v.get("value", v.get("mean", 0)))
                else:
                    values.append(float(v) if v else 0)
            colors = plt.cm.Set2([i / max(len(keys), 1) for i in range(len(keys))])
            ax.bar(range(len(keys)), values, color=colors, edgecolor="white", linewidth=0.5)
            ax.set_xticks(range(len(keys)))
            ax.set_xticklabels(keys, rotation=45, ha="right")

    elif plot_type == "scatter":
        results = data.get("results", data)
        if isinstance(results, list):
            x_vals = [r.get("x", i) for i, r in enumerate(results)]
            y_vals = [r.get("y", r.get("value", 0)) for r in results]
            ax.scatter(x_vals, y_vals, c="#2196F3", s=30, alpha=0.7, edgecolors="white", linewidth=0.5)

    elif plot_type == "heatmap":
        results = data.get("results", data)
        if isinstance(results, list) and results and isinstance(results[0], list):
            im = ax.imshow(results, cmap="YlOrRd", aspect="auto")
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set_ylabel(args.ylabel or "Value")
    ax.set_xlabel(args.xlabel or "")
    if args.title:
        ax.set_title(args.title)

    output_path = args.output
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fig.savefig(output_path, format=os.path.splitext(output_path)[1].lstrip(".") or "svg")
    plt.close(fig)
    print(f"Result plot saved to {output_path}")
    return 0


def cmd_compare(args):
    """Generate model comparison chart."""
    if not check_matplotlib():
        return 1
    import matplotlib.pyplot as plt
    import numpy as np

    setup_style()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    fig, ax = plt.subplots(figsize=(8, 5))

    models = data.get("models", data.get("candidates", []))
    metric = args.metric or "accuracy"

    if isinstance(models, list) and models:
        names = [m.get("name", f"Model {i+1}") for i, m in enumerate(models)]
        values = []
        stds = []
        for m in models:
            metrics = m.get("metrics", m)
            val = metrics.get(metric, metrics.get("value", 0))
            values.append(float(val) if val else 0)
            std = metrics.get(f"{metric}_std", metrics.get("std", 0))
            stds.append(float(std) if std else 0)

        x = np.arange(len(names))
        colors = plt.cm.Set2([i / max(len(names), 1) for i in range(len(names))])
        bars = ax.bar(x, values, yerr=stds, capsize=4, color=colors,
                      edgecolor="white", linewidth=0.5, alpha=0.9)

        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=30, ha="right")
        ax.set_ylabel(metric.replace("_", " ").title())

        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=8)

    if args.title:
        ax.set_title(args.title)
    else:
        ax.set_title(f"Model Comparison ({metric.replace('_', ' ').title()})")

    output_path = args.output
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fig.savefig(output_path, format=os.path.splitext(output_path)[1].lstrip(".") or "svg")
    plt.close(fig)
    print(f"Comparison chart saved to {output_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Scientific diagram generator for math modeling papers")
    subparsers = parser.add_subparsers(dest="command", help="Diagram type")

    p_flow = subparsers.add_parser("flowchart", help="Generate flowchart")
    p_flow.add_argument("--nodes", required=True, help="Comma-separated node names")
    p_flow.add_argument("--edges", help="Comma-separated edges (A->B,B->C)")
    p_flow.add_argument("-o", "--output", required=True, help="Output file path (SVG/PNG)")

    p_dag = subparsers.add_parser("dag", help="Generate DAG from model_dag.json")
    p_dag.add_argument("--spec", required=True, help="Path to model_dag.json")
    p_dag.add_argument("-o", "--output", required=True, help="Output file path")

    p_result = subparsers.add_parser("result", help="Generate result plot")
    p_result.add_argument("--data", required=True, help="Path to all_results.json")
    p_result.add_argument("--type", choices=["line", "bar", "scatter", "heatmap"], default="bar")
    p_result.add_argument("--title", help="Chart title")
    p_result.add_argument("--xlabel", help="X-axis label")
    p_result.add_argument("--ylabel", help="Y-axis label")
    p_result.add_argument("-o", "--output", required=True, help="Output file path")

    p_compare = subparsers.add_parser("compare", help="Generate model comparison chart")
    p_compare.add_argument("--data", required=True, help="Path to all_results.json")
    p_compare.add_argument("--metric", help="Metric to compare (default: accuracy)")
    p_compare.add_argument("--title", help="Chart title")
    p_compare.add_argument("-o", "--output", required=True, help="Output file path")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "flowchart": cmd_flowchart,
        "dag": cmd_dag,
        "result": cmd_result,
        "compare": cmd_compare,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
