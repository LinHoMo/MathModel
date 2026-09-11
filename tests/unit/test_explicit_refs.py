# -*- coding: utf-8 -*-
"""L5 显式引用契约 + L4 双级门禁 + G4 evidence_refs 对象形态（TDD，先 RED）。

判据来源：docs/architecture/MODEL_QUALITY_CRITERIA.md §2.1.2/§2.1.3（v1.2）。

设计语义（v1.2 演进，见 THEORY_FOUNDATION_REVIEW §9.1/§9.2）：
  * parameters[].used_in = [{type, ref}] 为**显式引用契约**：
    - type ∈ {equation, mechanism, objective, constraint, validation, claim, code}
    - 非 code 类型：ref 必须能在 model_ir 对应 id 集合中解析；
    - code 类型：ref（相对项目根，可带 #Lxx 锚点）必须指向真实文件且不越界；
    - 声明了 used_in 却无任一可解析引用 → 硬门禁 FAIL（声明不诚实）。
  * 双级：启发式（字符串匹配）未命中且未声明 used_in → 不再硬 FAIL，
    由 check_dead_param_scan 以 WARN 级报告（启发式不可靠，降为咨询）。
  * G4 obligations 条目支持对象形态 {"layer":"EV1","evidence_refs":[id,...]}，
    refs 必须解析到真实 model_ir id；字符串形态保留（启发式支撑）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import (  # noqa: E402
    check_parsimony_budget,
    check_dead_param_scan,
    check_evidence_obligations,
)


def _proj(tmp_path, params, mir_extra=None, code_files=None):
    proj = tmp_path / "projects" / "t"
    (proj / "artifacts" / "code").mkdir(parents=True)
    mir = {
        "model_family": "t",
        "parameters": params,
        "equations": [
            {"equation_id": "E01", "latex": "T(r,t)=R0*exp(-t/tau)"},
            {"equation_id": "E02", "latex": "Q=h*A*dT"},
        ],
        "mechanisms": [{"mechanism_id": "ME01", "governing_principle": "Fick",
                        "related_equations": ["E01"]}],
        "objectives": [{"objective_id": "O01", "expression": "min E"}],
        "constraints": [{"constraint_id": "C01", "expression": "x>=0"}],
        "validations": [{"validation_id": "V01", "type": "convergence"}],
        "claims": [{"claim_id": "CL01", "text": "结论"}],
    }
    if mir_extra:
        mir.update(mir_extra)
    (proj / "model_ir.json").write_text(
        json.dumps(mir, ensure_ascii=False), encoding="utf-8")
    (proj / "all_results.json").write_text(
        json.dumps({"summary": {}}, ensure_ascii=False), encoding="utf-8")
    for name, text in (code_files or {}).items():
        (proj / "artifacts" / "code" / name).write_text(text, encoding="utf-8")
    return tmp_path


# ---------- G5 used_in 显式契约 ----------

def test_used_in_equation_ref_resolves(tmp_path):
    """used_in 指向真实 equation_id → 硬门禁 PASS（即使启发式无命中）。"""
    p = {"parameter_id": "P01", "name": "x", "symbol": "ZZZ_UNLIKELY",
         "value": 999999.0, "source": "derived",
         "used_in": [{"type": "equation", "ref": "E02"}]}
    ok, msg = check_parsimony_budget(_proj(tmp_path, [p]))
    assert ok, msg


def test_used_in_broken_ref_fails(tmp_path):
    """used_in 指向不存在的 equation_id → 硬门禁 FAIL。"""
    p = {"parameter_id": "P01", "name": "x", "symbol": "x", "value": 1.0,
         "source": "derived",
         "used_in": [{"type": "equation", "ref": "E99"}]}
    ok, msg = check_parsimony_budget(_proj(tmp_path, [p]))
    assert not ok, msg
    assert "E99" in msg


def test_used_in_bad_type_fails(tmp_path):
    """used_in 条目的 type 不在词表 → FAIL。"""
    p = {"parameter_id": "P01", "name": "x", "symbol": "x", "value": 1.0,
         "source": "derived",
         "used_in": [{"type": "nonsense", "ref": "E01"}]}
    ok, msg = check_parsimony_budget(_proj(tmp_path, [p]))
    assert not ok, msg
    assert "nonsense" in msg


def test_used_in_code_ref_existing_file_passes(tmp_path):
    """used_in code 引用真实文件（可带 #L 锚点）→ PASS。"""
    p = {"parameter_id": "P01", "name": "x", "symbol": "ZZZ", "value": 1.0,
         "source": "derived",
         "used_in": [{"type": "code", "ref": "artifacts/code/solve.py#L3"}]}
    ok, msg = check_parsimony_budget(
        _proj(tmp_path, [p], code_files={"solve.py": "x=1\n"}))
    assert ok, msg


def test_used_in_code_ref_missing_file_fails(tmp_path):
    """used_in code 引用不存在的文件 → FAIL。"""
    p = {"parameter_id": "P01", "name": "x", "symbol": "ZZZ", "value": 1.0,
         "source": "derived",
         "used_in": [{"type": "code", "ref": "artifacts/code/ghost.py"}]}
    ok, msg = check_parsimony_budget(_proj(tmp_path, [p]))
    assert not ok, msg
    assert "ghost.py" in msg


def test_used_in_path_traversal_fails(tmp_path):
    """used_in code 引用越出项目根（../）→ FAIL。"""
    p = {"parameter_id": "P01", "name": "x", "symbol": "ZZZ", "value": 1.0,
         "source": "derived",
         "used_in": [{"type": "code", "ref": "../../../etc/passwd"}]}
    ok, msg = check_parsimony_budget(_proj(tmp_path, [p]))
    assert not ok, msg


# ---------- L4 双级：启发式未命中降 WARN ----------

def test_heuristic_dead_not_hard_fail(tmp_path):
    """未声明 used_in 且启发式未命中 → 硬门禁不再 FAIL（只报 suspect 数）。"""
    p = {"parameter_id": "P99", "name": "幽灵", "symbol": "G_ghost",
         "value": 42.0, "source": "convention"}
    ok, msg = check_parsimony_budget(_proj(tmp_path, [p]))
    assert ok, msg  # 硬门禁通过
    assert "suspect=1" in msg


def test_dead_scan_flags_heuristic_dead(tmp_path):
    """WARN 级扫描：未声明 used_in 且启发式未命中 → ok=False（渲染为 WARN）。"""
    p = {"parameter_id": "P99", "name": "幽灵", "symbol": "G_ghost",
         "value": 42.0, "source": "convention"}
    ok, msg = check_dead_param_scan(_proj(tmp_path, [p]))
    assert not ok, msg
    assert "P99" in msg


def test_dead_scan_skips_explicitly_declared(tmp_path):
    """已声明可解析 used_in 的参数不参与启发式扫描（显式契约优先）。"""
    p = {"parameter_id": "P01", "name": "x", "symbol": "ZZZ_UNLIKELY",
         "value": 999999.0, "source": "derived",
         "used_in": [{"type": "equation", "ref": "E01"}]}
    ok, msg = check_dead_param_scan(_proj(tmp_path, [p]))
    assert ok, msg


# ---------- G4 evidence_refs 对象形态 ----------

def test_object_obligation_with_resolvable_refs_passes(tmp_path):
    """对象形态义务 + 可解析 evidence_refs → PASS（无需启发式凑词）。"""
    obligs = {"Q1": [{"layer": "EV5", "evidence_refs": ["V01"]}]}
    # V01 类型 convergence 本不支撑 EV5 启发式，但显式 refs 解析即成立
    ok, msg = check_evidence_obligations(
        _proj(tmp_path, [], mir_extra={"evidence_obligations": obligs}))
    assert ok, msg


def test_object_obligation_broken_ref_fails(tmp_path):
    """对象形态义务的 evidence_refs 含不存在 id → FAIL。"""
    obligs = {"Q1": [{"layer": "EV5", "evidence_refs": ["V99"]}]}
    ok, msg = check_evidence_obligations(
        _proj(tmp_path, [], mir_extra={"evidence_obligations": obligs}))
    assert not ok, msg
    assert "V99" in msg


def test_object_obligation_empty_refs_fails(tmp_path):
    """对象形态义务 evidence_refs 为空 → FAIL（声明不诚实）。"""
    obligs = {"Q1": [{"layer": "EV5", "evidence_refs": []}]}
    ok, msg = check_evidence_obligations(
        _proj(tmp_path, [], mir_extra={"evidence_obligations": obligs}))
    assert not ok, msg


def test_mixed_str_and_object_obligations(tmp_path):
    """字符串形态与对象形态混用，均成立 → PASS。"""
    obligs = {"Q1": ["EV2", {"layer": "EV5", "evidence_refs": ["V01"]}]}
    ok, msg = check_evidence_obligations(
        _proj(tmp_path, [], mir_extra={"evidence_obligations": obligs}))
    assert ok, msg
