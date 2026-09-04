"""
项目结构集成测试
"""
import os
import tempfile
import shutil
import pytest
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


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
    
    def test_new_project_scaffold_structure(self):
        """新建项目脚手架创建完整目录结构"""
        import uuid
        # 使用唯一项目名在真实 projects 目录下测试，测试后清理
        # 名称必须匹配 ^[a-z][a-z0-9-]{1,63}$（仅小写字母、数字、连字符）
        unique_name = f"testproj{uuid.uuid4().hex[:8]}"
        problem_file = os.path.join(ROOT, "tests", "fixtures", "sample_problem.txt")
        
        # 确保 fixtures 目录和样例文件存在
        os.makedirs(os.path.dirname(problem_file), exist_ok=True)
        if not os.path.exists(problem_file):
            with open(problem_file, "w", encoding="utf-8") as f:
                f.write("测试赛题内容")
        
        from core.tools.new_project import scaffold, PROJECT_DIRS
        
        proj_dir = None
        try:
            proj_dir = scaffold(
                unique_name,
                "cumcm",
                [problem_file],
                force=True
            )
            
            # 验证所有 PROJECT_DIRS 都被创建
            for sub in PROJECT_DIRS:
                assert os.path.isdir(os.path.join(proj_dir, sub)), f"缺失目录: {sub}"
            
            # 验证赛题文件被复制
            assert os.path.isfile(os.path.join(proj_dir, "inputs", "sample_problem.txt"))
            
            # 验证模板文件
            assert os.path.isfile(os.path.join(proj_dir, "work", "time_budget.yaml"))
            assert os.path.isfile(os.path.join(proj_dir, "work", "handoff.md"))
            
        finally:
            # 清理测试项目
            if proj_dir and os.path.exists(proj_dir):
                shutil.rmtree(proj_dir, ignore_errors=True)
    
    def test_archived_project_marked(self):
        """归档目录存在但不要求完整结构（历史项目）"""
        # archives/ 目录存在即可，不验证内部具体项目
        assert os.path.isdir("archives")
        # 仅验证归档目录存在，不验证内部完整结构
