"""
文件引用完整性测试
验证 SKILL.md 中引用的文件都实际存在
"""
import os
import re
import pytest


def extract_file_references(skill_md_path):
    """从 SKILL.md 中提取所有文件引用（支持跨手引用 Modeler/Programmer/Writer/ 前缀）"""
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配可选的手前缀 + knowledge/laws/templates 路径
    refs = re.findall(
        r'(?:(?:Modeler|Programmer|Writer)/)?(?:knowledge|laws|templates)/[\w/\-_.]+(?:\.md|\.py|\.yaml)',
        content,
    )
    return list(set(refs))


# 共享层路径（根 knowledge/ 下，三手共用）——按仓库根解析，不补 hand 前缀
SHARED_PREFIXES = (
    "knowledge/methodology",
    "knowledge/paper-cases",
    "core/validators/modules",
    "knowledge/templates",
    "schemas/",
    "env/",
)


def _ref_exists(ref, hand):
    """判定 SKILL.md 中的文件引用是否真实存在。

    三类路径的解析规则（重构后统一加 `core/` 前缀）：
    1. 带手前缀（Modeler/… Programmer/… Writer/…）→ `core/` + 仓库根相对
    2. 共享层（knowledge/methodology、knowledge/paper-cases、
       core/validators/modules、knowledge/templates、schemas、env）→ `core/` + 仓库根相对
    3. 本手私有层（laws/、templates/、agents/、knowledge/domain 等）→ `core/{hand}/` 前缀

    此前只实现了 1 和 3，导致 Writer/SKILL.md 中对共享层
    core/validators/modules/*.py 的引用被误判为缺失。
    """
    if ref.startswith(("Modeler/", "Programmer/", "Writer/")):
        return os.path.exists("core/" + ref)
    if ref.startswith(SHARED_PREFIXES):
        return os.path.exists("core/" + ref)
    return os.path.exists(f"core/{hand}/{ref}")


class TestModelerReferences:
    """测试 Modeler SKILL.md 中的文件引用"""
    
    def test_all_references_exist(self):
        """所有引用的文件都存在"""
        refs = extract_file_references("core/Modeler/SKILL.md")
        missing = []
        for ref in refs:
            if not _ref_exists(ref, "Modeler"):
                missing.append(ref)
        assert not missing, f"缺失文件: {missing}"


class TestProgrammerReferences:
    """测试 Programmer SKILL.md 中的文件引用"""
    
    def test_all_references_exist(self):
        """所有引用的文件都存在"""
        refs = extract_file_references("core/Programmer/SKILL.md")
        missing = []
        for ref in refs:
            if not _ref_exists(ref, "Programmer"):
                missing.append(ref)
        assert not missing, f"缺失文件: {missing}"


class TestWriterReferences:
    """测试 Writer SKILL.md 中的文件引用"""
    
    def test_all_references_exist(self):
        """所有引用的文件都存在"""
        refs = extract_file_references("core/Writer/SKILL.md")
        missing = []
        for ref in refs:
            if not _ref_exists(ref, "Writer"):
                missing.append(ref)
        assert not missing, f"缺失文件: {missing}"


class TestCrossRoleContracts:
    """测试跨角色契约完整性"""
    
    def test_model_spec_template_has_required_sections(self):
        """MODEL_SPEC 模板包含必需章节"""
        with open("core/Modeler/templates/MODEL_SPEC_TEMPLATE.md", 'r', encoding='utf-8') as f:
            content = f.read()
        required = ["问题理解", "模型假设", "符号说明", "模型选型", "模型建立", "代码实现要求", "验证要求"]
        missing = [s for s in required if s not in content]
        assert not missing, f"MODEL_SPEC 模板缺少章节: {missing}"
    
    def test_code_deliverables_template_has_required_sections(self):
        """CODE_DELIVERABLES 模板包含必需章节"""
        with open("core/Programmer/templates/CODE_DELIVERABLES_TEMPLATE.md", 'r', encoding='utf-8') as f:
            content = f.read()
        required = ["环境要求", "代码文件", "结果文件", "运行说明", "验证结果", "数值结果"]
        missing = [s for s in required if s not in content]
        assert not missing, f"CODE_DELIVERABLES 模板缺少章节: {missing}"
    
    def test_paper_spec_template_has_required_sections(self):
        """PAPER_SPEC 模板包含必需章节"""
        with open("core/Writer/templates/PAPER_SPEC_TEMPLATE.md", 'r', encoding='utf-8') as f:
            content = f.read()
        required = ["论文文件", "论文结构", "数值结果", "图表清单", "参考文献", "校验结果"]
        missing = [s for s in required if s not in content]
        assert not missing, f"PAPER_SPEC 模板缺少章节: {missing}"


class TestLawNumberingConsistency:
    """测试铁律编号一致性"""
    
    def test_modeler_laws_use_m_prefix(self):
        """Modeler 铁律使用 M 前缀"""
        with open("core/Modeler/laws/rules.md", 'r', encoding='utf-8') as f:
            content = f.read()
        assert "### M1:" in content, "Modeler 铁律应使用 M1 前缀"
        assert "### M7:" in content, "Modeler 铁律应有 M7"
    
    def test_programmer_laws_use_p_prefix(self):
        """Programmer 铁律使用 P 前缀"""
        with open("core/Programmer/laws/rules.md", 'r', encoding='utf-8') as f:
            content = f.read()
        assert "### P1:" in content, "Programmer 铁律应使用 P1 前缀"
        assert "### P9:" in content, "Programmer 铁律应有 P9"
    
    def test_writer_laws_use_w_prefix(self):
        """Writer 铁律使用 W 前缀"""
        with open("core/Writer/laws/rules.md", 'r', encoding='utf-8') as f:
            content = f.read()
        assert "### W1:" in content, "Writer 铁律应使用 W1 前缀"
        assert "### W10:" in content, "Writer 铁律应有 W10"
    
    def test_modeler_skill_md_uses_m_prefix(self):
        """Modeler SKILL.md 铁律引用使用 M 前缀"""
        with open("core/Modeler/SKILL.md", 'r', encoding='utf-8') as f:
            content = f.read()
        assert "### M1:" in content
    
    def test_programmer_skill_md_uses_p_prefix(self):
        """Programmer SKILL.md 铁律引用使用 P 前缀"""
        with open("core/Programmer/SKILL.md", 'r', encoding='utf-8') as f:
            content = f.read()
        assert "### P1:" in content
        assert "C1" not in content, "Programmer SKILL.md 不应使用 C1 前缀"
    
    def test_writer_skill_md_uses_w_prefix(self):
        """Writer SKILL.md 铁律引用使用 W 前缀"""
        with open("core/Writer/SKILL.md", 'r', encoding='utf-8') as f:
            content = f.read()
        assert "### W1:" in content
        # 检查没有 P1-P10 前缀（Writer 的铁律）
        lines = content.split('\n')
        for line in lines:
            if line.startswith('### P') and ':' in line:
                pytest.fail(f"Writer SKILL.md 不应使用 P 前缀: {line}")
