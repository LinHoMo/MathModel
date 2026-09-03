# 随机过程（Stochastic Processes）领域知识

## 一、核心概念

### 1.1 定位
- 随机过程是"随时间（或空间）演化的随机现象"的数学框架，是排队论、可靠性、金融建模、传染病随机模型的基础。
- 与马尔可夫链（离散状态离散时间）互补：本篇覆盖**计数过程（Poisson）、布朗运动、生灭过程、SDE**。

### 1.2 常用过程速查
| 过程 | 核心参数 | 典型应用 |
|---|---|---|
| Poisson 过程 | 强度 λ | 呼叫/事故/到达计数 |
| 生灭过程 | 出生率 λₙ、死亡率 μₙ | 排队系统、种群 |
| 布朗运动/维纳过程 | 漂移 μ、波动 σ | 金融价格、扩散 |
| 复合 Poisson | λ + 跳跃分布 | 保险理赔总额 |

---

## 二、基本方法

### 2.1 Poisson 过程与到达建模

```python
import numpy as np

def poisson_arrivals(rate: float, horizon: float, seed: int = 42) -> np.ndarray:
    """齐次 Poisson 过程的到达时刻（指数间隔）。"""
    rng = np.random.default_rng(seed)
    intervals = rng.exponential(1.0 / rate, size=int(rate * horizon * 3) + 10)
    times = np.cumsum(intervals)
    return times[times <= horizon]
```

- **λ 的估计**: λ̂ = 总事件数 / 总观测时长；多段观测给置信区间（正态近似或精确 χ²）。
- **平稳增量检验**: 分段计数做卡方拟合优度，验证齐次性假设。

### 2.2 生灭过程稳态（排队/种群）

```python
def birth_death_stationary(lam: np.ndarray, mu: np.ndarray, n_max: int = 200) -> np.ndarray:
    """π_n = π_0 Π_{i=1}^n λ_{i-1}/μ_i，归一化。要求截断尾部质量 <1e-8。"""
    pi = [1.0]
    for n in range(1, n_max + 1):
        pi.append(pi[-1] * lam[min(n - 1, len(lam) - 1)] / mu[min(n, len(mu) - 1)])
    pi = np.array(pi)
    return pi / pi.sum()
```

- M/M/1 经典结论（对照用）：ρ=λ/μ<1 时 πₙ=(1-ρ)ρⁿ，平均队长 L=ρ/(1-ρ)。

### 2.3 SDE 数值解（Euler-Maruyama）

```python
def em_sde(mu, sigma, x0, T, n_steps, seed=42):
    """dX = mu(X)dt + sigma(X)dW 的 Euler-Maruyama 离散。"""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    x = np.empty(n_steps + 1); x[0] = x0
    sq = np.sqrt(dt)
    for k in range(n_steps):
        x[k + 1] = x[k] + mu(x[k]) * dt + sigma(x[k]) * sq * rng.standard_normal()
    return x
```

- **步长收敛性检查必须做**: 步长减半，路径统计量（均值/方差/首达时间）变化应小于容差，否则结论是步长假象。

---

## 三、竞赛应用要点

### 3.1 选型写法
- 题面有"随机到达/随机故障/价格波动/传播"且关注**时间演化的分布**（不只是均值）时用。
- 写清三要素：状态、驱动随机的分布、参数估计来源。

### 3.2 参数与验证
- 参数必须从题给数据估计并给置信区间；文献参数须论证迁移合理性。
- 仿真验证：解析可得的量（平稳分布、期望首达时间）与仿真对比，误差 <1%。
- 多种子运行报均值±标准差（铁律 P1）。

### 3.3 图表规范
- 样本路径图（多条路径叠加，体现随机性）
- 计数/到达的观测-拟合对比（柱状 + 理论曲线）
- 稳态分布柱状图（仿真 vs 解析）

### 3.4 LaTeX 代码

```latex
\begin{equation}
P\{N(t) = k\} = \frac{(\lambda t)^k}{k!} e^{-\lambda t},\qquad
L = \frac{\rho}{1-\rho},\ \rho = \frac{\lambda}{\mu}
\label{eq:poisson_mm1}
\end{equation}
```

---

## 四、常见错误

1. **指数间隔假设不检验**: 到达数据常非齐次/非独立，须做间隔分布拟合检验（KS 检验）。
2. **SDE 不做步长收敛检查**: 数值假象当成模型结论。
3. **稳态不存在硬算稳态**: ρ≥1 时生灭过程无平稳分布，必须判稳态存在性。
4. **单条路径下结论**: 随机过程结论必须基于路径集合的统计量。

---

## 五、参考文献

1. Grimmett G R, Stirzaker D R. Probability and Random Processes. Oxford University Press, 2020.
2. Ross S M. Introduction to Probability Models. Academic Press, 2019.
3. Kloeden P E, Platen E. Numerical Solution of Stochastic Differential Equations. Springer, 1992.
