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
    canonicalize_token, family_similarity, continuous_structure_distance,
    build_ontology, AUDIT_TOLERANCE,
)

# 合成词表（零依赖注入，不读 yaml）：pde 与 ode 共享部分机制，opt 独立
_FAMS = [
    {"id": "numerical_pde", "aliases": ["pde", "finite_difference"],
     "mechanism": ["conservation_law", "spatial_temporal_field",
                   "diffusion", "boundary_condition"],
     "methods": ["finite_difference_method", "method_of_lines"],
     "solvers": ["fdm_solver"]},
    {"id": "ode_models", "aliases": ["ode"],
     "mechanism": ["state_transition", "continuous_dynamics",
                   "conservation_law"],
     "methods": ["rk4", "euler"], "solvers": ["solve_ivp"]},
    {"id": "optimization", "aliases": ["numerical_optimization"],
     "mechanism": ["objective_extremum"],
     "methods": ["gradient_descent"], "solvers": ["scipy_optimize"]},
]


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


# ---- §9.3 深化：连续结构距离 + 本体图相似度 + 声明审计 ----

def _onto():
    return build_ontology(_FAMS)


def test_canonicalize_resolves_alias():
    """别名 pde 解析到 canonical family numerical_pde。"""
    _, resolve = _onto()
    assert canonicalize_token("pde", resolve) == "numerical_pde"
    assert canonicalize_token("unknown_x", resolve) == "unknown_x"


def test_family_similarity_self_is_one():
    """同族相似度=1。"""
    graph, _ = _onto()
    assert family_similarity("numerical_pde", "numerical_pde", graph) == 1.0


def test_family_similarity_neighbor_decays():
    """pde 与 ode 共享 conservation_law ⇒ 一跳相似度=0.5。"""
    graph, _ = _onto()
    assert family_similarity("numerical_pde", "ode_models", graph) == 0.5


def test_continuous_known_structure_is_zero():
    """模型结构在 allowed 内 ⇒ 连续距离=0（与「结构距离=0」一致）。"""
    graph, resolver = _onto()
    cd = continuous_structure_distance(
        {"primary": "pde"}, ["pde", "heat_transfer"], resolver, graph)
    assert cd == 0.0


def test_continuous_neighbor_partial_distance():
    """模型=ode（近邻），allowed=数值PDE ⇒ d=1−0.5=0.5（连续而非二值）。"""
    graph, resolver = _onto()
    cd = continuous_structure_distance(
        {"primary": "ode"}, ["pde"], resolver, graph)
    assert cd == 0.5


def test_continuous_novel_family_far():
    """模型结构不在图中 ⇒ 视为最远（1.0）。"""
    graph, resolver = _onto()
    cd = continuous_structure_distance(
        {"primary": "graph_neural_network"}, ["pde"], resolver, graph)
    assert cd == 1.0


def test_audit_overclaimed_innovation_warns():
    """声明 0.42 但模型实为已知结构（computed=0）⇒ WARN_mismatch。"""
    report = {"structure_distance": 0.42}
    assert _compute_audit_value(report, 0.0) == "WARN_mismatch"


def test_audit_consistent_ok():
    """声明值与机械值一致（偏差≤阈值）⇒ ok。"""
    assert _compute_audit_value({"structure_distance": 0.0}, 0.05) == "ok"
    assert _compute_audit_value({"structure_distance": 0.1}, 0.1) == "ok"


def test_audit_no_declaration():
    """未声明 ⇒ no_declaration（不误报）。"""
    assert _compute_audit_value({}, 0.0) == "no_declaration"


def _compute_audit_value(innov, computed):
    # 复用 innovation_metrics 内部审计逻辑（避免重复实现）
    from modeling_harness.cli.innovation_metrics import _compute_audit
    return _compute_audit(innov.get("structure_distance"), computed)


def test_report_includes_computed_and_audit(tmp_path):
    """报告含 computed_structure_distance 与 audit 字段。"""
    innov = {"structure_distance": 0.0,
             "dimensions": {"composition_novelty": 0.3},
             "difference_arguments": [{"dimension": "composition_novelty",
                                       "vs_known": "pde", "argument_ref": "m.md"}]}
    root = _proj(tmp_path, "pde", ["pde"], innovation=innov)
    rep = innovation_report(root)
    entry = rep["per_project"]["t"]
    assert "computed_structure_distance" in entry
    assert entry["audit"] in ("ok", "no_declaration", "WARN_mismatch")
    assert entry["computed_structure_distance"] == 0.0  # pde∈allowed
