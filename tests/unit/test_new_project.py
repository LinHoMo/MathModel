# -*- coding: utf-8 -*-
"""new_project.py 的单元测试：脚手架创建、赛题导入、边界拒绝。"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import new_project  # noqa: E402


@pytest.fixture
def fake_root(tmp_path, monkeypatch):
    """伪造仓库根：含 core/templates/latex/{cumcm,mcm} 与 projects/。"""
    for comp in ("cumcm", "mcm"):
        (tmp_path / "core" / "templates" / "latex" / comp).mkdir(parents=True)
    (tmp_path / "projects").mkdir()
    monkeypatch.setattr(new_project, "ROOT", tmp_path)
    return tmp_path


def test_scaffold_creates_full_tree(fake_root):
    proj = new_project.scaffold("demo1", "cumcm", [])
    assert proj == fake_root / "projects" / "demo1"
    for sub in new_project.PROJECT_DIRS:
        assert (proj / sub).is_dir(), sub


def test_scaffold_copies_problem_files(fake_root, tmp_path):
    pdf = tmp_path / "problem.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    proj = new_project.scaffold("demo2", "mcm", [str(pdf)])
    assert (proj / "inputs" / "problem.pdf").read_bytes() == b"%PDF-1.4 fake"


def test_scaffold_rejects_existing(fake_root):
    new_project.scaffold("demo3", "cumcm", [])
    with pytest.raises(ValueError, match="已存在"):
        new_project.scaffold("demo3", "cumcm", [])
    # --force 只补齐，不删除
    new_project.scaffold("demo3", "cumcm", [], force=True)


def test_scaffold_rejects_bad_name(fake_root):
    for bad in ("Demo", "1abc", "x", "has space", "UPPER"):
        with pytest.raises(ValueError, match="不合法"):
            new_project.scaffold(bad, "cumcm", [])


def test_scaffold_rejects_unknown_competition(fake_root):
    with pytest.raises(ValueError, match="未知竞赛包"):
        new_project.scaffold("demo4", "no-such-comp", [])


def test_scaffold_missing_problem_file(fake_root):
    with pytest.raises(ValueError, match="赛题文件不存在"):
        new_project.scaffold("demo5", "cumcm", ["/nonexistent/file.txt"])


def test_main_exit_codes(fake_root, capsys):
    assert new_project.main(["demo6", "--competition", "cumcm"]) == 0
    out = capsys.readouterr().out
    assert "demo6" in out and "state.py demo6 init" in out
    assert new_project.main(["demo6", "--competition", "cumcm"]) == 2


def test_known_competitions(fake_root):
    assert new_project.known_competitions() == ["cumcm", "mcm"]
