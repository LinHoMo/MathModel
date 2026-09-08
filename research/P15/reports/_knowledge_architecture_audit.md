# Modeling Knowledge Architecture Audit — 四层知识结构覆盖审计

> **审计性质**：只诊断，不修复。不创建新方法卡、不修改现有方法卡、不修改 e2e_metrics.py、不实现任何知识架构。
> **审计日期**：2026-09-08
> **审计范围**：`core/knowledge/methods/cards/` 全部 16 张 YAML + `research/P15/benchmark/` 5 题 B0 数据
> **输出位置**：`research/P15/reports/_knowledge_architecture_audit.md`

---

## 0. 治理原则声明

### 0.1 三层模型定位

方法卡库**不是**"把所有数学建模方法做成卡片让 LLM 按卡片选方法"。正确定位是三层模型：

| 层 | 角色 | 说明 |
|---|---|---|
| **Layer 1** | LLM = Model Generator | 自由建模思考，提出模型结构与假设 |
| **Layer 2** | Modeling Knowledge = Constraint / Prior | 方法卡提供 requirements / supports / risks / verification，约束"你声称某方法适用"的资格，但不直接告诉 LLM "必须用 X" |
| **Layer 3** | Evidence | 实验和证据决定模型是否成立 |

### 0.2 核心治理原则

> **Knowledge coverage must constrain evaluation, not constrain creativity.**

- 知识库可以限制"你声称某方法适用"的资格（evaluation gate）
- 知识库**不能**限制 LLM "提出一个新方法/新模型"的自由（creativity）
- 当 LLM 提出知识库中不存在的方法时，应标记为 `alternative_method`，进入人工审查，而非自动判错
- 知识架构的目标是**校准评估仪器**（calibration），而非**干预 Agent 建模过程**（intervention）

### 0.3 本审计的定位

本报告是 **research-layer 仪器校准**（instrument calibration），不是 Agent 干预方案。所有结论用于：
- 诊断当前知识架构在哪一层存在盲区
- 设计未来知识架构 v0.1 的标签体系与字段规范
- 为 e2e_metrics 的 method_selection 指标提供四层语义对齐的改进方向

---

## 1. 当前方法卡库现状

### 1.1 字段完整性检查

对 16 张 YAML 逐张提取核心字段，检查是否扮演 Constraint/Prior 角色：

| card_id | name | family | problem_types | requires | good_for (supports) | risks | validation | P8 决策字段 | 知识深度 |
|---|---|---|---|---|---|---|---|---|---|
| mc-ahp | 层次分析法 AHP | decision_analysis | evaluation, ranking, weighting, decision | ✓ | ✓ | ✓ | ✓ | ✓ | deep+ |
| mc-arima | ARIMA | classical_timeseries | prediction, timeseries | ✓ | ✓ | ✓ | ✓ | ✓ | deep+ |
| mc-entropy-weight | 熵权法 | composite_evaluation | evaluation, ranking, weighting | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-fuzzy-evaluation | 模糊综合评价 | decision_analysis | evaluation, ranking | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-ga | 遗传算法 | metaheuristics | optimization | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-grey-gm11 | 灰色预测 GM(1,1) | classical_timeseries | prediction, timeseries | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-kmeans | KMeans/层次聚类 | unsupervised | clustering, classification | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-lstm | LSTM/GRU | timeseries_learning | prediction, timeseries, classification | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-monte-carlo | 蒙特卡洛模拟 | uncertainty_propagation | uncertainty, simulation, prediction | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-nsga2 | NSGA-II | multi_objective_optimization | optimization, multi-objective | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-ols | 最小二乘回归 | statistical_modeling | fitting, prediction | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-pca | 主成分分析 | dimensionality_reduction | dimensionality-reduction, evaluation | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-pso | 粒子群优化 | metaheuristics | optimization | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-sa | 模拟退火 | metaheuristics | optimization | ✓ | ✓ | ✓ | ✓ | ✗ | deep |
| mc-topsis | TOPSIS | composite_evaluation | evaluation, ranking | ✓ | ✓ | ✓ | ✓ | ✓ | deep+ |
| mc-xgboost | XGBoost/LightGBM | supervised_learning | classification, prediction | ✓ | ✓ | ✓ | ✓ | ✓ | deep+ |

**字段完整性结论**：
- 16/16 张卡均具备 `requires`（requirements）、`good_for`（supports）、`risks`、`validation`（verification）四字段，**结构上全部扮演 Constraint/Prior 角色**，不存在仅 name+family 的 shallow 卡。
- 4/16 张卡（mc-ahp, mc-arima, mc-topsis, mc-xgboost）额外具备 P8 竞争智能字段（objective_types / applicability / risk / evidence_requirements / costs / robustness 等），评级为 **deep+**。
- 12/16 张卡具备核心四字段但无 P8 扩展，评级为 **deep（core only）**。
- **无 shallow / medium 卡**——当前卡库的问题不是"卡太浅"，而是"卡的覆盖面太窄"（见第 2 节）。

### 1.2 family 分布

| family | 数量 | 卡片 |
|---|---|---|
| metaheuristics | 3 | mc-ga, mc-pso, mc-sa |
| decision_analysis | 2 | mc-ahp, mc-fuzzy-evaluation |
| classical_timeseries | 2 | mc-arima, mc-grey-gm11 |
| composite_evaluation | 2 | mc-entropy-weight, mc-topsis |
| unsupervised | 1 | mc-kmeans |
| timeseries_learning | 1 | mc-lstm |
| uncertainty_propagation | 1 | mc-monte-carlo |
| multi_objective_optimization | 1 | mc-nsga2 |
| statistical_modeling | 1 | mc-ols |
| dimensionality_reduction | 1 | mc-pca |
| supervised_learning | 1 | mc-xgboost |

**缺失的 family**（从 benchmark 36 题 core_methods 反推）：
`kinematics`, `geometric_modeling`, `dynamic_programming`, `MDP`, `game_theory`, `PDE`（heat_equation / wave_equation）, `finite_difference`, `queuing_theory`, `heat_transfer`, `ODE_modeling`, `integer_programming`, `linear_programming`, `graph_search`, `spatial_geometry`, `traffic_flow_modeling`, `event_driven_simulation`, `parameter_inversion`, `radon_transform`, `optical_interference`, `calendar_algorithm`, `vibration_dynamics`, `force_equilibrium`, `hydraulic_modeling`, `mixed_effects_model`, `signal_smoothing`, `colorimetric_modeling` 等。

---

## 2. 四层知识结构覆盖分析

### 2.1 四层标签体系定义

| 层 | 标签集 | 说明 |
|---|---|---|
| **L1 Problem Structure** | motion/geometry, network/traffic, scheduling, diffusion, competition/game, decision, uncertainty, data/evaluation | 问题的物理/结构类型 |
| **L2 Modeling Pattern** | state transition, conservation law, flow balance, distance/geometry, resource constraint, queue, spatial-temporal field, interaction/game | 建模时的核心模式/机理 |
| **L3 Mathematical Formulation** | optimization, differential equation, graph, probability, statistics, linear algebra | 数学表述形式 |
| **L4 Solver/Algorithm** | numerical PDE, DP, Monte Carlo, GA, regression, clustering | 求解算法类别 |

### 2.2 16 张卡的四层覆盖标注

| card_id | family | L1 Problem Structure | L2 Modeling Pattern | L3 Formulation | L4 Solver |
|---|---|---|---|---|---|
| mc-ahp | decision_analysis | decision, data/evaluation | — | linear algebra, optimization | — |
| mc-arima | classical_timeseries | data/evaluation | state transition | statistics, probability | regression |
| mc-entropy-weight | composite_evaluation | decision, data/evaluation | — | statistics, probability | — |
| mc-fuzzy-evaluation | decision_analysis | decision, uncertainty | — | probability, statistics | — |
| mc-ga | metaheuristics | — | — | optimization | GA |
| mc-grey-gm11 | classical_timeseries | data/evaluation | state transition | differential equation (grey DE), statistics | regression |
| mc-kmeans | unsupervised | data/evaluation | — | statistics, linear algebra | clustering |
| mc-lstm | timeseries_learning | data/evaluation | state transition | statistics | regression |
| mc-monte-carlo | uncertainty_propagation | uncertainty | — | probability, statistics | Monte Carlo |
| mc-nsga2 | multi_objective_optimization | decision | — | optimization | GA (evolutionary) |
| mc-ols | statistical_modeling | data/evaluation | — | statistics, linear algebra | regression |
| mc-pca | dimensionality_reduction | data/evaluation | — | linear algebra, statistics | — |
| mc-pso | metaheuristics | — | — | optimization | — *(metaheuristic, 不在 L4 标签集)* |
| mc-sa | metaheuristics | — | — | optimization | — *(metaheuristic, 不在 L4 标签集)* |
| mc-topsis | composite_evaluation | decision, data/evaluation | distance/geometry | linear algebra, statistics | — |
| mc-xgboost | supervised_learning | data/evaluation | — | statistics | regression |

> **标注说明**：
> - "—" 表示该卡不覆盖该层的任何标签（solver-agnostic 卡如 GA/PSO/SA 在 L1/L2 层天然为空）。
> - mc-grey-gm11 的 "differential equation" 是灰色微分方程（弱形式），非严格 PDE/ODE。
> - mc-pso / mc-sa 是重要的元启发式求解器，但当前 L4 标签集（numerical PDE, DP, Monte Carlo, GA, regression, clustering）未包含 "metaheuristic optimization" 类别——这是 **L4 标签体系本身的缺口**，不是卡的问题。

### 2.3 四层覆盖率统计

#### L1 Problem Structure（8 个标签）

| 标签 | 覆盖卡片数 | 覆盖卡片 | 状态 |
|---|---|---|---|
| motion/geometry | 0 | — | **缺失** |
| network/traffic | 0 | — | **缺失** |
| scheduling | 0 | — | **缺失** |
| diffusion | 0 | — | **缺失** |
| competition/game | 0 | — | **缺失** |
| decision | 5 | mc-ahp, mc-entropy-weight, mc-fuzzy-evaluation, mc-nsga2, mc-topsis | 覆盖 |
| uncertainty | 2 | mc-fuzzy-evaluation, mc-monte-carlo | 覆盖 |
| data/evaluation | 10 | mc-arima, mc-entropy-weight, mc-grey-gm11, mc-kmeans, mc-lstm, mc-ols, mc-pca, mc-topsis, mc-xgboost (+mc-fuzzy-evaluation) | 覆盖 |

**L1 覆盖率 = 3/8 = 37.5%**
- 5/8 标签完全缺失：motion/geometry, network/traffic, scheduling, diffusion, competition/game
- 这 5 个缺失标签恰好对应国赛 A 题（连续力学/几何/热传导）和 B 题（离散调度/博弈/交通）的核心问题结构

#### L2 Modeling Pattern（8 个标签）

| 标签 | 覆盖卡片数 | 覆盖卡片 | 状态 |
|---|---|---|---|
| state transition | 3 | mc-arima, mc-grey-gm11, mc-lstm | 覆盖（但仅时序语境） |
| conservation law | 0 | — | **缺失** |
| flow balance | 0 | — | **缺失** |
| distance/geometry | 1 | mc-topsis | 覆盖（但仅评价排序语境） |
| resource constraint | 0 | — | **缺失** |
| queue | 0 | — | **缺失** |
| spatial-temporal field | 0 | — | **缺失** |
| interaction/game | 0 | — | **缺失** |

**L2 覆盖率 = 2/8 = 25%**
- 6/8 标签完全缺失
- state transition 仅在时间序列预测语境下被覆盖（ARIMA/GM/LSTM 的递推结构），**不覆盖决策语境下的 MDP 状态转移**
- distance/geometry 仅在 TOPSIS 的"距离理想点"语境下被覆盖，**不覆盖几何建模中的空间距离/轨迹约束**

#### L3 Mathematical Formulation（6 个标签）

| 标签 | 覆盖卡片数 | 覆盖卡片 | 状态 |
|---|---|---|---|
| optimization | 5 | mc-ahp, mc-ga, mc-nsga2, mc-pso, mc-sa | 覆盖 |
| differential equation | 1 | mc-grey-gm11 (grey DE, 弱形式) | 弱覆盖 |
| graph | 0 | — | **缺失** |
| probability | 4 | mc-arima, mc-entropy-weight, mc-fuzzy-evaluation, mc-monte-carlo | 覆盖 |
| statistics | 11 | mc-arima, mc-entropy-weight, mc-fuzzy-evaluation, mc-grey-gm11, mc-kmeans, mc-lstm, mc-monte-carlo, mc-ols, mc-pca, mc-topsis, mc-xgboost | 强覆盖 |
| linear algebra | 5 | mc-ahp, mc-kmeans, mc-ols, mc-pca, mc-topsis | 覆盖 |

**L3 覆盖率 = 5/6 = 83.3%**（若将 grey DE 视为弱覆盖则为 4.5/6 = 75%）
- graph 完全缺失（图论/网络建模无对应卡）
- differential equation 仅有灰色微分方程的弱覆盖，**无 ODE/PDE 卡**
- statistics 是覆盖最强的层（11/16 卡涉及），反映当前卡库高度偏向数据驱动型方法

#### L4 Solver/Algorithm（6 个标签）

| 标签 | 覆盖卡片数 | 覆盖卡片 | 状态 |
|---|---|---|---|
| numerical PDE | 0 | — | **缺失** |
| DP | 0 | — | **缺失** |
| Monte Carlo | 1 | mc-monte-carlo | 覆盖 |
| GA | 2 | mc-ga, mc-nsga2 | 覆盖 |
| regression | 5 | mc-arima, mc-grey-gm11, mc-lstm, mc-ols, mc-xgboost | 强覆盖 |
| clustering | 1 | mc-kmeans | 覆盖 |

**L4 覆盖率 = 4/6 = 66.7%**
- numerical PDE 和 DP 完全缺失——这两个恰好是国赛 A 题（PDE 数值求解）和 B 题（动态规划）的核心求解器
- **L4 标签体系缺口**：metaheuristic optimization（PSO/SA）、analytical methods（AHP/熵权/TOPSIS 的闭式计算）、dimensionality reduction（PCA）未被纳入标签集

### 2.4 四层覆盖总览

| 层 | 标签数 | 已覆盖 | 覆盖率 | 缺失标签 |
|---|---|---|---|---|
| L1 Problem Structure | 8 | 3 | **37.5%** | motion/geometry, network/traffic, scheduling, diffusion, competition/game |
| L2 Modeling Pattern | 8 | 2 | **25.0%** | conservation law, flow balance, resource constraint, queue, spatial-temporal field, interaction/game |
| L3 Mathematical Formulation | 6 | 5 (含1弱) | **83.3%** (75% 严格) | graph; differential equation 仅弱覆盖 |
| L4 Solver/Algorithm | 6 | 4 | **66.7%** | numerical PDE, DP |

**关键发现**：覆盖率从 L1 → L2 → L3 → L4 呈现 **U 型曲线**（37.5% → 25% → 83.3% → 66.7%）。
- L3（数学表述）和 L4（求解算法）覆盖较好，因为当前卡库本质上是"算法卡"——每张卡对应一个具体算法
- L1（问题结构）和 L2（建模模式）覆盖极差，因为**没有任何卡从问题结构或建模机理的角度组织知识**
- **最根本的缺失在 L2 Modeling Pattern（25%）**——这是连接"问题是什么"和"用什么数学"的中间层，当前完全断裂

---

## 3. 5 题知识结构映射

### 3.1 映射表

基于 benchmark `core_methods` + GT manifest `model_family_hint` / `problem_type` / `tags` 交叉验证：

| Problem | benchmark family | core_methods (benchmark) | model_family_hint (manifest) | L1 Structure | L2 Pattern | L3 Formulation | L4 Solver | method_selection |
|---|---|---|---|---|---|---|---|---|
| **2024_A** | 几何运动, 综合 | kinematics, geometric_modeling, numerical_solution | multibody_dynamics + differential_geometry + numerical_optimization | motion/geometry | trajectory + collision detection + geometric constraint | differential equation (ODE) + optimization + linear algebra | numerical optimization + kinematics simulation | **0** |
| **2022_C** | 数据+评价+决策 | clustering, discriminant_analysis, PCA, statistical_analysis | statistical_classification / regression / clustering / pca / correlation | data/evaluation, decision | (data-driven, 无物理模式) | statistics + linear algebra | clustering + regression + dimensionality reduction | **100** |
| **2020_B** | 离散调度/博弈 | dynamic_programming, MDP, game_theory, Monte_Carlo | dynamic_programming / resource_allocation / game_theory / MDP / integer_programming | competition/game, scheduling, decision | state transition (MDP) + resource constraint + interaction/game | optimization + probability | DP + game theory + Monte Carlo | **0** |
| **2018_A** | 热传导/温度场 | heat_equation_PDE, parameter_inversion, optimization | heat_conduction_pde / finite_difference / numerical_optimization / inverse_problem | diffusion | spatial-temporal field + conservation law (energy) | differential equation (PDE) + optimization | numerical PDE (finite difference) + optimization | **0** |
| **2019_C** | 交通/网络 | queuing_analysis, optimization, decision_modeling | queueing_theory / decision_analysis / optimization / monte_carlo_simulation / game_theory | network/traffic, decision | queue + flow balance + interaction/game | optimization + probability + statistics | queuing + optimization + Monte Carlo + decision | **100** |

### 3.2 映射验证与修正说明

- **2024_A**：参考框架原标注 "geometric constraints + ODE"，manifest 确认 `multibody_dynamics + differential_geometry`，benchmark 确认 `kinematics + geometric_modeling`。L3 补充 linear algebra（螺线参数化需要坐标变换）。L4 修正为 "numerical optimization + kinematics simulation"（非单纯 numerical optimization）。
- **2022_C**：参考框架标注 "statistical"，manifest 确认 `statistical_classification / regression / clustering / pca`，benchmark 确认 `clustering + discriminant_analysis + PCA + statistical_analysis`。L1 补充 decision（Q3 分类判别属于决策）。映射与参考框架一致。
- **2020_B**：参考框架标注 "state transition (MDP)"，manifest 确认 `dynamic_programming / MDP / game_theory`，benchmark 确认 `dynamic_programming, MDP, game_theory, Monte_Carlo`。L1 补充 scheduling（资源分配/行走计划本质是调度）。L2 补充 resource constraint（负重/资源消耗约束是核心）。
- **2018_A**：参考框架标注 "PDE (heat equation)"，manifest 确认 `heat_conduction_pde / finite_difference / inverse_problem`，tags 确认 `heat_transfer, pde, finite_difference, optimization, inverse_problem`。L2 补充 conservation law（热传导方程基于能量守恒）。L4 修正为 "numerical PDE (finite difference) + optimization"（parameter_inversion 需要优化）。
- **2019_C**：参考框架标注 "flow/queue/scheduling"，manifest 确认 `queueing_theory / decision_analysis / optimization / monte_carlo_simulation / game_theory`，benchmark 确认 `queuing_analysis, optimization, decision_modeling`。L1 修正为 network/traffic + decision（非 scheduling）。L2 补充 interaction/game（司机与乘客的双边匹配/博弈）。

---

## 4. 缺失层定位分析

### 4.1 method_selection = 0 的三题

#### 2024_A（板凳龙）— chosen=mc-monte-carlo, ref=[kinematics, geometric_modeling, numerical_solution]

| 层 | 该题需要 | 当前卡库是否有 | 缺口判定 |
|---|---|---|---|
| L1 | motion/geometry | **0 卡覆盖** | 完全缺失 |
| L2 | trajectory, collision detection, geometric constraint | state transition 有时序语境覆盖，但**无几何/运动语境**；collision/geometric constraint 完全缺失 | 完全缺失 |
| L3 | ODE + optimization + linear algebra | optimization ✓, linear algebra ✓, differential equation 仅 grey DE 弱覆盖 | PDE/ODE 弱覆盖 |
| L4 | numerical optimization + kinematics simulation | GA/PSO/SA 覆盖通用优化，但**无运动学仿真卡** | 部分缺失 |

**最根本缺失：L1 Problem Structure**。motion/geometry 标签零覆盖，导致 LLM 无法从问题结构层面识别"这是一个运动学/几何问题"，退而选择了最接近"仿真"语义的 mc-monte-carlo（family=uncertainty_propagation），但该家族与 kinematics/geometric_modeling 无任何匹配。

**级联效应**：L1 缺失 → L2 无法激活 trajectory/collision 模式 → L3 无法选择 ODE 表述 → L4 无法选择运动学数值求解器。LLM 只能在"通用优化/仿真"卡中随机选择。

---

#### 2020_B（穿越沙漠）— chosen=mc-ga, ref=[dynamic_programming, MDP, game_theory, Monte_Carlo]

| 层 | 该题需要 | 当前卡库是否有 | 缺口判定 |
|---|---|---|---|
| L1 | competition/game, scheduling, decision | decision ✓ (5卡), competition/game **0卡**, scheduling **0卡** | 部分缺失 |
| L2 | state transition (MDP), resource constraint, interaction/game | state transition 有时序语境覆盖但**无决策语境**；resource constraint **0卡**；interaction/game **0卡** | 完全缺失 |
| L3 | optimization, probability | optimization ✓, probability ✓ | 覆盖 |
| L4 | DP, game theory, Monte Carlo | Monte Carlo ✓ (mc-monte-carlo), DP **0卡**, game theory **0卡** | 严重缺失 |

**最根本缺失：L4 Solver + L2 Pattern 双重缺失**。
- L4 无 DP 卡、无 game theory 卡——这两个是该题的核心求解器
- L2 无 resource constraint、interaction/game 模式——LLM 无法从建模机理层面识别"这是一个资源约束下的序贯决策+博弈问题"
- LLM 选择了 mc-ga（metaheuristics）作为通用优化器的替代，但 GA 与 DP/MDP/game_theory 是不同的求解范式

**注意**：mc-monte-carlo 存在且 ref 包含 Monte_Carlo，理论上可以命中。但 LLM 的 top1 选择了 mc-ga，说明**即使 L4 有部分覆盖，L1/L2 的缺失导致 LLM 无法正确排序候选卡**。

---

#### 2018_A（高温作业服装）— chosen=mc-ga, ref=[heat_equation_PDE, parameter_inversion, optimization]

| 层 | 该题需要 | 当前卡库是否有 | 缺口判定 |
|---|---|---|---|
| L1 | diffusion | **0 卡覆盖** | 完全缺失 |
| L2 | spatial-temporal field, conservation law | **0 卡覆盖** | 完全缺失 |
| L3 | PDE + optimization | optimization ✓, differential equation 仅 grey DE 弱覆盖 | PDE 严重缺失 |
| L4 | numerical PDE (finite difference) + optimization | optimization ✓ (GA/PSO/SA), numerical PDE **0卡** | 严重缺失 |

**最根本缺失：L1 + L2 + L4 三层联动缺失**。
- L1 diffusion 零覆盖 → LLM 无法识别"这是一个热传导/扩散问题"
- L2 spatial-temporal field + conservation law 零覆盖 → LLM 无法建立"能量守恒→PDE"的建模路径
- L4 numerical PDE 零覆盖 → 即使建立了 PDE，也无对应求解器卡
- LLM 选择了 mc-ga（metaheuristics）应对 optimization 部分，但完全错过了 PDE 这个核心

**这是 5 题中缺失最严重的一题**：四层中有三层（L1/L2/L4）存在零覆盖标签，L3 也仅有弱覆盖。

---

### 4.2 method_selection = 100 的两题

#### 2022_C（古代玻璃）— 为什么能命中

| 层 | 该题需要 | 当前卡库覆盖 | 覆盖完整性 |
|---|---|---|---|
| L1 | data/evaluation, decision | data/evaluation ✓ (10卡), decision ✓ (5卡) | **完整** |
| L2 | (data-driven, 无物理模式) | N/A | N/A |
| L3 | statistics, linear algebra | statistics ✓ (11卡), linear algebra ✓ (5卡) | **完整** |
| L4 | clustering, regression, dimensionality reduction | clustering ✓ (mc-kmeans), regression ✓ (mc-ols/mc-xgboost/mc-arima/mc-grey-gm11/mc-lstm), PCA ✓ (mc-pca) | **完整** |

**命中原因**：该题的知识结构完全落在当前卡库的"舒适区"内——L1 data/evaluation + L3 statistics + L4 clustering/regression 是覆盖最强的组合。四层中三层完整覆盖，L2 不适用（纯数据驱动问题无物理建模模式）。mc-pca / mc-kmeans / mc-xgboost 直接对应 benchmark 的 core_methods。

**覆盖质量**：高。这是当前卡库设计的目标场景（数据+评价+决策类 C 题）。

---

#### 2019_C（机场出租车）— 为什么能命中

| 层 | 该题需要 | 当前卡库覆盖 | 覆盖完整性 |
|---|---|---|---|
| L1 | network/traffic, decision | network/traffic **0卡**, decision ✓ (5卡) | **部分** |
| L2 | queue, flow balance, interaction/game | queue **0卡**, flow balance **0卡**, interaction/game **0卡** | **缺失** |
| L3 | optimization, probability, statistics | optimization ✓, probability ✓, statistics ✓ | **完整** |
| L4 | queuing, optimization, Monte Carlo, decision | optimization ✓ (mc-ga), Monte Carlo ✓ (mc-monte-carlo), decision ✓ (mc-ahp), queuing **0卡** | **部分** |

**命中原因**：尽管 L1（network/traffic）和 L2（queue/flow balance/interaction）全部缺失，但 L3（optimization/probability/statistics）和 L4（optimization/Monte Carlo/decision）有足够的卡覆盖。LLM 可以在 solver 层面选择 mc-monte-carlo（仿真排队系统）、mc-ahp（决策分析）、mc-ga（优化），这些卡的 family 通过 e2e_metrics 的归一化+紧凑匹配与 benchmark ref 产生交集。

**覆盖质量**：**浅层命中**。命中发生在 L3/L4 solver 层面，但 L1/L2 的问题结构和建模模式完全没有被识别。具体表现：
- 无 queuing_theory 卡，mc-monte-carlo 只是"用仿真近似排队"，不是真正的排队论建模
- 无 network/traffic 问题结构标签，LLM 可能将其误判为"通用决策+优化"问题
- 这种命中是" solver 级别的偶然匹配"，不是"知识架构级别的系统覆盖"

---

### 4.3 缺失层定位总结

| Problem | method_selection | L1 | L2 | L3 | L4 | 最根本缺失层 |
|---|---|---|---|---|---|---|
| 2024_A | 0 | motion/geometry ✗ | trajectory/collision ✗ | ODE 弱 | kinematics ✗ | **L1**（问题结构零覆盖） |
| 2022_C | 100 | ✓ | N/A | ✓ | ✓ | 无（舒适区） |
| 2020_B | 0 | competition/game ✗ scheduling ✗ | resource constraint ✗ interaction/game ✗ | ✓ | DP ✗ game theory ✗ | **L4 + L2**（求解器+建模模式双缺） |
| 2018_A | 0 | diffusion ✗ | spatial-temporal ✗ conservation ✗ | PDE 弱 | numerical PDE ✗ | **L1+L2+L4 三层联动** |
| 2019_C | 100 | network/traffic ✗ | queue/flow/interaction ✗ | ✓ | queuing ✗ | 无（L3/L4 浅层命中） |

**核心结论**：
1. **三题 method_selection=0 的根本原因不是"LLM 选了错的卡"，而是"知识架构在 L1/L2 层没有对应标签，导致 LLM 无法从问题结构层面正确路由"**。
2. e2e_metrics 的 method_selection 仅检查 L4 card family 是否匹配 benchmark core_methods，**完全不检查 L1-L3 层**。这意味着即使 LLM 在 L1/L2 层完全错误，只要 L4 碰巧选了一个 family 匹配的卡，也能得 100 分（如 2019_C 的浅层命中）。
3. **2019_C 的 100 分是"假阳性"**——它在 solver 层面命中，但在问题结构和建模模式层面完全缺失。当前指标无法区分"系统覆盖"和"偶然匹配"。

---

## 5. Calibration 方向清单

> **声明**：以下为 research-layer 仪器校准方向，**不是 Agent 干预方案**。目标是校准知识架构的覆盖盲区与评估指标的语义对齐，不涉及修改 Agent 行为、不新增方法卡、不修改 e2e_metrics.py。

### 5.1 优先建立哪几层

| 优先级 | 层 | 理由 |
|---|---|---|
| **P0** | **L2 Modeling Pattern** | 当前覆盖率最低（25%），是连接问题结构与数学表述的关键中间层，断裂导致 LLM 无法从"问题是什么"推导到"用什么数学" |
| **P0** | **L1 Problem Structure** | 覆盖率 37.5%，5/8 标签缺失，直接对应国赛 A/B 题的核心问题类型；L1 缺失会级联导致 L2-L4 全部失效 |
| **P1** | **L4 Solver/Algorithm** | 需补充 numerical PDE、DP、game theory、queuing 等核心求解器标签；同时扩展标签集纳入 metaheuristic、analytical、dimensionality reduction |
| **P2** | **L3 Mathematical Formulation** | 覆盖率最高（83.3%），仅需补充 graph、强化 differential equation（ODE/PDE）；优先级最低 |

**建议**：v0.1 先建立 **L1 + L2 两层标签体系**（不急于补卡），因为这两层是当前知识架构的"骨架缺失"。L3/L4 的卡可以通过重新标注（retro-tagging）映射到新的 L1/L2 标签上，无需立即新建方法卡。

### 5.2 L1 Problem Structure 标签体系建议

基于 benchmark 36 题的 family 分布，建议 L1 标签集扩展为：

| 标签 | 说明 | benchmark 对应题目 |
|---|---|---|
| motion/geometry | 运动学、几何建模、空间定位 | 2024_A, 2015_A, 2017_A, 2021_A, 2022_B, 2023_B, 2025_A, 2025_B |
| continuous_mechanics | 连续力学、振动、动力学 | 2016_A, 2019_A, 2019_B, 2022_A |
| diffusion/heat_transfer | 热传导、扩散、温度场 | 2018_A, 2020_A |
| network/traffic | 交通流、网络、路网 | 2016_B, 2019_C, 2024_E |
| scheduling/discrete | 离散调度、RGV、生产计划 | 2018_B, 2021_C, 2024_C |
| competition/game | 博弈、多玩家竞争、机制设计 | 2020_B, 2025_D |
| decision/evaluation | 多准则决策、综合评价、排序 | 2015_B, 2017_B, 2018_C, 2020_C, 2022_C, 2023_C, 2025_C, 2025_E |
| uncertainty/data | 不确定性传播、数据分析、统计建模 | 2015_C, 2016_C, 2017_C, 2021_B, 2024_B |
| supply_chain/operations | 供应链、运营、库存 | 2021_C, 2024_C |
| optical/inverse | 光学、反演、图像重建 | 2017_A, 2025_B |

> 从 8 标签扩展到 10 标签，新增 continuous_mechanics、supply_chain/operations、optical/inverse；将原 data/evaluation 拆分为 decision/evaluation 和 uncertainty/data。

### 5.3 L2 Modeling Pattern 标签体系建议

| 标签 | 说明 | 典型对应 |
|---|---|---|
| state_transition | 状态转移（MDP/递推/时序） | 2020_B (MDP), ARIMA/GM/LSTM |
| conservation_law | 守恒律（能量/质量/动量） | 2018_A (能量守恒), 2019_A (连续性方程) |
| flow_balance | 流量平衡（交通流/水流/物流） | 2019_C (出租车流), 2016_B (交通流), 2025_D (水流) |
| distance_geometry | 距离/几何约束（轨迹/碰撞/定位） | 2024_A (螺线/碰撞), 2015_A (影子定位), TOPSIS |
| resource_constraint | 资源约束（负重/预算/容量/时间窗） | 2020_B (水/食物/资金), 2018_B (工序约束) |
| queue | 排队（到达/服务/等待） | 2019_C (出租车排队) |
| spatial_temporal_field | 时空场（温度场/浓度场/压力场） | 2018_A (温度场), 2020_A (回流焊温度场) |
| interaction_game | 交互/博弈（多玩家/双边匹配/机制设计） | 2020_B (多玩家), 2019_C (司机-乘客匹配) |
| statistical_association | 统计关联（相关/回归/分类/聚类） | 2022_C (玻璃成分分析), 2025_E (运动数据分析) |
| inverse_problem | 反问题（参数反演/图像重建/浓度反演） | 2018_A (热参数反演), 2017_C (浓度反演), 2025_B (厚度反演) |

> 从 8 标签扩展到 10 标签，新增 statistical_association 和 inverse_problem。这两个模式在国赛中高频出现但原标签集未覆盖。

### 5.4 方法卡从"方法描述"升级为"Constraint/Prior"的字段规范

当前 16 张卡已具备 requires/good_for/risks/validation 四字段，但要真正扮演四层知识架构中的 Constraint/Prior 角色，建议补充以下字段（**仅设计方向，不实现**）：

| 字段 | 作用 | 当前状态 | 升级方向 |
|---|---|---|---|
| `l1_problem_structures` | 标注该卡适用的 L1 问题结构标签 | **缺失** | 新增，多值枚举 |
| `l2_modeling_patterns` | 标注该卡支持的 L2 建模模式标签 | **缺失** | 新增，多值枚举 |
| `l3_formulations` | 标注该卡对应的 L3 数学表述 | **缺失**（隐含在 name/family 中） | 新增，显式标注 |
| `l4_solver_type` | 标注该卡的 L4 求解器类别 | **缺失**（隐含在 family 中） | 新增，显式标注 |
| `requires` | 适用前提条件 | ✓ 全部具备 | 保持 |
| `supports` (good_for) | 支持的场景 | ✓ 全部具备 | 保持，建议重命名为 `supports` |
| `risks` | 风险与反模式 | ✓ 全部具备 | 保持 |
| `verification` (validation) | 验证方法 | ✓ 全部具备 | 保持，建议重命名为 `verification` |
| `not_for` | 明确不适用的 L1/L2 标签 | **缺失** | 新增，用于约束"你声称某方法适用"的资格 |
| `evidence_requirements` | 使用该方法必须提供的证据 | 4/16 具备（P8 字段） | 推广到全部卡 |

**关键设计原则**：
- `l1_problem_structures` 和 `not_for` 共同构成 **evaluation gate**：如果 LLM 声称某方法适用于一个 `not_for` 中的 L1 标签，evaluator 可以标记为资格不符
- 四层标签字段是**约束性的**（constraint），不是**指令性的**（directive）——它们告诉 LLM "这个方法在什么结构下经过验证可用"，但不告诉 LLM "你必须用这个方法"
- LLM 仍然可以自由提出不在卡库中的方法（alternative_method），但需要提供额外证据

### 5.5 e2e_metrics method_selection 的四层语义对齐方向（仅设计，不修改）

当前 method_selection 仅检查 L4 card family 匹配。建议未来校准方向：

| 维度 | 当前 | 校准方向 |
|---|---|---|
| 检查层级 | 仅 L4 (card family) | 四层分别检查：L1 问题结构识别、L2 建模模式选择、L3 数学表述、L4 求解器 |
| 匹配方式 | family 字符串归一化+紧凑匹配 | 四层标签语义匹配（card.l1_tags ∩ problem.l1_tags） |
| 命中判定 | top3 任一卡 family 命中 ref | 分层计分：L1 识别正确 + L2 模式正确 + L3 表述正确 + L4 求解器正确，加权汇总 |
| alternative 处理 | family 不匹配但卡存在 → alt 标记 | 按层标记：L4 alt 但 L1-L3 正确 = 合理替代；L1 错误 = 结构性误判 |
| 假阳性检测 | 无 | 检测"L4 命中但 L1/L2 错误"的浅层命中（如 2019_C） |

### 5.6 "补方法卡" vs "建知识架构"的层次区分

| 层次 | 动作 | 解决什么问题 | 本审计建议 |
|---|---|---|---|
| **补方法卡**（L4 层） | 新增 mc-dp, mc-pde, mc-queuing, mc-game-theory 等卡 | 解决 L4 solver 覆盖率不足 | 必要但不充分——仅补卡无法解决 L1/L2 的路由问题 |
| **建知识架构**（L1+L2 层） | 建立四层标签体系，对现有 16 卡做 retro-tagging，设计 not_for 约束 | 解决"LLM 无法从问题结构正确路由到方法"的根本问题 | **优先**——这是仪器校准的核心 |
| **校准评估指标**（评估层） | method_selection 从单维 family 匹配升级为四层语义对齐 | 解决"2019_C 假阳性"等评估失真 | 与知识架构同步推进 |

**核心判断**：当前 method_selection=0 的三题，**即使补齐了 L4 卡（DP/PDE/queuing），如果 L1/L2 标签体系不建立，LLM 仍然可能选错卡**。因为问题的根源不是"没有对应的卡"，而是"LLM 无法识别问题属于哪个结构类别，从而无法激活正确的卡选择路径"。

---

## 6. 审计结论

1. **16 张方法卡结构完整**：全部具备 requires/supports/risks/verification 四字段，知识深度均为 deep 或 deep+，不存在 shallow 卡。问题不是"卡太浅"，而是"覆盖面太窄"。

2. **四层覆盖呈 U 型失衡**：L3 (83.3%) > L4 (66.7%) > L1 (37.5%) > L2 (25%)。L1/L2 是知识架构的骨架，当前严重缺失。

3. **三题 method_selection=0 的根本原因在 L1/L2 层**：
   - 2024_A：L1 motion/geometry 零覆盖
   - 2020_B：L2 resource constraint/interaction + L4 DP/game theory 双缺
   - 2018_A：L1 diffusion + L2 spatial-temporal/conservation + L4 numerical PDE 三层联动缺失

4. **2019_C 的 100 分是浅层命中（假阳性）**：L1/L2 完全缺失，但 L3/L4 solver 层面碰巧匹配。当前指标无法区分系统覆盖与偶然匹配。

5. **Calibration 优先级**：P0 建立 L1+L2 标签体系（不急于补卡），P1 补充 L4 solver 标签，P2 完善 L3。核心是"建知识架构"优先于"补方法卡"。

6. **治理原则**：知识架构约束 evaluation（资格审查），不约束 creativity（建模自由）。LLM 提出卡库外方法时标记为 alternative_method 进入人工审查，不自动判错。

---

*本报告为仪器校准文档，所有方向仅作设计参考，未执行任何修改操作。*
