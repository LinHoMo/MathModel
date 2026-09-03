# 优化算法方法论

> 本文件提供数学建模竞赛中常用的优化算法知识，包括算法选择、实现要点、防错策略和验证方法。

---

## 1. 算法选择决策树

```
优化问题类型识别：
├── 线性目标 + 线性约束 → 线性规划 (LP)
│   └── scipy.optimize.linprog
├── 含整数/0-1变量 → 整数规划 (MIP)
│   ├── scipy.optimize.milp (SciPy 1.9+)
│   └── pulp / gurobipy / ortools
├── 非线性目标/约束 → 非线性优化
│   ├── 连续可微 → scipy.optimize.minimize (SLSQP/L-BFGS-B)
│   ├── 不可微/多峰 → 启发式算法
│   │   ├── 遗传算法 (GA)
│   │   ├── 差分进化 (DE)
│   │   ├── 粒子群优化 (PSO)
│   │   └── 模拟退火 (SA)
│   └── 约束复杂 → 增广拉格朗日 / 惩罚函数法
├── 多目标冲突 → 多目标优化
│   ├── 加权和法 (先归一化)
│   └── NSGA-II (Pareto前沿)
└── 组合优化 (TSP/VRP/调度) → 元启发式
    ├── 遗传算法
    ├── 蚁群算法
    └── 模拟退火
```

---

## 2. 核心算法详解

### 2.1 遗传算法 (Genetic Algorithm)

**适用场景**：离散优化、组合优化、多峰函数、整数规划

**算法流程**：
```
初始化种群 → 评估适应度 → 选择 → 交叉 → 变异 → 新种群
    ↓
重复直到满足停止条件（最大迭代/适应度收敛）
```

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| 种群大小 | 50-200 | 大→多样性好，计算慢 |
| 交叉概率 | 0.7-0.9 | 高→探索能力强 |
| 变异概率 | 0.01-0.1 | 高→跳出局部最优 |
| 最大代数 | 100-500 | 依问题复杂度 |

**实现要点**：
- 编码方式：实数编码（连续变量）、二进制编码（离散变量）、排列编码（TSP）
- 选择策略：轮盘赌（适应度比例）、锦标赛（更稳定）
- 交叉方式：单点交叉、均匀交叉、模拟二进制交叉（SBX）
- 变异方式：均匀变异、高斯变异

**防错策略**：
- 整数变量：取整后必须重新验证可行性
- 约束处理：软惩罚 > 硬拒绝（避免可行域为空）
- 多次运行：≥5次，报告均值±标准差

**代码框架**：
```python
from scipy.optimize import differential_evolution
import numpy as np

# 定义目标函数（最小化）
def objective(x):
    # x[0], x[1], ... 为决策变量
    return cost_value

# 定义约束（可选）
constraints = [
    {'type': 'ineq', 'fun': lambda x: x[0] - 0},  # x[0] >= 0
    {'type': 'ineq', 'fun': lambda x: 10 - x[0]},  # x[0] <= 10
]

# 定义变量边界
bounds = [(0, 10), (0, 5), (0, 8)]

# 运行优化
result = differential_evolution(
    objective, 
    bounds, 
    seed=42,
    maxiter=1000,
    tol=1e-6
)

# 验证结果
print(f"最优解: {result.x}")
print(f"最优值: {result.fun}")
print(f"收敛状态: {result.success}")
```

---

### 2.2 差分进化 (Differential Evolution)

**适用场景**：连续优化、非线性、多峰、无导数需求

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
from scipy.optimize import differential_evolution

def objective(x):
    return np.sum(x**2)  # 示例：球函数

bounds = [(-5.12, 5.12)] * 10  # 10维问题

result = differential_evolution(
    objective,
    bounds,
    seed=42,
    strategy='best1bin',
    maxiter=1000,
    popsize=15,
    tol=1e-7,
    mutation=(0.5, 1),
    recombination=0.7
)
```

---

### 2.3 粒子群优化 (Particle Swarm Optimization)

**适用场景**：连续优化、多峰、需要快速收敛

**算法特点**：
- 每个粒子记录历史最优位置（pbest）
- 群体记录全局最优位置（gbest）
- 粒子速度更新考虑个体经验和群体经验

**速度更新公式**：
```
v_new = w * v + c1 * r1 * (pbest - x) + c2 * r2 * (gbest - x)
x_new = x + v_new
```

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
        
        # 初始化粒子位置和速度
        self.positions = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1], 
            (n_particles, self.dim)
        )
        self.velocities = np.random.uniform(-1, 1, (n_particles, self.dim))
        
        # 初始化个体最优和全局最优
        self.pbest = self.positions.copy()
        self.pbest_scores = np.array([objective(p) for p in self.positions])
        self.gbest_idx = np.argmin(self.pbest_scores)
        self.gbest = self.pbest[self.gbest_idx].copy()
        self.gbest_score = self.pbest_scores[self.gbest_idx]
    
    def optimize(self):
        w = 0.7  # 惯性权重
        c1, c2 = 2.0, 2.0  # 学习因子
        
        for iter in range(self.max_iter):
            for i in range(self.n_particles):
                # 更新速度
                r1, r2 = np.random.rand(2)
                self.velocities[i] = (
                    w * self.velocities[i] +
                    c1 * r1 * (self.pbest[i] - self.positions[i]) +
                    c2 * r2 * (self.gbest - self.positions[i])
                )
                
                # 更新位置
                self.positions[i] += self.velocities[i]
                
                # 边界处理
                self.positions[i] = np.clip(
                    self.positions[i], 
                    self.bounds[:, 0], 
                    self.bounds[:, 1]
                )
                
                # 评估
                score = self.objective(self.positions[i])
                
                # 更新个体最优
                if score < self.pbest_scores[i]:
                    self.pbest[i] = self.positions[i].copy()
                    self.pbest_scores[i] = score
                    
                    # 更新全局最优
                    if score < self.gbest_score:
                        self.gbest = self.positions[i].copy()
                        self.gbest_score = score
        
        return self.gbest, self.gbest_score
```

---

### 2.4 模拟退火 (Simulated Annealing)

**适用场景**：组合优化、TSP、调度问题、避免局部最优

**算法特点**：
- 模拟金属退火过程
- 以一定概率接受劣解（温度高时接受概率大）
- 温度逐渐降低，接受概率减小

**接受概率公式**：
```
P(accept) = exp(-ΔE / T)
```
- ΔE > 0（劣解）：接受概率随温度降低而减小
- ΔE < 0（优解）：总是接受

**温度调度**：
- 初始温度T0：足够高，使接受率约80%
- 降温系数α：0.95-0.99
- 停止温度Tmin：接近0

**代码框架**：
```python
import numpy as np
import math

def simulated_annealing(objective, initial_solution, bounds, 
                       T0=1000, Tmin=1e-3, alpha=0.95, max_iter=1000):
    """
    模拟退火算法
    """
    # 初始化
    current = initial_solution.copy()
    current_score = objective(current)
    best = current.copy()
    best_score = current_score
    T = T0
    
    for iteration in range(max_iter):
        # 生成邻域解（随机扰动）
        neighbor = current.copy()
        idx = np.random.randint(len(bounds))
        neighbor[idx] += np.random.normal(0, (bounds[idx][1] - bounds[idx][0]) * 0.1)
        neighbor[idx] = np.clip(neighbor[idx], bounds[idx][0], bounds[idx][1])
        
        # 计算能量差
        neighbor_score = objective(neighbor)
        delta = neighbor_score - current_score
        
        # 接受准则
        if delta < 0 or np.random.rand() < math.exp(-delta / T):
            current = neighbor
            current_score = neighbor_score
            
            # 更新全局最优
            if current_score < best_score:
                best = current.copy()
                best_score = current_score
        
        # 降温
        T *= alpha
        if T < Tmin:
            break
    
    return best, best_score
```

---

## 3. 约束处理方法

### 3.1 约束类型

| 类型 | 示例 | 处理方法 |
|------|------|---------|
| 等式约束 | g(x) = 0 | 惩罚函数 |
| 不等式约束 | h(x) ≥ 0 | 罚项/投影 |
| 变量边界 | a ≤ x ≤ b | bounds参数 |
| 整数约束 | x ∈ Z | 取整+验证 |
| 0-1约束 | x ∈ {0,1} | 二进制编码 |

### 3.2 惩罚函数法

**硬惩罚**（直接拒绝不可行解）：
```python
def objective_with_penalty(x):
    if not is_feasible(x):
        return 1e10  # 大数惩罚
    return original_objective(x)
```

**软惩罚**（渐进惩罚）：
```python
def objective_with_soft_penalty(x, lambda_val=1000):
    penalty = 0
    for constraint in constraints:
        violation = max(0, -constraint(x))  # 违反量
        penalty += violation ** 2
    return original_objective(x) + lambda_val * penalty
```

**自适应惩罚**：
```python
lambda_val = lambda_val * 1.1  # 每次迭代增大惩罚系数
```

### 3.3 投影法

将不可行解投影到可行域边界：
```python
def project_to_feasible(x, bounds):
    return np.clip(x, bounds[:, 0], bounds[:, 1])
```

---

## 4. 多目标优化

### 4.1 加权和法

```python
def multi_objective_weighted(x, weights, objectives):
    """
    weights: 各目标权重，和为1
    objectives: 各目标函数列表
    """
    total = 0
    for w, obj in zip(weights, objectives):
        total += w * obj(x)
    return total
```

**关键步骤**：
1. 各目标独立归一化（0-1范围）
2. 确定权重（专家法/熵权法/层次分析法）
3. 加权求和

### 4.2 Pareto前沿

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

algorithm = NSGA2(pop_size=100)
res = minimize(problem, algorithm, termination=('n_gen', 200), seed=42)
# res.F: Pareto前沿的目标值
# res.X: Pareto前沿的决策变量
```

---

## 5. 灵敏度分析

### 5.1 单参数扰动

```python
def sensitivity_analysis(base_solution, param_idx, perturbation_range=np.arange(-0.2, 0.21, 0.05)):
    """
    对单个参数进行扰动，观察目标函数变化
    """
    base_value = base_solution[param_idx]
    results = []
    
    for p in perturbation_range:
        perturbed = base_solution.copy()
        perturbed[param_idx] = base_value * (1 + p)
        obj_value = objective(perturbed)
        results.append((p, obj_value))
    
    return results
```

### 5.2 Tornado图

```python
import matplotlib.pyplot as plt

def tornado_plot(param_names, low_values, high_values, base_value):
    """
    绘制Tornado图展示参数影响力排序
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(param_names))
    
    ax.barh(y_pos, [h - base_value for h in high_values], height=0.4, 
            label='High (+20%)', color='red', alpha=0.6)
    ax.barh([y + 0.4 for y in y_pos], [l - base_value for l in low_values], 
            height=0.4, label='Low (-20%)', color='blue', alpha=0.6)
    
    ax.set_yticks([y + 0.2 for y in y_pos])
    ax.set_yticklabels(param_names)
    ax.axvline(x=0, color='black', linestyle='--')
    ax.set_xlabel('Change in Objective')
    ax.legend()
    plt.tight_layout()
    return fig
```

---

## 6. 防错速查表

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 局部最优 | 多次运行结果差异大 | 多起点运行≥5次，报告标准差 |
| 边界越界 | 优化变量超出物理范围 | bounds严格设置，clip处理 |
| 约束违反 | 最优解不满足约束 | 重新代入所有约束检查 |
| 整数取整 | 连续解取整后不可行 | 取整后重新验证可行性 |
| 目标函数不连续 | 优化器收敛困难 | 改用连续代理目标 |
| 维度灾难 | 高维问题收敛慢 | 降维/分阶段优化 |
| 多目标冲突 | 单目标优化丢失信息 | 加权和/Pareto分析 |

---

## 7. 参考论文（来自高教杯优秀论文）

| 论文编号 | 优化方法 | 应用场景 | 关键创新 |
|---------|---------|---------|---------|
| A001 | 遗传算法 | 波浪能装置参数优化 | 多目标加权+灵敏度分析 |
| A028 | 差分进化 | FAST反射面形状优化 | 约束处理+退化校验 |
| A070 | 遗传算法 | 炉温曲线优化 | 多阶段优化+边界约束 |
| A092 | 粒子群 | 定日镜场优化 | 多目标+Pareto分析 |
| B195 | 模拟退火 | 生产决策优化 | 多阶段+蒙特卡洛 |
| B196 | 蚁群+遗传 | 生产决策优化 | 混合算法+鲁棒性验证 |

---

## 8. 验证清单

- [ ] 优化器收敛状态为True
- [ ] 多次运行结果稳定（标准差/均值 < 10%）
- [ ] 最优解重新代入所有约束检查通过
- [ ] 整数变量已取整并重新验证可行性
- [ ] 灵敏度分析已执行（关键参数±20%）
- [ ] 与基准解（网格扫描/退化情形）对比
- [ ] 结果数量级与物理直觉一致
