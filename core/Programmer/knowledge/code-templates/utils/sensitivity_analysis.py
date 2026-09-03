"""
灵敏度分析工具模板
来源: 高教杯优秀论文 (A001, A092, B195)
适用问题: 参数敏感性分析、鲁棒性检验、模型验证
输入: 模型函数、基准参数、参数范围
输出: 灵敏度结果、Tornado图、参数影响排序
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class SensitivityAnalyzer:
    """
    灵敏度分析工具
    
    Parameters
    ----------
    model_func : callable
        模型函数，输入参数字典，输出目标值
    base_params : dict
        基准参数 {'param_name': base_value, ...}
    param_ranges : dict
        参数范围 {'param_name': (low, high), ...}
    """
    
    def __init__(
        self,
        model_func: Callable,
        base_params: Dict[str, float],
        param_ranges: Dict[str, Tuple[float, float]]
    ):
        self.model_func = model_func
        self.base_params = base_params
        self.param_ranges = param_ranges
        
        self.base_value = None
        self.results = {}
    
    def compute_base_value(self):
        """计算基准值"""
        self.base_value = self.model_func(self.base_params)
        return self.base_value
    
    def one_factor_at_a_time(self, n_points: int = 20) -> Dict[str, List[Tuple[float, float]]]:
        """
        单因素分析（OFAT）
        
        Parameters
        ----------
        n_points : int
            每个参数的采样点数
        
        Returns
        -------
        results : dict
            各参数的灵敏度结果
        """
        if self.base_value is None:
            self.compute_base_value()
        
        for param_name, (low, high) in self.param_ranges.items():
            values = np.linspace(low, high, n_points)
            objective_values = []
            
            for value in values:
                params = self.base_params.copy()
                params[param_name] = value
                obj_value = self.model_func(params)
                objective_values.append(obj_value)
            
            self.results[param_name] = list(zip(values, objective_values))
        
        return self.results
    
    def compute_sensitivity_indices(self) -> Dict[str, float]:
        """
        计算灵敏度指标
        
        Returns
        -------
        indices : dict
            灵敏度指标（归一化影响程度）
        """
        if not self.results:
            self.one_factor_at_a_time()
        
        indices = {}
        
        for param_name, values in self.results.items():
            obj_values = [v[1] for v in values]
            
            # 计算变化范围
            value_range = max(obj_values) - min(obj_values)
            
            # 归一化（相对于基准值）
            if self.base_value != 0:
                normalized_range = value_range / abs(self.base_value)
            else:
                normalized_range = value_range
            
            indices[param_name] = normalized_range
        
        # 归一化为总和=1
        total = sum(indices.values())
        if total > 0:
            indices = {k: v / total for k, v in indices.items()}
        
        return indices
    
    def tornado_plot(self, figsize: Tuple[int, int] = (10, 6)):
        """
        绘制Tornado图
        
        Parameters
        ----------
        figsize : tuple
            图形大小
        """
        if not self.results:
            self.one_factor_at_a_time()
        
        # 计算各参数的影响
        param_names = []
        low_effects = []
        high_effects = []
        
        for param_name, values in self.results.items():
            obj_values = [v[1] for v in values]
            low_effect = min(obj_values) - self.base_value
            high_effect = max(obj_values) - self.base_value
            
            param_names.append(param_name)
            low_effects.append(low_effect)
            high_effects.append(high_effect)
        
        # 按影响力排序
        total_effects = [abs(l) + abs(h) for l, h in zip(low_effects, high_effects)]
        sorted_indices = np.argsort(total_effects)[::-1]
        
        param_names = [param_names[i] for i in sorted_indices]
        low_effects = [low_effects[i] for i in sorted_indices]
        high_effects = [high_effects[i] for i in sorted_indices]
        
        # 绘图
        fig, ax = plt.subplots(figsize=figsize)
        y_pos = range(len(param_names))
        
        ax.barh(y_pos, high_effects, height=0.4, label='High (+20%)', 
                color='red', alpha=0.6, align='center')
        ax.barh([y + 0.4 for y in y_pos], low_effects, height=0.4, 
                label='Low (-20%)', color='blue', alpha=0.6, align='center')
        
        ax.set_yticks([y + 0.2 for y in y_pos])
        ax.set_yticklabels(param_names)
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
        ax.set_xlabel('Change in Objective')
        ax.set_title('Tornado Plot - Parameter Sensitivity')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        return fig
    
    def line_plot(self, figsize: Tuple[int, int] = (12, 6)):
        """
        绘制参数影响曲线图
        """
        if not self.results:
            self.one_factor_at_a_time()
        
        n_params = len(self.results)
        n_cols = min(3, n_params)
        n_rows = (n_params + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        if n_params == 1:
            axes = np.array([axes])
        axes = axes.flatten()
        
        for idx, (param_name, values) in enumerate(self.results.items()):
            x = [v[0] for v in values]
            y = [v[1] for v in values]
            
            axes[idx].plot(x, y, 'b-', linewidth=2, marker='o', markersize=4)
            axes[idx].axhline(y=self.base_value, color='r', linestyle='--', 
                            label='Base value')
            axes[idx].set_xlabel(param_name)
            axes[idx].set_ylabel('Objective')
            axes[idx].set_title(f'{param_name} Sensitivity')
            axes[idx].legend()
            axes[idx].grid(True, alpha=0.3)
        
        # 隐藏多余的子图
        for idx in range(n_params, len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        return fig
    
    def report(self) -> str:
        """生成灵敏度分析报告"""
        indices = self.compute_sensitivity_indices()
        
        report_lines = [
            "=" * 60,
            "灵敏度分析报告",
            "=" * 60,
            f"\n基准值: {self.base_value:.6f}",
            "\n参数灵敏度指标（归一化）:",
            "-" * 40
        ]
        
        # 按灵敏度排序
        sorted_params = sorted(indices.items(), key=lambda x: x[1], reverse=True)
        
        for param_name, index in sorted_params:
            bar_length = int(index * 50)
            bar = "█" * bar_length
            report_lines.append(f"{param_name:20s}: {index:.4f} {bar}")
        
        report_lines.extend([
            "\n" + "-" * 40,
            f"总影响力: {sum(indices.values()):.4f}",
            "\n结论:",
        ])
        
        # 识别最敏感参数
        if sorted_params:
            most_sensitive = sorted_params[0]
            report_lines.append(
                f"  最敏感参数: {most_sensitive[0]} (影响力: {most_sensitive[1]:.4f})"
            )
        
        return "\n".join(report_lines)


def run_example():
    """
    示例：波浪能装置参数灵敏度分析
    """
    # 定义模型函数
    def wave_energy_model(params):
        """
        简化的波浪能功率模型
        P = 0.5 * ρ * g * A² * Cw * η
        """
        A = params['wave_height']  # 波高
        T = params['wave_period']  # 波周期
        h = params['water_depth']  # 水深
        m = params['mass']  # 装置质量
        
        rho = 1025  # 海水密度
        g = 9.81   # 重力加速度
        
        # 简化功率计算
        omega = 2 * np.pi / T
        Cw = 0.5 * (1 - np.exp(-0.1 * h))  # 波浪能捕获系数
        eta = 1 / (1 + 0.01 * m)  # 效率（与质量负相关）
        
        P = 0.5 * rho * g * A**2 * Cw * eta
        
        return P
    
    # 基准参数
    base_params = {
        'wave_height': 2.0,    # 波高 2m
        'wave_period': 8.0,    # 波周期 8s
        'water_depth': 20.0,   # 水深 20m
        'mass': 1000.0         # 质量 1000kg
    }
    
    # 参数范围（±50%）
    param_ranges = {
        'wave_height': (1.0, 3.0),
        'wave_period': (4.0, 12.0),
        'water_depth': (10.0, 30.0),
        'mass': (500.0, 1500.0)
    }
    
    print("=" * 60)
    print("灵敏度分析示例 - 波浪能装置参数")
    print("=" * 60)
    
    # 创建分析器
    analyzer = SensitivityAnalyzer(wave_energy_model, base_params, param_ranges)
    
    # 计算基准值
    base_value = analyzer.compute_base_value()
    print(f"\n基准功率: {base_value:.2f} W")
    
    # 单因素分析
    results = analyzer.one_factor_at_a_time(n_points=10)
    
    # 计算灵敏度指标
    indices = analyzer.compute_sensitivity_indices()
    print("\n灵敏度指标:")
    for param, index in indices.items():
        print(f"  {param}: {index:.4f}")
    
    # 生成报告
    print("\n" + analyzer.report())
    
    # 绘制Tornado图
    fig = analyzer.tornado_plot()
    plt.savefig('figures/sensitivity_tornado.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # 绘制参数影响曲线
    fig = analyzer.line_plot()
    plt.savefig('figures/sensitivity_lines.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
