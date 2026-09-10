# -*- coding: utf-8 -*-
"""P1-1 验收：Constructor Adapter Protocol。

验收语义（ROADMAP P1-1）：
  * ConstructionBundle 可序列化/反序列化（to_dict/to_json/from_json 往返）
  * ConstructorAdapter ABC 定义完整（construct 抽象 + capability 推断）
  * mock adapter 完成 construct → apply_bundle → execute → validate 闭环
    （bundle 经官方通道注入，DAG 跑通）
  * Constructor 无 execution/fidelity/PASS 写权限（协议层不暴露）
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "tests" / "integration"))

from _real_session import MINIMAL_VALIDATION_SPEC, _minimal_mir  # noqa: E402

from runtime.constructors import (  # noqa: E402
    ConstructionBundle, ConstructorAdapter, ConstructorRegistry,
)
from runtime.constructors.registry import apply_bundle  # noqa: E402
from runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402

OK_CODE = """def solve(inputs):
    a = float(inputs["a"]); x = float(inputs["x"]); b = float(inputs["b"])
    return {"y": a * x + b, "ok": True}


if __name__ == "__main__":
    import json
    data = json.load(open("input.json", encoding="utf-8"))
    print(json.dumps(solve(data), ensure_ascii=False))
"""

LOOP_NODES = [
    "problem_analysis", "literature_search", "model_selection",
    "model_construction", "model_critique", "assumption_check",
    "code_generation", "model_execution", "model_validation",
]


class MockConstructor(ConstructorAdapter):
    """mock adapter：产出固定建模提案（测试用，等价外部 Agent）。"""

    name = "mock-constructor"
    capability = "C5"

    def construct(self, problem, context=None):
        mir = _minimal_mir(problem.get("question", "Q001"))
        if context and context.get("revision_of"):
            mir = dict(mir)
            mir["model_id"] = f"{mir['model_id']}-REV"
        return ConstructionBundle(
            question=problem.get("question", "Q001"),
            model_ir=mir,
            code=OK_CODE,
            validation_spec=dict(MINIMAL_VALIDATION_SPEC),
            output_mapping={},
            revision_of=(context or {}).get("revision_of"),
            reasoning_metadata={"mock": True},
            constructor="mock-constructor",
        )


@pytest.fixture()
def registry():
    r = ConstructorRegistry()
    r.register(MockConstructor())
    return r


class TestConstructorProtocol:
    """P1-1 验收。"""

    def test_bundle_serialization_roundtrip(self):
        b = ConstructionBundle(
            question="Q001", model_ir={"model_id": "M1", "variables": ["x"]},
            code=OK_CODE, output_mapping={"x": "pos"},
            validation_spec={"checks": []},
            revision_of="M0", reasoning_metadata={"note": "n"},
            constructor="mock-constructor")
        d = b.to_dict()
        j = b.to_json()
        b2 = ConstructionBundle.from_json(j)
        assert b2.to_dict() == d, "序列化往返必须一致"
        assert b2.question == "Q001" and b2.revision_of == "M0"

    def test_capability_level_inference(self):
        c0 = ConstructionBundle(question="Q001", model_ir={})
        assert c0.capability_level == "C0"
        c2 = ConstructionBundle(question="Q001", model_ir={"x": 1})
        assert c2.capability_level == "C2"
        c3 = ConstructionBundle(question="Q001", model_ir={"x": 1}, code="c")
        assert c3.capability_level == "C3"
        c4 = ConstructionBundle(question="Q001", model_ir={"x": 1}, code="c",
                                output_mapping={"x": "x"})
        assert c4.capability_level == "C4"
        c5 = ConstructionBundle(question="Q001", model_ir={"x": 1}, code="c",
                                output_mapping={"x": "x"},
                                validation_spec={"checks": []})
        assert c5.capability_level == "C5"

    def test_adapter_abc_complete(self, registry):
        assert registry.has("mock-constructor")
        assert registry.get("mock-constructor").describe() == {
            "name": "mock-constructor", "capability": "C5"}

    def test_mock_constructor_full_loop(self, tmp_path):
        """mock adapter → construct → apply_bundle → DAG 闭环。"""
        s = RuntimeSession(
            Path(tmp_path) / "proj", ["Q001"], max_workers=1,
            execution_adapter=LocalPythonAdapter())
        c = ConstructorRegistry().get if False else None
        reg = ConstructorRegistry()
        reg.register(MockConstructor())
        bundle = reg.get("mock-constructor").construct(
            {"question": "Q001"})
        apply_bundle(s, bundle, workdir=str(tmp_path / "work"))
        results = {}
        for nid in LOOP_NODES:
            results[nid] = s.engine.step(nid)
        assert results["model_execution"].status == "pass", \
            f"bundle 注入后执行应 pass: {results['model_execution'].reason}"
        assert results["model_validation"].status == "pass"
        # 产物真实登记
        execs = [a for a in s.registry.list_by_type("execution_result")]
        assert execs and execs[0].data["status"] == "success"

    def test_constructor_has_no_fact_writer(self):
        """Constructor 协议不暴露 execution/fidelity/PASS 写权限。"""
        b = ConstructionBundle(question="Q001", model_ir={"x": 1})
        d = b.to_dict()
        for forbidden in ("execution_result", "fidelity", "status", "verification"):
            assert forbidden not in d, \
                f"ConstructionBundle 不应含事实写入字段: {forbidden}"
