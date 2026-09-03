# Cookbook: 聚类/无监督学习类模型

> 适用场景：样本分组、模式发现、异常检测、降维可视化、数据分层。CUMCM C题、数据挖掘题高频。

---

## 1. 分区聚类

| 算法 | 原理 | 适用场景 | 关键参数 | 代码模板 |
|------|------|----------|----------|----------|
| **K-Means** | 最小化簇内平方和 (SSE)、Lloyd 算法 | 球状簇、大规模、K 已知、特征数值型 | `n_clusters`, `n_init`(10+), `max_iter`(300), `k-means++` 初始化 | `kmeans_template.py` |
| **K-Medoids (PAM/CLARA/CLARANS)** | 最小化到类中心(实测点)距离和 | 非欧氏距离、异常值鲁棒、类别特征 | `n_clusters`, `metric`, `init` | `kmedoids_template.py` |
| **K-Modes / K-Prototypes** | 类别/混合数据 | 纯类别/数值+类别混合 | `n_clusters`, `categorical`, `gamma` | `kmodes_template.py` |
| **MiniBatch K-Means** | 增量/流式、大规模 | 百万级样本、内存受限 | `batch_size`(1024), `max_no_improvement` | `minibatch_kmeans.py` |

**K 选择**：肘部法则、轮廓系数、Gap Statistic、CH 指数、DB 指数、稳定性选择

**验证清单**：✅ SSE 收敛 ✅ 轮廓系数 >0.5(较好) ✅ 簇大小均衡/符合业务 ✅ 多次运行稳定 (ARI>0.8) ✅ 簇中心可解释

---

## 2. 层次聚类

| 算法 | 链接准则 | 适用场景 | 代码模板 |
|------|----------|----------|----------|
| **凝聚层次 (AHC)** | Ward(方差最小)/Complete/Complete/Average/Single | 树形结构可视化、无需预设 K、中小规模 | `hierarchical_ward.py`, `hierarchical_linkage.py` |
| **可分层次** | 自顶向下分裂 | 大规模、自上而下 | `hierarchical_divisive.py` |

**截断获取平坦聚类**：`distance_threshold` / `n_clusters` / `fcluster` (inconsistent/maxclust/monocrit)

**树状图绘制**：`scipy.cluster.hierarchy.dendrogram` + 截断线可视化

---

## 3. 密度聚类

| 算法 | 原理 | 适用场景 | 关键参数 | 代码模板 |
|------|------|----------|----------|----------|
| **DBSCAN** | ε-邻域密度 ≥ MinPts → 核心点、边界点、噪声 | 任意形状、噪声鲁棒、发现噪声、无需 K | `eps`, `min_samples`(≥dim+1), `metric` | `dbscan_template.py` |
| **HDBSCAN** | 密度层次、稳定性选择、无需 ε | 变密度、自动 K、层次结构 | `min_cluster_size`, `min_samples`, `cluster_selection_method`(eom/leaf) | `hdbscan_template.py` |
| **OPTICS** | 可达距离排序、提取簇序 | 变密度、交互式探索 | `min_samples`, `xi`, `min_cluster_size` | `optics_template.py` |
| **DENCLUE** | 核密度估计、梯度上升、吸引子 | 高维、任意形状、平滑密度 | `sigma`, `xi`, `min_density` | `denclue_template.py` |

**eps 选择**：K-距离图 (K=MinPts) 拐点

---

## 4. 基于模型 / 概率聚类

| 算法 | 原理 | 适用场景 | 代码模板 |
|------|------|----------|----------|
| **高斯混合模型 (GMM)** | EM 算法、多元高斯混合、软分配 | 椭球簇、重叠、概率输出、模型选择 | `gmm_template.py` |
| **贝叶斯 GMM (DP-GMM/VB-GMM)** | 狄利克雷过程/变分贝叶斯、非参数 K | K 未知、自动模型选择 | `dp_gmm_template.py` |
| **隐马尔可夫模型 (HMM) 聚类** | 序列聚类、状态转移 | 时间序列分组、行为模式 | `hmm_clustering.py` |

**模型选择**：BIC/AIC/ICL、交叉验证对数似然、稳定性

---

## 5. 谱聚类 / 图聚类

| 算法 | 原理 | 适用场景 | 代码模板 |
|------|------|----------|----------|
| **谱聚类 (Ncut/RatioCut)** | 拉普拉斯特征向量 + K-Means | 非凸簇、流形、图划分 | `spectral_ncut.py` |
| **Louvain/Leiden (模块度优化)** | 贪心模块度优化、层次/非层次 | 大规模图、社区发现 | `community_louvain.py`, `community_leiden.py` |
| **Infomap** | 信息流压缩、随机游走编码 | 有向/加权、层次社区 | `community_infomap.py` |
| **标签传播 (LPA)** | 节点采纳邻居主流标签 | 快速、近线性、大图 | `community_lpa.py` |
| **随机块模型 (SBM/DC-SBM)** | 生成模型、变分/MCMC 推断 | 统计显著、重叠/分层/度校正 | `sbm_template.py` |

---

## 6. 基于网格 / 子空间 / 投影聚类

| 算法 | 原理 | 适用场景 | 代码模板 |
|------|------|----------|----------|
| **STING / CLIQUE / WaveCluster** | 网格划分、密度阈值、小波变换 | 高维、大规模、近似线性 | `grid_clustering.py` |
| **子空间聚类 (PROCLUS/CLIQUE/SUBCLU/火花)** | 寻找低维子空间中的簇 | 高维稀疏、不同簇不同相关维度 | `subspace_clustering.py` |
| **投影聚类 (PCA+K-Means / t-SNE/UMAP+K-Means)** | 降维后聚类 | 可视化驱动、非线性流形 | `projection_clustering.py` |

---

## 7. 聚类评价指标 (无监督/外部/内部/相对)

| 类别 | 指标 | 适用 | 代码模板 |
|------|------|------|----------|
| **内部 (无真标签)** | 轮廓系数、CH指数、DB指数、Dunn指数、I指数、C指数 | 模型选择、K选择 | `clustering_internal.py` |
| **外部 (有真标签)** | ARI、NMI、AMI、Fowlkes-Mallows、Jaccard、F1、纯度 | 基准测试、对比 | `clustering_external.py` |
| **相对/稳定性** | Bootstrap/Jaccard稳定性、共现矩阵、共识聚类 | 结果可靠性、K选择 | `clustering_stability.py` |
| **可视化** | t-SNE/UMAP/PCA/等值线/平行坐标/树状图 | 结果展示、解释 | `clustering_viz.py` |

---

## 8. 异常检测 / 新奇性检测 (聚类视角)

| 方法 | 原理 | 代码模板 |
|------|------|----------|
| **基于距离 (KNN/LOF/LOCI/COF/INFLO)** | 局部密度偏差 | `anomaly_lof.py`, `anomaly_knn.py` |
| **基于密度 (DBSCAN噪声/孤立森林/扩展孤立森林)** | 稀疏区域/路径长度 | `anomaly_isolation_forest.py` |
| **基于聚类 (小簇/远离中心/低概率)** | GMM低概率/小簇标记异常 | `anomaly_cluster_based.py` |
| **基于重构 (PCA/自编码器/字典学习重构误差)** | 正常模式重构好、异常重构差 | `anomaly_reconstruction.py` |
| **单类 SVM / 深度 SVDD** | 单类边界学习 | `anomaly_ocsvm.py`, `anomaly_svdd.py` |

---

## 9. 代码模板目录映射

```
core/Programmer/knowledge/code-templates/clustering/
├── kmeans_template.py
├── kmedoids_template.py
├── kmodes_template.py
├── minibatch_kmeans.py
├── hierarchical_ward.py
├── hierarchical_linkage.py
├── hierarchical_divisive.py
├── dbscan_template.py
├── hdbscan_template.py
├── optics_template.py
├── denclue_template.py
├── gmm_template.py
├── dp_gmm_template.py
├── hmm_clustering.py
├── spectral_ncut.py
├── community_louvain.py
├── community_leiden.py
├── community_infomap.py
├── community_lpa.py
├── community_cpm.py
├── sbm_template.py
├── grid_clustering.py
├── subspace_clustering.py
├── projection_clustering.py
├── clustering_internal.py
├── clustering_external.py
├── clustering_stability.py
├── clustering_viz.py
├── anomaly_lof.py
├── anomaly_knn.py
├── anomaly_isolation_forest.py
├── anomaly_cluster_based.py
├── anomaly_reconstruction.py
├── anomaly_ocsvm.py
└── anomaly_svdd.py
```

---

## 10. 选型决策树 (聚类类)

```
数据特征？
├─ 低维(≤10)、数值、球状簇、K已知 → K-Means/GMM → 首选
├─ 低维、任意形状、有噪声、K未知 → DBSCAN/HDBSCAN → 首选
├─ 高维(>50)、稀疏、不同簇不同维度 → 子空间聚类/投影聚类 → 首选
├─ 类别/混合数据 → K-Modes/K-Prototypes/Gower距离+层次 → 首选
├─ 序列/时间序列 → DTW距离+K-Means/层次/HMM聚类 → 首选
├─ 图/网络结构 → Louvain/Leiden/Infomap/SBM/谱聚类 → 首选
├─ 大规模(>10^5) → MiniBatch K-Means/LPA/网格/采样 → 首选
├─ 需层次/树状图 → 层次聚类(HDBSCAN/凝聚) → 首选
├─ 异常检测为主 → 孤立森林/LOF/重构误差 → 首选
└─ K未知、需自动选择 → HDBSCAN/DP-GMM/Gap Statistic/稳定性 → 首选
```

**铁律**：
- 聚类 **必须多指标评价** (内部+稳定性+可视化+业务可解释)
- K-Means **必须多次初始化 (n_init≥10)** 并报告最优/均值 SSE
- DBSCAN **必须给出 K-距离图选 eps 依据**
- 结果 **必须可视化** (t-SNE/UMAP 彩色散点 + 树状图/轮廓图)
- 簇 **必须给出画像** (均值/中位数/分布/特征重要性/业务标签)

---

## 11. 竞赛实战提示

| 竞赛 | 题型 | 推荐首选 | 避坑指南 |
|------|------|----------|----------|
| CUMCM C | 数据分层/用户画像 | K-Means/GMM/HDBSCAN + 画像 | 业务可解释性优先、特征工程关键 |
| 电工杯 | 设备状态/故障模式 | HMM/时序聚类/异常检测 | 标签少用半监督/异常检测 |
| 通用 | 探索性分析 | 多算法对比 + 共识聚类 | 稳定性选择、可视化贯穿始终 |

---

*版本：1.0 | 更新：2026-09-01 | 维护：Modeler 手*