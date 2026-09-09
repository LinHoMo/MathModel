"""2011_B 交巡警服务平台 — 图论Dijkstra+最近邻分配（自包含，纯标准库）。"""
import json
import heapq
import math

def solve(inputs: dict) -> dict:
    # 构建A区简化交通网络：20个节点，模拟城区道路
    # 节点坐标（km），用于计算距离
    random_seed = 42
    # 固定的20个节点坐标（模拟A区交通网络）
    coords = [
        (0.5, 0.5), (1.5, 0.3), (2.5, 0.6), (3.5, 0.4), (4.5, 0.7),
        (0.8, 1.5), (1.8, 1.8), (2.8, 1.5), (3.8, 1.9), (4.8, 1.6),
        (0.3, 2.8), (1.3, 3.0), (2.3, 2.7), (3.3, 3.1), (4.3, 2.8),
        (1.0, 4.0), (2.0, 4.2), (3.0, 3.9), (4.0, 4.1), (4.8, 3.8),
    ]
    n_nodes = len(coords)

    # 构建邻接表：相邻节点（距离<1.5km）之间有道路
    adj = {i: [] for i in range(n_nodes)}
    edges = []
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            dist = math.sqrt((coords[i][0] - coords[j][0])**2 +
                             (coords[i][1] - coords[j][1])**2)
            if dist < 1.5:
                adj[i].append((j, dist))
                adj[j].append((i, dist))
                edges.append((i, j, round(dist, 3)))

    # 20个交巡警服务平台（设在节点0,2,4,6,8,10,12,14,16,18,1,3,5,7,9,11,13,15,17）
    platforms = list(range(20))  # 每个节点都有平台（简化）

    # Dijkstra最短路径
    def dijkstra(source):
        dist = {i: float("inf") for i in range(n_nodes)}
        dist[source] = 0
        pq = [(0, source)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    heapq.heappush(pq, (dist[v], v))
        return dist

    # 从每个平台到所有节点的最短距离
    platform_distances = {}
    for p in platforms:
        platform_distances[p] = dijkstra(p)

    # 管辖范围分配：每个节点分配给最近的平台
    speed = 60.0  # km/h
    response_limit = 3.0  # 分钟
    distance_limit = speed * response_limit / 60.0  # 3km

    allocation = {}
    max_response = 0.0
    covered_count = 0
    platform_workload = {p: 0 for p in platforms}

    for node in range(n_nodes):
        best_platform = None
        best_dist = float("inf")
        for p in platforms:
            d = platform_distances[p][node]
            if d < best_dist:
                best_dist = d
                best_platform = p
        allocation[node] = {
            "platform": best_platform,
            "distance_km": round(best_dist, 3),
            "response_time_min": round(best_dist / speed * 60, 2),
            "within_3min": best_dist <= distance_limit,
        }
        platform_workload[best_platform] += 1
        if best_dist <= distance_limit:
            covered_count += 1
        max_response = max(max_response, best_dist / speed * 60)

    coverage_rate = covered_count / n_nodes

    # 工作量不均衡度（变异系数）
    workloads = list(platform_workload.values())
    mean_wl = sum(workloads) / len(workloads)
    std_wl = (sum((w - mean_wl)**2 for w in workloads) / len(workloads))**0.5
    cv_workload = std_wl / mean_wl if mean_wl > 0 else 0

    # 13条交通要道封锁调度（Q1第二问）
    # 模拟13个出入城区路口节点
    exit_nodes = [0, 4, 9, 14, 19, 1, 6, 11, 16, 3, 8, 13, 18]
    # 贪心分配：每个平台封锁一个路口，最小化总调度距离
    available_platforms = set(platforms)
    blockade_schedule = []
    total_blockade_dist = 0.0
    for exit_node in exit_nodes:
        best_p = None
        best_d = float("inf")
        for p in available_platforms:
            d = platform_distances[p][exit_node]
            if d < best_d:
                best_d = d
                best_p = p
        if best_p is not None:
            available_platforms.discard(best_p)
            blockade_schedule.append({
                "exit_node": exit_node,
                "platform": best_p,
                "distance_km": round(best_d, 3),
                "arrival_min": round(best_d / speed * 60, 2),
            })
            total_blockade_dist += best_d

    return {
        "n_nodes": n_nodes,
        "n_edges": len(edges),
        "n_platforms": len(platforms),
        "coverage_rate_3min": round(coverage_rate, 4),
        "max_response_time_min": round(max_response, 2),
        "avg_response_time_min": round(
            sum(a["response_time_min"] for a in allocation.values()) / n_nodes, 2),
        "workload_cv": round(cv_workload, 4),
        "platform_workload": platform_workload,
        "allocation": {str(k): v for k, v in allocation.items()},
        "blockade_n_exits": len(exit_nodes),
        "blockade_total_dist_km": round(total_blockade_dist, 3),
        "blockade_avg_arrival_min": round(
            sum(b["arrival_min"] for b in blockade_schedule) / len(blockade_schedule), 2),
        "blockade_schedule": blockade_schedule,
        "speed_kmh": speed,
        "response_limit_min": response_limit,
        "distance_limit_km": distance_limit,
    }

if __name__ == "__main__":
    print(json.dumps(solve({}), ensure_ascii=False))
