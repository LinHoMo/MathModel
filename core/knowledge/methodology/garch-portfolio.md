# GARCH 与组合投资方法论

> 本文件提供金融时间序列波动率建模（GARCH 族模型）与组合投资（均值-方差 / VaR / CVaR）的完整方法论，覆盖 ARCH 效应检验、Markowitz 有效前沿、风险度量与建模步骤。

---

## 一、方法选择决策树

```
金融序列分析
├── 目标：预测波动率（方差）？
│   ├── 收益率存在波动聚集（volatility clustering）→ GARCH 族
│   │   ├── 对称波动 → GARCH(1,1)
│   │   ├── 杠杆效应（下跌波动更大）→ EGARCH / GJR-GARCH
│   │   └── 长记忆 → FIGARCH
│   ├── 厚尾严重 → GARCH + Student-t / skewed-t 分布
│   └── 波动率恒定假设才满足 → 普通 ARMA 即可
├── 目标：分配资金（组合优化）？
│   ├── 已知均值与协方差 → Markowitz 均值-方差模型
│   │   ├── 允许卖空 → 等式约束 Σw=1
│   │   ├── 禁止卖空 → 额外 w ≥ 0
│   │   └── 需要稀疏持仓 → L1 惩罚 / 约束上限
│   └── 均值估计不可靠 → 最小方差组合 / Black-Litterman
└── 目标：度量尾部风险？
    ├── 参数法（收益率正态）→ VaR = μ + z·σ
    ├── 历史模拟 → 分位数直接取
    └── 一致性风险度量 → CVaR（线性规划可解）
```

---

## 二、GARCH 波动率建模

### 2.1 模型原理

金融收益率常呈「波动聚集」：大波动后跟大波动、小波动后跟小波动。普通 ARMA 假设方差恒定无法刻画，GARCH（广义自回归条件异方差）让条件方差随时间演化。

**GARCH(p,q) 模型方程**：

```
rₜ = μ + εₜ,  εₜ = σₜ·zₜ,  zₜ ~ i.i.d.(0,1)

σₜ² = ω + Σᵢ₌₁ᵖ αᵢ·εₜ₋ᵢ² + Σⱼ₌₁ᵠ βⱼ·σₜ₋ⱼ²
```

- ω > 0：长期基准波动
- αᵢ：新信息（冲击）对下一期方差的影响，衡量波动聚集强度
- βⱼ：方差自身的持续性
- 平稳条件：Σαᵢ + Σβⱼ < 1
- GARCH(1,1) 最常用：σₜ² = ω + α·εₜ₋₁² + β·σₜ₋₁²

**半生命周期**（波动冲击衰减到一半所需期数）：`halflife = ln(0.5) / ln(α+β)`

### 2.2 适用条件

| 条件 | 说明 |
|------|------|
| 收益率序列弱平稳 | 均值方程残差无显著自相关 |
| 存在 ARCH 效应 | 残差平方项显著自相关（Ljung-Box 通过） |
| 样本量足够 | 日频建议 ≥ 500 观测，参数才能稳定估计 |
| 分布假设合理 | 厚尾时优先 Student-t / skewed-t 而非正态 |

### 2.3 建模步骤

```
1. 数据准备：对数收益率 rₜ = ln(Pₜ/Pₜ₋₁)，去均值化
2. 平稳性检验：ADF 检验收益率本身（通常平稳）
3. 均值方程定阶：对 rₜ 拟合 ARMA，或直接取 μ 常数
4. ARCH 效应检验：对均值方程残差平方项做 Ljung-Box 检验
5. 拟合 GARCH：arch_model 选定 p,q 与分布，最大或然估计
6. 模型检验：标准化残差 zₜ=εₜ/σₜ 应近似白噪声
7. 滚动样本外预测：预测未来 h 期条件方差
```

---

## 三、ARCH 效应检验

### 3.1 检验原理

GARCH 建模的**前置条件**是「残差存在波动聚集」，即残差平方项序列存在自相关。检验分两步：

1. **ADF 检验**：确认收益率序列平稳（决定能否直接建模）
2. **Ljung-Box 检验**：对均值方程残差的**平方项** `εₜ²` 检验自相关，p 值显著（< 0.05）说明存在 ARCH 效应，适合 GARCH

### 3.2 代码要点

```python
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox

def arch_effect_test(returns):
    """
    returns: 收益率序列（对数收益率）
    步骤：ADF 平稳性 + 残差平方项 Ljung-Box 自相关检验
    """
    # 1. ADF 平稳性检验
    adf_stat, adf_p, *_ = adfuller(returns, autolag='AIC')
    print(f"ADF 统计量: {adf_stat:.4f}, p={adf_p:.4f}")
    print("序列" + ("平稳" if adf_p < 0.05 else "非平稳，需差分"))

    # 2. 均值方程：简单去均值得到残差（也可以先拟合 AR 模型）
    resid = returns - returns.mean()

    # 3. 对残差平方项做 Ljung-Box 检验（检验 ARCH 效应）
    resid_sq = resid ** 2
    lb = acorr_ljungbox(resid_sq, lags=[5, 10, 20], return_df=True)
    lb.columns = ['LB统计量', 'p值']
    print("\n残差平方项 Ljung-Box 检验:")
    print(lb)

    arch_exists = (lb.iloc[:, 1] < 0.05).any()
    print("\n结论:" + ("存在 ARCH 效应，适合 GARCH" if arch_exists
                        else "无 ARCH 效应，可用普通方差模型"))
    return arch_exists
```

### 3.3 拟合 GARCH(1,1)

```python
from arch import arch_model
import numpy as np

def fit_garch(returns, p=1, q=1, dist='t', horizon=10):
    """
    拟合 GARCH(p,q) 并预测条件波动率
    dist: 'normal' | 't' | 'skewt'
    """
    # 均值方程设为常数 + GARCH 方差
    am = arch_model(returns, mean='Constant', vol='GARCH',
                    p=p, q=q, dist=dist, rescale=True)
    res = am.fit(disp='off')
    print(res.summary())

    # 条件波动率（σₜ，年化需 ×√252）
    sigma = res.conditional_volatility

    # 样本外预测
    forecast = res.forecast(horizon=horizon)
    var_forecast = forecast.variance.iloc[-1, :]  # 未来 horizon 期条件方差
    vol_forecast = np.sqrt(var_forecast)

    return res, sigma, vol_forecast
```

---

## 四、均值-方差组合投资（Markowitz）

### 4.1 模型原理

Markowitz 均值-方差模型在给定预期收益下最小化组合风险（方差）：

```
min_w   wᵀ·Σ·w
s.t.    μᵀ·w = r_target        （目标收益）
        1ᵀ·w = 1               （资金全部投入）
        w ≥ 0                  （可选：禁止卖空）

其中 μ：资产期望收益向量，Σ：收益协方差矩阵，w：权重向量
```

**有效前沿**：对不同 `r_target` 求解上述二次规划，得到收益-风险平面上的最优组合集合。使用 `cvxpy` 系表达简便。

### 4.2 建模步骤

```
1. 计算各资产对数收益率的均值向量 μ、协方差矩阵 Σ（年化）
2. 若 Σ 病态 → 使用 shrinkage（Ledoit-Wolf）收窄估计
3. 设定目标收益网格 r_target ∈ [min(μ), max(μ)]
4. 逐点求解二次规划 → 得到有效前沿
5. 无风险利率存在时 → 求切点组合（最大夏普比率）
```

### 4.3 代码要点

```python
import numpy as np
import cvxpy as cp

def markowitz_frontier(mu, Sigma, n_points=50, allow_short=False):
    """
    mu:  资产期望收益向量 (n,)
    Sigma: 协方差矩阵 (n,n)
    返回有效前沿的 (收益, 风险) 与对应的权重矩阵
    """
    n = len(mu)
    w = cp.Variable(n)
    rp = mu @ w
    risk = cp.quad_form(w, Sigma)

    constraints = [cp.sum(w) == 1]
    if not allow_short:
        constraints.append(w >= 0)

    r_min, r_max = float(mu.min()), float(mu.max())
    returns = np.linspace(r_min, r_max, n_points)

    results = []
    for rt in returns:
        prob = cp.Problem(cp.Minimize(risk), constraints + [rp == rt])
        prob.solve(solver=cp.ECOS)
        if w.value is not None:
            results.append((rt, np.sqrt(prob.value), w.value.copy()))

    return results

def tangent_portfolio(mu, Sigma, rf=0.0, allow_short=False):
    """无风险利率 rf 下的切点组合（最大夏普比率）"""
    n = len(mu)
    w = cp.Variable(n)
    excess = mu - rf
    ret = excess @ w
    risk = cp.quad_form(w, Sigma)
    constraints = [cp.sum(w) == 1]
    if not allow_short:
        constraints.append(w >= 0)
    # 最大化夏普比率的平方（等价于切点组合）
    prob = cp.Problem(cp.Maximize(ret / cp.sqrt(risk)), constraints)
    try:
        prob.solve(solver=cp.ECOS)
        return w.value
    except Exception:
        return None
```

### 4.4 协方差收缩估计

```python
from sklearn.covariance import LedoitWolf

def shrink_cov(returns):
    """Ledoit-Wolf 收缩估计：样本量小、维度高时更稳健"""
    lw = LedoitWolf()
    lw.fit(returns)          # returns: (T, n) 收益率矩阵
    Sigma = lw.covariance_
    mu = returns.mean(axis=0)
    return mu, Sigma
```

---

## 五、风险度量 VaR / CVaR

### 5.1 原理

- **VaR（在险价值）**：给定置信水平 α（如 95%），在一定持有期内可能遭受的**最大**损失，即损失分布的 α 分位数。`VaR_α = -quantile(r, 1-α)`
- **CVaR（条件在险价值 / Expected Shortfall）**：超过 VaR 的损失的**期望值**，是一致性风险度量（满足次可加性）。`CVaR_α = -E[r | r ≤ -VaR_α]`

| 方法 | 优点 | 缺点 |
|------|------|------|
| 参数法 VaR | 计算快 | 依赖正态假设，低估厚尾 |
| 历史模拟 VaR | 无分布假设 | 极端事件可能不在样本内 |
| GARCH-VaR | 波动时变，更贴合实际 | 需先建波动率模型 |
| CVaR | 满足次可加性，刻画尾部 | 对尾部估计敏感 |

### 5.2 代码要点

```python
import numpy as np

def var_cvar(returns, alpha=0.95):
    """returns: 组合或资产收益率数组，alpha: 置信水平"""
    var = -np.quantile(returns, 1 - alpha)
    tail = returns[returns <= -var]
    cvar = -tail.mean() if len(tail) > 0 else var
    return var, cvar

def garch_var(res, alpha=0.95, horizon=1):
    """基于 GARCH 条件波动率的一步 VaR（参数法）"""
    import scipy.stats as st
    mu = res.params.get('mu', 0.0)
    sigma_next = float(res.forecast(horizon=horizon).variance.iloc[-1, -1] ** 0.5)
    z = st.norm.ppf(1 - alpha)          # 正态假设下的分位数
    return -(mu + z * sigma_next)
```

---

## 六、竞赛常见场景

| 题型 | 题型含义 | 典型场景 | 推荐方法组合 |
|------|---------|---------|-------------|
| A | 物理建模 | 金融序列宏观建模（如收益率波动传导） | GARCH + 传导系数（溢出/动态相关） |
| B | 实验设计 | 不同投资策略/参数配置对比 | 多组策略历史回测 + 方差分析 + 夏普比率 |
| C | 数据分析 | 股价/基金净值波动率预测、风险预警 | GARCH(1,1) + 滚动样本外预测 + 回测指标 |
| C | 数据分析 | 多资产组合权重优化 | Markowitz + Ledoit-Wolf 收缩 + 有效前沿 |
| D | 优化调度 | 资金/资产配置优化 | 均值-方差（二次规划）+ 约束（含投资上限/最小持有） |
| E | 交叉学科 | 金融风控（量化金融 × 统计） | GARCH-VaR / CVaR + 历史模拟对比 |

---

## 七、常见陷阱与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| GARCH 参数不显著或 α+β>1 | 序列无 ARCH 效应或含结构突变 | 先做 ARCH 检验，分段/去突变 |
| 结果对样本区间极敏感 | 波动聚集导致局部最优 | 采用滚动窗口 + 多种分布/Spec 对比 AIC/BIC |
| 权重出现极端负值（卖空过大） | 未加 w≥0 约束 | 增加禁止卖空或权重上下限约束 |
| Σ 矩阵奇异不可逆 | 资产数接近样本数、高度相关 | Ledoit-Wolf 收缩 / 降维 |
| 均值 μ 估计不可靠导致前沿漂移 | 收益均值噪声大 | 用最小方差组合或 Black-Litterman |
| VaR 低估尾部风险 | 正态假设、厚尾 | 改用历史模拟或 CVaR，或 Student-t GARCH |
| 年化口径不一致 | 日/周/月数据混用 | 统一年化因子 √252 / √52 / √12 |

---

## 八、参考资源

- 教材：《金融时间序列分析》（Tsay）、《RiskMetrics 技术文档》
- Python 库：`arch`（GARCH）、`cvxpy`（二次规划）、`sklearn.covariance`（收缩）
- 扩展：`riskfolio-lib`（组合优化一站式）、`PyPortfolioOpt`

### 检查清单

- [ ] 收益率序列通过 ADF 平稳性检验
- [ ] 残差平方项 Ljung-Box 检验 p < 0.05（确认 ARCH 效应）
- [ ] GARCH 参数约束满足（ω>0, α,β≥0, α+β<1）
- [ ] 标准化残差近似白噪声
- [ ] 有效前沿单调、权重和为 1
- [ ] 夏普比率 / VaR / CVaR 口径一致并对齐到同一年化口径
- [ ] 随机种子固定 42，多次运行报告均值与标准差