# 排队论方法论

> 本文档提供排队论的完整方法论，包括M/M/1、M/M/c、Little定理等核心方法。

---

## 一、方法选择决策树

```
排队系统分析
├── 服务台数量？
│   ├── 单服务台 → M/M/1
│   └── 多服务台 → M/M/c
├── 到达过程？
│   ├── 泊松到达 → 马尔可夫到达
│   └── 一般到达 → G/M/1
├── 服务时间？
│   ├── 指数分布 → M/M/1, M/M/c
│   └── 一般分布 → G/G/1
└── 系统容量？
│   ├── 无限容量 → M/M/1, M/M/c
│   └── 有限容量 → M/M/1/K
```

---

## 二、M/M/1排队模型

### 2.1 模型假设

- 到达过程：泊松过程，到达率λ
- 服务时间：指数分布，服务率μ
- 单服务台
- 系统容量无限
- 排队规则：FIFO

### 2.2 核心公式

**系统利用率**：ρ = λ/μ（必须ρ < 1）

**稳态概率**：

```
P₀ = 1 - ρ                    （系统空闲概率）
Pₙ = ρⁿ(1-ρ)                 （系统中有n个顾客的概率）
```

**性能指标**：

| 指标 | 公式 | 含义 |
|------|------|------|
| L | ρ/(1-ρ) | 系统中平均顾客数 |
| Lq | ρ²/(1-ρ) | 队列中平均顾客数 |
| W | 1/(μ-λ) | 平均逗留时间 |
| Wq | ρ/(μ-λ) | 平均等待时间 |

### 2.3 完整代码框架

```python
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

class MM1Queue:
    def __init__(self, arrival_rate, service_rate):
        """
        arrival_rate: 到达率λ（单位时间到达顾客数）
        service_rate: 服务率μ（单位时间服务顾客数）
        """
        self.lambda_ = arrival_rate
        self.mu = service_rate
        self.rho = self.lambda_ / self.mu
        
        if self.rho >= 1:
            raise ValueError(f"系统不稳定：ρ={self.rho:.2f} >= 1")
    
    def steady_state_prob(self, n):
        """系统中有n个顾客的稳态概率"""
        return self.rho ** n * (1 - self.rho)
    
    def utilization(self):
        """系统利用率"""
        return self.rho
    
    def avg_customers(self):
        """系统中平均顾客数L"""
        return self.rho / (1 - self.rho)
    
    def avg_queue_length(self):
        """队列中平均顾客数Lq"""
        return self.rho ** 2 / (1 - self.rho)
    
    def avg_time_in_system(self):
        """平均逗留时间W"""
        return 1 / (self.mu - self.lambda_)
    
    def avg_time_in_queue(self):
        """平均等待时间Wq"""
        return self.rho / (self.mu - self.lambda_)
    
    def probability_wait_longer(self, t):
        """等待时间超过t的概率"""
        return self.rho * np.exp(-self.mu * (1 - self.rho) * t)
    
    def simulate(self, n_customers, seed=42):
        """蒙特卡洛模拟"""
        np.random.seed(seed)
        
        inter_arrival = np.random.exponential(1/self.lambda_, n_customers)
        service_times = np.random.exponential(1/self.mu, n_customers)
        
        arrival_times = np.cumsum(inter_arrival)
        start_service = np.zeros(n_customers)
        end_service = np.zeros(n_customers)
        
        # 第一个顾客
        start_service[0] = arrival_times[0]
        end_service[0] = start_service[0] + service_times[0]
        
        # 后续顾客
        for i in range(1, n_customers):
            start_service[i] = max(arrival_times[i], end_service[i-1])
            end_service[i] = start_service[i] + service_times[i]
        
        wait_times = start_service - arrival_times
        time_in_system = end_service - arrival_times
        
        return {
            'arrival_times': arrival_times,
            'wait_times': wait_times,
            'time_in_system': time_in_system,
            'avg_wait': np.mean(wait_times),
            'avg_time_in_system': np.mean(time_in_system)
        }
    
    def report(self):
        """生成报告"""
        print("=" * 50)
        print("M/M/1 排队系统分析报告")
        print("=" * 50)
        print(f"到达率 λ: {self.lambda_:.2f} 顾客/单位时间")
        print(f"服务率 μ: {self.mu:.2f} 顾客/单位时间")
        print(f"系统利用率 ρ: {self.rho:.4f}")
        print("-" * 50)
        print(f"系统空闲概率 P₀: {1-self.rho:.4f}")
        print(f"平均顾客数 L: {self.avg_customers():.4f}")
        print(f"平均队列长度 Lq: {self.avg_queue_length():.4f}")
        print(f"平均逗留时间 W: {self.avg_time_in_system():.4f}")
        print(f"平均等待时间 Wq: {self.avg_time_in_queue():.4f}")
        print("=" * 50)
```

### 2.4 使用示例

```python
# 银行窗口：平均到达率20人/小时，服务率25人/小时
queue = MM1Queue(arrival_rate=20, service_rate=25)
queue.report()

# 模拟
sim_result = queue.simulate(n_customers=1000)
print(f"模拟平均等待时间: {sim_result['avg_wait']:.4f}")
```

---

## 三、M/M/c排队模型

### 3.1 模型假设

- 到达过程：泊松过程，到达率λ
- 服务时间：指数分布，服务率μ（每个服务台）
- c个并行服务台
- 系统容量无限

### 3.2 核心公式

**系统利用率**：ρ = λ/(cμ)（必须ρ < 1）

**稳态概率**：

```
P₀ = [Σ(k=0,c-1)(cρ)ᵏ/k! + (cρ)ᶜ/(c!(1-ρ))]⁻¹

Pₙ = (cρ)ⁿ/n! × P₀,  n ≤ c
Pₙ = (cρ)ᶜ/c! × ρⁿ⁻ᶜ × P₀,  n > c
```

**性能指标**：

| 指标 | 公式 |
|------|------|
| Lq | P₀(cρ)ᶜρ/(c!(1-ρ)²) |
| L | Lq + cρ |
| Wq | Lq/λ |
| W | Wq + 1/μ |

### 3.3 完整代码框架

```python
import numpy as np
from math import factorial

class MMcQueue:
    def __init__(self, arrival_rate, service_rate, n_servers):
        """
        arrival_rate: 到达率λ
        service_rate: 服务率μ（每个服务台）
        n_servers: 服务台数量c
        """
        self.lambda_ = arrival_rate
        self.mu = service_rate
        self.c = n_servers
        self.rho = self.lambda_ / (self.c * self.mu)
        
        if self.rho >= 1:
            raise ValueError(f"系统不稳定：ρ={self.rho:.2f} >= 1")
    
    def P0(self):
        """系统空闲概率"""
        sum_terms = sum([(self.c * self.rho) ** k / factorial(k) 
                        for k in range(self.c)])
        last_term = (self.c * self.rho) ** self.c / (
            factorial(self.c) * (1 - self.rho))
        return 1 / (sum_terms + last_term)
    
    def Lq(self):
        """队列中平均顾客数"""
        p0 = self.P0()
        numerator = p0 * (self.c * self.rho) ** self.c * self.rho
        denominator = factorial(self.c) * (1 - self.rho) ** 2
        return numerator / denominator
    
    def L(self):
        """系统中平均顾客数"""
        return self.Lq() + self.c * self.rho
    
    def Wq(self):
        """平均等待时间"""
        return self.Lq() / self.lambda_
    
    def W(self):
        """平均逗留时间"""
        return self.Wq() + 1 / self.mu
    
    def report(self):
        """生成报告"""
        print("=" * 50)
        print("M/M/c 排队系统分析报告")
        print("=" * 50)
        print(f"到达率 λ: {self.lambda_:.2f} 顾客/单位时间")
        print(f"服务率 μ: {self.mu:.2f} 顾客/单位时间（每台）")
        print(f"服务台数 c: {self.c}")
        print(f"系统利用率 ρ: {self.rho:.4f}")
        print("-" * 50)
        print(f"系统空闲概率 P₀: {self.P0():.4f}")
        print(f"平均顾客数 L: {self.L():.4f}")
        print(f"平均队列长度 Lq: {self.Lq():.4f}")
        print(f"平均逗留时间 W: {self.W():.4f}")
        print(f"平均等待时间 Wq: {self.Wq():.4f}")
        print("=" * 50)
```

---

## 四、Little定理

### 4.1 核心公式

**Little定理**：L = λW

- L：系统中平均顾客数
- λ：平均到达率
- W：平均逗留时间

**推论**：Lq = λWq

### 4.2 应用场景

| 已知 | 求解 | 公式 |
|------|------|------|
| L, λ | W | W = L/λ |
| Lq, λ | Wq | Wq = Lq/λ |
| λ, W | L | L = λW |
| λ, Wq | Lq | Lq = λWq |

### 4.3 代码实现

```python
def little_theorem(L=None, Lq=None, W=None, Wq=None, lam=None):
    """
    Little定理：已知任意三个量，求第四个
    """
    if L is not None and lam is not None:
        W = L / lam
        return {'L': L, 'lam': lam, 'W': W}
    elif Lq is not None and lam is not None:
        Wq = Lq / lam
        return {'Lq': Lq, 'lam': lam, 'Wq': Wq}
    elif lam is not None and W is not None:
        L = lam * W
        return {'lam': lam, 'W': W, 'L': L}
    elif lam is not None and Wq is not None:
        Lq = lam * Wq
        return {'lam': lam, 'Wq': Wq, 'Lq': Lq}
    else:
        raise ValueError("需要至少提供λ和L/Lq/W/Wq中的三个")
```

---

## 五、排队系统优化

### 5.1 成本优化模型

**总成本**：TC = Cs×L + Cw×Lq

- Cs：每个顾客在系统中的逗留成本
- Cw：每个顾客在队列中的等待成本
- L：平均顾客数
- Lq：平均队列长度

**最优服务率**：

```python
def optimal_service_rate(lam, Cs, Cw, mu_range):
    """
    寻找最优服务率使总成本最小
    """
    best_mu = None
    min_cost = float('inf')
    
    for mu in mu_range:
        if lam / mu >= 1:
            continue
        
        queue = MM1Queue(lam, mu)
        L = queue.avg_customers()
        Lq = queue.avg_queue_length()
        
        total_cost = Cs * L + Cw * Lq
        
        if total_cost < min_cost:
            min_cost = total_cost
            best_mu = mu
    
    return best_mu, min_cost
```

### 5.2 服务台数量优化

```python
def optimal_servers(lam, mu, Cs, Cw, max_c=10):
    """
    寻找最优服务台数量
    """
    results = []
    
    for c in range(1, max_c + 1):
        if lam / (c * mu) >= 1:
            continue
        
        queue = MMcQueue(lam, mu, c)
        L = queue.L()
        Lq = queue.Lq()
        
        total_cost = Cs * L + Cw * Lq + c * 100  # 假设每台成本100
        
        results.append({
            'c': c,
            'L': L,
            'Lq': Lq,
            'cost': total_cost
        })
    
    return results
```

---

## 六、竞赛常见场景

### 6.1 服务系统设计

| 场景 | 推荐模型 | 参考论文 |
|------|---------|---------|
| 银行窗口设计 | M/M/c | B195, B196 |
| 医院挂号系统 | M/M/c + 优先级 | B203, B225 |
| 超市收银台 | M/M/c + 成本优化 | B007, B050 |
| 网站服务器 | M/M/c/K（有限容量） | C142 |

### 6.2 调度优化

| 场景 | 推荐模型 | 参考论文 |
|------|---------|---------|
| 机场跑道 | M/M/1 + 调度 | A001, A022 |
| 物流分拣 | M/M/c + 排序 | B195 |
| 生产线平衡 | 排队网络 | B203 |

### 6.3 性能评估

| 场景 | 推荐模型 | 参考论文 |
|------|---------|---------|
| 网络延迟 | M/M/1 + 仿真 | C142 |
| 交通流量 | M/M/1 + 实测 | A070, A147 |
| 系统容量规划 | Little定理 | B195 |

---

## 七、常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| ρ≥1系统不稳定 | 到达率≥服务率 | 增加服务台/提高服务率 |
| 等待时间过长 | 服务台不足 | 增加服务台数量 |
| 队列过长 | 到达率波动大 | 引入预约系统 |
| 模拟不收敛 | 样本量不足 | 增加模拟时间/顾客数 |

---

## 八、参考资源

### 8.1 教材推荐

- 《运筹学》（清华大学出版社）
- 《排队论基础》（陆传赉）
- 《Introduction to Queueing Theory》（Robert B. Cooper）

### 8.2 Python库

- simpy：离散事件仿真
- queuesim：排队模拟

### 8.3 检查清单

- [ ] ρ < 1（系统稳定）
- [ ] Little定理验证通过
- [ ] 成本模型考虑完整
- [ ] 模拟结果与理论值对比
- [ ] 敏感性分析完成
