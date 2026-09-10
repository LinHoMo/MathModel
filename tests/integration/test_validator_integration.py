# -*- coding: utf-8 -*-
"""P0-3 验收：Engine Validator Hook 启用（方案 B）。

验收语义（ROADMAP P0-3）：
  * session 创建 WorkflowEngine 时注册 validators（全部 NODE_TYPES）
  * PASS 节点 outputs.artifacts 中不存在的 id → validator 否决 → 节点 FAIL
    （handler 不能自己说完成就算完成；The Agent Is Not The State）
  * outputs.evidence 端点不存在 → 否决
  * 合法产物/证据 → 正常 PASS（不误杀生产路径）

LLM-free：validator 纯机械复核。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests" / "integration"))

from _real_session import MINIMAL_VALIDATION_SPEC, _minimal_mir  # noqa: E402

from modeling_harness.runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from modeling_harness.runtime.execution.engine import NodeResult, PASS  # noqa: E402
from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402


def _make(tmp_path, mir, code):
    return RuntimeSession(
        Path(tmp_path) / "proj", ["Q001"], max_workers=1,
        execution_adapter=LocalPythonAdapter(),
        external_model_irs={"Q001": mir},
        external_code={"Q001": code},
        validation_specs={"Q001": dict(MINIMAL_VALIDATION_SPEC)})


class TestEngineValidators:
    """P0-3 验收。"""

    def test_validators_registered_on_session(self, tmp_path):
        """session 创建引擎时 validators 非空（全部 NODE_TYPES 覆盖）。"""
        from modeling_harness.runtime.execution.dag import NODE_TYPES
        s = _make(tmp_path, _minimal_mir("Q001"),
                  "def solve(inputs):\n    return {}\n")
        assert s.engine.validators, "engine.validators 必须非空"
        for t in NODE_TYPES:
            assert t in s.engine.validators, f"validator 未注册 type={t}"

    def test_fake_artifact_rejected(self, tmp_path):
        """PASS 节点声称不存在的 artifact → validator 否决 → FAIL。"""
        from modeling_harness.runtime.execution.validators import evidence_consistency_validator
        s = _make(tmp_path, _minimal_mir("Q001"),
                  "def solve(inputs):\n    return {}\n")
        v = evidence_consistency_validator(s.registry, s.graph)
        fake = NodeResult(PASS, "fake", outputs={"artifacts": ["NOPE-999"]})
        reason = v("problem_analysis", fake)
        assert reason and "NOPE-999" in reason

    def test_fake_evidence_endpoint_rejected(self, tmp_path):
        from modeling_harness.runtime.execution.validators import evidence_consistency_validator
        s = _make(tmp_path, _minimal_mir("Q001"),
                  "def solve(inputs):\n    return {}\n")
        v = evidence_consistency_validator(s.registry, s.graph)
        fake = NodeResult(PASS, "fake", outputs={
            "evidence": [{"from": "GHOST-1", "relation": "produces",
                          "to": "GHOST-2"}]})
        reason = v("problem_analysis", fake)
        assert reason and "GHOST" in reason

    def test_clean_pass_not_blocked(self, tmp_path):
        """合法产物/证据 → validator 通过（生产路径不误杀）。"""
        from modeling_harness.runtime.execution.validators import evidence_consistency_validator
        s = _make(tmp_path, _minimal_mir("Q001"),
                  "def solve(inputs):\n    return {}\n")
        art = s.registry.create("claim", title="t", question="Q001",
                                activate=True, created_by="test")
        v = evidence_consistency_validator(s.registry, s.graph)
        ok = NodeResult(PASS, "ok", outputs={
            "artifacts": [art.artifact_id],
            "evidence": [{"from": art.artifact_id, "relation": "supports",
                          "to": art.artifact_id}]})
        assert v("problem_analysis", ok) == ""

    def test_full_loop_still_green_with_validator(self, tmp_path):
        """VS-001 全闭环在 validator 启用下仍 PASS（不误杀真实产物）。"""
        import sys as _s
        _s.path.insert(0, str(REPO / "research" / "P15" / "vs001_run"))
        from vs001_driver import run_m1, run_m2

        s = make_here = RuntimeSession(
            Path(tmp_path) / "proj2", ["Q001"], max_workers=1,
            execution_adapter=LocalPythonAdapter())
        from vs001_driver import inject
        from vs001_fixtures import C1_CODE, M1_DICT
        inject(s, M1_DICT, C1_CODE, tmp_path / "work")
        nodes = ["problem_analysis", "literature_search", "model_selection",
                 "model_construction", "model_critique", "assumption_check",
                 "code_generation", "model_execution", "model_validation"]
        results = {}
        for nid in nodes:
            results[nid] = s.engine.step(nid)
        assert results["model_validation"].status == "fail"
        assert results["model_execution"].status == "pass", \
            "validator 不应误杀真实执行"
