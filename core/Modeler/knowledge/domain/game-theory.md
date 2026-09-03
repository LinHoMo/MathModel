# 博弈论与策略优化领域知识

## 一、核心概念

### 1.1 博弈论基础
- **参与者 (Player)**: 决策主体
- **策略 (Strategy)**: 行动方案
- **收益 (Payoff)**: 博弈结果
- **信息 (Information)**: 参与者知道什么

### 1.2 博弈类型
| 类型 | 特点 | 应用 |
|------|------|------|
| 合作博弈 | 可签订约束协议 | 联盟、合并 |
| 非合作博弈 | 独立决策 | 竞争、拍卖 |
| 完全信息博弈 | 知道所有收益 | 囚徒困境 |
| 不完全信息博弈 | 不完全知道 | 拍牌、竞标 |

### 1.3 均衡概念
- **纳什均衡**: 没有参与者能通过单方面改变策略获益
- **子博弈完美纳什均衡**: 每个子博弈都是纳什均衡
- **贝叶斯纳什均衡**: 不完全信息下的均衡

---

## 二、经典博弈模型

### 2.1 囚徒困境
```
              合作    背叛
合作        (-1,-1)  (-3,0)
背叛        (0,-3)   (-2,-2)
```
**结论**: 个体理性导致集体非最优

### 2.2 智猪博弈
```
              按按钮    等待
大猪        (5,1)     (4,4)
小猪        (9,-1)    (0,0)
```
**结论**: 小猪等待是占优策略

### 2.3 猎鹿博弈
```
              追鹿    追兔
追鹿        (4,4)    (0,3)
追兔        (3,0)    (3,3)
```
**结论**: 存在多个纳什均衡

### 2.4 性别战
```
              足球    芭蕾
男          (3,2)    (0,0)
女          (0,0)    (2,3)
```
**结论**: 需要协调机制

---

## 三、求解方法

### 3.1 划线法（纯策略）
```python
def find_nash_equilibrium(payoff_matrix):
    """
    寻找纯策略纳什均衡
    """
    n_strategies = len(payoff_matrix)
    best_responses = []
    for j in range(n_strategies):
        col_max = max(payoff_matrix[i][j] for i in range(n_strategies))
        best_responses.append(col_max)
    equilibria = []
    for i in range(n_strategies):
        for j in range(n_strategies):
            if (payoff_matrix[i][j][0] == best_responses[j] and 
                payoff_matrix[i][j][1] == best_responses[i]):
                equilibria.append((i, j))
    return equilibria
```

### 3.2 混合策略
```python
def mixed_strategy_nash_2x2(payoff_matrix):
    """
    计算2x2混合策略纳什均衡
    """
    a = payoff_matrix[0][0][0]
    b = payoff_matrix[0][1][0]
    c = payoff_matrix[1][0][0]
    d = payoff_matrix[1][1][0]
    e = payoff_matrix[0][0][1]
    f = payoff_matrix[0][1][1]
    g = payoff_matrix[1][0][1]
    h = payoff_matrix[1][1][1]
    p = (h - f) / (a - b - c + d)
    q = (d - b) / (a - c - b + d)
    return p, q
```

### 3.3 动态博弈（逆向归纳）
```python
def backward_induction(payoff_matrix, stages):
    """
    逆向归纳法求解动态博弈
    """
    n_players = len(payoff_matrix)
    value = payoff_matrix.copy()
    for stage in range(stages - 1, -1, -1):
        for state in range(len(value)):
            value[state] = max(value[state])
    return value[0]
```

---

## 四、沙漠穿越博弈

### 4.1 问题描述
- 多人合作穿越沙漠
- 资源有限，需要分配
- 合作可以提高整体收益

### 4.2 建模方法
**合作博弈**:
```
v(S) = f(S)  # 联盟S的总收益
```

**分配方案**:
- **Shapley值**: 每个参与者的边际贡献
- **核仁**: 最小化最大不满

### 4.3 Shapley值计算
```python
def shapley_value(v, players):
    """
    计算Shapley值
    v: 特征函数
    players: 参与者集合
    """
    from itertools import permutations
    n = len(players)
    shapley = {p: 0 for p in players}
    
    for perm in permutations(players):
        coalition = set()
        for player in perm:
            prev_value = v(coalition)
            coalition.add(player)
            marginal = v(coalition) - prev_value
            shapley[player] += marginal
    
    for p in players:
        shapley[p] /= n
    
    return shapley
```

### 4.4 沙漠穿越模型
```python
def desert_crossing_model(n_players, water_supplies, survival_days):
    """
    沙漠穿越博弈模型
    n_players: 参与人数
    water_supplies: 每人携带水量
    survival_days: 每人每天需水量
    """
    def value_function(coalition):
        total_water = sum(water_supplies[p] for p in coalition)
        total_need = len(coalition) * survival_days
        return min(total_water / total_need, 1.0)
    
    players = list(range(n_players))
    shapley = shapley_value(value_function, players)
    
    return shapley
```

---

## 五、协同巡逻博弈

### 5.1 问题描述
- 多架无人机协同巡逻
- 资源有限，需要分配区域
- 目标是最大化覆盖

### 5.2 建模方法
**非合作博弈**:
- 每架无人机独立决策
- 收益取决于覆盖范围

**合作博弈**:
- 联合决策
- 共享信息

### 5.3 均衡分析
```python
def patrol_game_equilibrium(drones, areas, costs):
    """
    巡逻博弈均衡分析
    drones: 无人机数量
    areas: 区域数量
    costs: 巡逻成本
    """
    n_drones = len(drones)
    n_areas = len(areas)
    
    # 构造收益矩阵
    payoff = np.zeros((n_areas, n_areas))
    for i in range(n_areas):
        for j in range(n_areas):
            payoff[i][j] = coverage(i, j) - costs[i] - costs[j]
    
    return find_nash_equilibrium(payoff)
```

---

## 六、论文写作要点

### 6.1 问题分析框架
1. **参与者识别**: 谁参与博弈
2. **策略空间**: 可选行动
3. **收益函数**: 结果评估
4. **均衡分析**: 预测行为
5. **机制设计**: 改进结果

### 6.2 图表规范
- **收益矩阵**: 表格形式
- **博弈树**: 树形图
- **均衡结果**: 标注
- **敏感性分析**: 参数影响

### 6.3 LaTeX代码
```latex
% 收益矩阵
\begin{table}[htbp]
\centering
\caption{博弈收益矩阵}
\begin{tabular}{c|cc}
\hline
& 策略A & 策略B \\
\hline
策略A & (3,2) & (0,0) \\
策略B & (0,0) & (2,3) \\
\hline
\end{tabular}
\end{table}

% 博弈树
\begin{figure}[htbp]
\centering
\includegraphics[width=0.6\textwidth]{game_tree.pdf}
\caption{动态博弈树}
\label{fig:game_tree}
\end{figure}
```

---

## 七、参考文献

1. 约翰纳什. 非合作博弈. 1950.
2. 张维迎. 博弈论与信息经济学. 上海人民出版社, 2004.
3. Osborne M J. An Introduction to Game Theory. Oxford University Press, 2004.
4. Fudenberg D. The Theory of Game Theory. MIT Press, 1991.
