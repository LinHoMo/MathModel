#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_figures.py —— 由模型真源生成 B 题的二维几何图示（GeometryIR → SVG/HTML）。

为什么需要：本模型的主体是平面几何（楔形角域交集、凸多边形定位区域、外接圆覆盖判据、
同心环覆盖网），纯文字与公式对人不友好。本脚本把模型里的**真实坐标与真实数字**渲染成
可直接在浏览器打开的图，并保证「图上的每个数都能在结果台账里找到出处」：

  * 算例 A / 反例的站址、源址、示向度 → ``artifacts/q1q2_v2_results.json``
  * 多边形、直径、最小包围圆            → 用 ``solve_b.location_region`` /
                                          ``diameter_circle_covers`` 现算（与求解同一份代码）
  * 覆盖环半径与检测点                  → 用 ``solve_b.coverage_detection_points`` 现算

产物（写入 ``artifacts/figures/``）：每个图三件套 ``<name>.ir.json``（真源）/ ``.svg`` /
``.html``。确定性：同一输入重复运行字节相等，可直接 git diff。

运行：``py -3.12 -X utf8 -m make_figures``（在 ``artifacts/code/`` 下）
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent.parent
REPO = PROJ.parent.parent

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.viz.geometry import GeometryIR, Item, Viewport  # noqa: E402
from modeling_harness.viz.geometry_svg import (  # noqa: E402
    render_geometry_html, render_geometry_svg,
)

import solve_b as S  # noqa: E402

FIGDIR = PROJ / "artifacts" / "figures"
EPS = S.EPS_BEARING


# ---------------------------------------------------------------- 图 1：楔形交会
def fig_wedge_region(zoom: bool = False) -> GeometryIR:
    """Q1 算例 A：两站四条 ±1° 边界射线交出一个凸多边形定位区域。

    ``zoom=False`` 给全局（站点 + 楔形走向 + 区域位置）；``zoom=True`` 把视口收到
    定位区域附近 —— 区域直径只有 46.9 m 而射线长 1600 m，不放大就只是全局图上的一个点，
    「让人看懂」的目标落空。两图共用同一份真源数据，只是视口不同。
    """
    data = json.loads((PROJ / "artifacts" / "q1q2_v2_results.json").read_text(encoding="utf-8"))
    case = data["problem1"]["cases"][0]
    stations = [tuple(p) for p in case["stations"]]
    bears = list(case["true_bearings_deg"])
    src = tuple(case["source"])

    reg = S.location_region(stations, bears)
    covers, diam, cd, rd, mec_c, mec_r = S.diameter_circle_covers(reg)

    items: list[Item] = []
    # 四条边界射线（每条示向度 ±ε 两条）；放大视口下由 viewBox 自然裁切
    for (sx, sy), b in zip(stations, bears):
        for off in (-EPS, EPS):
            items.append(Item(kind="ray", at=(sx, sy), bearing_deg=b + off, length=1600.0,
                              variant="muted"))
    # 定位区域
    items.append(Item(kind="polygon", points=list(reg), label="定位区域 Ω",
                      variant="emphasis"))
    # 直径圆（虚线）与最小包围圆
    items.append(Item(kind="circle", center=cd, radius=rd, variant="dashed",
                      label=f"直径圆 r={rd:.3f} m"))
    items.append(Item(kind="circle", center=mec_c, radius=mec_r, variant="dashed"))
    # 直径端点连线
    items.append(Item(kind="segment", points=[tuple(reg[0]), tuple(reg[2])], variant="danger",
                      label=f"直径 D={diam:.3f} m"))
    # 站点与源
    for i, (sx, sy) in enumerate(stations):
        items.append(Item(kind="point", points=[(sx, sy)], variant="accent",
                          label=f"S{i + 1}"))
    items.append(Item(kind="point", points=[src], variant="default", label="真源 G"))

    if zoom:
        half = max(diam, mec_r * 2.0) * 2.2
        cx = sum(p[0] for p in reg) / len(reg)
        cy = sum(p[1] for p in reg) / len(reg)
        span = max(half, 1.0)
        viewport = Viewport(xlim=(cx - span, cx + span), ylim=(cy - span, cy + span),
                            equal_aspect=True)
        title = (f"问题 1：定位区域放大（算例 A，χ={case['crossing_angle_deg']:.0f}°，"
                 f"直径 {diam:.3f} m）")
        legend = [f"每条示向度张成 2° 角域（±{EPS:g}°），四条界线围出凸多边形 Ω",
                  f"区域直径 D={diam:.3f} m",
                  f"最小包围圆半径 {mec_r:.3f} m（与直径圆同值 ⇒ 落在覆盖成立的边界）",
                  f"直径圆覆盖判定：{'成立' if covers else '不成立'}"]
    else:
        viewport = Viewport(equal_aspect=True)
        title = f"问题 1：两站楔形交会的全局（算例 A，χ={case['crossing_angle_deg']:.0f}°）"
        legend = [f"示向度误差 ±{EPS:g}° → 每条示向度张成 2° 角域",
                  "两条窄楔形的交集即定位区域 Ω（见同目录放大图）",
                  f"区域直径 D={diam:.3f} m",
                  f"直径圆覆盖判定：{'成立' if covers else '不成立'}"]

    return GeometryIR(title=title, items=items, viewport=viewport, legend=legend)


# ---------------------------------------------------------------- 图 2：Thales 反例
def fig_coverage_counterexample() -> GeometryIR:
    """Q1 反例：锐角三角形上「以直径为直径的圆」盖不住最小包围圆。"""
    data = json.loads((PROJ / "artifacts" / "q1q2_v2_results.json").read_text(encoding="utf-8"))
    tri = [(0.0, 0.0), (10.0, 0.0), (5.0, 6.0)]
    covers, diam, cd, rd, mec_c, mec_r = S.diameter_circle_covers(tri)

    items = [
        Item(kind="polygon", points=tri, variant="emphasis", label="定位区域（锐角三角形）"),
        Item(kind="circle", center=cd, radius=rd, variant="dashed",
             label=f"直径圆 r={rd:g} m"),
        Item(kind="circle", center=mec_c, radius=mec_r, variant="danger",
             label=f"最小包围圆 r={mec_r:.4f} m"),
        Item(kind="segment", points=[(0.0, 0.0), (10.0, 0.0)], variant="danger",
             label=f"D={diam:g} m"),
    ]
    return GeometryIR(
        title="问题 1：Thales 判据的反例 —— 直径圆不覆盖定位区域",
        items=items,
        viewport=Viewport(equal_aspect=True),
        legend=[f"直径圆半径 {rd:g} m < 最小包围圆半径 {mec_r:.4f} m",
                "覆盖成立 ⟺ 各顶点对直径端点张角 ≥90°（Thales）",
                f"本例判定：{'覆盖成立' if covers else '覆盖不成立'}"],
    )


# ---------------------------------------------------------------- 图 3：覆盖环
def fig_cover_rings() -> GeometryIR:
    """Q3/Q4 覆盖网：同心环 + 检测点 + 最近邻路线 + 目标区域。"""
    pts_omni = S.coverage_detection_points(False)
    pts_dir = S.coverage_detection_points(True)
    extra = [p for p in pts_dir if p not in pts_omni]

    items: list[Item] = [
        Item(kind="circle", center=(0.0, 0.0), radius=S.R_AREA, variant="muted",
             label=f"目标区域 R={S.R_AREA:g} m"),
        Item(kind="point", points=[(0.0, 0.0)], variant="accent", label="机器狗起点 O"),
    ]
    for r in S.COVER_RADII_OMNI:
        items.append(Item(kind="circle", center=(0.0, 0.0), radius=float(r), variant="dashed"))
    if extra:
        items.append(Item(kind="circle", center=(0.0, 0.0), radius=S.COVER_RADII_DIR[-1],
                          variant="danger", label=f"定向外侧环 r={S.COVER_RADII_DIR[-1]:g} m"))
    items.append(Item(kind="polyline", points=list(pts_omni), arrow=False, variant="default",
                      label="全向扫描路线（最近邻排序）"))
    for p in pts_omni:
        items.append(Item(kind="point", points=[p], variant="default"))
    for p in extra:
        items.append(Item(kind="point", points=[p], variant="danger"))

    return GeometryIR(
        title="问题 3/4：同心环覆盖网与最近邻扫描路线",
        items=items,
        viewport=Viewport(equal_aspect=True),
        legend=[f"全向环 {list(S.COVER_RADII_OMNI)} → {len(pts_omni)} 个检测点",
                f"定向另加外侧环 {S.COVER_RADII_DIR[-1]:g} m → 共 {len(pts_dir)} 点",
                "径向完备性：任意点到最近环 ≤ R/(2k) = 450 m ≪ 最小接收半径 1000 m",
                "弧向步长按环角色分级（500 / 900 / 1050 m）"],
    )


FIGS = {
    "fig_q1_wedge_global": lambda: fig_wedge_region(zoom=False),
    "fig_q1_wedge_zoom": lambda: fig_wedge_region(zoom=True),
    "fig_q1_coverage_counterexample": fig_coverage_counterexample,
    "fig_q3_cover_rings": fig_cover_rings,
}


def main() -> int:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    for name, builder in FIGS.items():
        ir = builder()
        ir.validate()
        svg = render_geometry_svg(ir)
        html = render_geometry_html(ir, svg=svg)
        (FIGDIR / f"{name}.ir.json").write_text(ir.to_json(), encoding="utf-8")
        (FIGDIR / f"{name}.svg").write_text(svg, encoding="utf-8")
        (FIGDIR / f"{name}.html").write_text(html, encoding="utf-8")
        print(f"[OK] {name}: {len(ir.items)} 图元 -> {FIGDIR.name}/{name}.{{ir.json,svg,html}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
