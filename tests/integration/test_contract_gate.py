# -*- coding: utf-8 -*-
"""契约 gate 测试 v2：用已验证合规的 example_2024_A.json 作 base。"""
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SCHEMA = (_REPO / "src" / "modeling_harness" / "schemas" / "v3" / "model"
           / "model_ir.schema.json")  # P1-4 唯一真源
_EXAMPLE = (_REPO / "research" / "P15" / "model_representation"
            / "example_2024_A.json")
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))


@pytest.fixture(scope="module")
def schema():
    return json.loads(_SCHEMA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def compliant():
    return json.loads(_EXAMPLE.read_text(encoding="utf-8"))


def _mutate(base, path: list, value):
    """深拷贝并按路径替换（用于制造不合规变体）。"""
    import copy
    obj = copy.deepcopy(base)
    cur = obj
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = value
    return obj


def test_schema_accepts_compliant_mir(schema, compliant):
    import jsonschema
    jsonschema.Draft202012Validator(schema).validate(compliant)


def test_schema_rejects_missing_description(schema, compliant):
    import jsonschema
    mir = _mutate(compliant, ["model_family"], {"primary": "optimization"})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(mir)


def test_schema_rejects_pending_sha256(schema, compliant):
    """CONTRACT_DRIFT：problem_sha256 禁止 pending 占位。"""
    import jsonschema
    mir = _mutate(compliant, ["problem_binding", "problem_sha256"], "pending")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(mir)


def test_schema_rejects_old_template_shape(schema, compliant):
    """旧模板（2018_A 型）：sub_questions 数组替代 sub_question_id → 拒。"""
    import jsonschema
    mir = _mutate(compliant, ["problem_binding"], {
        "problem_id": "2018_A",
        "sub_questions": ["Q1", "Q2", "Q3"],
        "problem_sha256": "a" * 64})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(mir)


def test_schema_rejects_missing_validations_method(schema, compliant):
    import jsonschema
    mir = _mutate(compliant, ["validations", 0, "method"], None)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(mir)


def test_runner_gate_exists():
    """register gate 已注入 k003_formal_runner（未来生成被拦）。"""
    runner = (_REPO / "research" / "P15" / "experiments" / "P15-K003"
              / "k003_formal_runner.py")
    src = runner.read_text(encoding="utf-8")
    assert "_assert_mir_schema" in src
    assert "Draft202012Validator" in src
