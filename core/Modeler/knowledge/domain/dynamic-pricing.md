# 动态定价与库存管理领域知识

## 一、核心概念

### 1.1 动态定价
- **定义**: 根据市场需求、竞争、成本等因素实时调整价格
- **目标**: 最大化利润或市场份额
- **关键因素**: 需求弹性、库存水平、保质期、竞争

### 1.2 库存管理
- **订货点法**: 当库存降至订货点时补货
- **定期检查法**: 固定时间间隔检查补货
- **(s,S)策略**: 库存低于s时补货到S

### 1.3 价格弹性
```
弹性系数 Ed = (ΔQ/Q) / (ΔP/P)
```
- |Ed| > 1: 富有弹性（降价增加收入）
- |Ed| < 1: 缺乏弹性（涨价增加收入）
- |Ed| = 1: 单位弹性

---

## 二、定价模型

### 2.1 线性需求模型
```
Q = a - b*P + c*P_comp + d*Promo
```
- Q: 需求量
- P: 价格
- P_comp: 竞争价格
- Promo: 促销变量

### 2.2 指数需求模型
```
Q = A * P^(-ε) * exp(β*X)
```
- ε: 价格弹性
- X: 其他因素

### 2.3 蔬菜定价特点
- **易腐性**: 保质期短（1-3天）
- **季节性**: 供应波动大
- **替代性**: 品种间可替代
- **损耗率**: 高损耗（20-40%）

### 2.4 定价公式
```python
def vegetable_price(cost, elasticity, target_margin, freshness):
    """
    蔬菜定价模型
    cost: 进货成本
    elasticity: 价格弹性
    target_margin: 目标利润率
    freshness: 新鲜度系数 (0-1)
    """
    base_price = cost * (1 + target_margin)
    # 新鲜度折扣
    freshness_factor = 0.7 + 0.3 * freshness
    # 弹性调整
    elasticity_factor = 1 / (1 + abs(elasticity) * 0.1)
    return base_price * freshness_factor * elasticity_factor
```

---

## 三、库存优化

### 3.1 EOQ模型（经济订货量）
```
EOQ = sqrt(2*D*S/H)
D: 年需求量
S: 每次订货成本
H: 单位持有成本
```

### 3.2 蔬菜库存特点
- **保质期约束**: 必须在保质期内销售
- **需求不确定**: 每日需求波动
- **补货周期短**: 通常每天补货

### 3.3 报童模型（单周期）
```python
def newsvendor_model(demand_mean, demand_std, selling_price, cost, salvage_value):
    """
    报童模型最优订货量
    """
    from scipy.stats import norm
    cu = selling_price - cost  # 欠货成本
    cp = cost - salvage_value  # 超储成本
    critical_ratio = cu / (cu + cp)
    Q = norm.ppf(critical_ratio, demand_mean, demand_std)
    return Q
```

### 3.4 多周期库存模型
```python
def multi_period_inventory(demand_forecast, lead_time, safety_stock):
    """
    多周期库存管理
    """
    reorder_point = demand_forecast * lead_time + safety_stock
    return reorder_point
```

---

## 四、优化算法

### 4.1 利润最大化
```
max Profit = Σ(P_i * Q_i - C_i * Q_i - H * I_i)
s.t. Q_i ≤ I_i (库存约束)
     I_{i+1} = I_i + R_i - Q_i (库存平衡)
     P_min ≤ P_i ≤ P_max (价格约束)
```

### 4.2 遗传算法求解
```python
def optimize_pricing_ga(demand_model, inventory, costs, pop_size=100):
    """
    使用遗传算法优化定价策略
    """
    def chromosome():
        return np.random.uniform(P_min, P_max, n_periods)
    
    def fitness(prices):
        revenue = sum(prices[i] * demand_model(prices[i]) for i in range(n_periods))
        return revenue
    
    # 遗传算法迭代
    # ...
    return best_prices
```

### 4.3 动态规划求解
```python
def dynamic_pricing_dp(demand_func, inventory, periods):
    """
    动态规划求解多周期定价
    """
    # 状态: 当前库存
    # 决策: 价格
    # 转移: 库存变化
    
    V = np.zeros((periods + 1, max_inventory + 1))
    policy = np.zeros((periods, max_inventory + 1))
    
    for t in range(periods - 1, -1, -1):
        for s in range(max_inventory + 1):
            best_value = -np.inf
            best_price = P_min
            for p in np.linspace(P_min, P_max, 20):
                demand = demand_func(p)
                sales = min(demand, s)
                revenue = p * sales
                next_inventory = s - sales
                value = revenue + V[t + 1, next_inventory]
                if value > best_value:
                    best_value = value
                    best_price = p
            V[t, s] = best_value
            policy[t, s] = best_price
    
    return policy
```

---

## 五、需求预测

### 5.1 时间序列预测
- **移动平均**: 简单、加权
- **指数平滑**: α*实际 + (1-α)*预测
- **ARIMA**: 趋势+季节性

### 5.2 回归预测
```python
def demand_regression(data):
    """
    需求回归模型
    """
    from sklearn.linear_model import LinearRegression
    
    features = ['price', 'promotion', 'day_of_week', 'temperature']
    X = data[features]
    y = data['sales']
    
    model = LinearRegression()
    model.fit(X, y)
    
    return model
```

### 5.3 机器学习预测
- **随机森林**: 非线性关系
- **XGBoost**: 高精度
- **神经网络**: 复杂模式

---

## 六、论文写作要点

### 6.1 问题分析框架
1. **数据理解**: 销售数据、价格数据、库存数据
2. **需求分析**: 需求弹性、影响因素
3. **定价模型**: 目标函数、约束条件
4. **库存策略**: 补货点、订货量
5. **结果分析**: 利润提升、库存周转
6. **灵敏度分析**: 参数影响

### 6.2 图表规范
- **价格-需求曲线**: 弹性分析
- **库存变化图**: 时间序列
- **利润对比**: 策略对比
- **敏感性分析**: 参数影响

### 6.3 LaTeX代码
```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{pricing_strategy.pdf}
\caption{动态定价策略}
\label{fig:pricing}
\end{figure}

\begin{table}[htbp]
\centering
\caption{库存管理策略对比}
\begin{tabular}{lccc}
\hline
策略 & 平均利润 & 库存周转率 & 缺货率 \\
\hline
固定价格 & 1000 & 5.2 & 2.1\% \\
动态定价 & 1250 & 6.8 & 1.5\% \\
\hline
\end{tabular}
\end{table}
```

---

## 七、参考文献

1. 刘伟. 动态定价理论与应用. 科学出版社, 2018.
2. 贾俊平. 统计学. 中国人民大学出版社, 2018.
3. Nahmias S. Production and Operations Analysis. McGraw-Hill, 2009.
4. Cachon G. Supply Chain Management: Pricing and Coordination. 2003.
