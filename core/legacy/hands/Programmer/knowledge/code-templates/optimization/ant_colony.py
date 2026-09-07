#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蚁群算法模板
功能：信息素更新、路径构建、结果可视化
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import random
import math
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class AntColonyOptimization:
    """蚁群算法优化器"""
    
    def __init__(self, n_ants=50, n_iterations=100, alpha=1.0, beta=2.0,
                 rho=0.1, q=1.0, elite_weight=2.0):
        """
        初始化蚁群算法
        参数：
            n_ants: 蚂蚁数量
            n_iterations: 迭代次数
            alpha: 信息素重要程度因子
            beta: 启发式信息重要程度因子
            rho: 信息素挥发系数
            q: 信息素增强强度
            elite_weight: 精英蚂蚁权重
        """
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.q = q
        self.elite_weight = elite_weight
        
        # 存储结果
        self.pheromone = None
        self.distance_matrix = None
        self.heuristic = None
        self.best_solution = None
        self.best_cost = float('inf')
        self.history = {
            'best_cost': [],
            'avg_cost': [],
            'convergence': []
        }
    
    def _calculate_distance_matrix(self, coords: np.ndarray) -> np.ndarray:
        """计算距离矩阵"""
        n = len(coords)
        dist_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist_matrix[i, j] = np.sqrt(np.sum((coords[i] - coords[j])**2))
                else:
                    dist_matrix[i, j] = np.inf  # 对角线设为无穷大
        
        return dist_matrix
    
    def _initialize_pheromone(self, n_cities: int, init_pheromone: float = 1.0):
        """初始化信息素矩阵"""
        self.pheromone = np.full((n_cities, n_cities), init_pheromone)
    
    def _calculate_heuristic(self):
        """计算启发式信息矩阵（距离的倒数）"""
        self.heuristic = 1.0 / (self.distance_matrix + 1e-10)  # 避免除零
        np.fill_diagonal(self.heuristic, 0)
    
    def _construct_solution(self, start_city: int = 0) -> Tuple[List[int], float]:
        """
        构建解路径
        参数：
            start_city: 起始城市
        返回：
            路径和总距离
        """
        n_cities = self.distance_matrix.shape[0]
        visited = [False] * n_cities
        path = [start_city]
        visited[start_city] = True
        
        total_distance = 0
        
        for _ in range(n_cities - 1):
            current_city = path[-1]
            
            # 计算转移概率
            probabilities = np.zeros(n_cities)
            
            for next_city in range(n_cities):
                if not visited[next_city]:
                    # 信息素强度
                    tau = self.pheromone[current_city, next_city] ** self.alpha
                    # 启发式信息
                    eta = self.heuristic[current_city, next_city] ** self.beta
                    probabilities[next_city] = tau * eta
            
            # 归一化概率
            prob_sum = probabilities.sum()
            if prob_sum > 0:
                probabilities = probabilities / prob_sum
            else:
                # 如果所有概率为0，随机选择
                probabilities = np.array([1.0/n_cities if not visited[i] else 0 
                                        for i in range(n_cities)])
                probabilities = probabilities / probabilities.sum()
            
            # 轮盘赌选择
            next_city = np.random.choice(n_cities, p=probabilities)
            
            path.append(next_city)
            visited[next_city] = True
            total_distance += self.distance_matrix[current_city, next_city]
        
        # 返回起始城市
        total_distance += self.distance_matrix[path[-1], path[0]]
        path.append(path[0])
        
        return path, total_distance
    
    def _update_pheromone(self, solutions: List[Tuple[List[int], float]]):
        """
        更新信息素
        参数：
            solutions: 所有蚂蚁的解决方案 [(路径, 距离), ...]
        """
        # 信息素挥发
        self.pheromone *= (1 - self.rho)
        
        # 按距离排序
        solutions.sort(key=lambda x: x[1])
        
        # 信息素增强
        for i, (path, distance) in enumerate(solutions):
            # 计算信息素增量
            delta_tau = self.q / distance
            
            # 普通蚂蚁
            for j in range(len(path) - 1):
                city_i, city_j = path[j], path[j + 1]
                self.pheromone[city_i, city_j] += delta_tau
                self.pheromone[city_j, city_i] += delta_tau
            
            # 精英蚂蚁（排名靠前的蚂蚁）
            if i < 3:  # 前3名为精英蚂蚁
                elite_delta = delta_tau * self.elite_weight / (i + 1)
                for j in range(len(path) - 1):
                    city_i, city_j = path[j], path[j + 1]
                    self.pheromone[city_i, city_j] += elite_delta
                    self.pheromone[city_j, city_i] += elite_delta
        
        # 限制信息素范围
        self.pheromone = np.clip(self.pheromone, 0.01, 10.0)
    
    def solve(self, coords: np.ndarray, start_city: int = 0) -> Tuple[List[int], float]:
        """
        执行蚁群算法
        参数：
            coords: 城市坐标
            start_city: 起始城市
        返回：
            最佳路径和距离
        """
        n_cities = len(coords)
        
        print("初始化蚁群算法...")
        print(f"城市数量: {n_cities}")
        print(f"蚂蚁数量: {self.n_ants}")
        print(f"迭代次数: {self.n_iterations}")
        print("-" * 40)
        
        # 计算距离矩阵
        self.distance_matrix = self._calculate_distance_matrix(coords)
        
        # 初始化信息素
        self._initialize_pheromone(n_cities)
        
        # 计算启发式信息
        self._calculate_heuristic()
        
        # 迭代优化
        for iteration in range(self.n_iterations):
            solutions = []
            
            # 每只蚂蚁构建解
            for ant in range(self.n_ants):
                path, distance = self._construct_solution(start_city)
                solutions.append((path, distance))
                
                # 更新最佳解
                if distance < self.best_cost:
                    self.best_cost = distance
                    self.best_solution = path
            
            # 记录历史
            costs = [s[1] for s in solutions]
            self.history['best_cost'].append(self.best_cost)
            self.history['avg_cost'].append(np.mean(costs))
            self.history['convergence'].append(
                np.std(costs) / np.mean(costs) if np.mean(costs) > 0 else 0
            )
            
            # 更新信息素
            self._update_pheromone(solutions)
            
            # 打印进度
            if (iteration + 1) % 20 == 0:
                print(f"迭代 {iteration + 1}/{self.n_iterations}: "
                      f"最佳距离 = {self.best_cost:.2f}, "
                      f"平均距离 = {np.mean(costs):.2f}")
        
        print("-" * 40)
        print(f"优化完成!")
        print(f"最佳距离: {self.best_cost:.2f}")
        print(f"最佳路径: {self.best_solution}")
        
        return self.best_solution, self.best_cost
    
    def plot_results(self, coords: np.ndarray):
        """可视化结果"""
        if self.best_solution is None:
            print("没有求解结果可绘制")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. 最佳路径图
        ax1 = axes[0, 0]
        
        # 绘制城市
        ax1.scatter(coords[:, 0], coords[:, 1], c='red', s=100, 
                   edgecolors='black', zorder=5, label='城市')
        
        # 绘制路径
        for i in range(len(self.best_solution) - 1):
            city_i = self.best_solution[i]
            city_j = self.best_solution[i + 1]
            ax1.plot([coords[city_i, 0], coords[city_j, 0]],
                    [coords[city_i, 1], coords[city_j, 1]],
                    'b-', linewidth=1.5, alpha=0.7)
        
        # 标记城市编号
        for i, (x, y) in enumerate(coords):
            ax1.annotate(str(i), (x, y), textcoords="offset points",
                        xytext=(0, 10), ha='center', fontsize=9)
        
        ax1.set_title(f'最佳路径 (距离: {self.best_cost:.2f})')
        ax1.set_xlabel('X坐标')
        ax1.set_ylabel('Y坐标')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 2. 收敛曲线
        ax2 = axes[0, 1]
        ax2.plot(self.history['best_cost'], linewidth=2, color='blue', label='最佳距离')
        ax2.plot(self.history['avg_cost'], linewidth=1, color='red', 
                alpha=0.7, label='平均距离')
        ax2.set_title('收敛曲线')
        ax2.set_xlabel('迭代次数')
        ax2.set_ylabel('距离')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 信息素矩阵热力图
        ax3 = axes[1, 0]
        im = ax3.imshow(self.pheromone, cmap='hot', aspect='auto')
        plt.colorbar(im, ax=ax3, label='信息素强度')
        ax3.set_title('信息素矩阵')
        ax3.set_xlabel('城市')
        ax3.set_ylabel('城市')
        
        # 4. 路径长度变化
        ax4 = axes[1, 1]
        if len(self.history['best_cost']) > 1:
            improvements = []
            for i in range(1, len(self.history['best_cost'])):
                improvement = (self.history['best_cost'][i-1] - self.history['best_cost'][i]) / \
                             self.history['best_cost'][i-1] * 100
                improvements.append(improvement)
            
            ax4.bar(range(len(improvements)), improvements, color='steelblue', 
                   edgecolor='black', alpha=0.7)
            ax4.axhline(y=0, color='red', linestyle='--', linewidth=1)
            ax4.set_title('每代改进百分比')
            ax4.set_xlabel('迭代次数')
            ax4.set_ylabel('改进百分比 (%)')
            ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.show()
    
    def plot_pheromone_evolution(self, coords: np.ndarray, snapshots: List[int] = None):
        """绘制信息素演化过程"""
        if snapshots is None:
            snapshots = [0, 25, 50, 75, 99]
        
        fig, axes = plt.subplots(1, len(snapshots), figsize=(4 * len(snapshots), 4))
        if len(snapshots) == 1:
            axes = [axes]
        
        # 这里简化处理，实际应用中需要记录每代的信息素
        for i, snap in enumerate(snapshots):
            if i < len(axes):
                # 绘制城市
                axes[i].scatter(coords[:, 0], coords[:, 1], c='red', s=50, 
                              edgecolors='black', zorder=5)
                
                # 绘制路径（简化）
                if self.best_solution:
                    for j in range(len(self.best_solution) - 1):
                        city_i = self.best_solution[j]
                        city_j = self.best_solution[j + 1]
                        axes[i].plot([coords[city_i, 0], coords[city_j, 0]],
                                    [coords[city_i, 1], coords[city_j, 1]],
                                    'b-', linewidth=1, alpha=0.5)
                
                axes[i].set_title(f'迭代 {snap}')
                axes[i].grid(True, alpha=0.3)
        
        plt.suptitle('信息素演化过程', fontsize=14)
        plt.tight_layout()
        plt.show()


def generate_cities(n_cities: int = 20, area_size: float = 100.0) -> np.ndarray:
    """生成随机城市坐标"""
    np.random.seed(42)
    coords = np.random.rand(n_cities, 2) * area_size
    return coords


def demo_tsp():
    """演示旅行商问题(TSP)"""
    print("=" * 60)
    print("蚁群算法解决旅行商问题(TSP)")
    print("=" * 60)
    
    # 生成城市
    n_cities = 20
    coords = generate_cities(n_cities, area_size=100)
    
    print(f"\n生成了{n_cities}个城市")
    print(f"城市坐标范围: [{coords.min():.2f}, {coords.max():.2f}]")
    
    # 创建蚁群算法求解器
    aco = AntColonyOptimization(
        n_ants=30,
        n_iterations=100,
        alpha=1.0,
        beta=2.0,
        rho=0.1,
        q=1.0,
        elite_weight=2.0
    )
    
    # 求解
    best_path, best_cost = aco.solve(coords, start_city=0)
    
    # 可视化结果
    aco.plot_results(coords)
    
    return aco, coords


def demo_function_optimization():
    """演示函数优化"""
    print("\n" + "=" * 60)
    print("蚁群算法进行函数优化")
    print("=" * 60)
    
    # 目标函数: Rastrigin函数
    def rastrigin(x):
        A = 10
        n = len(x)
        return A * n + sum(xi**2 - A * np.cos(2 * np.pi * xi) for xi in x)
    
    # 参数范围
    bounds = [(-5.12, 5.12)] * 2  # 2维Rastrigin函数
    
    print(f"优化Rastrigin函数")
    print(f"维度: 2")
    print(f"搜索范围: {bounds}")
    
    # 离散化搜索空间
    n_intervals = 50
    discretized_ranges = []
    for low, high in bounds:
        values = np.linspace(low, high, n_intervals)
        discretized_ranges.append(values)
    
    # 创建网格
    X, Y = np.meshgrid(discretized_ranges[0], discretized_ranges[1])
    grid_points = np.column_stack([X.ravel(), Y.ravel()])
    
    # 计算每个网格点的函数值
    grid_values = np.array([rastrigin(point) for point in grid_points])
    
    # 简化的蚁群算法用于函数优化
    n_ants = 20
    n_iterations = 50
    best_value = float('inf')
    best_point = None
    
    # 初始化信息素
    pheromone = np.ones(len(grid_points))
    
    history = []
    
    print("\n开始优化...")
    for iteration in range(n_iterations):
        solutions = []
        
        # 每只蚂蚁选择一个点
        for ant in range(n_ants):
            # 根据信息素和函数值选择
            probabilities = 1.0 / (grid_values + 1e-10) * pheromone
            probabilities = probabilities / probabilities.sum()
            
            selected_idx = np.random.choice(len(grid_points), p=probabilities)
            selected_point = grid_points[selected_idx]
            selected_value = grid_values[selected_idx]
            
            solutions.append((selected_point, selected_value, selected_idx))
            
            if selected_value < best_value:
                best_value = selected_value
                best_point = selected_point
        
        # 更新信息素
        pheromone *= 0.9  # 挥发
        
        # 增强好的解
        solutions.sort(key=lambda x: x[1])
        for i, (point, value, idx) in enumerate(solutions[:5]):
            pheromone[idx] += 1.0 / (value + 1e-10) * (6 - i)
        
        history.append(best_value)
        
        if (iteration + 1) % 10 == 0:
            print(f"迭代 {iteration + 1}/{n_iterations}: "
                  f"最佳值 = {best_value:.4f}")
    
    print(f"\n优化完成!")
    print(f"最佳点: {best_point}")
    print(f"最佳函数值: {best_value:.4f}")
    
    # 可视化
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # 函数等高线
    ax1 = axes[0]
    contour = ax1.contour(X, Y, grid_values.reshape(X.shape), levels=20, cmap='viridis')
    ax1.colorbar(contour)
    ax1.scatter(best_point[0], best_point[1], c='red', marker='*', s=200, 
               label='最佳解', zorder=5)
    ax1.set_title('Rastrigin函数等高线')
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 收敛曲线
    ax2 = axes[1]
    ax2.plot(history, linewidth=2, color='blue')
    ax2.set_title('收敛曲线')
    ax2.set_xlabel('迭代次数')
    ax2.set_ylabel('最佳函数值')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def main():
    """主函数 - 演示蚁群算法"""
    
    # 演示旅行商问题
    aco_tsp, coords_tsp = demo_tsp()
    
    # 演示函数优化
    demo_function_optimization()
    
    print("\n" + "=" * 60)
    print("所有演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
