# 动态规划领域知识

## 一、核心概念

### 1.1 动态规划定义
- **定义**: 将复杂问题分解为重叠子问题，自底向上求解
- **核心思想**: 最优子结构 + 重叠子问题
- **适用条件**: 无后效性、最优子结构

### 1.2 基本要素
- **状态**: 问题的阶段特征
- **决策**: 每个状态的选择
- **状态转移方程**: 状态间的关系
- **边界条件**: 初始/终止条件

### 1.3 求解步骤
```
1. 定义状态
2. 写出状态转移方程
3. 确定边界条件
4. 确定计算顺序
5. 回溯求解
```

---

## 二、经典问题

### 2.1 背包问题
```python
def knapsack_dp(weights, values, capacity):
    """
    0-1背包问题
    """
    n = len(weights)
    dp = np.zeros((n + 1, capacity + 1))
    
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i-1][w], 
                              dp[i-1][w-weights[i-1]] + values[i-1])
            else:
                dp[i][w] = dp[i-1][w]
    
    return dp[n][capacity]
```

### 2.2 最长公共子序列
```python
def lcs_length(X, Y):
    """
    最长公共子序列
    """
    m, n = len(X), len(Y)
    dp = np.zeros((m + 1, n + 1))
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if X[i-1] == Y[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]
```

### 2.3 最短路径
```python
def shortest_path_dp(graph, start, end):
    """
    动态规划求最短路径
    """
    n = len(graph)
    dist = np.full(n, np.inf)
    dist[start] = 0
    prev = np.full(n, -1)
    
    # Bellman-Ford算法
    for _ in range(n - 1):
        for u in range(n):
            for v in range(n):
                if graph[u][v] < np.inf:
                    if dist[u] + graph[u][v] < dist[v]:
                        dist[v] = dist[u] + graph[u][v]
                        prev[v] = u
    
    # 路径重建
    path = []
    current = end
    while current != -1:
        path.append(current)
        current = prev[current]
    
    return dist[end], path[::-1]
```

---

## 三、资源分配问题

### 3.1 生产调度
```python
def production_scheduling(demands, capacities, costs):
    """
    生产调度动态规划
    """
    n_periods = len(demands)
    max_inventory = sum(demands)
    
    # 状态: 库存水平
    # 决策: 生产量
    dp = np.full((n_periods + 1, max_inventory + 1), np.inf)
    dp[0][0] = 0
    policy = np.zeros((n_periods, max_inventory + 1), dtype=int)
    
    for t in range(n_periods):
        for inv in range(max_inventory + 1):
            if dp[t][inv] < np.inf:
                # 生产量范围
                min_prod = max(0, demands[t] - inv)
                max_prod = min(capacities[t], max_inventory - inv + demands[t])
                
                for prod in range(min_prod, max_prod + 1):
                    new_inv = inv + prod - demands[t]
                    cost = costs[t] * prod
                    if dp[t+1][new_inv] > dp[t][inv] + cost:
                        dp[t+1][new_inv] = dp[t][inv] + cost
                        policy[t][inv] = prod
    
    return dp[n_periods][0], policy
```

### 3.2 设备更新
```python
def equipment_replacement(age, costs, revenues, max_age):
    """
    设备更新动态规划
    """
    n_years = len(revenues)
    
    # 状态: 设备年龄
    # 决策: 保留/更换
    dp = np.zeros((n_years + 1, max_age + 1))
    policy = np.zeros((n_years, max_age + 1), dtype=int)
    
    for t in range(n_years - 1, -1, -1):
        for age in range(max_age + 1):
            # 保留
            keep_value = revenues[t] - costs[t][age] + dp[t+1][min(age+1, max_age)]
            
            # 更换
            replace_value = revenues[t] - costs[t][0] + dp[t+1][1]
            
            if keep_value > replace_value:
                dp[t][age] = keep_value
                policy[t][age] = 0  # 保留
            else:
                dp[t][age] = replace_value
                policy[t][age] = 1  # 更换
    
    return dp[0][0], policy
```

---

## 四、多阶段决策

### 4.1 逆向归纳
```python
def backward_induction(stages, transition, reward):
    """
    逆向归纳法
    """
    n_states = len(transition[0])
    V = np.zeros((stages + 1, n_states))
    policy = np.zeros((stages, n_states), dtype=int)
    
    # 逆向计算
    for t in range(stages - 1, -1, -1):
        for s in range(n_states):
            best_value = -np.inf
            best_action = 0
            
            for a in range(len(transition[t][s])):
                next_s = transition[t][s][a]
                value = reward[t][s][a] + V[t+1][next_s]
                
                if value > best_value:
                    best_value = value
                    best_action = a
            
            V[t][s] = best_value
            policy[t][s] = best_action
    
    return V[0][0], policy
```

### 4.2 随机动态规划
```python
def stochastic_dp(transitions, rewards, probabilities):
    """
    随机动态规划
    """
    n_states = len(transitions[0])
    V = np.zeros(n_states)
    
    for _ in range(max_iter):
        V_new = np.zeros(n_states)
        
        for s in range(n_states):
            best_value = -np.inf
            
            for a in range(len(transitions[s])):
                expected = sum(probabilities[s][a][next_s] * 
                              (rewards[s][a][next_s] + V[next_s])
                              for next_s in range(n_states))
                
                if expected > best_value:
                    best_value = expected
            
            V_new[s] = best_value
        
        if np.max(np.abs(V_new - V)) < tol:
            break
        V = V_new
    
    return V
```

---

## 五、论文写作要点

### 5.1 问题分析框架
1. **阶段划分**: 确定决策阶段
2. **状态定义**: 描述阶段特征
3. **决策变量**: 每个阶段的选择
4. **状态转移**: 阶段间关系
5. **目标函数**: 累积收益/成本
6. **求解方法**: 表格法/递归

### 5.2 图表规范
- **状态转移图**: 节点+箭头
- **DP表格**: 阶段×状态
- **最优路径**: 高亮显示
- **价值函数图**: 状态-价值

### 5.3 LaTeX代码
```latex
\begin{equation}
V_t(s) = \max_{a \in A(s)} \{r_t(s,a) + V_{t+1}(s')\}
\label{eq:dp}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{dp_table.pdf}
\caption{动态规划表格}
\label{fig:dp}
\end{figure}
```

---

## 六、参考文献

1. Bellman R E. Dynamic Programming. Princeton University Press, 1957.
2. Bertsekas D P. Dynamic Programming and Optimal Control. Athena Scientific, 2012.
3. 刘德铭. 动态规划. 科学出版社, 2005.
4. Puterman M L. Markov Decision Processes. Wiley, 1994.
