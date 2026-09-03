"""
Modeler 角色测试
"""
import os
import pytest


class TestModelerStructure:
    """测试Modeler目录结构"""
    
    def test_skill_md_exists(self):
        """SKILL.md文件存在"""
        assert os.path.exists("core/Modeler/SKILL.md")
    
    def test_laws_directory_exists(self):
        """laws目录存在"""
        assert os.path.isdir("core/Modeler/laws")
    
    def test_knowledge_directory_exists(self):
        """knowledge目录存在"""
        assert os.path.isdir("core/Modeler/knowledge")
    
    def test_templates_directory_exists(self):
        """templates目录存在"""
        assert os.path.isdir("core/Modeler/templates")
    
    def test_agents_directory_exists(self):
        """agents 目录存在且含 8 个 UTG agent"""
        assert os.path.isdir("core/Modeler/agents")
        agents = [d for d in os.listdir("core/Modeler/agents")
                  if os.path.isdir(os.path.join("core/Modeler/agents", d))]
        assert len(agents) == 8, f"Modeler agent 数应为 8，实际 {len(agents)}: {agents}"


class TestModelerLaws:
    """测试Modeler laws"""
    
    def test_rules_md_exists(self):
        """rules.md存在"""
        assert os.path.exists("core/Modeler/laws/rules.md")
    
    def test_rules_md_not_empty(self):
        """rules.md不为空"""
        assert os.path.getsize("core/Modeler/laws/rules.md") > 0


class TestModelerKnowledge:
    """测试Modeler knowledge"""
    
    def test_methodology_directory_exists(self):
        """methodology目录存在"""
        assert os.path.isdir("core/knowledge/methodology")
    
    def test_domain_directory_exists(self):
        """domain目录存在"""
        assert os.path.isdir("core/Modeler/knowledge/domain")
    
    def test_paper_cases_directory_exists(self):
        """paper-cases目录存在"""
        assert os.path.isdir("core/knowledge/paper-cases")
    
    def test_methodology_files_count(self):
        """methodology文件数量"""
        files = [f for f in os.listdir("core/knowledge/methodology") if f.endswith('.md')]
        assert len(files) >= 20
    
    def test_domain_files_count(self):
        """domain文件数量"""
        files = [f for f in os.listdir("core/Modeler/knowledge/domain") if f.endswith('.md')]
        assert len(files) >= 20


class TestModelerTemplates:
    """测试Modeler templates"""
    
    def test_model_spec_template_exists(self):
        """MODEL_SPEC_TEMPLATE.md存在"""
        assert os.path.exists("core/Modeler/templates/MODEL_SPEC_TEMPLATE.md")
