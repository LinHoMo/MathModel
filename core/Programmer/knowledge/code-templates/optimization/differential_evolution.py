#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
差分进化算法模板
功能：参数设置、约束处理、结果可视化
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import differential_evolution, minimize
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class DifferentialEvolutionOptimizer:
    """差分进化算法优化器"""
    
    def __init__(self, objective_func, bounds, constraints=None, 
                 strategy='best1bin', maxiter=1000, popsize=15,
                 mutation=(0.5, 1.0), recombination=0.7, seed=42):
        """
        初始化差分进化优化器
        参数：
            objective_func: 目标函数
            bounds: 变量边界 [(low, high), ...]
            constraints: 约束条件列表
            strategy: 变异策略
            maxiter: 最大迭代次数
            popsize: 种群大小
            mutation: 变异因子范围
            recombination: 交叉概率
            seed: 随机种子
        """
        self.objective_func = objective_func
        self.bounds = bounds
        self.constraints = constraints or []
        self.strategy = strategy
        self.maxiter = maxiter
        self.popsize = popsize
        self.mutation = mutation
        self.recombination = recombination
        self.seed = seed
        
        # 存储优化历史
        self.history = {
            'convergence': [],
            'best_fitness': [],
            'population_diversity': []
        }
        self.result = None
    
    def _callback(self, convergence, xk, *args):
        """回调函数，记录优化过程"""
        self.history['convergence'].append(convergence)
        self.history['best_fitness'].append(
            self.objective_func(xk) if not self.constraints else 
            self.objective_func(xk) + self._constraint_penalty(xk)
        )
    
    def _constraint_penalty(self, x):
        """计算约束惩罚"""
        penalty = 0
        for constraint in self.constraints:
            if constraint['type'] == 'eq':
                penalty += abs(constraint['fun'](x)) * constraint.get('penalty', 1000)
            elif constraint['type'] == 'ineq':
                violation = -constraint['fun'](x)
                if violation > 0:
                    penalty += violation * constraint.get('penalty', 1000)
        return penalty
    
    def optimize(self, callback=True):
        """
        执行优化
        返回：优化结果
        """
        print("开始差分进化优化...")
        print(f"策略: {self.strategy}")
        print(f"种群大小: {self.popsize}")
        print(f"最大迭代: {self.maxiter}")
        print("-" * 40)
        
        # 自定义回调
        iteration_count = [0]
        
        def custom_callback(xk, convergence):
            iteration_count[0] += 1
            self.history['convergence'].append(convergence)
            self.history['best_fitness'].append(self.objective_func(xk))
            
            if iteration_count[0] % 50 == 0:
                print(f"  迭代 {iteration_count[0]}: 最佳适应度 = {self.objective_func(xk):.6f}")
        
        # 执行优化
        self.result = differential_evolution(
            self.objective_func,
            self.bounds,
            strategy=self.strategy,
            maxiter=self.maxiter,
            popsize=self.popsize,
            mutation=self.mutation,
            recombination=self.recombination,
            seed=self.seed,
            callback=custom_callback if callback else None,
            constraints=self.constraints if self.constraints else None,
            tol=1e-7,
            polish=True  # 最后进行局部优化
        )
        
        print("-" * 40)
        print(f"优化完成!")
        print(f"最优解: {self.result.x}")
        print(f"最优值: {self.result.fun:.6f}")
        print(f"迭代次数: {self.result.nit}")
        print(f"函数评估次数: {self.result.nfev}")
        
        return self.result
    
    def plot_convergence(self):
        """绘制收敛曲线"""
        if not self.history['convergence']:
            print("没有收敛历史数据")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. 收敛曲线
        axes[0, 0].plot(self.history['convergence'], linewidth=2, color='blue')
        axes[0, 0].set_title('收敛曲线')
        axes[0, 0].set_xlabel('迭代次数')
        axes[0, 0].set_ylabel('收敛度')
        axes[0, 0].set_yscale('log')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 最佳适应度变化
        axes[0, 1].plot(self.history['best_fitness'], linewidth=2, color='red')
        axes[0, 1].set_title('最佳适应度变化')
        axes[0, 1].set_xlabel('迭代次数')
        axes[0, 1].set_ylabel('适应度值')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 参数空间搜索轨迹
        if len(self.bounds) >= 2:
            # 模拟搜索轨迹（实际中需要记录）
            n_points = min(100, len(self.history['best_fitness']))
            x轨迹 = np.random.uniform(
                [b[0] for b in self.bounds[:2]],
                [b[1] for b in self.bounds[:2]],
                (n_points, 2)
            )
            axes[1, 0].scatter(x轨迹[:, 0], x轨迹[:, 1], 
                              c=range(n_points), cmap='viridis', alpha=0.6)
            axes[1, 0].scatter(self.result.x[0], self.result.x[1], 
                              c='red', marker='*', s=200, label='最优解')
            axes[1, 0].set_title('参数空间搜索轨迹')
            axes[1, 0].set_xlabel('参数1')
            axes[1, 0].set_ylabel('参数2')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 最优解信息
        info_text = f"""
优化结果摘要:
================
最优值: {self.result.fun:.6f}
迭代次数: {self.result.nit}
函数评估: {self.result.nfev}
是否成功: {self.result.success}

最优解:
"""
        for i, (val, bound) in enumerate(zip(self.result.x, self.bounds)):
            info_text += f"  x[{i}] = {val:.6f} (范围: [{bound[0]:.2f}, {bound[1]:.2f}])\n"
        
        axes[1, 1].text(0.1, 0.5, info_text, transform=axes[1, 1].transAxes,
                       fontsize=10, verticalalignment='center',
                       fontfamily='monospace',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        axes[1, 1].axis('off')
        axes[1, 1].set_title('优化结果摘要')
        
        plt.tight_layout()
        plt.show()
    
    def sensitivity_analysis(self, n_samples=100):
        """参数敏感性分析"""
        if self.result is None:
            print("请先执行优化")
            return
        
        print("\n参数敏感性分析...")
        
        n_params = len(self.result.x)
        sensitivity = np.zeros(n_params)
        
        for i in range(n_params):
            # 在最优解附近扰动
            x_perturbed = self.result.x.copy()
            perturbation = (self.bounds[i][1] - self.bounds[i][0]) * 0.01
            
            # 正向扰动
            x_perturbed[i] = self.result.x[i] + perturbation
            f_plus = self.objective_func(x_perturbed)
            
            # 负向扰动
            x_perturbed[i] = self.result.x[i] - perturbation
            f_minus = self.objective_func(x_perturbed)
            
            # 计算敏感性
            sensitivity[i] = abs(f_plus - f_minus) / (2 * perturbation)
        
        # 归一化敏感性
        sensitivity_normalized = sensitivity / sensitivity.sum()
        
        # 绘制敏感性图
        plt.figure(figsize=(10, 6))
        bars = plt.bar(range(n_params), sensitivity_normalized, 
                      color='steelblue', edgecolor='black', alpha=0.7)
        plt.xlabel('参数索引')
        plt.ylabel('相对敏感性')
        plt.title('参数敏感性分析')
        plt.xticks(range(n_params))
        plt.grid(True, alpha=0.3, axis='y')
        
        # 在柱状图上显示数值
        for bar, val in zip(bars, sensitivity_normalized):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.show()
        
        return sensitivity_normalized


def demo_objective_functions():
    """演示目标函数"""
    
    # 1. Sphere函数 (简单凸函数)
    def sphere(x):
        return sum(xi**2 for xi in x)
    
    # 2. Rosenbrock函数 (经典测试函数)
    def rosenbrock(x):
        return sum(100.0 * (x[i+1] - x[i]**2)**2 + (1 - x[i])**2 
                  for i in range(len(x)-1))
    
    # 3. Rastrigin函数 (多峰函数)
    def rastrigin(x):
        A = 10
        n = len(x)
        return A * n + sum(xi**2 - A * np.cos(2 * np.pi * xi) for xi in x)
    
    # 4. Ackley函数 (多峰函数)
    def ackley(x):
        n = len(x)
        sum1 = sum(xi**2 for xi in x)
        sum2 = sum(np.cos(2 * np.pi * xi) for xi in x)
        return -20 * np.exp(-0.2 * np.sqrt(sum1 / n)) - np.exp(sum2 / n) + 20 + np.e
    
    return {
        'sphere': sphere,
        'rosenbrock': rosenbrock,
        'rastrigin': rastrigin,
        'ackley': ackley
    }


def main():
    """主函数 - 演示差分进化算法"""
    
    print("=" * 60)
    print("差分进化算法模板演示")
    print("=" * 60)
    
    # 获取演示函数
    functions = demo_objective_functions()
    
    # 示例1: 优化Sphere函数
    print("\n【示例1: 优化Sphere函数】")
    print("-" * 40)
    
    bounds_sphere = [(-5.0, 5.0)] * 5  # 5维Sphere函数
    
    optimizer_sphere = DifferentialEvolutionOptimizer(
        objective_func=functions['sphere'],
        bounds=bounds_sphere,
        strategy='best1bin',
        maxiter=200,
        popsize=20,
        seed=42
    )
    
    result_sphere = optimizer_sphere.optimize()
    optimizer_sphere.plot_convergence()
    optimizer_sphere.sensitivity_analysis()
    
    # 示例2: 优化Rosenbrock函数
    print("\n【示例2: 优化Rosenbrock函数】")
    print("-" * 40)
    
    bounds_rosenbrock = [(-5.0, 5.0)] * 3  # 3维Rosenbrock函数
    
    optimizer_rosenbrock = DifferentialEvolutionOptimizer(
        objective_func=functions['rosenbrock'],
        bounds=bounds_rosenbrock,
        strategy='rand1bin',
        maxiter=300,
        popsize=25,
        seed=42
    )
    
    result_rosenbrock = optimizer_rosenbrock.optimize()
    optimizer_rosenbrock.plot_convergence()
    
    # 示例3: 带约束的优化
    print("\n【示例3: 带约束的优化】")
    print("-" * 40)
    
    # 目标函数: 最小化 (x-1)^2 + (y-2)^2
    def constrained_objective(x):
        return (x[0] - 1)**2 + (x[1] - 2)**2
    
    # 约束条件: x + y <= 3, x >= 0, y >= 0
    constraints = [
        {'type': 'ineq', 'fun': lambda x: 3 - x[0] - x[1], 'penalty': 1000},
        {'type': 'ineq', 'fun': lambda x: x[0], 'penalty': 1000},
        {'type': 'ineq', 'fun': lambda x: x[1], 'penalty': 1000}
    ]
    
    bounds_constrained = [(0, 5), (0, 5)]
    
    optimizer_constrained = DifferentialEvolutionOptimizer(
        objective_func=constrained_objective,
        bounds=bounds_constrained,
        constraints=constraints,
        strategy='best1bin',
        maxiter=200,
        popsize=20,
        seed=42
    )
    
    result_constrained = optimizer_constrained.optimize()
    optimizer_constrained.plot_convergence()
    
    # 可视化约束
    plt.figure(figsize=(8, 6))
    x_range = np.linspace(0, 5, 100)
    y_range = np.linspace(0, 5, 100)
    X, Y = np.meshgrid(x_range, y_range)
    Z = (X - 1)**2 + (Y - 2)**2
    
    plt.contour(X, Y, Z, levels=20, cmap='viridis', alpha=0.7)
    plt.colorbar(label='目标函数值')
    
    # 绘制约束区域
    plt.fill_between(x_range, 0, 3 - x_range, alpha=0.3, color='gray', label='可行域')
    
    # 绘制最优解
    plt.scatter(result_constrained.x[0], result_constrained.x[1], 
               c='red', marker='*', s=200, label='最优解', zorder=5)
    
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('带约束优化结果可视化')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 5)
    plt.ylim(0, 5)
    plt.show()
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
