#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""text_cleanup.py — 文本清理工具

清理论文章节中的常见问题：
- 多余空行
- AI 痕迹
- 中英文混排格式
- 标点规范

用法:
    python core/tools/text_cleanup.py paper/sections/*.tex
    python core/tools/text_cleanup.py paper/main.tex --inplace
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AI_PATTERNS = [
    (re.compile(r"as an AI", re.IGNORECASE), "[AI-LANG]"),
    (re.compile(r"I cannot|I can(?:'t|not)", re.IGNORECASE), "[AI-LANG]"),
    (re.compile(r"作为一个 AI", re.IGNORECASE), "[AI-LANG]"),
    (re.compile(r"我无法|我不能", re.IGNORECASE), "[AI-LANG]"),
    (re.compile(r"language model", re.IGNORECASE), "[AI-LANG]"),
    (re.compile(r"大语言模型", re.IGNORECASE), "[AI-LANG]"),
]

MULTI_BLANK = re.compile(r"\n{3,}")
TRAILING_SPACE = re.compile(r"[ \t]+$", re.MULTILINE)
DOUBLE_SPACE = re.compile(r"  +")


def cleanup_text(text: str, fix_ai: bool = True) -> tuple[str, list[str]]:
    """清理文本，返回（清理后文本，问题列表）。"""
    issues = []

    if fix_ai:
        for pattern, tag in AI_PATTERNS:
            for match in pattern.finditer(text):
                issues.append(f"{tag} {match.group()} @ pos {match.start()}")

    text = MULTI_BLANK.sub("\n\n", text)
    text = TRAILING_SPACE.sub("", text)
    text = DOUBLE_SPACE.sub(" ", text)

    return text, issues


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="文本清理工具")
    parser.add_argument("files", nargs="+", help="输入文件")
    parser.add_argument("--inplace", action="store_true", help="就地修改")
    parser.add_argument("--no-ai-fix", action="store_true", help="不修复 AI 痕迹")
    args = parser.parse_args(argv)

    total_issues = 0

    for filepath in args.files:
        path = Path(filepath)
        if not path.exists():
            print(f"[WARN] 跳过不存在的文件: {path}", file=sys.stderr)
            continue

        text = path.read_text(encoding="utf-8")
        cleaned, issues = cleanup_text(text, fix_ai=not args.no_ai_fix)

        if issues:
            total_issues += len(issues)
            print(f"[{path.name}] 发现 {len(issues)} 个问题:")
            for issue in issues[:5]:
                print(f"  {issue}")
            if len(issues) > 5:
                print(f"  ... 及 {len(issues) - 5} 个其他问题")

        if args.inplace and cleaned != text:
            path.write_text(cleaned, encoding="utf-8")
            print(f"  [OK] 已清理: {path}")

    if total_issues == 0:
        print("[OK] 未发现问题")
    else:
        print(f"\n共发现 {total_issues} 个问题")

    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
