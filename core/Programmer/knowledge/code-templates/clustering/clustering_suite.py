"""
聚类算法统一接口模板
来源: 高教杯优秀论文
适用问题: 客户分群、异常检测、数据降维
输入: 特征矩阵X
输出: 聚类标签、评估指标、可视化
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Optional, List, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (silhouette_score, calinski_harabasz_score,
                             davies_bouldin_score)
import warnings
warnings.filterwarnings('ignore')


class ClusteringSuite:
    """
    聚类算法统一接口
    
    支持: K-Means、DBSCAN、层次聚类、高斯混合模型
    
    Parameters
    ----------
    X : ndarray or DataFrame
        特征矩阵
    feature_names : list, optional
        特征名称
    random_state : int
        随机种子
    """

    def __init__(self, X, feature_names: Optional[List[str]] = None,
                 random_state: int = 42):
        self.X = np.array(X, dtype=float)
        self.feature_names = feature_names or [f'Feature_{i}' for i in range(self.X.shape[1])]
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)
        self.models = {}
        self.results = {}

    def _evaluate(self, labels: np.ndarray, X_scaled: np.ndarray) -> Dict:
        """计算聚类评估指标"""
        n_clusters = len(set(labels) - {-1})  # 排除噪声点
        if n_clusters < 2:
            return {
                'n_clusters': n_clusters,
                'silhouette': -1,
                'calinski_harabasz': -1,
                'davies_bouldin': float('inf'),
                'noise_ratio': (labels == -1).sum() / len(labels)
            }

        # 排除噪声点后计算指标
        mask = labels != -1
        if mask.sum() < 2:
            return {'n_clusters': n_clusters, 'silhouette': -1,
                    'calinski_harabasz': -1, 'davies_bouldin': float('inf'),
                    'noise_ratio': (labels == -1).sum() / len(labels)}

        return {
            'n_clusters': n_clusters,
            'silhouette': silhouette_score(X_scaled[mask], labels[mask]),
            'calinski_harabasz': calinski_harabasz_score(X_scaled[mask], labels[mask]),
            'davies_bouldin': davies_bouldin_score(X_scaled[mask], labels[mask]),
            'noise_ratio': (labels == -1).sum() / len(labels)
        }

    def fit_kmeans(self, n_clusters: int) -> Dict:
        """K-Means聚类"""
        from sklearn.cluster import KMeans

        model = KMeans(n_clusters=n_clusters, random_state=self.random_state, n_init=10)
        labels = model.fit_predict(self.X_scaled)
        metrics = self._evaluate(labels, self.X_scaled)

        self.models['KMeans'] = model
        self.results['KMeans'] = {'labels': labels, 'metrics': metrics,
                                   'centers': model.cluster_centers_}
        return metrics

    def fit_dbscan(self, eps: float = 0.5, min_samples: int = 5) -> Dict:
        """DBSCAN聚类"""
        from sklearn.cluster import DBSCAN

        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = model.fit_predict(self.X_scaled)
        metrics = self._evaluate(labels, self.X_scaled)

        self.models['DBSCAN'] = model
        self.results['DBSCAN'] = {'labels': labels, 'metrics': metrics}
        return metrics

    def fit_hierarchical(self, n_clusters: int, linkage: str = 'ward') -> Dict:
        """层次聚类"""
        from sklearn.cluster import AgglomerativeClustering

        model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
        labels = model.fit_predict(self.X_scaled)
        metrics = self._evaluate(labels, self.X_scaled)

        self.models['Hierarchical'] = model
        self.results['Hierarchical'] = {'labels': labels, 'metrics': metrics}
        return metrics

    def fit_gmm(self, n_components: int) -> Dict:
        """高斯混合模型"""
        from sklearn.mixture import GaussianMixture

        model = GaussianMixture(n_components=n_components, random_state=self.random_state)
        labels = model.fit_predict(self.X_scaled)
        metrics = self._evaluate(labels, self.X_scaled)

        self.models['GMM'] = model
        self.results['GMM'] = {'labels': labels, 'metrics': metrics,
                                'centers': model.means_}
        return metrics

    def auto_select_k(self, max_k: int = 10, method: str = 'kmeans') -> int:
        """
        肘部法则 + 轮廓系数自动选择最优K
        
        Parameters
        ----------
        max_k : int
            最大聚类数
        method : str
            基础聚类方法
            
        Returns
        -------
        best_k : int
            最优聚类数
        """
        inertias = []
        silhouettes = []
        K_range = range(2, max_k + 1)

        for k in K_range:
            if method == 'kmeans':
                from sklearn.cluster import KMeans
                model = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            else:
                from sklearn.mixture import GaussianMixture
                model = GaussianMixture(n_components=k, random_state=self.random_state)

            labels = model.fit_predict(self.X_scaled)
            if hasattr(model, 'inertia_'):
                inertias.append(model.inertia_)
            else:
                inertias.append(-model.score(self.X_scaled) * len(self.X_scaled))

            silhouettes.append(silhouette_score(self.X_scaled, labels))

        self._elbow_data = {'K': list(K_range), 'inertia': inertias,
                            'silhouette': silhouettes}

        best_k = list(K_range)[np.argmax(silhouettes)]
        return best_k

    def fit_all(self, n_clusters: int) -> pd.DataFrame:
        """训练所有聚类算法"""
        self.fit_kmeans(n_clusters)
        self.fit_hierarchical(n_clusters)
        self.fit_gmm(n_clusters)

        # DBSCAN: 自动估算eps
        from sklearn.neighbors import NearestNeighbors
        nn = NearestNeighbors(n_neighbors=5)
        nn.fit(self.X_scaled)
        distances, _ = nn.kneighbors(self.X_scaled)
        eps = np.percentile(distances[:, -1], 90)
        self.fit_dbscan(eps=eps)

        # 汇总结果
        records = []
        for name, res in self.results.items():
            record = {'Method': name}
            record.update(res['metrics'])
            records.append(record)

        return pd.DataFrame(records)

    def plot_elbow(self, filename: Optional[str] = None):
        """绘制肘部法则图"""
        if not hasattr(self, '_elbow_data'):
            print("请先运行auto_select_k()")
            return

        data = self._elbow_data
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        ax1.plot(data['K'], data['inertia'], 'bo-', linewidth=2)
        ax1.set_xlabel('Number of Clusters (K)')
        ax1.set_ylabel('Inertia')
        ax1.set_title('Elbow Method')
        ax1.grid(True, alpha=0.3)

        ax2.plot(data['K'], data['silhouette'], 'ro-', linewidth=2)
        ax2.set_xlabel('Number of Clusters (K)')
        ax2.set_ylabel('Silhouette Score')
        ax2.set_title('Silhouette Analysis')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def plot_clusters_2d(self, method: str = 'KMeans', feat_x: int = 0,
                         feat_y: int = 1, filename: Optional[str] = None):
        """绘制2D聚类散点图"""
        if method not in self.results:
            print(f"方法 {method} 未训练")
            return

        labels = self.results[method]['labels']
        unique_labels = sorted(set(labels))

        plt.figure(figsize=(10, 8))
        colors = plt.cm.Set2(np.linspace(0, 1, len(unique_labels)))

        for label, color in zip(unique_labels, colors):
            mask = labels == label
            name = f'Cluster {label}' if label != -1 else 'Noise'
            plt.scatter(self.X[mask, feat_x], self.X[mask, feat_y],
                       c=[color], label=name, alpha=0.6, s=50)

        # 绘制聚类中心 (KMeans和GMM)
        if 'centers' in self.results[method]:
            centers = self.scaler.inverse_transform(self.results[method]['centers'])
            plt.scatter(centers[:, feat_x], centers[:, feat_y],
                       c='red', marker='X', s=200, label='Centers',
                       edgecolors='black', linewidths=2)

        plt.xlabel(self.feature_names[feat_x])
        plt.ylabel(self.feature_names[feat_y])
        plt.title(f'{method} Clustering Results')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def plot_comparison(self, filename: Optional[str] = None):
        """绘制各算法评估指标对比"""
        records = []
        for name, res in self.results.items():
            records.append({
                'Method': name,
                'Silhouette': res['metrics']['silhouette'],
                'CH Index': res['metrics']['calinski_harabasz'],
                'DB Index': res['metrics']['davies_bouldin']
            })

        df = pd.DataFrame(records)
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        metrics = ['Silhouette', 'CH Index', 'DB Index']
        colors = ['#2ecc71', '#3498db', '#e74c3c']

        for ax, metric, color in zip(axes, metrics, colors):
            ax.bar(df['Method'], df[metric], color=color, alpha=0.8)
            ax.set_title(metric)
            ax.set_ylabel(metric)
            ax.grid(True, alpha=0.3, axis='y')

        plt.suptitle('Clustering Algorithm Comparison')
        plt.tight_layout()

        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()


def run_example():
    """示例: 使用sklearn合成数据"""
    from sklearn.datasets import make_blobs

    print("=" * 60)
    print("聚类算法统一接口示例")
    print("=" * 60)

    # 生成合成数据
    np.random.seed(42)
    X, y_true = make_blobs(n_samples=300, centers=4, cluster_std=1.0,
                           random_state=42)
    feature_names = ['Feature_1', 'Feature_2']

    print(f"\n数据集: 合成数据")
    print(f"样本数: {X.shape[0]}, 特征数: {X.shape[1]}")
    print(f"真实簇数: {len(np.unique(y_true))}")

    # 创建聚类套件
    suite = ClusteringSuite(X, feature_names, random_state=42)

    # 自动选择K
    best_k = suite.auto_select_k(max_k=8)
    print(f"\n自动选择最优K: {best_k}")

    # 训练所有算法
    print("\n--- 训练所有聚类算法 ---")
    results_df = suite.fit_all(n_clusters=best_k)
    print("\n聚类结果对比:")
    print(results_df.to_string(index=False))

    # 详细分析KMeans结果
    kmeans_res = suite.results['KMeans']
    print(f"\n--- KMeans详细结果 ---")
    print(f"簇大小: {np.bincount(kmeans_res['labels'])}")

    centers = suite.scaler.inverse_transform(kmeans_res['centers'])
    centers_df = pd.DataFrame(centers, columns=feature_names)
    print(f"\n聚类中心 (原始尺度):")
    print(centers_df)

    # 绘图
    suite.plot_elbow('figures/clustering_elbow.png')
    suite.plot_clusters_2d('KMeans', filename='figures/clustering_kmeans.png')
    suite.plot_clusters_2d('GMM', filename='figures/clustering_gmm.png')
    suite.plot_comparison('figures/clustering_comparison.png')
    print("\n图片已保存到 figures/ 目录")


if __name__ == "__main__":
    run_example()
