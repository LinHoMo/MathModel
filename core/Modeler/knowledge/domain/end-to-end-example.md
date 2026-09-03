# 端到端竞赛案例演示

> 以2025年CUMCM C题为例，展示从问题分析到论文写作的完整流程。

---

## 一、案例选择

### 1.1 案例信息
- **题目**: 2025年CUMCM C题（蔬菜类商品定价与补货）
- **类型**: C题（数据分析）
- **获奖论文**: C050, C126, C228, C235

### 1.2 问题重述
某商超需要制定蔬菜类商品的：
1. 动态定价策略
2. 补货决策方案
3. 目标：最大化利润

---

## 二、问题分析（Step 1）

### 2.1 影响因素识别

```
输入因素：
├── 成本因素：进货成本、损耗成本、储存成本
├── 市场因素：需求弹性、竞争价格、季节性
├── 商品因素：保质期、库存、销售速度
└── 时间因素：时段、星期、节假日
```

### 2.2 建模假设

| 假设 | 内容 | 理由 |
|------|------|------|
| H1 | 需求服从泊松分布 | 蔬菜销售具有随机性 |
| H2 | 保质期内销售完 | 减少损耗 |
| H3 | 价格弹性已知 | 基于历史数据估计 |
| H4 | 每日补货一次 | 符合实际操作 |

### 2.3 技术路线图

```
数据理解 → 数据清洗 → 特征工程 → 需求预测 → 定价优化 → 补货决策
    ↓           ↓           ↓           ↓           ↓           ↓
  EDA报告    缺失值处理  价格弹性   时间序列    利润最大化   库存约束
```

---

## 三、数据预处理（Step 2）

### 3.1 数据探索

```python
# 使用EDA模板
from eda_template import EDAReport

reporter = EDAReport(df, target='sales')
report = reporter.generate_report()
```

### 3.2 数据清洗

```python
# 使用数据管道
from data_pipeline import DataPipeline

pipeline = DataPipeline(target_col='sales', task='regression')
X, y = pipeline.fit_transform(df)
```

### 3.3 特征工程

```python
# 价格弹性计算
df['price_elasticity'] = df.groupby('category')['sales'].transform(
    lambda x: (x.pct_change() / df['price'].pct_change()).rolling(7).mean()
)

# 时间特征
df['hour'] = pd.to_datetime(df['time']).dt.hour
df['day_of_week'] = pd.to_datetime(df['time']).dt.dayofweek
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
```

---

## 四、模型建立（Step 3）

### 4.1 需求预测模型

```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

# 特征选择
features = ['price', 'price_elasticity', 'temperature', 
            'hour', 'day_of_week', 'is_weekend', 'stock']

X = df[features]
y = df['sales']

# 训练模型
model = GradientBoostingRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
```

### 4.2 动态定价模型

```python
def dynamic_pricing(objective, constraints, bounds):
    """
    动态定价优化
    """
    from scipy.optimize import minimize
    
    def profit(prices):
        demands = model.predict(features_with_prices(prices))
        revenue = np.sum(prices * demands)
        cost = np.sum(cost_per_unit * demands)
        return -(revenue - cost)  # 最大化利润
    
    result = minimize(profit, x0, bounds=bounds, constraints=constraints)
    return result.x
```

### 4.3 补货决策模型

```python
def replenishment_decision(demand_forecast, current_stock, lead_time):
    """
    补货决策
    """
    safety_stock = 1.65 * np.std(demand_forecast) * np.sqrt(lead_time)
    reorder_point = np.mean(demand_forecast) * lead_time + safety_stock
    
    if current_stock < reorder_point:
        order_quantity = np.mean(demand_forecast) * (lead_time + 1) + safety_stock - current_stock
        return order_quantity
    return 0
```

---

## 五、模型求解（Step 4）

### 5.1 参数设置

```python
# 遗传算法参数
GA_PARAMS = {
    'pop_size': 100,
    'generations': 200,
    'crossover_rate': 0.8,
    'mutation_rate': 0.1
}

# 优化结果
optimal_prices = dynamic_pricing(profit, constraints, bounds)
optimal_replenishment = replenishment_decision(demand_forecast, stock, lead_time)
```

### 5.2 结果展示

```python
# 价格优化结果
print(f"最优定价: {optimal_prices}")
print(f"预期利润: {profit(optimal_prices):.2f}")

# 补货决策结果
print(f"补货数量: {optimal_replenishment}")
```

---

## 六、结果分析（Step 5）

### 6.1 灵敏度分析

```python
# 价格弹性敏感性
elasticities = np.linspace(0.5, 2.0, 10)
profits = []

for e in elasticities:
    df['price_elasticity'] = e
    model.fit(X_train, y_train)
    profits.append(profit(optimal_prices))

# 绘制敏感性曲线
plt.plot(elasticities, profits)
plt.xlabel('Price Elasticity')
plt.ylabel('Profit')
plt.title('Sensitivity Analysis')
```

### 6.2 对比实验

| 策略 | 利润 | 提升 |
|------|------|------|
| 固定价格 | 10000 | - |
| 动态定价 | 12500 | +25% |
| 动态定价+补货 | 14000 | +40% |

### 6.3 稳健性检验

```python
# 交叉验证
from sklearn.model_selection import cross_val_score

scores = cross_val_score(model, X, y, cv=5, scoring='r2')
print(f"R²: {scores.mean():.4f} ± {scores.std():.4f}")
```

---

## 七、论文写作（Step 6）

### 7.1 论文结构

```
1. 问题重述
2. 问题分析
3. 模型假设
4. 符号说明
5. 模型建立与求解
   5.1 需求预测模型
   5.2 动态定价模型
   5.3 补货决策模型
6. 结果分析
   6.1 灵敏度分析
   6.2 对比实验
   6.3 稳健性检验
7. 模型评价
   7.1 优点
   7.2 缺点
   7.3 改进方向
8. 参考文献
9. 附录
```

### 7.2 关键图表

1. **技术路线图**: 展示建模流程
2. **需求预测图**: 预测值vs实际值
3. **价格优化图**: 价格变化曲线
4. **利润对比图**: 不同策略对比
5. **敏感性分析图**: 参数影响

---

## 八、可借鉴点

### 8.1 建模技巧
- 需求预测作为定价的基础
- 价格弹性的动态估计
- 保质期约束的处理

### 8.2 写作技巧
- 问题分解清晰
- 假设说明完整
- 灵敏度分析深入

### 8.3 创新点
- 动态定价+补货联合优化
- 基于机器学习的需求预测
- 考虑损耗的成本模型

---

## 九、复现指南

### 9.1 环境准备

```bash
pip install numpy pandas scikit-learn matplotlib
```

### 9.2 数据准备

```python
# 加载数据
df = pd.read_csv('vegetable_sales.csv')
```

### 9.3 运行步骤

```python
# 1. 数据预处理
pipeline = DataPipeline(target_col='sales')
X, y = pipeline.fit_transform(df)

# 2. 需求预测
model = GradientBoostingRegressor()
model.fit(X_train, y_train)

# 3. 定价优化
optimal_prices = dynamic_pricing(profit, constraints, bounds)

# 4. 补货决策
optimal_replenishment = replenishment_decision(demand_forecast, stock, lead_time)
```

---

## 十、扩展思考

1. **如何处理多个商品的关联？** → 多商品联合优化
2. **如何考虑竞争对手？** → 博弈论模型
3. **如何处理不确定性？** → 随机规划
4. **如何实时更新？** → 在线学习
