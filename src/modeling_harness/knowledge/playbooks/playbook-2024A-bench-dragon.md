# Playbook: 2024A 板凳龙（机理/运动学建模）

> **题型**: CUMCM A 题 — 机理建模 + 运动学 + 几何
> **核心方法**: 多体递推 + 悬链线 + 微分几何 + 数值优化
> **难度**: ★★★★☆（物理建模 + 多子问递进）

---

## 1. 问题拆解

```json
{
  "problem": "2024A 板凳龙",
  "sub_questions": [
    {
      "id": "Q1",
      "desc": "建立板凳龙螺旋进场的运动学模型，计算各节位置/速度",
      "type": "forward_simulation",
      "depends_on": [],
      "key_output": "各节把手坐标序列 (x_i(t), y_i(t))"
    },
    {
      "id": "Q2",
      "desc": "确定调头时盘入/盘出的螺旋参数，保证不碰撞",
      "type": "parameter_optimization",
      "depends_on": ["Q1"],
      "key_output": "最小螺距、调头区域半径"
    },
    {
      "id": "Q3",
      "desc": "分析调头过程中相邻节之间的碰撞风险",
      "type": "collision_detection",
      "depends_on": ["Q1", "Q2"],
      "key_output": "碰撞时间/位置、安全裕度"
    },
    {
      "id": "Q4",
      "desc": "优化调头路径使得总路径最短或时间最少",
      "type": "trajectory_optimization",
      "depends_on": ["Q2", "Q3"],
      "key_output": "最优调头策略"
    }
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **A 题**（机理/连续） |
| 核心建模 | 刚体运动学 + 螺旋几何 |
| 求解类型 | 正向仿真 + 参数优化 |
| 数据需求 | 几何参数（龙身长度、节数、把手间距） |
| 方法方向 | 微分几何 + 数值方法 + 优化 |

## 3. 候选模型对比

| 方法 | 优势 | 劣势 | 适用子问 | 推荐度 |
|------|------|------|---------|--------|
| **多体递推（刚体链）** | 物理精确，可逐节追踪 | 计算量大，需处理约束 | Q1/Q3 | ★★★★★ |
| 悬链线近似 | 解析简洁，快速估算 | 忽略刚度，精度有限 | Q2 初估 | ★★★☆☆ |
| 有限元柔性体 | 最精确 | 过于复杂，竞赛不现实 | 全部 | ★☆☆☆☆ |
| 纯几何螺旋拟合 | 简单直观 | 无法处理动态约束 | Q2/Q4 | ★★★☆☆ |

**最终选择**: 多体递推（Q1/Q3）+ 螺旋几何解析（Q2/Q4）

## 4. 模型建立

### 4.1 符号定义

| 符号 | 含义 | 单位 |
|------|------|------|
| $N$ | 板凳龙总节数 | — |
| $L_i$ | 第 $i$ 节长度 | m |
| $d$ | 相邻把手间距 | m |
| $\theta_i(t)$ | 第 $i$ 节方位角 | rad |
| $(x_i, y_i)$ | 第 $i$ 节把手坐标 | m |
| $v_0$ | 龙头行进速度 | m/s |
| $R$ | 螺旋半径 | m |
| $p$ | 螺距 | m/rad |

### 4.2 螺旋进场模型

龙头沿阿基米德螺旋线运动：

$$x_0(t) = (R_0 - v_0 t) \cos\left(\frac{v_0 t}{p}\right)$$
$$y_0(t) = (R_0 - v_0 t) \sin\left(\frac{v_0 t}{p}\right)$$

### 4.3 多体递推（核心）

每节板凳视为刚体，后节位置由前节约束递推：

$$x_{i+1} = x_i - d \cos\theta_i$$
$$y_{i+1} = y_i - d \sin\theta_i$$

方位角由前节速度方向决定：

$$\theta_i(t) = \arctan\left(\frac{y_i(t) - y_i(t-\Delta t)}{x_i(t) - x_i(t-\Delta t)}\right)$$

### 4.4 碰撞检测

相邻节不碰撞条件：

$$\sqrt{(x_i - x_j)^2 + (y_i - y_j)^2} \geq w_{\min}, \quad \forall |i-j| > 1$$

其中 $w_{\min}$ 为龙身宽度。

### 4.5 调头螺旋优化

目标函数：$\min_{R, p} T_{\text{turn}}$

约束：
- 不碰撞：$d_{\min}(t) \geq w_{\min}$
- 螺距连续：$p_{\text{in}} = p_{\text{out}}$
- 边界：$R_{\min} \leq R \leq R_{\max}$

## 5. 代码实现

```python
"""2024A 板凳龙 — 多体递推运动学模型"""
import numpy as np
import json

np.random.seed(42)

# === 参数 ===
N = 223          # 板凳龙节数
d = 0.3          # 把手间距 (m)
w_min = 0.3      # 龙身宽度 (m)
v0 = 1.0         # 龙头速度 (m/s)
R0 = 6.0         # 初始螺旋半径 (m)
p = 0.5          # 螺距 (m/rad)
dt = 0.01        # 时间步长 (s)
T_total = 300.0  # 总时间 (s)

def spiral_position(t, R0, v0, p):
    """龙头沿阿基米德螺旋线位置"""
    r = R0 - v0 * t
    theta = v0 * t / p
    return r * np.cos(theta), r * np.sin(theta)

def forward_kinematics(N, d, dt, T_total, R0, v0, p):
    """多体递推求解各节把手轨迹"""
    n_steps = int(T_total / dt)
    # 存储所有节的位置
    x = np.zeros((N, n_steps))
    y = np.zeros((N, n_steps))

    for step in range(n_steps):
        t = step * dt
        # 龙头位置
        x[0, step], y[0, step] = spiral_position(t, R0, v0, p)

        if step == 0:
            # 初始时刻：所有节沿螺旋线排列
            for i in range(1, N):
                s_back = i * d
                t_back = s_back / v0
                x[i, 0], y[i, 0] = spiral_position(-t_back, R0, v0, p)
        else:
            # 递推：后节沿前节方向偏移 d
            for i in range(1, N):
                dx = x[i, step-1] - x[i-1, step]
                dy = y[i, step-1] - y[i-1, step]
                dist = np.sqrt(dx**2 + dy**2)
                if dist < 1e-10:
                    x[i, step] = x[i, step-1]
                    y[i, step] = y[i, step-1]
                else:
                    x[i, step] = x[i-1, step] + d * dx / dist
                    y[i, step] = y[i-1, step] + d * dy / dist

    return x, y

def check_collision(x, y, w_min, step):
    """检测某时刻是否存在碰撞"""
    N = x.shape[0]
    violations = []
    for i in range(N):
        for j in range(i+3, N):  # 跳过相邻节
            dist = np.sqrt((x[i, step]-x[j, step])**2 +
                          (y[i, step]-y[j, step])**2)
            if dist < w_min:
                violations.append((i, j, dist))
    return violations

def compute_min_clearance(x, y, step):
    """计算最小安全间距"""
    N = x.shape[0]
    min_dist = float('inf')
    for i in range(N):
        for j in range(i+2, N):
            dist = np.sqrt((x[i, step]-x[j, step])**2 +
                          (y[i, step]-y[j, step])**2)
            min_dist = min(min_dist, dist)
    return min_dist

# === 主程序 ===
if __name__ == "__main__":
    print("=== 2024A 板凳龙运动学仿真 ===")
    x, y = forward_kinematics(N, d, dt, T_total, R0, v0, p)

    # Q1: 输出关键节位置
    key_nodes = [0, N//4, N//2, 3*N//4, N-1]
    t_check = int(10.0 / dt)  # t=10s
    results = {"Q1_positions": {}}
    for idx in key_nodes:
        results["Q1_positions"][f"node_{idx}"] = {
            "x": round(float(x[idx, t_check]), 4),
            "y": round(float(y[idx, t_check]), 4)
        }

    # Q3: 碰撞检测
    collision_steps = []
    for step in range(0, int(T_total/dt), 100):
        viols = check_collision(x, y, w_min, step)
        if viols:
            collision_steps.append({
                "time": round(step * dt, 2),
                "pairs": len(viols)
            })
    results["Q3_collisions"] = collision_steps[:10]

    # Q2: 最小安全间距
    min_clearances = []
    for step in range(0, int(T_total/dt), 500):
        mc = compute_min_clearance(x, y, step)
        min_clearances.append({
            "time": round(step * dt, 2),
            "min_dist": round(float(mc), 4)
        })
    results["Q2_min_clearance"] = min_clearances

    # 保存结果
    with open("figures/all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"总节数: {N}, 仿真时间: {T_total}s")
    print(f"龙头初始位置: ({x[0,0]:.2f}, {y[0,0]:.2f})")
    print(f"最小安全间距: {min(mc['min_dist'] for mc in min_clearances):.4f} m")
    print(f"碰撞事件数: {len(collision_steps)}")
    print("结果已保存至 figures/all_results.json")
```

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| 把手间距守恒 | 逐帧检查 $\|P_i P_{i+1}\| = d$ | 相对误差 < 1e-6 |
| 能量守恒（无外力） | 龙头匀速 → 各节速率有界 | 速率不超过 $2 v_0$ |
| 网格收敛 | $\Delta t$ 减半后结果变化 | 变化 < 0.1% |
| 对称性 | 盘入/盘出对称参数 → 轨迹对称 | 对称误差 < 1% |

```python
def verify_rigid_constraint(x, y, d, tol=1e-6):
    """验证刚体约束：相邻节间距恒为 d"""
    N, T = x.shape
    max_err = 0
    for step in range(0, T, 100):
        for i in range(N-1):
            dist = np.sqrt((x[i,step]-x[i+1,step])**2 +
                          (y[i,step]-y[i+1,step])**2)
            max_err = max(max_err, abs(dist - d))
    return max_err < tol, max_err
```

## 7. 论文结构

| 章节 | 内容 | 字数 | 图表 |
|------|------|------|------|
| 摘要 | 问题概述 + 方法 + 关键结果 | 400 | — |
| 1. 问题分析 | 四问拆解 + 建模思路 | 800 | 图1: 板凳龙实物/螺旋进场示意 |
| 2. 模型假设 | 5-6 条假设 + 合理性 | 500 | 表1: 假设清单 |
| 3. Q1 运动学模型 | 多体递推推导 | 2000 | 图2: 递推示意, 图3: 轨迹图 |
| 4. Q2 调头参数 | 螺旋几何 + 优化 | 1800 | 图4: 调头区域, 表2: 最优参数 |
| 5. Q3 碰撞分析 | 碰撞检测 + 安全裕度 | 1500 | 图5: 碰撞热图 |
| 6. Q4 路径优化 | 优化模型 + 算法 | 1500 | 图6: 优化前后对比 |
| 7. 模型评价 | 优缺点 + 改进方向 | 600 | — |
| 参考文献 | 10-15 篇 | — | — |

## 8. 关键图表

| 编号 | 类型 | 内容 | 工具 |
|------|------|------|------|
| 图1 | 示意图 | 板凳龙螺旋进场俯视 | matplotlib |
| 图2 | 轨迹图 | 各节把手运动轨迹（彩色） | matplotlib |
| 图3 | 时间序列 | 龙头/龙中/龙尾速度变化 | matplotlib |
| 图4 | 热力图 | 碰撞风险时空分布 | matplotlib + seaborn |
| 图5 | 对比图 | 不同螺距下的安全裕度 | matplotlib |
| 表1 | 参数表 | 几何参数与物理参数 | — |

## 9. LaTeX 源码片段

```latex
\section{问题分析}
本题以板凳龙为对象，研究多体刚体链在螺旋路径上的运动学问题。
龙头沿阿基米德螺旋线盘入，各节板凳通过把手铰接，后节跟随前节运动。
需要解决四个递进子问：正向运动学仿真、调头参数确定、碰撞风险分析、路径优化。

\section{模型假设}
\begin{enumerate}
    \item 每节板凳视为刚体，忽略弯曲变形；
    \item 把手铰接为理想球铰，允许任意方向转动；
    \item 龙头匀速行进，速度 $v_0 = 1.0$ m/s；
    \item 龙身宽度均匀，$w = 0.3$ m；
    \item 地面平坦，忽略重力对运动的影响。
\end{enumerate}

\section{Q1：多体递推运动学模型}
设第 $i$ 节把手坐标为 $(x_i, y_i)$，相邻间距为 $d$。
后节位置由前节方向递推：
\begin{equation}
    x_{i+1} = x_i - d\cos\theta_i, \quad
    y_{i+1} = y_i - d\sin\theta_i
\end{equation}
其中 $\theta_i$ 为第 $i$ 节方位角，由历史位置差分确定。
```
