"""
遗传算法模板
来源: 高教杯优秀论文 (A001, A028, A070)
适用问题: 连续优化、离散优化、多峰函数、整数规划
输入: 目标函数、约束、变量边界
输出: 最优解、最优值、收敛历史
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class GeneticAlgorithm:
    """
    遗传算法实现
    
    Parameters
    ----------
    objective : callable
        目标函数（最小化）
    bounds : list of tuples
        变量边界 [(low, high), ...]
    constraints : list of callable, optional
        约束函数列表，每个函数返回 ≥0 表示可行
    pop_size : int, default=100
        种群大小
    max_generations : int, default=200
        最大代数
    crossover_rate : float, default=0.8
        交叉概率
    mutation_rate : float, default=0.1
        变异概率
    tournament_size : int, default=3
        锦标赛选择大小
    elitism : bool, default=True
        是否保留精英
    seed : int, default=42
        随机种子
    """
    
    def __init__(
        self,
        objective: Callable,
        bounds: List[Tuple[float, float]],
        constraints: Optional[List[Callable]] = None,
        pop_size: int = 100,
        max_generations: int = 200,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.1,
        tournament_size: int = 3,
        elitism: bool = True,
        seed: int = 42
    ):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.constraints = constraints or []
        self.pop_size = pop_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elitism = elitism
        self.seed = seed
        
        np.random.seed(seed)
        
        self.best_solution = None
        self.best_fitness = np.inf
        self.history = []
    
    def _initialize_population(self) -> np.ndarray:
        """初始化种群"""
        pop = np.zeros((self.pop_size, len(self.bounds)))
        for i in range(len(self.bounds)):
            low, high = self.bounds[i]
            pop[:, i] = np.random.uniform(low, high, self.pop_size)
        return pop
    
    def _evaluate_fitness(self, population: np.ndarray) -> np.ndarray:
        """评估适应度（含约束惩罚）"""
        fitness = np.zeros(self.pop_size)
        for i in range(self.pop_size):
            x = population[i]
            # 计算目标函数值
            obj_val = self.objective(x)
            # 计算约束惩罚
            penalty = 0
            for constraint in self.constraints:
                violation = max(0, -constraint(x))
                penalty += violation ** 2
            fitness[i] = obj_val + 1000 * penalty  # 软惩罚
        return fitness
    
    def _tournament_selection(self, population: np.ndarray, fitness: np.ndarray) -> np.ndarray:
        """锦标赛选择"""
        selected = np.zeros((self.pop_size, len(self.bounds)))
        for i in range(self.pop_size):
            # 随机选择tournament_size个个体
            candidates = np.random.choice(self.pop_size, self.tournament_size, replace=False)
            # 选择适应度最好的
            best_idx = candidates[np.argmin(fitness[candidates])]
            selected[i] = population[best_idx]
        return selected
    
    def _crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """模拟二进制交叉 (SBX)"""
        if np.random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        eta = 20  # 分布指数
        child1 = np.zeros_like(parent1)
        child2 = np.zeros_like(parent2)
        
        for i in range(len(parent1)):
            if np.random.random() < 0.5:
                child1[i] = parent1[i]
                child2[i] = parent2[i]
            else:
                u = np.random.random()
                if u <= 0.5:
                    beta = (2 * u) ** (1 / (eta + 1))
                else:
                    beta = (1 / (2 * (1 - u))) ** (1 / (eta + 1))
                
                child1[i] = 0.5 * ((1 + beta) * parent1[i] + (1 - beta) * parent2[i])
                child2[i] = 0.5 * ((1 - beta) * parent1[i] + (1 + beta) * parent2[i])
        
        # 边界处理
        for i in range(len(self.bounds)):
            low, high = self.bounds[i]
            child1[i] = np.clip(child1[i], low, high)
            child2[i] = np.clip(child2[i], low, high)
        
        return child1, child2
    
    def _mutate(self, individual: np.ndarray) -> np.ndarray:
        """高斯变异"""
        mutant = individual.copy()
        for i in range(len(self.bounds)):
            if np.random.random() < self.mutation_rate:
                low, high = self.bounds[i]
                sigma = (high - low) * 0.1  # 标准差为范围的10%
                mutant[i] += np.random.normal(0, sigma)
                mutant[i] = np.clip(mutant[i], low, high)
        return mutant
    
    def optimize(self) -> Tuple[np.ndarray, float]:
        """
        运行遗传算法
        
        Returns
        -------
        best_solution : ndarray
            最优解
        best_fitness : float
            最优值
        """
        # 初始化种群
        population = self._initialize_population()
        fitness = self._evaluate_fitness(population)
        
        # 记录初始最优
        best_idx = np.argmin(fitness)
        self.best_solution = population[best_idx].copy()
        self.best_fitness = fitness[best_idx]
        self.history.append(self.best_fitness)
        
        # 迭代
        for gen in range(self.max_generations):
            # 选择
            selected = self._tournament_selection(population, fitness)
            
            # 交叉和变异
            new_population = np.zeros_like(population)
            for i in range(0, self.pop_size, 2):
                parent1 = selected[i]
                parent2 = selected[i + 1] if i + 1 < self.pop_size else selected[0]
                
                child1, child2 = self._crossover(parent1, parent2)
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)
                
                new_population[i] = child1
                if i + 1 < self.pop_size:
                    new_population[i + 1] = child2
            
            # 精英保留
            if self.elitism:
                worst_idx = np.argmax(fitness)
                new_population[worst_idx] = self.best_solution.copy()
            
            # 评估新种群
            population = new_population
            fitness = self._evaluate_fitness(population)
            
            # 更新最优
            gen_best_idx = np.argmin(fitness)
            if fitness[gen_best_idx] < self.best_fitness:
                self.best_solution = population[gen_best_idx].copy()
                self.best_fitness = fitness[gen_best_idx]
            
            self.history.append(self.best_fitness)
            
            # 打印进度
            if (gen + 1) % 50 == 0:
                print(f"Generation {gen + 1}/{self.max_generations}, Best Fitness: {self.best_fitness:.6f}")
        
        return self.best_solution, self.best_fitness
    
    def plot_convergence(self):
        """绘制收敛曲线"""
        plt.figure(figsize=(10, 6))
        plt.plot(self.history, 'b-', linewidth=2)
        plt.xlabel('Generation')
        plt.ylabel('Best Fitness')
        plt.title('Genetic Algorithm Convergence')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return plt.gcf()


def run_example():
    """
    示例：优化 Rosenbrock 函数
    f(x) = (a - x₁)² + b(x₂ - x₁²)²
    最优解: x = (a, a²), f(x) = 0
    """
    # 定义目标函数
    def rosenbrock(x, a=1, b=100):
        return (a - x[0])**2 + b * (x[1] - x[0]**2)**2
    
    # 定义边界
    bounds = [(-5, 5), (-5, 5)]
    
    # 创建并运行GA
    ga = GeneticAlgorithm(
        objective=rosenbrock,
        bounds=bounds,
        pop_size=100,
        max_generations=200,
        seed=42
    )
    
    best_solution, best_fitness = ga.optimize()
    
    print(f"\n最优解: {best_solution}")
    print(f"最优值: {best_fitness:.6f}")
    print(f"理论最优: [1, 1], f(x) = 0")
    
    # 绘制收敛曲线
    ga.plot_convergence()
    plt.savefig('figures/ga_convergence.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
