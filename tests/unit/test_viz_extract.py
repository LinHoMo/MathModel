"""viz.extract 测试：MODEL_IR / Evidence Graph → DiagramIR 的派生正确性与确定性。

运行: py -3.12 -m pytest tests/unit/test_viz_extract.py -q

对应计划「Wave 2」验收：生成 SVG 的节点数须等于 model_ir.json 的 model_graph
节点数（用测试断言，非目测）；缺失源 fail-closed。
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import pytest  # noqa: E402

from modeling_harness.viz.extract import (  # noqa: E402
    MODEL_LAYER,
    from_evidence_graph,
    from_model_ir,
)
from modeling_harness.viz.ir import DiagramIRError  # noqa: E402
from modeling_harness.viz.svg import render_svg  # noqa: E402

PROJECTS = REPO / "projects"


def _node_ids(svg: str) -> list:
    root = ET.fromstring(svg)
    return [el.get("data-node-id") for el in root.iter() if el.get("data-node-id")]


def _write_ir(tmp_path: Path, payload: dict) -> Path:
    p = tmp_path / "model_ir.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return p


def test_model_ir_maps_types_to_layers(tmp_path):
    mir = _write_ir(tmp_path, {
        "title": "T",
        "model_graph": {
            "nodes": [
                {"id": "Q", "label": "题面", "type": "problem"},
                {"id": "ME01", "label": "机理", "type": "mechanism"},
                {"id": "SV", "label": "求解", "type": "solver"},
                {"id": "ZZ", "label": "未分类", "type": "weird_type"},
            ],
            "edges": [{"from": "Q", "to": "ME01", "relation": "x"},
                      {"from": "ZZ", "to": "ZZ", "relation": "self"}],
        },
    })
    ir = from_model_ir(mir)
    assert ir.kind == "model_map"
    assert ir.title == "T"
    groups = {n.id: n.group for n in ir.nodes}
    assert groups["Q"] == MODEL_LAYER["problem"]
    assert groups["ME01"] == MODEL_LAYER["mechanism"]
    assert groups["SV"] == MODEL_LAYER["solver"]
    assert groups["ZZ"] == "其他"
    assert [(e.source, e.target) for e in ir.edges] == [("Q", "ME01"), ("ZZ", "ZZ")]


def test_model_ir_missing_file_fails_closed(tmp_path):
    with pytest.raises(DiagramIRError):
        from_model_ir(tmp_path / "nope.json")


def test_model_ir_without_graph_fails_closed(tmp_path):
    mir = _write_ir(tmp_path, {"title": "T"})
    with pytest.raises(DiagramIRError, match="model_graph"):
        from_model_ir(mir)


@pytest.mark.parametrize("name", ["cumcm2024a", "cumcm2026a", "cumcm2026b"])
def test_svg_node_count_equals_model_graph(name):
    mir = PROJECTS / name / "model_ir.json"
    if not mir.is_file():  # 库模式/裁剪克隆下跳过
        pytest.skip(f"{name} 无 model_ir.json")
    expected = len(json.loads(mir.read_text(encoding="utf-8"))["model_graph"]["nodes"])
    svg = render_svg(from_model_ir(mir))
    assert len(_node_ids(svg)) == expected


def test_model_ir_derivation_is_deterministic():
    mir = PROJECTS / "cumcm2026b" / "model_ir.json"
    if not mir.is_file():
        pytest.skip("cumcm2026b 无 model_ir.json")
    assert render_svg(from_model_ir(mir)) == render_svg(from_model_ir(mir))


def test_evidence_graph_derivation():
    eg = PROJECTS / "cumcm2026b" / "state" / "evidence_graph.json"
    if not eg.is_file():
        pytest.skip("无 evidence_graph.json")
    ir = from_evidence_graph(eg)
    assert ir.kind == "evidence_graph"
    assert ir.nodes and ir.edges
    svg = render_svg(ir)
    assert len(_node_ids(svg)) == len(ir.nodes)


def test_evidence_graph_empty_relations_fails_closed(tmp_path):
    p = tmp_path / "eg.json"
    p.write_text(json.dumps({"relations": []}), encoding="utf-8")
    with pytest.raises(DiagramIRError):
        from_evidence_graph(p)
