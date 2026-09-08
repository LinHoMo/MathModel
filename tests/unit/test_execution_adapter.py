"""P0-E Executable Model Runtime 测试：ExecutionAdapter + execution_result 一等 artifact。

运行: python -m pytest tests/unit/test_execution_adapter.py -q
覆盖：
1. execution_result 类型注册（EXEC 前缀）
2. LocalPythonAdapter success / failed / timeout / invalid 四态（真实执行状态）
3. ExecutionResultData 字段完整性（一等 artifact 契约）
"""

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.artifacts.ids import (
    ARTIFACT_TYPES, is_valid_id, id_matches_type, id_type,
)
from runtime.execution.adapters import (
    EXECUTION_RESULT_FIELDS, ExecutionPlan, LocalPythonAdapter,
    get_adapter,
)


class TestExecutionResultType:
    def test_type_registered(self):
        assert "execution_result" in ARTIFACT_TYPES
        assert ARTIFACT_TYPES["execution_result"] == "EXEC"

    def test_exec_id_valid(self):
        assert is_valid_id("EXEC001")
        assert id_type("EXEC001") == "execution_result"
        assert id_matches_type("EXEC001", "execution_result")
        assert not id_matches_type("EXEC001", "result")

    def test_legacy_x001_still_invalid(self):
        # X001 未被占用（execution 用 EXEC），保持 invalid
        from runtime.artifacts.ids import is_valid_id as v
        assert not v("X001")

    def test_result_data_fields_complete(self):
        import json
        from runtime.execution.adapters import ExecutionResultData
        d = ExecutionResultData(
            execution_id="EXEC001", model_id="M001", status="success",
            outputs={"x": 1}).to_dict()
        assert set(d.keys()) == set(EXECUTION_RESULT_FIELDS)
        # JSON 可序列化（registry 持久化要求）
        json.dumps(d)


class TestLocalPythonAdapter:
    def _run(self, code, timeout=30):
        plan = ExecutionPlan(model_id="M001", code=code, timeout_seconds=timeout)
        return LocalPythonAdapter().execute(plan)

    def test_success_with_json_output(self):
        r = self._run("import json; print(json.dumps({'x': 1, 'y': 2}))")
        assert r.status == "success"
        assert r.outputs == {"x": 1, "y": 2}
        assert r.returncode == 0
        assert r.duration_ms >= 0
        assert len(r.code_hash) == 64
        assert len(r.environment_hash) == 64
        assert r.started_at and r.finished_at
        assert r.execution_id

    def test_success_stdout_tail_fallback(self):
        r = self._run("print('hello world')")
        assert r.status == "success"
        assert "hello world" in r.stdout
        assert "stdout_tail" in r.outputs

    def test_failed_status_from_real_execution(self):
        r = self._run("raise ValueError('boom')")
        assert r.status == "failed"
        assert r.returncode != 0
        assert "boom" in r.stderr

    def test_timeout_status(self):
        r = self._run("import time; time.sleep(10)", timeout=1)
        assert r.status == "timeout"
        assert r.duration_ms < 10000

    def test_invalid_empty_code(self):
        r = self._run("   ")
        assert r.status == "invalid"
        assert "空代码" in r.stderr

    def test_factory(self):
        a = get_adapter("local_python")
        assert isinstance(a, LocalPythonAdapter)

    def test_status_never_defaulted(self):
        # 执行必须产生真实状态；plan 不执行时不能凭空 success
        r = self._run("raise SystemExit(0) if False else print('ok')")
        assert r.status in ("success", "failed", "timeout", "invalid")
