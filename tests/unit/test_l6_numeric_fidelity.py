"""P2-1 L6 数值正确性：F6 约束数值满足 + F7 目标值有限（fidelity 升级）。

fidelity_checks_from_ir 必须产出：
- F6 constraint_satisfaction（仅对带显式 check={path,op,value} 的约束）
- F7 objective_finite（每个目标一条，NaN/Inf → fail）
run_checks 按真实数值判定，非结构占位。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.execution.fidelity import fidelity_checks_from_ir
from modeling_harness.runtime.execution.validation import run_checks


def _ir():
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


def test_f6_check_generated_only_for_explicit_assertions():
    checks = fidelity_checks_from_ir(_ir())
    f6 = [c for c in checks if c["kind"] == "constraint_satisfaction"]
    assert len(f6) == 1
    assert f6[0]["constraints"][0]["constraint_id"] == "c1"
    # 无显式断言 → 不生成 F6（不强行机械解析复杂表达式）
    ir = _ir()
    ir["constraints"] = [{"constraint_id": "c1", "expression": "fancy(x) <= 10"}]
    assert not [c for c in fidelity_checks_from_ir(ir)
                if c["kind"] == "constraint_satisfaction"]


def test_f6_violated_fails():
    checks = [c for c in fidelity_checks_from_ir(_ir())
              if c["kind"] == "constraint_satisfaction"]
    status, results = run_checks({"status": "success", "outputs": {"x": 12.0}},
                                 checks)
    assert status == "failed"
    assert any(not r["passed"] for r in results)


def test_f6_satisfied_passes():
    checks = [c for c in fidelity_checks_from_ir(_ir())
              if c["kind"] == "constraint_satisfaction"]
    status, _ = run_checks({"status": "success", "outputs": {"x": 3.0}},
                           checks)
    assert status == "passed"


def test_f7_generated_per_objective():
    checks = fidelity_checks_from_ir(_ir())
    f7 = [c for c in checks if c["kind"] == "objective_finite"]
    assert len(f7) == 1


def test_f7_nan_fails():
    checks = [c for c in fidelity_checks_from_ir(_ir())
              if c["kind"] == "objective_finite"]
    status, results = run_checks(
        {"status": "success", "outputs": {"x": float("nan")}}, checks)
    assert status == "failed"
    assert any(not r["passed"] for r in results)


def test_f7_all_finite_passes():
    checks = [c for c in fidelity_checks_from_ir(_ir())
              if c["kind"] == "objective_finite"]
    status, _ = run_checks({"status": "success", "outputs": {"x": 5.0}},
                           checks)
    assert status == "passed"
