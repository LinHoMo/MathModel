"""
validate_project.py 结构与可导入性测试

测试对象：项目根目录下的 validate_project.py（49 检查函数 + HARD/WARN/PASS 分级 + 题型触发）。
本轮为补门禁质量新增的可执行检查脚本，本测试只验证其结构完整与可加载性，
不实际执行检查（避免依赖具体 projects/<项目>/ 产物）。

测试从项目根目录运行（pytest 根目录为项目根）。
"""
import importlib.util
import os
import re
import subprocess
import sys

import pytest


# ---------------------------------------------------------------------------
# 被测文件路径
# ---------------------------------------------------------------------------
VALIDATE_PROJECT_PATH = os.path.join(os.getcwd(), "core", "tools", "validate_project.py")


# ---------------------------------------------------------------------------
# 49 个检查函数名清单（与 validate_project.py 的 CHECKS 列表一一对应）
# 关键函数：check_pdf/check_placeholders/check_numeric_traceability/
#           check_python_syntax/check_paper_pages 等
# 注：第 8 组 6 个为对标升级（mmagent-codex-main）新增检查函数
# ---------------------------------------------------------------------------
EXPECTED_CHECK_FUNCTIONS = [
    # 第 1 组：Required artifacts（4）
    "check_pdf", "check_source", "check_bib", "check_results_ledger",
    # 第 2 组：Content quality（11）
    "check_placeholders", "check_forbidden_words", "check_verify_report",
    "check_citation_integrity", "check_figure_refs", "check_paper_structure",
    "check_sensitivity_analysis", "check_model_evaluation",
    "check_assumptions_necessity", "check_table_figure_analysis",
    "check_problem_type_specific",
    # 第 3 组：Reproducibility（3）
    "check_reproducibility", "check_numeric_traceability", "check_code_template_usage",
    # 第 4 组：Physics model（6，题型触发）
    "check_coordinate_system", "check_analysis_report_physics",
    "check_code_coordinate_consistency", "check_geometry_criterion",
    "check_analytic_validation", "check_time_bounds",
    # 第 5 组：Directory structure（3）
    "check_directory_structure", "check_code_in_code_dir", "check_tables_in_tables_dir",
    # 第 6 组：Code quality（3）
    "check_python_syntax", "check_code_comments", "check_imports",
    # 第 7 组：Env thresholds（6）
    "check_paper_pages", "check_paper_words", "check_paper_figures",
    "check_paper_tables", "check_paper_equations", "check_paper_references",
    # 第 8 组：Writing guardrails / 新增检查（13，含升级新增 5 个 + 引用/摘要格式 2 个）
    "check_body_no_lists", "check_figure_as_subject", "check_internal_terms_leak",
    "check_abstract_words", "check_recent_refs", "check_inline_table_rows",
    "check_consecutive_same_opening", "check_phrase_frequency", "check_too_perfect",
    "check_deliverables_size", "check_no_undefined_refs",
    "check_citation_format", "check_abstract_keywords",
]


def _read_validate_project_source():
    """读取 validate_project.py 源码文本。"""
    with open(VALIDATE_PROJECT_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestValidateProjectStructure:
    """validate_project.py 文件结构完整性"""

    def test_file_exists(self):
        """validate_project.py 存在"""
        assert os.path.isfile(VALIDATE_PROJECT_PATH), \
            "validate_project.py 不存在"

    def test_main_function_exists(self):
        """含 main 函数（argparse 入口）"""
        src = _read_validate_project_source()
        assert re.search(r"^def\s+main\s*\(", src, re.MULTILINE), \
            "validate_project.py 缺少 main 函数"

    def test_main_entry_guard(self):
        """含 if __name__ == '__main__' 入口守卫"""
        src = _read_validate_project_source()
        assert '__name__' in src and "__main__" in src, \
            "validate_project.py 缺少 __main__ 入口守卫"

    def test_36_check_functions_exist(self):
        """49 个检查函数全部存在（关键函数抽样 + 总数核对）"""
        src = _read_validate_project_source()
        missing = []
        for fn_name in EXPECTED_CHECK_FUNCTIONS:
            # 匹配 def check_xxx(
            pat = r"^def\s+%s\s*\(" % re.escape(fn_name)
            if not re.search(pat, src, re.MULTILINE):
                missing.append(fn_name)
        assert missing == [], f"validate_project.py 缺少检查函数: {missing}"
        # 总数核对：用基线断言（>=49）而非硬编码相等，
        # 否则每新增一个检查函数都要改测试，反而掩盖真实回归。
        all_check_fns = re.findall(r"^def\s+(check_\w+)\s*\(", src, re.MULTILINE)
        assert len(all_check_fns) >= 49, \
            f"check_ 函数总数不应少于基线 49，实际 {len(all_check_fns)}"
        # 每个定义的 check_ 函数都应被登记进 CHECKS，避免"定义了但没跑"
        registered = set(re.findall(r"\b(check_\w+)\b(?!\s*\()", src.split("CHECKS = [")[-1]))
        orphan = [f for f in all_check_fns if f not in registered]
        assert not orphan, f"定义了但未注册进 CHECKS 的检查函数: {orphan}"

    def test_hard_warn_pass_grading(self):
        """含 HARD/WARN/PASS 三级分级机制（_hard/_warn/_pas 辅助函数）"""
        src = _read_validate_project_source()
        # 常量定义（validate_project.py 用元组解包：HARD, WARN, PASS = "HARD", "WARN", "PASS"）
        assert re.search(r"\bHARD\b.*=.*['\"]HARD['\"]", src), "缺少 HARD 常量定义"
        assert re.search(r"\bWARN\b.*=.*['\"]WARN['\"]", src), "缺少 WARN 常量定义"
        assert re.search(r"\bPASS\b.*=.*['\"]PASS['\"]", src), "缺少 PASS 常量定义"
        # 辅助函数
        assert re.search(r"^def\s+_hard\s*\(", src, re.MULTILINE), "缺少 _hard 函数"
        assert re.search(r"^def\s+_warn\s*\(", src, re.MULTILINE), "缺少 _warn 函数"
        assert re.search(r"^def\s+_pas\s*\(", src, re.MULTILINE), "缺少 _pas 函数"

    def test_problem_type_trigger(self):
        """含题型触发机制（_detect_problem_type 或 is_physics 标志）"""
        src = _read_validate_project_source()
        assert re.search(r"^def\s+_detect_problem_type\s*\(", src, re.MULTILINE), \
            "缺少 _detect_problem_type 函数"
        # 题型触发标志
        assert "_IS_PHYSICS" in src or "is_physics" in src, \
            "缺少 is_physics / _IS_PHYSICS 题型触发标志"
        # 物理关键词列表
        assert "PHYSICS_KEYWORDS" in src, "缺少 PHYSICS_KEYWORDS 关键词列表"

    def test_env_threshold_injection(self):
        """含 env 阈值动态注入（_env_get 辅助函数）"""
        src = _read_validate_project_source()
        assert re.search(r"^def\s+_env_get\s*\(", src, re.MULTILINE), \
            "缺少 _env_get 函数"
        assert re.search(r"^def\s+_load_env_loader\s*\(", src, re.MULTILINE), \
            "缺少 _load_env_loader 函数"

    def test_checks_grouped(self):
        """CHECKS 列表把 36 个检查函数分 7 组"""
        src = _read_validate_project_source()
        # CHECKS 列表存在
        assert re.search(r"^CHECKS\s*=\s*\[", src, re.MULTILINE), "缺少 CHECKS 列表"
        # 7 个分组名
        groups = ["Required artifacts", "Content quality", "Reproducibility",
                  "Physics model", "Directory structure", "Code quality",
                  "Env thresholds"]
        for g in groups:
            assert g in src, f"CHECKS 缺少分组: {g}"


class TestValidateProjectImportable:
    """validate_project.py 可被 importlib 动态加载（不实际跑检查）"""

    def test_module_loadable(self):
        """用 importlib 动态加载 validate_project.py，不报错"""
        assert os.path.isfile(VALIDATE_PROJECT_PATH), \
            "validate_project.py 不存在，无法加载"
        spec = importlib.util.spec_from_file_location(
            "_validate_project_test", VALIDATE_PROJECT_PATH
        )
        assert spec is not None, "无法创建加载器 spec"
        assert spec.loader is not None, "spec.loader 为 None"
        module = importlib.util.module_from_spec(spec)
        # exec_module 只执行模块顶层代码（定义函数/常量），不调用 main()
        spec.loader.exec_module(module)

    def test_module_exports_check_functions(self):
        """加载后模块导出 36 个 check_ 函数"""
        spec = importlib.util.spec_from_file_location(
            "_validate_project_test2", VALIDATE_PROJECT_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for fn_name in EXPECTED_CHECK_FUNCTIONS:
            assert hasattr(module, fn_name), f"模块未导出函数: {fn_name}"
            assert callable(getattr(module, fn_name)), f"{fn_name} 不可调用"

    def test_module_exports_grading_constants(self):
        """加载后模块导出 HARD/WARN/PASS 常量"""
        spec = importlib.util.spec_from_file_location(
            "_validate_project_test3", VALIDATE_PROJECT_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert getattr(module, "HARD", None) == "HARD"
        assert getattr(module, "WARN", None) == "WARN"
        assert getattr(module, "PASS", None) == "PASS"


class TestValidateProjectHelp:
    """运行 py validate_project.py --help 退出码 0（argparse 正常）"""

    def test_help_exits_zero(self):
        """--help 应退出码 0 且输出含 usage 字样"""
        # Windows 用 py 启动器
        result = subprocess.run(
            [sys.executable, "core/tools/validate_project.py", "--help"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=30,
        )
        assert result.returncode == 0, \
            f"--help 退出码非 0: {result.returncode}\nstderr: {result.stderr}"
        # argparse --help 输出含 usage 或 optional arguments
        combined = result.stdout + result.stderr
        assert "usage" in combined.lower() or "参数" in combined, \
            f"--help 输出异常: {combined[:200]}"

    def test_help_lists_project_arg(self):
        """--help 输出含 --project 参数说明"""
        result = subprocess.run(
            [sys.executable, "core/tools/validate_project.py", "--help"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=30,
        )
        combined = result.stdout + result.stderr
        assert "--project" in combined, \
            f"--help 未列出 --project 参数: {combined[:200]}"
