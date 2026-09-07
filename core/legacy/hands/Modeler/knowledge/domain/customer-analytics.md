# 客户分析与零售建模知识库

> 本文件提供数学建模竞赛中客户分析与零售相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 会员画像与客户分群
- 动态定价策略优化
- 超市补货策略设计
- 客户流失预测
- 商品关联分析（购物篮分析）
- 促销效果评估
- 客户生命周期价值(CLV)计算

### 1.2 常见约束条件
- 库存约束：最大/最小库存量、订货周期
- 价格约束：价格上下限、折扣范围
- 需求约束：季节性波动、促销影响
- 预算约束：营销预算、库存资金占用
- 时间约束：保质期、补货提前期
- 竞争约束：市场占有率、竞品价格

### 1.3 数据特点
- 交易数据：购买时间、商品、数量、金额
- 客户数据：会员信息、消费频次、偏好
- 商品数据：类别、价格、成本、库存
- 时间序列：销售趋势、季节性、周期性
- 缺失数据：部分会员信息不完整

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| RFM/RFMT模型 | 客户价值分析 | 简单直观 | 仅考虑历史行为 |
| K-Means聚类 | 客户分群 | 计算高效 | 需预设K值 |
| 关联规则(Apriori) | 购物篮分析 | 发现商品关联 | 规则数量多 |
| 价格弹性模型 | 定价优化 | 理论基础扎实 | 需要需求数据 |
| Logistic回归 | 流失预测 | 可解释性强 | 线性假设 |
| 生存分析 | 客户生命周期 | 处理删失数据 | 模型复杂 |
| 强化学习 | 动态定价 | 自适应 | 训练数据需求大 |

---

## 3. 数学基础

### 3.1 RFM模型

```
R (Recency): 最近一次购买距今天数
F (Frequency): 购买频次
M (Monetary): 消费金额

客户价值评分 = w₁f(R) + w₂f(F) + w₃f(M)
其中 f() 为标准化函数
```

**RFMT模型**（加入时间维度）：
```
T (Time): 客户活跃时长
RFMT = R × F × M × T
```

### 3.2 K-Means聚类

**目标函数**：
```
min J = Σᵢ₌₁ᴷ Σₓ∈Cᵢ ||x - μᵢ||²
μᵢ: 第i个聚类中心
Cᵢ: 第i个聚类
```

**聚类评估指标**：
```
轮廓系数: s(i) = (b(i) - a(i)) / max(a(i), b(i))
a(i): 样本i到同簇其他点的平均距离
b(i): 样本i到最近异簇点的平均距离
s(i) ∈ [-1, 1]，越大越好
```

### 3.3 价格弹性

**需求价格弹性**：
```
E = (ΔQ/Q) / (ΔP/P) = (dQ/dP) × (P/Q)
```

**弹性与收入关系**：
```
|E| > 1: 富有弹性，降价增加收入
|E| = 1: 单位弹性
|E| < 1: 缺乏弹性，涨价增加收入
```

### 3.4 客户生命周期价值(CLV)

```
CLV = Σₜ₌₁ᵀ [(m × rᵗ) / (1 + d)ᵗ] - C
m: 每期利润贡献
r: 客户留存率
d: 折现率
T: 预测期
C: 获客成本
```

**简化公式**：
```
CLV = m × r / (1 + d - r)
```

### 3.5 关联规则

**支持度**：
```
support(A→B) = P(A∪B) = count(A∪B) / N
```

**置信度**：
```
confidence(A→B) = P(B|A) = count(A∪B) / count(A)
```

**提升度**：
```
lift(A→B) = confidence(A→B) / P(B)
lift > 1 表示正相关
```

---

## 4. Python实现

### 4.1 RFM分析与客户分群

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def rfm_analysis(transactions_df, reference_date=None):
    """
    RFM分析与客户分群
    
    Parameters
    ----------
    transactions_df : DataFrame
        交易数据，包含列: customer_id, purchase_date, amount
    reference_date : datetime
        参考日期（计算R值的基准）
    
    Returns
    -------
    rfm_df : DataFrame
        RFM结果
    labels : array
        客户分群标签
    """
    if reference_date is None:
        reference_date = transactions_df['purchase_date'].max() + pd.Timedelta(days=1)
    
    # 计算RFM值
    rfm = transactions_df.groupby('customer_id').agg({
        'purchase_date': lambda x: (reference_date - x.max()).days,  # R
        'customer_id': 'count',  # F
        'amount': 'sum'  # M
    }).rename(columns={
        'purchase_date': 'Recency',
        'customer_id': 'Frequency',
        'amount': 'Monetary'
    })
    
    # 标准化
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm)
    
    # K-Means聚类
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = kmeans.fit_predict(rfm_scaled)
    
    rfm['Segment'] = labels
    
    # 分群解释
    segment_names = {0: '高价值', 1: '流失风险', 2: '新客户', 3: '低价值'}
    rfm['Segment_Name'] = rfm['Segment'].map(segment_names)
    
    return rfm, labels

def rfm_score(rfm_df, bins=5):
    """
    RFM评分（分位数法）
    """
    rfm_scored = rfm_df.copy()
    
    # R值越小越好（最近购买），所以反向打分
    rfm_scored['R_Score'] = pd.qcut(rfm_scored['Recency'], bins, 
                                      labels=range(bins, 0, -1))
    rfm_scored['F_Score'] = pd.qcut(rfm_scored['Frequency'].rank(method='first'), 
                                      bins, labels=range(1, bins+1))
    rfm_scored['M_Score'] = pd.qcut(rfm_scored['Monetary'].rank(method='first'), 
                                      bins, labels=range(1, bins+1))
    
    rfm_scored['Total_Score'] = (rfm_scored['R_Score'].astype(int) + 
                                   rfm_scored['F_Score'].astype(int) + 
                                   rfm_scored['M_Score'].astype(int))
    
    return rfm_scored
```

### 4.2 关联规则分析

```python
import pandas as pd
from itertools import combinations

def apriori_algorithm(transactions, min_support=0.1, min_confidence=0.5):
    """
    Apriori关联规则算法
    
    Parameters
    ----------
    transactions : list of lists
        交易列表，每个交易为商品列表
    min_support : float
        最小支持度
    min_confidence : float
        最小置信度
    
    Returns
    -------
    rules : list of dict
        关联规则列表
    """
    # 统计商品频率
    n_transactions = len(transactions)
    item_counts = {}
    
    for transaction in transactions:
        for item in transaction:
            item_counts[item] = item_counts.get(item, 0) + 1
    
    # 过滤频繁项集
    frequent_items = {item: count/n_transactions 
                      for item, count in item_counts.items() 
                      if count/n_transactions >= min_support}
    
    # 生成频繁2-项集
    frequent_pairs = {}
    for t in transactions:
        for i, j in combinations(t, 2):
            if i in frequent_items and j in frequent_items:
                pair = tuple(sorted([i, j]))
                frequent_pairs[pair] = frequent_pairs.get(pair, 0) + 1
    
    frequent_pairs = {pair: count/n_transactions 
                      for pair, count in frequent_pairs.items() 
                      if count/n_transactions >= min_support}
    
    # 生成关联规则
    rules = []
    for pair, support in frequent_pairs.items():
        # 计算置信度
        conf_12 = support / frequent_items[pair[0]]
        conf_21 = support / frequent_items[pair[1]]
        
        if conf_12 >= min_confidence:
            rules.append({
                'antecedent': pair[0],
                'consequent': pair[1],
                'support': support,
                'confidence': conf_12,
                'lift': conf_12 / frequent_items[pair[1]]
            })
        
        if conf_21 >= min_confidence:
            rules.append({
                'antecedent': pair[1],
                'consequent': pair[0],
                'support': support,
                'confidence': conf_21,
                'lift': conf_21 / frequent_items[pair[0]]
            })
    
    return rules
```

### 4.3 动态定价模型

```python
import numpy as np

def price_elasticity_model(prices, demands):
    """
    估计价格弹性
    
    Parameters
    ----------
    prices : array
        价格序列
    demands : array
        需求序列
    
    Returns
    -------
    elasticity : float
        价格弹性系数
    """
    # 对数线性回归: ln(Q) = a + b*ln(P)
    log_p = np.log(prices)
    log_d = np.log(demands)
    
    # 最小二乘拟合
    A = np.vstack([log_p, np.ones(len(log_p))]).T
    b, a = np.linalg.lstsq(A, log_d, rcond=None)[0]
    
    return b  # 弹性系数

def optimal_price(elasticity, marginal_cost, base_price=100):
    """
    计算最优价格（基于弹性）
    
    Parameters
    ----------
    elasticity : float
        价格弹性（负值）
    marginal_cost : float
        边际成本
    base_price : float
        基准价格
    
    Returns
    -------
    optimal_p : float
        最优价格
    """
    # Lerner指数: (P - MC) / P = -1/E
    # P = MC / (1 + 1/E)
    optimal_p = marginal_cost / (1 + 1/elasticity)
    
    return optimal_p

def dynamic_pricing_simulation(demand_func, cost, price_range, n_periods=30):
    """
    动态定价模拟
    
    Parameters
    ----------
    demand_func : callable
        需求函数 demand_func(price)
    cost : float
        单位成本
    price_range : tuple
        价格范围 (min, max)
    
    Returns
    -------
    prices : array
        各期价格
    profits : array
        各期利润
    """
    prices = np.zeros(n_periods)
    profits = np.zeros(n_periods)
    
    current_price = np.mean(price_range)
    
    for t in range(n_periods):
        # 简单搜索最优价格
        best_price = current_price
        best_profit = 0
        
        for p in np.linspace(price_range[0], price_range[1], 50):
            demand = demand_func(p)
            profit = (p - cost) * demand
            if profit > best_profit:
                best_profit = profit
                best_price = p
        
        prices[t] = best_price
        profits[t] = best_profit
        
        # 更新价格（加入随机扰动）
        current_price = best_price + np.random.normal(0, 0.5)
        current_price = np.clip(current_price, price_range[0], price_range[1])
    
    return prices, profits
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| RFM标准化错误 | 聚类结果偏向某指标 | 使用Z-score或Min-Max标准化 |
| K值选择不当 | 轮廓系数低 | 肘部法则+轮廓系数综合判断 |
| 关联规则过多 | 无法筛选有效规则 | 提高支持度/置信度阈值 |
| 弹性估计偏差 | 定价策略失效 | 使用工具变量或实验数据 |
| 忽略季节性 | 需求预测偏差 | 加入时间序列分解 |
| 样本偏差 | 分群结果不具代表性 | 确保样本随机性 |
| 过度拟合 | 模型泛化能力差 | 交叉验证、正则化 |

---

## 6. 验证方法

### 6.1 聚类效果验证
```
轮廓系数 > 0.5: 良好
Calinski-Harabasz指数: 越大越好
```

### 6.2 关联规则验证
- 提升度 > 1 表示有效规则
- 与业务直觉一致

### 6.3 弹性模型验证
- 与行业基准对比（通常-1到-3）
- 预测需求与实际需求的拟合度

### 6.4 定价策略验证
- 利润率是否提升
- 销量变化是否符合预期
- 客户反馈是否正面

---

## 7. 真题案例

### 案例1：2018C 会员画像与精准营销

**问题核心**：基于会员消费数据进行客户分群和个性化推荐

**建模要点**：
1. RFM模型计算客户价值
2. K-Means聚类进行客户分群
3. 关联规则挖掘商品组合
4. 针对不同群体制定营销策略

**典型解法**：
```
1. 数据清洗：处理缺失值、异常值
2. RFM计算：统计每个会员的R、F、M值
3. 标准化：Z-score标准化
4. 聚类：K-Means分4-5类
5. 分析：每类客户的特征画像
6. 策略：针对高价值客户提升服务，对流失风险客户进行召回
```

### 案例2：2025C 超市定价与补货策略

**问题核心**：优化商品定价和补货策略，最大化利润

**建模要点**：
1. 需求预测模型
2. 价格弹性估计
3. 库存优化（EOQ模型）
4. 动态定价策略

---

## 8. 代码模板参考

- 聚类: `sklearn.cluster.KMeans`
- 关联规则: `mlxtend.frequent_patterns`
- 回归: `sklearn.linear_model`
- 数据处理: `pandas`

---

## 9. 验证清单

- [ ] RFM值计算正确（R越小越好）
- [ ] 标准化方法合适
- [ ] K值选择经过验证
- [ ] 关联规则支持度/置信度阈值合理
- [ ] 价格弹性符号正确（通常为负）
- [ ] 库存模型考虑了提前期
- [ ] 利润计算包含所有成本
- [ ] 策略可实施、可解释

---

## 10. 参考文献

1. 陈启杰. 市场营销调研. 高等教育出版社, 2018.
2. Kotler P. Marketing Management. Pearson, 2016.
3. Han J. Data Mining: Concepts and Techniques. Morgan Kaufmann, 2011.
4. 王永贵. 客户关系管理. 清华大学出版社, 2019.
