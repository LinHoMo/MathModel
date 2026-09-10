# -*- coding: utf-8 -*-
"""P1-2 验收：自动修订闭环（V3 主 DAG 节点内，LLM-free）。

ROADMAP P1-2（Revision Loop 接入主 DAG，以节点内闭环实现——引擎
on_fail 回退语义专用于"重做前置"，不适合 revision 推进链；验收语义不变）：

  * M1 → model_validation FAIL（真实数值判 FAIL，VS-001 场景）
  * 无外部修订注入 → FAIL 如实（revision_blocked，等待外部 Constructor
    消费 revision_draft 后注入 revision_bundles 再重跑；禁止假装修订完成）
  * 外部注入 revision_bundles → 同一 model_validation 节点执行内自动闭环：
    M2 注册（revision_of 谱系边由 runtime 生成）→ M1 收口（supersedes 边
    由 runtime 生成，非手工 add_relation）→ M2 重跑 EXEC/R/VR → PASS
  * M2 重跑仍有失败 → FAIL 如实传播（revision_failed，不假装闭环完成）

LLM-free：MODEL_IR/CODE 由 fixtures 注入（外部 Model Constructor 产物）。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "research" / "P15" / "vs001_run"))

from vs001_driver import (  # noqa: E402
    LOOP_NODES,
    inject,
    make_session,
    step_all,
)
from vs001_fixtures import (  # noqa: E402
    C1_CODE,
    C2_CODE,
    M1_DICT,
    M2_DICT,
    OUTPUT_MAPPING,
    VALIDATION_SPEC,
)


def _inject_revision(session, mir2: dict, code: str | None):
    """注入外部修订包（P1-2：消费 revision_draft 后的 M2 产物）。"""
    session.executor_impl.shared["revision_bundles"] = {
        "Q001": {"model_ir": mir2, "code": code},
    }


def _model_irs(session):
    return [a for a in session.registry.list_by_type("model_ir")]


def _relations(session, relation):
    return {(r["from"], r["to"]) for r in session.graph.relations
            if r["relation"] == relation}


class TestAutoRevisionLoopInDag:
    """P1-2 自动修订闭环验收。"""

    def test_m1_fail_without_bundle_is_fail_not_fake(self, tmp_path):
        """无修订注入 → FAIL 如实（revision_blocked），不假装闭环完成。"""
        s = make_session(tmp_path / "proj")
        inject(s, M1_DICT, C1_CODE, tmp_path / "work")
        results = step_all(s)
        r = results["model_validation"]
        assert r.status == "fail"
        out = r.outputs or {}
        assert out.get("revision_blocked") == ["Q001"], \
            "无修订注入必须如实等待外部（revision_blocked），禁止假装修订完成"
        assert out.get("revision_packages", 0) >= 1, "必须有修订草案供外部消费"
        # M1 未被覆盖，谱系仍完整
        mirs = _model_irs(s)
        assert len(mirs) == 1, "无修订注入时不得生成 M2"

    def test_auto_revision_loop_m1_fail_m2_pass(self, tmp_path):
        """注入修订包 → 同一节点内 M1→FAIL→M2→PASS 自动闭环。"""
        s = make_session(tmp_path / "proj")
        inject(s, M1_DICT, C1_CODE, tmp_path / "work")
        # 步进到 model_validation 前（model_execution 之后注入修订包）
        pre = [n for n in LOOP_NODES if n != "model_validation"]
        step_all(s, nodes=pre)
        m1 = [a for a in _model_irs(s) if a.status not in ("superseded",)]
        assert m1, "M1 已注册"
        m1_id = m1[0].artifact_id
        m2 = dict(M2_DICT)
        m2["revision_of"] = m1_id
        _inject_revision(s, m2, C2_CODE)
        r = s.engine.step("model_validation")
        assert r.status == "pass", f"自动修订闭环必须 PASS: {r.reason}"
        # 1) revision_of / supersedes 谱系边由 runtime 生成
        assert _relations(s, "revision_of"), "revision_of 边必须由 runtime 生成"
        assert _relations(s, "supersedes"), "supersedes 边必须由 runtime 生成"
        # 2) M1 → superseded，M2 活跃
        by_id = {a.artifact_id: a for a in _model_irs(s)}
        assert by_id[m1_id].status == "superseded", "M1 必须被收口（superseded）"
        m2s = [a for a in _model_irs(s) if a.artifact_id != m1_id]
        assert m2s and m2s[0].status not in ("superseded",), "M2 活跃"
        # 3) M2 的 VR passed（真实数值验证通过）
        vrs = [a for a in s.registry.list_by_type("verification_result")]
        assert any((a.data or {}).get("status") == "passed" for a in vrs), \
            "M2 必须产出 passed VR"
        # 4) M2 有独立 EXEC/R（不覆盖 M1 谱系）
        execs = [a for a in s.registry.list_by_type("execution_result")]
        assert len(execs) >= 2, "M1/M2 各自独立 EXEC 谱系"

    def test_m2_failure_propagates_honestly(self, tmp_path):
        """修订 M2 重跑仍有失败 → FAIL 如实（revision_failed）。"""
        s = make_session(tmp_path / "proj")
        inject(s, M1_DICT, C1_CODE, tmp_path / "work")
        pre = [n for n in LOOP_NODES if n != "model_validation"]
        step_all(s, nodes=pre)
        m1 = [a for a in _model_irs(s)][0].artifact_id
        bad = dict(M2_DICT)
        bad["model_id"] = "M-BAD"
        bad["revision_of"] = m1
        bad["parameters"] = list(M1_DICT["parameters"])  # 回退 ρ=1.5 仍不稳定
        _inject_revision(s, bad, C2_CODE)
        r = s.engine.step("model_validation")
        assert r.status == "fail"
        out = r.outputs or {}
        assert out.get("revision_failed") == ["Q001"], \
            "M2 重跑失败必须如实 FAIL（revision_failed），禁止假装闭环"
