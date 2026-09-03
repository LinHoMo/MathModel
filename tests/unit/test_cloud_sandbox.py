# -*- coding: utf-8 -*-
"""cloud_sandbox.py 的单元测试：配置加载、可用性检测、本地降级与回退策略。

仅覆盖无需外部凭据的纯逻辑（E2B/Daytona SDK 需真实 API Key，不在单测范围）。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import cloud_sandbox as CS  # noqa: E402


def test_load_config_shape():
    cfg = CS._load_config()
    for key in ("enabled", "provider", "e2b", "daytona", "fallback"):
        assert key in cfg, f"缺配置键 {key}"
    assert cfg["e2b"]["api_key_env"] == "E2B_API_KEY"
    assert cfg["daytona"]["api_key_env"] == "DAYTONA_API_KEY"
    assert cfg["fallback"] == "local"


def test_check_status_local_always_available(monkeypatch):
    # 确保无 E2B/Daytona 凭据时后端判定正确
    monkeypatch.delenv("E2B_API_KEY", raising=False)
    monkeypatch.delenv("DAYTONA_API_KEY", raising=False)
    st = CS.check_status()
    assert st["backends"]["local"]["available"] is True
    assert st["backends"]["e2b"]["available"] is False
    assert st["backends"]["daytona"]["available"] is False


def test_run_local_executes():
    r = CS._run_local("print(42)")
    assert r["backend"] == "local"
    assert r["exit_code"] == 0
    assert "42" in r["stdout"]
    assert r["timeout"] is False


def test_run_local_reports_stderr_and_exit_code():
    r = CS._run_local("import sys; print('err', file=sys.stderr); sys.exit(3)")
    assert r["exit_code"] == 3
    assert "err" in r["stderr"]


def test_run_local_timeout():
    r = CS._run_local("import time; time.sleep(5)", timeout=1)
    assert r["timeout"] is True
    assert r["exit_code"] == -1
    assert "超时" in r["stderr"]


def test_run_code_disabled_uses_local_without_fallback_marker(monkeypatch):
    monkeypatch.setattr(CS, "_load_config", lambda: {
        "enabled": False, "provider": "e2b",
        "e2b": {"api_key_env": "E2B_API_KEY", "template": "python3", "timeout": 300, "memory_mb": 512},
        "daytona": {"api_key_env": "DAYTONA_API_KEY", "workspace": "default", "timeout": 300},
        "fallback": "local",
    })
    r = CS.run_code("print(1)")
    assert r["backend"] == "local"
    assert r["fallback_from"] is None


def test_run_code_falls_back_when_cloud_unavailable(monkeypatch):
    # enabled=True 但无 API key → 云端返回 None → 回退本地，并记录 fallback_from
    monkeypatch.delenv("E2B_API_KEY", raising=False)
    monkeypatch.setattr(CS, "_load_config", lambda: {
        "enabled": True, "provider": "e2b",
        "e2b": {"api_key_env": "E2B_API_KEY", "template": "python3", "timeout": 300, "memory_mb": 512},
        "daytona": {"api_key_env": "DAYTONA_API_KEY", "workspace": "default", "timeout": 300},
        "fallback": "local",
    })
    r = CS.run_code("print(1)")
    assert r["backend"] == "local"
    assert r["fallback_from"] == "e2b"


def test_run_code_skip_fallback_returns_none_backend(monkeypatch):
    monkeypatch.delenv("E2B_API_KEY", raising=False)
    monkeypatch.setattr(CS, "_load_config", lambda: {
        "enabled": True, "provider": "e2b",
        "e2b": {"api_key_env": "E2B_API_KEY", "template": "python3", "timeout": 300, "memory_mb": 512},
        "daytona": {"api_key_env": "DAYTONA_API_KEY", "workspace": "default", "timeout": 300},
        "fallback": "skip",
    })
    r = CS.run_code("print(1)")
    assert r["backend"] == "none"
    assert r["exit_code"] == -1
