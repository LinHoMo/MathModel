# PART A: Taxonomy Audit — 四层知识标签决策审计

> **综合代理**：Research-layer Calibration 综合代理
> **日期**：2026-09-08
> **输入**：4 份领域研究报告 + 原始审计报告
> **治理原则**：方法卡 = Constraint/Prior/Validation；Knowledge coverage constrains evaluation, not creativity
> **Decision 枚举**：KEEP / REVISE / SPLIT / MERGE / ADD / REMOVE

---

## 0. 冲突解决声明

4 份研究报告在以下关键点存在分歧，本审计做出如下统一裁决：

| 冲突点 | discrete_optimization 立场 | network_game 立场 | taxonomy_meta_validation 立场 | continuous_physics 立场 | **本审计裁决** |
|---|---|---|---|---|---|
| L3 optimization 是否拆分 | 下设 LP/IP/NLP/DP_formulation 子标签 | 未涉及 | 不拆分，子类型留 L4 | 未涉及 | **不拆分**。optimization 保持 L3 伞标签；LP/IP/NLP 区分归入 L4 exact_optimizer 的子类型；DP formulation 归入 L2 decision_state_transition + L4 DP_and_MDP。理由：L3 是数学表述形式层，min f(x) s.t. g(x)≤0 是统一框架；变量类型差异是求解器层的事 |
| L3 game-theoretic 是否独立 | 未涉及 | 应独立为 L3 标签 | REJECT，归入 optimization+probability | 未涉及 | **不独立**。博弈的独特性在 L2 interaction_game；L3 用 optimization（Nash↔互补问题）+ probability（混合策略）+ ODE（复制子动力学）组合标注。理由：合作博弈 Shapley 值是公理化解，可归入 analytical_methods（L4）；Nash 求解本质是优化/互补问题 |
| L3 stochastic_process 是否独立 | 未涉及 | 未涉及 | 合并入 probability_and_stochastic | 建议独立 L3 | **合并入 probability_and_stochastic**。随机过程基于概率论/测度论，与 probability 共享数学基础；拆分意义不大 |
| L4 标签数量 | 建议新增 DP, heuristic 子类型 | 建议新增 queuing solver, equilibrium algorithms, simulation | 建议 12 标签 | 建议新增 numerical ODE | **采纳 12 标签方案**（taxonomy_meta_validation 最全面且经 36 题验证），整合各域建议 |
| graph 层级 | L3 一级标签 | L3，不提升 L1 | L3 KEEP | 未涉及 | **L3 KEEP**（三方一致，无冲突） |
| L1 uncertainty | 未涉及 | 未涉及 | 降级为跨层属性 | 未涉及 | **降级为跨层属性**（stochastic/deterministic 维度） |

---

## 1. L1 Problem Structure 标签决策

### 1.1 现有 8 个标签

| Layer | Existing Label | Decision | Evidence | Reason |
|---|---|---|---|---|
| L1 | motion/geometry | **KEEP** | taxonomy §1.2.1 (36题中8题); continuous_physics §1.2 (2024_A板凳龙, 2016_A系泊); audit §2.3 (0卡覆盖) | 空间几何/运动学是国赛A题核心问题结构，跨来源一致确认。边界：涵盖运动学/几何建模/空间定位/光学几何，不涵盖连续力学（力平衡/变形/振动） |
| L1 | network/traffic | **KEEP** | taxonomy §1.2.2 (36题中4题); network_game §1.1 (2016_B, 2019_C, 2025_D); audit §2.3 (0卡覆盖) | 网络/交通问题具有独特的图结构拓扑和流量平衡模式，与其他问题结构区分度高。MCM/ICM D题专门为"运筹学/网络科学" |
| L1 | scheduling | **KEEP** | taxonomy §1.2.3 (36题中5题); discrete_optimization §1 (Graham三域表示法, 2018_B RGV); audit §2.3 (0卡覆盖) | 调度问题核心是时间窗/资源分配/序贯决策，具有稳定问题结构。需与 supply_chain/operations 区分：scheduling=单场景时间分配，supply_chain=多环节协调 |
| L1 | diffusion | **REVISE**（重命名为 diffusion/heat_transfer） | taxonomy §1.2.4 (36题中2题); continuous_physics §1.1 (Fick/Fourier定律, 抛物型PDE); audit §2.3 (0卡覆盖) | 热传导/扩散是经典问题结构，具有明确物理机理和稳定求解范式。重命名为 diffusion/heat_transfer 更准确。虽仅2题，但在更广泛数学建模领域涵盖污染物扩散、化学传质 |
| L1 | competition/game | **KEEP** | taxonomy §1.2.5 (36题中2题); network_game §1.2 (Nash均衡, 多玩家策略互动); discrete_optimization §6.1 (2020_B Q3); audit §2.3 (0卡覆盖) | 博弈问题具有独特的多玩家交互/均衡分析结构，与单决策者优化有本质区别。国赛中纯博弈题不多，但博弈元素常嵌入调度/决策题 |
| L1 | decision | **REVISE**（重命名为 decision_evaluation，与 data/evaluation 拆分后独立） | taxonomy §1.2.6 (36题中9题); audit §2.3 (5卡覆盖) | 决策/评价问题核心是指标体系→赋权→排序/选择，与纯数据分析有不同建模目标。拆分后 decision_evaluation 独立存在 |
| L1 | uncertainty | **REMOVE**（从L1降级为跨层属性维度） | taxonomy §1.2.7 (36题仅1题以uncertainty为主要结构); Wiley教材分类: deterministic/stochastic是模型属性维度 | uncertainty是所有问题类型都可能具有的属性，不是独立问题结构。将其作为L1标签导致分类冲突（热传导题涉及随机参数应标diffusion还是uncertainty？）。降级为跨层属性 stochastic/deterministic |
| L1 | data/evaluation | **SPLIT**（拆分为 data_analysis + decision_evaluation） | taxonomy §1.2.8 (11题内部异质性大); audit §2.3 (10卡覆盖) | data_analysis核心是从数据中提取模式（回归/分类/聚类/降维/时序），decision_evaluation核心是构建指标体系并排序/选择。两者建模目标、验证方法、失败模式完全不同。中国大学MOOC将"一元统计模型""多元统计分析模型"与"评价模型"分开教学 |

### 1.2 新增标签

| Layer | New Label | Decision | Evidence | Reason |
|---|---|---|---|---|
| L1 | continuous_mechanics | **ADD** | taxonomy §1.3.1 (36题中4题: 2016_A锚链, 2019_A振动, 2019_B碰撞, 2022_A振动); CUMCM-HMML领域7.1"物理/力学建模" | 连续力学核心是力平衡/变形/振动动力学，与motion/geometry的纯运动学/几何有本质区别。L3是ODE（牛顿第二定律）或代数方程（静力学平衡），L4是numerical_ODE或nonlinear_solver。与motion/geometry有清晰层间区分 |
| L1 | supply_chain/operations | **ADD**（MEDIUM置信度，允许与scheduling多标） | taxonomy §1.3.2 (36题中2题: 2021_C, 2024_C); MCM/ICM D题定义; CUMCM-HMML领域10 | 供应链/运营问题涉及多环节库存-运输-生产协调，与单一场景的scheduling（如RGV调度）有不同问题结构。国赛中此类题目较少（2/36），但MCM/ICM D题和运筹学领域稳定。允许与scheduling多标 |
| L1 | optical/inverse | **REJECT**（移至L2 inverse_problem） | taxonomy §1.3.3 (36题中3+2题涉及反演); continuous_physics §8.2 (inverse problem放L2) | 反问题通常与其他L1标签共存（2018_A同时是diffusion，2017_A同时是motion/geometry），不是独立问题结构。放在L2（建模模式）更合适：inverse_problem描述"已知输出反求输入/参数"的建模方向 |
| L1 | rule_based | **REJECT**（UNCERTAIN，暂不新增） | taxonomy §1.3.4 (36题仅1题2015_C农历历法) | 单一题目不具备稳定、可区分、可复用的地位。将2015_C归入data_analysis或作为outlier处理。若未来出现≥3题规则建模，重新评估 |

### 1.3 L1 最终标签集（9 个结构标签 + 1 个属性维度）

```
motion/geometry, continuous_mechanics, diffusion/heat_transfer, network/traffic,
scheduling, supply_chain/operations, competition/game, decision_evaluation,
data_analysis
+ [属性] stochastic/deterministic（原uncertainty降级）
```

---

## 2. L2 Modeling Pattern 标签决策

### 2.1 现有 8 个标签

| Layer | Existing Label | Decision | Evidence | Reason |
|---|---|---|---|---|
| L2 | state transition | **SPLIT**（拆分为 temporal_recurrence + decision_state_transition） | taxonomy §2.2.1 (ARIMA/GM/LSTM自治递推 vs MDP/DP决策依赖); discrete_optimization §2.2 (MDP五元组, Bellman方程); audit §2.3 (仅时序语境覆盖) | 时序递推是自治系统 x_{t+1}=f(x_t)，无决策变量；MDP是决策系统 x_{t+1}=f(x_t,a_t)，状态转移依赖行动选择。2020_B核心是MDP但原标签无时序语境外的覆盖。两者验证方法不同（时序用回测，MDP用策略收敛/值迭代） |
| L2 | conservation law | **KEEP** | taxonomy §2.2.2 (2018_A能量守恒, 2016_A力平衡); continuous_physics §2.1 (积分形式→微分形式PDE, 三大守恒律); audit §2.3 (0卡覆盖) | 守恒律是连续物理建模的第一性原理，从守恒律出发推导控制方程是标准建模路径。与flow_balance边界清晰：conservation law→连续场(PDE)，flow balance→离散网络(代数方程/图) |
| L2 | flow balance | **KEEP** | taxonomy §2.2.3 (2019_C, 2016_B, 2025_D); network_game §2.1 (节点流量守恒, 与conservation law区分); audit §2.3 (0卡覆盖) | 流量平衡是网络/交通问题的核心建模模式。数学形式是节点流量守恒方程。与conservation law的区别：conservation law是连续介质的物理守恒原理（积分→微分），flow balance是离散节点的流量会计（入流=出流+累积） |
| L2 | distance/geometry | **REVISE**（重命名为 geometric_constraint，扩展语义） | taxonomy §2.2.4 (当前仅TOPSIS使用, 2024_A核心是几何约束); continuous_physics §2.3 (刚体约束/碰撞检测/螺线参数化); audit §2.3 (仅TOPSIS弱覆盖) | 重命名为geometric_constraint后涵盖：(1)空间距离/轨迹约束（运动学、碰撞检测）；(2)几何投影/变换（CT标定、定位）；(3)评价空间中的距离度量（TOPSIS）。原标签语义被TOPSIS窄化，需扩展到运动学/几何建模语境 |
| L2 | resource constraint | **KEEP** | taxonomy §2.2.5 (2020_B, 2018_B, 2021_C, 2024_C); discrete_optimization §2.1 (7种资源类型, 可再生/不可更新); audit §2.3 (0卡覆盖) | 资源约束是将实际问题转化为数学规划的关键步骤：识别有限资源（时间/预算/容量/负重）并表达为不等式约束。是稳定、可区分的建模模式。注意：这是L2建模机理，不是L3的Ax≤b约束语法 |
| L2 | queue | **KEEP** | taxonomy §2.2.6 (2019_C典型排队论); network_game §2.2 (Kendall记号, Little定理, M/M/c); audit §2.3 (0卡覆盖) | 排队模式具有独特的到达-服务-等待结构，与一般flow balance不同：queue关注随机过程下的等待时间/队列长度分布，flow balance关注确定性流量守恒。高教社教材设"排队论"独立章节 |
| L2 | spatial-temporal field | **KEEP** | taxonomy §2.2.7 (2018_A温度场, 2020_A回流焊); continuous_physics §2.2 (u(x,t), 三种边界条件, Hadamard适定性); audit §2.3 (0卡覆盖) | 时空场是区分PDE问题与ODE/代数问题的关键：未知量是场函数（空间+时间分布）则需要PDE表述；仅是时间函数则是ODE。是稳定的建模模式分类 |
| L2 | interaction/game | **KEEP**（重命名为 interaction_game） | taxonomy §2.2.8 (2020_B, 2019_C, 2025_D); network_game §2.3 (判定测试: 固定他方策略本方最优解是否变化); discrete_optimization §6.1 (2020_B Q3); audit §2.3 (0卡覆盖) | interaction_game是区分单决策者优化与多决策者博弈的关键建模模式。核心分析工具是纳什均衡/最优响应。判定规则：如果修改其他主体策略会改变本主体最优选择，则是博弈；如果其他主体行为可视为固定外部环境参数，则是优化 |

### 2.2 新增标签

| Layer | New Label | Decision | Evidence | Reason |
|---|---|---|---|---|
| L2 | statistical_association | **ADD** | taxonomy §2.3.1 (36题中11题数据驱动但L2无对应标签; regression 7次, statistical_analysis 8次); 中国大学MOOC"一元统计模型""多元统计分析模型" | 统计关联是数据驱动建模的核心模式：通过统计方法（回归/分类/聚类/相关/降维）发现变量间关联关系。这是与机理驱动建模（conservation law/flow balance）并列的两大建模范式之一。当前L2完全缺失此标签，导致所有data_analysis题在L2层无家可归 |
| L2 | inverse_problem | **ADD** | taxonomy §2.3.2 (36题中5题涉及反演; allowed_model_families中inverse_problem出现5次); continuous_physics §8.2 (2018_A参数反演, 不适定性+正则化) | 反问题核心模式是"已知观测输出，反求输入/参数/初始条件"，与正问题"已知输入求输出"建模方向相反。具有独特特征：(1)通常不适定(ill-posed)，需正则化；(2)目标函数是观测值与模拟值残差最小化；(3)验证需扰动稳定性分析。放在L2（而非L1，因为通常与其他L1标签共存） |

### 2.3 L2 最终标签集（11 个）

```
temporal_recurrence, decision_state_transition, conservation_law, flow_balance,
geometric_constraint, resource_constraint, queue, spatial_temporal_field,
interaction_game, statistical_association, inverse_problem
```

---

## 3. L3 Mathematical Formulation 标签决策

### 3.1 现有 6 个标签

| Layer | Existing Label | Decision | Evidence | Reason |
|---|---|---|---|---|
| L3 | optimization | **KEEP**（不拆分，子类型留L4） | taxonomy §3.2.1 (36题中optimization出现39次最高频); discrete_optimization §3.2 (建议下设子标签，但本审计裁决不拆分); audit §2.3 (5卡覆盖) | L3是"数学表述形式"层，optimization作为统一表述形式（min f(x) s.t. g(x)≤0）是稳定的。LP/IP/NLP/MOP的区别在于约束和变量类型，属于L4 solver层的精确求解器分类。在L3拆分optimization会导致标签爆炸（LP/IP/NLP/MIP/SOCP/SDP...），且这些子类型共享同一数学框架 |
| L3 | differential equation | **SPLIT**（拆分为 ODE + PDE） | taxonomy §3.2.2 (36题中11题涉及DE, ODE用RK4, PDE用有限差分); continuous_physics §3 (6项论据: 物理本质/定解条件/数值方法/竞赛题分布均不同); CUMCM-HMML将1.1和1.2分为两个子领域; audit §2.3 (仅grey DE弱覆盖) | ODE和PDE的数学性质、求解方法、验证方式完全不同：(1)ODE是单变量（通常时间）微分方程，PDE是多变量（空间+时间）；(2)ODE求解用RK4/odeint，PDE求解用有限差分/有限元；(3)ODE验证是初值敏感性/平衡点稳定性，PDE验证是网格收敛性/边界条件正确性。methodology/ode-pde.md决策树第一步就是区分ODE和PDE |
| L3 | graph | **KEEP**（确认一级标签地位） | taxonomy §3.2.3 (36题中4题; CUMCM-HMML领域4); discrete_optimization §3.1 (独立数学范式, 图论问题不一定是优化问题); network_game §3.1 (保持L3, 不提升L1); audit §2.3 (0卡覆盖) | graph是独立的数学表述形式：用顶点和边表示系统结构，用邻接矩阵/关联矩阵表示关系。与optimization（目标函数+约束）、differential_equation（导数关系）、statistics（数据分布）有本质区别。三方一致确认L3地位。当前16张方法卡中graph零覆盖是卡库问题，不是标签问题 |
| L3 | probability | **REVISE**（扩展为 probability_and_stochastic） | taxonomy §3.2.4 (36题中probability_modeling 3次, simulation 8次); continuous_physics §3.4 (建议stochastic process独立但本审计裁决合并); network_game §2.2 (排队论基于生灭过程) | probability涵盖：概率分布、随机过程（马尔可夫链/泊松过程/布朗运动）、排队论、蒙特卡洛。当前标签名probability偏窄，扩展为probability_and_stochastic更准确。随机过程与probability共享概率空间基础，拆分意义不大（continuous_physics的独立建议被taxonomy的合并建议否决，因为CUMCM-HMML将二者放在同一领域） |
| L3 | statistics | **KEEP** | taxonomy §3.2.5 (36题中statistical_analysis 8次, 16卡中11张涉及); audit §2.3 (11卡覆盖, 最强层) | statistics是数据驱动建模的核心数学表述，涵盖回归、分类、聚类、假设检验、方差分析。与probability的边界：probability关注随机过程的理论分布，statistics关注从数据中估计和推断 |
| L3 | linear algebra | **KEEP** | taxonomy §3.2.6 (36题中geometric_modeling 8次, PCA 1次; 16卡中5张涉及); audit §2.3 (5卡覆盖) | linear algebra是几何建模、降维、谱方法的数学基础。虽然常作为工具出现在其他表述中，但作为独立L3标签有稳定地位（如纯几何问题的核心就是线性代数变换） |

### 3.2 新增/否决标签

| Layer | New Label | Decision | Evidence | Reason |
|---|---|---|---|---|
| L3 | stochastic_process | **MERGE**（并入 probability_and_stochastic，不独立） | taxonomy §3.3.1 (CUMCM-HMML将概率建模与随机过程放在同一领域); continuous_physics §8.1 (建议独立但置信度medium) | 随机过程（马尔可夫链、排队论、布朗运动）是概率理论的延伸。在L3层，probability和stochastic_process共享同一数学基础（测度论/概率空间），拆分意义不大。将probability标签语义扩展为probability_and_stochastic即可 |
| L3 | game_theoretic_formulation | **REJECT**（不独立，归入optimization+probability组合） | taxonomy §3.3.2 (博弈论本质是多目标优化+概率); network_game §3.2 (建议独立但本审计裁决否决) | 博弈的独特性在L2（interaction_game建模模式），不在L3。Nash均衡求解可转化为优化问题（线性互补问题/变分不等式）；混合策略是概率分布；合作博弈Shapley值是公理化解，归入L4 analytical_methods。在L3不独立可避免标签膨胀 |
| L3 | integer_programming / nonlinear_programming | **REJECT**（归入optimization，留L4区分） | taxonomy §3.3.3 (LP/IP/NLP共享min f(x) s.t. constraints框架); discrete_optimization §3.2 (建议下设子标签但本审计裁决不拆分) | LP/IP/NLP共享同一optimization框架，区别在变量类型和约束性质，属于L4 solver层分类。在L3拆分会导致标签爆炸且语义重叠 |

### 3.3 L3 最终标签集（7 个）

```
optimization, ODE, PDE, graph, probability_and_stochastic, statistics, linear_algebra
```

---

## 4. L4 Solver/Algorithm 标签决策

### 4.1 现有 6 个标签

| Layer | Existing Label | Decision | Evidence | Reason |
|---|---|---|---|---|
| L4 | numerical PDE | **KEEP** | taxonomy §4.2.1 (36题variants中finite_difference 3次, finite_element 3次); continuous_physics §4 (FDM/FEM/FVM九维对比, Lax等价定理, Crank-Nicolson); audit §2.3 (0卡覆盖) | numerical PDE是独立求解器类别（有限差分/有限元/有限体积），与ODE求解器（RK4）和通用优化器有本质区别。2018_A和2020_A的核心求解器 |
| L4 | DP | **REVISE**（扩展为 DP_and_MDP） | taxonomy §4.2.2 (36题variants中dynamic_programming 1次, MDP 2次); discrete_optimization §4.1 (Bellman原理, 最优子结构, 重叠子问题, 无后效性); audit §2.3 (0卡覆盖) | DP/MDP是独立求解范式（最优子结构+重叠子问题），与通用优化器和元启发式有本质区别。2020_B的核心求解器。扩展为DP_and_MDP以涵盖确定性DP和随机MDP值迭代/策略迭代 |
| L4 | Monte Carlo | **KEEP** | taxonomy §4.2.3 (36题variants中monte_carlo 3次); network_game §4.4 (MC仿真, 多种子≥5次); audit §2.3 (1卡覆盖mc-monte-carlo) | 蒙特卡洛是基于随机抽样的数值计算方法，适用于不确定性传播、复杂系统仿真、高维积分。是独立求解器类别。注意：与simulation的区别——Monte Carlo关注随机抽样的统计估计，simulation关注系统动态演化过程 |
| L4 | GA | **REVISE**（扩展为 metaheuristic_optimization，含GA/PSO/SA/DE/tabu） | taxonomy §4.2.4 (36题variants中GA出现14次最高频; PSO 1次, tabu 1次, NSGA_II 1次); discrete_optimization §4.4 (构造启发式/局部搜索/元启发式); audit §2.3 (mc-ga/mc-pso/mc-sa三张卡但L4仅GA标签) | GA、PSO、SA、DE、tabu search共享同一求解范式：基于种群/邻域的随机搜索，不保证全局最优，需要多种子运行统计。将它们统一为metaheuristic_optimization标签，比单独列GA更合理。GA是其子类。CUMCM-HMML子领域2.5"组合优化与元启发式"也采用此分类 |
| L4 | regression | **REVISE**（扩展为 regression_and_supervised） | taxonomy §4.2.5 (36题variants中regression类方法出现30次最高频); audit §2.3 (5卡覆盖: mc-ols/mc-arima/mc-grey-gm11/mc-lstm/mc-xgboost) | regression涵盖参数回归（OLS/Logistic）、非参数回归（树模型）、时序预测（ARIMA/LSTM）。这些方法共享"从数据中学习输入-输出映射"的求解范式。扩展为regression_and_supervised更准确 |
| L4 | clustering | **KEEP** | taxonomy §4.2.6 (36题variants中kmeans 2次); audit §2.3 (1卡覆盖mc-kmeans) | 聚类是无监督学习的核心求解范式，与回归（有监督）有本质区别 |

### 4.2 新增标签

| Layer | New Label | Decision | Evidence | Reason |
|---|---|---|---|---|
| L4 | exact_optimizer | **ADD** | taxonomy §4.3.1 (36题variants中LP 2次, IP 3次, 约束优化等共12次); discrete_optimization §4.2-4.3 (B&B, MILP求解器Gurobi/CPLEX/SCIP); CUMCM-HMML领域2.1/2.2 | exact_optimizer（LP/IP/NLP精确求解器）与metaheuristic的区别是：前者保证最优解（在凸问题中），后者只给近似解。当前L4标签集完全缺失精确求解器类别，导致2018_B(RGV调度→整数规划)、2021_C(供应链→LP/IP)等题在L4无对应标签 |
| L4 | numerical_ODE | **ADD** | taxonomy §4.3.2 (36题variants中Runge_Kutta 2次, multi_body_dynamics 2次); continuous_physics §4.7 (运动学数值求解与numerical PDE区分); methodology/ode-pde.md决策树: ODE→Euler/RK4/odeint | ODE求解器（RK4/Euler/odeint/打靶法）与PDE求解器（有限差分/有限元）是不同的数值方法族。L3拆分ODE/PDE后，L4必须对应拆分。2016_A(锚链)、2019_A(振动)、2022_A(振动)、2024_A(运动学)的核心求解器 |
| L4 | simulation | **ADD** | taxonomy §4.3.3 (36题variants中DES 3次, ABM 2次, CA 1次等共9次); network_game §4.4 (DES/ABS/MC/SD分类); CUMCM-HMML领域8; methodology/simulation.md | simulation（离散事件仿真/多智能体仿真/元胞自动机）是独立求解范式：通过时间步进模拟系统演化，不追求解析解。与Monte Carlo（随机抽样计算）的区别：simulation关注系统动态演化过程，Monte Carlo关注随机抽样的统计估计 |
| L4 | analytical_methods | **ADD** | taxonomy §4.3.4 (36题variants中解析/闭式方法出现29次20.1%); audit §1.1 (mc-ahp/mc-topsis/mc-entropy-weight三张决策分析卡均为闭式计算) | analytical_methods涵盖：(1)解析推导（静力平衡方程求解、球面三角）；(2)闭式统计方法（M/M/c排队公式、ANOVA、相关系数）；(3)决策分析方法（AHP/TOPSIS/熵权）。共同特征是有明确的计算公式/步骤，无需迭代搜索。当前L4完全缺失此类别 |
| L4 | graph_algorithm | **ADD**（MEDIUM置信度） | taxonomy §4.3.5 (36题variants中BFS/Dijkstra/A*出现在2025_D); discrete_optimization §3.1 (Dijkstra/Bellman-Ford/Ford-Fulkerson/Dinic); network_game §4.1 (最短路径/最大流/最小费用流); CUMCM-HMML领域4.1; methodology/graph-theory.md | 图算法（最短路/最大流/最小生成树）是独立求解器类别。国赛中纯图算法题不多（1/36），但网络/交通问题常涉及图算法。建议作为L4标签保留 |
| L4 | dimensionality_reduction | **ADD**（归入L4） | taxonomy §4.3.6 (36题variants中PCA 2次, LDA 1次); audit §1.1 (mc-pca卡存在但L4无对应标签) | PCA/LDA是独立的数据变换算法（特征值分解/SVD），既不是回归（无监督），也不是聚类（不分组）。在建模流程中通常是预处理步骤，但作为求解器类别有独立地位。归入L4（而非L3，因为是具体算法而非数学表述形式） |

### 4.3 L4 最终标签集（12 个）

```
numerical_PDE, numerical_ODE, DP_and_MDP, monte_carlo, metaheuristic_optimization,
exact_optimizer, regression_and_supervised, clustering, dimensionality_reduction,
simulation, analytical_methods, graph_algorithm
```

---

## 5. 决策统计汇总

| 层 | 原标签数 | KEEP | REVISE | SPLIT | MERGE | ADD | REMOVE | REJECT | 最终标签数 |
|---|---|---|---|---|---|---|---|---|---|
| L1 | 8 | 3 | 2 | 1 | 0 | 2 | 1 | 2 | 9 + 1属性 |
| L2 | 8 | 6 | 1 | 1 | 0 | 2 | 0 | 0 | 11 |
| L3 | 6 | 4 | 1 | 1 | 1 | 0 | 0 | 2 | 7 |
| L4 | 6 | 2 | 3 | 0 | 0 | 6 | 0 | 0 | 12 |
| **合计** | **28** | **15** | **7** | **3** | **1** | **10** | **1** | **4** | **39 + 1属性** |

---

*本审计为 research-layer calibration 文档，所有决策基于4份领域研究报告的交叉验证和冲突裁决。不涉及修改 core/knowledge 下的任何现有文件。*
