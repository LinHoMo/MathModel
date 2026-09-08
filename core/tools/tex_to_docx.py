#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tex_to_docx.py — LaTeX → DOCX 转换（L5 层 · P3）

把编译好的 PDF 所对应的 .tex 源文件转为结构化 DOCX，供人工编辑与评审。

用法:
    python core/tools/tex_to_docx.py paper/main.tex -o paper/main.docx
    python core/tools/tex_to_docx.py paper/main.tex --ai-scan

零 pypandoc 依赖（降级：逐段落手工映射）。"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "tools"))

from docx_post_processor import postprocess, scan_ai_traces  # 同级模块

try:
    from docx import Document
    from docx.shared import Pt, Inches
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

LATEX_INLINE_MATH = re.compile(r"\$([^$]+)\$")
LATEX_BLOCK_MATH = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
LATEX_CMD = re.compile(r"\\(?:textbf|textit|emph|texttt)\{([^}]+)\}")
LATEX_SECTION = re.compile(r"\\(?:section|subsection|subsubsection)\*?\{([^}]+)\}")
LATEX_LABEL = re.compile(r"\\label\{([^}]+)\}")
LATEX_REF = re.compile(r"\\(?:ref|eqref)\{([^}]+)\}")
LATEX_INCLUDEGRAPHICS = re.compile(r"\\includegraphics(?:\[.*?\])?\{([^}]+)\}")
LATEX_TABULAR = re.compile(r"\\begin\{tabular\}.*?\\end\{tabular\}", re.DOTALL)
LATEX_FIGURE = re.compile(
    r"\\begin\{figure\}.*?\\end\{figure\}", re.DOTALL
)
LATEX_COMMENT = re.compile(r"(?:^|(?<=\n))%.*?(?=\n|$)", re.MULTILINE)
LATEX_TABLE_ENV = re.compile(r"\\begin\{table\}(.*?)\\end\{table\}", re.DOTALL)
LATEX_FIGURE_ENV = re.compile(r"\\begin\{figure\}(.*?)\\end\{figure\}", re.DOTALL)
LATEX_EQUATION_ENV = re.compile(r"\\begin\{equation\}(.*?)\\end\{equation\}", re.DOTALL)
LATEX_ALIGN_ENV = re.compile(r"\\begin\{align\}(.*?)\\end\{align\}", re.DOTALL)
LATEX_CAPTION = re.compile(r"\\caption\{([^}]+)\}")
LATEX_INCLUDEGRAPHICS = re.compile(r"\\includegraphics(?:\[.*?\])?\{([^}]+)\}")


def _strip_comments(tex: str) -> str:
    return LATEX_COMMENT.sub("", tex)


def _parse_tabular(body: str) -> tuple[list[str], list[list[str]]]:
    """解析 tabular 环境体，返回 (headers, rows)。"""
    lines = [l.strip() for l in body.strip().split("\n") if l.strip()]
    headers = []
    rows = []
    for line in lines:
        # 跳过 \hline、空行、列格式说明 {ccc}
        if line.startswith("\\hline") or line == "" or re.match(r"^\{[a-z]+\}$", line):
            continue
        cells = [c.strip() for c in line.split("&")]
        cells = [re.sub(r"\\\\.*$", "", c).strip() for c in cells]
        if not headers:
            headers = cells
        else:
            rows.append(cells)
    return headers, rows


def _latex_to_blocks(tex: str) -> list[dict]:
    """把 LaTeX 文档解析为结构化块列表。"""
    tex = _strip_comments(tex)
    blocks = []
    eq_num = 0

    # 提取标题
    title_m = re.search(r"\\title\{([^}]+)\}", tex)
    if title_m:
        blocks.append({"type": "title", "text": title_m.group(1)})

    # 按行处理
    lines = tex.split("\n")
    i = 0
    in_equation = False
    eq_lines = []
    in_table = False
    table_lines = []
    in_figure = False
    figure_lines = []

    while i < len(lines):
        line = lines[i].strip()

        # 跳过 preamble
        if line.startswith("\\documentclass") or line.startswith("\\usepackage"):
            i += 1
            continue

        # 方程环境
        if line.startswith("\\begin{equation}") or line.startswith("\\begin{align}"):
            in_equation = True
            eq_lines = []
            i += 1
            continue
        if in_equation:
            if line.startswith("\\end{equation}") or line.startswith("\\end{align}"):
                in_equation = False
                eq_num += 1
                eq_text = " ".join(eq_lines)
                hint = re.sub(r"\\label\{[^}]+\}", "", eq_text).strip()
                blocks.append({"type": "equation", "num": eq_num, "hint": hint, "raw": eq_text})
            else:
                eq_lines.append(line)
            i += 1
            continue

        # 表格环境
        if line.startswith("\\begin{table}"):
            in_table = True
            table_lines = []
            i += 1
            continue
        if in_table:
            if line.startswith("\\end{table}"):
                in_table = False
                body = "\n".join(table_lines)
                cap_m = LATEX_CAPTION.search(body)
                caption = cap_m.group(1) if cap_m else ""
                tabular_m = re.search(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", body, re.DOTALL)
                if tabular_m:
                    headers, rows = _parse_tabular(tabular_m.group(1))
                else:
                    headers, rows = [], []
                blocks.append({"type": "table", "caption": caption, "headers": headers, "rows": rows})
            else:
                table_lines.append(line)
            i += 1
            continue

        # 图环境
        if line.startswith("\\begin{figure}"):
            in_figure = True
            figure_lines = []
            i += 1
            continue
        if in_figure:
            if line.startswith("\\end{figure}"):
                in_figure = False
                body = "\n".join(figure_lines)
                cap_m = LATEX_CAPTION.search(body)
                caption = cap_m.group(1) if cap_m else ""
                img_m = LATEX_INCLUDEGRAPHICS.search(body)
                image = img_m.group(1) if img_m else ""
                blocks.append({"type": "figure", "caption": caption, "image": image})
            else:
                figure_lines.append(line)
            i += 1
            continue

        # 标题
        sec_m = LATEX_SECTION.search(line)
        if sec_m:
            level = 1
            if "subsection" in line:
                level = 2
            elif "subsubsection" in line:
                level = 3
            blocks.append({"type": "heading", "level": level, "text": sec_m.group(1)})
            i += 1
            continue

        # 普通段落
        if line and not line.startswith("\\"):
            text = _latex_to_plain(line)
            if text.strip():
                blocks.append({"type": "para", "text": text})
            i += 1
            continue

        i += 1

    return blocks


def build_docx_text(tex: str, title: str, output: str) -> bool:
    """从 LaTeX 文本构建 DOCX 文件。"""
    if not HAS_DOCX:
        return False

    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()

    # 设置样式
    style = doc.styles["Normal"]
    style.font.size = Pt(12)

    # 添加标题
    if title:
        doc.add_heading(title, level=0)

    # 解析并添加内容
    blocks = _latex_to_blocks(tex)
    for block in blocks:
        btype = block.get("type")
        if btype == "heading":
            doc.add_heading(block["text"], level=block.get("level", 1))
        elif btype == "para":
            doc.add_paragraph(block["text"])
        elif btype == "table":
            headers = block.get("headers", [])
            rows = block.get("rows", [])
            if headers:
                table = doc.add_table(rows=1 + len(rows), cols=len(headers))
                table.style = "Table Grid"
                # 添加表格边框
                tbl = table._tbl
                tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')
                borders = OxmlElement('w:tblBorders')
                for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                    border = OxmlElement(f'w:{border_name}')
                    border.set(qn('w:val'), 'single')
                    border.set(qn('w:sz'), '4')
                    border.set(qn('w:space'), '0')
                    border.set(qn('w:color'), '000000')
                    borders.append(border)
                tblPr.append(borders)
                for j, h in enumerate(headers):
                    table.rows[0].cells[j].text = h
                for ri, row in enumerate(rows):
                    for ci, cell in enumerate(row):
                        table.rows[ri + 1].cells[ci].text = cell
        elif btype == "equation":
            doc.add_paragraph(f"[Equation {block.get('num', '')}]: {block.get('hint', '')}", style="Intense Quote")
        elif btype == "figure":
            doc.add_paragraph(f"[Figure]: {block.get('caption', '')}", style="Intense Quote")

    doc.save(output)
    return True


def _extract_title(tex: str) -> str:
    m = re.search(r"\\title\{([^}]+)\}", tex)
    return m.group(1) if m else ""


def _extract_content(tex: str) -> list[dict]:
    """提取正文内容段落（跳过 preamble、公式块、图表环境）。"""
    sections = []
    lines = tex.split("\n")
    in_preamble = False
    in_equation = False
    current_text = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith(r"\begin{equation}") or stripped.startswith(r"\["):
            in_equation = True
            continue
        if stripped.startswith(r"\end{equation}") or stripped.startswith(r"\]"):
            in_equation = False
            continue
        if in_equation:
            continue

        sec_match = LATEX_SECTION.search(stripped)
        if sec_match:
            if current_text:
                sections.append({"type": "text", "content": "\n".join(current_text)})
                current_text = []
            sections.append({"type": "section", "content": sec_match.group(1)})
            continue

        if stripped.startswith(r"\begin{figure}") or stripped.startswith(r"\begin{table}"):
            if current_text:
                sections.append({"type": "text", "content": "\n".join(current_text)})
                current_text = []
            sections.append({"type": "placeholder", "content": "[图表占位]"})
            continue

        current_text.append(stripped)

    if current_text:
        sections.append({"type": "text", "content": "\n".join(current_text)})

    return sections


def _latex_to_plain(text: str) -> str:
    """简单 LaTeX → 纯文本转换。"""
    text = LATEX_CMD.sub(r"\1", text)
    text = LATEX_LABEL.sub("", text)
    text = LATEX_REF.sub(r"[\1]", text)
    text = LATEX_INLINE_MATH.sub(r"\1", text)
    text = text.replace("~", " ")
    text = text.replace("\\%", "%")
    text = text.replace("\\&", "&")
    text = text.replace("\\#", "#")
    return text


def tex_to_docx(tex_path: str, output: str | None = None) -> str:
    """把 .tex 转为 .docx。"""
    if not HAS_DOCX:
        print("[FAIL] 需要 python-docx: pip install python-docx", file=sys.stderr)
        sys.exit(1)

    tex = Path(tex_path).read_text(encoding="utf-8")
    tex = _strip_comments(tex)
    title = _extract_title(tex)
    sections = _extract_content(tex)

    doc = Document()

    style = doc.styles["Normal"]
    style.font.size = Pt(12)

    if title:
        doc.add_heading(title, level=0)

    for sec in sections:
        content = _latex_to_plain(sec["content"])
        if sec["type"] == "section":
            doc.add_heading(content, level=1)
        elif sec["type"] == "text" and content.strip():
            doc.add_paragraph(content)
        elif sec["type"] == "placeholder":
            doc.add_paragraph("[图表占位]", style="Intense Quote")

    out_path = output or str(Path(tex_path).with_suffix(".docx"))
    doc.save(out_path)
    return out_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="LaTeX → DOCX 转换")
    parser.add_argument("input", help="输入 .tex 文件")
    parser.add_argument("-o", "--output", help="输出 .docx 路径")
    parser.add_argument("--ai-scan", action="store_true", help="扫描 AI 痕迹")
    args = parser.parse_args(argv)

    if not Path(args.input).exists():
        print(f"[FAIL] 文件不存在: {args.input}", file=sys.stderr)
        return 1

    if args.ai_scan:
        docx_path = args.output or str(Path(args.input).with_suffix(".docx"))
        if not Path(docx_path).exists():
            print(f"[FAIL] DOCX 不存在: {docx_path}（需先转换）", file=sys.stderr)
            return 1
        issues = scan_ai_traces(docx_path)
        if issues:
            print(f"[WARN] 发现 {len(issues)} 处 AI 痕迹:")
            for issue in issues:
                print(f"  段落 {issue['paragraph']}: {issue['matched']}")
        else:
            print("[OK] 未发现 AI 痕迹")
        return 1 if issues else 0

    out = tex_to_docx(args.input, args.output)
    print(f"[OK] DOCX 已生成: {out}")

    postprocess(out, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
