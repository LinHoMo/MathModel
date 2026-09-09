# -*- coding: utf-8 -*-
"""audit FIX-5.2：数值验证从 MODEL_IR 动态派生（消除硬编码字段依赖）。

- derive_checks_from_mir：从 variables[].symbol / objectives 派生
  output_field_exists 检查
- _validation_spec 回退：无外部 spec 时派生兜底（不跳过验证）

运行: python -m pytest tests/unit/test_validation_derived.py -q
"""

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "core") not in sys.path:
    sys.path.insert(0, str(_REPO / "core"))

from runtime.execution.validation import (derive_checks_from_mir,  # noqa: E402
                                          run_numeric_validation)


def _mir() -> dict:
    return {
        "variables": [
            {"variable_id": "V001", "symbol": "x", "domain": [0, 100]},
            {"variable_id": "V002", "symbol": "y"},
        ],
        "objectives": [
            {"objective_id": "OBJ1", "target": "total_cost"},
        ],
        "constraints": [],
    }


def test_derive_checks_from_mir():
    checks = derive_checks_from_mir(_mir())
    kinds = [c["kind"] for c in checks]
    paths = [c["path"] for c in checks]
    assert kinds == ["output_field_exists"] * 3
    assert "x" in paths and "y" in paths and "total_cost" in paths


def test_derived_checks_pass_when_outputs_complete():
    checks = derive_checks_from_mir(_mir())
    spec = {"checks": checks}
    verdict = run_numeric_validation(
        {"x": 1.0, "y": 2.0, "total_cost": 3.0}, spec)
    assert verdict["status"] == "passed"
    assert verdict["mathematical_valid"] is True


def test_derived_checks_fail_when_variable_missing():
    checks = derive_checks_from_mir(_mir())
    spec = {"checks": checks}
    verdict = run_numeric_validation({"x": 1.0}, spec)
    assert verdict["status"] == "failed"
    missing = [c for c in verdict["checks"]
               if not c.get("passed") and c["kind"] == "output_field_exists"]
    assert missing, "缺失变量必须被检出"
    assert any("y" in c["name"] for c in missing)


def test_validation_spec_does_not_auto_derive(tmp_path):
    """无外部 validation_spec → _validation_spec 返回 None（不自动派生）。

    诚实语义：无验证规格 = 不做数值验证。derive_checks_from_mir 是外部
    构造方显式调用的工具，绝不自动回退注入（防止"无 spec 也假装验证"）。
    """
    from conftest import injected_session
    s = injected_session(tmp_path, questions=("Q001",))
    s.executor_impl.shared.pop("validation_specs", None)
    spec = s.executor_impl._validation_spec("Q001")
    assert spec is None
