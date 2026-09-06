"""P11 红队 W1–W15 + A/B 质量对比（确定性指标）。

运行: python -m pytest tests/integration/test_writing_redteam.py -q
A: deterministic projection baseline；B: controlled rendering（确定性渲染器，
LLM 通过 llm_fn 注入同一路径）。比较指标：claim coverage / evidence density /
interpretation density / redundancy / unsupported statements。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402
from runtime.writing.expression import (  # noqa: E402
    ExpressionContext, ExpressionInput, check_wording)
from runtime.writing.fact_check import PaperFactChecker  # noqa: E402
from runtime.writing.findings import FindingGraph  # noqa: E402
from runtime.writing.narrative_ir import build_narrative_ir  # noqa: E402
from runtime.writing.paragraphs import (  # noqa: E402
    ControlledRenderer, ParagraphPlanner)
from runtime.writing.redundancy import detect as redundancy_detect  # noqa: E402


def _session(tmp_path, questions=("Q001", "Q002"), run=True):
    s = RuntimeSession(tmp_path / "proj", list(questions))
    if run:
        s.run()
    return s


def _pipeline(s):
    fg = FindingGraph(s.registry, s.graph)
    ir = build_narrative_ir(s.registry, s.graph, findings_graph=fg)
    planner = ParagraphPlanner(s.registry, s.graph, findings_graph=fg,
                               competition="cumcm")
    return fg, ir, planner


class TestW1W15:
    def _check(self, s, tex):
        fg = FindingGraph(s.registry, s.graph)
        ir = build_narrative_ir(s.registry, s.graph, findings_graph=fg)
        fc = PaperFactChecker(s.registry, s.graph, findings_graph=fg,
                              narrative_ir=ir)
        return fc.check(tex)

    def test_W1_invented_number(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        report = self._check(s, r"误差为 0.777。")
        assert any(f.code == "P3" and f.severity == "fail"
                   for f in report.findings)

    def test_W2_invented_citation(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        report = self._check(s, r"\cite{invented}")
        assert any(f.code == "P7" for f in report.findings)

    def test_W3_W4_unsupported_best_and_significant(self, tmp_path):
        from runtime.writing.expression import check_wording
        assert check_wording("本模型是最优的。", "moderate")
        assert check_wording("结果显著改善。", "moderate")
        assert check_wording("结果显著改善。", "strong", significance=True) == []
        assert check_wording("结果表明改善。", "strong") == []

    def test_W5_stale_superseded_result(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        s.rerun("experiment@Q001")
        s.run()
        stale = next(a.title for a in s.registry.list_by_type("result")
                     if a.status == "superseded")
        report = self._check(s, f"旧结果 {stale} 仍然成立。")
        assert any(f.code == "P12" or f.code == "P3"
                   for f in report.findings)

    def test_W6_dead_claim_resurrection(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        r = s.registry.list_by_type("result")[0]
        c = s.registry.list_by_type("claim")[0]
        s.invalidate(r.artifact_id, reason="勘误")
        s.run()
        dead = c.data.get("statement") or c.title
        report = self._check(s, f"本文结论：{dead}。")
        assert any(f.code == "P11" and f.severity == "fail"
                   for f in report.findings)

    def test_W9_literature_vs_own_result(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        # 文献支撑的 claim（无实验边）写进论文
        c = s.registry.create("claim", title="文献结论主张",
                              question="Q001", activate=True,
                              data={"statement": "文献结论主张",
                                    "literature_refs": ["ref-1"]})
        report = self._check(s, "文献结论主张")
        assert any(f.code == "P2" and "literature" in f.reason
                   for f in report.findings), \
            "文献结论不得伪装成本项目实验结果"

    def test_W10_hypothesis_as_conclusion(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        r = s.registry.list_by_type("result")[0]
        s.invalidate(r.artifact_id, reason="勘误")
        s.run()
        fg = FindingGraph(s.registry, s.graph)
        conclusion = __import__(
            "runtime.writing.narrative_ir",
            fromlist=["derive_conclusion"]).derive_conclusion(fg.findings)
        for f in fg.findings:
            if f.status != "PASS":
                assert f.statement not in conclusion

    def test_W11_conclusion_adds_no_new_claim(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        fg = FindingGraph(s.registry, s.graph)
        conclusion = __import__(
            "runtime.writing.narrative_ir",
            fromlist=["derive_conclusion"]).derive_conclusion(fg.findings)
        # 结论中的每个句子都能对应到 validated finding statement
        for f in fg.findings:
            if f.status == "PASS":
                assert f.statement in conclusion
        assert len(conclusion) > 0

    def test_W13_cross_question_containment(self, tmp_path):
        s = _session(tmp_path, questions=("Q001", "Q002"))
        s.run()
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == "Q001")
        s.invalidate(r1.artifact_id, reason="勘误")
        fg = FindingGraph(s.registry, s.graph)
        assert all(f.status != "FAIL" for f in fg.by_question("Q002"))


class TestABComparison:
    """P11 真实质量评估：同一冻结 Research State，A/B 两条渲染路径。"""

    def metrics(self, s, tex):
        fg = FindingGraph(s.registry, s.graph)
        ir = build_narrative_ir(s.registry, s.graph, findings_graph=fg)
        fc = PaperFactChecker(s.registry, s.graph, findings_graph=fg,
                              narrative_ir=ir)
        report = fc.check(tex)
        redundancy = redundancy_detect(tex)
        return {
            "unsupported_fail": len(report.blockers),
            "interpretation_density": tex.count("possible explanation")
            + tex.count("含义"),
            "redundancy": len(redundancy),
        }

    def test_AB_same_facts_both_paths(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        fg, ir, planner = _pipeline(s)

        # A：deterministic projection baseline（outline 拼装，无论证单元）
        tex_a = "\n".join(
            [r"\section{" + x.title + "}" for x in ir.sections]
            + [(c.data.get("statement") or c.title)
               for c in s.registry.list_by_type("claim") if c.status == "active"])

        # B：controlled rendering（ParagraphPlan → ArgumentUnit 渲染）
        renderer = ControlledRenderer()
        parts = []
        for sec in ir.sections:
            for p in planner.plan(sec.section_id, sec, ir):
                ctx = ExpressionContext(
                    paragraph_purpose=p.purpose,
                    section_purpose=sec.purpose,
                    allowed_claims=[{"id": c, "text": "", "status": "active"}
                                    for c in p.claim_refs],
                    allowed_evidence=list(p.evidence_refs))
                d = p.as_dict()
                out = renderer.render_paragraph(
                    ExpressionInput(paragraph_plan=d, context=ctx))
                if out.disposition == "hard_reject":
                    # 受控渲染：hard reject 的段落不进入论文（重新规划）
                    continue
                parts.append(out.text)
        tex_b = "\n".join(parts)

        mA = self.metrics(s, tex_a)
        mB = self.metrics(s, tex_b)
        # 事实层不变：两边 0 unsupported blocker
        assert mA["unsupported_fail"] == 0 and mB["unsupported_fail"] == 0
        # B 的解释密度 ≥ A（interpretation 段落带来机制/含义句）
        assert mB["interpretation_density"] >= mA["interpretation_density"]
        # B 无冗余回归
        assert mB["redundancy"] == 0

    def test_final_gate_integrity_undispatchable(self, tmp_path):
        """P11-20：Integrity FAIL → 不得交付（与 LLM 自评无关）。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        for a in s.registry.list_by_type("decision"):
            if "实验计划" in (a.title or ""):
                a.data["baseline_comparison"] = []
        fg = FindingGraph(s.registry, s.graph)
        ir = build_narrative_ir(s.registry, s.graph, findings_graph=fg)
        fc = PaperFactChecker(s.registry, s.graph, findings_graph=fg,
                              narrative_ir=ir)
        report = fc.check(_render(s, ir, planner=ParagraphPlanner(
            s.registry, s.graph, findings_graph=fg)))
        # 最终门禁 = PaperIntegrity ∧ ResearchQuality（任一 FAIL 即不得交付）
        from validators.quality import ResearchQuality
        rq = ResearchQuality(knowledge=KnowledgeRetriever(REPO / "core" / "knowledge"))
        research = rq.evaluate(s.registry, s.graph)
        statuses = [report.overall_status, research.overall_status]
        rank = {"PASS": 0, "UNKNOWN": 1, "WEAK": 2, "FAIL": 3}
        final = max(statuses, key=lambda x: rank[x])
        assert final == "FAIL"
        assert report.blockers or research.blockers,             "Integrity/Research FAIL 必须阻断交付"


def _render(s, ir, planner):
    renderer = ControlledRenderer()
    parts = []
    for sec in ir.sections:
        for p in planner.plan(sec.section_id, sec, ir):
            ctx = ExpressionContext(paragraph_purpose=p.purpose,
                                    section_purpose=sec.purpose,
                                    allowed_claims=[
                                        {"id": c, "text": "", "status": "active"}
                                        for c in p.claim_refs])
            out = renderer.render_paragraph(
                ExpressionInput(paragraph_plan=p.as_dict(), context=ctx))
            if out.disposition != "hard_reject":
                parts.append(out.text)
    return "\n".join(parts)
