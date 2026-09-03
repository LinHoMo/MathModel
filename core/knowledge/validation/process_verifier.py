"""
L3: Process Verification - 过程验证器
在每个阶段交接时验证输出完整性，而非只在最后检查
"""
import json
from pathlib import Path
from typing import Optional


class VerificationResult:
    """单步验证结果"""
    def __init__(self, step: str, passed: bool, issues: list = None, confidence: float = 1.0):
        self.step = step
        self.passed = passed
        self.issues = issues or []
        self.confidence = confidence

    def to_dict(self):
        return {
            "step": self.step,
            "passed": self.passed,
            "issues": self.issues,
            "confidence": self.confidence
        }


class ProcessVerifier:
    """L3: 过程验证引擎 - 每步验证"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.results = []
    
    def verify_modeler_output(self) -> VerificationResult:
        """验证Modeler输出的MODEL_SPEC.md"""
        issues = []
        
        spec_path = self.project_path / "Modeler" / "output" / "MODEL_SPEC.md"
        if not spec_path.exists():
            return VerificationResult("modeler_output", False, ["MODEL_SPEC.md不存在"])
        
        content = spec_path.read_text(encoding="utf-8")
        
        # 检查必要章节
        required_sections = ["问题理解", "模型假设", "符号说明", "模型选型", "模型建立"]
        for section in required_sections:
            if section not in content:
                issues.append(f"缺少章节: {section}")
        
        # 检查假设数量（至少1个）
        if content.count("H1") == 0:
            issues.append("未发现假设定义")
        
        # 检查是否有公式
        if "$$" not in content and "\\begin{equation}" not in content:
            issues.append("未发现数学公式")
        
        # 检查符号表
        if "符号" in content and "| 符号 |" not in content and "|符号|" not in content:
            issues.append("符号说明不是表格格式")
        
        passed = len(issues) == 0
        return VerificationResult("modeler_output", passed, issues)
    
    def verify_programmer_output(self) -> VerificationResult:
        """验证Programmer输出的代码和结果"""
        issues = []
        
        # 检查代码文件
        code_dir = self.project_path / "Programmer" / "output"
        py_files = list(code_dir.glob("*.py")) if code_dir.exists() else []
        
        if not py_files:
            # 也检查 projects 目录下的代码
            code_dir = self.project_path / "projects"
            py_files = list(code_dir.rglob("code/*.py"))
        
        if not py_files:
            issues.append("未找到代码文件")
        
        # 检查all_results.json
        results_found = False
        for pattern in ["**/all_results.json", "**/results.json"]:
            matches = list(self.project_path.glob(pattern))
            if matches:
                results_found = True
                try:
                    data = json.loads(matches[0].read_text(encoding="utf-8"))
                    if not data:
                        issues.append("all_results.json为空")
                except json.JSONDecodeError:
                    issues.append("all_results.json格式错误")
                break
        
        if not results_found:
            issues.append("未找到all_results.json")
        
        # 检查随机种子
        for py_file in py_files[:3]:  # 只检查前3个
            try:
                content = py_file.read_text(encoding="utf-8")
                if "seed" not in content.lower() and "random" not in content.lower():
                    issues.append(f"{py_file.name}: 未设置随机种子")
            except:
                pass
        
        passed = len(issues) == 0
        return VerificationResult("programmer_output", passed, issues)
    
    def verify_writer_output(self) -> VerificationResult:
        """验证Writer输出的论文"""
        issues = []
        
        # 检查LaTeX源文件
        tex_files = list(self.project_path.rglob("*.tex"))
        if not tex_files:
            issues.append("未找到.tex文件")
        
        # 检查PDF
        pdf_files = list(self.project_path.rglob("*.pdf"))
        if not pdf_files:
            issues.append("未找到.pdf文件")
        
        # 检查bib文件
        bib_files = list(self.project_path.rglob("*.bib"))
        if not bib_files:
            issues.append("未找到.bib文件")
        
        # 检查LaTeX内容
        for tex_file in tex_files:
            try:
                content = tex_file.read_text(encoding="utf-8")
                
                # 检查必要章节
                required = ["\\section", "abstract", "references"]
                for req in required:
                    if req not in content.lower():
                        issues.append(f"{tex_file.name}: 缺少 {req}")
                
                # 检查占位符
                placeholders = ["TODO", "FIXME", "TBD", "XXX"]
                for ph in placeholders:
                    if ph in content:
                        issues.append(f"{tex_file.name}: 包含占位符 {ph}")
                
                # 检查禁用词
                forbidden = ["综上所述", "众所周知", "显而易见"]
                for fw in forbidden:
                    if fw in content:
                        issues.append(f"{tex_file.name}: 包含禁用词 {fw}")
                        
            except:
                pass
        
        passed = len(issues) == 0
        return VerificationResult("writer_output", passed, issues)
    
    def verify_stage交接(self, from_stage: str, to_stage: str) -> dict:
        """验证阶段交接"""
        verifiers = {
            ("Modeler", "Programmer"): self.verify_modeler_output,
            ("Programmer", "Writer"): self.verify_programmer_output,
            ("Writer", "Final"): self.verify_writer_output,
        }
        
        key = (from_stage, to_stage)
        if key in verifiers:
            result = verifiers[key]()
            self.results.append(result)
            return result.to_dict()
        
        return {"step": f"{from_stage}->{to_stage}", "passed": False, "issues": ["未知阶段交接"]}
    
    def verify_all(self) -> dict:
        """验证所有阶段"""
        self.results = []
        
        self.verify_modeler_output()
        self.verify_programmer_output()
        self.verify_writer_output()
        
        return {
            "total_steps": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "details": [r.to_dict() for r in self.results]
        }
    
    def summary(self) -> str:
        """返回验证摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        return f"过程验证: {passed}/{total} 步通过"
