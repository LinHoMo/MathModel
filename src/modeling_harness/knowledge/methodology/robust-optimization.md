# 鲁棒优化（Robust Optimization）领域知识

## 一、核心概念

### 1.1 定义
- 参数不确定时，要求解在**不确定集内所有实现下均可行且尽可能优**的决策。
- 与随机优化的区别：随机优化需要分布假设并优化期望；鲁棒优化只需不确定集（盒子/椭球/预算集），优化最坏情形。
- 适用信号：题面出现"波动/不确定/最坏情况/抗风险/裕度"等表述。

### 1.2 不确定集常用形式
| 形式 | 数学表达 | 特点 |
|---|---|---|
| 盒子集 | ξ ∈ [ξ̄-δ, ξ̄+δ] 逐分量 | 保守、建模简单 |
| 椭球集 | ‖Σ⁻¹ᐟ²(ξ-ξ̄)‖₂ ≤ Ω | 联合波动、可转 SOCP |
| 预算集（Γ-鲁棒） | Σ\|z_i\| ≤ Γ, ξ=ξ̄+diag(δ)z | 可调保守度，Bertsimas-Sim |

---

## 二、基本方法

### 2.1 Γ-鲁棒线性规划（Bertsimas-Sim 形式）

```text
min  c^T x + max_{S⊆{1..n},|S|≤Γ} Σ_{i∈S} δ_i |x_i|
s.t. Ax ≤ b, x ≥ 0
```

- 内层 max 有对偶线性形式，整体仍可写成一个规模更大的 LP（可用线性规划求解器）。
- **Γ 是保守度旋钮**：Γ=0 退化为名义解；Γ=n 为最保守。论文应扫描 Γ 画"成本-违约概率"权衡曲线。

### 2.2 场景法（数据驱动的近似鲁棒）

```python
import numpy as np

def scenario_cost(x, scenarios: np.ndarray, A, b) -> float:
    """scenarios: (n_scen, n_param) 的参数实现；返回最坏场景成本。"""
    costs = []
    for xi in scenarios:
        if np.any(A @ x > b + 1e-9):  # 可行性（按场景）
            return np.inf
        costs.append(float(xi @ x))
    return max(costs)

def sample_scenarios(n_scen, mu, delta, seed=42):
    rng = np.random.default_rng(seed)
    return rng.uniform(mu - delta, mu + delta, size=(n_scen, len(mu)))
```

### 2.3 机会约束的近似
- P(违反约束) ≤ ε 可用样本近似：场景数 N ≥ 1/ε 量级才能估小概率；论文须说明样本量依据。

---

## 三、竞赛应用要点

### 3.1 选型写法
- 决策树「不确定决策族」分支：分布未知 → 鲁棒/场景法；分布已知 → 随机规划（两阶段）。
- 必须写清不确定集的**构造依据**（数据标准差、题给波动范围、文献），不允许"设 δ=10%" 无理由。

### 3.2 必做分析
- **保守度曲线**: Γ（或 δ）从 0 到上限扫描，目标值与违约频率双轴图。
- **与名义解对比**: 鲁棒解的目标代价（price of robustness）量化。
- **蒙特卡洛压力测试**: 抽 10⁴ 个场景，统计名义解与鲁棒解的违约率（铁律：固定种子）。

### 3.3 图表规范
- 保守度权衡曲线（核心图）
- 违约率对比柱状图（名义 vs 鲁棒，不同 δ）
- 关键决策变量随 Γ 的变化曲线

### 3.4 LaTeX 代码

```latex
\begin{equation}
\min_{x}\; c^\top x + \Gamma\,\theta + \sum_{i} q_i,\quad
\theta + q_i \ge \delta_i |x_i|,\; q_i \ge 0
\label{eq:gamma_robust}
\end{equation}
```

---

## 四、常见错误

1. **不确定集无依据**: δ/Γ 取值没有数据或题面支撑，评审一票否定点。
2. **只给最保守解**: 必须给权衡曲线让决策者选，而不是单一解。
3. **场景数不足估违约率**: 1000 场景估 1% 违约率误差极大；至少 10⁴ 并给置信区间。
4. **把鲁棒当灵敏度**: 鲁棒优化是决策方法（改变解），灵敏度分析是事后检验——两者都要，不可互替。

---

## 五、参考文献

1. Ben-Tal A, Nemirovski A. Robust Optimization. Princeton University Press, 2009.
2. Bertsimas D, Sim M. The price of robustness. Operations Research, 2004, 52(1): 35-53.
3. Gabrel V, Murat C, Thiele A. Recent advances in robust optimization: An overview. European Journal of Operational Research, 2014, 235(3): 471-483.
