# -*- coding: utf-8 -*-
"""P0-2 验收：Failure Diagnosis 接入生产 DAG（validation FAIL → 诊断 + 修订草案）。

验收语义（ROADMAP P0-2）：
  * model_validation FAIL（无存活候选）→ 自动生成 diagnosis artifact
    （failed_components / root_cause / suggested_fixes）+ diagnosed_by 边
  * build_revision_draft 生成 M2 草案（revision_packages，model_id=*-REV1，
    modeling_trace 含 revision_draft 步骤、changed_components 非空）
  * VS-001 全闭环：M1 FAIL 诊断 → M2 PASS，finalize_revision 不重复诊断
    （整个闭环仅 1 个 DIAG）
  * 诊断是机械证据（root_cause 来自 constraint_violation_max），非 LLM 推断

LLM-free：MODEL_IR/CODE 由 fixtures 注入（外部 Model Constructor 产物）。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "research" / "P15" / "vs001_run"))

from vs001_driver import (  # noqa: E402
    make_session, relation_pairs, run_m1, run_m2,
)


@pytest.fixture()
def session(tmp_path):
    return make_session(tmp_path / "proj")


def _diag_artifacts(session):
    return [a for a in session.registry.list_by_type("diagnosis")]


def _diagnosed_by(session):
    return {(r["from"], r["to"]) for r in session.graph.relations
            if r["relation"] == "diagnosed_by"}


class TestFailureDiagnosisInDag:
    """P0-2 验收。"""

    def test_m1_fail_generates_diagnosis_and_draft(self, tmp_path):
        s = make_session(tmp_path / "proj")
        _, results = run_m1(s, tmp_path / "work")
        assert results["model_validation"].status == "fail"
        # 1) diagnosis artifact 已生成（含三要素）
        diags = _diag_artifacts(s)
        assert diags, "M1 FAIL 后必须有 diagnosis artifact"
        data = diags[0].data or {}
        assert data["failed_components"], "failed_components 非空"
        assert data["root_cause"], "root_cause 非空"
        assert data["suggested_fixes"], "suggested_fixes 非空"
        assert data["verification_id"], "diagnosis 必须溯源到 VR"
        # 2) diagnosed_by 边
        assert _diagnosed_by(s), "必须有 (MIR, diagnosed_by, DIAG) 边"
        # 3) 修订草案在 shared（供外部 Constructor 消费）
        pkgs = (s.executor_impl.shared.get("revision_packages") or {})
        q_pkgs = pkgs.get("Q001") or []
        assert q_pkgs, "revision_packages.Q001 必须有草案"
        pkg = q_pkgs[0]
        assert pkg["diagnosis_id"] == diags[0].artifact_id
        draft = pkg["draft"]
        assert draft["model_id"].endswith("-REV1")
        # MODEL_IR 契约：modeling_trace 为 object（generation_order/
        # version_history）——修订步骤追加在 generation_order，版本条目在
        # version_history
        mt = draft.get("modeling_trace") or {}
        assert isinstance(mt, dict), "modeling_trace 应为 object 契约形态"
        gen = [g for g in (mt.get("generation_order") or [])
               if isinstance(g, dict)]
        assert any(g.get("node_id") == "revision_draft" for g in gen), \
            "generation_order 必须含 revision_draft 步骤"
        hist = [h for h in (mt.get("version_history") or [])
                if isinstance(h, dict)]
        assert hist, "version_history 必须有修订版本条目"
        assert "revision_draft" in (hist[-1].get("change_summary") or ""), \
            "版本条目必须溯源到 revision_draft"
        assert draft.get("changed_components"), \
            "草案必须标注 changed_components（顶层）"

    def test_root_cause_mechanical_from_constraint_violation(self, tmp_path):
        """诊断来自机械证据：M1 的根因含约束违反（constraint_violation_max）。"""
        s = make_session(tmp_path / "proj")
        _, _ = run_m1(s, tmp_path / "work")
        diag = (_diag_artifacts(s))[0].data or {}
        assert "约束违反" in diag["root_cause"] or \
            any("constraint" in c for c in diag["failed_components"]), \
            f"M1 根因应含约束违反证据: {diag['root_cause']}"

    def test_revision_draft_inherits_m1_and_marks_changes(self, tmp_path):
        s = make_session(tmp_path / "proj")
        _, _ = run_m1(s, tmp_path / "work")
        pkg = (s.executor_impl.shared.get("revision_packages") or {})["Q001"][0]
        draft = pkg["draft"]
        # 继承 M1 结构字段（parameters/constraints 等仍在）
        assert draft.get("parameters") and draft.get("constraints")
        changes = draft.get("changed_components") or []
        assert changes, "changed_components 必须映射到 M1 结构组件"
        assert all(isinstance(c, dict) and c.get("component")
                   for c in changes), "变更条目需含 component 字段"

    def test_full_loop_single_diagnosis_no_duplicate(self, tmp_path):
        """VS-001 全闭环：M1 诊断（DAG 内）→ M2 PASS → finalize_revision
        不重复诊断——全闭环仅 1 个 DIAG。"""
        s = make_session(tmp_path / "proj")
        _, res1 = run_m1(s, tmp_path / "work")
        assert res1["model_validation"].status == "fail"
        # 找到 M1 的 MIR artifact id
        mir1 = None
        for a in s.registry.list_by_type("model_ir"):
            if (a.data or {}).get("model_id") == "M2024A-Q1-v1":
                mir1 = a.artifact_id
                break
        assert mir1
        _, res2 = run_m2(s, mir1, tmp_path / "work")
        assert res2["model_validation"].status == "pass"
        diags = _diag_artifacts(s)
        assert len(diags) == 1, \
            f"全闭环应仅 1 个 DIAG（DAG 内生成，finalize 去重），实际 {len(diags)}"
        # 幂等：M2 修订环重跑不新增诊断
        assert len(_diagnosed_by(s)) == 1

    def test_llm_free_boundary(self, tmp_path):
        """诊断与草案由机械逻辑生成：provenance.created_by 非 LLM。"""
        s = make_session(tmp_path / "proj")
        _, _ = run_m1(s, tmp_path / "work")
        diag = _diag_artifacts(s)[0]
        assert diag.created_by == "model_validation", \
            f"诊断由 DAG 节点生成: {diag.created_by}"
