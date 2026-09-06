"""P1 Workflow Composition 测试：base + stages + competition → 可执行 DAG。

运行: python -m pytest tests/unit/test_workflow_compose.py -q
同时覆盖 yamlio 子集解析器。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.execution.composer import ComposeError, WorkflowComposer
from runtime.execution.yamlio import YamlSyntaxError, loads

WF = REPO / "core" / "workflows"


class TestYamlio:
    def test_nested_map(self):
        out = loads("a:\n  b: 1\n  c: [x, y]\n")
        assert out == {"a": {"b": 1, "c": ["x", "y"]}}

    def test_list_of_scalars(self):
        out = loads("items:\n  - a\n  - b\n")
        assert out == {"items": ["a", "b"]}

    def test_list_of_maps(self):
        out = loads("edges:\n  - from: a\n    to: b\n  - from: b\n    to: c\n")
        assert out == {"edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "c"}]}

    def test_scalars(self):
        out = loads('i: 3\nf: 1.5\nb: true\nn: null\nq: "hello world"\ns: no-quote')
        assert out == {"i": 3, "f": 1.5, "b": True, "n": None,
                       "q": "hello world", "s": "no-quote"}

    def test_comments_ignored(self):
        out = loads("# header\nkey: value  # tail comment\n")
        assert out == {"key": "value"}

    def test_hash_inside_quotes_preserved(self):
        out = loads('key: "a # b"\n')
        assert out == {"key": "a # b"}

    def test_tab_rejected(self):
        with pytest.raises(YamlSyntaxError):
            loads("a:\n\tb: 1\n")

    def test_bad_line_rejected(self):
        with pytest.raises(YamlSyntaxError):
            loads("just a sentence\n")

    def test_nested_map_value(self):
        out = loads("node:\n  type: critique\n  on_fail: back\n  per_question: true\n")
        assert out["node"] == {"type": "critique", "on_fail": "back",
                               "per_question": True}


class TestComposer:
    def test_base_loads(self):
        comp = WorkflowComposer(WF)
        base = comp.load_base()
        assert base["stages"] == ["problem-analysis", "modeling", "experiment",
                                  "evidence", "paper"]

    def test_compose_default(self):
        comp = WorkflowComposer(WF)
        dag = comp.compose()
        problems = dag.validate()
        assert problems == []
        # 关键节点存在
        for nid in ("problem_analysis", "literature_search", "model_selection",
                    "model_construction", "model_critique", "assumption_check",
                    "experiment_design", "evidence_build", "evidence_gate",
                    "research_direction", "paper_projection", "paper_review"):
            assert nid in dag.nodes, nid

    def test_stage_ordering(self):
        comp = WorkflowComposer(WF)
        dag = comp.compose()
        # 跨 stage 串联: problem_analysis → literature_search → model_selection
        assert "problem_analysis" in dag.nodes["literature_search"].depends_on
        assert "literature_search" in dag.nodes["model_selection"].depends_on
        assert "assumption_check" in dag.nodes["experiment_design"].depends_on
        # P9: quality_evaluation 插入 evidence_gate 与 research_direction 之间
        assert "quality_evaluation" in dag.nodes["research_direction"].depends_on
        assert "evidence_gate" in dag.nodes["quality_evaluation"].depends_on

    def test_feedback_loops_present(self):
        comp = WorkflowComposer(WF)
        dag = comp.compose()
        assert dag.nodes["model_critique"].on_fail == "model_construction"
        assert dag.nodes["evidence_gate"].on_fail == "experiment_design"
        assert dag.nodes["quality_evaluation"].on_fail == "evidence_build"
        assert dag.nodes["paper_review"].on_fail == "paper_projection"

    def test_compose_with_competition(self):
        comp = WorkflowComposer(WF)
        dag = comp.compose("cumcm")
        assert dag.validate() == []
        dag2 = comp.compose("mcm")
        assert dag2.validate() == []

    def test_unknown_competition_rejected(self):
        comp = WorkflowComposer(WF)
        with pytest.raises(ComposeError):
            comp.compose("neurips")

    def test_per_question_expansion(self):
        comp = WorkflowComposer(WF)
        exp = comp.compose_executable(["Q001", "Q002", "Q003", "Q004"])
        # per_question 节点按 Qi 展开
        for qi in ("Q001", "Q002", "Q003", "Q004"):
            assert f"experiment@{qi}" in exp.nodes
            assert f"paper_sections@{qi}" in exp.nodes
        # 模板节点被移除
        assert "experiment" not in exp.nodes
        assert "paper_sections" not in exp.nodes
        # evidence_build 依赖全部实验批判实例（P3 起 experiment_critique 前置）
        assert set(exp.nodes["evidence_build"].depends_on) == {
            f"experiment_critique@{q}" for q in ("Q001", "Q002", "Q003", "Q004")}
        # experiment_critique 依赖实验实例并带反馈环
        assert set(exp.nodes["experiment_critique@Q001"].depends_on) == {"experiment@Q001"}
        assert exp.nodes["experiment_critique@Q001"].on_fail == "experiment@Q001"
        assert exp.validate() == []

    def test_executable_dag_runs_end_to_end(self):
        """可执行 DAG + 全 pass executor → 全节点完成（结构完整性冒烟）。"""
        from runtime.execution.engine import WorkflowEngine

        class AllPass:
            def __call__(self, node_id, ctx):
                from runtime.execution.engine import NodeResult
                return NodeResult("pass")

        comp = WorkflowComposer(WF)
        exp = comp.compose_executable(["Q001", "Q002"])
        eng = WorkflowEngine(exp, AllPass())
        result = eng.run()
        assert result["total"] == len(exp.nodes)
        assert len(result["completed"]) == len(exp.nodes)
        assert not result["blocked"]

    def test_all_workflow_files_parse(self):
        """workflows/ 下所有 YAML 必须可解析（防止手改语法漂移）。"""
        for f in sorted(WF.rglob("*.yaml")):
            data = loads(f.read_text(encoding="utf-8"))
            assert isinstance(data, dict), f
