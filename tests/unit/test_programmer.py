"""
Programmer 角色测试
"""
import os
import pytest


class TestProgrammerStructure:
    """测试Programmer目录结构"""
    
    def test_skill_md_exists(self):
        """SKILL.md文件存在"""
        assert os.path.exists("core/Programmer/SKILL.md")
    
    def test_laws_directory_exists(self):
        """laws目录存在"""
        assert os.path.isdir("core/Programmer/laws")
    
    def test_knowledge_directory_exists(self):
        """knowledge目录存在"""
        assert os.path.isdir("core/Programmer/knowledge")
    
    def test_templates_directory_exists(self):
        """templates目录存在"""
        assert os.path.isdir("core/Programmer/templates")
    
    def test_agents_directory_exists(self):
        """agents 目录存在且含 6 个 UTG agent"""
        assert os.path.isdir("core/Programmer/agents")
        agents = [d for d in os.listdir("core/Programmer/agents")
                  if os.path.isdir(os.path.join("core/Programmer/agents", d))]
        assert len(agents) == 6, f"Programmer agent 数应为 6，实际 {len(agents)}: {agents}"


class TestProgrammerLaws:
    """测试Programmer laws"""
    
    def test_rules_md_exists(self):
        """rules.md存在"""
        assert os.path.exists("core/Programmer/laws/rules.md")
    
    def test_rules_md_not_empty(self):
        """rules.md不为空"""
        assert os.path.getsize("core/Programmer/laws/rules.md") > 0


class TestProgrammerKnowledge:
    """测试Programmer knowledge"""
    
    def test_methodology_directory_exists(self):
        """methodology目录存在"""
        assert os.path.isdir("core/knowledge/methodology")
    
    def test_code_templates_directory_exists(self):
        """code-templates目录存在"""
        assert os.path.isdir("core/Programmer/knowledge/code-templates")
    
    def test_algorithms_directory_exists(self):
        """algorithms目录存在"""
        assert os.path.isdir("core/Programmer/knowledge/code-templates")
    
    def test_validation_directory_exists(self):
        """validation目录存在"""
        assert os.path.isdir("core/validators/modules")
    
    def test_methodology_files_count(self):
        """methodology文件数量"""
        files = [f for f in os.listdir("core/knowledge/methodology") if f.endswith('.md')]
        assert len(files) >= 10
    
    def test_code_templates_files_count(self):
        """code-templates文件数量"""
        count = sum([len(files) for r, d, files in os.walk("core/Programmer/knowledge/code-templates")])
        assert count >= 30


class TestProgrammerTemplates:
    """测试Programmer templates"""
    
    def test_code_deliverables_template_exists(self):
        """CODE_DELIVERABLES_TEMPLATE.md存在"""
        assert os.path.exists("core/Programmer/templates/CODE_DELIVERABLES_TEMPLATE.md")
