"""
L2: Type System - 类型推导系统
用类型约束输出，保证语义合法性
"""
import re
from typing import Any, Optional


class TypeDefinition:
    """类型定义"""
    def __init__(self, name: str, validator=None, description: str = ""):
        self.name = name
        self.validator = validator
        self.description = description
    
    def validate(self, value: Any) -> dict:
        """验证值是否符合类型"""
        if self.validator:
            return self.validator(value)
        return {"valid": True}


class TypeSystem:
    """L2: 类型推导系统 - 保证输出类型正确"""
    
    def __init__(self):
        self.types = self._init_types()
        self.errors = []
    
    def _init_types(self) -> dict:
        """初始化类型定义"""
        return {
            "positive_int": TypeDefinition(
                "positive_int",
                lambda v: {"valid": isinstance(v, int) and v > 0, "issue": "必须为正整数"},
                "正整数"
            ),
            "non_negative_int": TypeDefinition(
                "non_negative_int",
                lambda v: {"valid": isinstance(v, int) and v >= 0, "issue": "必须为非负整数"},
                "非负整数"
            ),
            "positive_float": TypeDefinition(
                "positive_float",
                lambda v: {"valid": isinstance(v, (int, float)) and v > 0, "issue": "必须为正数"},
                "正数"
            ),
            "probability": TypeDefinition(
                "probability",
                lambda v: {"valid": isinstance(v, (int, float)) and 0 <= v <= 1, "issue": "必须为[0,1]之间的概率"},
                "概率值"
            ),
            "percentage": TypeDefinition(
                "percentage",
                lambda v: {"valid": isinstance(v, (int, float)) and 0 <= v <= 100, "issue": "必须为[0,100]之间的百分比"},
                "百分比"
            ),
            "coordinate_2d": TypeDefinition(
                "coordinate_2d",
                lambda v: {"valid": isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v), "issue": "必须为二维坐标[x, y]"},
                "二维坐标"
            ),
            "coordinate_3d": TypeDefinition(
                "coordinate_3d",
                lambda v: {"valid": isinstance(v, (list, tuple)) and len(v) == 3 and all(isinstance(x, (int, float)) for x in v), "issue": "必须为三维坐标[x, y, z]"},
                "三维坐标"
            ),
            "result_dict": TypeDefinition(
                "result_dict",
                lambda v: {"valid": isinstance(v, dict) and "values" in v and "units" in v, "issue": "必须包含values和units字段"},
                "结果字典"
            ),
            "array": TypeDefinition(
                "array",
                lambda v: {"valid": isinstance(v, (list, tuple)) and len(v) > 0, "issue": "必须为非空数组"},
                "非空数组"
            ),
            "matrix": TypeDefinition(
                "matrix",
                lambda v: {"valid": isinstance(v, (list, tuple)) and len(v) > 0 and all(isinstance(row, (list, tuple)) for row in v), "issue": "必须为矩阵格式"},
                "矩阵"
            ),
            "string": TypeDefinition(
                "string",
                lambda v: {"valid": isinstance(v, str) and len(v) > 0, "issue": "必须为非空字符串"},
                "非空字符串"
            ),
        }
    
    def register_type(self, name: str, validator, description: str = "") -> None:
        """注册自定义类型"""
        self.types[name] = TypeDefinition(name, validator, description)
    
    def validate(self, value: Any, type_name: str) -> dict:
        """验证值是否符合指定类型"""
        if type_name not in self.types:
            return {"valid": False, "issue": f"未知类型: {type_name}"}
        
        result = self.types[type_name].validate(value)
        if not result["valid"]:
            self.errors.append({"value": value, "type": type_name, "issue": result.get("issue", "")})
        return result
    
    def validate_dict(self, data: dict, schema: dict) -> dict:
        """验证字典是否符合schema
        
        schema格式: {"key": "type_name", ...}
        """
        issues = []
        
        for key, type_name in schema.items():
            if key not in data:
                issues.append(f"缺失字段: {key}")
            else:
                result = self.validate(data[key], type_name)
                if not result["valid"]:
                    issues.append(f"{key}: {result['issue']}")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def validate_list(self, data: list, item_type: str) -> dict:
        """验证列表中每个元素的类型"""
        issues = []
        
        for i, item in enumerate(data):
            result = self.validate(item, item_type)
            if not result["valid"]:
                issues.append(f"[{i}]: {result['issue']}")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def infer_type(self, value: Any) -> str:
        """推断值的类型"""
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            if value > 0:
                return "positive_int"
            elif value == 0:
                return "non_negative_int"
            else:
                return "int"
        elif isinstance(value, float):
            if 0 <= value <= 1:
                return "probability"
            elif 0 <= value <= 100:
                return "percentage"
            elif value > 0:
                return "positive_float"
            else:
                return "float"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, (list, tuple)):
            if len(value) == 2:
                return "coordinate_2d"
            elif len(value) == 3:
                return "coordinate_3d"
            else:
                return "array"
        elif isinstance(value, dict):
            return "result_dict"
        return "unknown"
    
    def check_type_consistency(self, values: list, expected_type: str) -> dict:
        """检查一组值的类型一致性"""
        types = [self.infer_type(v) for v in values]
        unique_types = set(types)
        
        if len(unique_types) == 1:
            return {"consistent": True, "type": types[0]}
        else:
            return {"consistent": False, "types": list(unique_types)}


def validate_output_types(data: dict, schema: dict) -> dict:
    """便捷函数：验证输出数据类型"""
    ts = TypeSystem()
    return ts.validate_dict(data, schema)
