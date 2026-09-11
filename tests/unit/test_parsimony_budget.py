# -*- coding: utf-8 -*-
"""G5 复杂度预算门禁（check_parsimony_budget）语义测试。

判据来源：docs/architecture/MODEL_QUALITY_CRITERIA.md §2.3（G5，v1.1）。

规则（「参数付租」）：
  * model_ir.json 每个 parameter 必须至少在一处**使用语料**中被引用，
    否则视为死参数（dead parameter）→ FAIL；
  * 使用语料 = model_ir.json（剔除 parameters 数组自身，避免自证）+ all_results.json
    + artifacts/code/*.py + 项目根 *.md 模型描述文档；
  * 引用信号（任一命中即算使用）：parameter_id / symbol / 归一化符号
    （剥离 Unicode 上下标并转大写）/ 参数名 / 数值字符串；
  * 报告复杂度指标（参数/方程/机制计数）为 Rank 数据，不阻塞。

这些测试先于实现（RED）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import check_parsimony_budget  # noqa: E402


def _proj(tmp_path, params, code_text=None, mir_extra=None, md_text=None):
    proj = tmp_path / "projects" / "t"
    (proj / "artifacts" / "code").mkdir(parents=True)
    mir = {"model_family": "t",
           "parameters": params,
           "equations": [{"equation_id": "E01", "latex": "T(r,t)=R₀*exp(-t/tau)"}],
           "claims": []}
    if mir_extra:
        mir.update(mir_extra)
    (proj / "model_ir.json").write_text(
        json.dumps(mir, ensure_ascii=False), encoding="utf-8")
    (proj / "all_results.json").write_text(
        json.dumps({"summary": {}}, ensure_ascii=False), encoding="utf-8")
    if code_text is not None:
        (proj / "artifacts" / "code" / "solve.py").write_text(
            code_text, encoding="utf-8")
    if md_text is not None:
        (proj / "model.md").write_text(md_text, encoding="utf-8")
    return tmp_path


P_USED = {"parameter_id": "P01", "name": "初始半径", "symbol": "R₀",
          "value": 0.02, "unit": "m", "source": "problem_given"}
P_DEAD = {"parameter_id": "P99", "name": "幽灵参数", "symbol": "G_ghost",
          "value": 42.0, "unit": "-", "source": "convention"}


def test_all_params_used_passes(tmp_path):
    """参数经 symbol（方程 latex）被引用 → PASS，并报告复杂度指标。"""
    ok, msg = check_parsimony_budget(_proj(tmp_path, [P_USED]))
    assert ok, msg
    assert "复杂度" in msg


def test_dead_parameter_fails(tmp_path):
    """参数在任何语料中均无引用（id/符号/名称/数值）→ FAIL 并点名。"""
    ok, msg = check_parsimony_budget(_proj(tmp_path, [P_DEAD]))
    assert not ok, msg
    assert "P99" in msg


def test_used_via_code_passes(tmp_path):
    """参数仅出现在代码中（归一化符号）→ PASS（付租渠道含代码）。"""
    code = "T0 = 28.0  # 初始温度\nSEED = 42\nTAU_AIR = 450.0\n"
    params = [
        {"parameter_id": "P03", "name": "初始温度", "symbol": "T₀",
         "value": 28.0, "source": "problem_given"},
        {"parameter_id": "P11", "name": "随机种子", "symbol": "seed",
         "value": 42, "source": "convention"},
        {"parameter_id": "P12", "name": "时间常数", "symbol": "τ_air",
         "value": 450.0, "source": "calibration"},
    ]
    ok, msg = check_parsimony_budget(_proj(tmp_path, params, code_text=code))
    assert ok, msg


def test_used_via_model_doc_passes(tmp_path):
    """参数仅出现在模型描述文档中（名称）→ PASS。"""
    md = "烘干含水率阈值取 0.15 kg/kg。"
    params = [{"parameter_id": "P07", "name": "烘干含水率阈值",
               "symbol": "C_th", "value": 0.15, "source": "problem_given"}]
    ok, msg = check_parsimony_budget(_proj(tmp_path, params, md_text=md))
    assert ok, msg


def test_no_parameters_passes(tmp_path):
    """无参数 → PASS（空集无死参数）。"""
    ok, msg = check_parsimony_budget(_proj(tmp_path, []))
    assert ok, msg


def test_mixed_dead_and_live_reports_only_dead(tmp_path):
    """混合：活参数 + 死参数 → FAIL 且只点名死参数。"""
    params = [P_USED, P_DEAD]
    ok, msg = check_parsimony_budget(_proj(tmp_path, params))
    assert not ok, msg
    assert "P99" in msg
    assert "P01" not in msg


def test_string_value_with_float_code_passes(tmp_path):
    """字符串值（"450, 1350"）以浮点格式（"450.0"）出现在代码 → PASS。

    回归：2026b P13/P14 曾因此漏检为死参数（值字符串 + 代码 .0 格式）。
    """
    code = "COVER_RADII_DIR = (450.0, 1350.0, 1200.0, 1799.0)\n"
    params = [
        {"parameter_id": "P13", "name": "覆盖环半径", "symbol": "ρ_ring",
         "value": "450, 1350", "source": "derived"},
        {"parameter_id": "P14", "name": "覆盖环半径含定向", "symbol": "ρ_ring,dir",
         "value": "450, 1350, 1200, 1799", "source": "derived"},
    ]
    ok, msg = check_parsimony_budget(_proj(tmp_path, params, code_text=code))
    assert ok, msg


def test_int_value_with_float_code_passes(tmp_path):
    """整数值（450）以浮点格式（"450.0"）出现在代码 → PASS（int↔float 互化）。"""
    code = "R = 450.0  # m\n"
    params = [{"parameter_id": "P20", "name": "半径", "symbol": "R",
               "value": 450, "source": "problem_given"}]
    ok, msg = check_parsimony_budget(_proj(tmp_path, params, code_text=code))
    assert ok, msg


def test_separator_variant_symbol_passes(tmp_path):
    """符号分隔符变体（τ-air）归一化后命中代码（TAU_AIR）→ PASS。"""
    code = "TAU_AIR = 450.0\n"
    params = [{"parameter_id": "P21", "name": "时间常数", "symbol": "τ-air",
               "value": 450.0, "source": "calibration"}]
    ok, msg = check_parsimony_budget(_proj(tmp_path, params, code_text=code))
    assert ok, msg
