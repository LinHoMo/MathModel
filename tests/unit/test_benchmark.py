# -*- coding: utf-8 -*-
"""benchmark.py 的单元测试：题库健康检查与开工演练流程。"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import benchmark  # noqa: E402


@pytest.fixture
def fake_root(tmp_path, monkeypatch):
    for comp in ("cumcm", "mcm"):
        (tmp_path / "core" / "templates" / "latex" / comp).mkdir(parents=True)
    (tmp_path / "projects").mkdir()
    monkeypatch.setattr(benchmark, "ROOT", tmp_path)
    monkeypatch.setattr(benchmark.new_project, "ROOT", tmp_path)
    return tmp_path


def _write_knowledge(root: Path):
    prob = root / "core" / "knowledge" / "problems"
    prob.mkdir(parents=True)
    (prob / "INDEX.md").write_text(
        "# 赛题索引\n## 2020 年\n| 2020 | A | 炉温曲线 | x | 中 | 备注 |\n"
        "| 2020 | B | 穿越沙漠 | x | 难 | 备注 |\n## 2021 年\n"
        "| 2021 | A | FAST | x | 难 | 备注 |\n（待补）\n", encoding="utf-8")
    (prob / "MCM-ICM.md").write_text(
        "# MCM\n| 2024 | MCM C | Tennis Momentum | x | 多源可核实 |\n"
        "| 其余年份 | — | （待核实后补充） | — | 待补 |\n", encoding="utf-8")


def test_library_report_counts(fake_root):
    _write_knowledge(fake_root)
    rep = benchmark.library_report()
    assert rep["cumcm"]["years_covered"] == ["2020", "2021"]
    assert rep["cumcm"]["entries"] == 3
    assert rep["cumcm"]["pending_marks"] == 1
    assert rep["mcm"]["verified_titles"] == 1
    assert rep["mcm"]["pending_marks"] >= 1


def test_library_report_missing_files(fake_root):
    rep = benchmark.library_report()
    assert "error" in rep["cumcm"] and "error" in rep["mcm"]


def test_pipeline_report_scaffold_failure(fake_root):
    rep = benchmark.pipeline_report("no-such-comp")
    assert rep["steps"]["scaffold"].startswith("FAIL")
    assert not (fake_root / "projects").iterdir().__next__() if list(
        (fake_root / "projects").iterdir()) else True


def test_pipeline_report_cleanup(fake_root, monkeypatch):
    monkeypatch.setattr(benchmark, "_run", lambda cmd, cwd: (0, "ok"))
    rep = benchmark.pipeline_report("cumcm")
    assert rep["steps"]["scaffold"] == "PASS"
    assert rep["steps"]["state_init"] == "PASS"
    assert rep["steps"]["doctor"] == "PASS"
    assert rep["cleaned"] is True
    assert list((fake_root / "projects").iterdir()) == []


def test_pipeline_report_keep(fake_root, monkeypatch):
    monkeypatch.setattr(benchmark, "_run", lambda cmd, cwd: (0, "ok"))
    rep = benchmark.pipeline_report("mcm", keep=True)
    assert rep["cleaned"] is False
    kept = list((fake_root / "projects").iterdir())
    assert len(kept) == 1 and kept[0].name.startswith("bench-mcm-")


def test_pipeline_report_failure_recorded(fake_root, monkeypatch):
    monkeypatch.setattr(benchmark, "_run", lambda cmd, cwd: (2, "boom"))
    rep = benchmark.pipeline_report("cumcm")
    assert rep["steps"]["state_init"].startswith("FAIL")
    assert "state_init_detail" in rep["steps"]
    assert rep["cleaned"] is True


def test_main_library_json(fake_root, capsys):
    _write_knowledge(fake_root)
    rc = benchmark.main(["library", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "library"


def test_main_pipeline_exit_code(fake_root, monkeypatch):
    monkeypatch.setattr(benchmark, "_run", lambda cmd, cwd: (1, "x"))
    rc = benchmark.main(["pipeline", "--competition", "cumcm"])
    assert rc == 1
