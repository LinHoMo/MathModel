# -*- coding: utf-8 -*-
"""P3-1 验收：E2B Execution Backend。

- 无 E2B_API_KEY/SDK → available()=False，select_execution_adapter()
  自动回退 LocalPythonAdapter（真实执行不受影响）。
- 显式选择 e2b 但不可用 → execute 如实 invalid（绝不假装 success）。
- mock e2b Sandbox 可用时 → execute 走沙箱路径，输出格式/execution_token
  与 LocalPythonAdapter 完全一致（adapter 签发，The Agent Is Not The State）。
"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.execution.adapters import (  # noqa: E402
    LocalPythonAdapter, ExecutionPlan,
)
from modeling_harness.runtime.execution.e2b_adapter import (  # noqa: E402
    E2BAdapter, select_execution_adapter,
)


def _plan(code: str):
    return ExecutionPlan(code=code, model_id="M001", inputs={},
                         workdir=None, env={}, timeout_seconds=30)


class TestE2BUnavailable:
    def test_available_false_without_key(self, monkeypatch):
        monkeypatch.delenv("E2B_API_KEY", raising=False)
        assert E2BAdapter.available() is False

    def test_factory_falls_back_to_local(self, monkeypatch):
        monkeypatch.delenv("E2B_API_KEY", raising=False)
        adapter = select_execution_adapter()
        assert isinstance(adapter, LocalPythonAdapter), \
            "E2B 不可用必须自动回退 LocalPythonAdapter"

    def test_explicit_e2b_unavailable_reports_invalid(self, monkeypatch):
        monkeypatch.delenv("E2B_API_KEY", raising=False)
        adapter = select_execution_adapter("e2b")
        assert isinstance(adapter, E2BAdapter)
        r = adapter.execute(_plan("print(1)"))
        assert r.status == "invalid", \
            "不可用的后端必须如实 invalid，不得默认 success"
        assert "E2B 不可用" in (r.stderr or "")

    def test_fallback_local_still_executes(self, monkeypatch):
        monkeypatch.delenv("E2B_API_KEY", raising=False)
        adapter = select_execution_adapter()
        r = adapter.execute(
            _plan('import json; print(json.dumps({"y": 7}))'))
        assert r.status == "success"
        assert r.outputs == {"y": 7}
        assert r.execution_token, "adapter 必须签发 execution_token"


class TestE2BAvailable:
    @pytest.fixture()
    def fake_e2b(self, monkeypatch):
        """注入假 e2b SDK + 假 Sandbox（验证 e2b 执行路径与输出契约）。"""
        import json

        class FakeProcess:
            def __init__(self, code):
                # 真实执行 code（模拟沙箱内 python3 运行）
                import subprocess
                import tempfile

                self.stdout = ""
                self.stderr = ""
                self.exit_code = 0
                try:
                    with tempfile.NamedTemporaryFile(
                            "w", suffix=".py", delete=False) as f:
                        f.write(code)
                        fname = f.name
                    p = subprocess.run([sys.executable, fname],
                                       capture_output=True, text=True,
                                       timeout=30)
                    self.stdout = p.stdout
                    self.stderr = p.stderr
                    self.exit_code = p.returncode
                except Exception as e:
                    self.stderr = str(e)
                    self.exit_code = 1

            def wait(self):
                return self

        class FakeFS:
            def __init__(self):
                self.files = {}

            def write(self, path, content):
                self.files[path] = content

            def read(self, path):
                return self.files.get(path, "")

        class FakeSandbox:
            def __init__(self, api_key=None):
                assert api_key, "E2BAdapter 必须透传 api_key"
                self.filesystem = FakeFS()

            @property
            def process(self):
                return self

            def start(self, cmd, cwd=None):
                code = self.filesystem.read(cmd[1])
                return FakeProcess(code)

            def close(self):
                pass

        sys.modules["e2b"] = type(sys)("e2b")
        sys.modules["e2b"].Sandbox = FakeSandbox
        monkeypatch.setenv("E2B_API_KEY", "test-key")
        return FakeSandbox

    def test_e2b_path_outputs_match_local_contract(self, fake_e2b, monkeypatch):
        monkeypatch.setenv("E2B_API_KEY", "test-key")
        assert E2BAdapter.available() is True
        adapter = select_execution_adapter()
        assert isinstance(adapter, E2BAdapter), "E2B 可用时工厂必须自动切换"
        r = adapter.execute(_plan('import json; print(json.dumps({"y": 7}))'))
        assert r.status == "success"
        assert r.outputs == {"y": 7}
        assert r.execution_token, "e2b adapter 必须签发 execution_token"
        assert r.provenance.get("adapter") == "e2b"
        assert r.code_hash, "必须有 code_hash（replay 支撑）"
        assert r.environment_hash, "必须有 environment_hash（replay 支撑）"

    def test_e2b_failed_status_real(self, fake_e2b, monkeypatch):
        monkeypatch.setenv("E2B_API_KEY", "test-key")
        adapter = select_execution_adapter("e2b")
        r = adapter.execute(_plan("import sys; sys.exit(3)"))
        assert r.status == "failed"
        assert r.returncode == 3
