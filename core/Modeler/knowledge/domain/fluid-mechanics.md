# 流体力学与压力控制领域知识

## 一、核心概念

### 1.1 流体力学基础
- **连续性方程**: 质量守恒
- **纳维-斯托克斯方程**: 动量守恒
- **伯努利方程**: 能量守恒（理想流体）

### 1.2 关键参数
| 参数 | 符号 | 单位 | 说明 |
|------|------|------|------|
| 压力 | p | Pa | 单位面积力 |
| 流速 | v | m/s | 流体速度 |
| 流量 | Q | m³/s | 单位时间体积 |
| 粘度 | μ | Pa·s | 流体粘性 |

### 1.3 常用公式
```
连续性方程: A1*v1 = A2*v2
伯努利方程: p1 + 0.5*ρ*v1² + ρ*g*h1 = p2 + 0.5*ρ*v2² + ρ*g*h2
达西-魏斯巴赫: Δf = λ*(L/D)*(ρ*v²/2)
```

---

## 二、高压油管模型

### 2.1 问题描述
- 高压油管内燃油压力控制
- 通过高压油泵和喷油嘴调节
- 压力波动需要稳定

### 2.2 数学模型
**压力变化率**:
```
dp/dt = (β/V) * (Q_in - Q_out)
β: 燃油体积模量
V: 油管容积
Q_in: 进油流量
Q_out: 出油流量
```

**流量计算**:
```
Q = C_d * A * sqrt(2*Δp/ρ)
C_d: 流量系数
A: 截面积
Δp: 压差
ρ: 燃油密度
```

### 2.3 Python实现
```python
import numpy as np
from scipy.integrate import odeint

def pressure_dynamics(y, t, params):
    """
    高压油管压力动力学
    y: [压力]
    t: 时间
    params: 系统参数
    """
    p = y[0]
    beta = params['beta']  # 体积模量
    V = params['volume']   # 油管容积
    Q_in = params['Q_in'](t)   # 进油流量
    Q_out = params['Q_out'](p)  # 出油流量
    
    dpdt = (beta / V) * (Q_in - Q_out)
    return [dpdt]

def solve_pressure_control():
    """
    求解压力控制问题
    """
    params = {
        'beta': 1.5e9,  # 体积模量 (Pa)
        'volume': 1e-4,  # 油管容积 (m³)
        'Q_in': lambda t: 1e-5 if t % 0.01 < 0.005 else 0,  # 周期性进油
        'Q_out': lambda p: 1e-6 * np.sqrt(max(p - 1e5, 0))  # 出油
    }
    
    t = np.linspace(0, 1, 1000)
    y0 = [1e5]  # 初始压力
    
    solution = odeint(pressure_dynamics, y0, t, args=(params,))
    
    return t, solution
```

---

## 三、ODE求解方法

### 3.1 数值方法
- **欧拉法**: 一阶精度
- **龙格-库塔法**: 四阶精度
- **Adams法**: 多步法

### 3.2 scipy求解
```python
from scipy.integrate import solve_ivp

def solve_ode():
    """
    使用scipy求解ODE
    """
    def func(t, y):
        return [y[0] * (1 - y[0])]
    
    sol = solve_ivp(func, [0, 10], [0.1], max_step=0.1)
    return sol.t, sol.y
```

### 3.3 刚性问题
```python
def solve_stiff_ode():
    """
    求解刚性ODE
    """
    def func(t, y):
        return [-1000 * y[0] + 1]
    
    # 使用刚性求解器
    sol = solve_ivp(func, [0, 1], [0], method='BDF')
    return sol.t, sol.y
```

---

## 四、压力控制策略

### 4.1 PID控制
```python
def pid_controller(error, integral, derivative, Kp, Ki, Kd):
    """
    PID控制器
    """
    output = Kp * error + Ki * integral + Kd * derivative
    return output
```

### 4.2 最优控制
```
min J = ∫(x^T Q x + u^T R u) dt
s.t. dx/dt = Ax + Bu
     x(0) = x0
```

### 4.3 模型预测控制（MPC）
```python
def mpc_control(model, x0, horizon):
    """
    模型预测控制
    """
    from scipy.optimize import minimize
    
    def objective(u):
        cost = 0
        x = x0
        for k in range(horizon):
            x = model(x, u[k])
            cost += x.T @ Q @ x + u[k] @ R @ u[k]
        return cost
    
    u0 = np.zeros(horizon)
    result = minimize(objective, u0, method='SLSQP')
    return result.x
```

---

## 五、论文写作要点

### 5.1 问题分析框架
1. **物理机理**: 流体力学方程
2. **参数确定**: 材料参数、几何参数
3. **数值求解**: ODE求解方法
4. **控制策略**: PID、最优控制
5. **结果分析**: 压力曲线、稳定性
6. **灵敏度分析**: 参数影响

### 5.2 图表规范
- **压力曲线**: 时间序列
- **相图**: 状态空间
- **控制信号**: 输入输出
- **误差分析**: 误差曲线

### 5.3 LaTeX代码
```latex
\begin{equation}
\frac{dp}{dt} = \frac{\beta}{V}(Q_{in} - Q_{out})
\label{eq:pressure}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{pressure_control.pdf}
\caption{压力控制结果}
\label{fig:pressure}
\end{figure}
```

---

## 六、参考文献

1. 周光坰. 流体力学. 高等教育出版社, 2000.
2. Anderson J D. Computational Fluid Dynamics. McGraw-Hill, 1995.
3. 王福军. 流体机械内部流场数值模拟. 机械工业出版社, 2011.
4. Dorf R C. Modern Control Systems. Pearson, 2012.
