"""P4 NarrativeCritic 测试：N1-N7 检查项 / PASS-FAIL 判定。

运行: python -m pytest tests/unit/test_narrative_critic.py -q
覆盖任务书: P4 验收「judge/narrative critic 单测」之 narrative 部分。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.writing import NarrativeCritic, NarrativeReport
from runtime.writing.director import Narrative, StoryArc


# --------------------------------------------------------------- 工具

def make_outline(*, result_claims=None, sens_evidence=None, pending=None,
                 section_figures=None):
    """构造投影 dict（结构同 PaperProjection.project 产物）。"""
    return {
        "sections": [
            {"section": "问题重述与分析", "claims": [], "figures": []},
            {"section": "模型建立", "models": [], "claims": [], "figures": []},
            {"section": "结果与分析", "claims": result_claims or [],
             "figures": section_figures if section_figures is not None
             else sorted({f for c in (result_claims or [])
                          for f in c.get("figures", [])})},
            {"section": "灵敏度与稳健性", "evidence": sens_evidence or [],
             "claims": [], "figures": []},
            {"section": "结论", "claims": [], "figures": []},
        ],
        "pending_placement": pending or [],
    }


def healthy_narrative():
    return Narrative(
        problem="p",
        arcs=[StoryArc(claim_id="C001", statement="s", question="Q001",
                       evidence_ids=["R001"], status="supported")],
    )


def healthy_outline():
    return make_outline(
        result_claims=[{"claim": "C001", "statement": "s",
                        "placement": ["S001"], "figures": ["F001"],
                        "supported": True}],
        sens_evidence=["R001"],
        section_figures=["F001"],
    )


def codes(report: NarrativeReport) -> list[str]:
    return [f.code for f in report.findings]


# --------------------------------------------------------------- 基线

class TestHealthy:
    def test_pass_no_findings(self):
        report = NarrativeCritic().evaluate(healthy_narrative(), healthy_outline())
        assert report.verdict == "PASS"
        assert report.passed
        assert report.findings == []

    def test_summary(self):
        s = NarrativeCritic().evaluate(
            healthy_narrative(), healthy_outline()).summary()
        assert "[narrative-critic] PASS" in s


# --------------------------------------------------------------- FAIL 项

class TestFailConditions:
    def test_n1_no_claims(self):
        report = NarrativeCritic().evaluate(Narrative(), make_outline())
        assert report.verdict == "FAIL"
        assert codes(report) == ["N1"]

    def test_n2_dead_arc(self):
        nar = healthy_narrative()
        nar.arcs[0].status = "dead"
        nar.arcs[0].dead_evidence = ["R001"]
        report = NarrativeCritic().evaluate(nar, healthy_outline())
        assert report.verdict == "FAIL"
        assert "N2" in codes(report)
        f = next(f for f in report.findings if f.code == "N2")
        assert f.items == ["C001"]

    def test_n3_unsupported_in_results(self):
        outline = make_outline(result_claims=[
            {"claim": "C001", "statement": "s", "placement": ["S001"],
             "figures": [], "supported": False},
        ])
        report = NarrativeCritic().evaluate(healthy_narrative(), outline)
        assert report.verdict == "FAIL"
        f = next(f for f in report.findings if f.code == "N3")
        assert f.items == ["C001"]

    def test_n4_pending_placement(self):
        outline = make_outline(
            result_claims=[{"claim": "C001", "statement": "s",
                            "placement": [], "figures": [], "supported": True}],
            pending=["C001"])
        report = NarrativeCritic().evaluate(healthy_narrative(), outline)
        assert report.verdict == "FAIL"
        assert "N4" in codes(report)

    def test_n5_empty_result_section(self):
        report = NarrativeCritic().evaluate(healthy_narrative(), make_outline())
        assert report.verdict == "FAIL"
        assert "N5" in codes(report)

    def test_fail_beats_weak(self):
        """fail 与 weak 并存 → FAIL（同 evidence gate 语义）。"""
        nar = healthy_narrative()
        nar.arcs.append(StoryArc(claim_id="C002", statement="孤儿",
                                 status="unsupported"))
        outline = healthy_outline()
        outline["pending_placement"] = ["C002"]      # N4 fail
        # N7 weak: 段落级图不被任何主张引用
        outline["sections"][2]["figures"] = ["F001", "F999"]
        report = NarrativeCritic().evaluate(nar, outline)
        assert report.verdict == "FAIL"
        assert "N4" in codes(report) and "N7" in codes(report)


# --------------------------------------------------------------- WEAK 项

class TestWeakConditions:
    def test_n6_no_sensitivity_evidence(self):
        outline = healthy_outline()
        outline["sections"][3]["evidence"] = []
        report = NarrativeCritic().evaluate(healthy_narrative(), outline)
        # N6 是 weak，单独存在不改变 PASS
        assert "N6" in codes(report)
        f = next(f for f in report.findings if f.code == "N6")
        assert f.severity == "weak"
        assert report.verdict == "PASS"

    def test_n7_orphan_figure(self):
        outline = healthy_outline()
        outline["sections"][2]["figures"] = ["F001", "F002"]  # F002 无主张引用
        report = NarrativeCritic().evaluate(healthy_narrative(), outline)
        f = next(f for f in report.findings if f.code == "N7")
        assert f.severity == "weak"
        assert f.items == ["F002"]
        assert report.verdict == "PASS"


# --------------------------------------------------------------- 集成

class TestEndToEnd:
    def test_pipeline_dead_evidence_flagged(self, tmp_path):
        """真实 registry/graph → director → projection → critic 全链。"""
        from runtime.artifacts.registry import ArtifactRegistry
        from runtime.graph.evidence_graph import EvidenceGraph
        from runtime.writing import PaperProjection, ResearchDirector

        reg = ArtifactRegistry(tmp_path / "registry.json")
        reg.project = "t"
        reg.create("question", title="Q1", activate=True)
        reg.create("experiment", title="e", question="Q001", activate=True)
        reg.create("result", title="r", question="Q001", activate=True,
                   tags=["sensitivity"])
        reg.create("claim", title="c", question="Q001", activate=True,
                   data={"statement": "s"})
        g = EvidenceGraph(reg, path=tmp_path / "g.json")
        for f, r, t in [("E001", "produces", "R001"), ("R001", "supports", "C001")]:
            g.add_relation(f, r, t)
        reg.invalidate("R001", "勘误")

        nar = ResearchDirector(reg, g).build()
        outline = PaperProjection(reg, g).project(nar)
        report = NarrativeCritic().evaluate(nar, outline)
        assert report.verdict == "FAIL"
        # N2 语义已精化：director 保留死弧供审计，投影正确排除 → 不再误报 N2；
        # 死主张被剔除后结果章节空 → N5 FAIL（需重跑实验补新主张）
        assert "N5" in codes(report)
        assert outline["dead_claims_excluded"] == ["C001"]
