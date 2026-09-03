# 养老金精算建模知识库

> 本文件提供数学建模竞赛中养老金精算相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 养老金缺口预测与预警
- 替代率（养老金/退休前工资）分析
- 政策参数（缴费率、退休年龄）敏感性分析
- 养老金基金收支平衡预测
- 人口老龄化对养老金体系的影响

### 1.2 常见约束条件
- 政策约束：法定退休年龄、最低缴费年限
- 精算约束：收支平衡、基金充足率
- 经济约束：工资增长率、通胀率、投资收益率
- 人口约束：死亡率、生育率、迁移率

### 1.3 数据特点
- 人口数据：年龄结构、死亡率表
- 经济数据：工资水平、增长率、通胀率
- 政策数据：缴费率、替代率、退休年龄
- 时间序列：历史缴费、历史支出

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| Logistic增长模型 | 人口/工资预测 | S型增长合理 | 长期预测偏差大 |
| 复利公式 | 基金余额计算 | 理论基础扎实 | 假设收益率固定 |
| 回归分析 | 参数关系建模 | 可解释性强 | 需要大量数据 |
| 缺口分析 | 收支平衡预测 | 直观易理解 | 假设条件多 |
| 精算现值法 | 养老金负债评估 | 国际标准方法 | 计算复杂 |
| Monte Carlo | 不确定性分析 | 考虑随机性 | 计算量大 |

---

## 3. 数学基础

### 3.1 工资增长预测

**Logistic增长模型**：
```
W(t) = W_max / (1 + e^(-k(t-t₀)))
```

其中：
- W(t): t年平均工资
- W_max: 工资上限（饱和值）
- k: 增长速率参数
- t₀: 拐点时间

**指数增长模型**：
```
W(t) = W₀ · (1 + g)^t
```

其中：
- W₀: 基期工资
- g: 年均工资增长率

### 3.2 替代率计算

**替代率定义**：
```
替代率 = 养老金 / 退休前工资 × 100%
```

**目标替代率**：
```
目标替代率 = (基本养老金 + 个人账户养老金) / 在职工资
```

**国际警戒线**：替代率低于40%则养老金不足。

### 3.3 基金余额建模

**精算平衡方程**：
```
B(t+1) = B(t) · (1 + r) + C(t) - P(t)
```

其中：
- B(t): t年末基金余额
- r: 基金投资收益率
- C(t): t年缴费收入
- P(t): t年养老金支出

**缴费收入**：
```
C(t) = N(t) · W(t) · c
```

其中：
- N(t): t年缴费人数
- c: 缴费率

**养老金支出**：
```
P(t) = Σ M(t,a) · B(a) · R(t,a)
```

其中：
- M(t,a): t年a岁退休人数
- B(a): a岁人均养老金
- R(t,a): 给付调整系数

### 3.4 缺口分析

**累计缺口**：
```
G(T) = Σ_{t=1}^{T} [P(t) - C(t)] · (1+r)^{T-t}
```

**年缺口率**：
```
g(t) = [P(t) - C(t)] / C(t)
```

---

## 4. 代码实现

### 4.1 Logistic工资增长模型

```python
import numpy as np
from scipy.optimize import curve_fit

def logistic_growth(t, W_max, k, t0):
    """
    Logistic增长模型
    
    Parameters
    ----------
    t : array
        时间
    W_max : float
        工资上限
    k : float
        增长速率
    t0 : float
        拐点时间
    
    Returns
    -------
    W : array
        工资预测值
    """
    return W_max / (1 + np.exp(-k * (t - t0)))


def fit_logistic(t_data, W_data):
    """
    拟合Logistic模型参数
    
    Parameters
    ----------
    t_data : array
        时间序列
    W_data : array
        工资数据
    
    Returns
    -------
    params : dict
        拟合参数
    """
    # 初始猜测
    p0 = [np.max(W_data) * 1.5, 0.1, np.mean(t_data)]
    
    # 拟合
    params, covariance = curve_fit(logistic_growth, t_data, W_data, p0=p0)
    
    return {
        'W_max': params[0],
        'k': params[1],
        't0': params[2],
        'covariance': covariance
    }


def predict_wage(t_future, params):
    """
    预测未来工资
    """
    return logistic_growth(t_future, params['W_max'], params['k'], params['t0'])
```

### 4.2 养老金基金余额模拟

```python
import numpy as np

def pension_fund_simulation(
    years=30,
    initial_fund=10000,  # 亿元
    contribution_rate=0.08,
    replacement_rate=0.4,
    wage_growth_rate=0.05,
    inflation_rate=0.03,
    investment_return=0.06,
    initial_workers=10000,  # 万人
    initial_retirees=3000,  # 万人
    retirement_age=60,
    life_expectancy=80
):
    """
    养老金基金余额模拟
    
    Parameters
    ----------
    years : int
        模拟年数
    initial_fund : float
        初始基金余额（亿元）
    contribution_rate : float
        缴费率
    replacement_rate : float
        替代率
    wage_growth_rate : float
        工资年增长率
    investment_return : float
        基金投资收益率
    
    Returns
    -------
    results : dict
        模拟结果
    """
    # 初始化
    fund_balance = initial_fund
    workers = initial_workers
    retirees = initial_retirees
    
    # 存储结果
    history = {
        'year': [],
        'fund_balance': [],
        'contribution': [],
        'pension': [],
        'gap': []
    }
    
    avg_wage = 5.0  # 初始平均工资（万元/年）
    
    for year in range(years):
        # 工资增长
        avg_wage *= (1 + wage_growth_rate)
        
        # 缴费收入
        contribution = workers * avg_wage * contribution_rate
        
        # 养老金支出
        pension = retirees * avg_wage * replacement_rate
        
        # 基金投资收益
        investment_income = fund_balance * investment_return
        
        # 更新基金余额
        fund_balance = fund_balance + investment_income + contribution - pension
        
        # 记录数据
        history['year'].append(year + 2020)
        history['fund_balance'].append(fund_balance)
        history['contribution'].append(contribution)
        history['pension'].append(pension)
        history['gap'].append(pension - contribution)
        
        # 人口变化（简化）
        workers = workers * 0.99  # 逐年减少1%
        retirees = retirees * 1.02  # 逐年增加2%
    
    return history
```

### 4.3 替代率分析

```python
import numpy as np

def replacement_rate_analysis(
    contribution_years=35,
    contribution_rate=0.08,
    wage_growth=0.05,
    investment_return=0.06,
    retirement_age=60,
    life_expectancy=80,
    average_wage=5.0
):
    """
    替代率分析
    
    Parameters
    ----------
    contribution_years : int
        缴费年限
    contribution_rate : float
        缴费率
    wage_growth : float
        工资增长率
    investment_return : float
        投资收益率
    
    Returns
    -------
    result : dict
        替代率分析结果
    """
    # 个人账户积累
    account_balance = 0
    annual_wage = average_wage
    
    for year in range(contribution_years):
        # 年缴费
        contribution = annual_wage * contribution_rate
        # 账户积累（复利）
        account_balance = (account_balance + contribution) * (1 + investment_return)
        # 工资增长
        annual_wage *= (1 + wage_growth)
    
    # 退休后领取年限
    payout_years = life_expectancy - retirement_age
    
    # 月养老金（简化：账户余额/领取月数）
    monthly_pension = (account_balance * 10000) / (payout_years * 12)  # 转换为元
    
    # 替代率
    retirement_wage = average_wage * (1 + wage_growth) ** contribution_years
    monthly_retirement_wage = retirement_wage * 10000 / 12
    
    replacement_rate = monthly_pension / monthly_retirement_wage
    
    return {
        'account_balance': account_balance,
        'monthly_pension': monthly_pension,
        'replacement_rate': replacement_rate,
        'payout_years': payout_years
    }
```

### 4.4 敏感性分析

```python
import numpy as np
import matplotlib.pyplot as plt

def sensitivity_analysis(base_params, param_ranges, n_samples=100):
    """
    参数敏感性分析
    
    Parameters
    ----------
    base_params : dict
        基准参数
    param_ranges : dict
        参数变化范围
    
    Returns
    -------
    sensitivity : dict
        敏感性结果
    """
    results = {}
    
    for param_name, (min_val, max_val) in param_ranges.items():
        values = np.linspace(min_val, max_val, n_samples)
        fund_balances = []
        
        for val in values:
            # 修改参数
            params = base_params.copy()
            params[param_name] = val
            
            # 运行模拟
            sim = pension_fund_simulation(**params)
            final_balance = sim['fund_balance'][-1]
            fund_balances.append(final_balance)
        
        results[param_name] = {
            'values': values,
            'fund_balances': np.array(fund_balances)
        }
    
    return results


def plot_sensitivity(sensitivity_results):
    """
    绘制敏感性分析图
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    for idx, (param_name, data) in enumerate(sensitivity_results.items()):
        if idx >= len(axes):
            break
        
        ax = axes[idx]
        ax.plot(data['values'], data['fund_balances'], 'b-', linewidth=2)
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        ax.set_xlabel(param_name)
        ax.set_ylabel('基金余额（亿元）')
        ax.set_title(f'{param_name} 敏感性分析')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 忽略通胀影响 | 实际购买力高估 | 使用实际工资而非名义工资 |
| 死亡率假设不当 | 养老金支出低估 | 使用生命表数据 |
| 收益率假设过高 | 基金余额虚高 | 使用保守收益率假设 |
| 人口结构变化忽略 | 缺口预测偏差 | 引入人口预测模型 |
| 单位换算错误 | 数量级错误 | 统一使用亿元和万人 |
| 未考虑政策变化 | 结果过时 | 加入政策调整情景 |

---

## 6. 验证方法

### 6.1 精算验证
- 检查收支平衡方程是否成立
- 验证复利计算是否正确
- 确认替代率在合理范围（40%-70%）

### 6.2 历史数据验证
- 与历史基金余额对比
- 与实际替代率对比
- 检验模型拟合优度

### 6.3 情景分析
- 乐观情景（高增长、高收益）
- 基准情景
- 悲观情景（低增长、低收益）

### 6.4 压力测试
- 极端参数下的模型表现
- 长期预测的稳定性
- 关键参数的临界值

---

## 7. 真题案例

### 2011C 养老金模型

**题目概述**：研究中国城镇职工基本养老保险基金的收支平衡问题，预测未来养老金缺口。

**关键信息**：
- 给定历史缴费和支出数据
- 需要预测未来30年基金余额
- 分析不同政策参数的影响

**解题思路**：
1. 建立Logistic工资增长模型
2. 构建基金余额动态方程
3. 进行参数标定和模型验证
4. 分析政策参数敏感性
5. 提出政策建议

**参考代码框架**：
```python
# 2011C问题求解框架
# 1. 数据准备
years = np.arange(2000, 2020)
wages = [...]  # 历史工资数据
fund_balance = [...]  # 历史基金余额

# 2. 拟合工资增长模型
params = fit_logistic(years, wages)

# 3. 模拟未来
simulation = pension_fund_simulation(years=30, **params)

# 4. 敏感性分析
param_ranges = {
    'contribution_rate': (0.06, 0.12),
    'replacement_rate': (0.3, 0.5)
}
sensitivity = sensitivity_analysis(params, param_ranges)
```

---

## 8. 参考文献

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| 2011C-A01 | Logistic+缺口分析 | 多情景预测 |
| 2011C-A02 | 精算现值法 | 国际比较 |
| 2011C-A03 | Monte Carlo | 不确定性量化 |

---

## 9. 验证清单

- [ ] 工资增长模型拟合优度R² > 0.95
- [ ] 替代率计算结果在40%-70%范围
- [ ] 基金余额方程平衡验证
- [ ] 敏感性分析覆盖关键参数
- [ ] 情景分析包含乐观/基准/悲观
- [ ] 人口结构变化已纳入模型
- [ ] 通胀和实际工资已区分
- [ ] 结果图表清晰规范
