"""P0-E Executable Model Runtime 集成测试：do_experiment 真实执行链路。

验证：
1. 未提供 adapter 时：result.status == "not_executed"（现有行为，不回归）
2. 提供 adapter 但无 code：result.status == "not_executed"（静默回退）
3. 提供 adapter + code：真实执行 → execution_result（EXEC）artifact 登记，
   result.status 来自真实状态（success/failed/timeout/invalid）
4. Evidence 绑定：execution_result 以 executed_by 边挂到 result
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402


def _session(tmp_path, adapter=None):
    s = RuntimeSession(tmp_path / "proj", ["Q001"], max_workers=1,
                       execution_adapter=adapter)
    return s


def _find_result(s):
    for a in s.registry.list_by_type("result"):
        if a.question == "Q001":
            return a
    return None


class TestDoExperimentExecutionIntegration:
    def test_no_adapter_keeps_not_executed(self, tmp_path):
        s = _session(tmp_path, adapter=None)
        s.run()
        r = _find_result(s)
        assert r is not None
        assert r.data.get("status") == "not_executed"
        # 无 EXEC artifact
        assert not s.registry.list_by_type("execution_result")

    def test_adapter_without_code_keeps_not_executed(self, tmp_path):
        s = _session(tmp_path, adapter=LocalPythonAdapter())
        s.run()   # plan 无 code → 不执行
        r = _find_result(s)
        assert r.data.get("status") == "not_executed"

    def test_adapter_with_code_executes_and_updates_status(self, tmp_path):
        s = _session(tmp_path, adapter=LocalPythonAdapter())
        # 注入可执行代码（外部 executor / 未来 code generator 路径）
        plan_code = "import json; print(json.dumps({'answer': 42}))"
        for qid in s.questions:
            s.executor_impl.shared.setdefault(qid, {})["plan"] = {"code": plan_code}
        s.run()
        r = _find_result(s)
        assert r.data.get("status") == "success"
        assert r.data.get("value") == {"answer": 42}
        execs = s.registry.list_by_type("execution_result")
        assert len(execs) == 1
        x = execs[0]
        assert x.data["status"] == "success"
        assert x.data["execution_id"]
        assert x.data["code_hash"]
        assert x.data["environment_hash"]
        # Evidence 绑定：result executed_by execution_result
        rels = {(rel["from"], rel["relation"], rel["to"])
                for rel in s.graph.relations}
        assert (r.artifact_id, "executed_by", x.artifact_id) in rels

    def test_adapter_failed_code_yields_failed_status(self, tmp_path):
        s = _session(tmp_path, adapter=LocalPythonAdapter())
        for qid in s.questions:
            s.executor_impl.shared.setdefault(qid, {})["plan"] = {
                "code": "raise ValueError('model divergence')"}
        s.run()
        r = _find_result(s)
        assert r.data.get("status") == "failed"
        execs = s.registry.list_by_type("execution_result")
        assert len(execs) == 1
        assert "model divergence" in execs[0].data["stderr"]
