# 离散优化域（Discrete Optimization）知识架构校准研究

> **研究代理**：离散优化域领域研究代理
> **研究范围**：L1 scheduling / L2 resource constraint + state transition(决策语境) / L3 optimization(graph, integer programming, nonlinear programming) / L4 DP + branch-and-bound + MILP solver + heuristic
> **研究日期**：2026-09-08
> **治理原则**：方法卡 = Constraint/Prior/Validation，不是答案库。Knowledge coverage must constrain evaluation, not constrain creativity.
> **状态真源**：本文所有结论均附证据记录（claim/evidence/source/source_type/confidence/reasoning）

---

## 0. 研究框架与四层严格区分

本研究严格遵循四层标签体系的语义边界：

| 层 | 语义 | 本域标签 | 禁止混淆 |
|---|---|---|---|
| **L1 Problem Structure** | 问题的物理/结构类型 | scheduling | ≠ 求解算法 |
| **L2 Modeling Pattern** | 建模时的核心机理/模式 | resource constraint, state transition(决策语境) | ≠ 数学约束语法；≠ 算法名 |
| **L3 Mathematical Formulation** | 数学表述形式 | optimization, graph, integer programming, nonlinear programming, linear programming | ≠ 求解算法；optimization ≠ GA/DP |
| **L4 Solver/Algorithm** | 求解算法类别 | DP, branch-and-bound, MILP solver, heuristic | DP formulation(L3) ≠ DP algorithm(L4) |

**核心区分原则**：
- `optimization` 是 L3 数学表述（目标函数+约束的形式化），`GA/DP/MILP` 是 L4 求解算法
- `DP formulation`（Bellman方程作为数学表述）属于 L3；`DP algorithm`（值迭代/策略迭代/表格递推）属于 L4
- `resource constraint` 是 L2 建模机理（"有限资源如何约束决策"的建模思路），不是 L3 的 `Ax ≤ b` 约束语法
- `state transition` 在决策语境下指 MDP/序贯决策的状态演化机理，不同于时间序列预测中的递推结构

---

## 1. L1 标签研究：Scheduling（调度问题结构）

### 1.1 定义

**Scheduling（调度）**是在时间维度上将有限资源（机器、人力、设备、时间窗）分配给一组任务（作业、工序、活动），以优化一个或多个目标函数（如最大完工时间 Cmax、总延迟、吞吐量、资源利用率）的问题结构。

> **核心机理**：调度的本质是**资源约束下的时序决策**——"谁在什么时间用什么资源做什么事"。它天然包含三个要素：(1) 任务集合及其工艺约束（先后序）；(2) 资源集合及其容量约束；(3) 时间维度上的分配决策。

### 1.2 调度问题的分类体系

调度理论采用 **Graham 三域表示法（α|β|γ）** 进行标准化分类（Stanford MS&E 324, Dartmouth CO 454）：

| 域 | 含义 | 典型取值 |
|---|---|---|
| **α（机器环境）** | 资源的拓扑结构 | `1` 单机；`Pm` 同速并行机；`Qm` 匀速并行机；`Rm` 无关并行机；`Fm` 流水车间；`Jm` 作业车间；`Om` 开放车间 |
| **β（作业/约束特征）** | 任务的附加约束 | `r_j` 释放时间；`d_j` 截止期；`prec` 优先约束；`s_jk` 准备时间；`M_j` 机器可用性 |
| **γ（目标函数）** | 优化目标 | `Cmax` 最大完工时间；`ΣC_j` 总完工时间；`Lmax` 最大延迟；`ΣT_j` 总延迟；`Σw_jC_j` 加权总完工时间 |

**主要调度类型**：

| 类型 | 特征 | 复杂度 | 典型应用 |
|---|---|---|---|
| **单机调度 (1‖γ)** | 一台机器，所有任务依次加工 | 多数可多项式求解（SPT/EDD等规则） | 单瓶颈机床、单服务器 |
| **并行机调度 (Pm‖γ)** | 多台同构机器，任务可在任意一台加工 | `P2‖Cmax` 已 NP-hard | 多CNC加工、多服务器负载均衡 |
| **流水车间 (Fm‖Cmax)** | 所有任务按相同顺序经过所有机器 | `F2‖Cmax` 可多项式（Johnson规则），`F3‖Cmax` NP-hard | 生产线、装配线 |
| **作业车间 (Jm‖Cmax)** | 每个任务有独立的工艺路线和机器序列 | 强 NP-hard，是调度理论的核心难题 | 柔性制造系统、机加工车间 |
| **开放车间 (Om‖γ)** | 任务的工序顺序无约束 | `O2‖Cmax` 可多项式，一般 NP-hard | 维修车间、诊断系统 |

### 1.3 调度问题的数学表述

调度问题可以表述为多种 L3 数学形式：

**(1) 整数规划（Integer Programming）表述**

以作业车间调度 Jm‖Cmax 为例（Dartmouth CO 454, arXiv 2407.18111）：

```
决策变量：
  x_{(i,j'),(i,j)} ∈ {0,1}：机器上工序 (i,j') 是否先于 (i,j)
  s_{i,j} ≥ 0：工序 (i,j) 的开始时间
  C ≥ 0：最大完工时间

目标：min C

约束：
  s_{i,j} + p_{i,j} ≤ s_{i,j+1}              （工艺优先约束）
  s_{i,j} + p_{i,j} ≤ s_{i',j} + M(1 - x_{(i,j),(i',j)})  （资源互斥约束1）
  s_{i',j} + p_{i',j} ≤ s_{i,j} + M·x_{(i,j),(i',j)}        （资源互斥约束2）
  s_{i,j} + p_{i,j} ≤ C                       （完工时间定义）
```

其中 M 是大 M 常数（通常取所有加工时间之和）。这是典型的 **disjunctive formulation（析取规划）**。

**(2) 图论（Graph）表述**

调度问题可建模为**析取图（disjunctive graph）**：节点表示工序，合取弧（conjunctive arcs）表示工艺优先关系，析取弧（disjunctive arcs）连接同一机器上的工序对，表示二者的先后顺序待定。调度 = 为每条析取弧定向，使图无环且 Cmax 最小。

**(3) 组合优化（Combinatorial Optimization）表述**

调度本质是在有限排列/分配空间中搜索最优解：`min_{π ∈ Π} f(π)`，其中 Π 是所有可行调度的集合。

### 1.4 调度的常用求解器（L4）

| 求解器类别 | 代表方法 | 适用场景 | 最优性保证 |
|---|---|---|---|
| **精确算法** | 分支定界 (B&B)、分支切割 (B&C)、动态规划 | 小规模（n ≤ 20-50） | ✓ 全局最优 |
| **MILP 求解器** | Gurobi, CPLEX, SCIP, scipy.optimize.milp | 中等规模，结构化约束 | ✓（在时间限制内） |
| **构造启发式** | 优先调度规则 (SPT/EDD/MWR)、Johnson规则、NEH | 大规模，快速求可行解 | ✗ |
| **元启发式** | GA, SA, PSO, 禁忌搜索, 蚁群算法 | 大规模 NP-hard，近优解 | ✗ |
| **离散事件仿真** | DES + 调度策略搜索 | 动态调度、随机环境、碰撞检测 | ✗（策略评估） |
| **强化学习** | DQN, PPO, 多智能体 RL | 在线动态调度、不确定环境 | ✗ |

### 1.5 调度与 resource constraint + state transition 的关系

- **调度 ⊃ resource constraint**：调度问题的核心约束就是资源约束（机器容量、时间窗、人力）。RCPSP（Resource-Constrained Project Scheduling Problem）是调度与资源约束交叉的经典问题。
- **调度 ⊃ state transition**：动态调度（如 RGV 实时调度）中，系统状态（各机器加工状态、RGV位置、队列长度）随事件演化，决策基于当前状态。这是 MDP 状态转移在调度中的体现。
- **静态调度**（所有参数已知，一次性制定计划）主要是 resource constraint + optimization；
- **动态调度**（参数随时间变化/未知，需在线决策）还涉及 state transition + stochastic optimization。

### 1.6 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 调度三域表示法 α\|β\|γ 是标准分类体系 | Stanford MS&E 324 Lecture 2 明确给出 1/Pm/Qm/Rm/Om/Fm/Jm 分类 | Stanford University course materials | Tier 1 | 高 |
| 作业车间 Jm‖Cmax 是强 NP-hard | arXiv 2407.18111 及 Dartmouth CO 454 均确认 | peer-reviewed preprint + university course | Tier 1 | 高 |
| 调度可表述为析取图（disjunctive graph） | Wiley 论文及 Dartmouth 讲义均使用析取弧建模机器互斥 | Wiley peer-reviewed + university course | Tier 1 | 高 |
| 调度的整数规划表述使用大 M 析取约束 | Dartmouth CO 454 Lecture 19-21 给出完整 IP 公式 | university course | Tier 1 | 高 |
| F2‖Cmax 可用 Johnson 规则多项式求解 | 调度理论经典结论，多来源交叉验证 | textbook-level | Tier 1 | 高 |

---

## 2. L2 标签研究

### 2.1 Resource Constraint（资源约束建模模式）

#### 2.1.1 定义

**Resource Constraint（资源约束）**作为 L2 Modeling Pattern，是指在建模时将"有限资源的可用性"作为核心机理来构造问题结构的建模模式。它回答的是：**"稀缺资源如何限制可行决策空间？"**

> **关键区分**：resource constraint 不是 L3 层面的 `Ax ≤ b` 数学约束语法，而是 L2 层面的**建模机理**——即识别问题中哪些是有限资源、资源如何被任务消耗、资源容量如何约束决策序列。同一个 resource constraint 模式可以表述为 LP、IP、NLP 等多种 L3 形式。

#### 2.1.2 资源类型分类

| 资源类型 | 定义 | 典型例子 | 建模特征 |
|---|---|---|---|
| **容量资源 (Capacity)** | 单位时间内可处理量有上限 | 机器产能、仓库容量、带宽 | 累积约束 `cumulative([s_i],[d_i],[r_ik],R_k)` |
| **预算资源 (Budget)** | 总花费有上限 | 资金、成本 | 全局约束 `Σ c_i x_i ≤ B` |
| **人力资源 (Labor)** | 可用人数/工时有限 | 工人、操作员、专家 | 时间依赖的容量约束 |
| **机器资源 (Machine)** | 设备数量/可用性有限 | CNC、RGV、服务器 | 互斥约束（同一时刻一台机器一个任务） |
| **时间资源 (Time)** | 时间窗/截止期有限 | 交付期、班次、季节 | 时间窗约束 `r_j ≤ s_j ≤ d_j` |
| **库存资源 (Inventory)** | 存储/持有量有限 | 原材料、半成品、成品 | 状态转移中的库存平衡约束 |
| **共享资源 (Shared Resource)** | 多任务/多玩家竞争同一资源 | 公共矿山、村庄、道路 | 外部性/拥塞效应（k人共享时效率下降） |

#### 2.1.3 核心机理

资源约束建模模式的核心机理包括：

1. **资源消耗建模**：每个决策/行动消耗多少资源？消耗是线性的还是非线性的？（如 2020_B 中行走消耗 2 倍基础消耗，挖矿消耗 3 倍）
2. **资源容量约束**：任意时刻资源使用量不超过容量。对于可更新资源（renewable，如机器时间），是逐时段约束；对于不可更新资源（non-renewable，如预算），是全局约束。
3. **资源耦合**：多种资源之间可能存在耦合约束（如 2020_B 中水和食物的总负重不能超过上限，二者非独立）。
4. **资源外部性**：多玩家共享资源时，个人消耗受他人行为影响（如 2020_B Q3 中 k 人同行消耗 2k 倍，k 人同矿收益 1/k）。

#### 2.1.4 与 L1/L3/L4 的关系

| 关系 | 说明 |
|---|---|
| **与 L1 scheduling** | 调度是资源约束在时间维度上的具体化。scheduling ⊃ resource constraint |
| **与 L1 competition/game** | 多玩家竞争共享资源时，resource constraint 产生博弈外部性 |
| **与 L3 optimization** | 资源约束定义了优化问题的可行域。`min f(x) s.t. resource_constraints(x)` |
| **与 L3 integer programming** | 离散资源分配（如任务-机器指派）自然产生 0-1 整数变量 |
| **与 L3 graph** | 资源网络（如交通网、供应链）可建模为图，资源流为图上的流 |
| **与 L4 DP** | 资源水平常作为 DP 状态变量（如 2020_B 的水量/食物量） |
| **与 L4 MILP** | MILP 求解器天然处理资源约束的线性/整数形式 |

#### 2.1.5 典型应用场景

- **生产计划**：产能约束 + 库存平衡 + 需求满足 → 多周期生产计划
- **项目调度 (RCPSP)**：活动优先约束 + 可再生资源容量约束 → 最小化项目工期
- **背包问题**：容量约束下的物品选择 → 0-1 背包/多维背包
- **资源分配**：预算约束下的活动分配 → 非线性/整数规划
- **路径规划**：燃料/时间资源约束下的路径选择 → 带资源约束的最短路
- **2020_B 穿越沙漠**：水/食物/资金/负重的多重资源约束 → DP/MDP

### 2.2 State Transition（状态转移，决策语境）

#### 2.2.1 定义

**State Transition（状态转移）**在决策语境下，是指将问题建模为**马尔可夫决策过程（MDP）**或多阶段决策过程时，系统状态随决策动作演化的建模机理。它回答的是：**"在当前状态下做出决策后，系统如何演化到下一状态？"**

> **关键区分**：本标签特指**决策语境**下的状态转移（MDP/序贯决策/控制），不同于时间序列预测中的递推结构（ARIMA 的 `y_t = c + φy_{t-1} + ε_t`）。前者的核心是**动作驱动的状态演化 + 累积奖励优化**；后者的核心是**数据驱动的预测**。

#### 2.2.2 MDP 形式化

MDP 定义为五元组 `(S, A, P, R, γ)`（Stanford CME 241, INRIA Lille, PKU BICMR）：

| 元素 | 定义 | 2020_B 对应 |
|---|---|---|
| **S 状态空间** | 系统所有可能状态的集合 | `(day, position, water, food, money)` |
| **A 动作空间** | 每个状态下可选择的动作 | `{停留, 行走至相邻区域, 挖矿}`（受天气约束） |
| **P 状态转移概率** | `P(s'|s,a)`：在状态 s 执行动作 a 后到达 s' 的概率 | 天气随机导致资源消耗随机（Q2） |
| **R 奖励函数** | `R(s,a,s')`：转移的即时奖励/成本 | 资金变化（挖矿收益 - 资源消耗成本） |
| **γ 折扣因子** | 未来奖励的折扣率 | 有限时域问题通常 γ=1 |

#### 2.2.3 Bellman 最优性方程

确定性 DP（Q1 天气全已知）：
$$V_t(s) = \max_{a \in A(s)} \left\{ r_t(s,a) + V_{t+1}(s') \right\}$$

随机性 MDP（Q2 仅知当天天气）：
$$V^*(s) = \max_{a \in A(s)} \left\{ R(s,a) + \gamma \sum_{s' \in S} P(s'|s,a) V^*(s') \right\}$$

动作价值函数：
$$Q^*(s,a) = R(s,a) + \gamma \sum_{s'} P(s'|s,a) V^*(s')$$

#### 2.2.4 马尔可夫性（Markov Property）

状态转移建模的核心前提是**马尔可夫性**：给定当前状态，未来与过去条件独立。即当前状态必须包含所有对未来决策相关的历史信息。

> **常见建模错误**：状态定义不完整导致马尔可夫性不成立。例如 2020_B 中如果状态只包含 `(day, position)` 而不包含 `(water, food)`，则无法正确计算未来的资源消耗和生存概率，违反马尔可夫性。

#### 2.2.5 与 L1/L3/L4 的关系

| 关系 | 说明 |
|---|---|
| **与 L1 scheduling** | 动态调度是 MDP 的典型应用：状态 = 系统加工状态，动作 = 调度决策 |
| **与 L1 decision** | 所有多阶段决策问题天然涉及状态转移 |
| **与 L2 resource constraint** | 资源水平是状态的核心维度；状态转移方程中包含资源消耗 |
| **与 L3 optimization** | Bellman 方程本身就是一种递归优化表述 |
| **与 L3 probability** | 随机 MDP 的转移概率矩阵是概率模型 |
| **与 L4 DP** | DP 是求解 MDP 的核心算法（值迭代/策略迭代） |
| **与 L4 Monte Carlo** | 当状态空间过大或转移概率未知时，用 MC 模拟评估策略 |

#### 2.2.6 决策语境 vs 时序语境的区分

| 维度 | 决策语境 state transition | 时序语境 state transition |
|---|---|---|
| 核心问题 | 如何决策使累积奖励最优？ | 如何预测未来状态？ |
| 驱动因素 | 动作 (action) 驱动 | 时间/数据驱动 |
| 数学框架 | MDP / Bellman 方程 | 递推方程 / 状态空间模型 |
| 优化目标 | `max Σ γ^t r_t` | 最小化预测误差 |
| 典型方法 | DP / 值迭代 / 策略迭代 / RL | ARIMA / Kalman 滤波 / LSTM |
| 2020_B 对应 | Q1/Q2 的行动决策 | —（本题无时序预测需求） |

### 2.3 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| MDP 定义为五元组 (S,A,P,R,γ) | Stanford CME 241、INRIA Lille、PKU BICMR 讲义一致定义 | multiple Tier 1 university courses | Tier 1 | 高 |
| Bellman 最优性方程是 MDP 求解的核心 | Stanford CME 241 给出 V*(s) 和 Q*(s,a) 的完整公式 | Stanford University course | Tier 1 | 高 |
| 马尔可夫性要求当前状态包含所有相关历史信息 | PKU BICMR 讲义明确表述 "future is independent of the past given current state" | Peking University course | Tier 1 | 高 |
| resource constraint 是建模机理而非数学约束语法 | RCPSP 文献及 OR 教材将资源约束作为问题结构的核心定义 | Wiley + textbook-level | Tier 1 | 高 |
| 资源分为可再生(renewable)和不可更新(non-renewable) | Wiley RCPSP 论文明确区分 Kρ（可再生）和 Kv（不可更新） | Wiley peer-reviewed | Tier 1 | 高 |
| 多玩家共享资源产生外部性 | 2020_B Q3 题面明确：k人同行消耗2k倍，k人同矿收益1/k | CUMCM official problem statement | Tier 1 | 高 |

---

## 3. L3 标签研究

### 3.1 Graph（图论）是否应成为 L3 一级标签？

#### 3.1.1 结论：**是，graph 应成为 L3 一级标签**

#### 3.1.2 论证

**(1) Graph 是独立的数学表述范式**

图论 `G = (V, E)` 是一种独立的数学结构，用于建模实体间的成对关系。它与 optimization（目标+约束的形式化）、probability（随机变量+分布）、differential equation（连续演化方程）是并列的数学表述形式，而非 optimization 的子类型。

> IEEE Technology Navigator："Graph theory is the branch of discrete mathematics that studies graphs: abstract structures consisting of vertices connected by edges. Graphs model pairwise relationships in almost any domain."

**(2) 图论问题不一定是优化问题**

- 图的连通性判定、二分图判定、拓扑排序——这些是图论问题但不是优化问题
- 图着色问题是约束满足问题（CSP），不是严格的 optimization
- 因此 graph 不能被 optimization 完全包含

**(3) 图论在离散优化域中的核心地位**

在本域（scheduling + resource constraint + DP）中，graph 是高频表述：

| 应用 | 图建模方式 |
|---|---|
| 调度问题 | 析取图 (disjunctive graph)：节点=工序，析取弧=机器互斥 |
| 最短路径 | 有向加权图：节点=位置，边=移动+消耗 |
| 网络流 | 流网络：节点=转运点，边=容量+费用 |
| 2020_B 地图 | 平面图：节点=区域，边=相邻关系 |
| 资源分配 | 二部图：任务↔资源的匹配 |
| DP 状态转移 | 状态图：节点=状态，边=决策转移 |

**(4) 图论有独立的算法体系（L4）**

| 图论问题 | 对应 L4 算法 |
|---|---|
| 最短路径 | Dijkstra, Bellman-Ford, Floyd-Warshall |
| 最大流/最小割 | Ford-Fulkerson, Edmonds-Karp, Dinic |
| 最小生成树 | Kruskal, Prim |
| 匹配 | 匈牙利算法 |
| 图着色 | 贪心/回溯/精确算法 |

这些算法不是 generic optimization solver，而是图结构特有的算法。

**(5) 图论与 optimization 的交叉**

图论问题可以转化为 optimization 表述（如最短路径 = LP，最大流 = LP），但这只是**等价表述**，不代表 graph 是 optimization 的子标签。正如 differential equation 可以离散化为 optimization 问题，但二者仍是独立的 L3 标签。

#### 3.1.3 现有知识库状态

- `core/knowledge/methodology/graph-theory.md` 已存在，覆盖最短路径、网络流、最小生成树、匹配、着色
- `core/knowledge/methodology/graph-network-vrp.md` 覆盖 VRP
- 但 16 张方法卡中**无任何 graph 相关卡**，L3 graph 标签覆盖率为 0

### 3.2 Integer Programming / Nonlinear Programming / Linear Programming 的层级定位

#### 3.2.1 问题

当前 L3 仅有一个 `optimization` 标签，过于宽泛。需要研究是否应拆分为 `integer programming`、`linear programming`、`nonlinear programming` 等更明确的子标签。

#### 3.2.2 数学规划的层级结构

数学规划（Mathematical Programming）的标准层级（IEEE Technology Navigator, University of Padova, NIST）：

```
Mathematical Programming (数学规划)
├── Linear Programming (LP)
│   └── 目标+约束均为线性，变量连续
├── Nonlinear Programming (NLP)
│   └── 目标或约束为非线性，变量连续
├── Integer Programming (IP)
│   ├── Pure Integer Programming (PIP)：全部变量整数
│   ├── Mixed Integer Programming (MIP/MILP)：部分整数部分连续
│   └── 0-1 Programming (Binary IP)：变量取 0/1
└── Combinatorial Optimization
    └── 在离散结构（图、集合、排列）上的优化
```

**关键关系**：
- IP 由于整数约束引入非凸性，在技术上可视为 NLP 的特例（StudyGuides："hierarchically positioned under nonlinear programming due to the non-convexity introduced by integrality"）
- 但在实践中，IP 有完全不同的求解方法（B&B、割平面），通常作为独立类别处理
- MILP = Mixed Integer Linear Programming，是 IP 中最常用的子类（目标和约束线性，部分变量整数）

#### 3.2.3 结论与建议

**建议：保持 `optimization` 作为 L3 一级伞标签，新增以下子标签（sub-tags）：**

| 子标签 | 定义 | 本域相关性 |
|---|---|---|
| `linear programming` | 线性目标+线性约束+连续变量 | 资源分配、网络流、生产计划 |
| `integer programming` | 含整数变量的优化（含 0-1、MILP） | 调度（任务指派/排序）、背包、选址 |
| `nonlinear programming` | 非线性目标或约束 | 资源消耗非线性、外部性函数 |
| `dynamic programming formulation` | Bellman 方程作为数学表述 | 多阶段决策、MDP |

**理由**：
1. `optimization` 作为伞标签保留，因为很多问题的表述跨越 LP/IP/NLP（如调度问题的 MINLP 表述）
2. 子标签提供更精细的表述区分，有助于 evaluator 判断"LLM 选择的数学形式是否合理"
3. `integer programming` 在本域（调度+资源约束）中是最核心的表述形式，必须独立标注
4. `dynamic programming formulation` 作为 L3 子标签，明确区分于 L4 的 `DP algorithm`

**不建议将 integer programming 提升为与 optimization 并列的一级标签**，因为：
- IP 本质上是 mathematical programming 的子类，与 LP/NLP 同层
- 提升为一级标签会破坏层级一致性（graph/probability/differential equation 是并列的一级范式，IP 是 optimization 范式内的子类）

### 3.3 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| graph 是独立的离散数学分支，建模成对关系 | IEEE Technology Navigator Graph Theory 条目 | IEEE professional resource | Tier 1 | 高 |
| 最短路径可表述为 LP | Chalmers MVE165 讲义及 PKU BICMR 讲义均给出 LP 公式 | university courses | Tier 1 | 高 |
| 最大流最小割定理 (Ford-Fulkerson 1956) | 多来源交叉验证 | textbook-level theorem | Tier 1 | 高 |
| 数学规划分为 LP/NLP/IP/MILP | IEEE Technology Navigator + University of Padova 讲义一致分类 | IEEE + university course | Tier 1 | 高 |
| IP 因整数约束引入非凸性，技术上属 NLP 特例 | StudyGuides Integer Programming 条目明确说明 | professional study resource | Tier 2 | 中 |
| MILP 求解器基于 B&B（Land and Doig 1960） | arXiv 2511.09219 及 Mosek 文档均引用 | peer-reviewed preprint + commercial solver doc | Tier 1 | 高 |
| 调度的 MINLP 表述存在 | CSDN 文库 2018B 二等奖方案使用 MINLP | competition solution | Tier 3 | 中低 |

---

## 4. L4 标签研究

### 4.1 Dynamic Programming（动态规划）— 核心深入研究

#### 4.1.1 基本思想

**动态规划（DP）**是一种通过将复杂问题分解为重叠子问题（overlapping subproblems），并利用最优子结构（optimal substructure）自底向上或自顶向下求解的算法范式。

**核心五要素**：

| 要素 | 定义 | 2020_B 对应 |
|---|---|---|
| **阶段 (Stage)** | 问题的时间/逻辑划分 | 每一天 t = 0,1,...,T |
| **状态 (State)** | 每个阶段的系统特征 | `(position, water, food, money)` |
| **决策 (Decision/Action)** | 每个状态下的可选动作 | `{停留, 行走, 挖矿}` |
| **状态转移 (Transition)** | 执行决策后状态如何演化 | `s_{t+1} = f(s_t, a_t, weather)` |
| **目标函数 (Objective)** | 累积收益/成本的最优值 | `max 最终资金 = Σ 每日净收益` |

#### 4.1.2 Bellman 最优性原理

> **Bellman's Principle of Optimality**（Bellman 1957, *Dynamic Programming*, Princeton University Press）：
> "An optimal policy has the property that whatever the initial state and initial decision are, the remaining decisions must constitute an optimal policy with regard to the state resulting from the first decision."

**中文表述**：一个最优策略具有这样的性质——无论初始状态和初始决策如何，剩余决策必须构成相对于第一个决策所产生状态的最优策略。

**Bellman 方程**（确定性有限时域）：
$$V_t(s) = \max_{a \in A(s)} \left\{ r_t(s, a) + V_{t+1}(s') \right\}, \quad s' = f(s, a)$$

边界条件：$V_T(s) = g(s)$（终端奖励/成本）

#### 4.1.3 最优子结构与重叠子问题

DP 适用的两个**必要且充分的结构性质**（Stanford CS 161, Princeton COS 226, IEEE Technology Navigator）：

**(1) 最优子结构 (Optimal Substructure)**
- 定义：原问题的最优解包含其子问题的最优解
- 意义：可以通过组合子问题的最优解来构造原问题的最优解
- 验证方法：cut-and-paste 论证——假设子问题解不是最优的，用更优解替换后能改进原问题解，矛盾

**(2) 重叠子问题 (Overlapping Subproblems)**
- 定义：同一子问题在递归求解中被反复访问
- 意义：通过记忆化（memoization）或表格（tabulation）存储已求解的子问题，避免指数级重复计算
- 效率公式：`运行时间 = 子问题数 × 每个子问题的计算代价`

> **注意**：仅有最优子结构而无重叠子问题 → 用分治法（divide-and-conquer）即可，不需要 DP（如归并排序）。
> 仅有重叠子问题而无最优子结构 → 不能用 DP 保证最优性。

#### 4.1.4 无后效性（No-aftereffect / Markovianity）

DP 适用的第三个关键条件（中文运筹学教材强调）：
- 定义：某阶段的状态一旦确定，此后过程的演变不再受此前各状态和决策的直接影响
- 等价于马尔可夫性：未来只依赖于当前状态，不依赖于历史
- 这是状态定义正确性的核心检验标准

#### 4.1.5 什么样的数学建模问题真正适合 DP？

**核心回答**：当问题同时满足以下条件时，DP 是真正合适的求解方法：

| 条件 | 检验问题 | 反例 |
|---|---|---|
| **多阶段序贯决策** | 问题是否可以划分为一系列按时间/逻辑顺序的决策？ | 单阶段静态优化（如一次性资源分配）→ LP 更合适 |
| **有限/可数状态空间** | 状态变量是否离散且数量可管理（多项式级）？ | 连续状态空间（如温度场优化）→ PDE/变分法 |
| **最优子结构** | 全局最优是否由子问题最优构成？ | 博弈中的均衡问题（纳什均衡不由子博弈最优简单构成）→ 博弈论方法 |
| **无后效性** | 当前状态是否包含所有决策相关的历史信息？ | 路径依赖问题（历史决策影响当前选项且无法压缩到状态中） |
| **重叠子问题** | 递归求解中是否反复访问相同子问题？ | 树结构无重叠（如决策树搜索）→ DFS/BFS 即可 |
| **状态空间不爆炸** | 状态总数是否在计算可行范围内？ | 多维资源状态导致维数灾难（如 10 种资源各 100 级 = 10^20 状态） |

**典型适合 DP 的数学建模问题**：
1. **资源约束下的多阶段决策**：如 2020_B（水/食物/资金约束下的每日行动决策）
2. **背包类问题**：0-1 背包、多维背包、无限背包
3. **最短路径**：DAG 上的最短路、Bellman-Ford
4. **生产计划/库存**：多周期生产-库存决策（Wagner-Whitin 模型）
5. **设备更新**：保留 vs 更换的多阶段决策
6. **项目调度**：小型 RCPSP（状态 = 已完成活动集合）
7. **排序/排列**：状态压缩 DP（bitmask DP）处理小规模排列问题

#### 4.1.6 DP 不适用的条件

| 不适用条件 | 原因 | 替代方法 |
|---|---|---|
| **状态空间爆炸（维数灾难）** | 状态变量维度高或每维取值多，导致状态数指数增长 | 近似 DP、函数逼近、强化学习、MILP、启发式 |
| **无最优子结构** | 全局最优不能由子问题最优构造 | 博弈论、元启发式、局部搜索 |
| **连续状态/动作空间** | 无法枚举状态和动作 | 变分法、最优控制（Pontryagin）、强化学习 |
| **后效性无法消除** | 历史影响无法压缩到当前状态中 | 扩展状态定义（可能加剧爆炸）或换用其他方法 |
| **问题规模过大** | 即使状态空间多项式，但 n 太大导致计算不可行 | 启发式、元启发式、MILP 求解器 |
| **实时性要求高** | DP 离线计算完整策略表，不适合在线快速决策 | 贪心策略、强化学习、近似动态规划 |

#### 4.1.7 常见建模错误

| 错误 | 表现 | 后果 | 修正方法 |
|---|---|---|---|
| **状态定义不完整** | 遗漏关键状态变量（如 2020_B 中忘记包含食物量） | 违反无后效性，转移方程错误 | 检查：当前状态是否足以计算所有未来转移和奖励 |
| **状态维度过高** | 将所有历史信息都塞进状态 | 维数灾难，计算不可行 | 状态压缩：只保留决策相关的充分统计量 |
| **转移方程错误** | 未正确建模动作对状态的影响 | 策略非最优或不可行 | 逐动作验证转移：对每个 a∈A(s)，手动计算 s' |
| **忽略动作空间的约束** | 天气/资源限制下某些动作不可行但未排除 | 产生不可行策略 | 在 A(s) 中显式排除不可行动作 |
| **边界条件错误** | 终端奖励/初始状态设定错误 | 最优值偏移 | 验证：从边界条件出发手动计算前几步 |
| **将 DP 当黑盒** | 只写代码不验证最优子结构 | 可能根本不满足 DP 条件 | 先做 cut-and-paste 论证再写代码 |
| **连续变量不离散化** | 直接对连续资源量做 DP | 状态空间不可数 | 合理离散化（如按箱/按单位），分析离散化误差 |
| **混淆 DP formulation 与 DP algorithm** | 把 Bellman 方程当作算法实现 | 无法落地 | Bellman 方程是 L3 表述；值迭代/策略迭代/表格递推是 L4 算法 |

#### 4.1.8 验证方式

| 验证方法 | 具体操作 | 通过标准 |
|---|---|---|
| **最优子结构证明** | cut-and-paste 论证：假设子问题非最优，替换后矛盾 | 逻辑严密 |
| **小规模 brute-force 对比** | 对 n ≤ 10 的实例，枚举所有策略对比 DP 结果 | DP 结果 = 枚举最优值 |
| **收敛性检验** | 值迭代/策略迭代的价值函数变化 < ε | `\|\|V_{k+1} - V_k\|\|_∞ < 1e-6` |
| **策略可行性检验** | 检查 DP 输出的策略是否满足所有约束 | 资源不耗尽、天气规则遵守、到达终点 |
| **多种子/多实例稳定性** | 对不同参数实例运行 DP，检查结果合理性 | 无异常值、单调性符合直觉 |
| **下界验证** | 用松弛问题（如忽略某些约束）的最优值作为下界 | DP 最优值 ≥ 松弛下界 |
| **回溯一致性** | 从 DP 表回溯最优策略，手动模拟验证 | 回溯路径的累积奖励 = DP 表中的最优值 |

#### 4.1.9 DP 与其他求解器的区别

| 维度 | DP | Greedy | GA | MILP |
|---|---|---|---|---|
| **最优性** | 全局最优（条件满足时） | 仅当有贪心选择性质时最优 | 近优，无保证 | 全局最优（求解器完成时） |
| **核心思想** | 子问题最优 + 记忆化 | 每步局部最优 | 种群进化 + 适者生存 | LP 松弛 + 分支定界 + 割平面 |
| **状态要求** | 需要明确的状态定义和转移 | 不需要状态空间 | 需要解的编码方式 | 需要线性/整数规划模型 |
| **适用问题** | 多阶段序贯决策、有限状态 | 具有贪心选择性质的问题 | 大规模 NP-hard、黑盒目标 | 结构化线性/整数约束 |
| **计算复杂度** | O(状态数 × 动作数) | O(n log n) ~ O(n) | 依赖种群和迭代数 | 指数级最坏情况，实际高效 |
| **可解释性** | 高（状态转移表可追溯） | 高（每步决策明确） | 低（进化过程黑盒） | 中（求解器内部黑盒，但模型透明） |
| **2020_B 适配性** | **高**（Q1/Q2 核心方法） | 低（无贪心选择性质） | 中（可作为替代但非最优） | 中（可建模但状态维度高） |
| **2018_B 适配性** | 低（状态空间过大，连续时间） | 中（贪心调度规则是基线） | **高**（GA 优化调度序列） | 中（0-1 规划建模） |

#### 4.1.10 DP 的数学表述（L3）vs 算法（L4）区分

| 层面 | 内容 | 例子 |
|---|---|---|
| **L3 DP Formulation** | 将问题表述为 Bellman 方程的形式：定义状态、动作、转移、奖励，写出递归方程 | `V_t(s) = max_a {r(s,a) + V_{t+1}(s')}` |
| **L4 DP Algorithm** | 具体求解 Bellman 方程的计算方法 | 值迭代 (Value Iteration)、策略迭代 (Policy Iteration)、自底向上表格递推、自顶向下记忆化递归、Dijkstra（特殊 DP） |

> **关键**：一个问题可以有 L3 的 DP formulation 但不用 L4 的 DP algorithm 求解（如用强化学习近似求解 Bellman 方程）。反之，用了 DP algorithm 必然意味着有 L3 的 DP formulation。

### 4.2 Branch-and-Bound（分支定界）

#### 4.2.1 定义与原理

**分支定界（B&B）**是一种用于离散/组合优化的精确求解算法范式，通过系统性枚举候选解空间并利用上下界剪枝来避免全量搜索（Land and Doig 1960）。

**三步核心循环**：
1. **分支 (Branch)**：将当前问题分解为若干子问题（通常通过对某个分数变量施加 `x ≤ ⌊x⌋` 和 `x ≥ ⌈x⌉` 约束）
2. **定界 (Bound)**：求解每个子问题的松弛问题（通常是 LP 松弛），得到该子问题最优值的上界（最大化问题）
3. **剪枝 (Prune)**：若子问题的上界 ≤ 当前已知最优解（下界），则该子问题不可能包含更优解，剪掉；若子问题无可行解，也剪掉

#### 4.2.2 与 MILP 的关系

- B&B 是 MILP 求解器的**核心算法骨架**
- 现代 MILP 求解器（Gurobi/CPLEX/SCIP）在 B&B 基础上增加：
  - **割平面 (Cutting Planes)**：在每个节点添加有效不等式收紧 LP 松弛
  - **分支切割 (Branch-and-Cut)**：B&B + 割平面的混合
  - **启发式 (Heuristics)**：在搜索树中快速找可行解以改进下界
  - **预处理 (Presolve)**：简化模型、消除冗余约束和变量

#### 4.2.3 适用场景

- 整数规划/混合整数规划的精确求解
- 小规模组合优化问题（n ≤ 50-100）
- 需要全局最优性保证的场景
- 问题结构允许有效的 LP 松弛和界估计

### 4.3 MILP Solver（混合整数线性规划求解器）

#### 4.3.1 定位

MILP 求解器是**通用精确优化引擎**，输入为线性目标 + 线性约束 + 部分变量整数的数学规划模型，输出为最优解（或在时间限制内的最佳可行解+最优性间隙）。

#### 4.3.2 主流求解器

| 求解器 | 类型 | 特点 | Python 接口 |
|---|---|---|---|
| **Gurobi** | 商业 | 性能最强，支持 MILP/MIQP/MINLP，大规模问题 | `gurobipy` |
| **CPLEX** | 商业 | IBM 出品，企业级稳定性 | `docplex` |
| **SCIP** | 开源学术 | 功能全面，支持 MINLP，非商业免费 | `pyscipopt` |
| **CBC (COIN-OR)** | 开源 | 纯 MILP，轻量级 | `pulp` |
| **scipy.optimize.milp** | 开源 | SciPy 内置，基于 HiGHS，适合中小规模 | `scipy` |
| **HiGHS** | 开源 | 高性能 LP/MILP，SciPy 后端 | `highspy` |

#### 4.3.3 在数学建模竞赛中的定位

- MILP 求解器是**工具**，不是**建模方法**
- 建模的核心在于：如何将问题转化为 MILP 形式（决策变量定义、约束线性化、目标函数构造）
- 常见陷阱：非线性约束未线性化、大 M 取值不当导致数值不稳定、变量过多导致求解超时
- 竞赛中 scipy.optimize.milp 是最易获取的免费选择，但大规模问题性能有限

### 4.4 Heuristic（启发式）

#### 4.4.1 定义与分类

**启发式算法**是在合理计算时间内寻求近优解的近似算法，不保证全局最优。

| 类别 | 代表方法 | 特点 |
|---|---|---|
| **构造启发式** | 优先调度规则 (SPT/EDD/LPT)、贪心、NEH、Johnson | 从空解逐步构造，速度快，解质量依赖规则 |
| **局部搜索** | 爬山法、2-opt、Or-opt、变邻域搜索 (VNS) | 从初始解出发邻域迭代，易陷入局部最优 |
| **元启发式** | GA, SA, PSO, 禁忌搜索 (TS), 蚁群 (ACO), 差分进化 (DE) | 引入随机性/记忆机制逃离局部最优，通用性强 |
| **超启发式** | 启发式选择、遗传规划 | 自动选择/生成启发式规则 |

#### 4.4.2 在调度问题中的应用

- 调度规则 (dispatching rules) 是最简单的构造启发式：SPT（最短加工时间优先）、EDD（最早截止期优先）、MWR（剩余工作量最多优先）
- 元启发式（GA/SA/PSO）是大规模调度问题的主流求解方法
- 2018_B RGV 调度中，获奖方案普遍使用 GA/SA 优化调度序列（GitHub Hecate2 国一方案、CSDN 多篇获奖论文）

#### 4.4.3 与精确算法的选择决策

```
问题规模 n ≤ 20-30？
├── 是 → 精确算法（B&B / MILP 求解器 / DP），追求全局最优
└── 否 → 问题结构是否特殊（如 F2‖Cmax 有 Johnson 规则）？
    ├── 是 → 多项式精确算法
    └── 否 → 启发式/元启发式，追求近优解 + 多次运行稳定性
```

### 4.5 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| Bellman 1957 年出版《Dynamic Programming》提出最优性原理 | Manning 章节及 AI Wiki 均引用 Princeton University Press 1957 | book history + multiple sources | Tier 1 | 高 |
| DP 需要最优子结构 + 重叠子问题两个性质 | Stanford CS 161、Princeton COS 226、IEEE Technology Navigator 一致表述 | multiple Tier 1 universities + IEEE | Tier 1 | 高 |
| DP 运行时间 = 子问题数 × 每子问题代价 | Princeton COS 226 讲义明确给出 | Princeton University course | Tier 1 | 高 |
| B&B 由 Land and Doig 1960 提出 | arXiv 2511.09219 明确引用 | peer-reviewed preprint | Tier 1 | 高 |
| MILP 求解器基于 B&B + 割平面 + 启发式 | Mosek 文档及 PKU BICMR 讲义一致描述 | commercial solver doc + university course | Tier 1 | 高 |
| 2018_B 获奖方案使用 GA 优化调度序列 | GitHub Hecate2（国一）README 及 CSDN 多篇获奖论文 | competition solutions | Tier 2-3 | 中高 |
| 2020_B 可建模为 DP：状态=(天数,区域,水量,食物量) | CSDN 多篇求解方案及 GitHub youngzhou1999（国一）一致 | competition solutions | Tier 2-3 | 中高 |
| 2020_B Q2 是 MDP（天气随机） | CSDN 文库方案明确使用 MDP 框架 | competition solution | Tier 3 | 中 |
| scipy.optimize.milp 可用于中小规模 MILP | 现有 knowledge/integer-programming.md 代码框架使用 scipy | internal knowledge + official docs | Tier 1 | 高 |

---

## 5. L1→L2→L3→L4 映射表：离散优化域完整知识链

### 5.1 主映射表

| L1 Problem Structure | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 典型问题 |
|---|---|---|---|---|
| **scheduling**（单机） | resource constraint（机器容量）+ state transition（加工状态演化） | integer programming（0-1 排序变量）+ optimization | DP（状态=已排序任务集）+ greedy（SPT/EDD）+ MILP | 单机调度 1‖ΣC_j |
| **scheduling**（并行机） | resource constraint（多机容量）+ state transition | integer programming（指派变量）+ optimization | MILP + heuristic（LPT/GA）+ DP（小规模） | 并行机调度 Pm‖Cmax |
| **scheduling**（流水车间） | resource constraint（机器序列）+ state transition | integer programming + graph（排列图）+ optimization | Johnson 规则（F2）+ NEH + GA/SA + MILP | 流水车间 Fm‖Cmax |
| **scheduling**（作业车间） | resource constraint（机器互斥）+ state transition（工序状态） | integer programming（析取模型）+ graph（析取图）+ optimization | B&B + MILP + shifting bottleneck + GA/SA + dispatching rules | 作业车间 Jm‖Cmax |
| **scheduling**（动态/实时） | resource constraint + state transition（MDP 事件驱动） | optimization + probability + graph | DES + heuristic（dispatching）+ RL + rolling horizon DP | RGV 动态调度 (2018_B) |
| **scheduling**（项目/RCPSP） | resource constraint（可再生+不可更新资源）+ state transition | integer programming + optimization + graph（AOE网） | B&B + MILP + priority rules + GA/SA + DP（小规模） | 资源约束项目调度 |
| **competition/game**（多玩家资源竞争） | resource constraint（共享资源外部性）+ state transition（MDP）+ interaction/game | optimization + probability + game theory（纳什均衡） | DP（单人子问题）+ game theory（均衡求解）+ Monte Carlo（策略评估） | 2020_B Q3 |
| **decision**（多阶段资源分配） | resource constraint（预算/容量）+ state transition（库存/资源水平演化） | optimization + integer programming + dynamic programming formulation | DP（表格递推）+ MILP + greedy（特定结构） | 背包、生产计划、设备更新 |

### 5.2 2020_B 穿越沙漠的完整知识链

| 层 | 标签 | 具体内容 |
|---|---|---|
| **L1** | scheduling + competition/game + decision | 每日行动调度（行走/停留/挖矿）；Q3 多玩家竞争；多阶段决策 |
| **L2** | resource constraint + state transition(MDP) + interaction/game | 水/食物/资金/负重四重资源约束；每日状态演化（位置+资源水平）；Q3 多玩家共享资源外部性 |
| **L3** | optimization + probability + graph + dynamic programming formulation | 最大化最终资金的优化目标；天气随机概率模型；地图为平面图；Bellman 方程表述 |
| **L4** | DP（Q1确定性）+ MDP值迭代（Q2随机性）+ game theory（Q3均衡）+ Monte Carlo（策略评估） | Q1：确定性DP逆推；Q2：MDP值迭代/策略迭代；Q3：纳什均衡+MC模拟 |

### 5.3 2018_B RGV 调度的完整知识链

| 层 | 标签 | 具体内容 |
|---|---|---|
| **L1** | scheduling | RGV 对 8 台 CNC 的动态调度（单工序/双工序/故障） |
| **L2** | resource constraint + state transition（事件驱动） | CNC 机器资源互斥、RGV 移动时间约束、碰撞避免约束；系统状态随加工完成事件演化 |
| **L3** | optimization + integer programming（0-1规划）+ graph | 最大化产量的优化目标；RGV 调度路径的 0-1 变量；CNC 位置为线性图 |
| **L4** | heuristic（greedy + GA/SA）+ DES 仿真 + 0-1 规划 | 贪心调度规则为基线；GA/SA 优化调度序列；DES 评估策略；小规模可用 0-1 规划精确求解 |

### 5.4 知识链的路由逻辑（LLM 应如何从问题推导到方法）

```
问题输入
  ↓
L1 识别：这是什么类型的问题？
  ├── 有时间维度的资源分配？ → scheduling
  ├── 多玩家竞争？ → competition/game
  └── 多阶段决策？ → decision
  ↓
L2 建模：核心机理是什么？
  ├── 有限资源约束决策？ → resource constraint
  ├── 状态随决策/时间演化？ → state transition
  │   ├── 确定性演化？ → 确定性 DP formulation
  │   └── 随机性演化？ → MDP formulation
  └── 多玩家交互？ → interaction/game
  ↓
L3 表述：用什么数学形式？
  ├── 目标+约束？ → optimization
  │   ├── 变量整数？ → integer programming
  │   ├── 全线性？ → linear programming
  │   └── 非线性？ → nonlinear programming
  ├── 实体+关系？ → graph
  ├── 随机？ → probability
  └── 递归最优？ → dynamic programming formulation
  ↓
L4 求解：用什么算法？
  ├── 小规模 + 最优子结构 → DP
  ├── 结构化整数约束 → MILP solver / B&B
  ├── 大规模 NP-hard → heuristic / metaheuristic
  ├── 随机动态 → MDP 值迭代 / Monte Carlo / RL
  └── 图结构 → 图算法（Dijkstra/最大流/匹配）
```

---

## 6. 真实竞赛题映射

### 6.1 2020_B 穿越沙漠

#### 6.1.1 问题概述

玩家在沙漠地图中，以天为单位决策（停留/行走/挖矿），管理水、食物、资金三种资源，受负重上限和天气（晴朗/高温/沙暴）约束，目标是在规定时间内到达终点并保留最多资金。Q3 扩展为 n 名玩家共享资源的博弈。

#### 6.1.2 四层映射

| 层 | 标签 | 映射依据 |
|---|---|---|
| **L1** | scheduling + competition/game + decision | 每日行动调度（时间维度的资源分配决策）；Q3 多玩家竞争博弈；整体是多阶段序贯决策 |
| **L2** | resource constraint + state transition(MDP) + interaction/game | **resource constraint**：水/食物/资金/负重四重约束（规则2、6、7、8）；行走消耗2倍、挖矿消耗3倍（规则5、7）；水+食物总负重上限（规则2）。**state transition**：每日状态=(day, position, water, food, money)，动作驱动状态演化；Q1 确定性转移（天气全已知），Q2 随机性转移（天气随机→MDP）。**interaction/game**：Q3 中 k 人同行消耗2k倍、k人同矿收益1/k、k人同村价格4倍（规则Q3），产生策略外部性 |
| **L3** | optimization + probability + graph + dynamic programming formulation | **optimization**：max 最终资金 = 初始资金 + 挖矿收益 - 购买成本 + 退回价值。**probability**：Q2/Q3(2) 天气随机，需建立天气转移概率矩阵。**graph**：地图为平面图，节点=区域，边=相邻关系（注1）。**dynamic programming formulation**：Bellman 方程 V_t(pos,w,f,m) = max_a {reward(a) + V_{t+1}(s')} |
| **L4** | DP + MDP值迭代 + game theory + Monte Carlo | **Q1（天气全已知）**：确定性 DP，逆推法从终点倒推，状态=(day,position,water,food)，动作={停留,行走,挖矿}。**Q2（仅知当天天气）**：MDP 值迭代/策略迭代，天气转移概率驱动期望价值。**Q3(1)（天气已知+开环策略）**：多人联合优化或博弈均衡，可用 DP 求解单人最优响应后迭代求均衡。**Q3(2)（天气随机+闭环策略）**：随机博弈 + 蒙特卡洛模拟评估策略 |

#### 6.1.3 为什么这种建模路线是合理的？

1. **DP/MDP 是 Q1/Q2 的自然选择**：
   - 问题具有明确的多阶段结构（每天一个决策阶段）
   - 状态空间有限且可管理（天数 ≤ 30，区域数 ≤ ~30，水量/食物量按箱离散化后各 ≤ ~50）
   - 满足最优子结构：第 t 天从状态 s 出发的最优策略，其第 t+1 天起的子策略必须是从 s' 出发的最优策略（Bellman 原理）
   - 满足无后效性：状态 (day,position,water,food,money) 包含了所有决策相关信息
   - 重叠子问题：不同路径可能到达相同 (day,position,water,food) 状态，DP 表格避免重复计算

2. **Resource constraint 是建模核心**：
   - 水和食物的消耗规则（停留1倍/行走2倍/挖矿3倍，天气依赖）定义了状态转移中的资源动态
   - 负重上限（水+食物总质量 ≤ 上限）是耦合约束，使水和食物非独立
   - 资金约束影响购买/挖矿决策
   - 这些资源约束共同定义了 DP 的可行状态空间和动作空间

3. **Game theory 是 Q3 的必要扩展**：
   - Q3 的共享资源外部性（k人消耗/收益/价格变化）使个人最优依赖于他人策略
   - 这是典型的博弈论场景，需要求解纳什均衡而非单人最优
   - 开环（Q3(1)）和闭环（Q3(2)）对应不同的博弈均衡概念

4. **GA 不是 Q1/Q2 的合适主求解器**：
   - GA 是元启发式，不保证全局最优
   - 2020_B Q1/Q2 的状态空间在 DP 可行范围内，应优先使用精确 DP
   - 当前方法卡库无 DP 卡导致 LLM 退而选择 mc-ga，这是知识架构缺口导致的方法误选（见审计报告 2020_B 分析）

#### 6.1.4 建模注意事项

- **状态离散化**：水和食物以箱为单位（规则2明确"最小计量单位均为箱"），天然离散，无需额外离散化
- **天气处理**：Q1 天气全已知 → 确定性 DP，天气作为参数嵌入转移方程；Q2 仅知当天 → MDP，需估计天气转移概率（可从历史数据或题目给定的天气分布估计）
- **矿山/村庄特殊位置**：挖矿和购买只在特定位置可行，需在动作空间 A(s) 中根据 position 条件性包含
- **起点购买限制**：规则6"不能多次在起点购买资源"——这是一个历史依赖约束，需要在状态中标记"是否已在起点购买过"，或通过初始决策处理
- **终点退回**：到达终点后剩余水/食物按半价退回，这是终端奖励函数 V_T(s) 的一部分

### 6.2 2018_B 智能 RGV 的动态调度策略

#### 6.2.1 问题概述

8 台 CNC + 1 辆（或 2 辆）RGV 组成的智能加工系统。RGV 在轨道上移动为 CNC 上下料，CNC 加工物料。目标是 8 小时内最大化产量。包含单工序、双工序、故障鲁棒性、双 RGV 碰撞避免等子问题。

#### 6.2.2 四层映射

| 层 | 标签 | 映射依据 |
|---|---|---|
| **L1** | scheduling | RGV 对 CNC 的服务调度（何时去哪台 CNC 上下料），是典型的动态调度问题 |
| **L2** | resource constraint + state transition（事件驱动） | **resource constraint**：单台 RGV 同一时刻只能服务一台 CNC；每台 CNC 同一时刻只能加工一个物料；RGV 移动时间约束；双 RGV 碰撞避免约束（距离 ≥ d_min）。**state transition**：系统状态=(各CNC状态[空闲/加工/等待], RGV位置, 已产量)，随"CNC加工完成"事件驱动演化 |
| **L3** | optimization + integer programming + graph | **optimization**：max 8小时产量。**integer programming**：RGV 调度路径的 0-1 变量（x_{ij}=1 表示 RGV 第 i 次服务 CNC j）；获奖论文使用 0-1 规划建模。**graph**：CNC 在轨道上的位置为线性图，RGV 移动为图上的路径 |
| **L4** | heuristic（greedy + GA/SA）+ DES 仿真 + 0-1 规划 | **贪心基线**：RGV 选择等待时间最长的 CNC（或最近的 CNC）。**GA/SA 优化**：将 RGV 服务序列编码为染色体，用 GA/SA 搜索最优调度序列（国一方案 Hecate2 使用 GA）。**DES 仿真**：事件驱动仿真评估调度策略的产量和利用率。**0-1 规划**：小规模可用 MILP 精确求解，但大规模状态空间导致求解困难 |

#### 6.2.3 为什么不用纯 DP？

- **状态空间过大**：连续时间 + 8 台 CNC 状态 + RGV 位置，若离散化时间则状态数爆炸
- **循环模式**：RGV 调度存在周期性循环模式（如前 17 次上下料构成一个循环），DP 的有限时域假设不自然
- **事件驱动而非时间驱动**：系统演化由离散事件（加工完成）驱动，不是固定时间步，DP 的等时间步假设不匹配
- **因此 DES + heuristic 是更合适的求解范式**

#### 6.2.4 与 2020_B 的对比

| 维度 | 2020_B | 2018_B |
|---|---|---|
| 时间结构 | 离散时间步（天） | 连续时间 + 事件驱动 |
| 状态空间 | 有限可管理（DP 可行） | 大且连续（DP 不可行） |
| 决策频率 | 每天一次（≤30次） | 事件触发（数百次） |
| 最优方法 | DP/MDP | DES + GA/SA |
| 资源约束 | 水/食物/资金/负重 | CNC/RGV 时间/碰撞 |
| 随机性 | 天气随机 | 故障随机 |

### 6.3 其他代表性题目

#### 6.3.1 2021_C 供应链企业生产库存配送策略

- **L1**：scheduling + decision（生产计划+库存+配送的联合调度）
- **L2**：resource constraint（产能/库存容量/预算）+ state transition（库存水平演化）
- **L3**：optimization + integer programming
- **L4**：MILP + DP（多周期库存）+ heuristic
- **为什么合理**：多周期生产-库存-配送是经典的运筹学问题，具有资源约束和状态转移（库存平衡）结构，MILP 是标准建模方式

#### 6.3.2 2005_B DVD 在线租赁（资源分配经典题）

- **L1**：decision + scheduling（租赁需求分配）
- **L2**：resource constraint（DVD 库存容量/购买预算）
- **L3**：optimization + integer programming（0-1 指派）
- **L4**：MILP + greedy + DP
- **为什么合理**：DVD 分配是带容量约束的指派问题，0-1 整数规划是自然表述

---

## 7. 证据记录

### 7.1 DP 核心理论证据

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E-DP-01 | Bellman 最优性原理是 DP 的理论基础 | "An optimal policy has the property that whatever the initial state and initial decision are, the remaining decisions must constitute an optimal policy with regard to the state resulting from the first decision." | Bellman R. Dynamic Programming. Princeton University Press, 1957.（经 Manning 章节和 AI Wiki 交叉引用） | Tier 1 (经典著作) | 高 | 这是 DP 的奠基性原理，所有 DP 应用的逻辑前提 |
| E-DP-02 | DP 需要最优子结构 + 重叠子问题两个必要性质 | "The method applies to any problem exhibiting two structural properties. First, optimal substructure... Second, subproblems must overlap..." | IEEE Technology Navigator - Dynamic Programming | Tier 1 (IEEE) | 高 | IEEE 专业资源的权威定义，与 Stanford/Princeton 课程一致 |
| E-DP-03 | DP 运行时间 = 子问题数 × 每子问题代价 | "running time = # subproblems × cost per subproblem" | Princeton COS 226 Dynamic Programming 讲义 | Tier 1 (大学课程) | 高 | Princeton 算法课程的标准分析框架 |
| E-DP-04 | 无后效性/马尔可夫性是 DP 状态定义的核心检验 | "The defining property of MDPs is the Markov property which says that the future is independent of the past given the current state." | PKU BICMR 讲义 - Dynamic Programming: MDP | Tier 1 (大学课程) | 高 | 北大数学中心讲义，明确马尔可夫性与状态定义的关系 |
| E-DP-05 | Bellman 方程 V*(s)=max_a[R(s,a)+γΣP(s'\|s,a)V*(s')] | Stanford CME 241 讲义给出完整 Bellman 最优性方程和动作价值函数 Q*(s,a) | Stanford CME 241 - A Guided Tour of MDP and Bellman Equations | Tier 1 (大学课程) | 高 | Stanford 专业课程讲义，公式完整 |
| E-DP-06 | DP 不适用连续状态空间（维数灾难） | "直接应用经典DP面临'维数灾难'——连续资源变量需离散化处理，若将水与食物各划分为100个等级，则状态总数达10^4量级" | CSDN 文库 - 2020B 穿越沙漠建模与求解分析 | Tier 3 (竞赛分析) | 中 | 竞赛实践中的观察，需结合理论理解；维数灾难是 DP 的经典局限 |
| E-DP-07 | 贪心需要额外的贪心选择性质，DP 则不需要 | "Greedy methods require the greedy-choice property in addition to optimal substructure. Dynamic programming, by contrast, systematically evaluates subproblems... and guarantees a global optimum when the problem has optimal substructure and overlapping subproblems." | Coursify - DP and Greedy Comparative Analysis | Tier 2 (专业教程) | 中高 | 清晰区分了贪心与 DP 的适用条件差异 |

### 7.2 Scheduling 证据

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E-SCH-01 | 调度三域表示法 α\|β\|γ 是标准分类 | Stanford MS&E 324 Lecture 2 明确给出 1/Pm/Qm/Rm/Om/Fm/Jm 机器环境分类及 β、γ 域 | Stanford MS&E 324 - Scheduling and Queueing | Tier 1 (大学课程) | 高 | Stanford 运筹学课程的标准分类体系 |
| E-SCH-02 | 作业车间 Jm‖Cmax 是强 NP-hard | "The scheduling problem denoted as Jm‖Cmax... strongly NP-hard" 及 Dartmouth 讲义确认 | arXiv 2407.18111 + Dartmouth CO 454 | Tier 1 (预印本+课程) | 高 | 调度理论的经典复杂度结论 |
| E-SCH-03 | 调度可建模为析取图 | "The JSSP is governed by two primary sets of constraints. The first is the precedence constraint... The second is the resource constraint, which arises from the limited availability of machines." | Wiley - Heterogeneous Graph Transformers for JSSP | Tier 1 (同行评审) | 高 | Wiley 期刊论文明确调度的两类核心约束 |
| E-SCH-04 | 调度的 IP 表述使用大 M 析取约束 | Dartmouth CO 454 Lecture 19-21 给出完整的作业车间整数规划公式，包括大 M 析取约束 | Dartmouth CO 454 - Shop Scheduling Problems | Tier 1 (大学课程) | 高 | Dartmouth 运筹学课程讲义 |
| E-SCH-05 | F2‖Cmax 可用 Johnson 规则多项式求解 | 调度理论经典结论，多来源交叉验证（Stanford/Dartmouth 课程及 OR 教材） | textbook-level | Tier 1 | 高 | 调度理论中少数可多项式求解的非平凡问题 |

### 7.3 Resource Constraint 证据

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E-RC-01 | 资源分为可再生(renewable)和不可更新(non-renewable) | "The renewable resources are encapsulated into a set Kρ... similarly, there is a set Kv of consumable resources" | Wiley - Multimode RCPSP Selection Based on DEA | Tier 1 (同行评审) | 高 | Wiley 期刊论文明确 RCPSP 的资源分类 |
| E-RC-02 | RCPSP 使用 cumulative 约束建模资源容量 | "cumulative([s_i], [d_i], [r_ik], R_k) for each resource k" 及时间传播机制 | GitHub Constraint Solving POTD - RCPSP | Tier 2 (专业技术资源) | 中高 | CP 社区对 RCPSP 标准约束的描述 |
| E-RC-03 | 2020_B 多玩家共享资源产生外部性 | 题面 Q3 规则："若某天其中的任意k名玩家均从区域A行走到区域B，则他们中的任一位消耗的资源数量均为基础消耗量的2k倍" | CUMCM 2020_B 官方题面 | Tier 1 (官方) | 高 | 题目原文明确的共享资源外部性 |
| E-RC-04 | 资源约束是 LP/IP 模型的核心约束类型 | "LP models are particularly effective for resource allocation problems" 及 IP 扩展用于离散资源分配 | IJFMR - Mathematical Optimization for Scheduling | Tier 2 (专业期刊) | 中高 | 运筹学中资源分配与 LP/IP 的标准对应关系 |

### 7.4 L3 标签层级证据

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E-L3-01 | graph 是独立的离散数学分支 | "Graph theory is the branch of discrete mathematics that studies graphs: abstract structures consisting of vertices connected by edges. Graphs model pairwise relationships in almost any domain." | IEEE Technology Navigator - Graph Theory | Tier 1 (IEEE) | 高 | IEEE 对图论的权威定义，明确其独立学科地位 |
| E-L3-02 | 最短路径可表述为 LP | Chalmers MVE165 讲义及 PKU BICMR 讲义均给出最短路径的 LP 公式：min Σc_ij x_ij s.t. 流量平衡约束 | Chalmers + PKU BICMR 讲义 | Tier 1 (大学课程) | 高 | 图论问题与 optimization 的等价表述关系 |
| E-L3-03 | 数学规划分为 LP/NLP/IP/MILP | "Linear programming (LP)... Integer programming (IP) adds integrality constraints... Branch-and-bound partitions the feasible space" | IEEE Technology Navigator - Optimization Methods + Mathematical Programming | Tier 1 (IEEE) | 高 | IEEE 对数学规划分类的权威描述 |
| E-L3-04 | IP 因整数约束引入非凸性 | "Integer Programming (IP) falls within the broader category of mathematical programming, specifically as a subclass of combinatorial optimization... hierarchically positioned under nonlinear programming due to the non-convexity introduced by integrality" | StudyGuides - Integer Programming | Tier 2 (专业学习资源) | 中 | 技术上正确但实践中 IP 通常独立处理，标记为中置信度 |
| E-L3-05 | MILP 求解器基于 B&B（Land and Doig 1960） | "Modern MILP solvers are built upon the branch-and-bound (B&B) paradigm (Land and Doig 1960)" | arXiv 2511.09219 - Planning in Branch-and-Bound | Tier 1 (预印本) | 高 | 明确引用 B&B 的奠基性文献 |

### 7.5 竞赛题证据

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E-CMP-01 | 2020_B 可建模为 DP，状态=(天数,区域,水量,食物量) | "设状态dp[k][j][w][f]代表第k天时在第j个点剩余水为w箱剩余食物为f箱的最大资金" | dummerchen.github.io - 2020B 穿越沙漠 + CSDN 多篇方案 | Tier 3 (竞赛解) | 中高 | 多个独立竞赛解决方案一致使用此 DP 状态定义 |
| E-CMP-02 | 2020_B Q2 是 MDP（天气随机） | "本题本质上是一个离散时间、有限状态空间的马尔可夫决策过程（MDP）" 及国一方案使用 MDP + 线性规划 | CSDN 文库 + GitHub youngzhou1999（国一） | Tier 2-3 | 中 | 国一获奖方案使用 MDP 框架，CSDN 分析确认 |
| E-CMP-03 | 2018_B 获奖方案使用 GA 优化调度序列 | "用遗传进化的方式来优化贪婪的结果。将每次去的CNC的编号按顺序串起来，形成一个长度为好几百的序列" | GitHub Hecate2/CUMCM_2018_ProblemB（国一） | Tier 2 (竞赛解) | 中高 | 国一获奖方案的明确描述 |
| E-CMP-04 | 2018_B 可用 0-1 规划建模 | "以RGV的调度路径为决策变量，以获得最多成料为目标函数，约束条件为...根据0-1规划的思想建立单目标规划模型" | 中国大学生在线 - 2018B 获奖论文 B203 + book118 获奖论文 | Tier 2 (官方展示论文) | 中高 | 官方展示的获奖论文明确使用 0-1 规划 |
| E-CMP-05 | 2020_B 当前方法卡选择 mc-ga 是知识缺口导致的误选 | "本题核心是多阶段资源约束下的序列决策优化。理想方法为动态规划(DP)，但方法卡库中无DP专用卡...遗传算法是最接近DP的替代" | P15 b0_manifest 2020_B 02_method_selection.json | Tier 1 (内部审计数据) | 高 | 项目内部 B0 基线数据明确记录了此方法选择及其原因 |

---

## 8. 争议与不确定项

### 8.1 UNCERTAIN 项

| ID | 内容 | 争议点 | 当前倾向 | 置信度 |
|---|---|---|---|---|
| U-01 | **integer programming 是否应提升为 L3 一级标签（与 optimization 并列）** | 一种观点认为 IP 有完全不同的求解方法和问题结构，应独立；另一种观点认为 IP 是 mathematical programming 的子类，应作为 optimization 的子标签 | 保持 optimization 为一级伞标签，IP 为子标签。理由：层级一致性——graph/probability/DE 是并列的数学范式，IP 是 optimization 范式内的子类 | 中高 |
| U-02 | **dynamic programming formulation 是否应作为 L3 标签** | Bellman 方程是一种数学表述（L3），但 DP 通常被视为算法（L4）。将 DP formulation 放在 L3 是否会导致与 L4 DP algorithm 的混淆？ | 应作为 L3 子标签，但必须明确标注 "formulation" 后缀以区分于 L4 算法。理由：Bellman 方程作为递归优化表述，与 LP/IP/NLP 同属 L3 数学形式 | 中 |
| U-03 | **state transition 是否应拆分为"决策语境"和"时序语境"两个独立标签** | 当前 L2 state transition 标签被 ARIMA/GM/LSTM（时序预测）和 MDP/DP（决策）共用，但二者语义差异大。是否应拆分为 `state_transition_decision` 和 `state_transition_timeseries`？ | 建议在标签定义中明确区分语境，但不急于拆分为两个独立标签。理由：拆分可能导致标签碎片化；可以通过标签的 `context` 字段区分 | 中 |
| U-04 | **2020_B Q3(2) 的随机博弈是否有实用的精确求解方法** | 多玩家随机博弈的纳什均衡计算在理论上是 PPAD-hard，实际中通常用近似方法（如迭代最佳响应+MC模拟）。但竞赛中是否有队伍使用了更精确的方法？ | 倾向于近似方法（迭代最佳响应 + 蒙特卡洛模拟评估）是竞赛中的主流。精确求解在 n≥3 时计算不可行 | 中低 |
| U-05 | **heuristic 是否应作为 L4 一级标签，还是应拆分为构造启发式/局部搜索/元启发式** | 当前 L4 标签集较粗，heuristic 涵盖了从简单贪心规则到复杂元启发式的广泛范围。拆分有助于更精细的方法评估 | 建议 heuristic 作为一级标签，下设子类型（constructive/local_search/metaheuristic）。理由：保持标签体系简洁，子类型通过字段标注 | 中高 |
| U-06 | **graph 与 network/traffic（L1）的边界** | 有些问题（如交通流）既是 L1 的 network/traffic 问题结构，又是 L3 的 graph 数学表述。如何避免重复标注？ | L1 描述问题的物理/领域结构（交通网络），L3 描述数学表述形式（图论模型）。二者可以同时标注，语义不重复 | 中高 |

### 8.2 待进一步研究的问题

1. **DP 方法卡的具体字段设计**：如果未来创建 mc-dp 方法卡，其 `requires`/`supports`/`risks`/`verification` 字段应如何设计？特别是 `requires` 应包含"最优子结构可证明"、"状态空间多项式可管理"等前置条件
2. **resource constraint 模式卡的设计**：L2 标签是否需要独立的"模式卡"（不同于 L4 方法卡）？模式卡应提供什么内容（约束识别指南、常见建模陷阱、验证清单）？
3. **scheduling 问题的自动分类器**：如何从题面文本自动识别调度问题的 α|β|γ 分类？这对 L1 标签的自动标注有意义
4. **DP 状态空间爆炸的量化阈值**：在数学建模竞赛的计算环境下（通常 8GB 内存，几分钟计算时间），DP 状态空间的实用上限是多少？（经验估计 10^6-10^7，但需实证）
5. **MILP 求解器在竞赛中的适用边界**：scipy.optimize.milp 在竞赛中的变量数/约束数上限是多少？超过后应如何降级到启发式？

---

## 9. 对知识架构校准的核心建议

### 9.1 标签体系建议

| 层 | 建议动作 | 具体内容 |
|---|---|---|
| **L1** | 保留 scheduling | 已在审计报告建议的 10 标签体系中 |
| **L2** | 强化 resource constraint + state transition(决策语境) | 明确 resource constraint 是建模机理而非约束语法；state transition 增加决策语境定义（MDP），与时序语境区分 |
| **L3** | 新增 graph 为一级标签；optimization 下设子标签 | graph 独立一级；optimization 下新增 integer_programming / linear_programming / nonlinear_programming / dynamic_programming_formulation 子标签 |
| **L4** | 新增 DP；扩展 heuristic 子类型 | DP 是本域核心求解器，必须有对应卡/标签；heuristic 下分 constructive/local_search/metaheuristic |

### 9.2 方法卡优先级建议

基于本域研究，建议优先创建的方法卡（按 P0-P2 排序）：

| 优先级 | 方法卡 ID | 类型 | 理由 |
|---|---|---|---|
| **P0** | mc-dp | L4 求解器 | 2020_B method_selection=0 的直接原因；DP 是离散优化域核心求解器；当前完全缺失 |
| **P0** | mc-milp | L4 求解器 | 调度/资源分配的标准精确求解工具；scipy 内置可直接使用；当前无对应卡 |
| **P1** | mc-scheduling | L1 问题结构卡 | 调度是国赛 B 题高频问题结构；需提供问题分类、建模框架、求解器选择指南 |
| **P1** | mc-mdp | L3 表述 + L4 求解 | 随机序贯决策的标准框架；2020_B Q2 核心方法；与 DP 卡互补 |
| **P2** | mc-branch-and-bound | L4 求解器 | 整数规划精确求解的核心算法；可作为 mc-milp 的理论补充 |
| **P2** | mc-graph-optimization | L3 表述 + L4 求解 | 最短路径/最大流/匹配等图优化问题的统一方法卡 |

### 9.3 治理原则重申

- 方法卡 = Constraint/Prior/Validation，不是答案库
- Knowledge coverage must constrain evaluation, not constrain creativity
- 多解模型原则：benchmark 用 allowed_model_families，不用 core_methods/gold method
- 不追求全方法覆盖，聚焦 Tier 0-3 核心覆盖
- LLM = Model Generator（自由建模），Modeling Knowledge = Constraint/Prior（约束资格），Evidence = Adjudication（证据裁决）

---

*本研究文档为离散优化域的知识架构校准证据，所有结论均附来源和置信度。未修改任何 core/knowledge 下的现有文件。*
