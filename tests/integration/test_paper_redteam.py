"""P10-12 Paper Intelligence 红队（攻击 A–L）。

运行: python -m pytest tests/integration/test_paper_redteam.py -q
A invalidated claim leakage / B superseded experiment leakage /
C unsupported number / D unsupported conclusion / E unsupported figure /
F hallucinated citation / G stale abstract / H stale conclusion /
I orphan figure / J orphan table / K orphan equation /
L cross-question containment + 全链失效传播（M 死 → Paper 重建）。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.writing.findings import FindingGraph  # noqa: E402
from runtime.writing.fact_check import PaperFactChecker  # noqa: E402
from runtime.writing.narrative_ir import (  # noqa: E402
    build_narrative_ir, claim_coverage, derive_conclusion)


def _session(tmp_path, questions=("Q001", "Q002"), run=True):
    s = RuntimeSession(tmp_path / "proj", list(questions))
    if run:
        s.run()
    return s


def _checker(s, ir=None):
    fg = FindingGraph(s.registry, s.graph)
    ir = ir or build_narrative_ir(s.registry, s.graph, findings_graph=fg)
    return fg, PaperFactChecker(s.registry, s.graph, findings_graph=fg,
                                narrative_ir=ir)


def _tex_for(s, extra=""):
    """从 IR 确定性渲染一份"合格"论文（模拟投影产物）。"""
    ir = build_narrative_ir(s.registry, s.graph)
    lines = [r"\section{" + x.title + "}" for x in ir.sections]
    for c in s.registry.list_by_type("claim"):
        if c.status == "active":
            lines.append(c.data.get("statement") or c.title)
    for r in s.registry.list_by_type("result"):
        if r.status == "active":
            lines.append(r"\includegraphics{" + (r.title or "") + "}")
    return "\n".join(lines) + extra


class TestRedTeamAL:
    def test_A_invalidated_claim_leakage(self, tmp_path):
        """A：失效 claim 写进论文 → P11 FAIL。"""
        s = _session(tmp_path, questions=("Q001",))
        r = s.registry.list_by_type("result")[0]
        c = s.registry.list_by_type("claim")[0]
        s.invalidate(r.artifact_id, reason="勘误")
        s.run()
        fg, fc = _checker(s)
        bad_tex = _tex_for(s) + f"\n{c.data.get('statement') or c.title}"
        report = fc.check(bad_tex)
        assert any(f.code == "P11" and f.severity == "fail"
                   for f in report.findings)

    def test_B_superseded_experiment_leakage(self, tmp_path):
        """B：superseded 实验链不得支撑当前 claim。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        s.rerun("experiment@Q001")
        s.run()
        superseded_results = {a.artifact_id
                              for a in s.registry.list_by_type("result")
                              if a.status == "superseded"}
        for c in s.registry.list_by_type("claim"):
            if c.status != "active":
                continue
            for e in s.graph.relations:
                if e["relation"] == "supports" and e["to"] == c.artifact_id:
                    assert e["from"] not in superseded_results

    def test_C_unsupported_number(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        fg, fc = _checker(s)
        report = fc.check(_tex_for(s) + "\n改进幅度 42.7%。")
        assert any(f.code == "P3" and "42.7" in f.subject
                   for f in report.findings)

    def test_D_unsupported_conclusion(self, tmp_path):
        """D：无证据 claim 进入论文 → P2 FAIL。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        s.registry.create("claim", title="凭空断言",
                          question="Q001", activate=True)
        fg, fc = _checker(s)
        report = fc.check(_tex_for(s) + "\n凭空断言")
        assert any(f.code == "P2" and f.severity == "fail"
                   for f in report.findings)

    def test_E_unsupported_figure(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        fg, fc = _checker(s)
        report = fc.check(_tex_for(s) + r"\includegraphics{幻觉图}")
        assert any(f.code == "P4" and "幻觉图" in f.subject
                   for f in report.findings)

    def test_F_hallucinated_citation(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        fg, fc = _checker(s)
        report = fc.check(_tex_for(s) + r"\cite{no-such-ref}")
        assert any(f.code == "P7" and "no-such-ref" in f.subject
                   for f in report.findings)

    def test_G_H_stale_abstract_and_conclusion(self, tmp_path):
        """G/H：Abstract/Conclusion 是派生式——重新派生必须与当前 State 幂等
        （不存在"残留旧文案"的载体），且 FAIL 发现不得进入结论。"""
        s = _session(tmp_path, questions=("Q001",))
        r = s.registry.list_by_type("result")[0]
        s.invalidate(r.artifact_id, reason="勘误")
        s.run()
        ir_a = build_narrative_ir(s.registry, s.graph)
        ir_b = build_narrative_ir(s.registry, s.graph)
        assert ir_a.abstract == ir_b.abstract, "派生必须幂等（无旧文案残留）"
        fg = FindingGraph(s.registry, s.graph)
        conclusion = derive_conclusion(fg.findings)
        for f in fg.findings:
            if f.status != "PASS":
                assert f.statement not in conclusion, \
                    "非 PASS 发现不得进入结论"

    def test_I_orphan_figure(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        fg, fc = _checker(s)
        report = fc.check(_tex_for(s))
        assert any(f.code == "P4" and f.severity == "weak"
                   and "orphan" in f.reason
                   for f in report.findings)

    def test_J_orphan_table(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        fg, fc = _checker(s)
        tex = _tex_for(s) + "\n\\begin{table}\\end{table}\n" * 2
        report = fc.check(tex)
        assert any(f.code == "P5" and f.severity == "fail"
                   for f in report.findings)

    def test_K_orphan_equation(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        fg, fc = _checker(s)
        tex = _tex_for(s) + "\n\\begin{equation}x=y\\end{equation}\n" * 3
        report = fc.check(tex)
        assert any(f.code == "P6" for f in report.findings)

    def test_L_cross_question_containment(self, tmp_path):
        """L：Q001 失效不污染 Q002 的 finding。"""
        s = _session(tmp_path, questions=("Q001", "Q002"))
        s.run()
        r1 = next(a for a in s.registry.list_by_type("result")
                  if a.question == "Q001")
        s.invalidate(r1.artifact_id, reason="勘误")
        fg = FindingGraph(s.registry, s.graph)
        q2 = fg.by_question("Q002")
        assert q2 and all(f.status != "FAIL" for f in q2)

    def test_full_chain_model_death_propagates(self, tmp_path):
        """终局：M1 证伪 → E/C 判死 → 投影重建后无死主张。"""
        s = _session(tmp_path, questions=("Q001",))
        s.run()
        model = s.registry.list_by_type("model")[0]
        model.transition("invalidated", by="redteam", reason="模型证伪")
        s.run()
        assert model.status == "invalidated"
        ir = build_narrative_ir(s.registry, s.graph)
        terminal = {a.artifact_id for a in s.registry.list_by_type("claim")
                    if a.status in ("invalidated", "superseded")}
        # 重建后活跃 claim 均非死主张
        active_now = {a.artifact_id for a in s.registry.list_by_type("claim")
                      if a.status == "active"}
        for sec in ir.sections:
            for cid in sec.claims:
                if cid in terminal:
                    assert cid not in active_now
