# B题：实验设计专项

## 概述

本知识文档专门针对数学建模竞赛B题（实验设计类）问题，提供从问题分析到论文撰写的完整流程指导。B题通常涉及实验数据的统计分析和优化，要求参赛者具备扎实的统计学基础和实验设计能力。

**适用场景**：
- 乙醇制备C4烯烃催化剂优化
- 无人机无源定位
- RGV动态调度
- 同心鼓协作策略
- 穿越沙漠游戏策略

---

## 一、适用问题特征

### 1.1 核心特征识别

| 特征维度 | 具体表现 |
|---------|---------|
| 数据类型 | 实验数据、正交试验、响应面实验 |
| 分析方法 | 方差分析、回归分析、假设检验 |
| 优化目标 | 因素筛选、参数优化、条件优化 |
| 验证方式 | 统计检验、交叉验证、蒙特卡洛模拟 |
| 输出形式 | 最优条件、预测模型、显著性分析 |

### 1.2 典型问题分类

#### 催化剂优化类
- 多因素多水平实验
- 催化剂组合优化
- 反应条件优化

#### 调度优化类
- 资源分配问题
- 时序调度问题
- 动态调整问题

#### 策略优化类
- 博弈策略
- 决策优化
- 风险分析

#### 定位测量类
- 信号处理
- 参数估计
- 误差分析

### 1.3 问题识别检查清单

```
□ 是否涉及实验数据？
□ 是否需要回归分析或方差分析？
□ 是否需要因素筛选和参数优化？
□ 是否需要统计检验和假设检验？
□ 是否需要蒙特卡洛模拟？
□ 结果是否需要统计显著性支持？
□ 是否需要预测模型？
```

---

## 二、完整建模流程

### Step 1: 问题分析与实验设计

#### 1.1 识别实验类型
- **正交试验**：多因素多水平，筛选关键因素
- **响应面实验**：因素优化，寻找最优配比
- **单因素实验**：逐一验证各因素影响
- **析因实验**：研究因素交互作用

#### 1.2 确定因素和水平
- 识别所有可能影响结果的因素
- 确定各因素的水平数（通常2-5个水平）
- 考虑因素间的交互作用

#### 1.3 选择实验设计方法

**常用设计**：

| 设计类型 | 适用场景 | 实验次数 |
|---------|---------|---------|
| 全因素设计 | 因素少（≤4），水平少 | L = m^n |
| 正交设计 | 因素多，水平多 | L = N × (m-1) + 1 |
| Box-Behnken | 3因素，3水平 | 15次 |
| 中心复合设计 | 5因素，5水平 | 50+次 |
| 均匀设计 | 因素多，水平多 | 较少 |

#### 1.4 实验设计代码

```python
import numpy as np
import pandas as pd
from pyDOE2 import doe_star

def create_orthogonal_design(factors, levels, n_runs=None):
    """
    创建正交实验设计
    
    Parameters
    ----------
    factors : list
        因素名称列表
    levels : list
        各因素水平数列表
    n_runs : int, optional
        实验次数（None则自动计算）
    
    Returns
    -------
    design : DataFrame
        实验设计矩阵
    """
    n_factors = len(factors)
    max_levels = max(levels)
    
    if n_runs is None:
        # 使用L9正交表
        n_runs = 9
    
    # 生成正交表
    design = np.zeros((n_runs, n_factors))
    
    for j, (factor, level) in enumerate(zip(factors, levels)):
        # 均匀分配水平
        design[:, j] = np.random.choice(level, n_runs)
    
    return pd.DataFrame(design, columns=factors)
```

---

### Step 2: 数据分析方法

#### 2.1 方差分析 (ANOVA)

**适用场景**：判断因素影响是否显著

**Python实现**：

```python
import statsmodels.api as sm
from statsmodels.formula.api import ols
import pandas as pd

def anova_analysis(data, formula):
    """
    方差分析
    
    Parameters
    ----------
    data : DataFrame
        实验数据
    formula : str
        回归公式，如 'Y ~ A + B + C'
    
    Returns
    -------
    anova_table : DataFrame
        方差分析表
    significant_factors : list
        显著因素列表
    """
    model = ols(formula, data=data).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    
    # 显著性判断（α=0.05）
    significant_factors = anova_table[anova_table['PR(>F)'] < 0.05].index.tolist()
    
    return anova_table, significant_factors


def anova_with_interaction(data, formula):
    """
    含交互项的方差分析
    """
    model = ols(formula, data=data).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    
    return anova_table
```

#### 2.2 多元回归分析

**适用场景**：建立因素与响应的关系模型

**模型形式**：
```
y = β₀ + β₁x₁ + β₂x₂ + ... + βₖxₖ + ε
```

**关键检查**：
- R²和调整R²
- 系数显著性（p值）
- 残差正态性
- 多重共线性（VIF < 10）

**代码实现**：

```python
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import numpy as np

def multiple_regression(data, target, features):
    """
    多元回归分析
    """
    X = data[features]
    X = sm.add_constant(X)  # 添加截距项
    y = data[target]
    
    model = sm.OLS(y, X).fit()
    
    # VIF检验
    vif_data = pd.DataFrame()
    vif_data["Feature"] = features
    vif_data["VIF"] = [variance_inflation_factor(X.values, i+1) for i in range(len(features))]
    
    return model, vif_data


def check_regression_assumptions(model, data, features):
    """
    回归假设检验
    """
    from scipy import stats
    
    # 1. 残差正态性检验
    residuals = model.resid
    stat, p_value = stats.shapiro(residuals)
    normality_ok = p_value > 0.05
    
    # 2. 残差方差齐性检验
    # Breusch-Pagan检验
    from statsmodels.stats.diagnostic import het_breuschpagan
    bp_stat, bp_p_value, _, _ = het_breuschpagan(residuals, sm.add_constant(data[features]))
    homoscedasticity_ok = bp_p_value > 0.05
    
    # 3. 多重共线性
    vif_values = [variance_inflation_factor(sm.add_constant(data[features]).values, i+1) 
                  for i in range(len(features))]
    multicollinearity_ok = all(v < 10 for v in vif_values)
    
    return {
        'normality': normality_ok,
        'homoscedasticity': homoscedasticity_ok,
        'multicollinearity': multicollinearity_ok,
        'vif_values': vif_values
    }
```

#### 2.3 响应面法 (RSM)

**适用场景**：因素优化，寻找最优配比

**模型形式**：
```
y = β₀ + Σβᵢxᵢ + Σβᵢᵢxᵢ² + ΣΣβᵢⱼxᵢxⱼ + ε
```

**关键步骤**：
1. 拟合二阶多项式模型
2. 检验模型显著性
3. 寻找最优条件（岭回归/规范分析）

**代码实现**：

```python
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
import numpy as np

def response_surface_analysis(data, target, features):
    """
    响应面分析
    """
    X = data[features].values
    y = data[target].values
    
    # 创建多项式特征（二阶）
    poly = PolynomialFeatures(degree=2, include_bias=False)
    X_poly = poly.fit_transform(X)
    
    # 拟合模型
    model = LinearRegression()
    model.fit(X_poly, y)
    
    # 预测网格
    def predict(X_new):
        X_new_poly = poly.transform(X_new)
        return model.predict(X_new_poly)
    
    return model, predict, poly


def find_optimal_conditions(predict_func, feature_ranges, n_features):
    """
    寻找最优条件
    """
    from scipy.optimize import minimize
    
    def objective(x):
        return -predict_func(x.reshape(1, -1))[0]  # 最大化
    
    # 初始点
    x0 = np.mean(feature_ranges, axis=1)
    
    # 约束
    bounds = [(low, high) for low, high in feature_ranges]
    
    # 优化
    result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
    
    return result.x, -result.fun
```

---

### Step 3: 优化与预测

#### 3.1 参数优化

**常用方法**：
- 岭回归：处理多重共线性
- LASSO：特征选择
- 遗传算法：非线性优化

**代码实现**：

```python
from sklearn.linear_model import Ridge, Lasso
from sklearn.preprocessing import StandardScaler
import numpy as np

def optimize_parameters(X, y, method='ridge'):
    """
    参数优化
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if method == 'ridge':
        model = Ridge(alpha=1.0)
    elif method == 'lasso':
        model = Lasso(alpha=0.1)
    
    model.fit(X_scaled, y)
    
    return model, scaler
```

#### 3.2 预测模型

**交叉验证**：

```python
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestRegressor

def validate_model(X, y, model=None):
    """
    模型验证
    """
    if model is None:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    
    return cv_scores.mean(), cv_scores.std()
```

---

### Step 4: 蒙特卡洛模拟

#### 4.1 不确定性分析

**适用场景**：考虑参数不确定性对结果的影响

**代码实现**：

```python
import numpy as np

def monte_carlo_simulation(model, X_mean, X_std, n_simulations=10000):
    """
    蒙特卡洛模拟
    
    Parameters
    ----------
    model : 预测模型
    X_mean : 特征均值
    X_std : 特征标准差
    n_simulations : 模拟次数
    
    Returns
    -------
    results : 模拟结果分布
    """
    results = []
    
    for _ in range(n_simulations):
        # 生成随机样本
        X_sample = np.random.normal(X_mean, X_std)
        
        # 预测
        y_pred = model.predict(X_sample.reshape(1, -1))
        results.append(y_pred[0])
    
    results = np.array(results)
    
    # 统计信息
    stats = {
        'mean': np.mean(results),
        'std': np.std(results),
        'ci_95': np.percentile(results, [2.5, 97.5])
    }
    
    return results, stats
```

---

### Step 5: 代码实现

#### 5.1 代码结构

```
code/
├── main.py              # 主程序入口
├── data_analysis.py     # 数据分析（ANOVA、回归）
├── optimization.py      # 参数优化
├── simulation.py        # 蒙特卡洛模拟
├── visualization.py     # 可视化
└── utils.py             # 工具函数
```

#### 5.2 数据预处理

```python
import pandas as pd
import numpy as np

def preprocess_data(df):
    """
    数据预处理
    """
    # 1. 检查缺失值
    print(f"缺失值统计:\n{df.isnull().sum()}")
    
    # 2. 检查异常值
    for col in df.select_dtypes(include=[np.number]).columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)).sum()
        if outliers > 0:
            print(f"{col}: {outliers}个异常值")
    
    # 3. 标准化
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    
    return df, scaler
```

---

### Step 6: 结果分析

#### 6.1 显著性分析
- 各因素的显著性水平（p值）
- 因素贡献率排序
- 交互作用分析

#### 6.2 优化结果
- 最优条件组合
- 预测响应值
- 置信区间

#### 6.3 灵敏度分析
- 各因素对结果的影响程度
- 关键因素识别
- 鲁棒性分析

---

### Step 7: 论文撰写

#### 7.1 章节结构
1. 摘要（最后撰写）
2. 问题重述与分析
3. 模型假设
4. 符号说明
5. 模型建立与求解
   - 5.1 数据预处理
   - 5.2 方差分析
   - 5.3 回归模型
   - 5.4 参数优化
   - 5.5 蒙特卡洛模拟
6. 结果分析与检验
7. 灵敏度分析（必备）
8. 模型评价与推广
9. 参考文献
10. 附录

#### 7.2 图表规范
- 方差分析表：包含F值、p值、显著性标记
- 回归系数表：包含系数、标准误、t值、p值
- 残差图：正态Q-Q图、残差vs拟合值图
- 响应面图：3D响应面、等高线图

---

## 三、核心方法清单

### 3.1 实验设计方法

| 方法 | 适用场景 | 特点 |
|-----|---------|------|
| 全因素设计 | 因素少 | 完整信息，实验次数多 |
| 正交设计 | 因素多 | 均衡分散，实验次数少 |
| Box-Behnken | 3因素 | 无极端组合，效率高 |
| 中心复合设计 | 5因素 | 可拟合二阶模型 |
| 均匀设计 | 多因素 | 实验次数最少 |

### 3.2 统计分析方法

| 方法 | 目的 | 适用场景 |
|-----|------|---------|
| 方差分析 | 因素显著性 | 多组比较 |
| 回归分析 | 建立关系模型 | 预测和优化 |
| 响应面法 | 条件优化 | 寻找最优组合 |
| 蒙特卡洛 | 不确定性分析 | 风险评估 |

### 3.3 优化方法

| 方法 | 特点 | 适用场景 |
|-----|------|---------|
| 岭回归 | 处理共线性 | 高相关数据 |
| LASSO | 特征选择 | 变量筛选 |
| 遗传算法 | 全局优化 | 非线性问题 |
| 模拟退火 | 避免局部最优 | 复杂优化 |

---

## 四、典型问题案例

### 4.1 催化剂优化

**问题描述**：优化乙醇制备C4烯烃的催化剂组合和反应条件。

**建模要点**：
- 实验设计（正交/响应面）
- 方差分析（因素显著性）
- 回归模型（预测响应）
- 条件优化（最优组合）

**核心代码**：
```python
# 方差分析
anova_table, significant_factors = anova_analysis(
    data, 'Y ~ A + B + C + A:B'
)

# 响应面优化
model, predict, poly = response_surface_analysis(
    data, 'Y', ['A', 'B', 'C']
)
optimal_conditions, max_response = find_optimal_conditions(
    predict, [(0, 100), (0, 100), (0, 100)], 3
)
```

### 4.2 调度优化

**问题描述**：优化RGV的调度策略，提高生产效率。

**建模要点**：
- 调度规则设计
- 仿真模型建立
- 参数优化
- 鲁棒性分析

**核心代码**：
```python
def simulate_scheduling(strategy, params):
    """
    调度仿真
    """
    # 初始化
    rgv = RGV()
    cncs = [CNC() for _ in range(n_cncs)]
    
    # 仿真循环
    for t in range(simulation_time):
        # 调度决策
        action = strategy(rgv, cncs, params)
        # 执行动作
        rgv.execute(action)
        # 更新状态
        update_states(rgv, cncs)
    
    return calculate_efficiency(rgv, cncs)
```

### 4.3 策略优化

**问题描述**：优化穿越沙漠的游戏策略。

**建模要点**：
- 博弈模型
- 动态规划
- 随机优化
- 风险分析

---

## 五、代码实现模板

### 5.1 实验设计模板

```python
import numpy as np
import pandas as pd
from itertools import product

class ExperimentalDesign:
    """实验设计框架"""
    
    def __init__(self, factors, levels):
        self.factors = factors
        self.levels = levels
    
    def full_factorial(self):
        """全因素设计"""
        design = list(product(*[range(l) for l in self.levels]))
        return pd.DataFrame(design, columns=self.factors)
    
    def orthogonal_array(self, n_runs=9):
        """正交设计"""
        n_factors = len(self.factors)
        design = np.zeros((n_runs, n_factors), dtype=int)
        
        for j, level in enumerate(self.levels):
            design[:, j] = np.random.choice(level, n_runs)
        
        return pd.DataFrame(design, columns=self.factors)
    
    def box_behnken(self):
        """Box-Behnken设计"""
        if len(self.factors) != 3:
            raise ValueError("Box-Behnken设计需要3个因素")
        
        design = [
            [-1, -1, 0],
            [1, -1, 0],
            [-1, 1, 0],
            [1, 1, 0],
            [-1, 0, -1],
            [1, 0, -1],
            [-1, 0, 1],
            [1, 0, 1],
            [0, -1, -1],
            [0, 1, -1],
            [0, -1, 1],
            [0, 1, 1],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]
        
        return pd.DataFrame(design, columns=self.factors)
```

### 5.2 统计分析模板

```python
import statsmodels.api as sm
from statsmodels.formula.api import ols
import pandas as pd

class StatisticalAnalysis:
    """统计分析框架"""
    
    def __init__(self, data):
        self.data = data
    
    def anova(self, formula):
        """方差分析"""
        model = ols(formula, data=self.data).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)
        
        # 提取显著因素
        significant = anova_table[anova_table['PR(>F)'] < 0.05].index.tolist()
        
        return anova_table, significant
    
    def regression(self, target, features):
        """多元回归"""
        X = self.data[features]
        X = sm.add_constant(X)
        y = self.data[target]
        
        model = sm.OLS(y, X).fit()
        
        return model
    
    def rsm(self, target, features):
        """响应面分析"""
        from sklearn.preprocessing import PolynomialFeatures
        from sklearn.linear_model import LinearRegression
        
        X = self.data[features].values
        y = self.data[target].values
        
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)
        
        model = LinearRegression()
        model.fit(X_poly, y)
        
        return model, poly
    
    def monte_carlo(self, model, X_mean, X_std, n_simulations=10000):
        """蒙特卡洛模拟"""
        results = []
        
        for _ in range(n_simulations):
            X_sample = np.random.normal(X_mean, X_std)
            y_pred = model.predict(X_sample.reshape(1, -1))
            results.append(y_pred[0])
        
        results = np.array(results)
        
        return {
            'mean': np.mean(results),
            'std': np.std(results),
            'ci_95': np.percentile(results, [2.5, 97.5])
        }
```

### 5.3 优化框架模板

```python
from scipy.optimize import minimize, differential_evolution
import numpy as np

class OptimizationFramework:
    """优化框架"""
    
    def __init__(self, model, bounds):
        self.model = model
        self.bounds = bounds
    
    def gradient_optimization(self, x0):
        """梯度优化"""
        result = minimize(
            lambda x: -self.model.predict(x.reshape(1, -1))[0],
            x0,
            bounds=self.bounds,
            method='L-BFGS-B'
        )
        return result.x, -result.fun
    
    def evolutionary_optimization(self):
        """进化优化"""
        result = differential_evolution(
            lambda x: -self.model.predict(x.reshape(1, -1))[0],
            self.bounds,
            seed=42
        )
        return result.x, -result.fun
    
    def response_surface_optimization(self, poly):
        """响应面优化"""
        def objective(x):
            x_poly = poly.transform(x.reshape(1, -1))
            return -self.model.predict(x_poly)[0]
        
        x0 = np.mean(self.bounds, axis=1)
        result = minimize(objective, x0, bounds=self.bounds, method='L-BFGS-B')
        
        return result.x, -result.fun
```

---

## 六、论文写作要点

### 6.1 摘要写作

**结构**：
1. 问题背景（1-2句）
2. 方法概述（2-3句）
3. 主要结果（2-3句）
4. 关键词（3-5个）

**示例**：
> 本文针对乙醇制备C4烯烃的催化剂优化问题，建立了基于响应面法的实验设计与优化模型。首先，采用Box-Behnken设计进行了15组实验；其次，通过方差分析识别了显著因素；最后，建立了二阶多项式回归模型并优化了反应条件。结果表明，最优催化剂组合为A₂B₁C₃，预测产率达到85.3%。

### 6.2 方差分析章节

**写作要点**：
- 必须包含完整的方差分析表
- 必须说明显著性水平（α=0.05）
- 必须解释F值和p值含义
- 必须说明因素贡献率

### 6.3 回归模型章节

**写作要点**：
- 必须包含回归系数表
- 必须说明R²和调整R²
- 必须检验残差正态性
- 必须检验多重共线性

### 6.4 优化结果章节

**写作要点**：
- 必须说明优化方法
- 必须给出最优条件
- 必须给出预测值和置信区间
- 必须验证优化结果

---

## 七、常见陷阱与解决方案

### 7.1 实验设计陷阱

| 陷阱 | 后果 | 解决方案 |
|-----|------|---------|
| 因素选择不当 | 遗漏重要因子 | 充分调研文献 |
| 水平设置不合理 | 无法检测显著性 | 预实验确定范围 |
| 忽略交互作用 | 模型不准确 | 包含交互项 |

### 7.2 数据分析陷阱

| 陷阱 | 后果 | 解决方案 |
|-----|------|---------|
| 未做方差分析 | 无法判断显著性 | 必须进行ANOVA |
| 忽略残差检验 | 模型不可靠 | 检验正态性和方差齐性 |
| 多重共线性 | 系数不稳定 | 使用VIF检验和岭回归 |

### 7.3 优化陷阱

| 陷阱 | 后果 | 解决方案 |
|-----|------|---------|
| 过拟合 | 预测不准 | 交叉验证 |
| 外推预测 | 结果不可靠 | 仅在实验范围内预测 |
| 未验证优化结果 | 结果不可信 | 实验验证 |

### 7.4 论文写作陷阱

| 陷阱 | 后果 | 解决方案 |
|-----|------|---------|
| 图表不规范 | 不专业 | 按规范制作图表 |
| 缺少统计检验 | 说服力不足 | 包含p值和置信区间 |
| 解释不充分 | 审核不通过 | 详细解释统计结果 |

---

## 八、与其他题型的区别

### 8.1 与A题（物理建模）的区别

| 维度 | B题（实验设计） | A题（物理建模） |
|-----|---------------|---------------|
| 数据来源 | 实验数据 | 理论推导/实验验证 |
| 核心方法 | 回归分析/方差分析 | 微分方程/数值求解 |
| 验证方式 | 统计检验/交叉验证 | 物理校验/守恒验证 |
| 优化目标 | 实验条件最优 | 物理性能最优 |
| 论文重点 | 统计分析/实验设计 | 物理机理/数学推导 |

### 8.2 与C题（数据分析）的区别

| 维度 | B题（实验设计） | C题（数据分析） |
|-----|---------------|---------------|
| 数据来源 | 实验数据 | 实际业务数据 |
| 核心方法 | 统计分析 | 机器学习 |
| 模型类型 | 回归/响应面 | 分类/聚类/回归 |
| 优化目标 | 条件优化 | 预测/决策 |
| 论文重点 | 实验设计/统计检验 | 数据处理/模型解释 |

### 8.3 与D题（优化调度）的区别

| 维度 | B题（实验设计） | D题（优化调度） |
|-----|---------------|---------------|
| 问题性质 | 实验优化 | 资源分配 |
| 核心方法 | 统计分析 | 整数规划 |
| 约束类型 | 实验条件 | 资源约束 |
| 优化目标 | 响应最优 | 效率最高 |
| 论文重点 | 实验设计/统计分析 | 算法设计/复杂度分析 |

### 8.4 与E题（交叉学科）的区别

| 维度 | B题（实验设计） | E题（交叉学科） |
|-----|---------------|---------------|
| 学科领域 | 统计学 | 多学科交叉 |
| 核心方法 | 实验设计 | 多种方法综合 |
| 复杂度 | 统计方法复杂 | 系统交互复杂 |
| 创新点 | 实验设计创新 | 方法融合创新 |
| 论文重点 | 统计深度 | 跨学科广度 |

---

## 九、实战检查清单

### 9.1 实验设计阶段
- [ ] 因素识别完整
- [ ] 水平设置合理
- [ ] 实验设计方法选择正确
- [ ] 实验次数足够

### 9.2 数据分析阶段
- [ ] 数据预处理完成
- [ ] 方差分析完成
- [ ] 回归模型建立
- [ ] 残差检验通过
- [ ] 多重共线性检验通过

### 9.3 优化阶段
- [ ] 优化方法选择合理
- [ ] 优化结果收敛
- [ ] 优化结果验证
- [ ] 蒙特卡洛模拟完成

### 9.4 论文阶段
- [ ] 摘要完整
- [ ] 方差分析表规范
- [ ] 回归系数表规范
- [ ] 图表规范
- [ ] 灵敏度分析完整

---

## 十、参考资源

### 10.1 方法论
- 实验设计理论
- 回归分析方法
- 响应面方法

### 10.2 代码模板
- 正交设计
- 方差分析
- 响应面优化

### 10.3 领域知识
- 化学实验知识
- 统计学基础
- 优化理论

### 10.4 获奖论文参考
- B007: C4烯烃制备分析与试验设计
- B050: 乙醇偶合制备C4烯烃的多元回归与神经网络模型
- B160: 乙醇制备C4烯烃催化剂组合的分析与设计
- B026: 基于双因素方差分析的乙醇制备C4烯烃的研究
