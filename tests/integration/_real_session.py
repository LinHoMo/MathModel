# -*- coding: utf-8 -*-
"""测试公共真实会话工厂（audit FIX-1.5：fixture 真实化，禁止占位假闭环）。

背景：旧测试 fixture 让默认路径以「占位 claim + 假证据」跑通；新门禁
（FIX-1.1~1.4：execution_result schema 门禁 / 失败传播 / E9 数值真实性 /
占位 claim 拦截）下，无数值执行会如实 FAIL 并收敛为 blocked（引擎反馈环
收敛，audit P0）。

本 helper 注入外部 Model Constructor 的**真实产物**（MODEL_IR + 可执行
代码 + 数值验证规格），经真 subprocess 执行形成真证据闭环——测试继续走
production path（RuntimeSession.run() 全 DAG）。

LLM-free 边界：core 不构造模型；模型/代码/验证规格由外部注入（等同
K003/P1-VS-001 的「外部 Agent 提供模型，harness 执行」语义）。

用法：所有集成测试的 _session 改为
    from _real_session import make_real_session
    def _session(tmp_path, questions=("Q001", "Q002"), run=True, name="proj", **kw):
        return make_real_session(tmp_path, questions=questions, run=run,
                                 name=name, **kw)
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

# ---------------------------------------------------------------- 外部产物

_MINIMAL_CODE = '''# -*- coding: utf-8 -*-
"""测试夹具可执行模型：y = a*x + b（固定 ABI def solve(inputs) -> outputs）。

真实数值：a=2.0, x=3.0, b=1.0 → y = 7.0。subprocess 真执行，退出码来自 OS。
结构化输出约定（LocalPythonAdapter）：stdout 最后一块合法 JSON 作为 outputs。
"""
import json


def solve(inputs):
    a = float(inputs["a"])
    x = float(inputs["x"])
    b = float(inputs["b"])
    return {"y": a * x + b, "ok": True, "a": a, "x": x, "b": b}


if __name__ == "__main__":
    data = json.load(open("input.json", encoding="utf-8"))
    print(json.dumps(solve(data), ensure_ascii=False))
'''


def _minimal_mir_raw(qid: str) -> dict:
    """最小但真实的三层 MODEL_IR（L1 semantic / L2 mathematical / L3 computational）。

    所有数组节非空、id 字段齐备（validate_model_ir 全过 + model_ir.schema.json
    实例校验全过——audit FIX-5.4 契约对齐）；parameters 携带执行输入
    （_execution_inputs 从 symbol+value 派生 input.json）。
    """
    return {
        "ir_version": "1.0",
        "model_id": "M-TEST-{}-v1".format(qid),
        "model_family": {
            "primary": "algebraic_linear",
            "secondary": [],
            "description": "线性代数基准模型（测试夹具，外部 Model Constructor 注入）",
        },
        "problem_binding": {"problem_id": "TEST-PROB", "sub_question_id": "Q1", "problem_sha256": "b" * 64},
        "assumptions": [{
            "assumption_id": "A001",
            "text": "输入参数 a/x/b 在允许域内且为有限实数",
            "type": "simplification",
            "rationale": "测试夹具保证输入域",
            "source": "test_fixture",
            "confidence": 0.9,
            "sub_question_binding": ["Q1"],
        }],
        "variables": [{
            "variable_id": "V001",
            "name": "y",
            "symbol": "y",
            "definition": "模型输出（线性组合）",
            "unit": "-",
            "type": "state",
            "value_range": {"min": 0.0, "max": 1e6},
            "sub_question_binding": ["Q1"],
        }],
        "parameters": [
            {"parameter_id": "PARM001", "name": "a", "symbol": "a", "value": 2.0, "unit": "-", "source": "test_fixture"},
            {"parameter_id": "PARM002", "name": "x", "symbol": "x", "value": 3.0, "unit": "-", "source": "test_fixture"},
            {"parameter_id": "PARM003", "name": "b", "symbol": "b", "value": 1.0, "unit": "-", "source": "test_fixture"},
        ],
        "objectives": [{
            "objective_id": "OBJ001",
            "type": "compute",
            "expression": "y = a*x + b",
            "variables_refs": ["V001"],
            "parameters_refs": ["PARM001", "PARM002", "PARM003"],
            "sub_question_binding": ["Q1"],
        }],
        "constraints": [{
            "constraint_id": "C001",
            "type": "range",
            "expression": "y >= 0",
            "variables_refs": ["V001"],
            "source": "test_fixture",
            "sub_question_binding": ["Q1"],
        }],
        "mechanisms": [{
            "mechanism_id": "MECH001",
            "name": "linear_mapping",
            "description": "输入到输出的线性映射（affine）",
            "related_equations": ["E001"],
            "sub_question_binding": ["Q1"],
        }],
        "equations": [{
            "equation_id": "E001",
            "latex": "y = ax + b",
            "type": "constitutive",
            "variables_refs": ["V001"],
            "parameters_refs": ["PARM001", "PARM002", "PARM003"],
            "mechanism_ref": "MECH001",
            "derivation_trace": ["mechanism MECH001"],
            "sub_question_binding": ["Q1"],
        }],
        "dependencies": [{
            "dependency_id": "DEP001",
            "kind": "parameter_binding",
            "source": "PARM001/PARM002/PARM003",
            "target": "E001",
        }],
        "solvers": [{
            "solver_id": "S001",
            "name": "直接代入求解",
            "type": "direct",
            "method": "algebraic substitution",
            "implementation_ref": "CODE-{}".format(qid),
            "sub_question_binding": ["Q1"],
        }],
        "experiments": [{
            "experiment_id": "EXP001",
            "description": "基准输入求解 y = 2*3 + 1 = 7",
            "type": "simulation",
            "inputs": {"a": 2.0, "x": 3.0, "b": 1.0},
            "expected_outputs": ["y"],
            "sub_question_binding": ["Q1"],
        }],
        "validations": [{
            "validation_id": "VAL001",
            "type": "constraint_check",
            "spec": "outputs.y == 7.0",
            "status": "required",
            "method": "deterministic_check",
            "targets_refs": ["OBJ001"],
            "sub_question_binding": ["Q1"],
        }],
        "claims": [{
            "claim_id": "CLM001",
            "text": "模型输出 y = a*x + b",
            "type": "descriptive",
            "evidence_refs": ["EXP001"],
            "model_refs": ["M-TEST-{}-v1".format(qid)],
            "status": "candidate",
            "sub_question_binding": ["Q1"],
        }],
        "model_graph": {"nodes": ["V001", "E001"], "edges": [["E001", "V001"]]},
        "modeling_trace": [{"step": "linear_model", "note": "测试夹具模型"}],
    }


MINIMAL_VALIDATION_SPEC = {
    "constraint_tolerance": 1e-9,
    "checks": [
        {"name": "y_output_exists", "kind": "output_field_exists",
         "path": "y"},
        {"name": "y_is_numeric", "kind": "output_numeric", "path": "y"},
        {"name": "y_equals_7", "kind": "output_equals", "path": "y",
         "expect": 7.0, "tolerance": 1e-9},
        {"name": "y_in_domain", "kind": "output_range", "path": "y",
         "min": 0.0, "max": 1e6},
    ],
    "objective": {"name": "y", "expect": 7.0, "tolerance": 1e-9},
    "domain": {"min": 0.0, "max": 1e6},
}


def make_real_session(tmp_path, questions=("Q001", "Q002"), run=True,
                      name="proj", **kw):
    """构造注入真实外部产物的 RuntimeSession（production path 全 DAG）。

    内联注入（不 import conftest——pytest 插件机制下 from conftest import
    会取到加载中的模块实例，函数 globals 不完整）：外部 MODEL_IR + CODE +
    validation_spec（外部 Model Constructor 产物），挂真实 LocalPythonAdapter。

    ADR-0008：features 由问题理解层从题面派生，故写入最小题面（真实项目必备）。
    """
    from modeling_harness.runtime.execution.session import RuntimeSession
    from modeling_harness.runtime.execution.adapters import LocalPythonAdapter

    proj = Path(tmp_path) / name
    (proj / "inputs").mkdir(parents=True, exist_ok=True)
    (proj / "inputs" / "problem.txt").write_text(
        "2026 年数学建模竞赛题目\n\n"
        "问题1　根据给定的数据，对候选方案作综合评价。\n",
        encoding="utf-8")

    qs = list(questions)
    external_model_irs = {q: _minimal_mir(q) for q in qs}
    external_code = {q: _MINIMAL_CODE for q in qs}
    validation_specs = {q: dict(MINIMAL_VALIDATION_SPEC) for q in qs}
    kw.setdefault("max_workers", 1)
    s = RuntimeSession(
        proj, qs,
        execution_adapter=LocalPythonAdapter(),
        external_model_irs=external_model_irs,
        external_code=external_code,
        validation_specs=validation_specs,
        **kw)
    if run:
        s.run()
    return s


def _minimal_mir(qid: str) -> dict:
    """MODEL_IR 契约 v1.0 迁移（唯一真源 src/modeling_harness/schemas/v3/model/model_ir.schema.json）。"""
    try:
        from mir_compat import migrate_model_ir
    except ImportError:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "P15" / "vs001_run"))
        from mir_compat import migrate_model_ir
    return migrate_model_ir(_minimal_mir_raw(qid))
