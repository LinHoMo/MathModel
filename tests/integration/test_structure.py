"""
项目结构集成测试
"""
import os
import pytest


class TestProjectStructure:
    """测试项目整体结构"""
    
    def test_readme_exists(self):
        """README.md存在"""
        assert os.path.exists("README.md")
    
    def test_architecture_exists(self):
        """ARCHITECTURE.md存在"""
        assert os.path.exists("docs/ARCHITECTURE.md")
    
    def test_pyproject_exists(self):
        """pyproject.toml存在"""
        assert os.path.exists("pyproject.toml")
    
    def test_validate_exists(self):
        """validate.py存在"""
        assert os.path.exists("core/tools/validate.py")


class TestContractFiles:
    """测试契约文件模板"""
    
    def test_model_spec_template(self):
        """MODEL_SPEC_TEMPLATE.md存在"""
        assert os.path.exists("core/Modeler/templates/MODEL_SPEC_TEMPLATE.md")
    
    def test_code_deliverables_template(self):
        """CODE_DELIVERABLES_TEMPLATE.md存在"""
        assert os.path.exists("core/Programmer/templates/CODE_DELIVERABLES_TEMPLATE.md")
    
    def test_paper_spec_template(self):
        """PAPER_SPEC_TEMPLATE.md存在"""
        assert os.path.exists("core/Writer/templates/PAPER_SPEC_TEMPLATE.md")


class TestProjectsDirectory:
    """测试projects目录"""
    
    def test_projects_exists(self):
        """projects目录存在"""
        assert os.path.isdir("projects")
    
    def test_active_project_exists(self):
        """活跃示例项目存在（cumcm2024a）"""
        assert os.path.isdir("projects/cumcm2024a")

    def test_active_project_inputs_exists(self):
        """活跃项目 inputs 目录存在"""
        assert os.path.isdir("projects/cumcm2024a/inputs")

    def test_active_project_output_exists(self):
        """活跃项目 output 目录存在（三手产物契约）"""
        assert os.path.isdir("projects/cumcm2024a/output")

    def test_active_project_code_exists(self):
        """活跃项目 code 目录存在"""
        assert os.path.isdir("projects/cumcm2024a/code")

    def test_active_project_paper_exists(self):
        """活跃项目 paper 目录存在"""
        assert os.path.isdir("projects/cumcm2024a/paper")

    def test_active_project_deliverables(self):
        """活跃项目的三手产物契约齐全"""
        for name in ("MODEL_SPEC.md", "CODE_DELIVERABLES.md", "PAPER_SPEC.md"):
            path = f"projects/cumcm2024a/output/{name}"
            assert os.path.isfile(path), f"产物契约缺失: {path}"
