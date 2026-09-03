# 回归分析方法论

> 本文件提供数学建模竞赛中常用的回归分析知识，包括模型选择、诊断检验、防错策略和验证方法。

---

## 1. 回归模型选择决策树

```
回归问题类型识别：
├── 线性关系 + 无多重共线性 → 多元线性回归
│   └── sklearn.linear_model.LinearRegression
├── 多重共线性严重 → 岭回归/LASSO
│   ├── 岭回归 (L2正则) → sklearn.linear_model.Ridge
│   └── LASSO (L1正则) → sklearn.linear_model.Lasso
├── 非线性关系 → 非线性回归
│   ├── 多项式回归 → sklearn.preprocessing.PolynomialFeatures
│   ├── 分段回归 → 门限回归/样条回归
│   └── 非线性最小二乘 → scipy.optimize.curve_fit
├── 交互作用显著 → 含交互项的回归
│   └── X1*X2 交互项
├── 异方差/自相关 → 广义最小二乘
│   └── statsmodels.GLS
└── 响应面问题 → 响应面法 (RSM)
    └── 二阶多项式 + 中心复合设计
```

---

## 2. 核心方法详解

### 2.1 多元线性回归

**模型形式**：
```
y = β₀ + β₁x₁ + β₂x₂ + ... + βₖxₖ + ε
```

**假设检验**：
- 正态性：残差服从正态分布（Shapiro-Wilk检验）
- 同方差性：残差方差恒定（Breusch-Pagan检验）
- 无自相关：残差无序列相关（Durbin-Watson检验）
- 无多重共线性：VIF < 10

**代码框架**：
```python
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

def multiple_regression(X, y, feature_names=None):
    """
    多元线性回归分析
    """
    # 添加常数项
    X_with_const = sm.add_constant(X)
    
    # 拟合模型
    model = sm.OLS(y, X_with_const).fit()
    
    # 输出回归结果
    print(model.summary())
    
    # VIF检验（多重共线性）
    vif_data = pd.DataFrame()
    vif_data["Feature"] = ["const"] + list(feature_names) if feature_names else range(X_with_const.shape[1])
    vif_data["VIF"] = [variance_inflation_factor(X_with_const, i) for i in range(X_with_const.shape[1])]
    print("\nVIF检验:")
    print(vif_data)
    
    # 残差诊断
    residuals = model.resid
    
    # 正态性检验
    from scipy.stats import shapiro
    stat, p_value = shapiro(residuals)
    print(f"\nShapiro-Wilk正态性检验: p={p_value:.4f}")
    
    # Durbin-Watson检验（自相关）
    from statsmodels.stats.stattools import durbin_watson
    dw = durbin_watson(residuals)
    print(f"Durbin-Watson统计量: {dw:.4f}")
    
    return model, residuals, vif_data
```

### 2.2 岭回归 (Ridge Regression)

**适用场景**：多重共线性严重（VIF > 10）

**模型形式**：
```
min Σ(yᵢ - ŷᵢ)² + αΣβⱼ²
```

**关键参数**：
- α（正则化强度）：通过交叉验证选择

**代码框架**：
```python
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

def ridge_regression(X, y, alphas=np.logspace(-3, 3, 100)):
    """
    岭回归分析
    """
    # 标准化（重要！）
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 交叉验证选择α
    ridge_cv = RidgeCV(alphas=alphas, cv=5)
    ridge_cv.fit(X_scaled, y)
    best_alpha = ridge_cv.alpha_
    
    # 拟合最优模型
    ridge = Ridge(alpha=best_alpha)
    ridge.fit(X_scaled, y)
    
    print(f"最优α: {best_alpha:.4f}")
    print(f"R²: {ridge.score(X_scaled, y):.4f}")
    print(f"系数: {ridge.coef_}")
    
    return ridge, scaler, best_alpha
```

### 2.3 LASSO回归

**适用场景**：特征选择（自动将不重要特征系数压缩为0）

**模型形式**：
```
min Σ(yᵢ - ŷᵢ)² + αΣ|βⱼ|
```

**代码框架**：
```python
from sklearn.linear_model import Lasso, LassoCV
from sklearn.preprocessing import StandardScaler

def lasso_regression(X, y, alphas=np.logspace(-3, 3, 100)):
    """
    LASSO回归分析
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 交叉验证选择α
    lasso_cv = LassoCV(alphas=alphas, cv=5, random_state=42)
    lasso_cv.fit(X_scaled, y)
    best_alpha = lasso_cv.alpha_
    
    # 拟合最优模型
    lasso = Lasso(alpha=best_alpha)
    lasso.fit(X_scaled, y)
    
    print(f"最优α: {best_alpha:.4f}")
    print(f"R²: {lasso.score(X_scaled, y):.4f}")
    print(f"非零系数: {np.sum(lasso.coef_ != 0)}/{len(lasso.coef_)}")
    
    return lasso, scaler, best_alpha
```

### 2.4 多项式回归

**适用场景**：非线性关系

**代码框架**：
```python
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

def polynomial_regression(X, y, degree=2):
    """
    多项式回归分析
    """
    model = Pipeline([
        ('poly', PolynomialFeatures(degree=degree, include_bias=False)),
        ('linear', LinearRegression())
    ])
    
    model.fit(X, y)
    
    r2 = model.score(X, y)
    print(f"多项式阶数: {degree}")
    print(f"R²: {r2:.4f}")
    
    return model
```

### 2.5 响应面法 (Response Surface Methodology)

**适用场景**：实验设计优化（如C4烯烃催化剂配比优化）

**典型设计**：
- 二阶多项式模型
- 中心复合设计（CCD）或Box-Behnken设计

**模型形式**：
```
y = β₀ + Σβᵢxᵢ + Σβᵢᵢxᵢ² + ΣΣβᵢⱼxᵢxⱼ + ε
```

**代码框架**：
```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

def response_surface_analysis(data, factors, response):
    """
    响应面分析
    data: 包含因素和响应的DataFrame
    factors: 因素列名列表
    response: 响应列名
    """
    X = data[factors].values
    y = data[response].values
    
    # 创建二阶多项式特征（含交互项和平方项）
    poly = PolynomialFeatures(degree=2, include_bias=False)
    X_poly = poly.fit_transform(X)
    
    # 拟合模型
    model = LinearRegression()
    model.fit(X_poly, y)
    
    # 输出系数
    feature_names = poly.get_feature_names_out(factors)
    coef_df = pd.DataFrame({
        'Feature': feature_names,
        'Coefficient': model.coef_
    })
    print("响应面系数:")
    print(coef_df)
    print(f"\nR²: {model.score(X_poly, y):.4f}")
    
    return model, poly
```

---

## 3. 实验设计方法

### 3.1 正交试验设计

**适用场景**：多因素多水平实验，筛选关键因素

**步骤**：
1. 确定因素和水平
2. 选择正交表（如L9(3⁴)）
3. 按正交表安排实验
4. 方差分析确定显著因素

**代码框架**：
```python
import numpy as np
import pandas as pd
from itertools import product

def orthogonal_experiment_design(factors, levels):
    """
    正交试验设计
    factors: 因素名称列表
    levels: 各因素水平数列表
    """
    # 生成正交表（简化版，实际应用需使用标准正交表）
    n_factors = len(factors)
    n_levels = max(levels)
    n_experiments = n_levels ** 2  # 简化
    
    # 生成实验方案
    experiments = []
    for i in range(n_experiments):
        exp = {}
        for j, factor in enumerate(factors):
            exp[factor] = (i // (n_levels ** j)) % n_levels
        experiments.append(exp)
    
    return pd.DataFrame(experiments)
```

### 3.2 方差分析 (ANOVA)

**适用场景**：判断因素影响是否显著

**代码框架**：
```python
import statsmodels.api as sm
from statsmodels.formula.api import ols

def anova_analysis(data, formula):
    """
    方差分析
    formula: 如 'Y ~ A + B + C'
    """
    model = ols(formula, data=data).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    print("方差分析表:")
    print(anova_table)
    
    # 显著性判断（α=0.05）
    significant_factors = anova_table[anova_table['PR(>F)'] < 0.05].index.tolist()
    print(f"\n显著因素 (p<0.05): {significant_factors}")
    
    return anova_table, significant_factors
```

---

## 4. 模型诊断

### 4.1 残差分析

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

def residual_diagnostics(residuals, fitted_values):
    """
    残差诊断图
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. 残差vs拟合值
    axes[0, 0].scatter(fitted_values, residuals, alpha=0.6)
    axes[0, 0].axhline(y=0, color='r', linestyle='--')
    axes[0, 0].set_xlabel('Fitted Values')
    axes[0, 0].set_ylabel('Residuals')
    axes[0, 0].set_title('Residuals vs Fitted')
    
    # 2. Q-Q图（正态性）
    stats.probplot(residuals, dist="norm", plot=axes[0, 1])
    axes[0, 1].set_title('Normal Q-Q Plot')
    
    # 3. 残差直方图
    axes[1, 0].hist(residuals, bins=20, edgecolor='black', alpha=0.7)
    axes[1, 0].set_xlabel('Residuals')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Residuals Histogram')
    
    # 4. 残差自相关图
    from pandas.plotting import autocorrelation_plot
    autocorrelation_plot(residuals, ax=axes[1, 1])
    axes[1, 1].set_title('Residuals Autocorrelation')
    
    plt.tight_layout()
    return fig
```

### 4.2 影响度分析

```python
def influence_analysis(model, X_with_const):
    """
    影响度分析（识别强影响点）
    """
    from statsmodels.stats.outliers_influence import OLSInfluence
    
    influence = OLSInfluence(model)
    
    # Cook's距离
    cooks_d = influence.cooks_distance[0]
    
    # 杠杆值
    leverage = influence.hat_matrix_diag
    
    # DFFITS
    dffits = influence.dffits[0]
    
    # 识别异常点
    n = len(cooks_d)
    threshold_cooks = 4 / n
    threshold_leverage = 2 * X_with_const.shape[1] / n
    
    influential_points = np.where(cooks_d > threshold_cooks)[0]
    high_leverage_points = np.where(leverage > threshold_leverage)[0]
    
    print(f"强影响点 (Cook's D > {threshold_cooks:.4f}): {influential_points}")
    print(f"高杠杆点 (h > {threshold_leverage:.4f}): {high_leverage_points}")
    
    return cooks_d, leverage, influential_points
```

---

## 5. 防错速查表

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 多重共线性 | 系数符号与预期相反 | VIF检验，改用岭回归/LASSO |
| 异方差 | 残差图呈喇叭形 | 加权最小二乘/稳健标准误 |
| 过拟合 | 训练R²高，测试R²低 | 交叉验证/正则化 |
| 遗漏交互项 | 交互效应未考虑 | 添加交互项 |
| 未标准化 | 系数大小不可比 | 标准化后比较系数 |
| 遗漏非线性 | 残差图有规律 | 多项式/样条回归 |
| 伪回归 | 时序数据虚假相关 | 单位根检验/差分 |

---

## 6. 参考论文（来自高教杯优秀论文）

| 论文编号 | 回归方法 | 应用场景 | 关键创新 |
|---------|---------|---------|---------|
| B007 | 多项式回归 | C4烯烃产量预测 | 正交试验+响应面 |
| B050 | 神经网络+回归 | C4烯烃催化剂优化 | 多模型对比 |
| B160 | 多元回归 | 催化剂组合分析 | 方差分析+交互项 |
| B026 | 双因素方差分析 | 乙醇制备C4烯烃 | 正交试验+ANOVA |
| C126 | 多元回归 | 蔬菜销售预测 | 特征工程+时序 |

---

## 7. 验证清单

- [ ] 残差正态性检验通过（p > 0.05）
- [ ] 无严重多重共线性（VIF < 10）
- [ ] 无异方差（残差图无规律）
- [ ] 交叉验证R²与训练R²差异 < 0.1
- [ ] 系数符号与业务逻辑一致
- [ ] 显著性检验通过（p < 0.05）
- [ ] 预测区间合理（与物理直觉一致）
