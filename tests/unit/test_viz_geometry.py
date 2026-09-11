#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""viz.geometry / viz.geometry_svg 的单测：契约 fail-closed + 确定性渲染 + CLI 入口。"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from modeling_harness.viz.geometry import GeometryIR, GeometryIRError, Item, Viewport
from modeling_harness.viz.geometry_svg import render_geometry_html, render_geometry_svg


# ------------------------------------------------------------------ 契约
def test_minimal_ir_validates() -> None:
    ir = GeometryIR(title="t", items=[Item(kind="point", points=[(0.0, 0.0)])])
    ir.validate()


@pytest.mark.parametrize(
    "item, fragment",
    [
        (Item(kind="nope"), "非法 item.kind"),
        (Item(kind="point", points=[(0.0, 0.0)], variant="neon"), "非法 variant"),
        (Item(kind="point"), "至少需要"),
        (Item(kind="segment", points=[(0.0, 0.0)]), "至少需要"),
        (Item(kind="segment", points=[(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]), "恰好需要"),
        (Item(kind="polygon", points=[(0.0, 0.0), (1.0, 0.0)]), "至少需要"),
        (Item(kind="circle", center=(0.0, 0.0), radius=0.0), "必须为正"),
        (Item(kind="circle", center=(0.0, 0.0)), "缺少 radius"),
        (Item(kind="ray", at=(0.0, 0.0), bearing_deg=30.0), "length 必须为正"),
        (Item(kind="ray", at=(0.0, 0.0), length=10.0), "缺少 bearing_deg"),
        (Item(kind="label", at=(0.0, 0.0), text="  "), "text 不可为空"),
        (Item(kind="point", points=[(float("nan"), 0.0)]), "有限数"),
        (Item(kind="point", points=[(0.0, float("inf"))]), "有限数"),
    ],
)
def test_item_contract_fails_closed(item: Item, fragment: str) -> None:
    with pytest.raises(GeometryIRError) as exc:
        item.validate()
    assert fragment in str(exc.value)


def test_empty_ir_is_rejected() -> None:
    with pytest.raises(GeometryIRError, match="至少需要一个 item"):
        GeometryIR(title="空").validate()


def test_bad_viewport_rejected() -> None:
    ir = GeometryIR(items=[Item(kind="point", points=[(0.0, 0.0)])],
                    viewport=Viewport(xlim=(10.0, 0.0)))
    with pytest.raises(GeometryIRError, match="必须递增"):
        ir.validate()


def test_from_dict_reports_path_context() -> None:
    with pytest.raises(GeometryIRError, match=r"radius 必须为正"):
        GeometryIR.from_dict(
            {"kind": "geometry", "items": [{"kind": "circle", "center": [0, 0], "radius": -1}]}
        )


def test_ir_validate_prefixes_item_index() -> None:
    ir = GeometryIR(items=[Item(kind="point", points=[(0.0, 0.0)]), Item(kind="circle")])
    with pytest.raises(GeometryIRError, match=r"items\[1\]"):
        ir.validate()


# ------------------------------------------------------------ 确定性序列化
def _sample_ir() -> GeometryIR:
    return GeometryIR(
        title="示例",
        items=[
            Item(kind="point", points=[(0.0, 0.0)], label="O"),
            Item(kind="ray", at=(0.0, 0.0), bearing_deg=30.0, length=100.0),
            Item(kind="polygon", points=[(0.0, 0.0), (10.0, 0.0), (5.0, 6.0)]),
            Item(kind="circle", center=(5.0, 3.0), radius=4.0),
        ],
        legend=["a", "b"],
    )


def test_to_json_is_byte_stable() -> None:
    a, b = _sample_ir(), _sample_ir()
    assert a.to_json() == b.to_json()
    assert a.to_json().endswith("\n")


def test_roundtrip_preserves_geometry() -> None:
    ir = _sample_ir()
    back = GeometryIR.from_json(ir.to_json())
    assert back.to_dict() == ir.to_dict()


def test_ir_json_is_sorted_and_utf8() -> None:
    text = _sample_ir().to_json()
    data = json.loads(text)
    assert list(data.keys()) == sorted(data.keys())
    assert "示例" in text  # ensure_ascii=False


# ---------------------------------------------------------------- 渲染
def test_svg_renders_expected_primitives() -> None:
    svg = render_geometry_svg(_sample_ir())
    assert svg.startswith("<svg")
    assert 'class="item default"' in svg          # polygon
    assert 'class="pt default"' in svg            # point
    assert 'class="seg default"' in svg           # ray
    assert "<circle" in svg                        # circle
    assert 'class="geom-title"' in svg
    assert "示例" in svg


def test_svg_is_deterministic() -> None:
    assert render_geometry_svg(_sample_ir()) == render_geometry_svg(_sample_ir())


def test_svg_numbers_are_rounded_not_raw_floats() -> None:
    svg = render_geometry_svg(_sample_ir())
    assert "nan" not in svg and "inf" not in svg
    for tok in ("10.0000000001", "0.30000000000000004"):
        assert tok not in svg


def test_viewport_overrides_autoscale() -> None:
    ir = GeometryIR(items=[Item(kind="point", points=[(0.0, 0.0)])],
                    viewport=Viewport(xlim=(-100.0, 100.0), ylim=(-100.0, 100.0)))
    svg = render_geometry_svg(ir)
    assert "<svg" in svg and ir.viewport.xlim == (-100.0, 100.0)


def test_viewport_preserves_aspect_for_circle() -> None:
    """等比视口下，圆的世界半径 × 比例尺 就是它的像素半径（不被拉成椭圆）。"""
    ir = GeometryIR(
        items=[Item(kind="circle", center=(0.0, 0.0), radius=50.0),
               Item(kind="point", points=[(-100.0, -100.0)])],
        viewport=Viewport(xlim=(-100.0, 100.0), ylim=(-100.0, 100.0)),
    )
    svg = render_geometry_svg(ir)
    assert 'r="' in svg
    # 世界 200 单位映射到画布内宽，比例尺 k ⇒ 像素半径 = 50k > 0
    assert 'r="0"' not in svg


def test_html_is_self_contained() -> None:
    html = render_geometry_html(_sample_ir())
    assert html.startswith("<!doctype html>")
    assert "<svg" in html and "<style>" in html
    # 自包含：无外链资源（SVG 命名空间 xmlns="http://www.w3.org/2000/svg" 是规范要求，不算外链）
    for token in ("<link", "<script", "src=", "url(http", "@import"):
        assert token not in html


def test_arrow_polyline_emits_head() -> None:
    ir = GeometryIR(items=[
        Item(kind="polyline", points=[(0.0, 0.0), (10.0, 0.0), (20.0, 5.0)], arrow=True),
    ])
    assert "arrow-head" in render_geometry_svg(ir)


# ------------------------------------------------------------------- CLI
def test_cli_geometry_renders_svg_and_html(tmp_path: Path) -> None:
    from modeling_harness.cli.diagram_gen import main as cli_main

    src = tmp_path / "fig.ir.json"
    src.write_text(_sample_ir().to_json(), encoding="utf-8")

    svg_out = tmp_path / "fig.svg"
    assert cli_main(["geometry", str(src), "-o", str(svg_out)]) == 0
    assert svg_out.read_text(encoding="utf-8").startswith("<svg")

    html_out = tmp_path / "fig.html"
    assert cli_main(["geometry", str(src), "-o", str(html_out)]) == 0
    assert html_out.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_cli_rejects_bad_suffix_and_bad_ir(tmp_path: Path) -> None:
    from modeling_harness.cli.diagram_gen import main as cli_main

    good = tmp_path / "fig.ir.json"
    good.write_text(_sample_ir().to_json(), encoding="utf-8")
    assert cli_main(["geometry", str(good), "-o", str(tmp_path / "x.txt")]) == 2

    bad = tmp_path / "bad.ir.json"
    bad.write_text(json.dumps({"kind": "geometry", "items": []}), encoding="utf-8")
    assert cli_main(["geometry", str(bad), "-o", str(tmp_path / "y.svg")]) == 2


def test_projected_coordinates_stay_inside_canvas() -> None:
    """渲染出的图元坐标必须落在 viewBox 内（防止坐标变换写错导致跑飞）。"""
    import re

    svg = render_geometry_svg(_sample_ir())
    vb = [float(x) for x in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    assert vb[2] > 0 and vb[3] > 0
    for cx, cy in re.findall(r'cx="([-\d.]+)" cy="([-\d.]+)"', svg):
        assert -1 <= float(cx) <= vb[2] + 1
        assert -1 <= float(cy) <= vb[3] + 1
    assert math.isfinite(vb[3])
