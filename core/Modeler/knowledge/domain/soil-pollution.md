# 土壤重金属污染知识库

> 本文件提供数学建模竞赛中土壤重金属污染相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 污染物空间分布建模与制图
- 污染源识别与溯源分析
- 重金属健康风险评估
- 土壤污染等级划分
- 污染趋势预测与预警

### 1.2 常见约束条件
- 空间约束：采样点分布、区域边界
- 浓度约束：检出限、背景值
- 标准约束：国家/地方土壤质量标准
- 时间约束：采样时间一致性

### 1.3 数据特点
- 空间数据：采样点经纬度、海拔
- 浓度数据：多种重金属含量（mg/kg）
- 辅助数据：土地利用类型、工业分布
- 标准数据：土壤背景值、质量标准

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| Kriging插值 | 空间分布建模 | 最优无偏估计 | 需要变异函数拟合 |
| IDW插值 | 快速空间估计 | 计算简单 | 受采样点影响大 |
| 主成分分析 | 污染源识别 | 降维效果好 | 结果解释需专业知识 |
| 相关性分析 | 元素关联性 | 直观易理解 | 无法确定因果关系 |
| 污染指数法 | 污染评价 | 国际通用 | 权重确定主观 |
| GIS空间分析 | 综合制图 | 可视化效果好 | 需要专业软件 |

---

## 3. 数学基础

### 3.1 Kriging空间插值

**普通Kriging公式**：
```
Z(s₀) = Σᵢ λᵢ Z(sᵢ)
```

其中：
- Z(s₀): 待估点s₀的估计值
- λᵢ: 第i个采样点的权重
- Z(sᵢ): 第i个采样点的实测值

**权重求解**：
```
Σⱼ λⱼ γ(sᵢ, sⱼ) + μ = γ(sᵢ, s₀), ∀i
Σᵢ λᵢ = 1
```

其中：
- γ(sᵢ, sⱼ): 半变异函数值
- μ: 拉格朗日乘子

### 3.2 半变异函数

**理论模型**：
```
γ(h) = C₀ + C₁ · f(h/a)
```

常用模型：
- 球状模型：f(h/a) = 1.5(h/a) - 0.5(h/a)³, h≤a
- 指数模型：f(h/a) = 1 - exp(-3h/a)
- 高斯模型：f(h/a) = 1 - exp(-3h²/a²)

参数含义：
- C₀: 块金值（微观变异）
- C₁: 基台值（总变异）
- a: 变程（空间相关距离）

### 3.3 污染评价指数

**单因子指数法**：
```
Pᵢ = Cᵢ / Sᵢ
```

其中：
- Pᵢ: 第i种重金属的污染指数
- Cᵢ: 实测浓度
- Sᵢ: 评价标准

**内梅罗综合指数**：
```
P = √[(P_avg² + P_max²) / 2]
```

**地累积指数**：
```
Igeo = log₂[Cₙ / (1.5 × Bₙ)]
```

其中：
- Bₙ: 背景值
- 1.5: 修正系数

### 3.4 风险评估

**健康风险模型**：
```
HQ = CDI / RfD
```

其中：
- HQ: 危害商数
- CDI: 暴露剂量
- RfD: 参考剂量

**致癌风险**：
```
CR = CDI × SF
```

其中：
- SF: 斜率因子

---

## 4. 代码实现

### 4.1 Kriging插值

```python
import numpy as np
from scipy.spatial.distance import cdist
from scipy.optimize import minimize

class OrdinaryKriging:
    """
    普通Kriging插值
    """
    def __init__(self, X, Z, model='spherical'):
        """
        Parameters
        ----------
        X : array
            采样点坐标 (n, 2)
        Z : array
            采样值 (n,)
        model : str
            变异函数模型
        """
        self.X = np.array(X)
        self.Z = np.array(Z)
        self.n = len(Z)
        self.model = model
    
    def variogram(self, h, C0, C1, a):
        """
        计算变异函数值
        
        Parameters
        ----------
        h : float/array
            距离
        C0 : float
            块金值
        C1 : float
            基台值
        a : float
            变程
        """
        h = np.asarray(h)
        gamma = np.zeros_like(h, dtype=float)
        
        mask = h > 0
        h_masked = h[mask]
        
        if self.model == 'spherical':
            idx = h_masked <= a
            gamma[mask][idx] = C0 + C1 * (1.5 * h_masked[idx]/a - 0.5 * (h_masked[idx]/a)**3)
            gamma[mask][~idx] = C0 + C1
        elif self.model == 'exponential':
            gamma[mask] = C0 + C1 * (1 - np.exp(-3 * h_masked / a))
        elif self.model == 'gaussian':
            gamma[mask] = C0 + C1 * (1 - np.exp(-3 * h_masked**2 / a**2))
        
        return gamma
    
    def fit_variogram(self):
        """
        拟合变异函数参数
        """
        # 计算实验变异函数
        distances = cdist(self.X, self.X)
        pairs = []
        
        for i in range(self.n):
            for j in range(i+1, self.n):
                pairs.append((distances[i, j], (self.Z[i] - self.Z[j])**2 / 2))
        
        pairs = np.array(pairs)
        
        # 分组计算平均值
        h_max = np.max(pairs[:, 0])
        n_bins = min(15, self.n // 3)
        bins = np.linspace(0, h_max, n_bins + 1)
        
        experimental_h = []
        experimental_gamma = []
        
        for k in range(n_bins):
            mask = (pairs[:, 0] >= bins[k]) & (pairs[:, 0] < bins[k+1])
            if np.sum(mask) > 0:
                experimental_h.append(np.mean(pairs[mask, 0]))
                experimental_gamma.append(np.mean(pairs[mask, 1]))
        
        experimental_h = np.array(experimental_h)
        experimental_gamma = np.array(experimental_gamma)
        
        # 拟合参数
        def objective(params):
            C0, C1, a = params
            if C0 < 0 or C1 < 0 or a < 0:
                return 1e10
            predicted = self.variogram(experimental_h, C0, C1, a)
            return np.sum((predicted - experimental_gamma)**2)
        
        result = minimize(objective, [0, np.var(self.Z), h_max/3], 
                         method='Nelder-Mead')
        
        self.C0, self.C1, self.a = result.x
        return self.C0, self.C1, self.a
    
    def predict(self, X_pred):
        """
        预测新位置的值
        """
        X_pred = np.array(X_pred)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(1, -1)
        
        m = len(X_pred)
        Z_pred = np.zeros(m)
        
        for k in range(m):
            # 计算预测点与采样点的距离
            h = cdist(X_pred[k:k+1], self.X)[0]
            
            # 构建Kriging方程组
            gamma = self.variogram(h, self.C0, self.C1, self.a)
            Gamma = self.variogram(cdist(self.X, self.X), self.C0, self.C1, self.a)
            
            # 增广矩阵
            A = np.zeros((self.n + 1, self.n + 1))
            A[:self.n, :self.n] = Gamma
            A[:self.n, self.n] = 1
            A[self.n, :self.n] = 1
            
            b = np.zeros(self.n + 1)
            b[:self.n] = gamma
            
            # 求解权重
            weights = np.linalg.solve(A, b)
            
            # 预测
            Z_pred[k] = np.sum(weights[:self.n] * self.Z)
        
        return Z_pred
```

### 4.2 污染评价

```python
import numpy as np

def single_factor_index(concentration, standard):
    """
    单因子污染指数
    
    Parameters
    ----------
    concentration : float/array
        实测浓度
    standard : float
        评价标准
    
    Returns
    -------
    P : float/array
        单因子指数
    """
    return concentration / standard


def nemerow_index(P_values):
    """
    内梅罗综合污染指数
    
    Parameters
    ----------
    P_values : array
        各因子指数
    
    Returns
    -------
    P : float
        综合指数
    """
    P_avg = np.mean(P_values)
    P_max = np.max(P_values)
    return np.sqrt((P_avg**2 + P_max**2) / 2)


def geo_accumulation_index(concentration, background, correction=1.5):
    """
    地累积指数
    
    Parameters
    ----------
    concentration : float
        实测浓度
    background : float
        背景值
    correction : float
        修正系数
    
    Returns
    -------
    Igeo : float
        地累积指数
    """
    return np.log2(concentration / (correction * background))


def pollution_classification(P):
    """
    污染等级划分
    
    Returns
    -------
    level : str
        污染等级
    """
    if P <= 0.7:
        return '清洁'
    elif P <= 1.0:
        return '尚清洁'
    elif P <= 2.0:
        return '轻度污染'
    elif P <= 3.0:
        return '中度污染'
    else:
        return '重度污染'


def risk_assessment(concentration, ingestion_rate, exposure_frequency,
                    body_weight, RfD):
    """
    健康风险评估
    
    Parameters
    ----------
    concentration : float
        重金属浓度 (mg/kg)
    ingestion_rate : float
        土壤摄入率 (kg/day)
    exposure_frequency : float
        暴露频率 (days/year)
    body_weight : float
        体重 (kg)
    RfD : float
        参考剂量 (mg/kg/day)
    
    Returns
    -------
    HQ : float
        危害商数
    """
    # 暴露剂量 (ADD)
    ADD = (concentration * ingestion_rate * exposure_frequency) / (body_weight * 365)
    
    # 危害商数
    HQ = ADD / RfD
    
    return HQ
```

### 4.3 空间统计分析

```python
import numpy as np
from scipy.spatial.distance import cdist

def spatial_autocorrelation(X, Z, k=5):
    """
    空间自相关分析（Moran's I）
    
    Parameters
    ----------
    X : array
        坐标
    Z : array
        观测值
    k : int
        近邻数
    
    Returns
    -------
    I : float
        Moran's I指数
    """
    n = len(Z)
    
    # 构建空间权重矩阵（k近邻）
    W = np.zeros((n, n))
    distances = cdist(X, X)
    
    for i in range(n):
        nearest = np.argsort(distances[i])[1:k+1]
        W[i, nearest] = 1
    
    # 行标准化
    row_sums = W.sum(axis=1)
    row_sums[row_sums == 0] = 1
    W = W / row_sums[:, np.newaxis]
    
    # 计算Moran's I
    Z_mean = np.mean(Z)
    Z_centered = Z - Z_mean
    
    numerator = n * np.sum(W * np.outer(Z_centered, Z_centered))
    denominator = np.sum(W) * np.sum(Z_centered**2)
    
    I = numerator / denominator
    
    return I


def hot_spot_analysis(X, Z, confidence=0.95):
    """
    热点分析（Getis-Ord Gi*）
    
    Parameters
    ----------
    X : array
        坐标
    Z : array
        观测值
    confidence : float
        置信水平
    
    Returns
    -------
    gi_star : array
        Gi*统计量
    p_values : array
        p值
    """
    n = len(Z)
    distances = cdist(X, X)
    
    # 空间权重（距离衰减）
    max_dist = np.percentile(distances, 80)
    W = np.exp(-distances**2 / (2 * max_dist**2))
    np.fill_diagonal(W, 0)
    
    # 计算Gi*
    Z_mean = np.mean(Z)
    Z_std = np.std(Z)
    
    gi_star = np.zeros(n)
    
    for i in range(n):
        numerator = np.sum(W[i] * Z) - Z_mean * np.sum(W[i])
        denominator = Z_std * np.sqrt(
            (n * np.sum(W[i]**2) - np.sum(W[i])**2) / (n - 1)
        )
        
        if denominator > 0:
            gi_star[i] = numerator / denominator
        else:
            gi_star[i] = 0
    
    # p值（正态分布近似）
    from scipy import stats
    p_values = 2 * (1 - stats.norm.cdf(np.abs(gi_star)))
    
    return gi_star, p_values
```

### 4.4 可视化

```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

def plot_pollution_map(X, Z, grid_size=100, title="重金属浓度分布图"):
    """
    绘制污染分布图
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # 创建网格
    x_min, x_max = X[:, 0].min(), X[:, 0].max()
    y_min, y_max = X[:, 1].min(), X[:, 1].max()
    
    xi = np.linspace(x_min, x_max, grid_size)
    yi = np.linspace(y_min, y_max, grid_size)
    XI, YI = np.meshgrid(xi, yi)
    
    # Kriging插值
    krig = OrdinaryKriging(X, Z)
    krig.fit_variogram()
    ZI = krig.predict(np.column_stack([XI.ravel(), YI.ravel()])).reshape(grid_size, grid_size)
    
    # 自定义颜色
    colors = ['green', 'yellow', 'orange', 'red', 'darkred']
    cmap = LinearSegmentedColormap.from_list('pollution', colors)
    
    # 绘图
    im = ax.pcolormesh(XI, YI, ZI, cmap=cmap, shading='auto')
    ax.scatter(X[:, 0], X[:, 1], c='black', s=50, marker='o', label='采样点')
    
    # 等值线
    contour = ax.contour(XI, YI, ZI, levels=8, colors='black', linewidths=0.5)
    ax.clabel(contour, inline=True, fontsize=8)
    
    ax.set_xlabel('X坐标 (m)')
    ax.set_ylabel('Y坐标 (m)')
    ax.set_title(title)
    ax.legend()
    
    plt.colorbar(im, ax=ax, label='浓度 (mg/kg)')
    plt.tight_layout()
    plt.show()
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 变异函数拟合不当 | 插值结果失真 | 尝试多种模型并交叉验证 |
| 忽略各向异性 | 方向性变异忽略 | 使用各向异性变异函数 |
| 采样点分布不均 | 局部估计偏差 | 使用局部插值或密度加权 |
| 标准选择错误 | 评价结果偏差 | 使用最新国家标准 |
| 单位换算错误 | 浓度量级错误 | 统一使用mg/kg |
| 忽略背景值 | 污染程度高估 | 区分地质背景和人为污染 |

---

## 6. 验证方法

### 6.1 交叉验证
- 留一法交叉验证
- 计算RMSE、MAE、R²
- 检验残差空间自相关性

### 6.2 结果验证
- 与实测值对比
- 检查浓度范围合理性
- 验证污染等级划分

### 6.3 空间验证
- 检查空间分布是否符合已知污染源
- 验证热点区域是否与工业区吻合
- 检查插值结果边界效应

### 6.4 敏感性分析
- 采样点数量的影响
- 变异函数参数的影响
- 插值方法的选择影响

---

## 7. 真题案例

### 2011A 城市土壤重金属污染

**题目概述**：研究某城市土壤重金属（Cd、Cr、Cu、Pb、Zn等）的空间分布特征和污染来源。

**关键信息**：
- 采样点坐标和重金属浓度数据
- 需要绘制空间分布图
- 识别主要污染源

**解题思路**：
1. 数据预处理（异常值检测、正态性检验）
2. 描述性统计分析
3. Kriging空间插值
4. 主成分分析/因子分析（污染源识别）
5. 污染评价（内梅罗指数、地累积指数）
6. 综合制图

**参考代码框架**：
```python
# 2011A问题求解框架
# 1. 数据加载
X = np.array([...])  # 坐标
Z_cd = np.array([...])  # Cd浓度

# 2. Kriging插值
krig = OrdinaryKriging(X, Z_cd, model='spherical')
krig.fit_variogram()
Z_pred = krig.predict(grid_points)

# 3. 污染评价
P_cd = single_factor_index(Z_cd, standard_cd=0.3)
P_nemerow = nemerow_index(P_cd)

# 4. 可视化
plot_pollution_map(X, Z_cd, title='Cd浓度分布')
```

---

## 8. 参考文献

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| 2011A-A01 | Kriging+PCA | 多元素综合分析 |
| 2011A-A02 | GIS+地统计学 | 空间可视化 |
| 2011A-A03 | 因子分析 | 污染源解析 |

---

## 9. 验证清单

- [ ] 数据正态性检验（Shapiro-Wilk检验）
- [ ] 变异函数拟合优度检查
- [ ] Kriging插值RMSE < 实测值标准差的30%
- [ ] Moran's I > 0 表示空间正相关
- [ ] 污染评价标准使用正确
- [ ] 背景值选取合理
- [ ] 地图比例尺和图例完整
- [ ] 采样点分布图已展示
