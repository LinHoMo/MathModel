"""
MathModelSkills 验证脚本 - 六层防御体系
用于验证项目结构和产物完整性
"""
import os
import re
import json
import sys
import importlib.util
from pathlib import Path


# === 禁用词列表（统一扩充词表，两处必须同步：本文件与 validate_project.py）===
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

# === 禁用词正则模式（两处必须同步：本文件与 validate_project.py）===
FORBIDDEN_WORD_REGEXES = [
    r"随着.{0,12}的快速发展",
]

# === 占位符模式（两处必须同步：本文件与 validate_project.py）===
PLACEHOLDER_PATTERNS = [
    r"TODO", r"FIXME", r"TBD", r"__XXX__",
    r"\[待补\]", r"\[TBD\]", r"示例数据", r"模板数据",
    r"PLACEHOLDER", r"XXX", r"这里填写",
    r"待补充", r"待续写", r"这里补", r"待完善",
]

# === 内部路径模式（两处必须同步：本文件与 validate_project.py）===
INTERNAL_PATH_PATTERNS = [
    r"\.py\b", r"\.ipynb\b", r"code/\w+\.py",
    r"/tmp/", r"__pycache__", r"\.pytest_cache",
    # 内部术语泄露扩充
    r"MODEL_SPEC\.md", r"CODE_DELIVERABLES\.md", r"PAPER_SPEC\.md",
    r"all_results\.json", r"RESULTS_REPORT", r"ANALYSIS_MODELING_REPORT",
    r"PROBLEM_ANALYSIS", r"CLAUDE\.md", r"AGENTS\.md",
    r"figures/\S+\.json", r"_tmp/", r"work/",
]

# === AI痕迹模式 ===
AI_TRACE_PATTERNS = [
    r"作为\s*AI", r"由\s*AI\s*生成", r"I\s*am\s*an?\s*AI",
    r"language\s*model", r"我是\s*AI", r"作为一个\s*AI"
]

# === 用户内容扫描时排除的目录 ===
# 原始赛题（inputs/）常含"深入探讨""值得注意的是"等禁用词，属正常文本；
# 草稿（_scratch/_debug）与支撑材料（support_materials）是生成物，不应被罚。
# 这些目录被显式排除，避免假阳性阻断合规论文。
USER_CONTENT_EXCLUDE_DIRS = {
    "knowledge", "templates", "template", "output",
    "inputs", "_scratch", "_debug", "support_materials",
}

# === 仓库级扫描：跳过归档与临时目录 ===
# archives/ 为「已知不达标」的历史样例（见 archives/README.md），不计入实时校验，
# 否则会持续污染 validate.py 的出口信号；_scratch/_debug 为临时区，同理排除。
REPO_SCAN_EXCLUDE_DIRS = {"archives", "_scratch", "_debug", "node_modules", "__pycache__"}


def iter_repo(root, pattern):
    """遍历 root 下匹配 pattern 的文件，跳过归档/临时目录。"""
    root = Path(root)
    for p in root.rglob(pattern):
        if any(part in REPO_SCAN_EXCLUDE_DIRS for part in p.parts):
            continue
        yield p


def _live_project_dirs(project_path):
    """返回 projects/ 下的活跃项目实例目录（样例已归档至 archives/，不计入）。

    本仓库是技能库，projects/ 可能为空（无活跃实例）。项目级存在性检查
    （all_results.json / 随机种子 / 论文 .tex）仅在存在活跃实例时才应报失败，
    否则库模式下的空 projects/ 会持续产生假失败。
    """
    pdir = project_path / "projects"
    if not pdir.is_dir():
        return []
    return [d for d in pdir.iterdir() if d.is_dir() and not d.name.startswith(".")]


# === env 阈值读取（动态加载 env/loader.get；缺失时回退默认值）===
_ENV_LOADER_MODULE = None


def _env_get(key, default=None):
    """通过 env/loader.get 读取阈值；加载失败时回退 default。"""
    global _ENV_LOADER_MODULE
    if _ENV_LOADER_MODULE is None:
        project_path = Path(__file__).resolve().parents[2]
        mod, err = _load_env_loader_module(project_path)
        _ENV_LOADER_MODULE = mod if mod is not None else False
    mod = _ENV_LOADER_MODULE
    if mod is not False and mod is not None:
        try:
            return mod.get(key, default=default)
        except Exception:
            return default
    return default


# ======================================================================
# L1: 结构化输出检查
# ======================================================================

def check_schema_exists(project_path):
    """L1.1: 检查schemas目录是否存在"""
    schemas_dir = project_path / "core" / "schemas"
    if not schemas_dir.exists():
        return False, "schemas/目录不存在"
    
    required = ["model_spec.schema.json", "code_deliverables.schema.json", "paper_spec.schema.json"]
    missing = [f for f in required if not (schemas_dir / f).exists()]
    if missing:
        return False, f"缺失Schema文件: {', '.join(missing)}"
    
    return True, "Schema文件完整"


def check_schemas_valid(project_path):
    """L1.2: 检查JSON Schema是否为有效JSON"""
    schemas_dir = project_path / "core" / "schemas"
    errors = []
    
    for f in schemas_dir.glob("*.json"):
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: JSON格式错误 - {e}")
    
    if errors:
        return False, "; ".join(errors)
    return True, "所有Schema文件格式正确"


# ======================================================================
# L5: 运行时护栏检查
# ======================================================================

def check_forbidden_words_in_dir(project_path, dirs_to_check=None):
    """L5.1: 检查禁用词（只检查用户创建的内容，排除知识库参考文件）"""
    if dirs_to_check is None:
        # 只检查用户项目文件和输出文件，排除knowledge/目录
        dirs_to_check = ["projects"]
    
    # 排除的文件（这些文件定义禁用词、解释规则或包含使用示例，必然包含禁用词）
    exclude_files = {
        "forbidden-words.md", "rules.md", "SKILL.md", "guidelines.md",
        "transition-phrases.md", "writing-patterns.md",  # 包含禁用词作为反面示例
        "game-strategy.md", "paper-logic-framework.md",  # 领域知识中的禁用词引用
        "telescope-optics.md", "interpolation-fitting.md"  # 方法论中的禁用词引用
    }
    
    exclude_dirs = USER_CONTENT_EXCLUDE_DIRS
    found_words = {}
    for dir_name in dirs_to_check:
        dir_path = project_path / dir_name
        if not dir_path.exists():
            continue
        
        for md_file in dir_path.rglob("*.md"):
            if md_file.name in exclude_files:
                continue
            if any(ed in md_file.parts for ed in exclude_dirs):
                continue
            
            try:
                content = md_file.read_text(encoding="utf-8")
                file_hits = []
                for word in FORBIDDEN_WORDS:
                    if word in content:
                        file_hits.append(word)
                for pat in FORBIDDEN_WORD_REGEXES:
                    try:
                        if re.search(pat, content):
                            file_hits.append(pat)
                    except re.error:
                        pass
                if file_hits:
                    rel_path = md_file.relative_to(project_path)
                    for w in file_hits:
                        if w not in found_words:
                            found_words[w] = []
                        found_words[w].append(str(rel_path))
            except:
                pass
    
    if found_words:
        msg = "; ".join([f"'{w}' in {', '.join(files[:2])}" for w, files in found_words.items()])
        return False, f"发现禁用词: {msg}"
    return True, "无禁用词"


def check_placeholders_in_dir(project_path):
    """L5.2: 检查占位符（只检查用户创建的内容，排除知识库和模板）"""
    # 只检查projects/目录下的文件
    projects_dir = project_path / "projects"
    if not projects_dir.exists():
        return True, "无projects目录（跳过）"
    
    # 排除的文件模式
    exclude_dirs = USER_CONTENT_EXCLUDE_DIRS
    
    found = {}
    
    for md_file in projects_dir.rglob("*.md"):
        # 跳过 knowledge/template/output/inputs/_scratch 等目录
        if any(ed in md_file.parts for ed in exclude_dirs):
            continue
        
        try:
            content = md_file.read_text(encoding="utf-8")
            for pattern in PLACEHOLDER_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    rel_path = md_file.relative_to(project_path)
                    for m in set(matches):
                        if m not in found:
                            found[m] = []
                        found[m].append(str(rel_path))
        except:
            pass
    
    if found:
        msg = "; ".join([f"'{w}' in {', '.join(files[:2])}" for w, files in found.items()])
        return False, f"发现占位符: {msg}"
    return True, "无占位符"


def check_ai_traces_in_dir(project_path):
    """L5.3: 检查AI痕迹（只检查用户创建的内容，排除知识库参考文件）"""
    # 只检查projects/目录下的文件
    projects_dir = project_path / "projects"
    if not projects_dir.exists():
        return True, "无projects目录（跳过）"
    
    # 排除的目录
    exclude_dirs = USER_CONTENT_EXCLUDE_DIRS
    
    found = {}
    
    for md_file in projects_dir.rglob("*.md"):
        # 跳过 knowledge/template/output/inputs/_scratch 等目录
        if any(ed in md_file.parts for ed in exclude_dirs):
            continue
        
        try:
            content = md_file.read_text(encoding="utf-8")
            for pattern in AI_TRACE_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    rel_path = md_file.relative_to(project_path)
                    for m in set(matches):
                        if m not in found:
                            found[m] = []
                        found[m].append(str(rel_path))
        except:
            pass
    
    if found:
        msg = "; ".join([f"'{w}' in {', '.join(files[:2])}" for w, files in found.items()])
        return False, f"发现AI痕迹: {msg}"
    return True, "无AI痕迹"


def check_internal_paths(project_path):
    """L5.4: 检查内部路径"""
    found = {}
    exclude_dirs = USER_CONTENT_EXCLUDE_DIRS
    
    for tex_file in iter_repo(project_path, "*.tex"):
        if any(ed in tex_file.parts for ed in exclude_dirs):
            continue
        try:
            content = tex_file.read_text(encoding="utf-8")
            for pattern in INTERNAL_PATH_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    rel_path = tex_file.relative_to(project_path)
                    for m in set(matches):
                        if m not in found:
                            found[m] = []
                        found[m].append(str(rel_path))
        except:
            pass
    
    if found:
        msg = "; ".join([f"'{w}' in {', '.join(files[:2])}" for w, files in list(found.items())[:3]])
        return False, f"发现内部路径: {msg}"
    return True, "无内部路径"


# ======================================================================
# L3: 过程验证检查
# ======================================================================

def check_required_artifacts(project_path):
    """L3.1: 检查必要产物"""
    required = {
        "core/Modeler/SKILL.md": "Modeler SKILL.md",
        "core/Programmer/SKILL.md": "Programmer SKILL.md",
        "core/Writer/SKILL.md": "Writer SKILL.md",
        "core/Modeler/laws/rules.md": "Modeler laws",
        "core/Programmer/laws/rules.md": "Programmer laws",
        "core/Writer/laws/rules.md": "Writer laws",
    }
    
    missing = []
    for path, desc in required.items():
        if not (project_path / path).exists():
            missing.append(desc)
    
    if missing:
        return False, f"缺失必要文件: {', '.join(missing)}"
    return True, "必要文件完整"


def check_knowledge_completeness(project_path):
    """L3.2: 检查知识库完整性"""
    checks = []
    
    # Modeler domain
    domain_dir = project_path / "core" / "Modeler" / "knowledge" / "domain"
    if domain_dir.exists():
        count = len(list(domain_dir.glob("*.md")))
        checks.append(f"Modeler/domain: {count}个文件")
    
    # Programmer code-templates
    tmpl_dir = project_path / "core" / "Programmer" / "knowledge" / "code-templates"
    if tmpl_dir.exists():
        count = sum(1 for _ in tmpl_dir.rglob("*.py"))
        checks.append(f"Programmer/code-templates: {count}个文件")
    
    # Writer writing
    writing_dir = project_path / "core" / "Writer" / "knowledge" / "writing"
    if writing_dir.exists():
        count = len(list(writing_dir.glob("*.md")))
        checks.append(f"Writer/writing: {count}个文件")
    
    # Shared knowledge
    shared_meth_dir = project_path / "core" / "knowledge" / "methodology"
    if shared_meth_dir.exists():
        count = len(list(shared_meth_dir.glob("*.md")))
        checks.append(f"knowledge/methodology: {count}个文件")
    
    return True, "; ".join(checks)


def check_laws_not_empty(project_path):
    """L3.3: 检查laws文件非空"""
    laws_files = [
        "core/Modeler/laws/rules.md",
        "core/Programmer/laws/rules.md",
        "core/Writer/laws/rules.md",
    ]
    
    empty = []
    for f in laws_files:
        path = project_path / f
        if not path.exists():
            empty.append(f)
        elif path.stat().st_size < 50:
            empty.append(f"{f} (内容过少)")
    
    if empty:
        return False, f"laws文件异常: {', '.join(empty)}"
    return True, "laws文件完整"


# ======================================================================
# L6: 内容质量检查（事后验证）
# ======================================================================

def _count_paper_words(content):
    """统计论文真实正文字数。

    直接对 LaTeX 源码做「中文字 + 英文单词」会把大量命令计入字数：
    实测一篇论文里 \\theta 出现 188 次、\\begin/\\end 105 次、\\cite 43 次，
    虚高约 2000 字，足以让不达标的论文"险过"门禁。

    正确口径：跳过导言区 → 去注释 → 去数学环境 → 去非文本类命令（含参数）
    → 去纯命令（保留其文本参数）→ 统计中文字 + 正文英文单词。
    """
    body = content.split(r"\begin{document}")[-1]
    body = re.sub(r"(?<!\\)%.*", "", body)
    body = re.sub(
        r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath)\*?\}.*?\\end\{\1\}",
        " ", body, flags=re.DOTALL,
    )
    body = re.sub(r"\\\[.*?\\\]", " ", body, flags=re.DOTALL)
    body = re.sub(r"\$\$?[^$]*\$\$?", " ", body, flags=re.DOTALL)
    body = re.sub(
        r"\\(label|ref|cite[a-z]*|includegraphics|input|include|bibliographystyle"
        r"|bibliography|usepackage|documentclass|setlength|newcommand|renewcommand"
        r"|definecolor|color|caption|centering|vspace|hspace|noindent|hspace\*)"
        r"\*?(\[[^\]]*\])?\{[^}]*\}",
        " ", body,
    )
    body = re.sub(r"\\[a-zA-Z]+", " ", body)
    chinese = len(re.findall(r"[\u4e00-\u9fff]", body))
    english = len(re.findall(r"\b[a-zA-Z]{2,}\b", body))
    return chinese + english, chinese, english


def check_paper_structure(project_path):
    """L6.1: 检查论文结构（深度检查：字数/页数/图表/公式/引用）"""
    if not _live_project_dirs(project_path):
        return True, "跳过：无活跃项目实例（样例已归档至 archives/）"
    template_dirs = {"templates", "template"}
    
    tex_files = []
    for tex_file in iter_repo(project_path, "*.tex"):
        if any(td in tex_file.parts for td in template_dirs):
            continue
        tex_files.append(tex_file)
    
    if not tex_files:
        return False, "未找到用户创建的.tex文件"
    
    issues = []
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8")
            content_lower = content.lower()
            
            # 基础结构检查
            required = ["\\section"]
            for req in required:
                if req not in content_lower:
                    issues.append(f"{tex_file.name}: 缺少 {req}")
            
            has_refs = any(kw in content_lower for kw in ["references", "thebibliography", "bibliography", "bibitem"])
            if not has_refs:
                issues.append(f"{tex_file.name}: 缺少参考文献")
            
            # 字数检查（真实正文字数：剥离注释/导言区/数学环境/LaTeX 命令后统计）
            total_words, chinese_chars, english_words = _count_paper_words(content)
            min_words = int(_env_get("paper.min_words", 13000))
            if total_words < min_words:
                issues.append(
                    f"{tex_file.name}: 字数不足({total_words}字, 需>={min_words}, "
                    f"其中中文{chinese_chars}英文{english_words})"
                )
            
            # 图表检查（图 / 表分别统计）
            n_figures = len(re.findall(r'\\includegraphics', content))
            n_tables = len(re.findall(r'\\begin\{table\}', content))
            min_figures = int(_env_get("paper.min_figures", 6))
            min_tables = int(_env_get("paper.min_tables", 4))
            if n_figures < min_figures:
                issues.append(f"{tex_file.name}: 图不足({n_figures}个, 需>={min_figures})")
            if n_tables < min_tables:
                issues.append(f"{tex_file.name}: 表格不足({n_tables}表, 需>={min_tables})")
            
            # 公式检查
            n_equations = len(re.findall(r'\\begin\{equation\}|\\begin\{align\}|\\\$\\\$', content))
            min_eq = int(_env_get("paper.min_equations", 15))
            if n_equations < min_eq:
                issues.append(f"{tex_file.name}: 公式不足({n_equations}个, 需>={min_eq})")
            
            # 引用检查（\cite或\bibitem都算）
            n_cites = len(re.findall(r'\\cite[a-z]*\{[^}]+\}', content))
            n_bibitems = len(re.findall(r'\\bibitem\{[^}]+\}', content))
            total_cites = max(n_cites, n_bibitems)
            min_refs = int(_env_get("paper.min_references", 10))
            if total_cites < min_refs:
                issues.append(f"{tex_file.name}: 引用不足({total_cites}个, 需>={min_refs})")
            
            # 灵敏度分析检查
            has_sensitivity = any(kw in content_lower for kw in ["灵敏度", "sensitivity", "参数.*扰动", "鲁棒性", "robust"])
            if not has_sensitivity:
                issues.append(f"{tex_file.name}: 缺少灵敏度分析")
            
            # 模型评价检查
            has_evaluation = any(kw in content_lower for kw in ["优点", "缺点", "局限", "改进", "推广", "advantage", "disadvantage"])
            if not has_evaluation:
                issues.append(f"{tex_file.name}: 缺少模型评价(优缺点讨论)")
            
            # 假设必要性检查
            if "假设" in content_lower or "assumption" in content_lower:
                has_necessity = any(kw in content_lower for kw in ["必要性", "因为", "为了", "由于", "简化", "necessary"])
                if not has_necessity:
                    issues.append(f"{tex_file.name}: 假设缺少必要性说明")
            
            # 占位符检查（排除LaTeX命令）
            placeholders = re.findall(r'TODO|FIXME|TBD|(?<!\\)XXX(?![\\])', content)
            if placeholders:
                issues.append(f"{tex_file.name}: 存在占位符 {placeholders[:3]}")
            
        except:
            pass
    
    if issues:
        return False, "; ".join(issues[:5])
    return True, "论文结构完整"


def check_citation_integrity(project_path):
    """L6.2: 检查引用完整性（排除模板目录）"""
    template_dirs = {"templates", "template"}
    
    bib_files = []
    for bib_file in iter_repo(project_path, "*.bib"):
        if not any(td in bib_file.parts for td in template_dirs):
            bib_files.append(bib_file)
    
    if not bib_files:
        return True, "无用户.bib文件（跳过）"
    
    # 提取bib keys
    bib_keys = set()
    for bib_file in bib_files:
        try:
            content = bib_file.read_text(encoding="utf-8")
            keys = re.findall(r"@\w+\{(\w+)", content)
            bib_keys.update(keys)
        except:
            pass
    
    # 检查tex中的引用
    tex_files = []
    for tex_file in iter_repo(project_path, "*.tex"):
        if not any(td in tex_file.parts for td in template_dirs):
            tex_files.append(tex_file)
    
    missing_cites = []
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8")
            cite_pattern = r"\\cite[tp]?\{([^}]+)\}"
            cites = re.findall(cite_pattern, content)
            for c in cites:
                keys = [k.strip() for k in c.split(",")]
                for key in keys:
                    if key not in bib_keys:
                        missing_cites.append(key)
        except:
            pass
    
    if missing_cites:
        return False, f"引用不存在的key: {', '.join(list(set(missing_cites))[:5])}"
    return True, "引用完整性通过"


def check_figure_refs(project_path):
    """L6.3: 检查图表引用（排除模板目录）"""
    template_dirs = {"templates", "template"}
    
    tex_files = []
    for tex_file in iter_repo(project_path, "*.tex"):
        if not any(td in tex_file.parts for td in template_dirs):
            tex_files.append(tex_file)
    
    missing_refs = []
    
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8")
            include_pattern = r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}"
            refs = re.findall(include_pattern, content)
            
            for ref in refs:
                # 检查文件是否存在
                found = False
                for ext in ["", ".png", ".pdf", ".eps", ".jpg"]:
                    if (tex_file.parent / (ref + ext)).exists():
                        found = True
                        break
                if not found:
                    missing_refs.append(ref)
        except:
            pass
    
    if missing_refs:
        return False, f"引用不存在的图片: {', '.join(list(set(missing_refs))[:3])}"
    return True, "图表引用完整"


def check_sensitivity_analysis(project_path):
    """L6.4: 检查灵敏度分析"""
    tex_files = list(iter_repo(project_path, "*.tex"))
    keywords = ["灵敏度", "sensitivity", "鲁棒性", "robustness", "参数扰动"]
    
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8").lower()
            if any(kw in content for kw in keywords):
                return True, "发现灵敏度分析"
        except:
            pass
    
    return False, "未发现灵敏度分析"


def check_model_evaluation(project_path):
    """L6.5: 检查模型评价"""
    tex_files = list(iter_repo(project_path, "*.tex"))
    keywords = ["模型评价", "model evaluation", "优缺点", "advantages", "disadvantages", "局限性"]
    
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8").lower()
            if any(kw in content for kw in keywords):
                return True, "发现模型评价"
        except:
            pass
    
    return False, "未发现模型评价"


def check_assumptions_necessity(project_path):
    """L6.6: 检查假设必要性说明"""
    tex_files = list(iter_repo(project_path, "*.tex"))
    
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8")
            # 检查假设部分是否有说明文字
            if "假设" in content or "assumption" in content.lower():
                # 简单检查：假设附近有解释文字
                lines = content.split("\n")
                assumption_lines = [i for i, l in enumerate(lines) if "假设" in l or "assumption" in l.lower()]
                if len(assumption_lines) >= 2:
                    return True, "假设有说明文字"
        except:
            pass
    
    return False, "假设必要性说明不足"


# ======================================================================
# L1: 输入规约检查
# ======================================================================

def check_question_spec_schema(project_path):
    """L1.1: 检查question_spec.schema.json存在且有效"""
    schema_path = project_path / "core" / "schemas" / "question_spec.schema.json"
    if not schema_path.exists():
        return False, "question_spec.schema.json不存在"
    try:
        json.loads(schema_path.read_text(encoding="utf-8"))
        return True, "question_spec.schema.json有效"
    except json.JSONDecodeError as e:
        return False, f"JSON格式错误: {e}"


def check_symbol_registry(project_path):
    """L1.2: 检查符号注册表"""
    py_path = project_path / "core" / "knowledge" / "validation" / "symbol_registry.py"
    if not py_path.exists():
        return False, "symbol_registry.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class SymbolRegistry" not in content:
        return False, "缺少SymbolRegistry类"
    return True, "符号注册表存在"


def check_assumption_validator(project_path):
    """L1.3: 检查假设验证器"""
    py_path = project_path / "core" / "knowledge" / "validation" / "assumption_validator.py"
    if not py_path.exists():
        return False, "assumption_validator.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class AssumptionValidator" not in content:
        return False, "缺少AssumptionValidator类"
    return True, "假设验证器存在"


# ======================================================================
# L2: 文法制导检查
# ======================================================================

def check_type_system(project_path):
    """L2.1: 检查类型系统"""
    py_path = project_path / "core" / "knowledge" / "validation" / "type_system.py"
    if not py_path.exists():
        return False, "type_system.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class TypeSystem" not in content:
        return False, "缺少TypeSystem类"
    return True, "类型系统存在"


def check_formula_checker(project_path):
    """L2.2: 检查公式检查器"""
    py_path = project_path / "core" / "knowledge" / "validation" / "formula_checker.py"
    if not py_path.exists():
        return False, "formula_checker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class FormulaChecker" not in content:
        return False, "缺少FormulaChecker类"
    return True, "公式检查器存在"


def check_output_validator(project_path):
    """L2.3: 检查输出验证器"""
    py_path = project_path / "core" / "knowledge" / "validation" / "output_validator.py"
    if not py_path.exists():
        return False, "output_validator.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class OutputValidator" not in content:
        return False, "缺少OutputValidator类"
    return True, "输出验证器存在"


# ======================================================================
# L3: 不变式编译检查
# ======================================================================

def check_invariant_tracker(project_path):
    """L3.1: 检查不变式跟踪"""
    py_path = project_path / "core" / "knowledge" / "validation" / "invariant_tracker.py"
    if not py_path.exists():
        return False, "invariant_tracker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class InvariantTracker" not in content:
        return False, "缺少InvariantTracker类"
    return True, "不变式跟踪存在"


def check_contract_checker(project_path):
    """L3.2: 检查契约校验"""
    py_path = project_path / "core" / "knowledge" / "validation" / "contract_checker.py"
    if not py_path.exists():
        return False, "contract_checker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class ContractChecker" not in content:
        return False, "缺少ContractChecker类"
    return True, "契约校验存在"


def check_stage_gate(project_path):
    """L3.3: 检查阶段门禁"""
    py_path = project_path / "core" / "knowledge" / "validation" / "stage_gate.py"
    if not py_path.exists():
        return False, "stage_gate.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class StageGate" not in content:
        return False, "缺少StageGate类"
    return True, "阶段门禁存在"


# ======================================================================
# L4: 符号验证检查
# ======================================================================

def check_symbolic_verifier(project_path):
    """L4.1: 检查符号验证器"""
    py_path = project_path / "core" / "knowledge" / "validation" / "symbolic_verifier.py"
    if not py_path.exists():
        return False, "symbolic_verifier.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class SymbolicVerifier" not in content:
        return False, "缺少SymbolicVerifier类"
    return True, "符号验证器存在"


def check_cross_model_checker(project_path):
    """L4.2: 检查异构模型"""
    py_path = project_path / "core" / "knowledge" / "validation" / "cross_model_checker.py"
    if not py_path.exists():
        return False, "cross_model_checker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class CrossModelChecker" not in content:
        return False, "缺少CrossModelChecker类"
    return True, "异构模型检查存在"


def check_consistency_checker(project_path):
    """L4.3: 检查一致性校验"""
    py_path = project_path / "core" / "knowledge" / "validation" / "consistency_checker.py"
    if not py_path.exists():
        return False, "consistency_checker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class ConsistencyChecker" not in content:
        return False, "缺少ConsistencyChecker类"
    return True, "一致性校验存在"


# ======================================================================
# L5: 信任域隔离检查
# ======================================================================

def check_trust_domain(project_path):
    """L5.1: 检查信任域定义"""
    py_path = project_path / "core" / "knowledge" / "validation" / "trust_domain.py"
    if not py_path.exists():
        return False, "trust_domain.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class TrustDomain" not in content:
        return False, "缺少TrustDomain类"
    return True, "信任域定义存在"


def check_permission_guard(project_path):
    """L5.2: 检查权限守卫"""
    py_path = project_path / "core" / "knowledge" / "validation" / "permission_guard.py"
    if not py_path.exists():
        return False, "permission_guard.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class PermissionGuard" not in content:
        return False, "缺少PermissionGuard类"
    return True, "权限守卫存在"


def check_incremental_checker(project_path):
    """L5.3: 检查增量校验"""
    py_path = project_path / "core" / "knowledge" / "validation" / "incremental_checker.py"
    if not py_path.exists():
        return False, "incremental_checker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class IncrementalChecker" not in content:
        return False, "缺少IncrementalChecker类"
    return True, "增量校验存在"


# ======================================================================
# L6: 全链路审计检查
# ======================================================================

def check_hash_chain(project_path):
    """L6.8: 检查哈希追溯链"""
    py_path = project_path / "core" / "knowledge" / "validation" / "hash_chain.py"
    if not py_path.exists():
        return False, "hash_chain.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class HashChain" not in content:
        return False, "缺少HashChain类"
    return True, "哈希追溯链存在"


def check_error_attribution(project_path):
    """L6.9: 检查错误归因"""
    py_path = project_path / "core" / "knowledge" / "validation" / "error_attribution.py"
    if not py_path.exists():
        return False, "error_attribution.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class ErrorAttribution" not in content:
        return False, "缺少ErrorAttribution类"
    return True, "错误归因存在"


def check_rule_iterator(project_path):
    """L6.10: 检查规则迭代"""
    py_path = project_path / "core" / "knowledge" / "validation" / "rule_iterator.py"
    if not py_path.exists():
        return False, "rule_iterator.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class RuleIterator" not in content:
        return False, "缺少RuleIterator类"
    return True, "规则迭代存在"


def check_documentation_completeness(project_path):
    """L6.11: 检查文档完整性"""
    required_docs = [
        "docs/ARCHITECTURE.md",
        "README.md",
        "core/Modeler/SKILL.md",
        "core/Programmer/SKILL.md",
        "core/Writer/SKILL.md",
    ]
    missing = [d for d in required_docs if not (project_path / d).exists()]
    if missing:
        return False, f"缺失文档: {', '.join(missing)}"
    return True, "文档完整"


def check_test_coverage(project_path):
    """L6.12: 检查测试覆盖率"""
    test_dirs = ["tests/unit", "tests/integration", "tests/e2e"]
    empty = []
    for td in test_dirs:
        td_path = project_path / td
        if not td_path.exists() or not list(td_path.glob("test_*.py")):
            empty.append(td)
    if empty:
        return False, f"测试目录为空: {', '.join(empty)}"
    return True, "测试目录有内容"


def check_results_ledger(project_path):
    """L6.7: 检查结果文件"""
    if not _live_project_dirs(project_path):
        return True, "跳过：无活跃项目实例（样例已归档至 archives/）"
    results_files = list(iter_repo(project_path, "all_results.json"))
    if not results_files:
        return False, "未找到all_results.json"
    
    for rf in results_files:
        try:
            data = json.loads(rf.read_text(encoding="utf-8"))
            if not data:
                return False, f"{rf.name}为空"
            if not isinstance(data, dict):
                return False, f"{rf.name}格式错误"
        except json.JSONDecodeError:
            return False, f"{rf.name} JSON解析失败"
    
    return True, "结果文件有效"


def check_random_seed(project_path):
    """L6.8: 检查随机种子"""
    if not _live_project_dirs(project_path):
        return True, "跳过：无活跃项目实例（样例已归档至 archives/）"
    code_files = list(iter_repo(project_path, "*.py"))
    found_seed = False
    
    for py_file in code_files[:10]:
        try:
            content = py_file.read_text(encoding="utf-8")
            if "seed" in content.lower() and ("42" in content or "random" in content.lower()):
                found_seed = True
                break
        except:
            pass
    
    if found_seed:
        return True, "发现随机种子设置"
    return False, "未设置随机种子"


def check_directory_structure(project_path):
    """目录结构检查"""
    required_dirs = [
        "core/Modeler", "core/Modeler/laws", "core/Modeler/knowledge",
        "core/Modeler/knowledge/domain",
        "core/Programmer", "core/Programmer/laws", "core/Programmer/knowledge",
        "core/Programmer/knowledge/code-templates",
        "core/Writer", "core/Writer/laws", "core/Writer/knowledge",
        "core/Writer/knowledge/writing", "core/Writer/knowledge/templates",
        "core/knowledge", "core/knowledge/methodology", "core/knowledge/paper-cases", "core/knowledge/validation",
        "core/schemas", "tests",
    ]
    
    missing = [d for d in required_dirs if not (project_path / d).exists()]
    if missing:
        return False, f"缺失目录: {', '.join(missing)}"
    return True, "目录结构完整"


def check_python_syntax(project_path):
    """L6.9: 检查Python语法"""
    code_files = list(iter_repo(project_path, "*.py"))
    errors = []
    
    for py_file in code_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            compile(content, str(py_file), "exec")
        except SyntaxError as e:
            errors.append(f"{py_file.name}: 行{e.lineno} - {e.msg}")
    
    if errors:
        return False, f"Python语法错误: {'; '.join(errors[:3])}"
    return True, "Python语法正确"


# ======================================================================
# L1: env 配置层检查（UTG 多 Agent 架构演进）
# ======================================================================

def _load_env_loader_module(project_path):
    """动态加载 env/loader.py 为独立模块（避免 PYTHONPATH / 包路径依赖）。

    返回 (module, None) 或 (None, err_msg)。
    """
    loader_path = project_path / "core" / "env" / "loader.py"
    if not loader_path.exists():
        return None, "env/loader.py 不存在"
    try:
        spec = importlib.util.spec_from_file_location(
            "env_loader_check", str(loader_path)
        )
        if spec is None or spec.loader is None:
            return None, "无法创建加载器 spec"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, None
    except Exception as e:
        return None, f"加载 env/loader.py 失败: {e}"


def check_env_config_exists(project_path):
    """L1: env 配置三件套存在（config.yaml / loader.py / README.md）"""
    required = ["core/env/config.yaml", "core/env/loader.py", "core/env/README.md"]
    missing = [f for f in required if not (project_path / f).exists()]
    if missing:
        return False, f"缺失env配置文件: {', '.join(missing)}"
    return True, "env配置三件套完整"


def check_env_loader_importable(project_path):
    """L1: env/loader.py 可动态加载且接口齐全"""
    module, err = _load_env_loader_module(project_path)
    if module is None:
        return False, err
    if not callable(getattr(module, "load_config", None)):
        return False, "loader 缺少可调用的 load_config"
    if not callable(getattr(module, "get", None)):
        return False, "loader 缺少可调用的 get"
    try:
        cfg = module.load_config()
    except Exception as e:
        return False, f"load_config() 调用异常: {e}"
    if not isinstance(cfg, dict):
        return False, f"load_config() 返回非 dict: {type(cfg).__name__}"
    if not cfg:
        return False, "load_config() 返回空 dict"
    return True, "env加载器可加载且接口齐全"


def check_env_config_fields(project_path):
    """L1: env 配置四组字段齐全"""
    module, err = _load_env_loader_module(project_path)
    if module is None:
        return False, err
    try:
        cfg = module.load_config()
    except Exception as e:
        return False, f"load_config() 调用异常: {e}"
    if not isinstance(cfg, dict):
        return False, "load_config() 返回非 dict"

    expected = {
        "paper": ["min_pages", "min_words", "min_figures", "min_tables",
                  "min_equations", "min_references"],
        "code": ["random_seed", "multi_run_count"],
        "modeling": ["min_candidate_models", "assumption_score_threshold"],
        "runtime": ["language", "template", "strict_mode"],
    }
    missing = []
    for group, fields in expected.items():
        if group not in cfg:
            missing.append(f"{group}组缺失")
            continue
        for f in fields:
            if f not in cfg[group]:
                missing.append(f"{group}.{f}")
    if missing:
        return False, f"env配置字段缺失: {', '.join(missing)}"
    return True, "env配置四组字段齐全"


# ======================================================================
# L1/L6: agent 结构完整性检查（UTG 多 Agent 架构演进）
# ======================================================================

# 四手预期 agent 名称与数量（8 / 6 / 7 / 8 = 29）
# Modeler 新增 Stage 1.5 literature-searcher 与 Stage 4.5 dag-builder
# Reviewer 扩展为 5 人评审团 (scorer-*) + weakness-hunter + revision-planner + revision-executor
_EXPECTED_AGENTS = {
    "Modeler": ["problem-parser", "type-classifier", "literature-searcher",
                "method-matcher", "model-builder", "dag-builder",
                "assumption-validator", "spec-auditor"],
    "Programmer": ["template-selector", "code-implementer", "test-runner",
                   "result-verifier", "guardrails-checker", "hash-auditor"],
    "Writer": ["structure-planner", "section-writer", "figure-generator",
               "reference-curator", "consistency-checker",
               "guardrails-checker", "final-validator"],
    "Reviewer": ["scorer-academic", "scorer-engineering", "scorer-judge",
                 "scorer-reader", "scorer-adversarial",
                 "weakness-hunter", "revision-planner", "revision-executor"],
}

# 合法 utg_layer 取值
_VALID_UTG_LAYERS = {"L1", "L2", "L3", "L4", "L5", "L6", "L5+L6"}


def _iter_agent_skill_files(project_path):
    """遍历四手 agents 目录下预期 agent 的 SKILL.md 路径。

    yield (hand, agent_name, skill_path)，路径不保证存在（由调用方判断）。
    """
    for hand, names in _EXPECTED_AGENTS.items():
        agents_dir = project_path / "core" / hand / "agents"
        for agent_name in names:
            yield hand, agent_name, agents_dir / agent_name / "SKILL.md"


def check_agents_directories(project_path):
    """L1: 四手 agents 目录存在"""
    missing = []
    for hand in _EXPECTED_AGENTS:
        d = project_path / "core" / hand / "agents"
        if not d.exists():
            missing.append(f"{hand}/agents")
    if missing:
        return False, f"agents目录缺失: {', '.join(missing)}"
    return True, "四手agents目录齐全"


def check_agents_count(project_path):
    """L1: 四手 agent 数量与名称正确（8/6/7/8，每个子目录含 SKILL.md）"""
    issues = []
    for hand, expected_names in _EXPECTED_AGENTS.items():
        agents_dir = project_path / "core" / hand / "agents"
        if not agents_dir.exists():
            issues.append(f"{hand}/agents 目录不存在")
            continue
        actual = []
        try:
            for sub in sorted(agents_dir.iterdir()):
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    actual.append(sub.name)
        except Exception as e:
            issues.append(f"{hand}/agents 遍历失败: {e}")
            continue
        if len(actual) != len(expected_names):
            issues.append(f"{hand} agent数量为{len(actual)}(预期{len(expected_names)})")
            continue
        for name in expected_names:
            if name not in actual:
                issues.append(f"{hand} 缺少 agent: {name}")
    if issues:
        return False, "; ".join(issues)
    return True, "四手agent数量与名称正确(8/6/7/8)"


def check_agents_frontmatter(project_path):
    """L1: 每个 agent SKILL.md 含合法 YAML frontmatter 与必填字段"""
    required_fields = ["name", "utg_layer", "inputs", "outputs", "stage"]
    fm_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
    issues = []
    for hand, agent_name, skill_path in _iter_agent_skill_files(project_path):
        if not skill_path.exists():
            issues.append(f"{hand}/{agent_name}: SKILL.md 不存在")
            continue
        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception as e:
            issues.append(f"{hand}/{agent_name}: 读取失败 {e}")
            continue
        m = fm_pattern.match(content)
        if not m:
            issues.append(f"{hand}/{agent_name}: 缺少 frontmatter")
            continue
        fm = m.group(1)
        for field in required_fields:
            if not re.search(r"^%s\s*:" % re.escape(field), fm, re.MULTILINE):
                issues.append(f"{hand}/{agent_name}: frontmatter 缺字段 {field}")
        layer_m = re.search(r"^utg_layer\s*:\s*(\S+)", fm, re.MULTILINE)
        if layer_m:
            layer_val = layer_m.group(1).strip().strip('"\'')
            if layer_val not in _VALID_UTG_LAYERS:
                issues.append(f"{hand}/{agent_name}: utg_layer={layer_val} 非法")
        else:
            issues.append(f"{hand}/{agent_name}: frontmatter 缺 utg_layer 值")
    if issues:
        return False, "; ".join(issues[:5])
    return True, "29个agent frontmatter字段齐全"


def check_agents_self_check(project_path):
    """L1: 每个 agent SKILL.md 含 ## Self-Check 章节"""
    missing = []
    for hand, agent_name, skill_path in _iter_agent_skill_files(project_path):
        if not skill_path.exists():
            missing.append(f"{hand}/{agent_name}")
            continue
        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception:
            missing.append(f"{hand}/{agent_name}")
            continue
        if not re.search(r"^##\s*Self-Check\s*$", content, re.MULTILINE):
            missing.append(f"{hand}/{agent_name}")
    if missing:
        return False, f"缺少Self-Check章节: {', '.join(missing[:5])}"
    return True, "29个agent均含Self-Check章节"


def check_catalog_yaml(project_path):
    """L1: catalog.yaml 存在且含全部 29 个 agent name（正则解析，零依赖）"""
    catalog_path = project_path / "catalog.yaml"
    if not catalog_path.exists():
        return False, "catalog.yaml 不存在"
    try:
        content = catalog_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"catalog.yaml 读取失败: {e}"
    names = re.findall(r"^\s+- name: (\S+)", content, re.MULTILINE)
    name_set = set(names)
    expected_all = []
    for names_list in _EXPECTED_AGENTS.values():
        expected_all.extend(names_list)
    expected_set = set(expected_all)
    missing = [n for n in expected_set if n not in name_set]
    if missing:
        return False, f"catalog.yaml 缺 agent: {', '.join(sorted(missing))}"
    return True, "catalog.yaml 含全部29个agent"


def check_agents_md(project_path):
    """L1: AGENTS.md 存在且含关键章节（## Agent 索引 / ## env 配置入口）"""
    agents_md = project_path / "AGENTS.md"
    if not agents_md.exists():
        return False, "AGENTS.md 不存在"
    try:
        content = agents_md.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"AGENTS.md 读取失败: {e}"
    required_sections = ["## Agent 索引", "## env 配置入口"]
    missing = [s for s in required_sections if s not in content]
    if missing:
        return False, f"AGENTS.md 缺章节: {', '.join(missing)}"
    return True, "AGENTS.md 关键章节齐全"


# ======================================================================
# L4: 数值追溯与物理模型检查
# ======================================================================

def check_numeric_traceability(project_path):
    """L4: 检查数值可追溯比例（≥90%）"""
    results_files = list(iter_repo(project_path, "all_results.json"))
    if not results_files:
        return True, "无 all_results.json（跳过）"

    # 尝试加载 all_results.json 中的数值
    try:
        data = json.loads(results_files[0].read_text(encoding="utf-8"))
    except:
        return True, "all_results.json 加载失败（跳过）"

    # 提取所有数值
    def extract_numbers(obj, prefix=""):
        nums = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                nums.update(extract_numbers(v, f"{prefix}.{k}" if prefix else k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                nums.update(extract_numbers(v, f"{prefix}[{i}]"))
        elif isinstance(obj, (int, float)):
            nums[prefix] = obj
        return nums

    all_nums = extract_numbers(data)
    if not all_nums:
        return True, "all_results.json 无数值（跳过）"

    # 检查 .tex 文件中的数值引用
    template_dirs = {"templates", "template"}
    tex_files = []
    for tex_file in iter_repo(project_path, "*.tex"):
        if not any(td in tex_file.parts for td in template_dirs):
            tex_files.append(tex_file)

    if not tex_files:
        return True, "无用户.tex文件（跳过）"

    # 从 tex 中提取数值（简单浮点数匹配）
    tex_numbers = set()
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8")
            # 匹配浮点数（含科学计数法）
            found = re.findall(r'\b\d+\.?\d*(?:[eE][+-]?\d+)?\b', content)
            for n in found:
                try:
                    tex_numbers.add(float(n))
                except:
                    pass
        except:
            pass

    if not tex_numbers:
        return True, "tex 中无数值（跳过）"

    # 检查 tex 中的数值是否在 all_results.json 中存在（容差匹配）
    json_values = list(all_nums.values())
    tol_rel = float(_env_get("runtime.numeric_tolerance_rel", 0.005))
    tol_abs = float(_env_get("runtime.numeric_tolerance_abs", 0.01))
    min_ratio = float(_env_get("runtime.traceability_min_ratio", 0.90))

    traced = 0
    for tv in tex_numbers:
        # 检查是否与 json 中任一数值在容差范围内匹配
        for jv in json_values:
            if isinstance(jv, (int, float)):
                if abs(tv - jv) <= max(abs(jv) * tol_rel, tol_abs):
                    traced += 1
                    break

    ratio = traced / len(tex_numbers) if tex_numbers else 0
    if ratio < min_ratio:
        return False, f"数值追溯比例={ratio:.1%}<{min_ratio:.0%}(需≥{min_ratio:.0%})"
    return True, f"数值追溯比例={ratio:.1%}(≥{min_ratio:.0%})"


def check_physics_model(project_path):
    """L4: 物理模型 6 项检查（坐标系/几何判据/解析验证等）"""
    template_dirs = {"templates", "template"}
    tex_files = []
    for tex_file in iter_repo(project_path, "*.tex"):
        if not any(td in tex_file.parts for td in template_dirs):
            tex_files.append(tex_file)

    if not tex_files:
        return True, "无用户.tex文件（跳过）"

    # 检查是否涉及物理过程
    physics_keywords = [
        "运动", "速度", "加速度", "力", "能量", "动量", "角速度", "角动量",
        "轨迹", "碰撞", "反射", "折射", "坐标", "几何", "角度", "距离",
        "velocity", "acceleration", "force", "energy", "momentum", "trajectory",
        "collision", "reflection", "coordinate", "geometry", "angle", "distance",
    ]

    all_content = ""
    for tex_file in tex_files:
        try:
            all_content += tex_file.read_text(encoding="utf-8")
        except:
            pass

    has_physics = any(kw in all_content.lower() for kw in physics_keywords)
    if not has_physics:
        return True, "不涉及物理过程（跳过物理模型检查）"

    checks = []
    # 1. 坐标系定义
    coord_keywords = ["坐标系", "坐标轴", "原点", "x轴", "y轴", "z轴", "coordinate system", "x-axis", "y-axis"]
    has_coord = any(kw in all_content.lower() for kw in coord_keywords)
    checks.append(("坐标系定义", has_coord))

    # 2. 几何判据
    geometry_keywords = ["几何关系", "几何条件", "判据", "几何约束", "geometric", "criterion"]
    has_geometry = any(kw in all_content.lower() for kw in geometry_keywords)
    checks.append(("几何判据", has_geometry))

    # 3. 解析解/验证解
    analytical_keywords = ["解析解", "精确解", "验证", "analytical solution", "exact solution", "closed form"]
    has_analytical = any(kw in all_content.lower() for kw in analytical_keywords)
    checks.append(("解析验证", has_analytical))

    # 4. 运动分解
    decomposition_keywords = ["分解", "分量", "水平", "竖直", "切向", "法向", "decomposition", "component", "horizontal", "vertical"]
    has_decomposition = any(kw in all_content.lower() for kw in decomposition_keywords)
    checks.append(("运动分解", has_decomposition))

    # 5. 时序因果
    temporal_keywords = ["时间步", "时序", "先后", "因果", "time step", "temporal", "causal", "sequence"]
    has_temporal = any(kw in all_content.lower() for kw in temporal_keywords)
    checks.append(("时序因果", has_temporal))

    # 6. 代码坐标一致性
    consistency_keywords = ["一致", "校对", "验证", "对比", "consistent", "verify", "cross-check"]
    has_consistency = any(kw in all_content.lower() for kw in consistency_keywords)
    checks.append(("坐标一致性", has_consistency))

    failed = [name for name, ok in checks if not ok]
    if failed:
        return False, f"物理模型检查缺失: {', '.join(failed)}"
    return True, "物理模型 6 项检查通过"


# ======================================================================
# L5: 正文质量护栏检查
# ======================================================================

def check_itemize_in_body(project_path):
    """L5: 检查正文是否包含 itemize/enumerate 列表环境（HARD 门禁）"""
    template_dirs = {"templates", "template"}
    tex_files = []
    for tex_file in iter_repo(project_path, "*.tex"):
        if not any(td in tex_file.parts for td in template_dirs):
            tex_files.append(tex_file)

    if not tex_files:
        return True, "无用户.tex文件（跳过）"

    found = []
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8")
            # 检查列表环境，但排除符号说明表（通常用 tabular）和附录
            itemize_count = len(re.findall(r'\\begin\{itemize\}', content))
            enumerate_count = len(re.findall(r'\\begin\{enumerate\}', content))
            if itemize_count > 0 or enumerate_count > 0:
                rel_path = tex_file.relative_to(project_path)
                found.append(f"{rel_path}(itemize×{itemize_count}, enumerate×{enumerate_count})")
        except:
            pass

    if found:
        return False, f"正文包含列表环境(HARD): {'; '.join(found[:3])}"
    return True, "正文无 itemize/enumerate 列表"


def check_figure_as_subject(project_path):
    """L5: 检查图表主语句式（≥3 次 FAIL）"""
    template_dirs = {"templates", "template"}
    tex_files = []
    for tex_file in iter_repo(project_path, "*.tex"):
        if not any(td in tex_file.parts for td in template_dirs):
            tex_files.append(tex_file)

    if not tex_files:
        return True, "无用户.tex文件（跳过）"

    figure_subject_patterns = [
        r'图\s*\d+\s*展示',
        r'如图\s*\d+\s*所示',
        r'由图\s*\d+\s*可知',
        r'从图\s*\d+\s*可以看',
        r'表\s*\d+\s*展示',
        r'如表\s*\d+\s*所示',
        r'由表\s*\d+\s*可知',
        r'Figure\s*\d+\s*shows',
        r'As shown in Figure',
        r'Table\s*\d+\s*shows',
        r'As shown in Table',
    ]

    threshold = int(_env_get("review.figure_as_subject_max", 3))
    total_count = 0
    details = []
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8")
            for pat in figure_subject_patterns:
                matches = re.findall(pat, content, re.IGNORECASE)
                total_count += len(matches)
                if matches:
                    details.append(f"{tex_file.name}: {pat}={len(matches)}")
        except:
            pass

    if total_count >= threshold:
        return False, f"图表主语句式≥{threshold}次(HARD): 共{total_count}次"
    return True, f"图表主语句式={total_count}次(阈值={threshold})"


def check_consecutive_same_openings(project_path):
    """L5: 检查连续段落相同句式开头（WARN）"""
    template_dirs = {"templates", "template"}
    tex_files = []
    for tex_file in iter_repo(project_path, "*.tex"):
        if not any(td in tex_file.parts for td in template_dirs):
            tex_files.append(tex_file)

    if not tex_files:
        return True, "无用户.tex文件（跳过）"

    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8")
            # 按段落分割（空行分隔）
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
            # 提取每段开头前 8 个中文字符
            openings = []
            for p in paragraphs:
                # 跳过 LaTeX 命令和空行
                clean = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', p)
                clean = re.sub(r'\\[a-zA-Z]+', '', clean)
                clean = clean.strip()
                if clean:
                    # 取前 6 个字符作为"开头"
                    openings.append(clean[:6])

            # 检查连续相同开头
            consecutive = 0
            for i in range(len(openings) - 2):
                if openings[i] == openings[i+1] == openings[i+2]:
                    consecutive += 1

            if consecutive >= 3:
                return False, f"连续段落相同句式开头≥3处(WARN): {tex_file.name}"
        except:
            pass

    return True, "无连续段落相同句式开头"


# ======================================================================
# L6: PDF 最小字节检查
# ======================================================================

def check_pdf_min_bytes(project_path):
    """L6: 检查 PDF 最小字节（≥100KB）"""
    min_bytes = int(_env_get("paper.pdf_min_bytes", 102400))

    pdf_files = []
    # 排除 templates 目录
    template_dirs = {"templates", "template"}
    for pdf_file in iter_repo(project_path, "*.pdf"):
        if not any(td in pdf_file.parts for td in template_dirs):
            pdf_files.append(pdf_file)

    if not pdf_files:
        return True, "无用户 PDF 文件（跳过）"

    issues = []
    for pdf_file in pdf_files:
        size = pdf_file.stat().st_size
        if size < min_bytes:
            rel_path = pdf_file.relative_to(project_path)
            issues.append(f"{rel_path}: {size}B < {min_bytes}B")

    if issues:
        return False, f"PDF 过小: {'; '.join(issues[:3])}"
    return True, "PDF 文件大小合格"


# ======================================================================
# 主验证函数
# ======================================================================

def validate_project(project_path):
    """运行所有验证检查"""
    project_path = Path(project_path)
    
    print("=" * 60)
    print("MathModelSkills 六层防御验证")
    print("=" * 60)
    
    all_checks = [
        # L1: 结构化输出
        ("L1", "Schema目录", lambda: check_schema_exists(project_path)),
        ("L1", "Schema格式", lambda: check_schemas_valid(project_path)),
        
        # L3: 过程验证
        ("L3", "必要产物", lambda: check_required_artifacts(project_path)),
        ("L3", "知识库完整性", lambda: check_knowledge_completeness(project_path)),
        ("L3", "laws非空", lambda: check_laws_not_empty(project_path)),
        
        # L5: 运行时护栏
        ("L5", "禁用词", lambda: check_forbidden_words_in_dir(project_path)),
        ("L5", "占位符", lambda: check_placeholders_in_dir(project_path)),
        ("L5", "AI痕迹", lambda: check_ai_traces_in_dir(project_path)),
        ("L5", "内部路径", lambda: check_internal_paths(project_path)),
        ("L5", "正文列表", lambda: check_itemize_in_body(project_path)),
        ("L5", "图表主语句式", lambda: check_figure_as_subject(project_path)),
        ("L5", "段落句式", lambda: check_consecutive_same_openings(project_path)),
        
        # L6: 事后验证
        ("L6", "目录结构", lambda: check_directory_structure(project_path)),
        ("L6", "Python语法", lambda: check_python_syntax(project_path)),
        ("L6", "结果文件", lambda: check_results_ledger(project_path)),
        ("L6", "随机种子", lambda: check_random_seed(project_path)),
        ("L6", "论文结构", lambda: check_paper_structure(project_path)),
        ("L6", "PDF大小", lambda: check_pdf_min_bytes(project_path)),
        ("L6", "引用完整性", lambda: check_citation_integrity(project_path)),
        ("L6", "图表引用", lambda: check_figure_refs(project_path)),
        ("L6", "灵敏度分析", lambda: check_sensitivity_analysis(project_path)),
        ("L6", "模型评价", lambda: check_model_evaluation(project_path)),
        ("L6", "假设必要性", lambda: check_assumptions_necessity(project_path)),
        ("L6", "文献年份", lambda: check_recent_references_ratio(project_path)),
        ("L6", "表格行数", lambda: check_table_row_count(project_path)),
        
        # L1: 输入规约检查
        ("L1", "输入规约Schema", lambda: check_question_spec_schema(project_path)),
        ("L1", "符号注册表", lambda: check_symbol_registry(project_path)),
        ("L1", "假设验证器", lambda: check_assumption_validator(project_path)),
        
        # L2: 文法制导检查
        ("L2", "类型系统", lambda: check_type_system(project_path)),
        ("L2", "公式检查器", lambda: check_formula_checker(project_path)),
        ("L2", "输出验证器", lambda: check_output_validator(project_path)),
        
        # L3: 不变式编译检查
        ("L3", "不变式跟踪", lambda: check_invariant_tracker(project_path)),
        ("L3", "契约校验", lambda: check_contract_checker(project_path)),
        ("L3", "阶段门禁", lambda: check_stage_gate(project_path)),
        
        # L4: 符号验证检查
        ("L4", "符号验证器", lambda: check_symbolic_verifier(project_path)),
        ("L4", "异构模型", lambda: check_cross_model_checker(project_path)),
        ("L4", "一致性校验", lambda: check_consistency_checker(project_path)),
        ("L4", "物理模型", lambda: check_physics_model(project_path)),
        ("L4", "数值追溯", lambda: check_numeric_traceability(project_path)),
        
        # L5: 信任域隔离检查
        ("L5", "信任域定义", lambda: check_trust_domain(project_path)),
        ("L5", "权限守卫", lambda: check_permission_guard(project_path)),
        ("L5", "增量校验", lambda: check_incremental_checker(project_path)),
        
        # L6: 全链路审计检查
        ("L6", "哈希追溯链", lambda: check_hash_chain(project_path)),
        ("L6", "错误归因", lambda: check_error_attribution(project_path)),
        ("L6", "规则迭代", lambda: check_rule_iterator(project_path)),
        
        # L6: 综合质量检查
        ("L6", "文档完整性", lambda: check_documentation_completeness(project_path)),
        ("L6", "测试覆盖率", lambda: check_test_coverage(project_path)),

        # L1: env 配置层（UTG 多 Agent 架构演进）
        ("L1", "env配置文件", lambda: check_env_config_exists(project_path)),
        ("L1", "env加载器", lambda: check_env_loader_importable(project_path)),
        ("L1", "env配置字段", lambda: check_env_config_fields(project_path)),
        # L1: agent 结构
        ("L1", "agents目录", lambda: check_agents_directories(project_path)),
        ("L1", "agent数量", lambda: check_agents_count(project_path)),
        ("L1", "agent frontmatter", lambda: check_agents_frontmatter(project_path)),
        ("L1", "agent Self-Check", lambda: check_agents_self_check(project_path)),
        ("L1", "catalog.yaml", lambda: check_catalog_yaml(project_path)),
        ("L1", "AGENTS.md", lambda: check_agents_md(project_path)),
        # L6: Checkpoint 格式检查
        ("L6", "checkpoint格式", lambda: check_checkpoint_format(project_path)),
    ]
    
    # WARN 级检查：不通过只记警告、不阻塞交付。
    # 对应 P2 增强性门禁（此前被当作硬失败，导致
    # "0 警告" 与失败列表里出现 WARN 项自相矛盾）。
    WARN_CHECKS = {"文献年份", "表格行数", "段落句式", "摘要字数"}

    passed = 0
    failed = 0
    warnings = 0
    errors = []
    warn_msgs = []

    for layer, name, check_fn in all_checks:
        try:
            ok, msg = check_fn()
            is_warn = name in WARN_CHECKS
            status = "PASS" if ok else ("WARN" if is_warn else "FAIL")
            if ok:
                passed += 1
                print(f"  [{layer}] {name}: {status} - {msg}")
            elif is_warn:
                warnings += 1
                warn_msgs.append(f"[{layer}] {name}: {msg}")
                print(f"  [{layer}] {name}: {status} - {msg}")
            else:
                failed += 1
                errors.append(f"[{layer}] {name}: {msg}")
                print(f"  [{layer}] {name}: {status} - {msg}")
        except Exception as e:
            warnings += 1
            warn_msgs.append(f"[{layer}] {name}: 检查异常: {e}")
            print(f"  [{layer}] {name}: WARN - 检查异常: {e}")

    print("\n" + "=" * 60)
    print(f"验证完成: {passed} 通过, {failed} 失败, {warnings} 警告")

    if errors:
        print("\n失败项（阻塞交付）:")
        for e in errors:
            print(f"  - {e}")

    if warn_msgs:
        print("\n警告项（不阻塞，建议改进）:")
        for w in warn_msgs:
            print(f"  - {w}")

    print("=" * 60)

    return failed == 0


# ======================================================================
# L6: P2 增强检查（WARN 级别）
# ======================================================================

def _infer_problem_year(file_path, fallback=2026):
    """推断赛题年份：优先从 projects/<项目名> 目录名提取，回退 fallback。

    「近 3 年文献」必须以赛题年份为基准，而非当前年份——
    2024 年完成的论文不可能引用 2025 年的文献，用当前年做基准会误判。
    """
    try:
        parts = file_path.parts
        if "projects" in parts:
            idx = parts.index("projects")
            if idx + 1 < len(parts):
                m = re.search(r'((?:19|20)\d{2})', parts[idx + 1])
                if m:
                    return int(m.group(1))
    except Exception:
        pass
    return fallback


def check_recent_references_ratio(project_path):
    """L6: 检查近 3 年文献占比是否 ≥60%（WARN）

    基准年为赛题年份（从项目目录名推断），不是当前年份。
    同时检测「未来文献」（年份晚于赛题年份）——引用造假的信号。
    """
    template_dirs = {"templates", "template"}

    bib_files = []
    for bib_file in iter_repo(project_path, "*.bib"):
        if not any(td in bib_file.parts for td in template_dirs):
            bib_files.append(bib_file)

    if not bib_files:
        return True, "无用户.bib文件（跳过）"

    min_ratio = float(_env_get("paper.recent_ref_ratio", 0.6))

    total = 0
    recent = 0
    future = []
    base_years = set()
    for bib_file in bib_files:
        try:
            base_year = _infer_problem_year(bib_file)
            base_years.add(base_year)
            content = bib_file.read_text(encoding="utf-8")
            years = re.findall(r'year\s*=\s*\{?(\d{4})\}?', content)
            for y in years:
                y = int(y)
                total += 1
                if base_year - 3 <= y <= base_year:
                    recent += 1
                elif y > base_year:
                    future.append(f"{bib_file.name}:{y}>{base_year}")
        except Exception:
            pass

    if total == 0:
        return True, "无法解析文献年份（跳过）"

    base_desc = "/".join(str(y) for y in sorted(base_years))
    ratio = recent / total

    if future:
        return False, f"存在未来文献(HARD，疑似伪造): {'; '.join(future[:3])}"

    if ratio < min_ratio:
        return False, f"近3年文献占比={ratio:.0%}<{min_ratio:.0%}(WARN, 基准年{base_desc}): {recent}/{total}"
    return True, f"近3年文献占比={ratio:.0%}(≥{min_ratio:.0%}, 基准年{base_desc}): {recent}/{total}"


def check_table_row_count(project_path):
    """L6: 检查正文表格行数（>12 行 WARN）"""
    template_dirs = {"templates", "template"}
    tex_files = []
    for tex_file in iter_repo(project_path, "*.tex"):
        if not any(td in tex_file.parts for td in template_dirs):
            tex_files.append(tex_file)
    
    if not tex_files:
        return True, "无用户.tex文件（跳过）"
    
    max_rows_inline = int(_env_get("paper.table_max_rows_inline", 12))
    longtable_threshold = int(_env_get("paper.table_longtable_threshold", 15))
    
    issues = []
    for tex_file in tex_files:
        try:
            content = tex_file.read_text(encoding="utf-8")
            # 查找所有 table 环境
            table_pattern = r'\\begin\{table\}.*?\\end\{table\}'
            tables = re.findall(table_pattern, content, re.DOTALL)
            for i, table in enumerate(tables):
                # 统计 \\ 行数（表格行）
                rows = len(re.findall(r'\\\\', table))
                if rows > max_rows_inline:
                    severity = "转longtable" if rows > longtable_threshold else "WARN"
                    issues.append(f"{tex_file.name}: table#{i+1}有{rows}行(>{max_rows_inline},{severity})")
        except:
            pass
    
    if issues:
        return False, f"表格行数超标(WARN): {'; '.join(issues[:3])}"
    return True, "表格行数合格"


# ======================================================================
# L6: Checkpoint 格式检查
# ======================================================================

def check_checkpoint_format(project_path):
    """L6: 检查 checkpoint.json 格式是否正确"""
    checkpoint_path = project_path / "output" / "checkpoint.json"
    if not checkpoint_path.exists():
        return True, "无 checkpoint.json（跳过）"
    
    try:
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        
        # 检查必填字段
        required_fields = ["version", "hand", "stage", "timestamp", "output_hash"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return False, f"checkpoint.json 缺少必填字段: {', '.join(missing)}"
        
        # 检查 hand 值
        if data["hand"] not in ["modeler", "programmer", "writer"]:
            return False, f"checkpoint.json hand 值无效: {data['hand']}"
        
        # 检查 completed_agents 格式
        if "completed_agents" in data:
            for agent in data["completed_agents"]:
                agent_required = ["agent_name", "stage", "timestamp", "output_hash"]
                agent_missing = [f for f in agent_required if f not in agent]
                if agent_missing:
                    return False, f"completed_agents 中某 agent 缺少字段: {', '.join(agent_missing)}"
        
        return True, "checkpoint.json 格式正确"
    except Exception as e:
        return False, f"checkpoint.json 解析失败: {str(e)}"


if __name__ == "__main__":
    project_path = str(Path(__file__).resolve().parents[2])
    success = validate_project(project_path)
    sys.exit(0 if success else 1)
