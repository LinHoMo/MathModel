"""
错误诊断机制
来源: 高教杯论文代码常见错误
适用问题: 代码运行失败时自动分析原因并提供修复建议
输入: 错误信息、代码上下文
输出: 错误原因、修复建议
"""

import traceback
import sys
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ErrorType(Enum):
    """错误类型枚举"""
    DATA_ERROR = "数据错误"
    MODEL_ERROR = "模型错误"
    SHAPE_ERROR = "形状错误"
    TYPE_ERROR = "类型错误"
    VALUE_ERROR = "值错误"
    IMPORT_ERROR = "导入错误"
    MEMORY_ERROR = "内存错误"
    TIMEOUT_ERROR = "超时错误"
    UNKNOWN_ERROR = "未知错误"


@dataclass
class DiagnosisResult:
    """诊断结果"""
    error_type: ErrorType
    error_message: str
    cause: str
    suggestion: str
    code_fix: Optional[str] = None


class ErrorDiagnostician:
    """
    错误诊断器
    
    自动分析Python代码错误，提供修复建议。
    """
    
    # 常见错误模式
    ERROR_PATTERNS = {
        "ValueError: could not convert string to float": {
            "type": ErrorType.TYPE_ERROR,
            "cause": "字符串无法转换为数值",
            "suggestion": "检查数据中是否包含非数值字符",
            "code_fix": "df['col'] = pd.to_numeric(df['col'], errors='coerce')"
        },
        "ValueError: Input contains NaN": {
            "type": ErrorType.DATA_ERROR,
            "cause": "输入数据包含NaN值",
            "suggestion": "先处理缺失值",
            "code_fix": "df = df.dropna() 或 df = df.fillna(df.median())"
        },
        "IndexError: index out of range": {
            "type": ErrorType.INDEX_ERROR,
            "cause": "索引超出范围",
            "suggestion": "检查数组维度和索引值",
            "code_fix": "检查 len(array) 和 index 值"
        },
        "KeyError": {
            "type": ErrorType.KEY_ERROR,
            "cause": "字典或DataFrame中不存在该键",
            "suggestion": "检查列名是否正确",
            "code_fix": "print(df.columns) 查看可用列名"
        },
        "TypeError": {
            "type": ErrorType.TYPE_ERROR,
            "cause": "数据类型不匹配",
            "suggestion": "检查数据类型",
            "code_fix": "df['col'] = df['col'].astype(float)"
        },
        "MemoryError": {
            "type": ErrorType.MEMORY_ERROR,
            "cause": "内存不足",
            "suggestion": "减少数据量或使用更小的数据类型",
            "code_fix": "df['col'] = df['col'].astype('float32')"
        },
        "ImportError": {
            "type": ErrorType.IMPORT_ERROR,
            "cause": "模块未安装或导入失败",
            "suggestion": "安装所需模块",
            "code_fix": "pip install 模块名"
        },
        "AttributeError": {
            "type": ErrorType.ATTRIBUTE_ERROR,
            "cause": "对象没有该属性或方法",
            "suggestion": "检查对象类型和可用方法",
            "code_fix": "print(type(obj)) 和 print(dir(obj))"
        },
    }
    
    def __init__(self):
        self.diagnosis_history = []
    
    def diagnose(self, error: Exception, code: Optional[str] = None) -> DiagnosisResult:
        """
        诊断错误
        
        Parameters
        ----------
        error : Exception
            捕获的异常
        code : str
            相关代码（可选）
        
        Returns
        -------
        DiagnosisResult
            诊断结果
        """
        error_msg = str(error)
        error_type = type(error).__name__
        
        # 匹配已知模式
        for pattern, info in self.ERROR_PATTERNS.items():
            if pattern in error_msg:
                result = DiagnosisResult(
                    error_type=info["type"],
                    error_message=error_msg,
                    cause=info["cause"],
                    suggestion=info["suggestion"],
                    code_fix=info["code_fix"]
                )
                self.diagnosis_history.append(result)
                return result
        
        # 通用诊断
        result = self._general_diagnosis(error, error_msg, code)
        self.diagnosis_history.append(result)
        return result
    
    def _general_diagnosis(self, error: Exception, error_msg: str, code: Optional[str]) -> DiagnosisResult:
        """通用诊断"""
        
        error_type_name = type(error).__name__
        
        # 数值相关错误
        if "nan" in error_msg.lower() or "inf" in error_msg.lower():
            return DiagnosisResult(
                error_type=ErrorType.DATA_ERROR,
                error_message=error_msg,
                cause="数据包含NaN或无穷大",
                suggestion="检查数据预处理流程",
                code_fix="print(np.isnan(df).sum()) 检查缺失值"
            )
        
        # 形状相关错误
        if "shape" in error_msg.lower() or "dimension" in error_msg.lower():
            return DiagnosisResult(
                error_type=ErrorType.SHAPE_ERROR,
                error_message=error_msg,
                cause="数组维度不匹配",
                suggestion="检查输入输出的形状",
                code_fix="print(X.shape, y.shape) 检查维度"
            )
        
        # 索引相关错误
        if "index" in error_msg.lower() or "key" in error_msg.lower():
            return DiagnosisResult(
                error_type=ErrorType.KEY_ERROR,
                error_message=error_msg,
                cause="索引或键不存在",
                suggestion="检查可用的索引或键",
                code_fix="print(df.columns) 或 print(dict.keys())"
            )
        
        # 默认返回
        return DiagnosisResult(
            error_type=ErrorType.UNKNOWN_ERROR,
            error_message=error_msg,
            cause=f"未知错误: {error_type_name}",
            suggestion="请检查代码逻辑和数据",
            code_fix=None
        )
    
    def diagnose_shape_error(self, expected_shape: Tuple, actual_shape: Tuple) -> DiagnosisResult:
        """诊断形状错误"""
        cause = f"期望形状{expected_shape}，实际形状{actual_shape}"
        
        if len(expected_shape) != len(actual_shape):
            suggestion = "维度数量不匹配，检查是否遗漏了维度"
            code_fix = f"使用 reshape 或 np.newaxis 调整维度"
        elif expected_shape != actual_shape:
            suggestion = "形状不匹配，检查数据转换过程"
            code_fix = f"使用 np.reshape 或 .values 调整形状"
        else:
            suggestion = "检查具体哪个维度不匹配"
            code_fix = None
        
        return DiagnosisResult(
            error_type=ErrorType.SHAPE_ERROR,
            error_message=f"Shape mismatch: {expected_shape} vs {actual_shape}",
            cause=cause,
            suggestion=suggestion,
            code_fix=code_fix
        )
    
    def diagnose_data_error(self, df: pd.DataFrame) -> DiagnosisResult:
        """诊断数据问题"""
        issues = []
        
        # 检查缺失值
        missing = df.isnull().sum()
        if missing.sum() > 0:
            issues.append(f"缺失值: {missing[missing > 0].to_dict()}")
        
        # 检查无穷大
        inf_count = np.isinf(df.select_dtypes(include=[np.number])).sum()
        if inf_count.sum() > 0:
            issues.append(f"无穷大: {inf_count[inf_count > 0].to_dict()}")
        
        # 检查常数列
        const_cols = [col for col in df.columns if df[col].nunique() == 1]
        if const_cols:
            issues.append(f"常数列: {const_cols}")
        
        # 检查高相关性
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr().abs()
            high_corr = [(corr.columns[i], corr.columns[j]) 
                        for i in range(len(corr.columns))
                        for j in range(i+1, len(corr.columns))
                        if corr.iloc[i, j] > 0.95]
            if high_corr:
                issues.append(f"高相关性: {high_corr[:3]}")
        
        if issues:
            return DiagnosisResult(
                error_type=ErrorType.DATA_ERROR,
                error_message="数据质量问题",
                cause="\n".join(issues),
                suggestion="修复数据质量问题后再运行模型",
                code_fix=None
            )
        
        return DiagnosisResult(
            error_type=ErrorType.DATA_ERROR,
            error_message="未发现明显数据问题",
            cause="数据质量正常",
            suggestion="检查模型参数或其他代码逻辑",
            code_fix=None
        )
    
    def get_report(self) -> str:
        """生成诊断报告"""
        if not self.diagnosis_history:
            return "无诊断记录"
        
        report = ["=" * 50, "错误诊断报告", "=" * 50, ""]
        
        for i, result in enumerate(self.diagnosis_history, 1):
            report.append(f"诊断 {i}:")
            report.append(f"  错误类型: {result.error_type.value}")
            report.append(f"  错误信息: {result.error_message}")
            report.append(f"  原因分析: {result.cause}")
            report.append(f"  修复建议: {result.suggestion}")
            if result.code_fix:
                report.append(f"  代码修复: {result.code_fix}")
            report.append("")
        
        return "\n".join(report)


def run_example():
    """
    示例：错误诊断
    """
    diagnostician = ErrorDiagnostician()
    
    print("=" * 60)
    print("错误诊断示例")
    print("=" * 60)
    
    # 示例1: 类型错误
    try:
        x = float("abc")
    except Exception as e:
        result = diagnostician.diagnose(e)
        print(f"\n错误1: {result.error_type.value}")
        print(f"  原因: {result.cause}")
        print(f"  建议: {result.suggestion}")
    
    # 示例2: 缺失值错误
    try:
        df = pd.DataFrame({'a': [1, 2, np.nan], 'b': [4, 5, 6]})
        x = df.values
        raise ValueError("Input contains NaN")
    except Exception as e:
        result = diagnostician.diagnose(e)
        print(f"\n错误2: {result.error_type.value}")
        print(f"  原因: {result.cause}")
        print(f"  建议: {result.suggestion}")
        print(f"  修复: {result.code_fix}")
    
    # 示例3: 数据质量诊断
    df = pd.DataFrame({
        'a': [1, 2, np.inf, 4],
        'b': [5, 5, 5, 5],  # 常数列
        'c': [1, 2, 3, 4]
    })
    result = diagnostician.diagnose_data_error(df)
    print(f"\n数据质量诊断:")
    print(f"  类型: {result.error_type.value}")
    print(f"  原因:\n{result.cause}")
    
    # 输出完整报告
    print("\n" + diagnostician.get_report())


if __name__ == "__main__":
    run_example()
