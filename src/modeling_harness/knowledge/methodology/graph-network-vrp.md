# 图论、网络与路径优化

> 适用：路径规划、物流配送、网络流、选址、传播与影响力分析、复杂系统建模。
> 本篇补足 `graph-theory.md` 未覆盖的部分：**TSP / VRP、复杂网络指标、NetworkX 实战**。

## 一、基础问题速查

| 问题 | 算法 | 复杂度 | 备注 |
|---|---|---|---|
| 单源最短路径（非负权） | Dijkstra | $O((V+E)\log V)$ | NetworkX 默认 |
| 单源最短路径（含负权） | Bellman-Ford | $O(VE)$ | 可检测负权环 |
| 全源最短路径 | Floyd | $O(V^3)$ | 规模 <500 可用 |
| 启发式最短路 | A* | 取决于启发函数 | 有坐标信息时快很多 |
| 最小生成树 | Prim / Kruskal | $O(E\log V)$ | 稠密图 Prim 更优 |
| 最大流 / 最小割 | Dinic / Edmonds-Karp | $O(V^2E)$ | 容量受限路径、匹配 |
| 最小费用最大流 | SPFA 增广 | — | 带成本的网络流 |
| 二分图匹配 | 匈牙利算法 | $O(VE)$ | 指派问题 |
| 拓扑排序 | Kahn / DFS | $O(V+E)$ | DAG 调度 |

**先确认问题属于哪一类，再选算法。** 把 VRP 当 TSP 解、把最大流当最短路解，是常见的建模错误。

## 二、TSP（旅行商问题）

### 2.1 规模决定解法

| 城市数 | 方法 | 说明 |
|---|---|---|
| $n\le 12$ | 动态规划（状态压缩） | 精确解，$O(n^2 2^n)$ |
| $n\le 100$ | 分支定界 / 整数规划 | 可用 Gurobi / OR-Tools 求精确解 |
| $n>100$ | 启发式 | ACO / SA / 遗传，或构造式 + 局部搜索 |

**关键原则：能求精确解就先求精确解**，用它作为启发式的对照基线。只报启发式结果而不与精确解比对，无法说明解的质量。

### 2.2 构造式方法（快速基线）

- **最近邻**：每次走向最近的未访问点。快，但质量差（通常比最优差 25%）
- **最小生成树法**：MST × 2 倍近似，保证 ≤2 倍最优
- **插入法**：逐步插入代价最小的城市
- **Christofides**：保证 ≤1.5 倍最优（需满足三角不等式）

构造解**必须再做局部搜索**，否则质量不可接受。

### 2.3 局部搜索算子

| 算子 | 操作 | 适用 |
|---|---|---|
| 2-opt | 反转路径中一段 | TSP 最经典，消除交叉 |
| Or-opt | 把 1–3 个连续点移到别处 | 比 2-opt 温和 |
| 2h-opt / Or-3opt | 三边重连 | 质量更高、更慢 |

2-opt 消除路径交叉是**最直观也最有效的改进**，配合 SA 就能得到不错的结果。

### 2.4 整数规划形式（小规模精确解）

$$\min\sum_{i,j}d_{ij}x_{ij}\quad\text{s.t.}\quad
\sum_j x_{ij}=1,\ \sum_i x_{ij}=1,\
u_i-u_j+nx_{ij}\le n-1$$

最后一组是 **MTZ 子回路消除约束**——漏掉会得到"几个独立小环"的非法解，这是最经典的建模陷阱。

## 三、VRP（车辆路径问题）

### 3.1 变体

| 变体 | 约束 | 说明 |
|---|---|---|
| CVRP | 车辆容量 | 最常见 |
| VRPTW | 时间窗 | 早到等待、晚到不可 |
| MDVRP | 多车场 | 起点不同 |
| VRPB | 带回程取货 | 送货 + 取货 |

### 3.2 经典算法

- **节约算法（Clarke-Wright）**：从"每客户一车"出发，合并节约量最大的两条路径。快、易实现、质量尚可，是很好的基线。
  节约量 $s_{ij}=d_{i0}+d_{0j}-d_{ij}$。
- **扫描算法**：按极角扫描客户，按容量切分成若干扇区，每个扇区内解 TSP。
- **插入法**：按插入代价最小逐步把客户加入路径。
- **元启发式**：ACO / 禁忌搜索 / 遗传，配合局部搜索。

### 3.3 陷阱

- **忘记车辆数或容量约束**——VRP 的核心就是这些约束，漏掉就退化成 TSP
- 时间窗建模时未区分"硬时间窗"（不可违反）与"软时间窗"（罚函数）
- 距离矩阵未对称检查（实际路网常不对称，不能用无向图）
- 只用一种方法、不与节约算法基线对比

## 四、复杂网络指标

| 指标 | 含义 | 用途 |
|---|---|---|
| 度 $k_i$ / 度分布 | 连接数 | 识别枢纽节点 |
| 聚类系数 $C$ | 邻居间互连程度 | 小世界特征 |
| 平均路径长度 $L$ | 两节点平均距离 | 小世界特征（$L$ 小、$C$ 大） |
| 度中心性 | 度 / (n−1) | 影响力粗判 |
| 介数中心性 | 经过该点最短路占比 | **识别关键枢纽/桥梁** |
| 接近中心性 | 到所有点距离倒数 | 传播最快节点 |
| 特征向量中心性 / PageRank | 考虑邻居重要性 | 影响力传播 |
| 模块度 $Q$ | 社区划分质量 | 社区发现评价 |

### 经典模型

- **ER 随机图**：度分布近似泊松
- **WS 小世界**：高聚类 + 短路径
- **BA 无标度**：度分布幂律，存在枢纽节点，对随机攻击鲁棒、对枢纽攻击脆弱

**建模时先算这些指标，判断网络属于哪类**，再选传播/鲁棒性模型。直接假设"网络是随机的"通常不成立。

## 五、传播与鲁棒性（常考题）

| 模型 | 适用 |
|---|---|
| SI / SIR / SIS | 传染病、信息传播、谣言扩散 |
| 独立级联 IC | 影响力最大化 |
| 线性阈值 LT | 群体行为扩散 |
| 渗流理论 | 网络鲁棒性、级联失效 |

**必须做**：不同攻击策略下（随机失效 vs 蓄意攻击枢纽）的网络效率变化曲线——这是鲁棒性分析的标准写法，也是拉开差距的地方。

## 六、NetworkX 实战要点

```python
import networkx as nx
import numpy as np

G = nx.Graph()
G.add_weighted_edges_from([(1, 2, 3.5), (2, 3, 1.2)])

# 最短路（有坐标时优先 A*，比 Dijkstra 快很多）
path = nx.astar_path(G, src, dst, heuristic=lambda a, b: dist(a, b))
length = nx.astar_path_length(G, src, dst, heuristic=lambda a, b: dist(a, b))

# 中心性
deg = nx.degree_centrality(G)
bet = nx.betweenness_centrality(G, weight="weight")   # 记得带权
pr = nx.pagerank(G, weight="weight")

# 社区发现（模块度评价）
from networkx.algorithms.community import greedy_modularity_communities
comms = greedy_modularity_communities(G, weight="weight")
mod = nx.algorithms.community.modularity(G, comms, weight="weight")
```

**要点**：

- 中心性、最短路、社区发现都要传 `weight=`，否则默认按跳数而非实际距离
- 大图（>5000 节点）的介数中心性很慢，可用采样近似
- 有向 / 无向、加权 / 非加权要与实际路网一致——**实际道路常不对称**

## 七、常见扣分点

1. TSP 建模漏掉子回路消除约束（MTZ），得到非法解
2. VRP 漏掉容量或车辆数约束
3. 能求精确解的规模却只用启发式，且不对照
4. 距离矩阵当作对称矩阵，与实际路网不符
5. 中心性、最短路未传 `weight=`
6. 构造解后不做局部搜索
7. 启发式只跑一次，不做多次运行统计（见 `swarm-intelligence.md`）
8. 网络建模前不算基本指标，凭直觉假设网络类型
9. 鲁棒性分析只做随机失效，不做蓄意攻击枢纽
10. 传播模型参数（感染率、恢复率）未做敏感性分析

## 八、代码骨架（TSP 的 2-opt + SA）

```python
import numpy as np

def tour_length(tour, D):
    """路径总长（回到起点）。D 为距离矩阵，可不对称。"""
    return sum(D[tour[i], tour[(i + 1) % len(tour)]] for i in range(len(tour)))


def two_opt(tour, i, k):
    """反转 tour[i:k+1] 段——消除路径交叉的基本算子。"""
    return tour[:i] + tour[i:k + 1][::-1] + tour[k + 1:]


def tsp_sa(D, iters=20000, T0=None, alpha=0.995, seed=42):
    """模拟退火解 TSP。D 可为非对称矩阵。"""
    rng = np.random.default_rng(seed)
    n = len(D)
    tour = list(rng.permutation(n))
    cur = tour_length(tour, D)
    if T0 is None:
        T0 = cur * 0.1          # 初始温度按量级设定，别硬编码
    T = T0
    best, best_len = tour[:], cur

    for _ in range(iters):
        i, k = sorted(rng.choice(n, 2, replace=False))
        cand = two_opt(tour, i, k)
        new = tour_length(cand, D)
        delta = new - cur
        if delta < 0 or rng.random() < np.exp(-delta / max(T, 1e-12)):
            tour, cur = cand, new
            if cur < best_len:
                best, best_len = tour[:], cur
        T *= alpha
        if T < 1e-8:
            break
    return best, best_len
```
