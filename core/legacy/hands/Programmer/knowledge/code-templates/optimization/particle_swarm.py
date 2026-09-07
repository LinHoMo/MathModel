"""
粒子群优化模板
来源: 高教杯优秀论文 (A092, A165)
适用问题: 连续优化、多峰函数、快速收敛
输入: 目标函数、变量边界
输出: 最优解、最优值、收敛历史
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class ParticleSwarmOptimization:
    """
    粒子群优化算法
    
    Parameters
    ----------
    objective : callable
        目标函数（最小化）
    bounds : list of tuples
        变量边界 [(low, high), ...]
    n_particles : int, default=30
        粒子数
    max_iterations : int, default=100
        最大迭代次数
    w : float, default=0.7
        惯性权重
    c1 : float, default=2.0
        个体学习因子
    c2 : float, default=2.0
        社会学习因子
    seed : int, default=42
        随机种子
    """
    
    def __init__(
        self,
        objective: Callable,
        bounds: List[Tuple[float, float]],
        n_particles: int = 30,
        max_iterations: int = 100,
        w: float = 0.7,
        c1: float = 2.0,
        c2: float = 2.0,
        seed: int = 42
    ):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.n_particles = n_particles
        self.max_iterations = max_iterations
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.seed = seed
        
        np.random.seed(seed)
        
        self.dim = len(bounds)
        self.positions = None
        self.velocities = None
        self.pbest = None
        self.pbest_scores = None
        self.gbest = None
        self.gbest_score = np.inf
        self.history = []
    
    def _initialize(self):
        """初始化粒子位置和速度"""
        # 位置：在边界内随机初始化
        self.positions = np.zeros((self.n_particles, self.dim))
        for i in range(self.dim):
            low, high = self.bounds[i]
            self.positions[:, i] = np.random.uniform(low, high, self.n_particles)
        
        # 速度：在位置范围的10%内随机初始化
        self.velocities = np.zeros((self.n_particles, self.dim))
        for i in range(self.dim):
            low, high = self.bounds[i]
            range_val = high - low
            self.velocities[:, i] = np.random.uniform(-range_val * 0.1, range_val * 0.1, self.n_particles)
        
        # 初始化个体最优
        self.pbest = self.positions.copy()
        self.pbest_scores = np.array([self.objective(p) for p in self.positions])
        
        # 初始化全局最优
        best_idx = np.argmin(self.pbest_scores)
        self.gbest = self.pbest[best_idx].copy()
        self.gbest_score = self.pbest_scores[best_idx]
    
    def _update_velocity(self, i: int):
        """更新粒子速度"""
        r1, r2 = np.random.rand(2)
        
        # 速度更新公式
        self.velocities[i] = (
            self.w * self.velocities[i] +
            self.c1 * r1 * (self.pbest[i] - self.positions[i]) +
            self.c2 * r2 * (self.gbest - self.positions[i])
        )
        
        # 速度限制（防止速度过大）
        for d in range(self.dim):
            max_vel = (self.bounds[d][1] - self.bounds[d][0]) * 0.2
            self.velocities[i, d] = np.clip(self.velocities[i, d], -max_vel, max_vel)
    
    def _update_position(self, i: int):
        """更新粒子位置"""
        self.positions[i] += self.velocities[i]
        
        # 边界处理
        for d in range(self.dim):
            low, high = self.bounds[d]
            if self.positions[i, d] < low:
                self.positions[i, d] = low
                self.velocities[i, d] *= -0.5  # 反弹
            elif self.positions[i, d] > high:
                self.positions[i, d] = high
                self.velocities[i, d] *= -0.5  # 反弹
    
    def _evaluate(self, i: int):
        """评估粒子"""
        score = self.objective(self.positions[i])
        
        # 更新个体最优
        if score < self.pbest_scores[i]:
            self.pbest[i] = self.positions[i].copy()
            self.pbest_scores[i] = score
            
            # 更新全局最优
            if score < self.gbest_score:
                self.gbest = self.positions[i].copy()
                self.gbest_score = score
    
    def optimize(self) -> Tuple[np.ndarray, float]:
        """
        运行粒子群优化
        
        Returns
        -------
        best_solution : ndarray
            最优解
        best_fitness : float
            最优值
        """
        self._initialize()
        self.history.append(self.gbest_score)
        
        for iteration in range(self.max_iterations):
            for i in range(self.n_particles):
                self._update_velocity(i)
                self._update_position(i)
                self._evaluate(i)
            
            self.history.append(self.gbest_score)
            
            # 打印进度
            if (iteration + 1) % 20 == 0:
                print(f"Iteration {iteration + 1}/{self.max_iterations}, Best Fitness: {self.gbest_score:.6f}")
        
        return self.gbest, self.gbest_score
    
    def plot_convergence(self):
        """绘制收敛曲线"""
        plt.figure(figsize=(10, 6))
        plt.plot(self.history, 'b-', linewidth=2)
        plt.xlabel('Iteration')
        plt.ylabel('Best Fitness')
        plt.title('Particle Swarm Optimization Convergence')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return plt.gcf()
    
    def plot_particles(self, iteration: int = 0):
        """绘制粒子分布（仅适用于2D问题）"""
        if self.dim != 2:
            print("只能绘制2D问题的粒子分布")
            return
        
        plt.figure(figsize=(10, 8))
        plt.scatter(self.positions[:, 0], self.positions[:, 1], c='blue', alpha=0.6, label='Particles')
        plt.scatter(self.gbest[0], self.gbest[1], c='red', s=200, marker='*', label='Global Best')
        plt.xlabel('x₁')
        plt.ylabel('x₂')
        plt.title(f'Particle Distribution (Iteration {iteration})')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return plt.gcf()


def run_example():
    """
    示例：优化 Sphere 函数
    f(x) = Σxᵢ²
    最优解: x = (0, 0, ..., 0), f(x) = 0
    """
    # 定义目标函数
    def sphere(x):
        return np.sum(x**2)
    
    # 定义边界
    bounds = [(-5.12, 5.12)] * 10  # 10维问题
    
    # 创建并运行PSO
    pso = ParticleSwarmOptimization(
        objective=sphere,
        bounds=bounds,
        n_particles=50,
        max_iterations=100,
        seed=42
    )
    
    best_solution, best_fitness = pso.optimize()
    
    print(f"\n最优解: {best_solution}")
    print(f"最优值: {best_fitness:.6f}")
    print(f"理论最优: 全0向量, f(x) = 0")
    
    # 绘制收敛曲线
    pso.plot_convergence()
    plt.savefig('figures/pso_convergence.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
