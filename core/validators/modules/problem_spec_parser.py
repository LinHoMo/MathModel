"""
L1: Problem Spec Parser - 赛题结构化规约解析器
将自然语言赛题转译为结构化规约，从源头消除输入歧义
"""
import re
import json
from pathlib import Path
from typing import Optional


class ProblemSpecParser:
    """L1: 赛题解析器 - 自然语言→结构化规约"""
    
    def __init__(self):
        self.parsed = None
    
    def parse(self, text: str) -> dict:
        """将赛题文本解析为结构化规约"""
        spec = {
            "metadata": self._extract_metadata(text),
            "background": self._extract_background(text),
            "problems": self._extract_problems(text),
            "constraints": self._extract_constraints(text),
            "data": self._extract_data(text),
            "delivery": self._extract_delivery(text)
        }
        self.parsed = spec
        return spec
    
    def _extract_metadata(self, text: str) -> dict:
        """提取元数据"""
        metadata = {
            "contest": "CUMCM",
            "year": 2024,
            "topic_id": "A001",
            "topic_type": "A-physical",
            "language": "zh"
        }
        
        # 检测竞赛类型
        if "MCM" in text or "ICM" in text:
            metadata["contest"] = "MCM" if "MCM" in text else "ICM"
            metadata["language"] = "en"
        
        # 检测年份
        year_match = re.search(r"20\d{2}", text)
        if year_match:
            metadata["year"] = int(year_match.group())
        
        # 检测题号
        topic_match = re.search(r"([ABC])\s*(\d{3})", text)
        if topic_match:
            metadata["topic_id"] = f"{topic_match.group(1)}{topic_match.group(2)}"
        
        # 检测题型
        if any(kw in text for kw in ["物理", "运动", "动力", "热传导", "电磁", "光学", "physical"]):
            metadata["topic_type"] = "A-physical"
        elif any(kw in text for kw in ["实验", "正交", "响应面", "experiment"]):
            metadata["topic_type"] = "B-experiment"
        elif any(kw in text for kw in ["数据", "销售", "客户", "金融", "data"]):
            metadata["topic_type"] = "C-data"
        elif any(kw in text for kw in ["评价", "决策", "调度", "optimization"]):
            metadata["topic_type"] = "D-operations"
        
        return metadata
    
    def _extract_background(self, text: str) -> dict:
        """提取背景信息"""
        # 提取第一段作为背景
        paragraphs = text.split("\n\n")
        background_text = paragraphs[0] if paragraphs else text[:500]
        
        # 提取领域关键词
        domain_keywords = self._extract_domain_keywords(text)
        
        # 提取物理过程（A题）
        physical_processes = []
        if any(kw in text for kw in ["运动", "动力", "热传导", "电磁", "光学"]):
            process_map = {
                "运动": "kinematics", "动力": "dynamics",
                "热传导": "heat_transfer", "电磁": "electromagnetic",
                "光学": "optics", "振动": "vibration"
            }
            for cn, en in process_map.items():
                if cn in text:
                    physical_processes.append(en)
        
        return {
            "context": background_text[:1000],
            "domain_keywords": domain_keywords,
            "physical_processes": physical_processes
        }
    
    def _extract_domain_keywords(self, text: str) -> list:
        """提取领域关键词"""
        keywords = []
        keyword_patterns = [
            "板凳龙", "螺线", "把手", "碰撞", "调头",  # 2024A
            "波浪", "水动力", "风力", "太阳能", "热传导",
            "优化", "调度", "路径", "排队", "博弈",
            "回归", "分类", "聚类", "时序", "预测",
            "评价", "决策", "图论", "网络"
        ]
        for kw in keyword_patterns:
            if kw in text:
                keywords.append(kw)
        return keywords[:10]  # 最多10个
    
    def _extract_problems(self, text: str) -> list:
        """提取子问题"""
        problems = []
        
        # 匹配 "问题一"、"问题二" 等
        pattern = r"问题[一二三四五六七八九十\d]+[：:]\s*(.*?)(?=问题[一二三四五六七八九十\d]+[：:]|$)"
        matches = re.findall(pattern, text, re.DOTALL)
        
        for i, match in enumerate(matches):
            problem_text = match.strip()
            problem = {
                "id": i + 1,
                "description": problem_text[:200],
                "input_variables": self._extract_variables(problem_text, "input"),
                "output_variables": self._extract_variables(problem_text, "output"),
                "constraints": self._extract_problem_constraints(problem_text),
                "dependencies": list(range(1, i + 1)) if i > 0 else []
            }
            problems.append(problem)
        
        # 如果没有匹配到，尝试其他模式
        if not problems:
            # 尝试匹配 "Question 1" 等
            q_pattern = r"Question\s+(\d+)[：:]\s*(.*?)(?=Question\s+\d+|$)"
            q_matches = re.findall(q_pattern, text, re.DOTALL | re.IGNORECASE)
            for match in q_matches:
                problems.append({
                    "id": int(match[0]),
                    "description": match[1].strip()[:200],
                    "input_variables": [],
                    "output_variables": [],
                    "constraints": [],
                    "dependencies": []
                })
        
        return problems
    
    def _extract_variables(self, text: str, var_type: str) -> list:
        """提取变量"""
        variables = []
        
        # 通用变量模式
        var_patterns = [
            (r"速度[为是]\s*(\d+\.?\d*)\s*(m/s|cm/s)", "velocity", "continuous"),
            (r"距离[为是]\s*(\d+\.?\d*)\s*(m|cm)", "distance", "continuous"),
            (r"时间为?\s*(\d+\.?\d*)\s*(s|秒)", "time", "continuous"),
            (r"数量[为是]\s*(\d+)", "count", "discrete"),
        ]
        
        for pattern, name, vtype in var_patterns:
            match = re.search(pattern, text)
            if match:
                variables.append({
                    "name": name,
                    "type": vtype,
                    "unit": match.group(2),
                    "range": f"={match.group(1)}"
                })
        
        return variables
    
    def _extract_problem_constraints(self, text: str) -> list:
        """提取问题约束"""
        constraints = []
        
        constraint_patterns = [
            (r"不[能可]超过\s*(\d+\.?\d*)\s*(m/s|cm/s)", "inequality"),
            (r"至少[为是]\s*(\d+\.?\d*)", "inequality"),
            (r"必须[为是]\s*(\d+\.?\d*)", "equality"),
            (r"直径[为是]\s*(\d+\.?\d*)\s*m", "equality"),
        ]
        
        for pattern, ctype in constraint_patterns:
            match = re.search(pattern, text)
            if match:
                constraints.append({
                    "type": ctype,
                    "expression": match.group(0)
                })
        
        return constraints
    
    def _extract_constraints(self, text: str) -> dict:
        """提取全局约束"""
        global_constraints = []
        
        # 检测常见约束
        if "碰撞" in text:
            global_constraints.append({"type": "physical", "expression": "板凳之间不发生碰撞"})
        if "速度" in text and "限制" in text:
            global_constraints.append({"type": "inequality", "expression": "把手速度不超过2m/s"})
        
        return {
            "global_constraints": global_constraints,
            "time_constraints": [],
            "spatial_constraints": []
        }
    
    def _extract_data(self, text: str) -> dict:
        """提取数据信息"""
        provided_files = []
        
        # 检测给定数据
        data_patterns = [
            (r"(\d+)\s*节板凳", "板凳数量"),
            (r"长(\d+\.?\d*)\s*cm", "板凳长度"),
            (r"宽(\d+\.?\d*)\s*cm", "板凳宽度"),
            (r"螺距[为是]\s*(\d+\.?\d*)\s*cm", "螺距"),
        ]
        
        parameters = {}
        for pattern, name in data_patterns:
            match = re.search(pattern, text)
            if match:
                parameters[name] = match.group(1)
        
        return {
            "provided_files": provided_files,
            "parameters": parameters
        }
    
    def _extract_delivery(self, text: str) -> dict:
        """提取交付要求"""
        requirements = []
        
        if "建立数学模型" in text:
            requirements.append("建立数学模型")
        if "求解" in text:
            requirements.append("求解问题")
        if "分析" in text:
            requirements.append("结果分析")
        
        return {
            "requirements": requirements,
            "page_limit": 25,
            "submission_format": "pdf"
        }
    
    def validate(self, spec: dict) -> dict:
        """验证规约完整性"""
        issues = []
        
        # 检查必填字段
        required = ["metadata", "background", "problems", "constraints", "data", "delivery"]
        for field in required:
            if field not in spec:
                issues.append(f"缺失必填字段: {field}")
        
        # 检查子问题
        if "problems" in spec:
            if len(spec["problems"]) == 0:
                issues.append("未识别到子问题")
            for p in spec["problems"]:
                if len(p.get("description", "")) < 10:
                    issues.append(f"问题{p['id']}描述过短")
        
        # 检查背景
        if "background" in spec:
            if len(spec["background"].get("context", "")) < 20:
                issues.append("背景描述过短")
            if len(spec["background"].get("domain_keywords", [])) < 3:
                issues.append("领域关键词不足3个")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "completeness": 1 - len(issues) / 10  # 粗略评分
        }
    
    def to_json(self, spec: dict, path: str = None) -> str:
        """导出为JSON"""
        json_str = json.dumps(spec, ensure_ascii=False, indent=2)
        if path:
            Path(path).write_text(json_str, encoding="utf-8")
        return json_str


def parse_problem_spec(text: str) -> dict:
    """便捷函数：解析赛题文本"""
    parser = ProblemSpecParser()
    spec = parser.parse(text)
    validation = parser.validate(spec)
    return {"spec": spec, "validation": validation}
