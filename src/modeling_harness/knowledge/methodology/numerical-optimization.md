# 数值优化方法论

> 本文件提供数学建模竞赛中常用的数值优化知识，包括算法选择、实现要点、防错策略和验证方法。

---

## 1. 算法选择决策树

```
数值优化问题类型识别：
├── 无约束优化
│   ├── 可导函数
│   │   ├── 低维 → BFGS/L-BFGS-B
│   │   └── 高维 → L-BFGS-B/共轭梯度
│   └── 不可导 → Nelder-Mead/差分进化
├── 有约束优化
│   ├── 线性约束 → SLSQP
│   ├── 非线性约束 → SLSQP/内点法
│   └── 边界约束 → L-BFGS-B
├── 非线性最小二乘
│   └── 曲线拟合 → leastsq/curve_fit
└── 全局优化
    ├── 低维 → 网格搜索/多起点
    └── 高维 → 差分进化/遗传算法
```

---

## 2. 核心算法详解

### 2.1 BFGS拟牛顿法

**方法原理**：
通过迭代构建Hessian矩阵的近似，利用二阶信息加速收敛。

**适用场景**：
- 连续可导函数
- 中小规模问题
- 需要快速收敛

**关键特性**：
- 超线性收敛
- 需要梯度信息
- 内存消耗适中

**代码框架**：
```python
from scipy.optimize import minimize
import numpy as np

def bfgs_optimization(objective, gradient, x0, bounds=None):
    """
    BFGS优化
    """
    result = minimize(
        objective, x0, jac=gradient, method='BFGS',
        options={'disp': True, 'maxiter': 1000}
    )
    return result

# 使用示例
def rosenbrock(x):
    return sum(100*(x[i+1] - x[i]**2)**2 + (1 - x[i])**2 for i in range(len(x)-1))

def rosenbrock_grad(x):
    grad = np.zeros_like(x)
    for i in range(len(x)-1):
        grad[i] = -400*x[i]*(x[i+1] - x[i]**2) + 2*(x[i] - 1)
        grad[i+1] = 200*(x[i+1] - x[i]**2)
    return grad

x0 = np.array([-1.0, 1.0, 0.5])
result = bfgs_optimization(rosenbrock, rosenbrock_grad, x0)
print(f"最优解: {result.x}")
print(f"最优值: {result.fun}")
```

---

### 2.2 L-BFGS-B（有限内存拟牛顿法）

**方法原理**：
BFGS的有限内存版本，适合高维问题，支持边界约束。

**适用场景**：
- 高维优化（维度>1000）
- 有边界约束
- 内存受限

**代码框架**：
```python
from scipy.optimize import minimize
import numpy as np

def lbfgsb_optimization(objective, gradient, x0, bounds):
    """
    L-BFGS-B优化（支持边界约束）
    """
    result = minimize(
        objective, x0, jac=gradient, method='L-BFGS-B',
        bounds=bounds,
        options={'disp': True, 'maxiter': 1000}
    )
    return result

# 使用示例
def sphere(x):
    return np.sum(x**2)

def sphere_grad(x):
    return 2 * x

x0 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
bounds = [(-10, 10)] * 5

result = lbfgsb_optimization(sphere, sphere_grad, x0, bounds)
print(f"最优解: {result.x}")
print(f"最优值: {result.fun}")
```

---

### 2.3 SLSQP（序列最小二乘规划）

**方法原理**：
处理非线性约束优化，通过序列二次规划迭代求解。

**适用场景**：
- 有非线性约束
- 等式/不等式约束
- 工程优化问题

**代码框架**：
```python
from scipy.optimize import minimize
import numpy as np

def slsqp_optimization(objective, x0, constraints=None, bounds=None):
    """
    SLSQP优化（支持非线性约束）
    """
    result = minimize(
        objective, x0, method='SLSQP',
        constraints=constraints,
        bounds=bounds,
        options={'disp': True, 'maxiter': 1000}
    )
    return result

# 使用示例
def objective(x):
    return x[0]**2 + x[1]**2

# 约束：x[0] + x[1] >= 1
constraints = [
    {'type': 'ineq', 'fun': lambda x: x[0] + x[1] - 1}
]

bounds = [(0, None), (0, None)]
x0 = np.array([0.5, 0.5])

result = slsqp_optimization(objective, x0, constraints, bounds)
print(f"最优解: {result.x}")
print(f"最优值: {result.fun}")
```

---

### 2.4 Nelder-Mead单纯形法

**方法原理**：
无导数优化方法，通过单纯形的反射、扩展、收缩操作搜索最优解。

**适用场景**：
- 不可导函数
- 噪声函数
- 低维问题（维度<20）

**代码框架**：
```python
from scipy.optimize import minimize
import numpy as np

def nelder_mead_optimization(objective, x0):
    """
    Nelder-Mead优化（无导数需求）
    """
    result = minimize(
        objective, x0, method='Nelder-Mead',
        options={'disp': True, 'maxiter': 1000, 'xatol': 1e-8}
    )
    return result

# 使用示例
def noisy_function(x):
    return sum((xi - 1)**2 for xi in x) + np.random.normal(0, 0.01)

x0 = np.array([0.0, 0.0, 0.0])
result = nelder_mead_optimization(noisy_function, x0)
print(f"最优解: {result.x}")
print(f"最优值: {result.fun}")
```

---

### 2.5 非线性最小二乘

**方法原理**：
最小化残差平方和，常用于曲线拟合和参数估计。

**代码框架**：
```python
from scipy.optimize import leastsq, curve_fit
import numpy as np

def nonlinear_least_squares(func, xdata, ydata, p0):
    """
    非线性最小二乘拟合
    """
    def residuals(params, x, y):
        return y - func(x, *params)
    
    popt, pcov = leastsq(residuals, p0, args=(xdata, ydata))
    
    # 计算拟合优度
    y_fit = func(xdata, *popt)
    ss_res = np.sum((ydata - y_fit)**2)
    ss_tot = np.sum((ydata - np.mean(ydata))**2)
    r2 = 1 - ss_res / ss_tot
    
    print(f"拟合参数: {popt}")
    print(f"R²: {r2:.4f}")
    
    return popt, pcov

# 使用示例
def model(x, a, b, c):
    return a * np.exp(-b * x) + c

xdata = np.linspace(0, 4, 50)
ydata = 2.5 * np.exp(-1.3 * xdata) + 0.5 + np.random.normal(0, 0.1, 50)

popt, pcov = nonlinear_least_squares(model, xdata, ydata, p0=[1, 1, 1])
```

---

### 2.6 多起点优化

**方法原理**：
从多个初始点运行优化，避免陷入局部最优。

**代码框架**：
```python
from scipy.optimize import minimize
import numpy as np

def multi_start_optimization(objective, bounds, n_starts=10):
    """
    多起点优化
    """
    best_result = None
    best_value = np.inf
    
    for i in range(n_starts):
        # 随机初始点
        x0 = np.random.uniform(
            [b[0] for b in bounds],
            [b[1] for b in bounds]
        )
        
        result = minimize(
            objective, x0, method='L-BFGS-B', bounds=bounds,
            options={'disp': False}
        )
        
        if result.fun < best_value:
            best_value = result.fun
            best_result = result
    
    print(f"最佳初始点: {best_result.x}")
    print(f"最佳值: {best_result.fun}")
    print(f"运行次数: {n_starts}")
    
    return best_result

# 使用示例
def multimodal(x):
    return np.sin(x[0]) + np.sin(x[1]) + 0.1*(x[0]**2 + x[1]**2)

bounds = [(-10, 10), (-10, 10)]
result = multi_start_optimization(multimodal, bounds, n_starts=20)
```

---

## 3. 约束处理方法

### 3.1 约束类型与处理

```python
# 等式约束: h(x) = 0
constraints_eq = {'type': 'eq', 'fun': lambda x: x[0] + x[1] - 1}

# 不等式约束: g(x) >= 0
constraints_ineq = {'type': 'ineq', 'fun': lambda x: x[0] - 0.5}

# 边界约束: lb <= x <= ub
bounds = [(0, 10), (0, 10)]
```

### 3.2 惩罚函数法

```python
def penalized_objective(x, original_obj, constraints, lambda_val=1000):
    penalty = 0
    for constraint in constraints:
        if constraint['type'] == 'ineq':
            violation = max(0, -constraint['fun'](x))
        elif constraint['type'] == 'eq':
            violation = abs(constraint['fun'](x))
        penalty += violation ** 2
    return original_obj(x) + lambda_val * penalty
```

---

## 4. 收敛诊断

### 4.1 收敛判断

```python
def check_convergence(result, tolerance=1e-6):
    """检查优化收敛状态"""
    checks = {
        '收敛成功': result.success,
        '函数评估次数': result.nfev,
        '梯度范数': np.linalg.norm(result.jac) if hasattr(result, 'jac') else None,
        '最优值': result.fun,
        '参数变化': np.linalg.norm(result.x - result.x0) if hasattr(result, 'x0') else None
    }
    
    for key, value in checks.items():
        if value is not None:
            print(f"{key}: {value}")
    
    return result.success
```

### 4.2 多次运行统计

```python
def optimization_statistics(objective, bounds, n_runs=10):
    """多次运行统计"""
    results = []
    for _ in range(n_runs):
        x0 = np.random.uniform([b[0] for b in bounds], [b[1] for b in bounds])
        result = minimize(objective, x0, method='L-BFGS-B', bounds=bounds)
        results.append(result)
    
    values = [r.fun for r in results]
    print(f"最优值: {min(values):.6f}")
    print(f"最差值: {max(values):.6f}")
    print(f"均值: {np.mean(values):.6f}")
    print(f"标准差: {np.std(values):.6f}")
    
    return results
```

---

## 5. 常见陷阱与最佳实践

### 5.1 常见陷阱

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 局部最优 | 多次运行结果差异大 | 多起点运行≥5次 |
| 收敛速度慢 | 迭代次数过多 | 检查梯度/换算法 |
| 初始值选择不当 | 收敛到次优解 | 多起点/网格搜索 |
| 约束处理不当 | 最优解不可行 | 重新检查约束 |
| 数值不稳定 | 求解器报错 | 缩放变量/预处理 |

### 5.2 最佳实践

- **多起点运行**：至少5次，报告统计结果
- **算法对比**：至少2种算法对比
- **收敛验证**：检查梯度范数和函数变化
- **约束验证**：求解后重新检查所有约束
- **结果解释**：结合业务逻辑解释最优解

---

## 6. 验证清单

- [ ] 优化器收敛状态为True
- [ ] 多次运行结果稳定（标准差/均值 < 10%）
- [ ] 最优解重新代入所有约束检查通过
- [ ] 与基准解对比（网格扫描/退化情形）
- [ ] 灵敏度分析已执行（关键参数±20%）
- [ ] 结果数量级与物理直觉一致
- [ ] 梯度范数足够小（接近0）
- [ ] 函数评估次数合理
