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
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402


# ---------------------------------------------------------------- 注入工具
# 最小真实 MODEL_IR（18 顶层字段契约）+ 自包含代码 + 数值验证规格。
# 模型语义：y = slope*x + intercept（确定性，无第三方依赖）。

def mir(qid: str, model_id: str) -> dict:
    """全测试共用 MODEL_IR 夹具：满足 model_ir.schema.json 各节 required。

    audit FIX-5.4：registry.create 接入 jsonschema 实例校验后，夹具必须
    对齐冻结契约（mechanisms.related_equations / equations.latex /
    solvers.implementation_ref / claims.evidence_refs+model_refs+status /
    experiments.inputs+expected_outputs 等）。
    """
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
                         "statement": "x 与 y 呈线性关系",
                         "text": "x 与 y 呈线性关系",
                         "rationale": "单变量确定性关系"}],
        "variables": [{"variable_id": "V1", "type": "decision", "symbol": "y",
                       "domain": "real", "description": "目标变量",
                       "name": "y", "definition": "目标变量", "unit": "-",
                       "sub_question_binding": qid}],
        "parameters": [{"parameter_id": "P1", "symbol": "slope", "value": 2.0,
                        "source": "假设", "description": "斜率",
                        "name": "slope"},
                       {"parameter_id": "P2", "symbol": "intercept", "value": 1.0,
                        "source": "假设", "description": "截距",
                        "name": "intercept"}],
        "objectives": [{"objective_id": "O1", "type": "estimate",
                        "expression": "y",
                        "sub_question_binding": qid,
                        "variables_refs": ["V1"]}],
        "constraints": [{"constraint_id": "C1", "expression": "y > -100",
                         "sub_question_binding": qid,
                         "type": "bound", "variables_refs": ["V1"],
                         "source": "domain_knowledge"}],
        "mechanisms": [{"mechanism_id": "M1", "type": "mechanism_assumption",
                        "description": "线性加性机制",
                        "sub_question_binding": qid,
                        "related_equations": ["E1"]}],
        "equations": [{"equation_id": "E1", "expression": "y = slope*x + intercept",
                       "latex": "y = a x + b", "type": "definition",
                       "variables_refs": ["V1", "P1", "P2"],
                       "derivation_trace": ["assumption A1"],
                       "sub_question_binding": qid}],
        "dependencies": [{"dependency_id": "D1", "kind": "data", "target": "x"}],
        "solvers": [{"solver_id": "S1", "family": "closed_form",
                     "backend": "python", "method": "evaluate",
                     "implementation_ref": None,
                     "sub_question_binding": qid}],
        "experiments": [{"experiment_id": "X1", "type": "simulation",
                         "sub_question_binding": qid,
                         "inputs": ["P1", "P2"],
                         "expected_outputs": ["y"]}],
        "validations": [{"validation_id": "VAL1", "type": "sensitivity",
                         "sub_question_binding": qid,
                         "method": "sensitivity_analysis",
                         "targets_refs": ["O1"]}],
        "claims": [{"claim_id": "CL1", "type": "comparative",
                    "sub_question_binding": qid,
                    "text": "模型可解释 y 的线性变化",
                    "evidence_refs": [], "model_refs": [model_id],
                    "status": "candidate"}],
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
    from modeling_harness.runtime.execution.adapters import LocalPythonAdapter
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


def _write_min_problem(project_dir) -> None:
    """写最小题面（ADR-0008）：测试项目的唯一输入，供问题理解层派生 features。

    文本刻意落在「评价」类型上，与旧默认画像的取型一致，使下游选型/规划行为
    保持可比；同时 has_data 由「给定数据」维持为真（不排除需要数据的方法卡）。
    """
    from pathlib import Path
    d = Path(project_dir) / "inputs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "problem.txt").write_text(
        "2026 年数学建模竞赛题目\n\n"
        "问题1　根据给定的数据，对候选方案作综合评价。\n",
        encoding="utf-8")


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

    ADR-0008：生产路径不再回退硬编码画像，features 由问题理解层从
    `inputs/problem.txt` 确定性派生。故本 fixture 必须写入最小题面——
    真实项目同样必备该输入；缺失时 model_selection 会如实 BLOCKED。
    """
    from modeling_harness.runtime.execution.adapters import LocalPythonAdapter
    proj = tmp_path / "proj"
    _write_min_problem(proj)
    s = RuntimeSession(proj, list(questions),
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
