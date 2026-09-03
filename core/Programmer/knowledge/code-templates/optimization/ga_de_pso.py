"""
遗传算法(GA)、差分进化(DE)、粒子群(PSO)统一优化模板
来源: 高教杯优秀论文
适用问题: 连续优化、多峰函数、约束优化
输入: 目标函数、约束、变量边界
输出: 最优解、最优值、收敛曲线对比
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class GeneticAlgorithm:
    """遗传算法 (GA)"""

    def __init__(self, objective: Callable, bounds: List[Tuple[float, float]],
                 constraints: Optional[List[Callable]] = None, pop_size: int = 100,
                 max_gen: int = 200, crossover_rate: float = 0.8,
                 mutation_rate: float = 0.1, seed: int = 42):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.constraints = constraints or []
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        np.random.seed(seed)
        self.history = []

    def _init_pop(self) -> np.ndarray:
        pop = np.zeros((self.pop_size, len(self.bounds)))
        for i, (lo, hi) in enumerate(self.bounds):
            pop[:, i] = np.random.uniform(lo, hi, self.pop_size)
        return pop

    def _fitness(self, pop: np.ndarray) -> np.ndarray:
        fit = np.zeros(self.pop_size)
        for i in range(self.pop_size):
            val = self.objective(pop[i])
            penalty = sum(max(0, -c(pop[i])) ** 2 for c in self.constraints)
            fit[i] = val + 1000 * penalty
        return fit

    def _select(self, pop: np.ndarray, fit: np.ndarray) -> np.ndarray:
        selected = np.zeros_like(pop)
        for i in range(self.pop_size):
            idxs = np.random.choice(self.pop_size, 3, replace=False)
            selected[i] = pop[idxs[np.argmin(fit[idxs])]]
        return selected

    def _crossover(self, p1: np.ndarray, p2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if np.random.random() > self.crossover_rate:
            return p1.copy(), p2.copy()
        eta = 20
        c1, c2 = np.zeros_like(p1), np.zeros_like(p2)
        for i in range(len(p1)):
            if np.random.random() < 0.5:
                c1[i], c2[i] = p1[i], p2[i]
            else:
                u = np.random.random()
                beta = (2 * u) ** (1 / (eta + 1)) if u <= 0.5 else (1 / (2 * (1 - u))) ** (1 / (eta + 1))
                c1[i] = 0.5 * ((1 + beta) * p1[i] + (1 - beta) * p2[i])
                c2[i] = 0.5 * ((1 - beta) * p1[i] + (1 + beta) * p2[i])
        for i, (lo, hi) in enumerate(self.bounds):
            c1[i] = np.clip(c1[i], lo, hi)
            c2[i] = np.clip(c2[i], lo, hi)
        return c1, c2

    def _mutate(self, ind: np.ndarray) -> np.ndarray:
        m = ind.copy()
        for i, (lo, hi) in enumerate(self.bounds):
            if np.random.random() < self.mutation_rate:
                m[i] += np.random.normal(0, (hi - lo) * 0.1)
                m[i] = np.clip(m[i], lo, hi)
        return m

    def optimize(self) -> Tuple[np.ndarray, float]:
        pop = self._init_pop()
        fit = self._fitness(pop)
        best_idx = np.argmin(fit)
        best_sol, best_val = pop[best_idx].copy(), fit[best_idx]
        self.history.append(best_val)

        for gen in range(self.max_gen):
            sel = self._select(pop, fit)
            new_pop = np.zeros_like(pop)
            for i in range(0, self.pop_size, 2):
                c1, c2 = self._crossover(sel[i], sel[(i + 1) % self.pop_size])
                new_pop[i] = self._mutate(c1)
                new_pop[(i + 1) % self.pop_size] = self._mutate(c2)
            new_fit = self._fitness(new_pop)
            gen_best = np.argmin(new_fit)
            if new_fit[gen_best] < best_val:
                best_sol, best_val = new_pop[gen_best].copy(), new_fit[gen_best]
            pop = new_pop
            fit = new_fit
            self.history.append(best_val)
        return best_sol, best_val


class DifferentialEvolution:
    """差分进化算法 (DE/rand/1/bin)"""

    def __init__(self, objective: Callable, bounds: List[Tuple[float, float]],
                 constraints: Optional[List[Callable]] = None, pop_size: int = 100,
                 max_gen: int = 200, F: float = 0.8, CR: float = 0.9, seed: int = 42):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.constraints = constraints or []
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.F = F  # 缩放因子
        self.CR = CR  # 交叉概率
        np.random.seed(seed)
        self.history = []

    def _fitness(self, x: np.ndarray) -> float:
        val = self.objective(x)
        penalty = sum(max(0, -c(x)) ** 2 for c in self.constraints)
        return val + 1000 * penalty

    def optimize(self) -> Tuple[np.ndarray, float]:
        dim = len(self.bounds)
        pop = np.zeros((self.pop_size, dim))
        for i, (lo, hi) in enumerate(self.bounds):
            pop[:, i] = np.random.uniform(lo, hi, self.pop_size)
        fitness = np.array([self._fitness(ind) for ind in pop])
        best_idx = np.argmin(fitness)
        best_sol, best_val = pop[best_idx].copy(), fitness[best_idx]
        self.history.append(best_val)

        for gen in range(self.max_gen):
            for i in range(self.pop_size):
                # 变异: DE/rand/1
                idxs = [j for j in range(self.pop_size) if j != i]
                a, b, c = pop[np.random.choice(idxs, 3, replace=False)]
                mutant = a + self.F * (b - c)

                # 交叉
                trial = pop[i].copy()
                j_rand = np.random.randint(dim)
                for j in range(dim):
                    if np.random.random() < self.CR or j == j_rand:
                        trial[j] = mutant[j]

                # 边界处理
                for j, (lo, hi) in enumerate(self.bounds):
                    trial[j] = np.clip(trial[j], lo, hi)

                # 选择
                trial_fit = self._fitness(trial)
                if trial_fit <= fitness[i]:
                    pop[i] = trial
                    fitness[i] = trial_fit

            best_idx = np.argmin(fitness)
            if fitness[best_idx] < best_val:
                best_sol, best_val = pop[best_idx].copy(), fitness[best_idx]
            self.history.append(best_val)
        return best_sol, best_val


class ParticleSwarmOptimization:
    """粒子群优化算法 (PSO)"""

    def __init__(self, objective: Callable, bounds: List[Tuple[float, float]],
                 constraints: Optional[List[Callable]] = None, pop_size: int = 100,
                 max_gen: int = 200, w: float = 0.7, c1: float = 1.5,
                 c2: float = 1.5, seed: int = 42):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.constraints = constraints or []
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.w = w  # 惯性权重
        self.c1 = c1  # 认知系数
        self.c2 = c2  # 社会系数
        np.random.seed(seed)
        self.history = []

    def _fitness(self, x: np.ndarray) -> float:
        val = self.objective(x)
        penalty = sum(max(0, -c(x)) ** 2 for c in self.constraints)
        return val + 1000 * penalty

    def optimize(self) -> Tuple[np.ndarray, float]:
        dim = len(self.bounds)
        pos = np.zeros((self.pop_size, dim))
        vel = np.zeros((self.pop_size, dim))
        for i, (lo, hi) in enumerate(self.bounds):
            pos[:, i] = np.random.uniform(lo, hi, self.pop_size)
            vel[:, i] = np.random.uniform(-(hi - lo) * 0.1, (hi - lo) * 0.1, self.pop_size)

        p_best = pos.copy()
        p_best_fit = np.array([self._fitness(ind) for ind in pos])
        g_best_idx = np.argmin(p_best_fit)
        g_best = p_best[g_best_idx].copy()
        g_best_val = p_best_fit[g_best_idx]
        self.history.append(g_best_val)

        for gen in range(self.max_gen):
            r1 = np.random.random((self.pop_size, dim))
            r2 = np.random.random((self.pop_size, dim))

            # 更新速度和位置
            vel = (self.w * vel +
                   self.c1 * r1 * (p_best - pos) +
                   self.c2 * r2 * (g_best - pos))
            pos = pos + vel

            # 边界处理
            for i, (lo, hi) in enumerate(self.bounds):
                pos[:, i] = np.clip(pos[:, i], lo, hi)

            # 评估
            for i in range(self.pop_size):
                fit = self._fitness(pos[i])
                if fit < p_best_fit[i]:
                    p_best[i] = pos[i].copy()
                    p_best_fit[i] = fit

            gen_best_idx = np.argmin(p_best_fit)
            if p_best_fit[gen_best_idx] < g_best_val:
                g_best = p_best[gen_best_idx].copy()
                g_best_val = p_best_fit[gen_best_idx]
            self.history.append(g_best_val)
        return g_best, g_best_val


def run_example():
    """示例: 优化Rastrigin函数（多峰）"""
    print("=" * 60)
    print("GA / DE / PSO 统一优化框架")
    print("=" * 60)

    # Rastrigin函数 (全局最小值=0, x=0)
    def rastrigin(x):
        A = 10
        return A * len(x) + sum(xi ** 2 - A * np.cos(2 * np.pi * xi) for xi in x)

    bounds = [(-5.12, 5.12)] * 5

    print("\n目标函数: Rastrigin (5维), 全局最优=0")
    print(f"搜索空间: [-5.12, 5.12]^5")

    # GA
    ga = GeneticAlgorithm(rastrigin, bounds, pop_size=100, max_gen=200, seed=42)
    sol_ga, val_ga = ga.optimize()
    print(f"\nGA:  f(x) = {val_ga:.6f}")

    # DE
    de = DifferentialEvolution(rastrigin, bounds, pop_size=100, max_gen=200, seed=42)
    sol_de, val_de = de.optimize()
    print(f"DE:  f(x) = {val_de:.6f}")

    # PSO
    pso = ParticleSwarmOptimization(rastrigin, bounds, pop_size=100, max_gen=200, seed=42)
    sol_pso, val_pso = pso.optimize()
    print(f"PSO: f(x) = {val_pso:.6f}")

    # 收敛曲线对比
    plt.figure(figsize=(10, 6))
    plt.semilogy(ga.history, label='GA', linewidth=2)
    plt.semilogy(de.history, label='DE', linewidth=2)
    plt.semilogy(pso.history, label='PSO', linewidth=2)
    plt.xlabel('Generation / Iteration')
    plt.ylabel('Best Fitness (log scale)')
    plt.title('GA vs DE vs PSO Convergence Comparison')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('figures/ga_de_pso_convergence.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("\n收敛曲线已保存: figures/ga_de_pso_convergence.png")


if __name__ == "__main__":
    run_example()
