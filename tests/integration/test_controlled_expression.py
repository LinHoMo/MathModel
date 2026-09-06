"""P11 Controlled Expression 测试：Contract / ParagraphPlan / Renderer / 校准 / 冗余。

运行: python -m pytest tests/integration/test_controlled_expression.py -q
覆盖 P11-1/2/3/8/9/10/17/19。
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.writing.expression import (  # noqa: E402
    ExpressionContext, classify_renderer_failure, check_wording,
    evidence_level_of)
from runtime.writing.findings import FindingGraph  # noqa: E402
from runtime.writing.narrative_ir import build_narrative_ir  # noqa: E402
from runtime.writing.paragraphs import (  # noqa: E402
    ControlledRenderer, DeterministicRenderer, ParagraphPlanner,
    question_dependencies)
from runtime.writing.patterns import patterns_for  # noqa: E402
from runtime.writing.redundancy import detect as redundancy_detect  # noqa: E402


def _session(tmp_path, questions=("Q001", "Q002"), run=True):
    s = RuntimeSession(tmp_path / "proj", list(questions))
    if run:
        s.run()
    return s


def _planner(s):
    fg = FindingGraph(s.registry, s.graph)
    return ParagraphPlanner(s.registry, s.graph, findings_graph=fg,
                            competition="cumcm")


def _plans(s):
    ir = build_narrative_ir(s.registry, s.graph,
                            findings_graph=FindingGraph(s.registry, s.graph))
    pl = _planner(s)
    return ir, {sec.section_id: pl.plan(sec.section_id, sec, ir)
                for sec in ir.sections}


class TestExpressionContract:
    def test_boundary_lists_frozen(self):
        from runtime.writing.expression import LLM_MAY_CHANGE, LLM_MAY_NOT_CHANGE
        assert "wording" in LLM_MAY_CHANGE
        assert "numeric_value" in LLM_MAY_NOT_CHANGE
        assert not set(LLM_MAY_CHANGE) & set(LLM_MAY_NOT_CHANGE)

    def test_calibration_levels(self):
        assert evidence_level_of("active", True, True) == "strong"
        assert evidence_level_of("active", True, False) == "moderate"
        assert evidence_level_of("active", False, False) == "weak"
        assert evidence_level_of("invalidated", True, True) == "unknown"
        # strong 以下禁强断言
        assert check_wording("模型显著优于基线", "moderate")
        assert not check_wording("结果表明模型优于基线", "strong")
        # unknown 不得写结论
        assert check_wording("任何文本", "unknown")

    def test_failure_semantics(self):
        assert classify_renderer_failure(["hallucinated_number: 42"]) == \
            "hard_reject"
        assert classify_renderer_failure(["hallucinated_citation: x"]) == \
            "hard_reject"
        assert classify_renderer_failure(["unsupported_claim"]) == "hard_reject"
        assert classify_renderer_failure(["format_failure"]) == \
            "deterministic_repair"
        assert classify_renderer_failure(["style_failure"]) == "rerender"


class TestParagraphPlans:
    def test_every_paragraph_has_purpose_and_content(self, tmp_path):
        s = _session(tmp_path)
        ir, plans = _plans(s)
        count = 0
        for sec_plans in plans.values():
            for p in sec_plans:
                count += 1
                assert p.purpose in (
                    "problem_context", "motivation", "method_choice",
                    "definition", "assumption", "derivation", "procedure",
                    "experiment_setup", "result", "comparison",
                    "interpretation", "robustness", "sensitivity",
                    "limitation", "implication", "transition", "summary")
                assert p.required_content, \
                    f"{p.paragraph_id} 无 required_content（为什么存在？）"
        assert count >= 8

    def test_argument_units_carry_argument_not_sentence(self, tmp_path):
        """P11-3：Claim → ArgumentUnit（support/comparison/解释/边界）。"""
        s = _session(tmp_path, questions=("Q001",))
        ir, plans = _plans(s)
        units = [u for ps in plans.values() for p in ps
                 for u in p.argument_units]
        assert units, "结果段必须有论证单元"
        for u in units:
            assert u.support, "论证单元必须挂支撑"
            assert u.comparison, "论证单元必须带对照"
            assert u.evidence_level in ("strong", "moderate", "weak",
                                        "unknown")

    def test_method_choice_justification_in_plan(self, tmp_path):
        """P11-0 问题 7：选型理由必须进入表达层 IR。"""
        s = _session(tmp_path, questions=("Q001",))
        ir, plans = _plans(s)
        m_plans = [p for ps in plans.values() for p in ps
                   if p.purpose == "method_choice"]
        assert m_plans
        assert any("选型依据" in rc or "选型理由" in rc
                   for p in m_plans for rc in p.required_content)

    def test_cross_question_transition(self, tmp_path):
        """P11-12：Q 依赖必须产生跨问题 transition 段。"""
        s = _session(tmp_path, questions=("Q001", "Q002"))
        s.registry.get("Q002").depends_on.append("Q001")   # 声明问题依赖
        deps = question_dependencies(s.registry, s.graph)
        assert deps, "Q002 依赖 Q001 时应派生产物继承关系"
        ir, plans = _plans(s)
        cross = [p for ps in plans.values() for p in ps
                 if p.cross_question_from]
        assert cross, "跨问题过渡段缺失"

    def test_figure_and_equation_bindings(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        pl = _planner(s)
        figs = pl.figure_bindings()
        assert figs
        for f in figs:
            assert f.why_exists and f.what_it_does_not_prove, \
                "图必须绑定 why_exists / does_not_prove"
        eqs = pl.equation_bindings()
        for e in eqs:
            assert e.model_ref and e.purpose, "公式必须绑定模型与用途"


class TestRenderers:
    def test_deterministic_renderer_fact_bound(self, tmp_path):
        s = _session(tmp_path, questions=("Q001",))
        ir, plans = _plans(s)
        r = DeterministicRenderer()
        outputs = []
        for ps in plans.values():
            for p in ps:
                if p.argument_units:
                    d = p.as_dict()
                    ctx = ExpressionContext(
                        paragraph_purpose=p.purpose,
                        section_purpose="results",
                        allowed_claims=[{"id": c, "text": "", "status": "active"}
                                        for c in p.claim_refs],
                        allowed_evidence=list(p.evidence_refs))
                    outputs.append(r.render_paragraph(
                        __import__("runtime.writing.expression",
                                   fromlist=["ExpressionInput"])
                        .ExpressionInput(paragraph_plan=d, context=ctx)))
        assert outputs
        for o in outputs:
            assert o.source_claim_ids, "输出必须可反查来源"

    def test_post_validation_rejects_hallucinated_number(self, tmp_path):
        """W1：LLM 渲染幻觉数字 → hard_reject。"""
        s = _session(tmp_path, questions=("Q001",))
        ir, plans = _plans(s)
        plan = next(p for ps in plans.values() for p in ps
                    if p.argument_units).as_dict()
        ctx = ExpressionContext(paragraph_purpose="result",
                                section_purpose="results",
                                allowed_numbers=["0.123"])
        renderer = ControlledRenderer(
            llm_fn=lambda inp: "模型误差为 0.999，大幅优于基线。")
        out = renderer.render_paragraph(
            __import__("runtime.writing.expression",
                       fromlist=["ExpressionInput"])
            .ExpressionInput(paragraph_plan=plan, context=ctx))
        assert any("hallucinated_number" in v for v in out.violations)
        assert out.disposition == "hard_reject"

    def test_post_validation_rejects_hallucinated_citation(self, tmp_path):
        """W2/F：幻觉引用 → hard_reject。"""
        s = _session(tmp_path, questions=("Q001",))
        ir, plans = _plans(s)
        plan = next(p for ps in plans.values() for p in ps).as_dict()
        ctx = ExpressionContext(paragraph_purpose="method_choice",
                                section_purpose="methodology",
                                allowed_references=["real2024"])
        renderer = ControlledRenderer(llm_fn=lambda inp: r"见 \cite{fake2026}。")
        out = renderer.render_paragraph(
            __import__("runtime.writing.expression",
                       fromlist=["ExpressionInput"])
            .ExpressionInput(paragraph_plan=plan, context=ctx))
        assert any("hallucinated_citation" in v for v in out.violations)

    def test_calibration_blocks_unsupported_superlative(self, tmp_path):
        """W3/W4：非 strong 证据 + 最优/显著 → 校准拦截。"""
        s = _session(tmp_path, questions=("Q001",))
        ir, plans = _plans(s)
        plan = next(p for ps in plans.values() for p in ps
                    if p.argument_units).as_dict()
        ctx = ExpressionContext(paragraph_purpose="result",
                                section_purpose="results")
        renderer = ControlledRenderer(
            llm_fn=lambda inp: "结果表明本模型显著优于基线，是最优的。")
        out = renderer.render_paragraph(
            __import__("runtime.writing.expression",
                       fromlist=["ExpressionInput"])
            .ExpressionInput(paragraph_plan=plan, context=ctx))
        # 措辞校准（weak/moderate 级）必须违规
        assert out.wording_violations


class TestRedundancy:
    def test_redundancy_detection(self):
        text = ("具有重要意义。\n具有重要意义。\n" * 3 +
                "首先其次最后。")
        findings = redundancy_detect(text)
        codes = {f.code for f in findings}
        assert "RED-2" in codes and "RED-3" in codes and "RED-6" in codes

    def test_w14_repeated_boilerplate_flagged(self):
        """W14：重复 boilerplate 段落被确定性检测。"""
        paras = ["本模型具有良好性质。", "本模型具有良好性质。",
                 "本模型具有良好性质。"]
        findings = redundancy_detect("", paragraphs=paras)
        assert any(f.code in ("RED-1", "RED-6") for f in findings)

    def test_w15_unsupported_causal_language(self):
        """W15：无证据因果措辞 → RED-5。"""
        findings = redundancy_detect("本方法证明是最优的。")
        assert any(f.code == "RED-5" for f in findings)


class TestWritingPatterns:
    def test_seven_patterns_distilled(self):
        from runtime.writing.patterns import WRITING_PATTERNS
        assert len(WRITING_PATTERNS) == 7
        for p in WRITING_PATTERNS.values():
            assert p.preconditions and p.structure and p.failure_mode

    def test_pattern_selection_by_purpose_and_competition(self):
        assert patterns_for("comparison", competition="cumcm",
                            evidence_ready={"baseline_comparison": True})
        assert patterns_for("comparison", competition="unknown-comp") == []
        assert not patterns_for("nonexistent-purpose")
