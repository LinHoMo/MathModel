"""P1-VS-001 C1 — MODEL_IR 升入 core 的单元测试。

验收：
  1. 字段齐全（18 required）→ ModelIRBuilder.from_dict 通过，三层视图完整
  2. 缺字段 → ModelIRError
  3. example_2024_A.json 黄金样本 → 通过（研究层真实样例，迁入 core 的基线）
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.modeling.model_ir import (  # noqa: E402
    MODEL_IR_REQUIRED_FIELDS,
    ModelIR,
    ModelIRBuilder,
    ModelIRError,
    validate_model_ir,
)

EXAMPLE = REPO / "research" / "P15" / "model_representation" / "example_2024_A.json"


def _minimal_full_ir() -> dict:
    """最小但 18 required 字段齐全、三层非空的 MODEL_IR。"""
    return {
        "ir_version": "1.0",
        "model_id": "M2024A-Q1-v0",
        "model_family": {"primary": "kinematics-rigid-chain",
                         "description": "刚性链运动学"},
        "problem_binding": {"problem_id": "2024_A",
                            "sub_question_id": "Q1",
                            "problem_sha256": "0" * 64},
        "assumptions": [{"assumption_id": "ASM001", "text": "刚性连接",
                         "type": "mechanism", "rationale": "题面规定"}],
        "variables": [{"variable_id": "VAR001", "name": "龙头角度",
                       "symbol": "theta", "definition": "龙头把手极角",
                       "unit": "rad", "type": "state",
                       "sub_question_binding": "Q1"}],
        "parameters": [{"parameter_id": "PARM001", "name": "初始半径",
                        "symbol": "R_A", "value": 8.8, "source": "题目"}],
        "objectives": [{"objective_id": "OBJ001", "type": "estimate",
                        "expression": "theta(t)", "variables_refs": ["VAR001"],
                        "sub_question_binding": "Q1"}],
        "constraints": [{"constraint_id": "C001", "type": "equality",
                         "expression": "R = R_A - b*theta",
                         "variables_refs": ["VAR001"], "source": "题目",
                         "sub_question_binding": "Q1"}],
        "mechanisms": [{"mechanism_id": "MECH001", "description": "等距螺线",
                        "related_equations": ["EQ001"],
                        "sub_question_binding": "Q1"}],
        "equations": [{"equation_id": "EQ001", "latex": "R(\\theta)=R_A-b\\theta",
                       "type": "geometry", "variables_refs": ["VAR001"],
                       "derivation_trace": "题面", "sub_question_binding": "Q1"}],
        "dependencies": [{"from": "EQ001", "to": "C001"}],
        "solvers": [{"solver_id": "SOLVER001", "method": "euler",
                     "implementation_ref": "run_model.py",
                     "sub_question_binding": "Q1"}],
        "experiments": [{"experiment_id": "EXP001", "type": "baseline",
                         "inputs": {"T": 300}, "expected_outputs": {"theta": 0},
                         "sub_question_binding": "Q1"}],
        "validations": [{"validation_id": "VAL001", "type": "baseline",
                         "method": "constraint_violation_max",
                         "targets_refs": ["C001"], "sub_question_binding": "Q1"}],
        "claims": [{"claim_id": "CLM001", "text": "龙头位置随时间推进",
                    "type": "descriptive", "evidence_refs": ["EXP001"],
                    "model_refs": ["M2024A-Q1-v0"],
                    "sub_question_binding": "Q1", "status": "proposed"}],
        "model_graph": {"nodes": ["EQ001", "C001"], "edges": []},
        "modeling_trace": [{"step": "读题", "outcome": "识别螺线几何"}],
    }


class TestRequiredFields:
    def test_full_fields_passes(self):
        mir = ModelIRBuilder.from_dict(_minimal_full_ir())
        assert isinstance(mir, ModelIR)
        assert mir.ir_version == "1.0"
        assert mir.model_id == "M2024A-Q1-v0"

    def test_missing_field_raises(self):
        data = _minimal_full_ir()
        del data["modeling_trace"]
        with pytest.raises(ModelIRError) as ei:
            ModelIRBuilder.from_dict(data)
        assert "modeling_trace" in str(ei.value)
        assert "required" in str(ei.value)

    def test_all_18_required_checked(self):
        assert len(MODEL_IR_REQUIRED_FIELDS) == 18
        data = {}
        problems = validate_model_ir(data)
        assert len(problems) >= 1
        assert "required" in problems[0]

    def test_non_dict_raises(self):
        with pytest.raises(ModelIRError):
            ModelIRBuilder.from_dict(["not", "a", "dict"])


class TestThreeLayers:
    def test_l1_l2_l3_layer_presence(self):
        mir = ModelIRBuilder.from_dict(_minimal_full_ir())
        layers = mir.layers()
        assert set(layers) == {"L1_semantic", "L2_mathematical", "L3_computational"}
        # L1: 问题语义（绑定/假设/变量/参数）
        assert set(layers["L1_semantic"]) == {
            "problem_binding", "assumptions", "variables", "parameters"}
        # L2: 数学形式（目标/约束/机理/方程/依赖）
        assert set(layers["L2_mathematical"]) == {
            "objectives", "constraints", "mechanisms", "equations",
            "dependencies"}
        # L3: 可计算（求解器/实验/验证）
        assert set(layers["L3_computational"]) == {
            "solvers", "experiments", "validations"}

    def test_parameters_dict(self):
        mir = ModelIRBuilder.from_dict(_minimal_full_ir())
        pd = mir.parameters_dict()
        assert pd["R_A"] == 8.8


class TestGoldenSample:
    def test_example_2024_A_passes(self):
        if not EXAMPLE.exists():
            pytest.skip("example_2024_A.json 不在仓库（golden 样本缺失）")
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        problems = validate_model_ir(data)
        assert problems == [], problems[:5]
        mir = ModelIRBuilder.from_dict(data)
        assert mir.l1["variables"] and mir.l2["equations"] \
            and mir.l3["solvers"]
