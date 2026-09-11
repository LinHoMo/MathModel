# -*- coding: utf-8 -*-
"""R3 结构距离度量工具（innovation_metrics.py）语义测试。

判据来源：docs/architecture/MODEL_QUALITY_CRITERIA.md §3（R3，v1.1）。

规则（Rank 工具，只读、不阻塞）：
  * 实例声明 `innovation.structure_distance` → 直接采用声明值；
  * 未声明 → 一阶二值距离：model_family.primary ∈ 题面
    allowed_modeling_structures → 0，否则 1（v1 二值，本体图深化后升级）；
  * 报告创新维度声明与 difference_arguments 数量；
  * 缺 model_ir / 无活跃实例 → 空报告，不崩溃。

这些测试先于实现（RED）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.innovation_metrics import (  # noqa: E402
    binary_structure_distance, innovation_report,
)


def _proj(tmp_path, family, allowed, innovation=None):
    proj = tmp_path / "projects" / "t"
    proj.mkdir(parents=True)
    mir = {"model_family": {"primary": family},
           "problem_binding": {"allowed_modeling_structures": allowed},
           "claims": []}
    if innovation is not None:
        mir["innovation"] = innovation
    (proj / "model_ir.json").write_text(
        json.dumps(mir, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_binary_distance_zero_when_allowed():
    """family 在 allowed 内 → 距离 0。"""
    assert binary_structure_distance("pde", ["pde", "heat_transfer"]) == 0.0


def test_binary_distance_one_when_not_allowed():
    """family 不在 allowed 内 → 距离 1（v1 二值）。"""
    assert binary_structure_distance("pde", ["kinematics"]) == 1.0


def test_binary_distance_missing_allowed_is_one():
    """allowed 缺失 → 视为不可算/不同 → 1。"""
    assert binary_structure_distance("pde", []) == 1.0


def test_report_uses_declared_distance(tmp_path):
    """声明了 structure_distance → 报告采用声明值。"""
    innov = {"structure_distance": 0.42,
             "dimensions": {"composition_novelty": 0.8},
             "difference_arguments": [{"dimension": "composition_novelty",
                                       "vs_known": "pde", "argument_ref": "m.md"}]}
    root = _proj(tmp_path, "pde", ["pde"], innovation=innov)
    rep = innovation_report(root)
    assert rep["total"] == 1
    entry = rep["per_project"]["t"]
    assert entry["structure_distance"] == 0.42
    assert entry["declared"] is True
    assert entry["arguments"] == 1


def test_report_computes_binary_when_undeclared(tmp_path):
    """未声明 → 用一阶二值距离计算。"""
    root = _proj(tmp_path, "pde", ["pde"])
    rep = innovation_report(root)
    entry = rep["per_project"]["t"]
    assert entry["structure_distance"] == 0.0
    assert entry["declared"] is False
