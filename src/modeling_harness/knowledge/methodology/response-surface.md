# 响应面法(RSM)领域知识

## 一、核心概念

### 1.1 响应面法定义
- **定义**: 一种实验设计和优化方法
- **目标**: 建立输入变量与响应之间的关系模型
- **应用**: 实验设计、参数优化、过程优化

### 1.2 适用场景
- 实验次数有限
- 因素间存在交互作用
- 需要寻找最优条件
- 响应与因素关系复杂

### 1.3 基本流程
```
1. 筛选显著因素
2. 确定因素范围
3. 设计实验方案
4. 建立回归模型
5. 寻找最优条件
6. 验证优化结果
```

---

## 二、实验设计

### 2.1 全因子设计
```
2^k 设计: k个因素，每个2水平
实验次数: 2^k
```

### 2.2 部分因子设计
```
2^(k-p) 设计: 2^k的1/2^p部分
实验次数: 2^(k-p)
```

### 2.3 中心复合设计（CCD）
```python
def ccd_design(n_factors, alpha='rotatable'):
    """
    中心复合设计
    """
    # 2^k 因子点
    factorial_points = np.array([[(-1)**((i >> j) & 1) 
                                  for j in range(n_factors)] 
                                 for i in range(2**n_factors)])
    
    # 轴向点
    axial_points = np.zeros((2*n_factors, n_factors))
    for i in range(n_factors):
        axial_points[2*i, i] = alpha
        axial_points[2*i+1, i] = -alpha
    
    # 中心点
    center_points = np.zeros((5, n_factors))
    
    return np.vstack([factorial_points, axial_points, center_points])
```

### 2.4 Box-Behnken设计
```python
def box_behnken_design(n_factors):
    """
    Box-Behnken设计
    """
    # 三因素设计
    if n_factors == 3:
        points = [
            [-1, -1, 0], [-1, 1, 0], [1, -1, 0], [1, 1, 0],
            [-1, 0, -1], [-1, 0, 1], [1, 0, -1], [1, 0, 1],
            [0, -1, -1], [0, -1, 1], [0, 1, -1], [0, 1, 1],
            [0, 0, 0], [0, 0, 0], [0, 0, 0]
        ]
        return np.array(points)
```

---

## 三、回归模型

### 3.1 一阶模型
```
y = β0 + Σβi*xi + ε
```

### 3.2 二阶模型（响应面）
```
y = β0 + Σβi*xi + Σβii*xi² + ΣΣβij*xi*xj + ε
```

### 3.3 模型拟合
```python
def fit_response_surface(X, y):
    """
    拟合响应面模型
    """
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.linear_model import LinearRegression
    
    # 生成二次项
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)
    
    # 拟合模型
    model = LinearRegression()
    model.fit(X_poly, y)
    
    return model, poly
```

### 3.4 模型评估
```python
def evaluate_model(model, X, y):
    """
    评估响应面模型
    """
    from sklearn.metrics import r2_score, mean_squared_error
    
    y_pred = model.predict(X)
    
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    
    return {'r2': r2, 'mse': mse}
```

---

## 四、优化方法

### 4.1 岭分析
```python
def ridge_analysis(model, poly):
    """
    岭分析寻找最陡上升方向
    """
    # 获取系数
    coef = model.coef_
    
    # 最陡上升方向
    direction = coef / np.linalg.norm(coef)
    
    return direction
```

### 4.2 规范形式
```python
def canonical_analysis(model, center):
    """
    规范形式分析
    """
    # 获取二次项系数
    B = model.coef_[1+n_factors:1+n_factors+n_factors**2].reshape(n_factors, n_factors)
    
    # 特征值分解
    eigenvalues, eigenvectors = np.linalg.eigh(B)
    
    return eigenvalues, eigenvectors
```

### 4.3 遗传算法优化
```python
def optimize_rsm_ga(model, poly, bounds):
    """
    使用遗传算法优化响应面
    """
    def fitness(x):
        X_poly = poly.transform(x.reshape(1, -1))
        return model.predict(X_poly)[0]
    
    # 遗传算法优化
    # ...
    return best_x, best_y
```

---

## 五、诊断与验证

### 5.1 残差分析
```python
def residual_analysis(model, X, y):
    """
    残差分析
    """
    y_pred = model.predict(X)
    residuals = y - y_pred
    
    # 正态性检验
    from scipy.stats import shapiro
    stat, p_value = shapiro(residuals)
    
    return {'residuals': residuals, 'p_value': p_value}
```

### 5.2 方差分析（ANOVA）
```python
def anova_analysis(model, X, y):
    """
    方差分析
    """
    from sklearn.metrics import mean_squared_error
    
    y_pred = model.predict(X)
    
    SS_res = np.sum((y - y_pred)**2)
    SS_tot = np.sum((y - np.mean(y))**2)
    
    R2 = 1 - SS_res/SS_tot
    R2_adj = 1 - (1-R2)*(len(y)-1)/(len(y)-X.shape[1]-1)
    
    return {'R2': R2, 'R2_adj': R2_adj}
```

---

## 六、论文写作要点

### 6.1 问题分析框架
1. **因素筛选**: 确定关键因素
2. **实验设计**: CCD/Box-Behnken
3. **模型建立**: 二阶响应面
4. **模型验证**: 残差分析、ANOVA
5. **优化求解**: 岭分析/遗传算法
6. **结果验证**: 最优条件实验

### 6.2 图表规范
- **等高线图**: 响应面投影
- **3D响应面图**: 立体展示
- **残差图**: 模型诊断
- **优化路径**: 最陡上升

### 6.3 LaTeX代码
```latex
\begin{equation}
y = \beta_0 + \sum_{i=1}^k \beta_i x_i + \sum_{i=1}^k \beta_{ii} x_i^2 + \sum_{i<j} \beta_{ij} x_i x_j + \varepsilon
\label{eq:rsm}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{response_surface.pdf}
\caption{响应面图}
\label{fig:rsm}
\end{figure}
```

---

## 七、参考文献

1. Montgomery D C. Design and Analysis of Experiments. Wiley, 2017.
2. Myers R H. Response Surface Methodology. Wiley, 2016.
3. 刘文卿. 实验设计. 清华大学出版社, 2005.
4. Box G E P. Statistics for Experiments. Wiley, 1978.
