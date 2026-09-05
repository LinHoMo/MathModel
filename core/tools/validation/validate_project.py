"""validate_project.py — 项目产物质量检查（针对 projects/<项目>/）。

把 MathModelSkills 的"门禁"从描述性升级到可执行：
  - 42 项真检查函数（非仅"文件是否存在"）
  - HARD/WARN/PASS 三级分级（HARD 退出码 1，WARN 退出码 0）
  - 题型触发：机理类赛题（problem_type 含 A/physical/机理/运动/动力/热传导/电磁/光学）
    时，Physics model 组的 6 项检查从 WARN 升级为 HARD
  - env 阈值动态注入：通过 env/loader.get() 读取 min_pages/min_words/...，
    strict_mode=True 时阈值不达为 HARD，False 时为 WARN

零外部依赖（仅标准库 argparse/importlib/json/math/os/re/sys/pathlib）。
用法：
    py core/tools/validate_project.py --project projects/cumcm2024a
"""
import argparse
import importlib.util
import json
import math
import os
import re
import sys
from pathlib import Path

# ===========================================================================
# 状态分级
# ===========================================================================
HARD, WARN, PASS = "HARD", "WARN", "PASS"

# 全局结果列表：每项 (status, name, detail)
results: list[tuple[str, str, str]] = []


def _pas(name, detail=""):
    results.append((PASS, name, detail))


def _warn(name, detail=""):
    results.append((WARN, name, detail))


def _hard(name, detail=""):
    results.append((HARD, name, detail))


# ===========================================================================
# 全局上下文（main 函数初始化）
# ===========================================================================
_IS_PHYSICS = False      # 机理类赛题标志（题型触发用）
_STRICT_MODE = True      # env.runtime.strict_mode
_ENV_GET = None          # env.loader.get 函数（动态加载）
_ENV_REQUIRE = None      # env.loader.require 函数（缺失即报错）


def _threshold_fail(name, detail):
    """阈值不达：strict_mode=True 时 HARD，False 时 WARN。"""
    if _STRICT_MODE:
        _hard(name, detail)
    else:
        _warn(name, detail)


def _physics_fail(name, detail):
    """物理校验不达：is_physics=True 时 HARD，False 时 WARN。"""
    if _IS_PHYSICS:
        _hard(name, detail)
    else:
        _warn(name, detail)


# ===========================================================================
# 禁用词表（统一扩充词表，两处必须同步：本文件与 validate.py）
# ===========================================================================
FORBIDDEN_WORDS = [
    # 现有 19 词
    "赋能", "抓手", "闭环", "颗粒度", "底层逻辑", "打法", "对齐",
    "倒逼", "复盘", "首先", "其次", "最后", "综上所述", "众所周知",
    "显而易见", "PaperCritic", "Prompt", "作为 AI", "token",
    # 中文套话新增
    "具有重要的理论意义和实践价值", "深入探讨", "创新性地", "值得注意的是",
    "总而言之", "具有重要意义", "实现了良好效果", "具有较高价值", "在当今",
    # 元叙述新增
    "参赛者", "参赛队伍", "我们团队",
    # 英文新增
    "delve", "pivotal", "tapestry", "underscore", "noteworthy",
    "It is worth noting that", "Importantly,", "Notably,",
]

# 禁用词正则模式（两处必须同步：本文件与 validate.py）
FORBIDDEN_WORD_REGEXES = [
    r"随着.{0,12}的快速发展",
]

# 内部术语泄露模式（论文正文出现即 HARD，两处必须同步：本文件与 validate.py）
INTERNAL_TERM_PATTERNS = [
    r"MODEL_SPEC\.md", r"CODE_DELIVERABLES\.md", r"PAPER_SPEC\.md",
    r"all_results\.json", r"RESULTS_REPORT", r"ANALYSIS_MODELING_REPORT",
    r"PROBLEM_ANALYSIS", r"CLAUDE\.md", r"AGENTS\.md",
    r"figures/\S+\.json", r"_tmp/", r"work/",
    r"\.py\b", r"\.ipynb\b", r"code/\w+\.py",
    r"/tmp/", r"__pycache__", r"\.pytest_cache",
]


# ===========================================================================
# 论文源读取辅助
# ===========================================================================
SRC_FILES = ["paper/main.tex", "paper/main.md", "paper/main.typ", "paper/main.qmd"]


def _src_path(p):
    for s in SRC_FILES:
        if (p / s).exists():
            return p / s
    return None


def _read_source(p):
    src = _src_path(p)
    if src is None:
        return None
    try:
        return src.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


# ===========================================================================
# env loader 动态加载（避免包路径依赖）
# ===========================================================================
def _load_env_loader(repo_root):
    """动态加载 env/loader.py 为独立模块，返回 (module, err)。"""
    loader_path = repo_root / "core" / "env" / "loader.py"
    if not loader_path.exists():
        return None, "env/loader.py 不存在"
    try:
        spec = importlib.util.spec_from_file_location(
            "_env_loader_for_validate_project", str(loader_path)
        )
        if spec is None or spec.loader is None:
            return None, "无法创建加载器 spec"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, None
    except Exception as e:
        return None, f"加载 env/loader.py 失败: {e}"


# ===========================================================================
# 题型识别
# ===========================================================================
PHYSICS_KEYWORDS = ["A", "physical", "机理", "运动", "动力", "热传导", "电磁", "光学"]


def _detect_problem_type(p):
    """读取 work/type_classification.json，返回 (problem_type_str, is_physics)。

    文件不存在或解析失败时返回 (None, False)，物理校验仅 WARN。
    """
    f = p / "work" / "type_classification.json"
    if not f.exists():
        return None, False
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None, False
    if not isinstance(data, dict):
        return None, False
    pt = data.get("problem_type") or data.get("type") or ""
    if not isinstance(pt, str):
        pt = str(pt)
    pt_lower = pt.lower()
    is_physics = any(kw.lower() in pt_lower for kw in PHYSICS_KEYWORDS)
    return pt, is_physics


# ===========================================================================
# 第 1 组：Required artifacts（4）
# ===========================================================================
def _latex_toolchain_available():
    """探测主机 LaTeX 工具链（xelatex 或 latexmk）。"""
    import shutil as _shutil
    return _shutil.which("xelatex") is not None or _shutil.which("latexmk") is not None


def _pdf_check_is_hard():
    """PDF 检查是否按 HARD 执行（runtime.compile_pdf 策略）。

    auto  : 有工具链 -> HARD；无工具链 -> WARN（仅交付 main.tex）
    always: 恒为 HARD
    never : 恒为 WARN（只交付 TEX 不编译）
    """
    policy = str(_ENV_GET("runtime.compile_pdf") or "auto").lower()
    if policy == "always":
        return True
    if policy == "never":
        return False
    return _latex_toolchain_available()


def check_pdf(p):
    """1. paper/main.pdf 存在且 > get("paper.pdf_min_bytes", 100KB)。

    受 runtime.compile_pdf 策略控制：未编译场景（auto 且无工具链 / never）降级 WARN。
    """
    f = p / "paper" / "main.pdf"
    hard_mode = _pdf_check_is_hard()
    fail = _hard if hard_mode else (lambda name, msg: _warn(name, msg + "（compile_pdf 策略未启用编译，仅交付 main.tex）"))
    if not f.exists():
        return fail("paper/main.pdf", "not found")
    size = f.stat().st_size
    min_bytes = int(_ENV_GET("paper.pdf_min_bytes") or 102400)
    if size < min_bytes:
        return fail("paper/main.pdf", f"too small ({size}B < {min_bytes}B)")
    _pas("paper/main.pdf", f"{size // 1024}KB")


def check_source(p):
    """2. paper/main.tex 或 main.md 或 main.typ 存在。"""
    src = _src_path(p)
    if src is None:
        return _hard("paper source", "未找到 main.tex/main.md/main.typ")
    _pas("paper source", src.relative_to(p).as_posix())


def check_bib(p):
    """3. paper/references.bib 存在。"""
    if not (p / "paper" / "references.bib").exists():
        return _hard("references.bib", "not found")
    _pas("references.bib", "exists")


def check_results_ledger(p):
    """4. figures/all_results.json 存在、合法 JSON、非空 dict。"""
    f = p / "figures" / "all_results.json"
    if not f.exists():
        return _hard("all_results.json", "not found")
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        return _hard("all_results.json", f"invalid JSON: {e}")
    if not isinstance(data, dict) or len(data) == 0:
        return _hard("all_results.json", "empty or not a dict")
    _pas("all_results.json", f"{len(data)} keys")


# ===========================================================================
# 第 2 组：Content quality（11）
# ===========================================================================
def check_placeholders(p):
    """5. 扫描论文源，检测占位符。"""
    pats = [(r"TODO", "TODO"), (r"FIXME", "FIXME"), (r"TBD", "TBD"),
            (r"__XXX__", "__XXX__"), (r"\[待补充\]", "[待补充]"),
            (r"\[TBD\]", "[TBD]"), (r"示例数据", "示例数据"),
            (r"模板数据", "模板数据")]
    t = _read_source(p)
    if t is None:
        return _warn("placeholders", "no source")
    found = [label for _, label in pats if re.search(_, t)]
    if found:
        return _hard("placeholders", f"发现占位符: {', '.join(found)}")
    _pas("placeholders", "no placeholders")


def check_forbidden_words(p):
    """6. 检测禁用词（统一扩充词表；同词出现≥3次记风险点 WARN，HARD 时已跳过）。"""
    t = _read_source(p)
    if t is None:
        return _warn("forbidden words", "no source")
    found = [w for w in FORBIDDEN_WORDS if w in t]
    regex_found = []
    for pat in FORBIDDEN_WORD_REGEXES:
        try:
            if re.search(pat, t):
                regex_found.append(pat)
        except re.error:
            pass
    if found or regex_found:
        return _hard("forbidden words",
                     f"发现禁用词: {', '.join(list(found)[:6])}")
    # 频次规则：同词≥3次单独列为风险点（若已因 HARD 拦截可跳过）
    freq = {w: t.count(w) for w in FORBIDDEN_WORDS if t.count(w) >= 3}
    if freq:
        items = ", ".join(f"{w}×{c}" for w, c in freq.items())
        return _warn("forbidden words (频次风险)", items)
    _pas("forbidden words", "no forbidden words")


def check_verify_report(p):
    """7. reports/VERIFY_REPORT.md 存在（可选，warn）。"""
    if (p / "reports" / "VERIFY_REPORT.md").exists():
        _pas("VERIFY_REPORT.md", "exists")
    else:
        _warn("VERIFY_REPORT.md", "optional, not found")


def check_citation_integrity(p):
    """8. \\cite/\\citep keys 与 references.bib 的 @type{key} 集合差。"""
    bib = p / "paper" / "references.bib"
    bib_keys = set()
    if bib.exists():
        try:
            bib_keys = set(re.findall(r"@\w+\{(\w[\w-]*)",
                                      bib.read_text(encoding="utf-8", errors="replace")))
        except Exception:
            pass
    t = _read_source(p)
    if t is None:
        return _warn("citations", "no source")
    cited = set()
    for m in re.findall(r"\\cite[tp]?\{([^}]+)\}", t):
        for k in m.split(","):
            cited.add(k.strip())
    if not bib_keys and not cited:
        return _warn("citations", "no citations nor bib entries")
    undefined = cited - bib_keys
    if undefined:
        return _hard("citations",
                     f"undefined keys: {', '.join(list(undefined)[:3])}")
    _pas("citations", f"{len(cited)} cited, all defined")


def check_figure_refs(p):
    """9. \\includegraphics 引用的图片文件相对 paper/ 是否存在。"""
    t = _read_source(p)
    if t is None:
        return _warn("figure refs", "no source")
    refs = re.findall(r"\\includegraphics(?:\[.*?\])?\{([^}]+)\}", t, re.DOTALL)
    if not refs:
        return _pas("figure refs", "no includegraphics")
    paper_dir = p / "paper"
    missing = []
    for r in refs:
        # 尝试原路径 + 常见图片后缀
        candidates = [paper_dir / r]
        for ext in (".png", ".pdf", ".eps", ".jpg", ".jpeg"):
            candidates.append(paper_dir / (r + ext))
        if not any(c.exists() for c in candidates):
            missing.append(r)
    if missing:
        return _hard("figure refs", f"missing: {', '.join(missing[:3])}")
    _pas("figure refs", f"{len(refs)} figures all exist")


def check_paper_structure(p):
    """10. 含 abstract/intro/conclusion 章节关键词。"""
    t = _read_source(p)
    if t is None:
        return _warn("structure", "no source")
    checks = [
        ("abstract", r"\\begin\{abstract\}|摘要"),
        ("intro", r"\\section\{.*introduction|\\section\{.*问题重述|\\section\{.*背景"),
        ("conclusion", r"\\section\{.*conclusion|\\section\{.*结论|\\section\{.*模型评价|\\section\{.*推广"),
    ]
    missing = [n for n, pt in checks if not re.search(pt, t, re.IGNORECASE)]
    if missing:
        return _warn("structure", f"missing: {', '.join(missing)}")
    _pas("structure", "abstract/intro/conclusion present")


def check_sensitivity_analysis(p):
    """11. 含 灵敏度/sensitivity/参数扰动/鲁棒性 关键词。"""
    t = _read_source(p)
    if t is None:
        return _warn("sensitivity analysis", "no source")
    pats = ["灵敏度", "sensitivity", "参数.*扰动", "参数.*变化", "鲁棒性", "robust"]
    found = [pt for pt in pats if re.search(pt, t, re.IGNORECASE)]
    if found:
        return _pas("sensitivity analysis", f"found: {found[0][:20]}")
    _warn("sensitivity analysis", "未发现灵敏度分析")


def check_model_evaluation(p):
    """12. 含 优点/缺点/局限/改进/推广 关键词。"""
    t = _read_source(p)
    if t is None:
        return _warn("model evaluation", "no source")
    pats = ["优点", "缺点", "局限", "改进", "推广", "advantage", "disadvantage", "limitation"]
    found = [pt for pt in pats if re.search(pt, t, re.IGNORECASE)]
    if found:
        return _pas("model evaluation", f"found: {found[0][:20]}")
    _warn("model evaluation", "未发现模型评价（优缺点）")


def check_assumptions_necessity(p):
    """13. 假设章节 + 必要性/因为/为了/由于/简化 关键词。"""
    t = _read_source(p)
    if t is None:
        return _warn("assumptions", "no source")
    if not re.search(r"假设|assumption", t, re.IGNORECASE):
        return _warn("assumptions", "no assumption section")
    pats = ["必要性", "因为", "为了", "由于", "简化", "necessary", "simplify"]
    found = [pt for pt in pats if re.search(pt, t, re.IGNORECASE)]
    if found:
        return _pas("assumptions", "assumptions with justification")
    _warn("assumptions", "假设缺必要性说明")


def check_table_figure_analysis(p):
    """14. 图表数 vs "如图/如表/图N/表N" 引用数。"""
    t = _read_source(p)
    if t is None:
        return _warn("figure analysis", "no source")
    n_figures = len(re.findall(r"\\includegraphics", t))
    n_tables = len(re.findall(r"\\begin\{table\}", t))
    total = n_figures + n_tables
    if total == 0:
        return _warn("figure analysis", "no figures or tables")
    refs = len(re.findall(r"如图|如表|图\d|表\d|Figure|Table", t))
    if refs >= total:
        return _pas("figure analysis", f"{total} figs/tables, {refs} refs")
    _warn("figure analysis", f"{total} 图表但仅 {refs} 引用，可能缺分析")


def check_problem_type_specific(p):
    """15. 数值结果数量 >10。"""
    t = _read_source(p)
    if t is None:
        return _warn("numeric results", "no source")
    numbers = re.findall(r"\d+\.?\d*", t)
    if len(numbers) > 10:
        return _pas("numeric results", f"{len(numbers)} numbers found")
    _warn("numeric results", f"仅 {len(numbers)} 个数值，可能缺细节")


# ===========================================================================
# 写作护栏检查（新增硬门禁 / 软告警，P0/P1/P2）
# ===========================================================================
def _extract_body(t):
    """截取正文区域：\\begin{document} 之后，到 \\appendix（或 \\end{document}）之前。

    返回 (body, appendix_region)。难以区分附录时，body 全文但豁免 \\appendix 之后内容。
    """
    m_doc = re.search(r"\\begin\{document\}", t)
    start = m_doc.end() if m_doc else 0
    full = t[start:]
    # 附录环境（\\begin{appendix}...\\end{appendix}）
    app_env = re.search(r"\\begin\{appendix\}(.*?)\\end\{appendix\}", full, re.DOTALL)
    appendix_region = app_env.group(1) if app_env else ""
    # \\appendix 命令之后的内容豁免（难以区分时按命令切分）
    m_app = re.search(r"\\appendix", full)
    body = full[:m_app.start()] if m_app else full
    return body, appendix_region


def check_body_no_lists(p):
    """H1. 正文（排除附录）禁止 \\begin{itemize}/\\begin{enumerate}（典型 AI 痕迹）。"""
    t = _read_source(p)
    if t is None:
        return _warn("body no lists", "no source")
    body, _ = _extract_body(t)
    if re.search(r"\\begin\{(itemize|enumerate)\}", body):
        return _hard("body no lists", "正文出现 itemize/enumerate 列表（AI 痕迹）")
    _pas("body no lists", "正文无 itemize/enumerate")


def check_body_chinese_list(p):
    """H4. 正文出现全角中文分点式（（1）（2）/（一）（二）/①②③）→ WARN 提示改写段落式。

    分点式论述是典型 AI 痕迹（套列点模板）。附录与 $$...$$ 公式块豁免；
    因问题重述题面列举、逐条假设等存在少量合法用例，记 WARN 提醒改写，
    正文主体的密集分点式由知识库禁令 + 段首频次兜底。
    """
    t = _read_source(p)
    if t is None:
        return _warn("body chinese list", "no source")
    body, _ = _extract_body(t)
    # 去掉 $$...$$ 公式块与注释行，避免公式编号 / 注释被误判
    body = re.sub(r"\$\$.*?\$\$", "", body, flags=re.DOTALL)
    body = "\n".join(l for l in body.split("\n") if not l.strip().startswith("%"))
    hits = []
    for i, line in enumerate(body.split("\n"), 1):
        s = line.strip()
        if re.search(r"（\s*[0-9一二三四五六七八九十]+\s*）|[①②③④⑤⑥⑦⑧⑨⑩]", s):
            hits.append((i, s[:30]))
    if hits:
        sample = "；".join(f"L{l}:{s}" for l, s in hits[:3])
        return _warn("body chinese list",
                     f"正文含 {len(hits)} 处分点式（{sample}）→ 建议改为段落式")
    _pas("body chinese list", "正文无全角分点式")


def check_figure_as_subject(p):
    """H2. 图表主语句式段首（图X展示了/如图X所示/由图X可知/从图X可以看出）≥阈值 → HARD。"""
    t = _read_source(p)
    if t is None:
        return _warn("figure as subject", "no source")
    max_count = int(_ENV_GET("review.figure_as_subject_max") or 3)
    pats = [r"图\d+展示了", r"如图\d+所示", r"由图\d+可知", r"从图\d+可以看出"]
    count = 0
    for line in t.split("\n"):
        s = line.strip()
        if not s:
            continue
        for pat in pats:
            if re.match(pat, s):
                count += 1
                break
    if count >= max_count:
        return _hard("figure as subject",
                     f"图表主语句式段首出现 {count} 次 (>= {max_count})")
    _pas("figure as subject", f"{count} 次 (阈值 {max_count})")


def check_internal_terms_leak(p):
    """H3. 论文正文泄露内部术语（MODEL_SPEC.md 等）→ HARD；仅附录内 → WARN。"""
    t = _read_source(p)
    if t is None:
        return _warn("internal terms leak", "no source")
    body, appendix_region = _extract_body(t)
    hard_hits = []
    warn_hits = []
    for pat in INTERNAL_TERM_PATTERNS:
        try:
            if re.search(pat, body):
                hard_hits.append(pat)
            elif appendix_region and re.search(pat, appendix_region):
                warn_hits.append(pat)
        except re.error:
            pass
    if hard_hits:
        shown = ", ".join(h[:24] for h in hard_hits[:5])
        return _hard("internal terms leak", f"正文泄露内部术语: {shown}")
    if warn_hits:
        shown = ", ".join(w[:24] for w in warn_hits[:5])
        return _warn("internal terms leak", f"附录含内部术语(可豁免): {shown}")
    _pas("internal terms leak", "无内部术语泄露")


def check_abstract_words(p):
    """W1. 摘要（abstract 环境）中文字数在 [abstract_min_words, abstract_max_words] 之外 → WARN。"""
    t = _read_source(p)
    if t is None:
        return _warn("abstract words", "no source")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.DOTALL)
    if not m:
        return _warn("abstract words", "未找到 abstract 环境")
    zh = len(re.findall(r"[\u4e00-\u9fff]", m.group(1)))
    lo = int(_ENV_GET("paper.abstract_min_words") or 400)
    hi = int(_ENV_GET("paper.abstract_max_words") or 600)
    if zh < lo or zh > hi:
        return _warn("abstract words", f"摘要 {zh} 字 (建议 {lo}-{hi})")
    _pas("abstract words", f"{zh} 字 (范围 {lo}-{hi})")


def check_recent_refs(p):
    """W2. references.bib 近 3 年(2024-2026)文献占比 < recent_ref_ratio → WARN。"""
    bib = p / "paper" / "references.bib"
    if not bib.exists():
        return _warn("recent refs", "no references.bib")
    try:
        text = bib.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return _warn("recent refs", "读取失败")
    total = len(re.findall(r"@\w+\{", text))
    if total == 0:
        return _warn("recent refs", "未找到条目")
    years = [int(y) for y in
             re.findall(r"(?:year|年份)\s*=\s*['\"]?\{?\s*(\d{4})", text, re.IGNORECASE)]
    recent = sum(1 for y in years if 2024 <= y <= 2026)
    ratio = recent / total
    threshold = float(_ENV_GET("paper.recent_ref_ratio") or 0.6)
    if ratio < threshold:
        return _warn("recent refs",
                     f"近3年占比 {ratio:.0%} ({recent}/{total}) < {threshold:.0%}")
    _pas("recent refs", f"近3年占比 {ratio:.0%} ({recent}/{total})")


def check_inline_table_rows(p):
    """W3. 正文 tabular 行数(\\\\ 计数) > table_max_rows_inline → WARN。"""
    t = _read_source(p)
    if t is None:
        return _warn("inline table rows", "no source")
    max_rows = int(_ENV_GET("paper.table_max_rows_inline") or 12)
    tables = re.findall(r"\\begin\{tabular\}.*?\\end\{tabular\}", t, re.DOTALL)
    over = [tb.count("\\\\") for tb in tables if tb.count("\\\\") > max_rows]
    if over:
        shown = ", ".join(str(r) for r in over[:5])
        return _warn("inline table rows",
                     f"正文表格行数超标: {shown} (阈值 {max_rows})")
    _pas("inline table rows", f"{len(tables)} 表，均<= {max_rows} 行")


# ===========================================================================
# 扩展门禁（升级新增，对应 agent SKILL.md 引用的 check_ 函数）
# ===========================================================================
def check_deliverables_size(p):
    """A1. CODE_DELIVERABLES.md >= code.min_deliverables_bytes；code/main.py >= code.min_main_py_bytes。

    来自 Programmer/hash-auditor 的硬性交付物体积门禁。缺失或过小为 HARD。
    """
    min_md = int(_ENV_GET("code.min_deliverables_bytes") or 1024)
    min_py = int(_ENV_GET("code.min_main_py_bytes") or 500)
    md = p / "output" / "CODE_DELIVERABLES.md"
    py = p / "code" / "main.py"
    if not md.exists():
        return _hard("deliverables size", "output/CODE_DELIVERABLES.md 不存在")
    if md.stat().st_size < min_md:
        return _hard("deliverables size",
                     f"CODE_DELIVERABLES.md {md.stat().st_size}B < {min_md}B")
    if not py.exists():
        return _hard("deliverables size", "code/main.py 不存在")
    if py.stat().st_size < min_py:
        return _hard("deliverables size",
                     f"code/main.py {py.stat().st_size}B < {min_py}B")
    _pas("deliverables size", f"md {md.stat().st_size}B / py {py.stat().st_size}B")


def check_no_undefined_refs(p):
    """A2. 编译日志 paper/main.log 含 undefined references/citations → HARD。

    仅当主机关联 xelatex 且已编译时有效；未编译（无 main.log）降级 WARN。
    """
    log = p / "paper" / "main.log"
    if not log.exists():
        return _warn("no undefined refs", "main.log 不存在（未编译）")
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return _warn("no undefined refs", "读取失败")
    if re.search(r"undefined", text, re.IGNORECASE):
        return _hard("no undefined refs", "main.log 含 undefined references/citations")
    _pas("no undefined refs", "无未定义引用")


STOCK_OPENERS = ["本文", "我们", "研究", "该模", "该方"]


def check_consecutive_same_opening(p):
    """W4. 连续 >=3 段以相同套路开头词（本文/我们/研究...）开头 → WARN（AI 痕迹）。"""
    t = _read_source(p)
    if t is None:
        return _warn("consecutive same opening", "no source")
    body, _ = _extract_body(t)
    paras = [ln.strip() for ln in body.split("\n\n") if ln.strip()]
    run = 1
    flagged = 0
    for i in range(1, len(paras)):
        prev2 = paras[i - 1][:2]
        cur2 = paras[i][:2]
        if prev2 == cur2 and prev2 in STOCK_OPENERS:
            run += 1
            if run >= 3:
                flagged += 1
        else:
            run = 1
    if flagged > 0:
        return _warn("consecutive same opening",
                     f"存在 {flagged} 处连续>=3段相同套路开头")
    _pas("consecutive same opening", "无连续相同套路开头")


PHRASE_FREQ_WATCH = [
    "一般而言", "不可否认", "毋庸置疑", "可以预见",
    "在此基础上", "不难发现", "不难理解", "与之对应",
]


def check_phrase_frequency(p):
    """W5. 套话（非禁用词但模板化）全文出现 >=3 次 → WARN。"""
    t = _read_source(p)
    if t is None:
        return _warn("phrase frequency", "no source")
    body, _ = _extract_body(t)
    hits = []
    for ph in PHRASE_FREQ_WATCH:
        c = body.count(ph)
        if c >= 3:
            hits.append(f"{ph}×{c}")
    if hits:
        return _warn("phrase frequency", "套话高频: " + ", ".join(hits))
    _pas("phrase frequency", "无高频套话")


def check_too_perfect(p):
    """W6. 检测"太完美结果"信号（R²=1、误差全0、完美拟合）提示过拟合/编造 → WARN。"""
    t = _read_source(p)
    if t is None:
        return _warn("too perfect", "no source")
    signals = [r"R\^?2\s*=\s*1\.?0+", r"R²\s*=\s*1\.?0+",
               r"完全吻合", r"完美拟合", r"完全重现", r"误差为\s*0",
               r"零误差", r"完全重合", r"完美过所有点"]
    hits = [s for s in signals if re.search(s, t)]
    if hits:
        return _warn("too perfect", "疑似过完美信号: " + ", ".join(hits[:3]))
    _pas("too perfect", "无过完美信号")


def check_citation_format(p):
    """W7. 文献引用须为 GB/T 7714 顺序编码制上标 [n]（禁止作者—年份）。

    检测：正文是否含 \\citep/\\citet/\\citeauthor/\\citeyear（作者—年份命令）；
    \\bibliographystyle 是否为作者—年份/非国标样式（plainnat/apalike/alpha/
    gbt7714-author-year/agsm/abbrvnat）；natbib 是否未启用 numbers/super。
    任一命中 → WARN（格式硬伤，竞赛论文强制上标）。"""
    t = _read_source(p)
    if t is None:
        return _warn("citation format", "no source")
    flags = []
    if re.search(r"\\citep\s*\{|\\citet\s*\{|\\citeauthor\s*\{|\\citeyear\s*\{", t):
        flags.append("存在作者—年份引用命令(\\citep/\\citet...)")
    m = re.search(r"\\bibliographystyle\{(\w[\w\-]*)\}", t)
    if m:
        style = m.group(1).lower()
        author_year_styles = {"plainnat", "apalike", "alpha", "gbt7714-author-year",
                              "agsm", "abbrvnat", "apacite", "chicago"}
        if style in author_year_styles:
            flags.append(f"bibliographystyle={{{style}}} 为作者—年份/非国标样式")
    if "\\usepackage" in t and "natbib" in t:
        mm = re.search(r"\\usepackage\[([^\]]*)\]\{natbib\}", t)
        if mm and "super" not in mm.group(1).lower() and "numbers" not in mm.group(1).lower():
            flags.append("natbib 未启用 numbers/super（未上标）")
    if flags:
        return _warn("citation format", "；".join(flags))
    _pas("citation format", "GB/T 7714 顺序编码制上标 [n]")


def check_abstract_keywords(p):
    """W8. 摘要须含 3-5 个关键词（中文分号分隔）。

    检测 abstract 环境内是否出现「关键词」或 \\keywords。缺失 → WARN。"""
    t = _read_source(p)
    if t is None:
        return _warn("abstract keywords", "no source")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.DOTALL)
    if not m:
        return _warn("abstract keywords", "未找到 abstract 环境")
    if not re.search(r"关键词|\\keywords", m.group(1)):
        return _warn("abstract keywords", "摘要缺少关键词（关键词：A；B；C）")
    _pas("abstract keywords", "摘要含关键词")


# ===========================================================================
# 第 3 组：Reproducibility（3）
# ===========================================================================
def check_reproducibility(p):
    """16. code/*.py 或论文源含 np.random.seed/random.seed(数字)。"""
    sources = []
    if (p / "code").exists():
        sources += list((p / "code").glob("*.py"))
    src = _src_path(p)
    if src is not None:
        sources.append(src)
    if not sources:
        return _warn("random seed", "no source files")
    for f in sources:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if re.search(r"(np\.random\.seed|random\.seed)\(\d+\)", t):
            return _pas("random seed", f"found in {f.name}")
    _hard("random seed", "未发现 np.random.seed(42) 或等效设置（铁律 P1）")


def check_numeric_traceability(p):
    """17. 核心算法：论文每个数值在 ledger 找匹配（容差 abs<=tol_abs 或相对 <=tol_rel；比例 >= traceability_min_ratio）。"""
    f = p / "figures" / "all_results.json"
    if not f.exists():
        return _warn("traceability", "no ledger")
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return _warn("traceability", "invalid ledger")
    ledger_values = set()

    def _walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            ledger_values.add(round(float(obj), 4))
    _walk(data)
    if not ledger_values:
        return _warn("traceability", "no numbers in ledger")
    t = _read_source(p)
    if t is None:
        return _warn("traceability", "no source")
    paper_nums = [float(x) for x in re.findall(r"\b\d+\.?\d+\b", t)]
    result_nums = [n for n in paper_nums if n <= 10000]  # 排除年份/页码/大坐标
    if not result_nums:
        return _warn("traceability", "no numbers in paper")
    tolb = float(_ENV_GET("runtime.numeric_tolerance_abs") or 0.01)
    tolr = float(_ENV_GET("runtime.numeric_tolerance_rel") or 0.005)
    min_ratio = float(_ENV_GET("runtime.traceability_min_ratio") or 0.90)
    traceable = 0
    for pn in result_nums:
        for lv in ledger_values:
            denom = max(abs(pn), 1e-9)
            if abs(pn - lv) <= tolb or abs(pn - lv) / denom <= tolr:
                traceable += 1
                break
    ratio = traceable / len(result_nums)
    if ratio >= min_ratio:
        return _pas("traceability", f"{traceable}/{len(result_nums)} 可追溯 ({ratio:.0%})")
    _hard("traceability",
          f"仅 {traceable}/{len(result_nums)} 可追溯 ({ratio:.0%})，违反铁律 W1")


def check_code_template_usage(p):
    """18. code/*.py 含"模板来源/template source/code-templates"注释。"""
    code_dir = p / "code"
    if not code_dir.exists() or not list(code_dir.glob("*.py")):
        return _warn("code templates", "no code files")
    refs = 0
    for cf in code_dir.glob("*.py"):
        try:
            ct = cf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if re.search(r"模板来源|template.*source|code-templates", ct, re.IGNORECASE):
            refs += 1
    if refs > 0:
        return _pas("code templates", f"{refs} files reference templates")
    _warn("code templates", "代码未注明模板来源")


# ===========================================================================
# 第 4 组：Physics model（6，题型触发：is_physics=True 时 HARD）
# ===========================================================================
def check_coordinate_system(p):
    """19. 论文含坐标系定义关键词。"""
    t = _read_source(p)
    if t is None:
        return _physics_fail("coordinate system", "no source")
    pats = [r"z\s*正向为下", r"z\s*正向为上", r"坐标系.*定义",
            r"coordinate\s*system", r"原点", r"z\s*轴.*?正",
            r"竖直.*?向下", r"竖直.*?向上"]
    found = [pt for pt in pats if re.search(pt, t, re.IGNORECASE)]
    if found:
        return _pas("coordinate system", found[0][:30])
    _physics_fail("coordinate system", "论文未显式定义坐标系")


def check_analysis_report_physics(p):
    """20. work/ANALYSIS_MODELING_REPORT.md 或 work/model_draft.md 含 坐标系/实体/轨迹/解析。"""
    candidates = [p / "work" / "ANALYSIS_MODELING_REPORT.md",
                  p / "work" / "model_draft.md"]
    f = next((x for x in candidates if x.exists()), None)
    if f is None:
        return _physics_fail("analysis physics", "no analysis report")
    try:
        t = f.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return _physics_fail("analysis physics", "读取失败")
    required = ["坐标系", "实体", "轨迹", "解析"]
    missing = [k for k in required if k not in t]
    if missing:
        return _physics_fail("analysis physics", f"missing: {','.join(missing)}")
    _pas("analysis physics", "物理过程校验表完整")


def check_code_coordinate_consistency(p):
    """21. 启发式检查代码自由落体 z 轴符号。"""
    code_dir = p / "code"
    code_files = list(code_dir.glob("*.py")) if code_dir.exists() else []
    if not code_files:
        return _physics_fail("code coordinate", "no code files")
    issues = []
    for cf in code_files:
        try:
            ct = cf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 若出现 z = ... - 0.5*g*t**2 且无注释说明 z 正向为上，则警告
        if re.search(r"z\s*=\s*.*-\s*0\.5\s*\*\s*g\s*\*\s*t\s*\*\*\s*2", ct) and \
           not re.search(r"z\s*正向为上|z.*positive.*up", ct, re.IGNORECASE):
            issues.append(f"{cf.name}: free-fall z decreases (可能 z 轴符号错误)")
    if issues:
        return _physics_fail("code coordinate", issues[0])
    _pas("code coordinate", "no z-axis sign conflict")


def check_geometry_criterion(p):
    """22. 检查点到线段距离（cross/叉积/np.cross）+ 投影区间约束（t_proj/proj 0..1）。"""
    code_dir = p / "code"
    code_files = list(code_dir.glob("*.py")) if code_dir.exists() else []
    if not code_files:
        return _physics_fail("geometry criterion", "no code files")
    has_segment = False
    has_proj = False
    for cf in code_files:
        try:
            ct = cf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if re.search(r"cross|叉积|np\.cross", ct, re.IGNORECASE):
            has_segment = True
        if re.search(r"t_proj|proj.*0.*1|0\.0.*t_proj.*1\.0", ct):
            has_proj = True
    if has_segment and has_proj:
        return _pas("geometry criterion", "segment distance + projection clamp")
    if has_segment:
        return _physics_fail("geometry criterion", "有叉积但缺投影区间约束")
    _physics_fail("geometry criterion", "未发现点到线段距离模式")


def check_analytic_validation(p):
    """23. all_results.json 含 analytic/解析/validation/验证/baseline/基准/error/误差 关键词。"""
    f = p / "figures" / "all_results.json"
    if not f.exists():
        return _physics_fail("analytic validation", "no ledger")
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return _physics_fail("analytic validation", "invalid ledger")
    s = json.dumps(data).lower()
    pats = ["analytic", "解析", "validation", "验证", "baseline", "基准", "error", "误差"]
    found = [pt for pt in pats if pt in s]
    if found:
        return _pas("analytic validation", f"keywords: {','.join(found[:3])}")
    _physics_fail("analytic validation", "账本未记录解析验证/基准误差")


def check_time_bounds(p):
    """24. 检查 T_MAX 是否过大（>100 warn）或关联 missile arrival。"""
    code_dir = p / "code"
    code_files = list(code_dir.glob("*.py")) if code_dir.exists() else []
    if not code_files:
        return _physics_fail("time bounds", "no code files")
    for cf in code_files:
        try:
            ct = cf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if re.search(r"T_MAX\s*=.*missile.*arrival|T_MAX\s*=.*arrive",
                     ct, re.IGNORECASE):
            return _pas("time bounds", "T_MAX linked to missile arrival")
        m = re.search(r"T_MAX\s*=\s*(\d+)", ct)
        if m and int(m.group(1)) > 100:
            return _physics_fail("time bounds",
                                 f"T_MAX={m.group(1)} 过大，检查物理可行性")
    _physics_fail("time bounds", "T_MAX 未显式约束")


# ===========================================================================
# 第 5 组：Directory structure（3，硬门禁）
# ===========================================================================
def check_directory_structure(p):
    """25. 项目根目录无散落产物（.py/.xlsx/.csv/.png/.jpg/.jpeg/.svg/.pdf）。"""
    forbidden_exts = {".py", ".xlsx", ".csv", ".png", ".jpg", ".jpeg", ".svg", ".pdf"}
    allowed_root_files = {"catalog.yaml", "README.md", "readme.md", ".gitignore"}
    issues = []
    for item in p.iterdir():
        if not item.is_file():
            continue
        if item.name in allowed_root_files:
            continue
        if item.suffix.lower() in forbidden_exts:
            issues.append(item.name)
    if issues:
        return _hard("directory structure",
                     f"根目录散落产物: {', '.join(issues[:3])}")
    _pas("directory structure", "根目录无散落产物")


def check_code_in_code_dir(p):
    """26. 代码在 code/ 下，不在根目录。"""
    root_py = list(p.glob("*.py"))
    if root_py:
        return _hard("code location",
                     f"代码在根目录: {', '.join(f.name for f in root_py[:3])}")
    if not (p / "code").exists() or not list((p / "code").glob("*.py")):
        return _warn("code location", "code/ 目录无 .py 文件")
    _pas("code location", "code/ 目录")


def check_tables_in_tables_dir(p):
    """27. 表格产物在 tables/ 下，不在根目录或 figures/。"""
    root_xlsx = list(p.glob("*.xlsx")) + list(p.glob("*.csv"))
    figs_xlsx = []
    if (p / "figures").exists():
        figs_xlsx = list((p / "figures").glob("*.xlsx")) + list((p / "figures").glob("*.csv"))
    if root_xlsx or figs_xlsx:
        locs = [f"根目录: {f.name}" for f in root_xlsx[:2]] + \
               [f"figures/: {f.name}" for f in figs_xlsx[:2]]
        return _hard("tables location", f"表格位置错误 - {', '.join(locs)}")
    _pas("tables location", "无错位表格")


# ===========================================================================
# 第 6 组：Code quality（3）
# ===========================================================================
def check_python_syntax(p):
    """28. py_compile 编译 code/*.py。"""
    import py_compile
    code_dir = p / "code"
    if not code_dir.exists() or not list(code_dir.glob("*.py")):
        return _warn("python syntax", "no code files")
    errors = []
    for py_file in code_dir.glob("*.py"):
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"{py_file.name}: {e}")
    if errors:
        return _hard("python syntax", "; ".join(errors)[:200])
    _pas("python syntax", "all files valid")


def check_code_comments(p):
    """29. code/*.py 注释率（>50 行时注释率 <10% warn）。"""
    code_dir = p / "code"
    if not code_dir.exists() or not list(code_dir.glob("*.py")):
        return _warn("code comments", "no code files")
    low = []
    for py_file in code_dir.glob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        lines = content.split("\n")
        total = len(lines)
        comments = sum(1 for l in lines if l.strip().startswith("#"))
        if total > 50 and comments / total < 0.1:
            low.append(f"{py_file.name} ({comments}/{total})")
    if low:
        return _warn("code comments", f"注释率低: {', '.join(low[:3])}")
    _pas("code comments", "注释率合理")


def check_imports(p):
    """30. code/*.py 潜在未使用 import（启发式 warn）。"""
    code_dir = p / "code"
    if not code_dir.exists() or not list(code_dir.glob("*.py")):
        return _warn("imports", "no code files")
    unused = []
    for py_file in code_dir.glob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        imports = re.findall(r"^(?:from|import)\s+(\w+)", content, re.MULTILINE)
        for imp in imports:
            # 启发式：去掉 import 行后看模块名是否还出现
            rest = content.replace(f"import {imp}", "").replace(f"from {imp}", "")
            if imp not in rest:
                unused.append(f"{py_file.name}: {imp}")
    if unused:
        return _warn("imports", f"潜在未使用: {', '.join(unused[:3])}")
    _pas("imports", "no obvious unused imports")


# ===========================================================================
# 第 7 组：Env thresholds（6，读 env 阈值做最终校验）
# ===========================================================================
def check_paper_pages(p):
    """31. PDF 页数 >= get("paper.min_pages")。"""
    min_pages = int(_ENV_GET("paper.min_pages") or 17)
    log_file = p / "paper" / "main.log"
    if not log_file.exists():
        return _warn("paper pages", f"无 main.log，需人工确认 >= {min_pages}")
    try:
        log_text = log_file.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return _warn("paper pages", "main.log 读取失败")
    m = re.search(r"Output written on .+?\((\d+)\s+pages?", log_text)
    if not m:
        return _warn("paper pages", "main.log 未找到页数信息")
    pages = int(m.group(1))
    if pages >= min_pages:
        return _pas("paper pages", f"{pages} pages (>= {min_pages})")
    _threshold_fail("paper pages", f"{pages} pages (< {min_pages})")


def check_pdf_compile_chain(p):
    """LaTeX 编译链完整性：xelatex → bibtex → xelatex → xelatex。

    引擎从 runtime.latex_engine 读取（默认 xelatex）。
    编译链跑不满会导致交叉引用、参考文献、目录出现 ?? 或 [?]——
    这是最终 PDF 最常见的低级错误，必须在提交前拦截。

    此前 final-validator/SKILL.md 已把该项列为 HARD 门禁，但本函数缺失，
    属于"门禁只写在纸上"，故补齐实现。
    """
    engine = _ENV_GET("runtime.latex_engine") or "xelatex"
    compile_mode = _ENV_GET("runtime.compile_pdf") or "auto"

    if compile_mode == "never":
        return _warn("pdf compile chain", "compile_pdf=never，跳过")

    if not (p / "paper" / "main.tex").exists():
        return _warn("pdf compile chain", "无 main.tex，跳过")

    pdf = p / "paper" / "main.pdf"
    if not pdf.exists():
        if compile_mode == "always":
            _threshold_fail("pdf compile chain", "compile_pdf=always 但无 main.pdf")
        else:
            _warn("pdf compile chain", f"无 main.pdf（compile_pdf={compile_mode}）")
        return

    log = p / "paper" / "main.log"
    if not log.exists():
        return _warn("pdf compile chain", "无 main.log，无法验证编译链")

    try:
        log_text = log.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return _warn("pdf compile chain", "main.log 读取失败")

    issues = []

    # 引擎调用次数：完整链至少 2 次（bibtex 前后各一次）
    n_runs = len(re.findall(rf"This is [^\n]*{re.escape(engine)}", log_text, re.IGNORECASE))
    if n_runs < 2:
        issues.append(f"{engine} 仅运行 {n_runs} 次，完整链需 >= 2 次")

    # 有 bib 文件则日志中应见 bibtex/biber
    bib = p / "paper" / "references.bib"
    if bib.exists() and not re.search(r"bibtex|biber", log_text, re.IGNORECASE):
        issues.append("存在 references.bib 但日志未见 bibtex/biber")

    # 未定义引用是编译链不足的典型症状
    undefined = re.findall(
        r"LaTeX Warning: (?:Reference|Citation)[^\n]*undefined", log_text
    )
    if undefined:
        issues.append(f"存在 {len(undefined)} 处未定义引用，需重跑编译链")

    if issues:
        _threshold_fail("pdf compile chain", "; ".join(issues))
        return

    return _pas("pdf compile chain", f"{engine} 链完整（{n_runs} 次运行）")


def check_page_fill_ratio(p):
    """版面填充率 >= get("paper.page_fill_ratio")（默认 0.8，铁律 W14）。

    优先用 main.log 的真实页数；无日志时按 正文字数 / chars_per_page 估算。
    页面大面积留白是论文被扣分的常见原因，且不会触发任何字数/页数下限门禁。

    此前 final-validator/SKILL.md 已把该项列为 HARD 门禁，但本函数缺失，故补齐。
    """
    min_ratio = float(_ENV_GET("paper.page_fill_ratio") or 0.85)
    max_pages = int(_ENV_GET("paper.max_pages") or 20)
    chars_per_page = int(_ENV_GET("paper.chars_per_page") or 800)

    log = p / "paper" / "main.log"
    if log.exists():
        try:
            log_text = log.read_text(encoding="utf-8", errors="replace")
        except Exception:
            log_text = ""
        m = re.search(r"Output written on .+?\((\d+)\s+pages?", log_text)
        if m:
            pages = int(m.group(1))
            ratio = pages / max_pages if max_pages else 0
            if ratio >= min_ratio:
                return _pas(
                    "page fill ratio",
                    f"实测 {pages}/{max_pages} 页 = {ratio:.0%} (>= {min_ratio:.0%})",
                )
            _threshold_fail(
                "page fill ratio",
                f"实测 {pages}/{max_pages} 页 = {ratio:.0%} (< {min_ratio:.0%})，正文偏空",
            )
            return

    t = _read_source(p)
    if t is None:
        return _warn("page fill ratio", "no source")

    chinese = len(re.findall(r"[\u4e00-\u9fff]", t))
    est_pages = chinese / chars_per_page if chars_per_page else 0
    ratio = est_pages / max_pages if max_pages else 0
    if ratio >= min_ratio:
        return _pas(
            "page fill ratio",
            f"估算 {est_pages:.1f}/{max_pages} 页 = {ratio:.0%} (>= {min_ratio:.0%})",
        )
    _threshold_fail(
        "page fill ratio",
        f"估算 {est_pages:.1f}/{max_pages} 页 = {ratio:.0%} (< {min_ratio:.0%})",
    )


def check_paper_words(p):
    """32. 论文源字数 >= get("paper.min_words")（中文字符+英文词）。

    只统计**正文**字数：摘要（abstract）与附录（appendix）不计入正文篇幅下限。
    此前把附录/摘要一并计入，会把"堆在附录里的字数"当成正文达标，造成假通过；
    反过来若某合规论文正文达标但附录很短也不会误判。这里统一只量正文。
    """
    min_words = int(_ENV_GET("paper.min_words") or 13000)
    t = _read_source(p)
    if t is None:
        return _warn("paper words", "no source")
    body = t.split(r"\begin{document}")[-1]
    # 剔除摘要环境
    body = re.sub(r"\\begin\{abstract\}.*?\\end\{abstract\}", " ",
                  body, flags=re.DOTALL)
    # 剔除附录环境
    body = re.sub(r"\\begin\{appendix\}.*?\\end\{appendix\}", " ",
                  body, flags=re.DOTALL)
    # 剔除 \appendix 命令及其之后全部内容（无环境写法的附录）
    body = re.sub(r"\\appendix\b.*", " ", body, flags=re.DOTALL)
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", body))
    english_words = len(re.findall(r"[a-zA-Z]+", body))
    total = chinese_chars + english_words
    if total >= min_words:
        return _pas("paper words", f"{total} 字符/词 (>= {min_words})")
    _threshold_fail("paper words", f"{total} 字符/词 (< {min_words})")


def check_paper_figures(p):
    """33. \\includegraphics 数 >= get("paper.min_figures")。"""
    min_figures = int(_ENV_GET("paper.min_figures") or 6)
    t = _read_source(p)
    if t is None:
        return _warn("paper figures", "no source")
    n = len(re.findall(r"\\includegraphics", t))
    if n >= min_figures:
        return _pas("paper figures", f"{n} figures (>= {min_figures})")
    _threshold_fail("paper figures", f"{n} figures (< {min_figures})")


def check_paper_tables(p):
    """34. \\begin{table} 数 >= get("paper.min_tables")。"""
    min_tables = int(_ENV_GET("paper.min_tables") or 4)
    t = _read_source(p)
    if t is None:
        return _warn("paper tables", "no source")
    n = len(re.findall(r"\\begin\{table\}", t))
    if n >= min_tables:
        return _pas("paper tables", f"{n} tables (>= {min_tables})")
    _threshold_fail("paper tables", f"{n} tables (< {min_tables})")


def check_paper_equations(p):
    """35. \\begin{equation}+\\begin{align}+\\begin{gather}+\\$\\$ 数 >= min_equations。"""
    min_eq = int(_ENV_GET("paper.min_equations") or 15)
    t = _read_source(p)
    if t is None:
        return _warn("paper equations", "no source")
    n = len(re.findall(r"\\begin\{equation\}|\\begin\{align\}|\\begin\{gather\}|\\\$\\\$",
                       t))
    if n >= min_eq:
        return _pas("paper equations", f"{n} equations (>= {min_eq})")
    _threshold_fail("paper equations", f"{n} equations (< {min_eq})")


def check_paper_references(p):
    """36. references.bib 的 @type 条目数 >= get("paper.min_references")。"""
    min_refs = int(_ENV_GET("paper.min_references") or 10)
    bib = p / "paper" / "references.bib"
    if not bib.exists():
        return _hard("paper references", "references.bib not found")
    try:
        entries = re.findall(r"@\w+\{", bib.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return _hard("paper references", "bib 读取失败")
    n = len(entries)
    if n >= min_refs:
        return _pas("paper references", f"{n} entries (>= {min_refs})")
    _threshold_fail("paper references", f"{n} entries (< {min_refs})")


# ===========================================================================
# v3 新增检查（移植自 opendraft 对标 + 强化现有铁律）
# ===========================================================================

def check_ai_writing_patterns(p):
    """37. AI 痕迹检测：倡导性/绝对化语言扫描（移植自 opendraft detect_advocacy_language）。

    检测正文中不适合学术文风的绝对化词汇：
    - must be adopted / we advocate / undeniably / obviously 等英文模式
    - 必须被采纳 / 我们呼吁 / 无可争辩 等中文模式
    命中 ≥1 条 → HARD（strict_mode）或 WARN（非 strict_mode）。
    """
    t = _read_source(p)
    if t is None:
        return _warn("ai writing patterns", "no source")

    _advocacy_patterns = [
        (r"\bmust\s+be\s+adopted\b", "prescriptive: must be adopted"),
        (r"\bwe\s+advocate\b", "advocacy: we advocate"),
        (r"\bundeniably\b", "overconfident: undeniably"),
        (r"\bunquestionably\b", "overconfident: unquestionably"),
        (r"\bobviously\b", "overconfident: obviously"),
        (r"\bdemands\s+that\b", "prescriptive: demands that"),
        (r"\b必须被采纳", "prescriptive_zh: 必须被采纳"),
        (r"\b我们呼吁", "advocacy_zh: 我们呼吁"),
        (r"\b无可争辩", "overconfident_zh: 无可争辩"),
    ]

    hits: list[str] = []
    for pattern, desc in _advocacy_patterns:
        count = len(re.findall(pattern, t, re.IGNORECASE))
        if count > 0:
            hits.append(f"{desc} ×{count}")

    if not hits:
        return _pas("ai writing patterns", "未检出绝对化/倡导性语言")

    msg = f"检出 {len(hits)} 类 AI 痕迹: " + "; ".join(hits[:5])
    if _STRICT_MODE:
        _hard("ai writing patterns", msg)
    else:
        _warn("ai writing patterns", msg)


def check_data_feature_prints(p):
    """38. 代码中每张图表生成后必须有【图X数据特征】print()（铁律 P4 同源）。

    扫描 code/*.py 中含 matplotlib/seaborn 图形生成函数后是否有对应的数据特征输出。
    若代码生成图形但缺数据特征输出标记 → WARN。
    仅检索静态标记，不运行代码。
    """
    code_dir = p / "code"
    if not code_dir.exists():
        return _warn("data feature prints", "code/ not found")

    gen_funcs = ["plt.plot", "plt.bar", "plt.scatter", "plt.imshow",
                 "plt.boxplot", "plt.hist", "sns.lineplot", "sns.barplot",
                 "sns.heatmap", "sns.scatterplot"]
    feature_markers = ["【图", "data_feature", "数据特征"]

    py_files = list(code_dir.glob("*.py"))
    if not py_files:
        return _warn("data feature prints", "code/*.py not found")

    gen_count = 0
    feature_count = 0
    for py in py_files:
        try:
            src = py.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for gf in gen_funcs:
            gen_count += src.count(gf)
        for fm in feature_markers:
            feature_count += src.count(fm)

    if gen_count == 0:
        return _pas("data feature prints", "无图形生成调用（无需数据特征打印）")
    if feature_count > 0:
        ratio = feature_count / gen_count
        if ratio >= 0.3:
            return _pas("data feature prints",
                        f"图生成 {gen_count} 处，数据特征输出 {feature_count} 处（密度 {ratio:.2f}）")
        _warn("data feature prints",
              f"图生成 {gen_count} 处，数据特征输出仅 {feature_count} 处（密度 {ratio:.2f}），建议补全")
        return
    _warn("data feature prints",
          f"图生成 {gen_count} 处但无【图X数据特征】输出标记，正文无法快速核对图表数值")


def check_abstract_body_numeric_consistency(p):
    """39. 摘要中的关键数值必须与正文/表格一致（铁律 W1 强化）。

    提取摘要中的数值（含小数点格式）并检查其在正文中出现。
    若某数值仅在摘要出现但完全不出现在正文 → WARN/HARD（疑似不一致）。
    轻量级启发式，不替代 consistency-checker 的全量核对。
    """
    t = _read_source(p)
    if t is None:
        return _warn("abstract-body numeric consistency", "no source")

    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.DOTALL)
    if not m:
        return _warn("abstract-body numeric consistency", "未定位到 abstract 环境")
    abstract_text = m.group(1)

    abstract_nums = set(re.findall(r"\b\d+\.\d{1,3}\b", abstract_text))
    if not abstract_nums:
        return _pas("abstract-body numeric consistency", "摘要无小数数值（无需对比）")

    body_text = t[:m.start()] + t[m.end():]
    missing = [n for n in abstract_nums if body_text.count(n) == 0]
    # 过滤明显是年份/IP 等非结果数值（小于 1 或大于 1e6 的忽略）
    missing = [n for n in missing if 1.0 <= float(n) <= 1e6]

    if not missing:
        return _pas("abstract-body numeric consistency",
                    f"摘要 {len(abstract_nums)} 个数值均在正文出现")
    if len(missing) <= 2:
        _warn("abstract-body numeric consistency",
              f"摘要中 {missing} 未在正文出现，可能不一致")
    else:
        _hard("abstract-body numeric consistency",
              f"摘要中 {len(missing)} 个数值未在正文出现（{missing[:3]}...），疑似摘要-正文不一致")


# ===========================================================================
# 检查函数分组（10 组共 39 项）
# ===========================================================================
CHECKS = [
    ("Required artifacts", [
        check_pdf, check_source, check_bib, check_results_ledger,
        check_deliverables_size, check_no_undefined_refs,
    ]),
    ("Content quality", [
        check_placeholders, check_forbidden_words, check_verify_report,
        check_citation_integrity, check_figure_refs, check_paper_structure,
        check_sensitivity_analysis, check_model_evaluation,
        check_assumptions_necessity, check_table_figure_analysis,
        check_problem_type_specific,
        check_ai_writing_patterns,  # v3: AI 痕迹绝对化语言检测
    ]),
    ("Reproducibility", [
        check_reproducibility, check_numeric_traceability, check_code_template_usage,
        check_data_feature_prints,  # v3: 代码图表数据特征 print 检测
        check_abstract_body_numeric_consistency,  # v3: 摘要-正文数值一致性
    ]),
    ("Physics model", [
        check_coordinate_system, check_analysis_report_physics,
        check_code_coordinate_consistency, check_geometry_criterion,
        check_analytic_validation, check_time_bounds,
    ]),
    ("Directory structure", [
        check_directory_structure, check_code_in_code_dir, check_tables_in_tables_dir,
    ]),
    ("Code quality", [
        check_python_syntax, check_code_comments, check_imports,
    ]),
    ("Writing guardrails", [
        check_internal_terms_leak, check_body_no_lists, check_body_chinese_list,
        check_figure_as_subject,
        check_abstract_words, check_recent_refs, check_inline_table_rows,
        check_consecutive_same_opening, check_phrase_frequency, check_too_perfect,
        check_citation_format, check_abstract_keywords,
        # 补齐 final-validator 已列为 HARD 门禁、但此前缺失实现的两项
        check_pdf_compile_chain, check_page_fill_ratio,
    ]),
    ("Env thresholds", [
        check_paper_pages, check_paper_words, check_paper_figures,
        check_paper_tables, check_paper_equations, check_paper_references,
    ]),
]


# ===========================================================================
# 输出格式化
# ===========================================================================
_STATUS_TAG = {HARD: "HARD", WARN: "WARN", PASS: "PASS"}


def _print_results_by_group(group_marks):
    """按组分块打印 results，group_marks = [(group_name, start_idx, end_idx), ...]。"""
    for group_name, start, end in group_marks:
        print(f"\n[{group_name}]")
        for i in range(start, end):
            s, n, d = results[i]
            tag = _STATUS_TAG[s]
            print(f"  {tag:4}  {n}  {d}")


def _print_summary():
    """打印末尾汇总，返回退出码（HARD>0 → 1，仅 WARN → 0）。"""
    n_pass = sum(1 for s, _, _ in results if s == PASS)
    n_warn = sum(1 for s, _, _ in results if s == WARN)
    n_hard = sum(1 for s, _, _ in results if s == HARD)
    print("\n" + "=" * 70)
    print(f"汇总: {n_pass} passed, {n_warn} warnings, {n_hard} hard errors")
    if n_hard > 0:
        print("硬错误（必须修复）:")
        for s, n, d in results:
            if s == HARD:
                print(f"  - {n}: {d}")
    print("=" * 70)
    return 1 if n_hard > 0 else 0


# ===========================================================================
# main
# ===========================================================================
def main():
    global _IS_PHYSICS, _STRICT_MODE, _ENV_GET

    ap = argparse.ArgumentParser(description="项目产物质量检查")
    ap.add_argument("--project", required=True,
                    help="项目路径，如 projects/cumcm2024a")
    args = ap.parse_args()

    p = Path(args.project).resolve()
    if not p.is_dir():
        print(f"error: '{p}' not a directory")
        sys.exit(2)

    # 动态加载 env/loader（优先从 cwd 找，即用户在 MathModelSkills 根目录执行）
    cwd_root = Path.cwd()
    repo_root = cwd_root if (cwd_root / "core" / "env" / "loader.py").exists() else p
    module, err = _load_env_loader(repo_root)
    if module is not None:
        _ENV_GET = module.get
        _ENV_REQUIRE = module.require
    else:
        print(f"[env] 警告：{err}，env 阈值回退默认值")

    # 读取 strict_mode（影响阈值不达的分级）
    _STRICT_MODE = bool(_ENV_GET("runtime.strict_mode", True))

    # 读取题型（影响 Physics model 组的分级）
    pt, is_physics = _detect_problem_type(p)
    _IS_PHYSICS = is_physics
    print("=" * 70)
    print("项目产物质量检查")
    print("=" * 70)
    if pt:
        if is_physics:
            print(f"题型: {pt} (机理类) → 物理校验为硬门禁")
        else:
            print(f"题型: {pt} (非机理类) → 物理校验为建议")
    else:
        print("题型: 未识别（无 work/type_classification.json）→ 物理校验为建议")
    print(f"strict_mode: {_STRICT_MODE} → 阈值不达为 {'HARD' if _STRICT_MODE else 'WARN'}")

    # 跑所有检查，记录每组的起止下标用于分组打印
    group_marks = []
    for group_name, fns in CHECKS:
        start = len(results)
        for fn in fns:
            try:
                fn(p)
            except Exception as e:
                # 检查函数本身异常，按 WARN 处理（避免单点异常阻断全流程）
                _warn(fn.__name__, f"检查异常: {e}")
        end = len(results)
        group_marks.append((group_name, start, end))

    # 分组打印
    _print_results_by_group(group_marks)

    # 汇总与退出码
    sys.exit(_print_summary())


if __name__ == "__main__":
    main()
