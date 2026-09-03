# Playbook: MCM A 连续/机理建模（物理系统）

> **题型**: MCM A 题 — 连续系统 + ODE/PDE + 优化
> **核心方法**: 微分方程建模 + 数值求解 + 参数优化
> **难度**: ★★★★★（物理建模 + 数学推导）

---

## 1. 问题拆解

```json
{
  "problem": "MCM A 连续系统建模（典型：物理/生物系统）",
  "sub_questions": [
    {"id": "Q1", "desc": "建立物理/生物系统的微分方程模型", "type": "ode_pde", "depends_on": []},
    {"id": "Q2", "desc": "数值求解并分析系统动态行为", "type": "simulation", "depends_on": ["Q1"]},
    {"id": "Q3", "desc": "参数敏感性分析与稳定性判定", "type": "sensitivity", "depends_on": ["Q2"]},
    {"id": "Q4", "desc": "优化控制策略使系统达到目标状态", "type": "optimal_control", "depends_on": ["Q2", "Q3"]}
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **MCM A**（连续/机理） |
| 核心建模 | ODE/PDE + 动力系统 |
| 求解类型 | 数值求解 + 优化 |
| 方法方向 | 微分方程 + 相平面 + 最优控制 |

## 3. 候选模型对比

| 方法 | 适用场景 | 推荐度 |
|------|---------|--------|
| **ODE 系统 + RK45** | 集总参数动态系统 | ★★★★★ |
| PDE + 有限差分 | 分布参数系统 | ★★★★☆ |
| 系统动力学 | 宏观反馈系统 | ★★★☆☆ |
| Agent-Based | 异质个体交互 | ★★★☆☆ |

## 4. 模型建立

### 4.1 典型 ODE 系统（以 SIR 传染病为例）
$$\frac{dS}{dt} = -\beta S I$$
$$\frac{dI}{dt} = \beta S I - \gamma I$$
$$\frac{dR}{dt} = \gamma I$$

### 4.2 基本再生数
$$R_0 = \frac{\beta}{\gamma}$$

### 4.3 最优控制
$$\min_{u(t)} \int_0^T [I(t) + c \cdot u(t)^2] dt$$
$$\text{s.t.} \quad \frac{dS}{dt} = -(1-u)\beta S I$$

## 5. 代码实现

```python
"""MCM A 连续系统 — ODE 建模 + 最优控制"""
import numpy as np
import json

np.random.seed(42)

def sir_model(y, t, beta, gamma):
    """SIR 传染病模型"""
    S, I, R = y
    dS = -beta * S * I
    dI = beta * S * I - gamma * I
    dR = gamma * I
    return [dS, dI, dR]

def rk4_step(f, y, t, dt, *args):
    """RK4 单步"""
    k1 = np.array(f(y, t, *args))
    k2 = np.array(f(y + 0.5*dt*k1, t + 0.5*dt, *args))
    k3 = np.array(f(y + 0.5*dt*k2, t + 0.5*dt, *args))
    k4 = np.array(f(y + dt*k3, t + dt, *args))
    return y + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)

def simulate_ode(f, y0, t_span, dt, *args):
    """ODE 数值求解"""
    t = np.arange(t_span[0], t_span[1], dt)
    y = np.zeros((len(t), len(y0)))
    y[0] = y0
    for i in range(1, len(t)):
        y[i] = rk4_step(f, y[i-1], t[i-1], dt, *args)
    return t, y

def sensitivity_analysis(f, y0, t_span, dt, params, param_names, perturbation=0.1):
    """局部灵敏度分析"""
    _, y_base = simulate_ode(f, y0, t_span, dt, *params)
    sensitivities = {}
    for k, pname in enumerate(param_names):
        params_pert = list(params)
        params_pert[k] *= (1 + perturbation)
        _, y_pert = simulate_ode(f, y0, t_span, dt, *params_pert)
        sens = np.max(np.abs(y_pert - y_base)) / (perturbation * params[k])
        sensitivities[pname] = round(float(sens), 4)
    return sensitivities

def basic_reproduction_number(beta, gamma):
    return beta / gamma

if __name__ == "__main__":
    print("=== MCM A 连续系统建模 ===")

    beta, gamma = 0.3, 0.1
    y0 = [0.99, 0.01, 0.0]
    t_span = (0, 200)
    dt = 0.1

    t, y = simulate_ode(sir_model, y0, t_span, dt, beta, gamma)
    R0 = basic_reproduction_number(beta, gamma)

    sens = sensitivity_analysis(sir_model, y0, t_span, dt,
                                [beta, gamma], ['beta', 'gamma'])

    # 峰值分析
    peak_I = np.max(y[:, 1])
    peak_time = t[np.argmax(y[:, 1])]
    final_R = y[-1, 2]

    results = {
        "Q1_model": {
            "type": "SIR ODE system",
            "R0": round(float(R0), 2),
            "epidemic": R0 > 1
        },
        "Q2_dynamics": {
            "peak_infection": round(float(peak_I), 4),
            "peak_time": round(float(peak_time), 1),
            "final_recovered": round(float(final_R), 4)
        },
        "Q3_sensitivity": sens,
        "Q4_control_note": "最优控制 u*(t) 由 Pontryagin 极大值原理导出"
    }

    with open("figures/all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"R0 = {R0:.2f} ({'流行' if R0 > 1 else '消退'})")
    print(f"感染峰值 = {peak_I:.4f} at t = {peak_time:.1f}")
    print(f"最终感染比例 = {final_R:.4f}")
    print(f"灵敏度: {sens}")
    print("结果已保存至 figures/all_results.json")
```

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| 守恒律 | S + I + R = 1 | 误差 < 1e-6 |
| 步长收敛 | dt 减半 | 变化 < 0.1% |
| R0 阈值 | R0 < 1 → 消退 | 定性正确 |
| 文献对比 | 与已知解析/数值结果 | 一致 |

## 7-9. 论文结构/图表/LaTeX

关键图表：S/I/R 时间序列、相平面图 (S vs I)、灵敏度龙卷风图、控制策略对比图。
