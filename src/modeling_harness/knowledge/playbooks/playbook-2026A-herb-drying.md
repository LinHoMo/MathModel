# Playbook: 2026A 药材烘干（PDE 传热传质 + 移动边界）

> **题型**: CUMCM A 题 — 机理建模 + 偏微分方程 + 移动边界
> **核心方法**: 径向耦合传热传质 + 隐式有限差分 + Landau 坐标变换 + 网格收敛
> **难度**: ★★★★☆（物性强非线性 + 域边界待求）

---

## 1. 问题拆解

```json
{
  "problem": "2026A 药材烘干",
  "sub_questions": [
    {"id": "Q1", "desc": "预热平衡阶段 1800 s 内温度与含水率的时空演化", "type": "forward_simulation", "depends_on": [], "key_output": "T(r,t) 与 C(r,t) 网格表"},
    {"id": "Q2", "desc": "整个烘干过程（预热 + 恒温干燥）分段参数下的演化", "type": "forward_simulation", "depends_on": ["Q1"], "key_output": "0.5 h 间隔的过程表"},
    {"id": "Q3", "desc": "给定各处含水率 < 0.15 kg/kg，求烘干时长", "type": "inverse_time", "depends_on": ["Q2"], "key_output": "烘干时长（h）"},
    {"id": "Q4", "desc": "考虑失水收缩（尺寸变化）下的烘干时长与最终尺寸", "type": "moving_boundary_inverse", "depends_on": ["Q3"], "key_output": "烘干时长 + 最终半径 + 含水率分布"}
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **A 题**（机理/连续） |
| 核心建模 | 抛物型 PDE（热 + 质耦合）+ 移动边界 |
| 求解类型 | 正问题仿真 + 单点阈值反解时间 |
| 数据需求 | 附录物性关联式 + 工艺温度/湿度曲线；无观测数据拟合 |
| 方法方向 | 数值 PDE + 变物性 + 网格/时间步收敛 |

## 3. 候选模型对比

| 方法 | 优势 | 劣势 | 适用子问 | 推荐度 |
|------|------|------|---------|--------|
| **径向 1D 耦合 PDE（隐式 FDM）** | 物理完整，可算变物性与移动域 | 需处理非线性与网格收敛 | Q1–Q4 | ★★★★★ |
| 集总参数（集中热容/薄层） | 极简、快 | 无法给内部剖面，中心判据不可用 | 不适用 | ★☆☆☆☆ |
| 经验干燥曲线拟合（Page/Midilli） | 参数少、易用 | 需数据标定，无预测能力，无法回答空间分布 | Q3 粗估 | ★★☆☆☆ |
| 2D/3D 有限元 | 可含轴向 | 长径比大 ⇒ 收益极低、成本高 | 不适用 | ★☆☆☆☆ |

**最终选择**: 径向 1D 耦合 PDE（Q1–Q3）+ Landau 变换移动边界（Q4）

## 4. 模型建立

### 4.1 符号定义

| 符号 | 含义 | 单位 |
|------|------|------|
| $T(r,t)$ | 药材温度 | °C |
| $C(r,t)$ | 干基含水率 | kg/kg |
| $R(t)$ | 外半径（Q4 为待求） | m |
| $k(C)$ | 有效热导率 | W/(m·K) |
| $D(C,T)$ | 水分扩散系数 | m²/s |
| $h, h_m$ | 对流换热/传质系数 | W/(m²·K), m/s |
| $\bar C$ | 体积加权平均含水率 | kg/kg |

### 4.2 控制方程

$$\rho(C)c_p(C)\frac{\partial T}{\partial t}=\frac{1}{r}\frac{\partial}{\partial r}\left(r k(C)\frac{\partial T}{\partial r}\right),\qquad
\frac{\partial C}{\partial t}=\frac{1}{r}\frac{\partial}{\partial r}\left(r D(C,T)\frac{\partial C}{\partial r}\right)$$

### 4.3 边界与初值

$$-k\frac{\partial T}{\partial r}\Big|_{r=R}=h(T-T_{air}),\quad -D\frac{\partial C}{\partial r}\Big|_{r=R}=h_m(C-C_{air}),\quad
\frac{\partial T}{\partial r}\Big|_{r=0}=\frac{\partial C}{\partial r}\Big|_{r=0}=0$$

### 4.4 移动边界（Q4）

令 $\xi=r/R(t)$，则

$$\frac{\partial C}{\partial t}\Big|_r=\frac{\partial C}{\partial t}\Big|_\xi-\frac{\xi\dot R}{R}\frac{\partial C}{\partial\xi}
\quad\Longrightarrow\quad \text{固定域求解 + 附加对流项}$$

半径闭合（单位长度干物质守恒）：

$$R(t)=R_0\sqrt{\frac{\rho(C_0)}{1+C_0}\cdot\frac{1+\bar C}{\rho(\bar C)}}$$

### 4.5 烘干判据

中心 r=0 是径向单调剖面的极值点，故 $\max_r C(r,t)=C(0,t)$，判据退化为

$$t_{dry}=\inf\{t:\ C(0,t)<0.15\}$$

## 5. 代码实现

```python
"""2026A 药材烘干 — 径向耦合传热传质（隐式 + 移动边界）"""
import numpy as np, math

np.random.seed(42)          # 确定性求解；种子固定以备校验流程

R0, L, T0, C0 = 0.02, 0.25, 28.0, 2.55
H, HM, C_TH = 25.0, 8e-7, 0.15
N, DT = 1280, 10.0          # 网格 1280（Δr=0.0015625 cm），Δt=10 s

def props(C, T, mode):
    Cm = np.maximum(C, 1e-6)
    if mode == 1:                                   # 附录 2 常物性
        return (np.full_like(C, 820.), np.full_like(C, 2600.), np.full_like(C, .36),
                7e-9*np.exp(-0.89/Cm))
    if mode in (2, 3):                              # 附录 3 变物性
        return (650+128*C, 1450+2736*C/(C+1), 0.21+0.38*C/(C+1),
                2.4e-3*np.exp(-0.45/Cm)*np.exp(-3850/T))
    return (760+90*C, 1850+2150*C/(C+1), 0.12+0.20*C/(C+1),
            4.2e-4*np.exp(-0.30/Cm)*np.exp(-3850/T))  # 附录 4

def step(u, beta, kappa, dt, R, dRdt, heff, amb):
    """ξ∈[0,1] 上一步隐式推进（有限体积 + Robin ghost 消元）"""
    h, xi = 1.0/N, np.arange(N+1)/N
    kh = 2*kappa[:-1]*kappa[1:]/(kappa[:-1]+kappa[1:]+1e-30)
    lam = dt/(beta*R*R*h*h)
    a, b, c = np.zeros(N+1), np.zeros(N+1), np.zeros(N+1)
    i = np.arange(1, N)
    ad, cd = lam[i]*kh[i-1]*(i-.5)*h/xi[i], lam[i]*kh[i]*(i+.5)*h/xi[i]
    s = .5*dt*(dRdt/R)*xi[i]/h
    a[i], b[i], c[i] = -(ad-s), 1+ad+cd, -(cd+s)
    b[0], c[0] = 1+4*kappa[0]*lam[0], -4*kappa[0]*lam[0]       # 中心对称
    A = lam[N]*kh[N-1]*(N-.5)*h/xi[N]; Cc = lam[N]*(1+.5*h)*kappa[N]
    B = 2*h*R*heff/(kappa[N]+1e-30); sN = .5*dt*(dRdt/R)*xi[N]/h
    a[N], b[N] = -(Cc+A)-sN, 1+Cc+A+B*(Cc+sN); c[N] = 0.
    rhs = u.copy(); rhs[N] = u[N]+B*(Cc+sN)*amb
    # 三对角追赶法（Thomas）
    cp = np.zeros(N+1); dp = np.zeros(N+1); x = np.zeros(N+1)
    cp[0] = c[0]/b[0]; dp[0] = rhs[0]/b[0]
    for j in range(1, N+1):
        den = b[j]-a[j]*cp[j-1]
        cp[j] = (c[j]/den) if j < N else 0.0
        dp[j] = (rhs[j]-a[j]*dp[j-1])/den
    x[N] = dp[N]
    for j in range(N-1, -1, -1):
        x[j] = dp[j]-cp[j]*x[j+1]
    return x

def solve(mode, moving=False, t_end=8*24*3600., T_target=50.):
    T, C, R = np.full(N+1, T0), np.full(N+1, C0), R0
    t = 0.
    while t < t_end:
        t += DT
        Tair = T0+(T_target-T0)*(1-math.exp(-t/450.))
        Cair = 0.10 if mode == 1 else (0.15 if t < 1800 else 0.05)
        rho, cp, k, D = props(C, T+273.15, mode)
        dRdt = 0.
        if moving:                                  # 干物质守恒闭合 R(t)
            idx = np.arange(N+1)+1e-30
            Cbar = float((C*idx).sum()/idx.sum())
            Rn = R0*math.sqrt((760+90*C0)/(1+C0)*(1+Cbar)/(760+90*Cbar))
            dRdt, R = (Rn-R)/DT, Rn
        T = step(T, rho*cp, k, DT, R, dRdt, H, Tair)
        C = np.clip(step(C, np.ones(N+1), D, DT, R, dRdt, HM, Cair), 0., C0)
        if C[0] < C_TH:
            break
    return t/3600., R, C

if __name__ == "__main__":
    for tag, mode, mv in (("Q3 固定半径", 3, False), ("Q4 收缩", 4, True)):
        h, R, C = solve(mode, moving=mv)
        print(f"{tag}: t_dry={h:.4f} h  R_end={R*100:.4f} cm  C_center={C[0]:.7f}")
```

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| 空间网格收敛 | N = 160/320/640/1280/2560，取高两档 | 相邻档差 < 0.1% |
| 时间步收敛 | Δt = 20/10/5 s | 差 < 0.1% |
| 温度敏感性 | T_target = 45/50/55/60 °C | 时长单调下降，报告区间 |
| 干物质守恒（Q4） | 逐步累计干物质总量 | 相对误差 < 1e-6 |
| 物理合理性 | 单调性 + 极值点核查 | 剖面单调、中心为极值 |

```python
def spatial_convergence():
    out = []
    for n in (160, 320, 640, 1280, 2560):
        globals()['N'] = n
        out.append((n, solve(3)[0]))
    return out      # 检查相邻档相对差，取平台段
```

## 7. 论文结构

| 章节 | 内容 | 图表 |
|------|------|------|
| 摘要 | 问题—模型—关键结果 | — |
| 1 问题分析 | 四问拆解 + 降维依据（长径比） | 图1 几何与坐标系 |
| 2 假设与符号 | 物性滞后、两段工艺、各向同性收缩 | 表1 符号表 |
| 3 模型建立 | 控制方程 + 边界 + 移动边界变换 | 图2 网格示意 |
| 4 数值方法 | 隐式格式 + 三对角 + 判据 | 表2 离散系数 |
| 5 结果 | Q1–Q4 表与剖面图 | 图3–6 温度/含水率剖面 |
| 6 验证 | 网格/时间收敛 + 敏感性 | 图7 收敛曲线 |
| 7 评价 | 局限：温度标定值、均匀网格残差 | — |

## 8. 关键图表

| 编号 | 类型 | 内容 | 工具 |
|------|------|------|------|
| 图1 | 示意图 | 圆柱药材截面 + 径向坐标 + Robin 边界 | matplotlib |
| 图2 | 曲线 | 不同时刻的温度/含水率径向剖面 | matplotlib |
| 图3 | 曲线 | 中心与表面含水率随时间（含阈值线） | matplotlib |
| 图4 | 曲线 | 网格/时间步收敛序列 | matplotlib |
| 图5 | 曲线 | 半径 R(t) 收缩轨迹（Q4） | matplotlib |
| 图6 | 热图 | C(r,t) 时空分布 | matplotlib |

## 9. LaTeX 源码片段

```latex
\section{移动边界模型}
失水收缩使求解域 $[0,R(t)]$ 随时间变化。令 $\xi=r/R(t)$ 将其映到固定域 $[0,1]$，得
\begin{equation}
  \frac{\partial C}{\partial t}
  =\frac{1}{R^2\xi}\frac{\partial}{\partial \xi}\left(\xi D\frac{\partial C}{\partial \xi}\right)
   +\frac{\xi \dot R}{R}\frac{\partial C}{\partial \xi},
\end{equation}
其中附加对流项 $-\xi\dot R/R\,\partial C/\partial\xi$ 由坐标变换产生，不可略去。
半径 $R(t)$ 由单位长度干物质守恒闭合：
\begin{equation}
  R(t)=R_0\sqrt{\frac{\rho(C_0)}{1+C_0}\cdot\frac{1+\bar C}{\rho(\bar C)}} .
\end{equation}
```

## 10. 复用要点

- **降维先证时间尺度比**：$(L/R_0)^2$ 远大于 1 才可只保留径向。
- **判据取极值点**：先证明剖面单调，再用中心点判烘干终点。
- **移动边界必查两项**：附加对流项是否写全、守恒量残差是否量级正确。
- **网格收敛做 ≥4 档**：变物性 + 薄边界层容易出现「假收敛平台」。
- **标定量要显式**：工艺温度若由时长窗口反标定，必须给出敏感性区间。
