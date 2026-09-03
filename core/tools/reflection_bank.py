#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reflection_bank.py — 反思银行：跨项目经验沉淀与检索

把各项目的赛后回顾（RETROSPECTIVE.json）聚合为可检索的经验库。支持：
- 扫描所有项目 retrospective 数据
- 按关键词 / 手 / 竞赛类型检索
- 工具接地验证（确认引用的工具脚本确实存在）
- 导出为 pitfalls/ 格式供知识库归档

用法:
    python core/tools/reflection_bank.py scan          # 扫描所有项目，更新银行
    python core/tools/reflection_bank.py search <关键词> # 搜索经验
    python core/tools/reflection_bank.py grounding      # 验证工具引用接地
    python core/tools/reflection_bank.py stats           # 统计概览
    python core/tools/reflection_bank.py export-pitfalls # 导出为 pitfalls 格式

零第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "projects"
BANK_DIR = PROJECTS_DIR / "_bank"
BANK_FILE = BANK_DIR / "reflections.json"

HANDS = ("modeler", "programmer", "writer", "reviewer")
TOOL_SCRIPTS = sorted(
    p.name for p in (ROOT / "core" / "tools").glob("*.py")
    if p.name != "__init__.py"
)


def _load_retrospective(project_dir: Path) -> dict | None:
    json_path = project_dir / "work" / "RETROSPECTIVE.json"
    if not json_path.exists():
        return None
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    data["_project"] = project_dir.name
    data["_path"] = str(json_path)
    mtime = json_path.stat().st_mtime
    data["_mtime"] = datetime.fromtimestamp(mtime).isoformat(timespec="seconds")
    return data


def _extract_lessons(report: dict) -> list[dict]:
    """从回顾报告中提取可检索的经验条目。"""
    lessons = []
    project = report.get("_project", "unknown")

    failures = report.get("failure_records", [])
    for rec in failures:
        if isinstance(rec, dict):
            lessons.append({
                "source": project,
                "type": "failure",
                "hand": rec.get("hand", ""),
                "agent": rec.get("agent", ""),
                "detail": json.dumps(rec, ensure_ascii=False),
                "keywords": _extract_keywords(json.dumps(rec, ensure_ascii=False)),
            })

    review = report.get("review", {})
    weak = review.get("weak_dimensions", [])
    if weak:
        lessons.append({
            "source": project,
            "type": "weak_dimension",
            "hand": "reviewer",
            "agent": "judge-scorer",
            "detail": f"薄弱维度: {', '.join(weak)}",
            "keywords": weak,
        })

    by_hand_fail = report.get("failed_by_hand", {})
    for hand, count in by_hand_fail.items():
        if count > 0:
            lessons.append({
                "source": project,
                "type": "hand_failure_summary",
                "hand": hand,
                "agent": "",
                "detail": f"{hand} 手失败 {count} 次",
                "keywords": [hand, "failure", f"count={count}"],
            })

    return lessons


def _extract_keywords(text: str) -> list[str]:
    """简单关键词提取：中文词组 + 英文标识符。"""
    cn = re.findall(r"[\u4e00-\u9fff]{2,6}", text)
    en = re.findall(r"[a-zA-Z_][\w-]{2,}", text)
    return list(set(cn + en))[:20]


def scan_projects() -> dict:
    """扫描所有项目，聚合经验到银行。"""
    BANK_DIR.mkdir(parents=True, exist_ok=True)

    all_lessons = []
    projects_scanned = 0
    projects_with_retro = 0

    if not PROJECTS_DIR.exists():
        return {"lessons": [], "projects_scanned": 0, "projects_with_retro": 0}

    for entry in sorted(PROJECTS_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        projects_scanned += 1
        retro = _load_retrospective(entry)
        if retro is None:
            continue
        projects_with_retro += 1
        lessons = _extract_lessons(retro)
        all_lessons.extend(lessons)

    bank = {
        "updated": datetime.now().isoformat(timespec="seconds"),
        "projects_scanned": projects_scanned,
        "projects_with_retro": projects_with_retro,
        "total_lessons": len(all_lessons),
        "lessons": all_lessons,
    }

    BANK_FILE.write_text(
        json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return bank


def load_bank() -> dict:
    if not BANK_FILE.exists():
        return {"lessons": [], "total_lessons": 0}
    with open(BANK_FILE, encoding="utf-8") as f:
        return json.load(f)


def search_bank(query: str) -> list[dict]:
    """按关键词搜索经验条目。"""
    bank = load_bank()
    query_lower = query.lower()
    results = []
    for lesson in bank.get("lessons", []):
        text = lesson.get("detail", "") + " " + " ".join(lesson.get("keywords", []))
        if query_lower in text.lower():
            results.append(lesson)
    return results


def check_grounding() -> list[dict]:
    """检查经验条目中引用的工具脚本是否存在。"""
    bank = load_bank()
    issues = []
    tool_pattern = re.compile(r"(?:core/tools/)?(\w+\.py)")

    for lesson in bank.get("lessons", []):
        detail = lesson.get("detail", "")
        refs = tool_pattern.findall(detail)
        for ref in refs:
            if ref not in TOOL_SCRIPTS:
                issues.append({
                    "source": lesson.get("source", ""),
                    "referenced_tool": ref,
                    "exists": False,
                    "available": TOOL_SCRIPTS,
                })

    return issues


def compute_stats() -> dict:
    """统计概览。"""
    bank = load_bank()
    lessons = bank.get("lessons", [])

    by_type = {}
    by_hand = {}
    by_source = {}

    for lesson in lessons:
        t = lesson.get("type", "unknown")
        h = lesson.get("hand", "unknown")
        s = lesson.get("source", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        by_hand[h] = by_hand.get(h, 0) + 1
        by_source[s] = by_source.get(s, 0) + 1

    return {
        "total_lessons": len(lessons),
        "by_type": by_type,
        "by_hand": by_hand,
        "by_source": by_source,
        "projects_scanned": bank.get("projects_scanned", 0),
        "projects_with_retro": bank.get("projects_with_retro", 0),
        "updated": bank.get("updated", ""),
    }


def export_pitfalls() -> list[dict]:
    """把经验条目转为 pitfalls/ 归档格式。"""
    bank = load_bank()
    pitfalls = []

    for lesson in bank.get("lessons", []):
        if lesson.get("type") == "failure":
            pitfalls.append({
                "id": f"retro-{lesson['source']}-{lesson.get('agent', 'unknown')}",
                "title": f"[{lesson['source']}] {lesson.get('hand', '')}/{lesson.get('agent', '')} 失败",
                "category": lesson.get("hand", "general"),
                "severity": "medium",
                "description": lesson.get("detail", ""),
                "source": f"reflection_bank: {lesson['source']}",
                "keywords": lesson.get("keywords", []),
            })

    return pitfalls


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="反思银行：跨项目经验沉淀与检索")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("scan", help="扫描所有项目，更新银行")

    sp_search = sub.add_parser("search", help="搜索经验")
    sp_search.add_argument("query", help="搜索关键词")

    sub.add_parser("grounding", help="验证工具引用接地")
    sub.add_parser("stats", help="统计概览")
    sub.add_parser("export-pitfalls", help="导出为 pitfalls 格式")

    args = parser.parse_args(argv)

    if args.command == "scan":
        bank = scan_projects()
        print(f"[OK] 扫描 {bank['projects_scanned']} 个项目，"
              f"{bank['projects_with_retro']} 个有回顾数据，"
              f"提取 {bank['total_lessons']} 条经验")
        print(f"[OK] 银行已更新: {BANK_FILE}")
        return 0

    elif args.command == "search":
        results = search_bank(args.query)
        if not results:
            print(f"未找到匹配 '{args.query}' 的经验")
            return 0
        print(f"找到 {len(results)} 条匹配:\n")
        for r in results:
            print(f"  [{r['type']}] {r['source']} | {r['hand']}/{r['agent']}")
            print(f"    {r['detail']}")
            print()
        return 0

    elif args.command == "grounding":
        issues = check_grounding()
        if not issues:
            print("[OK] 所有工具引用均已接地")
            return 0
        print(f"[WARN] 发现 {len(issues)} 个未接地引用:")
        for issue in issues:
            print(f"  {issue['source']}: 引用 '{issue['referenced_tool']}' 不存在")
        return 1

    elif args.command == "stats":
        stats = compute_stats()
        print(f"反思银行统计:")
        print(f"  更新时间: {stats['updated']}")
        print(f"  扫描项目: {stats['projects_scanned']}")
        print(f"  有回顾数据: {stats['projects_with_retro']}")
        print(f"  经验总数: {stats['total_lessons']}")
        if stats["by_type"]:
            print(f"  按类型: {json.dumps(stats['by_type'], ensure_ascii=False)}")
        if stats["by_hand"]:
            print(f"  按手: {json.dumps(stats['by_hand'], ensure_ascii=False)}")
        return 0

    elif args.command == "export-pitfalls":
        pitfalls = export_pitfalls()
        if not pitfalls:
            print("无可导出的经验条目")
            return 0
        out_path = BANK_DIR / "pitfalls_export.json"
        out_path.write_text(
            json.dumps(pitfalls, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[OK] 导出 {len(pitfalls)} 条到 {out_path}")
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
