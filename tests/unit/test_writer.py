"""
Writer 角色测试
"""
import os
import pytest


class TestWriterStructure:
    """测试Writer目录结构"""
    
    def test_skill_md_exists(self):
        """SKILL.md文件存在"""
        assert os.path.exists("core/Writer/SKILL.md")
    
    def test_laws_directory_exists(self):
        """laws目录存在"""
        assert os.path.isdir("core/Writer/laws")
    
    def test_knowledge_directory_exists(self):
        """knowledge目录存在"""
        assert os.path.isdir("core/Writer/knowledge")
    
    def test_templates_directory_exists(self):
        """templates目录存在"""
        assert os.path.isdir("core/Writer/knowledge/templates")
    
    def test_writing_directory_exists(self):
        """writing目录存在"""
        assert os.path.isdir("core/Writer/knowledge/writing")
    
    def test_reference_directory_exists(self):
        """reference目录存在"""
        assert os.path.isdir("core/Writer/knowledge/reference")
    
    def test_agents_directory_exists(self):
        """agents 目录存在且含 7 个 UTG agent"""
        assert os.path.isdir("core/Writer/agents")
        agents = [d for d in os.listdir("core/Writer/agents")
                  if os.path.isdir(os.path.join("core/Writer/agents", d))]
        assert len(agents) == 7, f"Writer agent 数应为 7，实际 {len(agents)}: {agents}"
    
    def test_writing_knowledge_exists(self):
        """写作规范目录存在（10 个规范文档）"""
        assert os.path.isdir("core/Writer/knowledge/writing")
        files = [f for f in os.listdir("core/Writer/knowledge/writing") if f.endswith(".md")]
        assert len(files) >= 8, f"写作规范文档不足: {len(files)}"


class TestWriterLaws:
    """测试Writer laws"""
    
    def test_rules_md_exists(self):
        """rules.md存在"""
        assert os.path.exists("core/Writer/laws/rules.md")
    
    def test_rules_md_not_empty(self):
        """rules.md不为空"""
        assert os.path.getsize("core/Writer/laws/rules.md") > 0


class TestWriterKnowledge:
    """测试Writer knowledge"""
    
    def test_templates_directory_exists(self):
        """templates目录存在"""
        assert os.path.isdir("core/Writer/knowledge/templates")
    
    def test_writing_directory_exists(self):
        """writing目录存在"""
        assert os.path.isdir("core/Writer/knowledge/writing")
    
    def test_reference_directory_exists(self):
        """reference目录存在"""
        assert os.path.isdir("core/Writer/knowledge/reference")
    
    def test_paper_cases_directory_exists(self):
        """paper-cases目录存在"""
        assert os.path.isdir("core/knowledge/paper-cases")


class TestWriterTemplates:
    """测试Writer templates"""
    
    def test_paper_spec_template_exists(self):
        """PAPER_SPEC_TEMPLATE.md存在"""
        assert os.path.exists("core/Writer/templates/PAPER_SPEC_TEMPLATE.md")
