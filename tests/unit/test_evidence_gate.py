"""P3 Evidence Gate 测试：E1-E8 检查项 / PASS-WEAK-FAIL 判定 / 反馈环语义。

运行: python -m pytest tests/unit/test_evidence_gate.py -q
覆盖任务书: evidence gate（无证据不得进入论文投影）。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.artifacts.registry import ArtifactRegistry
from runtime.graph.evidence_graph import EvidenceGraph
from validators.evidence import evidence_gate as eg


@pytest.fixture
def setup(tmp_path):
    """完整健康链: E001 produces R001 → supports C001，含 sensitivity tag。"""
    reg = ArtifactRegistry(tmp_path / "registry.json")
    reg.project = "test"
    reg.create("question", title="Q1", activate=True)
    reg.create("model", title="model", question="Q001", activate=True)
    reg.create("experiment", title="exp", question="Q001", activate=True)
    reg.create("result", title="result", question="Q001", activate=True,
               tags=["sensitivity", "baseline"])
    reg.create("claim", title="claim", question="Q001", activate=True)

    g = EvidenceGraph(reg, path=tmp_path / "graph.json")
    for f, r, t in [
        ("Q001", "solved_by", "M001"),
        ("M001", "validated_by", "E001"),
        ("E001", "produces", "R001"),
        ("R001", "supports", "C001"),
    ]:
        g.add_relation(f, r, t)
    return reg, g


class TestHealthyGraph:
    def test_pass_when_all_good(self, setup):
        reg, g = setup
        report = eg.evaluate(reg, g)
        assert report.verdict == "PASS"
        assert report.passed
        assert report.coverage["claims_supported"] == 1
        assert not report.findings

    def test_summary_readable(self, setup):
        reg, g = setup
        s = eg.evaluate(reg, g).summary()
        assert "PASS" in s and "1/1" in s


class TestFailConditions:
    def test_e1_no_claims(self, tmp_path):
        reg = ArtifactRegistry(tmp_path / "r.json")
        reg.project = "t"
        reg.create("experiment", title="e", activate=True)
        g = EvidenceGraph(reg, path=tmp_path / "g.json")
        report = eg.evaluate(reg, g)
        assert report.verdict == "FAIL"
        assert report.findings[0].code == "E1"

    def test_e2_unsupported_claim(self, setup):
        reg, g = setup
        reg.create("claim", title="悬空主张", question="Q001", activate=True)
        report = eg.evaluate(reg, g)
        assert report.verdict == "FAIL"
        codes = [f.code for f in report.findings]
        assert "E2" in codes
        f = next(f for f in report.findings if f.code == "E2")
        assert "C002" in f.artifacts

    def test_e3_dead_evidence_in_chain(self, setup):
        reg, g = setup
        # 数据修正 → R001 失效 → claim 证据链含失效节点
        reg.create("dataset", title="data", question="Q001", activate=True)
        g.add_relation("E001", "uses", "DATA001")
        g.invalidate("DATA001", "数据勘误")
        report = eg.evaluate(reg, g)
        assert report.verdict == "FAIL"
        f = next(f for f in report.findings if f.code == "E3")
        assert any("DATA001" in a or "R001" in a for a in f.artifacts)

    def test_e4_experiment_without_results(self, setup):
        reg, g = setup
        reg.create("experiment", title="空实验", question="Q001", activate=True)
        report = eg.evaluate(reg, g)
        assert report.verdict == "FAIL"
        f = next(f for f in report.findings if f.code == "E4")
        assert "E002" in f.artifacts

    def test_fail_beats_weak(self, setup):
        """同时存在 fail 与 weak 时，verdict 必须是 FAIL。"""
        reg, g = setup
        reg.create("claim", title="悬空", question="Q001", activate=True)  # E2 fail
        # E8 weak: 去掉 tags
        reg.artifacts["R001"].tags = []
        report = eg.evaluate(reg, g)
        assert report.verdict == "FAIL"


class TestWeakConditions:
    def test_e6_draft_evidence(self, setup):
        reg, g = setup
        reg.artifacts["R001"].status = "draft"   # 未过验证的结果
        report = eg.evaluate(reg, g)
        assert report.verdict == "WEAK"
        assert any(f.code == "E6" for f in report.findings)

    def test_e5_orphan_result(self, setup):
        reg, g = setup
        reg.create("result", title="无来源结果", question="Q001", activate=True)
        report = eg.evaluate(reg, g)
        assert report.verdict == "WEAK"
        assert any(f.code == "E5" for f in report.findings)

    def test_e7_low_coverage(self, setup):
        reg, g = setup
        reg.create("claim", title="第二主张", question="Q001", activate=True)
        report = eg.evaluate(reg, g)
        assert report.coverage["claims_total"] == 2
        assert report.coverage["coverage_ratio"] == 0.5
        # C002 无支撑 → E2 fail 优先于 E7 weak
        assert report.verdict == "FAIL"
        assert any(f.code == "E7" for f in report.findings)

    def test_e8_no_sensitivity_tags(self, setup):
        reg, g = setup
        reg.artifacts["R001"].tags = []
        report = eg.evaluate(reg, g)
        assert report.verdict == "WEAK"
        f = next(f for f in report.findings if f.code == "E8")
        assert "sensitivity" in f.message

    def test_min_coverage_threshold_configurable(self, setup):
        reg, g = setup
        reg.create("claim", title="第二主张", question="Q001", activate=True)
        # coverage=0.5 ≥ 0.4 → E7 不触发（C002 无支撑的 E2 仍会 FAIL，但那是 E2 的职责）
        report = eg.evaluate(reg, g, min_coverage=0.4)
        codes = [f.code for f in report.findings]
        assert "E7" not in codes


class TestReportShape:
    def test_as_dict(self, setup):
        reg, g = setup
        d = eg.evaluate(reg, g).as_dict()
        assert d["verdict"] == "PASS"
        assert d["coverage"]["claims_total"] == 1
        assert d["findings"] == []
