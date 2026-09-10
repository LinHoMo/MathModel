# -*- coding: utf-8 -*-
"""参数来源门禁（check_parameter_provenance）语义测试。

背景：MODEL_IR 的参数 source 是自由字符串，此前无任何门禁校验
「声称 problem_given 的参数是否真的出自题面」。这堵住输入侧最经典的诚信漏洞：
把建模者自选的常数标成"题面给定"，使结论显得不可协商。

判据（机械可判）：
  * 每个 parameter 必须有 source，且取值在批准词表内；
  * source == "problem_given" 的数值参数，其值必须能在 inputs/problem.txt 原文中
    找到——仅允许 ×10^k 的单位换算（cm↔m 等）。若该值需经 ÷2 等推导得到，
    则它应标注为 derived 而非 problem_given。

这些测试先于实现（RED）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import check_parameter_provenance  # noqa: E402


def _make(tmp_path, params, problem_text):
    proj = tmp_path / "projects" / "t"
    (proj / "inputs").mkdir(parents=True)
    (proj / "inputs" / "problem.txt").write_text(problem_text, encoding="utf-8")
    (proj / "model_ir.json").write_text(
        json.dumps({"parameters": params}, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_problem_given_value_must_appear_in_problem(tmp_path):
    """声称题面给定、但题面里根本没有该值 → FAIL。"""
    root = _make(tmp_path,
                 [{"parameter_id": "P1", "name": "x", "value": 12345.0,
                   "source": "problem_given"}],
                 "本题半径 2 cm，速度 5 m/s。")
    ok, msg = check_parameter_provenance(root)
    assert not ok, msg
    assert "P1" in msg


def test_unit_scale_conversion_allowed(tmp_path):
    """题面以 cm 给出、参数以 m 记录（×10^k 单位换算）→ 通过。"""
    root = _make(tmp_path,
                 [{"parameter_id": "P1", "name": "R", "value": 0.02,
                   "source": "problem_given"}],
                 "圆柱半径 2 cm。")
    ok, msg = check_parameter_provenance(root)
    assert ok, msg


def test_derivation_not_problem_given(tmp_path):
    """题面给直径 9 m、参数用半径 4.5 m（需 ÷2 推导）→ 标 problem_given 应 FAIL。"""
    root = _make(tmp_path,
                 [{"parameter_id": "P1", "name": "R_t", "value": 4.5,
                   "source": "problem_given"}],
                 "调头空间为直径 9 m 的圆形区域。")
    ok, msg = check_parameter_provenance(root)
    assert not ok, "÷2 推导得到的值不应标为 problem_given"
    assert "P1" in msg


def test_unknown_source_rejected(tmp_path):
    """source 不在批准词表内 → FAIL。"""
    root = _make(tmp_path,
                 [{"parameter_id": "P1", "name": "x", "value": 1.0,
                   "source": "made_up_source"}],
                 "任意题面。")
    ok, msg = check_parameter_provenance(root)
    assert not ok, msg
    assert "made_up_source" in msg


def test_derived_not_value_checked(tmp_path):
    """derived 参数不做题面匹配（其值来自计算）→ 通过。"""
    root = _make(tmp_path,
                 [{"parameter_id": "P1", "name": "grid", "value": 1280,
                   "source": "derived"}],
                 "题面无 1280。")
    ok, msg = check_parameter_provenance(root)
    assert ok, msg
