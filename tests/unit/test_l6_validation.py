# -*- coding: utf-8 -*-
"""P2-1 验收：L6 数值正确性机械判定层（ground-truth 断言）。

ROADMAP P2-1：
  * 正确数值 → PASS（l6_score=1.0）
  * 错误数值 → FAIL（l6_score<1.0，来自真实数值不编造）
  * 无 GT 断言 → unverifiable（l6_score=None，不编造分数）
  * fidelity 升级：F6 约束数值满足（带显式 check 断言时判定）、
    F7 目标值有限（输出 NaN/Inf → fail）
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.validation import validate_against_gt  # noqa: E402
from runtime.execution.fidelity import fidelity_checks_from_ir  # noqa: E402
from runtime.execution.validation import run_checks  # noqa: E402


def _ok_exec(outputs, **extra):
    d = {"status": "success", "outputs": outputs}
    d.update(extra)
    return d


GT = {
    "version": "1.0",
    "checks": [
        {"name": "feasibility", "kind": "constraint_violation_max",
         "op": "<=", "value": 0, "source": "mathematical_necessity"},
        {"name": "objective_finite", "kind": "objective_sane",
         "source": "mathematical_necessity"},
        {"name": "outputs_nonnegative", "kind": "output_nonnegative",
         "source": "problem_statement"},
    ],
}


class TestValidateAgainstGt:
    def test_correct_values_pass(self):
        r = validate_against_gt(
            _ok_exec({"cost": 12.5, "demand": 30},
                     constraint_violation_max=0.0,
                     objective_value=12.5, objective_sane=True),
            GT)
        assert r["status"] == "passed"
        assert r["l6_score"] == 1.0

    def test_constraint_violation_fails(self):
        r = validate_against_gt(
            _ok_exec({"cost": 12.5},
                     constraint_violation_max=4.2,
                     objective_value=12.5, objective_sane=True),
            GT)
        assert r["status"] == "failed"
        assert r["l6_score"] < 1.0
        bad = [c for c in r["checks"] if not c["passed"]]
        assert any(c["name"] == "feasibility" for c in bad)

    def test_nan_output_fails_objective_finite(self):
        r = validate_against_gt(
            _ok_exec({"cost": float("nan")},
                     constraint_violation_max=0.0,
                     objective_value=float("nan"), objective_sane=False),
            GT)
        assert r["status"] == "failed"
        bad = [c for c in r["checks"] if not c["passed"]]
        assert any(c["name"] == "objective_finite" for c in bad)

    def test_missing_objective_is_skipped_not_failed(self):
        """模型无标量目标输出：objective 断言不可判定（skipped），
        不误伤无目标输出的合法模型；其余断言仍判定。"""
        r = validate_against_gt(
            _ok_exec({"x": 2.0, "demand": 30},
                     constraint_violation_max=0.0,
                     objective_value=None, objective_sane=False),
            GT)
        assert r["status"] == "passed"  # feasibility + nonnegative 过，objective skipped
        assert r["skipped"] == 1
        obj = [c for c in r["checks"] if c["name"] == "objective_finite"][0]
        assert obj.get("skipped") is True

    def test_negative_output_fails_nonnegative(self):
        r = validate_against_gt(
            _ok_exec({"profit": -1.5, "x": 2.0},
                     constraint_violation_max=0.0,
                     objective_value=2.0, objective_sane=True),
            GT)
        assert r["status"] == "failed"
        bad = [c for c in r["checks"] if not c["passed"]]
        assert any(c["name"] == "outputs_nonnegative" for c in bad)

    def test_no_assertions_is_unverifiable(self):
        r = validate_against_gt(_ok_exec({"x": 1}), None)
        assert r["status"] == "unverifiable"
        assert r["l6_score"] is None

    def test_non_success_execution_is_invalid(self):
        r = validate_against_gt(
            {"status": "failed", "outputs": {}}, GT)
        assert r["status"] == "invalid"
        assert r["l6_score"] is None


class TestFidelityNumericUpgrade:
    """P2-1 fidelity 退化修复：F6 约束数值满足 + F7 目标值有限。"""

    def _ir(self):
        return {
            "variables": [{"variable_id": "x", "name": "x", "symbol": "x"}],
            "objectives": [{"objective_id": "o1", "name": "min_cost",
                            "expression": "sum(x)"}],
            "constraints": [
                {"constraint_id": "c1", "name": "x_leq_10",
                 "expression": "x <= 10",
                 "check": {"path": "x", "op": "<=", "value": 10}},
            ],
        }

    def test_f6_constraint_satisfaction_violated(self):
        checks = fidelity_checks_from_ir(self._ir())
        f6 = [c for c in checks if c["kind"] == "constraint_satisfaction"]
        assert f6
        status, results = run_checks(
            {"status": "success", "outputs": {"x": 12.0}}, f6)
        assert status == "failed"
        assert any(not r["passed"] for r in results)

    def test_f6_constraint_satisfaction_ok(self):
        checks = fidelity_checks_from_ir(self._ir())
        f6 = [c for c in checks if c["kind"] == "constraint_satisfaction"]
        status, results = run_checks(
            {"status": "success", "outputs": {"x": 3.0}}, f6)
        assert status == "passed"

    def test_f6_no_explicit_check_skips_without_judging(self):
        ir = self._ir()
        ir["constraints"] = [{"constraint_id": "c1",
                              "expression": "fancy(x) <= 10"}]
        checks = fidelity_checks_from_ir(ir)
        f6 = [c for c in checks if c["kind"] == "constraint_satisfaction"]
        status, results = run_checks(
            {"status": "success", "outputs": {"x": 3.0}}, f6)
        # 无可机械判定项 → 不误判（pass 语义 = 跳过），F1 负责键存在
        assert status == "passed"

    def test_f7_objective_finite_nan_fails(self):
        ir = self._ir()
        checks = fidelity_checks_from_ir(ir)
        f7 = [c for c in checks if c["kind"] == "objective_finite"]
        assert f7
        status, results = run_checks(
            {"status": "success", "outputs": {"x": float("nan")}}, f7)
        assert status == "failed"

    def test_f7_objective_finite_all_finite_passes(self):
        ir = self._ir()
        checks = fidelity_checks_from_ir(ir)
        f7 = [c for c in checks if c["kind"] == "objective_finite"]
        status, results = run_checks(
            {"status": "success", "outputs": {"x": 5.0}}, f7)
        assert status == "passed"
