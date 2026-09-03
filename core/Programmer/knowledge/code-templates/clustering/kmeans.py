"""
K-Means聚类模板
来源: 高教杯优秀论文 (C008, C052, C101)
适用问题: 客户分群、数据降维、无监督学习
输入: 特征矩阵X
输出: 聚类标签、聚类中心、评估指标
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class KMeansClustering:
    """
    K-Means聚类模板
    
    Parameters
    ----------
    X : ndarray or DataFrame
        特征矩阵
    feature_names : list, optional
        特征名称
    random_state : int, default=42
        随机种子
    """
    
    def __init__(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None,
        random_state: int = 42
    ):
        self.X = np.array(X)
        self.feature_names = feature_names or [f'Feature_{i+1}' for i in range(self.X.shape[1])]
        self.random_state = random_state
        
        self.scaler = None
        self.X_scaled = None
        self.model = None
        self.labels = None
        self.centers = None
        self.inertias = []
        self.silhouette_scores = []
    
    def preprocess(self) -> np.ndarray:
        """数据标准化（重要！）"""
        from sklearn.preprocessing import StandardScaler
        
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)
        
        return self.X_scaled
    
    def find_optimal_k(self, max_k: int = 10) -> int:
        """
        使用肘部法则和轮廓系数选择最佳聚类数
        
        Parameters
        ----------
        max_k : int
            最大聚类数
            
        Returns
        -------
        best_k : int
            最佳聚类数
        """
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        
        if self.X_scaled is None:
            self.preprocess()
        
        self.inertias = []
        self.silhouette_scores = []
        K_range = range(2, max_k + 1)
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            kmeans.fit(self.X_scaled)
            
            self.inertias.append(kmeans.inertia_)
            self.silhouette_scores.append(silhouette_score(self.X_scaled, kmeans.labels_))
        
        # 选择最佳K（轮廓系数最大）
        best_k = list(K_range)[np.argmax(self.silhouette_scores)]
        
        return best_k
    
    def fit(self, n_clusters: int) -> dict:
        """
        拟合K-Means模型
        
        Parameters
        ----------
        n_clusters : int
            聚类数
            
        Returns
        -------
        results : dict
            聚类结果
        """
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
        
        if self.X_scaled is None:
            self.preprocess()
        
        # 训练模型
        self.model = KMeans(
            n_clusters=n_clusters, 
            random_state=self.random_state, 
            n_init=10
        )
        self.labels = self.model.fit_predict(self.X_scaled)
        self.centers = self.model.cluster_centers_
        
        # 计算评估指标
        results = {
            'labels': self.labels,
            'centers': self.centers,
            'inertia': self.model.inertia_,
            'silhouette_score': silhouette_score(self.X_scaled, self.labels),
            'calinski_harabasz_score': calinski_harabasz_score(self.X_scaled, self.labels),
            'davies_bouldin_score': davies_bouldin_score(self.X_scaled, self.labels),
            'cluster_sizes': np.bincount(self.labels)
        }
        
        return results
    
    def analyze_clusters(self) -> pd.DataFrame:
        """分析各聚类的特征"""
        if self.labels is None:
            print("请先运行fit()方法")
            return None
        
        # 创建包含聚类标签的DataFrame
        df = pd.DataFrame(self.X, columns=self.feature_names)
        df['Cluster'] = self.labels
        
        # 计算各聚类的统计量
        cluster_stats = df.groupby('Cluster').agg(['mean', 'std', 'median'])
        
        # 计算各聚类的中心（原始尺度）
        centers_original = self.scaler.inverse_transform(self.centers)
        centers_df = pd.DataFrame(centers_original, columns=self.feature_names)
        centers_df.index.name = 'Cluster'
        
        return centers_df
    
    def plot_elbow_method(self):
        """绘制肘部法则图"""
        K_range = range(2, len(self.inertias) + 2)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 肘部法则
        ax1.plot(K_range, self.inertias, 'bo-', linewidth=2, markersize=8)
        ax1.set_xlabel('Number of Clusters (K)')
        ax1.set_ylabel('Inertia')
        ax1.set_title('Elbow Method')
        ax1.grid(True, alpha=0.3)
        
        # 轮廓系数
        ax2.plot(K_range, self.silhouette_scores, 'ro-', linewidth=2, markersize=8)
        ax2.set_xlabel('Number of Clusters (K)')
        ax2.set_ylabel('Silhouette Score')
        ax2.set_title('Silhouette Analysis')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_clusters_2d(self, feature_idx_x: int = 0, feature_idx_y: int = 1):
        """绘制2D聚类图"""
        if self.labels is None:
            print("请先运行fit()方法")
            return
        
        plt.figure(figsize=(10, 8))
        
        # 绘制各聚类的点
        colors = plt.cm.Set2(np.linspace(0, 1, len(np.unique(self.labels))))
        
        for cluster_id in np.unique(self.labels):
            mask = self.labels == cluster_id
            plt.scatter(
                self.X[mask, feature_idx_x], 
                self.X[mask, feature_idx_y],
                c=[colors[cluster_id]], 
                label=f'Cluster {cluster_id}',
                alpha=0.6,
                s=50
            )
        
        # 绘制聚类中心
        centers_original = self.scaler.inverse_transform(self.centers)
        plt.scatter(
            centers_original[:, feature_idx_x], 
            centers_original[:, feature_idx_y],
            c='red', 
            marker='X', 
            s=200, 
            label='Centers',
            edgecolors='black',
            linewidths=2
        )
        
        plt.xlabel(self.feature_names[feature_idx_x])
        plt.ylabel(self.feature_names[feature_idx_y])
        plt.title('K-Means Clustering Results')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return plt.gcf()
    
    def plot_clusters_radar(self, cluster_ids: Optional[List[int]] = None):
        """绘制雷达图展示各聚类特征"""
        if self.labels is None:
            print("请先运行fit()方法")
            return
        
        centers_original = self.scaler.inverse_transform(self.centers)
        centers_df = pd.DataFrame(centers_original, columns=self.feature_names)
        
        if cluster_ids is None:
            cluster_ids = list(range(len(centers_df)))
        
        # 标准化到0-1范围（用于雷达图）
        centers_normalized = (centers_df - centers_df.min()) / (centers_df.max() - centers_df.min())
        
        # 雷达图
        angles = np.linspace(0, 2 * np.pi, len(self.feature_names), endpoint=False).tolist()
        angles += angles[:1]  # 闭合
        
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
        
        colors = plt.cm.Set2(np.linspace(0, 1, len(cluster_ids)))
        
        for idx, cluster_id in enumerate(cluster_ids):
            values = centers_normalized.iloc[cluster_id].values.tolist()
            values += values[:1]  # 闭合
            
            ax.plot(angles, values, 'o-', linewidth=2, label=f'Cluster {cluster_id}', 
                   color=colors[idx])
            ax.fill(angles, values, alpha=0.1, color=colors[idx])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(self.feature_names)
        ax.set_title('Cluster Profiles (Normalized)', size=14, y=1.1)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        plt.tight_layout()
        return fig
    
    def get_cluster_profiles(self) -> pd.DataFrame:
        """获取聚类画像"""
        if self.labels is None:
            print("请先运行fit()方法")
            return None
        
        df = pd.DataFrame(self.X, columns=self.feature_names)
        df['Cluster'] = self.labels
        
        # 计算各聚类的统计量
        profiles = []
        for cluster_id in sorted(df['Cluster'].unique()):
            cluster_data = df[df['Cluster'] == cluster_id]
            profile = {
                'Cluster': cluster_id,
                'Size': len(cluster_data),
                'Percentage': len(cluster_data) / len(df) * 100
            }
            
            for feature in self.feature_names:
                profile[f'{feature}_mean'] = cluster_data[feature].mean()
                profile[f'{feature}_std'] = cluster_data[feature].std()
            
            profiles.append(profile)
        
        return pd.DataFrame(profiles)


def run_example():
    """
    示例：客户分群分析
    
    使用RFM指标进行客户分群
    """
    # 生成模拟客户数据
    np.random.seed(42)
    n_customers = 200
    
    # 模拟RFM数据
    data = {
        'Recency': np.random.exponential(30, n_customers),  # 最近购买距今天数
        'Frequency': np.random.poisson(5, n_customers) + 1,  # 购买频率
        'Monetary': np.random.lognormal(6, 1, n_customers)  # 消费金额
    }
    
    df = pd.DataFrame(data)
    feature_names = ['Recency', 'Frequency', 'Monetary']
    
    print("=" * 60)
    print("K-Means聚类示例 - 客户分群分析")
    print("=" * 60)
    
    # 创建聚类对象
    kmeans = KMeansClustering(df[feature_names].values, feature_names)
    
    # 预处理
    kmeans.preprocess()
    
    # 寻找最佳K
    best_k = kmeans.find_optimal_k(max_k=8)
    print(f"\n最佳聚类数: {best_k}")
    
    # 拟合模型
    results = kmeans.fit(n_clusters=best_k)
    
    print(f"\n聚类评估指标:")
    print(f"  轮廓系数: {results['silhouette_score']:.4f}")
    print(f"  Calinski-Harabasz指数: {results['calinski_harabasz_score']:.4f}")
    print(f"  Davies-Bouldin指数: {results['davies_bouldin_score']:.4f}")
    print(f"  聚类大小: {results['cluster_sizes']}")
    
    # 分析聚类特征
    centers_df = kmeans.analyze_clusters()
    print(f"\n聚类中心（原始尺度）:")
    print(centers_df)
    
    # 获取聚类画像
    profiles = kmeans.get_cluster_profiles()
    print(f"\n聚类画像:")
    print(profiles[['Cluster', 'Size', 'Percentage'] + 
                  [f'{f}_mean' for f in feature_names]])
    
    # 绘制肘部法则图
    fig = kmeans.plot_elbow_method()
    plt.savefig('figures/kmeans_elbow.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # 绘制2D聚类图
    fig = kmeans.plot_clusters_2d(feature_idx_x=1, feature_idx_y=2)  # Frequency vs Monetary
    plt.savefig('figures/kmeans_clusters_2d.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # 绘制雷达图
    fig = kmeans.plot_clusters_radar()
    plt.savefig('figures/kmeans_radar.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
