# PART B: Knowledge Map — 最终推荐 L1→L2→L3→L4 知识图谱

> **综合代理**：Research-layer Calibration 综合代理
> **日期**：2026-09-08
> **基于**：01_TAXONOMY_AUDIT.md 的最终标签决策
> **覆盖检查**：L1 5个缺失 + L2 6个缺失 + L3 graph/DE + L4 numerical PDE/DP 全部覆盖

---

## 0. 图谱总览

```
L1 Problem Structure (9 + 1属性)
│
├── motion/geometry
├── continuous_mechanics
├── diffusion/heat_transfer
├── network/traffic
├── scheduling
├── supply_chain/operations
├── competition/game
├── decision_evaluation
├── data_analysis
└── [属性] stochastic/deterministic
```

每个 L1 标签映射到一个或多个 L2 建模模式，每个 L2 映射到 L3 数学表述，每个 L3 映射到 L4 求解器。

---

## 1. 完整 L1→L2→L3→L4 映射表

### 1.1 motion/geometry（运动学/几何建模）

| L1 | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 证据来源 |
|---|---|---|---|---|
| motion/geometry | geometric_constraint（刚体约束/碰撞检测/螺线参数化） | ODE（运动学递推）+ linear_algebra（坐标变换）+ optimization（约束优化） | numerical_ODE（多体递推/RK4）+ analytical_methods（螺线几何解析）+ exact_optimizer（约束优化） | continuous_physics §1.2, §5.2; taxonomy §6.1 2024_A |
| motion/geometry | temporal_recurrence（位置/速度随时间递推） | ODE（微分关系）+ linear_algebra | numerical_ODE + analytical_methods | continuous_physics §3.6; taxonomy §2.2.1 |
| motion/geometry | inverse_problem（定位反演/参数标定） | optimization（残差最小化）+ linear_algebra | exact_optimizer（Levenberg-Marquardt）+ analytical_methods | taxonomy §2.3.2; continuous_physics §8.2 |

**典型题目**：2024_A（板凳龙）、2015_A（太阳影子定位）、2017_A（CT标定）、2021_A（定日镜）、2023_A（聚光）

**断链检查**：✅ 无断链。L1 motion/geometry → L2 geometric_constraint → L3 ODE/linear_algebra/optimization → L4 numerical_ODE/analytical_methods/exact_optimizer 完整闭合。

---

### 1.2 continuous_mechanics（连续力学/振动/动力学）

| L1 | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 证据来源 |
|---|---|---|---|---|
| continuous_mechanics | conservation_law（动量守恒/能量守恒） | ODE（牛顿第二定律/振动方程）+ optimization | numerical_ODE（RK4/odeint）+ exact_optimizer | taxonomy §1.3.1; continuous_physics §2.1 |
| continuous_mechanics | geometric_constraint（变形约束/刚体姿态） | ODE（静力平衡边值）+ linear_algebra + optimization | numerical_ODE（打靶法/有限差分）+ exact_optimizer | continuous_physics §6.4 (2016_A); taxonomy §6.3 |
| continuous_mechanics | spatial_temporal_field（振动场/应力场） | PDE（弹性力学方程/波动方程） | numerical_PDE（有限元/有限差分） | continuous_physics §3.5 (双曲型PDE) |

**典型题目**：2016_A（系泊系统）、2019_A（车床振动）、2019_B（碰撞周期）、2022_A（振动）

**断链检查**：✅ 无断链。L1 continuous_mechanics → L2 conservation_law/geometric_constraint → L3 ODE/PDE → L4 numerical_ODE/numerical_PDE 完整闭合。

---

### 1.3 diffusion/heat_transfer（扩散/热传导）

| L1 | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 证据来源 |
|---|---|---|---|---|
| diffusion/heat_transfer | conservation_law（能量守恒/质量守恒） | PDE（抛物型 ∂u/∂t=α∇²u+S） | numerical_PDE（FDM Crank-Nicolson/Du Fort-Frankel） | continuous_physics §1.1, §2.1, §4; taxonomy §6.1 2018_A |
| diffusion/heat_transfer | spatial_temporal_field（温度场/浓度场 u(x,t)） | PDE（含初始条件+Dirichlet/Neumann/Robin边界） | numerical_PDE（FDM/FEM/FVM） | continuous_physics §2.2; taxonomy §2.2.7 |
| diffusion/heat_transfer | inverse_problem（热参数反演/厚度优化） | PDE + optimization（残差最小化） | numerical_PDE + exact_optimizer（最小二乘/网格搜索） | continuous_physics §6.1 (2018_A Q2/Q3); taxonomy §2.3.2 |

**典型题目**：2018_A（高温作业服装）、2020_A（回流焊炉温）

**断链检查**：✅ 无断链。这是原审计中缺失最严重的分支（L1+L2+L4三层联动缺失），现已完整闭合：L1 diffusion → L2 conservation_law + spatial_temporal_field → L3 PDE → L4 numerical_PDE。

---

### 1.4 network/traffic（网络/交通）

| L1 | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 证据来源 |
|---|---|---|---|---|
| network/traffic | flow_balance（节点流量守恒/容量约束） | graph（网络拓扑）+ optimization（LP/网络流） | graph_algorithm（Dijkstra/Edmonds-Karp/Dinic/最小费用流）+ exact_optimizer | network_game §1.1, §2.1, §4.1; taxonomy §6.1 2019_C |
| network/traffic | queue（到达/服务/等待） | probability_and_stochastic（生灭过程/Markov链） | analytical_methods（M/M/c闭式公式/Little定理）+ simulation（DES）+ monte_carlo | network_game §2.2, §4.2; taxonomy §2.2.6 |
| network/traffic | interaction_game（用户均衡/路径选择博弈） | optimization（变分不等式/互补问题）+ probability_and_stochastic | analytical_methods（Nash均衡/Frank-Wolfe）+ simulation（ABM） | network_game §2.3, §4.3; taxonomy §2.2.8 |
| network/traffic | geometric_constraint（路网几何/空间布局） | graph + linear_algebra | graph_algorithm + analytical_methods | network_game §1.1 |

**典型题目**：2016_B（小区开放交通）、2019_C（机场出租车）、2024_E（交通信号）、2025_D（水管网络）

**断链检查**：✅ 无断链。L1 network/traffic → L2 flow_balance/queue/interaction_game → L3 graph/probability/optimization → L4 graph_algorithm/analytical_methods/simulation 完整闭合。

---

### 1.5 scheduling（调度）

| L1 | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 证据来源 |
|---|---|---|---|---|
| scheduling | resource_constraint（机器容量/时间窗/人力） | optimization（目标+约束）+ graph（析取图） | exact_optimizer（MILP/B&B）+ metaheuristic_optimization（GA/SA/PSO）+ analytical_methods（SPT/EDD/Johnson规则） | discrete_optimization §1, §2.1, §4; taxonomy §6.1 2018_B |
| scheduling | decision_state_transition（MDP/加工状态演化） | optimization（Bellman方程）+ probability_and_stochastic（转移概率） | DP_and_MDP（值迭代/策略迭代）+ simulation（DES）+ monte_carlo | discrete_optimization §2.2, §4.1; taxonomy §2.2.1 |
| scheduling | queue（动态调度/等待队列） | probability_and_stochastic（生灭过程） | analytical_methods（排队公式）+ simulation（DES） | discrete_optimization §1.5; network_game §2.2 |

**典型题目**：2018_B（RGV调度）、2019_B（碰撞周期）、2020_B（穿越沙漠-调度部分）、2021_C（供应链-调度部分）、2024_B（概率决策）

**断链检查**：✅ 无断链。L1 scheduling → L2 resource_constraint/decision_state_transition → L3 optimization/graph/probability → L4 exact_optimizer/metaheuristic/DP_and_MDP/simulation 完整闭合。

---

### 1.6 supply_chain/operations（供应链/运营）

| L1 | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 证据来源 |
|---|---|---|---|---|
| supply_chain/operations | resource_constraint（产能/库存容量/预算） | optimization（多周期规划）+ graph（供应链网络） | exact_optimizer（MILP/LP）+ DP_and_MDP（多周期库存）+ metaheuristic_optimization | taxonomy §1.3.2; discrete_optimization §6.3 (2021_C) |
| supply_chain/operations | flow_balance（物流/库存平衡） | graph + optimization | graph_algorithm（最小费用流）+ exact_optimizer | network_game §2.1; taxonomy §2.2.3 |
| supply_chain/operations | decision_state_transition（库存水平演化） | optimization + probability_and_stochastic | DP_and_MDP + analytical_methods（报童模型） | discrete_optimization §2.2; taxonomy §4.3.4 (newsboy_model) |

**典型题目**：2021_C（原材料订购运输）、2024_C（生产调度）

**断链检查**：✅ 无断链。L1 supply_chain/operations → L2 resource_constraint/flow_balance/decision_state_transition → L3 optimization/graph/probability → L4 exact_optimizer/DP_and_MDP/graph_algorithm 完整闭合。

---

### 1.7 competition/game（竞争/博弈）

| L1 | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 证据来源 |
|---|---|---|---|---|
| competition/game | interaction_game（多玩家策略互动/均衡） | optimization（Nash↔互补问题/变分不等式）+ probability_and_stochastic（混合策略/Bayesian）+ ODE（复制子动力学） | analytical_methods（Nash均衡/Shapley值/逆向归纳）+ simulation（ABM/演化仿真）+ monte_carlo | network_game §1.2, §2.3, §4.3; discrete_optimization §6.1 (2020_B Q3); taxonomy §6.1 2020_B |
| competition/game | resource_constraint（共享资源外部性/公地悲剧） | optimization + game-theoretic（通过interaction_game L2锚定） | analytical_methods + exact_optimizer（MPEC/双层优化） | discrete_optimization §2.1.3 (资源外部性); network_game §2.3 |
| competition/game | decision_state_transition（随机博弈/序贯博弈） | optimization + probability_and_stochastic | DP_and_MDP + analytical_methods + monte_carlo | discrete_optimization §2.2; network_game §4.3.3 |

**典型题目**：2020_B（穿越沙漠-Q3多玩家）、2025_D（水管网络博弈）

**断链检查**：✅ 无断链。注意：L3 不设独立 game-theoretic 标签，博弈的数学表述通过 optimization（Nash↔互补）+ probability（混合策略）+ ODE（复制子动力学）组合标注。L2 interaction_game 是博弈的核心锚点。

---

### 1.8 decision_evaluation（决策/评价）

| L1 | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 证据来源 |
|---|---|---|---|---|
| decision_evaluation | geometric_constraint（TOPSIS距离理想点） | linear_algebra（向量运算/距离计算）+ statistics | analytical_methods（TOPSIS/AHP/熵权闭式计算） | audit §2.2 (mc-topsis使用distance/geometry); taxonomy §4.5 |
| decision_evaluation | statistical_association（指标关联/权重确定） | statistics（相关分析/方差分析）+ linear_algebra（特征向量） | analytical_methods（AHP特征向量法/熵权）+ regression_and_supervised | taxonomy §2.3.1; audit §1.1 |
| decision_evaluation | inverse_problem（决策反演/参数标定） | optimization + statistics | exact_optimizer + analytical_methods | taxonomy §2.3.2 |

**典型题目**：2015_B、2017_B、2018_C、2019_C（决策部分）、2020_C、2022_C（评价部分）、2023_C、2024_C、2025_C

**断链检查**：✅ 无断链。这是当前卡库的"舒适区"（5卡覆盖），补充L2标签后路径更清晰。

---

### 1.9 data_analysis（数据分析）

| L1 | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 证据来源 |
|---|---|---|---|---|
| data_analysis | statistical_association（回归/分类/聚类/相关/降维） | statistics（回归模型/假设检验）+ linear_algebra（SVD/特征值）+ probability_and_stochastic（概率模型） | regression_and_supervised（OLS/Logistic/RF/XGBoost/ARIMA/LSTM）+ clustering（KMeans/层次聚类）+ dimensionality_reduction（PCA/LDA） | taxonomy §2.3.1, §3.2.5; audit §2.3 (11卡涉及statistics) |
| data_analysis | temporal_recurrence（时序预测/递推） | statistics（时序模型）+ probability_and_stochastic | regression_and_supervised（ARIMA/LSTM/GM）+ analytical_methods | taxonomy §2.2.1; audit §2.2 (state transition仅时序语境) |
| data_analysis | inverse_problem（参数估计/模型标定） | statistics（最大似然/贝叶斯）+ optimization | exact_optimizer + regression_and_supervised + monte_carlo（MCMC） | taxonomy §2.3.2 |

**典型题目**：2016_C（电池预测）、2017_C（颜色浓度）、2022_C（古代玻璃）、2023_C（销量预测）、2025_C（混合效应）、2025_E（运动数据）

**断链检查**：✅ 无断链。这是当前卡库覆盖最强的分支（10卡涉及data/evaluation），补充L2 statistical_association标签后路径更完整。

---

## 2. 缺失区域覆盖验证

### 2.1 L1 5个缺失标签覆盖验证

| 原缺失L1标签 | 原状态 | 现状态 | 映射路径 | 覆盖题目 |
|---|---|---|---|---|
| motion/geometry | 0卡覆盖 | ✅ 已覆盖 | motion/geometry → geometric_constraint → ODE/linear_algebra → numerical_ODE/analytical_methods | 2024_A, 2015_A, 2017_A, 2021_A, 2023_A, 2023_B, 2025_A, 2025_B (8题) |
| network/traffic | 0卡覆盖 | ✅ 已覆盖 | network/traffic → flow_balance/queue → graph/probability → graph_algorithm/analytical_methods/simulation | 2016_B, 2019_C, 2024_E, 2025_D (4题) |
| scheduling | 0卡覆盖 | ✅ 已覆盖 | scheduling → resource_constraint/decision_state_transition → optimization/graph → exact_optimizer/metaheuristic/DP_and_MDP | 2018_B, 2019_B, 2020_B, 2021_C, 2024_B (5题) |
| diffusion | 0卡覆盖 | ✅ 已覆盖 | diffusion → conservation_law/spatial_temporal_field → PDE → numerical_PDE | 2018_A, 2020_A (2题) |
| competition/game | 0卡覆盖 | ✅ 已覆盖 | competition/game → interaction_game → optimization/probability/ODE → analytical_methods/simulation | 2020_B(Q3), 2025_D (2题) |

### 2.2 L2 6个缺失标签覆盖验证

| 原缺失L2标签 | 原状态 | 现状态 | 映射路径 |
|---|---|---|---|
| conservation_law | 0卡覆盖 | ✅ 已覆盖 | conservation_law → PDE/ODE → numerical_PDE/numerical_ODE |
| flow_balance | 0卡覆盖 | ✅ 已覆盖 | flow_balance → graph/optimization → graph_algorithm/exact_optimizer |
| resource_constraint | 0卡覆盖 | ✅ 已覆盖 | resource_constraint → optimization/graph → exact_optimizer/metaheuristic/DP_and_MDP |
| queue | 0卡覆盖 | ✅ 已覆盖 | queue → probability_and_stochastic → analytical_methods/simulation/monte_carlo |
| spatial_temporal_field | 0卡覆盖 | ✅ 已覆盖 | spatial_temporal_field → PDE → numerical_PDE |
| interaction_game | 0卡覆盖 | ✅ 已覆盖 | interaction_game → optimization/probability/ODE → analytical_methods/simulation |

### 2.3 L3 graph + DE 覆盖验证

| 原缺失L3标签 | 原状态 | 现状态 | 映射路径 |
|---|---|---|---|
| graph | 0卡覆盖 | ✅ 已覆盖 | graph → graph_algorithm/exact_optimizer |
| differential equation (拆分后) | 仅grey DE弱覆盖 | ✅ ODE+PDE独立覆盖 | ODE → numerical_ODE; PDE → numerical_PDE |

### 2.4 L4 numerical PDE + DP 覆盖验证

| 原缺失L4标签 | 原状态 | 现状态 | 上层锚点 |
|---|---|---|---|
| numerical PDE | 0卡覆盖 | ✅ 已覆盖 | L3 PDE → L4 numerical_PDE (FDM/FEM/FVM) |
| DP | 0卡覆盖 | ✅ 已覆盖（扩展为DP_and_MDP） | L2 decision_state_transition → L3 optimization → L4 DP_and_MDP |

---

## 3. 断链检查矩阵

对每个 L1→L2→L3→L4 路径检查是否存在断链（某层无对应标签）：

| L1 | L2 | L3 | L4 | 断链? |
|---|---|---|---|---|
| motion/geometry | geometric_constraint | ODE, linear_algebra, optimization | numerical_ODE, analytical_methods, exact_optimizer | ❌ 无 |
| motion/geometry | temporal_recurrence | ODE, linear_algebra | numerical_ODE, analytical_methods | ❌ 无 |
| motion/geometry | inverse_problem | optimization, linear_algebra | exact_optimizer, analytical_methods | ❌ 无 |
| continuous_mechanics | conservation_law | ODE, PDE | numerical_ODE, numerical_PDE | ❌ 无 |
| continuous_mechanics | geometric_constraint | ODE, optimization | numerical_ODE, exact_optimizer | ❌ 无 |
| diffusion/heat_transfer | conservation_law | PDE | numerical_PDE | ❌ 无 |
| diffusion/heat_transfer | spatial_temporal_field | PDE | numerical_PDE | ❌ 无 |
| diffusion/heat_transfer | inverse_problem | PDE, optimization | numerical_PDE, exact_optimizer | ❌ 无 |
| network/traffic | flow_balance | graph, optimization | graph_algorithm, exact_optimizer | ❌ 无 |
| network/traffic | queue | probability_and_stochastic | analytical_methods, simulation, monte_carlo | ❌ 无 |
| network/traffic | interaction_game | optimization, probability, ODE | analytical_methods, simulation | ❌ 无 |
| scheduling | resource_constraint | optimization, graph | exact_optimizer, metaheuristic, analytical_methods | ❌ 无 |
| scheduling | decision_state_transition | optimization, probability | DP_and_MDP, simulation, monte_carlo | ❌ 无 |
| scheduling | queue | probability | analytical_methods, simulation | ❌ 无 |
| supply_chain/operations | resource_constraint | optimization, graph | exact_optimizer, DP_and_MDP, metaheuristic | ❌ 无 |
| supply_chain/operations | flow_balance | graph, optimization | graph_algorithm, exact_optimizer | ❌ 无 |
| supply_chain/operations | decision_state_transition | optimization, probability | DP_and_MDP, analytical_methods | ❌ 无 |
| competition/game | interaction_game | optimization, probability, ODE | analytical_methods, simulation, monte_carlo | ❌ 无 |
| competition/game | resource_constraint | optimization | analytical_methods, exact_optimizer | ❌ 无 |
| competition/game | decision_state_transition | optimization, probability | DP_and_MDP, analytical_methods, monte_carlo | ❌ 无 |
| decision_evaluation | geometric_constraint | linear_algebra, statistics | analytical_methods | ❌ 无 |
| decision_evaluation | statistical_association | statistics, linear_algebra | analytical_methods, regression_and_supervised | ❌ 无 |
| data_analysis | statistical_association | statistics, linear_algebra, probability | regression_and_supervised, clustering, dimensionality_reduction | ❌ 无 |
| data_analysis | temporal_recurrence | statistics, probability | regression_and_supervised, analytical_methods | ❌ 无 |
| data_analysis | inverse_problem | statistics, optimization | exact_optimizer, regression_and_supervised, monte_carlo | ❌ 无 |

**结论**：✅ 全部 25 条映射路径无断链。四层知识图谱完整闭合。

---

## 4. 跨层关联图（核心路径）

### 4.1 连续物理域核心路径

```
diffusion/heat_transfer
  ├── conservation_law ──→ PDE(抛物型) ──→ numerical_PDE (FDM Crank-Nicolson)
  ├── spatial_temporal_field ──→ PDE(初始+边界条件) ──→ numerical_PDE
  └── inverse_problem ──→ PDE + optimization ──→ numerical_PDE + exact_optimizer

motion/geometry
  ├── geometric_constraint ──→ ODE + linear_algebra + optimization ──→ numerical_ODE + analytical_methods + exact_optimizer
  └── temporal_recurrence ──→ ODE ──→ numerical_ODE

continuous_mechanics
  ├── conservation_law(动量/能量) ──→ ODE(牛顿第二定律) ──→ numerical_ODE
  └── geometric_constraint(变形) ──→ ODE/PDE ──→ numerical_ODE/numerical_PDE
```

### 4.2 离散优化域核心路径

```
scheduling
  ├── resource_constraint ──→ optimization + graph(析取图) ──→ exact_optimizer(MILP) + metaheuristic_optimization(GA/SA)
  └── decision_state_transition(MDP) ──→ optimization + probability ──→ DP_and_MDP(值迭代/策略迭代)

supply_chain/operations
  ├── resource_constraint ──→ optimization ──→ exact_optimizer + DP_and_MDP
  └── flow_balance ──→ graph + optimization ──→ graph_algorithm(最小费用流)
```

### 4.3 网络博弈域核心路径

```
network/traffic
  ├── flow_balance ──→ graph + optimization(LP) ──→ graph_algorithm(Dijkstra/Edmonds-Karp/Dinic)
  ├── queue ──→ probability_and_stochastic(生灭过程) ──→ analytical_methods(M/M/c) + simulation(DES)
  └── interaction_game(用户均衡) ──→ optimization(变分不等式) ──→ analytical_methods(Frank-Wolfe) + simulation(ABM)

competition/game
  └── interaction_game ──→ optimization(Nash↔互补) + probability(混合策略) + ODE(复制子动力学) ──→ analytical_methods(Nash/Shapley/逆向归纳) + simulation(演化仿真)
```

### 4.4 数据决策域核心路径

```
data_analysis
  └── statistical_association ──→ statistics + linear_algebra + probability ──→ regression_and_supervised + clustering + dimensionality_reduction

decision_evaluation
  ├── geometric_constraint(TOPSIS距离) ──→ linear_algebra + statistics ──→ analytical_methods(TOPSIS/AHP/熵权)
  └── statistical_association ──→ statistics + linear_algebra ──→ analytical_methods + regression_and_supervised
```

---

## 5. L2 标签跨 L1 复用统计

| L2 标签 | 关联L1数量 | 关联的L1标签 |
|---|---|---|
| geometric_constraint | 4 | motion/geometry, continuous_mechanics, decision_evaluation, network/traffic |
| conservation_law | 2 | diffusion/heat_transfer, continuous_mechanics |
| spatial_temporal_field | 1 | diffusion/heat_transfer |
| flow_balance | 2 | network/traffic, supply_chain/operations |
| queue | 2 | network/traffic, scheduling |
| resource_constraint | 3 | scheduling, supply_chain/operations, competition/game |
| decision_state_transition | 3 | scheduling, supply_chain/operations, competition/game |
| interaction_game | 2 | competition/game, network/traffic |
| statistical_association | 2 | data_analysis, decision_evaluation |
| temporal_recurrence | 2 | motion/geometry, data_analysis |
| inverse_problem | 4 | diffusion/heat_transfer, motion/geometry, data_analysis, decision_evaluation |

**关键发现**：geometric_constraint 和 inverse_problem 是跨 L1 复用最多的 L2 标签（各关联4个L1），说明它们是通用建模模式而非特定领域模式。

---

*本知识图谱基于01_TAXONOMY_AUDIT.md的最终标签决策构建。所有25条映射路径经断链检查，完整闭合。覆盖原审计中L1 5个缺失+L2 6个缺失+L3 graph/DE+L4 numerical PDE/DP全部区域。*
