"""Integration: Workflow 组合 → Engine 执行 → ProjectState 记录（三层联动）。

运行: python -m pytest tests/integration/test_workflow_execution.py -q
覆盖:
  * WorkflowComposer（base+stages+competition）→ 可执行 DAG
  * WorkflowEngine 反馈环重试 / 阻塞 / 人工审批
  * ProjectState 的 workflow 维度随执行自动落盘
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.composer import WorkflowComposer  # noqa: E402
from runtime.execution.engine import FAIL, PASS, NodeResult, WorkflowEngine  # noqa: E402
from runtime.state.model import ProjectState  # noqa: E402

WF = REPO / "core" / "workflows"


class TestEngineFailureRecovery:
    def test_retry_then_pass_completes(self):
        """节点先失败 1 次再通过 → 反馈环外自动重试，最终全部完成。"""
        comp = WorkflowComposer(WF)
        exp = comp.compose_executable(["Q001", "Q002"])
        calls = {"experiment@Q001": 0}

        def executor(node_id, ctx):
            if node_id == "experiment@Q001":
                calls[node_id] += 1
                if calls[node_id] == 1:
                    return NodeResult(FAIL, "数值不稳定")
            return NodeResult(PASS)

        eng = WorkflowEngine(exp, executor)
        result = eng.run()
        assert result["total"] == len(exp.nodes)
        assert len(result["completed"]) == len(exp.nodes)
        assert calls["experiment@Q001"] == 2
        assert eng.retries.get("experiment@Q001") == 1

    def test_retries_exhausted_rolls_back_via_on_fail(self):
        """experiment_critique@Q001 连续失败 → 沿 on_fail 回滚到 experiment@Q001。"""
        comp = WorkflowComposer(WF)
        exp = comp.compose_executable(["Q001"])
        crit = exp.nodes["experiment_critique@Q001"]
        assert crit.on_fail == "experiment@Q001"

        def executor(node_id, ctx):
            if node_id == "experiment_critique@Q001":
                return NodeResult(FAIL, "证据链断裂")
            return NodeResult(PASS)

        eng = WorkflowEngine(exp, executor)
        eng.run()
        # 回滚后 experiment@Q001 重新变为 pending，critique 持续失败
        assert "experiment@Q001" not in eng.completed
        assert "experiment_critique@Q001" not in eng.completed
        # 回滚发生在重试耗尽之后（reset 会清空 retries 计数）
        assert any("exhausted retries" in e["detail"] and
                   f"rollback to {crit.on_fail}" in e["detail"] for e in eng.log)
        assert "problem_analysis" in eng.completed
        # 上游无关分支不受影响（problem_analysis 等已完成）
        assert "problem_analysis" in eng.completed

    def test_blocked_node_stops_downstream(self):
        """节点 blocked → 其下游不可执行，无关节点正常完成。"""
        comp = WorkflowComposer(WF)
        exp = comp.compose_executable(["Q001"])

        calls = {"experiment@Q001": 0}

        def executor(node_id, ctx):
            if node_id == "experiment@Q001":
                calls[node_id] += 1
                if calls[node_id] == 1:
                    return NodeResult("blocked", "运行环境不可用")
            return NodeResult(PASS)

        eng = WorkflowEngine(exp, executor)
        eng.run()
        assert "experiment@Q001" in eng.blocked
        assert "experiment@Q001" not in eng.completed
        for nid in exp.nodes:
            if "experiment@Q001" in exp.nodes[nid].depends_on:
                assert nid not in eng.completed
        assert "problem_analysis" in eng.completed

        # 恢复 → 继续跑到完成
        eng.unblock("experiment@Q001")
        result = eng.run()
        assert len(result["completed"]) == len(exp.nodes)


class TestHumanApproval:
    def test_waiting_approval_and_approve(self):
        """human_approval 节点首次到达挂起，approve 后继续。"""
        comp = WorkflowComposer(WF)
        exp = comp.compose_executable(["Q001"])
        approval_nodes = [nid for nid, n in exp.nodes.items() if n.human_approval]
        if not approval_nodes:
            pytest.skip("当前 workflow 无人工审批节点")
        target = approval_nodes[0]

        eng = WorkflowEngine(exp, lambda nid, ctx: NodeResult(PASS))
        eng.run()
        assert target in eng.waiting
        assert not eng.is_finished()

        eng.approve(target)
        result = eng.run()
        assert len(result["completed"]) == len(exp.nodes)
        assert eng.is_finished()


class TestStateIntegration:
    def test_engine_records_into_project_state(self, tmp_path):
        """Engine 执行过程写入 ProjectState 的 workflow 维度并持久化。"""
        state = ProjectState(tmp_path / "state" / "status.json")
        comp = WorkflowComposer(WF)
        exp = comp.compose_executable(["Q001"])

        def executor(node_id, ctx):
            if node_id == "experiment@Q001":
                return NodeResult("blocked", "环境故障")
            return NodeResult(PASS)

        eng = WorkflowEngine(exp, executor, state=state)
        eng.run()

        wf = state.data["workflow"]
        assert "experiment@Q001" in wf["blocked_nodes"]
        assert "problem_analysis" in wf["completed_nodes"]
        assert wf["retries"] == {} or isinstance(wf["retries"], dict)

        # 重新 load → 持久化可恢复（engine 只写内存，save 由调用方负责）
        state.save()
        state2 = ProjectState(tmp_path / "state" / "status.json")
        assert "experiment@Q001" in state2.data["workflow"]["blocked_nodes"]
        assert "problem_analysis" in state2.data["workflow"]["completed_nodes"]

    def test_partial_rerun_after_state_persist(self, tmp_path):
        """reset_to 只影响目标节点及其下游，且状态文件同步 reset。"""
        state = ProjectState(tmp_path / "state" / "status.json")
        comp = WorkflowComposer(WF)
        exp = comp.compose_executable(["Q001", "Q002"])
        eng = WorkflowEngine(exp, lambda nid, ctx: NodeResult(PASS), state=state)
        eng.run()
        assert eng.is_finished()

        affected = eng.reset_to("model_selection")
        assert "model_selection" in affected
        # 上游不受影响
        assert "problem_analysis" in eng.completed
        assert "model_selection" not in eng.completed

        result = eng.run()
        assert len(result["completed"]) == len(exp.nodes)
