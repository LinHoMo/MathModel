"""viz 核心契约测试：DiagramIR 校验 / 确定性序列化 / SVG·HTML 渲染。

运行: py -3.12 -m pytest tests/unit/test_viz_core.py -q

对应计划「Wave 1」验收：
- 契约破损 fail-closed（重复 id / 悬空边 / 非法 kind / 非法 variant 均抛 DiagramIRError）；
- 同 IR 两次序列化与渲染字节相等（确定性硬约束）；
- 渲染产物为合法 XML 且节点集合与 IR 一致。
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import pytest  # noqa: E402

from modeling_harness.cli import diagram_gen  # noqa: E402
from modeling_harness.viz.html import render_html  # noqa: E402
from modeling_harness.viz.ir import (  # noqa: E402
    DiagramIR,
    DiagramIRError,
    Edge,
    Node,
)
from modeling_harness.viz.svg import render_svg  # noqa: E402


def _sample_ir() -> DiagramIR:
    return DiagramIR(
        kind="model_map",
        title="示例模型图",
        nodes=[
            Node(id="P", label="题面", group="L1 语义层"),
            Node(id="V", label="变量 V01", group="L1 语义层"),
            Node(id="ME", label="机理 ME01", group="L2 数学层"),
            Node(id="S", label="求解器 S01", group="L3 计算层", variant="emphasis"),
        ],
        edges=[
            Edge(source="P", target="V"),
            Edge(source="V", target="ME", label="构造"),
            Edge(source="ME", target="S", kind="dependency"),
        ],
        legend=["L1 语义层", "L2 数学层", "L3 计算层"],
    )


def _node_ids(svg: str) -> list:
    root = ET.fromstring(svg)
    return [el.get("data-node-id") for el in root.iter() if el.get("data-node-id")]


def _edge_pairs(svg: str) -> list:
    root = ET.fromstring(svg)
    return [
        (el.get("data-edge-from"), el.get("data-edge-to"))
        for el in root.iter()
        if el.get("data-edge-from")
    ]


# ---- 契约校验（fail-closed）--------------------------------------------------

def test_valid_ir_passes_validation():
    _sample_ir().validate()  # 不抛即通过


def test_duplicate_node_id_is_rejected():
    ir = DiagramIR(kind="model_map", nodes=[Node(id="A", label="a"), Node(id="A", label="b")])
    with pytest.raises(DiagramIRError, match="重复"):
        ir.validate()


def test_dangling_edge_is_rejected():
    ir = DiagramIR(
        kind="model_map",
        nodes=[Node(id="A", label="a")],
        edges=[Edge(source="A", target="MISSING")],
    )
    with pytest.raises(DiagramIRError, match="不存在"):
        ir.validate()


def test_unknown_kind_is_rejected():
    ir = DiagramIR(kind="not_a_kind", nodes=[Node(id="A", label="a")])
    with pytest.raises(DiagramIRError, match="kind"):
        ir.validate()


def test_unknown_variant_is_rejected():
    ir = DiagramIR(kind="model_map", nodes=[Node(id="A", label="a", variant="neon")])
    with pytest.raises(DiagramIRError, match="variant"):
        ir.validate()


def test_empty_nodes_is_rejected():
    with pytest.raises(DiagramIRError):
        DiagramIR(kind="model_map", nodes=[]).validate()


# ---- 序列化确定性 -------------------------------------------------------------

def test_json_roundtrip_preserves_structure():
    ir = _sample_ir()
    back = DiagramIR.from_json(ir.to_json())
    assert back == ir


def test_to_json_is_byte_stable():
    assert _sample_ir().to_json() == _sample_ir().to_json()
    assert _sample_ir().to_json().encode("utf-8") == _sample_ir().to_json().encode("utf-8")


def test_from_json_rejects_broken_ir():
    with pytest.raises(DiagramIRError):
        DiagramIR.from_json('{"schema_version": "1.0", "kind": "model_map", "nodes": []}')


# ---- SVG 渲染 ----------------------------------------------------------------

def test_svg_is_valid_xml_with_all_nodes_and_edges():
    svg = render_svg(_sample_ir())
    # 合法性：能解析为 XML
    ET.fromstring(svg)
    assert set(_node_ids(svg)) == {"P", "V", "ME", "S"}
    assert set(_edge_pairs(svg)) == {("P", "V"), ("V", "ME"), ("ME", "S")}
    assert "示例模型图" in svg


def test_svg_render_is_deterministic():
    assert render_svg(_sample_ir()) == render_svg(_sample_ir())


def test_svg_escapes_special_characters():
    ir = DiagramIR(kind="model_map", nodes=[Node(id="X", label="a & b <c>")])
    svg = render_svg(ir)
    ET.fromstring(svg)  # 未转义会解析失败
    assert "a &amp; b &lt;c&gt;" in svg


# ---- HTML 渲染 ---------------------------------------------------------------

def test_html_is_self_contained_and_embeds_svg():
    html = render_html(_sample_ir())
    assert html.lstrip().lower().startswith("<!doctype html")
    assert "<svg" in html
    assert "http://" not in html.replace("http://www.w3.org", "")  # 无外链依赖


def test_html_render_is_deterministic():
    assert render_html(_sample_ir()) == render_html(_sample_ir())


# ---- CLI build 子命令 --------------------------------------------------------

def test_cli_build_writes_svg_and_html(tmp_path):
    ir_path = tmp_path / "ir.json"
    ir_path.write_text(_sample_ir().to_json(), encoding="utf-8")
    svg_out = tmp_path / "out.svg"
    rc = diagram_gen.main(["build", str(ir_path), "-o", str(svg_out)])
    assert rc == 0
    ET.fromstring(svg_out.read_text(encoding="utf-8"))

    html_out = tmp_path / "out.html"
    assert diagram_gen.main(["build", str(ir_path), "-o", str(html_out)]) == 0
    assert html_out.read_text(encoding="utf-8").lstrip().lower().startswith("<!doctype html")


def test_cli_build_rejects_bad_ir(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version": "1.0", "kind": "model_map", "nodes": []}', encoding="utf-8")
    rc = diagram_gen.main(["build", str(bad), "-o", str(tmp_path / "x.svg")])
    assert rc != 0
    assert not (tmp_path / "x.svg").exists()  # fail-closed：不留半成品
