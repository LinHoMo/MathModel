# -*- coding: utf-8 -*-
"""retrospect.py 的单元测试：复盘统计与报告渲染。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import retrospect  # noqa: E402


def _sample_state():
    return {
        "project": "demo",
        "completed": [
            {"hand": "modeler", "agent": "problem-parser", "stage": 1},
            {"hand": "modeler", "agent": "type-classifier", "stage": 2},
            {"hand": "programmer", "agent": "code-implementer", "stage": 2},
        ],
        "failed": [
            {"hand": "writer", "agent": "section-writer", "reason": "占位符残留"},
        ],
        "q_states": {
            "q1": {"status": "fixed"},
            "q2": {"status": "open"},
        },
        "review": {
            "round": 2,
            "max_rounds": 4,
            "verdict": "refine",
            "weighted": 7.1,
            "min_dimensions": ["创新与亮点"],
        },
    }


def test_build_report_counts():
    report = retrospect.build_report(_sample_state())
    assert report["project"] == "demo"
    assert report["completed_total"] == 3
    assert report["completed_by_hand"]["modeler"] == 2
    assert report["completed_by_hand"]["programmer"] == 1
    assert report["failed_total"] == 1
    assert report["failed_by_hand"]["writer"] == 1
    assert report["qfix_used"] == 1
    assert report["review"]["verdict"] == "refine"
    assert report["review"]["weak_dimensions"] == ["创新与亮点"]


def test_build_report_empty_state():
    report = retrospect.build_report({})
    assert report["completed_total"] == 0
    assert report["failed_total"] == 0
    assert report["qfix_used"] == 0
    assert report["review"]["verdict"] == ""


def test_render_markdown_contains_key_sections():
    md = retrospect.render_markdown(retrospect.build_report(_sample_state()))
    for token in ("# 赛后回顾报告 — demo", "2 / 4", "refine",
                  "section-writer", "经验沉淀", "知识库归档去向"):
        assert token in md


def test_main_writes_outputs(tmp_path, monkeypatch):
    proj_dir = tmp_path / "projects" / "demo"
    (proj_dir / "work").mkdir(parents=True)
    (proj_dir / "work" / "state.json").write_text(
        json.dumps(_sample_state()), encoding="utf-8")
    monkeypatch.setattr(retrospect, "ROOT", tmp_path)
    rc = retrospect.main(["demo"])
    assert rc == 0
    md_path = proj_dir / "work" / "RETROSPECTIVE.md"
    js_path = proj_dir / "work" / "RETROSPECTIVE.json"
    assert md_path.exists() and js_path.exists()
    data = json.loads(js_path.read_text(encoding="utf-8"))
    assert data["completed_total"] == 3


def test_main_missing_project(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(retrospect, "ROOT", tmp_path)
    rc = retrospect.main(["no-such-project"])
    assert rc == 2
