# -*- coding: utf-8 -*-
"""freeze_numbers.py 的单元测试：冻结、追溯判定与阈值口径。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import freeze_numbers as F  # noqa: E402


class _Args:
    limit = 5


def _setup(tmp_path, monkeypatch, results, tex):
    proj = tmp_path / "projects" / "demo"
    (proj / "figures").mkdir(parents=True)
    (proj / "paper").mkdir(parents=True)
    (proj / "figures" / "all_results.json").write_text(
        json.dumps(results), encoding="utf-8")
    (proj / "paper" / "main.tex").write_text(tex, encoding="utf-8")
    monkeypatch.setattr(F.S, "project_dir",
                        lambda p: tmp_path / "projects" / p)
    return proj


def test_freeze_writes_table(tmp_path, monkeypatch):
    proj = _setup(tmp_path, monkeypatch, {"a": 12.34, "b": {"c": 56.78}}, "")
    assert F.cmd_freeze("demo", _Args()) == 0
    frozen = json.loads((proj / "work/frozen_numbers.json")
                        .read_text(encoding="utf-8"))
    assert frozen["count"] == 2
    assert frozen["numbers"]["a"]["value"] == 12.34


def test_check_pass_when_all_traced(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch,
           {"a": 12.34, "b": 56.78},
           "结果 12.34 与 56.78 均吻合。")
    assert F.cmd_freeze("demo", _Args()) == 0
    assert F.cmd_check("demo", _Args()) == 0


def test_check_fail_when_untraced(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch,
           {"a": 12.34, "b": 56.78},
           "结果 12.34 成立，但 999.01 与 123.45 无出处。")
    assert F.cmd_freeze("demo", _Args()) == 0
    assert F.cmd_check("demo", _Args()) == 1


def test_check_fail_when_source_changed(tmp_path, monkeypatch):
    proj = _setup(tmp_path, monkeypatch, {"a": 12.34}, "数值 12.34。")
    assert F.cmd_freeze("demo", _Args()) == 0
    (proj / "figures" / "all_results.json").write_text(
        json.dumps({"a": 99.99}), encoding="utf-8")
    assert F.cmd_check("demo", _Args()) == 1


def test_check_threshold_matches_env(tmp_path, monkeypatch):
    # 10 个数追溯 9 个 = 90%，等于 env 阈值 0.90 → PASS（不是旧硬编码 0.95）
    results = {f"k{i}": 10.0 + i for i in range(9)}
    traced = " ".join(f"{10 + i}.00" for i in range(9))
    _setup(tmp_path, monkeypatch, results, traced + " 以及 999.01 无出处。")
    assert F.cmd_freeze("demo", _Args()) == 0
    assert F.cmd_check("demo", _Args()) == 0
