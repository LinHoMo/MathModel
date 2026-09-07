# 调度优化建模知识库

> 本文件提供数学建模竞赛中调度优化相关问题的建模知识，包括RGV调度、无人机调度、生产调度等问题。

---

## 1. 问题特征

### 1.1 典型问题描述
- RGV动态调度优化
- 无人机遂行编队飞行
- 生产过程中的决策优化
- 资源分配与调度

### 1.2 常见约束条件
- 时间约束：任务截止时间、处理时间
- 资源约束：设备数量、人员数量
- 顺序约束：任务优先级、依赖关系
- 安全约束：避碰、距离限制

### 1.3 数据特点
- 任务数据：处理时间、到达时间
- 资源数据：数量、能力、位置
- 时间数据：开始时间、结束时间
- 成本数据：加工成本、延迟成本

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 蒙特卡洛模拟 | 不确定性调度 | 处理随机性 | 计算量大 |
| 遗传算法 | 组合优化 | 全局搜索 | 收敛慢 |
| 模拟退火 | NP难问题 | 避免局部最优 | 参数敏感 |
| 贪心算法 | 在线调度 | 快速响应 | 解质量一般 |
| 动态规划 | 序列决策 | 最优解 | 维度灾难 |

---

## 3. 数学基础

### 3.1 调度问题模型

**作业车间调度**：
```
min C_max (makespan)
s.t. 
  C_ij ≥ C_i(j-1) + p_ij  # 工序约束
  C_ij ≥ C_kj + p_kj      # 资源约束
```

**RGV调度模型**：
- 目标：最小化总加工时间或最大化产出
- 约束：RGV移动时间、上下料时间、设备加工时间

### 3.2 无人机调度

**覆盖路径规划**：
```
min Σ d_ij × x_ij
s.t.
  Σ x_ij = 1  # 每个任务被覆盖一次
  Σ x_ij ≤ 1  # 每个位置最多被访问一次
```

### 3.3 生产调度

**流水车间调度**：
```
min Σ C_i (总完成时间)
s.t.
  C_i ≥ r_i  # 释放时间约束
  C_i ≥ C_j + p_i  # 加工顺序约束
```

---

## 4. 代码实现

### 4.1 蒙特卡洛模拟

```python
import numpy as np

def monte_carlo_scheduling(n_simulations, task_times, processing_times, seed=42):
    """
    蒙特卡洛模拟调度
    
    Parameters
    ----------
    n_simulations : int
        模拟次数
    task_times : array
        任务到达时间
    processing_times : array
        处理时间
    
    Returns
    -------
    results : dict
        模拟结果
    """
    np.random.seed(seed)
    
    total_times = []
    completion_times = []
    
    for _ in range(n_simulations):
        # 生成随机任务到达时间
        arrival_times = np.sort(np.random.exponential(5, len(task_times)))
        
        # 简单调度：按到达时间排序
        schedule = np.argsort(arrival_times)
        
        # 计算完成时间
        current_time = 0
        completion = []
        for task_id in schedule:
            start = max(current_time, arrival_times[task_id])
            end = start + processing_times[task_id]
            completion.append(end)
            current_time = end
        
        total_times.append(current_time)
        completion_times.append(completion)
    
    results = {
        'mean_total_time': np.mean(total_times),
        'std_total_time': np.std(total_times),
        'mean_completion': np.mean([np.mean(c) for c in completion_times]),
        'min_total_time': np.min(total_times),
        'max_total_time': np.max(total_times)
    }
    
    return results
```

### 4.2 RGV调度优化

```python
import numpy as np
from scipy.optimize import linear_sum_assignment

def rgv_scheduling(n_stations, processing_times, move_times):
    """
    RGV调度优化（匈牙利算法）
    
    Parameters
    ----------
    n_stations : int
        工位数量
    processing_times : array
        各工位加工时间
    move_times : array
        RGV移动时间矩阵
    
    Returns
    -------
    assignment : dict
        分配结果
    total_time : float
        总加工时间
    """
    # 构建成本矩阵
    cost_matrix = np.zeros((n_stations, n_stations))
    for i in range(n_stations):
        for j in range(n_stations):
            cost_matrix[i, j] = move_times[i, j] + processing_times[j]
    
    # 匈牙利算法
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # 计算总时间
    total_time = cost_matrix[row_ind, col_ind].sum()
    
    assignment = {
        'rgv_to_station': dict(zip(row_ind, col_ind)),
        'total_time': total_time
    }
    
    return assignment
```

### 4.3 遗传算法调度

```python
import numpy as np

def genetic_algorithm_scheduling(n_tasks, processing_times, 
                                precedence_constraints, seed=42):
    """
    遗传算法求解调度问题
    
    Parameters
    ----------
    n_tasks : int
        任务数量
    processing_times : array
        各任务处理时间
    precedence_constraints : list
        优先约束 [(i, j), ...] 表示任务i必须在任务j之前
    seed : int
        随机种子
    
    Returns
    -------
    best_schedule : array
        最优调度
    best_makespan : float
        最小化makespan
    """
    np.random.seed(seed)
    
    # 种群初始化（拓扑排序）
    def random_topological_sort():
        """生成满足优先约束的随机调度"""
        in_degree = np.zeros(n_tasks)
        for i, j in precedence_constraints:
            in_degree[j] += 1
        
        schedule = []
        available = list(np.where(in_degree == 0)[0])
        
        while available:
            # 随机选择
            idx = np.random.randint(len(available))
            task = available.pop(idx)
            schedule.append(task)
            
            # 更新入度
            for i, j in precedence_constraints:
                if i == task:
                    in_degree[j] -= 1
                    if in_degree[j] == 0:
                        available.append(j)
        
        return np.array(schedule)
    
    # 计算makespan
    def calculate_makespan(schedule):
        finish_times = np.zeros(n_tasks)
        for task in schedule:
            # 检查前置任务
            predecessors = [i for i, j in precedence_constraints if j == task]
            if predecessors:
                start_time = max(finish_times[predecessors])
            else:
                start_time = 0
            finish_times[task] = start_time + processing_times[task]
        return np.max(finish_times)
    
    # 遗传算法
    pop_size = 50
    n_generations = 100
    
    # 初始化种群
    population = [random_topological_sort() for _ in range(pop_size)]
    fitness = [calculate_makespan(ind) for ind in population]
    
    best_idx = np.argmin(fitness)
    best_schedule = population[best_idx].copy()
    best_makespan = fitness[best_idx]
    
    for gen in range(n_generations):
        # 选择
        tournament_size = 3
        new_population = []
        
        for _ in range(pop_size):
            candidates = np.random.choice(pop_size, tournament_size, replace=False)
            winner = candidates[np.argmin([fitness[c] for c in candidates])]
            new_population.append(population[winner].copy())
        
        # 交叉（顺序交叉）
        for i in range(0, pop_size, 2):
            if i + 1 < pop_size:
                # 简化：随机交换部分任务
                cut1 = np.random.randint(n_tasks)
                cut2 = np.random.randint(cut1, n_tasks)
                
                child1 = new_population[i].copy()
                child2 = new_population[i+1].copy()
                
                child1[cut1:cut2] = new_population[i+1][cut1:cut2]
                child2[cut1:cut2] = new_population[i][cut1:cut2]
                
                new_population[i] = child1
                new_population[i+1] = child2
        
        # 变异（交换两个任务）
        for i in range(pop_size):
            if np.random.random() < 0.1:
                idx1, idx2 = np.random.choice(n_tasks, 2, replace=False)
                new_population[i][idx1], new_population[i][idx2] = \
                    new_population[i][idx2], new_population[i][idx1]
        
        # 评估
        population = new_population
        fitness = [calculate_makespan(ind) for ind in population]
        
        best_idx = np.argmin(fitness)
        if fitness[best_idx] < best_makespan:
            best_schedule = population[best_idx].copy()
            best_makespan = fitness[best_idx]
    
    return best_schedule, best_makespan
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 忽略移动时间 | 总时间估计偏低 | 包含RGV移动时间 |
| 并发冲突 | 多设备同时访问 | 加入资源约束 |
| 优先约束违反 | 任务顺序错误 | 使用拓扑排序 |
| 指数爆炸 | 问题规模大 | 使用启发式算法 |
| 忽略随机性 | 结果不稳定 | 蒙特卡洛模拟 |

---

## 6. 验证方法

### 6.1 调度可行性
- 检查所有任务是否被分配
- 验证优先约束是否满足
- 检查资源约束是否满足

### 6.2 性能评估
- 与最优解对比（小规模）
- 与贪心算法对比
- 计算理论下界

### 6.3 灵敏度分析
- 改变任务数量，观察性能变化
- 改变处理时间，观察调度变化
- 改变资源数量，观察性能变化

---

## 7. 参考论文

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| B195 | 蒙特卡洛模拟 | 多阶段生产决策 |
| B196 | 蚁群+遗传算法 | 混合优化算法 |
| B203 | 0-1规划 | RGV动态调度 |
| B217 | 蒙特卡洛模拟 | RGV调度模型 |
| B225 | 动态调度策略 | 智能RGV调度 |
| B334 | 调度优化 | RGV调度问题 |

---

## 8. 验证清单

- [ ] 所有任务被分配
- [ ] 优先约束满足
- [ ] 资源约束满足
- [ ] 总时间计算正确
- [ ] 调度可行
- [ ] 灵敏度分析已执行
- [ ] 结果与基准对比
