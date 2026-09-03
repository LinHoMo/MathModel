"""
L1: Assumption Validator - 假设一致性校验
确保假设之间无矛盾，且与问题约束一致
"""
import re
from typing import Optional


class AssumptionValidator:
    """L1: 假设一致性校验器"""
    
    def __init__(self):
        self.assumptions = []
        self.contradictions = []
    
    def add_assumption(self, assumption: dict) -> None:
        """添加假设"""
        self.assumptions.append(assumption)
    
    def validate_all(self) -> dict:
        """验证所有假设的一致性"""
        issues = []
        
        # 检查假设数量
        if len(self.assumptions) == 0:
            issues.append({"type": "missing", "message": "未定义任何假设"})
        
        # 检查每个假设的完整性
        for i, a in enumerate(self.assumptions):
            if "content" not in a or len(a.get("content", "")) < 5:
                issues.append({"type": "incomplete", "message": f"假设H{i+1}内容不完整"})
            if "necessity" not in a or len(a.get("necessity", "")) < 10:
                issues.append({"type": "no_necessity", "message": f"假设H{i+1}缺少必要性说明"})
            if "validation" not in a:
                issues.append({"type": "no_validation", "message": f"假设H{i+1}缺少量化验证"})
            elif "composite_score" in a["validation"]:
                if a["validation"]["composite_score"] < 6:
                    issues.append({"type": "low_score", "message": f"假设H{i+1}综合评分<6: {a['validation']['composite_score']}"})
        
        # 检查假设间矛盾
        contradictions = self._check_contradictions()
        issues.extend(contradictions)
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_assumptions": len(self.assumptions),
            "valid_assumptions": sum(1 for a in self.assumptions if a.get("validation", {}).get("composite_score", 0) >= 6)
        }
    
    def _check_contradictions(self) -> list:
        """检查假设间矛盾"""
        contradictions = []
        
        # 矛盾关键词对
        contradiction_pairs = [
            ("理想", "实际"), ("刚体", "弹性"), ("忽略", "考虑"),
            ("线性", "非线性"), ("均匀", "非均匀"), ("稳态", "瞬态"),
            ("无摩擦", "有摩擦"), ("无阻力", "有阻力")
        ]
        
        for i, a1 in enumerate(self.assumptions):
            for j, a2 in enumerate(self.assumptions):
                if i >= j:
                    continue
                c1 = a1.get("content", "")
                c2 = a2.get("content", "")
                
                for pos, neg in contradiction_pairs:
                    if (pos in c1 and neg in c2) or (neg in c1 and pos in c2):
                        contradictions.append({
                            "type": "contradiction",
                            "assumptions": [f"H{i+1}", f"H{j+1}"],
                            "message": f"H{i+1}和H{j+1}可能存在矛盾: '{pos}' vs '{neg}'"
                        })
        
        return contradictions
    
    def check_necessity(self, assumption: dict) -> dict:
        """检查单个假设的必要性"""
        content = assumption.get("content", "")
        necessity = assumption.get("necessity", "")
        
        issues = []
        
        # 必要性说明长度
        if len(necessity) < 10:
            issues.append("必要性说明过短（<10字）")
        
        # 检查是否解释了为什么需要
        necessity_keywords = ["因为", "由于", "为了", "需要", "必须", "假设", "简化"]
        if not any(kw in necessity for kw in necessity_keywords):
            issues.append("必要性说明未解释原因")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def check_validation_score(self, assumption: dict) -> dict:
        """检查假设验证分数"""
        validation = assumption.get("validation", {})
        
        required_fields = ["physical_rationality", "math_consistency", "data_support", "impact_degree", "composite_score"]
        missing = [f for f in required_fields if f not in validation]
        
        if missing:
            return {"valid": False, "issues": [f"缺少验证字段: {', '.join(missing)}"]}
        
        # 检查评分范围
        issues = []
        for field in required_fields[:4]:  # 前4个是0-10分
            val = validation[field]
            if not (0 <= val <= 10):
                issues.append(f"{field}评分超出范围[0,10]: {val}")
        
        # 检查综合评分
        composite = validation["composite_score"]
        if not (0 <= composite <= 10):
            issues.append(f"综合评分超出范围[0,10]: {composite}")
        elif composite < 6:
            issues.append(f"综合评分<6: {composite}")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def extract_from_text(self, text: str) -> dict:
        """从文本中提取假设"""
        # 匹配 "假设1"、"H1" 等
        patterns = [
            r"假设\s*(\d+)[：:]\s*(.*?)(?=假设\s*\d+[：:]|符号|模型|$)",
            r"H(\d+)[：:]\s*(.*?)(?=H\d+[：:]|符号|模型|$)",
        ]
        
        extracted = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                assumption = {
                    "id": f"H{match[0]}",
                    "content": match[1].strip()[:200],
                    "type": "secondary",
                    "necessity": "",
                    "validation": {}
                }
                self.add_assumption(assumption)
                extracted.append(assumption)
        
        return {"extracted": len(extracted), "assumptions": extracted}


def validate_assumptions(text: str) -> dict:
    """便捷函数：验证文本中的假设"""
    validator = AssumptionValidator()
    validator.extract_from_text(text)
    return validator.validate_all()
