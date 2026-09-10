# 时间序列分析方法论

> 本文档提供时间序列分析的完整方法论，包括ARIMA、指数平滑、季节分解等核心方法。

---

## 一、方法选择决策树

```
时间序列分析
├── 平稳性？
│   ├── 平稳 → ARMA(p,q)
│   │   ├── 自相关拖尾 → AR(p)
│   │   ├── 偏自相关拖尾 → MA(q)
│   │   └── 均拖尾 → ARMA(p,q)
│   └── 非平稳 → 差分 → ARIMA(p,d,q)
│       ├── 一阶差分平稳 → d=1
│       ├── 二阶差分平稳 → d=2
│       └── 季节差分 → SARIMA
├── 趋势？
│   ├── 线性趋势 → 线性趋势+ARIMA
│   └── 非线性趋势 → 指数平滑
└── 季节性？
    ├── 有 → SARIMA / 季节分解
    └── 无 → ARIMA / 指数平滑
```

---

## 二、ARIMA模型

### 2.1 模型原理

**ARIMA(p,d,q)**：自回归积分滑动平均模型

- p：自回归阶数
- d：差分阶数
- q：滑动平均阶数

**模型方程**：

```
(1-ΣφᵢLⁱ)(1-Lᵈ)Xₜ = (1+ΣθⱼLʲ)εₜ
```

其中 L 为滞后算子，φᵢ 为自回归系数，θⱼ 为滑动平均系数。

### 2.2 建模流程

```
1. 平稳性检验（ADF检验）
   ↓
2. 差分处理（使序列平稳）
   ↓
3. 模型定阶（ACF/PACF分析）
   ↓
4. 参数估计（最大似然/最小二乘）
   ↓
5. 模型检验（残差白噪声检验）
   ↓
6. 预测
```

### 2.3 平稳性检验

**ADF检验（Augmented Dickey-Fuller）**：

```python
from statsmodels.tsa.stattools import adfuller

def adf_test(series):
    result = adfuller(series)
    print(f'ADF统计量: {result[0]:.4f}')
    print(f'p值: {result[1]:.4f}')
    print('临界值:')
    for key, value in result[4].items():
        print(f'  {key}: {value:.4f}')
    
    if result[1] < 0.05:
        print("结论: 序列平稳")
        return True
    else:
        print("结论: 序列非平稳，需要差分")
        return False
```

### 2.4 模型定阶

**ACF/PACF分析规则**：

| 模型 | ACF表现 | PACF表现 |
|------|---------|----------|
| AR(p) | 拖尾（指数衰减） | p阶截尾 |
| MA(q) | q阶截尾 | 拖尾（指数衰减） |
| ARMA(p,q) | 拖尾 | 拖尾 |

```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt

def plot_acf_pacf(series, lags=20):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    plot_acf(series, lags=lags, ax=ax1)
    plot_pacf(series, lags=lags, ax=ax2)
    plt.tight_layout()
    plt.savefig('figures/acf_pacf.png', dpi=300, bbox_inches='tight')
    plt.close()
```

### 2.5 完整代码框架

```python
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class ARIMAModel:
    def __init__(self, order=(1,1,1)):
        self.order = order
        self.model = None
        self.results = None
    
    def check_stationarity(self, series):
        result = adfuller(series)
        return result[1] < 0.05
    
    def difference(self, series, d=1):
        diff = series.copy()
        for _ in range(d):
            diff = diff.diff().dropna()
        return diff
    
    def fit(self, train_data):
        self.model = ARIMA(train_data, order=self.order)
        self.results = self.model.fit()
        return self.results
    
    def predict(self, steps=10):
        forecast = self.results.forecast(steps=steps)
        return forecast
    
    def evaluate(self, test_data, predictions):
        mse = mean_squared_error(test_data, predictions)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(test_data, predictions)
        mape = np.mean(np.abs((test_data - predictions) / test_data)) * 100
        
        return {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'MAPE': mape
        }
    
    def auto_order(self, series, max_p=5, max_d=2, max_q=5):
        best_aic = float('inf')
        best_order = (1,1,1)
        
        for p in range(max_p + 1):
            for d in range(max_d + 1):
                for q in range(max_q + 1):
                    try:
                        model = ARIMA(series, order=(p,d,q))
                        results = model.fit()
                        if results.aic < best_aic:
                            best_aic = results.aic
                            best_order = (p,d,q)
                    except:
                        continue
        
        self.order = best_order
        return best_order, best_aic
```

### 2.6 预测评估指标

| 指标 | 公式 | 说明 |
|------|------|------|
| MSE | Σ(yₜ-ŷₜ)²/n | 均方误差 |
| RMSE | √MSE | 均方根误差 |
| MAE | Σ|yₜ-ŷₜ|/n | 平均绝对误差 |
| MAPE | Σ|yₜ-ŷₜ|/|yₜ|×100/n | 平均绝对百分比误差 |
| AIC | -2ln(L)+2k | 赤池信息准则（越小越好） |
| BIC | -2ln(L)+k×ln(n) | 贝叶斯信息准则（越小越好） |

---

## 三、指数平滑法

### 3.1 模型分类

| 模型 | 适用场景 | 公式 |
|------|---------|------|
| 单参数（Simple） | 无趋势无季节 | Ŝₜ = αYₜ + (1-α)Ŝₜ₋₁ |
| 双参数（Holt） | 有趋势无季节 | 水平+趋势 |
| 三参数（Holt-Winters） | 有趋势有季节 | 水平+趋势+季节 |

### 3.2 单参数指数平滑

```python
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

def simple_exponential_smoothing(series, alpha=0.3):
    model = SimpleExpSmoothing(series)
    fit = model.fit(smoothing_level=alpha)
    forecast = fit.forecast(10)
    return fit, forecast
```

### 3.3 双参数指数平滑（Holt线性趋势）

```python
from statsmodels.tsa.holtwinters import Holt

def holt_linear(series, alpha=0.3, beta=0.1):
    model = Holt(series)
    fit = model.fit(smoothing_level=alpha, smoothing_trend=beta)
    forecast = fit.forecast(10)
    return fit, forecast
```

### 3.4 三参数指数平滑（Holt-Winters）

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def holt_winters(series, seasonal_periods=12, trend='add', seasonal='add'):
    model = ExponentialSmoothing(
        series, 
        trend=trend, 
        seasonal=seasonal,
        seasonal_periods=seasonal_periods
    )
    fit = model.fit()
    forecast = fit.forecast(10)
    return fit, forecast
```

### 3.5 参数优化

```python
def optimize_exponential_smoothing(series, seasonal_periods=12):
    from sklearn.model_selection import TimeSeriesSplit
    
    best_score = float('inf')
    best_params = None
    
    tscv = TimeSeriesSplit(n_splits=5)
    
    for trend in ['add', 'mul']:
        for seasonal in ['add', 'mul']:
            try:
                scores = []
                for train_idx, test_idx in tscv.split(series):
                    train = series.iloc[train_idx]
                    test = series.iloc[test_idx]
                    
                    model = ExponentialSmoothing(
                        train, 
                        trend=trend, 
                        seasonal=seasonal,
                        seasonal_periods=seasonal_periods
                    )
                    fit = model.fit()
                    pred = fit.forecast(len(test))
                    score = mean_squared_error(test, pred)
                    scores.append(score)
                
                avg_score = np.mean(scores)
                if avg_score < best_score:
                    best_score = avg_score
                    best_params = (trend, seasonal)
            except:
                continue
    
    return best_params, best_score
```

---

## 四、季节性分解

### 4.1 分解方法

| 方法 | 模型 | 适用场景 |
|------|------|---------|
| 加法分解 | Yₜ = Tₜ + Sₜ + Rₜ | 季节波动幅度恒定 |
| 乘法分解 | Yₜ = Tₜ × Sₜ × Rₜ | 季节波动随趋势变化 |
| STL分解 | Loess局部回归 | 鲁棒性好 |

### 4.2 代码实现

```python
from statsmodels.tsa.seasonal import seasonal_decompose, STL

def decompose_series(series, model='additive', period=12):
    decomposition = seasonal_decompose(series, model=model, period=period)
    
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 10))
    decomposition.observed.plot(ax=ax1)
    ax1.set_ylabel('原始序列')
    decomposition.trend.plot(ax=ax2)
    ax2.set_ylabel('趋势')
    decomposition.seasonal.plot(ax=ax3)
    ax3.set_ylabel('季节性')
    decomposition.resid.plot(ax=ax4)
    ax4.set_ylabel('残差')
    plt.tight_layout()
    plt.savefig('figures/decomposition.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return decomposition

def stl_decompose(series, period=12):
    stl = STL(series, period=period)
    result = stl.fit()
    return result
```

---

## 五、模型诊断

### 5.1 残差检验

| 检验类型 | 方法 | 判断标准 |
|---------|------|---------|
| 白噪声检验 | Ljung-Box检验 | p > 0.05 |
| 正态性检验 | Shapiro-Wilk检验 | p > 0.05 |
| 自相关检验 | ACF图 | 无显著自相关 |

### 5.2 代码实现

```python
from statsmodels.stats.diagnostic import acorr_ljungbox
from scipy import stats

def residual_diagnostics(residuals):
    results = {}
    
    # Ljung-Box白噪声检验
    lb_test = acorr_ljungbox(residuals, lags=10, return_df=True)
    results['ljung_box'] = lb_test
    
    # Shapiro-Wilk正态性检验
    if len(residuals) <= 5000:
        sw_stat, sw_p = stats.shapiro(residuals)
        results['shapiro'] = {'statistic': sw_stat, 'p_value': sw_p}
    
    # ACF图
    fig, ax = plt.subplots(figsize=(10, 4))
    plot_acf(residuals, lags=20, ax=ax)
    plt.savefig('figures/residual_acf.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return results
```

---

## 六、竞赛常见场景

### 6.1 预测类问题

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 销量预测 | ARIMA + XGBoost | C008, C052 |
| 电力负荷预测 | SARIMA + 神经网络 | C142, C227 |
| 股价预测 | LSTM + 注意力机制 | C305 |
| 人口预测 | Logistic + ARIMA | C101 |

### 6.2 季节性分析

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 旅游旺季分析 | STL分解 + 季节指数 | B007, B050 |
| 商品销售季节性 | Holt-Winters | C008 |
| 气温变化分析 | SARIMA | A070, A147 |

### 6.3 异常检测

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 传感器异常 | 3σ原则 + ARIMA残差 | A022, A171 |
| 金融异常交易 | Isolation Forest | C142 |

---

## 七、常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| ADF检验不通过 | 序列有趋势 | 差分处理 |
| ACF拖尾严重 | 非平稳 | 增加差分阶数 |
| 预测发散 | 模型过拟合 | 减少参数/正则化 |
| 季节性不明显 | 周期判断错误 | 尝试不同周期 |
| MAPE过大 | 有异常值 | 剔除异常值/使用MAE |

---

## 八、参考资源

### 8.1 教材推荐

- 《时间序列分析》（王黎明）
- 《应用时间序列分析》（何书元）
- 《Forecasting: principles and practice》（Hyndman）

### 8.2 Python库

- statsmodels：ARIMA、指数平滑
- prophet：Facebook时序预测
- pmdarima：自动ARIMA
- sktime：统一时序接口

### 8.3 检查清单

- [ ] 平稳性检验通过
- [ ] 模型定阶合理
- [ ] 残差通过白噪声检验
- [ ] 预测精度可接受
- [ ] 季节性处理正确
