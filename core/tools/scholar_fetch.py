#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scholar_fetch.py — 学术文献检索 + BibTeX 导出（L11 层）

用法:
    python core/tools/scholar_fetch.py bibtex "多目标 灰色预测 TOPSIS" --limit 5
    python core/tools/scholar_fetch.py bibtex "KNN imputation" --limit 3 --output refs.bib

零第三方依赖（使用 Semantic Scholar 开放 API）。
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_FIELDS = "title,authors,year,externalIds,url,abstract,venue"

REQUEST_HEADERS = {
    "User-Agent": "MathModel/1.0 (academic research assistant)",
    "Accept": "application/json",
}

DEFAULT_LIMIT = 5
DEFAULT_TIMEOUT = 15


def _query_semantic_scholar(query: str, *, limit: int = DEFAULT_LIMIT,
                            timeout: int = DEFAULT_TIMEOUT) -> list[dict]:
    """调用 Semantic Scholar Search API，返回结果列表。"""
    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": SEMANTIC_SCHOLAR_FIELDS,
    })
    url = f"{SEMANTIC_SCHOLAR_API}?{params}"
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("data") or []
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"[scholar_fetch] API 请求失败: {exc}", file=sys.stderr)
        return []


def _format_bibtex_entry(paper: dict) -> str:
    """把 Semantic Scholar 记录转成 BibTeX entry 字符串。"""
    authors = paper.get("authors") or []
    author_str = " and ".join(a.get("name", "Unknown") for a in authors)
    year = paper.get("year", "")
    title = paper.get("title", "Untitled")
    venue = paper.get("venue", "")
    url = paper.get("url", "")
    abstract = paper.get("abstract", "")
    doi = (paper.get("externalIds") or {}).get("DOI", "")

    first_author_last = author_str.split()[0].rstrip(",") if author_str else "unknown"
    cite_key = f"{first_author_last}{year}"

    lines = [
        f"@article{{{cite_key},",
        f"  title     = {{{title}}},",
        f"  author    = {{{author_str}}},",
        f"  year      = {{{year}}},",
    ]
    if venue:
        lines.append(f"  journal   = {{{venue}}},")
    if doi:
        lines.append(f"  doi       = {{{doi}}},")
    if url:
        lines.append(f"  url       = {{{url}}},")
    if abstract:
        wrapped = textwrap.fill(abstract, width=72, initial_indent="  ",
                                subsequent_indent="    ")
        lines.append(f"  abstract  = {{{abstract}}},")
    lines.append("}")
    return "\n".join(lines)


def cmd_bibtex(args) -> int:
    query = args.query
    limit = args.limit or DEFAULT_LIMIT
    print(f"[scholar_fetch] 正在检索: '{query}' (limit={limit}) ...", file=sys.stderr)

    papers = _query_semantic_scholar(query, limit=limit, timeout=args.timeout)
    if not papers:
        print("[scholar_fetch] 未找到匹配结果。", file=sys.stderr)
        return 1

    bib_entries = []
    print(f"\n找到 {len(papers)} 条结果:\n", file=sys.stderr)
    for i, paper in enumerate(papers, 1):
        title = paper.get("title", "Untitled")
        authors = ", ".join(a.get("name", "?") for a in (paper.get("authors") or []))
        year = paper.get("year", "?")
        venue = paper.get("venue", "")
        print(f"  {i}. [{year}] {title}")
        print(f"     作者: {authors}")
        if venue:
            print(f"     来源: {venue}")
        print()
        bib_entries.append(_format_bibtex_entry(paper))

    bib_content = "\n\n".join(bib_entries) + "\n"

    if args.output:
        Path(args.output).write_text(bib_content, encoding="utf-8")
        print(f"[scholar_fetch] BibTeX 已写入: {args.output}", file=sys.stderr)
    else:
        print("--- BibTeX ---\n")
        print(bib_content)

    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="学术文献检索 + BibTeX 导出（Semantic Scholar API）"
    )
    sub = parser.add_subparsers(dest="command")

    p_bib = sub.add_parser("bibtex", help="检索并输出 BibTeX 格式引用")
    p_bib.add_argument("query", help="检索关键词")
    p_bib.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="最大返回数")
    p_bib.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="超时秒数")
    p_bib.add_argument("--output", "-o", help="输出 .bib 文件路径（默认打印到 stdout）")
    p_bib.set_defaults(fn=cmd_bibtex)

    args = parser.parse_args(argv)
    if not hasattr(args, "fn"):
        parser.print_help()
        return 1
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
