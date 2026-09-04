"""P1 Evidence Graph 测试：typed relations / traversal / invalidation propagation / coverage。

运行: python -m pytest tests/unit/test_evidence_graph.py -q
覆盖任务书 §36 Graph Tests: relation creation / traversal / dependency /
invalidation propagation / cycle（传播终止）。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.artifacts.registry import ArtifactRegistry
from runtime.graph.evidence_graph import (
    RELATION_TYPES, EvidenceGraph, GraphError, STRONG_RELATIONS, WEAK_RELATIONS,
    propagation_tiers,
)


@pytest.fixture
def setup(tmp_path):
    """构建典型研究链: P→Q→M(←A)→CODE/E(→R→F/C→S) + DATA。"""
    reg = ArtifactRegistry(tmp_path / "registry.json")
    reg.project = "test"
    reg.create("problem", title="problem", activate=True)
    reg.create("question", title="Q1", activate=True)
    reg.create("question", title="Q2", activate=True)
    reg.create("model", title="model", question="Q001", activate=True)
    reg.create("assumption", title="assumption", activate=True)
    reg.create("dataset", title="data", question="Q001", activate=True)
    reg.create("code", title="code", activate=True)
    reg.create("experiment", title="exp", question="Q001", activate=True)
    reg.create("result", title="result", question="Q001", activate=True)
    reg.create("figure", title="figure", activate=True)
    reg.create("claim", title="claim", question="Q001", activate=True)
    reg.create("paper_section", title="section", activate=True)

    g = EvidenceGraph(reg, path=tmp_path / "evidence_graph.json")
    edges = [
        ("P001", "motivates", "Q001"),
        ("Q001", "solved_by", "M001"),
        ("M001", "assumes", "A001"),
        ("M001", "implemented_by", "CODE001"),
        ("M001", "validated_by", "E001"),
        ("E001", "uses", "DATA001"),
        ("E001", "produces", "R001"),
        ("R001", "visualized_by", "F001"),
        ("R001", "supports", "C001"),
        ("C001", "appears_in", "S001"),
    ]
    for f, r, t in edges:
        g.add_relation(f, r, t)
    return reg, g


class TestRelations:
    def test_all_14_relation_types_defined(self):
        assert len(RELATION_TYPES) == 14

    def test_relation_added(self, setup):
        _, g = setup
        assert ("P001", "motivates", "Q001") in [
            (e["from"], e["relation"], e["to"]) for e in g.relations]

    def test_unknown_relation_rejected(self, setup):
        _, g = setup
        with pytest.raises(GraphError):
            g.add_relation("P001", "loves", "Q001")

    def test_type_mismatch_rejected(self, setup):
        _, g = setup
        # motivates 要求 problem → question
        with pytest.raises(GraphError):
            g.add_relation("M001", "motivates", "Q001")
        # uses 只允许 experiment → dataset/code
        with pytest.raises(GraphError):
            g.add_relation("M001", "uses", "DATA001")

    def test_self_loop_rejected(self, setup):
        _, g = setup
        with pytest.raises(GraphError):
            g.add_relation("M001", "derived_from", "M001")

    def test_duplicate_rejected(self, setup):
        _, g = setup
        with pytest.raises(GraphError):
            g.add_relation("Q001", "solved_by", "M001")

    def test_unknown_artifact_rejected(self, setup):
        _, g = setup
        with pytest.raises(KeyError):
            g.add_relation("M999", "implemented_by", "CODE001")

    def test_remove_relation(self, setup):
        _, g = setup
        g.remove_relation("Q001", "solved_by", "M001")
        assert not g.out_edges("Q001")
        with pytest.raises(GraphError):
            g.remove_relation("Q001", "solved_by", "M001")

    def test_registry_relations_view_synced(self, setup):
        reg, g = setup
        art = reg.get("Q001")
        outs = [r["relation"] for r in art.relations if r["from"] == "Q001"]
        ins = [r["relation"] for r in art.relations if r["to"] == "Q001"]
        assert "solved_by" in outs
        assert "motivates" in ins


class TestTraversal:
    def test_downstream_of_dataset(self, setup):
        _, g = setup
        # DATA001 的传播下游: E001 → R001 → {F001, C001} → S001
        # （CODE001 经 M001 -implemented_by-> 挂在模型下，不随数据死）
        ds = g.downstream("DATA001")
        assert ds == {"E001", "R001", "F001", "C001", "S001"}

    def test_upstream_of_section(self, setup):
        _, g = setup
        # S001 的传播上游: C001 ← R001 ← E001 ← {M001, DATA001} ← Q001 ← P001
        # A001 经 assumes 反向（reval 档）也是上游（假设死 → 模型需复查）
        ups = g.upstream("S001")
        assert ups == {"C001", "R001", "E001", "M001", "DATA001", "Q001",
                       "P001", "A001"}
        # F001（图表是结果下游）不在上游
        assert "F001" not in ups
        assert "CODE001" not in ups

    def test_bidirectional_pair_no_infinite_loop(self, setup):
        # tests / validated_by 构成双向对，遍历必须终止（cycle 防护）
        reg, g = setup
        g.add_relation("E001", "tests", "M001")   # 与 M001 -validated_by-> E001 成对
        assert g.downstream("M001")  # 不挂起即通过
        assert g.upstream("E001")

    def test_strong_parents(self, setup):
        _, g = setup
        # R001 的 kill 级支撑: E001（produces）
        assert set(g.killer_supports("R001")) == {"E001"}
        # E001 的 kill 级支撑: M001（validated_by）+ DATA001（uses 反向）
        assert set(g.killer_supports("E001")) == {"M001", "DATA001"}

    def test_evidence_chain_of_claim(self, setup):
        _, g = setup
        chain = g.evidence_chain("C001")
        rels = {(e["from"], e["relation"]) for e in chain}
        assert ("R001", "supports") in rels
        assert ("E001", "produces") in rels
        assert ("M001", "validated_by") in rels


class TestInvalidation:
    """传播语义: kill 边全支撑死亡才判死；部分死亡 / reval 边 → requires_revalidation。"""

    def test_conservative_chain_with_live_model(self, setup):
        """数据失效，但模型（E001 的另一 kill 支撑）仍活着 → 全链保守判复查。"""
        reg, g = setup
        report = g.invalidate("DATA001", reason="数据源勘误")
        # E001 的 kill 支撑 = {M001(活), DATA001(死)} → 只需复查
        assert "E001" in report["requires_revalidation"]
        assert "E001" not in report["invalidated"]
        # 下游沿 reval 来源继续传播 reval
        for aid in ("R001", "F001", "C001", "S001"):
            assert aid in report["requires_revalidation"], aid
        # 无关 Artifact 不受影响
        assert "Q002" in report["unaffected"]
        assert "A001" in report["unaffected"]   # assumes 不正向传播
        # Registry contract 已写回
        assert reg.get("E001").status != "invalidated"
        assert reg.get("E001").invalidation["status"] == "requires_revalidation"
        assert reg.get("S001").invalidation["invalidated_by"] == "DATA001"

    def test_canonical_linear_chain(self, tmp_path):
        """任务书 §7 典型链: DATA → E → R → C → S（单支撑链，全链判死）。"""
        reg = ArtifactRegistry(tmp_path / "r.json")
        reg.project = "t"
        reg.create("dataset", title="D003", activate=True)
        reg.create("question", title="Q1", activate=True)
        reg.create("experiment", title="E017", question="Q001", activate=True)
        reg.create("result", title="R021", question="Q001", activate=True)
        reg.create("claim", title="C008", question="Q001", activate=True)
        reg.create("paper_section", title="S004", activate=True)
        g = EvidenceGraph(reg, path=tmp_path / "g.json")
        g.add_relation("E001", "uses", "DATA001")
        g.add_relation("E001", "produces", "R001")
        g.add_relation("R001", "supports", "C001")
        g.add_relation("C001", "appears_in", "S001")

        report = g.invalidate("DATA001", reason="数据源勘误")
        # kill 边 + 单支撑全死 → 判死（报告按 ID 排序输出）
        assert report["invalidated"] == ["C001", "DATA001", "E001", "R001"]
        # appears_in 是 reval 边 → 章节只需复查
        assert report["requires_revalidation"] == ["S001"]
        # Registry 写回
        assert reg.get("E001").status == "invalidated"
        assert reg.get("R001").status == "invalidated"
        assert reg.get("C001").status == "invalidated"
        assert reg.get("S001").status != "invalidated"
        assert reg.get("S001").invalidation["status"] == "requires_revalidation"

    def test_root_marked_invalidated(self, setup):
        reg, g = setup
        g.invalidate("DATA001", reason="x")
        assert reg.get("DATA001").status == "invalidated"

    def test_model_invalidation_hits_model_chain(self, setup):
        reg, g = setup
        report = g.invalidate("M001", reason="模型重推导")
        # E001 的 kill 支撑 = {M001(死), DATA001(活)} → 保守判复查
        assert "E001" in report["requires_revalidation"]
        assert "E001" not in report["invalidated"]
        # 假设是 M 的 assumes 指向（不正向传播），代码经 implemented_by 判死
        assert "A001" in report["unaffected"]
        assert "CODE001" in report["invalidated"]

    def test_partial_evidence_gives_requires_revalidation(self, tmp_path):
        """Claim 有两条支撑，只死一条 → requires_revalidation 而非 invalidated。"""
        reg = ArtifactRegistry(tmp_path / "r.json")
        reg.project = "t"
        reg.create("result", title="r1", activate=True)
        reg.create("result", title="r2", activate=True)
        reg.create("claim", title="c1", activate=True)
        reg.create("experiment", title="e1", activate=True)
        reg.create("experiment", title="e2", activate=True)
        g = EvidenceGraph(reg, path=tmp_path / "g.json")
        g.add_relation("E001", "produces", "R001")
        g.add_relation("E002", "produces", "R002")
        g.add_relation("R001", "supports", "C001")
        g.add_relation("R002", "supports", "C001")
        g.invalidate("E001", reason="实验配置错误")
        # C001 的强上游 R002 仍活着 → 只需复查
        c = reg.get("C001")
        assert c.status != "invalidated"
        assert c.invalidation["status"] == "requires_revalidation"
        assert reg.get("R001").status == "invalidated"

    def test_dirty_same_question(self, setup):
        reg, g = setup
        # Q001 名下放一个与 DATA001 无边关系的旁支 artifact
        reg.create("assumption", title="旁支假设", question="Q001", activate=True)
        report = g.invalidate("DATA001", reason="x")
        # A002 与死链无直接边 → 同问旁染 dirty
        assert "A002" in report["dirty"]
        assert "A002" not in report["invalidated"]

    def test_unaffected_stays_clean(self, setup):
        reg, g = setup
        report = g.invalidate("DATA001", reason="x")
        for aid in report["unaffected"]:
            assert not reg.get(aid).invalidation, aid

    def test_terminal_artifacts_skipped(self, setup):
        reg, g = setup
        reg.deprecate("S001", reason="章节废弃")
        report = g.invalidate("DATA001", reason="x")
        assert "S001" not in report["requires_revalidation"]
        assert "S001" not in report["invalidated"]


class TestCoverage:
    def test_coverage_full(self, setup):
        _, g = setup
        cov = g.coverage()
        assert cov["claims_total"] == 1
        assert cov["claims_supported"] == 1
        assert cov["coverage_ratio"] == 1.0

    def test_coverage_empty(self, tmp_path):
        reg = ArtifactRegistry(tmp_path / "r.json")
        g = EvidenceGraph(reg, path=tmp_path / "g.json")
        assert g.coverage()["coverage_ratio"] is None


class TestPersistence:
    def test_save_load_roundtrip(self, setup):
        reg, g = setup
        g.save()
        assert g.graph_version == 1
        g.add_relation("E001", "tests", "M001")
        g.save()
        g2 = EvidenceGraph(reg, path=g.path)
        assert g2.graph_version == 2
        assert len(g2.relations) == len(g.relations)

    def test_version_incompatible_rejected(self, setup):
        reg, g = setup
        g.save()
        import json
        raw = json.loads(g.path.read_text(encoding="utf-8"))
        raw["graph_schema_version"] = 2
        g.path.write_text(json.dumps(raw), encoding="utf-8")
        with pytest.raises(GraphError):
            EvidenceGraph(reg, path=g.path)


class TestIntegrity:
    def test_integrity_clean(self, setup):
        _, g = setup
        assert g.integrity_check() == []

    def test_integrity_detects_dangling(self, setup):
        reg, g = setup
        g.relations.append({"from": "M999", "relation": "uses", "to": "DATA001", "at": ""})
        problems = g.integrity_check()
        assert any("悬空" in p for p in problems)

    def test_integrity_detects_type_mismatch(self, setup):
        reg, g = setup
        g.relations.append({"from": "M001", "relation": "motivates", "to": "Q001", "at": ""})
        problems = g.integrity_check()
        assert any("类型不匹配" in p for p in problems)
