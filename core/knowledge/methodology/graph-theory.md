# 图论与网络方法论

> 本文档提供图论与网络的完整方法论，包括最短路径、网络流、图着色等核心方法。

---

## 一、方法选择决策树

```
图论问题
├── 最短路径？
│   ├── 非负权 → Dijkstra算法
│   ├── 有负权 → Bellman-Ford算法
│   ├── 全源最短路 → Floyd-Warshall算法
│   └── 动态规划 → 状态压缩DP
├── 网络流？
│   ├── 最大流 → Ford-Fulkerson/Edmonds-Karp
│   ├── 最小费用流 → 最小费用最大流
│   └── 最小割 → 最大流最小割定理
├── 树？
│   ├── 最小生成树 → Kruskal/Prim算法
│   └── 最优树 → Huffman编码
├── 匹配？
│   ├── 二部图最大匹配 →匈牙利算法
│   └── 带权匹配 → 匈牙利算法
└── 着色？
    ├── 图着色 → 贪心算法/精确算法
    └── 区间着色 → 贪心算法
```

---

## 二、最短路径算法

### 2.1 Dijkstra算法

**适用**：非负权图的单源最短路径

```python
import heapq
import numpy as np

def dijkstra(graph, source, n_nodes):
    """
    Dijkstra算法
    graph: 邻接表 {node: [(neighbor, weight), ...]}
    source: 源节点
    n_nodes: 节点数
    """
    dist = [float('inf')] * n_nodes
    prev = [-1] * n_nodes
    dist[source] = 0
    
    pq = [(0, source)]
    
    while pq:
        d, u = heapq.heappop(pq)
        
        if d > dist[u]:
            continue
        
        for v, weight in graph.get(u, []):
            if dist[u] + weight < dist[v]:
                dist[v] = dist[u] + weight
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
    
    return dist, prev

def get_path(prev, target):
    """重建路径"""
    path = []
    current = target
    while current != -1:
        path.append(current)
        current = prev[current]
    return path[::-1]
```

### 2.2 Bellman-Ford算法

**适用**：有负权边的单源最短路径（可检测负环）

```python
def bellman_ford(edges, n_nodes, source):
    """
    Bellman-Ford算法
    edges: [(u, v, weight), ...]
    """
    dist = [float('inf')] * n_nodes
    prev = [-1] * n_nodes
    dist[source] = 0
    
    # 松弛 n-1 次
    for _ in range(n_nodes - 1):
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
    
    # 检测负环
    for u, v, w in edges:
        if dist[u] + w < dist[v]:
            return None, None  # 存在负环
    
    return dist, prev
```

### 2.3 Floyd-Warshall算法

**适用**：全源最短路径

```python
def floyd_warshall(n_nodes, edges):
    """
    Floyd-Warshall算法
    返回所有节点对之间的最短距离
    """
    # 初始化距离矩阵
    dist = [[float('inf')] * n_nodes for _ in range(n_nodes)]
    
    for i in range(n_nodes):
        dist[i][i] = 0
    
    for u, v, w in edges:
        dist[u][v] = w
    
    # 动态规划
    for k in range(n_nodes):
        for i in range(n_nodes):
            for j in range(n_nodes):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    
    return dist
```

---

## 三、网络流

### 3.1 最大流（Edmonds-Karp）

```python
from collections import deque

def edmonds_karp(capacity, source, sink, n_nodes):
    """
    Edmonds-Karp算法（BFS实现Ford-Fulkerson）
    capacity: 容量矩阵
    """
    flow = [[0] * n_nodes for _ in range(n_nodes)]
    max_flow = 0
    
    while True:
        # BFS找增广路
        parent = [-1] * n_nodes
        parent[source] = source
        queue = deque([source])
        
        while queue:
            u = queue.popleft()
            
            for v in range(n_nodes):
                if parent[v] == -1 and capacity[u][v] - flow[u][v] > 0:
                    parent[v] = u
                    queue.append(v)
        
        if parent[sink] == -1:
            break
        
        # 找瓶颈容量
        path_flow = float('inf')
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, capacity[u][v] - flow[u][v])
            v = u
        
        # 更新流量
        v = sink
        while v != source:
            u = parent[v]
            flow[u][v] += path_flow
            flow[v][u] -= path_flow
            v = u
        
        max_flow += path_flow
    
    return max_flow, flow
```

### 3.2 最小费用最大流

```python
from collections import deque

def min_cost_max_flow(capacity, cost, source, sink, n_nodes):
    """
    最小费用最大流
    """
    flow = [[0] * n_nodes for _ in range(n_nodes)]
    total_flow = 0
    total_cost = 0
    
    while True:
        # BFS找最短增广路（按费用）
        dist = [float('inf')] * n_nodes
        parent = [-1] * n_nodes
        parent_edge = [(-1, -1)] * n_nodes
        dist[source] = 0
        
        in_queue = [False] * n_nodes
        queue = deque([source])
        in_queue[source] = True
        
        while queue:
            u = queue.popleft()
            in_queue[u] = False
            
            for v in range(n_nodes):
                if capacity[u][v] - flow[u][v] > 0:
                    new_dist = dist[u] + cost[u][v]
                    if new_dist < dist[v]:
                        dist[v] = new_dist
                        parent[v] = u
                        parent_edge[v] = (u, v)
                        if not in_queue[v]:
                            queue.append(v)
                            in_queue[v] = True
        
        if parent[sink] == -1:
            break
        
        # 找瓶颈
        path_flow = float('inf')
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, capacity[u][v] - flow[u][v])
            v = u
        
        # 更新
        v = sink
        while v != source:
            u = parent[v]
            flow[u][v] += path_flow
            flow[v][u] -= path_flow
            total_cost += path_flow * cost[u][v]
            v = u
        
        total_flow += path_flow
    
    return total_flow, total_cost, flow
```

---

## 四、最小生成树

### 4.1 Kruskal算法

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True

def kruskal(n_nodes, edges):
    """
    Kruskal算法
    edges: [(weight, u, v), ...]
    """
    edges.sort()
    mst = []
    uf = UnionFind(n_nodes)
    
    for weight, u, v in edges:
        if uf.union(u, v):
            mst.append((u, v, weight))
            if len(mst) == n_nodes - 1:
                break
    
    return mst
```

### 4.2 Prim算法

```python
import heapq

def prim(graph, n_nodes):
    """
    Prim算法
    graph: 邻接表 {node: [(neighbor, weight), ...]}
    """
    mst = []
    visited = [False] * n_nodes
    pq = [(0, 0, -1)]  # (weight, node, parent)
    
    while pq:
        weight, u, parent = heapq.heappop(pq)
        
        if visited[u]:
            continue
        visited[u] = True
        
        if parent != -1:
            mst.append((parent, u, weight))
        
        for v, w in graph.get(u, []):
            if not visited[v]:
                heapq.heappush(pq, (w, v, u))
    
    return mst
```

---

## 五、图着色

### 5.1 贪心着色

```python
def greedy_graph_coloring(graph, n_nodes):
    """
    贪心图着色
    graph: 邻接表
    """
    result = [-1] * n_nodes
    result[0] = 0
    
    for u in range(1, n_nodes):
        # 找邻居使用的颜色
        used_colors = set()
        for v in graph.get(u, []):
            if result[v] != -1:
                used_colors.add(result[v])
        
        # 分配最小可用颜色
        color = 0
        while color in used_colors:
            color += 1
        
        result[u] = color
    
    return result
```

### 5.2 区间着色

```python
def interval_coloring(intervals):
    """
    区间着色问题
    intervals: [(start, end), ...]
    """
    # 按开始时间排序
    sorted_intervals = sorted(enumerate(intervals), key=lambda x: x[1][0])
    
    colors = [0] * len(intervals)
    end_times = []  # (end_time, color)
    
    for idx, (start, end) in sorted_intervals:
        # 找可用颜色
        available_color = 0
        
        # 移除已结束的区间
        end_times = [(e, c) for e, c in end_times if e <= start]
        
        if end_times:
            used_colors = {c for _, c in end_times}
            available_color = 0
            while available_color in used_colors:
                available_color += 1
        
        colors[idx] = available_color
        end_times.append((end, available_color))
    
    return colors
```

---

## 六、竞赛常见场景

### 6.1 路径规划

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 最短路径 | Dijkstra | A001, A022 |
| 多目标路径 | Pareto最短路 | A171 |
| 动态路网 | 时间依赖最短路 | B195 |

### 6.2 物流调度

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 车辆路径 | TSP/VRP | B195, B196 |
| 配送中心选址 | 网络流 | B203 |
| 供应链网络 | 最小费用流 | B195 |

### 6.3 网络优化

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 通信网络 | 最大流 | C142 |
| 交通网络 | 最小割 | A070 |
| 社区网络 | 图着色 | C101 |

### 6.4 资源分配

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 任务分配 | 二部图匹配 | D017, D026 |
| 频率分配 | 图着色 | D034 |
| 项目调度 | 关键路径法 | D033 |

---

## 七、参考资源

### 7.1 教材推荐

- 《图论导引》（Douglas West）
- 《算法导论》（CLRS）
- 《网络流》（Ahuja）

### 7.2 Python库

- networkx：图论工具箱
- igraph：高性能图计算
- pulp：网络流建模

### 7.3 检查清单

- [ ] 图的表示正确（邻接矩阵/表）
- [ ] 最短路径算法选择恰当
- [ ] 网络流容量约束满足
- [ ] 最小生成树无环
- [ ] 图着色无冲突
