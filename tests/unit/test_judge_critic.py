"""P4 JudgeCritic 测试：PASS / WEAK / FAIL / UNKNOWN 四态 + 风险聚合。

运行: python -m pytest tests/unit/test_judge_critic.py -q
覆盖任务书: P4 验收「judge/narrative critic 单测」之 judge 部分。
关键: 信息不足必须 UNKNOWN，宁可不作判不可瞎判。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.artifacts.registry import ArtifactRegistry
from runtime.graph.evidence_graph import EvidenceGraph
from validators.evidence import evidence_gate as eg
from runtime.writing import JudgeCritic, PaperProjection, ResearchDirector


@pytest.fixture
def healthy(tmp_path):
    reg = ArtifactRegistry(tmp_path / "registry.json")
    reg.project = "test"
    reg.create("question", title="Q1", activate=True)
    reg.create("experiment", title="exp", question="Q001", activate=True)
    reg.create("result", title="result", question="Q001", activate=True,
               tags=["sensitivity", "baseline"])
    reg.create("claim", title="claim", question="Q001", activate=True,
               data={"statement": "主张成立"})
    reg.create("paper_section", title="结果分析", activate=True)
    g = EvidenceGraph(reg, path=tmp_path / "graph.json")
    for f, r, t in [
        ("E001", "produces", "R001"),
        ("R001", "supports", "C001"),
        ("C001", "appears_in", "S001"),
    ]:
        g.add_relation(f, r, t)
    return reg, g


def build(reg, g):
    nar = ResearchDirector(reg, g).build()
    outline = PaperProjection(reg, g).project(nar)
    ev = eg.evaluate(reg, g)
    return nar, outline, ev


class TestVerdicts:
    def test_pass_when_healthy(self, healthy):
        reg, g = healthy
        nar, outline, ev = build(reg, g)
        report = JudgeCritic().evaluate(nar, outline, ev)
        assert report.verdict == "PASS"
        assert report.passed
        assert report.risks == []
        assert report.coverage["claims_supported"] == 1

    def test_unknown_without_evidence_report(self, healthy):
        """证据门禁缺报告 → 不得瞎判。"""
        reg, g = healthy
        nar, outline, _ = build(reg, g)
        report = JudgeCritic().evaluate(nar, outline)   # 不传 evidence_report
        assert report.verdict == "UNKNOWN"
        assert not report.passed
        assert report.risks == []

    def test_unknown_empty_narrative(self, healthy):
        reg, g = healthy
        from runtime.writing import Narrative
        outline = PaperProjection(reg, g).project(
            ResearchDirector(reg, g).build())
        report = JudgeCritic().evaluate(Narrative(), outline,
                                        eg.evaluate(reg, g))
        assert report.verdict == "UNKNOWN"

    def test_unknown_empty_outline(self, healthy):
        reg, g = healthy
        nar, _, ev = build(reg, g)
        report = JudgeCritic().evaluate(nar, {}, ev)
        assert report.verdict == "UNKNOWN"

    def test_fail_when_evidence_gate_fails(self, healthy):
        reg, g = healthy
        reg.create("claim", title="悬空主张", question="Q001", activate=True)
        nar, outline, ev = build(reg, g)
        report = JudgeCritic().evaluate(nar, outline, ev)
        assert report.verdict == "FAIL"
        sources = {(r.source, r.code) for r in report.risks}
        assert ("evidence-gate", "E2") in sources
        # 叙事侧同时发现 N3/N4（悬空主张进结果章节且无归属）
        assert any(r.source == "narrative-critic" for r in report.risks)

    def test_weak_when_only_weak_findings(self, healthy):
        reg, g = healthy
        reg.artifacts["R001"].status = "draft"   # E6 weak
        nar, outline, ev = build(reg, g)
        report = JudgeCritic().evaluate(nar, outline, ev)
        assert report.verdict == "WEAK"
        assert all(r.severity != "fail" for r in report.risks)
        assert any(r.code == "E6" and r.source == "evidence-gate"
                   for r in report.risks)

    def test_fail_beats_weak(self, healthy):
        reg, g = healthy
        reg.create("claim", title="悬空主张", question="Q001", activate=True)  # E2 fail
        reg.artifacts["R001"].tags = []                                          # E8 weak
        nar, outline, ev = build(reg, g)
        report = JudgeCritic().evaluate(nar, outline, ev)
        assert report.verdict == "FAIL"


class TestRiskAggregation:
    def test_risks_sorted_fail_first(self, healthy):
        reg, g = healthy
        reg.create("claim", title="悬空主张", question="Q001", activate=True)  # fail
        reg.artifacts["R001"].tags = []                                        # weak
        nar, outline, ev = build(reg, g)
        report = JudgeCritic().evaluate(nar, outline, ev)
        severities = [r.severity for r in report.risks]
        pivot = severities.index("fail")
        assert "fail" in severities and "weak" in severities
        # fail 全部在 weak 之前
        assert severities[:pivot + 1].count("weak") == 0

    def test_narrative_findings_aggregated(self, healthy):
        """叙事侧发现必须进入 judge 风险清单（无需调用方先跑 narrative-critic）。"""
        reg, g = healthy
        g.remove_relation("C001", "appears_in", "S001")   # 去掉章节归属
        nar, outline, ev = build(reg, g)
        report = JudgeCritic().evaluate(nar, outline, ev)
        # 无 appears_in 边 → pending_placement 含 C001 → N4 fail → FAIL
        assert report.verdict == "FAIL"
        assert any(r.source == "narrative-critic" and r.code == "N4"
                   for r in report.risks)

    def test_summary_readable(self, healthy):
        reg, g = healthy
        nar, outline, ev = build(reg, g)
        s = JudgeCritic().evaluate(nar, outline, ev).summary()
        assert "[judge-critic] PASS" in s
        assert "1/1" in s


class TestPipelineConsistency:
    def test_evidence_gate_dead_data_propagates_to_judge(self, healthy):
        """E3 场景（死数据在证据闭包内）必须一路传到 judge FAIL。"""
        reg, g = healthy
        reg.create("dataset", title="data", question="Q001", activate=True)
        g.add_relation("E001", "uses", "DATA001")
        g.invalidate("DATA001", "数据勘误")
        nar, outline, ev = build(reg, g)
        report = JudgeCritic().evaluate(nar, outline, ev)
        assert report.verdict == "FAIL"
        assert any(r.code == "E3" for r in report.risks)
