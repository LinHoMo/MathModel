# 贝叶斯方法

> 贝叶斯统计与机器学习方法，适用于小样本、不确定性量化。

---

## 一、贝叶斯基础

### 1.1 贝叶斯定理

```
P(θ|D) = P(D|θ) * P(θ) / P(D)

后验 = 似然 × 先验 / 证据
```

### 1.2 贝叶斯推断流程

```
1. 设定先验分布 P(θ)
2. 收集数据 D
3. 计算似然函数 P(D|θ)
4. 计算后验分布 P(θ|D)
5. 进行预测和决策
```

### 1.3 先验选择

| 先验类型 | 适用场景 | 示例 |
|---------|---------|------|
| 无信息先验 | 无先验知识 | 均匀分布、Jeffreys先验 |
| 共轭先验 | 计算方便 | Beta-Binomial、Normal-Normal |
| 信息先验 | 有先验知识 | 专家意见、历史数据 |

---

## 二、贝叶斯回归

### 2.1 线性回归

```python
import numpy as np
from scipy import stats

class BayesianLinearRegression:
    """
    贝叶斯线性回归
    """
    def __init__(self, alpha=1.0, beta=1.0):
        self.alpha = alpha  # 先验精度
        self.beta = beta    # 噪声精度
        self.w_mean = None
        self.w_cov = None
    
    def fit(self, X, y):
        """拟合模型"""
        # 先验
        S0 = np.eye(X.shape[1]) / self.alpha
        
        # 后验
        SN = np.linalg.inv(S0 + self.beta * X.T @ X)
        mN = self.beta * SN @ X.T @ y
        
        self.w_mean = mN
        self.w_cov = SN
        
        return self
    
    def predict(self, X, return_std=True):
        """预测"""
        y_mean = X @ self.w_mean
        
        if return_std:
            y_var = 1/self.beta + np.sum(X @ self.w_cov * X, axis=1)
            y_std = np.sqrt(y_var)
            return y_mean, y_std
        
        return y_mean
```

### 2.2 岭回归

```python
def bayesian_ridge(X, y, alpha=1.0):
    """
    贝叶斯岭回归
    """
    # 后验均值
    w_mean = np.linalg.solve(X.T @ X + alpha * np.eye(X.shape[1]), X.T @ y)
    
    # 后验协方差
    w_cov = np.linalg.inv(X.T @ X + alpha * np.eye(X.shape[1]))
    
    return w_mean, w_cov
```

---

## 三、贝叶斯分类

### 3.1 朴素贝叶斯

```python
class NaiveBayes:
    """
    朴素贝叶斯分类器
    """
    def __init__(self):
        self.class_prior = {}
        self.class_mean = {}
        self.class_var = {}
    
    def fit(self, X, y):
        """拟合模型"""
        classes = np.unique(y)
        
        for c in classes:
            X_c = X[y == c]
            self.class_prior[c] = len(X_c) / len(X)
            self.class_mean[c] = X_c.mean(axis=0)
            self.class_var[c] = X_c.var(axis=0) + 1e-9
        
        return self
    
    def predict(self, X):
        """预测"""
        predictions = []
        
        for x in X:
            posteriors = []
            
            for c in self.class_prior:
                # 对数后验
                log_prior = np.log(self.class_prior[c])
                log_likelihood = -0.5 * np.sum(np.log(2*np.pi*self.class_var[c]) + 
                                                (x - self.class_mean[c])**2 / self.class_var[c])
                posteriors.append(log_prior + log_likelihood)
            
            predictions.append(list(self.class_prior.keys())[np.argmax(posteriors)])
        
        return np.array(predictions)
```

### 3.2 贝叶斯网络

```python
def bayesian_network_structure(data, var_names):
    """
    贝叶斯网络结构学习
    """
    from pgmpy.estimators import HillClimbSearch, BicScore
    from pgmpy.models import BayesianNetwork
    
    # 结构学习
    hc = HillClimbSearch(data)
    model = hc.estimate(scoring_method=BicScore(data))
    
    return model
```

---

## 四、贝叶斯优化

### 4.1 高斯过程

```python
class GaussianProcess:
    """
    高斯过程回归
    """
    def __init__(self, kernel='rbf', length_scale=1.0, noise=1e-6):
        self.length_scale = length_scale
        self.noise = noise
        self.X_train = None
        self.y_train = None
    
    def rbf_kernel(self, X1, X2):
        """RBF核函数"""
        sqdist = np.sum(X1**2, 1).reshape(-1, 1) + np.sum(X2**2, 1) - 2 * np.dot(X1, X2.T)
        return np.exp(-0.5 * sqdist / self.length_scale**2)
    
    def fit(self, X, y):
        """拟合模型"""
        self.X_train = X
        self.y_train = y
        
        K = self.rbf_kernel(X, X) + self.noise * np.eye(len(X))
        self.K_inv = np.linalg.inv(K)
        
        return self
    
    def predict(self, X, return_std=True):
        """预测"""
        K_s = self.rbf_kernel(X, self.X_train)
        K_ss = self.rbf_kernel(X, X)
        
        mu = K_s @ self.K_inv @ self.y_train
        sigma = np.sqrt(np.diag(K_ss - K_s @ self.K_inv @ K_s.T))
        
        if return_std:
            return mu, sigma
        return mu
```

### 4.2 贝叶斯优化

```python
def bayesian_optimization(objective, bounds, n_iterations=20):
    """
    贝叶斯优化
    """
    gp = GaussianProcess()
    
    # 初始采样
    X_init = np.random.uniform(bounds[:, 0], bounds[:, 1], (5, len(bounds)))
    y_init = np.array([objective(x) for x in X_init])
    
    gp.fit(X_init, y_init)
    
    for i in range(n_iterations):
        # 采集函数（Expected Improvement）
        def acquisition(x):
            mu, sigma = gp.predict(x.reshape(1, -1))
            best_y = np.max(y_init)
            
            with np.errstate(divide='ignore'):
                Z = (mu - best_y) / sigma
                ei = (mu - best_y) * stats.norm.cdf(Z) + sigma * stats.norm.pdf(Z)
                ei[sigma == 0.0] = 0.0
            
            return ei
        
        # 优化采集函数
        from scipy.optimize import minimize
        x_next = bounds[:, 0] + np.random.rand(len(bounds)) * (bounds[:, 1] - bounds[:, 0])
        
        result = minimize(lambda x: -acquisition(x), x_next, bounds=bounds)
        x_next = result.x
        
        # 评估目标函数
        y_next = objective(x_next)
        
        # 更新模型
        X_init = np.vstack([X_init, x_next.reshape(1, -1)])
        y_init = np.append(y_init, y_next)
        gp.fit(X_init, y_init)
    
    best_idx = np.argmax(y_init)
    return X_init[best_idx], y_init[best_idx]
```

---

## 五、贝叶斯模型选择

### 5.1 贝叶斯信息准则（BIC）

```python
def bic_score(model, X, y):
    """
    计算BIC
    """
    n = len(X)
    k = len(model.coef_) + 1
    y_pred = model.predict(X)
    
    rss = np.sum((y - y_pred)**2)
    bic = n * np.log(rss/n) + k * np.log(n)
    
    return bic
```

### 5.2 贝叶斯因子

```python
def bayes_factor(model1, model2):
    """
    计算贝叶斯因子
    """
    # 近似计算
    bf = np.exp((model1.bic - model2.bic) / 2)
    return bf
```

---

## 六、论文写作要点

### 6.1 问题分析框架
1. **先验选择**: 说明先验的来源和合理性
2. **后验计算**: MCMC或变分推断
3. **不确定性量化**: 置信区间
4. **模型比较**: BIC、贝叶斯因子

### 6.2 图表规范
- **后验分布图**: 直方图+核密度
- **置信区间图**: 误差棒
- **MCMC轨迹图**: 收敛性诊断
- **模型比较表**: BIC值

### 6.3 LaTeX代码
```latex
\begin{equation}
P(\theta|D) \propto P(D|\theta) P(\theta)
\label{eq:bayes}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{posterior.pdf}
\caption{后验分布}
\label{fig:posterior}
\end{figure}
```

---

## 七、参考文献

1. Gelman A. Bayesian Data Analysis. CRC Press, 2013.
2. Murphy K P. Machine Learning: A Probabilistic Perspective. MIT Press, 2012.
3. Bishop C M. Pattern Recognition and Machine Learning. Springer, 2006.
4. Robert C P. The Bayesian Choice. Springer, 2007.
