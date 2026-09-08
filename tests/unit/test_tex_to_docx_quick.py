"""Quick test for tex_to_docx.py block-based parser."""
import tempfile
import shutil
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from core.tools.tex_to_docx import (
    _parse_tabular, _latex_to_blocks, build_docx_text, _extract_title
)

TAB_BODY = "\\hline\nMethod & Accuracy & Time \\\\\n\\hline\nGA & 95.2 & 12.3 \\\\\nPSO & 93.8 & 8.7 \\\\\n\\hline\n"

TEX_LINES = [
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


def test_tabular_parser():
    headers, rows = _parse_tabular(TAB_BODY)
    assert len(headers) == 3
    assert len(rows) == 2


def test_block_parser():
    tex_content = "\n".join(TEX_LINES)
    blocks = _latex_to_blocks(tex_content)

    table_count = sum(1 for b in blocks if b["type"] == "table")
    eq_count = sum(1 for b in blocks if b["type"] == "equation")
    fig_count = sum(1 for b in blocks if b["type"] == "figure")
    head_count = sum(1 for b in blocks if b["type"] == "heading")

    assert table_count == 1
    assert eq_count == 2
    assert fig_count == 1
    assert head_count >= 3


def test_docx_generation():
    tex_content = "\n".join(TEX_LINES)
    tmp = Path(tempfile.mkdtemp())
    try:
        docx_path = tmp / "test.docx"
        title = _extract_title(tex_content)
        ok = build_docx_text(tex_content, title, str(docx_path))
        assert ok
        assert docx_path.stat().st_size > 0

        with zipfile.ZipFile(docx_path) as z:
            names = z.namelist()
            assert "word/styles.xml" in names
            assert "word/document.xml" in names
            doc_xml = z.read("word/document.xml").decode("utf-8")
            assert "<w:tbl>" in doc_xml
            assert "w:tblBorders" in doc_xml
            assert "Heading1" in doc_xml
            assert "Equation" in doc_xml
    finally:
        shutil.rmtree(tmp)
