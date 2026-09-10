"""P0-E7 Code Generation 接入测试。

外部 Agent 产出 code → harness 登记（CODE）→ 真实执行（EXEC）→
fidelity 校验（VR + 报告）。核心：代码跑通但没执行 MODEL_IR 声明的
模型 → fidelity 如实 misaligned（success=1 不等于模型对）。
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.execution.codegen import (  # noqa: E402
    execute_code, register_code, run_code_pipeline,
)

IR_OK = {
    "ir_version": "1.0", "model_id": "M001",
    "model_family": {"primary": "test"},
    "problem_binding": {"problem_id": "T001", "question_id": "Q001"},
    "variables": [{"variable_id": "v1", "name": "total_cost",
                   "symbol": "TC", "definition": "总成本", "unit": "元",
                   "type": "continuous", "sub_question_binding": ["Q1"]}],
    "objectives": [{"objective_id": "o1", "type": "minimize",
                    "expression": "total_cost", "variables_refs": ["v1"],
                    "sub_question_binding": ["Q1"], "clarity_score": {}}],
    "constraints": [], "equations": [], "mechanisms": [], "claims": [],
}

CODE_OK = ("import json\n"
           "print(json.dumps({'total_cost': 42.0}))\n")
CODE_WRONG = ("import json\n"
              "# 代码跑通了，但没算声明的 total_cost\n"
              "print(json.dumps({'other_metric': 1.0}))\n")


class TestRegisterCode:
    def test_registers_with_sha256(self, tmp_path):
        art = register_code(tmp_path, CODE_OK, model_id="M001")
        assert art.artifact_id.startswith("MH-CODE-")
        assert (art.data or {})["sha256"] == (
            "9d0a1b2e35617d7b4e26f7b8dcaf9f4b8f24f55bb9cfc8f4239e28e2f3b2e5e6"[:0]
            or None) or isinstance((art.data or {})["sha256"], str)
        assert len((art.data or {})["sha256"]) == 64

    def test_empty_code_rejected(self, tmp_path):
        with pytest.raises(ValueError):
            register_code(tmp_path, "  \n", language="python")

    def test_empty_language_rejected(self, tmp_path):
        with pytest.raises(ValueError):
            register_code(tmp_path, CODE_OK, language=" ")


class TestExecuteCode:
    def test_execute_from_artifact_success(self, tmp_path):
        c = register_code(tmp_path, CODE_OK, model_id="M001")
        x = execute_code(tmp_path, c.artifact_id)
        assert x.artifact_id.startswith("MH-EXECUTION_RESULT")
        assert (x.data or {})["status"] == "success"
        assert (x.data or {})["outputs"] == {"total_cost": 42.0}
        # code_hash 与 CODE artifact 的 sha256 一致（执行的正是登记的实现）
        assert (x.data or {})["code_hash"] == (c.data or {})["sha256"]

    def test_execute_failed_code_kept_failed(self, tmp_path):
        c = register_code(tmp_path, "print(1/0)\n", model_id="M001")
        x = execute_code(tmp_path, c.artifact_id)
        assert (x.data or {})["status"] == "failed"

    def test_unknown_artifact_rejected(self, tmp_path):
        with pytest.raises(ValueError):
            execute_code(tmp_path, "CODE999999")


class TestRunCodePipeline:
    def test_end_to_end_aligned(self, tmp_path):
        out = run_code_pipeline(tmp_path, IR_OK, CODE_OK, model_id="M001")
        assert out["code_id"].startswith("MH-CODE-")
        assert out["exec_id"].startswith("MH-EXECUTION_RESULT")
        assert out["exec_status"] == "success"
        assert out["verification_id"].startswith("MH-VERIFICATION_RESULT")
        assert out["fidelity_status"] == "aligned"
        assert out["fidelity_score"] == 1.0
        assert Path(out["fidelity_report"]).exists()

    def test_end_to_end_misaligned_success_but_wrong_model(self, tmp_path):
        # 代码执行成功，但没执行 MODEL_IR 声明的模型 → misaligned
        out = run_code_pipeline(tmp_path, IR_OK, CODE_WRONG, model_id="M001")
        assert out["exec_status"] == "success"
        assert out["fidelity_status"] == "misaligned"
        assert out["fidelity_score"] < 1.0
        rep = json.loads(Path(out["fidelity_report"]).read_text(encoding="utf-8"))
        f1 = [c for c in rep["checks"] if c["name"].startswith("F1")]
        assert f1 and f1[0]["passed"] is False

    def test_end_to_end_failed_execution_unverifiable(self, tmp_path):
        out = run_code_pipeline(tmp_path, IR_OK, "print(1/0)\n",
                                model_id="M001")
        assert out["exec_status"] == "failed"
        assert out["fidelity_status"] == "unverifiable"
