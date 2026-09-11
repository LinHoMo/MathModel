#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADR-0015：legacy_unverified 豁免必须由 registry 实例显式开启。

缺口：`_check_exec_auth` 原先直接读 payload 的 `legacy_unverified` 并短路 token
校验——豁免写在**被检查的数据**里，任何能构造 artifact data 的代码都能自授权
绕过来源鉴别，与「The Agent Is Not The State」冲突。

修复后：
  * 默认 `ArtifactRegistry(path)` —— payload 即便带 legacy_unverified 也拒绝登记；
  * `ArtifactRegistry(path, allow_legacy_unverified=True)` —— 显式开启才承认该声明；
  * 有合法 token 的 EXEC 在默认实例照常登记（正常路径不受影响）。

运行: python -m pytest tests/unit/test_registry_legacy_gate.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import pytest  # noqa: E402

from modeling_harness.runtime.artifacts.artifact import ContractError  # noqa: E402
from modeling_harness.runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from modeling_harness.runtime.execution.execution_auth import issue_token  # noqa: E402


def _reg(tmp_path, **kw) -> ArtifactRegistry:
    reg = ArtifactRegistry(tmp_path / "registry.json", **kw)
    if not reg.exists("Q001"):
        reg.create("question", artifact_id="Q001", title="Q001", activate=True)
    return reg


def _legacy_data() -> dict:
    return {"status": "success", "code_hash": "a" * 16,
            "outputs": {"x": 1.0}, "legacy_unverified": True}


def test_default_registry_rejects_payload_legacy_flag(tmp_path):
    """默认实例：payload 自带 legacy_unverified 也不得免除 token 校验。"""
    reg = _reg(tmp_path)
    with pytest.raises(ContractError):
        reg.create("execution_result", title="X", question="Q001",
                   data=_legacy_data())


def test_optin_registry_accepts_legacy_flag(tmp_path):
    """显式开启豁免的实例：承认 legacy_unverified 声明（不追溯重算）。"""
    reg = _reg(tmp_path, allow_legacy_unverified=True)
    art = reg.create("execution_result", title="X", question="Q001",
                     data=_legacy_data())
    assert art.artifact_id
    assert art.data.get("legacy_unverified") is True


def test_default_registry_accepts_valid_token(tmp_path):
    """回归：有合法 token 时默认实例照常登记（收紧不影响正常路径）。"""
    ts = "2026-09-11T00:00:00Z"
    tok = issue_token("b" * 16, "local", ts)
    reg = _reg(tmp_path)
    art = reg.create("execution_result", title="Y", question="Q001",
                     data={"status": "success", "code_hash": "b" * 16,
                           "outputs": {"x": 2.0}, "execution_token": tok,
                           "started_at": ts,
                           "provenance": {"adapter": "local"}})
    assert art.artifact_id


def test_optin_does_not_waive_missing_token_without_declaration(tmp_path):
    """开启豁免的实例也不接受「无 token 且无 legacy 声明」的 success EXEC。"""
    reg = _reg(tmp_path, allow_legacy_unverified=True)
    with pytest.raises(ContractError):
        reg.create("execution_result", title="Z", question="Q001",
                   data={"status": "success", "code_hash": "c" * 16,
                         "outputs": {"x": 3.0}})
