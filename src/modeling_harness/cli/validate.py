"""
Modeling-Harness 验证脚本 - 六层防御体系
用于验证项目结构和产物完整性
"""
import re
import json
import sys
import importlib.util
from pathlib import Path


# === 禁用词列表（统一扩充词表）===
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

# === 禁用词正则模式 ===
FORBIDDEN_WORD_REGEXES = [
    r"随着.{0,12}的快速发展",
]

# === 占位符模式 ===
PLACEHOLDER_PATTERNS = [
    r"TODO", r"FIXME", r"TBD", r"__XXX__",
    r"\[待补\]", r"\[TBD\]", r"示例数据", r"模板数据",
    r"PLACEHOLDER", r"XXX", r"这里填写",
    r"待补充", r"待续写", r"这里补", r"待完善",
]

# === 内部路径模式 ===
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

# === 仓库级扫描：跳过临时与缓存目录 ===
# _scratch/_debug 为临时区，node_modules/__pycache__ 为构建缓存，均排除在实时校验外。
REPO_SCAN_EXCLUDE_DIRS = {"_scratch", "_debug", "node_modules", "__pycache__"}
RESEARCH_PROJECT_PREFIXES = ("p151-", "rcs1-", "v3-real-", "bench-")


def _is_research_scan_path(p: Path) -> bool:
    """路径是否属于研究实验（research/ 或 projects/ 下的 P15/历史实验项目）。

    研究实验不属于论文交付校验范围（validate.py 文档声明）；projects/ 内
    滞留的历史研究实验项目（p151-*/rcs1-*/v3-real-*/bench-*）同样排除。
    """
    parts = p.parts
    for idx, part in enumerate(parts):
        if part == "research":
            return True
        if part == "tests":
            # 测试夹具（tests/fixtures/*）不是交付项目实例，排除出论文
            # 交付校验（全量 pytest 会在 tests/fixtures/ 生成样例项目残留）
            return True
        if part == "projects" and idx + 1 < len(parts):
            nxt = parts[idx + 1]
            if nxt.startswith(RESEARCH_PROJECT_PREFIXES):
                return True
    return False


def iter_repo(root, pattern):
    """遍历 root 下匹配 pattern 的文件，跳过归档/临时/研究实验路径。"""
    root = Path(root)
    for p in root.rglob(pattern):
        if any(part in REPO_SCAN_EXCLUDE_DIRS for part in p.parts):
            continue
        if _is_research_scan_path(p):
            continue
        yield p


def _live_project_dirs(project_path):
    """返回 projects/ 下的活跃项目实例目录（样例已迁移至 tests/fixtures/）。

    本仓库是技能库，projects/ 可能为空（无活跃实例）。项目级存在性检查
    （all_results.json / 随机种子 / 论文 .tex）仅在存在活跃实例时才应报失败，
    否则库模式下的空 projects/ 会持续产生假失败。

    研究实验（P13-3D 系列 / bench 运行 / P15 实验项目 p151-*/rcs1-*/v3-real-*）
    不属于论文交付校验范围（research/ 不在本函数扫描内；projects/ 内滞留的
    P15 历史研究实验项目同样排除——它们没有论文交付契约）。
    """
    pdir = project_path / "projects"
    if not pdir.is_dir():
        return []
    return [d for d in pdir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
            and not (d / "work" / "e2e_problem.json").exists()
            and not d.name.startswith(RESEARCH_PROJECT_PREFIXES)]


# === env 阈值读取（动态加载 env/loader.get；缺失时回退默认值）===
_ENV_LOADER_MODULE = None


def _env_get(key, default=None):
    """通过 env/loader.get 读取阈值；加载失败时回退 default。"""
    global _ENV_LOADER_MODULE
    if _ENV_LOADER_MODULE is None:
        project_path = Path(__file__).resolve().parent.parent.parent.parent
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
    schemas_dir = project_path / "src" / "modeling_harness" / "schemas"
    if not schemas_dir.exists():
        return False, "schemas/目录不存在"

    required = ["v3/model/model_ir.schema.json", "v3/artifact/artifact.schema.json",
                "v3/evidence/graph.schema.json", "v3/decision/decision.schema.json"]
    missing = [f for f in required if not (schemas_dir / f).exists()]
    if missing:
        return False, f"缺失Schema文件: {', '.join(missing)}"

    return True, "Schema文件完整"


def check_schemas_valid(project_path):
    """L1.2: 检查JSON Schema是否为有效JSON"""
    schemas_dir = project_path / "src" / "modeling_harness" / "schemas"
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
            except Exception:
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
        except Exception:
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
        except Exception:
            pass

    if found:
        msg = "; ".join([f"'{w}' in {', '.join(files[:2])}" for w, files in found.items()])
        return False, f"发现AI痕迹: {msg}"
    return True, "无AI痕迹"


def check_internal_paths(project_path):
    """L5.4: 检查交付物内部路径泄漏（只扫 projects/ 用户交付物，与 L5.1 一致）。

    仓库治理文档（AGENTS.md / CHANGELOG.md 等）必然引用源码路径，不属于交付
    泄漏；projects/ 交付文档中的内部路径（/tmp/、__pycache__、code/*.py 等）
    仍会被拦截。
    """
    found = {}
    exclude_dirs = USER_CONTENT_EXCLUDE_DIRS
    proj_root = project_path / "projects"
    if not proj_root.exists():
        return True, "无 projects 目录（跳过）"

    for md_file in proj_root.rglob("*.md"):
        if md_file.parent == proj_root:
            continue  # projects/ 目录说明文档（README.md），非项目交付物
        if any(ed in md_file.parts for ed in exclude_dirs):
            continue
        if _is_research_scan_path(md_file):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
            for pattern in INTERNAL_PATH_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    rel_path = md_file.relative_to(project_path)
                    for m in set(matches):
                        if m not in found:
                            found[m] = []
                        found[m].append(str(rel_path))
        except Exception:
            pass

    if found:
        msg = "; ".join([f"'{w}' in {', '.join(files[:2])}" for w, files in list(found.items())[:3]])
        return False, f"发现内部路径: {msg}"
    return True, "无内部路径"
# ======================================================================
# L3: 过程验证检查
# ======================================================================

def check_required_artifacts(project_path):
    """L3.1: 检查必要产物（V3：MODEL_IR schema + 模型描述文档模板）"""
    required = {
        "src/modeling_harness/schemas/v3/model/model_ir.schema.json": "MODEL_IR schema",
        "src/modeling_harness/schemas/v3/artifact/artifact.schema.json": "Artifact schema",
        "src/modeling_harness/schemas/v3/evidence/graph.schema.json": "Evidence Graph schema",
        "src/modeling_harness/schemas/v3/decision/decision.schema.json": "Decision schema",
    }
    missing = []
    for path, desc in required.items():
        if not (project_path / path).exists():
            missing.append(desc)
    if missing:
        return False, f"缺失必要产物 schema: {', '.join(missing)}"
    return True, "V3 必要 schema 完整"


def check_knowledge_completeness(project_path):
    """L3.2: 检查知识库完整性（V3：src/modeling_harness/knowledge 子目录）"""
    checks = []
    for sub in ("methodology", "cookbooks", "methods", "failures",
                "patterns", "pitfalls", "validation", "playbooks"):
        d = project_path / "src" / "modeling_harness" / "knowledge" / sub
        if d.exists():
            n = len(list(d.glob("*.md"))) + len(list(d.glob("*.yaml")))
            checks.append(f"knowledge/{sub}: {n}个文件")
    if not checks:
        return True, "知识库目录未就绪（跳过统计）"
    return True, "; ".join(checks)


def check_laws_not_empty(project_path):
    """L3.3: 检查 V3 角色定义与 validator 目录非空"""
    empty = []
    roles_dir = project_path / "src" / "modeling_harness" / "roles"
    if roles_dir.exists():
        role_files = sorted(roles_dir.glob("*.yaml"))
        if not role_files:
            empty.append("modeling_harness/roles 无角色定义")
        for rf in role_files:
            if rf.stat().st_size == 0:
                empty.append(f"{rf.name} 为空")
    else:
        empty.append("modeling_harness/roles 目录缺失")
    if empty:
        return False, "; ".join(empty)
    return True, "V3 角色定义完整"



def check_figure_refs(project_path):
    """L6.3: 检查模型描述文档（*.md）中的图表/Mermaid 引用完整性（V3）。"""
    live = _live_project_dirs(project_path)
    if not live:
        return True, "跳过：无活跃项目实例"
    problems = []
    checked = 0
    for pdir in live:
        mdocs = sorted(pdir.glob("*.md"))
        if not mdocs:
            continue
        checked += 1
        for d in mdocs:
            try:
                content = d.read_text(encoding="utf-8")
            except Exception:
                continue
            # Mermaid 块必须闭合
            if content.count("```mermaid") != content.count("```"):
                problems.append(f"{pdir.name}/{d.name}: Mermaid 代码块未闭合")
            # 图片引用必须指向存在的本地文件
            for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", content):
                src = m.group(2).split("#")[0].strip()
                if src and not (pdir / src).exists() and not src.startswith("http"):
                    problems.append(f"{pdir.name}/{d.name}: 图片引用不存在 {src}")
    if problems:
        return False, "; ".join(problems[:5])
    return True, f"图表引用检查通过（{checked} 个活跃项目）"


def check_question_spec_schema(project_path):
    """L1.1: 检查活跃项目的输入规约（V3：inputs/question_spec.json 或 problem.txt）。

    question_spec.json 必须为有效 JSON 且顶层为 object（与
    runtime/modeling/problem_repr.py 的解析契约一致）；两者皆缺 → 失败。
    V2 归档 schema（schemas/retired/question_spec.schema.json）不参与校验。
    """
    live = _live_project_dirs(project_path)
    if not live:
        return True, "无活跃项目（库模式，跳过）"
    checked = 0
    for p in sorted(live, key=lambda d: d.name):
        spec = p / "inputs" / "question_spec.json"
        txt = p / "inputs" / "problem.txt"
        if spec.exists():
            try:
                raw = json.loads(spec.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                return False, f"{p.name}/inputs/question_spec.json 无法解析: {e}"
            if not isinstance(raw, dict):
                return False, f"{p.name}/inputs/question_spec.json 顶层必须是 object"
            checked += 1
        elif txt.exists():
            checked += 1
        else:
            return False, (f"{p.name} 缺少输入规约"
                           f"（inputs/question_spec.json 或 inputs/problem.txt）")
    return True, f"输入规约检查通过（{checked} 个活跃项目）"


def check_symbol_registry(project_path):
    """L1.2: 检查符号注册表"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "symbol_registry.py"
    if not py_path.exists():
        return False, "symbol_registry.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class SymbolRegistry" not in content:
        return False, "缺少SymbolRegistry类"
    return True, "符号注册表存在"


def check_assumption_validator(project_path):
    """L1.3: 检查假设验证器"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "assumption_validator.py"
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
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "type_system.py"
    if not py_path.exists():
        return False, "type_system.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class TypeSystem" not in content:
        return False, "缺少TypeSystem类"
    return True, "类型系统存在"


def check_formula_checker(project_path):
    """L2.2: 检查公式检查器"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "formula_checker.py"
    if not py_path.exists():
        return False, "formula_checker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class FormulaChecker" not in content:
        return False, "缺少FormulaChecker类"
    return True, "公式检查器存在"


def check_output_validator(project_path):
    """L2.3: 检查输出验证器"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "output_validator.py"
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
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "invariant_tracker.py"
    if not py_path.exists():
        return False, "invariant_tracker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class InvariantTracker" not in content:
        return False, "缺少InvariantTracker类"
    return True, "不变式跟踪存在"


def check_contract_checker(project_path):
    """L3.2: 检查契约校验"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "contract_checker.py"
    if not py_path.exists():
        return False, "contract_checker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class ContractChecker" not in content:
        return False, "缺少ContractChecker类"
    return True, "契约校验存在"


def check_stage_gate(project_path):
    """L3.3: 检查阶段门禁"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "stage_gate.py"
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
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "symbolic_verifier.py"
    if not py_path.exists():
        return False, "symbolic_verifier.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class SymbolicVerifier" not in content:
        return False, "缺少SymbolicVerifier类"
    return True, "符号验证器存在"


def check_cross_model_checker(project_path):
    """L4.2: 检查异构模型"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "cross_model_checker.py"
    if not py_path.exists():
        return False, "cross_model_checker.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class CrossModelChecker" not in content:
        return False, "缺少CrossModelChecker类"
    return True, "异构模型检查存在"


def check_consistency_checker(project_path):
    """L4.3: 检查一致性校验"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "consistency_checker.py"
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
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "trust_domain.py"
    if not py_path.exists():
        return False, "trust_domain.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class TrustDomain" not in content:
        return False, "缺少TrustDomain类"
    return True, "信任域定义存在"


def check_permission_guard(project_path):
    """L5.2: 检查权限守卫"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "permission_guard.py"
    if not py_path.exists():
        return False, "permission_guard.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class PermissionGuard" not in content:
        return False, "缺少PermissionGuard类"
    return True, "权限守卫存在"


def check_incremental_checker(project_path):
    """L5.3: 检查增量校验"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "incremental_checker.py"
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
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "hash_chain.py"
    if not py_path.exists():
        return False, "hash_chain.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class HashChain" not in content:
        return False, "缺少HashChain类"
    return True, "哈希追溯链存在"


def check_error_attribution(project_path):
    """L6.9: 检查错误归因"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "error_attribution.py"
    if not py_path.exists():
        return False, "error_attribution.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class ErrorAttribution" not in content:
        return False, "缺少ErrorAttribution类"
    return True, "错误归因存在"


def check_rule_iterator(project_path):
    """L6.10: 检查规则迭代"""
    py_path = project_path / "src" / "modeling_harness" / "validators" / "modules" / "rule_iterator.py"
    if not py_path.exists():
        return False, "rule_iterator.py不存在"
    content = py_path.read_text(encoding="utf-8")
    if "class RuleIterator" not in content:
        return False, "缺少RuleIterator类"
    return True, "规则迭代存在"


def check_numeric_traceability(project_path):
    """L4: 所有数值可追溯到已验证的 Result Artifact（V3：模型描述文档数值 vs all_results.json）。"""
    live = _live_project_dirs(project_path)
    if not live:
        return True, "无活跃项目实例（跳过）"
    results_files = list(iter_repo(project_path, "all_results.json"))
    if not results_files:
        return True, "未找到 all_results.json（跳过）"
    all_nums = {}
    for rf in results_files:
        try:
            data = json.loads(rf.read_text(encoding="utf-8"))
        except Exception:
            continue
        def extract_numbers(obj, prefix=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    extract_numbers(v, f"{prefix}.{k}" if prefix else k)
            elif isinstance(obj, list):
                for idx, v in enumerate(obj):
                    extract_numbers(v, f"{prefix}[{idx}]")
            elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
                all_nums[prefix] = obj
        extract_numbers(data)

    if not all_nums:
        return True, "all_results.json 无数值（跳过）"

    # 从模型描述文档（*.md）中提取数值
    md_numbers = set()
    for pdir in live:
        for md_file in pdir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                found = re.findall(r"\b\d+\.?\d*(?:[eE][+-]?\d+)?\b", content)
                for n in found:
                    try:
                        md_numbers.add(float(n))
                    except ValueError:
                        pass
            except OSError:
                pass

    if not md_numbers:
        return True, "模型描述文档中无数值（跳过）"

    json_values = list(all_nums.values())
    tol_rel = float(_env_get("runtime.numeric_tolerance_rel", 0.005))
    tol_abs = float(_env_get("runtime.numeric_tolerance_abs", 0.01))
    min_ratio = float(_env_get("runtime.traceability_min_ratio", 0.90))

    traced = 0
    for mv in md_numbers:
        for jv in json_values:
            if isinstance(jv, (int, float)):
                if abs(mv - jv) <= max(abs(jv) * tol_rel, tol_abs):
                    traced += 1
                    break

    ratio = traced / len(md_numbers) if md_numbers else 0
    if ratio < min_ratio:
        return False, f"数值追溯比例={ratio:.1%}<{min_ratio:.0%}(需≥{min_ratio:.0%})"
    return True, f"数值追溯比例={ratio:.1%}(≥{min_ratio:.0%})"


def check_physics_model(project_path):
    """L4: 物理模型检查（V3：模型描述文档坐标系/几何判据/解析验证等）。"""
    live = _live_project_dirs(project_path)
    if not live:
        return True, "无活跃项目实例（跳过）"
    md_files = []
    for pdir in live:
        md_files.extend(pdir.glob("*.md"))

    if not md_files:
        return True, "无模型描述文档（跳过）"

    physics_keywords = [
        "运动", "速度", "加速度", "力", "能量", "动量", "角速度", "角动量",
        "轨迹", "碰撞", "反射", "折射", "坐标", "几何", "角度", "距离",
        "velocity", "acceleration", "force", "energy", "momentum", "trajectory",
        "collision", "reflection", "coordinate", "geometry", "angle", "distance",
    ]

    all_content = ""
    for md_file in md_files:
        try:
            all_content += md_file.read_text(encoding="utf-8")
        except OSError:
            pass

    has_physics = any(kw in all_content.lower() for kw in physics_keywords)
    if not has_physics:
        return True, "不涉及物理过程（跳过物理模型检查）"

    checks = []
    coord_keywords = ["坐标系", "坐标轴", "原点", "x轴", "y轴", "z轴", "coordinate system", "x-axis", "y-axis"]
    checks.append(("坐标系定义", any(kw in all_content.lower() for kw in coord_keywords)))

    geometry_keywords = ["几何关系", "几何条件", "判据", "几何约束", "geometric", "criterion"]
    checks.append(("几何判据", any(kw in all_content.lower() for kw in geometry_keywords)))

    analytical_keywords = ["解析解", "精确解", "验证", "analytical solution", "exact solution", "closed form"]
    checks.append(("解析验证", any(kw in all_content.lower() for kw in analytical_keywords)))

    decomposition_keywords = ["分解", "分量", "水平", "竖直", "切向", "法向", "decomposition", "component", "horizontal", "vertical"]
    checks.append(("运动分解", any(kw in all_content.lower() for kw in decomposition_keywords)))

    temporal_keywords = ["时间步", "时序", "先后", "因果", "time step", "temporal", "causal", "sequence"]
    checks.append(("时序因果", any(kw in all_content.lower() for kw in temporal_keywords)))

    consistency_keywords = ["一致", "校对", "验证", "对比", "consistent", "verify", "cross-check"]
    checks.append(("坐标一致性", any(kw in all_content.lower() for kw in consistency_keywords)))

    failed = [name for name, ok in checks if not ok]
    if failed:
        return False, f"物理模型检查缺失: {', '.join(failed)}"
    return True, "物理模型 6 项检查通过"


def check_documentation_completeness(project_path):
    """L6.11: 检查文档完整性（V3）"""
    required_docs = [
        "docs/ARCHITECTURE.md",
        "README.md",
        "AGENTS.md",
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
        return True, "跳过：无活跃项目实例"
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
        return True, "跳过：无活跃项目实例"
    code_files = list(iter_repo(project_path, "*.py"))
    found_seed = False

    for py_file in code_files[:10]:
        try:
            content = py_file.read_text(encoding="utf-8")
            if "seed" in content.lower() and ("42" in content or "random" in content.lower()):
                found_seed = True
                break
        except Exception:
            pass

    if found_seed:
        return True, "发现随机种子设置"
    return False, "未设置随机种子"


def check_directory_structure(project_path):
    """目录结构检查（V3：runtime / roles / validators / workflows）"""
    required_dirs = [
        "src/modeling_harness/runtime", "src/modeling_harness/roles", "src/modeling_harness/validators", "src/modeling_harness/workflows",
        "src/modeling_harness/schemas", "src/modeling_harness/knowledge", "src/modeling_harness/knowledge/methodology",
        "src/modeling_harness/validators/modules", "src/modeling_harness/cli", "tests",
    ]
    missing = [d for d in required_dirs if not (project_path / d).exists()]
    if missing:
        return False, f"缺失目录: {', '.join(missing)}"
    return True, "V3 目录结构完整"


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
    loader_path = project_path / "src" / "modeling_harness" / "env" / "loader.py"
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

def check_validator_modules_importable(project_path):
    """L6: validator modules 必须可导入且有校验入口（audit FIX-5.1 / P1-16）。

    替换"字符串存在性检查"：对 src/modeling_harness/validators/modules/ 下每个模块做真实
    包路径 import + 冒烟（暴露顶层可调用对象 check/validate/evaluate/
    类等）。import 失败或无任何可调用入口 = 死代码，如实报告。接线状态
    （哪些已接入 DAG 节点）在 STATUS.md 声明，这里只保证模块本身可运行。
    """
    import importlib
    import sys
    mods_dir = project_path / "src" / "modeling_harness" / "validators" / "modules"
    if not mods_dir.exists():
        return False, "src/modeling_harness/validators/modules 目录不存在"
    py_files = sorted(p for p in mods_dir.glob("*.py")
                      if not p.name.startswith("_"))
    if not py_files:
        return False, "validator modules 为空"
    core_dir = str(project_path / "src")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    broken = []
    loaded = 0
    for py in py_files:
        try:
            module = importlib.import_module(
                "modeling_harness.validators.modules." + py.stem)
            loaded += 1
            entries = [n for n, v in vars(module).items()
                       if not n.startswith("_") and callable(v)]
            if not entries:
                broken.append(py.name + ": 无顶层可调用对象")
        except Exception as e:
            broken.append(py.name + ": import 失败 " + str(e))
    if broken:
        return False, str(len(broken)) + "/" + str(len(py_files)) \
            + " validator modules 死代码: " + "; ".join(broken[:5])
    return True, str(loaded) + " 个 validator modules 可导入且有顶层可调用入口"


def check_env_config_exists(project_path):
    """L1: env 配置三件套存在（config.yaml / loader.py / README.md）"""
    required = ["src/modeling_harness/env/config.yaml", "src/modeling_harness/env/loader.py", "src/modeling_harness/env/README.md"]
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
        "code": ["random_seed", "multi_run_count", "solver_timeout_small"],
        "modeling": ["min_candidate_models", "assumption_score_threshold"],
        "review": ["max_rounds", "pass_score"],
        "runtime": ["language", "strict_mode", "numeric_tolerance_rel"],
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
# L5: 正文质量护栏检查
# ======================================================================





def validate_project(project_path):
    """运行所有验证检查"""
    project_path = Path(project_path)

    print("=" * 60)
    print("Modeling-Harness 六层防御验证")
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

        # L6: 事后验证
        ("L6", "目录结构", lambda: check_directory_structure(project_path)),
        ("L6", "Python语法", lambda: check_python_syntax(project_path)),
        ("L6", "结果文件", lambda: check_results_ledger(project_path)),
        ("L6", "随机种子", lambda: check_random_seed(project_path)),
        ("L6", "图表引用", lambda: check_figure_refs(project_path)),

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
        ("L6", "validator模块冒烟", lambda: check_validator_modules_importable(project_path)),
        ("L6", "文档完整性", lambda: check_documentation_completeness(project_path)),
        ("L6", "测试覆盖率", lambda: check_test_coverage(project_path)),

        # L1: env 配置层（UTG 多 Agent 架构演进）
        ("L1", "env配置文件", lambda: check_env_config_exists(project_path)),
        ("L1", "env加载器", lambda: check_env_loader_importable(project_path)),
        ("L1", "env配置字段", lambda: check_env_config_fields(project_path)),
        # L1: V3 产出物（MODEL_IR + 模型描述文档）
        ("L1", "MODEL_IR schema", lambda: check_model_ir(project_path)),
        ("L1", "模型描述文档", lambda: check_model_doc(project_path)),
        # L1: catalog / AGENTS.md 一致性
        ("L1", "catalog.yaml", lambda: check_catalog_yaml(project_path)),
        ("L1", "AGENTS.md", lambda: check_agents_md(project_path)),
        # L6: Checkpoint 格式检查
        ("L6", "checkpoint格式", lambda: check_checkpoint_format(project_path)),
    ]

    # WARN 级检查：不通过只记警告、不阻塞交付。
    # 对应 P2 增强性门禁（此前被当作硬失败，导致
    # "0 警告" 与失败列表里出现 WARN 项自相矛盾）。
    WARN_CHECKS = set()

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

def check_model_ir(project_path):
    """L1: V3 产出物——projects/<p>/model_ir.json 存在且通过 schema（如 schema 存在）。"""
    live = _live_project_dirs(project_path)
    if not live:
        return True, "跳过：无活跃项目实例"
    schema_path = project_path / "src" / "modeling_harness" / "schemas" / "v3" / "model" / "model_ir.schema.json"
    import json as _json
    problems = []
    checked = 0
    for pdir in live:
        mir = pdir / "model_ir.json"
        if not mir.exists():
            problems.append(f"{pdir.name}: model_ir.json 缺失")
            continue
        checked += 1
        try:
            data = _json.loads(mir.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{pdir.name}: model_ir.json 解析失败 ({exc})")
            continue
        if not isinstance(data, dict) or "model_family" not in data:
            problems.append(f"{pdir.name}: model_ir.json 缺 model_family")
        if schema_path.exists():
            try:
                import jsonschema
                jsonschema.validate(data, _json.loads(
                    schema_path.read_text(encoding="utf-8")))
            except ImportError:
                pass
            except Exception as exc:
                problems.append(f"{pdir.name}: model_ir.json schema 校验失败 ({exc})")
    if problems:
        return False, "; ".join(problems[:5])
    return True, f"MODEL_IR 校验通过（{checked} 个活跃项目）"


def check_model_doc(project_path):
    """L1: V3 产出物——projects/<p>/ 模型描述文档（*.md 含 Mermaid 或结构化描述）。"""
    live = _live_project_dirs(project_path)
    if not live:
        return True, "跳过：无活跃项目实例"
    problems = []
    checked = 0
    for pdir in live:
        mdocs = sorted(pdir.glob("*.md"))
        if not mdocs:
            problems.append(f"{pdir.name}: 无模型描述文档（*.md）")
            continue
        checked += 1
        if not any("```mermaid" in d.read_text(encoding="utf-8", errors="ignore")
                   for d in mdocs):
            problems.append(f"{pdir.name}: 模型描述文档缺 Mermaid 图")
    if problems:
        return False, "; ".join(problems[:5])
    return True, f"模型描述文档通过（{checked} 个活跃项目）"


def check_catalog_yaml(project_path):
    """L1: catalog 视图一致性（V3：v3 视图 roles/nodes/validators）"""
    content = None
    for p in ("src/modeling_harness/catalog/v3.yaml",
                   "src/modeling_harness/catalog/catalog.yaml"):
        fp = project_path / p
        if fp.exists():
            content = fp.read_text(encoding="utf-8", errors="ignore")
            break
    if content is None:
        return False, "src/modeling_harness/catalog/v3.yaml 缺失"
    for key in ("roles:", "nodes:", "validators:"):
        if not re.search(rf"^[ ]+{key}[ ]*(#.*)?$", content, re.MULTILINE):
            return False, f"catalog v3 节缺少 {key.rstrip(':')}"
    return True, "catalog v3 视图齐全（roles/nodes/validators）"


def check_agents_md(project_path):
    """L1: AGENTS.md 存在且含 V3 关键章节"""
    fp = project_path / "AGENTS.md"
    if not fp.exists():
        return False, "AGENTS.md 缺失"
    text = fp.read_text(encoding="utf-8", errors="ignore")
    for sec in ("## 核心定位", "## 目录结构", "## 不可违反的规则"):
        if sec not in text:
            return False, f"AGENTS.md 缺少章节: {sec}"
    return True, "AGENTS.md V3 章节齐全"


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
        if data["hand"] not in ["analyst", "modeler", "experimenter", "critic"]:
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
    project_path = str(Path(__file__).resolve().parent.parent.parent.parent)
    success = validate_project(project_path)
    sys.exit(0 if success else 1)
