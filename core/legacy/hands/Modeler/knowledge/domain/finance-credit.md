# 金融信贷建模知识库

> 本文件提供数学建模竞赛中金融信贷相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 银行信贷策略制定
- 贷款定价与风险评估
- 投资组合优化
- 信用评分卡模型
- 违约概率预测
- 风险价值(VaR/CVaR)计算
- 农作物种植风险管理

### 1.2 常见约束条件
- 资本约束：贷款总额上限、资本充足率
- 风险约束：不良贷款率、违约概率阈值
- 监管约束：行业集中度、单一客户限额
- 流动性约束：资金可用量、回收周期
- 收益约束：最低收益率要求
- 公平性约束：歧视性定价限制

### 1.3 数据特点
- 客户数据：收入、负债、信用记录、行业
- 贷款数据：金额、期限、利率、担保方式
- 违约数据：违约概率、损失率、回收率
- 市场数据：基准利率、行业景气指数
- 历史数据：违约样本通常较少（不平衡数据）

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 逻辑回归 | 违约预测 | 可解释性强 | 线性假设 |
| 决策树/随机森林 | 信用评分 | 处理非线性 | 容易过拟合 |
| TOPSIS评价 | 综合评价 | 无需权重假设 | 主观性较强 |
| 线性规划 | 资源配置 | 全局最优 | 需线性假设 |
| CVaR模型 | 风险度量 | 尾部风险控制 | 计算复杂 |
| 生存分析 | 违约时间预测 | 处理删失数据 | 模型复杂 |
| XGBoost | 违约预测 | 精度高 | 黑箱模型 |

---

## 3. 数学基础

### 3.1 信用评分模型（逻辑回归）

**违约概率**：
```
P(Y=1|X) = 1 / (1 + exp(-(β₀ + β₁x₁ + ... + βₙxₙ)))
Y=1: 违约
Y=0: 正常
```

**似然函数**：
```
L(β) = Πᵢ P(yᵢ|xᵢ)ʸⁱ × (1-P(yᵢ|xᵢ))¹⁻ʸⁱ
```

**WOE变换**：
```
WOE = ln(%坏客户 / %好客户)
IV = Σ (%坏客户 - %好客户) × WOE
IV > 0.3: 有效预测变量
```

### 3.2 贷款定价模型

**成本加成定价**：
```
贷款利率 = 资金成本 + 运营成本 + 风险成本 + 资本回报
r = r_f + c_ops + PD × LGD × EAD + r_equity × (EAD/Capital)
```

**风险调整定价**：
```
r* = r_f + β × (r_m - r_f) + 监管资本成本
β: 系统性风险系数
```

### 3.3 风险价值(VaR/CVaR)

**VaR (Value at Risk)**：
```
P(Loss > VaR_α) = 1 - α
即：在置信度α下，最大损失不超过VaR
```

**CVaR (Conditional VaR)**：
```
CVaR_α = E[Loss | Loss > VaR_α]
即：超过VaR时的平均损失（尾部风险）
```

### 3.4 线性规划（信贷分配）

```
max 目标函数: Σ wᵢ × xᵢ
s.t. 约束条件:
  Σ xᵢ ≤ Budget  (资金约束)
  xᵢ ≤ Cap_i     (单笔上限)
  xᵢ ≥ Min_i     (最低额度)
  Risk(Σ xᵢ) ≤ Risk_Limit  (风险约束)
```

### 3.5 TOPSIS评价

```
步骤:
1. 构建决策矩阵 X = [xᵢⱼ]ₘ×ₙ
2. 标准化: rᵢⱼ = xᵢⱼ / √(Σxᵢⱼ²)
3. 加权: vᵢⱼ = wⱼ × rᵢⱼ
4. 正理想解: A⁺ = {max(vᵢⱼ)} (效益型)
   负理想解: A⁻ = {min(vᵢⱼ)}
5. 距离: D⁺ = √(Σ(vᵢⱼ-vⱼ⁺)²), D⁻ = √(Σ(vᵢⱼ-vⱼ⁻)²)
6. 相对接近度: Cᵢ = D⁻ / (D⁺ + D⁻)
```

---

## 4. Python实现

### 4.1 逻辑回归信用评分

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report

def credit_scoring_model(X, y, test_size=0.3):
    """
    逻辑回归信用评分模型
    
    Parameters
    ----------
    X : DataFrame
        特征变量
    y : array
        违约标签 (0/1)
    
    Returns
    -------
    model : LogisticRegression
        训练好的模型
    metrics : dict
        评估指标
    """
    # 划分训练集/测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    # 逻辑回归
    model = LogisticRegression(
        penalty='l2', C=1.0, class_weight='balanced',
        max_iter=1000, random_state=42
    )
    model.fit(X_train, y_train)
    
    # 预测
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    
    # 评估
    auc = roc_auc_score(y_test, y_pred_proba)
    
    # 特征重要性（系数）
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'coefficient': model.coef_[0],
        'odds_ratio': np.exp(model.coef_[0])
    }).sort_values('coefficient', ascending=False)
    
    metrics = {
        'auc': auc,
        'classification_report': classification_report(y_test, y_pred),
        'feature_importance': feature_importance
    }
    
    return model, metrics

def calculate_woe_iv(X, y, n_bins=10):
    """
    计算WOE和IV值
    
    Parameters
    ----------
    X : Series
        特征变量
    y : Series
        违约标签
    
    Returns
    -------
    woe_df : DataFrame
        WOE值
    iv : float
        IV值
    """
    df = pd.DataFrame({'feature': X, 'target': y})
    df['bin'] = pd.qcut(df['feature'], n_bins, duplicates='drop')
    
    # 统计每组好坏客户数
    grouped = df.groupby('bin')['target'].agg(['count', 'sum'])
    grouped.columns = ['total', 'bad']
    grouped['good'] = grouped['total'] - grouped['bad']
    
    # 计算占比
    grouped['pct_bad'] = grouped['bad'] / grouped['bad'].sum()
    grouped['pct_good'] = grouped['good'] / grouped['good'].sum()
    
    # WOE
    grouped['woe'] = np.log(grouped['pct_bad'] / grouped['pct_good'])
    
    # IV
    grouped['iv'] = (grouped['pct_bad'] - grouped['pct_good']) * grouped['woe']
    iv = grouped['iv'].sum()
    
    return grouped, iv
```

### 4.2 TOPSIS评价模型

```python
import numpy as np

def topsis_evaluation(decision_matrix, weights, benefit_criteria=None):
    """
    TOPSIS综合评价
    
    Parameters
    ----------
    decision_matrix : array
        决策矩阵 (m×n)，m个方案，n个指标
    weights : array
        权重向量
    benefit_criteria : array
        效益型指标索引（默认全部为效益型）
    
    Returns
    -------
    scores : array
        相对接近度
    rankings : array
        排名
    """
    m, n = decision_matrix.shape
    
    if benefit_criteria is None:
        benefit_criteria = np.arange(n)
    
    # 标准化
    norm_matrix = decision_matrix / np.sqrt(np.sum(decision_matrix**2, axis=0))
    
    # 加权
    weighted_matrix = norm_matrix * weights
    
    # 正理想解和负理想解
    ideal_best = np.max(weighted_matrix[:, benefit_criteria], axis=0)
    ideal_worst = np.min(weighted_matrix[:, benefit_criteria], axis=0)
    
    # 距离计算
    dist_best = np.sqrt(np.sum((weighted_matrix - ideal_best)**2, axis=1))
    dist_worst = np.sqrt(np.sum((weighted_matrix - ideal_worst)**2, axis=1))
    
    # 相对接近度
    scores = dist_worst / (dist_best + dist_worst)
    
    # 排名
    rankings = np.argsort(-scores) + 1
    
    return scores, rankings

# 示例：银行信贷策略
def bank_credit_strategy(applicants, risk_scores, loan_amounts, interest_rates):
    """
    银行信贷策略优化
    
    Parameters
    ----------
    applicants : array
        申请人特征矩阵
    risk_scores : array
        风险评分（0-1）
    loan_amounts : array
        申请贷款金额
    interest_rates : array
        建议利率
    
    Returns
    -------
    decisions : array
        贷款决策（1=批准，0=拒绝）
    """
    n = len(risk_scores)
    
    # 约束条件
    max_total_loan = 1e9  # 总贷款上限
    max_single_loan = 1e7  # 单笔上限
    max_risk_ratio = 0.05  # 最大违约率
    
    # 目标：最大化预期收益
    # 预期收益 = 利息收入 × (1 - 违约概率) - 违约损失 × 违约概率
    
    decisions = np.zeros(n)
    
    # 按风险评分排序，优先批准低风险
    sorted_idx = np.argsort(risk_scores)
    
    total_loan = 0
    approved_count = 0
    
    for i in sorted_idx:
        if risk_scores[i] > 0.3:  # 高风险拒绝
            continue
        
        if total_loan + loan_amounts[i] > max_total_loan:
            continue
        
        if loan_amounts[i] > max_single_loan:
            continue
        
        # 批准
        decisions[i] = 1
        total_loan += loan_amounts[i]
        approved_count += 1
    
    return decisions
```

### 4.3 CVaR风险计算

```python
import numpy as np

def calculate_var(returns, confidence=0.95):
    """
    计算VaR (历史模拟法)
    
    Parameters
    ----------
    returns : array
        收益率序列
    confidence : float
        置信度
    
    Returns
    -------
    var : float
        VaR值
    """
    return np.percentile(returns, (1 - confidence) * 100)

def calculate_cvar(returns, confidence=0.95):
    """
    计算CVaR (条件风险价值)
    
    Parameters
    ----------
    returns : array
        收益率序列
    confidence : float
        置信度
    
    Returns
    -------
    cvar : float
        CVaR值
    """
    var = calculate_var(returns, confidence)
    return np.mean(returns[returns <= var])

def portfolio_cvar_optimization(expected_returns, cov_matrix, target_return, confidence=0.95):
    """
    CVaR投资组合优化
    
    Parameters
    ----------
    expected_returns : array
        预期收益率
    cov_matrix : array
        协方差矩阵
    target_return : float
        目标收益率
    confidence : float
        置信度
    
    Returns
    -------
    weights : array
        最优权重
    """
    from scipy.optimize import minimize
    
    n = len(expected_returns)
    
    def objective(weights):
        # 组合收益
        portfolio_return = np.dot(weights, expected_returns)
        
        # 模拟组合收益
        np.random.seed(42)
        n_simulations = 10000
        simulated_returns = np.random.multivariate_normal(
            expected_returns, cov_matrix, n_simulations
        )
        portfolio_simulated = np.dot(simulated_returns, weights)
        
        # 计算CVaR
        cvar = calculate_cvar(portfolio_simulated, confidence)
        
        return -cvar  # 最小化负CVaR = 最大化CVaR
    
    # 约束
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # 权重和为1
        {'type': 'ineq', 'fun': lambda w: np.dot(w, expected_returns) - target_return}
    ]
    
    # 边界
    bounds = [(0, 1) for _ in range(n)]
    
    # 优化
    result = minimize(objective, np.ones(n)/n, method='SLSQP',
                     bounds=bounds, constraints=constraints)
    
    return result.x
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 样本不平衡 | 模型偏向多数类 | 使用class_weight='balanced'或过采样 |
| 过拟合 | 训练集AUC高，测试集低 | 正则化、交叉验证 |
| 多重共线性 | 系数不稳定 | VIF检验、特征选择 |
| 忽略时间效应 | 违约预测偏差 | 加入时间窗口、趋势特征 |
| 定价忽略风险 | 高风险客户定价过低 | 风险调整定价 |
| CVaR计算样本不足 | 风险估计偏差 | 增加模拟次数、使用参数法 |
| 监管约束遗漏 | 策略不可实施 | 加入监管约束条件 |

---

## 6. 验证方法

### 6.1 模型评估
```
AUC > 0.7: 良好
KS值 > 0.3: 区分能力好
Gini系数 = 2×AUC - 1
```

### 6.2 风险回测
```
VaR回测: 实际损失 > VaR 的比例应接近 (1-置信度)
Kupiec检验: 检验违约频率是否符合预期
```

### 6.3 策略验证
- 贷款组合的预期违约率 vs 实际违约率
- 利息收入 vs 预期收益
- 资本充足率是否达标

### 6.4 稳定性检验
- PSI (Population Stability Index) < 0.1: 稳定
- 特征重要性在不同时间段一致

---

## 7. 真题案例

### 案例1：2020C 银行信贷策略

**问题核心**：基于客户数据制定信贷策略，最大化利润同时控制风险

**建模要点**：
1. 客户违约概率预测（逻辑回归/XGBoost）
2. 贷款定价模型（风险调整定价）
3. 资源配置优化（线性规划）
4. 风险约束（VaR/CVaR）

**典型解法**：
```
1. 特征工程：收入、负债比、信用记录等
2. 违约预测：逻辑回归或随机森林
3. 定价：r = 基准利率 + 风险溢价
4. 优化：线性规划求解最优贷款分配
5. 风险控制：设定VaR约束
```

### 案例2：2024C 农作物种植CVaR风险管理

**问题核心**：在价格波动下优化种植结构，控制尾部风险

**建模要点**：
1. 农产品价格波动模型
2. 产量不确定性
3. CVaR风险度量
4. 种植面积优化

---

## 8. 代码模板参考

- 逻辑回归: `sklearn.linear_model.LogisticRegression`
- 随机森林: `sklearn.ensemble.RandomForestClassifier`
- 线性规划: `scipy.optimize.linprog`
- CVaR优化: `scipy.optimize.minimize`

---

## 9. 验证清单

- [ ] 违约标签定义清晰（0/1）
- [ ] 特征标准化处理
- [ ] 样本不平衡已处理
- [ ] 模型AUC > 0.7
- [ ] 贷款定价包含风险成本
- [ ] 约束条件完整（资金、风险、监管）
- [ ] CVaR计算方法正确
- [ ] 策略可实施、可解释

---

## 10. 参考文献

1. 牛播恩. 信用风险管理. 中国金融出版社, 2018.
2. Basel Committee. Basel III: Finalising post-crisis reforms. 2017.
3. Hull J C. Risk Management and Financial Institutions. Wiley, 2018.
4. 陈雨露. 金融学. 中国人民大学出版社, 2019.
