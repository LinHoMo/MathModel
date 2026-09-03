# 交通运营优化建模知识库

> 本文件提供数学建模竞赛中交通运营优化相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 出租车资源配置优化
- 机场出租车调度与蓄车池管理
- 共享单车投放与调度
- 交通信号配时优化
- 公交线路规划

### 1.2 常见约束条件
- 车辆数量有限
- 驾驶员工作时间限制
- 乘客等待时间上限
- 道路容量限制
- 供需均衡要求

### 1.3 数据特点
- 出租车GPS轨迹数据
- 订单时间-地点数据
- 交通流量数据
- 道路网络拓扑数据
- 时间序列数据（早晚高峰等）

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 排队论 | 服务系统建模 | 理论基础扎实 | 假设条件严格 |
| 二部图匹配 | 供需匹配 | 全局最优匹配 | 计算复杂度高 |
| 供需均衡模型 | 区域资源配置 | 平衡供需关系 | 需要大量数据 |
| 整数规划 | 调度优化 | 精确求解 | 维数灾难 |
| 最短路径 | 路线规划 | 高效准确 | 需要路网数据 |
| 仿真模拟 | 复杂系统分析 | 灵活性高 | 耗时长 |

---

## 3. 数学基础

### 3.1 排队论

**M/M/c排队模型**：
```
到达率: λ (单位时间到达乘客数)
服务率: μ (单位时间服务乘客数)
服务台数: c

系统强度: ρ = λ / (c * μ)
稳态条件: ρ < 1
```

**关键指标**：
```
系统中平均乘客数: L = ρ * (1 - P₀) / (1 - ρ)² + c*ρ
等待队列平均长度: Lq = ρ² * P₀ / (c! * (1-ρ)²) * (λ/μ)^c
平均等待时间: Wq = Lq / λ
平均逗留时间: W = L / λ
```

**P₀ (系统空闲概率)**：
```
P₀ = [Σ(k=0,c-1) (cρ)^k/k! + (cρ)^c/c! * 1/(1-ρ)]⁻¹
```

### 3.2 匹配度指标

**供需匹配度**：
```
匹配度 = min(供给, 需求) / max(供给, 需求)
全局匹配度 = Σ(min(S_i, D_i)) / Σ(max(S_i, D_i))
```

**二部图匹配**：
```
max Σ w_ij * x_ij
s.t. Σ_j x_ij ≤ 1  (∀i)
     Σ_i x_ij ≤ 1  (∀j)
     x_ij ∈ {0, 1}
```

### 3.3 最短路径

**Dijkstra算法**：
```
初始化: d[s] = 0, d[v] = ∞ (∀v ≠ s)
重复: u = argmin d[v] (v未访问)
       对每个邻接点v: d[v] = min(d[v], d[u] + w(u,v))
```

**Floyd-Warshall算法**：
```
d[i][j] = min(d[i][j], d[i][k] + d[k][j])
```

### 3.4 整数规划

**调度优化模型**：
```
min Σ c_ij * x_ij
s.t. Σ_j x_ij = 1  (∀i)  [每辆车分配一个任务]
     Σ_i x_ij = 1  (∀j)  [每个任务分配一辆车]
     x_ij ∈ {0, 1}
```

---

## 4. Python实现

### 4.1 排队论模型

```python
import numpy as np
from math import factorial

class MMCQueue:
    """M/M/c排队模型"""
    
    def __init__(self, arrival_rate, service_rate, n_servers):
        """
        Parameters
        ----------
        arrival_rate : float
            到达率 λ (人/小时)
        service_rate : float
            服务率 μ (人/小时/服务台)
        n_servers : int
            服务台数 c
        """
        self.lam = arrival_rate
        self.mu = service_rate
        self.c = n_servers
        self.rho = self.lam / (self.c * self.mu)  # 系统强度
    
    def check_stability(self):
        """检查系统是否稳定"""
        return self.rho < 1
    
    def P0(self):
        """系统空闲概率"""
        if not self.check_stability():
            return None
        
        rho = self.rho
        c = self.c
        
        sum_terms = sum([(c * rho)**k / factorial(k) for k in range(c)])
        last_term = (c * rho)**c / (factorial(c) * (1 - rho))
        
        return 1 / (sum_terms + last_term)
    
    def L(self):
        """系统中平均乘客数"""
        if not self.check_stability():
            return float('inf')
        
        P0 = self.P0()
        rho = self.rho
        c = self.c
        
        Lq = (rho * P0 * (c * rho)**c) / (factorial(c) * (1 - rho)**2)
        L = Lq + c * rho
        
        return L
    
    def Lq(self):
        """等待队列平均长度"""
        if not self.check_stability():
            return float('inf')
        
        P0 = self.P0()
        rho = self.rho
        c = self.c
        
        Lq = (rho * P0 * (c * rho)**c) / (factorial(c) * (1 - rho)**2)
        
        return Lq
    
    def W(self):
        """平均逗留时间 (小时)"""
        return self.L() / self.lam
    
    def Wq(self):
        """平均等待时间 (小时)"""
        return self.Lq() / self.lam
    
    def summary(self):
        """打印系统指标"""
        print(f"系统强度 ρ = {self.rho:.3f}")
        print(f"系统空闲概率 P₀ = {self.P0():.4f}")
        print(f"平均乘客数 L = {self.L():.2f} 人")
        print(f"平均队列长度 Lq = {self.Lq():.2f} 人")
        print(f"平均逗留时间 W = {self.W()*60:.1f} 分钟")
        print(f"平均等待时间 Wq = {self.Wq()*60:.1f} 分钟")
```

### 4.2 二部图匹配

```python
import numpy as np
from scipy.optimize import linear_sum_assignment

def bipartite_matching(cost_matrix):
    """
    二部图最优匹配（匈牙利算法）
    
    Parameters
    ----------
    cost_matrix : ndarray
        成本矩阵 (n_supply x n_demand)
    
    Returns
    -------
    row_ind, col_ind : ndarray
        匹配的行索引和列索引
    total_cost : float
        总成本
    """
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    total_cost = cost_matrix[row_ind, col_ind].sum()
    
    return row_ind, col_ind, total_cost

def supply_demand_matching(supply, demand, distance_matrix):
    """
    供需匹配
    
    Parameters
    ----------
    supply : ndarray
        各区域供给量
    demand : ndarray
        各区域需求量
    distance_matrix : ndarray
        区域间距离矩阵
    
    Returns
    -------
    matching : dict
        匹配结果
    """
    n_supply = len(supply)
    n_demand = len(demand)
    
    # 扩充成本矩阵以处理不平衡情况
    max_size = max(n_supply, n_demand)
    cost_matrix = np.full((max_size, max_size), 1e6)
    
    for i in range(n_supply):
        for j in range(n_demand):
            cost_matrix[i, j] = distance_matrix[i, j]
    
    # 匈牙利算法求解
    row_ind, col_ind, total_cost = bipartite_matching(cost_matrix)
    
    # 过滤有效匹配
    matching = {}
    for r, c in zip(row_ind, col_ind):
        if r < n_supply and c < n_demand:
            matching[r] = c
    
    return matching, total_cost

def calculate_matching_degree(supply, demand):
    """计算供需匹配度"""
    min_sum = np.sum(np.minimum(supply, demand))
    max_sum = np.sum(np.maximum(supply, demand))
    
    return min_sum / max_sum if max_sum > 0 else 0
```

### 4.3 最短路径

```python
import numpy as np
import heapq

def dijkstra(graph, start, end=None):
    """
    Dijkstra最短路径算法
    
    Parameters
    ----------
    graph : dict
        邻接表表示的图 {node: [(neighbor, weight), ...]}
    start : str
        起始节点
    end : str, optional
        目标节点
    
    Returns
    -------
    distances : dict
        到各节点的最短距离
    paths : dict
        到各节点的最短路径
    """
    distances = {node: float('infinity') for node in graph}
    distances[start] = 0
    paths = {node: [] for node in graph}
    paths[start] = [start]
    
    pq = [(0, start)]
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        if current_dist > distances[current]:
            continue
        
        for neighbor, weight in graph[current]:
            distance = current_dist + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                paths[neighbor] = paths[current] + [neighbor]
                heapq.heappush(pq, (distance, neighbor))
    
    if end:
        return distances[end], paths[end]
    
    return distances, paths

def floyd_warshall(n_nodes, edges):
    """
    Floyd-Warshall全源最短路径
    
    Parameters
    ----------
    n_nodes : int
        节点数
    edges : list
        边列表 [(u, v, w), ...]
    
    Returns
    -------
    dist : ndarray
        最短距离矩阵
    """
    dist = np.full((n_nodes, n_nodes), float('infinity'))
    np.fill_diagonal(dist, 0)
    
    for u, v, w in edges:
        dist[u][v] = w
        dist[v][u] = w  # 无向图
    
    for k in range(n_nodes):
        for i in range(n_nodes):
            for j in range(n_nodes):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    
    return dist
```

### 4.4 出租车调度优化

```python
import numpy as np
from scipy.optimize import linprog

def taxi_dispatch_optimization(n_taxis, n_orders, 
                                distance_matrix, time_windows):
    """
    出租车调度整数规划模型
    
    Parameters
    ----------
    n_taxis : int
        出租车数量
    n_orders : int
        订单数量
    distance_matrix : ndarray
        出租车到订单的距离矩阵
    time_windows : list
        订单时间窗口 [(start, end), ...]
    
    Returns
    -------
    assignment : ndarray
        分配矩阵
    total_distance : float
        总行驶距离
    """
    from scipy.optimize import linprog
    
    # 构建目标函数（最小化总距离）
    c = distance_matrix.flatten()
    
    # 约束：每辆出租车最多接一个订单
    A_eq = np.zeros((n_taxis, n_taxis * n_orders))
    b_eq = np.ones(n_taxis)
    
    for i in range(n_taxis):
        A_eq[i, i*n_orders:(i+1)*n_orders] = 1
    
    # 约束：每个订单最多被一辆出租车接
    A_demand = np.zeros((n_orders, n_taxis * n_orders))
    b_demand = np.ones(n_orders)
    
    for j in range(n_orders):
        A_demand[j, j::n_orders] = 1
    
    # 合并等式约束
    A_eq_full = np.vstack([A_eq, A_demand])
    b_eq_full = np.concatenate([b_eq, b_demand])
    
    # 变量边界
    bounds = [(0, 1) for _ in range(n_taxis * n_orders)]
    
    # 求解
    result = linprog(c, A_eq=A_eq_full, b_eq=b_eq_full,
                    bounds=bounds, method='highs')
    
    if result.success:
        assignment = result.x.reshape(n_taxis, n_orders)
        total_distance = result.fun
        return assignment, total_distance
    
    return None, None
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 排队论假设不满足 | M/M/c模型不适用 | 检查泊松到达和服务假设 |
| 匹配不平衡 | 供给≠需求 | 添加虚拟节点平衡 |
| 忽略时间约束 | 调度不可行 | 加入时间窗口约束 |
| 单位不一致 | 计算错误 | 统一使用小时和人次 |
| 未考虑空驶率 | 效率估计偏高 | 引入空驶率修正系数 |
| 忽略交通拥堵 | 时间估计不准 | 使用实际路况数据 |

---

## 6. 验证方法

### 6.1 排队论验证
- 检查稳态条件 ρ < 1
- 与仿真结果对比
- 验证Little公式 L = λW

### 6.2 匹配优化验证
- 检查匹配是否为最优（与已知最优解对比）
- 验证约束满足情况

### 6.3 最短路径验证
- 与已知最短路径对比
- 检查三角不等式

### 6.4 仿真验证
- 蒙特卡洛仿真验证系统性能
- 与实际运营数据对比

---

## 7. 真题案例

### 7.1 2015B 出租车资源配置

**题目要点**：
- 分析出租车供需关系
- 优化出租车资源配置
- 评估调度策略效果

**解题思路**：
1. 收集出租车GPS和订单数据
2. 建立供需匹配模型
3. 设计调度优化算法
4. 评估优化效果

### 7.2 2019C 机场出租车

**题目要点**：
- 机场出租车蓄车池管理
- 乘客等待时间优化
- 出租车收益最大化

**解题思路**：
1. 建立排队论模型分析蓄车池
2. 设计蓄车池容量和调度策略
3. 优化乘客-出租车匹配
4. 平衡等待时间和收益

**关键公式**：
```
蓄车池容量: C ≥ λ * Wq
乘客等待时间: Wq = Lq / λ
出租车空驶率: η_empty = T_empty / T_total
```

---

## 8. 验证清单

- [ ] 排队论模型稳态条件满足
- [ ] 供需匹配度合理（>0.8）
- [ ] 最短路径算法正确
- [ ] 调度约束满足（时间窗口、车辆容量）
- [ ] 空驶率在合理范围（15%-40%）
- [ ] 乘客等待时间在可接受范围
- [ ] 结果与实际数据吻合
