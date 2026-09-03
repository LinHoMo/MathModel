"""
模拟退火模板
来源: 高教杯优秀论文 (B195, B196)
适用问题: 组合优化、TSP、调度问题、避免局部最优
输入: 目标函数、初始解、变量边界
输出: 最优解、最优值、收敛历史
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, List, Tuple, Optional
import math
import warnings
warnings.filterwarnings('ignore')


class SimulatedAnnealing:
    """
    模拟退火算法
    
    Parameters
    ----------
    objective : callable
        目标函数（最小化）
    bounds : list of tuples
        变量边界 [(low, high), ...]
    initial_solution : ndarray, optional
        初始解，若不提供则随机生成
    T0 : float, default=1000
        初始温度
    Tmin : float, default=1e-3
        停止温度
    alpha : float, default=0.95
        降温系数
    max_iterations : int, default=1000
        每个温度的最大迭代次数
    seed : int, default=42
        随机种子
    """
    
    def __init__(
        self,
        objective: Callable,
        bounds: List[Tuple[float, float]],
        initial_solution: Optional[np.ndarray] = None,
        T0: float = 1000,
        Tmin: float = 1e-3,
        alpha: float = 0.95,
        max_iterations: int = 1000,
        seed: int = 42
    ):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.T0 = T0
        self.Tmin = Tmin
        self.alpha = alpha
        self.max_iterations = max_iterations
        self.seed = seed
        
        np.random.seed(seed)
        
        self.dim = len(bounds)
        
        # 初始化解
        if initial_solution is not None:
            self.current = initial_solution.copy()
        else:
            self.current = np.zeros(self.dim)
            for i in range(self.dim):
                low, high = self.bounds[i]
                self.current[i] = np.random.uniform(low, high)
        
        self.current_score = self.objective(self.current)
        self.best = self.current.copy()
        self.best_score = self.current_score
        self.history = []
    
    def _generate_neighbor(self, solution: np.ndarray, temperature: float) -> np.ndarray:
        """
        生成邻域解
        
        使用自适应步长：温度高时步长大，温度低时步长小
        """
        neighbor = solution.copy()
        
        # 选择随机维度进行扰动
        n_perturb = max(1, self.dim // 3)  # 扰动1/3的维度
        indices = np.random.choice(self.dim, n_perturb, replace=False)
        
        for idx in indices:
            low, high = self.bounds[idx]
            range_val = high - low
            
            # 步长随温度衰减
            step_size = range_val * 0.1 * (temperature / self.T0)
            
            # 高斯扰动
            neighbor[idx] += np.random.normal(0, step_size)
            
            # 边界处理
            neighbor[idx] = np.clip(neighbor[idx], low, high)
        
        return neighbor
    
    def _acceptance_probability(self, delta: float, temperature: float) -> float:
        """
        计算接受概率
        
        Parameters
        ----------
        delta : float
            能量差（新解 - 当前解）
        temperature : float
            当前温度
        """
        if delta < 0:
            return 1.0
        else:
            return math.exp(-delta / temperature)
    
    def optimize(self) -> Tuple[np.ndarray, float]:
        """
        运行模拟退火
        
        Returns
        -------
        best_solution : ndarray
            最优解
        best_fitness : float
            最优值
        """
        temperature = self.T0
        self.history.append(self.best_score)
        
        while temperature > self.Tmin:
            for _ in range(self.max_iterations):
                # 生成邻域解
                neighbor = self._generate_neighbor(self.current, temperature)
                neighbor_score = self.objective(neighbor)
                
                # 计算能量差
                delta = neighbor_score - self.current_score
                
                # 接受准则
                if self._acceptance_probability(delta, temperature) > np.random.random():
                    self.current = neighbor
                    self.current_score = neighbor_score
                    
                    # 更新全局最优
                    if self.current_score < self.best_score:
                        self.best = self.current.copy()
                        self.best_score = self.current_score
                
                self.history.append(self.best_score)
            
            # 降温
            temperature *= self.alpha
        
        return self.best, self.best_score
    
    def plot_convergence(self):
        """绘制收敛曲线"""
        plt.figure(figsize=(10, 6))
        plt.plot(self.history, 'b-', linewidth=2)
        plt.xlabel('Iteration')
        plt.ylabel('Best Fitness')
        plt.title('Simulated Annealing Convergence')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return plt.gcf()
    
    def plot_temperature_profile(self):
        """绘制温度变化曲线"""
        temperatures = []
        temp = self.T0
        while temp > self.Tmin:
            temperatures.append(temp)
            temp *= self.alpha
        
        plt.figure(figsize=(10, 6))
        plt.plot(temperatures, 'r-', linewidth=2)
        plt.xlabel('Cooling Step')
        plt.ylabel('Temperature')
        plt.title('Temperature Profile')
        plt.yscale('log')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return plt.gcf()


def run_tsp_example():
    """
    示例：求解旅行商问题 (TSP)
    
    使用最近邻启发式生成初始解，模拟退火优化
    """
    # 随机生成城市坐标
    np.random.seed(42)
    n_cities = 20
    cities = np.random.rand(n_cities, 2) * 100
    
    # 计算距离矩阵
    def distance_matrix(cities):
        n = len(cities)
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.sqrt(np.sum((cities[i] - cities[j])**2))
        return dist
    
    dist = distance_matrix(cities)
    
    # 目标函数：总距离
    def total_distance(route):
        distance = 0
        for i in range(len(route) - 1):
            distance += dist[route[i], route[i+1]]
        distance += dist[route[-1], route[0]]  # 返回起点
        return distance
    
    # 最近邻启发式生成初始解
    def nearest_neighbor():
        visited = [0]  # 从城市0开始
        unvisited = list(range(1, n_cities))
        
        while unvisited:
            current = visited[-1]
            nearest = min(unvisited, key=lambda x: dist[current, x])
            visited.append(nearest)
            unvisited.remove(nearest)
        
        return np.array(visited)
    
    initial_route = nearest_neighbor()
    initial_distance = total_distance(initial_route)
    print(f"初始路线距离: {initial_distance:.2f}")
    
    # 定义邻域操作：交换两个城市
    def swap_neighbor(route):
        new_route = route.copy()
        i, j = np.random.choice(len(route), 2, replace=False)
        new_route[i], new_route[j] = new_route[j], new_route[i]
        return new_route
    
    # 使用模拟退火优化（简化版）
    current = initial_route.copy()
    current_score = initial_distance
    best = current.copy()
    best_score = current_score
    
    T0 = 1000
    Tmin = 1
    alpha = 0.99
    history = [best_score]
    
    temperature = T0
    while temperature > Tmin:
        for _ in range(100):
            neighbor = swap_neighbor(current)
            neighbor_score = total_distance(neighbor)
            delta = neighbor_score - current_score
            
            if delta < 0 or np.random.random() < math.exp(-delta / temperature):
                current = neighbor
                current_score = neighbor_score
                
                if current_score < best_score:
                    best = current.copy()
                    best_score = current_score
        
        history.append(best_score)
        temperature *= alpha
    
    print(f"优化后路线距离: {best_score:.2f}")
    print(f"改进: {(initial_distance - best_score) / initial_distance * 100:.1f}%")
    
    # 绘制路线
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 初始路线
    ax1.plot(cities[:, 0], cities[:, 1], 'ro', markersize=8)
    route = np.append(initial_route, initial_route[0])
    ax1.plot(cities[route, 0], cities[route, 1], 'b-', alpha=0.6)
    ax1.set_title(f'Initial Route (Distance: {initial_distance:.2f})')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.grid(True, alpha=0.3)
    
    # 优化后路线
    ax2.plot(cities[:, 0], cities[:, 1], 'ro', markersize=8)
    route = np.append(best, best[0])
    ax2.plot(cities[route, 0], cities[route, 1], 'g-', linewidth=2)
    ax2.set_title(f'Optimized Route (Distance: {best_score:.2f})')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figures/sa_tsp.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # 绘制收敛曲线
    plt.figure(figsize=(10, 6))
    plt.plot(history, 'b-', linewidth=2)
    plt.xlabel('Iteration')
    plt.ylabel('Best Distance')
    plt.title('Simulated Annealing for TSP')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('figures/sa_convergence.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_tsp_example()
