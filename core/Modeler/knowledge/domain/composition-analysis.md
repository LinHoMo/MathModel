# 成分数据分析领域知识

## 一、核心概念

### 1.1 成分数据定义
- **定义**: 各组分比例之和为1的数据
- **特点**: 有约束（Σx_i = 1）、非负
- **示例**: 化学成分、市场份额、人口比例

### 1.2 常见问题
- **分类鉴别**: 根据成分判断类别
- **成分回归**: 成分作为自变量/因变量
- **异常检测**: 识别异常成分

### 1.3 数据预处理
- **CLR变换**: 中心对数比变换
- **ILR变换**: 等距对数比变换
- **ALR变换**: 加法对数比变换

---

## 二、CLR变换

### 2.1 CLR变换公式
```
CLR(x) = [ln(x1/g), ln(x2/g), ..., ln(xn/g)]
g = (Πx_i)^(1/n)  # 几何平均
```

### 2.2 Python实现
```python
import numpy as np

def clr_transform(x):
    """
    中心对数比变换
    """
    geo_mean = np.exp(np.mean(np.log(x)))
    clr = np.log(x / geo_mean)
    return clr

def clr_inverse(clr):
    """
    CLR逆变换
    """
    x = np.exp(clr)
    x = x / np.sum(x)
    return x
```

### 2.3 应用场景
- **成分聚类**: 对CLR变换后数据聚类
- **成分PCA**: 对CLR变换后数据降维
- **成分回归**: CLR后进行线性回归

---

## 三、分类鉴别

### 3.1 逻辑回归
```python
def composition_classification(X, y):
    """
    成分数据分类
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    
    # CLR变换
    X_clr = np.array([clr_transform(x) for x in X])
    
    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_clr)
    
    # 逻辑回归
    model = LogisticRegression()
    model.fit(X_scaled, y)
    
    return model
```

### 3.2 随机森林
```python
def random_forest_composition(X, y):
    """
    随机森林分类
    """
    from sklearn.ensemble import RandomForestClassifier
    
    # CLR变换
    X_clr = np.array([clr_transform(x) for x in X])
    
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_clr, y)
    
    return model
```

### 3.3 支持向量机
```python
def svm_composition(X, y):
    """
    SVM分类
    """
    from sklearn.svm import SVC
    from sklearn.preprocessing import StandardScaler
    
    X_clr = np.array([clr_transform(x) for x in X])
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_clr)
    
    model = SVC(kernel='rbf')
    model.fit(X_scaled, y)
    
    return model
```

---

## 四、成分聚类

### 4.1 K-Means聚类
```python
def kmeans_composition(X, n_clusters):
    """
    成分数据聚类
    """
    from sklearn.cluster import KMeans
    
    # CLR变换
    X_clr = np.array([clr_transform(x) for x in X])
    
    model = KMeans(n_clusters=n_clusters)
    labels = model.fit_predict(X_clr)
    
    return labels, model.cluster_centers_
```

### 4.2 层次聚类
```python
def hierarchical_composition(X, n_clusters):
    """
    层次聚类
    """
    from sklearn.cluster import AgglomerativeClustering
    from scipy.spatial.distance import pdist, squareform
    
    X_clr = np.array([clr_transform(x) for x in X])
    
    # 计算距离矩阵
    dist_matrix = squareform(pdist(X_clr, metric='euclidean'))
    
    model = AgglomerativeClustering(n_clusters=n_clusters, 
                                    metric='precomputed',
                                    linkage='average')
    labels = model.fit_predict(dist_matrix)
    
    return labels
```

---

## 五、异常检测

### 5.1 基于距离的异常
```python
def distance_outlier_detection(X, threshold=2):
    """
    基于距离的异常检测
    """
    X_clr = np.array([clr_transform(x) for x in X])
    
    from sklearn.neighbors import NearestNeighbors
    
    model = NearestNeighbors(n_neighbors=5)
    model.fit(X_clr)
    
    distances, indices = model.kneighbors(X_clr)
    avg_distances = np.mean(distances, axis=1)
    
    outliers = avg_distances > threshold * np.mean(avg_distances)
    
    return outliers
```

### 5.2 基于密度的异常
```python
def lof_outlier_detection(X):
    """
    LOF异常检测
    """
    from sklearn.neighbors import LocalOutlierFactor
    
    X_clr = np.array([clr_transform(x) for x in X])
    
    model = LocalOutlierFactor(n_neighbors=20)
    outliers = model.fit_predict(X_clr)
    
    return outliers == -1
```

---

## 六、论文写作要点

### 6.1 问题分析框架
1. **数据理解**: 成分特征、类别分布
2. **数据变换**: CLR/ILR变换
3. **特征分析**: 主成分、相关性
4. **模型选择**: 分类/聚类/异常检测
5. **结果分析**: 准确率、混淆矩阵
6. **灵敏度分析**: 特征重要性

### 6.2 图表规范
- **三元图**: 三组分可视化
- **堆叠条形图**: 成分比例
- **相关性热力图**: 成分相关性
- **聚类树状图**: 层次聚类

### 6.3 LaTeX代码
```latex
\begin{equation}
CLR(\mathbf{x}) = \left[\ln\frac{x_1}{g}, \ln\frac{x_2}{g}, \ldots, \ln\frac{x_n}{g}\right]
\label{eq:clr}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{ternary_plot.pdf}
\caption{三元图}
\label{fig:ternary}
\end{figure}
```

---

## 七、参考文献

1. Aitchison J. The Statistical Analysis of Compositional Data. Wiley, 1986.
2. Pawlowsky-Glahn V. Compositional Data Analysis. Wiley, 2015.
3. van den Boogaart K G. Analyzing Compositional Data with R. Springer, 2013.
4. 朱明. 成分数据分析. 高等教育出版社, 2018.
