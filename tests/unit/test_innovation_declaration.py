# -*- coding: utf-8 -*-
"""R4 创新声明契约门禁（check_innovation_declaration）语义测试。

判据来源：docs/architecture/MODEL_QUALITY_CRITERIA.md §3（R4，v1.1）。

规则（契约检查，防「自称创新」）：
  * model_ir.json 顶层 `innovation`（可选）若声明必须结构合法：
      - dimensions 键 ∈ {mechanism_novelty, solver_novelty,
        composition_novelty, representation_novelty}，值 ∈ [0,1]；
      - structure_distance ∈ [0,1]（可缺省，缺省时由 R3 工具计算）；
      - 任一维度 > 0 → difference_arguments 非空，且对应维度有
        vs_known 与 argument_ref 均非空的条目；
  * 未声明 innovation → PASS（opt-in）；
  * 创新是 Rank 线（R），本门禁只做契约合法性与证据义务检查，不评创新高低。

这些测试先于实现（RED）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import check_innovation_declaration  # noqa: E402


def _proj(tmp_path, innovation=None):
    proj = tmp_path / "projects" / "t"
    proj.mkdir(parents=True)
    mir = {"model_family": {"primary": "pde"}, "claims": []}
    if innovation is not None:
        mir["innovation"] = innovation
    (proj / "model_ir.json").write_text(
        json.dumps(mir, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_no_innovation_passes(tmp_path):
    """未声明 innovation → PASS（opt-in）。"""
    ok, msg = check_innovation_declaration(_proj(tmp_path))
    assert ok, msg


def test_zero_novelty_passes(tmp_path):
    """全零创新声明（忠实实例化）→ PASS。"""
    innov = {"structure_distance": 0.0,
             "dimensions": {"mechanism_novelty": 0.0, "solver_novelty": 0.0,
                            "composition_novelty": 0.0,
                            "representation_novelty": 0.0},
             "difference_arguments": []}
    ok, msg = check_innovation_declaration(_proj(tmp_path, innov))
    assert ok, msg


def test_novelty_without_arguments_fails(tmp_path):
    """维度 > 0 但缺 difference_arguments → FAIL。"""
    innov = {"structure_distance": 0.3,
             "dimensions": {"composition_novelty": 0.8},
             "difference_arguments": []}
    ok, msg = check_innovation_declaration(_proj(tmp_path, innov))
    assert not ok, msg
    assert "composition_novelty" in msg


def test_argument_for_other_dimension_fails(tmp_path):
    """维度 > 0 但 difference_arguments 指向别的维度 → FAIL。"""
    innov = {"structure_distance": 0.3,
             "dimensions": {"mechanism_novelty": 0.5},
             "difference_arguments": [{"dimension": "composition_novelty",
                                       "vs_known": "pde",
                                       "argument_ref": "model.md"}]}
    ok, msg = check_innovation_declaration(_proj(tmp_path, innov))
    assert not ok, msg
    assert "mechanism_novelty" in msg


def test_valid_novelty_passes(tmp_path):
    """维度 > 0 且有对应完整参数条目 → PASS。"""
    innov = {"structure_distance": 0.3,
             "dimensions": {"composition_novelty": 0.8},
             "difference_arguments": [{"dimension": "composition_novelty",
                                       "vs_known": "pde",
                                       "argument_ref": "model.md#sec3"}]}
    ok, msg = check_innovation_declaration(_proj(tmp_path, innov))
    assert ok, msg


def test_unknown_dimension_fails(tmp_path):
    """dimensions 键不在词表 → FAIL。"""
    innov = {"dimensions": {"magic_novelty": 0.5},
             "difference_arguments": []}
    ok, msg = check_innovation_declaration(_proj(tmp_path, innov))
    assert not ok, msg
    assert "magic_novelty" in msg


def test_out_of_range_value_fails(tmp_path):
    """维度值越界（1.5）→ FAIL。"""
    innov = {"dimensions": {"solver_novelty": 1.5},
             "difference_arguments": []}
    ok, msg = check_innovation_declaration(_proj(tmp_path, innov))
    assert not ok, msg


def test_bad_structure_distance_fails(tmp_path):
    """structure_distance 越界（-0.1）→ FAIL。"""
    innov = {"structure_distance": -0.1,
             "dimensions": {}, "difference_arguments": []}
    ok, msg = check_innovation_declaration(_proj(tmp_path, innov))
    assert not ok, msg
    assert "structure_distance" in msg
