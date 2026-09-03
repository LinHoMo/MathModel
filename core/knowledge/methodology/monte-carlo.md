# 蒙特卡洛模拟领域知识

## 一、核心概念

### 1.1 蒙特卡洛方法
- **定义**: 基于随机抽样的数值计算方法
- **核心思想**: 用频率近似概率，用样本统计量近似总体参数
- **应用**: 积分计算、优化、风险分析

### 1.2 理论基础
- **大数定律**: 样本均值收敛于期望
- **中心极限定理**: 样本均值近似正态分布
- **误差收敛**: 误差 ∝ 1/√N

### 1.3 适用场景
- 解析解难以获得
- 维度高、变量多
- 存在随机性/不确定性
- 需要风险评估

---

## 二、基本方法

### 2.1 直接抽样
```python
def direct_sampling(n_samples, func):
    """
    直接蒙特卡洛抽样
    """
    samples = np.random.uniform(0, 1, n_samples)
    results = func(samples)
    
    mean = np.mean(results)
    std = np.std(results) / np.sqrt(n_samples)
    
    return mean, std
```

### 2.2 重要性抽样
```python
def importance_sampling(n_samples, func, proposal_dist):
    """
    重要性抽样
    """
    samples = proposal_dist.rvs(n_samples)
    weights = func(samples) / proposal_dist.pdf(samples)
    
    mean = np.mean(weights)
    return mean
```

### 2.3 方差缩减技术
```python
def antithetic_variates(n_samples, func):
    """
    对偶变量法
    """
    samples = np.random.uniform(0, 1, n_samples)
    results1 = func(samples)
    results2 = func(1 - samples)
    
    mean = (np.mean(results1) + np.mean(results2)) / 2
    return mean

def control_variates(n_samples, func, control_func, control_mean):
    """
    控制变量法
    """
    samples = np.random.uniform(0, 1, n_samples)
    results = func(samples)
    control = control_func(samples)
    
    # 使用控制变量
    mean = np.mean(results) - (np.mean(control) - control_mean)
    return mean
```

---

## 三、积分计算

### 3.1 定积分近似
```python
def monte_carlo_integral(func, a, b, n_samples):
    """
    蒙特卡洛积分
    """
    samples = np.random.uniform(a, b, n_samples)
    results = func(samples)
    
    integral = (b - a) * np.mean(results)
    error = (b - a) * np.std(results) / np.sqrt(n_samples)
    
    return integral, error
```

### 3.2 多重积分
```python
def monte_carlo多重积分(func, bounds, n_samples):
    """
    多重积分计算
    """
    dim = len(bounds)
    samples = np.zeros((n_samples, dim))
    
    for i in range(dim):
        samples[:, i] = np.random.uniform(bounds[i][0], bounds[i][1], n_samples)
    
    results = func(samples)
    
    volume = np.prod([b[1] - b[0] for b in bounds])
    integral = volume * np.mean(results)
    
    return integral
```

---

## 四、风险分析

### 4.1 项目风险评估
```python
def project_risk_analysis(costs, revenues, n_simulations=10000):
    """
    项目风险分析
    """
    npv_samples = []
    
    for _ in range(n_simulations):
        # 随机抽样成本和收入
        cost = np.random.normal(costs['mean'], costs['std'])
        revenue = np.random.normal(revenues['mean'], revenues['std'])
        
        npv = revenue - cost
        npv_samples.append(npv)
    
    # 统计分析
    mean_npv = np.mean(npv_samples)
    std_npv = np.std(npv_samples)
    prob_loss = np.mean(np.array(npv_samples) < 0)
    
    return {
        'mean_npv': mean_npv,
        'std_npv': std_npv,
        'prob_loss': prob_loss
    }
```

### 4.2 VaR计算
```python
def value_at_risk(returns, confidence=0.95):
    """
    计算VaR
    """
    sorted_returns = np.sort(returns)
    index = int((1 - confidence) * len(sorted_returns))
    
    var = -sorted_returns[index]
    return var
```

### 4.3 蒙特卡洛期权定价
```python
def monte_carlo_option(S0, K, T, r, sigma, n_simulations):
    """
    蒙特卡洛期权定价
    """
    Z = np.random.standard_normal(n_simulations)
    
    # 期权到期价格
    ST = S0 * np.exp((r - 0.5*sigma**2)*T + sigma*np.sqrt(T)*Z)
    
    # 期权收益
    payoff = np.maximum(ST - K, 0)
    
    # 折现
    option_price = np.exp(-r*T) * np.mean(payoff)
    
    return option_price
```

---

## 五、随机过程模拟

### 5.1 布朗运动
```python
def brownian_motion(n_steps, dt, sigma):
    """
    几何布朗运动
    """
    dW = np.random.normal(0, np.sqrt(dt), n_steps)
    W = np.cumsum(dW)
    
    return W
```

### 5.2 泊松过程
```python
def poisson_process(rate, T, n_simulations):
    """
    泊松过程模拟
    """
    events = []
    
    for _ in range(n_simulations):
        t = 0
        event_times = []
        
        while t < T:
            t += np.random.exponential(1/rate)
            if t < T:
                event_times.append(t)
        
        events.append(event_times)
    
    return events
```

---

## 六、论文写作要点

### 6.1 问题分析框架
1. **问题定义**: 随机变量、目标函数
2. **模型建立**: 概率分布、随机过程
3. **抽样方法**: 直接/重要性/方差缩减
4. **结果分析**: 统计量、置信区间
5. **误差分析**: 收敛性、精度
6. **灵敏度分析**: 参数影响

### 6.2 图表规范
- **收敛曲线**: 迭代次数 vs 误差
- **分布图**: 直方图+核密度
- **置信区间**: 误差棒
- **敏感性分析**: 龙卷风图

### 6.3 LaTeX代码
```latex
\begin{equation}
\hat{I} = \frac{1}{N}\sum_{i=1}^N f(X_i)
\label{eq:mc}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{mc_convergence.pdf}
\caption{蒙特卡洛收敛曲线}
\label{fig:mc}
\end{figure}
```

---

## 七、参考文献

1. Robert C P. Monte Carlo Methods. Springer, 2004.
2. Kroese D P. Handbook of Monte Carlo Methods. Wiley, 2011.
3. Glasserman P. Monte Carlo Methods in Financial Engineering. Springer, 2003.
4. 陈希孺. 概率论与数理统计. 中国科学技术大学出版社, 2009.
