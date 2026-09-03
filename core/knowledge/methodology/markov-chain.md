# 马尔可夫链方法论

> 本文档提供马尔可夫链的完整方法论，包括离散/连续MC、HMM、MDP等核心方法。

---

## 一、方法选择决策树

```
马尔可夫过程分析
├── 状态空间？
│   ├── 有限/可数 → 离散马尔可夫链
│   └── 连续 → 连续时间马尔可夫链
├── 观测？
│   ├── 完全可观测 → 马尔可夫链
│   └── 部分可观测 → 隐马尔可夫模型(HMM)
├── 决策？
│   ├── 无决策 → 马尔可夫链
│   └── 有决策 → 马尔可夫决策过程(MDP)
└── 稳态？
    ├── 需要稳态分布 → 平稳MC
    └── 时变 → 非平稳MC
```

---

## 二、离散时间马尔可夫链

### 2.1 模型原理

**状态转移**：P(Xₙ₊₁|Xₙ,Xₙ₋₁,...,X₀) = P(Xₙ₊₁|Xₙ)

**转移矩阵**：P = [pᵢⱼ]，其中 pᵢⱼ = P(Xₙ₊₁=j|Xₙ=i)

**n步转移**：P⁽ⁿ⁾ = Pⁿ

### 2.2 核心性质

| 性质 | 定义 | 判断方法 |
|------|------|---------|
| 不可约 | 任意两状态可达 | 转移图连通 |
| 周期性 | 返回周期有公因子 | d = gcd{n: pᵢᵢ⁽ⁿ⁾>0} |
| 遍历性 | 不可约+非周期 | d=1 |
| 平稳分布 | πP = π | 求解线性方程组 |

### 2.3 完整代码框架

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import eig

class DiscreteMarkovChain:
    def __init__(self, transition_matrix, state_names=None):
        """
        transition_matrix: 转移概率矩阵
        state_names: 状态名称列表
        """
        self.P = np.array(transition_matrix, dtype=float)
        self.n_states = self.P.shape[0]
        self.state_names = state_names or [f"S{i}" for i in range(self.n_states)]
        
        # 验证行和为1
        row_sums = self.P.sum(axis=1)
        if not np.allclose(row_sums, 1):
            raise ValueError("转移矩阵每行之和必须为1")
    
    def is_irreducible(self):
        """判断是否不可约"""
        # BFS检查连通性
        visited = set()
        queue = [0]
        
        while queue:
            state = queue.pop(0)
            if state in visited:
                continue
            visited.add(state)
            
            for j in range(self.n_states):
                if self.P[state, j] > 0 and j not in visited:
                    queue.append(j)
        
        return len(visited) == self.n_states
    
    def period(self, state=0):
        """计算状态周期"""
        # 找到所有使pᵢᵢ⁽ⁿ⁾>0的n
        n_values = []
        P_power = np.eye(self.n_states)
        
        for n in range(1, self.n_states + 1):
            P_power = P_power @ self.P
            if P_power[state, state] > 0:
                n_values.append(n)
        
        if not n_values:
            return 0
        
        # 计算gcd
        from math import gcd
        from functools import reduce
        return reduce(gcd, n_values)
    
    def is_ergodic(self):
        """判断是否遍历（不可约+非周期）"""
        return self.is_irreducible() and self.period() == 1
    
    def stationary_distribution(self):
        """求解平稳分布"""
        # 求解 πP = π，即 π(P-I) = 0
        A = (self.P.T - np.eye(self.n_states))
        A[-1] = 1  # 添加约束 Σπᵢ = 1
        b = np.zeros(self.n_states)
        b[-1] = 1
        
        try:
            pi = np.linalg.solve(A, b)
            return pi
        except np.linalg.LinAlgError:
            return None
    
    def n_step_transition(self, n):
        """n步转移矩阵"""
        return np.linalg.matrix_power(self.P, n)
    
    def simulate(self, initial_state, n_steps, seed=42):
        """模拟状态序列"""
        np.random.seed(seed)
        
        states = [initial_state]
        current = initial_state
        
        for _ in range(n_steps):
            probs = self.P[current]
            current = np.random.choice(self.n_states, p=probs)
            states.append(current)
        
        return states
    
    def absorption_analysis(self):
        """吸收态分析"""
        # 找吸收态（pᵢᵢ=1的态）
        absorbing = [i for i in range(self.n_states) if self.P[i, i] == 1]
        
        if not absorbing:
            return None
        
        # 重新排列矩阵
        transient = [i for i in range(self.n_states) if i not in absorbing]
        
        # 提取子矩阵
        Q = self.P[np.ix_(transient, transient)]
        R = self.P[np.ix_(transient, absorbing)]
        
        # 基本矩阵 N = (I-Q)⁻¹
        N = np.linalg.inv(np.eye(len(transient)) - Q)
        
        # 吸收概率 B = NR
        B = N @ R
        
        return {
            'absorbing_states': absorbing,
            'transient_states': transient,
            'fundamental_matrix': N,
            'absorption_probabilities': B
        }
    
    def plot_transition_diagram(self, filename='figures/markov_transition.png'):
        """绘制状态转移图"""
        import networkx as nx
        
        G = nx.DiGraph()
        
        for i in range(self.n_states):
            G.add_node(self.state_names[i])
        
        for i in range(self.n_states):
            for j in range(self.n_states):
                if self.P[i, j] > 0:
                    G.add_edge(self.state_names[i], self.state_names[j], 
                              weight=self.P[i, j])
        
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_size=2000, 
                node_color='lightblue', font_size=10, font_weight='bold')
        
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
```

### 2.4 使用示例

```python
# 天气转移矩阵：晴、阴、雨
P = [
    [0.6, 0.3, 0.1],  # 晴
    [0.2, 0.5, 0.3],  # 阴
    [0.1, 0.3, 0.6]   # 雨
]

mc = DiscreteMarkovChain(P, ['晴', '阴', '雨'])

print("是否不可约:", mc.is_irreducible())
print("周期:", mc.period())
print("是否遍历:", mc.is_ergodic())
print("平稳分布:", mc.stationary_distribution())

# 模拟
states = mc.simulate(0, 100)
print("状态序列:", states)
```

---

## 三、隐马尔可夫模型(HMM)

### 3.1 模型原理

**HMM**：状态不可直接观测，只能观测到与状态相关的输出。

**五元组**：(S, V, π, A, B)

- S：状态集合
- V：观测集合
- π：初始状态概率
- A：状态转移矩阵
- B：观测概率矩阵

### 3.2 三个核心问题

| 问题 | 算法 | 用途 |
|------|------|------|
| 评估问题 | 前向算法 | 计算观测序列概率 |
| 解码问题 | Viterbi算法 | 找最可能的状态序列 |
| 学习问题 | Baum-Welch算法 | 估计模型参数 |

### 3.3 完整代码框架

```python
import numpy as np

class HMM:
    def __init__(self, n_states, n_observations):
        self.n_states = n_states
        self.n_observations = n_observations
        
        # 随机初始化参数
        self.pi = np.ones(n_states) / n_states  # 初始概率
        self.A = np.ones((n_states, n_states)) / n_states  # 转移矩阵
        self.B = np.ones((n_states, n_observations)) / n_observations  # 观测概率
    
    def forward(self, observations):
        """前向算法"""
        T = len(observations)
        alpha = np.zeros((T, self.n_states))
        
        # 初始化
        alpha[0] = self.pi * self.B[:, observations[0]]
        
        # 递推
        for t in range(1, T):
            for j in range(self.n_states):
                alpha[t, j] = np.sum(alpha[t-1] * self.A[:, j]) * self.B[j, observations[t]]
        
        # 终止
        return np.sum(alpha[T-1])
    
    def viterbi(self, observations):
        """Viterbi算法"""
        T = len(observations)
        delta = np.zeros((T, self.n_states))
        psi = np.zeros((T, self.n_states), dtype=int)
        
        # 初始化
        delta[0] = self.pi * self.B[:, observations[0]]
        
        # 递推
        for t in range(1, T):
            for j in range(self.n_states):
                temp = delta[t-1] * self.A[:, j]
                psi[t, j] = np.argmax(temp)
                delta[t, j] = temp[psi[t, j]] * self.B[j, observations[t]]
        
        # 回溯
        states = np.zeros(T, dtype=int)
        states[T-1] = np.argmax(delta[T-1])
        
        for t in range(T-2, -1, -1):
            states[t] = psi[t+1, states[t+1]]
        
        return states, delta[T-1, states[T-1]]
    
    def baum_welch(self, observations, n_iter=100):
        """Baum-Welch算法（EM）"""
        T = len(observations)
        
        for _ in range(n_iter):
            # E步：前向-后向算法
            alpha = np.zeros((T, self.n_states))
            beta = np.zeros((T, self.n_states))
            
            # 前向
            alpha[0] = self.pi * self.B[:, observations[0]]
            for t in range(1, T):
                for j in range(self.n_states):
                    alpha[t, j] = np.sum(alpha[t-1] * self.A[:, j]) * self.B[j, observations[t]]
            
            # 后向
            beta[T-1] = 1
            for t in range(T-2, -1, -1):
                for i in range(self.n_states):
                    beta[t, i] = np.sum(self.A[i, :] * self.B[:, observations[t+1]] * beta[t+1])
            
            # 计算gamma和xi
            gamma = alpha * beta
            gamma = gamma / gamma.sum(axis=1, keepdims=True)
            
            # M步：更新参数
            self.pi = gamma[0]
            
            for i in range(self.n_states):
                for j in range(self.n_states):
                    xi_sum = np.sum(alpha[:-1, i] * self.A[i, j] * 
                                   self.B[j, observations[1:]] * beta[1:, j])
                    self.A[i, j] = xi_sum / np.sum(gamma[:-1, i])
            
            for j in range(self.n_states):
                for k in range(self.n_observations):
                    mask = (observations == k)
                    self.B[j, k] = np.sum(gamma[mask, j]) / np.sum(gamma[:, j])
            
            # 归一化
            self.A = self.A / self.A.sum(axis=1, keepdims=True)
            self.B = self.B / self.B.sum(axis=1, keepdims=True)
```

---

## 四、马尔可夫决策过程(MDP)

### 4.1 模型原理

**MDP**：在马尔可夫链基础上加入决策，寻找最优策略。

**五元组**：(S, A, P, R, γ)

- S：状态集合
- A：动作集合
- P：转移概率 P(s'|s,a)
- R：奖励函数 R(s,a,s')
- γ：折扣因子

### 4.2 核心算法

**值迭代**：

```python
def value_iteration(P, R, gamma=0.9, theta=1e-6):
    """
    值迭代算法
    P: 转移概率 P[s,a,s']
    R: 奖励函数 R[s,a,s']
    gamma: 折扣因子
    """
    n_states, n_actions = R.shape[:2]
    V = np.zeros(n_states)
    
    while True:
        V_new = np.zeros(n_states)
        
        for s in range(n_states):
            q_values = []
            for a in range(n_actions):
                q = sum(P[s, a, s_next] * (R[s, a, s_next] + gamma * V[s_next])
                       for s_next in range(n_states))
                q_values.append(q)
            V_new[s] = max(q_values)
        
        if np.max(np.abs(V_new - V)) < theta:
            break
        V = V_new
    
    # 提取最优策略
    policy = np.zeros(n_states, dtype=int)
    for s in range(n_states):
        q_values = []
        for a in range(n_actions):
            q = sum(P[s, a, s_next] * (R[s, a, s_next] + gamma * V[s_next])
                   for s_next in range(n_states))
            q_values.append(q)
        policy[s] = np.argmax(q_values)
    
    return V, policy
```

**策略迭代**：

```python
def policy_iteration(P, R, gamma=0.9):
    """策略迭代算法"""
    n_states, n_actions = R.shape[:2]
    policy = np.zeros(n_states, dtype=int)
    
    while True:
        # 策略评估
        V = np.zeros(n_states)
        while True:
            V_new = np.zeros(n_states)
            for s in range(n_states):
                a = policy[s]
                V_new[s] = sum(P[s, a, s_next] * (R[s, a, s_next] + gamma * V[s_next])
                              for s_next in range(n_states))
            if np.max(np.abs(V_new - V)) < 1e-6:
                break
            V = V_new
        
        # 策略改进
        new_policy = np.zeros(n_states, dtype=int)
        for s in range(n_states):
            q_values = []
            for a in range(n_actions):
                q = sum(P[s, a, s_next] * (R[s, a, s_next] + gamma * V[s_next])
                       for s_next in range(n_states))
                q_values.append(q)
            new_policy[s] = np.argmax(q_values)
        
        if np.array_equal(policy, new_policy):
            break
        policy = new_policy
    
    return V, policy
```

---

## 五、竞赛常见场景

### 5.1 预测类

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 天气预测 | 离散MC | A070, A147 |
| 股价趋势 | HMM | C305 |
| 交通流量预测 | MC + 回归 | A022, A171 |

### 5.2 决策类

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 设备维护策略 | MDP | B203 |
| 库存管理 | MDP + Q-learning | B195 |
| 投资组合 | HMM + MDP | C142 |

### 5.3 分析类

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 客户状态转移 | MC | C008, C052 |
| 页面排名 | MC（PageRank） | C101 |
| 语音识别 | HMM | D033 |

---

## 六、参考资源

### 6.1 教材推荐

- 《随机过程》（汪荣鑫）
- 《马尔可夫决策过程》（Cputerman）
- 《Pattern Recognition and Machine Learning》（Bishop）

### 6.2 Python库

- hmmlearn：HMM实现
- pymdptoolbox：MDP工具箱
- pomegranate：概率图模型

### 6.3 检查清单

- [ ] 转移矩阵行和为1
- [ ] 平稳分布存在且唯一
- [ ] HMM参数估计收敛
- [ ] MDP折扣因子0<γ<1
- [ ] 策略迭代收敛
