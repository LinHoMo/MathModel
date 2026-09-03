# 化学实验建模知识库

> 本文件提供数学建模竞赛中化学实验相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 乙醇制备C4烯烃催化剂优化
- 催化剂配比对产量的影响分析
- 反应条件优化（温度、压力、时间）
- 多因素实验设计与分析

### 1.2 常见约束条件
- 实验条件约束：温度范围、压力范围、时间限制
- 材料约束：催化剂用量、反应物浓度
- 安全约束：爆炸极限、毒性限制
- 经济约束：成本、产率

### 1.3 数据特点
- 实验数据：正交试验、响应面实验
- 因素数据：连续变量（温度、压力）、分类变量（催化剂类型）
- 响应数据：产率、选择性、转化率
- 数据量：通常较小（20-100组实验）

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 正交试验设计 | 多因素多水平筛选 | 实验次数少 | 无法考虑交互作用 |
| 方差分析 | 因素显著性检验 | 统计基础扎实 | 要求正态性 |
| 多元回归 | 建立因素-响应关系 | 模型简单 | 线性假设 |
| 响应面法 | 因素优化 | 可考虑交互作用 | 需要足够实验点 |
| 神经网络 | 非线性关系 | 拟合能力强 | 需要较多数据 |

---

## 3. 数学基础

### 3.1 正交试验设计

**正交表**：
- L9(3⁴)：3因素3水平，9次实验
- L16(4⁵)：5因素4水平，16次实验
- L25(5⁶)：6因素5水平，25次实验

**方差分析表**：
| 来源 | 平方和 | 自由度 | 均方 | F值 | p值 | 显著性 |
|------|--------|--------|------|-----|-----|--------|
| 因素A | SSA | fA | MSA=SSA/fA | MSA/MSE | pA | *或** |
| 因素B | SSB | fB | MSB=SSB/fB | MSB/MSE | pB | *或** |
| 误差 | SSE | fE | MSE=SSE/fE | | | |
| 总和 | SST | fT | | | | |

### 3.2 多元回归模型

**模型形式**：
```
y = β₀ + β₁x₁ + β₂x₂ + ... + βₖxₖ + ε
```

**含交互项**：
```
y = β₀ + β₁x₁ + β₂x₂ + β₁₂x₁x₂ + ε
```

**含平方项**：
```
y = β₀ + β₁x₁ + β₂x₂ + β₁₁x₁² + β₂₂x₂² + β₁₂x₁x₂ + ε
```

### 3.3 响应面法 (RSM)

**二阶多项式模型**：
```
y = β₀ + Σβᵢxᵢ + Σβᵢᵢxᵢ² + ΣΣβᵢⱼxᵢxⱼ + ε
```

**规范分析**：
- 编码变量：将原始变量转换为[-1, 1]范围
- 寻找最速上升方向
- 岭分析：在约束条件下寻找最优

---

## 4. 代码实现

### 4.1 正交试验设计

```python
import numpy as np
import pandas as pd
from itertools import product

def orthogonal_design(n_factors, n_levels, factors=None):
    """
    正交试验设计
    
    Parameters
    ----------
    n_factors : int
        因素数
    n_levels : int
        水平数
    factors : list, optional
        因素名称
    
    Returns
    -------
    design : DataFrame
        正交设计表
    """
    # 使用statsmodels库（如果可用）
    try:
        from statsmodels.design import Taguchi
        design = Taguchi(n_levels=n_levels, n_factors=n_factors).design
    except:
        # 简化版：全因素设计
        levels = list(range(n_levels))
        design = list(product(levels, repeat=n_factors))
        design = np.array(design)
    
    if factors is None:
        factors = [f'Factor_{i+1}' for i in range(n_factors)]
    
    df = pd.DataFrame(design, columns=factors)
    return df
```

### 4.2 方差分析

```python
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

def anova_analysis(data, formula, alpha=0.05):
    """
    方差分析
    
    Parameters
    ----------
    data : DataFrame
        实验数据
    formula : str
        回归公式，如 'Y ~ A + B + C'
    alpha : float
        显著性水平
    
    Returns
    -------
    anova_table : DataFrame
        方差分析表
    significant_factors : list
        显著因素列表
    """
    model = ols(formula, data=data).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    
    # 添加显著性标记
    anova_table['Significance'] = ''
    anova_table.loc[anova_table['PR(>F)'] < 0.01, 'Significance'] = '**'
    anova_table.loc[(anova_table['PR(>F)'] >= 0.01) & 
                    (anova_table['PR(>F)'] < 0.05), 'Significance'] = '*'
    
    # 识别显著因素
    significant_factors = anova_table[anova_table['PR(>F)'] < alpha].index.tolist()
    significant_factors = [f for f in significant_factors if f != 'Residual']
    
    return anova_table, significant_factors
```

### 4.3 响应面分析

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def response_surface_analysis(data, factors, response, degree=2):
    """
    响应面分析
    
    Parameters
    ----------
    data : DataFrame
        实验数据
    factors : list
        因素列名
    response : str
        响应列名
    degree : int
        多项式阶数
    
    Returns
    -------
    model : 训练好的模型
    results : 分析结果
    """
    X = data[factors].values
    y = data[response].values
    
    # 创建多项式特征
    poly = PolynomialFeatures(degree=degree, include_bias=False)
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
    
    results = {
        'model': model,
        'poly': poly,
        'coefficients': coef_df,
        'r_squared': model.score(X_poly, y),
        'intercept': model.intercept_
    }
    
    return model, results
```

### 4.4 优化求解

```python
import numpy as np
from scipy.optimize import minimize

def optimize_conditions(model, poly, factors, constraints=None):
    """
    优化实验条件
    
    Parameters
    ----------
    model : 训练好的模型
    poly : 多项式特征转换器
    factors : list
        因素名称
    constraints : dict, optional
        约束条件 {'factor': (min, max)}
    
    Returns
    -------
    optimal_conditions : dict
        最优条件
    optimal_response : float
        最优响应值
    """
    def objective(x):
        X_poly = poly.transform(x.reshape(1, -1))
        return -model.predict(X_poly)[0]  # 最大化取负
    
    # 设置边界
    if constraints:
        bounds = [constraints.get(f, (-np.inf, np.inf)) for f in factors]
    else:
        bounds = [(-10, 10)] * len(factors)  # 默认范围
    
    # 初始猜测
    x0 = np.zeros(len(factors))
    
    # 优化
    result = minimize(objective, x0, method='L-BFGS-B', bounds=bounds)
    
    optimal_conditions = dict(zip(factors, result.x))
    optimal_response = -result.fun
    
    return optimal_conditions, optimal_response
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 未考虑交互作用 | 模型拟合差 | 添加交互项 |
| 样本量不足 | 过拟合 | 交叉验证/正则化 |
| 未标准化 | 系数不可比 | 标准化后比较 |
| 忽略异常值 | 模型偏差 | 识别并处理异常值 |
| 过度拟合 | 预测性能差 | 简化模型/正则化 |
| 伪相关 | 错误结论 | 因果推断/实验验证 |

---

## 6. 验证方法

### 6.1 模型验证
- R²和调整R²
- 交叉验证分数
- 残差分析（正态性、同方差性）

### 6.2 实验验证
- 重复实验验证预测结果
- 与文献数据对比
- 物理/化学合理性检查

### 6.3 灵敏度分析
- 各因素对结果的影响程度
- 关键因素识别
- 鲁棒性分析

---

## 7. 参考论文

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| B007 | 正交试验+回归 | 催化剂优化 |
| B050 | 神经网络+回归 | 多模型对比 |
| B160 | 多元回归+方差分析 | 交互作用分析 |
| B026 | 双因素方差分析 | 显著性检验 |

---

## 8. 代码模板参考

- 回归分析: `resources/code-templates/regression/multiple_regression.py`
- 优化算法: `resources/code-templates/optimization/genetic_algorithm.py`

---

## 9. 验证清单

- [ ] 实验设计合理（正交表/响应面）
- [ ] 方差分析表完整（F值、p值、显著性）
- [ ] 回归模型R² > 0.7
- [ ] 残差正态性检验通过（p > 0.05）
- [ ] 交互作用已考虑（如适用）
- [ ] 优化结果在实验范围内
- [ ] 灵敏度分析已执行
- [ ] 结果与文献/实验数据一致
