# Cookbook: 网络/图论类模型

> 适用场景：关系/连接/流动/传播/优化在图结构上。CUMCM D题、MCM B题、网络科学题高频。

---

## 1. 图基础与表示

| 表示 | 适用场景 | 代码模板 |
|------|----------|----------|
| **邻接矩阵** | 稠密图、矩阵运算、谱分析 | `graph_adjacency.py` |
| **邻接表** | 稀疏图、遍历/搜索、内存高效 | `graph_adjlist.py` |
| **边列表** | 边属性丰富、流算法、外部存储 | `graph_edgelist.py` |
| **NetworkX Graph/DiGraph/MultiGraph** | 通用分析、算法库丰富 | `graph_nx_basics.py` |
| **PyTorch Geometric / DGL** | 图神经网络、深度学习 | `graph_pyg_basics.py` |

---

## 2. 经典图算法

| 算法 | 问题 | 复杂度 | 代码模板 |
|------|------|--------|----------|
| **最短路径** | Dijkstra(非负权)、Bellman-Ford(负权)、Floyd-Warshall(全对)、A*(启发式) | O(E log V) / O(VE) / O(V³) | `shortest_path.py` |
| **最小生成树** | Prim / Kruskal / Boruvka | O(E log V) | `mst_template.py` |
| **最大流/最小割** | Edmonds-Karp / Dinic / Push-Relabel / ISAP | O(VE²) / O(V²E) / O(V³) | `maxflow_template.py` |
| **最小费用流** | 连续松弛 / 网络单纯形 / SSP | O(F·E log V) | `mincost_flow.py` |
| **二分匹配/最大匹配** | Hopcroft-Karp / 匈牙利 / Blossom(一般图) | O(E√V) / O(V³) | `matching_template.py` |
| **拓扑排序** | DAG 依赖/调度 | O(V+E) | `toposort_template.py` |
| **强连通分量** | Kosaraju / Tarjan | O(V+E) | `scc_template.py` |

---

## 3. 中心性与结构指标

| 指标 | 含义 | 适用场景 | 代码模板 |
|------|------|----------|----------|
| **度中心性** | 直接连接数 | 影响力/枢纽识别 | `centrality_degree.py` |
| **介数中心性** | 最短路径通过比例 | 桥梁/控制点/信息流控制 | `centrality_betweenness.py` |
| **接近中心性** | 到其他节点平均距离倒数 | 传播速度/可达性 | `centrality_closeness.py` |
| **特征向量/PageRank** | 邻居重要性加权 | 网页排名/关键节点/影响力传播 | `centrality_pagerank.py` |
| **Katz/Alpha 中心性** | 路径衰减加权 | 带衰减的影响力 | `centrality_katz.py` |
| **聚类系数** | 邻居间连接紧密度 | 社团/小世界/结构洞 | `clustering_coeff.py` |
| **K-core/K-truss** | 核心分解/稠密子图 | 核心团体/鲁棒性 | `kcore_template.py` |

---

## 4. 社区发现 / 聚类

| 算法 | 原理 | 适用场景 | 代码模板 |
|------|------|----------|----------|
| **Louvain/Leiden** | 模块度优化、层次/非层次 | 大规模、无需预设 K | `community_louvain.py` |
| **标签传播 (LPA)** | 节点采纳邻居主流标签 | 快速、近线性、无监督 | `community_lpa.py` |
| **Infomap** | 信息流压缩、随机游走 | 有向/加权、层次社区 | `community_infomap.py` |
| **谱聚类** | 拉普拉斯特征向量 + K-Means | 小图、全局最优 | `community_spectral.py` |
| **Clique Percolation (CPM)** | k-团重叠 | 重叠社区 | `community_cpm.py` |
| **随机块模型 (SBM)** | 生成模型、统计推断 | 模型选择、重叠/分层 | `community_sbm.py` |

**评价指标**：模块度 Q、NMI/ARI (有真标签)、导电率、分离度

---

## 5. 网络动力学 / 传播模型

| 模型 | 方程/规则 | 适用场景 | 代码模板 |
|------|-----------|----------|----------|
| **SIR/SIS/SEIR/SEIRS** | 微分方程/随机仿真 | 流行病/谣言/信息传播 | `dynamics_sir.py` |
| **独立级联 (IC) / 线性阈值 (LT)** | 离散步、概率/阈值激活 | 影响力最大化/病毒营销 | `dynamics_ic_lt.py` |
| **基于代理 (ABM)** | 个体规则、异质网络 | 复杂行为/决策/适应 | `dynamics_abm.py` (Mesa) |
| **同步/振子 (Kuramoto/Winfree)** | 相位耦合 ODE | 神经/功率网格/生物节律 | `dynamics_kuramoto.py` |
| **博弈动力学** | 复制子方程/最佳响应 | 合作/背叛演化 | `dynamics_game.py` |

**关键参数**：基本再生数 R₀、传播阈值、免疫阈值、临界转移点

---

## 6. 影响力最大化

| 问题 | 算法 | 近似保证 | 代码模板 |
|------|------|----------|----------|
| **IC/LT 模型下 Top-k 种子节点** | 贪心 + 惰性评估 (CELF) | (1-1/e) 最优 | `influence_maximization.py` |
| **可扩展近似** | RIS/RRR/SSA/IMM | (1-1/e-ε) | `influence_scalable.py` |
| **多目标/预算约束** | Pareto 贪心/NSGA-II | 启发式 | `influence_multiobj.py` |

---

## 7. 网络鲁棒性 / 脆弱性

| 分析 | 指标 | 代码模板 |
|------|------|----------|
| **节点/边攻击** | 巨连通分量相对大小、效率、直径、聚类系数变化 | `robustness_attack.py` |
| **级联失效** | 负载-容量模型、流量重分配、阈值失效 | `robustness_cascade.py` |
| **关键基础设施** | 介数/度/PageRank 攻击 vs 随机攻击 | `robustness_critical.py` |
| **恢复策略** | 增边/重连/备份/隔离 | `robustness_recovery.py` |

---

## 8. 图神经网络 (GNN)

| 模型 | 消息传递 | 适用任务 | 代码模板 |
|------|----------|----------|----------|
| **GCN** | 归一化邻接聚合 | 节点分类/链接预测 | `gnn_gcn.py` (PyG) |
| **GraphSAGE** | 采样邻居聚合 | 大规模归纳式 | `gnn_sage.py` |
| **GAT** | 注意力加权聚合 | 异质重要性 | `gnn_gat.py` |
| **GIN** | 和聚合 + MLP | 图同构/图分类 | `gnn_gin.py` |
| **Graph Transformer** | 全局注意力 | 长程依赖/大图 | `gnn_transformer.py` |
| **时序 GNN (TGN/T-GNN)** | 时间编码 + 记忆 | 动态图/链接预测 | `gnn_temporal.py` |

**任务**：节点分类、链接预测、图分类、图生成、预训练/微调

---

## 9. 空间/几何图

| 类型 | 构建规则 | 代码模板 |
|------|----------|----------|
| **K近邻图 (KNN)** | 距离最近 k 个 | `spatial_knn.py` |
| **半径图 (Radius)** | 距离 < r | `spatial_radius.py` |
| **Delaunay 三角剖分 / Voronoi** | 空间分割、最近邻 | `spatial_delaunay.py` (SciPy/CGAL) |
| **Gabriel / Relative Neighborhood** | 空间邻近性判据 | `spatial_gabriel.py` |

---

## 10. 代码模板目录映射

```
core/Programmer/knowledge/code-templates/network/
├── graph_adjacency.py
├── graph_adjlist.py
├── graph_edgelist.py
├── graph_nx_basics.py
├── graph_pyg_basics.py
├── shortest_path.py
├── mst_template.py
├── maxflow_template.py
├── mincost_flow.py
├── matching_template.py
├── toposort_template.py
├── scc_template.py
├── centrality_degree.py
├── centrality_betweenness.py
├── centrality_closeness.py
├── centrality_pagerank.py
├── centrality_katz.py
├── clustering_coeff.py
├── kcore_template.py
├── community_louvain.py
├── community_lpa.py
├── community_infomap.py
├── community_spectral.py
├── community_cpm.py
├── community_sbm.py
├── dynamics_sir.py
├── dynamics_ic_lt.py
├── dynamics_abm.py
├── dynamics_kuramoto.py
├── dynamics_game.py
├── influence_maximization.py
├── influence_scalable.py
├── influence_multiobj.py
├── robustness_attack.py
├── robustness_cascade.py
├── robustness_critical.py
├── robustness_recovery.py
├── gnn_gcn.py
├── gnn_sage.py
├── gnn_gat.py
├── gnn_gin.py
├── gnn_transformer.py
├── gnn_temporal.py
├── spatial_knn.py
├── spatial_radius.py
├── spatial_delaunay.py
└── spatial_gabriel.py
```

---

## 11. 选型决策树 (网络类)

```
问题本质？
├─ 路径/流/匹配/调度 → 经典图算法 (最短路/最大流/匹配/拓扑排序) → 首选
├─ 关键节点/影响力识别 → 中心性 (PageRank/介数/特征向量) → 首选
├─ 社团/模块/分组 → 社区发现 (Louvain/Leiden/Infomap/SBM) → 首选
├─ 传播/扩散/流行病 → SIR/IC/LT/ABM/Kuramoto → 按离散/连续/个体选
├─ 种子选择/影响力最大化 → 贪心(CELF)/RIS/IMM → 首选
├─ 鲁棒性/脆弱性/级联 → 攻击仿真/负载容量模型 → 首选
├─ 节点/链接/图预测 → GNN (GCN/SAGE/GAT/GIN/Transformer) → 首选
├─ 空间/几何约束 → KNN/Radius/Delaunay/Gabriel → 首选
└─ 多层/时序/异质网络 → 多层网络/时序GNN/异质GNN → 进阶
```

**铁律**：
- 网络构建 **必须明确节点/边定义、有向/无向、权重含义**
- 算法选择 **必须给出复杂度分析**，大图 (V>10^5) 必用近似/采样/分布式
- 传播模型 **必须给出 R₀/阈值分析**，并做参数敏感性
- 社区发现 **必须多算法交叉验证** (模块度/NMI/可解释性)
- GNN **必须做归纳式测试** (未见节点/图) 并报告推理时间

---

## 12. 竞赛实战提示

| 竞赛 | 题型 | 推荐首选 | 避坑指南 |
|------|------|----------|----------|
| CUMCM D | 运筹/网络 | 最大流/最小费用流/网络设计 | 边容量=物理上限、整数流 |
| MCM B | 离散/图论 | 最短路/匹配/支配集/覆盖 | Memo 清楚定义图模型 |
| 网络科学 | 传播/演化 | SIR/IC/LT + 影响力最大化 | 真实网络拓扑、参数校准 |
| 电工杯 | 电网/基础设施 | 鲁棒性/级联失效/恢复 | N-1准则、物理约束硬 |

---

*版本：1.0 | 更新：2026-09-01 | 维护：Modeler 手*