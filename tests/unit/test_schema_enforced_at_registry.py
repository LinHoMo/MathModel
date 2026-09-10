# -*- coding: utf-8 -*-
"""audit FIX-5.4：jsonschema 实例校验接入 registry.create。

- 有 schema 的类型（model_ir/decision）登记时做实例校验，违规抛 ContractError
- decision 元数据（decision_id/question/created_by/created_at/status/
  reversible）由 registry 注入，handler 只写业务字段
- 无 schema 的类型不受影响

运行: python -m pytest tests/unit/test_schema_enforced_at_registry.py -q
"""

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from modeling_harness.runtime.artifacts.artifact import ContractError  # noqa: E402
from modeling_harness.runtime.artifacts.registry import ArtifactRegistry  # noqa: E402


@pytest.fixture
def reg(tmp_path):
    r = ArtifactRegistry(tmp_path / "registry.json")
    r.create("question", artifact_id="Q001", title="Q001", data={"question_id": "Q001",
                                             "title": "t"},
             activate=True)
    return r


def test_model_ir_schema_enforced(reg):
    """model_ir 缺 schema required 字段 → ContractError（不静默跳过）。"""
    bad = {
        "ir_version": "1.0",
        "model_id": "M-BAD",
        # 缺 model_family / problem_binding / 全部数组节
    }
    with pytest.raises(ContractError, match="model_ir 实例校验失败"):
        reg.create("model_ir", title="bad", data=bad, activate=True)


def test_decision_metadata_injected_by_registry(reg):
    """decision 元数据字段由 registry 注入，handler 只写业务字段。"""
    d = reg.create(
        "decision", title="test", question="Q001", created_by="tester",
        data={"kind": "candidate_selection", "chosen": "M1",
              "alternatives": ["M1", "M2"], "criteria": ["c1"],
              "evidence_ids": [], "reasoning": "r", "confidence": 0.5},
        activate=True)
    data = d.data or {}
    assert data["decision_id"] == d.artifact_id
    assert data["question"] == "Q001"
    assert data["created_by"] == "tester"
    assert data["status"] == "active"
    assert data["reversible"] is False
    assert data["kind"] == "candidate_selection"


def test_decision_schema_rejects_type_violation(reg):
    """decision 业务字段违反 schema 类型 → ContractError（校验真实生效）。"""
    with pytest.raises(ContractError):
        reg.create("decision", title="bad", question="Q001",
                   data={"kind": "candidate_selection",
                         "chosen": 123,   # 必须为 string
                         "alternatives": [], "criteria": [],
                         "evidence_ids": [], "reasoning": "r",
                         "confidence": 0.5},
                   activate=True)


def test_type_without_schema_unaffected(reg):
    """无 schema 的类型（如 problem）登记不受影响。"""
    art = reg.create("problem", title="P1", question="Q001",
                     data={"problem_id": "P1"}, activate=True)
    assert art.type == "problem"
    assert art.status == "active"
