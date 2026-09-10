"""Execution Adapter — P0-E Executable Model Runtime（执行层）。

三层架构（docs/architecture/THREE_LAYER_ARCHITECTURE.md v2）Layer 2 的核心：
Epistemic 产出 Model Artifact → Execution 消费并产生**真实数值**的 ExecutionResult。

设计原则（用户战略裁决 2026-09-09）：
1. ExecutionResult.status 只能来自真实执行状态（not_executed / running /
   success / failed / timeout / invalid），**禁止 handler 默认生成 success**。
2. ExecutionResult 是一等 Artifact（EXEC 前缀，注册进 ArtifactRegistry），
   携带 execution_id / model_id / status / inputs / outputs / stdout / stderr /
   duration_ms / code_hash / environment_hash / started_at / finished_at / provenance。
3. Evidence 不是 Agent 写出来的，而是 execution substrate 产生的：
   Claim → requires Evidence → Execution → ExecutionResult → Evidence → supported/unsupported。
4. Replay 由 code_hash + environment_hash + 完整时间戳支撑。

本模块零第三方依赖（subprocess 标准库），可被替换为 E2B / Docker / Syslab 等
远端后端（见 ExecutionAdapter 接口）。
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runtime.execution.execution_auth import issue_token

# 执行状态：唯一合法来源（not_executed 为初始态，绝不默认 success）
EXEC_STATUS = ("not_executed", "running", "success", "failed", "timeout", "invalid")

# 一等 artifact 的 data 结构（用户指定字段全集；P0-E4 扩展字段标 ★）
EXECUTION_RESULT_FIELDS = (
    "execution_id", "model_id", "status", "inputs", "outputs",
    "stdout", "stderr", "returncode", "duration_ms",
    "code_hash", "environment_hash",
    "started_at", "finished_at", "provenance",
    "code",           # ★ P0-E4：code 本体（replay/审计需要；用户最小字段集之外）
    "environment_manifest",  # ★ P0-E4：执行环境声明（replay 偏差归因）
    "execution_token",  # ★ P0-3：adapter 签发来源鉴别（HMAC）
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def environment_hash() -> str:
    """执行环境指纹（python 版本 + 平台 + 主版本），用于 replay 溯源。

    未来将演化为 Execution Environment Manifest（随机种子/包版本/OS/浮点/
    外部数据/时间/网络/求解器非确定性），见 THREE_LAYER_ARCHITECTURE §2.8。
    """
    return sha256_text(environment_manifest())


def environment_manifest() -> str:
    """执行环境声明：确定性可比较的文本（replay 偏差归因用）。"""
    return "\n".join([
        f"python={sys.version.split()[0]}",
        f"platform={platform.platform()}",
        f"executable={sys.executable}",
    ])


@dataclass
class ExecutionPlan:
    """一次执行的计划：从 MODEL_IR/实验设计派生。"""

    model_id: str                # 关联模型 artifact（Mxxx）
    code: str                    # 待执行代码（Python 或脚本）
    inputs: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 120
    workdir: str | None = None   # 执行工作目录（None → 系统临时目录）
    env: dict[str, str] = field(default_factory=dict)
    adapter: str = "local_python"
    meta: dict[str, Any] = field(default_factory=dict)   # 扩展（如题目/实验绑定）


@dataclass
class ExecutionResultData:
    """一等 ExecutionResult artifact 的 data（字段见 EXECUTION_RESULT_FIELDS）。"""

    execution_id: str
    model_id: str
    status: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    duration_ms: int = 0
    code_hash: str = ""
    environment_hash: str = ""
    started_at: str = ""
    finished_at: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    code: str = ""                    # ★ P0-E4：code 本体（replay）
    environment_manifest: str = ""    # ★ P0-E4：环境声明（replay 归因）
    execution_token: str = ""         # ★ P0-3：adapter 签发来源鉴别（HMAC）

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "execution_id": self.execution_id,
            "model_id": self.model_id,
            "status": self.status,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "duration_ms": self.duration_ms,
            "code_hash": self.code_hash,
            "environment_hash": self.environment_hash,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "provenance": self.provenance,
            "code": self.code,
            "environment_manifest": self.environment_manifest,
            "execution_token": self.execution_token,
        }
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ExecutionResultData":
        return cls(**{k: d.get(k) for k in EXECUTION_RESULT_FIELDS})


def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


class ExecutionError(RuntimeError):
    """执行层错误（adapter 不可用 / 非法计划等）。"""


class ExecutionAdapter(ABC):
    """执行后端抽象。实现者负责把 ExecutionPlan 变成真实执行。"""

    name: str = "abstract"

    @abstractmethod
    def execute(self, plan: ExecutionPlan) -> ExecutionResultData:
        """执行计划，返回真实执行状态的结果。绝不默认 success。"""

    @classmethod
    def available(cls) -> bool:
        """后端是否可用（环境探测）。"""
        return True


class LocalPythonAdapter(ExecutionAdapter):
    """本地 Python subprocess 执行（零依赖，Windows/Linux 通用）。

    执行方式：code 写入临时 .py 文件 → subprocess 运行 → 捕获 stdout/stderr/
    returncode/耗时。输出解析约定：stdout 最后一块合法 JSON 作为结构化 outputs
    （若无 JSON 则 outputs={"stdout_tail": ...}，仍以 stdout 全量留痕）。
    """

    name = "local_python"

    def __init__(self, python: str | None = None):
        self.python = python or sys.executable

    @classmethod
    def available(cls) -> bool:
        try:
            import subprocess  # noqa: F401
            return True
        except Exception:
            return False

    def execute(self, plan: ExecutionPlan) -> ExecutionResultData:
        if not plan.code or not plan.code.strip():
            return ExecutionResultData(
                execution_id="", model_id=plan.model_id,
                status="invalid", stderr="空代码：执行计划无 code",
                provenance={"adapter": self.name, "reason": "empty_code"},
            )
        exec_id = uuid.uuid4().hex[:12]
        started = _iso_now()
        t0 = time.perf_counter()
        code_hash = sha256_text(plan.code)
        env_hash = environment_hash()

        workdir = Path(plan.workdir) if plan.workdir else Path(tempfile.gettempdir())
        workdir.mkdir(parents=True, exist_ok=True)
        script = workdir / f"exec_{exec_id}.py"

        try:
            script.write_text(plan.code, encoding="utf-8")
            env = dict(os.environ)
            env.update(plan.env)
            proc = subprocess.run(
                [self.python, str(script)],
                capture_output=True, text=True, timeout=plan.timeout_seconds,
                cwd=str(workdir), env=env,
            )
            duration_ms = int((time.perf_counter() - t0) * 1000)
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            status = "success" if proc.returncode == 0 else "failed"
            outputs: dict[str, Any] = {}
            # 结构化输出约定：stdout 最后一块合法 JSON
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
                stderr=stderr, returncode=proc.returncode,
                duration_ms=duration_ms, code_hash=code_hash,
                environment_hash=env_hash, started_at=started,
                finished_at=_iso_now(),
                provenance={"adapter": self.name, "python": self.python},
                code=plan.code, environment_manifest=environment_manifest(),
                # P0-3：adapter 签发来源鉴别（HMAC(code_hash|adapter|ts)）——
                # Agent/Handler 无 secret，无法伪造 execution_result
                execution_token=issue_token(code_hash, self.name, started),
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            return ExecutionResultData(
                execution_id=exec_id, model_id=plan.model_id, status="timeout",
                inputs=plan.inputs, stdout=(exc.stdout or "") if hasattr(exc, "stdout") else "",
                stderr=f"timeout after {plan.timeout_seconds}s",
                returncode=None, duration_ms=duration_ms, code_hash=code_hash,
                environment_hash=env_hash, started_at=started,
                finished_at=_iso_now(),
                provenance={"adapter": self.name, "reason": "timeout"},
                code=plan.code, environment_manifest=environment_manifest(),
            )
        except Exception as exc:  # 执行框架级错误（写文件失败等）
            duration_ms = int((time.perf_counter() - t0) * 1000)
            return ExecutionResultData(
                execution_id=exec_id, model_id=plan.model_id, status="invalid",
                inputs=plan.inputs, stderr=f"execution framework error: {exc}",
                returncode=None, duration_ms=duration_ms, code_hash=code_hash,
                environment_hash=env_hash, started_at=started,
                finished_at=_iso_now(),
                provenance={"adapter": self.name, "reason": "framework_error"},
                code=plan.code, environment_manifest=environment_manifest(),
            )
        finally:
            try:
                script.unlink(missing_ok=True)
            except Exception:
                pass


def get_adapter(name: str = "local_python", **kwargs) -> ExecutionAdapter:
    """adapter 工厂（当前仅 local_python；未来 e2b/docker/syslab 在此注册）。"""
    if name == "local_python":
        return LocalPythonAdapter(python=kwargs.get("python"))
    raise ExecutionError(f"未知执行后端: {name!r}（当前仅 local_python）")
