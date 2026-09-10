# -*- coding: utf-8 -*-
"""doctor.py 的单元测试：工具链/目录/角色/catalog 检查与阻塞判定。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import doctor  # noqa: E402


def _fake_root(tmp_path):
    tools = tmp_path / "core" / "tools"
    tools.mkdir(parents=True)
    for name, _ in doctor.REQUIRED_TOOLS:
        (tools / name).write_text("", encoding="utf-8")
    for d, _ in doctor.REQUIRED_DIRS:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    # V3 角色定义
    roles = tmp_path / "core" / "roles"
    roles.mkdir(parents=True, exist_ok=True)
    for name in ("analyst", "modeler", "experimenter", "critic"):
        (roles / f"{name}.yaml").write_text("", encoding="utf-8")
    return tmp_path


def test_check_tools_blocks_on_missing(tmp_path, monkeypatch):
    root = _fake_root(tmp_path)
    (root / "core" / "tools" / "validate.py").unlink()
    monkeypatch.setattr(doctor, "ROOT", root)
    r = doctor.Result()
    doctor.check_tools(r)
    assert any(name == "core/tools/validate.py" for name, _ in r.block)


def test_agent_count_ok(tmp_path, monkeypatch):
    root = _fake_root(tmp_path)
    monkeypatch.setattr(doctor, "ROOT", root)
    r = doctor.Result()
    doctor.check_agent_count(r)
    assert any(name == "V3 角色定义" for name, _ in r.ok)


def test_agent_count_mismatch_blocks(tmp_path, monkeypatch):
    root = _fake_root(tmp_path)
    (root / "core" / "roles" / "critic.yaml").unlink()
    monkeypatch.setattr(doctor, "ROOT", root)
    r = doctor.Result()
    doctor.check_agent_count(r)
    assert any(name == "V3 角色定义" for name, _ in r.block)


def test_check_dirs_ok(tmp_path, monkeypatch):
    root = _fake_root(tmp_path)
    monkeypatch.setattr(doctor, "ROOT", root)
    r = doctor.Result()
    doctor.check_dirs(r)
    assert not r.block
