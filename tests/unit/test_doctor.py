# -*- coding: utf-8 -*-
"""doctor.py 的单元测试：引擎映射、竞赛包检查与阻塞判定。"""
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
    for hand, n in (("Modeler", 6), ("Programmer", 6), ("Writer", 7)):
        for i in range(n):
            (tmp_path / "core" / hand / "agents" / f"a{i}").mkdir(parents=True)
    for pack in ("cumcm", "huawei"):
        (tmp_path / "core" / "templates" / "latex" / pack).mkdir(parents=True)
    return tmp_path


def test_engine_mapping():
    assert doctor.ENGINE_BY_COMPETITION == {
        "cumcm": "xelatex",
        "huawei": "xelatex",
        "diangong": "xelatex",
        "huashu": "xelatex",
        "mcm": "pdflatex",
        "apmcm": "xelatex",
        "mathorcup": "xelatex",
        "renzhengbei": "xelatex",
        "shuweibei": "xelatex",
    }


def test_competition_pack_found(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "ROOT", _fake_root(tmp_path))
    r = doctor.Result()
    doctor.check_competition_pack(r, "huawei")
    assert len(r.ok) == 1 and not r.warn and not r.block


def test_competition_pack_missing_warns(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "ROOT", _fake_root(tmp_path))
    r = doctor.Result()
    doctor.check_competition_pack(r, "diangong")
    assert not r.ok
    assert len(r.warn) == 1
    assert "回退到默认模板" in r.warn[0][1]


def test_check_tools_blocks_on_missing(tmp_path, monkeypatch):
    root = _fake_root(tmp_path)
    (root / "core" / "tools" / "gatelib.py").unlink()
    monkeypatch.setattr(doctor, "ROOT", root)
    r = doctor.Result()
    doctor.check_tools(r)
    assert any(name == "core/tools/gatelib.py" for name, _ in r.block)


def test_agent_count_mismatch_blocks(tmp_path, monkeypatch):
    root = _fake_root(tmp_path)
    extra = root / "core" / "Writer" / "agents" / "extra"
    extra.mkdir()
    monkeypatch.setattr(doctor, "ROOT", root)
    r = doctor.Result()
    doctor.check_agent_count(r)
    assert any(name == "Writer agent 数" for name, _ in r.block)
