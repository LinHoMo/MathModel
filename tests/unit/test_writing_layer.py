"""P4 Writing 层测试：ResearchDirector + PaperProjection 集成行为。

运行: python -m pytest tests/unit/test_writing_layer.py -q
覆盖任务书: P4 验收「叙事是 Research State 的投影（倒置原则）」。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.artifacts.registry import ArtifactRegistry
from runtime.graph.evidence_graph import EvidenceGraph
from runtime.writing import PaperProjection, ResearchDirector


@pytest.fixture
def healthy(tmp_path):
    """完整健康链: P→Q→M→(A)→E→R→F + R supports C + C appears_in S。"""
    reg = ArtifactRegistry(tmp_path / "registry.json")
    reg.project = "test"
    reg.create("problem", title="板凳排列问题", activate=True)
    reg.create("question", title="子问题一", activate=True)
    reg.create("model", title="TOPSIS 评价模型", question="Q001", activate=True)
    reg.create("assumption", title="厚度可忽略", question="Q001", activate=True)
    reg.create("experiment", title="对比实验", question="Q001", activate=True)
    reg.create("result", title="排序结果", question="Q001", activate=True,
               tags=["sensitivity", "baseline"])
    reg.create("figure", title="排序条形图", question="Q001", activate=True)
    reg.create("claim", title="主张", question="Q001", activate=True,
               data={"statement": "TOPSIS 排序对权重扰动稳健"})
    reg.create("paper_section", title="结果分析", activate=True)

    g = EvidenceGraph(reg, path=tmp_path / "graph.json")
    for f, r, t in [
        ("P001", "motivates", "Q001"),
        ("Q001", "solved_by", "M001"),
        ("M001", "assumes", "A001"),
        ("M001", "validated_by", "E001"),
        ("E001", "produces", "R001"),
        ("R001", "visualized_by", "F001"),
        ("R001", "supports", "C001"),
        ("C001", "appears_in", "S001"),
    ]:
        g.add_relation(f, r, t)
    return reg, g


class TestResearchDirector:
    def test_healthy_narrative(self, healthy):
        reg, g = healthy
        nar = ResearchDirector(reg, g).build()
        assert nar.problem == "板凳排列问题"
        assert nar.questions == [
            {"id": "Q001", "models": ["M001"], "claims": ["C001"]}]
        assert len(nar.arcs) == 1
        arc = nar.arcs[0]
        assert arc.claim_id == "C001"
        assert arc.statement == "TOPSIS 排序对权重扰动稳健"
        assert arc.status == "supported"
        # 证据闭包（双向）包含 result / experiment / figure
        for aid in ("R001", "E001", "F001"):
            assert aid in arc.evidence_ids
        assert not arc.dead_evidence

    def test_supported_arcs_property(self, healthy):
        reg, g = healthy
        nar = ResearchDirector(reg, g).build()
        assert [a.claim_id for a in nar.supported_arcs] == ["C001"]
        assert nar.unsupported == []
        assert nar.dead_arcs == []

    def test_dead_evidence_kills_arc(self, healthy):
        reg, g = healthy
        reg.invalidate("R001", "数据勘误")   # 不走传播，只标 R001 死
        nar = ResearchDirector(reg, g).build()
        arc = nar.arcs[0]
        assert arc.status == "dead"
        assert arc.dead_evidence == ["R001"]
        assert [a.claim_id for a in nar.dead_arcs] == ["C001"]

    def test_unsupported_claim(self, healthy):
        reg, g = healthy
        reg.create("claim", title="悬空主张", question="Q001", activate=True)
        nar = ResearchDirector(reg, g).build()
        assert nar.unsupported == ["C002"]

    def test_statement_falls_back_to_title(self, healthy):
        reg, g = healthy
        nar = ResearchDirector(reg, g).build()
        # claim 无 data.statement 时回退 title
        assert nar.arcs[0].statement  # 健康例有 statement，不回退
        reg.create("claim", title="只有标题的主张", question="Q001", activate=True)
        nar2 = ResearchDirector(reg, g).build()
        arc2 = next(a for a in nar2.arcs if a.claim_id == "C002")
        assert arc2.statement == "只有标题的主张"


class TestPaperProjection:
    def test_five_sections_in_order(self, healthy):
        reg, g = healthy
        nar = ResearchDirector(reg, g).build()
        outline = PaperProjection(reg, g).project(nar)
        names = [s["section"] for s in outline["sections"]]
        assert names == ["问题重述与分析", "模型建立", "结果与分析",
                         "灵敏度与稳健性", "结论"]
        assert outline["problem"] == "板凳排列问题"

    def test_model_section_carries_assumptions(self, healthy):
        reg, g = healthy
        nar = ResearchDirector(reg, g).build()
        outline = PaperProjection(reg, g).project(nar)
        model_sec = outline["sections"][1]
        assert model_sec["models"] == [
            {"model": "M001", "question": "Q001", "assumptions": ["A001"]}]

    def test_result_section_claims_and_figures(self, healthy):
        reg, g = healthy
        nar = ResearchDirector(reg, g).build()
        outline = PaperProjection(reg, g).project(nar)
        result = outline["sections"][2]
        assert result["claims"][0]["claim"] == "C001"
        assert result["claims"][0]["supported"] is True
        assert result["claims"][0]["placement"] == ["S001"]
        assert result["claims"][0]["figures"] == ["F001"]
        assert result["figures"] == ["F001"]

    def test_sensitivity_section_from_tags(self, healthy):
        reg, g = healthy
        nar = ResearchDirector(reg, g).build()
        outline = PaperProjection(reg, g).project(nar)
        assert outline["sections"][3]["evidence"] == ["R001"]

    def test_dead_claim_excluded(self, healthy):
        reg, g = healthy
        reg.invalidate("R001", "数据勘误")
        nar = ResearchDirector(reg, g).build()
        outline = PaperProjection(reg, g).project(nar)
        assert outline["dead_claims_excluded"] == ["C001"]
        result = outline["sections"][2]
        assert result["claims"] == []          # 死主张不得投影
        assert outline["sections"][4]["claims"] == []  # 结论只有 supported

    def test_pending_placement_when_no_appears_in(self, healthy):
        reg, g = healthy
        g.remove_relation("C001", "appears_in", "S001")
        nar = ResearchDirector(reg, g).build()
        outline = PaperProjection(reg, g).project(nar)
        assert outline["pending_placement"] == ["C001"]
        result = outline["sections"][2]
        assert result["claims"][0]["placement"] == []
