# 博弈论方法论

> 本文档提供博弈论的完整方法论，包括Nash均衡、合作博弈等核心方法。

---

## 一、方法选择决策树

```
博弈论分析
├── 参与人关系？
│   ├── 非合作博弈 → Nash均衡分析
│   │   ├── 完全信息 → 静态/动态博弈
│   │   └── 不完全信息 → 贝叶斯博弈
│   └── 合作博弈 → Shapley值/核心
├── 策略类型？
│   ├── 纯策略 → 最优反应法
│   └── 混合策略 → 概率分布
├── 博弈次数？
│   ├── 单次 → 静态博弈
│   └── 重复 → 重复博弈/触发策略
└── 均衡求解？
    ├── 有限策略 → 最优反应/ iterated删除劣策略
    └── 连续策略 → 求解方程组
```

---

## 二、Nash均衡

### 2.1 静态博弈

**定义**：每个参与人的策略都是对其他参与人策略的最优反应。

**纯策略Nash均衡**：s* = (s₁*, s₂*, ..., sₙ*)，其中 uᵢ(sᵢ*, s₋ᵢ*) ≥ uᵢ(sᵢ, s₋ᵢ*)

### 2.2 完整代码框架

```python
import numpy as np
from itertools import product

class NormalFormGame:
    def __init__(self, players, payoffs):
        """
        players: 参与人数量
        payoffs: 收益函数列表，每个元素是n维数组
        """
        self.players = players
        self.payoffs = payoffs
        self.n_strategies = [payoffs[0].shape[i] for i in range(players)]
    
    def best_response(self, player, other_strategies):
        """计算最优反应"""
        n_actions = self.n_strategies[player]
        utilities = np.zeros(n_actions)
        
        for action in range(n_actions):
            strategies = list(other_strategies)
            strategies.insert(player, action)
            strategies = tuple(strategies)
            utilities[action] = self.payoffs[player][strategies]
        
        return np.argmax(utilities)
    
    def find_pure_nash(self):
        """寻找纯策略Nash均衡"""
        equilibria = []
        
        # 遍历所有策略组合
        all_strategies = product(*[range(n) for n in self.n_strategies])
        
        for strategies in all_strategies:
            is_nash = True
            
            for player in range(self.players):
                other = list(strategies)
                other.pop(player)
                other = tuple(other)
                
                best = self.best_response(player, other)
                if strategies[player] != best:
                    is_nash = False
                    break
            
            if is_nash:
                equilibria.append(strategies)
        
        return equilibria
    
    def is_dominated(self, player, strategy1, strategy2):
        """检查strategy1是否被strategy2严格劣策略"""
        n其他玩家策略 = np.prod([self.n_strategies[i] for i in range(self.players) if i != player])
        
        dominated = True
        for other_strategies in product(*[range(self.n_strategies[i]) 
                                          for i in range(self.players) if i != player]):
            strategies1 = list(other_strategies)
            strategies1.insert(player, strategy1)
            strategies1 = tuple(strategies1)
            
            strategies2 = list(other_strategies)
            strategies2.insert(player, strategy2)
            strategies2 = tuple(strategies2)
            
            if self.payoffs[player][strategies1] >= self.payoffs[player][strategies2]:
                dominated = False
                break
        
        return dominated
    
    def iterated_dominance(self):
        """迭代删除劣策略"""
        remaining = [list(range(n)) for n in self.n_strategies]
        
        changed = True
        while changed:
            changed = False
            
            for player in range(self.players):
                to_remove = []
                
                for s1 in remaining[player]:
                    for s2 in remaining[player]:
                        if s1 != s2:
                            # 检查s1是否被s2劣
                            dominated = True
                            other_combos = product(*[remaining[i] for i in range(self.players) if i != player])
                            
                            for other in other_combos:
                                strats1 = list(other)
                                strats1.insert(player, s1)
                                strats1 = tuple(strats1)
                                
                                strats2 = list(other)
                                strats2.insert(player, s2)
                                strats2 = tuple(strats2)
                                
                                if self.payoffs[player][strats1] >= self.payoffs[player][strats2]:
                                    dominated = False
                                    break
                            
                            if dominated and s1 not in to_remove:
                                to_remove.append(s1)
                                changed = True
                
                for s in to_remove:
                    remaining[player].remove(s)
        
        return remaining
```

### 2.3 混合策略Nash均衡

```python
def mixed_strategy_nash_2p(payoff_matrix_1, payoff_matrix_2):
    """
    两人博弈的混合策略Nash均衡
    """
    # 假设参与人1有m个策略，参与人2有n个策略
    m, n = payoff_matrix_1.shape
    
    # 参与人1的混合策略（使参与人2无差异）
    # 参与人2在各纯策略的收益相等
    A = payoff_matrix_2.T  # 参与人2的收益矩阵转置
    b = np.ones(n)
    
    try:
        p = np.linalg.lstsq(A, b, rcond=None)[0]
        p = p / p.sum()  # 归一化
    except:
        p = np.ones(m) / m
    
    # 参与人2的混合策略（使参与人1无差异）
    A = payoff_matrix_1
    b = np.ones(m)
    
    try:
        q = np.linalg.lstsq(A, b, rcond=None)[0]
        q = q / q.sum()
    except:
        q = np.ones(n) / n
    
    return p, q
```

---

## 三、合作博弈

### 3.1 Shapley值

**定义**：公平分配合作收益的唯一解。

**公式**：φᵢ(v) = Σ (|S|!(n-|S|-1)!/n!) × [v(S∪{i}) - v(S)]

```python
from itertools import combinations
from math import factorial

def shapley_value(characteristic_function, n_players):
    """
    计算Shapley值
    characteristic_function: 特征函数 v(S)，S为参与人集合
    n_players: 参与人数量
    """
    shapley = np.zeros(n_players)
    
    for player in range(n_players):
        for size in range(n_players):
            for coalition in combinations(range(n_players), size):
                if player in coalition:
                    continue
                
                coalition_with = tuple(sorted(coalition + (player,)))
                
                marginal = (characteristic_function(coalition_with) - 
                           characteristic_function(coalition))
                
                weight = (factorial(size) * factorial(n_players - size - 1) / 
                         factorial(n_players))
                
                shapley[player] += weight * marginal
    
    return shapley
```

### 3.2 核心(Core)

**定义**：没有联盟有动机脱离的分配方案。

```python
def core(characteristic_function, n_players):
    """计算核心（简化版）"""
    from scipy.optimize import linprog
    
    # 所有可能的联盟
    coalitions = []
    for size in range(2, n_players):
        for c in combinations(range(n_players), size):
            coalitions.append(c)
    
    # 约束：每个联盟的分配之和 >= 特征函数值
    A_ub = []
    b_ub = []
    
    for coalition in coalitions:
        row = np.zeros(n_players)
        for p in coalition:
            row[p] = -1
        A_ub.append(row)
        b_ub.append(-characteristic_function(coalition))
    
    # 约束：所有参与人分配之和 = v(N)
    A_eq = np.ones((1, n_players))
    b_eq = [characteristic_function(tuple(range(n_players)))]
    
    # 目标函数（任意）
    c = np.zeros(n_players)
    
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                    bounds=[(0, None)] * n_players)
    
    return result
```

---

## 四、动态博弈

### 4.1 逆向归纳法

```python
class ExtensiveFormGame:
    def __init__(self):
        self.tree = {}
    
    def add_node(self, node_id, player, actions, payoffs=None):
        self.tree[node_id] = {
            'player': player,
            'actions': actions,
            'payoffs': payoffs
        }
    
    def backward_induction(self):
        """逆向归纳法"""
        # 从叶节点向上推导
        values = {}
        
        for node_id, node in reversed(self.tree.items()):
            if node['payoffs'] is not None:
                values[node_id] = node['payoffs']
            else:
                # 选择最优行动
                best_action = None
                best_value = float('-inf')
                
                for action, child_id in node['actions'].items():
                    if child_id in values:
                        if node['player'] == 0:  # 参与人1最大化
                            if values[child_id][0] > best_value:
                                best_value = values[child_id][0]
                                best_action = action
                        else:  # 参与人2最小化（或最大化自己的收益）
                            if values[child_id][1] > best_value:
                                best_value = values[child_id][1]
                                best_action = action
                
                values[node_id] = values.get(node['actions'][best_action])
        
        return values
```

### 4.2 重复博弈

```python
def folk_theorem_payoff(stage_game_nash, min_individual, max_total, n_players):
    """
    无名氏定理：重复博弈的可行收益集
    """
    # 可行收益集是凸包
    # 最小最大惩罚收益
    minmax = [min_individual] * n_players
    
    # 所有可行收益
    feasible = []
    
    # 阶段博弈Nash均衡收益
    feasible.append(stage_game_nash)
    
    # 添加其他可行收益（通过相关策略）
    # ...
    
    return feasible
```

---

## 五、竞赛常见场景

### 5.1 定价博弈

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 寡头定价 | Cournot/Bertrand模型 | C142, C305 |
| 动态定价 | 重复博弈 | B195, B196 |
| 拍卖设计 | 拍卖博弈 | C227 |

### 5.2 资源分配

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 网络资源分配 | 博弈论+优化 | C101 |
| 供应链协调 | 合作博弈 | B195 |
| 公共资源管理 | 公地悲剧博弈 | D034 |

### 5.3 竞争分析

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 市场竞争 | Nash均衡 | C008, C052 |
| 技术标准竞争 | 动态博弈 | D017 |
| 军事对抗 | 博弈树分析 | A001, A022 |

---

## 六、参考资源

### 6.1 教材推荐

- 《博弈论基础》（罗伯特·吉本斯）
- 《博弈论》（奥斯本）
- 《合作博弈理论》（姚国庆）

### 6.2 Python库

- nashpy：Nash均衡计算
- gambit：博弈论工具箱
- axelrod：重复博弈模拟

### 6.3 检查清单

- [ ] 收益矩阵正确
- [ ] Nash均衡验证通过
- [ ] Shapley值满足有效性
- [ ] 核心约束满足
- [ ] 动态博弈时序正确
