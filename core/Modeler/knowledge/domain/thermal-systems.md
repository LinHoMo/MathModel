# 热传导系统建模知识库

> 本文件提供数学建模竞赛中热传导系统相关问题的建模知识，包括炉温曲线、高温服装、热传导优化等问题。

---

## 1. 问题特征

### 1.1 典型问题描述
- 回焊炉炉温曲线优化
- 高温作业专用服装设计
- 热传导过程建模
- 温度场分析与控制

### 1.2 常见约束条件
- 温度约束：最高/最低温度、升温/降温速率
- 时间约束：加热时间、冷却时间
- 材料约束：导热系数、比热容、密度
- 安全约束：温度梯度、热应力

### 1.3 数据特点
- 温度数据：空间分布、时间演化
- 材料参数：导热系数、比热容、密度
- 几何数据：尺寸、形状
- 边界条件：对流、辐射、热源

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 解析解法 | 简单几何 | 精确 | 适用范围有限 |
| 有限差分法 | 一维/二维 | 简单 | 精度有限 |
| 有限元法 | 复杂几何 | 精确 | 实现复杂 |
| 优化算法 | 参数优化 | 自动搜索 | 计算量大 |

---

## 3. 数学基础

### 3.1 热传导方程

**一维热传导方程**：
```
ρc ∂T/∂t = k ∂²T/∂x² + q
```
其中：
- ρ: 密度 (kg/m³)
- c: 比热容 (J/(kg·K))
- T: 温度 (K)
- t: 时间 (s)
- k: 导热系数 (W/(m·K))
- x: 位置 (m)
- q: 内热源 (W/m³)

### 3.2 边界条件

**第一类边界条件（Dirichlet）**：
```
T(x=0, t) = T₀
```

**第二类边界条件（Neumann）**：
```
-k ∂T/∂x|_{x=0} = q₀
```

**第三类边界条件（Robin）**：
```
-k ∂T/∂x|_{x=0} = h(T - T_∞)
```
其中h为对流换热系数。

### 3.3 解析解

**无限大平板解析解**：
```
T(x,t) = T₀ + (T₁ - T₀) × erf(x / (2√(αt)))
```
其中：
- α: 热扩散系数 = k/(ρc)
- erf: 误差函数

---

## 4. 代码实现

### 4.1 有限差分法

```python
import numpy as np

def heat_conduction_1d(L, nx, nt, alpha, T_left, T_right, T_init):
    """
    一维热传导有限差分求解
    
    Parameters
    ----------
    L : float
        板厚 (m)
    nx : int
        空间网格数
    nt : int
        时间步数
    alpha : float
        热扩散系数 (m²/s)
    T_left : float
        左边界温度 (K)
    T_right : float
        右边界温度 (K)
    T_init : float
        初始温度 (K)
    
    Returns
    -------
    x : array
        空间坐标
    t : array
        时间坐标
    T : array
        温度场 (nt, nx)
    """
    # 网格
    dx = L / (nx - 1)
    dt = 0.5 * dx**2 / alpha  # 稳定性条件
    
    x = np.linspace(0, L, nx)
    t = np.arange(0, nt * dt, dt)
    
    # 初始化温度场
    T = np.zeros((nt, nx))
    T[0, :] = T_init
    
    # 边界条件
    T[:, 0] = T_left
    T[:, -1] = T_right
    
    # 有限差分求解
    for n in range(0, nt - 1):
        for i in range(1, nx - 1):
            T[n+1, i] = T[n, i] + alpha * dt / dx**2 * (
                T[n, i+1] - 2*T[n, i] + T[n, i-1]
            )
    
    return x, t, T
```

### 4.2 热传导求解器

```python
import numpy as np
from scipy.integrate import odeint

def heat_conduction_ode(x, t, k, rho, cp, T_boundary_left, T_boundary_right):
    """
    热传导ODE形式
    """
    # 这里简化为集总参数模型
    # 实际应用需要使用PDE求解器
    T = x[0]  # 温度
    q = x[1]  # 热流
    
    # 简化模型
    dTdt = q / (rho * cp)
    dqdt = 0  # 假设热流恒定
    
    return [dTdt, dqdt]
```

### 4.3 优化炉温曲线

```python
import numpy as np
from scipy.optimize import minimize

def optimize_furnace_profile(target_profile, time_points, 
                            temp_range, heating_rate_limit):
    """
    优化炉温曲线
    
    Parameters
    ----------
    target_profile : array
        目标温度曲线
    time_points : array
        时间点
    temp_range : tuple
        温度范围 (T_min, T_max)
    heating_rate_limit : float
        升温速率限制 (K/s)
    
    Returns
    -------
    optimal_profile : array
        最优温度曲线
    """
    def objective(profile):
        # 计算与目标曲线的差异
        return np.sum((profile - target_profile)**2)
    
    def constraint_heating_rate(profile):
        # 升温速率限制
        rates = np.diff(profile) / np.diff(time_points)
        return heating_rate_limit - np.max(np.abs(rates))
    
    # 初始猜测
    x0 = np.interp(time_points, [time_points[0], time_points[-1]], 
                   [temp_range[0], temp_range[1]])
    
    # 约束
    constraints = {'type': 'ineq', 'fun': constraint_heating_rate}
    
    # 边界
    bounds = [(temp_range[0], temp_range[1])] * len(time_points)
    
    # 优化
    result = minimize(objective, x0, method='SLSQP', 
                     bounds=bounds, constraints=constraints)
    
    return result.x
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 网格不稳定 | 数值振荡 | 满足稳定性条件 |
| 边界处理错误 | 温度异常 | 正确设置边界条件 |
| 参数单位错误 | 温度量级错误 | 统一使用SI单位 |
| 忽略热源 | 温度分布偏差 | 加入热源项 |
| 时间步长过大 | 精度不足 | 减小时间步长 |

---

## 6. 验证方法

### 6.1 解析验证
- 与解析解对比（简单情况）
- 检查能量守恒

### 6.2 基准测试
- 与已知实验数据对比
- 与商业软件结果对比

### 6.3 灵敏度分析
- 改变导热系数，观察温度变化
- 改变边界条件，观察温度变化

---

## 7. 参考论文

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| A070 | 一维热传导方程 | 炉温曲线机理建模 |
| A147 | 热传导方程 | 炉温曲线优化 |
| A195 | 一维热传导 | 回焊炉温模型 |
| A212 | 温度控制 | 回焊炉温曲线优化 |
| A229 | 非稳态导热 | 高温服装设计 |
| A401 | 热传导模型 | 高温服装设计 |
| A440 | 热传导 | 高温作业服设计 |
| A466 | 热传导 | 高温服装设计 |

---

## 8. 验证清单

- [ ] 热传导方程建立正确
- [ ] 边界条件设置正确
- [ ] 网格稳定性条件满足
- [ ] 温度单位正确（K或℃）
- [ ] 能量守恒检查通过
- [ ] 灵敏度分析已执行
- [ ] 结果与物理直觉一致
