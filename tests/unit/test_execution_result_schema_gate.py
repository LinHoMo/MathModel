# -*- coding: utf-8 -*-
"""FIX-1.1：execution_result data schema 门禁测试（audit P0-01 / C-001）。

原则：ExecutionResult 只能由 execution substrate 创建；Agent 直接构造的
空壳（outputs={} / code_hash="" / duration_ms=0 / 假 status / 哈希不匹配）
必须在登记时被拒绝。真实执行产物（success + 非空 outputs + 一致 code_hash）
必须通过。
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.artifacts.artifact import Artifact, ContractError
from runtime.artifacts.registry import ArtifactRegistry


def _real_data() -> dict:
    code = "def solve(inputs):\n    return {'x': 1.0}\n"
    return {
        "execution_id": "EXEC-instance-0001",
        "model_id": "M-001",
        "status": "success",
        "inputs": {},
        "outputs": {"x": 1.0},
        "stdout": "ok",
        "stderr": "",
        "returncode": 0,
        "duration_ms": 42,
        "code_hash": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        "environment_hash": "abc",
        "started_at": "2026-09-09T00:00:00Z",
        "finished_at": "2026-09-09T00:00:01Z",
        "provenance": {"reason": "real_subprocess"},
        "code": code,
        "environment_manifest": "py3.12",
    }


@pytest.fixture
def reg(tmp_path):
    return ArtifactRegistry(tmp_path / "state" / "registry.json")


def test_real_execution_result_passes(reg):
    art = reg.create("execution_result", title="真实执行",
                     data=_real_data(), activate=True)
    assert art.status == "active"
    assert reg.integrity_check() == []


def test_fake_status_rejected(reg):
    data = _real_data()
    data["status"] = "fake"
    # FIX-5.4：jsonschema 实例校验先拦截（status enum），行为等价拒绝
    with pytest.raises(ContractError, match="status"):
        reg.create("execution_result", data=data)


def test_success_with_empty_outputs_rejected(reg):
    """K003 伪造事件的核心形态：status=success 但 outputs={}。"""
    data = _real_data()
    data["outputs"] = {}
    with pytest.raises(ContractError, match="outputs 为空"):
        reg.create("execution_result", data=data)


def test_success_with_empty_code_hash_rejected(reg):
    data = _real_data()
    data["code_hash"] = ""
    with pytest.raises(ContractError, match="code_hash"):
        reg.create("execution_result", data=data)


def test_code_hash_mismatch_rejected(reg):
    data = _real_data()
    data["code_hash"] = "0" * 64
    with pytest.raises(ContractError, match="code_hash 与 code 本体不一致"):
        reg.create("execution_result", data=data)


def test_outputs_not_dict_rejected(reg):
    data = _real_data()
    data["outputs"] = "not a dict"
    # FIX-5.4：jsonschema 实例校验先拦截（outputs 必须 object）
    with pytest.raises(ContractError, match="outputs"):
        reg.create("execution_result", data=data)


def test_negative_duration_rejected(reg):
    data = _real_data()
    data["duration_ms"] = -1
    with pytest.raises(ContractError, match="duration_ms"):
        reg.create("execution_result", data=data)


def test_success_with_nonzero_returncode_rejected(reg):
    data = _real_data()
    data["returncode"] = 1
    with pytest.raises(ContractError, match="returncode"):
        reg.create("execution_result", data=data)


def test_failed_status_is_legal(reg):
    """执行失败是合法状态：failed 可以有空 outputs、无 code_hash。"""
    data = {
        "execution_id": "EXEC-instance-0002",
        "model_id": "M-002",
        "status": "failed",
        "inputs": {},
        "outputs": {},
        "stdout": "",
        "stderr": "Traceback ...",
        "returncode": 1,
        "duration_ms": 5,
        "code_hash": "",
    }
    art = reg.create("execution_result", data=data)
    assert art.data["status"] == "failed"


def test_load_rejects_fabricated_registry(tmp_path):
    """已落盘的伪造 execution_result 必须 fail-closed（from_dict 拒绝加载）。"""
    rp = tmp_path / "state" / "registry.json"
    rp.parent.mkdir(parents=True)
    fake_data = _real_data()
    fake_data["outputs"] = {}
    fake_data["code_hash"] = ""
    reg = ArtifactRegistry(rp)
    art = Artifact(artifact_id="EXEC001", type="execution_result",
                   data=fake_data)
    # 手工构造一个不含门禁的 registry.json（绕过 create 直接写盘）
    payload = {
        "registry_version": 3,
        "project": "tmp",
        "counters": {"execution_result": 1},
        "artifacts": {"EXEC001": art.to_dict()},
        "history": {},
    }
    rp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ContractError, match="outputs 为空"):
        ArtifactRegistry(rp)
