# 数据挖掘建模知识库

> 本文件提供数学建模竞赛中数据挖掘相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 大型百货商场会员画像描绘
- 商超蔬菜类商品动态定价与补货决策
- 银行对中小微企业的信贷策略
- 农作物种植策略优化
- 机场出租车司机决策问题

### 1.2 常见约束条件
- 数据约束：数据质量、数据量、时效性
- 业务约束：成本、利润、风险
- 时间约束：决策周期、响应时间
- 资源约束：库存、人员、设备

### 1.3 数据特点
- 数据类型：结构化数据（表格）、时序数据
- 数据规模：中等规模（1000-100000条记录）
- 特征类型：数值特征、分类特征、时序特征
- 标签类型：有标签（分类/回归）、无标签（聚类）

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 随机森林 | 分类/回归 | 不易过拟合 | 可解释性差 |
| XGBoost | 分类/回归 | 精度高 | 需要调参 |
| K-Means | 聚类 | 简单快速 | 需预设K |
| 决策树 | 分类 | 可解释性强 | 容易过拟合 |
| 逻辑回归 | 二分类 | 概率输出 | 线性假设 |
| 时序模型 | 预测 | 考虑时间依赖 | 需要足够数据 |

---

## 3. 数学基础

### 3.1 会员画像（RFM/RFMS模型）

**RFM指标**：
- R (Recency)：最近购买距今天数
- F (Frequency)：购买频率
- M (Monetary)：消费金额

**RFMS指标**（扩展）：
- S (Score)：综合评分

**聚类分群**：
- 使用K-Means对RFM指标进行聚类
- 识别不同客户群体（高价值、低价值、流失风险等）

### 3.2 动态定价

**价格弹性模型**：
```
Q = a * P^b
```
其中：
- Q: 需求量
- P: 价格
- b: 价格弹性系数

**最优定价**：
```
max Profit = (P - C) * Q(P)
```
其中C为成本。

### 3.3 信贷决策

**信用评分模型**：
- 逻辑回归：P(default) = 1 / (1 + exp(-(β₀ + β₁x₁ + ...)))
- 随机森林：多棵树投票
- XGBoost：梯度提升

**风险评估**：
- 违约概率 (PD)
- 违约损失率 (LGD)
- 违约敞口 (EAD)

---

## 4. 代码实现

### 4.1 会员画像

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

def create_rfm_model(transactions, customer_id='customer_id', 
                     date_col='date', amount_col='amount'):
    """
    创建RFM模型
    
    Parameters
    ----------
    transactions : DataFrame
        交易数据
    customer_id : str
        客户ID列名
    date_col : str
        日期列名
    amount_col : str
        金额列名
    
    Returns
    -------
    rfm : DataFrame
        RFM指标
    """
    # 转换日期
    transactions[date_col] = pd.to_datetime(transactions[date_col])
    
    # 计算RFM
    current_date = transactions[date_col].max() + pd.Timedelta(days=1)
    
    rfm = transactions.groupby(customer_id).agg({
        date_col: lambda x: (current_date - x.max()).days,  # R
        customer_id: 'count',  # F
        amount_col: 'sum'  # M
    })
    
    rfm.columns = ['Recency', 'Frequency', 'Monetary']
    
    # 标准化
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm)
    
    return rfm, rfm_scaled, scaler

def segment_customers(rfm_scaled, n_clusters=4):
    """
    客户分群
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(rfm_scaled)
    
    return labels, kmeans
```

### 4.2 动态定价

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

def estimate_demand elasticity(price_data, quantity_data):
    """
    估计价格弹性
    
    Parameters
    ----------
    price_data : array
        价格数据
    quantity_data : array
        需求量数据
    
    Returns
    -------
    elasticity : float
        价格弹性系数
    """
    # 对数变换
    log_price = np.log(price_data)
    log_quantity = np.log(quantity_data)
    
    # 线性回归
    model = LinearRegression()
    model.fit(log_price.reshape(-1, 1), log_quantity)
    
    elasticity = model.coef_[0]
    
    return elasticity

def optimize_price(elasticity, cost, price_range=(1, 100)):
    """
    优化定价
    
    Parameters
    ----------
    elasticity : float
        价格弹性系数
    cost : float
        成本
    price_range : tuple
        价格范围
    
    Returns
    -------
    optimal_price : float
        最优价格
    max_profit : float
        最大利润
    """
    from scipy.optimize import minimize_scalar
    
    def profit(price):
        # 需求量（简化模型）
        quantity = 1000 * price ** elasticity  # 基准需求量1000
        return -(price - cost) * quantity  # 负号用于最小化
    
    result = minimize_scalar(profit, bounds=price_range, method='bounded')
    
    optimal_price = result.x
    max_profit = -result.fun
    
    return optimal_price, max_profit
```

### 4.3 信贷决策

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

def credit_scoring_model(data, target_col='default', test_size=0.2):
    """
    信用评分模型
    
    Parameters
    ----------
    data : DataFrame
        信贷数据
    target_col : str
        目标变量列名（是否违约）
    test_size : float
        测试集比例
    
    Returns
    -------
    model : 训练好的模型
    results : 评估结果
    """
    # 分离特征和目标
    X = data.drop(columns=[target_col])
    y = data[target_col]
    
    # 划分数据
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    # 训练模型
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 预测
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # 评估
    results = {
        'classification_report': classification_report(y_test, y_pred),
        'auc': roc_auc_score(y_test, y_prob),
        'feature_importance': dict(zip(X.columns, model.feature_importances_))
    }
    
    return model, results

def credit_decision(model, new_applications, threshold=0.5):
    """
    信贷决策
    
    Parameters
    ----------
    model : 训练好的模型
    new_applications : DataFrame
        新申请数据
    threshold : float
        违约概率阈值
    
    Returns
    -------
    decisions : DataFrame
        决策结果
    """
    # 预测违约概率
    prob_default = model.predict_proba(new_applications)[:, 1]
    
    # 决策
    decisions = pd.DataFrame({
        'application_id': range(len(new_applications)),
        'prob_default': prob_default,
        'decision': ['reject' if p > threshold else 'approve' for p in prob_default]
    })
    
    return decisions
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 数据泄露 | 测试集信息泄露 | 先划分再标准化 |
| 类别不平衡 | 少数类预测不准 | SMOTE/加权/调整阈值 |
| 过拟合 | 训练好测试差 | 交叉验证/正则化 |
| 未考虑时序 | 时序数据随机划分 | 时间序列划分 |
| 特征冗余 | 多重共线性 | 特征选择/VIF检验 |
| 外推风险 | 预测超出训练范围 | 声明适用范围 |

---

## 6. 验证方法

### 6.1 模型验证
- 交叉验证分数
- 测试集评估指标
- 混淆矩阵/ROC曲线

### 6.2 业务验证
- 与历史数据对比
- 专家判断
- A/B测试

### 6.3 灵敏度分析
- 各因素对结果的影响程度
- 关键因素识别
- 鲁棒性分析

---

## 7. 参考论文

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| C008 | RFMT+K-Means+决策树 | 会员画像 |
| C052 | RFMS+K-Means+随机森林 | 多模型对比 |
| C142 | 随机森林 | 信贷决策 |
| C228 | 价格弹性+回归 | 动态定价 |
| C126 | 多元回归 | 蔬菜销售预测 |

---

## 8. 代码模板参考

- 随机森林: `resources/code-templates/machine-learning/random_forest.py`
- K-Means聚类: `resources/code-templates/clustering/kmeans.py`

---

## 9. 验证清单

- [ ] 数据预处理完成（缺失值、异常值）
- [ ] 特征工程完成（编码、标准化）
- [ ] 模型选择合理（交叉验证）
- [ ] 模型评估指标完整
- [ ] 特征重要性已分析
- [ ] 业务解释合理
- [ ] 灵敏度分析已执行
- [ ] 代码中所有文件保存使用目录前缀
