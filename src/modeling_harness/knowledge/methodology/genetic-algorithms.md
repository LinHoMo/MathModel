# 遗传算法与进化计算方法论

> 本文件提供数学建模竞赛中常用的遗传算法与进化计算知识，包括算法选择、实现要点、防错策略和验证方法。

---

## 1. 算法选择决策树

```
进化计算问题类型识别：
├── 连续参数优化
│   ├── 低维(d<10) → 差分进化(DE)
│   ├── 高维(d≥10) → 粒子群(PSO)
│   └── 多峰/噪声 → 遗传算法(GA)
├── 组合优化(TSP/调度/选址)
│   ├── 排列问题 → 遗传算法(排列编码)
│   ├── 集合问题 → 0-1遗传算法
│   └── 大规模 → 蚁群算法(ACO)
├── 多目标优化
│   ├── 2-3个目标 → NSGA-II
│   └── 更多目标 → MOEA/D
└── 混合整数规划
    ├── 小规模 → 枚举+GA
    └── 大规模 → DE+约束处理
```

---

## 2. 核心方法详解

### 2.1 遗传算法 (Genetic Algorithm)

**方法原理**：
模拟自然选择过程，通过选择、交叉、变异操作进化种群，使适应度逐代提升。

**适用场景**：
- 离散优化、组合优化（TSP、调度、选址）
- 多峰函数全局优化
- 整数规划、0-1规划
- 需要可并行化的大规模问题

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| 种群大小 | 50-200 | 大→多样性好，计算慢 |
| 交叉概率 | 0.7-0.9 | 高→探索能力强 |
| 变异概率 | 0.01-0.1 | 高→跳出局部最优 |
| 最大代数 | 100-500 | 依问题复杂度 |

**代码框架**：
```python
import numpy as np
from typing import Callable, List, Tuple

class GeneticAlgorithm:
    def __init__(self, objective: Callable, bounds: List[Tuple], 
                 pop_size: int = 100, max_gen: int = 200,
                 crossover_rate: float = 0.8, mutation_rate: float = 0.1):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.dim = len(bounds)
        
    def init_population(self):
        low = self.bounds[:, 0]
        high = self.bounds[:, 1]
        return np.random.uniform(low, high, (self.pop_size, self.dim))
    
    def evaluate(self, pop):
        return np.array([self.objective(ind) for ind in pop])
    
    def selection(self, pop, fitness, tournament_size=3):
        selected = []
        for _ in range(self.pop_size):
            contestants = np.random.choice(self.pop_size, tournament_size, replace=False)
            winner = contestants[np.argmin(fitness[contestants])]
            selected.append(pop[winner].copy())
        return np.array(selected)
    
    def crossover(self, parent1, parent2):
        if np.random.rand() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        alpha = np.random.rand(self.dim)
        child1 = alpha * parent1 + (1 - alpha) * parent2
        child2 = (1 - alpha) * parent1 + alpha * parent2
        return child1, child2
    
    def mutate(self, individual):
        for i in range(self.dim):
            if np.random.rand() < self.mutation_rate:
                low, high = self.bounds[i]
                individual[i] += np.random.normal(0, (high - low) * 0.1)
                individual[i] = np.clip(individual[i], low, high)
        return individual
    
    def optimize(self):
        pop = self.init_population()
        best_idx = np.argmin(self.evaluate(pop))
        best = pop[best_idx].copy()
        best_fitness = self.objective(best)
        
        for gen in range(self.max_gen):
            fitness = self.evaluate(pop)
            
            # 更新全局最优
            gen_best_idx = np.argmin(fitness)
            if fitness[gen_best_idx] < best_fitness:
                best = pop[gen_best_idx].copy()
                best_fitness = fitness[gen_best_idx]
            
            # 选择
            selected = self.selection(pop, fitness)
            
            # 交叉和变异
            new_pop = []
            for i in range(0, self.pop_size, 2):
                p1, p2 = selected[i], selected[min(i+1, self.pop_size-1)]
                c1, c2 = self.crossover(p1, p2)
                c1 = self.mutate(c1)
                c2 = self.mutate(c2)
                new_pop.extend([c1, c2])
            pop = np.array(new_pop[:self.pop_size])
        
        return best, best_fitness

# 使用示例
def sphere(x):
    return np.sum(x**2)

bounds = [(-5.12, 5.12)] * 10
ga = GeneticAlgorithm(sphere, bounds, pop_size=100, max_gen=200)
best, best_fit = ga.optimize()
print(f"最优解: {best}")
print(f"最优值: {best_fit}")
```

---

### 2.2 差分进化 (Differential Evolution)

**方法原理**：
使用差分向量产生变异向量，通过交叉和选择操作进化种群。特别适合连续优化问题。

**适用场景**：
- 连续参数优化
- 非线性、多峰函数
- 无导数需求的黑箱优化

**与遗传算法的区别**：
- DE使用实数编码，更适合连续优化
- DE的变异策略更强大（差分向量）
- DE通常更稳定，参数更少

**关键参数**：
| 参数 | 典型范围 | 说明 |
|------|---------|------|
| 种群大小 | 10*d (d=维度) | 维度越高需要越大 |
| 缩放因子F | 0.5-1.0 | 控制差分步长 |
| 交叉概率CR | 0.7-0.9 | 控制交叉程度 |

**代码框架**：
```python
import numpy as np
from scipy.optimize import differential_evolution

def objective(x):
    return np.sum(x**2)

bounds = [(-5.12, 5.12)] * 10

result = differential_evolution(
    objective, bounds, seed=42,
    strategy='best1bin', maxiter=1000,
    popsize=15, tol=1e-7,
    mutation=(0.5, 1), recombination=0.7
)

print(f"最优解: {result.x}")
print(f"最优值: {result.fun}")
print(f"收敛: {result.success}")
```

---

### 2.3 粒子群优化 (Particle Swarm Optimization)

**方法原理**：
模拟鸟群觅食行为，每个粒子记录历史最优位置(pbest)和群体全局最优位置(gbest)，通过速度更新公式迭代搜索。

**速度更新公式**：
```
v_new = w * v + c1 * r1 * (pbest - x) + c2 * r2 * (gbest - x)
x_new = x + v_new
```

**适用场景**：
- 连续参数优化
- 多峰函数快速收敛
- 需要简单实现的场景

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| 惯性权重w | 0.4-0.9 | 大→全局探索，小→局部开发 |
| 学习因子c1 | 1.5-2.0 | 个体学习能力 |
| 学习因子c2 | 1.5-2.0 | 社会学习能力 |
| 粒子数 | 30-100 | 依问题复杂度 |

**代码框架**：
```python
import numpy as np

class PSO:
    def __init__(self, objective, bounds, n_particles=30, max_iter=100):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.n_particles = n_particles
        self.max_iter = max_iter
        self.dim = len(bounds)
        
        self.positions = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1],
            (n_particles, self.dim)
        )
        self.velocities = np.random.uniform(-1, 1, (n_particles, self.dim))
        
        self.pbest = self.positions.copy()
        self.pbest_scores = np.array([objective(p) for p in self.positions])
        self.gbest_idx = np.argmin(self.pbest_scores)
        self.gbest = self.pbest[self.gbest_idx].copy()
        self.gbest_score = self.pbest_scores[self.gbest_idx]
    
    def optimize(self):
        w, c1, c2 = 0.7, 2.0, 2.0
        
        for _ in range(self.max_iter):
            for i in range(self.n_particles):
                r1, r2 = np.random.rand(2)
                self.velocities[i] = (
                    w * self.velocities[i] +
                    c1 * r1 * (self.pbest[i] - self.positions[i]) +
                    c2 * r2 * (self.gbest - self.positions[i])
                )
                self.positions[i] += self.velocities[i]
                self.positions[i] = np.clip(
                    self.positions[i], self.bounds[:, 0], self.bounds[:, 1]
                )
                
                score = self.objective(self.positions[i])
                if score < self.pbest_scores[i]:
                    self.pbest[i] = self.positions[i].copy()
                    self.pbest_scores[i] = score
                    if score < self.gbest_score:
                        self.gbest = self.positions[i].copy()
                        self.gbest_score = score
        
        return self.gbest, self.gbest_score
```

---

### 2.4 蚁群算法 (Ant Colony Optimization)

**方法原理**：
模拟蚂蚁觅食行为，通过信息素更新和概率转移选择路径，逐步收敛到最优解。特别适合组合优化问题。

**适用场景**：
- TSP旅行商问题
- 路径规划
- 调度问题
- 网络路由

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| 蚂蚁数量 | 20-50 | 多→搜索广，计算慢 |
| 信息素α | 1-3 | 大→偏向已知路径 |
| 启发式β | 2-5 | 大→偏向局部最优 |
| 信息素挥发ρ | 0.1-0.5 | 大→遗忘快，探索强 |

**代码框架**：
```python
import numpy as np

class ACO:
    def __init__(self, dist_matrix, n_ants=20, n_iter=100,
                 alpha=1.0, beta=2.0, rho=0.1, Q=1.0):
        self.dist = dist_matrix
        self.n_cities = len(dist_matrix)
        self.n_ants = n_ants
        self.n_iter = n_iter
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q
        self.pheromone = np.ones((self.n_cities, self.n_cities)) * 0.1
    
    def _probability(self, current, unvisited):
        prob = np.zeros(self.n_cities)
        for j in unvisited:
            tau = self.pheromone[current, j] ** self.alpha
            eta = (1.0 / (self.dist[current, j] + 1e-10)) ** self.beta
            prob[j] = tau * eta
        prob_sum = prob[unvisited].sum()
        if prob_sum > 0:
            prob[unvisited] /= prob_sum
        return prob
    
    def _construct_solution(self):
        tour = [np.random.randint(self.n_cities)]
        unvisited = set(range(self.n_cities)) - {tour[0]}
        
        while unvisited:
            current = tour[-1]
            prob = self._probability(current, list(unvisited))
            next_city = np.random.choice(self.n_cities, p=prob)
            tour.append(next_city)
            unvisited.remove(next_city)
        
        return tour
    
    def _tour_length(self, tour):
        length = 0
        for i in range(len(tour)):
            length += self.dist[tour[i], tour[(i+1) % len(tour)]]
        return length
    
    def optimize(self):
        best_tour = None
        best_length = float('inf')
        
        for _ in range(self.n_iter):
            all_tours = []
            all_lengths = []
            
            for _ in range(self.n_ants):
                tour = self._construct_solution()
                length = self._tour_length(tour)
                all_tours.append(tour)
                all_lengths.append(length)
                
                if length < best_length:
                    best_tour = tour.copy()
                    best_length = length
            
            # 更新信息素
            self.pheromone *= (1 - self.rho)
            for tour, length in zip(all_tours, all_lengths):
                for i in range(len(tour)):
                    i_next = tour[(i+1) % len(tour)]
                    self.pheromone[tour[i], i_next] += self.Q / length
        
        return best_tour, best_length
```

---

## 3. 约束处理方法

### 3.1 惩罚函数法

```python
def penalized_objective(x, original_obj, constraints, lambda_val=1000):
    penalty = 0
    for constraint in constraints:
        violation = max(0, -constraint(x))
        penalty += violation ** 2
    return original_obj(x) + lambda_val * penalty
```

### 3.2 可行解优先选择

```python
def tournament_selection(pop, fitness, feasible_mask):
    # 优先选择可行解
    contestants = np.random.choice(len(pop), 3, replace=False)
    feasible_contestants = contestants[feasible_mask[contestants]]
    if len(feasible_contestants) > 0:
        return pop[feasible_contestants[np.argmin(fitness[feasible_contestants])]]
    return pop[contestants[np.argmin(fitness[contestants])]]
```

---

## 4. 常见陷阱与最佳实践

### 4.1 常见陷阱

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 过早收敛 | 种群多样性丧失，陷入局部最优 | 增大种群/变异率，使用 niching |
| 参数选择不当 | 收敛慢或震荡 | 参考典型范围，网格搜索 |
| 约束处理不当 | 最优解不可行 | 惩罚函数+取整验证 |
| 编码设计不合理 | 搜索效率低 | 选择合适的编码方式 |
| 终止条件过早 | 未收敛就停止 | 监控适应度变化，设置容差 |
| 多次运行差异大 | 结果不稳定 | 报告均值±标准差 |

### 4.2 最佳实践

- **种群大小**：通常为决策变量数的10-20倍
- **交叉率**：0.7-0.9，保证充分探索
- **变异率**：0.01-0.1，平衡探索与开发
- **多次运行**：至少运行5次，报告统计结果
- **约束处理**：优先使用软惩罚而非硬拒绝

---

## 5. 验证清单

- [ ] 种群多样性监控（适应度标准差不为0）
- [ ] 适应度曲线收敛（不再显著下降）
- [ ] 多次运行结果稳定（标准差/均值 < 10%）
- [ ] 最优解重新代入所有约束检查通过
- [ ] 整数变量已取整并重新验证可行性
- [ ] 与基准解（网格扫描/退化情形）对比
- [ ] 参数敏感性分析（交叉率/变异率±20%）
- [ ] 结果数量级与物理直觉一致
