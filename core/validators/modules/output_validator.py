"""
L2: Output Validator - 输出类型校验
验证代码输出是否符合预期类型和格式
"""
import json
from pathlib import Path
from typing import Any


class OutputValidator:
    """L2: 输出类型校验器"""
    
    def __init__(self):
        self.errors = []
    
    def validate_all_results(self, path: str) -> dict:
        """验证all_results.json的完整性和类型"""
        self.errors = []
        
        file_path = Path(path)
        if not file_path.exists():
            return {"valid": False, "issues": [f"文件不存在: {path}"]}
        
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return {"valid": False, "issues": [f"JSON解析错误: {e}"]}
        
        # 检查顶层结构
        if not isinstance(data, dict):
            return {"valid": False, "issues": ["顶层必须为对象"]}
        
        # 检查每个子问题的结果
        for key, value in data.items():
            if key.startswith("problem_"):
                result = self._validate_problem_result(key, value)
                if not result["valid"]:
                    self.errors.extend(result["issues"])
        
        return {"valid": len(self.errors) == 0, "issues": self.errors}
    
    def _validate_problem_result(self, key: str, value: Any) -> dict:
        """验证单个子问题的结果"""
        issues = []
        
        if not isinstance(value, dict):
            issues.append(f"{key}: 结果必须为字典")
            return {"valid": False, "issues": issues}
        
        # 检查values字段
        if "values" not in value:
            issues.append(f"{key}: 缺少values字段")
        elif not isinstance(value["values"], dict):
            issues.append(f"{key}: values必须为字典")
        elif len(value["values"]) == 0:
            issues.append(f"{key}: values不能为空")
        
        # 检查units字段
        if "units" not in value:
            issues.append(f"{key}: 缺少units字段")
        elif not isinstance(value["units"], dict):
            issues.append(f"{key}: units必须为字典")
        
        # 检查数值类型
        if "values" in value and isinstance(value["values"], dict):
            for vk, vv in value["values"].items():
                if not isinstance(vv, (int, float)):
                    # 可能是嵌套结构
                    if isinstance(vv, dict):
                        for subk, subv in vv.items():
                            if not isinstance(subv, (int, float)):
                                issues.append(f"{key}.values.{vk}.{subk}: 值必须为数字")
                    elif isinstance(vv, list):
                        for i, item in enumerate(vv):
                            if not isinstance(item, (int, float)):
                                issues.append(f"{key}.values.{vk}[{i}]: 值必须为数字")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def validate_code_output(self, output: Any, expected_schema: dict) -> dict:
        """验证代码函数输出"""
        issues = []
        
        if not isinstance(output, dict):
            return {"valid": False, "issues": ["输出必须为字典"]}
        
        for key, expected_type in expected_schema.items():
            if key not in output:
                issues.append(f"缺失字段: {key}")
            else:
                type_result = self._check_type(output[key], expected_type)
                if not type_result["valid"]:
                    issues.append(f"{key}: {type_result['issue']}")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def _check_type(self, value: Any, expected: str) -> dict:
        """检查值类型"""
        type_map = {
            "int": lambda v: isinstance(v, int),
            "float": lambda v: isinstance(v, (int, float)),
            "str": lambda v: isinstance(v, str),
            "bool": lambda v: isinstance(v, bool),
            "list": lambda v: isinstance(v, list),
            "dict": lambda v: isinstance(v, dict),
            "number": lambda v: isinstance(v, (int, float)),
            "array": lambda v: isinstance(v, (list, tuple)),
        }
        
        if expected in type_map:
            if type_map[expected](value):
                return {"valid": True}
            return {"valid": False, "issue": f"类型不匹配: 期望{expected}, 实际{type(value).__name__}"}
        
        return {"valid": True}  # 未知类型默认通过
    
    def validate_numeric_range(self, value: float, name: str, min_val: float = None, max_val: float = None) -> dict:
        """验证数值范围"""
        if not isinstance(value, (int, float)):
            return {"valid": False, "issue": f"{name}必须为数字"}
        
        if min_val is not None and value < min_val:
            return {"valid": False, "issue": f"{name}={value} < 最小值{min_val}"}
        
        if max_val is not None and value > max_val:
            return {"valid": False, "issue": f"{name}={value} > 最大值{max_val}"}
        
        return {"valid": True}
    
    def validate_result_consistency(self, results: dict, expected_keys: list) -> dict:
        """验证结果一致性"""
        issues = []
        
        for key in expected_keys:
            if key not in results:
                issues.append(f"缺失子问题结果: {key}")
        
        for key in results:
            if key not in expected_keys:
                issues.append(f"多余的子问题结果: {key}")
        
        return {"valid": len(issues) == 0, "issues": issues}


def validate_output(data: dict, expected_keys: list = None) -> dict:
    """便捷函数：验证输出数据"""
    validator = OutputValidator()
    
    if expected_keys:
        return validator.validate_result_consistency(data, expected_keys)
    
    return {"valid": True, "issues": []}
