# Playbook: 2021D 交通运输与网络优化

> **题型**: CUMCM D 题 — 图论 + VRP + 网络流
> **核心方法**: Dijkstra + 节约算法 + 遗传算法
> **难度**: ★★★★☆（组合优化 + 多约束 + 大规模）

---

## 1. 问题拆解

```json
{
  "problem": "2021D 交通运输",
  "sub_questions": [
    {"id": "Q1", "desc": "建立路网模型，计算最短路径", "type": "shortest_path", "depends_on": []},
    {"id": "Q2", "desc": "车辆路径规划 (VRP)，最小化总里程", "type": "vrp", "depends_on": ["Q1"]},
    {"id": "Q3", "desc": "带时间窗的 VRP (VRPTW)", "type": "vrptw", "depends_on": ["Q2"]},
    {"id": "Q4", "desc": "动态需求下的实时调度", "type": "dynamic_routing", "depends_on": ["Q3"]}
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **D 题**（网络/运筹） |
| 核心建模 | 图论 + 车辆路径 |
| 求解类型 | NP-hard → 启发式 |
| 方法方向 | 最短路 + VRP 启发式 |

## 3. 候选模型对比

| 方法 | 适用场景 | 推荐度 |
|------|---------|--------|
| **Dijkstra + 节约算法** | 中小规模 VRP | ★★★★★ |
| 遗传算法 | 大规模/多约束 | ★★★★☆ |
| 蚁群算法 | 路径类问题 | ★★★★☆ |
| 精确算法 (Branch-and-Cut) | 小规模精确解 | ★★★☆☆ |

## 4. 模型建立

### 4.1 路网图模型
$$G = (V, E, W), \quad V: \text{节点}, E: \text{路段}, W: \text{权重矩阵}$$

### 4.2 VRP 数学模型
$$\min \sum_{i}\sum_{j} d_{ij} x_{ij}$$
$$\text{s.t.} \quad \sum_j x_{ij} = 1, \quad \sum_i x_{ij} = 1 \quad \forall i,j$$
$$\sum_{i \in S} q_i \leq Q, \quad \forall \text{路线 } S$$

## 5. 代码实现

```python
"""2021D 交通运输 — 最短路 + VRP"""
import numpy as np
import json

np.random.seed(42)

# === 路网数据 ===
N_NODES = 20
N_VEHICLES = 4
VEHICLE_CAP = 50

# 随机生成路网（完全图 + 距离）
coords = np.random.uniform(0, 100, (N_NODES, 2))
dist_matrix = np.zeros((N_NODES, N_NODES))
for i in range(N_NODES):
    for j in range(N_NODES):
        dist_matrix[i, j] = np.sqrt(np.sum((coords[i]-coords[j])**2))

# 需求
demands = np.random.randint(5, 20, N_NODES)
demands[0] = 0  #  depot 无需求

def dijkstra(dist, src):
    """Dijkstra 单源最短路"""
    n = len(dist)
    visited = [False] * n
    d = [float('inf')] * n
    prev = [-1] * n
    d[src] = 0
    for _ in range(n):
        u = -1
        for v in range(n):
            if not visited[v] and (u == -1 or d[v] < d[u]):
                u = v
        if d[u] == float('inf'):
            break
        visited[u] = True
        for v in range(n):
            if d[u] + dist[u, v] < d[v]:
                d[v] = d[u] + dist[u, v]
                prev[v] = u
    return d, prev

def clarke_wright(dist, demands, cap, depot=0):
    """Clarke-Wright 节约算法"""
    n = len(dist)
    customers = [i for i in range(n) if i != depot]
    # 初始：每客户一条独立路线
    routes = [[c] for c in customers]
    # 计算节约值
    savings = []
    for i in range(len(customers)):
        for j in range(i+1, len(customers)):
            ci, cj = customers[i], customers[j]
            s = dist[depot, ci] + dist[depot, cj] - dist[ci, cj]
            savings.append((s, ci, cj))
    savings.sort(reverse=True)
    # 合并路线
    for s, ci, cj in savings:
        ri = next((r for r in routes if ci in r), None)
        rj = next((r for r in routes if cj in r), None)
        if ri is None or rj is None or ri == rj:
            continue
        if ri[-1] == ci and rj[0] == cj:
            load = sum(demands[k] for k in ri + rj)
            if load <= cap:
                ri.extend(rj)
                routes.remove(rj)
        elif ri[0] == ci and rj[-1] == cj:
            load = sum(demands[k] for k in ri + rj)
            if load <= cap:
                rj.extend(ri)
                routes.remove(ri)
    return routes

def route_distance(route, dist, depot=0):
    """计算路线总距离"""
    if not route:
        return 0
    d = dist[depot, route[0]]
    for i in range(len(route)-1):
        d += dist[route[i], route[i+1]]
    d += dist[route[-1], depot]
    return d

if __name__ == "__main__":
    print("=== 2021D 交通运输网络优化 ===")

    # Q1: 最短路
    d0, _ = dijkstra(dist_matrix, 0)

    # Q2: VRP
    routes = clarke_wright(dist_matrix, demands, VEHICLE_CAP, 0)
    total_dist = sum(route_distance(r, dist_matrix) for r in routes)

    results = {
        "Q1_shortest_paths": {
            f"node_{i}": round(float(d0[i]), 2) for i in range(1, min(6, N_NODES))
        },
        "Q2_vrp": {
            "n_routes": len(routes),
            "total_distance": round(float(total_dist), 2),
            "routes": [r[:5] for r in routes[:4]]
        },
        "Q3_vrptw_note": "加入时间窗约束后采用插入启发式",
        "Q4_dynamic_note": "滚动时域 + 实时重优化"
    }

    with open("figures/all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Q1: 节点 1-5 最短路: {[round(d0[i],1) for i in range(1,6)]}")
    print(f"Q2: {len(routes)} 条路线, 总距离 = {total_dist:.2f}")
    print("结果已保存至 figures/all_results.json")
```

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| 需求覆盖 | 所有客户被访问 | 100% 覆盖 |
| 容量约束 | 每条路线 ≤ Q | 全部满足 |
| 距离下界 | 对比最小生成树 × 2 | 差距 < 30% |
| 多次运行 | 5 次独立 | 标准差 < 5% |

## 7-9. 论文结构/图表/LaTeX

关键图表：路网拓扑图、VRP 路线可视化、收敛曲线、灵敏度分析表。
