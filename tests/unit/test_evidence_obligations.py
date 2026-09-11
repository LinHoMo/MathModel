# -*- coding: utf-8 -*-
"""G4 证据义务矩阵门禁（check_evidence_obligations）语义测试。

判据来源：docs/architecture/MODEL_QUALITY_CRITERIA.md §2.2（G4，v1.1）。

规则：
  * model_ir.json 顶层 `evidence_obligations`（可选，opt-in 契约）为
    {子问题: [证据层, ...]}；
  * 证据层 ∈ {EV1 数学必然, EV2 机制保真, EV3 数据拟合, EV4 样本外预测, EV5 决策效用}
    （前缀 EV 规避既有 Evidence Gate E1–E9 编号冲突）；
  * 每个声明的层必须在该实例中有机械可查的证据支撑（实例级检查，v1 粒度）；
  * 未声明 obligations 的实例不判失败（接口是 opt-in，实例合规另行声明）。

这些测试先于实现（RED）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import check_evidence_obligations  # noqa: E402


def _proj(tmp_path, mir_extra=None):
    proj = tmp_path / "projects" / "t"
    proj.mkdir(parents=True)
    mir = {
        "model_family": "t",
        "equations": [
            {"equation_id": "E01", "latex": "x=1",
             "derivation_trace": "能量守恒 + Fourier 定律"},
        ],
        "mechanisms": [
            {"mechanism_id": "ME01", "governing_principle": "Fick 定律",
             "related_equations": ["E01"]},
        ],
        "validations": [
            {"validation_id": "V01", "type": "convergence"},
        ],
        "claims": [{"claim_id": "CL01", "text": "结论 X（附件2 实测对照）"}],
    }
    if mir_extra:
        mir.update(mir_extra)
    (proj / "model_ir.json").write_text(
        json.dumps(mir, ensure_ascii=False), encoding="utf-8")
    (proj / "all_results.json").write_text(
        json.dumps({"calibration_sensitivity": {"P08": {
            "varied": {"T": [1.0, 2.0, 3.0]}, "outcomes": [1, 2, 3]}}},
            ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_no_obligations_passes(tmp_path):
    """未声明 evidence_obligations → PASS（opt-in 契约不强制）。"""
    ok, msg = check_evidence_obligations(_proj(tmp_path))
    assert ok, msg


def test_all_layers_backed_passes(tmp_path):
    """EV1–EV5 全声明且有证据 → PASS。"""
    obligs = {"Q1": ["EV1", "EV2", "EV3", "EV4", "EV5"]}
    mir = {"evidence_obligations": obligs,
           "claims": [{"claim_id": "CL01", "text": "数据驱动边界 + 附件2 实测对照"}]}
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir))
    assert ok, msg


def test_unbacked_EV1_fails(tmp_path):
    """声明 EV1 但实例既无守恒/不变量推导词、也无 invariant 类验证 → FAIL。"""
    mir = {"evidence_obligations": {"Q1": ["EV1"]},
           "equations": [{"equation_id": "E01", "latex": "y=ax+b",
                          "derivation_trace": "经验拟合"}]}
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir))
    assert not ok, msg
    assert "EV1" in msg


def test_unbacked_EV2_fails(tmp_path):
    """声明 EV2 但无任何含 governing_principle+related_equations 的机制 → FAIL。"""
    mir = {"evidence_obligations": {"Q1": ["EV2"]},
           "mechanisms": [{"mechanism_id": "ME01",
                           "governing_principle": "",
                           "related_equations": []}]}
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir))
    assert not ok, msg
    assert "EV2" in msg


def test_unbacked_EV3_fails(tmp_path):
    """声明 EV3 但既无拟合类验证、也无结果拟合指标、claims 也无数据驱动/拟合词 → FAIL。"""
    mir = {"evidence_obligations": {"Q1": ["EV3"]},
           "claims": [{"claim_id": "CL01", "text": "纯机理推导结论"}]}
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir))
    assert not ok, msg
    assert "EV3" in msg


def test_unbacked_EV4_fails(tmp_path):
    """声明 EV4 但既无样本外/反事实验证、claims 也无实测对照 → FAIL。"""
    mir = {"evidence_obligations": {"Q1": ["EV4"]},
           "claims": [{"claim_id": "CL01", "text": "纯解析结论"}]}
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir))
    assert not ok, msg
    assert "EV4" in msg


def test_unbacked_EV5_fails(tmp_path):
    """声明 EV5 但无 sensitivity/robustness 验证、结果也无敏感性键 → FAIL。"""
    mir = {"evidence_obligations": {"Q1": ["EV5"]},
           "validations": [{"validation_id": "V01", "type": "convergence"}]}
    proj = tmp_path / "projects" / "t"
    proj.mkdir(parents=True)
    (proj / "model_ir.json").write_text(
        json.dumps({"model_family": "t", "equations": [],
                    "mechanisms": [], "validations": mir["validations"],
                    "claims": [], "evidence_obligations": mir["evidence_obligations"]},
                   ensure_ascii=False), encoding="utf-8")
    (proj / "all_results.json").write_text(
        json.dumps({"summary": {"x": 1}}, ensure_ascii=False), encoding="utf-8")
    ok, msg = check_evidence_obligations(tmp_path)
    assert not ok, msg
    assert "EV5" in msg


def test_invalid_layer_fails(tmp_path):
    """声明非法证据层（EV9）→ FAIL。"""
    mir = {"evidence_obligations": {"Q1": ["EV9"]}}
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir))
    assert not ok, msg
    assert "EV9" in msg


def test_obligations_not_dict_fails(tmp_path):
    """evidence_obligations 非对象（如列表）→ FAIL。"""
    mir = {"evidence_obligations": ["EV1"]}
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir))
    assert not ok, msg


def test_break_one_layer_fails_others_pass():
    """反向验收模式：5 层全声明，抽掉 EV3 证据后只有 EV3 报 FAIL。"""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        proj = root / "projects" / "t"
        proj.mkdir(parents=True)
        mir = {
            "model_family": "t",
            "equations": [{"equation_id": "E01", "latex": "x=1",
                           "derivation_trace": "能量守恒"}],
            "mechanisms": [{"mechanism_id": "ME01", "governing_principle": "Fick",
                            "related_equations": ["E01"]}],
            "validations": [{"validation_id": "V01", "type": "sensitivity"}],
            "claims": [{"claim_id": "CL01", "text": "附件2 实测对照（纯机理，无经验标定）"}],
            "evidence_obligations": {"Q1": ["EV1", "EV2", "EV3", "EV4", "EV5"]},
        }
        (proj / "model_ir.json").write_text(
            json.dumps(mir, ensure_ascii=False), encoding="utf-8")
        (proj / "all_results.json").write_text(
            json.dumps({"summary": {}}, ensure_ascii=False), encoding="utf-8")
        ok, msg = check_evidence_obligations(root)
        # EV3 无拟合证据 → 应 FAIL 且点名 EV3
        assert not ok, msg
        assert "EV3" in msg


# ---- §9.4 子问题粒度 + 证据独立性 ----

def test_subquestion_scope_fails_when_evidence_tagged_elsewhere(tmp_path):
    """§9.4：开启子问题作用域 opt-in 后，Q2 声明 EV1 但唯一 EV1 证据绑定在
    Q1 ⇒ 子问题级 FAIL（证据不跨子问题复用）。"""
    mir = {
        "model_family": "t",
        "equations": [{"equation_id": "E01", "latex": "x=1",
                       "derivation_trace": "能量守恒",
                       "sub_question_binding": ["Q1"]}],
        "mechanisms": [],
        "validations": [],
        "claims": [{"claim_id": "CL01", "text": "结论"}],
        "evidence_obligations_subquestion_scope": True,
        "evidence_obligations": {"Q2": ["EV1"]},
    }
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir_extra=mir))
    assert not ok, msg
    assert "Q2" in msg and "EV1" in msg


def test_subquestion_scope_passes_when_evidence_tagged_for_qid(tmp_path):
    """§9.4：开启 opt-in 后，Q2 声明 EV1 且守恒推导方程绑定 Q2 ⇒ 子问题级 PASS。"""
    mir = {
        "model_family": "t",
        "equations": [{"equation_id": "E01", "latex": "x=1",
                       "derivation_trace": "能量守恒",
                       "sub_question_binding": ["Q2"]}],
        "mechanisms": [],
        "validations": [],
        "claims": [{"claim_id": "CL01", "text": "结论"}],
        "evidence_obligations_subquestion_scope": True,
        "evidence_obligations": {"Q2": ["EV1"]},
    }
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir_extra=mir))
    assert ok, msg


def test_subquestion_scope_optin_required_for_strict(tmp_path):
    """§9.4 向后兼容：未开启 opt-in 时，子问题键按 v1 实例级检查——

    Q2 声明 EV1，但 EV1 证据（守恒推导）仅绑定在 Q1；未 opt-in 时不应
    因子问题作用域误伤（保护按实例级 G4 撰写的历史合规实例）。
    """
    mir = {
        "model_family": "t",
        "equations": [{"equation_id": "E01", "latex": "x=1",
                       "derivation_trace": "能量守恒",
                       "sub_question_binding": ["Q1"]}],
        "mechanisms": [],
        "validations": [],
        "claims": [{"claim_id": "CL01", "text": "结论"}],
        # 注意：未声明 evidence_obligations_subquestion_scope
        "evidence_obligations": {"Q2": ["EV1"]},
    }
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir_extra=mir))
    assert ok, msg


def test_evidence_independence_note_nonblocking(tmp_path):
    """§9.4：对象形态下同一 evidence_ref 支撑多层义务 ⇒ 非阻塞提示（仍 PASS）。"""
    mir = {
        "model_family": "t",
        "equations": [{"equation_id": "E01", "latex": "x=1",
                       "derivation_trace": "能量守恒"}],
        "mechanisms": [{"mechanism_id": "ME01", "governing_principle": "Fick",
                        "related_equations": ["E01"]}],
        "validations": [{"validation_id": "V01", "type": "convergence"}],
        "claims": [{"claim_id": "CL01", "text": "附件2 实测对照"}],
        "evidence_obligations": {
            "Q1": [
                {"layer": "EV1", "evidence_refs": ["V01"]},
                {"layer": "EV2", "evidence_refs": ["V01"]},  # 复用 V01
            ]
        },
    }
    ok, msg = check_evidence_obligations(_proj(tmp_path, mir_extra=mir))
    assert ok, msg
    assert "独立性" in msg
