# 波浪能建模知识库

> 本文件提供数学建模竞赛中波浪能相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 波浪能装置的输出功率优化
- 装置参数设计与优化
- 波浪能捕获效率最大化
- 多装置协同工作优化

### 1.2 常见约束条件
- 物理约束：装置尺寸、材料强度、运动范围
- 环境约束：波浪条件、水深、海流
- 经济约束：成本、维护难度
- 安全约束：极端海况下的保护

### 1.3 数据特点
- 波浪数据：波高、波周期、波向
- 装置参数：尺寸、质量、阻尼系数
- 环境参数：水深、海流速度
- 输出数据：功率、效率、运动轨迹

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 微分方程建模 | 装置运动动力学 | 物理意义明确 | 求解复杂 |
| 数值模拟 | 复杂系统仿真 | 灵活性高 | 计算量大 |
| 遗传算法 | 参数优化 | 全局搜索能力强 | 收敛慢 |
| 响应面法 | 参数敏感性分析 | 计算效率高 | 精度有限 |
| 能量守恒 | 功率计算 | 理论基础扎实 | 需要简化假设 |

---

## 3. 数学基础

### 3.1 波浪理论

**线性波浪理论（Airy波浪理论）**：
```
波面方程: η = A cos(kx - ωt)
水质点速度: u = Aω cosh(k(z+h)) / sinh(kh) * cos(kx - ωt)
           v = Aω sinh(k(z+h)) / sinh(kh) * sin(kx - ωt)
```

其中：
- A: 波幅 (m)
- k: 波数 = 2π/λ
- ω: 圆频率 = 2π/T
- h: 水深 (m)
- λ: 波长 (m)
- T: 波周期 (s)

**色散关系**：
```
ω² = gk tanh(kh)
```

### 3.2 装置运动方程

**单自由度运动方程**：
```
mẍ + cẋ + kx = F_wave(t)
```

其中：
- m: 装置质量 (kg)
- c: 阻尼系数 (N·s/m)
- k: 弹簧刚度 (N/m)
- F_wave: 波浪力 (N)

**多自由度运动方程**：
```
Mẍ + Cẋ + Kx = F_wave(t)
```

### 3.3 功率计算

**瞬时功率**：
```
P(t) = F_wave(t) * ẋ(t)
```

**平均功率**：
```
P_avg = (1/T) ∫₀ᵀ P(t) dt
```

**捕获宽度比**：
```
η = P_avg / (ρgA²c_g/2)
```
其中c_g为群速度。

---

## 4. 代码实现

### 4.1 波浪力计算

```python
import numpy as np

def wave_force(A, k, h, z, t, rho=1025, g=9.81):
    """
    计算波浪力（Morison方程简化版）
    
    Parameters
    ----------
    A : float
        波幅 (m)
    k : float
        波数 (1/m)
    h : float
        水深 (m)
    z : float
        水质点z坐标 (m)，从静水面向下为正
    t : float
        时间 (s)
    rho : float
        海水密度 (kg/m³)
    g : float
        重力加速度 (m/s²)
    
    Returns
    -------
    F : float
        波浪力 (N/m)
    """
    omega = np.sqrt(g * k * np.tanh(k * h))
    
    # 水平速度
    u = A * omega * np.cosh(k * (z + h)) / np.sinh(k * h) * np.cos(-omega * t)
    
    # 水平加速度
    du_dt = A * omega**2 * np.cosh(k * (z + h)) / np.sinh(k * h) * np.sin(-omega * t)
    
    # Morison方程（简化：只考虑惯性力）
    F = rho * np.pi * 0.5**2 * du_dt  # 假设直径1m
    
    return F
```

### 4.2 装置运动仿真

```python
import numpy as np
from scipy.integrate import odeint

def device_dynamics(y, t, A, k, h, m, c, k_spring, rho=1025, g=9.81):
    """
    装置运动微分方程
    
    Parameters
    ----------
    y : array
        [位置, 速度]
    t : float
        时间
    A, k, h : float
        波浪参数
    m, c, k_spring : float
        装置参数
    
    Returns
    -------
    dydt : array
        [速度, 加速度]
    """
    x, v = y
    
    # 波浪力
    F_wave = wave_force(A, k, h, 0, t, rho, g)
    
    # 运动方程: m*a + c*v + k*x = F_wave
    a = (F_wave - c * v - k_spring * x) / m
    
    return [v, a]

def simulate_device(A, k, h, m, c, k_spring, T_sim=10, dt=0.01):
    """
    仿真装置运动
    """
    t = np.arange(0, T_sim, dt)
    y0 = [0, 0]  # 初始状态：静止
    
    # 求解微分方程
    solution = odeint(device_dynamics, y0, t, args=(A, k, h, m, c, k_spring))
    
    x = solution[:, 0]  # 位置
    v = solution[:, 1]  # 速度
    
    # 计算功率
    omega = np.sqrt(9.81 * k * np.tanh(k * h))
    F_wave = A * 9.81 * k * np.cosh(k * (0 + h)) / np.sinh(k * h) * np.cos(-omega * t)
    P = F_wave * v  # 瞬时功率
    
    return t, x, v, P
```

### 4.3 参数优化

```python
from scipy.optimize import differential_evolution
import numpy as np

def optimize_device(A, k, h, m_range, c_range, k_range):
    """
    优化装置参数以最大化功率
    
    Parameters
    ----------
    A, k, h : float
        波浪条件
    m_range, c_range, k_range : tuple
        参数范围 (min, max)
    
    Returns
    -------
    best_params : dict
        最优参数
    best_power : float
        最大平均功率
    """
    def objective(params):
        m, c, k_spring = params
        
        # 仿真
        t, x, v, P = simulate_device(A, k, h, m, c, k_spring, T_sim=20)
        
        # 计算平均功率（取后半段稳态）
        P_avg = np.mean(P[len(P)//2:])
        
        # 返回负值（因为differential_evolution是最小化）
        return -P_avg
    
    # 参数边界
    bounds = [m_range, c_range, k_range]
    
    # 优化
    result = differential_evolution(
        objective, 
        bounds, 
        seed=42,
        maxiter=100,
        tol=1e-6
    )
    
    best_params = {
        'mass': result.x[0],
        'damping': result.x[1],
        'stiffness': result.x[2]
    }
    best_power = -result.fun
    
    return best_params, best_power
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 忽略波浪相位 | 功率计算错误 | 考虑波浪与装置运动的相位差 |
| 边界条件错误 | 优化结果非物理 | 严格设置参数边界 |
| 简化过度 | 模型精度不足 | 保留关键物理机制 |
| 未考虑阻尼 | 功率估计偏高 | 合理设置阻尼系数 |
| 忽略非线性 | 失真 | 在大振幅时考虑非线性效应 |
| 单位不一致 | 计算错误 | 统一使用SI单位制 |

---

## 6. 验证方法

### 6.1 解析验证
- 在简单条件下（如线性波、小振幅），与解析解对比
- 检查能量守恒：输入功率 ≈ 输出功率 + 耗散功率

### 6.2 基准测试
- 与已知实验数据对比
- 与商业软件（如WAMIT、ANSYS）结果对比

### 6.3 灵敏度分析
- 改变波浪条件，观察功率变化是否合理
- 改变装置参数，观察优化结果是否稳定

### 6.4 物理合理性检查
- 功率数量级是否合理（kW-MW级别）
- 效率是否在合理范围（<100%）
- 运动幅度是否在物理限制内

---

## 7. 参考论文

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| A001 | 遗传算法优化 | 多目标加权+灵敏度分析 |
| A022 | 功率最大化模型 | 装置参数优化 |
| A171 | 解析+数值方法 | 多种求解方法对比 |

---

## 8. 代码模板参考

- 优化算法模板: `resources/code-templates/optimization/genetic_algorithm.py`
- 数值积分: `scipy.integrate.odeint` 或 `solve_ivp`
- 参数优化: `scipy.optimize.differential_evolution`

---

## 9. 验证清单

- [ ] 波浪参数（波高、周期、水深）单位正确
- [ ] 色散关系满足 ω² = gk tanh(kh)
- [ ] 运动方程包含惯性项、阻尼项、弹簧项
- [ ] 功率计算考虑了波浪力与速度的相位关系
- [ ] 优化边界设置合理（物理可行域）
- [ ] 灵敏度分析已执行
- [ ] 结果数量级与物理直觉一致
