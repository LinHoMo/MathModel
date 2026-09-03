# Playbook: MCM B 离散/图论建模

> **题型**: MCM B 题 — 离散优化 + 图论 + 网络设计
> **核心方法**: 图论 + 网络流 + 启发式算法
> **难度**: ★★★★☆（组合优化 + 图结构设计）

---

## 1. 问题拆解

```json
{
  "problem": "MCM B 离散系统建模（典型：网络设计/资源分配）",
  "sub_questions": [
    {"id": "Q1", "desc": "建立网络/图模型，定义节点与边", "type": "graph_modeling", "depends_on": []},
    {"id": "Q2", "desc": "求解网络最优设计（最小成本/最大流）", "type": "network_optimization", "depends_on": ["Q1"]},
    {"id": "Q3", "desc": "分析网络鲁棒性与脆弱性", "type": "robustness", "depends_on": ["Q1"]},
    {"id": "Q4", "desc": "动态网络：节点/边随时间变化的策略", "type": "dynamic_network", "depends_on": ["Q2", "Q3"]}
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **MCM B**（离散/图论） |
| 核心建模 | 图论 + 网络优化 |
| 求解类型 | 组合优化 |
| 方法方向 | 最短路/网络流/启发式 |

## 3. 候选模型对比

| 方法 | 适用场景 | 推荐度 |
|------|---------|--------|
| **图论 + 启发式** | 网络设计/调度 | ★★★★★ |
| 整数规划 | 小规模精确解 | ★★★★☆ |
| 最小生成树 | 连通/布线 | ★★★★☆ |
| 网络流 | 流量分配 | ★★★☆☆ |

## 4. 模型建立

### 4.1 图模型
$$G = (V, E, w), \quad w: E \to \mathbb{R}^+$$

### 4.2 最小成本网络设计
$$\min \sum_{e \in E} c_e x_e$$
$$\text{s.t.} \quad \text{连通性}, \text{容量约束}, \text{度约束}$$

### 4.3 网络鲁棒性
$$R(G) = 1 - \frac{1}{n}\sum_{i} \frac{s_i}{n-1}$$
其中 $s_i$ 为移除节点 $i$ 后最大连通分量大小。

## 5. 代码实现

```python
"""MCM B 离散/图论 — 网络设计与鲁棒性"""
import numpy as np
import json

np.random.seed(42)

N_NODES = 30
EDGE_PROB = 0.15

def generate_random_graph(n, p):
    """生成随机图"""
    adj = np.zeros((n, n))
    weights = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            if np.random.random() < p:
                adj[i, j] = adj[j, i] = 1
                w = np.random.uniform(1, 10)
                weights[i, j] = weights[j, i] = w
    return adj, weights

def dijkstra(weights, src):
    n = len(weights)
    dist = [float('inf')] * n
    dist[src] = 0
    visited = [False] * n
    for _ in range(n):
        u = min((v for v in range(n) if not visited[v]),
                key=lambda v: dist[v], default=-1)
        if u == -1 or dist[u] == float('inf'):
            break
        visited[u] = True
        for v in range(n):
            if weights[u, v] > 0 and dist[u] + weights[u, v] < dist[v]:
                dist[v] = dist[u] + weights[u, v]
    return dist

def mst_prim(weights):
    """Prim 最小生成树"""
    n = len(weights)
    in_tree = [False] * n
    tree_edges = []
    in_tree[0] = True
    for _ in range(n-1):
        best_w, best_u, best_v = float('inf'), -1, -1
        for u in range(n):
            if not in_tree[u]:
                continue
            for v in range(n):
                if not in_tree[v] and weights[u, v] > 0:
                    if weights[u, v] < best_w:
                        best_w = weights[u, v]
                        best_u, best_v = u, v
        if best_v >= 0:
            in_tree[best_v] = True
            tree_edges.append((best_u, best_v, best_w))
    return tree_edges

def network_robustness(adj, n):
    """节点移除后的鲁棒性曲线"""
    degrees = adj.sum(axis=1)
    order = np.argsort(-degrees)  # 度从高到低
    robustness = []
    current_adj = adj.copy()
    for k in range(0, n, max(1, n//10)):
        # 移除前 k 个高度节点
        removed = set(order[:k])
        visited = set()
        start = next(i for i in range(n) if i not in removed)
        stack = [start]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for nb in range(n):
                if current_adj[node, nb] > 0 and nb not in visited and nb not in removed:
                    stack.append(nb)
        robustness.append(len(visited) / n)
    return robustness

if __name__ == "__main__":
    print("=== MCM B 离散/图论建模 ===")

    adj, weights = generate_random_graph(N_NODES, EDGE_PROB)
    n_edges = int(adj.sum() / 2)

    # Q1: 图属性
    degrees = adj.sum(axis=1)
    avg_degree = degrees.mean()

    # Q2: MST
    mst = mst_prim(weights)
    mst_cost = sum(w for _, _, w in mst)

    # Q3: 最短路
    dist0 = dijkstra(weights, 0)
    avg_dist = np.mean([d for d in dist0 if d < float('inf')])

    # Q4: 鲁棒性
    robustness = network_robustness(adj, N_NODES)

    results = {
        "Q1_graph": {
            "nodes": N_NODES,
            "edges": n_edges,
            "avg_degree": round(float(avg_degree), 2),
            "density": round(float(n_edges / (N_NODES*(N_NODES-1)/2)), 3)
        },
        "Q2_mst": {
            "total_cost": round(float(mst_cost), 2),
            "n_edges": len(mst)
        },
        "Q3_shortest_path": {
            "avg_distance": round(float(avg_dist), 2),
            "max_distance": round(float(max(d for d in dist0 if d < float('inf'))), 2)
        },
        "Q4_robustness": {
            "initial_connected": robustness[0] > 0.99,
            "after_10pct_removal": round(float(robustness[min(3, len(robustness)-1)]), 3)
        }
    }

    with open("figures/all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"图: {N_NODES} 节点, {n_edges} 边, 平均度 = {avg_degree:.2f}")
    print(f"MST 成本 = {mst_cost:.2f}")
    print(f"平均最短距离 = {avg_dist:.2f}")
    print("结果已保存至 figures/all_results.json")
```

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| MST 最优性 | 与 Kruskal 对比 | 成本一致 |
| 连通性 | BFS/DFS 验证 | 全连通 |
| 度分布 | 与理论对比 | 趋势一致 |
| 鲁棒性曲线 | 随机/定向移除对比 | 定向更脆弱 |

## 7-9. 论文结构/图表/LaTeX

关键图表：网络拓扑图、MST 可视化、度分布直方图、鲁棒性衰减曲线。
