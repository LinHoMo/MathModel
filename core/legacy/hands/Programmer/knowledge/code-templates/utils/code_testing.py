"""
代码测试模板
来源: 高教杯论文代码质量保证
适用问题: 单元测试、集成测试、结果验证
输入: 待测试的函数/模型
输出: 测试报告
"""

import numpy as np
import pandas as pd
import time
import sys
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum
import traceback


class TestStatus(Enum):
    """测试状态"""
    PASS = "通过"
    FAIL = "失败"
    ERROR = "错误"
    SKIP = "跳过"


@dataclass
class TestCase:
    """测试用例"""
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    expected: Any = None
    expected_type: type = None
    expected_range: tuple = None
    status: TestStatus = TestStatus.PASS
    message: str = ""
    execution_time: float = 0.0


class CodeTester:
    """
    代码测试器
    
    支持：
    1. 单元测试
    2. 集成测试
    3. 结果验证
    4. 性能测试
    """
    
    def __init__(self):
        self.test_cases: List[TestCase] = []
        self.results: Dict[str, TestStatus] = {}
    
    def add_test(self, name: str, func: Callable, *args, 
                 expected: Any = None, expected_type: type = None,
                 expected_range: tuple = None, **kwargs):
        """添加测试用例"""
        test = TestCase(
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            expected=expected,
            expected_type=expected_type,
            expected_range=expected_range
        )
        self.test_cases.append(test)
    
    def run_all(self) -> str:
        """运行所有测试"""
        passed = 0
        failed = 0
        errors = 0
        
        print("=" * 60)
        print("开始测试")
        print("=" * 60)
        
        for test in self.test_cases:
            try:
                start_time = time.time()
                result = test.func(*test.args, **test.kwargs)
                test.execution_time = time.time() - start_time
                
                # 验证结果
                if test.expected is not None:
                    if np.allclose(result, test.expected, rtol=1e-5, atol=1e-8):
                        test.status = TestStatus.PASS
                        test.message = "结果匹配"
                    else:
                        test.status = TestStatus.FAIL
                        test.message = f"期望{test.expected}，实际{result}"
                
                elif test.expected_type is not None:
                    if isinstance(result, test.expected_type):
                        test.status = TestStatus.PASS
                        test.message = "类型匹配"
                    else:
                        test.status = TestStatus.FAIL
                        test.message = f"期望类型{test.expected_type}，实际{type(result)}"
                
                elif test.expected_range is not None:
                    low, high = test.expected_range
                    if low <= result <= high:
                        test.status = TestStatus.PASS
                        test.message = "范围匹配"
                    else:
                        test.status = TestStatus.FAIL
                        test.message = f"期望范围[{low}, {high}]，实际{result}"
                
                else:
                    test.status = TestStatus.PASS
                    test.message = "执行成功"
                
            except Exception as e:
                test.status = TestStatus.ERROR
                test.message = str(e)
            
            # 输出结果
            status_icon = "✓" if test.status == TestStatus.PASS else "✗"
            print(f"  {status_icon} {test.name}: {test.status.value} ({test.execution_time:.3f}s)")
            if test.status != TestStatus.PASS:
                print(f"    {test.message}")
            
            self.results[test.name] = test.status
            
            if test.status == TestStatus.PASS:
                passed += 1
            elif test.status == TestStatus.FAIL:
                failed += 1
            else:
                errors += 1
        
        # 汇总
        total = len(self.test_cases)
        print("\n" + "=" * 60)
        print(f"测试完成: {passed}/{total} 通过, {failed} 失败, {errors} 错误")
        print("=" * 60)
        
        return self.generate_report()
    
    def generate_report(self) -> str:
        """生成测试报告"""
        report = [
            "=" * 60,
            "测试报告",
            "=" * 60,
            f"总测试数: {len(self.test_cases)}",
            ""
        ]
        
        passed = sum(1 for s in self.results.values() if s == TestStatus.PASS)
        failed = sum(1 for s in self.results.values() if s == TestStatus.FAIL)
        errors = sum(1 for s in self.results.values() if s == TestStatus.ERROR)
        
        report.append(f"通过: {passed}")
        report.append(f"失败: {failed}")
        report.append(f"错误: {errors}")
        report.append(f"通过率: {passed/len(self.test_cases)*100:.1f}%")
        report.append("")
        
        # 详细结果
        report.append("详细结果:")
        for test in self.test_cases:
            report.append(f"  [{test.status.value}] {test.name}")
            if test.status != TestStatus.PASS:
                report.append(f"    原因: {test.message}")
        
        return "\n".join(report)


def test_data_processing():
    """测试数据处理函数"""
    tester = CodeTester()
    
    # 测试数据加载
    def load_data():
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [5, 4, 3, 2, 1]
        })
        return df
    
    tester.add_test("数据加载", load_data, expected_type=pd.DataFrame)
    
    # 测试缺失值处理
    def handle_missing(df):
        return df.fillna(df.median())
    
    df = pd.DataFrame({'a': [1, 2, np.nan], 'b': [4, 5, 6]})
    tester.add_test("缺失值处理", handle_missing, df, expected_type=pd.DataFrame)
    
    # 测试标准化
    def normalize(df):
        return (df - df.mean()) / df.std()
    
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    result = normalize(df)
    tester.add_test("标准化", normalize, df, expected_range=(0, 1))
    
    return tester


def test_model_training():
    """测试模型训练函数"""
    tester = CodeTester()
    
    # 测试线性回归
    from sklearn.linear_model import LinearRegression
    
    def train_linear():
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([2, 4, 6, 8, 10])
        model = LinearRegression()
        model.fit(X, y)
        return model.score(X, y)
    
    tester.add_test("线性回归训练", train_linear, expected_range=(0.9, 1.0))
    
    # 测试预测
    def predict():
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([2, 4, 6, 8, 10])
        model = LinearRegression()
        model.fit(X, y)
        return model.predict([[6]])[0]
    
    tester.add_test("线性回归预测", predict, expected_range=(10, 14))
    
    return tester


def test_optimization():
    """测试优化函数"""
    tester = CodeTester()
    
    # 测试遗传算法
    def ga_optimization():
        def f(x):
            return -(x[0]**2 + x[1]**2)
        
        best_x = [0, 0]
        best_y = 0
        
        for _ in range(100):
            x = np.random.uniform(-10, 10, 2)
            y = f(x)
            if y > best_y:
                best_x = x
                best_y = y
        
        return best_y
    
    tester.add_test("遗传算法优化", ga_optimization, expected_range=(-1, 0))
    
    # 测试粒子群
    def pso_optimization():
        def f(x):
            return (x[0]-1)**2 + (x[1]-2)**2
        
        best_x = np.random.uniform(-10, 10, 2)
        best_y = f(best_x)
        
        for _ in range(50):
            x = best_x + np.random.randn(2) * 0.5
            y = f(x)
            if y < best_y:
                best_x = x
                best_y = y
        
        return best_y
    
    tester.add_test("粒子群优化", pso_optimization, expected_range=(0, 10))
    
    return tester


def run_example():
    """
    示例：完整测试套件
    """
    print("=" * 60)
    print("代码测试示例")
    print("=" * 60)
    
    # 数据处理测试
    print("\n--- 数据处理测试 ---")
    tester1 = test_data_processing()
    tester1.run_all()
    
    # 模型训练测试
    print("\n--- 模型训练测试 ---")
    tester2 = test_model_training()
    tester2.run_all()
    
    # 优化测试
    print("\n--- 优化测试 ---")
    tester3 = test_optimization()
    tester3.run_all()
    
    # 汇总报告
    all_results = {**tester1.results, **tester2.results, **tester3.results}
    passed = sum(1 for s in all_results.values() if s == TestStatus.PASS)
    total = len(all_results)
    
    print("\n" + "=" * 60)
    print(f"总测试结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    run_example()
