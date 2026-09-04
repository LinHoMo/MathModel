"""P1 Workflow DAG + Engine 测试：DAG 执行 / 条件分支 / 重试 / 反馈环 / partial rerun / Per-Qi。

运行: python -m pytest tests/unit/test_dag_engine.py -q
覆盖任务书 §36 Workflow Tests。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.execution.dag import DAGError, Node, WorkflowDAG
from runtime.execution.engine import (
    BLOCKED, FAIL, PASS, WAITING, EngineError, NodeResult, WorkflowEngine,
)


def make_dag(**overrides) -> WorkflowDAG:
    """小型标准 DAG: a → b → {c1, c2} → d，b 失败回退 a。"""
    nodes = {
        "a": Node("a", type="reasoning"),
        "b": Node("b", type="execution", depends_on=["a"], on_fail="a"),
        "c1": Node("c1", type="generation", depends_on=["b"]),
        "c2": Node("c2", type="generation", depends_on=["b"]),
        "d": Node("d", type="critique", depends_on=["c1", "c2"], validator="x"),
    }
    nodes.update(overrides)
    return WorkflowDAG(name="test", nodes=nodes)


class ScriptedExecutor:
    """按脚本回放结果的 executor: {node: [result1, result2, ...]}。"""

    def __init__(self, script):
        self.script = dict(script)
        self.calls: list[str] = []

    def __call__(self, node_id, context):
        self.calls.append(node_id)
        results = self.script.get(node_id, [])
        if results:
            r = results.pop(0)
            if isinstance(r, str):
                return NodeResult(r)
            return NodeResult(**r)
        return NodeResult(PASS)


class TestDagValidation:
    def test_valid_dag(self):
        assert make_dag().validate() == []

    def test_unknown_dependency(self):
        dag = make_dag()
        dag.nodes["d"].depends_on = ["ghost"]
        assert any("ghost" in p for p in dag.validate())

    def test_cycle_detection(self):
        dag = make_dag()
        dag.nodes["a"].depends_on = ["d"]   # a→b→c→d→a 成环
        problems = dag.validate()
        assert any("环" in p for p in problems)

    def test_on_fail_self_rejected(self):
        with pytest.raises(DAGError):
            Node("x", on_fail="x")

    def test_unknown_node_type(self):
        with pytest.raises(DAGError):
            Node("x", type="magic")

    def test_unknown_field(self):
        with pytest.raises(DAGError):
            Node("x", color="red")

    def test_validator_only_on_validation_nodes(self):
        with pytest.raises(DAGError):
            Node("x", type="reasoning", validator="v")


class TestEngineBasics:
    def test_sequential_execution(self):
        ex = ScriptedExecutor({})
        eng = WorkflowEngine(make_dag(), ex)
        eng.run()
        assert eng.completed == {"a", "b", "c1", "c2", "d"}
        assert eng.is_finished()

    def test_dependency_order_respected(self):
        ex = ScriptedExecutor({})
        eng = WorkflowEngine(make_dag(), ex)
        eng.run()
        assert ex.calls.index("a") < ex.calls.index("b")
        assert ex.calls.index("b") < ex.calls.index("c1")
        assert ex.calls.index("c1") < ex.calls.index("d")

    def test_ready_nodes(self):
        eng = WorkflowEngine(make_dag(), ScriptedExecutor({}))
        assert eng.ready() == ["a"]
        eng.step("a")
        assert eng.ready() == ["b"]
        eng.step("b")
        assert eng.ready() == ["c1", "c2"]   # 并行组就绪

    def test_step_requires_ready(self):
        eng = WorkflowEngine(make_dag(), ScriptedExecutor({}))
        with pytest.raises(EngineError):
            eng.step("d")   # 依赖未满足

    def test_invalid_dag_rejected(self):
        dag = make_dag()
        dag.nodes["a"].depends_on = ["d"]   # 环
        with pytest.raises(EngineError):
            WorkflowEngine(dag, ScriptedExecutor({}))


class TestRetriesAndFeedback:
    def test_fail_then_pass_within_retries(self):
        ex = ScriptedExecutor({"b": [FAIL, PASS]})
        eng = WorkflowEngine(make_dag(), ex)
        eng.run()
        assert "b" in eng.completed
        assert eng.retries["b"] == 1

    def test_exhausted_retries_triggers_feedback_loop(self):
        """b 失败 3 轮（max_retries=3）→ 回退到 a，a 及下游重置（retries 一并清零）。"""
        ex = ScriptedExecutor({"b": [FAIL, FAIL, FAIL]})
        eng = WorkflowEngine(make_dag(), ex)
        eng.step("a")
        for _ in range(3):
            eng.step("b")
        assert "b" not in eng.completed
        # 3 轮失败记录: 2 次 retry + 1 次耗尽回退
        fails = [e for e in eng.log if e["node"] == "b" and e["status"] == FAIL]
        assert len(fails) == 3
        assert any("rollback" in e["detail"] for e in fails)
        # 反馈环: b 的失败把 a（及其下游）重置
        assert "a" not in eng.completed
        assert "b" not in eng.retries   # 重置时清零

    def test_blocked_when_no_on_fail(self):
        dag = make_dag()
        dag.nodes["b"].on_fail = None
        ex = ScriptedExecutor({"b": [FAIL, FAIL, FAIL]})
        eng = WorkflowEngine(dag, ex)
        eng.step("a")
        for _ in range(3):
            result = eng.step("b")   # 3 轮失败（max_retries=3）
        assert eng.blocked.get("b")
        assert eng.ready() == []           # 无可执行节点
        # 恢复
        eng.unblock("b")
        assert "b" not in eng.blocked

    def test_max_retries_custom(self):
        dag = make_dag()
        dag.nodes["b"].max_retries = 1
        ex = ScriptedExecutor({"b": [FAIL]})
        eng = WorkflowEngine(dag, ex)
        eng.step("a")
        result = eng.step("b")   # 1 轮即耗尽 → 反馈环回退 a
        assert result.status == FAIL
        assert "a" not in eng.completed
        assert "b" not in eng.completed


class TestConditionalAndApproval:
    def test_human_approval_gate(self):
        dag = make_dag()
        dag.nodes["d"].human_approval = True
        ex = ScriptedExecutor({})
        eng = WorkflowEngine(dag, ex)
        eng.step("a"); eng.step("b"); eng.step("c1"); eng.step("c2")
        result = eng.step("d")
        assert result.status == WAITING
        assert "d" in eng.waiting
        assert eng.ready() == []           # 等待人工放行
        eng.approve("d")
        eng.step("d")
        assert "d" in eng.completed

    def test_executor_blocked(self):
        ex = ScriptedExecutor({"c1": [{"status": BLOCKED, "reason": "外部依赖不可用"}]})
        eng = WorkflowEngine(make_dag(), ex)
        eng.step("a"); eng.step("b")
        eng.step("c1")
        assert "c1" in eng.blocked
        # c2 仍可执行（独立分支）
        eng.step("c2")
        assert "c2" in eng.completed
        # d 不 ready（c1 阻塞）
        assert "d" not in eng.ready()


class TestPartialRerun:
    def test_reset_to_clears_downstream_only(self):
        ex = ScriptedExecutor({})
        eng = WorkflowEngine(make_dag(), ex)
        eng.run()
        affected = eng.reset_to("b")
        assert affected == {"b", "c1", "c2", "d"}
        assert eng.completed == {"a"}
        assert eng.ready() == ["b"]

    def test_reset_branch_leaves_sibling_alone(self):
        ex = ScriptedExecutor({})
        eng = WorkflowEngine(make_dag(), ex)
        eng.run()
        eng.reset_to("c1")
        # c1 的下游 d 一并重置（d 依赖 c1），兄弟分支 c2 不动
        assert eng.completed == {"a", "b", "c2"}
        assert eng.ready() == ["c1"]


class TestPerQuestion:
    def build_per_q_dag(self) -> WorkflowDAG:
        """problem → experiment*(per_question) → evidence → sections*(per_question)。"""
        nodes = {
            "problem": Node("problem", type="reasoning"),
            "experiment": Node("experiment", type="execution", per_question=True,
                               depends_on=["problem"]),
            "evidence": Node("evidence", type="validation", validator="evidence-gate",
                             depends_on=["experiment*"]),
            "sections": Node("sections", type="generation", per_question=True,
                             depends_on=["paper_proj"]),
            "paper_proj": Node("paper_proj", type="projection", depends_on=["evidence"]),
        }
        return WorkflowDAG(name="pq", nodes=nodes)

    def test_expand_questions(self):
        dag = self.build_per_q_dag()
        exp = dag.expand_questions(["Q001", "Q002", "Q003"])
        assert "experiment@Q001" in exp.nodes
        assert "experiment@Q002" in exp.nodes
        assert "experiment@Q003" in exp.nodes
        assert "sections@Q001" in exp.nodes
        # evidence 依赖全部 experiment 实例
        assert set(exp.nodes["evidence"].depends_on) == {
            "experiment@Q001", "experiment@Q002", "experiment@Q003"}
        assert exp.validate() == []

    def test_expand_preserves_on_fail_locality(self):
        nodes = {
            "design": Node("design", type="reasoning"),
            "experiment": Node("experiment", type="execution", per_question=True,
                               depends_on=["design"], on_fail="design"),
        }
        exp = WorkflowDAG(name="x", nodes=nodes).expand_questions(["Q001", "Q002"])
        assert exp.nodes["experiment@Q001"].on_fail == "design"
        assert exp.nodes["experiment@Q002"].on_fail == "design"

    def test_per_qi_rerun_only_touches_that_question(self):
        """任务书 §9: Q2 失败只重跑 Q2，Q1/Q3 不被无意义重跑。"""
        dag = self.build_per_q_dag()
        exp = dag.expand_questions(["Q001", "Q002", "Q003"])
        ex = ScriptedExecutor({})
        eng = WorkflowEngine(exp, ex)
        eng.run()
        assert eng.completed == set(exp.nodes)

        affected = eng.reset_question("Q002")
        assert "experiment@Q002" in affected
        assert "sections@Q002" in affected
        # 其他 Question 的节点未被重置
        assert "experiment@Q001" in eng.completed
        assert "experiment@Q003" in eng.completed
        assert "sections@Q001" in eng.completed

    def test_q_failure_does_not_block_siblings(self):
        dag = self.build_per_q_dag()
        exp = dag.expand_questions(["Q001", "Q002"])
        # Q002 的实验永远失败且无 on_fail → 阻塞自己的分支
        ex = ScriptedExecutor({"experiment@Q002": [
            FAIL, FAIL, FAIL, FAIL, FAIL, FAIL]})
        eng = WorkflowEngine(exp, ex)
        eng.run()
        assert "experiment@Q001" in eng.completed
        assert "experiment@Q002" in eng.blocked
        # evidence 依赖两个实验 → 不 ready
        assert "evidence" not in eng.ready()
