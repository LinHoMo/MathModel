# -*- coding: utf-8 -*-
"""P3-1：E2B 沙箱执行后端（ExecutionAdapter 接口实现）。

设计原则（与 LocalPythonAdapter 完全同构）：
- execute() 只产生真实执行状态（success/failed/timeout/invalid），
  绝不默认 success；adapter 签发 execution_token（HMAC 同源）。
- available() 探测 E2B_API_KEY 与 e2b SDK；不可用 → 回退 LocalPythonAdapter
  （select_execution_adapter 工厂保证自动切换）。
- 输出解析约定与 Local 一致：stdout 最后一块合法 JSON 作为结构化 outputs。
"""
from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

from .adapters import (  # 复用同文件类型（见模块尾部 get_adapter 注册）
    ExecutionAdapter, ExecutionPlan, ExecutionResultData, LocalPythonAdapter,
    environment_hash, environment_manifest, issue_token, sha256_text, _iso_now,
)


class E2BAdapter(ExecutionAdapter):
    """E2B 云端隔离沙箱执行（可选后端，需 E2B_API_KEY + e2b SDK）。

    代码上传沙箱 /tmp 后以子进程运行，捕获 stdout/stderr/returncode；
    超时/异常如实映射 timeout/invalid。无 key/SDK → available()=False。
    """

    name = "e2b"

    def __init__(self, api_key: str | None = None, timeout_seconds: int = 120):
        self.api_key = api_key or os.environ.get("E2B_API_KEY")
        self.timeout_seconds = timeout_seconds

    @classmethod
    def available(cls) -> bool:
        try:
            import e2b  # noqa: F401
        except Exception:
            return False
        return bool(os.environ.get("E2B_API_KEY"))

    def execute(self, plan: ExecutionPlan) -> ExecutionResultData:
        if not plan.code or not plan.code.strip():
            return ExecutionResultData(
                execution_id="", model_id=plan.model_id,
                status="invalid", stderr="空代码：执行计划无 code",
                provenance={"adapter": self.name, "reason": "empty_code"},
            )
        if not self.available():
            return ExecutionResultData(
                execution_id="", model_id=plan.model_id,
                status="invalid",
                stderr="E2B 不可用（缺少 E2B_API_KEY 或 e2b SDK）；"
                       "请用 select_execution_adapter() 回退 LocalPythonAdapter",
                provenance={"adapter": self.name, "reason": "unavailable"},
            )
        exec_id = uuid.uuid4().hex[:12]
        started = _iso_now()
        t0 = time.perf_counter()
        code_hash = sha256_text(plan.code)
        env_hash = environment_hash()

        try:
            from e2b import Sandbox
        except Exception as exc:
            return ExecutionResultData(
                execution_id=exec_id, model_id=plan.model_id, status="invalid",
                inputs=plan.inputs, stderr=f"e2b SDK import 失败: {exc}",
                returncode=None, duration_ms=0, code_hash=code_hash,
                environment_hash=env_hash, started_at=started,
                finished_at=_iso_now(),
                provenance={"adapter": self.name, "reason": "sdk_missing"},
                code=plan.code, environment_manifest=environment_manifest(),
            )

        sandbox = None
        try:
            sandbox = Sandbox(api_key=self.api_key)
            remote = f"/tmp/exec_{exec_id}.py"
            sandbox.filesystem.write(remote, plan.code)
            proc = sandbox.process.start(
                ["python3", remote], cwd="/tmp")
            out = proc.wait()
            duration_ms = int((time.perf_counter() - t0) * 1000)
            stdout = out.stdout or ""
            stderr = out.stderr or ""
            status = "success" if out.exit_code == 0 else "failed"
            outputs: dict[str, Any] = {}
            for line in reversed(stdout.strip().splitlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                    if isinstance(parsed, dict):
                        outputs = parsed
                    elif isinstance(parsed, list):
                        outputs = {"data": parsed}
                    break
                except json.JSONDecodeError:
                    continue
            if not outputs:
                outputs = {"stdout_tail": stdout.strip()[-2000:]}
            return ExecutionResultData(
                execution_id=exec_id, model_id=plan.model_id, status=status,
                inputs=plan.inputs, outputs=outputs, stdout=stdout,
                stderr=stderr, returncode=out.exit_code,
                duration_ms=duration_ms, code_hash=code_hash,
                environment_hash=env_hash, started_at=started,
                finished_at=_iso_now(),
                provenance={"adapter": self.name, "sandbox": "e2b"},
                code=plan.code, environment_manifest=environment_manifest(),
                execution_token=issue_token(code_hash, self.name, started),
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            return ExecutionResultData(
                execution_id=exec_id, model_id=plan.model_id, status="invalid",
                inputs=plan.inputs, stderr=f"e2b execution error: {exc}",
                returncode=None, duration_ms=duration_ms, code_hash=code_hash,
                environment_hash=env_hash, started_at=started,
                finished_at=_iso_now(),
                provenance={"adapter": self.name, "reason": "e2b_error"},
                code=plan.code, environment_manifest=environment_manifest(),
            )
        finally:
            try:
                if sandbox is not None:
                    sandbox.close()
            except Exception:
                pass


def select_execution_adapter(name: str | None = None,
                             **kwargs) -> ExecutionAdapter:
    """执行后端选择工厂（P3-1）：优先 E2B（可用时自动切换），
    不可用回退 LocalPythonAdapter；显式 name 时按 name 选择。"""
    if name == "e2b":
        return E2BAdapter(api_key=kwargs.get("api_key"))
    if name == "local_python":
        return LocalPythonAdapter(python=kwargs.get("python"))
    if E2BAdapter.available():
        return E2BAdapter(api_key=kwargs.get("api_key"))
    return LocalPythonAdapter(python=kwargs.get("python"))
