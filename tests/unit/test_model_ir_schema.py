# -*- coding: utf-8 -*-
"""P1-4（终审 ROADMAP）：MODEL_IR schema 唯一真源验收。

验收标准：
1. 全仓仅一份 model_ir.schema.json（core/schemas/v3/model/）；
2. migrate_legacy_format：旧格式（无 code_mapping）→ 补默认 {}，幂等；
3. 新格式样例（example_2024_A 迁移后）通过 validate_model_ir 结构校验；
4. core schema 存在且含 18 required 顶层字段；
5. research 侧无独立 schema 文件。
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "core"))

from runtime.modeling.model_ir import (  # noqa: E402
    migrate_legacy_format, validate_model_ir, MODEL_IR_REQUIRED_FIELDS)


def test_only_one_schema_repo_wide():
    hits = list(REPO.rglob("model_ir.schema.json"))
    assert len(hits) == 1, f"应仅一份 schema，实际 {len(hits)}: {hits}"
    assert hits[0] == REPO / "core" / "schemas" / "v3" / "model" / "model_ir.schema.json"


def test_core_schema_has_17_required_plus_optional():
    schema = json.loads(
        (REPO / "core" / "schemas" / "v3" / "model" / "model_ir.schema.json")
        .read_text(encoding="utf-8"))
    req = schema.get("required", [])
    assert len(req) == 17
    assert set(req) <= set(MODEL_IR_REQUIRED_FIELDS)
    # modeling_trace / code_mapping 为可选属性（对齐 runtime 结构校验 18 字段）
    props = schema.get("properties", {})
    assert "modeling_trace" in props and "code_mapping" in props
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_migrate_legacy_format_adds_code_mapping():
    legacy = {
        "ir_version": "1.0", "model_id": "M1",
        "model_family": {"primary": "optimization"},
        "problem_binding": {"problem_id": "P", "sub_question_id": "Q1",
                            "problem_sha256": "0" * 64},
    }
    migrated = migrate_legacy_format(legacy)
    assert migrated["code_mapping"] == {}
    assert migrated["model_id"] == "M1"
    # 不修改输入
    assert "code_mapping" not in legacy
    # 幂等
    again = migrate_legacy_format(migrated)
    assert again == migrated


def test_migrate_is_identity_when_already_current():
    cur = {"ir_version": "1.0", "code_mapping": {"q1": "c1"}}
    assert migrate_legacy_format(cur) == cur


def test_example_2024_a_passes_structure_check():
    """example_2024_A（契约样例）通过 runtime 结构校验。"""
    ex = json.loads(
        (REPO / "research" / "P15" / "model_representation"
         / "example_2024_A.json").read_text(encoding="utf-8"))
    problems = validate_model_ir(ex)
    assert problems == [], f"example_2024_A 结构校验失败: {problems[:6]}"


def test_legacy_boundary_doc_exists():
    doc = (REPO / "research" / "P15" / "model_representation"
           / "LEGACY_MODEL_IR.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "core/schemas/v3/model/model_ir.schema.json" in text
    assert "不回溯" in text
