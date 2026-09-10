# -*- coding: utf-8 -*-
"""FIX-3.1（audit P1-03/P1-09）：MODEL_IR→Code 映射一致性校验。

MIR.solvers[].implementation_ref 声明实现引用时，实际执行的 code 必须命中；
未声明（测试注入/骨架 MIR）跳过。映射断裂 → HandlerError 如实传播。

运行: python -m pytest tests/integration/test_ir_code_mapping.py -q
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from conftest import CODE, injected_session, mir, validation_spec  # noqa: E402


def _session_with_mir(tmp_path, mir_data):
    s = injected_session(tmp_path, questions=("Q001",))
    s.executor_impl.shared["external_model_irs"] = {"Q001": mir_data}
    return s


def _mir_with_ref(ref: str) -> dict:
    d = mir("Q001", "M-Q001")
    d["solvers"] = [{"solver_id": "S1", "method": "evaluate",
                     "implementation_ref": ref,
                     "sub_question_binding": "Q001"}]
    return d


def test_ir_code_mapping_validated_when_declared(tmp_path):
    """声明 implementation_ref=model_id（M-Q001）→ 与登记 code 的 model_id 一致，
    执行链真实发生。"""
    s = _session_with_mir(tmp_path, _mir_with_ref("M-Q001"))
    s.run()
    execs = s.registry.list_by_type("execution_result")
    assert execs, "声明映射一致时执行必须真实发生"
    assert all((e.data or {}).get("status") == "success" for e in execs)


def test_ir_code_mapping_mismatch_fails_honestly(tmp_path):
    """声明 implementation_ref=不存在的 model_id（M-OTHER）→ 映射断裂，
    HandlerError 如实传播（run 抛错或节点 FAIL），不产生假 success EXEC。"""
    from modeling_harness.runtime.execution.handlers import HandlerError
    s = _session_with_mir(tmp_path, _mir_with_ref("M-OTHER"))
    try:
        rep = s.run()
        fails = rep["progress"].get("failures", {})
        assert any("映射断裂" in str(m) or "implementation_ref" in str(m)
                   for m in fails.values()), \
            f"执行映射断裂必须 FAIL，实际 failures={fails}"
    except HandlerError:
        pass  # HandlerError 如实传播到顶层也是合法形态
    execs = s.registry.list_by_type("execution_result")
    assert not any((e.data or {}).get("status") == "success" for e in execs)


def test_ir_code_mapping_absent_skips_check(tmp_path):
    """未声明 implementation_ref（conftest.mir 默认）→ 跳过校验，链路照常。"""
    s = injected_session(tmp_path, questions=("Q001",))
    s.run()
    execs = s.registry.list_by_type("execution_result")
    assert execs and all((e.data or {}).get("status") == "success"
                         for e in execs)
