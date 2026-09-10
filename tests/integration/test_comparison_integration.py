# -*- coding: utf-8 -*-
"""P1-3 验收：Model Comparison 接入生产 revision flow。

复用 vs001_driver（M1 FAIL → M2 PASS 真实闭环）。验收语义：
  * M1 FAIL → M2 PASS 时（revision_of 谱系）验证后自动机械比较
  * 比较结果包含 better_model / recommendation / deltas
  * decision artifact 进入 registry + compared_with/supported_by 边
  * 无修订谱系时不产生比较决策
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "research" / "P15" / "vs001_run"))

from vs001_driver import make_session, run_m1, run_m2  # noqa: E402


@pytest.fixture()
def session(tmp_path):
    return make_session(tmp_path / "proj")


def _comparisons(session):
    return [d for d in session.registry.list_by_type("decision")
            if (d.data or {}).get("decision_type") == "model_comparison"]


class TestModelComparisonIntegration:
    """P1-3 验收。"""

    def test_no_revision_no_comparison(self, session, tmp_path):
        """M1 单独跑（无 M2 谱系）→ 不产生比较决策。"""
        run_m1(session, tmp_path / "exec")
        assert _comparisons(session) == [], "无修订谱系不应有比较决策"

    def test_m1_fail_m2_pass_auto_compare(self, session, tmp_path):
        """M1 FAIL → M2 PASS：自动比较，better=M2/accept。"""
        run_m1(session, tmp_path / "exec")
        mir1 = [a.artifact_id for a in session.registry.list_by_type("model_ir")][0]
        run_m2(session, mir1, tmp_path / "exec")
        cmps = _comparisons(session)
        assert cmps, "修订谱系必须产生比较决策"
        d = cmps[0].data or {}
        # better_model 是 registry artifact id（系统事实真源）；
        # 对应业务模型是 M2024A-Q1-v2（修订环里 PASS 的那一个）
        assert d["better_model"].startswith("MIR"), d
        assert d["recommendation"] == "accept", d
        m2 = session.registry.get(d["better_model"])
        assert m2 is not None and m2.data["model_id"] == "M2024A-Q1-v2"
        assert "deltas" in d and "reasoning" in d
        assert d.get("advisory") is True, "比较决策是 advisory，不自动改状态"

    def test_comparison_lineage_edges(self, session, tmp_path):
        """revision_of / compared_with / supported_by 边真实登记。"""
        run_m1(session, tmp_path / "exec")
        mir1 = [a.artifact_id for a in session.registry.list_by_type("model_ir")][0]
        run_m2(session, mir1, tmp_path / "exec")
        rels = {(r["from"], r["relation"], r["to"])
                for r in session.graph.relations}
        assert any(rel[1] == "revision_of" and rel[0].startswith("MIR")
                   for rel in rels), "M2 revision_of M1 边必须存在"
        assert any(rel[1] == "compared_with" and rel[0].startswith("MIR")
                   for rel in rels), "compared_with 边必须存在"
        assert any(rel[1] == "based_on" and rel[0].startswith("D")
                   for rel in rels), "decision based_on 边必须存在"
