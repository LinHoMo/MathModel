#!/usr/bin/env python3
"""Quick test for tex_to_docx.py block-based parser."""
import tempfile, shutil, os, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))

from core.tools.tex_to_docx import (
    _parse_tabular, _latex_to_blocks, build_docx_text, _extract_title
)

# --- Test 1: tabular parser ---
tab_body = "\\hline\nMethod & Accuracy & Time \\\\\n\\hline\nGA & 95.2 & 12.3 \\\\\nPSO & 93.8 & 8.7 \\\\\n\\hline\n"
headers, rows = _parse_tabular(tab_body)
print(f"Tabular: {len(headers)} cols, {len(rows)} rows")
print(f"  Headers: {headers}")
for i, r in enumerate(rows):
    print(f"  Row {i}: {r}")
assert len(headers) == 3, f"Expected 3 headers, got {len(headers)}"
assert len(rows) == 2, f"Expected 2 data rows, got {len(rows)}"
print("  PASS")

# --- Test 2: full pipeline ---
tex_lines = [
    "\\documentclass{article}",
    "\\title{Test Paper}",
    "\\begin{document}",
    "",
    "\\section{Introduction}",
    "Some text here with \\textbf{bold} and \\emph{emphasis}.",
    "",
    "\\subsection{Data}",
    "See table below.",
    "",
    "\\begin{table}[htbp]",
    "\\caption{Experimental Data}",
    "\\begin{tabular}{ccc}",
    "\\hline",
    "Method & Accuracy & Time \\\\",
    "\\hline",
    "GA & 95.2 & 12.3 \\\\",
    "PSO & 93.8 & 8.7 \\\\",
    "SA & 91.5 & 15.1 \\\\",
    "\\hline",
    "\\end{tabular}",
    "\\end{table}",
    "",
    "\\section{Model}",
    "We build the following model:",
    "",
    "\\begin{equation}",
    "\\label{eq:obj}",
    "f(x) = x^2 + y^2",
    "\\end{equation}",
    "",
    "With constraints:",
    "",
    "\\begin{align}",
    "g(x) &\\leq 0 \\\\",
    "h(x) &= 0",
    "\\end{align}",
    "",
    "\\section{Results}",
    "Results shown in figure.",
    "",
    "\\begin{figure}[htbp]",
    "\\includegraphics[width=0.8\\textwidth]{result.png}",
    "\\caption{Optimization Results}",
    "\\end{figure}",
    "",
    "Our method \\cite{smith2020} outperforms baseline.",
    "",
    "\\end{document}",
]
tex_content = "\n".join(tex_lines)

blocks = _latex_to_blocks(tex_content)
print(f"\nBlocks ({len(blocks)}):")
table_count = 0
eq_count = 0
fig_count = 0
head_count = 0
para_count = 0
for b in blocks:
    t = b["type"]
    if t == "table":
        table_count += 1
        print(f"  TABLE: {len(b['headers'])} cols, {len(b['rows'])} rows, cap={b['caption']}")
        assert len(b["headers"]) == 3
        assert len(b["rows"]) == 3
    elif t == "equation":
        eq_count += 1
        print(f"  EQUATION #{b['num']}: {b['hint'][:50]}")
    elif t == "figure":
        fig_count += 1
        print(f"  FIGURE: {b['caption']}")
    elif t == "heading":
        head_count += 1
        print(f"  HEADING H{b['level']}: {b['text']}")
    else:
        para_count += 1
        print(f"  PARA: {b['text'][:60]}")

print(f"\nSummary: {head_count} headings, {para_count} paras, {table_count} tables, {eq_count} equations, {fig_count} figures")
assert table_count == 1, f"Expected 1 table, got {table_count}"
assert eq_count == 2, f"Expected 2 equations, got {eq_count}"
assert fig_count == 1, f"Expected 1 figure, got {fig_count}"
assert head_count >= 3, f"Expected >=3 headings, got {head_count}"

# --- Test 3: DOCX generation ---
tmp = Path(tempfile.mkdtemp())
docx_path = tmp / "test.docx"
title = _extract_title(tex_content)
ok = build_docx_text(tex_content, title, str(docx_path))
assert ok, "DOCX build failed"
size = docx_path.stat().st_size
print(f"\nDOCX: OK, {size} bytes")

with zipfile.ZipFile(docx_path) as z:
    names = z.namelist()
    assert "word/styles.xml" in names, "Missing styles.xml"
    assert "word/document.xml" in names, "Missing document.xml"
    doc_xml = z.read("word/document.xml").decode("utf-8")
    assert "<w:tbl>" in doc_xml, "Missing table element"
    assert "w:tblBorders" in doc_xml, "Missing table borders"
    assert "Heading1" in doc_xml, "Missing Heading1 style"
    assert "Equation" in doc_xml, "Missing Equation style"
    print("  styles.xml: present")
    print("  <w:tbl>: present")
    print("  Heading1 style: present")
    print("  Equation style: present")

shutil.rmtree(tmp)
print("\nAll tests PASSED!")
