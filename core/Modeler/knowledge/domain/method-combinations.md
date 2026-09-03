# 方法组合库

> 从117篇获奖论文中提取的"非常规"方法组合，展示如何将多个方法有机融合。

---

## 一、优化类组合

### 1.1 GA + 响应面法 (RSM)
**来源**: B196, C038, C094
**思路**: 用GA搜索全局最优，用RSM构建代理模型加速

```python
# 组合逻辑
def ga_rsm_combination(objective_func, bounds, n_initial=20):
    """
    GA-RSM组合优化
    """
    # 1. 初始采样
    initial_points = latin_hypercube_sampling(n_initial, bounds)
    initial_values = [objective_func(x) for x in initial_points]
    
    # 2. 构建RSM代理模型
    rsm_model = fit_response_surface(initial_points, initial_values)
    
    # 3. 用GA优化RSM
    def surrogate(x):
        return rsm_model.predict(x.reshape(1, -1))[0]
    
    best_x, best_y = genetic_algorithm(surrogate, bounds)
    
    # 4. 用真实函数验证
    true_y = objective_func(best_x)
    
    return best_x, true_y
```

**优势**: 减少真实函数调用次数，适合计算昂贵的问题

### 1.2 遗传算法 + 模拟退火 (GA+SA)
**来源**: B196
**思路**: GA提供全局搜索，SA局部精细搜索

```python
def ga_sa_hybrid(population, objective, generations=100):
    """
    GA-SA混合算法
    """
    # GA阶段
    for gen in range(generations // 2):
        population = ga_step(population, objective)
    
    # SA阶段
    best = get_best(population)
    best = simulated_annealing(best, objective, T0=100)
    
    return best
```

**优势**: 兼顾全局搜索和局部精细

### 1.3 粒子群 + 蚁群 (PSO+ACO)
**来源**: B196
**思路**: PSO连续空间搜索，ACO离散组合优化

---

## 二、回归/分类组合

### 2.1 多元回归 + 神经网络
**来源**: B050
**思路**: 回归捕获线性关系，NN捕获非线性

```python
def regression_nn_ensemble(X, y):
    """
    回归+神经网络集成
    """
    # 线性部分
    lr = LinearRegression()
    lr.fit(X, y)
    y_linear = lr.predict(X)
    
    # 非线性部分（残差）
    residuals = y - y_linear
    nn = MLPRegressor()
    nn.fit(X, residuals)
    y_nonlinear = nn.predict(X)
    
    # 集成
    y_pred = y_linear + y_nonlinear
    
    return y_pred
```

### 2.2 XGBoost + Logistic回归
**来源**: C109
**思路**: XGBoost特征提取，LR可解释性

### 2.3 PCA + 随机森林
**来源**: C155, C229
**思路**: PCA降维去除噪声，RF分类

---

## 三、时间序列组合

### 3.1 ARIMA + 神经网络
**来源**: 通用方法
**思路**: ARIMA线性趋势，NN残差

```python
def arima_nn_hybrid(series, steps):
    """
    ARIMA-NN混合预测
    """
    # ARIMA预测
    arima_model = ARIMA(series)
    arima_pred = arima_model.forecast(steps)
    
    # 残差预测
    residuals = series - arima_model.fittedvalues
    nn = LSTM()
    nn.fit(residuals)
    nn_pred = nn.predict(steps)
    
    # 集成
    final_pred = arima_pred + nn_pred
    
    return final_pred
```

---

## 四、聚类/分类组合

### 4.1 K-Means + 随机森林
**来源**: C008, C052, C101
**思路**: K-Means聚类发现模式，RF解释

```python
def kmeans_rf_pipeline(X, y, n_clusters=3):
    """
    K-Means + RF管道
    """
    # 聚类
    kmeans = KMeans(n_clusters=n_clusters)
    clusters = kmeans.fit_predict(X)
    
    # 每个簇训练RF
    models = {}
    for c in range(n_clusters):
        mask = clusters == c
        rf = RandomForestClassifier()
        rf.fit(X[mask], y[mask])
        models[c] = rf
    
    return kmeans, models
```

### 4.2 层次聚类 + SVM
**来源**: C065
**思路**: 层次聚类发现结构，SVM精细分类

---

## 五、优化+仿真组合

### 5.1 遗传算法 + 蒙特卡洛
**来源**: B196
**思路**: GA优化策略，MC评估风险

```python
def ga_monte_carlo(strategy_func, uncertain_params):
    """
    GA-MC组合优化
    """
    def fitness(strategy):
        # 蒙特卡洛模拟
        results = []
        for _ in range(1000):
            params = sample_uncertainty(uncertain_params)
            result = strategy_func(strategy, params)
            results.append(result)
        
        # 风险调整收益
        mean_return = np.mean(results)
        std_return = np.std(results)
        sharpe = mean_return / std_return
        
        return sharpe
    
    # GA优化
    best_strategy = genetic_algorithm(fitness)
    
    return best_strategy
```

### 5.2 粒子群 + 动态规划
**来源**: B159
**思路**: PSO连续决策，DP离散阶段

---

## 六、多目标组合

### 6.1 NSGA-II + TOPSIS
**来源**: 通用方法
**思路**: NSGA-II生成Pareto前沿，TOPSIS选择最终方案

```python
def nsga2_topsis(objectives, constraints):
    """
    NSGA-II + TOPSIS组合
    """
    # NSGA-II求解
    pareto_front, pareto_solutions = nsga2(objectives, constraints)
    
    # TOPSIS决策
    weights = normalize_weights(objectives)
    scores = topsis(pareto_front, weights)
    
    best_idx = np.argmax(scores)
    best_solution = pareto_solutions[best_idx]
    
    return best_solution
```

### 6.2 加权和 + 遗传算法
**来源**: C283
**思路**: 加权转化为单目标，GA优化

---

## 七、特征工程组合

### 7.1 WOE编码 + IV筛选 + XGBoost
**来源**: C109, C142, C227
**思路**: 评分卡标准流程

```python
def woe_iv_xgboost(X, y):
    """
    WOE-IV-XGBoost流程
    """
    # WOE编码
    X_woe = woe_encode(X, y)
    
    # IV筛选
    selected = []
    for col in X_woe.columns:
        iv = calculate_iv(X_woe[col], y)
        if iv > 0.02:
            selected.append(col)
    
    # XGBoost
    model = XGBClassifier()
    model.fit(X_woe[selected], y)
    
    return model, selected
```

### 7.2 PCA + 人工特征 + 随机森林
**来源**: C126
**思路**: PCA降维 + 领域特征构造

---

## 八、使用原则

### 8.1 选择依据
1. **问题特性**: 连续/离散、线性/非线性
2. **数据特点**: 样本量、维度、噪声
3. **计算资源**: 时间限制、内存限制
4. **可解释性要求**: 是否需要解释

### 8.2 组合原则
1. **互补性**: 两个方法解决不同方面的问题
2. **顺序性**: 先粗后精，先全局后局部
3. **验证性**: 用简单方法验证复杂方法
4. **鲁棒性**: 多方法对比，结论稳健

### 8.3 避免的陷阱
- ❌ 过度组合（方法堆砌，没有逻辑）
- ❌ 黑箱组合（不知道为什么有效）
- ❌ 复杂优先（简单能解决就不要复杂）
- ❌ 忽视对比（必须和基线方法对比）
