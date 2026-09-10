# 整数规划与0-1规划方法论

> 本文件提供数学建模竞赛中常用的整数规划与0-1规划知识，包括模型建立、求解方法、防错策略和验证方法。

---

## 1. 问题类型识别

```
整数规划问题类型：
├── 纯整数规划 (All-Integer)
│   ├── 小规模(n≤50) → 分支定界
│   └── 大规模(n>50) → 启发式
├── 混合整数规划 (MIP)
│   ├── 线性目标+线性约束 → MIP求解器
│   └── 非线性目标 → MINLP求解器
├── 0-1整数规划
│   ├── 指派问题 → 匈牙利算法
│   ├── 背包问题 → 动态规划/GA
│   └── 选址问题 → 建模为0-1MIP
└── 二次整数规划 (MIQP)
    └── 二次目标+整数约束 → 求解器
```

---

## 2. 核心方法详解

### 2.1 整数线性规划 (ILP)

**模型形式**：
```
min  c^T x
s.t. A_ub x ≤ b_ub
     A_eq x = b_eq
     lb ≤ x ≤ ub
     x ∈ Z^n (整数约束)
```

**求解方法**：
- 分支定界法 (Branch and Bound)
- 割平面法 (Cutting Plane)
- 分支切割法 (Branch and Cut)

**代码框架**：
```python
from scipy.optimize import milp, LinearConstraint, Bounds
import numpy as np

def solve_ilp(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None,
              bounds=None, integrality=None):
    """
    求解混合整数线性规划
    c: 目标函数系数
    A_ub, b_ub: 不等式约束
    A_eq, b_eq: 等式约束
    bounds: 变量边界
    integrality: 整数约束 (1=整数, 0=连续)
    """
    constraints = []
    if A_ub is not None and b_ub is not None:
        constraints.append(LinearConstraint(A_ub, -np.inf, b_ub))
    if A_eq is not None and b_eq is not None:
        constraints.append(LinearConstraint(A_eq, b_eq, b_eq))
    
    if bounds is None:
        bounds = Bounds(lb=0, ub=np.inf)
    
    if integrality is None:
        integrality = np.ones(len(c))
    
    result = milp(c, constraints=constraints, bounds=bounds,
                  integrality=integrality)
    return result

# 示例：生产计划问题
c = [-40, -30]  # 目标：最大化利润 → 最小化负利润
A_ub = [[7, 3], [10, 5]]  # 资源约束
b_ub = [40, 60]
bounds = Bounds(lb=[0, 0], ub=[np.inf, np.inf])
integrality = [1, 1]  # 整数决策

result = solve_ilp(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds,
                   integrality=integrality)
print(f"最优解: {result.x}")
print(f"最优值: {-result.fun}")  # 转回最大化
```

---

### 2.2 0-1整数规划

**模型形式**：
```
min  c^T x
s.t. A_ub x ≤ b_ub
     A_eq x = b_eq
     x_i ∈ {0, 1}
```

**典型应用**：
- 指派问题
- 背包问题
- 选址问题
- 固定费用问题

**代码框架**：
```python
from scipy.optimize import milp, LinearConstraint, Bounds
import numpy as np

def solve_01_programming(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None,
                         bounds=None):
    """
    求解0-1整数规划
    """
    constraints = []
    if A_ub is not None and b_ub is not None:
        constraints.append(LinearConstraint(A_ub, -np.inf, b_ub))
    if A_eq is not None and b_eq is not None:
        constraints.append(LinearConstraint(A_eq, b_eq, b_eq))
    
    if bounds is None:
        bounds = Bounds(lb=0, ub=1)
    
    integrality = np.ones(len(c))  # 所有变量为整数
    
    result = milp(c, constraints=constraints, bounds=bounds,
                  integrality=integrality)
    return result

# 示例：指派问题 (3人3任务)
cost_matrix = np.array([
    [9, 2, 7],
    [6, 4, 3],
    [5, 8, 1]
])

n = 3
# 目标：最小化总成本
c = cost_matrix.flatten()

# 约束：每人只能做1个任务
A_eq_person = np.zeros((n, n*n))
for i in range(n):
    A_eq_person[i, i*n:(i+1)*n] = 1
b_eq_person = np.ones(n)

# 约束：每个任务只能1人做
A_eq_task = np.zeros((n, n*n))
for j in range(n):
    A_eq_task[j, j::n] = 1
b_eq_task = np.ones(n)

A_eq = np.vstack([A_eq_person, A_eq_task])
b_eq = np.concatenate([b_eq_person, b_eq_task])

bounds = Bounds(lb=0, ub=1)

result = solve_01_programming(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
assignment = result.x.reshape(n, n)
print("指派矩阵:")
print(np.round(assignment))
print(f"最小总成本: {result.fun}")
```

---

### 2.3 PuLP建模框架

**适用场景**：建模复杂、需要清晰表达约束逻辑

```python
from pulp import *

def solve_with_pulp():
    # 创建问题
    prob = LpProblem("Production_Planning", LpMinimize)
    
    # 决策变量
    x1 = LpVariable("x1", lowBound=0, cat='Integer')
    x2 = LpVariable("x2", lowBound=0, cat='Integer')
    y1 = LpVariable("y1", cat='Binary')  # 0-1变量
    
    # 目标函数
    prob += 40 * x1 + 30 * x2 + 1000 * y1
    
    # 约束
    prob += 7 * x1 + 3 * x2 <= 40 * y1
    prob += 10 * x1 + 5 * x2 <= 60
    prob += x1 <= 10 * y1
    
    # 求解
    prob.solve(PULP_CBC_CMD(msg=0))
    
    print(f"状态: {LpStatus[prob.status]}")
    for v in prob.variables():
        print(f"{v.name} = {v.varValue}")
    print(f"最优值 = {value(prob.objective)}")
    
    return prob

solve_with_pulp()
```

---

### 2.4 分支定界法原理

```
分支定界流程：
1. 松弛：忽略整数约束，求解LP松弛
2. 定界：LP最优值为下界(最小化)
3. 分支：选择非整数变量，分为两支
4. 剪枝：
   ├── 不可行 → 剪枝
   ├── LP最优值 > 当前上界 → 剪枝 (界外)
   └── 全整数解 → 更新上界
5. 重复直到所有节点处理完毕
```

---

## 3. 常见约束建模技巧

### 3.1 逻辑约束

```python
# 如果x1 > 0，则x2 = 0 (互斥约束)
# 引入辅助变量y ∈ {0,1}
# x1 ≤ M * y
# x2 ≤ M * (1-y)

# 如果x1 ≥ 1，则x2 ≥ 1 (蕴含约束)
# x2 ≥ x1
```

### 3.2 条件约束

```python
# 固定费用问题：使用y变量
# 成本 = f*y + c*x, 当x>0时y=1
# x ≤ M*y
# 成本 = f*y + c*x
```

### 3.3 求和约束

```python
# 选择k个物品中恰好m个
# sum(x_i) = m, x_i ∈ {0,1}
```

---

## 4. 常见陷阱与最佳实践

### 4.1 常见陷阱

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 条件约束建模错误 | 约束逻辑不正确 | 画图验证约束 |
| 大规模问题求解困难 | 超时/内存不足 | 使用启发式/降规模 |
| 松弛值不紧 | 分支定界效率低 | 添加有效不等式 |
| 变量范围设置不当 | 求解器搜索空间大 | 设置合理上下界 |
| 数值不稳定 | 求解器报错 | 预处理/缩放系数 |

### 4.2 最佳实践

- **建模清晰**：使用PuLP等建模库，代码可读性好
- **预处理**：删除固定变量、简化约束
- **有效不等式**：添加割平面加速求解
- **多起点**：对非凸问题使用多起点求解
- **验证可行性**：求解后重新检查所有约束

---

## 5. 验证清单

- [ ] 所有整数变量取整值（0或整数）
- [ ] 所有约束重新代入验证通过
- [ ] 目标函数值合理（与LP松弛对比）
- [ ] 与基准解对比（如有）
- [ ] 大规模问题求解时间可接受
- [ ] 灵敏度分析已执行（关键参数±20%）
