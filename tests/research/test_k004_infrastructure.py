# -*- coding: utf-8 -*-
"""P2-1 验收：K004 基建（Reference Constructor + 协议接入）。

验收语义（ROADMAP P2-1 基建部分）：
  * Reference Constructor（LLM-free）产出合规 ConstructionBundle（C3）
  * bundle 经 P1-1 apply_bundle 注入 → DAG 执行闭环跑通
  * MathModelAgent Adapter 契约存在（未装配时报清晰错误，不静默降级）
  * 预注册协议文档存在且含判定规则（5 结论形态）
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests" / "integration"))
sys.path.insert(0, str(REPO / "research" / "P15" / "k004"))

from _real_session import make_real_session  # noqa: E402
from reference_constructor import ReferenceConstructor  # noqa: E402

from modeling_harness.runtime.constructors.protocol import (  # noqa: E402
    ConstructionBundle, ConstructorAdapter)
from modeling_harness.runtime.constructors.registry import ConstructorRegistry, apply_bundle  # noqa: E402
from modeling_harness.runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402


@pytest.fixture()
def problem():
    return {"question": "Q001",
            "statement": "资源配置优化问题：最小化成本并满足需求约束",
            "features": {"problem_types": ["optimization"],
                         "sub_questions": ["Q1"]}}


class TestK004Infrastructure:
    """P2-1 基建验收。"""

    def test_reference_constructor_produces_bundle(self, problem):
        c = ReferenceConstructor()
        b = c.construct(problem)
        assert b.constructor == "ref"
        assert b.model_ir.get("ir_version") == "1.0"
        assert b.model_ir.get("model_family", {}).get("primary") == "optimization"
        assert b.code and "def solve" in b.code
        assert b.capability_level in ("C3", "C4"), b.capability_level
        # 序列化往返（Constructor 协议契约）
        b2 = ConstructionBundle.from_json(b.to_json())
        assert b2.to_dict() == b.to_dict()

    def test_reference_bundle_applies_and_runs(self, problem, tmp_path):
        """bundle → apply_bundle → DAG 闭环（真实 subprocess）。"""
        b = ReferenceConstructor().construct(problem)
        s = make_real_session(tmp_path / "proj", ["Q001"], run=False)
        apply_bundle(s, b, workdir=str(tmp_path / "work"))
        results = {}
        for nid in ["problem_analysis", "literature_search", "model_selection",
                    "model_construction", "model_critique", "assumption_check",
                    "code_generation", "model_execution", "model_validation"]:
            results[nid] = s.engine.step(nid)
        assert results["model_execution"].status == "pass", \
            f"ref bundle 执行应 pass: {results['model_execution'].reason}"
        assert results["model_validation"].status == "pass"

    def test_registry_accepts_reference(self, problem):
        reg = ConstructorRegistry()
        reg.register(ReferenceConstructor())
        assert reg.has("ref")
        assert reg.get("ref").capability == "C3"

    def test_mma_adapter_contract_clear_error(self, problem):
        """MMA 未装配时报清晰错误（不静默降级/不伪造）。"""
        from mma_adapter import MathModelAgentAdapter
        a = MathModelAgentAdapter(entry="__no_such_agent__")
        with pytest.raises(Exception, match="MathModelAgent 未装配"):
            a.construct(problem)

    def test_preregistration_has_decision_rules(self):
        p = REPO / "research" / "P15" / "protocol" / "preregistration" \
            / "P15-K004-v1.0.md"
        text = p.read_text(encoding="utf-8")
        assert "PREREGISTERED" in text
        assert "判定规则" in text or "结果形态" in text
        assert "64 runs" in text
