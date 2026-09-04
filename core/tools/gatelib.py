#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""门禁公共库 —— 供 tools/gate.py 与各 agent 的 gate 断言复用。

零依赖（只用标准库），任何 Python 3 / 任何 agent runtime 都能调用。

设计原则：**能自动验证的不依赖"记得检查"**。
此前 19 个 agent 的 Self-Check 全是人读的 `[ ]` 复选框，等于没有门禁。
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------- 禁用词
# 与 validate.py / validate_project.py 保持同一词表（单一来源待收敛到本文件）
FORBIDDEN_WORDS = [
    "赋能", "抓手", "闭环", "颗粒度", "底层逻辑", "打法", "对齐",
    "倒逼", "复盘", "首先", "其次", "最后", "综上所述", "众所周知",
    "显而易见", "PaperCritic", "Prompt", "作为 AI", "token",
    "具有重要的理论意义和实践价值", "深入探讨", "创新性地", "值得注意的是",
    "总而言之", "具有重要意义", "实现了良好效果", "具有较高价值", "在当今",
    "参赛者", "参赛队伍", "我们团队",
    "delve", "pivotal", "tapestry", "underscore", "noteworthy",
    "It is worth noting that", "Importantly,", "Notably,",
]

FORBIDDEN_WORD_REGEXES = [r"随着.{0,12}的快速发展"]

PLACEHOLDER_PATTERNS = [
    r"TODO", r"FIXME", r"TBD", r"__XXX__",
    r"\[待补\]", r"\[TBD\]", r"示例数据", r"模板数据",
    r"PLACEHOLDER", r"XXX", r"这里填写",
    r"待补充", r"待续写", r"这里补", r"待完善",
]

INTERNAL_TERM_PATTERNS = [
    r"MODEL_SPEC\.md", r"CODE_DELIVERABLES\.md", r"PAPER_SPEC\.md",
    r"all_results\.json", r"RESULTS_REPORT", r"ANALYSIS_MODELING_REPORT",
    r"PROBLEM_ANALYSIS", r"CLAUDE\.md", r"AGENTS\.md",
    r"figures/\S+\.json", r"_tmp/", r"work/",
]

# 国赛验收（6verity Step4）：论文正文不得出现工作流内部文件名/路径。
# 比 INTERNAL_TERM_PATTERNS 更广——覆盖 code/、output/、reports/、模板名、脚本名。
CUMCM_INTERNAL_PATTERNS = [
    r"\bwork/", r"\b_tmp/", r"\bcode/", r"\boutput/", r"\breports/",
    r"figures/\S+\.json", r"all_results\.json",
    r"MODEL_SPEC\.md", r"CODE_DELIVERABLES\.md", r"PAPER_SPEC\.md",
    r"RESULTS_REPORT", r"ANALYSIS_MODELING_REPORT", r"PROBLEM_ANALYSIS",
    r"plan\.md", r"todo\.md", r"CLAUDE\.md", r"AGENTS\.md",
    r"references\.bib", r"main\.tex", r"\b\w+\.py\b",
]

# 国赛论文必备章节（6verity Step2）。每个条目给出若干可接受的关键词，命中其一即可。
CUMCM_REQUIRED_SECTIONS = [
    ("问题重述/分析", ["问题重述", "问题分析", "问题背景", "问题描述"]),
    ("模型假设", ["模型假设", "基本假设", "假设条件", "问题假设"]),
    ("符号说明", ["符号说明", "符号表", "符号定义", "符号约定"]),
    ("模型建立与求解", ["模型建立", "模型求解", "模型的建立", "模型构建",
                        "建模与求解", "模型构建与求解"]),
    ("模型评价/推广", ["模型评价", "评价与推广", "模型推广", "优缺点", "模型评估"]),
]

# 强烈建议项：缺失不阻塞（软失败），但会提示。
CUMCM_RECOMMENDED_SECTIONS = [
    ("结果分析与检验", ["结果分析", "结果检验", "模型检验", "结果验证", "结果对比"]),
    ("灵敏度分析", ["灵敏度", "敏感性"]),
]

# 门禁报告常见「占位符 | PASS | 无 TODO/FIXME/TBD」这类**描述检测规则自身**的文字。
# 直接扫描会把规则描述误判为违规——检测器命中了自己。
# 按行剔除：同行既含否定/规则词、又含占位符关键词的，视为规则描述行。
_NEGATION_CUES = ("无", "不含", "没有", "禁止", "检测", "检查", "排查", "扫描", "清理", "残留")
_PH_KEYWORDS = (
    r"TODO", r"FIXME", r"TBD", r"XXX", r"PLACEHOLDER",
    r"待补充", r"待续写", r"这里补", r"待完善", r"这里填写",
    r"示例数据", r"模板数据", r"\[待补\]", r"\[TBD\]",
)
_PH_KEYWORDS_RE = re.compile("|".join(_PH_KEYWORDS))


def strip_rule_descriptions(text):
    """剔除规则描述行，避免检测器自噬。"""
    kept = []
    for line in text.split("\n"):
        if any(cue in line for cue in _NEGATION_CUES) and _PH_KEYWORDS_RE.search(line):
            continue
        kept.append(line)
    return "\n".join(kept)

# 正文禁止的列表环境（铁律 W11，附录豁免）
BODY_LIST_ENVS = [r"\\begin\{itemize\}", r"\\begin\{enumerate\}"]


# ---------------------------------------------------------------- 基础工具
class Check:
    """单条门禁断言的结果。"""

    __slots__ = ("ok", "name", "detail", "hard")

    def __init__(self, ok, name, detail="", hard=True):
        self.ok = ok
        self.name = name
        self.detail = detail
        self.hard = hard

    def __repr__(self):
        tag = "PASS" if self.ok else ("FAIL" if self.hard else "WARN")
        return f"[{tag}] {self.name}" + (f" - {self.detail}" if self.detail else "")


def ok(name, detail=""):
    return Check(True, name, detail)


def fail(name, detail="", hard=True):
    return Check(False, name, detail, hard)


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def sha256(obj):
    if isinstance(obj, (str, bytes)):
        data = obj.encode("utf-8") if isinstance(obj, str) else obj
    else:
        data = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def project_dir(project):
    p = Path(project)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        p = ROOT / "projects" / project
    return p


# ---------------------------------------------------------------- 通用断言
def check_files_exist(project, rel_paths, label="产物"):
    """一组相对路径必须存在且非空。"""
    base = project_dir(project)
    missing = []
    empty = []
    for rel in rel_paths:
        f = base / rel
        if not f.exists():
            missing.append(rel)
        elif f.stat().st_size == 0:
            empty.append(rel)
    if missing:
        return fail(f"{label}存在性", f"缺失: {', '.join(missing)}")
    if empty:
        return fail(f"{label}非空", f"空文件: {', '.join(empty)}")
    return ok(f"{label}存在性", f"{len(rel_paths)} 个文件齐全")


def check_json_valid(project, rel_path, label=None):
    """JSON 产物可解析。"""
    base = project_dir(project)
    f = base / rel_path
    if not f.exists():
        return fail(label or f"{rel_path} 可解析", "文件不存在")
    try:
        json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        return fail(label or f"{rel_path} 可解析", f"JSON 解析失败: {e}")
    return ok(label or f"{rel_path} 可解析")


def check_guardrails(project, rel_paths, allow_internal=False):
    """运行时护栏 L5：禁用词 / 占位符 / 内部术语。

    allow_internal=True 用于中间产物（work/ 下的 JSON 允许提及内部路径）。
    """
    base = project_dir(project)
    hits = []
    for rel in rel_paths:
        text = read(base / rel)
        if text is None:
            continue
        # 先剔除「无 TODO/FIXME」这类规则描述，避免把检测报告自身判为违规
        text = strip_rule_descriptions(text)
        for w in FORBIDDEN_WORDS:
            if w in text:
                hits.append(f"{rel}: 禁用词「{w}」")
        for pat in FORBIDDEN_WORD_REGEXES:
            if re.search(pat, text):
                hits.append(f"{rel}: 禁用句式 /{pat}/")
        for pat in PLACEHOLDER_PATTERNS:
            if re.search(pat, text):
                hits.append(f"{rel}: 占位符 /{pat}/")
        if not allow_internal:
            for pat in INTERNAL_TERM_PATTERNS:
                if re.search(pat, text):
                    hits.append(f"{rel}: 内部术语 /{pat}/")
    if hits:
        return fail("运行时护栏", "; ".join(hits[:5]))
    return ok("运行时护栏", "无禁用词/占位符/内部术语")


def check_tex_no_lists(project, rel_path):
    """铁律 W11：论文正文禁止 itemize / enumerate。"""
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("正文禁列表", f"无法读取 {rel_path}", hard=False)
    found = []
    for pat in BODY_LIST_ENVS:
        n = len(re.findall(pat, text))
        if n:
            found.append(f"{pat}×{n}")
    if found:
        return fail("正文禁列表(W11)", f"{rel_path} 含列表环境: {', '.join(found)}")
    return ok("正文禁列表(W11)", "无 itemize/enumerate")


def check_min_count(project, rel_path, pattern, minimum, label):
    """按正则统计数量并比对下限。"""
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail(label, f"无法读取 {rel_path}", hard=False)
    n = len(re.findall(pattern, text))
    if n < minimum:
        return fail(label, f"{n} < {minimum}")
    return ok(label, f"{n} >= {minimum}")


def check_schema(project, rel_path, schema_rel):
    """用极简 JSON Schema 子集校验：required 字段 + 类型 + minItems。

    不引入 jsonschema 依赖，只实现本项目 schema 实际用到的关键字。
    """
    base = project_dir(project)
    data_f = base / rel_path
    sch_f = ROOT / schema_rel
    if not data_f.exists():
        return fail(f"Schema {schema_rel}", f"数据文件不存在: {rel_path}")
    if not sch_f.exists():
        return fail(f"Schema {schema_rel}", f"Schema 文件不存在", hard=False)
    try:
        data = json.loads(data_f.read_text(encoding="utf-8"))
        schema = json.loads(sch_f.read_text(encoding="utf-8"))
    except Exception as e:
        return fail(f"Schema {schema_rel}", f"解析失败: {e}")

    errors = _validate(data, schema, "$")
    if errors:
        return fail(f"Schema {schema_rel}", "; ".join(errors[:5]))
    return ok(f"Schema {schema_rel}", "符合契约")


def _validate(data, schema, path):
    errors = []
    st = schema.get("type")
    if st == "object" and not isinstance(data, dict):
        return [f"{path}: 应为 object"]
    if st == "array" and not isinstance(data, list):
        return [f"{path}: 应为 array"]

    if isinstance(data, dict):
        for req in schema.get("required", []):
            if req not in data:
                errors.append(f"{path}.{req}: 缺失必填字段")
        for key, sub in (schema.get("properties") or {}).items():
            if key in data:
                errors += _validate(data[key], sub, f"{path}.{key}")

    if isinstance(data, list):
        mi = schema.get("minItems")
        if mi is not None and len(data) < mi:
            errors.append(f"{path}: 元素数 {len(data)} < minItems {mi}")
        items = schema.get("items")
        if items:
            for i, item in enumerate(data):
                errors += _validate(item, items, f"{path}[{i}]")
    return errors

# ======================================================================
# 内容级校验（P2-9）：不只是"文件在不在"，而是"内容对不对"
# ======================================================================

def _tex_body(text):
    """取论文正文：跳过导言区、去注释、去数学环境。"""
    body = text.split(r"\begin{document}")[-1]
    body = re.sub(r"(?<!\\)%.*", "", body)
    body = re.sub(
        r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath)\*?\}.*?\\end\{\1\}",
        " ", body, flags=re.DOTALL)
    return body


def check_symbols_consistency(project, rel_path="paper/main.tex"):
    """符号表与正文一致性：正文用到的符号必须在符号表中定义。

    这是最常见的"看起来很专业、实际对不上"的问题。
    """
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("符号表一致性", f"无法读取 {rel_path}", hard=False)

    # 定位符号说明表（常见写法：\begin{table} 内含 符号 & 含义 & 单位）
    table_blocks = re.findall(r"\\begin\{table\}.*?\\end\{table\}", text, re.DOTALL)
    declared = set()
    for t in table_blocks:
        # 匹配 $xxx$ 或 \(xxx\) 形式的符号
        declared |= set(re.findall(r"\$([A-Za-z_][A-Za-z0-9_\\{}^]*)\$", t))
        declared |= set(re.findall(r"\\\\?\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\\\\?\)", t))

    if not declared:
        return fail("符号表一致性", "未找到符号说明表", hard=False)

    body = _tex_body(text)
    # 正文中出现的所有行内/行间公式符号
    used = set(re.findall(r"\$([A-Za-z_][A-Za-z0-9_]*)\$", body))
    used |= set(re.findall(r"\\?\\?\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\\?\\?\)", body))

    # 排除 LaTeX 常见命令名误匹配与单字母通用符号
    noise = {"t", "s", "m", "n", "i", "j", "k", "pi", "theta", "sum", "max", "min",
             "exp", "ln", "log", "sin", "cos", "tan", "lim", "arg", "det", "dim"}
    used = {u for u in used if u not in noise and len(u) >= 1}
    declared = {d for d in declared if d not in noise}

    missing = sorted(u for u in used if u not in declared)
    if missing and len(missing) > 12:
        # 注意：正文"随文说明"是合理的（符号表只列全局符号），
        # 因此这里只在脱节严重时才提示，且措辞为"确认"而非"失败"。
        return fail("符号表一致性",
                    f"{len(missing)} 个正文符号不在符号表中，请确认已随文说明；"
                    f"前几个: {', '.join(missing[:6])}",
                    hard=False)
    return ok("符号表一致性",
              f"符号表 {len(declared)} 项；{len(missing)} 个随文说明的符号（属正常）")


def check_assumptions_referenced(project, rel_path="paper/main.tex"):
    """假设必须被后文引用——写了不用的假设等于没写，反而暴露不严谨。"""
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("假设被引用", f"无法读取 {rel_path}", hard=False)

    body = _tex_body(text)
    # 抽取"假设一/假设二/假设 1"等编号
    ids = re.findall(r"假设\s*([一二三四五六七八九十\d]+)", body)
    if not ids:
        return fail("假设被引用", "正文未找到假设条目", hard=False)

    unused = []
    for a in set(ids):
        # 除定义处外，正文中是否再次出现（引用）
        cnt = len(re.findall(r"假设\s*%s" % re.escape(a), body))
        if cnt < 2:
            unused.append(f"假设{a}")
    if unused:
        return fail("假设被引用",
                    f"{len(unused)} 条假设定义后未被引用: {', '.join(sorted(unused)[:6])}",
                    hard=False)
    return ok("假设被引用", f"{len(set(ids))} 条假设均被后文引用")


def check_sensitivity_really_scanned(project, rel_path="paper/main.tex"):
    """灵敏度分析必须真的扫了参数——检查是否出现多组扰动取值。

    只写"本文做了灵敏度分析"而没有多组数值，是最典型的假分析。
    """
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("灵敏度真实性", f"无法读取 {rel_path}", hard=False)

    body = _tex_body(text)
    idx = body.find("灵敏度")
    if idx < 0:
        return fail("灵敏度真实性", "正文未找到灵敏度分析章节", hard=False)

    seg = body[idx:idx + 6000]
    # 统计扰动幅度表述。注意 LaTeX 中百分号必须转义为 \%，
    # 且正负号常写成 \pm 命令——早期正则未考虑这两点，导致全部漏判。
    pct = re.findall(r"(?:±|\\pm|\\mp|[+-])\s*(\d+(?:\.\d+)?)\s*\\?%", seg)
    if len(set(pct)) < 2:
        return fail("灵敏度真实性",
                    f"扰动取值仅 {len(set(pct))} 种，灵敏度分析可能流于形式",
                    hard=False)
    return ok("灵敏度真实性", f"检测到 {len(set(pct))} 种扰动幅度")


def check_figures_referenced(project, rel_path="paper/main.tex"):
    """每张图都必须被正文提到——未被引用的图等于白占版面。

    两种合规引用方式都接受：
    1. LaTeX 交叉引用 \\ref{fig:x}
    2. 中文括号旁注（图N）—— 这是本项目的**规范写法**
       （铁律 W12 禁止以图表做主语开头，要求用括号旁注）

    早期版本只认 \\ref，导致对规范写法大量假阳性。
    """
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("图表被引用", f"无法读取 {rel_path}", hard=False)

    labels = re.findall(r"\\label\{fig:([^}]+)\}", text)
    if not labels:
        return fail("图表被引用", "未找到 fig 标签", hard=False)

    body = _tex_body(text)
    refs = set(re.findall(r"\\ref\{fig:([^}]+)\}", text))

    # 中文旁注：（图N）／（图N、图M）／（图N,M）
    # 注意"图"字会在多图旁注中重复出现（如"图5、图6"），
    # 因此先整体捕获括号内容再提取其中所有数字。
    noted = set()
    for m in re.finditer(r"（图[^）]*）", body):
        for n in re.findall(r"\d+", m.group(0)):
            noted.add(int(n))

    # 图号按 \label 在文中出现的先后顺序确定
    orphan = []
    for idx, lab in enumerate(labels, 1):
        if lab in refs:
            continue
        if idx in noted:
            continue
        orphan.append(f"图{idx}({lab})")

    if orphan:
        return fail("图表被引用",
                    f"{len(orphan)} 张图正文未提到（既无 \\ref 也无（图N）旁注）: "
                    f"{', '.join(orphan[:5])}",
                    hard=False)
    return ok("图表被引用",
              f"{len(labels)} 张图均被正文提到（\\ref {len(refs)} + 旁注 {len(noted)}）")


def check_rubric_alignment(project):
    """P2-7：评分点对齐文件存在且已核销。"""
    f = project_dir(project) / "work" / "rubric_alignment.json"
    if not f.exists():
        return fail("评分点对齐",
                    "无 work/rubric_alignment.json（由 structure-planner 产出）",
                    hard=False)
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        return fail("评分点对齐", f"解析失败: {e}", hard=False)
    items = data.get("items", [])
    if not items:
        return fail("评分点对齐", "评分点清单为空", hard=False)
    unmapped = [i.get("id") for i in items if not i.get("section")]
    if unmapped:
        return fail("评分点对齐",
                    f"{len(unmapped)} 个评分点未映射到论文章节: {unmapped[:5]}",
                    hard=False)
    return ok("评分点对齐", f"{len(items)} 个评分点已全部映射到章节")


def check_risk_probe(project):
    """P2-3：编码前风险探针已完成。

    探针在 method-matcher 阶段执行，目的是在投入编码前暴露
    方法不可行（假设不成立、数据不覆盖、输出退化、规模超预算）。
    """
    f = project_dir(project) / "work" / "risk_probe.json"
    if not f.exists():
        return fail("风险探针",
                    "无 work/risk_probe.json —— 编码前必须完成风险探针",
                    hard=True)
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        return fail("风险探针", f"解析失败: {e}")
    verdict = str(data.get("verdict", "")).lower()
    if verdict not in ("pass", "pass_with_watch"):
        return fail("风险探针",
                    f"探针结论为 {verdict or '空'}，须更换候选模型后再进入编码")
    checks = data.get("checks", [])
    if len(checks) < 5:
        return fail("风险探针",
                    f"探针仅覆盖 {len(checks)} 项，应至少 5 项"
                    "（假设/数据覆盖/输出退化/扰动敏感/规模可行性）")
    return ok("风险探针",
              f"{verdict}，覆盖 {len(checks)} 项")


# ======================================================================
# 国赛验收（目标 A）—— 固化 6verity 的硬性检查为可执行断言
# ======================================================================

def check_cumcm_placeholders(project, rel_path="paper/main.tex"):
    """国赛验收（6verity Step4）：占位符清零。

    论文正文不得残留 TODO / FIXME / TBD / 待补充 / 示例数据 等占位符。
    占位符暴露论文未完成，属硬错误。
    """
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("占位符清零", f"无法读取 {rel_path}", hard=False)
    text = strip_rule_descriptions(text)
    hits = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for pat in PLACEHOLDER_PATTERNS:
            m = re.search(pat, line)
            if m:
                hits.append(f"L{lineno}:{m.group(0)}")
    if hits:
        return fail("占位符清零",
                    f"残留 {len(hits)} 处: {', '.join(hits[:5])}")
    return ok("占位符清零", "无 TODO/PLACEHOLDER/待补充/示例数据")


def check_cumcm_internal_leaks(project, rel_path="paper/main.tex"):
    """国赛验收（6verity Step4）：内部文件泄露。

    论文正文不得出现工作流内部文件名/路径（work/、code/、output/、
    figures/*.json、结果 JSON、报告名、模板名、脚本名等）。
    """
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("内部路径泄露", f"无法读取 {rel_path}", hard=False)
    hits = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for pat in CUMCM_INTERNAL_PATTERNS:
            m = re.search(pat, line)
            if m:
                hits.append(f"L{lineno}:{m.group(0)}")
    if hits:
        return fail("内部路径泄露",
                    f"泄露 {len(hits)} 处: {', '.join(hits[:5])}")
    return ok("内部路径泄露", "无 work/、code/、figures/*.json 等内部路径")


def check_cumcm_section_structure(project, rel_path="paper/main.tex"):
    """国赛验收（6verity Step2）：论文章节结构。

    国赛论文须具备：摘要、问题重述/分析、模型假设、符号说明、
    模型建立与求解、模型评价、参考文献。
    结果分析与检验、灵敏度分析为强烈建议项（缺失软失败）。
    """
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("国赛章节结构", f"无法读取 {rel_path}", hard=False)

    titles = " ".join(re.findall(
        r"\\(?:section|subsection)\*?\{([^}]*)\}", text))

    missing_req = [label for label, kws in CUMCM_REQUIRED_SECTIONS
                   if not any(k in titles for k in kws)]
    missing_rec = [label for label, kws in CUMCM_RECOMMENDED_SECTIONS
                   if not any(k in titles for k in kws)]

    problems = []
    if not re.search(r"\\begin\{abstract\}|摘\s*要", text):
        problems.append("摘要")
    if not re.search(r"参考文献|\\bibliography|\\begin\{thebibliography\}", text):
        problems.append("参考文献")
    problems += missing_req

    if problems:
        return fail("国赛章节结构", f"缺失核心章节: {', '.join(problems)}")

    if missing_rec:
        return fail("国赛章节结构",
                    f"核心章节齐全；建议补充: {', '.join(missing_rec)}",
                    hard=False)
    return ok("国赛章节结构", "摘要/问题/假设/符号/建模求解/评价/参考文献 齐全")


# ======================================================================
# 国赛官方披露合规（P2-1 / 目标 A）—— CUMCM 2025 硬性要求
# 1) 正文须含 AI 使用声明（且不在附录）
# 2) 支撑材料须有「AI工具使用详情」(.tex 必备，.pdf 力争)
# 3) 正文应提及该支撑材料便于评委定位
# 4) 参考文献必须正文内联引用（不得只在文末堆砌）
# ======================================================================

def _ai_report_name():
    """支撑材料文件名，取自 env: deliverables.ai_report_name（可插拔）。"""
    try:
        import sys as _s
        _s.path.insert(0, str(ROOT / "core"))
        from env.loader import get
        return str(get("deliverables.ai_report_name", default="AI工具使用详情")
                   or "AI工具使用详情")
    except Exception:
        return "AI工具使用详情"


def _competition():
    """从 env profile 推导赛事简称（如 cumcm-2025 -> cumcm）。"""
    try:
        import sys as _s
        _s.path.insert(0, str(ROOT / "core"))
        from env.loader import get
        prof = str(get("profile", default="") or "")
        return prof.split("-")[0]
    except Exception:
        return ""


def check_cumcm_ai_disclosure_body(project, rel_path="paper/main.tex"):
    """国赛验收：正文（附录之前）须含 AI 使用声明。

    CUMCM 2025 要求 AI 使用情况在**正文**声明，不能只在附录。
    若把声明写在附录里，此处判 HARD——索引到附录之前的内容即可。
    非国赛（mcm/huawei/...）无此硬性要求，跳过以免阻塞。
    """
    if _competition() != "cumcm":
        return ok("AI披露-正文声明", "非国赛，跳过")
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("AI披露-正文声明", f"无法读取 {rel_path}", hard=False)
    body = text.split(r"\begin{document}")[-1]
    # 定位附录起点：\begin{appendix} 或 \appendix 命令
    ai = body.find(r"\begin{appendix}")
    if ai < 0:
        ai = body.find(r"\appendix")
    if ai < 0:
        ai = len(body)
    pre = body[:ai]
    patterns = ["AI 工具", "AI工具", "人工智能工具", "人工智能辅助",
                "AI 使用", "AI使用", "生成式人工智能", "大语言模型"]
    if not any(p in pre for p in patterns):
        return fail("AI披露-正文声明",
                    "正文（附录之前）未找到 AI 使用声明，国赛要求正文须声明 AI 使用情况")
    return ok("AI披露-正文声明", "正文含 AI 使用声明（位于附录之前）")


def check_cumcm_ai_support(project):
    """国赛验收：支撑材料「AI工具使用详情」(.tex 必备；.pdf 力争)。

    落在 deliverables/（投稿交付物目录，见 REFACTOR_PLAN §6.2）。
    .tex 由 render_ai_usage.py 必然生成，故缺失即 HARD；
    .pdf 依赖 xelatex 环境，缺失仅 SOFT（评委处可编译）。
    非国赛跳过。
    """
    if _competition() != "cumcm":
        return ok("AI披露-支撑材料", "非国赛，跳过")
    name = _ai_report_name()
    base = project_dir(project) / "deliverables"
    tex = base / f"{name}.tex"
    pdf = base / f"{name}.pdf"
    if not tex.exists() and not pdf.exists():
        return fail("AI披露-支撑材料",
                    f"缺少 {name}.tex / .pdf（先运行 render_ai_usage.py render --competition cumcm）")
    if not pdf.exists():
        return fail("AI披露-支撑材料",
                    f"{name}.pdf 未生成（需 xelatex 编译；.tex 已存在，不阻塞）",
                    hard=False)
    return ok("AI披露-支撑材料", f"{name}.pdf 存在")


def check_cumcm_ai_referenced(project, rel_path="paper/main.tex"):
    """国赛验收：正文应提及支撑材料，便于评委定位（软失败）。非国赛跳过。"""
    if _competition() != "cumcm":
        return ok("AI披露-正文提及", "非国赛，跳过")
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("AI披露-正文提及", f"无法读取 {rel_path}", hard=False)
    name = _ai_report_name()
    if name in text or "AI工具使用详情" in text or r"\input{" in text:
        return ok("AI披露-正文提及", "正文提及 AI 使用支撑材料")
    return fail("AI披露-正文提及",
                "正文未提及 AI 使用支撑材料（建议在正文或参考文献处标注其存在）",
                hard=False)


def check_cumcm_inline_citation(project, rel_path="paper/main.tex"):
    r"""国赛验收：参考文献必须正文内联引用（不得只在文末堆砌）。

    取 references.bib 的全部 @type{key}，核对正文 \cite/\citep/\citet 等
    是否逐条引用；存在未被引用的孤儿文献即 HARD。
    """
    text = read(project_dir(project) / rel_path)
    if text is None:
        return fail("内联引用", f"无法读取 {rel_path}", hard=False)
    bib = project_dir(project) / "paper" / "references.bib"
    bib_keys = set()
    if bib.exists():
        try:
            bib_keys = set(re.findall(
                r"@\w+\{(\w[\w-]*)", bib.read_text(encoding="utf-8", errors="replace")))
        except Exception:
            pass
    body = text.split(r"\begin{document}")[-1]
    cited = re.findall(r"\\(?:cite|citep|citet|autocite|textcite|nocite)\*?\{([^}]*)\}",
                       body)
    cited_keys = set()
    for grp in cited:
        cited_keys |= {k.strip() for k in grp.split(",") if k.strip()}
    if bib_keys and not cited_keys:
        return fail("内联引用", "references.bib 有条目但正文无任何 \\cite 引用")
    orphan = bib_keys - cited_keys
    if orphan:
        return fail("内联引用",
                    f"{len(orphan)} 条参考文献未被正文引用: "
                    f"{', '.join(sorted(orphan)[:6])}")
    return ok("内联引用", f"全部 {len(bib_keys)} 条参考文献均被正文引用")
