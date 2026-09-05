#!/usr/bin/env python3
"""LaTeX 论文 → DOCX 转换工具（零第三方依赖）。

MathModelSkills 项目工具，供 final-validator 在 `runtime.deliver_docx != never` 时产出 Word 交付件。

设计原则（与项目「单一主线」铁则一致）：
- `paper/main.tex`（LaTeX）是唯一真值主线；`paper/main.docx` 是**交付分支**，仅作竞赛/评审提交件，不改写论文数值。
- 优先用 pandoc（若主机已装）做高质量转换（公式/图表/表格全保留）。
- 无 pandoc 时，用纯标准库生成「文本降级版」DOCX（OOXML zip 包装），公式/图表以占位说明标注，保证总有可打开的 Word 文件。

用法：
    python core/tools/tex_to_docx.py paper/main.tex paper/main.docx
    python core/tools/tex_to_docx.py paper/main.tex paper/main.docx --force-pandoc   # 必须用 pandoc，无则报错
    python core/tools/tex_to_docx.py paper/main.tex paper/main.docx --no-pandoc     # 跳过 pandoc，纯文本降级版
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


# ---------------------------------------------------------------------------
# OOXML（DOCX 本质是 zip 包）最小骨架
# ---------------------------------------------------------------------------

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

_DOC_HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>"""

_DOC_FOOTER = """    <w:sectPr/>
  </w:body>
</w:document>"""

_STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:after="200"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="36"/><w:szCs w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="30"/><w:szCs w:val="30"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:pPr><w:spacing w:before="200" w:after="80"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Equation">
    <w:name w:val="Equation"/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="120"/></w:pPr>
    <w:rPr><w:i/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Caption">
    <w:name w:val="Caption"/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:before="60" w:after="120"/></w:pPr>
    <w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/><w:color w:val="666666"/></w:rPr>
  </w:style>
</w:styles>"""


def _xml_escape(text: str) -> str:
    """转义 XML 特殊字符，保证 DOCX 可被 Word 打开。"""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


def _styled_paragraph(text: str, style: str | None = None) -> str:
    ppr = f"<w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>" if style else ""
    return (f'    <w:p>{ppr}<w:r><w:t xml:space="preserve">'
            + _xml_escape(text) + "</w:t></w:r></w:p>")


def _paragraph(text: str) -> str:
    return _styled_paragraph(text)


# -- 三线表 OOXML 生成 --

_THREE_LINE_BORDER = (
    '<w:tblBorders>'
    '  <w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
    '  <w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
    '  <w:left w:val="none" w:sz="0" w:space="0" w:color="000000"/>'
    '  <w:right w:val="none" w:sz="0" w:space="0" w:color="000000"/>'
    '  <w:insideH w:val="none" w:sz="0" w:space="0" w:color="000000"/>'
    '  <w:insideV w:val="none" w:sz="0" w:space="0" w:color="000000"/>'
    '</w:tblBorders>'
)

_HEADER_ROW_BORDER = (
    '<w:tblBorders>'
    '  <w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
    '  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
    '  <w:left w:val="none" w:sz="0" w:space="0" w:color="000000"/>'
    '  <w:right w:val="none" w:sz="0" w:space="0" w:color="000000"/>'
    '</w:tblBorders>'
)


def _table_cell(text: str, bold: bool = False) -> str:
    rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return (f'<w:tc><w:tcPr/></w:tcPr>'
            f'<w:p><w:r>{rpr}<w:t xml:space="preserve">'
            f'{_xml_escape(text)}</w:t></w:r></w:p></w:tc>')


def _table_row(cells: list[str], is_header: bool = False) -> str:
    tcs = "".join(_table_cell(c, bold=is_header) for c in cells)
    border = _HEADER_ROW_BORDER if is_header else ""
    ppr = f"<w:tblPr>{border}</w:tblPr>" if is_header else ""
    return f"<w:tr>{ppr}{tcs}</w:tr>"


def build_three_line_table(headers: list[str], rows: list[list[str]],
                           caption: str = "") -> str:
    """生成三线表 OOXML（1.5pt 顶/底 + 0.5pt 表头底线）。"""
    all_rows_xml = [_table_row(headers, is_header=True)]
    for row in rows:
        padded = row + [""] * (len(headers) - len(row))
        all_rows_xml.append(_table_row(padded[:len(headers)]))
    tbl_content = "".join(all_rows_xml)
    tbl = (f'<w:tbl><w:tblPr>{_THREE_LINE_BORDER}'
           f'<w:jc w:val="center"/></w:tblPr>'
           f'{tbl_content}</w:tbl>')
    parts = []
    if caption:
        parts.append(_styled_paragraph(caption, "Caption"))
    parts.append(tbl)
    parts.append(_styled_paragraph(""))
    return "\n".join(parts)


def build_equation_placeholder(label: str, eq_num: int, content_hint: str = "") -> str:
    """居中编号公式占位（降级路径）。"""
    hint = f" — {content_hint}" if content_hint else ""
    text = f"[公式 ({eq_num}){hint}]"
    ppr = '<w:pPr><w:pStyle w:val="Equation"/></w:pPr>'
    return (f'    <w:p>{ppr}<w:r><w:t xml:space="preserve">'
            f'{_xml_escape(text)}</w:t></w:r></w:p>')


def build_figure_placeholder(caption: str = "") -> str:
    """图片占位（降级路径）。"""
    parts = [_styled_paragraph("[图片占位 — 请从 PDF 版获取原图]", "Caption")]
    if caption:
        parts.append(_styled_paragraph(caption, "Caption"))
    return "\n".join(parts)

# ---------------------------------------------------------------------------
# LaTeX → 纯文本段落（降级路径用，保守提取，不追求完美排版）
# ---------------------------------------------------------------------------

def _strip_preamble(tex: str) -> str:
    m = re.search(r"\\begin\{document\}", tex)
    if not m:
        return tex
    body = tex[m.end():]
    body = re.sub(r"\\end\{document\}.*$", "", body, flags=re.DOTALL)
    return body

def _extract_title(tex: str) -> str:
    m = re.search(r"\\title\s*\{([^}]*)\}", tex, flags=re.DOTALL)
    return m.group(1).strip() if m else ""


def _clean_inline_latex(text: str) -> str:
    """清理行内 LaTeX 命令，保留可读文本。"""
    text = re.sub(r"\\cite\s*\{[^}]*\}", "[参考文献]", text)
    text = re.sub(r"\\ref\s*\{[^}]*\}", "(见引用)", text)
    text = re.sub(r"\\label\s*\{[^}]*\}", "", text)
    text = re.sub(r"\\textbf\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\emph\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\textit\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\mathbf\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+\*?", "", text)
    text = text.replace("{", "").replace("}", "")
    return text.strip()


def _parse_tabular(tabular_body: str) -> tuple[list[str], list[list[str]]]:
    """从 tabular 环境体中提取表头和数据行。"""
    lines = tabular_body.strip().splitlines()
    rows: list[list[str]] = []
    buf = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith((r"\hline", r"\toprule", r"\midrule",
                                r"\bottomrule", r"\caption")):
            continue
        has_row_end = stripped.endswith(r"\\")
        if has_row_end:
            stripped = stripped[:-2].strip()
        buf += (" " if buf else "") + stripped
        if has_row_end:
            cleaned = _clean_inline_latex(buf)
            cells = [c.strip() for c in cleaned.split("&")]
            if cells and any(cells):
                rows.append(cells)
            buf = ""
    if buf.strip():
        cleaned = _clean_inline_latex(buf)
        cells = [c.strip() for c in cleaned.split("&")]
        if cells and any(cells):
            rows.append(cells)

    if len(rows) >= 2:
        return rows[0], rows[1:]
    if len(rows) == 1:
        return rows[0], []
    return ["列1", "列2"], [["", ""]]


def _latex_to_blocks(tex: str) -> list[dict]:
    """将 LaTeX 正文解析为结构化 block 列表。

    block 类型：
      {"type": "heading", "level": 1|2, "text": str}
      {"type": "paragraph", "text": str}
      {"type": "table", "headers": [...], "rows": [[...]], "caption": str}
      {"type": "equation", "label": str, "hint": str}
      {"type": "figure", "caption": str}
    """
    body = _strip_preamble(tex)
    body = re.sub(r"(?<!\\)%.*$", "", body, flags=re.MULTILINE)

    blocks: list[dict] = []
    eq_counter = 0

    pos = 0
    while pos < len(body):
        # 章节标题
        m_sec = re.match(
            r"\\(section|subsection|subsubsection)\*?\{([^}]*)\}",
            body[pos:])
        if m_sec:
            cmd = m_sec.group(1)
            level = {"section": 1, "subsection": 2, "subsubsection": 2}[cmd]
            blocks.append({"type": "heading", "level": level,
                           "text": m_sec.group(2).strip()})
            pos += m_sec.end()
            continue

        # table 环境（含 tabular 内容）
        m_tbl = re.match(
            r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}",
            body[pos:], re.DOTALL)
        if m_tbl:
            tbl_body = m_tbl.group(1)
            cap_m = re.search(r"\\caption\s*\{([^}]*)\}", tbl_body)
            caption = f"表 {_clean_inline_latex(cap_m.group(1))}" if cap_m else ""
            tab_m = re.search(
                r"\\begin\{tabular\}[^{]*\{[^}]*\}(.*?)\\end\{tabular\}",
                tbl_body, re.DOTALL)
            if tab_m:
                headers, rows = _parse_tabular(tab_m.group(1))
                blocks.append({"type": "table", "headers": headers,
                               "rows": rows, "caption": caption})
            else:
                blocks.append({"type": "paragraph",
                               "text": caption or "[表]"})
            pos += m_tbl.end()
            continue

        # 独立 tabular（不在 table 浮动体内）
        m_tabular = re.match(
            r"\\begin\{tabular\}[^{]*\{[^}]*\}(.*?)\\end\{tabular\}",
            body[pos:], re.DOTALL)
        if m_tabular:
            headers, rows = _parse_tabular(m_tabular.group(1))
            blocks.append({"type": "table", "headers": headers,
                           "rows": rows, "caption": ""})
            pos += m_tabular.end()
            continue

        # equation 环境
        m_eq = re.match(
            r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}",
            body[pos:], re.DOTALL)
        if m_eq:
            eq_counter += 1
            eq_body = m_eq.group(1).strip()
            lbl_m = re.search(r"\\label\{([^}]*)\}", eq_body)
            label = lbl_m.group(1) if lbl_m else ""
            hint = _clean_inline_latex(
                re.sub(r"\\label\{[^}]*\}", "", eq_body))[:80]
            blocks.append({"type": "equation", "label": label,
                           "num": eq_counter, "hint": hint})
            pos += m_eq.end()
            continue

        # align 环境
        m_align = re.match(
            r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}",
            body[pos:], re.DOTALL)
        if m_align:
            eq_counter += 1
            blocks.append({"type": "equation", "label": "",
                           "num": eq_counter, "hint": "[公式组]"})
            pos += m_align.end()
            continue

        # figure 环境
        m_fig = re.match(
            r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}",
            body[pos:], re.DOTALL)
        if m_fig:
            fig_body = m_fig.group(1)
            cap_m = re.search(r"\\caption\s*\{([^}]*)\}", fig_body)
            caption = f"图 {_clean_inline_latex(cap_m.group(1))}" if cap_m else ""
            blocks.append({"type": "figure", "caption": caption})
            pos += m_fig.end()
            continue

        # 跳过其余环境
        m_env = re.match(r"\\begin\{([^}]*)\}", body[pos:])
        if m_env:
            env_name = m_env.group(1)
            end_pat = re.compile(r"\\end\{" + re.escape(env_name) + r"\}")
            m_end = end_pat.search(body, pos + m_env.end())
            if m_end:
                inner = body[pos + m_env.end():m_end.start()].strip()
                if inner:
                    cleaned = _clean_inline_latex(inner)
                    if cleaned:
                        blocks.append({"type": "paragraph", "text": cleaned})
                pos = m_end.end()
                continue
            pos += m_env.end()
            continue

        # 普通文本行
        nl = body.find("\n", pos)
        if nl == -1:
            line = body[pos:].strip()
            pos = len(body)
        else:
            line = body[pos:nl].strip()
            pos = nl + 1

        if not line:
            continue
        cleaned = _clean_inline_latex(line)
        if cleaned:
            blocks.append({"type": "paragraph", "text": cleaned})

    return blocks


def _blocks_to_ooxml(blocks: list[dict]) -> str:
    """将 block 列表转为 OOXML 片段。"""
    parts: list[str] = []
    for b in blocks:
        t = b["type"]
        if t == "heading":
            style = "Heading1" if b["level"] == 1 else "Heading2"
            parts.append(_styled_paragraph(b["text"], style))
        elif t == "paragraph":
            parts.append(_paragraph(b["text"]))
        elif t == "table":
            parts.append(build_three_line_table(
                b["headers"], b["rows"], b.get("caption", "")))
        elif t == "equation":
            parts.append(build_equation_placeholder(
                b.get("label", ""), b["num"], b.get("hint", "")))
        elif t == "figure":
            parts.append(build_figure_placeholder(b.get("caption", "")))
    return "\n".join(parts)


def _latex_to_paragraphs(tex: str) -> list[str]:
    """向后兼容：从 block 列表提取纯文本行。"""
    lines = []
    for b in _latex_to_blocks(tex):
        if b["type"] == "heading":
            lines.append(b["text"])
        elif b["type"] == "paragraph":
            lines.append(b["text"])
        elif b["type"] == "table":
            lines.append(b.get("caption", "[表]"))
        elif b["type"] == "equation":
            lines.append(f"[公式 ({b['num']})]")
        elif b["type"] == "figure":
            lines.append(b.get("caption", "[图]"))
    return lines


# ---------------------------------------------------------------------------
# 转换入口
# ---------------------------------------------------------------------------

def find_pandoc() -> bool:
    return shutil.which("pandoc") is not None

def convert_with_pandoc(src: str, dst: str) -> tuple[bool, str]:
    cmd = ["pandoc", src, "-o", dst]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        return False, "pandoc 不可用"
    except subprocess.TimeoutExpired:
        return False, "pandoc 转换超时（>120s）"
    if proc.returncode != 0:
        return False, (proc.stderr or "pandoc 返回非零退出码").strip()[:500]
    return Path(dst).exists(), "pandoc 转换成功"

def build_docx_text(tex: str, title: str, dst: str) -> bool:
    """用结构化 block 生成 DOCX（三线表 + 编号公式 + 标题样式）。"""
    blocks = _latex_to_blocks(tex)
    if not blocks:
        blocks = [{"type": "paragraph", "text": "（LaTeX 正文为空，无法提取内容）"}]
    body_xml = _blocks_to_ooxml(blocks)
    title_xml = _styled_paragraph(title, "Title") if title else ""
    document = _DOC_HEADER + "\n" + title_xml + "\n" + body_xml + "\n" + _DOC_FOOTER
    try:
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", _CONTENT_TYPES)
            z.writestr("_rels/.rels", _RELS)
            z.writestr("word/document.xml", document)
            z.writestr("word/styles.xml", _STYLES_XML)
    except OSError as e:
        print(f"[tex_to_docx] 写入失败: {e}", file=sys.stderr)
        return False
    return True


def post_process_docx(dst: str, verbose: bool = False, options: Optional[dict] = None) -> bool:
    """调用 docx_post_processor 修复 pandoc 生成的 DOCX 结构（可选依赖 python-docx）。"""
    from core.tools.docx_post_processor import insert_academic_structure
    return insert_academic_structure(Path(dst), verbose=verbose, options=options or {})


def main() -> int:
    ap = argparse.ArgumentParser(description="LaTeX 论文 → DOCX（优先 pandoc，无则结构化降级版）")
    ap.add_argument("src", help="LaTeX 源文件，如 paper/main.tex")
    ap.add_argument("dst", help="目标 DOCX，如 paper/main.docx")
    ap.add_argument("--force-pandoc", action="store_true",
                    help="必须使用 pandoc，无 pandoc 时报错退出")
    ap.add_argument("--no-pandoc", action="store_true",
                    help="跳过 pandoc，直接生成结构化降级版 DOCX")
    ap.add_argument("--institution", help="机构名（pandoc 路径：居中插入标题前；需 python-docx）")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_file():
        print(f"[tex_to_docx] 源文件不存在: {args.src}", file=sys.stderr)
        return 1
    tex = src.read_text(encoding="utf-8", errors="replace")

    dst = Path(args.dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    used_pandoc = False
    if not args.no_pandoc and find_pandoc():
        ok, msg = convert_with_pandoc(str(src), str(dst))
        if ok:
            used_pandoc = True
            print(f"[tex_to_docx] {msg} -> {args.dst}")
            # pandoc 成功后，可选后处理（修复标题居中/分页/表格宽度）
            opts = {}
            if args.institution:
                opts["institution"] = args.institution
            if opts:
                post_process_docx(str(dst), verbose=args.verbose, options=opts)
            return 0
        if args.force_pandoc:
            print(f"[tex_to_docx] 转换失败：{msg}", file=sys.stderr)
            return 1
        print(f"[tex_to_docx] {msg}，回退结构化降级版", file=sys.stderr)

    title = _extract_title(tex)
    if not build_docx_text(tex, title, str(dst)):
        return 1
    mode = "结构化降级版（三线表+编号公式+标题样式，无 pandoc）" if not used_pandoc else ""
    print(f"[tex_to_docx] 生成 {args.dst}（{mode}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())