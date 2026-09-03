# 博弈策略建模知识库

> 本文件提供数学建模竞赛中博弈策略相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 穿越沙漠游戏策略优化
- 多人博弈均衡分析
- 资源配置博弈
- 拍卖机制设计
- 讨价还价策略
- 军事对抗模拟
- 市场竞争定价博弈

### 1.2 常见约束条件
- 资源约束：初始资源、补给限制
- 时间约束：回合数、决策时限
- 信息约束：完全信息/不完全信息、对称/不对称
- 行动约束：可行行动集、行动顺序
- 收益约束：支付函数、风险偏好
- 合作约束：联盟可能性、承诺可信性

### 1.3 数据特点
- 策略空间：可能的行动组合
- 支付矩阵：各策略组合的收益
- 概率分布：不确定性事件
- 历史数据：对手行为记录
- 信息结构：共同知识、私人信息

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 纳什均衡分析 | 静态博弈 | 理论最优 | 均衡可能不唯一 |
| 动态博弈/子博弈完美 | 序贯决策 | 考虑时序 | 计算复杂 |
| 混合策略 | 无纯策略均衡 | 总有解 | 实际执行困难 |
| 随机建模 | 不确定性博弈 | 处理概率 | 模型假设敏感 |
| 决策树分析 | 多阶段决策 | 可视化清晰 | 分支爆炸 |
| 多目标优化 | 多方利益冲突 | Pareto最优 | 解集庞大 |
| 强化学习 | 自适应博弈 | 无需模型 | 训练数据需求 |

---

## 3. 数学基础

### 3.1 博弈论基础

**博弈三要素**：
- 参与人集合: N = {1, 2, ..., n}
- 策略空间: Sᵢ (第i个参与人的策略集)
- 支付函数: uᵢ: S₁×...×Sₙ → ℝ

**标准式博弈**（矩阵博弈）：
```
          玩家2
         策略A  策略B
玩家1 策略A  (3,2)  (1,4)
      策略B  (4,1)  (2,3)
```

### 3.2 纳什均衡

**定义**：策略组合(s₁*,...,sₙ*)是纳什均衡，当且仅当：
```
∀i, ∀sᵢ ∈ Sᵢ: uᵢ(sᵢ*, s₋ᵢ*) ≥ uᵢ(sᵢ, s₋ᵢ*)
```
即：给定其他人的策略，没有人能通过单方面改变策略获益。

**混合策略纳什均衡**：
```
每个参与人i以概率分布 pᵢ = (pᵢ₁, ..., pᵢₘ) 选择策略
期望支付: E[uᵢ] = Σ pᵢ(s) × uᵢ(s)
```

### 3.3 子博弈完美纳什均衡(SPE)

**逆向归纳法**（有限博弈）：
1. 从最后一个决策点开始
2. 在每个决策点选择最优行动
3. 向前推导至起点

**可信威胁**：均衡中使用的策略在每个子博弈中都是最优的

### 3.4 穿越沙漠游戏模型

**问题设定**：
- 玩家从起点到终点，距离D
- 携带资源R，移动消耗c/格
- 可放置资源点，返回补充
- 目标：到达终点时剩余资源最多

**策略建模**：
```
状态: (当前位置, 携带资源, 已放置资源点)
行动: 前进/后退/放置资源
转移: 资源变化 = -移动成本 + 补充(如在资源点)
目标: 最大化到达终点时的资源
```

### 3.5 支付矩阵与均衡求解

**2×2博弈均衡条件**：
```
纯策略均衡: 存在占优策略
混合策略均衡: p₁ = (d-b)/(a-b-c+d)
其中支付矩阵为:
        玩家2
       合作  背叛
玩家1 合作 (a,c) (b,d)
      背叛 (d,b) (c,c)
```

---

## 4. Python实现

### 4.1 纳什均衡求解

```python
import numpy as np
from itertools import product

def find_pure_nash_equilibria(payoff_matrix):
    """
    求解纯策略纳什均衡
    
    Parameters
    ----------
    payoff_matrix : list of list of tuple
        支付矩阵: payoff_matrix[i][j] = (u1, u2)
    
    Returns
    -------
    equilibria : list of tuple
        纳什均衡列表 (i, j)
    """
    n_rows = len(payoff_matrix)
    n_cols = len(payoff_matrix[0])
    
    equilibria = []
    
    for i in range(n_rows):
        for j in range(n_cols):
            # 检查是否为纳什均衡
            is_ne = True
            
            # 玩家1是否有动机偏离
            current_u1 = payoff_matrix[i][j][0]
            for i_prime in range(n_rows):
                if payoff_matrix[i_prime][j][0] > current_u1:
                    is_ne = False
                    break
            
            if not is_ne:
                continue
            
            # 玩家2是否有动机偏离
            current_u2 = payoff_matrix[i][j][1]
            for j_prime in range(n_cols):
                if payoff_matrix[i][j_prime][1] > current_u2:
                    is_ne = False
                    break
            
            if is_ne:
                equilibria.append((i, j))
    
    return equilibria

def find_mixed_nash_equilibrium_2x2(a, b, c, d):
    """
    求解2×2博弈的混合策略纳什均衡
    
    支付矩阵:
            玩家2
           策略1  策略2
    玩家1 策略1  (a,a)  (b,c)
          策略2  (c,b)  (d,d)
    
    Returns
    -------
    p : float
        玩家1选择策略1的概率
    q : float
        玩家2选择策略1的概率
    """
    # 混合策略均衡条件
    # 玩家2无差异: a*p + c*(1-p) = b*p + d*(1-p)
    denom = a - b - c + d
    if abs(denom) < 1e-10:
        return None, None  # 无混合策略均衡
    
    q = (d - b) / denom  # 玩家2的混合策略
    
    # 对称情况
    p = (d - c) / denom  # 玩家1的混合策略
    
    # 检查概率有效性
    if 0 <= p <= 1 and 0 <= q <= 1:
        return p, q
    else:
        return None, None
```

### 4.2 穿越沙漠游戏动态规划

```python
import numpy as np
from functools import lru_cache

class DesertCrossingGame:
    """
    穿越沙漠游戏
    """
    def __init__(self, distance, carry_capacity, move_cost=1):
        """
        Parameters
        ----------
        distance : int
            总距离（格数）
        carry_capacity : int
            最大携带资源
        move_cost : int
            每格移动消耗
        """
        self.D = distance
        self.C = carry_capacity
        self.cost = move_cost
        
        # 状态: (当前位置, 携带资源, 资源点位置集合)
        # 动态规划: dp[pos][res] = 最优策略下的期望收益
    
    def solve_dp(self):
        """
        动态规划求解最优策略
        
        Returns
        -------
        strategy : dict
            最优策略
        max_resource : float
            到达终点的最大资源
        """
        # 简化：只考虑单人，无对手
        # dp[pos][res] = 从(pos, res)出发到达终点的最大剩余资源
        
        dp = {}
        policy = {}
        
        # 终点
        for res in range(self.C + 1):
            dp[(self.D, res)] = res
            policy[(self.D, res)] = 'arrive'
        
        # 逆向递推
        for pos in range(self.D - 1, -1, -1):
            for res in range(self.C + 1):
                best_val = -float('inf')
                best_action = None
                
                # 行动1: 前进
                if res >= self.cost:
                    new_res = res - self.cost
                    val = dp.get((pos + 1, new_res), -float('inf'))
                    if val > best_val:
                        best_val = val
                        best_action = ('forward', new_res)
                
                # 行动2: 放置资源（如果还有足够资源）
                if res >= 2 * self.cost:  # 保证能返回
                    # 放置部分资源
                    place_amount = min(res - self.cost, self.C - res)
                    if place_amount > 0:
                        new_res = res - place_amount
                        # 假设之后能取回
                        val = dp.get((pos, new_res), -float('inf'))
                        if val > best_val:
                            best_val = val
                            best_action = ('place', place_amount)
                
                dp[(pos, res)] = best_val
                policy[(pos, res)] = best_action
        
        return dp, policy
    
    def simulate_game(self, strategy_func, start_resource=None):
        """
        模拟游戏过程
        
        Parameters
        ----------
        strategy_func : callable
            策略函数 strategy_func(pos, res, depots) -> action
        start_resource : int
            初始资源
        
        Returns
        -------
        trajectory : list
            轨迹
        final_resource : int
            最终资源
        """
        if start_resource is None:
            start_resource = self.C
        
        pos = 0
        res = start_resource
        depots = {}  # {位置: 资源量}
        trajectory = [(pos, res, dict(depots))]
        
        while pos < self.D:
            action = strategy_func(pos, res, depots)
            
            if action[0] == 'forward':
                res -= self.cost
                pos += 1
            elif action[0] == 'place':
                amount = action[1]
                depots[pos] = depots.get(pos, 0) + amount
                res -= amount
            elif action[0] == 'pickup':
                if pos in depots:
                    pickup = min(depots[pos], self.C - res)
                    res += pickup
                    depots[pos] -= pickup
                    if depots[pos] == 0:
                        del depots[pos]
            
            trajectory.append((pos, res, dict(depots)))
        
        return trajectory, res
```

### 4.3 多人博弈均衡分析

```python
import numpy as np
from itertools import product

class GameTheory:
    """
    博弈论工具类
    """
    @staticmethod
    def best_response(payoff_matrix, player, opponent_strategy):
        """
        计算最佳响应
        
        Parameters
        ----------
        payoff_matrix : array
            支付矩阵
        player : int
            玩家编号
        opponent_strategy : array
            对手策略分布
        
        Returns
        -------
        best_resp : int
            最佳响应策略
        """
        n_strategies = payoff_matrix.shape[player]
        expected_payoffs = np.zeros(n_strategies)
        
        if player == 0:
            for s in range(n_strategies):
                expected_payoffs[s] = np.dot(
                    payoff_matrix[s, :, 0], opponent_strategy
                )
        else:
            for s in range(n_strategies):
                expected_payoffs[s] = np.dot(
                    payoff_matrix[:, s, 1], opponent_strategy
                )
        
        return np.argmax(expected_payoffs)
    
    @staticmethod
    def iterated_best_response(payoff_matrix, max_iter=100, tol=1e-6):
        """
        迭代最佳响应法求纳什均衡
        
        Returns
        -------
        eq : tuple
            混合策略纳什均衡 (p1, p2)
        """
        n1, n2, _ = payoff_matrix.shape
        
        # 初始化均匀分布
        p1 = np.ones(n1) / n1
        p2 = np.ones(n2) / n2
        
        for _ in range(max_iter):
            # 更新玩家1的最佳响应
            br1 = GameTheory.best_response(payoff_matrix, 0, p2)
            p1_new = np.zeros(n1)
            p1_new[br1] = 1.0
            
            # 更新玩家2的最佳响应
            br2 = GameTheory.best_response(payoff_matrix, 1, p1_new)
            p2_new = np.zeros(n2)
            p2_new[br2] = 1.0
            
            # 检查收敛
            if (np.max(np.abs(p1_new - p1)) < tol and 
                np.max(np.abs(p2_new - p2)) < tol):
                return p1_new, p2_new
            
            p1, p2 = p1_new, p2_new
        
        return p1, p2
    
    @staticmethod
    def monte_carlo_simulation(payoff_matrix, n_simulations=10000):
        """
        蒙特卡洛博弈模拟
        
        Parameters
        ----------
        payoff_matrix : array
            支付矩阵
        n_simulations : int
            模拟次数
        
        Returns
        -------
        avg_payoffs : array
            平均支付
        """
        n1, n2, _ = payoff_matrix.shape
        
        # 随机策略
        p1_dist = np.random.dirichlet(np.ones(n1), n_simulations)
        p2_dist = np.random.dirichlet(np.ones(n2), n_simulations)
        
        payoffs = np.zeros((n_simulations, 2))
        
        for sim in range(n_simulations):
            # 根据分布选择策略
            s1 = np.random.choice(n1, p=p1_dist[sim])
            s2 = np.random.choice(n2, p=p2_dist[sim])
            
            payoffs[sim] = payoff_matrix[s1, s2]
        
        return np.mean(payoffs, axis=0)
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 混淆策略和行动 | 均衡定义错误 | 区分策略(概率分布)和行动(具体选择) |
| 忽略混合策略均衡 | 遗漏均衡 | 检查纯策略均衡后求混合策略 |
| 逆向归纳错误 | SPE求解错误 | 从最后一个决策点开始逆推 |
| 状态空间爆炸 | 计算不可行 | 状态约简、近似方法 |
| 忽略信息结构 | 均衡不适用 | 区分完全/不完全信息博弈 |
| 支付函数错误 | 均衡无意义 | 验证支付函数的单调性 |
| 均衡选择困难 | 多个均衡时无法决策 | 使用风险占优、聚点等精炼标准 |

---

## 6. 验证方法

### 6.1 均衡验证
```
纳什均衡检验: 给定对手策略，任何单方面偏离都不获益
验证: uᵢ(sᵢ*, s₋ᵢ*) ≥ uᵢ(sᵢ, s₋ᵢ*) ∀sᵢ ∈ Sᵢ
```

### 6.2 策略合理性
- 概率分布: Σpᵢ = 1, pᵢ ≥ 0
- 支付单调性: 资源越多越好
- 行动可行性: 在约束范围内

### 6.3 灵敏度分析
- 改变参数（距离、消耗、容量）观察均衡变化
- 改变支付结构观察策略变化

### 6.4 蒙特卡洛验证
- 大量模拟检验策略的期望收益
- 与理论值对比

---

## 7. 真题案例

### 案例1：2020B 穿越沙漠游戏策略

**问题核心**：在资源有限的沙漠中，设计最优穿越策略

**建模要点**：
1. 建立状态空间模型（位置、资源、资源点）
2. 动态规划求解最优策略
3. 考虑对手策略的博弈均衡
4. 多阶段决策优化

**典型解法**：
```
1. 状态定义: (位置, 携带资源, 资源点分布)
2. 行动: 前进/后退/放置资源/拾取资源
3. 转移方程: 资源变化 = -移动成本 ± 补充
4. 动态规划逆推
5. 博弈均衡: 对手干扰时的最优响应
```

**关键结论**：
- 最优策略通常是在中间位置建立资源点
- 资源分配需要平衡前进和返回的需求
- 对手干扰时需要调整策略（防御性策略）

### 案例2：多人资源配置博弈

**问题核心**：多个参与人竞争有限资源

**建模要点**：
1. 支付函数设计
2. 纳什均衡分析
3. 机制设计（激励相容）
4. 社会福利优化

---

## 8. 代码模板参考

- 博弈求解: 自定义实现或 `nashpy` 库
- 动态规划: 自定义实现
- 优化: `scipy.optimize`
- 模拟: `numpy.random`

---

## 9. 验证清单

- [ ] 支付矩阵定义正确
- [ ] 纳什均衡条件满足
- [ ] 混合策略概率和为1
- [ ] 逆向归纳从最后一个决策点开始
- [ ] 状态空间完整（位置、资源、资源点）
- [ ] 行动可行性验证
- [ ] 灵敏度分析已执行
- [ ] 结果与物理直觉一致

---

## 10. 参考文献

1. Osborne M J. An Introduction to Game Theory. Oxford University Press, 2004.
2. Fudenberg D. Game Theory. MIT Press, 1991.
3. 熊义杰. 博弈论及其应用. 科学出版社, 2018.
4. Myerson R B. Game Theory. Harvard University Press, 2013.
