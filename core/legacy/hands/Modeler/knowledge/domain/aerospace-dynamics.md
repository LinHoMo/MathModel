# 航天动力学建模知识库

> 本文件提供数学建模竞赛中航天动力学相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 嫦娥三号软着陆轨道设计与控制策略
- 弹道导弹轨迹优化与突防策略
- 航天器轨道转移（霍曼转移、双椭圆转移）
- 卫星星座设计与覆盖优化
- 空间交会对接轨道规划
- 轨道摄动分析与预报

### 1.2 常见约束条件
- 动力约束：发动机推力上限、燃料总量限制
- 轨道约束：近月点/远月点高度、轨道倾角
- 着陆约束：着陆速度、着陆角度、避障要求
- 时间约束：飞行时间窗口、通信链路约束
- 能源约束：太阳能帆板供电、蓄电池容量
- 安全约束：轨道碰撞规避、热防护

### 1.3 数据特点
- 初始状态：位置矢量、速度矢量、质量
- 轨道参数：半长轴、偏心率、倾角、升交点赤经
- 环境参数：天体引力场、大气密度、太阳光压
- 控制量：推力方向、推力大小、发动机开关序列
- 测量数据：测距、测速、角度观测

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 龙格-库塔法(ODE) | 轨道数值积分 | 精度高、稳定性好 | 计算量较大 |
| 遗传算法+模拟退火 | 轨道优化 | 全局搜索能力强 | 收敛速度慢 |
| 蒙特卡洛仿真 | 不确定性分析 | 处理随机因素 | 需要大量样本 |
| 庞特里亚金极大值原理 | 最优控制 | 理论最优解 | 求解复杂 |
| 逐步线性化(STM) | 轨道预报 | 计算效率高 | 局部线性化近似 |
| 打靶法 | 边值问题 | 处理两点边值 | 对初值敏感 |

---

## 3. 数学基础

### 3.1 二体问题动力学方程

**牛顿第二定律 + 万有引力**：
```
m * d²r/dt² = -G * M * m / |r|³ * r
```

化简为状态空间形式：
```
dr/dt = v
dv/dt = -μ * r / |r|³
```
其中 μ = GM 为引力常数（月球 μ ≈ 4902.8 km³/s²）

### 3.2 开普勒轨道要素

```
a: 半长轴 (描述轨道大小)
e: 偏心率 (描述轨道形状, 0为圆, 0-1为椭圆)
i: 轨道倾角 (轨道面与参考面夹角)
Ω: 升交点赤经 (轨道面与参考面交线方位)
ω: 近心点幅角 (轨道面内近心点方位)
ν: 真近点角 (航天器在轨道上的位置)
```

**轨道周期**：
```
T = 2π * √(a³/μ)
```

### 3.3 轨道转移

**霍曼转移**（共面圆轨道间最省燃料）：
```
转移轨道半长轴: a_t = (r₁ + r₂) / 2
速度增量: Δv₁ = √(μ/r₁) * (√(2r₂/(r₁+r₂)) - 1)
         Δv₂ = √(μ/r₂) * (1 - √(2r₁/(r₁+r₂)))
总 Δv = Δv₁ + Δv₂
```

### 3.4 软着陆动力学（嫦娥三号模型）

**极坐标系下的运动方程**：
```
径向: m(d²r/dt² - rθ̇²) = T*sin(α) - G*M*m/r²
切向: m(rθ̇² + 2ṙθ̇) = T*cos(α)
质量: dm/dt = -T / (Isp * g₀)
```
其中 T 为推力，α 为推力方向角，Isp 为比冲

---

## 4. Python实现

### 4.1 轨道数值积分（RK4）

```python
import numpy as np

def gravitational_acceleration(r, mu=4902.8):
    """
    计算万有引力加速度（月球）
    
    Parameters
    ----------
    r : array
        位置矢量 [x, y, z] (km)
    mu : float
        引力常数 (km³/s²)
    
    Returns
    -------
    a : array
        加速度矢量 (km/s²)
    """
    r_mag = np.linalg.norm(r)
    a = -mu * r / r_mag**3
    return a

def rk4_step(state, dt, mu=4902.8):
    """
    四阶龙格-库塔法单步积分
    
    Parameters
    ----------
    state : array
        状态 [x, y, z, vx, vy, vz]
    dt : float
        时间步长 (s)
    
    Returns
    -------
    new_state : array
        新状态
    """
    r = state[:3]
    v = state[3:]
    
    # k1
    k1_v = gravitational_acceleration(r, mu)
    k1_r = v
    
    # k2
    k2_v = gravitational_acceleration(r + 0.5*dt*k1_r, mu)
    k2_r = v + 0.5*dt*k1_v
    
    # k3
    k3_v = gravitational_acceleration(r + 0.5*dt*k2_r, mu)
    k3_r = v + 0.5*dt*k2_v
    
    # k4
    k4_v = gravitational_acceleration(r + dt*k3_r, mu)
    k4_r = v + dt*k3_v
    
    new_r = r + (dt/6) * (k1_r + 2*k2_r + 2*k3_r + k4_r)
    new_v = v + (dt/6) * (k1_v + 2*k2_v + 2*k3_v + k4_v)
    
    return np.concatenate([new_r, new_v])

def propagate_orbit(state0, t_span, dt=1.0, mu=4902.8):
    """
    轨道传播
    
    Parameters
    ----------
    state0 : array
        初始状态 [x, y, z, vx, vy, vz]
    t_span : tuple
        (t_start, t_end) 时间范围 (s)
    dt : float
        时间步长 (s)
    
    Returns
    -------
    states : array
        各时刻状态
    times : array
        时间序列
    """
    t_start, t_end = t_span
    times = np.arange(t_start, t_end, dt)
    states = np.zeros((len(times), 6))
    
    states[0] = state0
    for i in range(1, len(times)):
        states[i] = rk4_step(states[i-1], dt, mu)
    
    return states, times
```

### 4.2 软着陆优化（遗传算法+模拟退火）

```python
import numpy as np
from scipy.optimize import differential_evolution

def soft_landing_dynamics(params, t_points, mu=4902.8, Isp=3000, g0=9.81):
    """
    计算软着陆轨迹
    
    Parameters
    ----------
    params : array
        控制参数序列 [α₁, α₂, ..., αₙ, T₁, T₂, ..., Tₙ]
    t_points : array
        时间节点
    
    Returns
    -------
    final_state : array
        最终状态
    cost : float
        燃料消耗
    """
    n = len(t_points) - 1
    alpha = params[:n]  # 推力方向角
    thrust = params[n:2*n]  # 推力大小
    
    # 初始状态 (环月轨道15km)
    r0 = np.array([1738 + 15, 0, 0])  # km
    v0 = np.array([0, 1.63, 0])  # km/s
    m0 = 2400  # kg
    
    state = np.concatenate([r0, v0])
    mass = m0
    
    for i in range(n):
        dt = t_points[i+1] - t_points[i]
        T = thrust[i] * 1000  # 转换为N
        
        # 计算加速度
        r = state[:3]
        v = state[3:]
        r_mag = np.linalg.norm(r)
        
        # 引力加速度
        a_grav = -mu * r / r_mag**3
        
        # 推力加速度 (推力方向)
        alpha_i = alpha[i]
        a_thrust = (T / mass) * np.array([np.sin(alpha_i), np.cos(alpha_i), 0]) / 1000  # km/s²
        
        # 总加速度
        a_total = a_grav + a_thrust
        
        # RK4积分
        k1_v = a_total
        k1_r = v
        k2_v = a_total
        k2_r = v + 0.5*dt*k1_v
        k3_v = a_total
        k3_r = v + 0.5*dt*k2_v
        k4_v = a_total
        k4_r = v + dt*k3_v
        
        state[:3] += (dt/6) * (k1_r + 2*k2_r + 2*k3_r + k4_r)
        state[3:] += (dt/6) * (k1_v + 2*k2_v + 2*k3_v + k4_v)
        
        # 质量消耗
        mass -= T * dt / (Isp * g0)
    
    return state, m0 - mass

def optimize_soft_landing():
    """
    优化软着陆轨迹：最小化燃料消耗
    """
    n_points = 20
    t_points = np.linspace(0, 800, n_points + 1)  # 800s着陆
    
    def objective(params):
        final_state, fuel = soft_landing_dynamics(params, t_points)
        
        # 着陆约束惩罚
        r_final = np.linalg.norm(final_state[:3]) - 1738  # 高度
        v_final = np.linalg.norm(final_state[3:])  # 速度
        
        penalty = 0
        penalty += 1000 * max(0, r_final - 0.1)  # 高度约束
        penalty += 1000 * max(0, v_final - 0.01)  # 速度约束
        
        return fuel + penalty
    
    # 参数边界
    bounds = [(0, np.pi/2)] * n_points + [(0, 4000)] * n_points  # 角度0-90°, 推力0-4000N
    
    result = differential_evolution(
        objective, bounds, seed=42,
        maxiter=200, tol=1e-6, popsize=20
    )
    
    return result.x, result.fun
```

### 4.3 蒙特卡洛仿真

```python
import numpy as np

def monte_carlo_orbit(state0, t_span, dt, n_samples=1000, 
                      position_noise=0.1, velocity_noise=0.001):
    """
    蒙特卡洛轨道仿真（考虑初始状态不确定性）
    
    Parameters
    ----------
    state0 : array
        标称初始状态
    t_span : tuple
        时间范围
    dt : float
        时间步长
    n_samples : int
        采样次数
    position_noise, velocity_noise : float
        噪声标准差
    
    Returns
    -------
    mean_states : array
        平均轨道
    std_states : array
        轨道标准差
    """
    all_states = []
    
    for _ in range(n_samples):
        # 添加随机扰动
        noise = np.concatenate([
            np.random.normal(0, position_noise, 3),
            np.random.normal(0, velocity_noise, 3)
        ])
        perturbed_state = state0 + noise
        
        # 轨道传播
        states, times = propagate_orbit(perturbed_state, t_span, dt)
        all_states.append(states)
    
    all_states = np.array(all_states)
    mean_states = np.mean(all_states, axis=0)
    std_states = np.std(all_states, axis=0)
    
    return mean_states, std_states
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 单位不一致 | 轨道高度/速度错误 | 统一使用km/s或m/s，注意km与m转换 |
| 引力常数错误 | 轨道周期偏差 | 明确使用哪个天体的μ值 |
| 推力方向定义混乱 | 控制效果相反 | 固定坐标系定义，推力方向与速度方向夹角 |
| 积分步长过大 | 轨道不闭合 | 步长取轨道周期的1/100以上 |
| 忽略摄动因素 | 长期预报偏差 | 根据精度需求考虑J2、大气阻力等 |
| 燃料质量变化未更新 | 推力加速度错误 | 实时更新航天器质量 |
| 边界条件遗漏 | 着陆失败 | 严格约束终端状态 |

---

## 6. 验证方法

### 6.1 轨道闭合性验证
- 圆轨道：检查半径是否恒定
- 椭圆轨道：检查能量是否守恒
- 霍曼转移：计算的Δv与理论值对比

### 6.2 量纲分析
- 引力加速度单位：km/s²
- 速度增量单位：km/s 或 m/s
- 燃料消耗单位：kg

### 6.3 物理合理性检查
- 着陆速度应小于安全阈值（<3 m/s）
- 轨道倾角应在合理范围（0-180°）
- 燃料消耗不应超过总质量

### 6.4 能量守恒验证
```
机械能 E = v²/2 - μ/r = 常数（无推力段）
```

---

## 7. 真题案例

### 案例1：2014A 嫦娥三号软着陆轨道设计与控制策略

**问题核心**：设计从15km环月轨道到月面着陆的最优轨迹

**建模要点**：
1. 建立极坐标系下的动力学方程
2. 将推力方向和大小作为控制变量
3. 以燃料消耗最小为目标函数
4. 约束：着陆点位置、着陆速度、避障

**典型解法**：
```
1. 将连续控制离散化为分段常值
2. 采用遗传算法+序列二次规划(SQP)混合优化
3. 蒙特卡洛分析初始偏差对轨迹的影响
4. 设计制导律（如显式制导、解析制导）
```

**关键结果**：
- 总飞行时间约720-800s
- 燃料消耗约600-800kg
- 着陆速度 < 3 m/s
- 着陆点精度 < 100m

### 案例2：弹道优化与突防策略

**问题核心**：在敌方拦截下实现有效突防

**建模要点**：
1. 弹道导弹飞行段划分（主动段、自由飞行段、再入段）
2. 拦截概率模型
3. 多弹头/诱饵分配策略
4. 突防概率最大化

---

## 8. 代码模板参考

- ODE求解: `scipy.integrate.solve_ivp`
- 优化算法: `scipy.optimize.differential_evolution`
- 随机采样: `numpy.random`
- 数值积分: 自定义RK4或 `scipy.integrate.odeint`

---

## 9. 验证清单

- [ ] 引力常数μ取值正确（月球/地球）
- [ ] 轨道要素物理意义正确
- [ ] 控制变量范围合理
- [ ] 着陆约束（速度、高度）已包含
- [ ] 燃料消耗计算正确
- [ ] 坐标系定义清晰一致
- [ ] 数值积分精度满足要求
- [ ] 结果与物理直觉一致

---

## 10. 参考文献

1. 王之. 航天器轨道力学. 国防工业出版社, 2018.
2. Bate R R. Fundamentals of Astrodynamics. Dover, 2010.
3. 崔乃刚. 航天器最优控制. 哈尔滨工业大学出版社, 2015.
4. Curtis H D. Orbital Mechanics for Engineering Students. Butterworth-Heinemann, 2013.
