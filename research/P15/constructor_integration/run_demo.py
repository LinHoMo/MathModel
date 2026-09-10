# -*- coding: utf-8 -*-
"""Constructor 集成实证（T-CONF-003 落地）：外部 Constructor 产物 → Harness 承载链路。

链路（与 tests/integration/test_constructor_protocol.py 的 mock 全环同构，但走
**MathModelAgentAdapter 目录加载通道**，即外部 Agent（Doubao/GPT/MMA）在 harness
之外产出 MODEL_IR + 代码，harness 只承载、执行、验证——LLM-free 定位的直接证据）：

    mma_out/（外部 Agent 产物目录）
      → MathModelAgentAdapter.construct()            # 打包为 ConstructionBundle
      → apply_bundle(session, bundle)                # 注入 harness shared 状态
      → engine.step(LOOP_NODES)                      # 真实 subprocess 执行
      → ExecutionResult.status == "success"          # 数值来自真实执行，非伪造

运行（Python 3.12）：
    py -3.12 run_demo.py
退出码 0 = 链路闭环；任何断言失败 = 非 0 退出。

注意：本脚本不修改 src/ 下任何代码；仅演示外部产物经 adapter 通道进入 harness。
MODEL_IR 需满足 model_ir.schema.json 的 18 个 required 字段（外部契约校验）。
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]          # research/P15/constructor_integration -> repo root
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from modeling_harness.adapters.mathmodel_agent import (  # noqa: E402
    ConstructorNotConfigured, MathModelAgentAdapter,
)
from modeling_harness.runtime.constructors.registry import apply_bundle  # noqa: E402
from modeling_harness.runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402

HERE = Path(__file__).resolve().parent
MMA_OUT = HERE / "mma_out"

# 链路需要走到的节点（与 DAG 主链一致；execution 为真实 subprocess）
LOOP_NODES = [
    "problem_analysis", "literature_search", "model_selection",
    "model_construction", "model_critique", "assumption_check",
    "code_generation", "model_execution", "model_validation",
]

# ---------------------------------------------------------------------------
# 外部 Constructor 产物样例（2024A 题材，简化校准模型；由本脚本生成到 mma_out/）
# ---------------------------------------------------------------------------

DEMO_CODE = '''# -*- coding: utf-8 -*-
"""2024A 简化校准模型（外部 Constructor 注入；demo 可执行模型）。

约定（LocalPythonAdapter）：stdout 最后一块合法 JSON 作为 outputs。
真实数值：a=2.0, x=3.0, b=1.0 -> y = 7.0。
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


def _demo_mir(qid: str = "Q001") -> dict:
    """合法三层 MODEL_IR（L1 semantic / L2 mathematical / L3 computational），
    满足 model_ir.schema.json 18 个 required 字段（外部契约校验）。"""
    return {
        "ir_version": "1.0",
        "model_id": f"M-2024A-{qid}-CONSTRUCTOR-V1",
        "model_family": {
            "primary": "algebraic_linear",
            "secondary": [],
            "description": "2024A 简化校准模型（外部 Constructor 注入，harness 承载）",
        },
        "problem_binding": {
            "problem_id": "2024A", "sub_question_id": qid, "problem_sha256": "0" * 64,
        },
        "assumptions": [{
            "assumption_id": "A001",
            "text": "输入参数 a/x/b 在允许域内且为有限实数",
            "type": "simplification",
            "rationale": "demo 夹具保证输入基",
            "source": "constructor-demo",
            "confidence": 0.9,
            "sub_question_binding": [qid],
        }],
        "variables": [{
            "variable_id": "V001",
            "name": "y",
            "symbol": "y",
            "definition": "模型输出（线性组合）",
            "unit": "-",
            "type": "state",
            "value_range": {"min": 0.0, "max": 1e6},
            "sub_question_binding": [qid],
        }],
        "parameters": [
            {"parameter_id": "PARM001", "name": "a", "symbol": "a", "value": 2.0, "unit": "-", "source": "constructor-demo"},
            {"parameter_id": "PARM002", "name": "x", "symbol": "x", "value": 3.0, "unit": "-", "source": "constructor-demo"},
            {"parameter_id": "PARM003", "name": "b", "symbol": "b", "value": 1.0, "unit": "-", "source": "constructor-demo"},
        ],
        "objectives": [{
            "objective_id": "OBJ001",
            "type": "compute",
            "expression": "y = a*x + b",
            "variables_refs": ["V001"],
            "parameters_refs": ["PARM001", "PARM002", "PARM003"],
            "sub_question_binding": [qid],
        }],
        "constraints": [{
            "constraint_id": "C001",
            "type": "range",
            "expression": "y >= 0",
            "variables_refs": ["V001"],
            "source": "constructor-demo",
            "sub_question_binding": [qid],
        }],
        "mechanisms": [{
            "mechanism_id": "MECH001",
            "name": "linear_mapping",
            "description": "输入到输出的线性映射（affine）",
            "related_equations": ["E001"],
            "sub_question_binding": [qid],
        }],
        "equations": [{
            "equation_id": "E001",
            "latex": "y = ax + b",
            "type": "constitutive",
            "variables_refs": ["V001"],
            "parameters_refs": ["PARM001", "PARM002", "PARM003"],
            "mechanism_ref": "MECH001",
            "derivation_trace": ["mechanism MECH001"],
            "sub_question_binding": [qid],
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
            "implementation_ref": f"CODE-{qid}",
            "sub_question_binding": [qid],
        }],
        "experiments": [{
            "experiment_id": "EXP001",
            "description": "基准输入求解 y = 2*3 + 1 = 7",
            "type": "simulation",
            "inputs": {"a": 2.0, "x": 3.0, "b": 1.0},
            "expected_outputs": ["y"],
            "sub_question_binding": [qid],
        }],
        "validations": [{
            "validation_id": "VAL001",
            "type": "constraint_check",
            "spec": "outputs.y == 7.0",
            "status": "required",
            "method": "deterministic_check",
            "targets_refs": ["OBJ001"],
            "sub_question_binding": [qid],
        }],
        "claims": [{
            "claim_id": "CLM001",
            "text": "模型输出 y = a*x + b",
            "type": "descriptive",
            "evidence_refs": ["EXP001"],
            "model_refs": [f"M-2024A-{qid}-CONSTRUCTOR-V1"],
            "status": "candidate",
            "sub_question_binding": [qid],
        }],
        "model_graph": {"nodes": ["V001", "E001"], "edges": ["E001->V001"]},
        "modeling_trace": [{"step": "linear_model", "note": "constructor-demo 模型"}],
    }


def _ensure_mma_out() -> Path:
    MMA_OUT.mkdir(parents=True, exist_ok=True)
    (MMA_OUT / "model_ir.json").write_text(
        json.dumps(_demo_mir(), ensure_ascii=False, indent=2), encoding="utf-8")
    (MMA_OUT / "code.py").write_text(DEMO_CODE, encoding="utf-8")
    (MMA_OUT / "output_mapping.json").write_text(
        json.dumps({"y": "y_hat"}, ensure_ascii=False, indent=2), encoding="utf-8")
    validation_spec = {
        "constraint_tolerance": 1e-9,
        "checks": [
            {"name": "y_output_exists", "kind": "output_field_exists", "path": "y"},
            {"name": "y_is_numeric", "kind": "output_numeric", "path": "y"},
            {"name": "y_equals_7", "kind": "output_equals", "path": "y",
             "expect": 7.0, "tolerance": 1e-9},
            {"name": "y_in_domain", "kind": "output_range", "path": "y",
             "min": 0.0, "max": 1e6},
        ],
        "objective": {"name": "y", "expect": 7.0, "tolerance": 1e-9},
        "domain": {"min": 0.0, "max": 1e6},
    }
    (MMA_OUT / "specs.json").write_text(
        json.dumps(validation_spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return MMA_OUT


def main() -> int:
    out = _ensure_mma_out()
    print(f"[1/4] 外部产物目录: {out}")

    # 未配置通道必须如实报错（禁止伪造/fallback）
    try:
        MathModelAgentAdapter().construct({"question": "Q001"})
        raise SystemExit("FAIL: 未配置 adapter 应抛 ConstructorNotConfigured")
    except ConstructorNotConfigured:
        print("[2/4] 未配置通道如实报错 ✓（禁止 fallback/伪造）")

    with tempfile.TemporaryDirectory() as td:
        s = RuntimeSession(
            Path(td) / "proj", ["Q001"], max_workers=1,
            execution_adapter=LocalPythonAdapter())
        adapter = MathModelAgentAdapter(source_dir=out)
        bundle = adapter.construct({"question": "Q001"})
        print(f"[3/4] construct → ConstructionBundle"
              f" (question={bundle.question}, constructor={bundle.constructor})")
        shared = apply_bundle(s, bundle, workdir=str(Path(td) / "work"))
        assert "Q001" in shared["external_model_irs"], "bundle 注入失败"
        assert "Q001" in shared["external_code"], "code 注入失败"

        results = {}
        for nid in LOOP_NODES:
            results[nid] = s.engine.step(nid)
        status = {nid: r.status for nid, r in results.items()}
        print(f"[4/4] 引擎主链 step 结果: {status}")
        assert results["model_execution"].status == "pass", (
            f"bundle 注入后 model_execution 应 pass: {results['model_execution'].reason}")
        assert results["model_validation"].status == "pass", "model_validation 应 pass"
        execs = [a for a in s.registry.list_by_type("execution_result")]
        assert execs and execs[0].data["status"] == "success", "ExecutionResult 应为真实 success"
        print(f"      ExecutionResult: {execs[0].data['execution_id']} "
              f"status={execs[0].data['status']} outputs={execs[0].data['outputs']}")

    print("链路闭环 ✓：外部 Constructor 产物 → adapter → bundle → harness 执行 → 真实证据")
    return 0


if __name__ == "__main__":
    sys.exit(main())
