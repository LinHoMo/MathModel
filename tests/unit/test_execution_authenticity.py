# -*- coding: utf-8 -*-
"""P0-3（终审 ROADMAP）：EXEC 来源鉴别——execution_token 验收。

验收标准（ROADMAP P0-3）：
1. 真实 adapter 产出的 ExecutionResult 携带有效 execution_token，
   registry.create 通过；
2. 伪造 EXEC（无 token / 无效 token / 空壳 hash）在登记时被拒绝；
3. 历史 EXEC（无 token）显式标记 legacy_unverified 可豁免（不追溯重算）。
"""

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "core"))

import pytest  # noqa: E402

from runtime.execution.adapters import LocalPythonAdapter, ExecutionPlan  # noqa: E402
from runtime.execution.execution_auth import issue_token, verify_token  # noqa: E402
from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402


def _make_reg():
    reg = ArtifactRegistry(Path("__tmp__") / "reg.json")
    reg.create("question", title="Q001", activate=True)
    return reg


def _exec_data(**overrides):
    """合法 EXEC 基座（真实 adapter 形态字段，code_hash 与 code 一致）。"""
    code = "print(json.dumps({'y': 3.0}))"
    data = {
        "execution_id": "exec_000001",
        "model_id": "M-0001",
        "status": "success",
        "inputs": {"x": 1},
        "outputs": {"y": 3.0},
        "stdout": '{"y": 3.0}',
        "stderr": "",
        "returncode": 0,
        "duration_ms": 12,
        "code_hash": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        "environment_hash": "b" * 64,
        "started_at": "2026-09-10T10:00:00+0800",
        "finished_at": "2026-09-10T10:00:00+0800",
        "provenance": {"adapter": "local_python"},
        "code": code,
        "environment_manifest": "{}",
    }
    data.update(overrides)
    return data


def _real_exec():
    """真实 adapter 执行的最小代码（确定性，零依赖）。"""
    plan = ExecutionPlan(
        model_id="M-0001",
        code="import json\n"
             "def solve(inputs):\n    return {'y': float(inputs['x']) + 2}\n"
             "print(json.dumps(solve({'x': 1.0})))\n",
        inputs={"x": 1.0},
        timeout_seconds=30,
    )
    return LocalPythonAdapter().execute(plan)


def test_real_adapter_exec_registers_with_token():
    """真实 adapter 产出 → 带有效 token → registry.create 通过。"""
    xr = _real_exec()
    assert xr.status == "success"
    assert xr.execution_token, "adapter 必须签发 execution_token"
    reg = _make_reg()
    art = reg.create("execution_result", title="真实执行", question="Q001",
                     data=xr.to_dict(), activate=True)
    assert art.artifact_id


def test_forged_exec_without_token_rejected():
    """伪造 EXEC（无 token）→ 登记被拒绝。"""
    reg = _make_reg()
    with pytest.raises(Exception) as ei:
        reg.create("execution_result", title="伪造", question="Q001",
                   data=_exec_data(), activate=True)
    msg = str(ei.value)
    assert "execution_token" in msg and "来源未鉴别" in msg


def test_forged_exec_with_bad_token_rejected():
    """伪造 EXEC（token 无效 HMAC）→ 登记被拒绝。"""
    reg = _make_reg()
    data = _exec_data(execution_token="0" * 64)
    with pytest.raises(Exception) as ei:
        reg.create("execution_result", title="伪造", question="Q001",
                   data=data, activate=True)
    msg = str(ei.value)
    assert "execution_token 校验失败" in msg


def test_legacy_exec_explicit_marker_allowed():
    """历史 EXEC（无 token + legacy_unverified 显式标记）→ 豁免。"""
    reg = _make_reg()
    data = _exec_data(legacy_unverified=True)
    art = reg.create("execution_result", title="历史", question="Q001",
                     data=data, activate=True)
    assert art.artifact_id


def test_issued_token_verifies_and_tamper_rejected():
    """issue_token/verify_token 正反例（常数时间比较）。"""
    ts = "2026-09-10T10:00:00+0800"
    tok = issue_token("a" * 64, "local_python", ts)
    assert verify_token("a" * 64, "local_python", ts, tok)
    assert not verify_token("b" * 64, "local_python", ts, tok)
    assert not verify_token("a" * 64, "other", ts, tok)
    assert not verify_token("a" * 64, "local_python", ts, "")
