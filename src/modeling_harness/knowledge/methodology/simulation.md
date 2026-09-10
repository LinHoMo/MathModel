# 仿真方法方法论

> 本文件提供数学建模竞赛中常用的仿真方法知识，包括算法选择、实现要点、防错策略和验证方法。

---

## 1. 方法选择决策树

```
仿真问题类型识别：
├── 连续系统仿真
│   ├── 确定性 → ODE/PDE数值解
│   └── 随机性 → 蒙特卡洛仿真
├── 离散事件仿真
│   ├── 排队系统 → SimPy
│   ├── 生产系统 → 离散事件仿真
│   └── 交通流 → 元胞自动机
├── Agent-Based仿真
│   ├── 社会系统 → Mesa
│   ├── 生态系统 → NetLogo
│   └── 经济系统 → ABM框架
└── 混合仿真
    └── 连续+离散 → 混合建模
```

---

## 2. 核心方法详解

### 2.1 蒙特卡洛仿真

**方法原理**：
通过大量随机抽样模拟随机过程，用统计方法估计目标量。

**适用场景**：
- 风险评估
- 概率估计
- 积分计算
- 不确定性分析

**代码框架**：
```python
import numpy as np

def monte_carlo_integration(func, a, b, n_samples=100000):
    """蒙特卡洛积分"""
    samples = np.random.uniform(a, b, n_samples)
    values = func(samples)
    integral = (b - a) * np.mean(values)
    std_error = (b - a) * np.std(values) / np.sqrt(n_samples)
    return integral, std_error

def monte_carlo_simulation(n_simulations=10000, seed=42):
    """蒙特卡洛仿真示例：项目风险评估"""
    np.random.seed(seed)
    
    # 参数分布
    cost_mean, cost_std = 100, 20
    revenue_mean, revenue_std = 150, 30
    time_mean, time_std = 12, 2
    
    results = []
    for _ in range(n_simulations):
        cost = np.random.normal(cost_mean, cost_std)
        revenue = np.random.normal(revenue_mean, revenue_std)
        time = np.random.normal(time_mean, time_std)
        
        profit = revenue - cost
        roi = profit / cost * 100
        
        results.append({
            'profit': profit,
            'roi': roi,
            'time': time
        })
    
    profits = [r['profit'] for r in results]
    
    # 统计分析
    mean_profit = np.mean(profits)
    std_profit = np.std(profits)
    prob_loss = np.mean(np.array(profits) < 0)
    
    print(f"平均利润: {mean_profit:.2f}")
    print(f"利润标准差: {std_profit:.2f}")
    print(f"亏损概率: {prob_loss:.2%}")
    print(f"95%置信区间: [{np.percentile(profits, 2.5):.2f}, "
          f"{np.percentile(profits, 97.5):.2f}]")
    
    return results

results = monte_carlo_simulation()
```

---

### 2.2 离散事件仿真 (Discrete Event Simulation)

**方法原理**：
模拟系统中事件的发生和处理，事件按时间顺序执行，改变系统状态。

**适用场景**：
- 排队系统（银行、医院）
- 生产调度
- 物流配送
- 网络通信

**代码框架（使用SimPy）**：
```python
import simpy
import numpy as np

class QueueSystem:
    def __init__(self, env, n_servers, service_time_mean):
        self.env = env
        self.servers = simpy.Resource(env, capacity=n_servers)
        self.service_time_mean = service_time_mean
        self.wait_times = []
        self.system_times = []
    
    def customer(self, name, arrival_time):
        with self.servers.request() as req:
            yield req
            
            wait_time = self.env.now - arrival_time
            self.wait_times.append(wait_time)
            
            service_time = np.random.exponential(self.service_time_mean)
            yield self.env.timeout(service_time)
            
            system_time = self.env.now - arrival_time
            self.system_times.append(system_time)
    
    def run(self, n_customers, arrival_rate):
        for i in range(n_customers):
            arrival_time = np.random.exponential(1.0 / arrival_rate)
            yield self.env.timeout(arrival_time)
            self.env.process(self.customer(i, self.env.now))

def simulate_queue(n_servers=2, service_time_mean=5, arrival_rate=0.3,
                   n_customers=100, n_replications=10):
    """排队系统仿真"""
    all_wait_times = []
    all_system_times = []
    
    for rep in range(n_replications):
        env = simpy.Environment()
        system = QueueSystem(env, n_servers, service_time_mean)
        env.process(system.run(n_customers, arrival_rate))
        env.run()
        
        all_wait_times.append(np.mean(system.wait_times))
        all_system_times.append(np.mean(system.system_times))
    
    print(f"平均等待时间: {np.mean(all_wait_times):.2f} ± {np.std(all_wait_times):.2f}")
    print(f"平均系统时间: {np.mean(all_system_times):.2f} ± {np.std(all_system_times):.2f}")
    
    return all_wait_times, all_system_times
```

---

### 2.3 Agent-Based仿真

**方法原理**：
模拟多个自主Agent的行为和交互，观察宏观涌现现象。

**适用场景**：
- 社会系统（舆论传播）
- 经济系统（市场行为）
- 生态系统（种群动态）
- 交通系统（车辆行为）

**代码框架**：
```python
import numpy as np

class Agent:
    def __init__(self, agent_id, position, opinion):
        self.id = agent_id
        self.position = position
        self.opinion = opinion
    
    def interact(self, other, influence_rate=0.1):
        distance = np.linalg.norm(self.position - other.position)
        if distance < 1.0:
            self.opinion += influence_rate * (other.opinion - self.opinion)
            other.opinion += influence_rate * (self.opinion - other.opinion)

class ABM:
    def __init__(self, n_agents=100, grid_size=10):
        self.agents = []
        self.grid_size = grid_size
        
        for i in range(n_agents):
            pos = np.random.uniform(0, grid_size, 2)
            opinion = np.random.uniform(-1, 1)
            self.agents.append(Agent(i, pos, opinion))
    
    def step(self):
        for agent in self.agents:
            for other in self.agents:
                if agent.id != other.id:
                    agent.interact(other)
    
    def run(self, n_steps=100):
        history = []
        for step in range(n_steps):
            self.step()
            opinions = [a.opinion for a in self.agents]
            history.append({
                'step': step,
                'mean_opinion': np.mean(opinions),
                'std_opinion': np.std(opinions),
                'min_opinion': np.min(opinions),
                'max_opinion': np.max(opinions)
            })
        return history

# 运行仿真
abm = ABM(n_agents=50, grid_size=10)
history = abm.run(n_steps=50)

print("仿真结果:")
for h in history[::10]:
    print(f"Step {h['step']}: mean={h['mean_opinion']:.3f}, "
          f"std={h['std_opinion']:.3f}")
```

---

### 2.4 元胞自动机 (Cellular Automata)

**方法原理**：
网格中每个元胞根据邻居状态和规则更新状态，模拟复杂系统演化。

**适用场景**：
- 交通流模拟
- 生命游戏
- 扩散过程
- 城市扩张

**代码框架**：
```python
import numpy as np

class CellularAutomata:
    def __init__(self, grid_size, rule='game_of_life'):
        self.grid_size = grid_size
        self.rule = rule
        self.grid = np.zeros((grid_size, grid_size), dtype=int)
    
    def init_random(self, density=0.3):
        self.grid = (np.random.random((self.grid_size, self.grid_size)) < density).astype(int)
    
    def count_neighbors(self, x, y):
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.grid_size
                ny = (y + dy) % self.grid_size
                count += self.grid[nx, ny]
        return count
    
    def step(self):
        new_grid = self.grid.copy()
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                neighbors = self.count_neighbors(i, j)
                
                if self.rule == 'game_of_life':
                    if self.grid[i, j] == 1:
                        if neighbors < 2 or neighbors > 3:
                            new_grid[i, j] = 0
                    else:
                        if neighbors == 3:
                            new_grid[i, j] = 1
        
        self.grid = new_grid
    
    def run(self, n_steps):
        history = [self.grid.copy()]
        for _ in range(n_steps):
            self.step()
            history.append(self.grid.copy())
        return history

# 运行生命游戏
ca = CellularAutomata(50, rule='game_of_life')
ca.init_random(density=0.3)
history = ca.run(100)
print(f"最终存活细胞数: {history[-1].sum()}")
```

---

## 3. 方差缩减技术

### 3.1 对偶变量法

```python
def antithetic_variates(func, n_samples=10000):
    samples = np.random.uniform(0, 1, n_samples)
    values1 = func(samples)
    values2 = func(1 - samples)
    estimate = np.mean((values1 + values2) / 2)
    return estimate
```

### 3.2 重要性抽样

```python
def importance_sampling(func, proposal_mean=0.5, proposal_std=0.2,
                       n_samples=10000):
    samples = np.random.normal(proposal_mean, proposal_std, n_samples)
    weights = np.exp(-0.5 * ((samples - 0.5) / 0.2) ** 2) / (
        0.2 * np.sqrt(2 * np.pi))
    values = func(samples)
    estimate = np.mean(values / weights)
    return estimate
```

---

## 4. 常见陷阱与最佳实践

### 4.1 常见陷阱

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 随机种子选择 | 结果不可复现 | 固定随机种子 |
| 收敛性不足 | 估计值不稳定 | 增加仿真次数 |
| 方差过大 | 置信区间过宽 | 方差缩减技术 |
| 模型验证不足 | 仿真结果不合理 | 与实际数据对比 |
| 计算时间过长 | 仿真效率低 | 并行化/简化模型 |

### 4.2 最佳实践

- **随机种子固定**：确保结果可复现
- **多次运行**：报告均值±标准差
- **收敛性分析**：监控估计值随仿真次数的变化
- **模型验证**：与已知结果或实际数据对比
- **敏感性分析**：分析关键参数对结果的影响

---

## 5. 验证清单

- [ ] 随机种子已固定（结果可复现）
- [ ] 仿真次数足够（收敛性验证）
- [ ] 方差估计已计算（置信区间）
- [ ] 与实际数据对比（模型验证）
- [ ] 敏感性分析已执行
- [ ] 计算时间可接受
- [ ] 结果可视化展示
- [ ] 仿真参数已记录
