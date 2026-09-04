"""
端到端管道测试
模拟完整的 Modeler → Programmer → Writer 流程
"""
import os
import json
import pytest


class TestEndToEndPipeline:
    """端到端管道测试"""

    # 使用新建的测试项目（若存在）
    PROJECT = "projects/cumcm2024anew"

    @classmethod
    def setup_class(cls):
        cls.has_proj = os.path.isdir(cls.PROJECT)

    def test_project_structure_complete(self):
        """活跃项目的目录结构完整"""
        if not self.has_proj:
            pytest.skip("测试项目不存在，跳过")
        required_dirs = [
            f"{self.PROJECT}/inputs",    # 赛题与原始数据
            f"{self.PROJECT}/output",    # 三手产物契约
            f"{self.PROJECT}/work",      # 中间产物与审计
            f"{self.PROJECT}/code",      # 求解代码
            f"{self.PROJECT}/figures",   # 图表与结果
            f"{self.PROJECT}/paper",     # 论文
        ]
        for d in required_dirs:
            assert os.path.isdir(d), f"缺失目录: {d}"

    def test_modeler_can_output(self):
        """Modeler 产物：MODEL_SPEC.md"""
        if not self.has_proj:
            pytest.skip("测试项目不存在，跳过")
        path = f"{self.PROJECT}/output/MODEL_SPEC.md"
        if not os.path.isfile(path):
            pytest.skip("Modeler 产物尚未生成，跳过")
        assert os.path.getsize(path) > 1000, f"{path} 内容过少"

    def test_programmer_can_output(self):
        """Programmer 产物：CODE_DELIVERABLES.md + figures/all_results.json"""
        if not self.has_proj:
            pytest.skip("测试项目不存在，跳过")
        for path in (
            f"{self.PROJECT}/output/CODE_DELIVERABLES.md",
            f"{self.PROJECT}/figures/all_results.json",
        ):
            if not os.path.isfile(path):
                pytest.skip(f"Programmer 产物 {path} 尚未生成，跳过")
            assert os.path.getsize(path) > 1000, f"{path} 内容过少"

    def test_writer_can_output(self):
        """Writer 产物：PAPER_SPEC.md + paper/main.tex"""
        if not self.has_proj:
            pytest.skip("测试项目不存在，跳过")
        for path in (
            f"{self.PROJECT}/output/PAPER_SPEC.md",
            f"{self.PROJECT}/paper/main.tex",
        ):
            if not os.path.isfile(path):
                pytest.skip(f"Writer 产物 {path} 尚未生成，跳过")
            assert os.path.getsize(path) > 1000, f"{path} 内容过少"
    
    def test_all_skill_files_complete(self):
        """所有 SKILL.md 文件完整"""
        skill_files = [
            "core/Modeler/SKILL.md",
            "core/Programmer/SKILL.md",
            "core/Writer/SKILL.md",
        ]
        for f in skill_files:
            assert os.path.exists(f), f"SKILL.md 不存在: {f}"
            assert os.path.getsize(f) > 1000, f"SKILL.md 内容过少: {f}"
    
    def test_all_laws_files_complete(self):
        """所有 laws/rules.md 文件完整"""
        law_files = [
            "core/Modeler/laws/rules.md",
            "core/Programmer/laws/rules.md",
            "core/Writer/laws/rules.md",
        ]
        for f in law_files:
            assert os.path.exists(f), f"laws/rules.md 不存在: {f}"
            assert os.path.getsize(f) > 500, f"laws/rules.md 内容过少: {f}"
    
    def test_all_templates_complete(self):
        """所有模板文件完整"""
        template_files = [
            "core/Modeler/templates/MODEL_SPEC_TEMPLATE.md",
            "core/Programmer/templates/CODE_DELIVERABLES_TEMPLATE.md",
            "core/Writer/templates/PAPER_SPEC_TEMPLATE.md",
        ]
        for f in template_files:
            assert os.path.exists(f), f"模板不存在: {f}"
            assert os.path.getsize(f) > 1000, f"模板内容过少: {f}"
    
    def test_knowledge_base_coverage(self):
        """知识库文件数量达标"""
        # Modeler methodology
        meth_dir = "core/knowledge/methodology"
        meth_files = [f for f in os.listdir(meth_dir) if f.endswith('.md')]
        assert len(meth_files) >= 30, f"core/Modeler/methodology 文件不足: {len(meth_files)}"
        
        # Modeler domain
        domain_dir = "core/Modeler/knowledge/domain"
        domain_files = [f for f in os.listdir(domain_dir) if f.endswith('.md')]
        assert len(domain_files) >= 40, f"core/Modeler/domain 文件不足: {len(domain_files)}"
        
        # Programmer code-templates
        templates_dir = "core/Programmer/knowledge/code-templates"
        py_files = []
        for r, d, files in os.walk(templates_dir):
            py_files.extend([f for f in files if f.endswith('.py')])
        assert len(py_files) >= 40, f"core/Programmer/code-templates 文件不足: {len(py_files)}"
        
        # Writer writing
        writing_dir = "core/Writer/knowledge/writing"
        writing_files = [f for f in os.listdir(writing_dir) if f.endswith('.md')]
        assert len(writing_files) >= 8, f"core/Writer/writing 文件不足: {len(writing_files)}"
    
    def test_no_phantom_references(self):
        """无幻影引用（不存在的路径）"""
        phantom_paths = [
            "src/paperflow",
            "core/knowledge/reference/contest-score-rubric.md",
        ]
        for path in phantom_paths:
            assert not os.path.exists(path), f"幻影引用仍存在: {path}"
