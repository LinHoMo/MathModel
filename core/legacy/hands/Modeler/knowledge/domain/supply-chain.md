# 供应链优化领域知识

## 一、核心概念

### 1.1 供应链组成
- **供应商**: 原材料供应
- **制造商**: 生产加工
- **分销商**: 仓储运输
- **零售商**: 终端销售
- **消费者**: 需求来源

### 1.2 供应链管理目标
- **成本最小化**: 采购、生产、运输、库存成本
- **服务水平**: 交货期、满足率
- **风险控制**: 供应中断、需求波动

### 1.3 关键指标
- **库存周转率**: 年销售成本/平均库存
- **订单满足率**: 满足的订单/总订单
- **供应链总成本**: 采购+生产+运输+库存

---

## 二、采购优化

### 2.1 经济订货量（EOQ）
```
EOQ = sqrt(2*D*S/H)
D: 年需求量
S: 每次订货成本
H: 单位持有成本
```

### 2.2 数量折扣模型
```python
def quantity_discount_model(demand, order_cost, holding_rate, discount_schedule):
    """
    数量折扣下的最优订货量
    discount_schedule: [(min_qty, price), ...]
    """
    best_cost = np.inf
    best_qty = 0
    
    for min_qty, price in discount_schedule:
        EOQ = np.sqrt(2 * demand * order_cost / (holding_rate * price))
        EOQ = max(EOQ, min_qty)
        
        total_cost = (demand * price + 
                     demand / EOQ * order_cost + 
                     EOQ / 2 * holding_rate * price)
        
        if total_cost < best_cost:
            best_cost = total_cost
            best_qty = EOQ
    
    return best_qty, best_cost
```

### 2.3 多源采购
```
min Σ c_ij * x_ij
s.t. Σ x_ij = d_j (需求约束)
     x_ij ≤ s_i (供应约束)
     x_ij ≥ 0
```

---

## 三、运输优化

### 3.1 运输问题
```
min Σ c_ij * x_ij
s.t. Σ_j x_ij ≤ a_i (供应约束)
     Σ_i x_ij ≥ b_j (需求约束)
```

### 3.2 车辆路径问题（VRP）
```python
def vrp_solver(n_customers, distance_matrix, vehicle_capacity, demand):
    """
    车辆路径问题求解
    """
    # 使用节约算法或遗传算法
    routes = []
    remaining = list(range(n_customers))
    
    while remaining:
        route = [0]  # 从配送中心出发
        load = 0
        
        while remaining:
            # 选择最近的未访问客户
            last = route[-1]
            nearest = min(remaining, key=lambda x: distance_matrix[last][x])
            
            if load + demand[nearest] <= vehicle_capacity:
                route.append(nearest)
                load += demand[nearest]
                remaining.remove(nearest)
            else:
                break
        
        route.append(0)  # 返回配送中心
        routes.append(route)
    
    return routes
```

### 3.3 多式联运
```
min Σ (c_ij^mode * x_ij^mode + f_ij * y_ij)
s.t. 流量守恒
     模式选择约束
     容量约束
```

---

## 四、库存优化

### 4.1 (s,S)策略
```
当库存 ≤ s时，订货到S
s: 再订货点
S: 最大库存水平
```

### 4.2 多级库存
```python
def multi_echelon_inventory(lead_times, demand_variance, service_level):
    """
    多级库存优化
    """
    from scipy.stats import norm
    z = norm.ppf(service_level)
    
    # 安全库存
    safety_stock = {}
    for node in nodes:
        upstream_var = sum(demand_variance[n] for n in upstream[node])
        safety_stock[node] = z * np.sqrt(sum(lt[n]**2 for n in upstream[node]) * demand_variance[node])
    
    return safety_stock
```

### 4.3 随机库存模型
```
min h*E[max(I,0)] + p*E[max(-I,0)] + c*E[R]
I: 库存水平
R: 订货量
h: 持有成本
p: 缺货成本
```

---

## 五、随机规划

### 5.1 两阶段随机规划
```
min c^T x + E[Q(x,ξ)]
s.t. Ax = b
     x ≥ 0
Q(x,ξ) = min q^T y
         s.t. Wy ≥ h(ξ) - T(ξ)x
              y ≥ 0
```

### 5.2 鲁棒优化
```
min c^T x
s.t. Ax ≥ b, ∀ u ∈ U
     x ≥ 0
U: 不确定集合
```

### 5.3 场景分析
```python
def scenario_analysis(scenarios, probabilities):
    """
    场景分析
    scenarios: 各场景的需求、成本
    probabilities: 场景概率
    """
    expected_cost = sum(prob * cost for prob, cost in zip(probabilities, costs))
    variance = sum(prob * (cost - expected_cost)**2 for prob, cost in zip(probabilities, costs))
    
    return expected_cost, np.sqrt(variance)
```

---

## 六、论文写作要点

### 6.1 问题分析框架
1. **供应链网络**: 节点、连接、流向
2. **不确定性**: 需求、供应、价格波动
3. **优化模型**: 目标函数、约束条件
4. **求解算法**: 精确解、启发式
5. **结果分析**: 成本节约、服务水平
6. **灵敏度分析**: 参数影响

### 6.2 图表规范
- **供应链网络图**: 节点+箭头
- **成本构成图**: 饼图/条形图
- **库存变化图**: 时间序列
- **敏感性分析**: 参数影响

### 6.3 LaTeX代码
```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{supply_chain_network.pdf}
\caption{供应链网络结构}
\label{fig:supply_chain}
\end{figure}
```

---

## 七、参考文献

1. 马士华. 供应链管理. 机械工业出版社, 2014.
2. Simchi-Levi D. Designing and Managing the Supply Chain. McGraw-Hill, 2008.
3. Shapiro J. Modeling the Supply Chain. Thomson Learning, 2001.
4. 漆安慎. 供应链管理：理论与应用. 高等教育出版社, 2015.
