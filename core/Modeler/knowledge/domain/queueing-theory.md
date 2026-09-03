# 排队论领域知识

## 一、核心概念

### 1.1 排队系统组成
- **顾客到达**: 到达过程（泊松过程等）
- **排队规则**: FCFS、LCFS、优先级
- **服务机制**: 服务台数量、服务时间分布

### 1.2 Kendall记号
```
A/B/C
A: 到达过程（M=泊松，D=确定，G=一般）
B: 服务时间分布（M=指数，D=确定，G=一般）
C: 服务台数量
```

### 1.3 性能指标
- **L**: 系统中顾客数（期望）
- **Lq**: 队列中顾客数（期望）
- **W**: 顾客逗留时间（期望）
- **Wq**: 顾客等待时间（期望）
- **ρ**: 服务台利用率

---

## 二、经典模型

### 2.1 M/M/1模型
```
λ: 到达率
μ: 服务率
ρ = λ/μ: 利用率

L = ρ/(1-ρ)
Lq = ρ²/(1-ρ)
W = 1/(μ-λ)
Wq = ρ/(μ-λ)
```

### 2.2 M/M/c模型
```python
import numpy as np
from scipy.special import factorial

def mm1_metrics(lambda_rate, mu_rate):
    """
    M/M/1模型性能指标
    """
    rho = lambda_rate / mu_rate
    
    L = rho / (1 - rho)
    Lq = rho**2 / (1 - rho)
    W = 1 / (mu_rate - lambda_rate)
    Wq = rho / (mu_rate - lambda_rate)
    
    return {'L': L, 'Lq': Lq, 'W': W, 'Wq': Wq, 'rho': rho}

def mmc_metrics(lambda_rate, mu_rate, c):
    """
    M/M/c模型性能指标
    """
    rho = lambda_rate / (c * mu_rate)
    
    # 计算P0
    sum_terms = sum([(lambda_rate/mu_rate)**n / factorial(n) for n in range(c)])
    last_term = ((lambda_rate/mu_rate)**c / factorial(c)) * (1 / (1 - rho))
    P0 = 1 / (sum_terms + last_term)
    
    # 性能指标
    Lq = P0 * ((lambda_rate/mu_rate)**c * rho / factorial(c)) / (1 - rho)**2
    L = Lq + lambda_rate / mu_rate
    Wq = Lq / lambda_rate
    W = Wq + 1 / mu_rate
    
    return {'L': L, 'Lq': Lq, 'W': W, 'Wq': Wq, 'rho': rho}
```

### 2.3 M/G/1模型
```python
def mg1_metrics(lambda_rate, mu_rate, service_variance):
    """
    M/G/1模型（Pollaczek-Khinchine公式）
    """
    rho = lambda_rate / mu_rate
    
    # P-K公式
    Lq = (lambda_rate**2 * service_variance + rho**2) / (2 * (1 - rho))
    L = Lq + rho
    Wq = Lq / lambda_rate
    W = Wq + 1 / mu_rate
    
    return {'L': L, 'Lq': Lq, 'W': W, 'Wq': Wq, 'rho': rho}
```

---

## 三、机场出租车模型

### 3.1 问题描述
- 乘客到达机场，需要出租车
- 出租车司机需要决策：排队等客还是去其他地方
- 存在等待时间成本

### 3.2 模型建立
```python
class AirportTaxiModel:
    """
    机场出租车排队模型
    """
    def __init__(self, arrival_rate, service_rate, n_taxis, taxi_cost):
        self.arrival_rate = arrival_rate  # 乘客到达率
        self.service_rate = service_rate  # 服务率
        self.n_taxis = n_taxis  # 出租车数量
        self.taxi_cost = taxi_cost  # 出租车成本
    
    def simulate(self, n_hours):
        """
        模拟出租车排队
        """
        from collections import deque
        
        queue = deque()
        waiting_times = []
        
        # 模拟时间步
        for t in range(n_hours * 60):
            # 乘客到达
            if np.random.poisson(self.arrival_rate / 60) > 0:
                queue.append(t)
            
            # 出租车服务
            if len(queue) > 0 and np.random.random() < self.service_rate / 60:
                arrival_time = queue.popleft()
                waiting_times.append(t - arrival_time)
        
        return waiting_times
    
    def optimal_strategy(self, n_hours):
        """
        最优策略分析
        """
        # 排队等待
        waiting_times = self.simulate(n_hours)
        avg_wait = np.mean(waiting_times) if waiting_times else 0
        
        # 不排队（去其他地方）
        alternative_profit = self.taxi_cost * n_hours
        
        # 排队利润
        queue_profit = len(waiting_times) * 50 - avg_wait * 0.1
        
        return max(queue_profit, alternative_profit)
```

### 3.3 博弈论分析
```python
def taxi_game_analysis(n_drivers, arrival_rate):
    """
    出租车博弈分析
    """
    # 纳什均衡
    # 每个司机的最优策略取决于其他司机的行为
    
    def best_response(n_other_drivers):
        # 其他司机排队时，自己的最优策略
        if n_other_drivers > n_drivers * 0.7:
            return "不排队"
        else:
            return "排队"
    
    # 均衡分析
    equilibrium = []
    for n in range(n_drivers + 1):
        if best_response(n) == "排队":
            equilibrium.append(n)
    
    return equilibrium
```

---

## 四、蒙特卡洛仿真

### 4.1 离散事件仿真
```python
def queue_simulation(arrival_rate, service_rate, n_servers, n_customers):
    """
    排队系统蒙特卡洛仿真
    """
    import heapq
    
    # 事件队列
    events = []
    heapq.heappush(events, (0, 'arrival'))
    
    # 状态
    servers_busy = 0
    queue_length = 0
    total_wait = 0
    
    # 仿真
    time = 0
    customers_served = 0
    
    while customers_served < n_customers:
        event_time, event_type = heapq.heappop(events)
        time = event_time
        
        if event_type == 'arrival':
            # 顾客到达
            if servers_busy < n_servers:
                # 直接服务
                servers_busy += 1
                service_time = np.random.exponential(1/service_rate)
                heapq.heappush(events, (time + service_time, 'departure'))
            else:
                # 排队
                queue_length += 1
            
            # 下一个到达
            interarrival = np.random.exponential(1/arrival_rate)
            heapq.heappush(events, (time + interarrival, 'arrival'))
        
        elif event_type == 'departure':
            # 顾客离开
            customers_served += 1
            servers_busy -= 1
            
            if queue_length > 0:
                # 从队列中取顾客
                queue_length -= 1
                servers_busy += 1
                service_time = np.random.exponential(1/service_rate)
                heapq.heappush(events, (time + service_time, 'departure'))
    
    return total_wait / customers_served
```

---

## 五、论文写作要点

### 5.1 问题分析框架
1. **系统描述**: 到达过程、服务过程
2. **模型选择**: M/M/c等
3. **参数估计**: 到达率、服务率
4. **性能分析**: L, Lq, W, Wq
5. **策略优化**: 服务台数量、调度策略
6. **灵敏度分析**: 参数影响

### 5.2 图表规范
- **队列长度变化**: 时间序列
- **等待时间分布**: 直方图
- **利用率图**: 服务台利用
- **敏感性分析**: 参数影响

### 5.3 LaTeX代码
```latex
\begin{equation}
L_q = \frac{\rho^{c+1}}{c!(1-\rho)^2} P_0
\label{eq:mmc}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{queue_analysis.pdf}
\caption{排队系统分析}
\label{fig:queue}
\end{figure}
```

---

## 六、参考文献

1. Gross D. Fundamentals of Queueing Theory. Wiley, 2008.
2. 孙荣恒. 排队论基础. 科学出版社, 2002.
3. Little J D C. A Proof for the Queuing Formula. Operations Research, 1961.
4. 陆传赉. 排队论. 北京邮电大学出版社, 2009.
