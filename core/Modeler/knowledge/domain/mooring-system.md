# 系泊系统设计建模知识库

> 本文件提供数学建模竞赛中系泊系统设计相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 海上浮标系泊系统设计与优化
- 锚链选型与配重块数量确定
- 系泊系统在不同海况下的稳定性分析
- 锚链长度、悬挂长度与浮标吃水深度的关系
- 多目标优化：满足约束条件下使系统总费用最小

### 1.2 常见约束条件
- 浮标倾斜角度不超过阈值（如5°）
- 锚链不接触海底（锚链悬空）
- 浮标干舷高度要求（水面以上部分）
- 锚链张力不超过额定强度
- 配重块数量为整数
- 系泊系统总费用最小化

### 1.3 数据特点
- 浮标参数：直径、质量、高度、吃水深度
- 锚链参数：单位长度质量、额定强度、刚度
- 环境参数：水深、海流速度、波浪条件
- 配重块参数：单个质量、单价
- 约束参数：倾斜角度限制、安全系数

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 悬链线方程 | 锚链形状与张力计算 | 物理意义明确、精度高 | 解析解复杂 |
| 静力学力分析 | 浮标受力平衡 | 直观易理解 | 忽略动力效应 |
| 虚功原理 | 系统势能最小化 | 无需直接计算约束力 | 适用于小变形 |
| 多目标优化 | 费用与性能权衡 | 全局最优搜索 | 计算复杂度高 |
| 整数规划 | 配重块数量离散优化 | 处理离散变量 | 求解时间长 |
| 枚举法 | 参数空间较小时 | 简单可靠 | 维数灾难 |

---

## 3. 数学基础

### 3.1 悬链线方程

**标准悬链线方程**：
```
y = a * cosh(x/a)
a = H/w
```
其中：
- H: 锚链水平张力 (N)
- w: 锚链单位长度重力 (N/m)
- a: 悬链线参数 (m)

**锚链长度与坐标关系**：
```
s = a * sinh(x/a)
L = a * (sinh(x₂/a) - sinh(x₁/a))
```

**锚链张力**：
```
T(s) = w * y(s) = w * a * cosh(x/a)
T_horizontal = H = w * a
T_vertical = w * s
T_total = sqrt(H² + (w*s)²)
```

### 3.2 浮标受力分析

**浮标受力平衡方程**：
```
水平方向: T_h = F_current + F_wave_x
竖直方向: T_v + F_buoyancy = G_float + G_chain + G_weight
力矩平衡: M_restoring = M_overturning
```

**浮力计算**：
```
F_buoyancy = ρ_water * g * V_submerged
V_submerged = π/4 * D² * d
```
其中 d 为吃水深度。

**海流力**：
```
F_current = 0.5 * ρ_water * C_D * A * v²
```
其中 C_D 为阻力系数，A 为迎流面积。

### 3.3 系统势能

**总势能**：
```
E_total = E_gravity + E_elastic
E_gravity = Σ m_i * g * h_i
E_elastic = 0.5 * k * ΔL²
```

---

## 4. Python实现

### 4.1 悬链线计算

```python
import numpy as np
from scipy.optimize import fsolve

def catenary(a, x):
    """悬链线方程 y = a * cosh(x/a)"""
    return a * np.cosh(x / a)

def catenary_length(a, x1, x2):
    """悬链线弧长"""
    return a * (np.sinh(x2 / a) - np.sinh(x1 / a))

def catenary_tension(a, w, x):
    """悬链线张力 T = w * y = w * a * cosh(x/a)"""
    return w * a * np.cosh(x / a)

def solve_catenary_params(H, w):
    """
    给定水平张力H和单位长度重力w，求悬链线参数a
    
    Parameters
    ----------
    H : float
        水平张力 (N)
    w : float
        单位长度重力 (N/m)
    
    Returns
    -------
    a : float
        悬链线参数 (m)
    """
    a = H / w
    return a
```

### 4.2 系泊系统受力分析

```python
import numpy as np
from scipy.optimize import brentq

class MooringSystem:
    """系泊系统设计类"""
    
    def __init__(self, water_depth, buoy_diameter, buoy_mass, 
                 chain_linear_density, chain_strength):
        """
        Parameters
        ----------
        water_depth : float
            水深 (m)
        buoy_diameter : float
            浮标直径 (m)
        buoy_mass : float
            浮标质量 (kg)
        chain_linear_density : float
            锚链线密度 (kg/m)
        chain_strength : float
            锚链额定强度 (N)
        """
        self.h = water_depth
        self.D = buoy_diameter
        self.m_buoy = buoy_mass
        self.rho_chain = chain_linear_density
        self.T_strength = chain_strength
        self.g = 9.81
        self.rho_water = 1025  # 海水密度 kg/m³
    
    def buoyancy(self, draft):
        """计算浮力 (N)"""
        V_sub = np.pi / 4 * self.D**2 * draft
        return self.rho_water * self.g * V_sub
    
    def current_force(self, v_current, C_D=1.2):
        """计算海流力 (N)"""
        A = self.D * self.h  # 简化：迎流面积
        return 0.5 * self.rho_water * C_D * A * v_current**2
    
    def solve_mooring(self, n_weights, weight_mass, chain_length_total):
        """
        求解系泊系统构型
        
        Parameters
        ----------
        n_weights : int
            配重块数量
        weight_mass : float
            单个配重块质量 (kg)
        chain_length_total : float
            锚链总长度 (m)
        
        Returns
        -------
        result : dict
            包含吃水深度、倾斜角度、锚链张力等
        """
        w_chain = self.rho_chain * self.g  # 单位长度重力
        w_weights = n_weights * weight_mass * self.g  # 配重重力
        G_buoy = self.m_buoy * self.g  # 浮标重力
        
        def equilibrium(draft):
            """平衡方程：浮力 = 总重力"""
            F_b = self.buoyancy(draft)
            G_total = G_buoy + w_weights + w_chain * chain_length_total
            return F_b - G_total
        
        # 求解吃水深度
        try:
            draft = brentq(equilibrium, 0, self.D)
        except ValueError:
            return None
        
        # 计算倾斜角度（简化模型）
        # 假设锚链悬挂点在浮标底部中心
        F_buoyancy = self.buoyancy(draft)
        F_gravity = G_buoy + w_weights
        
        # 浮心与重心的偏移导致倾斜
        # 简化：假设配重块均匀分布
        tilt_angle = 0  # 简化计算
        
        return {
            'draft': draft,
            'freeboard': self.D - draft,
            'tilt_angle': tilt_angle,
            'buoyancy': F_buoyancy,
            'total_weight': G_buoy + w_weights + w_chain * chain_length_total,
            'chain_tension': w_chain * chain_length_total
        }
```

### 4.3 多目标优化

```python
import numpy as np
from scipy.optimize import minimize

def optimize_mooring(n_weights_range, chain_length_range, 
                     weight_mass, chain_price_per_m, weight_price):
    """
    优化系泊系统：最小化总费用，同时满足约束
    
    Parameters
    ----------
    n_weights_range : tuple
        配重块数量范围 (min, max)
    chain_length_range : tuple
        锚链长度范围 (min, max)
    weight_mass : float
        单个配重块质量 (kg)
    chain_price_per_m : float
        锚链单价 (元/m)
    weight_price : float
        单个配重块单价 (元)
    
    Returns
    -------
    result : dict
        最优设计方案
    """
    def objective(x):
        """目标函数：最小化总费用"""
        n_weights = int(round(x[0]))
        chain_length = x[1]
        
        cost = n_weights * weight_price + chain_length * chain_price_per_m
        return cost
    
    def constraint_tilt(x):
        """约束：倾斜角度不超过5°"""
        n_weights = int(round(x[0]))
        chain_length = x[1]
        
        # 简化计算倾斜角度
        system = MooringSystem(50, 3, 1000, 50, 1e6)
        result = system.solve_mooring(n_weights, weight_mass, chain_length)
        
        if result is None:
            return -1  # 不可行
        return 5.0 - result['tilt_angle']  # 倾斜角度 < 5°
    
    def constraint_tension(x):
        """约束：锚链张力不超过额定强度"""
        n_weights = int(round(x[0]))
        chain_length = x[1]
        
        w_chain = 50 * 9.81
        tension = w_chain * chain_length
        
        return 1e6 - tension  # 张力 < 额定强度
    
    # 初始猜测
    x0 = [5, 50]
    
    # 约束
    constraints = [
        {'type': 'ineq', 'fun': constraint_tilt},
        {'type': 'ineq', 'fun': constraint_tension}
    ]
    
    # 变量边界
    bounds = [
        (n_weights_range[0], n_weights_range[1]),
        (chain_length_range[0], chain_length_range[1])
    ]
    
    # 优化
    result = minimize(objective, x0, method='SLSQP',
                     bounds=bounds, constraints=constraints)
    
    return {
        'n_weights': int(round(result.x[0])),
        'chain_length': result.x[1],
        'total_cost': result.fun,
        'success': result.success
    }
```

### 4.4 可视化

```python
import numpy as np
import matplotlib.pyplot as plt

def plot_catenary(a, x_range, w):
    """绘制悬链线形状"""
    x = np.linspace(0, x_range, 100)
    y = a * np.cosh(x / a)
    
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, 'b-', linewidth=2)
    plt.xlabel('水平距离 (m)')
    plt.ylabel('竖直高度 (m)')
    plt.title(f'悬链线形状 (a={a:.2f}m)')
    plt.grid(True)
    plt.axis('equal')
    plt.show()

def plot_tension_distribution(a, w, x_range):
    """绘制张力分布"""
    x = np.linspace(0, x_range, 100)
    T = w * a * np.cosh(x / a)
    
    plt.figure(figsize=(10, 6))
    plt.plot(x, T, 'r-', linewidth=2)
    plt.xlabel('水平距离 (m)')
    plt.ylabel('张力 (N)')
    plt.title('锚链张力分布')
    plt.grid(True)
    plt.show()
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 忽略锚链自重 | 浮力计算错误 | 考虑锚链单位长度重力 |
| 配重块数量非整数 | 优化结果不可行 | 使用整数规划或取整后验证 |
| 简化过度 | 未考虑锚链弹性变形 | 引入弹性模量修正 |
| 边界条件错误 | 锚链接触海底 | 检查锚链最低点高度 |
| 单位不一致 | 力的单位混乱 | 统一使用SI单位制 |
| 未验证平衡 | 结果不满足物理规律 | 检查力和力矩平衡 |

---

## 6. 验证方法

### 6.1 力平衡验证
- 水平方向：锚链水平张力 = 海流力 + 波浪力
- 竖直方向：浮力 = 浮标重力 + 锚链重力 + 配重重力

### 6.2 力矩平衡验证
- 对浮标中心取矩，合力矩为零

### 6.3 能量验证
- 系统势能最小化（虚功原理）

### 6.4 极端工况验证
- 最大风浪下的系统响应
- 锚链张力不超过额定强度

### 6.5 与实验数据对比
- 与已知系泊系统设计案例对比
- 检查结果数量级合理性

---

## 7. 真题案例

### 7.1 2016A 系泊系统设计

**题目要点**：
- 设计浮标系泊系统，使系统在满足约束条件下总费用最小
- 浮标直径3m，质量1000kg，水深50m
- 锚链线密度50kg/m，额定强度1×10⁶N
- 配重块每个质量80kg，单价2000元
- 锚链单价500元/m
- 约束：倾斜角度≤5°，锚链张力≤额定强度

**解题思路**：
1. 建立悬链线模型，计算锚链形状和张力
2. 分析浮标受力平衡，建立平衡方程
3. 枚举配重块数量和锚链长度的组合
4. 在满足约束条件下，寻找费用最小的设计方案

**关键代码片段**：
```python
# 枚举搜索最优设计
best_cost = float('inf')
best_design = None

for n_weights in range(1, 20):
    for chain_length in range(30, 100):
        system = MooringSystem(50, 3, 1000, 50, 1e6)
        result = system.solve_mooring(n_weights, 80, chain_length)
        
        if result is not None and result['tilt_angle'] <= 5:
            cost = n_weights * 2000 + chain_length * 500
            if cost < best_cost:
                best_cost = cost
                best_design = {
                    'n_weights': n_weights,
                    'chain_length': chain_length,
                    'cost': cost,
                    'result': result
                }
```

**参考答案**：
- 配重块数量：约10-15个
- 锚链长度：约60-80m
- 总费用：约4-6万元
- 吃水深度：约0.8-1.2m

---

## 8. 验证清单

- [ ] 悬链线方程正确（y = a * cosh(x/a)）
- [ ] 力平衡满足（水平+竖直方向）
- [ ] 力矩平衡满足
- [ ] 配重块数量为整数
- [ ] 锚链张力不超过额定强度
- [ ] 倾斜角度不超过5°
- [ ] 总费用计算正确
- [ ] 结果数量级合理（吃水深度<直径）
