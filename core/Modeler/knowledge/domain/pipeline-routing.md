# 输油管布置优化知识库

> 本文件提供数学建模竞赛中输油管布置相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 输油管线路路由优化（连接多个油井/站点）
- 共享管道设计与成本分摊
- 管道交叉、分支点位置选择
- 多目标约束下的成本最小化
- 费马点与斯坦纳树问题

### 1.2 常见约束条件
- 地理约束：地形、河流、道路等障碍物
- 成本约束：管道单位造价、交叉点额外成本
- 距离约束：最大/最小管长限制
- 技术约束：转弯半径、坡度限制
- 经济约束：总预算、运营维护费用

### 1.3 数据特点
- 坐标数据：各站点经纬度或平面坐标
- 成本数据：不同地形单位造价、交叉点成本
- 距离矩阵：站点间欧氏距离或曼哈顿距离
- 权重数据：各站点输油量或重要程度

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 费马点法 | 三站点最小连接 | 理论最优解 | 仅适用于3点 |
| 斯坦纳树 | 多站点网络设计 | 全局最优拓扑 | 计算复杂度高 |
| Lingo优化 | 单/多目标规划 | 求解精确 | 大规模问题慢 |
| 遗传算法 | 复杂约束问题 | 全局搜索能力强 | 收敛速度慢 |
| 几何分析 | 简单布局问题 | 直观易理解 | 适用范围有限 |
| Dijkstra算法 | 网络最短路径 | 时间复杂度低 | 需离散化处理 |

---

## 3. 数学基础

### 3.1 费马点理论

**费马点定义**：给定平面上三个点A、B、C，费马点P是使PA+PB+PC最小的点。

**求解条件**：
- 若三角形内角均小于120°，费马点在三角形内部，且∠APB=∠BPC=∠CPA=120°
- 若存在内角≥120°，费马点为该钝角顶点

**坐标计算（三站点情况）**：
```
P_x = (w_A·A_x + w_B·B_x + w_C·C_x) / (w_A + w_B + w_C)
P_y = (w_A·A_y + w_B·B_y + w_C·C_y) / (w_A + w_B + w_C)
```

其中w_i为各站点权重（如输油量）。

### 3.2 成本函数

**基础成本模型**：
```
C_total = Σ c_i · d_i + Σ f_j · n_j
```

其中：
- c_i: 第i段管道单位长度造价
- d_i: 第i段管道长度
- f_j: 第j个交叉点固定成本
- n_j: 第j个交叉点连接数

**加权成本模型**：
```
C = α·C_construction + β·C_maintenance + γ·C_operation
```

### 3.3 约束优化模型

**单目标优化**：
```
min C(x, y, t)
s.t. g_k(x, y, t) ≤ 0, k=1,2,...,m
     h_j(x, y, t) = 0, j=1,2,...,p
```

其中(x,y)为交叉点坐标，t为拓扑变量。

### 3.4 坐标系建立

**平面直角坐标系**：
- 以某参考点为原点
- x轴正东，y轴正北
- 距离公式：d = √[(x₂-x₁)² + (y₂-y₁)²]

---

## 4. 代码实现

### 4.1 费马点计算

```python
import numpy as np
from scipy.optimize import minimize

def fermat_point(points, weights=None):
    """
    计算加权费马点
    
    Parameters
    ----------
    points : array-like
        各点坐标 [(x1,y1), (x2,y2), ...]
    weights : array-like, optional
        各点权重，默认为等权重
    
    Returns
    -------
    fermat : array
        费马点坐标
    min_dist : float
        最小总距离
    """
    points = np.array(points)
    n = len(points)
    
    if weights is None:
        weights = np.ones(n)
    weights = np.array(weights) / np.sum(weights)
    
    def total_distance(p):
        dists = np.sqrt(np.sum((points - p)**2, axis=1))
        return np.sum(weights * dists)
    
    # 初始点：加权质心
    x0 = np.sum(weights * points[:, 0])
    y0 = np.sum(weights * points[:, 1])
    
    # 优化
    result = minimize(total_distance, [x0, y0], method='Nelder-Mead')
    
    return result.x, result.fun


def fermat_point_3point(A, B, C):
    """
    三站点费马点（解析法）
    当三角形内角均<120°时，费马点满足120°条件
    """
    A, B, C = np.array(A), np.array(B), np.array(C)
    
    # 计算三角形内角
    def angle(p1, vertex, p2):
        v1 = p1 - vertex
        v2 = p2 - vertex
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        return np.arccos(np.clip(cos_angle, -1, 1))
    
    angle_A = angle(B, A, C)
    angle_B = angle(A, B, C)
    angle_C = angle(A, C, B)
    
    # 检查是否有内角>=120°
    if angle_A >= 2*np.pi/3:
        return A
    if angle_B >= 2*np.pi/3:
        return B
    if angle_C >= 2*np.pi/3:
        return C
    
    # 使用数值方法求解120°条件
    def objective(p):
        dA = np.linalg.norm(p - A)
        dB = np.linalg.norm(p - B)
        dC = np.linalg.norm(p - C)
        return dA + dB + dC
    
    # 以质心为初始点
    x0 = (A + B + C) / 3
    result = minimize(objective, x0, method='Nelder-Mead')
    
    return result.x
```

### 4.2 管道路由优化（Lingo风格）

```python
import numpy as np
from scipy.optimize import linprog, minimize

def pipeline_routing_optimization(stations, unit_costs, cross_cost=0):
    """
    管道路由优化（简化版）
    
    Parameters
    ----------
    stations : array
        站点坐标 [(x1,y1), (x2,y2), ...]
    unit_costs : array
        各路段单位造价
    cross_cost : float
        交叉点额外成本
    
    Returns
    -------
    result : dict
        优化结果
    """
    n = len(stations)
    stations = np.array(stations)
    
    # 计算距离矩阵
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dist_matrix[i, j] = np.linalg.norm(stations[i] - stations[j])
    
    # 目标函数：最小化总成本
    def total_cost(connections):
        """
        connections: 连接关系 [从i到j的管道是否存在]
        """
        cost = 0
        for i in range(n):
            for j in range(i+1, n):
                if connections[i, j] > 0.5:
                    cost += dist_matrix[i, j] * unit_costs[0]
        return cost
    
    # 约束：每个站点至少连接一条管道
    constraints = []
    for i in range(n):
        def constraint(connections, idx=i):
            return np.sum(connections[idx, :]) + np.sum(connections[:, idx]) - 1
        constraints.append({'type': 'ineq', 'fun': constraint})
    
    # 初始连接矩阵
    x0 = np.zeros((n, n))
    
    # 优化
    result = minimize(
        lambda x: total_cost(x.reshape(n, n)),
        x0.flatten(),
        method='SLSQP',
        constraints=constraints,
        bounds=[(0, 1)] * (n * n)
    )
    
    connections = result.x.reshape(n, n)
    return {
        'connections': connections,
        'total_cost': result.fun,
        'routes': [(i, j) for i in range(n) for j in range(n) if connections[i, j] > 0.5]
    }
```

### 4.3 斯坦纳树近似

```python
import numpy as np
from itertools import combinations

def steiner_tree_approximation(points):
    """
    斯坦纳树近似算法（最小生成树+费马点）
    
    Parameters
    ----------
    points : array
        站点坐标
    
    Returns
    -------
    steiner_points : list
        斯坦纳点坐标
    total_length : float
        总管道长度
    """
    points = np.array(points)
    n = len(points)
    
    if n <= 1:
        return [], 0
    
    if n == 2:
        return [], np.linalg.norm(points[0] - points[1])
    
    # 计算所有可能的费马点
    steiner_candidates = []
    for combo in combinations(range(n), 3):
        A, B, C = points[combo[0]], points[combo[1]], points[combo[2]]
        fp = fermat_point_3point(A, B, C)
        steiner_candidates.append(fp)
    
    # 选择最佳费马点
    best_length = float('inf')
    best_steiner = None
    
    for sp in steiner_candidates:
        # 计算连接所有点的最小树长度
        all_points = np.vstack([points, sp.reshape(1, -1)])
        mst_length = minimum_spanning_tree_length(all_points)
        
        if mst_length < best_length:
            best_length = mst_length
            best_steiner = sp
    
    return best_steiner, best_length


def minimum_spanning_tree_length(points):
    """计算最小生成树长度（Prim算法）"""
    n = len(points)
    visited = [False] * n
    min_edge = [float('inf')] * n
    min_edge[0] = 0
    total = 0
    
    for _ in range(n):
        # 选择最小边
        u = -1
        for v in range(n):
            if not visited[v] and (u == -1 or min_edge[v] < min_edge[u]):
                u = v
        
        visited[u] = True
        total += min_edge[u]
        
        # 更新相邻边
        for v in range(n):
            if not visited[v]:
                dist = np.linalg.norm(points[u] - points[v])
                if dist < min_edge[v]:
                    min_edge[v] = dist
    
    return total
```

### 4.4 可视化

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_pipeline_routing(stations, routes, steiner_points=None, title="管道路由图"):
    """
    可视化管道路由方案
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    stations = np.array(stations)
    
    # 绘制站点
    ax.scatter(stations[:, 0], stations[:, 1], c='red', s=100, zorder=5, label='站点')
    
    # 标注站点编号
    for i, (x, y) in enumerate(stations):
        ax.annotate(f'S{i+1}', (x, y), textcoords="offset points", 
                   xytext=(0, 10), ha='center', fontsize=10, fontweight='bold')
    
    # 绘制管道
    for i, j in routes:
        ax.plot([stations[i, 0], stations[j, 0]], 
                [stations[i, 1], stations[j, 1]], 
                'b-', linewidth=2, alpha=0.7)
    
    # 绘制费马点/斯坦纳点
    if steiner_points is not None:
        steiner_points = np.array(steiner_points)
        ax.scatter(steiner_points[:, 0], steiner_points[:, 1], 
                  c='green', s=150, marker='*', zorder=5, label='斯坦纳点')
    
    ax.set_xlabel('X坐标 (km)')
    ax.set_ylabel('Y坐标 (km)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.show()
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 忽略地形差异 | 成本估算偏差大 | 引入分段造价系数 |
| 过度简化拓扑 | 结果不可行 | 考虑分支和交叉点 |
| 单位不一致 | 计算错误 | 统一使用km和万元 |
| 边界处理不当 | 优化陷入局部最优 | 多起点优化 |
| 忽略管道交叉 | 成本低估 | 加入交叉点惩罚项 |
| 坐标系错误 | 距离计算错误 | 确认坐标系一致 |

---

## 6. 验证方法

### 6.1 几何验证
- 检查费马点是否满足120°条件（三站点情况）
- 验证管道连接是否覆盖所有站点
- 检查是否有冗余管道

### 6.2 成本验证
- 重新计算各段管道长度并求和
- 比较不同方案的成本差异
- 进行灵敏度分析（单位造价变化±10%）

### 6.3 可行性验证
- 检查管道是否穿越障碍物
- 验证交叉点位置是否合理
- 确认所有约束条件是否满足

### 6.4 对比验证
- 与最小生成树结果对比
- 与枚举法（小规模问题）对比
- 与其他优化算法结果对比

---

## 7. 真题案例

### 2010C 输油管布置

**题目概述**：某油田有多个油井，需要设计输油管道网络，将原油输送到中央处理站。要求总成本最小化。

**关键信息**：
- 多个油井坐标已知
- 管道单位造价与距离成正比
- 交叉点有额外成本
- 需要确定管道网络拓扑和交叉点位置

**解题思路**：
1. 建立坐标系，计算各站点距离矩阵
2. 建立成本函数：C = Σ(管道长度×单位造价) + Σ(交叉点成本)
3. 使用费马点理论确定交叉点最优位置
4. 使用Lingo或Python优化求解
5. 进行灵敏度分析

**参考代码模板**：
```python
# 2010C问题求解框架
stations = np.array([...])  # 站点坐标
# 计算费马点
fp, cost = fermat_point(stations, weights=[...])
# 可视化结果
plot_pipeline_routing(stations, routes, [fp])
```

---

## 8. 参考文献

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| 2010C-A01 | 费马点+Lingo | 加权费马点求解 |
| 2010C-A02 | 遗传算法 | 多目标优化 |
| 2010C-A03 | 几何分析 | 解析解与数值解结合 |

---

## 9. 验证清单

- [ ] 坐标系建立正确，单位统一
- [ ] 距离矩阵计算无误
- [ ] 成本函数包含所有相关项
- [ ] 约束条件完整且合理
- [ ] 费马点位置满足120°条件（三站点）
- [ ] 优化结果全局最优或近似最优
- [ ] 灵敏度分析已执行
- [ ] 结果图表清晰规范
