"""P0-E6 Model-to-Execution Fidelity 测试。

核心：execution success=1 但 fidelity<1 完全可能（声明模型 ≠ 代码跑的）。
fidelity 是确定性结构映射（LLM-free），K002 的 model_fidelity 终点以此为准。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from runtime.execution.fidelity import (  # noqa: E402
    check_fidelity, fidelity_checks_from_ir, verify_fidelity,
)
from runtime.execution.session import RuntimeSession  # noqa: E402


def _make_exec(tmp_path, code, qid="Q001"):
    s = RuntimeSession(tmp_path / "proj", [qid], max_workers=1,
                       execution_adapter=LocalPythonAdapter())
    for q in s.questions:
        s.executor_impl.shared.setdefault(q, {})["plan"] = {"code": code}
    s.run()
    execs = s.registry.list_by_type("execution_result")
    assert len(execs) == 1
    return s, execs[0]


def _ir(variables, objectives=None, constraints=None, equations=None):
    return {
        "ir_version": "1.0", "model_id": "M001",
        "model_family": {"primary": "test"},
        "problem_binding": {"problem_id": "T001", "question_id": "Q001"},
        "variables": variables,
        "objectives": objectives or [],
        "constraints": constraints or [],
        "equations": equations or [],
        "mechanisms": [], "claims": [],
    }


VAR_COST = [{"variable_id": "v1", "name": "total_cost", "symbol": "TC",
             "definition": "总成本", "unit": "元", "type": "continuous",
             "sub_question_binding": ["Q1"]}]
OBJ_COST = [{"objective_id": "o1", "type": "minimize",
             "expression": "total_cost", "variables_refs": ["v1"],
             "sub_question_binding": ["Q1"], "clarity_score": {}}]


class TestFidelityChecks:
    def test_checks_generated_from_ir(self):
        checks = fidelity_checks_from_ir(_ir(VAR_COST, OBJ_COST))
        kinds = [c["kind"] for c in checks]
        assert "output_key_exists" in kinds
        assert any(c["kind"] == "output_key_exists" and c["name"].startswith("F2")
                   for c in checks)

    def test_aligned_when_outputs_match_declarations(self):
        out = check_fidelity(
            _ir(VAR_COST, OBJ_COST),
            {"status": "success", "outputs": {"total_cost": 42.0}})
        assert out["status"] == "aligned"
        assert out["fidelity_score"] == 1.0

    def test_misaligned_when_declared_variable_missing(self):
        # execution success，但代码没算声明的变量 → success=1, fidelity<1
        out = check_fidelity(
            _ir(VAR_COST, OBJ_COST),
            {"status": "success", "outputs": {"other_metric": 1.0}})
        assert out["status"] == "misaligned"
        assert out["fidelity_score"] < 1.0
        # 可归因：F1 检查指出缺失
        f1 = [c for c in out["checks"] if c["name"].startswith("F1")]
        assert f1 and f1[0]["passed"] is False
        assert "缺失声明" in f1[0]["detail"]

    def test_symbol_alias_resolution(self):
        # 输出用 symbol 而非 name 也可解析
        out = check_fidelity(
            _ir(VAR_COST),
            {"status": "success", "outputs": {"TC": 42.0}})
        assert out["status"] == "aligned"

    def test_range_violation_detected(self):
        v = dict(VAR_COST[0], value_range={"min": 0, "max": 100})
        out = check_fidelity(
            _ir([v]),
            {"status": "success", "outputs": {"total_cost": 150.0}})
        assert out["status"] == "misaligned"
        f5 = [c for c in out["checks"] if c["name"].startswith("F5")]
        assert f5 and f5[0]["passed"] is False

    def test_failed_execution_unverifiable(self):
        out = check_fidelity(_ir(VAR_COST),
                             {"status": "failed", "outputs": {}})
        assert out["status"] == "unverifiable"

    def test_no_declarations_unverifiable(self):
        out = check_fidelity(_ir([]), {"status": "success", "outputs": {"x": 1}})
        assert out["status"] == "unverifiable"
        assert out["reason"] == "no_declarations"


class TestVerifyFidelity:
    def test_end_to_end_registers_vr_and_report(self, tmp_path):
        s, x = _make_exec(tmp_path,
                          "import json; print(json.dumps({'total_cost': 42.0}))")
        out = verify_fidelity(s.project_dir, _ir(VAR_COST, OBJ_COST),
                              x.artifact_id)
        assert out["fidelity_status"] == "aligned"
        assert out["verification_id"].startswith("VR")
        rep = Path(out["report_path"])
        assert rep.exists()
        data = __import__("json").loads(rep.read_text(encoding="utf-8"))
        assert data["fidelity_score"] == 1.0
        assert data["execution_id"] == x.artifact_id

    def test_misaligned_report_kept(self, tmp_path):
        # 代码跑通但缺声明变量：success=1, fidelity<1，报告如实记录
        s, x = _make_exec(tmp_path,
                          "import json; print(json.dumps({'other': 1}))")
        out = verify_fidelity(s.project_dir, _ir(VAR_COST), x.artifact_id)
        assert out["fidelity_status"] == "misaligned"
        assert out["fidelity_score"] < 1.0
        rep = Path(out["report_path"])
        assert rep.exists()
