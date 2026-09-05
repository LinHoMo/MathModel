"""E2E: V3 标准 / 失败恢复 / Per-Qi 局部重跑 三类完整研究运行。

运行: python -m pytest tests/e2e/test_research_runs.py -q
DAG Runtime 的核心能力不是 happy path 走通，而是中间失败后能正确恢复。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.composer import WorkflowComposer  # noqa: E402
from runtime.execution.engine import FAIL, PASS, NodeResult, WorkflowEngine  # noqa: E402
from runtime.state.model import ProjectState  # noqa: E402

WF = REPO / "core" / "workflows"
QIDS = ["Q001", "Q002", "Q003", "Q004"]


def _new_run(tmp_path):
    state = ProjectState(tmp_path / "state" / "status.json")
    comp = WorkflowComposer(WF)
    exp = comp.compose_executable(QIDS)
    return state, exp


class TestStandardResearchRun:
    def test_full_run_all_questions(self, tmp_path):
        """全 pass executor → 全部节点完成，State 与 Engine 一致。"""
        state, exp = _new_run(tmp_path)
        eng = WorkflowEngine(exp, lambda nid, ctx: NodeResult(PASS), state=state)
        result = eng.run()
        assert len(result["completed"]) == len(exp.nodes)
        assert eng.is_finished()
        wf = state.data["workflow"]
        assert len(wf["completed_nodes"]) == len(exp.nodes)
        assert wf["blocked_nodes"] == []


class TestFailureRecoveryRun:
    def test_transient_failure_recovers(self, tmp_path):
        """瞬时失败 → 重试恢复 → 最终全完成，日志含失败记录。"""
        state, exp = _new_run(tmp_path)
        seen = set()

        def executor(nid, ctx):
            if nid == "model_construction" and nid not in seen:
                seen.add(nid)
                return NodeResult(FAIL, "假设矛盾")
            return NodeResult(PASS)

        eng = WorkflowEngine(exp, executor, state=state)
        result = eng.run()
        assert len(result["completed"]) == len(exp.nodes)
        assert any(e["node"] == "model_construction" and e["status"] == FAIL
                   for e in eng.log)

    def test_persistent_failure_blocks_and_manual_recovery(self, tmp_path):
        """持续失败 → 反馈环耗尽 → 阻塞；人工 unblock 后恢复运行。"""
        state, exp = _new_run(tmp_path)
        target = "experiment_critique@Q002"
        assert target in exp.nodes

        calls = {target: 0}

        def executor(nid, ctx):
            if nid == target:
                calls[nid] += 1
                return NodeResult(FAIL, "证据始终不足")
            return NodeResult(PASS)

        eng = WorkflowEngine(exp, executor, state=state)
        eng.run()
        assert not eng.is_finished()
        # Q002 链路未完成 → 汇聚节点 evidence_build 不应完成
        assert "problem_analysis" in eng.completed
        assert "evidence_build" not in eng.completed

        # 人工解除阻塞 + 修复执行器 → 反馈环回滚上游重跑 → 全部完成
        eng.executor = lambda nid, ctx: NodeResult(PASS)
        for nid in list(eng.blocked):
            eng.unblock(nid)
        result = eng.run()
        assert len(result["completed"]) == len(exp.nodes), eng.blocked
        assert eng.is_finished()


class TestPartialQuestionRerun:
    def test_reset_question_isolated(self, tmp_path):
        """reset_question(Q001) 不影响 Q002–Q004 的完成状态。"""
        state, exp = _new_run(tmp_path)
        eng = WorkflowEngine(exp, lambda nid, ctx: NodeResult(PASS), state=state)
        eng.run()
        before = set(eng.completed)

        affected = eng.reset_question("Q001")
        assert all(nid.endswith("@Q001") or "@Q001" not in nid for nid in affected)
        others_done = {nid for nid in before
                       if "@Q002" in nid or "@Q003" in nid or "@Q004" in nid}
        assert others_done <= eng.completed

        # 补跑 Q001 → 重新全完成
        result = eng.run()
        assert len(result["completed"]) == len(exp.nodes)
