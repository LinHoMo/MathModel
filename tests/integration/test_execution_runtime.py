"""P0-E Executable Model Runtime 集成测试：do_experiment 真实执行链路。

验证（audit FIX-1.2/1.5 迁移到新契约——代码经 MIR→implemented_by→code 链，
不再注入旧 shared[qid]["plan"]）：
1. 未提供 adapter 时：无 EXEC artifact，result 保持 not_executed，且 DAG
   如实失败传播（evidence_build FAIL → 反馈环收敛 blocked，不再假 PASS）
2. 提供 adapter + code：真实执行 → execution_result（EXEC）artifact 登记，
   result.status 来自真实状态（success/failed/timeout/invalid）
3. Evidence 绑定：execution_result 以 executed_by 边挂到 result
4. 失败代码：EXEC status=failed + stderr 真实，DAG 失败传播可见
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests" / "integration"))

from _real_session import make_real_session  # noqa: E402
from modeling_harness.runtime.execution.adapters import LocalPythonAdapter  # noqa: E402


def _find_result(s):
    for a in s.registry.list_by_type("result"):
        if a.question == "Q001":
            return a
    return None


def _exec_by_edge(s, rid):
    """code artifact 的 executed_by 边指向的 EXEC（code → EXEC → result 谱系）。"""
    for rel in s.graph.relations:
        if rel["from"] == rid and rel["relation"] == "executed_by":
            return rel["to"]
    return None


class TestDoExperimentExecutionIntegration:
    def test_no_adapter_keeps_not_executed_and_fails_honestly(self, tmp_path):
        """无 adapter：不产生 EXEC；无数值执行 → 证据链如实 FAIL（不假 PASS）。"""
        from modeling_harness.runtime.execution.session import RuntimeSession
        s = RuntimeSession(tmp_path / "proj", ["Q001"], max_workers=1,
                           execution_adapter=None)
        s.run()
        assert not s.registry.list_by_type("execution_result")
        # 新门禁（FIX-1.2/1.4）：无数值执行时 evidence_build 如实 FAIL，
        # 反馈环收敛为 blocked（禁止 200 次死循环 + 禁止占位 claim 假 PASS）
        assert s.engine.failures or s.engine.blocked, \
            "无数值执行必须如实失败传播，不得静默 PASS"
        claims = [c for c in s.registry.list_by_type("claim")
                  if not (c.data or {}).get("placeholder")]
        assert not claims, "无数值事实时不得有非占位 claim"

    def test_adapter_with_code_executes_and_updates_status(self, tmp_path):
        """adapter + 注入 code：真 subprocess → EXEC success + executed_by 边。"""
        s = make_real_session(tmp_path, questions=("Q001",))
        r = _find_result(s)
        assert r is not None
        execs = s.registry.list_by_type("execution_result")
        assert len(execs) == 1
        x = execs[0]
        assert x.data["status"] == "success"
        assert x.data["execution_id"]
        assert x.data["code_hash"]
        assert x.data["environment_hash"]
        # Evidence 绑定：code → executed_by → EXEC → produces → result 谱系
        code_id = next(a.artifact_id for a in s.registry.list_by_type("code"))
        ex_id = _exec_by_edge(s, code_id)
        assert ex_id == x.artifact_id
        assert any(rel["from"] == x.artifact_id and rel["relation"] == "produces"
                   and rel["to"] == r.artifact_id for rel in s.graph.relations)
        # 全 DAG 无阻塞（真实闭环成立）
        assert not s.engine.blocked and not s.engine.failures

    def test_adapter_failed_code_yields_failed_status(self, tmp_path):
        """失败代码：EXEC status=failed + stderr 真实；失败如实传播。"""
        s = make_real_session(tmp_path, questions=("Q001",), run=False)
        # 覆盖注入的 code 为失败代码（外部 Model Constructor 产物；须满足 L0 ABI）
        s.executor_impl.shared["external_code"]["Q001"] = (
            "def solve(inputs):\n"
            "    raise ValueError('model divergence')\n\n"
            "if __name__ == '__main__':\n"
            "    import json\n"
            "    print(json.dumps(solve({})))\n"
        )
        s.run()
        execs = s.registry.list_by_type("execution_result")
        assert len(execs) == 1
        x = execs[0]
        assert x.data["status"] == "failed"
        assert "model divergence" in x.data["stderr"]
        # FIX-1.2：失败必须真实传播（不得默认 PASS）
        assert s.engine.failures or s.engine.blocked, \
            "执行失败必须传播到 DAG（evidence 无法由失败产物支撑）"
