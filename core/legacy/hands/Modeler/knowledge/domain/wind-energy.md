# 风电场优化建模知识库

> 本文件提供数学建模竞赛中风电场优化相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 风资源评估与风速预测
- 风机选型与布局优化
- 风电场发电量估算
- 维护调度优化
- 尾流效应分析

### 1.2 常见约束条件
- 风机间距限制（通常≥3D，D为风轮直径）
- 地形约束（坡度、障碍物）
- 噪声限制
- 投资预算限制
- 电网接入容量

### 1.3 数据特点
- 风速数据：时序数据、概率分布
- 风向数据：玫瑰图
- 地形数据：DEM高程
- 风机参数：功率曲线、推力系数
- 经济数据：电价、维护成本

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| Weibull分布 | 风速统计建模 | 拟合效果好 | 需要足够数据 |
| 功率曲线拟合 | 发电量计算 | 物理意义明确 | 对风速敏感 |
| 尾流模型（Jensen） | 布局优化 | 计算简单 | 精度有限 |
| 双目标优化 | 经济性与技术平衡 | 多目标决策 | Pareto前沿复杂 |
| 遗传算法 | 布局优化 | 全局搜索 | 收敛慢 |
| 蒙特卡洛模拟 | 不确定性分析 | 量化风险 | 计算量大 |

---

## 3. 数学基础

### 3.1 Weibull分布

**概率密度函数**：
```
f(v) = (k/c) * (v/c)^(k-1) * exp(-(v/c)^k)
```
其中：
- v: 风速 (m/s)
- k: 形状参数 (无量纲)
- c: 尺度参数 (m/s)

**累积分布函数**：
```
F(v) = 1 - exp(-(v/c)^k)
```

**平均风速**：
```
v_mean = c * Γ(1 + 1/k)
```

**风能密度**：
```
WED = 0.5 * ρ * ∫₀^∞ v³ * f(v) dv = 0.5 * ρ * c³ * Γ(1 + 3/k)
```

### 3.2 功率曲线

**风力发电机功率模型**：
```
P(v) = 0.5 * ρ * A * Cp * v³  (v_in ≤ v ≤ v_rated)
P(v) = P_rated  (v_rated ≤ v ≤ v_out)
P(v) = 0  (v < v_in 或 v > v_out)
```
其中：
- ρ: 空气密度 (kg/m³)
- A: 风轮扫掠面积 (m²)
- Cp: 功率系数 (理论最大值=16/27≈0.593)
- v_in: 切入风速
- v_rated: 额定风速
- v_out: 切出风速

### 3.3 尾流模型

**Jensen尾流模型**：
```
v_wake = v_0 * (1 - 2a / (1 + α * x/r_0)²)
```
其中：
- v_0: 自由来流风速
- a: 轴向诱导因子
- x: 下游距离
- α: 尾流扩展系数 (~0.075)
- r_0: 风轮半径

**尾流重叠**：
```
v_eff = v_0 * (1 - Σ Δv_i)
```

### 3.4 年发电量

**年发电量 (AEP)**：
```
AEP = T * ∫₀^∞ P(v) * f(v) dv
```
其中 T 为年小时数 (8760h)。

---

## 4. Python实现

### 4.1 Weibull分布拟合

```python
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

def weibull_pdf(v, k, c):
    """Weibull概率密度函数"""
    return (k / c) * (v / c)**(k - 1) * np.exp(-(v / c)**k)

def weibull_cdf(v, k, c):
    """Weibull累积分布函数"""
    return 1 - np.exp(-(v / c)**k)

def fit_weibull(wind_speeds):
    """
    拟合Weibull分布
    
    Parameters
    ----------
    wind_speeds : ndarray
        风速数据
    
    Returns
    -------
    k, c : float
        形状参数和尺度参数
    """
    # 方法1: 使用scipy
    k_scipy, loc, c_scipy = stats.weibull_min.fit(wind_speeds, floc=0)
    
    # 方法2: 矩估计
    v_mean = np.mean(wind_speeds)
    v_std = np.std(wind_speeds)
    
    # 近似公式
    k_est = (v_std / v_mean)**(-1.086)
    c_est = v_mean / stats.gamma(1 + 1/k_est)
    
    return k_scipy, c_scipy

def wind_resource_analysis(wind_speeds, wind_directions=None):
    """
    风资源分析
    
    Returns
    -------
    analysis : dict
        包含Weibull参数、风能密度等
    """
    k, c = fit_weibull(wind_speeds)
    
    v_mean = c * stats.gamma(1 + 1/k)
    v_std = np.sqrt(c**2 * (stats.gamma(1 + 2/k) - 
                            stats.gamma(1 + 1/k)**2))
    
    # 风能密度 (假设空气密度1.225 kg/m³)
    rho = 1.225
    wed = 0.5 * rho * c**3 * stats.gamma(1 + 3/k)
    
    # 有效风速范围 (3-25 m/s) 的能量占比
    v_in, v_out = 3, 25
    energy_fraction = weibull_cdf(v_out, k, c) - weibull_cdf(v_in, k, c)
    
    return {
        'k': k,
        'c': c,
        'v_mean': v_mean,
        'v_std': v_std,
        'wind_energy_density': wed,
        'energy_fraction': energy_fraction
    }
```

### 4.2 功率曲线与发电量计算

```python
import numpy as np
from scipy.integrate import quad

class WindTurbine:
    """风力发电机模型"""
    
    def __init__(self, rotor_diameter, hub_height, 
                 v_in=3, v_rated=12, v_out=25, 
                 P_rated=2000, Cp=0.45):
        """
        Parameters
        ----------
        rotor_diameter : float
            风轮直径 (m)
        hub_height : float
            轮毂高度 (m)
        v_in, v_rated, v_out : float
            切入、额定、切出风速 (m/s)
        P_rated : float
            额定功率 (kW)
        Cp : float
            功率系数
        """
        self.D = rotor_diameter
        self.H = hub_height
        self.v_in = v_in
        self.v_rated = v_rated
        self.v_out = v_out
        self.P_rated = P_rated
        self.Cp = Cp
        
        self.A = np.pi * (rotor_diameter / 2)**2
        self.rho = 1.225  # 空气密度
    
    def power_curve(self, v):
        """功率曲线"""
        if v < self.v_in or v > self.v_out:
            return 0
        elif v < self.v_rated:
            # 立方关系
            P = 0.5 * self.rho * self.A * self.Cp * v**3
            return min(P, self.P_rated)
        else:
            return self.P_rated
    
    def power_curve_array(self, v_array):
        """向量化功率曲线"""
        return np.array([self.power_curve(v) for v in v_array])
    
    def thrust_coefficient(self, v):
        """推力系数"""
        if v < self.v_in or v > self.v_out:
            return 0
        elif v < self.v_rated:
            return 0.8  # 简化模型
        else:
            return 0.8 * (self.v_rated / v)**2
    
    def annual_energy_production(self, k, c):
        """
        计算年发电量
        
        Parameters
        ----------
        k, c : float
            Weibull参数
        
        Returns
        -------
        aep : float
            年发电量 (kWh)
        """
        def integrand(v):
            return self.power_curve(v) * weibull_pdf(v, k, c)
        
        aep, _ = quad(integrand, 0, 50)
        aep *= 8760  # 年小时数
        
        return aep
```

### 4.3 尾流效应模型

```python
import numpy as np

class JensenWakeModel:
    """Jensen尾流模型"""
    
    def __init__(self, rotor_diameter, ct=0.8, alpha=0.075):
        """
        Parameters
        ----------
        rotor_diameter : float
            风轮直径 (m)
        ct : float
            推力系数
        alpha : float
            尾流扩展系数
        """
        self.D = rotor_diameter
        self.r0 = rotor_diameter / 2
        self.ct = ct
        self.alpha = alpha
    
    def wake_velocity(self, v0, x):
        """
        计算尾流区风速
        
        Parameters
        ----------
        v0 : float
            自由来流风速 (m/s)
        x : float
            下游距离 (m)
        
        Returns
        -------
        v_wake : float
            尾流区风速 (m/s)
        """
        # 轴向诱导因子
        a = 0.5 * (1 - np.sqrt(1 - self.ct))
        
        # 尾流半径
        r_wake = self.r0 + self.alpha * x
        
        # 风速亏损
        delta_v = 2 * a * v0 * (self.r0 / r_wake)**2
        
        return v0 - delta_v
    
    def wake_overlap(self, x, y, turbine_positions):
        """
        计算尾流重叠面积
        
        Parameters
        ----------
        x, y : float
            下游风机位置
        turbine_positions : ndarray
            上游风机位置
        
        Returns
        -------
        overlap_ratio : float
            重叠比例
        """
        # 简化：假设圆形尾流
        r_wake = self.r0 + self.alpha * np.abs(x - turbine_positions[:, 0])
        
        # 计算距离
        distances = np.sqrt((x - turbine_positions[:, 0])**2 + 
                           (y - turbine_positions[:, 1])**2)
        
        # 重叠判断
        overlap = distances < (r_wake + self.r0)
        
        return np.sum(overlap)
    
    def effective_wind_speed(self, v0, x, y, turbine_positions):
        """
        计算有效风速（考虑尾流叠加）
        
        Parameters
        ----------
        v0 : float
            自由来流风速 (m/s)
        x, y : float
            风机位置
        turbine_positions : ndarray
            上游风机位置
        
        Returns
        -------
        v_eff : float
            有效风速 (m/s)
        """
        # 找出上游风机
        upstream = turbine_positions[turbine_positions[:, 0] < x]
        
        if len(upstream) == 0:
            return v0
        
        # 计算尾流影响
        v_deficit = 0
        for turbine in upstream:
            dx = x - turbine[0]
            v_wake = self.wake_velocity(v0, dx)
            v_deficit += (v0 - v_wake)
        
        return max(v0 - v_deficit, 0.3 * v0)  # 最小风速限制
```

### 4.4 风机布局优化

```python
import numpy as np
from scipy.optimize import differential_evolution

def optimize_wind_farm_layout(n_turbines, wind_resource, 
                               turbine_params, boundaries):
    """
    风机布局优化
    
    Parameters
    ----------
    n_turbines : int
        风机数量
    wind_resource : dict
        风资源参数 {k, c, direction_prob}
    turbine_params : WindTurbine
        风机参数
    boundaries : ndarray
        场地边界 [(x_min, x_max), (y_min, y_max)]
    
    Returns
    -------
    best_layout : ndarray
        最优布局
    best_aep : float
        最大年发电量
    """
    def objective(positions):
        """目标函数：负的年发电量（最小化）"""
        positions = positions.reshape(n_turbines, 2)
        
        total_aep = 0
        for i in range(n_turbines):
            # 计算有效风速
            v_eff = JensenWakeModel(turbine_params.D).effective_wind_speed(
                8.0,  # 假设自由来流风速8m/s
                positions[i, 0], positions[i, 1],
                positions[:i]
            )
            
            # 计算单机发电量
            aep = turbine_params.annual_energy_production(
                wind_resource['k'], wind_resource['c']
            )
            
            # 尾流损失修正
            wake_loss = 1 - (v_eff / 8.0)**3
            aep *= (1 - wake_loss)
            
            total_aep += aep
        
        return -total_aep
    
    # 约束：风机间距≥3D
    min_spacing = 3 * turbine_params.D
    
    def constraint_spacing(positions):
        """间距约束"""
        positions = positions.reshape(n_turbines, 2)
        for i in range(n_turbines):
            for j in range(i+1, n_turbines):
                dist = np.sqrt(np.sum((positions[i] - positions[j])**2))
                if dist < min_spacing:
                    return min_spacing - dist
        return 0
    
    # 变量边界
    bounds = [(boundaries[0][0], boundaries[0][1]),
              (boundaries[1][0], boundaries[1][1])] * n_turbines
    
    # 优化
    result = differential_evolution(
        objective, bounds,
        constraints={'type': 'ineq', 'fun': constraint_spacing},
        seed=42, maxiter=100, tol=1e-6
    )
    
    best_layout = result.x.reshape(n_turbines, 2)
    best_aep = -result.fun
    
    return best_layout, best_aep
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| Weibull参数估计不准 | 发电量偏差大 | 使用最大似然估计 |
| 忽略尾流效应 | 发电量高估 | 引入尾流模型 |
| 功率曲线简化过度 | 误差大 | 使用实测功率曲线 |
| 未考虑空气密度变化 | 结果偏差 | 根据海拔和温度修正 |
| 忽略风机间距约束 | 实际不可行 | 加入最小间距约束 |
| 风向处理不当 | 布局不合理 | 使用风向玫瑰图加权 |

---

## 6. 验证方法

### 6.1 Weibull分布验证
- 与历史数据K-S检验
- 检查参数合理性（k=1.5~3, c=5~15）

### 6.2 发电量验证
- 与同类型风电场数据对比
- 检查容量因子合理性（20%-50%）

### 6.3 布局验证
- 检查风机间距≥3D
- 验证尾流损失合理（10%-20%）

### 6.4 经济性验证
- 检查度电成本合理性
- 验证投资回收期

---

## 7. 真题案例

### 7.1 2016D 风电场运行优化

**题目要点**：
- 风电场风机选型
- 布局优化以最大化发电量
- 考虑尾流效应和经济性

**解题思路**：
1. 收集风资源数据（风速、风向）
2. 拟合Weibull分布
3. 选择合适机型
4. 使用优化算法布局
5. 计算发电量和经济效益

**关键公式**：
```
Weibull分布: f(v) = (k/c)(v/c)^(k-1)exp(-(v/c)^k)
年发电量: AEP = 8760 * ∫P(v)f(v)dv
尾流模型: v_wake = v0(1-2a/(1+αx/r0)²)
```

**参考答案**：
- 风机数量：约50-100台
- 间距：≥3D（约300-400m）
- 年发电量：约200-400GWh
- 容量因子：约25%-35%

---

## 8. 验证清单

- [ ] Weibull参数估计准确（k、c）
- [ ] 功率曲线与机型匹配
- [ ] 尾流效应已考虑
- [ ] 风机间距≥3D
- [ ] 年发电量计算正确
- [ ] 容量因子在合理范围（20%-50%）
- [ ] 经济性指标合理
