"""共享测试工具（无状态、只读，跨测试文件复用）。

audit FIX-1.5：测试不得再依赖默认路径（无外部注入）产出占位 claim 后
还断言 PASS。默认路径无真实执行事实 → evidence_build 如实 FAIL。
需要"完整闭环成功"的测试必须经 external_model_irs / external_code /
validation_specs 注入真实 Model Constructor 产物（LLM-free 边界：
构造来自外部，runtime 只执行/验证）。
"""

import json  # noqa: F401  （保留供下游可能引用）
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
import sys  # noqa: E402
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402


# ---------------------------------------------------------------- 注入工具
# 最小真实 MODEL_IR（18 顶层字段契约）+ 自包含代码 + 数值验证规格。
# 模型语义：y = slope*x + intercept（确定性，无第三方依赖）。

def mir(qid: str, model_id: str) -> dict:
    return {
        "ir_version": "1.0",
        "model_id": model_id,
        "model_family": {
            "primary": "linear_regression",
            "description": "确定性线性模型 y = a*x + b",
            "candidates": [{"family": "linear_regression",
                            "rationale": "单变量确定性关系"}],
        },
        "problem_binding": {
            "problem_id": "demo",
            "sub_question_id": qid,
            "problem_sha256": "a" * 64,
        },
        "assumptions": [{"assumption_id": "A1", "type": "simplification",
                         "statement": "x 与 y 呈线性关系"}],
        "variables": [{"variable_id": "V1", "type": "decision", "symbol": "y",
                       "domain": "real", "description": "目标变量"}],
        "parameters": [{"parameter_id": "P1", "symbol": "slope", "value": 2.0,
                        "source": "假设", "description": "斜率"},
                       {"parameter_id": "P2", "symbol": "intercept", "value": 1.0,
                        "source": "假设", "description": "截距"}],
        "objectives": [{"objective_id": "O1", "type": "estimate",
                        "expression": "y",
                        "sub_question_binding": qid}],
        "constraints": [{"constraint_id": "C1", "expression": "y > -100",
                         "sub_question_binding": qid}],
        "mechanisms": [{"mechanism_id": "M1", "type": "mechanism_assumption",
                        "description": "线性加性机制",
                        "sub_question_binding": qid}],
        "equations": [{"equation_id": "E1", "expression": "y = slope*x + intercept"}],
        "dependencies": [{"dependency_id": "D1", "kind": "data", "target": "x"}],
        "solvers": [{"solver_id": "S1", "family": "closed_form",
                     "backend": "python", "method": "evaluate"}],
        "experiments": [{"experiment_id": "X1", "type": "simulation",
                         "sub_question_binding": qid}],
        "validations": [{"validation_id": "VAL1", "type": "sensitivity",
                         "sub_question_binding": qid}],
        "claims": [{"claim_id": "CL1", "type": "comparative",
                    "sub_question_binding": qid}],
        "model_graph": {"nodes": [], "edges": []},
        "modeling_trace": [{"step": "construct", "note": "test injection"}],
    }


CODE = """\
import json
import os

def solve(inputs):
    x = float(inputs.get("x", 0.0))
    slope = float(inputs.get("slope", 2.0))
    intercept = float(inputs.get("intercept", 1.0))
    return {"y": slope * x + intercept, "x": x}

if __name__ == "__main__":
    _in = {}
    if os.path.exists("input.json"):
        with open("input.json", encoding="utf-8") as _f:
            _in = json.load(_f)
    print(json.dumps(solve(_in), ensure_ascii=False))
"""


def injected_resume(prev, questions):
    """同一 project_dir 上带注入物重建 session（resume 语义）。

    resume/续跑测试必须保留外部 Model Constructor 产物注入，否则默认路径
    无数值执行 → evidence_build 如实 FAIL（FIX-1.2/1.4）。
    """
    from runtime.execution.adapters import LocalPythonAdapter
    s = RuntimeSession(prev.project_dir, list(questions),
                       max_workers=getattr(prev, "_max_workers", 1),
                       execution_adapter=LocalPythonAdapter(),
                       external_model_irs=prev.executor_impl.shared.get(
                           "external_model_irs"),
                       external_code=prev.executor_impl.shared.get(
                           "external_code"),
                       validation_specs=prev.executor_impl.shared.get(
                           "validation_specs"))
    return s


def validation_spec() -> dict:
    return {
        "checks": [
            {"name": "y_field_exists", "kind": "output_field_exists",
             "path": "y"},
            {"name": "y_numeric", "kind": "output_numeric", "path": "y"},
            {"name": "y_in_range", "kind": "output_range", "path": "y",
             "min": -1000, "max": 1000},
        ],
    }


def injected_session(tmp_path, questions=("Q001", "Q002"), max_workers=1,
                     run_meta=None):
    """注入外部 Model Constructor 产物的 RuntimeSession（走真实执行闭环）。

    必须挂真实 LocalPythonAdapter：无数值执行 → evidence_build 如实 FAIL
    （FIX-1.2/1.4）；fixture 默认路径不得再以占位 claim 假 PASS（FIX-1.5）。
    """
    from runtime.execution.adapters import LocalPythonAdapter
    s = RuntimeSession(tmp_path / "proj", list(questions),
                       max_workers=max_workers, run_meta=run_meta or {},
                       execution_adapter=LocalPythonAdapter())
    for q in questions:
        qid = f"Q{questions.index(q) + 1:03d}"
        s.executor_impl.shared["external_model_irs"] = {
            **s.executor_impl.shared.get("external_model_irs", {}),
            qid: mir(qid, f"M-{qid}"),
        }
        s.executor_impl.shared["external_code"] = {
            **s.executor_impl.shared.get("external_code", {}),
            qid: CODE,
        }
        s.executor_impl.shared["validation_specs"] = {
            **s.executor_impl.shared.get("validation_specs", {}),
            qid: validation_spec(),
        }
    return s
