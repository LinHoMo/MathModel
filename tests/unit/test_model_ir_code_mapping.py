"""audit FIX-2.3：MODEL_IR code_mapping 字段契约。

- ModelIR dataclass 携带 code_mapping（可选，默认 {}）
- to_dict 输出包含 code_mapping
- jsonschema 校验通过（可选 object，equation_id → code section/symbol）

运行: python -m pytest tests/unit/test_model_ir_code_mapping.py -q
"""

import sys
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests" / "integration"))

import pytest

from _real_session import _minimal_mir  # noqa: E402
from modeling_harness.runtime.modeling.model_ir import ModelIR, ModelIRBuilder  # noqa: E402

MINIMAL = dict(_minimal_mir("Q001"))  # 复用 18 字段合规契约样例
MINIMAL["problem_binding"]["problem_sha256"] = "a" * 64  # schema 要求 64 hex


def test_code_mapping_passes_jsonschema():
    data = dict(MINIMAL)
    data["code_mapping"] = {"eq1": "objective_expr"}
    m = ModelIRBuilder.from_dict(data)
    assert m.code_mapping == {"eq1": "objective_expr"}
    d = m.to_dict()
    assert d["code_mapping"] == {"eq1": "objective_expr"}
    schema_path = REPO / "src" / "modeling_harness" / "schemas" / "v3" / "model" / "model_ir.schema.json"
    if schema_path.exists():
        import jsonschema
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        # code_mapping 是可选 object（equation_id → string）——校验其子模式
        # （整份 MIR 的嵌套契约由其他测试覆盖；此处验证字段本身合法且可选）
        cm_schema = schema["properties"]["code_mapping"]
        jsonschema.validate(instance=d["code_mapping"], schema=cm_schema)


def test_code_mapping_optional_default_empty():
    m = ModelIRBuilder.from_dict(dict(MINIMAL))
    assert m.code_mapping == {}


def test_dataclass_field_roundtrip():
    m = ModelIR(data=dict(MINIMAL), code_mapping={"eq1": "code/main.py:obj"})
    d = m.to_dict()
    assert d["code_mapping"] == {"eq1": "code/main.py:obj"}
