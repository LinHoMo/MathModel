# -*- coding: utf-8 -*-
"""结构解析与覆盖率度量（catalog.model_families 受控词表的消费者）。

背景（能力层缺口，见 docs/PROJECTS_FEEDBACK_AUDIT.md §4）：
  「基准的允许结构词表（几何建模 / 微分方程 / 优化 / 仿真）与方法卡家族词表无交集」——
  2026 A/B 题使用的结构名大量解析不到 canonical family，导致"方法结构对齐"指标不可用。

本模块提供确定性解析与覆盖率度量，把该缺口从散文变成可测数字；不改冻结词表本身。

解析规则（对齐 model_families.yaml 头部治理声明）：
  族命中 = primary OR secondary OR mechanism OR solver 任一落在本表；
  未命中 → "out_of_catalog"（不自动判错）。
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.structure_coverage import (  # noqa: E402
    build_index, resolve_structure, coverage_report,
)


def _fixture_families():
    """最小 canonical_families 夹具（pi 与真实结构无关的测试用）。"""
    return [
        {"id": "numerical_pde",
         "aliases": ["pde", "heat_transfer", "finite_difference"],
         "mechanism": ["diffusion", "conservation_law"],
         "methods": ["finite_volume_method"], "solvers": ["fdm_solver"]},
        {"id": "simulation",
         "aliases": ["monte_carlo", "discrete_event_simulation"],
         "mechanism": ["random_sampling"], "methods": ["monte_carlo"], "solvers": []},
    ]


def test_resolve_by_id_and_alias():
    idx = build_index(_fixture_families())
    assert resolve_structure("numerical_pde", idx) == "numerical_pde"
    assert resolve_structure("pde", idx) == "numerical_pde"        # alias
    assert resolve_structure("heat_transfer", idx) == "numerical_pde"
    assert resolve_structure("discrete_event_simulation", idx) == "simulation"


def test_resolve_by_mechanism_and_solver():
    idx = build_index(_fixture_families())
    assert resolve_structure("diffusion", idx) == "numerical_pde"       # mechanism
    assert resolve_structure("fdm_solver", idx) == "numerical_pde"      # solver
    assert resolve_structure("finite_volume_method", idx) == "numerical_pde"  # method


def test_unresolved_is_out_of_catalog():
    idx = build_index(_fixture_families())
    assert resolve_structure("mass_transfer", idx) == "out_of_catalog"
    assert resolve_structure("coverage_path_planning", idx) == "out_of_catalog"


def test_coverage_report_counts_and_lists(tmp_path):
    proj = tmp_path / "projects" / "t"
    proj.mkdir(parents=True)
    (proj / "model_ir.json").write_text(
        '{"allowed_modeling_structures": ["pde", "mass_transfer", "monte_carlo"]}',
        encoding="utf-8")
    rep = coverage_report(tmp_path, _fixture_families())
    assert rep["total"] == 3
    assert rep["resolved"] == 2
    assert abs(rep["ratio"] - 2 / 3) < 1e-9
    assert rep["out_of_catalog"] == [("t", "mass_transfer")]


def test_real_catalog_loads():
    """真实 model_families.yaml 可加载且至少含 numerical_pde。"""
    idx = build_index()
    assert resolve_structure("numerical_pde", idx) == "numerical_pde"
    assert resolve_structure("pde", idx) == "numerical_pde"


def test_2026_structures_resolve_after_revision():
    """2026 A/B 题结构名在 2026-09-11 词表修订后全部可解析（覆盖率 19/19）。"""
    idx = build_index()
    for name in ["mass_transfer", "moving_boundary", "effective_property_correlation",
                 "computational_geometry", "convex_polygon_clipping",
                 "diameter_and_min_enclosing_circle", "geometric_dilution_of_precision",
                 "coverage_path_planning", "greedy_nearest_neighbor"]:
        assert resolve_structure(name, idx) != "out_of_catalog", name
