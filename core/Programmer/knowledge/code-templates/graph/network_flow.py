"""
模板来源: resources/code-templates/graph/network_flow.py
修改说明: 
  - 新增网络流算法模板
  - 支持最大流、最小费用最大流
"""
from collections import deque
import numpy as np


def edmonds_karp(capacity, source, sink, n_nodes):
    """
    Edmonds-Karp算法（BFS实现Ford-Fulkerson最大流）
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


def min_cost_max_flow(capacity, cost, source, sink, n_nodes):
    """
    最小费用最大流
    capacity: 容量矩阵
    cost: 费用矩阵
    """
    flow = [[0] * n_nodes for _ in range(n_nodes)]
    total_flow = 0
    total_cost = 0
    
    while True:
        # BFS找最短增广路（按费用）
        dist = [float('inf')] * n_nodes
        parent = [-1] * n_nodes
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


def min_cut(capacity, flow, source, n_nodes):
    """找最小割"""
    # BFS找从source可达的节点
    visited = [False] * n_nodes
    queue = deque([source])
    visited[source] = True
    
    while queue:
        u = queue.popleft()
        for v in range(n_nodes):
            if not visited[v] and capacity[u][v] - flow[u][v] > 0:
                visited[v] = True
                queue.append(v)
    
    # 最小割边
    min_cut_edges = []
    for u in range(n_nodes):
        for v in range(n_nodes):
            if visited[u] and not visited[v] and capacity[u][v] > 0:
                min_cut_edges.append((u, v, capacity[u][v]))
    
    return visited, min_cut_edges


if __name__ == "__main__":
    # 示例：供水网络
    print("网络流示例：供水网络\n")
    
    # 定义网络
    n_nodes = 6
    source = 0
    sink = 5
    
    # 容量矩阵
    capacity = [
        [0, 10, 8, 0, 0, 0],
        [0, 0, 5, 0, 0, 0],
        [0, 0, 0, 7, 0, 0],
        [0, 0, 0, 0, 8, 0],
        [0, 0, 0, 0, 0, 10],
        [0, 0, 0, 0, 0, 0]
    ]
    
    # 费用矩阵
    cost = [
        [0, 2, 3, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 2, 0, 0],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 2],
        [0, 0, 0, 0, 0, 0]
    ]
    
    # 最大流
    max_flow, flow = edmonds_karp(capacity, source, sink, n_nodes)
    print(f"最大流: {max_flow}")
    print("流量分配:")
    for i in range(n_nodes):
        for j in range(n_nodes):
            if flow[i][j] > 0:
                print(f"  {i} -> {j}: {flow[i][j]}")
    
    # 最小费用最大流
    total_flow, total_cost, min_cost_flow = min_cost_max_flow(
        capacity, cost, source, sink, n_nodes
    )
    print(f"\n最小费用最大流:")
    print(f"  最大流: {total_flow}")
    print(f"  最小费用: {total_cost}")
    
    # 最小割
    visited, cut_edges = min_cut(capacity, flow, source, n_nodes)
    print(f"\n最小割:")
    print(f"  可达集合: {[i for i in range(n_nodes) if visited[i]]}")
    print(f"  不可达集合: {[i for i in range(n_nodes) if not visited[i]]}")
    print(f"  割边: {cut_edges}")
