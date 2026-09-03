# Playbook: 2019A 热传导与参数反演

> **题型**: CUMCM A 题 — PDE 机理建模 + 数值方法 + 逆问题
> **核心方法**: 有限差分法 + 热传导方程 + 参数反演
> **难度**: ★★★★★（偏微分方程 + 逆问题，数学要求高）

---

## 1. 问题拆解

```json
{
  "problem": "2019A 热传导与温度场",
  "sub_questions": [
    {"id": "Q1", "desc": "建立热传导偏微分方程模型", "type": "pde_modeling", "depends_on": []},
    {"id": "Q2", "desc": "数值求解温度场分布", "type": "numerical_solution", "depends_on": ["Q1"]},
    {"id": "Q3", "desc": "根据实测温度反演热扩散系数", "type": "inverse_problem", "depends_on": ["Q2"]},
    {"id": "Q4", "desc": "优化保温方案使温度均匀性最好", "type": "optimization", "depends_on": ["Q2", "Q3"]}
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **A 题**（机理/连续） |
| 核心建模 | 热传导 PDE + 逆问题 |
| 求解类型 | 正问题（数值求解）+ 逆问题（参数估计） |
| 方法方向 | 有限差分 + 优化反演 |

## 3. 候选模型对比

| 方法 | 适用场景 | 推荐度 |
|------|---------|--------|
| **有限差分 (Crank-Nicolson)** | 一维/二维热传导 | ★★★★★ |
| 有限元 (FEM) | 复杂几何 | ★★★★☆ |
| 解析解（分离变量） | 简单边界 | ★★★☆☆ |
| 蒙特卡洛随机游走 | 高维/复杂边界 | ★★☆☆☆ |

## 4. 模型建立

### 4.1 热传导方程
$$\frac{\partial T}{\partial t} = \alpha \nabla^2 T + Q(x,t)$$

一维简化：
$$\frac{\partial T}{\partial t} = \alpha \frac{\partial^2 T}{\partial x^2}$$

### 4.2 Crank-Nicolson 格式
$$\frac{T_i^{n+1} - T_i^n}{\Delta t} = \frac{\alpha}{2}\left(\frac{T_{i+1}^{n+1} - 2T_i^{n+1} + T_{i-1}^{n+1}}{\Delta x^2} + \frac{T_{i+1}^n - 2T_i^n + T_{i-1}^n}{\Delta x^2}\right)$$

### 4.3 逆问题（参数反演）
$$\min_\alpha \sum_k (T_{\text{model}}(x_k, t_k; \alpha) - T_{\text{measured}}(x_k, t_k))^2$$

## 5. 代码实现

```python
"""2019A 热传导 — 有限差分 + 参数反演"""
import numpy as np
import json

np.random.seed(42)

# === 参数 ===
L = 1.0          # 域长度 (m)
T_total = 10.0   # 总时间 (s)
Nx = 100         # 空间网格
Nt = 1000        # 时间步
dx = L / Nx
dt = T_total / Nt
alpha_true = 0.01  # 真实热扩散系数

def crank_nicolson(alpha, Nx, Nt, dx, dt, L, T_total, T_init, T_left, T_right):
    """Crank-Nicolson 求解一维热传导"""
    x = np.linspace(0, L, Nx+1)
    T = T_init(x).copy()
    r = alpha * dt / (2 * dx**2)

    # 三对角矩阵
    A = np.zeros((Nx-1, Nx-1))
    B = np.zeros((Nx-1, Nx-1))
    for i in range(Nx-1):
        A[i, i] = 1 + 2*r
        B[i, i] = 1 - 2*r
        if i > 0:
            A[i, i-1] = -r
            B[i, i-1] = r
        if i < Nx-2:
            A[i, i+1] = -r
            B[i, i+1] = r

    history = [T.copy()]
    for n in range(Nt):
        rhs = B @ T[1:-1] + r * np.array([T[0], 0, 0])
        rhs[-1] += r * T[-1]
        T[1:-1] = np.linalg.solve(A, rhs)
        T[0] = T_left
        T[-1] = T_right
        if (n+1) % (Nt//10) == 0:
            history.append(T.copy())

    return x, np.array(history)

def inverse_problem(x_measured, t_measured, T_measured, Nx, Nt, dx, dt, L, T_total):
    """最小二乘反演热扩散系数"""
    alphas = np.linspace(0.001, 0.05, 50)
    best_alpha, best_loss = None, float('inf')
    losses = []

    for alpha in alphas:
        T_init = lambda x: 20 + 80 * np.sin(np.pi * x / L)
        x, T_hist = crank_nicolson(alpha, Nx, Nt, dx, dt, L, T_total, T_init, 20, 20)
        # 在测量点插值
        loss = 0
        for k, (xm, tm) in enumerate(zip(x_measured, t_measured)):
            time_idx = min(int(tm / T_total * Nt), Nt)
            hist_idx = min(time_idx // (Nt//10), 9)
            T_model = np.interp(xm, x, T_hist[hist_idx])
            loss += (T_model - T_measured[k])**2
        losses.append(loss)
        if loss < best_loss:
            best_loss = loss
            best_alpha = alpha

    return best_alpha, alphas, losses

if __name__ == "__main__":
    print("=== 2019A 热传导与参数反演 ===")

    T_init = lambda x: 20 + 80 * np.sin(np.pi * x / L)
    x, T_hist = crank_nicolson(alpha_true, Nx, Nt, dx, dt, L, T_total, T_init, 20, 20)

    # 模拟测量数据（加噪声）
    x_meas = np.array([0.2, 0.4, 0.5, 0.6, 0.8])
    t_meas = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
    T_meas = []
    for xm, tm in zip(x_meas, t_meas):
        T_val = np.interp(xm, x, T_hist[-1]) + np.random.randn() * 0.5
        T_meas.append(T_val)
    T_meas = np.array(T_meas)

    # 反演
    best_alpha, alphas, losses = inverse_problem(x_meas, t_meas, T_meas,
                                                  Nx, Nt, dx, dt, L, T_total)

    results = {
        "Q2_temperature_field": {
            "x_grid_points": Nx + 1,
            "time_steps": Nt,
            "max_temperature": round(float(T_hist[-1].max()), 2),
            "min_temperature": round(float(T_hist[-1].min()), 2)
        },
        "Q3_inverse": {
            "true_alpha": alpha_true,
            "estimated_alpha": round(float(best_alpha), 5),
            "relative_error": round(float(abs(best_alpha - alpha_true)/alpha_true * 100), 1)
        },
        "Q4_optimization_note": "保温层厚度优化使温度标准差最小"
    }

    with open("figures/all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"真实 α = {alpha_true}, 反演 α = {best_alpha:.5f}")
    print(f"相对误差 = {results['Q3_inverse']['relative_error']}%")
    print("结果已保存至 figures/all_results.json")
```

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| 网格收敛 | Δx 减半 → 结果变化 | < 1% |
| 时间步收敛 | Δt 减半 → 结果变化 | < 0.5% |
| 能量守恒 | ∫T dx 变化 | < 2%（无源项） |
| 反演精度 | 已知数据 → 参数误差 | < 10% |

## 7-9. 论文结构/图表/LaTeX

关键图表：温度场时空分布热力图、测点对比曲线、反演目标函数曲线、网格收敛分析表。
