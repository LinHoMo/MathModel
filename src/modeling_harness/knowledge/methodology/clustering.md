# 聚类算法方法论

> 本文件提供数学建模竞赛中常用的聚类算法知识，包括算法选择、评估指标、防错策略和验证方法。

---

## 1. 算法选择决策树

```
聚类问题类型识别：
├── 数据量小(n<1000)
│   ├── 形状凸 → K-Means
│   ├── 形状复杂 → DBSCAN
│   └── 层次结构 → 层次聚类
├── 数据量大(n≥1000)
│   ├── K-Means → Mini-Batch K-Means
│   └── DBSCAN → HDBSCAN
├── 高维数据
│   ├── 降维后聚类 → PCA+t-SNE
│   └── 子空间聚类 → Spectral Clustering
└── 概率模型
    └── 软聚类 → 高斯混合模型(GMM)
```

---

## 2. 核心算法详解

### 2.1 K-Means聚类

**方法原理**：
将数据划分为K个簇，通过迭代更新簇中心，最小化簇内平方和。

**适用场景**：
- 数据量大，计算效率高
- 簇形状近似凸形
- 需要快速聚类
- 客户分群、图像分割

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| n_clusters | 2-10 | 聚类数（需预设） |
| max_iter | 100-300 | 最大迭代次数 |
| n_init | 10-20 | 不同初始化次数 |

**选择聚类数的方法**：
- 肘部法则（Elbow Method）
- 轮廓系数（Silhouette Score）
- Gap Statistic

**代码框架**：
```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import matplotlib.pyplot as plt
import numpy as np

def kmeans_clustering(X, max_k=10, random_state=42):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    inertias = []
    silhouette_scores = []
    K_range = range(2, max_k + 1)
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(X_scaled, kmeans.labels_))
    
    # 肘部图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(K_range, inertias, 'bo-')
    ax1.set_xlabel('聚类数K')
    ax1.set_ylabel('惯性值')
    ax1.set_title('肘部法则')
    
    ax2.plot(K_range, silhouette_scores, 'ro-')
    ax2.set_xlabel('聚类数K')
    ax2.set_ylabel('轮廓系数')
    ax2.set_title('轮廓分析')
    plt.tight_layout()
    
    best_k = K_range[np.argmax(silhouette_scores)]
    print(f"最佳聚类数: {best_k}")
    
    kmeans = KMeans(n_clusters=best_k, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    print(f"轮廓系数: {silhouette_score(X_scaled, labels):.4f}")
    print(f"CH指数: {calinski_harabasz_score(X_scaled, labels):.4f}")
    
    return kmeans, labels, best_k
```

---

### 2.2 DBSCAN

**方法原理**：
基于密度的聚类，将紧密相连的样本划分为同一簇，可发现任意形状的簇并识别噪声点。

**适用场景**：
- 簇形状不规则
- 需要识别噪声/异常点
- 数据分布不均匀
- 空间数据聚类

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| eps | 0.1-2.0 | 邻域半径 |
| min_samples | 3-10 | 最小样本数 |

**代码框架**：
```python
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import numpy as np

def dbscan_clustering(X, eps_range=np.arange(0.3, 2.0, 0.1),
                      min_samples_range=[3, 5, 7, 10]):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    best_score = -1
    best_params = None
    
    for eps in eps_range:
        for min_samples in min_samples_range:
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            labels = dbscan.fit_predict(X_scaled)
            
            # 排除噪声点计算轮廓系数
            if len(set(labels)) > 1 and -1 not in labels:
                score = silhouette_score(X_scaled, labels)
                if score > best_score:
                    best_score = score
                    best_params = (eps, min_samples)
    
    print(f"最佳参数: eps={best_params[0]}, min_samples={best_params[1]}")
    
    dbscan = DBSCAN(eps=best_params[0], min_samples=best_params[1])
    labels = dbscan.fit_predict(X_scaled)
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    
    print(f"聚类数: {n_clusters}")
    print(f"噪声点数: {n_noise}")
    print(f"轮廓系数: {best_score:.4f}")
    
    return dbscan, labels, best_params
```

---

### 2.3 层次聚类

**方法原理**：
通过计算簇间距离，逐步合并或分裂簇，形成层次树状结构。

**适用场景**：
- 数据量小
- 需要层次结构展示
- 不确定聚类数
- 生物学/社会科学分析

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| linkage | ward/complete/average | 簇间距离计算方法 |
| n_clusters | 2-10 | 最终聚类数 |

**代码框架**：
```python
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt

def hierarchical_clustering(X, n_clusters=3):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 绘制树状图
    linked = linkage(X_scaled, method='ward')
    plt.figure(figsize=(10, 6))
    dendrogram(linked, truncate_mode='lastp', p=30)
    plt.title('层次聚类树状图')
    plt.xlabel('样本')
    plt.ylabel('距离')
    plt.tight_layout()
    
    # 聚类
    model = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
    labels = model.fit_predict(X_scaled)
    
    print(f"聚类数: {n_clusters}")
    print(f"各簇样本数: {np.bincount(labels)}")
    
    return model, labels
```

---

### 2.4 高斯混合模型 (GMM)

**方法原理**：
假设数据由多个高斯分布混合生成，通过EM算法估计各分布参数，实现软聚类。

**适用场景**：
- 簇形状为椭圆形
- 需要软聚类（概率分配）
- 数据来自混合分布
- 客户分群（概率视角）

**代码框架**：
```python
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import numpy as np

def gmm_clustering(X, max_components=10):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    bics = []
    aics = []
    
    for k in range(2, max_components + 1):
        gmm = GaussianMixture(n_components=k, random_state=42)
        gmm.fit(X_scaled)
        bics.append(gmm.bic(X_scaled))
        aics.append(gmm.aic(X_scaled))
    
    best_k = np.argmin(bics) + 2
    print(f"BIC最佳聚类数: {best_k}")
    
    gmm = GaussianMixture(n_components=best_k, random_state=42)
    labels = gmm.fit_predict(X_scaled)
    probabilities = gmm.predict_proba(X_scaled)
    
    print(f"轮廓系数: {silhouette_score(X_scaled, labels):.4f}")
    
    return gmm, labels, probabilities
```

---

## 3. 聚类评估指标

### 3.1 内部评估指标

```python
from sklearn.metrics import (silhouette_score, calinski_harabasz_score,
                             davies_bouldin_score)

def clustering_evaluation(X, labels):
    sil = silhouette_score(X, labels)
    ch = calinski_harabasz_score(X, labels)
    db = davies_bouldin_score(X, labels)
    
    print(f"轮廓系数: {sil:.4f} (越高越好, 范围[-1,1])")
    print(f"CH指数: {ch:.4f} (越高越好)")
    print(f"DB指数: {db:.4f} (越低越好)")
    
    return {'silhouette': sil, 'calinski_harabasz': ch, 'davies_bouldin': db}
```

### 3.2 轮廓系数计算

```python
def silhouette_analysis(X, labels):
    from sklearn.metrics import silhouette_samples
    
    sample_silhouette_values = silhouette_samples(X, labels)
    
    for i in range(len(set(labels))):
        cluster_values = sample_silhouette_values[labels == i]
        print(f"簇{i}: 平均轮廓系数 = {cluster_values.mean():.4f}")
    
    overall = sample_silhouette_values.mean()
    print(f"总体平均轮廓系数: {overall:.4f}")
```

---

## 4. 常见陷阱与最佳实践

### 4.1 常见陷阱

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| K值选择不当 | 聚类结果不合理 | 肘部法+轮廓系数+业务判断 |
| 高维数据 | 距离度量失效 | 降维后聚类/子空间聚类 |
| 噪声敏感 | 异常值影响聚类 | DBSCAN/预处理去噪 |
| 未标准化 | 量纲影响距离 | StandardScaler |
| 只看单一指标 | 评估片面 | 多指标综合评估 |

### 4.2 最佳实践

- **数据标准化**：聚类前必须标准化
- **多指标评估**：轮廓系数+CH指数+DB指数
- **可视化验证**：2D/3D散点图展示聚类结果
- **业务解释**：聚类结果要有业务意义
- **参数敏感性**：分析关键参数对结果的影响

---

## 5. 验证清单

- [ ] 数据已标准化
- [ ] 聚类数选择合理（多指标验证）
- [ ] 轮廓系数 > 0.5（良好聚类）
- [ ] 各簇样本数分布合理（无极端不平衡）
- [ ] 聚类结果可视化展示
- [ ] 业务解释合理
- [ ] 噪声点处理（如适用）
- [ ] 与基准方法对比（如适用）
