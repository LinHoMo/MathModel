#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cloud_sandbox.py — 云执行沙箱（可选）

提供云端代码执行能力，支持 E2B / Daytona 后端。云端不可用时自动回退到本地执行。
主要用于 code-implementer / test-runner 在隔离环境中运行代码。

用法:
    python core/tools/cloud_sandbox.py run <代码文件>          # 执行代码
    python core/tools/cloud_sandbox.py run --code "print(42)"  # 执行内联代码
    python core/tools/cloud_sandbox.py status                   # 检查云端可用性
    python core/tools/cloud_sandbox.py config                   # 显示当前配置

零第三方依赖（云端 SDK 按需 import，不可用时回退本地）。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core" / "env"))

from loader import get  # noqa: E402


def _load_config() -> dict:
    return {
        "enabled": get("cloud_sandbox.enabled", default=False),
        "provider": get("cloud_sandbox.provider", default="e2b"),
        "e2b": {
            "api_key_env": get("cloud_sandbox.e2b.api_key_env", default="E2B_API_KEY"),
            "template": get("cloud_sandbox.e2b.template", default="python3"),
            "timeout": get("cloud_sandbox.e2b.timeout_seconds", default=300),
            "memory_mb": get("cloud_sandbox.e2b.memory_mb", default=512),
        },
        "daytona": {
            "api_key_env": get("cloud_sandbox.daytona.api_key_env", default="DAYTONA_API_KEY"),
            "workspace": get("cloud_sandbox.daytona.workspace", default="default"),
            "timeout": get("cloud_sandbox.daytona.timeout_seconds", default=300),
        },
        "fallback": get("cloud_sandbox.fallback", default="local"),
    }


def check_status() -> dict:
    """检查各后端可用性。"""
    cfg = _load_config()
    result = {"enabled": cfg["enabled"], "provider": cfg["provider"], "backends": {}}

    e2b_key = os.environ.get(cfg["e2b"]["api_key_env"], "")
    result["backends"]["e2b"] = {
        "available": bool(e2b_key),
        "api_key_set": bool(e2b_key),
        "template": cfg["e2b"]["template"],
        "timeout": cfg["e2b"]["timeout"],
    }

    daytona_key = os.environ.get(cfg["daytona"]["api_key_env"], "")
    result["backends"]["daytona"] = {
        "available": bool(daytona_key),
        "api_key_set": bool(daytona_key),
        "workspace": cfg["daytona"]["workspace"],
        "timeout": cfg["daytona"]["timeout"],
    }

    result["backends"]["local"] = {"available": True, "python": sys.executable}
    result["fallback"] = cfg["fallback"]
    return result


def _run_local(code: str, timeout: int = 300) -> dict:
    """本地执行代码（subprocess 隔离）。"""
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(ROOT),
        )
        elapsed = time.time() - start
        return {
            "backend": "local",
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "elapsed_seconds": round(elapsed, 3),
            "timeout": False,
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {
            "backend": "local",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"执行超时（{timeout}s）",
            "elapsed_seconds": round(elapsed, 3),
            "timeout": True,
        }


def _run_e2b(code: str, cfg: dict) -> dict | None:
    """E2B 云端执行。需要 e2b-sdk 已安装且 API Key 已设置。"""
    api_key = os.environ.get(cfg["e2b"]["api_key_env"], "")
    if not api_key:
        return None
    try:
        from e2b import Sandbox  # type: ignore
    except ImportError:
        return None

    start = time.time()
    try:
        with Sandbox(template=cfg["e2b"]["template"], api_key=api_key) as sbx:
            result = sbx.run_code(code, timeout=cfg["e2b"]["timeout"])
            elapsed = time.time() - start
            return {
                "backend": "e2b",
                "exit_code": 0 if not result.error else 1,
                "stdout": result.text or "",
                "stderr": str(result.error) if result.error else "",
                "elapsed_seconds": round(elapsed, 3),
                "timeout": False,
            }
    except Exception as exc:
        elapsed = time.time() - start
        return {
            "backend": "e2b",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"E2B 执行失败: {exc}",
            "elapsed_seconds": round(elapsed, 3),
            "timeout": False,
        }


def _run_daytona(code: str, cfg: dict) -> dict | None:
    """Daytona 云端执行。需要 daytona-sdk 已安装且 API Key 已设置。"""
    api_key = os.environ.get(cfg["daytona"]["api_key_env"], "")
    if not api_key:
        return None
    try:
        from daytona_sdk import Daytona  # type: ignore
    except ImportError:
        return None

    start = time.time()
    try:
        daytona = Daytona(api_key=api_key)
        ws = daytona.get_workspace(cfg["daytona"]["workspace"])
        result = ws.execute(code, timeout=cfg["daytona"]["timeout"])
        elapsed = time.time() - start
        return {
            "backend": "daytona",
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "elapsed_seconds": round(elapsed, 3),
            "timeout": False,
        }
    except Exception as exc:
        elapsed = time.time() - start
        return {
            "backend": "daytona",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Daytona 执行失败: {exc}",
            "elapsed_seconds": round(elapsed, 3),
            "timeout": False,
        }


def run_code(code: str, provider: str | None = None) -> dict:
    """执行代码，按配置选择后端。

    优先级：配置指定后端 → 回退策略。
    """
    cfg = _load_config()
    target = provider or cfg["provider"]

    result = None
    if cfg["enabled"]:
        if target == "e2b":
            result = _run_e2b(code, cfg)
        elif target == "daytona":
            result = _run_daytona(code, cfg)

    if result is None:
        if cfg["fallback"] == "skip":
            return {
                "backend": "none",
                "exit_code": -1,
                "stdout": "",
                "stderr": "云端不可用且 fallback=skip，已跳过执行",
                "elapsed_seconds": 0,
                "timeout": False,
            }
        timeout = cfg["e2b"]["timeout"] if target == "e2b" else cfg["daytona"]["timeout"]
        result = _run_local(code, timeout=timeout)
        result["fallback_from"] = target if cfg["enabled"] else None

    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="云执行沙箱")
    sub = parser.add_subparsers(dest="command")

    sp_run = sub.add_parser("run", help="执行代码")
    sp_run.add_argument("file", nargs="?", help="代码文件路径")
    sp_run.add_argument("--code", help="内联代码")
    sp_run.add_argument("--provider", choices=["e2b", "daytona", "local"], help="指定后端")

    sub.add_parser("status", help="检查云端可用性")
    sub.add_parser("config", help="显示当前配置")

    args = parser.parse_args(argv)

    if args.command == "status":
        status = check_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0

    elif args.command == "config":
        cfg = _load_config()
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
        return 0

    elif args.command == "run":
        if args.code:
            code = args.code
        elif args.file:
            path = Path(args.file)
            if not path.exists():
                print(f"[FAIL] 文件不存在: {path}", file=sys.stderr)
                return 2
            code = path.read_text(encoding="utf-8")
        else:
            code = sys.stdin.read()

        result = run_code(code, provider=args.provider)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["exit_code"] == 0 else 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
