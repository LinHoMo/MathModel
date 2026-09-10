# 全局优化理论工具

> 本文档提供全局优化的理论工具和实用验证方法，确保优化结果的可靠性和最优性。

---

## 一、理论工具分类

### 1.1 精确方法

| 方法 | 原理 | 适用问题 | 优点 | 缺点 |
|------|------|---------|------|------|
| 分支定界 | 系统搜索解空间 | 整数规划 | 保证全局最优 | 计算时间长 |
| 割平面法 | 添加切割平面 | 整数规划 | 收敛快 | 实现复杂 |
| 动态规划 | 最优子结构 | 序列决策 | 理论完备 | 维度灾难 |

### 1.2 松弛方法

| 方法 | 原理 | 适用问题 | 优点 | 缺点 |
|------|------|---------|------|------|
| 拉格朗日松弛 | 困难约束转化为惩罚项 | 约束优化 | 提供上界 | 对偶间隙 |
| 凸松弛 | 非凸问题松弛为凸问题 | 非线性优化 | 可精确求解 | 计算复杂 |
| 半正定松弛 | 矩阵约束松弛 | 二次规划 | 理论保证 | 维度限制 |

### 1.3 启发式方法

| 方法 | 原理 | 适用问题 | 优点 | 缺点 |
|------|------|---------|------|------|
| 遗传算法 | 生物进化 | 通用 | 全局搜索 | 不保证最优 |
| 模拟退火 | 金属退火 | 通用 | 跳出局部最优 | 参数敏感 |
| 粒子群 | 鸟群行为 | 连续优化 | 简单高效 | 易早熟 |

---

## 二、拉格朗日松弛详解

### 2.1 基本原理

**原问题**：

```
min f(x)
s.t. g(x) ≤ 0
     h(x) = 0
     x ∈ X
```

**拉格朗日松弛**：

```
L(x, λ, μ) = f(x) + λᵀg(x) + μᵀh(x)
```

其中 λ ≥ 0 是拉格朗日乘子。

### 2.2 对偶问题

```
max_λ,μ min_x L(x, λ, μ)
s.t. λ ≥ 0
```

**性质**：
- 对偶问题的最优值 ≤ 原问题的最优值（弱对偶性）
- 对偶间隙 = 原问题最优值 - 对偶问题最优值

### 2.3 实用验证方法

**拉格朗日松弛验证**：

```python
import numpy as np
from scipy.optimize import minimize

def lagrangian_relaxation(objective, constraints, bounds):
    """
    拉格朗日松弛验证
    
    Parameters:
    - objective: 目标函数
    - constraints: 约束函数列表
    - bounds: 变量边界
    
    Returns:
    - upper_bound: 可行解上界
    - lower_bound: 拉格朗日下界
    """
    
    def lagrangian(x, lambda_vals):
        # 拉格朗日函数
        L = objective(x)
        for i, (c, l) in enumerate(zip(constraints, lambda_vals)):
            L += l * c(x)
        return L
    
    # 求解对偶问题
    def dual_function(lambda_vals):
        result = minimize(lambda x: lagrangian(x, lambda_vals), x0, bounds=bounds)
        return -result.fun  # 取负号因为对偶是max问题
    
    # 求解原问题（启发式）
    result_primal = minimize(objective, x0, bounds=bounds, constraints=constraints)
    upper_bound = result_primal.fun
    
    # 求解对偶问题
    result_dual = minimize(lambda l: -dual_function(l), lambda0)
    lower_bound = -result_dual.fun
    
    # 对偶间隙
    duality_gap = upper_bound - lower_bound
    
    return {
        'upper_bound': upper_bound,
        'lower_bound': lower_bound,
        'duality_gap': duality_gap,
        'relative_gap': duality_gap / upper_bound
    }
```

### 2.4 判断标准

| 相对对偶间隙 | 结论 |
|-------------|------|
| < 1% | 高度可信，接近全局最优 |
| 1%-5% | 较为可信，可接受 |
| 5%-10% | 一般，需要进一步验证 |
| > 10% | 不可信，需要重新求解 |

---

## 三、凸松弛详解

### 3.1 基本原理

**凸松弛**：将非凸问题松弛为凸问题，凸问题的最优值是原问题最优值的下界。

**常用凸松弛技术**：

| 技术 | 适用问题 | 原理 |
|------|---------|------|
| McCormick松弛 | 双线性项 | 构造凸包络 |
| SDP松弛 | 二次规划 | 半正定约束 |
| 区间分析 | 非线性规划 | 区间运算 |

### 3.2 McCormick松弛

**双线性项 xy 的松弛**：

```
xy ≥ x_L·y + x·y_L - x_L·y_L  (下界)
xy ≤ x_H·y + x·y_L - x_H·y_L  (上界)
xy ≤ x_L·y + x·y_H - x_L·y_H  (上界)
xy ≥ x_H·y + x·y_H - x_H·y_H  (下界)
```

其中 [x_L, x_H] 和 [y_L, y_H] 是变量的区间。

### 3.3 实用验证方法

```python
import numpy as np
from scipy.optimize import minimize

def convex_relaxation verification(objective, nonconvex_constraints, bounds):
    """
    凸松弛验证
    
    Parameters:
    - objective: 目标函数（可凸可非凸）
    - nonconvex_constraints: 非凸约束
    - bounds: 变量边界
    
    Returns:
    - convex_lower_bound: 凸松弛下界
    - primal_upper_bound: 原问题上界
    """
    
    # 求解凸松弛问题（去掉非凸约束）
    def convex_objective(x):
        return objective(x)
    
    result_convex = minimize(convex_objective, x0, bounds=bounds)
    convex_lower_bound = result_convex.fun
    
    # 求解原问题（启发式）
    result_primal = minimize(objective, x0, bounds=bounds, constraints=nonconvex_constraints)
    primal_upper_bound = result_primal.fun
    
    # 验证
    relaxation_gap = primal_upper_bound - convex_lower_bound
    
    return {
        'convex_lower_bound': convex_lower_bound,
        'primal_upper_bound': primal_upper_bound,
        'relaxation_gap': relaxation_gap
    }
```

---

## 四、分支定界详解

### 4.1 基本原理

**分支定界**：系统搜索解空间，通过分支和剪枝提高效率。

**算法流程**：

```
1. 初始化：将原问题作为根节点
2. 求解松弛问题，得到下界
3. 分支：选择一个变量进行分支
4. 剪枝：
   - 如果松弛问题无解，剪枝
   - 如果松弛问题下界 > 当前最优解，剪枝
   - 如果松弛问题解为整数，更新最优解
5. 重复步骤2-4直到所有节点处理完毕
```

### 4.2 实用验证方法

```python
import numpy as np
from scipy.optimize import linprog

def branch_and_bound_verification(objective, constraints, bounds, integer_vars):
    """
    分支定界验证
    
    Parameters:
    - objective: 目标函数系数
    - constraints: 约束矩阵和向量
    - bounds: 变量边界
    - integer_vars: 整数变量索引
    
    Returns:
    - optimal_value: 最优值
    - optimal_solution: 最优解
    - bounds_history: 界限历史
    """
    
    # 求解LP松弛
    result_lp = linprog(objective, A_ub=constraints['A'], b_ub=constraints['b'],
                        bounds=bounds, method='highs')
    
    lp_bound = result_lp.fun
    
    # 分支定界（简化版）
    def branch_and_bound_recursive(current_bounds, current_best):
        # 求解当前节点的LP松弛
        result = linprog(objective, A_ub=constraints['A'], b_ub=constraints['b'],
                        bounds=current_bounds, method='highs')
        
        if not result.success:
            return current_best
        
        # 剪枝
        if result.fun >= current_best['value']:
            return current_best
        
        # 检查是否为整数解
        solution = result.x
        is_integer = all(solution[i] == int(solution[i]) for i in integer_vars)
        
        if is_integer:
            return {'value': result.fun, 'solution': solution}
        
        # 分支
        # 选择最接近整数的变量
        for i in integer_vars:
            if solution[i] != int(solution[i]):
                # 左分支：x ≤ floor(x)
                left_bounds = current_bounds.copy()
                left_bounds[i] = (current_bounds[i][0], int(solution[i]))
                current_best = branch_and_bound_recursive(left_bounds, current_best)
                
                # 右分支：x ≥ ceil(x)
                right_bounds = current_bounds.copy()
                right_bounds[i] = (int(solution[i]) + 1, current_bounds[i][1])
                current_best = branch_and_bound_recursive(right_bounds, current_best)
                break
        
        return current_best
    
    # 执行分支定界
    optimal = branch_and_bound_recursive(bounds, {'value': float('inf'), 'solution': None})
    
    return {
        'lp_bound': lp_bound,
        'optimal_value': optimal['value'],
        'optimal_solution': optimal['solution'],
        'integrality_gap': optimal['value'] - lp_bound
    }
```

---

## 五、实用验证方法汇总

### 5.1 多起点验证

**方法**：运行多次启发式算法，报告统计信息。

```python
import numpy as np

def multi_start_verification(objective, bounds, n_runs=10):
    """
    多起点验证
    """
    results = []
    
    for _ in range(n_runs):
        # 随机初始点
        x0 = np.random.uniform([b[0] for b in bounds], [b[1] for b in bounds])
        
        # 求解
        result = minimize(objective, x0, bounds=bounds)
        results.append(result.fun)
    
    # 统计分析
    mean = np.mean(results)
    std = np.std(results)
    cv = std / mean
    best = np.min(results)
    worst = np.max(results)
    
    return {
        'mean': mean,
        'std': std,
        'cv': cv,
        'best': best,
        'worst': worst,
        'all_results': results
    }
```

**判断标准**：

| 变异系数 | 结论 |
|---------|------|
| < 5% | 高度稳定，结果可信 |
| 5%-10% | 较稳定，可接受 |
| 10%-20% | 一般，需要更多运行 |
| > 20% | 不稳定，需要重新设计算法 |

### 5.2 网格扫描

**方法**：在解空间上进行网格搜索，与优化结果对比。

```python
import numpy as np

def grid_scan_verification(objective, bounds, grid_points=10):
    """
    网格扫描验证
    """
    # 生成网格
    grids = [np.linspace(b[0], b[1], grid_points) for b in bounds]
    mesh = np.meshgrid(*grids, indexing='ij')
    
    # 评估网格点
    grid_values = np.zeros_like(mesh[0])
    for i in range(grid_points):
        for j in range(grid_points):
            x = [mesh[k][i, j] for k in range(len(bounds))]
            grid_values[i, j] = objective(x)
    
    # 网格最优
    grid_optimal = np.min(grid_values)
    
    return {
        'grid_optimal': grid_optimal,
        'grid_mean': np.mean(grid_values),
        'grid_std': np.std(grid_values)
    }
```

### 5.3 理论对比

**方法**：与已知解析解对比，验证算法正确性。

```python
def analytical_comparison(algorithm, analytical_solution, problem_params):
    """
    理论对比验证
    """
    # 运行算法
    algorithm_result = algorithm(problem_params)
    
    # 计算误差
    absolute_error = abs(algorithm_result - analytical_solution)
    relative_error = absolute_error / abs(analytical_solution)
    
    return {
        'algorithm_result': algorithm_result,
        'analytical_solution': analytical_solution,
        'absolute_error': absolute_error,
        'relative_error': relative_error
    }
```

---

## 六、方法选择指南

### 6.1 问题类型与方法匹配

| 问题类型 | 推荐方法 | 理论保证 | 计算成本 |
|---------|---------|---------|---------|
| 低维连续优化（n<10） | 网格扫描 | 高 | 低 |
| 中维连续优化（10≤n<100） | 多起点+灵敏度 | 中 | 中 |
| 高维连续优化（n≥100） | 凸松弛+启发式 | 中 | 高 |
| 整数规划 | 分支定界 | 高 | 高 |
| 组合优化 | 拉格朗日松弛 | 中 | 中 |
| 非凸优化 | 凸松弛 | 中 | 高 |

### 6.2 验证方法选择

| 验证目的 | 推荐方法 | 适用场景 |
|---------|---------|---------|
| 算法正确性 | 理论对比 | 有解析解 |
| 结果稳定性 | 多起点验证 | 启发式算法 |
| 全局最优性 | 网格扫描 | 低维问题 |
| 对偶间隙 | 拉格朗日松弛 | 约束优化 |

### 6.3 综合验证策略

**推荐流程**：

```
1. 算法正确性验证（理论对比）
   ↓
2. 结果稳定性验证（多起点）
   ↓
3. 全局最优性验证（网格扫描/拉格朗日松弛）
   ↓
4. 灵敏度分析（参数扰动）
```

---

## 七、常见问题与解决方案

### 7.1 优化不收敛

**可能原因**：
- 目标函数不连续
- 约束冲突
- 参数设置不当

**解决方案**：
- 检查目标函数连续性
- 验证约束可行性
- 调整算法参数

### 7.2 结果不稳定

**可能原因**：
- 多个局部最优
- 算法早熟
- 初始点敏感

**解决方案**：
- 增加运行次数
- 使用混合算法
- 改进初始化策略

### 7.3 对偶间隙大

**可能原因**：
- 约束过于严格
- 问题结构复杂
- 松弛质量差

**解决方案**：
- 放松部分约束
- 改进松弛方法
- 使用精确算法

---

## 八、参考资源

### 8.1 教材推荐

- 《最优化导论》（Edwin K. P. Chong）
- 《凸优化》（Stephen Boyd）
- 《全局优化导论》（Horst & Tuy）

### 8.2 软件工具

- SCIP：混合整数规划求解器
- BARON：全局优化求解器
- COUENNE：非凸优化求解器

### 8.3 Python库

- scipy.optimize：基础优化
- pyomo：建模语言
- pulp：线性规划
- cvxpy：凸优化

### 8.4 检查清单

- [ ] 问题类型识别正确
- [ ] 方法选择恰当
- [ ] 验证方法充分
- [ ] 结果稳定性好
- [ ] 对偶间隙可接受
- [ ] 灵敏度分析完成
