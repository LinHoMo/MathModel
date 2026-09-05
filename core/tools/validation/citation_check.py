#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""citation_check.py —— 参考文献可信度静态检查

检查项:
1. 占位符扫描: 检测 {cite_XXX} / {ref_XXX} / @cite_XXX 等未解析的引用占位符
2. 格式校验: BibTeX 条目字段完整性 / DOI 格式 / 年份合理性
3. 引用闭合: 所有 \\cite{...} 键都在 references.bib 中存在
4. 承诺兑现: 扫一遍 main.tex 中声明性表述，结果/结论中是否有对应呼应

命令:
    python core/tools/citation_check.py --project <项目路径> [--json]
    python core/tools/citation_check.py --bib <references.bib> [--tex <main.tex>] [--json]

零第三方依赖。只读不写。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# 1. 占位符扫描
# ---------------------------------------------------------------------------

PLACEHOLDER_PATTERNS = [
    re.compile(r"\{cite_[^}]+\}"),
    re.compile(r"\{ref_[^}]+\}"),
    re.compile(r"\\?cite\{[?？]+\}"),
    re.compile(r"\\?citep\{[?？]+\}"),
    re.compile(r"\\?citet\{[?？]+\}"),
    re.compile(r"@cite_[a-zA-Z0-9_]+"),
    re.compile(r"\\?cite\{TODO|XXX|FIXME|TBD"),
]


def scan_placeholders(tex_text: str) -> list[dict]:
    """扫描正文中的未解析占位符。"""
    found: list[dict] = []
    seen: set[str] = set()
    for pat in PLACEHOLDER_PATTERNS:
        for m in pat.finditer(tex_text):
            val = m.group(0)
            if val not in seen:
                seen.add(val)
                line_no = tex_text.count("\n", 0, m.start()) + 1
                found.append({"value": val, "line": line_no, "type": "placeholder"})
    return found


# ---------------------------------------------------------------------------
# 2. BibTeX 解析与格式校验
# ---------------------------------------------------------------------------

BIB_ENTRY_START = re.compile(r"@(\w+)\s*\{\s*([^,]*),")
BIB_FIELD = re.compile(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|\w+)")
DOI_RE = re.compile(r"^10\.[0-9]{4,9}/[-._;()/:A-Za-z0-9]+$")
YEAR_NOW = datetime.now().year


def parse_bib(text: str) -> list[dict]:
    """极简 BibTeX 解析。"""
    entries: list[dict] = []
    for m in BIB_ENTRY_START.finditer(text):
        etype = m.group(1).lower()
        ekey = m.group(2).strip()
        depth = 1
        i = m.start()
        while i < len(text) and depth > 0:
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            i += 1
        body = text[m.end() - len(ekey) - 1:i - 1]
        fields: dict[str, str] = {}
        for fm in BIB_FIELD.finditer(body):
            k = fm.group(1).lower()
            v = fm.group(2)
            if v.startswith("{") and v.endswith("}"):
                v = v[1:-1]
            elif v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            fields[k] = v
        entries.append({"type": etype, "key": ekey, "fields": fields})
    return entries


def _blank(s: str | None) -> bool:
    return not s or not s.strip()


def validate_entry(entry: dict) -> list[str]:
    """校验单条 BibTeX 字段，返回问题列表。"""
    issues: list[str] = []
    key = entry.get("key", "")
    f = entry.get("fields", {})
    etype = entry.get("type", "")

    if not key:
        issues.append("空键 @ entry")
        return issues

    if etype == "article":
        for required in ("title", "author", "year"):
            if _blank(f.get(required)):
                issues.append(f"{key}: 缺必要字段 {required}")
        if _blank(f.get("journal")) and _blank(f.get("journaltitle")):
            issues.append(f"{key}: article 缺期刊字段(journal)")
    elif etype in ("book", "inbook"):
        for required in ("title", "author", "year"):
            if _blank(f.get(required)):
                issues.append(f"{key}: 缺必要字段 {required}")
        if _blank(f.get("publisher")):
            issues.append(f"{key}: book 缺 publisher")
    elif etype in ("inproceedings", "conference"):
        for required in ("title", "author", "year", "booktitle"):
            if _blank(f.get(required)):
                issues.append(f"{key}: 缺必要字段 {required}")
    elif etype in ("misc", "online"):
        if _blank(f.get("title")):
            issues.append(f"{key}: misc/online 缺 title")
        if _blank(f.get("url")) and _blank(f.get("howpublished")):
            issues.append(f"{key}: online 缺 url/howpublished")

    doi = f.get("doi", "").strip()
    if doi:
        doi_clean = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
        if not DOI_RE.match(doi_clean):
            issues.append(f"{key}: DOI 格式异常 {doi}")

    year_str = f.get("year", "").strip()
    if year_str:
        try:
            y = int(year_str)
            if y < 1900 or y > YEAR_NOW + 2:
                issues.append(f"{key}: 年份异常 {year_str}")
        except ValueError:
            issues.append(f"{key}: 非数字年份 {year_str}")

    author = f.get("author", "")
    if author and author.strip() in ("", "others", "et al"):
        issues.append(f"{key}: 作者字段占位 {author}")

    return issues


# ---------------------------------------------------------------------------
# 3. 引用闭合
# ---------------------------------------------------------------------------

CITE_KEYS_RE = re.compile(
    r"\\(?:cite|citep|citet|citeauthor|citeyear)\s*\{([^}]+)\}"
)


def extract_cite_keys(tex_text: str) -> set[str]:
    keys: set[str] = set()
    for m in CITE_KEYS_RE.finditer(tex_text):
        g = m.group(1)
        for k in g.split(","):
            keys.add(k.strip())
    return {k for k in keys if k}


def check_citation_closure(tex_files: list[Path], bib_entries: list[dict]) -> dict:
    defined_keys = {e["key"] for e in bib_entries if e.get("key")}
    undef_keys: list[str] = []
    unused_keys: set[str] = set(defined_keys)
    for tf in tex_files:
        if not tf.exists():
            continue
        try:
            text = tf.read_text(encoding="utf-8")
        except OSError:
            continue
        cite_keys = extract_cite_keys(text)
        unused_keys -= cite_keys
        for k in cite_keys:
            if k not in defined_keys:
                undef_keys.append(k)
    cited_keys = defined_keys - unused_keys
    return {
        "undefined_keys": sorted(set(undef_keys)),
        "unused_keys": sorted(unused_keys),
        "defined_count": len(defined_keys),
        "cited_count": len(cited_keys),
    }


# ---------------------------------------------------------------------------
# 4. 承诺兑现（基于正则的轻量扫描）
# ---------------------------------------------------------------------------

CLAIM_INTRO_RE = re.compile(
    r"(?:本文|我们|本研究)\s*(?:提出|建立|证明|给出|推导|构造|设计|改进)"
    r"([^。，；\n]{2,60})", re.MULTILINE
)
CLAIM_RESULT_RE = re.compile(
    r"(?:结果|实验|仿真|对比|数值)\s*(?:表明|显示|验证|证实|支持)"
    r"([^。，；\n]{2,60})", re.MULTILINE
)


def scan_claim_consistency(tex_files: list[Path]) -> dict:
    intro_claims: list[str] = []
    result_echoes: list[str] = []
    for tf in tex_files:
        if not tf.exists():
            continue
        try:
            text = tf.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in CLAIM_INTRO_RE.finditer(text):
            intro_claims.append(m.group(1))
        for m in CLAIM_RESULT_RE.finditer(text):
            result_echoes.append(m.group(1))
    return {
        "declaration_count": len(intro_claims),
        "result_echo_count": len(result_echoes),
        "declarations": intro_claims[:5],
        "echoes": result_echoes[:5],
    }


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def check_project(project_path: Path, as_json: bool = False) -> dict:
    """单项目引用检查入口。"""
    bib_files = list(project_path.rglob("references.bib")) + list(project_path.rglob("*.bib"))
    tex_files = list(project_path.rglob("*.tex"))
    tex_files = [t for t in tex_files
                 if "templates" not in t.parts and "template" not in t.parts]

    all_placeholders: list[dict] = []
    bib_issues: list[str] = []
    all_entries: list[dict] = []

    for tf in tex_files:
        try:
            text = tf.read_text(encoding="utf-8")
        except OSError:
            continue
        ph = scan_placeholders(text)
        for p in ph:
            p["file"] = str(tf.relative_to(project_path))
        all_placeholders.extend(ph)

    for bf in bib_files:
        try:
            btext = bf.read_text(encoding="utf-8")
        except OSError:
            continue
        entries = parse_bib(btext)
        all_entries.extend(entries)
        rel_bf = str(bf.relative_to(project_path))
        for e in entries:
            for issue in validate_entry(e):
                bib_issues.append(f"{rel_bf} :: {issue}")

    closure = check_citation_closure(tex_files, all_entries)
    claims = scan_claim_consistency(tex_files)

    has_blocking = bool(all_placeholders) or bool(closure.get("undefined_keys"))
    severity = "blocking" if has_blocking else ("warn" if bib_issues else "ok")
    passed = not has_blocking and not bib_issues

    report = {
        "mode": "citation_check",
        "project": str(project_path),
        "summary": {
            "bib_files": len(bib_files),
            "tex_files": len(tex_files),
            "bib_entries": len(all_entries),
            "undefined_cites": len(closure.get("undefined_keys", [])),
            "unused_bibs": len(closure.get("unused_keys", [])),
            "placeholders": len(all_placeholders),
            "bib_issues": len(bib_issues),
            "severity": severity,
            "passed": passed,
        },
        "placeholders": all_placeholders,
        "undefined_cites": closure.get("undefined_keys", []),
        "unused_bibs": closure.get("unused_keys", []),
        "bib_issues": bib_issues,
        "claim_consistency": claims,
    }

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    if passed:
        print(f"[citation] OK — {len(all_entries)} 条目，无占位符，无悬空引用")
    else:
        print(f"[citation] {severity.upper()} — "
              f"占位符 {len(all_placeholders)}，悬空 {len(closure.get('undefined_keys', []))}，"
              f"bib 格式问题 {len(bib_issues)}")
    if all_placeholders:
        print("  占位符:")
        for p in all_placeholders[:10]:
            print(f"    - {p['file']}:{p['line']}  {p['value']}")
    if closure.get("undefined_keys"):
        print("  悬空引用:")
        for k in closure["undefined_keys"][:10]:
            print(f"    - {k}")
    if bib_issues:
        print("  格式问题:")
        for i in bib_issues[:10]:
            print(f"    - {i}")

    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="参考文献可信度静态检查")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_proj = sub.add_parser("project", help="单项目检查")
    p_proj.add_argument("path", help="项目路径")
    p_proj.add_argument("--json", action="store_true")

    p_bib = sub.add_parser("bib", help="仅检查 bib 文件")
    p_bib.add_argument("path", help=".bib 文件路径")
    p_bib.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "project":
        report = check_project(Path(args.path), as_json=args.json)
        return 0 if report.get("summary", {}).get("passed") else 1

    if args.cmd == "bib":
        p = Path(args.path)
        if not p.exists():
            print(f"[citation] 文件不存在: {p}", file=sys.stderr)
            return 1
        text = p.read_text(encoding="utf-8")
        entries = parse_bib(text)
        issues_all: list[str] = []
        for e in entries:
            for issue in validate_entry(e):
                issues_all.append(issue)
        report = {
            "file": str(p),
            "entries": len(entries),
            "issues": len(issues_all),
            "details": issues_all[:30],
        }
        if getattr(args, "json", False):
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"[citation] {p.name}: {len(entries)} 条目, {len(issues_all)} 个问题")
            for i in issues_all[:20]:
                print(f"  - {i}")
        return 0 if not issues_all else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
