# -*- coding: utf-8 -*-
"""G3 校准参数门禁（check_calibration_parameters）语义测试。

判据来源：docs/architecture/MODEL_QUALITY_CRITERIA.md §2.1.1（FROZEN v1.0）。

规则：
  * source ∈ {problem_given, derived, convention} → 豁免；
  * 否则（assumption_derived / reasoning / calibration / estimated …）必须同时满足：
    (a) p.calibration_anchor_ref 指向一个 type=="calibration_anchor" 的假设；
    (b) all_results.json 顶层 calibration_sensitivity[pid] 存在，且 varied 至少一轴长度≥2、
        outcomes 与该轴等长。

这些测试先于实现（RED）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import check_calibration_parameters  # noqa: E402

ANCHOR = {"assumption_id": "A04", "type": "calibration_anchor", "text": "目标温度标定"}


def _proj(tmp_path, params, assumptions, results):
    proj = tmp_path / "projects" / "t"
    (proj / "inputs").mkdir(parents=True)
    (proj / "inputs" / "problem.txt").write_text("题面", encoding="utf-8")
    (proj / "model_ir.json").write_text(
        json.dumps({"parameters": params, "assumptions": assumptions},
                   ensure_ascii=False), encoding="utf-8")
    (proj / "all_results.json").write_text(
        json.dumps(results, ensure_ascii=False), encoding="utf-8")
    return tmp_path


CAL_PARAM = {"parameter_id": "P08", "name": "目标温度", "value": 50.0,
             "source": "assumption_derived", "calibration_anchor_ref": "A04"}


def test_missing_anchor_ref_fails(tmp_path):
    """非豁免参数缺 calibration_anchor_ref → FAIL。"""
    p = dict(CAL_PARAM)
    p.pop("calibration_anchor_ref")
    root = _proj(tmp_path, [p], [ANCHOR], {})
    ok, msg = check_calibration_parameters(root)
    assert not ok, msg
    assert "P08" in msg


def test_ref_not_calibration_anchor_fails(tmp_path):
    """calibration_anchor_ref 指向非 calibration_anchor 假设 → FAIL。"""
    asm = {"assumption_id": "A04", "type": "simplification", "text": "x"}
    root = _proj(tmp_path, [CAL_PARAM], [asm], {})
    ok, msg = check_calibration_parameters(root)
    assert not ok, msg
    assert "P08" in msg


def test_missing_sensitivity_fails(tmp_path):
    """锚定合法但 all_results.json 无 calibration_sensitivity[pid] → FAIL。"""
    root = _proj(tmp_path, [CAL_PARAM], [ANCHOR], {})
    ok, msg = check_calibration_parameters(root)
    assert not ok, msg
    assert "P08" in msg


def test_sensitivity_no_variation_fails(tmp_path):
    """calibration_sensitivity 的 varied 各轴长度均 <2 → FAIL。"""
    res = {"calibration_sensitivity": {"P08": {
        "symbol": "T_target", "nominal": 50.0,
        "varied": {"T_target_C": [50.0]}, "outcomes": [58.1]}}}
    root = _proj(tmp_path, [CAL_PARAM], [ANCHOR], res)
    ok, msg = check_calibration_parameters(root)
    assert not ok, msg
    assert "P08" in msg


def test_full_compliance_passes(tmp_path):
    """(a)(b) 全满足 → PASS。"""
    res = {"calibration_sensitivity": {"P08": {
        "symbol": "T_target", "nominal": 50.0,
        "varied": {"T_target_C": [45.0, 50.0, 55.0, 60.0]},
        "outcomes": [69.22, 58.10, 49.39, 42.48]}}}
    root = _proj(tmp_path, [CAL_PARAM], [ANCHOR], res)
    ok, msg = check_calibration_parameters(root)
    assert ok, msg


def test_exempt_sources_skip(tmp_path):
    """problem_given / derived / convention → 豁免，不做 (a)(b) 检查。"""
    params = [
        {"parameter_id": "P1", "value": 1.0, "source": "problem_given"},
        {"parameter_id": "P2", "value": 2.0, "source": "derived"},
        {"parameter_id": "P3", "value": 42, "source": "convention"},
    ]
    root = _proj(tmp_path, params, [], {})
    ok, msg = check_calibration_parameters(root)
    assert ok, msg
