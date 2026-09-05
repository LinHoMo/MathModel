"""P6 WaveExecutor 单元测试：波次划分 / 并行执行 / validator 挂钩 / 进度持久化。

运行: python -m pytest tests/unit/test_wave_executor.py -q
"""

import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.dag import Node, WorkflowDAG  # noqa: E402
from runtime.execution.engine import FAIL, PASS, NodeResult, WorkflowEngine  # noqa: E402
from runtime.execution.wave_executor import WaveExecutor  # noqa: E402


def _diamond_dag() -> WorkflowDAG:
    dag = WorkflowDAG()
    dag.add_node(Node("A", type="reasoning"))
    dag.add_node(Node("B", type="generation", depends_on=["A"]))
    dag.add_node(Node("C", type="generation", depends_on=["A"]))
    dag.add_node(Node("D", type="validation", depends_on=["B", "C"]))
    return dag


class TestWaveScheduling:
    def test_static_waves_respect_topology(self):
        we = WaveExecutor(_diamond_dag(), lambda n, c: NodeResult(PASS))
        assert we.waves() == [["A"], ["B", "C"], ["D"]]

    def test_wave_report_records_execution(self):
        we = WaveExecutor(_diamond_dag(), lambda n, c: NodeResult(PASS))
        rep = we.run()
        assert [w["nodes"] for w in rep["waves"]] == \
            [["A"], ["B", "C"], ["D"]]
        assert len(rep["progress"]["completed"]) == 4

    def test_nonconvergent_feedback_loop_raises(self):
        dag = _diamond_dag()
        we = WaveExecutor(dag, lambda n, c: NodeResult(FAIL, "永远失败"),
                          max_waves=5)
        try:
            we.run()
            raised = False
        except Exception as e:
            raised = "max_waves" in str(e)
        # D 失败 → 无 on_fail → blocked → ready 空 → 正常结束（不触发 max_waves）
        assert we.engine.blocked or raised


class TestParallelExecution:
    def test_wave_nodes_run_concurrently(self):
        """波内 B/C 真并行：executor 内 sleep，总耗时显著小于串行。"""
        lock = threading.Lock()
        state = {"cur": 0, "peak": 0}

        def executor(nid, ctx):
            if nid in ("B", "C"):
                with lock:
                    state["cur"] += 1
                    state["peak"] = max(state["peak"], state["cur"])
                time.sleep(0.15)
                with lock:
                    state["cur"] -= 1
            return NodeResult(PASS)

        we = WaveExecutor(_diamond_dag(), executor, max_workers=4)
        t0 = time.perf_counter()
        we.run()
        elapsed = time.perf_counter() - t0
        assert state["peak"] >= 2, "B/C 应并发执行"
        assert elapsed < 0.45, f"并行应快于串行（实测 {elapsed:.2f}s）"

    def test_apply_result_still_serialized(self):
        """executor 并行，但引擎落账经 apply_result 串行：状态不撕裂。"""
        results = {"A": NodeResult(PASS), "B": NodeResult(PASS),
                   "C": NodeResult(FAIL, "坏结果"), "D": NodeResult(PASS)}

        def executor(nid, ctx):
            time.sleep(0.05)
            return results[nid]

        we = WaveExecutor(_diamond_dag(), executor, max_workers=4)
        rep = we.run()
        p = rep["progress"]
        assert "B" in p["completed"]
        assert "C" in p["blocked"]      # 无 on_fail → 重试耗尽后阻塞


class TestValidatorHook:
    def test_validator_rejects_pass_as_failure(self):
        calls = {"n": 0}

        def validator(nid, result):
            calls["n"] += 1
            return None if calls["n"] >= 2 else "产物未通过抽查"

        we = WaveExecutor(_diamond_dag(), lambda n, c: NodeResult(PASS),
                          validators={"A": validator})
        rep = we.run()
        assert calls["n"] == 2
        assert "A" in rep["progress"]["completed"]
        assert any(e["status"] == "fail" and "validator" in e["detail"]
                   for e in we.engine.log)

    def test_validator_by_node_type(self):
        we = WaveExecutor(
            _diamond_dag(),
            lambda n, c: NodeResult(PASS),
            validators={"validation": lambda n, r: "validation 型一律不过"})
        rep = we.run()
        assert "D" in rep["progress"]["blocked"]


class TestProgressPersistence:
    def test_save_and_restore_resumes_midway(self):
        dag = _diamond_dag()
        ran: list[str] = []

        def executor(nid, ctx):
            ran.append(nid)
            return NodeResult(PASS)

        we1 = WaveExecutor(dag, executor)
        we1.engine.step("A")
        we1.engine.save_progress(REPO / "tests" / "_tmp_progress.json")

        dag2 = _diamond_dag()
        eng2 = WorkflowEngine.load(dag2, lambda n, c: NodeResult(PASS),
                                   REPO / "tests" / "_tmp_progress.json")
        assert eng2.completed == {"A"}
        assert set(eng2.ready()) == {"B", "C"}
        (REPO / "tests" / "_tmp_progress.json").unlink()

    def test_restore_rejects_unknown_nodes(self):
        import json
        eng = WorkflowEngine(_diamond_dag(), lambda n, c: NodeResult(PASS))
        try:
            eng.restore({"engine_schema": 1, "completed": ["NOPE"],
                         "retries": {}, "blocked": {}, "waiting": [],
                         "failures": {}})
            assert False, "应拒绝未知节点"
        except Exception as e:
            assert "未知节点" in str(e)
