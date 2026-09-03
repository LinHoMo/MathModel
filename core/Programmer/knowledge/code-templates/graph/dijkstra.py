"""
模板来源: resources/code-templates/graph/dijkstra.py
修改说明: 
  - 新增Dijkstra最短路径算法模板
  - 支持路径重建、可视化
"""
import heapq
import numpy as np
import matplotlib.pyplot as plt


def dijkstra(graph, source, n_nodes):
    """
    Dijkstra最短路径算法
    graph: 邻接表 {node: [(neighbor, weight), ...]}
    source: 源节点
    n_nodes: 节点数
    """
    dist = [float('inf')] * n_nodes
    prev = [-1] * n_nodes
    dist[source] = 0
    
    pq = [(0, source)]
    visited = set()
    
    while pq:
        d, u = heapq.heappop(pq)
        
        if u in visited:
            continue
        visited.add(u)
        
        for v, weight in graph.get(u, []):
            if v not in visited and dist[u] + weight < dist[v]:
                dist[v] = dist[u] + weight
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
    
    return dist, prev


def get_path(prev, target):
    """重建最短路径"""
    path = []
    current = target
    while current != -1:
        path.append(current)
        current = prev[current]
    return path[::-1]


def floyd_warshall(n_nodes, edges):
    """
    Floyd-Warshall全源最短路径
    edges: [(u, v, weight), ...]
    """
    dist = [[float('inf')] * n_nodes for _ in range(n_nodes)]
    
    for i in range(n_nodes):
        dist[i][i] = 0
    
    for u, v, w in edges:
        dist[u][v] = w
    
    for k in range(n_nodes):
        for i in range(n_nodes):
            for j in range(n_nodes):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    
    return dist


def plot_graph(graph, n_nodes, node_names=None, filename='figures/shortest_path.png'):
    """绘制图结构"""
    import networkx as nx
    
    G = nx.DiGraph()
    
    for i in range(n_nodes):
        name = node_names[i] if node_names else str(i)
        G.add_node(name)
    
    for u in graph:
        for v, w in graph[u]:
            u_name = node_names[u] if node_names else str(u)
            v_name = node_names[v] if node_names else str(v)
            G.add_edge(u_name, v_name, weight=w)
    
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=2000, 
            node_color='lightblue', font_size=10, font_weight='bold')
    
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"图已保存: {filename}")


def plot_shortest_path(graph, path, n_nodes, node_names=None, 
                      filename='figures/shortest_path_highlight.png'):
    """高亮显示最短路径"""
    import networkx as nx
    
    G = nx.DiGraph()
    
    for i in range(n_nodes):
        name = node_names[i] if node_names else str(i)
        G.add_node(name)
    
    for u in graph:
        for v, w in graph[u]:
            u_name = node_names[u] if node_names else str(u)
            v_name = node_names[v] if node_names else str(v)
            G.add_edge(u_name, v_name, weight=w)
    
    pos = nx.spring_layout(G)
    
    # 绘制所有边
    nx.draw(G, pos, with_labels=True, node_size=2000, 
            node_color='lightgray', font_size=10, font_weight='bold')
    
    # 高亮路径
    path_edges = [(node_names[path[i]], node_names[path[i+1]]) 
                  for i in range(len(path)-1)]
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, 
                          edge_color='red', width=3)
    
    # 高亮路径节点
    path_nodes = [node_names[n] for n in path]
    nx.draw_networkx_nodes(G, pos, nodelist=path_nodes, 
                          node_color='red', node_size=2500)
    
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"路径图已保存: {filename}")


if __name__ == "__main__":
    # 示例：城市交通网络
    print("Dijkstra最短路径算法示例\n")
    
    # 定义图（邻接表）
    n_nodes = 6
    graph = {
        0: [(1, 7), (2, 9), (5, 14)],
        1: [(0, 7), (2, 10), (3, 15)],
        2: [(0, 9), (1, 10), (3, 11), (5, 2)],
        3: [(1, 15), (2, 11), (4, 6)],
        4: [(3, 6), (5, 9)],
        5: [(0, 14), (2, 2), (4, 9)]
    }
    
    node_names = ['A', 'B', 'C', 'D', 'E', 'F']
    
    # Dijkstra算法
    source = 0
    target = 4
    
    dist, prev = dijkstra(graph, source, n_nodes)
    path = get_path(prev, target)
    
    print(f"从 {node_names[source]} 到 {node_names[target]} 的最短路径:")
    print(f"  路径: {' -> '.join([node_names[i] for i in path])}")
    print(f"  距离: {dist[target]}")
    
    # 绘制图
    plot_graph(graph, n_nodes, node_names)
    plot_shortest_path(graph, path, n_nodes, node_names)
    
    # Floyd-Warshall全源最短路径
    print("\n全源最短路径矩阵:")
    edges = []
    for u in graph:
        for v, w in graph[u]:
            edges.append((u, v, w))
    
    all_dist = floyd_warshall(n_nodes, edges)
    for i in range(n_nodes):
        print(f"  {node_names[i]}: {all_dist[i]}")
