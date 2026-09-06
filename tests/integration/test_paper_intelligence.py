"""P10 Paper Intelligence 集成测试：Narrative IR / Coverage / Finding / FactCheck。

运行: python -m pytest tests/integration/test_paper_intelligence.py -q
对照任务书 P10-1~P10-11；红队 A-L 在 test_paper_redteam.py。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.writing.findings import FindingGraph  # noqa: E402
from runtime.writing.narrative_ir import (  # noqa: E402
    ScientificNarrative, build_narrative_ir, claim_coverage,
    derive_conclusion)


def _session(tmp_path, questions=("Q001", "Q002"), run=True):
    s = RuntimeSession(tmp_path / "proj", list(questions))
    if run:
        s.run()
    return s


class TestNarrativeIR:
    def test_ir_built_with_six_sections(self, tmp_path):
        s = _session(tmp_path)
        ir = build_narrative_ir(s.registry, s.graph)
        assert isinstance(ir, ScientificNarrative)
        assert [x.purpose for x in ir.sections] == [
            "problem_definition", "methodology", "experiment", "results",
            "discussion", "conclusion"]
        assert ir.sections[3].evidence, "results 节必须锚定证据"
        assert ir.abstract, "Abstract 必须从 findings 派生"

    def test_reasoning_graph_vocabulary(self, tmp_path):
        s = _session(tmp_path)
        ir = build_narrative_ir(s.registry, s.graph)
        rels = {e["relation"] for e in ir.reasoning_edges}
        assert {"motivates", "supports", "limits"} <= rels
        for e in ir.reasoning_edges:
            assert e["relation"] in ("motivates", "supports", "contradicts",
                                     "explains", "compares", "limits",
                                     "extends")


class TestCoverageMatrix:
    def test_matrix_full_chain(self, tmp_path):
        """每条 claim 的 evidence/experiment/model/figure 全链可回溯。"""
        s = _session(tmp_path)
        rows = claim_coverage(s.registry, s.graph)
        assert rows
        for row in rows:
            assert row.evidence, f"{row.claim_id} 无证据行"
            assert row.experiments, f"{row.claim_id} 无实验链"
            assert row.models, f"{row.claim_id} 无模型链"
            assert row.publishable, "活跃且有证据的 claim 应可发布"

    def test_c1_no_evidence_not_publishable(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        c = s.registry.create("claim", title="无证据主张",
                              question="Q001", activate=True)
        rows = {r.claim_id: r for r in claim_coverage(s.registry, s.graph)}
        assert not rows[c.artifact_id].publishable, "C1：无证据不可发布"

    def test_c3_invalidated_claim_not_publishable(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        r = s.registry.list_by_type("result")[0]
        s.invalidate(r.artifact_id, reason="勘误")
        rows = claim_coverage(s.registry, s.graph)
        dead = [row for row in rows if row.status != "active"]
        assert dead and all(not row.publishable for row in dead), \
            "C3：失效 claim 不可发布"


class TestFindingGraph:
    def test_findings_derived_and_typed(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        fg = FindingGraph(s.registry, s.graph)
        types = {f.type for f in fg.findings}
        assert "descriptive" in types
        assert "comparative" in types
        # 单结果 → 比较型发现是 UNKNOWN（假设态），不得 PASS
        comp = [f for f in fg.findings if f.type == "comparative"]
        assert all(f.status == "UNKNOWN" for f in comp)

    def test_finding_status_tracks_evidence_lifecycle(self, tmp_path):
        """失效传播自动降级 finding（派生式失效传播）。"""
        s = _session(tmp_path, questions=("Q001",))
        fg1 = FindingGraph(s.registry, s.graph)
        assert any(f.status in ("PASS", "WEAK") for f in fg1.findings)
        r = s.registry.list_by_type("result")[0]
        s.invalidate(r.artifact_id, reason="勘误")
        fg2 = FindingGraph(s.registry, s.graph)
        assert all(f.status == "FAIL" for f in fg2.findings), \
            "支撑证据全部失效 → finding 必须判 FAIL"

    def test_conclusion_only_from_validated(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        fg = FindingGraph(s.registry, s.graph)
        text = derive_conclusion(fg.findings)
        assert text
        # 结论中出现的发现必须是 PASS 态
        for f in fg.findings:
            if f.status != "PASS":
                assert f.statement not in text


class TestFactChecker:
    TEX_OK = r"""
\section{问题重述与分析}
\section{模型建立}
\section{结果与分析}
Q001 的实验结果已获得（Q001 结果）。
Q001 结论
\includegraphics{Q001 结果}
"""

    def test_fact_check_clean_projection(self, tmp_path):
        """IR 投影出的论文 → FactCheck 无 blocker。"""
        s = _session(tmp_path, questions=("Q001",))
        ir = build_narrative_ir(s.registry, s.graph)
        tex = self.TEX_OK
        fc = PaperFactCheckerProxy(s, ir)
        report = fc.check(tex)
        fails = [f for f in report.findings if f.severity == "fail"]
        assert not fails, [f.reason for f in fails]

    def test_unsupported_number_flagged(self, tmp_path):
        """P3：论文数字在 Registry 无来源 → UNSUPPORTED。"""
        s = _session(tmp_path, questions=("Q001",))
        ir = build_narrative_ir(s.registry, s.graph)
        tex = self.TEX_OK + "\n准确率为 99.9%。"
        report = PaperFactCheckerProxy(s, ir).check(tex)
        p3 = [f for f in report.findings if f.code == "P3"]
        assert any("99.9" in f.subject for f in p3), "无来源数字必须被标记"

    def test_dead_claim_leakage(self, tmp_path):
        """P11：死主张写进论文 → FAIL。"""
        s = _session(tmp_path, questions=("Q001",))
        r = s.registry.list_by_type("result")[0]
        c = s.registry.list_by_type("claim")[0]
        s.invalidate(r.artifact_id, reason="勘误")
        ir = build_narrative_ir(s.registry, s.graph)
        dead_text = (c.data.get("statement") or c.title)
        report = PaperFactCheckerProxy(s, ir).check(
            self.TEX_OK + f"\n{dead_text}")
        assert any(f.code == "P11" and f.severity == "fail"
                   for f in report.findings), "死主张泄漏必须 FAIL"

    def test_hallucinated_citation(self, tmp_path):
        """P7：引用不在 bib → hallucinated citation。"""
        s = _session(tmp_path, questions=("Q001",))
        ir = build_narrative_ir(s.registry, s.graph)
        report = PaperFactCheckerProxy(s, ir).check(
            self.TEX_OK + r"\cite{fake2026}")
        assert any(f.code == "P7" and "fake2026" in f.subject
                   for f in report.findings)


class PaperFactCheckerProxy:
    """用 session 的 Registry/Graph/IR 构造 FactChecker 的便捷封装。"""

    def __init__(self, session, ir):
        from runtime.writing.fact_check import PaperFactChecker
        fg = FindingGraph(session.registry, session.graph)
        self._fc = PaperFactChecker(session.registry, session.graph,
                                    findings_graph=fg, narrative_ir=ir)

    def check(self, tex, bib_path=None):
        return self._fc.check(tex, bib_path=bib_path)
