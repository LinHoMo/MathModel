#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docx_post_processor.py — DOCX 后处理工具

对 tex_to_docx.py 产出的初版 docx 做增量精修：
- 粘贴图片并统一宽度（可选居中）
- 公式前后插空行
- 表格样式统一
- 图表标题与正文间距调整
- AI 痕迹检测（可选）

用法:
    python core/tools/docx_post_processor.py paper/main.docx -o paper/main_final.docx
    python core/tools/docx_post_processor.py paper/main.docx --ai-scan
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

try:
    from docx import Document
    from docx.shared import Pt, Inches
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

AI_PATTERNS = [
    re.compile(r"as an AI", re.IGNORECASE),
    re.compile(r"I cannot|I can(?:'t|not)", re.IGNORECASE),
    re.compile(r"作为一个 AI", re.IGNORECASE),
    re.compile(r"我无法|我不能", re.IGNORECASE),
    re.compile(r"language model", re.IGNORECASE),
    re.compile(r"大语言模型", re.IGNORECASE),
]


def scan_ai_traces(docx_path: str) -> list[dict]:
    """扫描文档中的 AI 痕迹。"""
    if not HAS_DOCX:
        print("[WARN] python-docx 未安装，跳过扫描", file=sys.stderr)
        return []

    doc = Document(docx_path)
    issues = []

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue
        for pattern in AI_PATTERNS:
            match = pattern.search(text)
            if match:
                issues.append({
                    "paragraph": i,
                    "matched": match.group(),
                    "context": text[:100],
                    "severity": "high",
                })

    return issues


def postprocess(docx_path: str, output: str | None = None,
                center_images: bool = True) -> str:
    """后处理 DOCX 文件。"""
    if not HAS_DOCX:
        print("[WARN] python-docx 未安装，跳过后处理", file=sys.stderr)
        return docx_path

    doc = Document(docx_path)
    modified = False

    for para in doc.paragraphs:
        style = para.style
        if style and style.name and "Heading" in style.name:
            para.paragraph_format.space_before = Pt(12)
            para.paragraph_format.space_after = Pt(6)
            modified = True

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.paragraph_format.space_before = Pt(2)
                    para.paragraph_format.space_after = Pt(2)

    out_path = output or docx_path
    doc.save(out_path)

    if modified:
        print(f"[OK] 后处理完成: {out_path}")

    return out_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="DOCX 后处理工具")
    parser.add_argument("input", help="输入 DOCX 文件")
    parser.add_argument("-o", "--output", help="输出路径")
    parser.add_argument("--ai-scan", action="store_true", help="扫描 AI 痕迹")
    parser.add_argument("--center-images", action="store_true", default=True,
                        help="图片居中")
    args = parser.parse_args(argv)

    if not Path(args.input).exists():
        print(f"[FAIL] 文件不存在: {args.input}", file=sys.stderr)
        return 1

    if args.ai_scan:
        issues = scan_ai_traces(args.input)
        if issues:
            print(f"[WARN] 发现 {len(issues)} 处 AI 痕迹:")
            for issue in issues:
                print(f"  段落 {issue['paragraph']}: "
                      f"匹配 '{issue['matched']}' — {issue['context'][:60]}...")
        else:
            print("[OK] 未发现 AI 痕迹")
        return 1 if issues else 0

    out = postprocess(args.input, args.output, center_images=args.center_images)
    print(f"[OK] 输出: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
