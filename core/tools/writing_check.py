#!/usr/bin/env python3
"""writing_check.py — 论文文本质量硬门禁扫描工具

移植并增强自 MathModelAgent-main skills/6verity/scripts/writing_check.sh。
在 gate.py 的 guardrails-checker 之后执行，提供独立的硬错误/警告扫描。

用法:
    python core/tools/writing_check.py <项目路径> [--main FILE] [--sections-dir DIR]
                                      [--figures-dir DIR] [--all-results FILE]

退出码: 0=PASS, 1=FAIL（存在 blocking 级问题）

检查项:
    1. 入口文件存在性（main.tex / main.typ）
    2. include 文件存在性 + 顺序 + 去重
    3. 章节标题缺失检测
    4. 占位符残留（PLACEHOLDER/TODO/TBD/XXX/待补充/待续写/示例数据/待完善）
    5. 内部文件名泄露（RESULTS_REPORT/md/CLAUDE.md/figures/*.json/_tmp/）
    6. 图片引用存在性
    7. 未引用图片检测
    8. Figure caption 检测 + 长度检查
    9. 引用标记检测（\\cite{} 但无引用/无 \\cite{}）
   10. 章节长度过短检测（<800 字符）
   11. 列表过多检测（≥3 个 itemize/enumerate 触发 WARN）
   12. 图片多但文字少检测（≥2 图 + <1000 字符触发 WARN）
   13. 数值一致性检测（all_results.json 关键数值是否在正文出现）
   14. 重复章节标题检测
"""  # noqa: docstring escape

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

PLACEHOLDER_RE = re.compile(
    r"PLACEHOLDER|TODO|TBD|XXX|待补充|待续写|这里补|示例数据|待完善"
)

DEFAULT_INTERNAL_TERMS = [
    "RESULTS_REPORT",
    "ANALYSIS_MODELING_REPORT\\.md",
    "PROBLEM_ANALYSIS\\.md",
    "CODE_DELIVERABLES\\.md",
    "MODEL_SPEC\\.md",
    "PAPER_SPEC\\.md",
    "CLAUDE\\.md",
    "AGENT[SM]?\\.md",
    "figures/.*\\.json",
    "_tmp/",
    "STATE\\.md",
]

SECTION_PATTERNS = {
    "latex": {
        "section": r"\\section\{([^}]*)\}",
        "subsection": r"\\subsection\{([^}]*)\}",
        "include": r"\\(?:input|include)\{([^}]+)\}",
        "image": r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}",
        "figure_env": r"\\begin\{figure\}.*?\\end\{figure\}",
        "caption": r"\\caption\{([^}]*)\}",
        "list_begin": r"\\begin\{(?:itemize|enumerate)\}",
        "citation": r"\\cite\w*\{[^}]+\}",
    }
}

MIN_SECTION_LENGTH = 800  # 章节最少字符数
MIN_FIGURE_PROSE = 1000   # 多图章节最少正文字符数
MAX_LISTS_PER_SECTION = 3  # 每节列表数上限
MAX_CAPTION_LENGTH = 200  # caption 最大字符数


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

class CheckResult:
    """扫描结果容器"""
    def __init__(self):
        self.errors: list[dict] = []
        self.warnings: list[dict] = []
        self.infos: list[dict] = []

    @property
    def failed(self) -> bool:
        return len(self.errors) > 0

    def error(self, check: str, location: str, detail: str):
        self.errors.append({"check": check, "location": location, "detail": detail})

    def warn(self, check: str, location: str, detail: str):
        self.warnings.append({"check": check, "location": location, "detail": detail})

    def info(self, check: str, location: str, detail: str):
        self.infos.append({"check": check, "location": location, "detail": detail})

    def summary(self) -> str:
        lines = [
            f"=== writing_check 扫描结果 ===",
            f"  硬错误: {len(self.errors)}",
            f"  警告:   {len(self.warnings)}",
            f"  信息:   {len(self.infos)}",
        ]
        for e in self.errors:
            lines.append(f"[FAIL] {e['check']} | {e['location']}: {e['detail']}")
        for w in self.warnings:
            lines.append(f"[WARN] {w['check']} | {w['location']}: {w['detail']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 检查函数
# ---------------------------------------------------------------------------

def check_entry_exists(paper_dir: Path, result: CheckResult):
    """Check 1: 入口文件存在性"""
    main_tex = paper_dir / "main.tex"
    main_typ = paper_dir / "main.typ"
    if main_tex.exists():
        result.info("entry_check", str(main_tex), "LaTeX 入口文件存在")
        return "latex", main_tex
    elif main_typ.exists():
        result.info("entry_check", str(main_typ), "Typst 入口文件存在")
        return "typst", main_typ
    else:
        result.error("entry_check", str(paper_dir), "缺少入口文件 main.tex / main.typ")
        return None, None


def find_sections(paper_dir: Path, engine: str, main_file: Path) -> list[Path]:
    """查找所有论文章节文件"""
    sections = []
    if engine == "latex":
        content = main_file.read_text(encoding="utf-8", errors="replace")
        includes = re.findall(r"\\(?:input|include)\{([^}]+)\}", content)
        for inc in includes:
            p = paper_dir / inc
            if not p.exists():
                p = paper_dir / f"{inc}.tex"
            if p.exists():
                sections.append(p)
    else:
        if (paper_dir / "sections").exists():
            sections = sorted((paper_dir / "sections").glob("*.typ"))
    # 也搜索 paper/*.tex 和 paper/sections/*.tex
    if engine == "latex" and not sections:
        sections = sorted(paper_dir.glob("**/*.tex"))
        sections = [s for s in sections if s != main_file and "sections" in str(s)]
    return sections


def check_includes(main_file: Path, sections: list[Path], result: CheckResult):
    """Check 2: include 文件存在性 + 顺序 + 去重"""
    if not sections:
        result.warn("include_check", str(main_file), "未发现章节文件")
        return
    names = [s.name for s in sections]
    seen = set()
    for name in names:
        if name in seen:
            result.error("include_check", str(main_file), f"重复 include: {name}")
        seen.add(name)
    # 检查编号顺序
    numbers = []
    for name in names:
        m = re.match(r"^(\d+)[_-]", name)
        if m:
            numbers.append(int(m.group(1)))
    if numbers and numbers != sorted(numbers):
        result.error("include_check", str(main_file), f"章节顺序非升序: {numbers}")
    result.info("include_check", str(main_file), f"共 {len(sections)} 个章节文件")


def check_sections(content: dict[Path, str], engine: str, result: CheckResult):
    """Check 3: 章节标题缺失 + Check 10: 章节长度"""
    for path, text in content.items():
        rel = path.name
        if engine == "latex":
            sections = re.findall(r"\\section\{([^}]*)\}", text)
            if not sections:
                result.error("heading_check", rel, "章节缺少 \\section{} 标题")
        else:
            sections = re.findall(r"(?m)^=\s+.+", text)
            if not sections:
                result.error("heading_check", rel, "章节缺少 Typst 标题 (= Title)")
        # 长度检查
        if len(text) < MIN_SECTION_LENGTH and not path.name.startswith(("A_", "abstract", "appendix")):
            result.warn("length_check", rel, f"章节过短 ({len(text)} 字符 < {MIN_SECTION_LENGTH})")


def check_placeholders(content: dict[Path, str], result: CheckResult):
    """Check 4: 占位符残留"""
    for path, text in content.items():
        if PLACEHOLDER_RE.search(text):
            matches = PLACEHOLDER_RE.findall(text)
            result.error("placeholder_check", path.name,
                        f"发现占位符残留: {', '.join(set(matches))}")


def check_internal_leaks(content: dict[Path, str], result: CheckResult):
    """Check 5: 内部文件名泄露"""
    internal_re = re.compile("|".join(DEFAULT_INTERNAL_TERMS))
    for path, text in content.items():
        if internal_re.search(text):
            matches = internal_re.findall(text)
            is_appendix = path.name.startswith("A_") or "appendix" in path.name.lower()
            level = "warn" if is_appendix else "error"
            msg = f"泄露内部文件名: {', '.join(set(matches))}"
            if level == "error":
                result.error("internal_leak_check", path.name, msg)
            else:
                result.warn("internal_leak_check", path.name, msg)


def check_images(content: dict[Path, str], figures_dir: Path | None, result: CheckResult):
    """Check 6: 图片引用存在性 + Check 7: 未引用图片 + Check 8: caption"""
    image_re = re.compile(r'\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}')
    figure_env_re = re.compile(r'\\begin\{figure\}.*?\\end\{figure\}', re.S)
    caption_re = re.compile(r'\\caption\{([^}]*)\}')

    for path, text in content.items():
        # 图片引用存在性
        for ref in image_re.findall(text):
            target = path.parent / ref
            if not target.exists() and figures_dir:
                target = figures_dir / ref
            if not target.exists():
                result.error("image_ref_check", path.name, f"引用的图片不存在: {ref}")
        # Figure caption 检查
        for block in figure_env_re.findall(text):
            cap_match = caption_re.search(block)
            if not cap_match:
                result.error("caption_check", path.name, "LaTeX figure 缺少 \\caption{}")
            else:
                cap = cap_match.group(1).strip()
                if len(cap) > MAX_CAPTION_LENGTH:
                    result.warn("caption_check", path.name, f"caption 过长 ({len(cap)} 字符)")
                if len(cap) < 4:
                    result.warn("caption_check", path.name, f"caption 过短 (<4 字符)")

    # 未引用图片检测
    if figures_dir and figures_dir.exists():
        all_images = set()
        for fig in figures_dir.iterdir():
            if fig.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".svg"):
                all_images.add(fig.name)
        all_text = "\n".join(content.values())
        for img in all_images:
            if img not in all_text:
                result.warn("unused_figure_check", str(figures_dir), f"图片未在正文引用: {img}")


def check_citations(content: dict[Path, str], references_file: Path | None, result: CheckResult):
    """Check 9: 引用标记检测"""
    citation_re = re.compile(r"\\cite\w*\{[^}]+\}")
    has_citation = False
    for text in content.values():
        if citation_re.search(text):
            has_citation = True
            break
    if references_file and references_file.exists():
        if not has_citation:
            result.warn("citation_check", references_file.name, "存在参考文献但正文无 \\cite{} 引用")
        else:
            result.info("citation_check", references_file.name, "引用标记正常")


def check_lists(content: dict[Path, str], result: CheckResult):
    """Check 11: 列表过多检测"""
    for path, text in content.items():
        list_count = len(re.findall(r"\\begin\{(?:itemize|enumerate)\}", text))
        if list_count >= MAX_LISTS_PER_SECTION:
            result.warn("list_check", path.name,
                       f"列表过多 {list_count} 个（建议改为段落式论述）")


def check_figure_prose_ratio(content: dict[Path, str], result: CheckResult):
    """Check 12: 多图少字检测"""
    figure_env_re = re.compile(r'\\begin\{figure\}.*?\\end\{figure\}', re.S)
    for path, text in content.items():
        fig_count = len(figure_env_re.findall(text))
        text_no_figs = figure_env_re.sub("", text)
        if fig_count >= 2 and len(text_no_figs.strip()) < MIN_FIGURE_PROSE:
            result.warn("figure_prose_check", path.name,
                       f"多图（{fig_count}）但正文不足（{len(text_no_figs.strip())} 字符 < {MIN_FIGURE_PROSE}）")


def check_numeric_consistency(content: dict[Path, str], all_results_file: Path | None, result: CheckResult):
    """Check 13: 数值一致性（all_results.json vs 正文）"""
    if not all_results_file or not all_results_file.exists():
        result.info("numeric_check", "", "无 all_results.json，跳过数值一致性检查")
        return

    try:
        data = json.loads(all_results_file.read_text(encoding="utf-8"))
    except Exception as exc:
        result.warn("numeric_check", str(all_results_file), f"JSON 解析失败: {exc}")
        return

    nums = []

    def walk(value):
        if isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
        elif isinstance(value, (int, float)):
            nums.append(value)

    walk(data)

    # 只检查 |num| >= 1 的数值（量级的关键数值）
    key_nums = []
    for num in nums:
        if abs(num) >= 1:
            key_nums.append(str(round(num, 4)).rstrip("0").rstrip("."))

    paper_text = "\n".join(content.values())
    found = sum(1 for n in key_nums[:30] if n and n in paper_text)
    if key_nums and found == 0:
        result.warn("numeric_check", str(all_results_file),
                   "all_results.json 的关键数值在正文中未出现，数值追溯可能不完整")
    else:
        result.info("numeric_check", str(all_results_file),
                   f"数值一致性检查通过（{found}/{min(len(key_nums), 30)} 个关键数值匹配）")


def check_duplicate_titles(content: dict[Path, str], engine: str, result: CheckResult):
    """Check 14: 重复章节标题"""
    all_titles = []
    for path, text in content.items():
        if engine == "latex":
            titles = re.findall(r"\\section\{([^}]*)\}", text)
        else:
            titles = [m.lstrip("= ").strip() for m in re.findall(r"(?m)^=\s+.+", text)]
        for t in titles:
            all_titles.append(t)

    seen = set()
    for t in all_titles:
        if t in seen:
            result.error("duplicate_title_check", "", f"重复章节标题: {t}")
        seen.add(t)


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def run_checks(project_path: Path, main_file: Path | None = None,
               sections_dir: Path | None = None,
               figures_dir: Path | None = None,
               all_results_file: Path | None = None) -> CheckResult:
    result = CheckResult()

    paper_dir = project_path / "paper"
    if not paper_dir.exists():
        result.error("structure_check", str(project_path), "缺少 paper/ 目录")
        return result

    # Check 1: 入口文件
    engine, main = check_entry_exists(paper_dir, result)
    if main_file:
        main = main_file
        engine = "latex" if main.suffix == ".tex" else "typst"
    if not main:
        return result

    # 查找章节
    sections = find_sections(paper_dir, engine, main)
    if sections_dir:
        sections = list(sections_dir.glob("*.tex")) if engine == "latex" else list(sections_dir.glob("*.typ"))

    # 读取全部内容
    all_files = {main: main.read_text(encoding="utf-8", errors="replace")}
    for s in sections:
        if s != main and s.exists():
            all_files[s] = s.read_text(encoding="utf-8", errors="replace")

    # Check 2: includes
    check_includes(main, sections, result)

    # Check 3 & 10: 章节标题 + 长度
    check_sections(all_files, engine, result)

    # Check 4: 占位符
    check_placeholders(all_files, result)

    # Check 5: 内部文件名泄露
    check_internal_leaks(all_files, result)

    # 定位 figures_dir
    if not figures_dir:
        for candidate in [project_path / "figures", project_path / "paper" / "figures"]:
            if candidate.exists():
                figures_dir = candidate
                break

    # Check 6 & 7 & 8: 图片引用 / 未引用 / caption
    check_images(all_files, figures_dir, result)

    # Check 9: 引用标记
    refs_file = paper_dir / "references.bib"
    if not refs_file.exists():
        refs_file = paper_dir / "references.tex"
    check_citations(all_files, refs_file, result)

    # Check 11: 列表过多
    check_lists(all_files, result)

    # Check 12: 多图少字
    check_figure_prose_ratio(all_files, result)

    # Check 13: 数值一致性
    if not all_results_file:
        candidate = project_path / "figures" / "all_results.json"
        if candidate.exists():
            all_results_file = candidate
    check_numeric_consistency(all_files, all_results_file, result)

    # Check 14: 重复标题
    check_duplicate_titles(all_files, engine, result)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="MathModelSkills writing_check — 论文文本质量硬门禁扫描"
    )
    parser.add_argument("project", help="项目根目录路径")
    parser.add_argument("--main", help="论文入口文件路径（自动检测为辅）")
    parser.add_argument("--sections-dir", help="章节文件目录")
    parser.add_argument("--figures-dir", help="图片目录")
    parser.add_argument("--all-results", help="all_results.json 路径")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    args = parser.parse_args()

    project_path = Path(args.project).resolve()
    if not project_path.is_dir():
        print(f"ERROR: 项目目录不存在: {project_path}", file=sys.stderr)
        sys.exit(1)

    result = run_checks(
        project_path=project_path,
        main_file=Path(args.main) if args.main else None,
        sections_dir=Path(args.sections_dir) if args.sections_dir else None,
        figures_dir=Path(args.figures_dir) if args.figures_dir else None,
        all_results_file=Path(args.all_results) if args.all_results else None,
    )

    if args.json:
        output = {
            "status": "FAIL" if result.failed else "PASS",
            "errors": result.errors,
            "warnings": result.warnings,
            "infos": result.infos,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(result.summary())
        print(f"\n{'FAIL: 存在 blocking 级问题' if result.failed else 'PASS: 文本质量门禁通过'}")

    sys.exit(1 if result.failed else 0)


if __name__ == "__main__":
    main()
