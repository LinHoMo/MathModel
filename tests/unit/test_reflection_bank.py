# -*- coding: utf-8 -*-
"""reflection_bank.py 的单元测试：经验提取、扫描聚合、检索、接地验证与统计。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import reflection_bank as RB  # noqa: E402


def _sample_report(project="demo"):
    return {
        "_project": project,
        "failure_records": [
            {"hand": "writer", "agent": "section-writer", "reason": "占位符残留"},
        ],
        "failed_by_hand": {"writer": 1, "modeler": 0, "programmer": 0, "reviewer": 0},
        "review": {"weak_dimensions": ["创新与亮点", "灵敏度分析"]},
    }


def test_extract_lessons_failure_and_weak():
    lessons = RB._extract_lessons(_sample_report())
    types = {l["type"] for l in lessons}
    # 1 条 failure + 1 条 weak_dimension + 1 条 hand_failure_summary
    assert "failure" in types
    assert "weak_dimension" in types
    assert "hand_failure_summary" in types
    weak = [l for l in lessons if l["type"] == "weak_dimension"][0]
    assert weak["keywords"] == ["创新与亮点", "灵敏度分析"]


def test_extract_keywords():
    kws = RB._extract_keywords("writer 手失败，占位符 todo 残留 main.py")
    assert any("占位符" in k for k in kws) or any("writer" in k for k in kws)


def test_scan_search_grounding_stats(tmp_path, monkeypatch):
    # 构造一个带回顾数据的项目
    proj = tmp_path / "projects" / "demo"
    (proj / "work").mkdir(parents=True)
    (proj / "work" / "RETROSPECTIVE.json").write_text(
        json.dumps(_sample_report("demo"), ensure_ascii=False), encoding="utf-8")

    bank_dir = tmp_path / "projects" / "_bank"
    monkeypatch.setattr(RB, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(RB, "BANK_DIR", bank_dir)
    monkeypatch.setattr(RB, "BANK_FILE", bank_dir / "reflections.json")

    # scan 聚合
    bank = RB.scan_projects()
    assert bank["projects_scanned"] == 1
    assert bank["projects_with_retro"] == 1
    assert bank["total_lessons"] >= 3

    # search 命中
    hits = RB.search_bank("section-writer")
    assert len(hits) >= 1
    assert hits[0]["source"] == "demo"

    # grounding 无未接地引用（failure detail 不含 .py 引用时）
    assert RB.check_grounding() == []

    # stats
    stats = RB.compute_stats()
    assert stats["total_lessons"] >= 3
    assert stats["by_source"]["demo"] >= 3


def test_scan_empty_when_no_retro(tmp_path, monkeypatch):
    proj = tmp_path / "projects" / "demo"
    (proj / "work").mkdir(parents=True)  # 无 RETROSPECTIVE.json
    bank_dir = tmp_path / "projects" / "_bank"
    monkeypatch.setattr(RB, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(RB, "BANK_DIR", bank_dir)
    monkeypatch.setattr(RB, "BANK_FILE", bank_dir / "reflections.json")
    bank = RB.scan_projects()
    assert bank["projects_scanned"] == 1
    assert bank["projects_with_retro"] == 0
    assert bank["total_lessons"] == 0
