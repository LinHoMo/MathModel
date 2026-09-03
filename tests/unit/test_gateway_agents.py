"""
6 个门禁 agent 的 Self-Check 升级测试

测试对象：UTG L4/L5/L6 承载的 6 个门禁 agent 的 SKILL.md：
  - Modeler/spec-auditor（L5+L6）
  - Programmer/guardrails-checker（L5）
  - Programmer/hash-auditor（L6）
  - Writer/consistency-checker（L4）
  - Writer/guardrails-checker（L5）
  - Writer/final-validator（L6）

本轮升级内容：
  - [HARD] / [WARN] 标签分级（Self-Check 区分硬阻塞与建议项）
  - 对接 validate_project.py: check_<函数>（从描述性门禁升级到可执行门禁）
  - 新增"运行可执行门禁"Step（py validate_project.py --project ...）

测试从项目根目录运行（pytest 根目录为项目根）。
"""
import os
import re

import pytest


# ---------------------------------------------------------------------------
# 6 个门禁 agent 的 SKILL.md 相对路径
# ---------------------------------------------------------------------------
GATEWAY_AGENT_SKILLS = [
    os.path.join("core", "Modeler", "agents", "spec-auditor", "SKILL.md"),
    os.path.join("core", "Programmer", "agents", "guardrails-checker", "SKILL.md"),
    os.path.join("core", "Programmer", "agents", "hash-auditor", "SKILL.md"),
    os.path.join("core", "Writer", "agents", "consistency-checker", "SKILL.md"),
    os.path.join("core", "Writer", "agents", "guardrails-checker", "SKILL.md"),
    os.path.join("core", "Writer", "agents", "final-validator", "SKILL.md"),
]


def _read(path):
    """读取文件文本（UTF-8）。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class TestGatewayAgentsHardWarn:
    """6 个门禁 agent 的 SKILL.md 含 [HARD] 和 [WARN] 标签"""

    def test_all_skills_exist(self):
        """6 个 SKILL.md 文件全部存在"""
        missing = [p for p in GATEWAY_AGENT_SKILLS if not os.path.exists(p)]
        assert missing == [], f"门禁 agent SKILL.md 缺失: {missing}"

    def test_all_skills_have_hard_tag(self):
        """每个门禁 agent SKILL.md 含 [HARD] 标签"""
        missing = []
        for skill_path in GATEWAY_AGENT_SKILLS:
            assert os.path.exists(skill_path), f"{skill_path} 不存在"
            content = _read(skill_path)
            if "[HARD]" not in content:
                missing.append(skill_path)
        assert missing == [], f"缺 [HARD] 标签: {missing}"

    def test_all_skills_have_warn_tag(self):
        """每个门禁 agent SKILL.md 含 [WARN] 标签"""
        missing = []
        for skill_path in GATEWAY_AGENT_SKILLS:
            assert os.path.exists(skill_path), f"{skill_path} 不存在"
            content = _read(skill_path)
            if "[WARN]" not in content:
                missing.append(skill_path)
        assert missing == [], f"缺 [WARN] 标签: {missing}"

    def test_hard_count_ge_warn_count(self):
        """[HARD] 标签数 >= [WARN] 标签数（硬门禁不少于建议项）"""
        for skill_path in GATEWAY_AGENT_SKILLS:
            content = _read(skill_path)
            n_hard = len(re.findall(r"\[HARD\]", content))
            n_warn = len(re.findall(r"\[WARN\]", content))
            assert n_hard >= 1, f"{skill_path}: [HARD] 数为 0"
            assert n_warn >= 1, f"{skill_path}: [WARN] 数为 0"
            assert n_hard >= n_warn, \
                f"{skill_path}: [HARD]={n_hard} < [WARN]={n_warn}（硬门禁应不少于建议项）"


class TestGatewayAgentsCheckMapping:
    """6 个门禁 agent 的 SKILL.md 含 validate_project.py: check_ 对接（每个至少 3 处）"""

    def test_all_skills_reference_check_functions(self):
        """每个门禁 agent SKILL.md 至少 3 处 validate_project.py: check_ 对接"""
        mapping_pattern = re.compile(r"validate_project\.py:\s*check_\w+")
        insufficient = []
        for skill_path in GATEWAY_AGENT_SKILLS:
            content = _read(skill_path)
            matches = mapping_pattern.findall(content)
            if len(matches) < 3:
                insufficient.append(f"{skill_path}: {len(matches)} 处（需>=3）")
        assert insufficient == [], \
            f"validate_project.py 对接不足: {insufficient}"

    def test_check_mapping_format(self):
        """对接格式为 validate_project.py: check_<函数名>"""
        pat = re.compile(r"validate_project\.py:\s*check_([a-z_]+)")
        for skill_path in GATEWAY_AGENT_SKILLS:
            content = _read(skill_path)
            matches = pat.findall(content)
            # 每个匹配到的函数名应是合法标识符（小写字母+下划线）
            for fn in matches:
                assert re.fullmatch(r"[a-z][a-z_]*", fn), \
                    f"{skill_path}: 非法 check 函数名 {fn}"

    def test_known_check_functions_referenced(self):
        """对接的 check_ 函数名是 validate_project.py 中真实存在的 36 个之一"""
        # validate_project.py 的 36 个 check 函数名（完整集合）
        known_fns = {
            "check_pdf", "check_placeholders", "check_forbidden_words",
            "check_citation_integrity", "check_figure_refs", "check_python_syntax",
            "check_code_in_code_dir", "check_directory_structure",
            "check_reproducibility", "check_numeric_traceability",
            "check_results_ledger", "check_paper_pages", "check_paper_words",
            "check_paper_figures", "check_paper_tables", "check_paper_equations",
            "check_paper_references", "check_bib", "check_source",
            "check_paper_structure", "check_table_figure_analysis",
            "check_assumptions_necessity", "check_sensitivity_analysis",
            "check_model_evaluation", "check_code_template_usage",
            "check_coordinate_system", "check_analysis_report_physics",
            "check_code_coordinate_consistency", "check_geometry_criterion",
            "check_analytic_validation", "check_time_bounds",
            "check_code_comments", "check_imports",             "check_verify_report",
            "check_problem_type_specific", "check_tables_in_tables_dir",
            # 升级新增的真实 check 函数
            "check_abstract_words", "check_body_no_lists", "check_body_chinese_list",
            "check_figure_as_subject",
            "check_inline_table_rows", "check_internal_terms_leak", "check_recent_refs",
            "check_deliverables_size", "check_no_undefined_refs",
            "check_consecutive_same_opening", "check_phrase_frequency", "check_too_perfect",
            # 引用/摘要格式新增（Request B：GB/T 7714 + 关键词）
            "check_citation_format", "check_abstract_keywords",
            # final-validator 列为 HARD 门禁、此前缺失实现，现已补齐
            "check_pdf_compile_chain", "check_page_fill_ratio",
        }
        # 捕获完整 check_ 函数名（含 check_ 前缀）
        pat = re.compile(r"validate_project\.py:\s*(check_[a-z_]+)")
        unknown = []
        for skill_path in GATEWAY_AGENT_SKILLS:
            content = _read(skill_path)
            for fn in pat.findall(content):
                if fn not in known_fns:
                    unknown.append(f"{skill_path}: {fn}")
        assert unknown == [], f"对接了未知的 check 函数: {unknown}"


class TestGatewayAgentsExecutableStep:
    """6 个门禁 agent 的 SKILL.md 含"运行可执行门禁"Step"""

    def test_all_skills_have_executable_step(self):
        """每个门禁 agent SKILL.md 含"运行可执行门禁"Step 标题"""
        missing = []
        for skill_path in GATEWAY_AGENT_SKILLS:
            content = _read(skill_path)
            # 匹配 ### Step N: 运行可执行门禁 或 ## Step ... 运行可执行门禁
            if not re.search(r"运行可执行门禁", content):
                missing.append(skill_path)
        assert missing == [], f"缺'运行可执行门禁'Step: {missing}"

    def test_executable_step_is_heading(self):
        """'运行可执行门禁' 出现在 Step 标题中（### Step N: 运行可执行门禁）"""
        # 放宽：至少有 1 个 SKILL.md 把它作为标题
        # 严格：每个都应作为 Step 标题
        pat = re.compile(r"^#+\s*Step\s+\d+\s*[:：]\s*运行可执行门禁", re.MULTILINE)
        non_heading = []
        for skill_path in GATEWAY_AGENT_SKILLS:
            content = _read(skill_path)
            if not pat.search(content):
                non_heading.append(skill_path)
        assert non_heading == [], \
            f"'运行可执行门禁' 未作为 Step 标题: {non_heading}"

    def test_executable_step_invokes_validate_project(self):
        """'运行可执行门禁' Step 含 py validate_project.py --project 调用指令"""
        pat = re.compile(r"validate_project\.py\s+--project")
        missing = []
        for skill_path in GATEWAY_AGENT_SKILLS:
            content = _read(skill_path)
            if not pat.search(content):
                missing.append(skill_path)
        assert missing == [], \
            f"'运行可执行门禁'Step 缺 validate_project.py --project 调用: {missing}"

    def test_executable_step_mentions_hard_pass(self):
        """'运行可执行门禁' Step 提及 HARD 检查须 PASS"""
        for skill_path in GATEWAY_AGENT_SKILLS:
            content = _read(skill_path)
            # 找到"运行可执行门禁"附近文本
            idx = content.find("运行可执行门禁")
            assert idx >= 0, f"{skill_path} 缺'运行可执行门禁'"
            # 取该 Step 后 500 字符窗口检查是否提及 HARD / PASS
            window = content[idx: idx + 600]
            assert "HARD" in window or "PASS" in window, \
                f"{skill_path}: '运行可执行门禁'Step 未提及 HARD/PASS 检查"
