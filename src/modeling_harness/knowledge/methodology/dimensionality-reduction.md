# 降维与特征提取领域知识

## 一、核心概念

### 1.1 降维定义
- **定义**: 将高维数据投影到低维空间
- **目的**: 减少计算复杂度、去除噪声、可视化
- **方法**: 线性降维、非线性降维

### 1.2 常用方法
| 方法 | 类型 | 特点 |
|------|------|------|
| PCA | 线性 | 方差最大化 |
| LDA | 线性 | 类别可分性 |
| t-SNE | 非线性 | 保持局部结构 |
| UMAP | 非线性 | 保持全局结构 |

### 1.3 应用场景
- 数据可视化
- 特征提取
- 去噪
- 加速计算

---

## 二、主成分分析（PCA）

### 2.1 PCA原理
```python
import numpy as np
from sklearn.decomposition import PCA

def pca_manual(X, n_components):
    """
    手动实现PCA
    """
    # 中心化
    mean = np.mean(X, axis=0)
    X_centered = X - mean
    
    # 计算协方差矩阵
    cov_matrix = np.cov(X_centered.T)
    
    # 特征值分解
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    
    # 选择前k个特征向量
    sorted_idx = np.argsort(eigenvalues)[::-1]
    top_k = eigenvectors[:, sorted_idx[:n_components]]
    
    # 投影
    X_pca = X_centered @ top_k
    
    return X_pca, eigenvalues, eigenvectors
```

### 2.2 方差解释率
```python
def variance_explained(eigenvalues, n_components):
    """
    计算方差解释率
    """
    total_variance = np.sum(eigenvalues)
    explained_variance = np.sum(eigenvalues[:n_components])
    
    return explained_variance / total_variance
```

### 2.3 选择主成分数量
```python
def select_n_components(X, variance_threshold=0.95):
    """
    选择主成分数量
    """
    pca = PCA()
    pca.fit(X)
    
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
    n_components = np.argmax(cumulative_variance >= variance_threshold) + 1
    
    return n_components
```

---

## 三、线性判别分析（LDA）

### 3.1 LDA原理
```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

def lda_manual(X, y, n_components):
    """
    手动实现LDA
    """
    classes = np.unique(y)
    n_classes = len(classes)
    
    # 计算类内散度矩阵
    S_W = np.zeros((X.shape[1], X.shape[1]))
    for c in classes:
        X_c = X[y == c]
        mean_c = np.mean(X_c, axis=0)
        S_W += np.cov(X_c.T)
    
    # 计算类间散度矩阵
    S_B = np.zeros((X.shape[1], X.shape[1]))
    mean_total = np.mean(X, axis=0)
    for c in classes:
        X_c = X[y == c]
        mean_c = np.mean(X_c, axis=0)
        n_c = len(X_c)
        S_B += n_c * np.outer(mean_c - mean_total, mean_c - mean_total)
    
    # 广义特征值分解
    eigenvalues, eigenvectors = np.linalg.eig(np.linalg.inv(S_W) @ S_B)
    
    # 选择前k个特征向量
    sorted_idx = np.argsort(eigenvalues)[::-1]
    top_k = eigenvectors[:, sorted_idx[:n_components]].real
    
    # 投影
    X_lda = X @ top_k
    
    return X_lda
```

---

## 四、t-SNE降维

### 4.1 t-SNE原理
```python
from sklearn.manifold import TSNE

def tsne降维(X, n_components=2, perplexity=30):
    """
    t-SNE降维
    """
    tsne = TSNE(n_components=n_components, perplexity=perplexity)
    X_tsne = tsne.fit_transform(X)
    
    return X_tsne
```

### 4.2 参数选择
```python
def tsne_parameter_selection(X, perplexities=[5, 10, 30, 50]):
    """
    t-SNE参数选择
    """
    results = {}
    
    for perp in perplexities:
        tsne = TSNE(n_components=2, perplexity=perp)
        X_tsne = tsne.fit_transform(X)
        results[perp] = X_tsne
    
    return results
```

---

## 五、UMAP降维

### 5.1 UMAP原理
```python
import umap

def umap降维(X, n_components=2, n_neighbors=15):
    """
    UMAP降维
    """
    reducer = umap.UMAP(n_components=n_components, n_neighbors=n_neighbors)
    X_umap = reducer.fit_transform(X)
    
    return X_umap
```

---

## 六、论文写作要点

### 6.1 问题分析框架
1. **数据理解**: 维度、特征、分布
2. **方法选择**: PCA/LDA/t-SNE/UMAP
3. **参数优化**: 主成分数量、困惑度
4. **结果分析**: 方差解释、可视化
5. **特征重要性**: 载荷分析
6. **灵敏度分析**: 参数影响

### 6.2 图表规范
- **碎石图**: 特征值分布
- **散点图**: 降维结果
- **载荷图**: 特征贡献
- **方差解释图**: 累积方差

### 6.3 LaTeX代码
```latex
\begin{equation}
Z = XW
\label{eq:pca}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{pca_scatter.pdf}
\caption{PCA降维结果}
\label{fig:pca}
\end{figure}
```

---

## 七、参考文献

1. Jolliffe I T. Principal Component Analysis. Springer, 2002.
2. van der Maaten L. Visualizing Data using t-SNE. JMLR, 2008.
3. McInnes L. UMAP: Uniform Manifold Approximation. 2018.
4. 李航. 统计学习方法. 清华大学出版社, 2012.
