# 多目标优化领域知识

## 一、核心概念

### 1.1 多目标优化定义
- **定义**: 同时优化多个相互冲突的目标
- **目标函数**: f(x) = [f1(x), f2(x), ..., fk(x)]
- **约束条件**: g(x) ≤ 0, h(x) = 0

### 1.2 Pareto最优
- **支配**: x1支配x2，如果所有目标都不差，至少一个更好
- **Pareto最优解**: 不被任何其他解支配
- **Pareto前沿**: 所有Pareto最优解的集合

### 1.3 常用术语
- **非支配排序**: 将解分为不同等级
- **拥挤度距离**: 同一级解的多样性
- **收敛性**: 接近真实Pareto前沿
- **多样性**: 解的分布均匀

---

## 二、求解方法

### 2.1 加权和法
```python
def weighted_sum_method(objectives, weights):
    """
    加权和法
    """
    # 归一化目标
    normalized = normalize(objectives)
    
    # 加权求和
    fitness = np.sum(normalized * weights, axis=1)
    
    return fitness
```

### 2.2 ε-约束法
```python
def epsilon_constraint_method(objectives, constraint_idx, epsilon):
    """
    ε-约束法
    """
    # 优化目标1，约束其他目标
    main_obj = objectives[:, 0]
    constraints = objectives[:, 1:]
    
    feasible = np.all(constraints <= epsilon, axis=1)
    
    return feasible
```

### 2.3 NSGA-II算法
```python
def nsga2(population, objectives, pop_size=100, generations=500):
    """
    NSGA-II多目标优化
    """
    # 非支配排序
    def non_dominated_sort(population, objectives):
        n = len(population)
        domination_count = np.zeros(n)
        dominated_set = [[] for _ in range(n)]
        ranks = np.zeros(n)
        
        for i in range(n):
            for j in range(i+1, n):
                if np.all(objectives[i] <= objectives[j]) and np.any(objectives[i] < objectives[j]):
                    dominated_set[i].append(j)
                    domination_count[j] += 1
                elif np.all(objectives[j] <= objectives[i]) and np.any(objectives[j] < objectives[i]):
                    dominated_set[j].append(i)
                    domination_count[i] += 1
        
        front = np.where(domination_count == 0)[0]
        rank = 0
        
        while len(front) > 0:
            ranks[front] = rank
            next_front = []
            
            for i in front:
                for j in dominated_set[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
            
            front = next_front
            rank += 1
        
        return ranks
    
    # 拥挤度距离
    def crowding_distance(population, objectives, ranks):
        n = len(population)
        distances = np.zeros(n)
        
        for rank in np.unique(ranks):
            front = np.where(ranks == rank)[0]
            
            for obj_idx in range(objectives.shape[1]):
                sorted_idx = front[np.argsort(objectives[front, obj_idx])]
                distances[sorted_idx[0]] = np.inf
                distances[sorted_idx[-1]] = np.inf
                
                obj_range = objectives[sorted_idx[-1], obj_idx] - objectives[sorted_idx[0], obj_idx]
                if obj_range > 0:
                    for i in range(1, len(sorted_idx)-1):
                        distances[sorted_idx[i]] += (objectives[sorted_idx[i+1], obj_idx] - 
                                                    objectives[sorted_idx[i-1], obj_idx]) / obj_range
        
        return distances
    
    # 主循环
    for gen in range(generations):
        # 选择、交叉、变异
        # ...
        
        # 非支配排序
        ranks = non_dominated_sort(population, objectives)
        distances = crowding_distance(population, objectives, ranks)
        
        # 选择
        selected = select(population, objectives, ranks, distances, pop_size)
    
    return population, objectives
```

### 2.4 MOEA/D算法
```python
def moead(population, objectives, pop_size=100, generations=500):
    """
    MOEA/D分解多目标优化
    """
    # 生成权重向量
    weights = generate_weights(population.shape[1], pop_size)
    
    # 初始化
    for gen in range(generations):
        for i in range(pop_size):
            # 选择邻域
            neighbors = get_neighbors(weights, i)
            
            # 生成子代
            child = crossover_mutation(population, neighbors)
            
            # 更新邻域
            update_neighbors(child, objectives, weights, neighbors)
    
    return population, objectives
```

---

## 三、性能指标

### 3.1 超体积指标
```python
def hypervolume(objectives, reference_point):
    """
    超体积指标
    """
    # 计算Pareto前沿覆盖的体积
    from scipy.spatial import ConvexHull
    
    points = np.vstack([objectives, reference_point])
    hull = ConvexHull(points)
    
    volume = hull.volume
    return volume
```

### 3.2 世代距离
```python
def generational_distance(obtained, true_front):
    """
    世代距离
    """
    distances = []
    
    for point in obtained:
        min_dist = np.min(np.linalg.norm(true_front - point, axis=1))
        distances.append(min_dist)
    
    return np.mean(distances)
```

### 3.3 分布性指标
```python
def spacing(obtained):
    """
    间距指标（分布均匀性）
    """
    distances = []
    
    for i, p1 in enumerate(obtained):
        min_dist = np.inf
        for j, p2 in enumerate(obtained):
            if i != j:
                dist = np.linalg.norm(p1 - p2)
                if dist < min_dist:
                    min_dist = dist
        distances.append(min_dist)
    
    mean_dist = np.mean(distances)
    spacing = np.sqrt(np.mean((distances - mean_dist)**2))
    
    return spacing
```

---

## 四、决策方法

### 4.1 最近理想点法
```python
def nadir_point(objectives):
    """
    计算Nadir点
    """
    return np.max(objectives, axis=0)
```

### 4.2 TOPSIS法
```python
def topsis(objectives, weights):
    """
    TOPSIS决策
    """
    # 归一化
    normalized = objectives / np.linalg.norm(objectives, axis=0)
    
    # 加权
    weighted = normalized * weights
    
    # 理想解和负理想解
    ideal = np.min(weighted, axis=0)
    nadir = np.max(weighted, axis=0)
    
    # 距离计算
    d_ideal = np.linalg.norm(weighted - ideal, axis=1)
    d_nadir = np.linalg.norm(weighted - nadir, axis=1)
    
    # 综合得分
    scores = d_nadir / (d_ideal + d_nadir)
    
    return scores
```

---

## 五、论文写作要点

### 5.1 问题分析框架
1. **问题定义**: 多个目标函数
2. **约束处理**: 约束条件
3. **算法选择**: NSGA-II/MOEA-D
4. **性能评估**: 超体积、世代距离
5. **决策分析**: 选择最终方案
6. **灵敏度分析**: 权重影响

### 5.2 图表规范
- **Pareto前沿图**: 散点图
- **平行坐标图**: 多目标展示
- **收敛曲线**: 迭代 vs 指标
- **决策矩阵**: 方案对比

### 5.3 LaTeX代码
```latex
\begin{equation}
\min F(x) = [f_1(x), f_2(x), \ldots, f_k(x)]
\label{eq:moo}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{pareto_front.pdf}
\caption{Pareto前沿}
\label{fig:pareto}
\end{figure}
```

---

## 六、参考文献

1. Deb K. Multi-Objective Optimization Using Evolutionary Algorithms. Wiley, 2001.
2. Coello C A C. Evolutionary Algorithms for Solving Multi-Objective Problems. Springer, 2007.
3. 郑金华. 多目标进化算法及其应用. 科学出版社, 2007.
4. Miettinen K. Nonlinear Multiobjective Optimization. Springer, 1999.
