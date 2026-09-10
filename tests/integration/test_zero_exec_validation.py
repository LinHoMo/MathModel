# -*- coding: utf-8 -*-
"""P0-4（终审 ROADMAP）：零执行/零验证 ≠ PASS 验收。

验收标准（ROADMAP P0-4）：
1. 无代码 → model_execution blocked（非 PASS）；
2. 有 EXEC 无 spec → model_validation blocked（非 PASS）；
3. 有 EXEC + spec → 正常执行验证（PASS 或如实 FAIL）。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))

from conftest import mir, CODE, validation_spec, injected_session  # noqa: E402

from modeling_harness.runtime.execution.engine import BLOCKED, PASS  # noqa: E402


def _bare_session(tmp_path):
    """无任何注入的默认 session（构造语义：无 MIR/无 code/无 spec）。"""
    return injected_session(tmp_path, questions=("Q001",))


def _setup_executable(s, qid="Q001"):
    """按 DAG 顺序注册 model + MIR + code（供执行/验证测试）。"""
    s.registry.create("model", title="M-Q001", question=qid, activate=True)
    mid = s.executor_impl.construct_model_ir(qid)
    assert mid, "construct_model_ir 必须成功"
    cids = s.executor_impl.generate_code(qid, "code_generation")
    assert cids, "generate_code 必须成功"
    return mid


def test_model_execution_blocked_without_any_model(tmp_path):
    """无任何活跃候选模型 → model_execution blocked（零执行 ≠ PASS）。"""
    s = _bare_session(tmp_path)
    s.executor_impl.shared["external_model_irs"] = {}
    s.executor_impl.shared["external_code"] = {}
    r = s.executor_impl.do_model_execution("model_execution")
    assert r.status == BLOCKED
    assert "零执行" in r.reason


def test_model_execution_blocked_with_mir_but_no_code(tmp_path):
    """有 MIR 但无实现代码 → model_execution blocked。"""
    s = _bare_session(tmp_path)
    s.executor_impl.shared["external_model_irs"] = {"Q001": mir("Q001", "M-Q001")}
    s.executor_impl.shared["external_code"] = {}
    s.registry.create("model", title="M-Q001", question="Q001", activate=True)
    assert s.executor_impl.construct_model_ir("Q001")
    r = s.executor_impl.do_model_execution("model_execution")
    assert r.status == BLOCKED
    assert "无实现代码" in r.reason


def test_model_validation_blocked_without_exec(tmp_path):
    """无活跃执行结果 → model_validation blocked（零验证 ≠ PASS）。"""
    s = _bare_session(tmp_path)
    s.executor_impl.shared["external_model_irs"] = {}
    s.executor_impl.shared["external_code"] = {}
    r = s.executor_impl.do_model_validation("model_validation")
    assert r.status == BLOCKED
    assert "零验证" in r.reason


def test_model_validation_blocked_with_exec_but_no_spec(tmp_path):
    """有 EXEC 但无验证规格 → model_validation blocked。"""
    s = _bare_session(tmp_path)
    s.executor_impl.shared["external_model_irs"] = {"Q001": mir("Q001", "M-Q001")}
    s.executor_impl.shared["external_code"] = {"Q001": CODE}
    s.executor_impl.shared["validation_specs"] = {}
    _setup_executable(s)
    er = s.executor_impl.do_model_execution("model_execution")
    assert er.status == PASS, er.reason
    r = s.executor_impl.do_model_validation("model_validation")
    assert r.status == BLOCKED
    assert "无验证规格" in r.reason


def test_execution_and_validation_normal_with_full_injection(tmp_path):
    """MIR+code+spec 全注入 → 执行 PASS、验证正常（PASS 或如实 FAIL）。"""
    s = _bare_session(tmp_path)
    s.executor_impl.shared["external_model_irs"] = {"Q001": mir("Q001", "M-Q001")}
    s.executor_impl.shared["external_code"] = {"Q001": CODE}
    s.executor_impl.shared["validation_specs"] = {"Q001": validation_spec()}
    _setup_executable(s)
    er = s.executor_impl.do_model_execution("model_execution")
    assert er.status == PASS, er.reason
    vr = s.executor_impl.do_model_validation("model_validation")
    assert vr.status in (PASS, "fail"), vr.reason
