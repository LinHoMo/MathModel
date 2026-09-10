# -*- coding: utf-8 -*-
"""audit FIX-5.3：L2 Mathematical 真实接线。

formula_checker（括号配对 / LaTeX 语法 / 常见错误）接入 MODEL_IR 校验：
- 合法 LaTeX 表达式通过
- 未闭合花括号 / 不平衡括号被检出
- 纯文本表达式不受影响（无 $ 包裹 = 无公式可查，不误报）
- 骨架 MIR 跳过 L2（无公式可查）

运行: python -m pytest tests/unit/test_mathematical_validation.py -q
"""

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from modeling_harness.runtime.modeling.model_ir import (MODEL_IR_REQUIRED_FIELDS,  # noqa: E402
                                       _check_l2_mathematical,
                                       _is_skeleton,
                                       validate_model_ir)


def _base_mir() -> dict:
    return {f: ([] if f not in ("ir_version", "model_id", "model_family",
                                "problem_binding", "modeling_trace")
                else None) for f in MODEL_IR_REQUIRED_FIELDS}


def _full_mir() -> dict:
    mir = _base_mir()
    mir.update({
        "ir_version": "1.0",
        "model_family": {"primary": "test_family"},
        "problem_binding": {"problem_id": "Q001",
                            "problem_sha256": "0" * 64},
        "assumptions": [{"assumption_id": "A1"}],
        "variables": [{"variable_id": "V1"}],
        "parameters": [{"parameter_id": "P1"}],
        "objectives": [{"objective_id": "O1",
                        "expression": r"$\min x + y$"}],
        "constraints": [{"constraint_id": "C1",
                         "expression": r"$x + y \geq 10$"}],
        "mechanisms": [{"mechanism_id": "M1"}],
        "equations": [{"equation_id": "E1",
                       "equation": r"$E = mc^2$"}],
        "dependencies": [{"dependency_id": "D1"}],
        "solvers": [{"solver_id": "S1"}],
        "experiments": [{"experiment_id": "X1"}],
        "validations": [{"validation_id": "VLD1"}],
        "claims": [{"claim_id": "CL1"}],
        "model_graph": {},
        "modeling_trace": [],
    })
    return mir


def test_valid_latex_passes():
    mir = _full_mir()
    assert _check_l2_mathematical(mir) == []


def test_unclosed_brace_detected():
    mir = _full_mir()
    mir["equations"][0]["equation"] = r"$\min_{x} f(x$"
    issues = _check_l2_mathematical(mir)
    assert issues, "未闭合花括号必须被检出"


def test_unbalanced_bracket_detected():
    mir = _full_mir()
    mir["constraints"][0]["expression"] = r"$(x + y \geq 10$"
    issues = _check_l2_mathematical(mir)
    assert issues, "不平衡括号必须被检出"


def test_plain_text_expression_not_false_positive():
    mir = _full_mir()
    mir["constraints"][0]["expression"] = "x + y >= 10"
    assert _check_l2_mathematical(mir) == []


def test_skeleton_skips_l2():
    mir = _full_mir()
    mir["modeling_trace"] = [{"note": "pending_model_spec: no model spec"}]
    assert _is_skeleton(mir)
    assert _check_l2_mathematical(mir) == []


def test_validate_model_ir_wires_l2():
    mir = _full_mir()
    assert validate_model_ir(mir) == []
    mir["equations"][0]["equation"] = r"$\min_{x} f(x$"
    problems = validate_model_ir(mir)
    assert any("equation[E1].equation" in p for p in problems), problems
