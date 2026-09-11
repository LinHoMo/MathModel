# -*- coding: utf-8 -*-
"""ADR-0008 问题理解层测试：子问题切分 / 类型映射 / 特征派生 / fail-closed。

运行: py -3.12 -m pytest tests/unit/test_problem_profile.py -q
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import pytest  # noqa: E402
import yaml  # noqa: E402

from modeling_harness.runtime.modeling.problem_profile import (  # noqa: E402
    classify_types,
    load_problem_understanding,
    split_sub_questions,
    understand_problem,
)

CARDS_DIR = REPO / "src" / "modeling_harness" / "knowledge" / "methods" / "cards"

# 三题真实题面的形态片段（来自 projects/*/inputs/problem.txt 实测）
SAMPLE_HEAD_SPACE = """2024 年高教社杯全国大学生数学建模竞赛题目

请建立数学模型，解决以下问题：

问题 1 舞龙队沿螺距为 55 cm 的等距螺线顺时针盘入，各把手中心均位于螺线上。

问题 2 舞龙队沿问题 1 设定的螺线盘入，请确定盘入的终止时刻。

问题 3 从盘入到盘出，需要一定的调头空间。
"""

SAMPLE_FULLWIDTH = """2026 年高教社杯全国大学生数学建模竞赛题目 A 题

请建立数学模型解决以下问题。

问题1　某中药材形状大致呈圆柱形，长为 25 cm，半径为 2 cm（见附件 2）。

问题2　烘干过程一般持续 2-3 天。

问题3　按照烘干要求，药材各处的水分浓度应低于 0.15 kg/kg。

问题4　在实际烘干过程中，药材会因水分流失发生尺寸变化。

附录2　问题1相关参数
密度 = 820 kg/m3
"""


class TestSplitSubQuestions:
    def test_space_separated_headers(self):
        subs = split_sub_questions(SAMPLE_HEAD_SPACE)
        assert [s["label"] for s in subs] == ["Q1", "Q2", "Q3"]

    def test_fullwidth_separated_headers(self):
        subs = split_sub_questions(SAMPLE_FULLWIDTH)
        assert [s["label"] for s in subs] == ["Q1", "Q2", "Q3", "Q4"]

    def test_appendix_inline_reference_not_a_header(self):
        """「附录2　问题1相关参数」里的「问题1相」数字后无分隔符 → 不得计入。"""
        subs = split_sub_questions(SAMPLE_FULLWIDTH)
        assert len(subs) == 4
        # 附录段落被从最后一问正文中截断
        assert "密度" not in subs[-1]["text"]

    def test_chinese_numerals_and_english(self):
        text = "问题一　第一个问题。\n\n问题二　第二个问题。\n"
        assert [s["label"] for s in split_sub_questions(text)] == ["Q1", "Q2"]
        en = "Question 1: build a model.\n\nQuestion 2: verify it.\n"
        assert [s["label"] for s in split_sub_questions(en)] == ["Q1", "Q2"]

    def test_no_header_returns_empty(self):
        assert split_sub_questions("这是一段没有任何子问题标题的文字。") == []

    def test_colon_form_still_supported(self):
        subs = split_sub_questions("问题1：建立模型。\n问题2：验证模型。")
        assert [s["label"] for s in subs] == ["Q1", "Q2"]


class TestClassifyTypes:
    def test_heat_diffusion_moving_boundary(self):
        tags = classify_types("药材烘干过程中的热传导与水分扩散，伴随失水收缩。")
        assert "heat_transfer" in tags
        assert "diffusion" in tags

    def test_bearing_localization(self):
        tags = classify_types("根据示向度采用交会定位法计算多边形定位区域。")
        assert "bearing_localization" in tags
        assert "wedge_intersection" in tags

    def test_empty_text_no_tags(self):
        assert classify_types("") == []

    def test_every_emitted_tag_exists_in_catalog_vocabulary(self):
        """不变量：profiler 产出的标签必须在方法卡 problem_types 词汇表内。

        否则检索永远不可能命中——这条测试防止后续擅自发明新标签。
        """
        vocab = set()
        for f in sorted(CARDS_DIR.glob("*.yaml")):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            vocab |= set(data.get("problem_types") or [])
        assert vocab, "方法卡词汇表为空，测试前提不成立"
        probes = [
            "热传导与水分扩散，含移动边界收缩",
            "示向度交会定位，覆盖搜索清除，机器狗演练模拟",
            "对方案综合评价与排序赋权",
            "时间序列预测与回归拟合",
            "排队服务系统与资源分配调度",
            "遗传算法求解多目标优化问题",
        ]
        for p in probes:
            for tag in classify_types(p):
                assert tag in vocab, f"标签 {tag!r} 不在方法卡词汇表中（源自 {p!r}）"


class TestUnderstandProblem:
    def test_subquestions_and_features(self):
        u = understand_problem(SAMPLE_FULLWIDTH)
        assert [s.label for s in u.sub_questions] == ["Q1", "Q2", "Q3", "Q4"]
        assert u.features["_features_source"] == "profiler-v1"
        assert u.features["has_data"] is True
        assert "per_question" in u.features
        assert set(u.per_question) == {"Q1", "Q2", "Q3", "Q4"}
        # 每问都有类型（第一问含几何/传热）
        assert u.sub_questions[0].problem_types

    def test_global_types_is_union_of_subquestions(self):
        u = understand_problem(SAMPLE_FULLWIDTH)
        for s in u.sub_questions:
            for t in s.problem_types:
                assert t in u.problem_types

    def test_empty_text_raises(self):
        with pytest.raises(ValueError):
            understand_problem("   ")


class TestLoadFromProject:
    def test_missing_inputs_returns_none(self, tmp_path):
        assert load_problem_understanding(tmp_path / "nothing") is None

    def test_reads_problem_txt(self, tmp_path):
        d = tmp_path / "proj" / "inputs"
        d.mkdir(parents=True)
        (d / "problem.txt").write_text(SAMPLE_FULLWIDTH, encoding="utf-8")
        u = load_problem_understanding(tmp_path / "proj")
        assert u is not None and len(u.sub_questions) == 4
        assert u.source == "problem_txt"

    def test_reads_question_spec_json(self, tmp_path):
        d = tmp_path / "proj" / "inputs"
        d.mkdir(parents=True)
        (d / "question_spec.json").write_text(
            '{"background": "背景", "problems": ['
            '{"id": "Q1", "title": "综合评价", "description": "对方案综合评价与排序"}]}',
            encoding="utf-8")
        u = load_problem_understanding(tmp_path / "proj")
        assert u is not None and u.source == "question_spec"
        assert [s.label for s in u.sub_questions] == ["Q1"]
        assert "evaluation" in u.sub_questions[0].problem_types


class TestSessionAutoDerivation:
    """生产入口：不传 questions / features 时由问题理解层派生（ADR-0008）。"""

    def _session(self, tmp_path, text=None, questions=None, **kw):
        from modeling_harness.runtime.execution.session import RuntimeSession
        proj = tmp_path / "proj"
        if text is not None:
            (proj / "inputs").mkdir(parents=True, exist_ok=True)
            (proj / "inputs" / "problem.txt").write_text(text, encoding="utf-8")
        return RuntimeSession(proj, questions, **kw)

    def test_questions_and_features_auto_derived(self, tmp_path):
        s = self._session(tmp_path, text=SAMPLE_FULLWIDTH)
        assert s.questions == ["Q1", "Q2", "Q3", "Q4"]
        assert s.features["_features_source"] == "profiler-v1"
        assert s.features["problem_types"]

    def test_explicit_questions_win(self, tmp_path):
        s = self._session(tmp_path, text=SAMPLE_FULLWIDTH,
                          questions=["Q001"])
        assert s.questions == ["Q001"]
        # 特征仍来自题面派生（显式 questions 不影响特征来源）
        assert s.features["_features_source"] == "profiler-v1"

    def test_explicit_features_win(self, tmp_path):
        s = self._session(tmp_path, text=SAMPLE_FULLWIDTH,
                          features={"problem_types": ["optimization"]})
        assert s.features["problem_types"] == ["optimization"]
        assert s.features["_features_source"] == "explicit"

    def test_no_inputs_raises(self, tmp_path):
        from modeling_harness.runtime.execution.session import SessionError
        with pytest.raises(SessionError):
            self._session(tmp_path, text=None, questions=None)

    def test_no_features_blocks_selection(self, tmp_path):
        """无注入、无题面 → 选型如实 BLOCKED，不得用默认画像冒充。"""
        from modeling_harness.runtime.execution.engine import BLOCKED
        s = self._session(tmp_path, text=None, questions=["Q001"])
        assert s.features.get("_features_source") == "absent"
        r = s.executor_impl.do_model_selection("model_selection")
        assert r.status == BLOCKED
        assert "ADR-0008" in r.reason

    def test_absent_but_external_model_does_not_fake_selection(self, tmp_path):
        """有外部模型注入但无题面：如实登记来源，不编造 card_id。

        只验证选型节点（do_model_selection）——外部 MODEL_IR 契约校验属
        model_construction 职责，此处只关心「不做方法族选型」这一事实。
        """
        s = self._session(tmp_path, text=None, questions=["Q001"],
                          external_model_irs={"Q001": {"model_id": "M-Q001"}})
        r = s.executor_impl.do_model_selection("model_selection")
        from modeling_harness.runtime.execution.engine import PASS
        assert r.status == PASS
        models = s.registry.list_by_type("model")
        assert models, "应登记容器模型"
        data = models[0].data or {}
        assert data.get("card_id") == "UNSELECTED"
        assert data.get("selection_status") == "external_constructor"
