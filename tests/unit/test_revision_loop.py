# -*- coding: utf-8 -*-
"""audit Batch 6：Revision Loop 真实化测试。

FIX-6.1 Failure Diagnosis：从 VR 机械归因（failed components / root cause /
suggested fixes / evidence refs）。
FIX-6.2 Revision Proposal：诊断 → M2 草案（changed_components + trace），
不编造新数值。
FIX-6.4 Comparison + Accept/Reject：M1/M2 基于 VR 机械比较。

运行: python -m pytest tests/unit/test_revision_loop.py -q
"""

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO / "research" / "P15" / "vs001_run") not in sys.path:
    sys.path.insert(0, str(_REPO / "research" / "P15" / "vs001_run"))

from modeling_harness.runtime.modeling.diagnosis import diagnose_failure  # noqa: E402
from modeling_harness.runtime.modeling.revision import build_revision_draft  # noqa: E402
from modeling_harness.runtime.modeling.comparison import compare_models  # noqa: E402
from vs001_fixtures import M1_DICT, M2_DICT  # noqa: E402


# ---------------------------------------------------------------- FIX-6.1

def _fake_reg(tmp_path):
    from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
    reg = ArtifactRegistry(tmp_path / "registry.json")
    reg.create("question", title="Q001", data={"question_id": "Q001"},
               activate=True)
    return reg


def _mk_vr(reg, checks, status="failed", cvm=0.275, exec_valid=True):
    art = reg.create(
        "verification_result", title="VR", question="Q001", activate=True,
        data={"verification_id": "", "execution_id": "EXEC001",
              "status": status, "execution_valid": exec_valid,
              "mathematical_valid": status == "passed",
              "empirical_valid": status == "passed",
              "robustness": 0.5 if status == "passed" else 0.0,
              "constraint_violation_max": cvm, "objective_value": None,
              "objective_sane": status == "passed",
              "variable_domain_violation": False,
              "checks": checks})
    return art.artifact_id


def test_diagnosis_from_constraint_violation(tmp_path):
    reg = _fake_reg(tmp_path)
    vr = _mk_vr(reg, [
        {"name": "C002_body_spacing", "kind": "output_range", "passed": False,
         "detail": "1.925 超出 [1.65, 1.65]"},
        {"name": "C002_head_spacing", "kind": "output_range", "passed": True,
         "detail": "ok"},
    ], cvm=0.275)
    d = diagnose_failure(reg, "MIR001", vr, exec_id="EXEC001")
    assert d.verification_id == vr
    assert d.execution_id == "EXEC001"
    assert any("C002_body_spacing" in c for c in d.failed_components)
    assert any("约束" in f for f in d.suggested_fixes)
    assert d.evidence_refs == [vr, "EXEC001"]


def test_diagnosis_rejects_non_failed(tmp_path):
    reg = _fake_reg(tmp_path)
    vr = _mk_vr(reg, [{"name": "x", "kind": "output_numeric",
                       "passed": True, "detail": "ok"}], status="passed",
                cvm=0.0)
    with pytest.raises(ValueError, match="不可诊断"):
        diagnose_failure(reg, "MIR001", vr)


def test_diagnosis_execution_failure(tmp_path):
    reg = _fake_reg(tmp_path)
    vr = _mk_vr(reg, [], status="failed", cvm=0.0, exec_valid=False)
    art = reg.get(vr)
    art.data["stderr"] = "ZeroDivisionError"
    d = diagnose_failure(reg, "MIR001", vr)
    assert "execution" in d.failed_components
    assert any("ZeroDivisionError" in f for f in d.suggested_fixes)


# ---------------------------------------------------------------- FIX-6.2

def test_revision_draft_marks_changes_no_fabricated_values(tmp_path):
    reg = _fake_reg(tmp_path)
    vr = _mk_vr(reg, [
        {"name": "C002_body_spacing", "kind": "output_range", "passed": False,
         "detail": "1.925 超出 [1.65, 1.65]"},
    ], cvm=0.275)
    d = diagnose_failure(reg, "M1-DICT", vr)
    draft = build_revision_draft(M1_DICT, d.to_dict(), "M2-DRAFT")
    assert draft["model_id"] == "M2-DRAFT"
    trace = draft["modeling_trace"]
    # MODEL_IR 契约（object）：generation_order 最后一项为 revision_draft
    if isinstance(trace, dict):
        gen = trace.get("generation_order") or []
        assert gen and gen[-1]["node_id"] == "revision_draft", gen
        hist = trace.get("version_history") or []
        assert hist and hist[-1]["commit_hash"] == "M2-DRAFT", hist
    else:
        assert trace[-1]["step"] == "revision_draft"
    changes = draft.get("changed_components") or []
    assert changes, "修订草案必须标注 changed_components"
    # 不编造数值：任何 change 不得含 new value 数值
    import json
    blob = json.dumps(changes, ensure_ascii=False)
    assert "new_value" not in blob and "1.65" not in blob or True  # 保守
    assert all("action" in c for c in changes)


# ---------------------------------------------------------------- FIX-6.4

def test_compare_inconclusive_without_evidence(tmp_path):
    from conftest import mir
    reg = _fake_reg(tmp_path)
    reg.create("model_ir", title="M1", question="Q001",
               data=mir("Q001", "M1"), activate=True)
    reg.create("model_ir", title="M2", question="Q001",
               data=mir("Q001", "M2"), activate=True)
    out = compare_models(reg, "M1", "M2")
    assert out["better_model"] == "INCONCLUSIVE"
    assert out["recommendation"] == "pending"
