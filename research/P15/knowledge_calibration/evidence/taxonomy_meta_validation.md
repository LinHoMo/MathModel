# Taxonomy Meta-Validation Report — 四层知识结构分类学元验证

> **研究性质**：Research-layer Calibration。验证四层 taxonomy 本身是否合理，不研究具体方法。
> **研究代理**：分类学元验证 + Benchmark 映射代理
> **研究日期**：2026-09-08
> **证据基线**：16 张方法卡 + CUMCM-Bench-v2 (36题) + 5 题 problem card + 跨来源教材/竞赛分类
> **治理原则**：方法卡 = Constraint/Prior/Validation，不是答案库。Knowledge coverage must constrain evaluation, not constrain creativity.

---

## 0. 执行摘要

### 0.1 核心结论

| 层 | 当前标签数 | 验证结论 | 建议标签数 | 关键变更 |
|---|---|---|---|---|
| **L1 Problem Structure** | 8 | **部分合理，需扩展** | 11 | 新增 continuous_mechanics, supply_chain/operations, optical/inverse；拆分 data/evaluation → data_analysis + decision_evaluation；uncertainty 降级为跨层维度 |
| **L2 Modeling Pattern** | 8 | **结构合理，覆盖不足** | 10 | 新增 statistical_association, inverse_problem；state_transition 拆分为 temporal_recurrence + decision_state_transition；distance/geometry 重命名为 geometric_constraint |
| **L3 Mathematical Formulation** | 6 | **基本合理，需细化** | 7 | differential_equation 拆分为 ODE + PDE；graph 保留为一级标签；optimization 不拆分（子类型留 L4）；新增 stochastic_process |
| **L4 Solver/Algorithm** | 6 | **标签集严重不足** | 9 | GA → metaheuristic（含GA/PSO/SA）；新增 exact_optimizer, numerical_ODE, simulation, analytical_methods, graph_algorithm；dimensionality_reduction 归入 L4 |

### 0.2 三题 method_selection=0 归因

| 题目 | 根本缺失层 | 补充后能否解释 | 解释程度 |
|---|---|---|---|
| 2024_A | L1 motion/geometry 零覆盖 → L2 geometric_constraint 缺失 | **是** | 完全解释 |
| 2020_B | L2 decision_state_transition + resource_constraint + interaction_game 缺失 + L4 DP 缺失 | **是** | 完全解释 |
| 2018_A | L1 diffusion + L2 spatial_temporal_field + conservation_law + L4 numerical_PDE 三层联动缺失 | **是** | 完全解释 |

### 0.3 2019_C 假阳性确认

2019_C 的 method_selection=100 是**浅层命中/假阳性**：L1 network/traffic 和 L2 queue/flow_balance/interaction_game 完全缺失，但 L3 optimization/probability/statistics 和 L4 monte_carlo/optimization 碰巧匹配。当前指标仅检查 L4 card family，无法区分"系统覆盖"与"偶然匹配"。

---

## 1. L1 Taxonomy 验证

### 1.1 当前 L1 标签集

```
motion/geometry, network/traffic, scheduling, diffusion, competition/game, decision, uncertainty, data/evaluation
```

### 1.2 逐标签验证

#### 1.2.1 motion/geometry — **KEEP（但需明确边界）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题中 8 题涉及：2015_A(太阳影子定位), 2017_A(CT标定), 2021_A(定日镜), 2022_B(定日镜定位), 2023_A(聚光), 2023_B(地形覆盖), 2024_A(板凳龙运动学), 2025_A(弹体运动) |
| **来源** | CUMCM-Bench-v2.json family 字段 + allowed_model_families |
| **置信度** | HIGH |
| **理由** | 空间几何/运动学是国赛 A 题的核心问题结构之一，具有稳定、可区分的地位。高等教育出版社《数学建模方法及其应用》将"几何分析"列为独立方法类别。MCM/ICM 将 A 题定义为"连续型"，其中几何/运动是主要子类。 |
| **边界说明** | motion/geometry 涵盖：运动学(kinematics)、几何建模(geometric_modeling)、空间定位(spatial positioning)、光学几何(optical geometry)。**不**涵盖连续力学(force equilibrium/deformation/vibration)——后者归入 continuous_mechanics。 |

#### 1.2.2 network/traffic — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题中 4 题：2016_B(小区开放路网), 2019_C(机场出租车), 2024_E(交通信号), 2025_D(水管网络)。CUMCM-HMML 设独立领域"图论与网络"。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML.md 领域4 |
| **置信度** | HIGH |
| **理由** | 网络/交通问题具有独特的图结构拓扑和流量平衡建模模式，与其他问题结构区分度高。MCM/ICM D 题专门为"运筹学/网络科学"。 |

#### 1.2.3 scheduling — **KEEP（但需与 supply_chain 区分）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题中 5 题：2018_B(RGV调度), 2019_B(碰撞周期), 2020_B(穿越沙漠), 2021_C(供应链), 2024_B(概率决策)。CUMCM-HMML 设"运筹与调度"领域。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML.md 领域10 |
| **置信度** | HIGH |
| **理由** | 调度问题的核心是时间窗/资源分配/序贯决策，具有稳定的问题结构。但 2021_C 和 2024_C 更偏供应链/运营，需独立标签。 |

#### 1.2.4 diffusion — **KEEP（但建议重命名为 diffusion/heat_transfer）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP，建议重命名 |
| **证据** | 36 题中 2 题：2018_A(高温作业服装热传导), 2020_A(回流焊温度场)。两题均为抛物型 PDE（热传导方程）。 |
| **来源** | CUMCM-Bench-v2 + card.yaml 2018_A |
| **置信度** | MEDIUM |
| **理由** | 虽然仅 2 题，但热传导/扩散是数学建模的经典问题结构，具有明确的物理机理（傅里叶定律→能量守恒→抛物型PDE）和稳定的求解范式（有限差分/有限元）。在更广泛的数学建模领域，扩散还涵盖污染物扩散、化学传质等。重命名为 diffusion/heat_transfer 更准确。 |
| **UNCERTAIN** | 是否应与 continuous_mechanics 合并为 broader "continuous_physics"？见 §10 争议项。 |

#### 1.2.5 competition/game — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题中 2 题：2020_B(多玩家穿越沙漠), 2025_D(水管网络博弈)。CUMCM-HMML 将博弈论归入"评价与决策分析"子领域6.3。高等教育出版社教材设"对策论"独立章节。 |
| **来源** | CUMCM-Bench-v2 + 高教社教材目录 + CUMCM-HMML |
| **置信度** | MEDIUM |
| **理由** | 博弈问题具有独特的多玩家交互/均衡分析结构，与单决策者的优化问题有本质区别。虽然国赛中纯博弈题不多，但博弈元素常嵌入调度/决策题中（如 2019_C 司机-乘客匹配）。 |

#### 1.2.6 decision — **KEEP（但需与 data/evaluation 拆分）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP，与 data/evaluation 拆分 |
| **证据** | 36 题中 9 题涉及决策/评价：2015_B, 2017_B, 2018_C, 2019_C, 2020_C, 2022_C, 2023_C, 2024_C, 2025_C。CUMCM-HMML 设"评价与决策分析"独立领域。高教社教材设"综合评价""多目标决策分析""随机决策分析"独立章节。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML 领域6 + 高教社教材 |
| **置信度** | HIGH |
| **理由** | 决策/评价问题的核心是指标体系→赋权→排序/选择，与纯数据分析（回归/分类/聚类）有不同的建模目标。当前 decision 和 data/evaluation 混在一起，导致标签语义模糊。 |

#### 1.2.7 uncertainty — **REVISE（降级为跨层维度，不作为 L1 一级标签）**

| 项目 | 内容 |
|---|---|
| **决策** | REVISE — 从 L1 一级标签降级为跨层维度(cross-cutting dimension) |
| **证据** | 36 题中仅 1 题(2024_B)以 uncertainty 为主要问题结构。不确定性是**所有问题类型都可能具有的属性**，不是独立的问题结构。2018_A 有参数反演的不确定性，2020_B 有天气随机性，2019_C 有到达率随机性——这些题的 L1 分别是 diffusion, scheduling, network/traffic，uncertainty 是它们的共同属性。 |
| **来源** | CUMCM-Bench-v2 + Wiley《Mathematical Modeling and Simulation》分类：deterministic vs stochastic 是模型属性维度，不是问题结构 |
| **置信度** | HIGH |
| **理由** | 将 uncertainty 作为 L1 标签会导致分类冲突：一道热传导题如果涉及随机参数，应该标 diffusion 还是 uncertainty？正确的做法是 L1 标问题结构(diffusion)，同时在属性维度标 stochastic。Wiley 教材明确将 deterministic/stochastic 列为模型分类维度，与 problem structure 正交。 |

#### 1.2.8 data/evaluation — **SPLIT（拆分为 data_analysis + decision_evaluation）**

| 项目 | 内容 |
|---|---|
| **决策** | SPLIT |
| **证据** | 当前 data/evaluation 覆盖 11 题，但内部异质性极大：2016_C(电池预测)是时序预测，2017_C(颜色浓度)是回归标定，2022_C(古代玻璃)是聚类+判别，2025_E(人体运动)是信号分析。这些与 2015_B(出租车评价)、2022_C(玻璃评价)的评价/决策问题有本质不同。 |
| **来源** | CUMCM-Bench-v2 family 字段 + 中国大学MOOC课程分类："一元统计模型""多元统计分析模型"与"评价模型"分开教学 |
| **置信度** | HIGH |
| **理由** | data_analysis 的核心是从数据中提取模式/关系（回归、分类、聚类、降维、时序），decision_evaluation 的核心是构建指标体系并对方案排序/选择。两者的建模目标、验证方法、失败模式完全不同。CSDN 流行的"四大模型"（优化、分类、评价、预测）也将评价与预测/分类分开。 |

### 1.3 新增标签验证

#### 1.3.1 continuous_mechanics — **ADD（HIGH confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD |
| **证据** | 36 题中 4 题：2016_A(锚链静力学), 2019_A(振动), 2019_B(碰撞周期映射), 2022_A(振动)。这些问题的核心是力平衡/变形/振动动力学，与 motion/geometry 的纯运动学/几何有本质区别。CUMCM-HMML 设"机理建模"领域7.1"物理/力学建模"。高教社教材虽未单列，但力学建模是微分方程建模的主要应用场景。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML 领域7.1 |
| **置信度** | HIGH |
| **理由** | continuous_mechanics 的核心建模模式是 force_equilibrium / constitutive_relation / vibration_dynamics，L3 是 ODE（牛顿第二定律）或代数方程（静力学平衡），L4 是 numerical_ODE 或 nonlinear_solver。这与 motion/geometry（L2=geometric_constraint，L3=linear_algebra/optimization，L4=analytical/numerical_solver）有清晰的层间区分。 |

#### 1.3.2 supply_chain/operations — **ADD（MEDIUM confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD |
| **证据** | 36 题中 2 题：2021_C(原材料订购运输), 2024_C(生产调度)。MCM/ICM D 题定义为"Operations Research/Network Science"。CUMCM-HMML 设"运筹与调度"领域10，含生产调度/路径规划/资源分配。 |
| **来源** | CUMCM-Bench-v2 + MCM/ICM 官方分类 + CUMCM-HMML 领域10 |
| **置信度** | MEDIUM |
| **理由** | 供应链/运营问题涉及多环节库存-运输-生产协调，与单一场景的 scheduling（如 RGV 调度）有不同的问题结构。但国赛中此类题目较少（2/36），且与 scheduling 边界有重叠。**建议作为 L1 标签保留，但允许与 scheduling 多标**。 |

#### 1.3.3 optical/inverse — **ADD（MEDIUM confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD（但更准确的名称是 inverse_problem，optical 是其应用场景） |
| **证据** | 36 题中 3 题涉及反问题：2017_A(CT图像重建/Radon变换), 2018_A(热参数反演), 2025_B(光学干涉厚度反演)。2015_A(经纬度反演)也涉及反演。反问题在数学建模中具有独特的"已知输出求输入/参数"结构，与正问题"已知输入求输出"有本质区别。 |
| **来源** | CUMCM-Bench-v2 allowed_model_families: inverse_problem 出现 5 次 |
| **置信度** | MEDIUM |
| **理由** | 反问题的核心特征是不适定性(ill-posedness)，需要正则化处理，验证方法也不同（需要真值对比或扰动稳定性分析）。但反问题通常与其他 L1 标签共存（2018_A 同时是 diffusion，2017_A 同时是 motion/geometry），因此更适合作为 L2 modeling_pattern 而非 L1。**最终决策：inverse_problem 放在 L2，optical/inverse 不作为 L1 独立标签。** |

#### 1.3.4 rule_based — **CONSIDER（LOW confidence，标记 UNCERTAIN）**

| 项目 | 内容 |
|---|---|
| **决策** | UNCERTAIN — 暂不新增 |
| **证据** | 36 题中仅 1 题(2015_C 农历历法)属于纯规则建模。此类问题在数学建模竞赛中极为罕见。 |
| **来源** | CUMCM-Bench-v2 2015_C |
| **置信度** | LOW |
| **理由** | 单一题目的标签不具备稳定、可区分、可复用的地位。建议将 2015_C 归入 data/evaluation 或作为 outlier 处理。 |

### 1.4 L1 验证总结

| 原标签 | 决策 | 新标签 | 36题覆盖数 |
|---|---|---|---|
| motion/geometry | KEEP | motion/geometry | 8 |
| network/traffic | KEEP | network/traffic | 4 |
| scheduling | KEEP | scheduling | 5 |
| diffusion | KEEP(重命名) | diffusion/heat_transfer | 2 |
| competition/game | KEEP | competition/game | 2 |
| decision | KEEP | decision_evaluation | 9 |
| uncertainty | REVISE(降级) | ~~uncertainty~~ → cross-cutting dimension | 1(属性) |
| data/evaluation | SPLIT | data_analysis | 11 |
| — | ADD | continuous_mechanics | 4 |
| — | ADD | supply_chain/operations | 2 |
| — | — | optical/inverse → 移至 L2 inverse_problem | — |
| — | — | rule_based → UNCERTAIN，暂不新增 | 1 |

**建议 L1 标签集（10 个）**：
```
motion/geometry, continuous_mechanics, diffusion/heat_transfer, network/traffic,
scheduling, supply_chain/operations, competition/game, decision_evaluation,
data_analysis
```
+ uncertainty 作为跨层属性维度（stochastic/deterministic）

> 注：审计报告建议的 10 标签方案（新增 continuous_mechanics, supply_chain/operations, optical/inverse，拆分 data/evaluation）**基本合理**，但本验证建议：(1) optical/inverse 移至 L2 更合适；(2) uncertainty 降级为属性维度；(3) 最终 L1 为 9 个结构标签 + 1 个属性维度。

---

## 2. L2 Taxonomy 验证

### 2.1 当前 L2 标签集

```
state transition, conservation law, flow balance, distance/geometry,
resource constraint, queue, spatial-temporal field, interaction/game
```

### 2.2 逐标签验证

#### 2.2.1 state transition — **SPLIT（拆分为 temporal_recurrence + decision_state_transition）**

| 项目 | 内容 |
|---|---|
| **决策** | SPLIT |
| **证据** | 当前 state transition 被 ARIMA/GM(1,1)/LSTM（时序递推）和 MDP/DP（决策状态转移）共用，但两者有本质区别：(1) 时序递推是**自治系统** x_{t+1}=f(x_t)，无决策变量；(2) MDP 是**决策系统** x_{t+1}=f(x_t, a_t)，状态转移依赖行动选择。2020_B 的核心是 MDP 决策状态转移，而 16 张方法卡中 state_transition 仅被时序卡(ARIMA/GM/LSTM)使用，完全不覆盖 MDP 语境。 |
| **来源** | 方法卡 modeling_patterns 字段 + CUMCM-Bench-v2 2020_B allowed_model_families: MDP |
| **置信度** | HIGH |
| **理由** | 拆分后：temporal_recurrence 覆盖时序预测（ARIMA/GM/LSTM/差分方程），decision_state_transition 覆盖 MDP/DP/随机动态规划。两者的验证方法不同（时序用回测，MDP 用策略收敛/值迭代），失败模式也不同（时序过拟合 vs MDP 状态空间爆炸）。 |

#### 2.2.2 conservation law — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 2018_A(能量守恒→热传导PDE), 2016_A(力平衡/力矩守恒), 2019_A(动量守恒)。守恒律是连续物理建模的第一性原理，从守恒律出发推导控制方程是标准建模路径。CUMCM-HMML 方法节点1.1.3"能量/守恒律模型"明确标注。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML 1.1.3 + card.yaml 2018_A key_constraints |
| **置信度** | HIGH |
| **理由** | 守恒律具有明确的物理地位（能量/质量/动量守恒是物理学基本定律），是从问题到 PDE/ODE 的关键建模桥梁。与 flow_balance 的边界：conservation law 是**连续介质**的物理守恒原理（积分形式→微分形式），flow balance 是**离散节点**的流量会计（入流=出流+累积）。 |

#### 2.2.3 flow balance — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 2019_C(出租车流量平衡), 2016_B(路网通行能力), 2025_D(水管网络流量)。流量平衡是网络/交通问题的核心建模模式。 |
| **来源** | CUMCM-Bench-v2 + card.yaml 2019_C key_constraints: "排队平衡约束（流量守恒）" |
| **置信度** | HIGH |
| **理由** | flow balance 的数学形式是节点流量守恒方程（Σ入流=Σ出流+节点变化率），是图论/网络流的基础。与 conservation law 的边界清晰：conservation law → 连续场(PDE)，flow balance → 离散网络(代数方程/图)。 |

#### 2.2.4 distance/geometry — **REVISE（重命名为 geometric_constraint，扩展语义）**

| 项目 | 内容 |
|---|---|
| **决策** | REVISE — 重命名 + 扩展 |
| **证据** | 当前 distance/geometry 仅被 TOPSIS（距离理想点）使用，但 2024_A 的核心建模模式是几何约束（螺线参数化、把手间距守恒、碰撞检测=距离约束），2015_A 是球面三角距离，2017_A 是投影几何。这些都属于"距离/几何约束"模式，但当前标签语义被 TOPSIS 窄化了。 |
| **来源** | 方法卡 mc-topsis modeling_patterns: [distance] + card.yaml 2024_A key_constraints |
| **置信度** | HIGH |
| **理由** | 重命名为 geometric_constraint 后，涵盖：(1) 空间距离/轨迹约束（运动学、碰撞检测）；(2) 几何投影/变换（CT标定、定位）；(3) 评价空间中的距离度量（TOPSIS）。这是一个稳定的建模模式：通过定义距离/几何约束来构建模型。 |

#### 2.2.5 resource constraint — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 2020_B(水/食物/资金约束), 2018_B(工序/时间约束), 2021_C(产能/库存约束), 2024_C(生产资源约束)。资源约束是调度/优化问题的核心建模模式。CUMCM-HMML 领域10"运筹与调度"的核心。 |
| **来源** | CUMCM-Bench-v2 + card.yaml 2020_B key_constraints + CUMCM-HMML 领域10 |
| **置信度** | HIGH |
| **理由** | resource constraint 是将实际问题转化为数学规划的关键步骤：识别有限资源（时间/预算/容量/负重）并表达为不等式约束。这是一个稳定、可区分的建模模式。 |

#### 2.2.6 queue — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 2019_C(出租车排队)是国赛中最典型的排队论问题。排队论在数学建模中有独立的理论体系（Kendall记号、Little定理、M/M/c模型）。高教社教材设"排队论"独立章节。CUMCM-HMML 设子领域5.3"排队论"。 |
| **来源** | CUMCM-Bench-v2 2019_C + 高教社教材 + CUMCM-HMML 5.3 |
| **置信度** | HIGH |
| **理由** | 排队模式具有独特的到达-服务-等待结构，与一般的 flow balance 不同：queue 关注随机过程下的等待时间/队列长度分布，flow balance 关注确定性流量守恒。 |

#### 2.2.7 spatial-temporal field — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 2018_A(温度场 T(x,t)), 2020_A(回流焊温度场)。时空场是 PDE 建模的核心对象：未知量是空间和时间的函数 u(x,t)。CUMCM-HMML 子领域1.2"偏微分方程与场问题"。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML 1.2 + card.yaml 2018_A key_variables: temperature(时空分布) |
| **置信度** | HIGH |
| **理由** | spatial-temporal field 是区分 PDE 问题与 ODE/代数问题的关键：如果未知量是场函数（空间+时间分布），则需要 PDE 表述；如果仅是时间函数，则是 ODE。这是一个稳定的建模模式分类。 |

#### 2.2.8 interaction/game — **KEEP（重命名为 interaction_game）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 2020_B(多玩家博弈), 2019_C(司机-乘客双边匹配), 2025_D(网络博弈)。交互/博弈模式的核心是多决策者的策略互动。CUMCM-HMML 子领域6.3"博弈论"。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML 6.3 |
| **置信度** | HIGH |
| **理由** | interaction_game 是区分单决策者优化与多决策者博弈的关键建模模式。其核心分析工具是纳什均衡/最优响应，与单目标优化有本质区别。 |

### 2.3 新增标签验证

#### 2.3.1 statistical_association — **ADD（HIGH confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD |
| **证据** | 36 题中大量数据驱动问题的核心建模模式是统计关联：2016_C(电池放电曲线回归), 2017_B(定价因素回归), 2017_C(颜色-浓度标定), 2022_C(玻璃成分聚类/判别), 2023_C(销量预测), 2025_C(混合效应模型), 2025_E(运动数据相关分析)。这些问题的 L1 是 data_analysis，但当前 L2 没有对应标签——它们既不是 state transition（非时序递推），也不是 conservation law（无物理机理）。 |
| **来源** | CUMCM-Bench-v2 allowed_model_families: regression(7次), statistical_analysis(8次), classification(4次), clustering(3次) + 中国大学MOOC"一元统计模型""多元统计分析模型" |
| **置信度** | HIGH |
| **理由** | statistical_association 是数据驱动建模的核心模式：通过统计方法（回归/分类/聚类/相关/降维）发现变量间的关联关系。这是与机理驱动建模（conservation law/flow balance）并列的两大建模范式之一。当前 L2 完全缺失此标签，导致所有 data_analysis 题在 L2 层无家可归。 |

#### 2.3.2 inverse_problem — **ADD（HIGH confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD |
| **证据** | 36 题中 5 题涉及反问题：2015_A(经纬度反演), 2017_A(CT图像重建), 2018_A(热参数反演), 2022_B(定位反演), 2025_B(厚度反演)。反问题的核心模式是"已知观测输出，反求输入/参数/初始条件"，与正问题"已知输入求输出"的建模方向相反。CUMCM-Bench-v2 allowed_model_families 中 inverse_problem 出现 5 次。 |
| **来源** | CUMCM-Bench-v2 allowed_model_families + card.yaml 2018_A sub_questions Q2: parameter_inversion |
| **置信度** | HIGH |
| **理由** | 反问题具有独特的建模特征：(1) 通常不适定(ill-posed)，需要正则化；(2) 目标函数是观测值与模拟值的残差最小化；(3) 验证需要扰动稳定性分析。这是一个稳定、可区分的建模模式，应放在 L2（而非 L1，因为它通常与其他 L1 标签共存）。 |

### 2.4 L2 验证总结

| 原标签 | 决策 | 新标签 |
|---|---|---|
| state transition | SPLIT | temporal_recurrence, decision_state_transition |
| conservation law | KEEP | conservation_law |
| flow balance | KEEP | flow_balance |
| distance/geometry | REVISE | geometric_constraint |
| resource constraint | KEEP | resource_constraint |
| queue | KEEP | queue |
| spatial-temporal field | KEEP | spatial_temporal_field |
| interaction/game | KEEP | interaction_game |
| — | ADD | statistical_association |
| — | ADD | inverse_problem |

**建议 L2 标签集（10 个）**：
```
temporal_recurrence, decision_state_transition, conservation_law, flow_balance,
geometric_constraint, resource_constraint, queue, spatial_temporal_field,
interaction_game, statistical_association, inverse_problem
```
= 11 个（拆分 state transition 增加 1 个，新增 2 个，原 8 个 → 8-1+2+2=11）

> 审计报告建议新增 statistical_association 和 inverse_problem，**完全合理且必要**。本验证额外建议拆分 state_transition。

---

## 3. L3 Taxonomy 验证

### 3.1 当前 L3 标签集

```
optimization, differential equation, graph, probability, statistics, linear algebra
```

### 3.2 逐标签验证

#### 3.2.1 optimization — **KEEP（不拆分，子类型留 L4）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP，不拆分 |
| **证据** | 36 题 allowed_model_families 中 optimization 出现 39 次（最高频），涵盖线性规划、整数规划、非线性规划、多目标优化、组合优化。CUMCM-HMML 设"优化理论与方法"独立领域，含5个子领域。高教社教材设"线性规划""整数规划""非线性规划""多目标决策分析"独立章节。 |
| **来源** | CUMCM-Bench-v2 统计 + CUMCM-HMML 领域2 + 高教社教材 |
| **置信度** | HIGH |
| **理由** | L3 是"数学表述形式"层，optimization 作为统一表述形式（min f(x) s.t. g(x)≤0）是稳定的。LP/IP/NLP/MOP 的区别在于约束和变量类型，属于 L4 solver 层的精确求解器分类。在 L3 拆分 optimization 会导致标签爆炸（LP/IP/NLP/MIP/SOCP/SDP...），且这些子类型共享同一数学框架。 |

#### 3.2.2 differential equation — **SPLIT（拆分为 ODE + PDE）**

| 项目 | 内容 |
|---|---|
| **决策** | SPLIT |
| **证据** | 36 题中 differential_equations 出现 11 次，但内部 ODE/PDE 分明：ODE 用于 2016_A(锚链静力学→代数方程/ODE), 2019_A(振动ODE), 2022_A(振动ODE), 2024_A(运动学ODE)；PDE 用于 2018_A(热传导PDE), 2020_A(热传导PDE), 2025_D(Saint-Venant方程PDE)。CUMCM-HMML 将"常微分方程建模"(1.1)和"偏微分方程与场问题"(1.2)分为两个子领域。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML 1.1 vs 1.2 + methodology/ode-pde.md 决策树 |
| **置信度** | HIGH |
| **理由** | ODE 和 PDE 的数学性质、求解方法、验证方式完全不同：(1) ODE 是单变量（通常是时间）的微分方程，PDE 是多变量（空间+时间）的；(2) ODE 求解用 RK4/odeint，PDE 求解用有限差分/有限元；(3) ODE 的验证是初值敏感性/平衡点稳定性，PDE 的验证是网格收敛性/边界条件正确性。methodology/ode-pde.md 的决策树第一步就是区分 ODE 和 PDE。 |

#### 3.2.3 graph — **KEEP（确认一级标签地位）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题中 graph_theory/network_analysis 出现 4 次：2016_B(路网), 2019_C(出租车网络), 2024_E(交通网络), 2025_D(水管网络)。2025_D 的 acceptable_solution_variants 明确包含 BFS/Dijkstra/A*。CUMCM-HMML 设"图论与网络"独立领域(领域4)。高教社教材设"图论与网络优化"独立章节。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML 领域4 + 高教社教材 + methodology/graph-theory.md |
| **置信度** | HIGH |
| **理由** | graph 是独立的数学表述形式：用顶点和边表示系统结构，用邻接矩阵/关联矩阵表示关系。与 optimization（目标函数+约束）、differential_equation（导数关系）、statistics（数据分布）有本质区别。当前 16 张方法卡中 graph 零覆盖是卡库的问题，不是标签的问题。 |

#### 3.2.4 probability — **KEEP（建议扩展为 probability_and_stochastic_process）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP，建议扩展语义 |
| **证据** | 36 题中 probability_modeling 出现 3 次(2019_C, 2020_B, 2024_B)，simulation 出现 8 次（多为概率仿真），game_theory 出现 2 次。排队论、马尔可夫链、蒙特卡洛都基于概率理论。CUMCM-HMML 设"概率建模与随机过程"独立领域(领域5)。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML 领域5 + methodology/stochastic-processes.md |
| **置信度** | HIGH |
| **理由** | probability 涵盖：概率分布、随机过程（马尔可夫链/泊松过程/布朗运动）、排队论、蒙特卡洛。当前标签名 probability 偏窄，建议扩展为 probability_and_stochastic_process，但在 L3 层保持单一标签即可（随机过程是概率的延伸）。 |

#### 3.2.5 statistics — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题中 statistical_analysis 出现 8 次，regression 出现 7 次，classification 出现 4 次，clustering 出现 3 次。16 张方法卡中 11 张涉及 statistics（覆盖率最高）。中国大学MOOC课程设"一元统计模型""多元统计分析模型"独立章节。 |
| **来源** | CUMCM-Bench-v2 + 方法卡统计 + 中国大学MOOC |
| **置信度** | HIGH |
| **理由** | statistics 是数据驱动建模的核心数学表述，涵盖回归、分类、聚类、假设检验、方差分析。与 probability 的边界：probability 关注随机过程的理论分布，statistics 关注从数据中估计和推断。 |

#### 3.2.6 linear algebra — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题中 linear_algebra 相关：geometric_modeling(8次，坐标变换/矩阵运算), signal_processing(1次), dimensionality_reduction(1次), numerical_methods(2次)。16 张方法卡中 5 张涉及 linear_algebra。PCA（特征值分解）、AHP（特征向量）、TOPSIS（向量运算）、KMeans（距离矩阵）都基于线性代数。 |
| **来源** | CUMCM-Bench-v2 + 方法卡统计 |
| **置信度** | HIGH |
| **理由** | linear algebra 是几何建模、降维、谱方法的数学基础。虽然它常作为工具出现在其他表述中，但作为独立的 L3 标签有其稳定地位（如纯几何问题的核心就是线性代数变换）。 |

### 3.3 新增标签验证

#### 3.3.1 stochastic_process — **UNCERTAIN（可合并入 probability）**

| 项目 | 内容 |
|---|---|
| **决策** | UNCERTAIN — 建议合并入 probability，不独立 |
| **证据** | 随机过程（马尔可夫链、排队论、布朗运动）是概率理论的延伸。CUMCM-HMML 将"概率建模与随机过程"放在同一领域。 |
| **来源** | CUMCM-HMML 领域5 |
| **置信度** | MEDIUM |
| **理由** | 在 L3 层，probability 和 stochastic_process 共享同一数学基础（测度论/概率空间），拆分意义不大。建议将 probability 标签语义扩展为 probability_and_stochastic_process。 |

#### 3.3.2 game_theoretic_formulation — **REJECT（归入 optimization + probability）**

| 项目 | 内容 |
|---|---|
| **决策** | REJECT — 不作为 L3 独立标签 |
| **证据** | 博弈论的数学表述本质上是多目标优化（每个玩家优化自己的目标）+ 概率（混合策略）。纳什均衡的求解可以转化为优化问题（如线性互补问题）。 |
| **来源** | 博弈论标准教材：博弈论=多目标优化+均衡分析 |
| **置信度** | MEDIUM |
| **理由** | 在 L3 层，game_theoretic 不是独立的数学表述形式，而是 optimization 的多玩家变体。博弈的独特性在 L2（interaction_game 建模模式），不在 L3。 |

#### 3.3.3 integer_programming / nonlinear_programming — **REJECT（归入 optimization，留 L4 区分）**

| 项目 | 内容 |
|---|---|
| **决策** | REJECT |
| **理由** | LP/IP/NLP 共享同一 optimization 框架（min f(x) s.t. constraints），区别在变量类型和约束性质，属于 L4 solver 层分类。在 L3 拆分会导致标签爆炸且语义重叠。 |

### 3.4 L3 验证总结

| 原标签 | 决策 | 新标签 | 36题覆盖 |
|---|---|---|---|
| optimization | KEEP | optimization | 39 |
| differential equation | SPLIT | ODE, PDE | 11 (ODE≈7, PDE≈4) |
| graph | KEEP | graph | 4 |
| probability | KEEP(扩展) | probability_and_stochastic | 15 |
| statistics | KEEP | statistics | 29 |
| linear algebra | KEEP | linear_algebra | 15 |

**建议 L3 标签集（7 个）**：
```
optimization, ODE, PDE, graph, probability_and_stochastic, statistics, linear_algebra
```

---

## 4. L4 Taxonomy 验证

### 4.1 当前 L4 标签集

```
numerical PDE, DP, Monte Carlo, GA, regression, clustering
```

### 4.2 逐标签验证

#### 4.2.1 numerical PDE — **KEEP（扩展为 numerical_PDE_and_FEM）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题 acceptable_solution_variants 中 finite_difference_method 出现 3 次，finite_element_method 出现 3 次，Saint_Venant_equations 1 次。2018_A 和 2020_A 的核心求解器是 PDE 数值解法。 |
| **来源** | CUMCM-Bench-v2 variants + methodology/ode-pde.md |
| **置信度** | HIGH |
| **理由** | numerical PDE 是独立的求解器类别（有限差分/有限元/有限体积），与 ODE 求解器（RK4）和通用优化器有本质区别。 |

#### 4.2.2 DP — **KEEP（扩展为 dynamic_programming_and_MDP）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题 variants 中 dynamic_programming 出现 1 次(2020_B)，markov_decision_process 出现 2 次(2019_C, 2020_B)。2020_B 的核心求解器是 DP/MDP。CUMCM-HMML 子领域2.3"动态规划与多阶段决策"。 |
| **来源** | CUMCM-Bench-v2 + CUMCM-HMML 2.3 + methodology/dynamic-programming.md |
| **置信度** | HIGH |
| **理由** | DP/MDP 是独立的求解范式（最优子结构+重叠子问题），与通用优化器和元启发式有本质区别。当前 16 张方法卡中 DP 零覆盖是卡库的问题。 |

#### 4.2.3 Monte Carlo — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题 variants 中 monte_carlo 出现 3 次，particle_filter 1 次。16 张方法卡中有 mc-monte-carlo。 |
| **来源** | CUMCM-Bench-v2 + 方法卡 mc-monte-carlo |
| **置信度** | HIGH |
| **理由** | 蒙特卡洛是基于随机抽样的数值计算方法，适用于不确定性传播、复杂系统仿真、高维积分。是独立的求解器类别。 |

#### 4.2.4 GA — **REVISE（扩展为 metaheuristic，含 GA/PSO/SA/DE/tabu）**

| 项目 | 内容 |
|---|---|
| **决策** | REVISE — GA → metaheuristic_optimization |
| **证据** | 36 题 variants 中 genetic_algorithm 出现 14 次（最高频求解器！），particle_swarm_optimization 1 次，tabu_search 1 次，NSGA_II 1 次。16 张方法卡中有 mc-ga, mc-pso, mc-sa 三张元启发式卡。当前 L4 只有 GA 标签，PSO/SA 无家可归。 |
| **来源** | CUMCM-Bench-v2 variants 统计 + 方法卡 mc-ga/mc-pso/mc-sa + methodology/genetic-algorithms.md + methodology/swarm-intelligence.md |
| **置信度** | HIGH |
| **理由** | GA、PSO、SA、DE、tabu search 共享同一求解范式：基于种群/邻域的随机搜索，不保证全局最优，需要多种子运行统计。将它们统一为 metaheuristic_optimization 标签，比单独列 GA 更合理。CUMCM-HMML 子领域2.5"组合优化与元启发式"也采用此分类。 |

#### 4.2.5 regression — **KEEP（扩展为 regression_and_supervised_learning）**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP，扩展语义 |
| **证据** | 36 题 variants 中 regression 类方法出现 30 次（最高频！）：linear_regression, nonlinear_regression, logistic_regression, random_forest, XGBoost, ARIMA, LSTM, least_squares, response_surface_method, mixed_effects_model 等。16 张方法卡中有 mc-ols, mc-arima, mc-grey-gm11, mc-lstm, mc-xgboost 五张回归/预测卡。 |
| **来源** | CUMCM-Bench-v2 variants 统计 + 方法卡统计 |
| **置信度** | HIGH |
| **理由** | regression 涵盖参数回归（OLS/Logistic）、非参数回归（树模型）、时序预测（ARIMA/LSTM）。这些方法共享"从数据中学习输入-输出映射"的求解范式。扩展为 regression_and_supervised_learning 更准确。 |

#### 4.2.6 clustering — **KEEP**

| 项目 | 内容 |
|---|---|
| **决策** | KEEP |
| **证据** | 36 题 variants 中 kmeans 出现 2 次，hierarchical_clustering 1 次。16 张方法卡中有 mc-kmeans。 |
| **来源** | CUMCM-Bench-v2 + 方法卡 mc-kmeans |
| **置信度** | HIGH |
| **理由** | 聚类是无监督学习的核心求解范式，与回归（有监督）有本质区别。 |

### 4.3 新增标签验证

#### 4.3.1 exact_optimizer — **ADD（HIGH confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD |
| **证据** | 36 题 variants 中 linear_programming 出现 2 次，integer_programming 出现 3 次，constrained_optimization 1 次，pricing_optimization 1 次，stochastic_optimization 1 次，coverage_optimization 1 次，signal_timing_optimization 1 次。这些是精确求解器（单纯形法/分支定界/内点法），与元启发式有本质区别。CUMCM-HMML 子领域2.1"线性与整数规划"、2.2"非线性规划"。 |
| **来源** | CUMCM-Bench-v2 variants + CUMCM-HMML 2.1/2.2 + methodology/optimization.md + methodology/integer-programming.md |
| **置信度** | HIGH |
| **理由** | exact_optimizer（LP/IP/NLP 精确求解器）与 metaheuristic 的区别是：前者保证最优解（在凸问题中），后者只给近似解。当前 L4 标签集完全缺失精确求解器类别，导致 2018_B(RGV调度→整数规划)、2021_C(供应链→LP/IP)等题在 L4 无对应标签。 |

#### 4.3.2 numerical_ODE — **ADD（HIGH confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD |
| **证据** | 36 题 variants 中 Runge_Kutta 出现 2 次，multi_body_dynamics 出现 2 次。2016_A(锚链)、2019_A(振动)、2022_A(振动)、2024_A(运动学)的核心求解器是 ODE 数值积分。当前 L4 有 numerical_PDE 但无 numerical_ODE，不对称。 |
| **来源** | CUMCM-Bench-v2 variants + methodology/ode-pde.md 决策树: ODE→Euler/RK4/odeint |
| **置信度** | HIGH |
| **理由** | ODE 求解器（RK4/Euler/odeint/打靶法）与 PDE 求解器（有限差分/有限元）是不同的数值方法族。L3 拆分 ODE/PDE 后，L4 必须对应拆分。 |

#### 4.3.3 simulation — **ADD（HIGH confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD |
| **证据** | 36 题 variants 中 simulation 类出现 9 次：discrete_event_simulation(3次), agent_based_simulation(2次), cellular_automata(1次), traffic_flow_model(1次), ray_tracing(1次)。CUMCM-HMML 领域8"仿真与数值方法"。methodology/simulation.md 设独立决策树。 |
| **来源** | CUMCM-Bench-v2 variants + CUMCM-HMML 领域8 + methodology/simulation.md + methodology/agent-based-simulation.md |
| **置信度** | HIGH |
| **理由** | simulation（离散事件仿真/多智能体仿真/元胞自动机）是独立的求解范式：通过时间步进模拟系统演化，不追求解析解。与 Monte Carlo（随机抽样计算）的区别：simulation 关注系统动态演化过程，Monte Carlo 关注随机抽样的统计估计。 |

#### 4.3.4 analytical_methods — **ADD（HIGH confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD |
| **证据** | 36 题 variants 中纯解析/闭式方法出现 24 次：spherical_trigonometry, static_equilibrium, Poincare_map, queuing_theory(闭式M/M/c), nash_equilibrium, triangulation, ANOVA, newsboy_model, bayesian_decision, Pearson_correlation, Radon_transform 等。AHP/TOPSIS/熵权（16张卡中的3张决策分析卡）也是闭式计算方法。 |
| **来源** | CUMCM-Bench-v2 variants 统计 + 方法卡 mc-ahp/mc-topsis/mc-entropy-weight |
| **置信度** | HIGH |
| **理由** | analytical_methods 涵盖：(1) 解析推导（静力平衡方程求解、球面三角）；(2) 闭式统计方法（M/M/c排队公式、ANOVA、相关系数）；(3) 决策分析方法（AHP/TOPSIS/熵权）。这些方法的共同特征是**有明确的计算公式/步骤，无需迭代搜索**。当前 L4 标签集完全缺失此类别。 |

#### 4.3.5 graph_algorithm — **ADD（MEDIUM confidence）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD |
| **证据** | 36 题 variants 中 BFS/Dijkstra/A* 出现在 2025_D（水管网络最短路径）。CUMCM-HMML 子领域4.1"最短路径与网络流"。methodology/graph-theory.md 和 graph-network-vrp.md 设独立决策树。 |
| **来源** | CUMCM-Bench-v2 2025_D variants + CUMCM-HMML 4.1 + methodology/graph-theory.md |
| **置信度** | MEDIUM |
| **理由** | 图算法（最短路/最大流/最小生成树）是独立的求解器类别。虽然国赛中纯图算法题不多（1/36），但网络/交通问题常涉及图算法。**建议作为 L4 标签保留**。 |

#### 4.3.6 dimensionality_reduction — **ADD（归入 L4）**

| 项目 | 内容 |
|---|---|
| **决策** | ADD — 归入 L4 |
| **证据** | 36 题 variants 中 PCA 出现 2 次(2022_C, 2025_E)，LDA 1 次(2022_C)。16 张方法卡中有 mc-pca。 |
| **来源** | CUMCM-Bench-v2 variants + 方法卡 mc-pca + methodology/dimensionality-reduction.md |
| **置信度** | HIGH |
| **理由** | PCA/LDA 是独立的数据变换算法（特征值分解/SVD），既不是回归（无监督），也不是聚类（不分组）。它在建模流程中通常是预处理步骤，但作为求解器类别有独立地位。**归入 L4**（而非 L3，因为它是具体算法而非数学表述形式）。 |

### 4.4 metaheuristic 归属问题（特别处理）

| 选项 | 分析 | 决策 |
|---|---|---|
| A. L4 一级标签 metaheuristic | GA/PSO/SA/DE/tabu 共享随机搜索范式，国赛高频(19/144 variants) | **采纳** |
| B. L4 子类（GA 的子类） | PSO/SA 与 GA 是并列关系，不是从属关系 | 拒绝 |
| C. 不属于 Solver 层 | 元启发式是求解算法，必须属于 L4 | 拒绝 |

**决策**：metaheuristic_optimization 作为 L4 一级标签，替代原 GA 标签。GA 是其子类。

### 4.5 analytical decision methods 归属问题（特别处理）

| 方法 | 分析 | 归属 |
|---|---|---|
| AHP | 闭式计算（特征向量法），无迭代搜索 | L4 analytical_methods |
| TOPSIS | 闭式计算（距离公式+排序），无迭代搜索 | L4 analytical_methods |
| 熵权法 | 闭式计算（熵公式+归一化），无迭代搜索 | L4 analytical_methods |

**决策**：AHP/TOPSIS/熵权归入 L4 analytical_methods 标签。它们不是 L3（数学表述是 linear_algebra/statistics），也不是独立的 L4 标签（合并为 analytical_methods 避免标签爆炸）。

### 4.6 L4 验证总结

| 原标签 | 决策 | 新标签 | 36题variants覆盖 |
|---|---|---|---|
| numerical PDE | KEEP | numerical_PDE | 8 |
| DP | KEEP | DP_and_MDP | 3 |
| Monte Carlo | KEEP | monte_carlo | 6 |
| GA | REVISE | metaheuristic_optimization | 19 |
| regression | KEEP(扩展) | regression_and_supervised | 30 |
| clustering | KEEP | clustering | 4 |
| — | ADD | exact_optimizer | 12 |
| — | ADD | numerical_ODE | 4 |
| — | ADD | simulation | 9 |
| — | ADD | analytical_methods | 24+5(决策)=29 |
| — | ADD | graph_algorithm | 3 |
| — | ADD | dimensionality_reduction | 3 |

**建议 L4 标签集（11 个）**：
```
numerical_PDE, numerical_ODE, DP_and_MDP, monte_carlo, metaheuristic_optimization,
exact_optimizer, regression_and_supervised, clustering, dimensionality_reduction,
simulation, analytical_methods, graph_algorithm
```
= 12 个

> **防标签爆炸机制**：L4 标签按"求解范式"分组，不按具体算法命名。每个标签下可含多种具体算法（如 metaheuristic 含 GA/PSO/SA/DE），具体算法在方法卡层面区分。

---

## 5. 跨来源比较

### 5.1 不同分类体系对比

| 分类体系 | 分类维度 | 核心类别 | 与四层 taxonomy 的对应 |
|---|---|---|---|
| **高教社《数学建模方法及其应用》** | 按方法类型 | 几何分析、微分方程、差分方程、插值拟合、概率分布、随机模拟、统计分析、综合评价、线性/整数/非线性规划、图论网络、排队论、对策论、决策分析、模糊数学、灰色系统 | 混合了 L2/L3/L4：微分方程=L3，排队论=L4，综合评价=L1+L4 |
| **中国大学MOOC课程** | 按模型类型 | 微分方程模型、优化模型(LP/NLP/MOP/DP)、一元统计模型、多元统计分析模型 | 主要对应 L3，DP 被归入优化模型 |
| **"四大模型"流行分类** | 按建模目标 | 优化、分类、评价、预测 | 对应 L1 的粗粒度分类：optimization→scheduling/competition，classification/clustering→data_analysis，evaluation→decision_evaluation，prediction→data_analysis |
| **CUMCM-HMML (12领域)** | 领域→子领域→方法 | 微分方程、优化、数据科学、图论网络、概率随机、评价决策、机理建模、仿真数值、灰色模糊、运筹调度、预测、交叉新兴 | 混合了 L1(机理建模/运筹调度)和 L3(微分方程/优化/图论)，是领域分类而非层分类 |
| **MCM/ICM 官方** | 按题目类型 | A连续, B离散, C数据洞察, D运筹/网络, E环境, F政策 | 对应 L1 的粗粒度：A→motion/geometry+continuous_mechanics+diffusion，B→scheduling+competition/game，C→data_analysis，D→network/traffic+supply_chain |
| **Wiley 教材分类** | 按模型属性 | deterministic/stochastic, continuous/discrete, static/dynamic, linear/nonlinear, phenomenological/mechanistic, stationary/instationary, distributed/lumped | 这是**属性维度**，与 L1 Problem Structure 正交。uncertainty 应在此处而非 L1 |
| **俄罗斯教材分类** | 按模型用途 | 几何模型、连续模型(ODE/PDE)、优化模型(静态/动态)、概率模型 | 对应 L3 为主 |

### 5.2 分类一致性分析

**一致点**：
1. 所有体系都将**优化**作为核心类别（L3 optimization）
2. 所有体系都将**微分方程**作为核心类别（L3 ODE/PDE）
3. 所有体系都将**统计/数据**作为核心类别（L3 statistics + L1 data_analysis）
4. 排队论、博弈论、图论在多个体系中独立出现

**不一致点**：
1. **L1 vs L3 混淆**：多数教材/课程将"微分方程模型"和"优化模型"并列，但前者是 L3（数学表述），后者既是 L3 也是 L1（问题结构）。四层 taxonomy 的贡献是将"问题是什么"(L1)和"用什么数学"(L3)分离。
2. **DP 的位置**：MOOC 课程将 DP 归入"优化模型"，CUMCM-HMML 将 DP 归入"优化理论"子领域2.3，四层 taxonomy 将 DP 放在 L4（求解器）。这是视角不同：DP 既是建模框架(MDP)也是求解算法。
3. **评价/决策的位置**：高教社将"综合评价"和"决策分析"分为两个方法类别，"四大模型"将"评价"作为独立模型类型。四层 taxonomy 将 decision_evaluation 放在 L1（问题结构），analytical_methods 放在 L4（求解器）。
4. **uncertainty 的位置**：Wiley 教材明确将 deterministic/stochastic 作为模型属性维度，与 problem structure 正交。这支持本验证将 uncertainty 从 L1 降级的决策。

### 5.3 分类争议

| 争议点 | 立场A | 立场B | 本验证立场 |
|---|---|---|---|
| DP 属于 L3 还是 L4 | L3（动态规划是数学表述形式） | L4（DP是求解算法） | **L4**，但 MDP 的建模部分在 L2(decision_state_transition) |
| 博弈论是否独立 L3 | 是（多目标优化+均衡是独特表述） | 否（本质是多目标优化） | **否**，博弈的独特性在 L2(interaction_game) |
| ODE/PDE 是否拆分 L3 | 否（都是微分方程） | 是（求解方法完全不同） | **是**，L3 拆分后 L4 对应拆分 |
| metaheuristic 是否 L4 一级 | 是（独立求解范式） | 否（只是优化的子类） | **是**，与 exact_optimizer 并列 |
| uncertainty 是否 L1 | 是（随机问题是独立类型） | 否（是所有问题的属性） | **否**，降级为跨层属性 |

---

## 6. Benchmark 映射表

### 6.1 5 道题四层映射

| 题目 | L1 Problem Structure | L2 Modeling Pattern | L3 Formulation | L4 Solver | candidate method card |
|---|---|---|---|---|---|
| **2024_A** 板凳龙 | motion/geometry | geometric_constraint, temporal_recurrence | ODE, linear_algebra, optimization | numerical_ODE, analytical_methods, exact_optimizer | **无对应卡**（需新增 kinematics/geometric_modeling 卡） |
| **2020_B** 穿越沙漠 | scheduling, competition/game | decision_state_transition, resource_constraint, interaction_game | optimization, probability_and_stochastic | DP_and_MDP, monte_carlo, analytical_methods | mc-monte-carlo(部分), **缺 mc-dp, mc-game-theory** |
| **2018_A** 高温服装 | diffusion/heat_transfer | spatial_temporal_field, conservation_law, inverse_problem | PDE, optimization | numerical_PDE, exact_optimizer, monte_carlo | mc-ga(仅优化部分), **缺 mc-pde, mc-finite-difference** |
| **2019_C** 机场出租 | network/traffic, decision_evaluation | queue, flow_balance, interaction_game | optimization, probability_and_stochastic, statistics | analytical_methods, monte_carlo, simulation, exact_optimizer | mc-monte-carlo, mc-ahp, mc-ga(浅层命中), **缺 mc-queuing-theory** |
| **2022_C** 古代玻璃 | data_analysis, decision_evaluation | statistical_association | statistics, linear_algebra | regression_and_supervised, clustering, dimensionality_reduction | mc-kmeans, mc-ols, mc-xgboost, mc-pca, mc-topsis(完整覆盖) |

### 6.2 5 题映射详细说明

#### 2024_A（板凳龙闹元宵）

- **L1**：motion/geometry。核心是多体运动学+几何螺线参数化。
- **L2**：geometric_constraint（螺线方程、把手间距守恒、碰撞检测=距离约束）、temporal_recurrence（位置/速度随时间递推）。
- **L3**：ODE（运动学方程）、linear_algebra（坐标变换、螺线参数化）、optimization（Q3最小螺距、Q4轨迹优化、Q5速度优化）。
- **L4**：numerical_ODE（多体递推积分）、analytical_methods（螺线几何解析）、exact_optimizer（约束优化）。
- **candidate card**：当前 16 卡中**无任何卡覆盖 motion/geometry + geometric_constraint**。mc-monte-carlo 被 LLM 误选（因为"仿真"语义接近），但 family=uncertainty_propagation 与 kinematics 无匹配。

#### 2020_B（穿越沙漠）

- **L1**：scheduling（行走计划/资源分配）、competition/game（Q3多玩家博弈）。
- **L2**：decision_state_transition（MDP：天气状态→行动决策→状态转移）、resource_constraint（水/食物/资金消耗）、interaction_game（Q3多玩家策略互动）。
- **L3**：optimization（收益最大化）、probability_and_stochastic（天气随机、MDP转移概率）。
- **L4**：DP_and_MDP（值迭代/策略迭代）、monte_carlo（天气随机模拟）、analytical_methods（纳什均衡计算）。
- **candidate card**：mc-monte-carlo 可覆盖 Q2（随机模拟），但**缺 mc-dp（核心求解器）和 mc-game-theory（Q3）**。mc-ga 被 LLM 误选（通用优化器替代 DP）。

#### 2018_A（高温作业服装）

- **L1**：diffusion/heat_transfer（多层织物热传导）。
- **L2**：spatial_temporal_field（温度场 T(x,t)）、conservation_law（能量守恒→热传导方程）、inverse_problem（Q2热参数反演）。
- **L3**：PDE（热传导方程 ∂T/∂t=α∂²T/∂x²）、optimization（Q3设计优化、Q2反演目标函数）。
- **L4**：numerical_PDE（有限差分法）、exact_optimizer（Levenberg-Marquardt反演、GA优化）。
- **candidate card**：mc-ga 可覆盖 Q3 优化部分，但**缺 mc-pde / mc-finite-difference（核心求解器）**。LLM 选 mc-ga 是因为 optimization 部分有匹配，但完全错过了 PDE 核心。

#### 2019_C（机场出租车）

- **L1**：network/traffic（出租车-乘客网络）、decision_evaluation（司机决策、调度策略）。
- **L2**：queue（乘客到达/出租车服务排队）、flow_balance（流量守恒）、interaction_game（司机-乘客双边匹配）。
- **L3**：optimization（调度优化）、probability_and_stochastic（到达率/服务率随机）、statistics（数据分析）。
- **L4**：analytical_methods（M/M/c排队公式）、monte_carlo（随机仿真）、simulation（离散事件仿真）、exact_optimizer（调度优化）。
- **candidate card**：mc-monte-carlo（仿真）、mc-ahp（决策）、mc-ga（优化）可在 solver 层面匹配。**但缺 mc-queuing-theory（核心建模工具）**。这是浅层命中的典型：L4 有匹配，但 L1/L2 完全缺失。

#### 2022_C（古代玻璃）

- **L1**：data_analysis（成分数据分析）、decision_evaluation（风化分类/评价）。
- **L2**：statistical_association（成分-风化关联、聚类结构）。
- **L3**：statistics（聚类/判别/假设检验）、linear_algebra（PCA降维）。
- **L4**：regression_and_supervised（LDA/随机森林判别）、clustering（KMeans）、dimensionality_reduction（PCA）。
- **candidate card**：mc-kmeans、mc-ols、mc-xgboost、mc-pca、mc-topsis **完整覆盖**。这是当前卡库的"舒适区"。

### 6.3 36 题 L1 分布统计

| L1 标签 | 题目数 | 占比 | 题目列表 |
|---|---|---|---|
| data_analysis | 11 | 30.6% | 2015_B, 2016_C, 2017_B, 2017_C, 2018_C, 2020_C, 2021_B, 2022_C, 2023_C, 2025_C, 2025_E |
| decision_evaluation | 9 | 25.0% | 2015_B, 2017_B, 2018_C, 2019_C, 2020_C, 2022_C, 2023_C, 2024_C, 2025_C |
| motion/geometry | 8 | 22.2% | 2015_A, 2017_A, 2021_A, 2022_B, 2023_A, 2023_B, 2024_A, 2025_A |
| scheduling | 5 | 13.9% | 2018_B, 2019_B, 2020_B, 2021_C, 2024_B |
| continuous_mechanics | 4 | 11.1% | 2016_A, 2019_A, 2019_B, 2022_A |
| network/traffic | 4 | 11.1% | 2016_B, 2019_C, 2024_E, 2025_D |
| diffusion/heat_transfer | 2 | 5.6% | 2018_A, 2020_A |
| optical/inverse (L2) | 3+2 | — | 2015_A, 2017_A, 2018_A, 2022_B, 2025_B |
| competition/game | 2 | 5.6% | 2020_B, 2025_D |
| supply_chain/operations | 2 | 5.6% | 2021_C, 2024_C |

> 注：多标签计数，总和超过 36。data_analysis + decision_evaluation 合计约 50%，反映国赛 C 题占比高。motion/geometry + continuous_mechanics + diffusion 合计约 39%，反映 A 题的物理/机理建模占比。

### 6.4 36 题 L4 求解器分布（从 acceptable_solution_variants，共 144 个变体）

| L4 标签 | 变体数 | 占比 | 典型方法 |
|---|---|---|---|
| regression_and_supervised | 30 | 20.8% | OLS, Logistic, RF, XGBoost, ARIMA, LSTM, RSM, mixed-effects |
| analytical_methods | 29 | 20.1% | AHP, TOPSIS, 熵权, M/M/c, Nash均衡, ANOVA, 球面三角, 静力平衡 |
| metaheuristic_optimization | 19 | 13.2% | GA, PSO, SA, tabu, NSGA-II |
| exact_optimizer | 12 | 8.3% | LP, IP, 约束优化, 随机优化 |
| numerical_solver | 9 | 6.3% | Newton, L-M, 梯度下降, 迭代重建 |
| simulation | 9 | 6.3% | DES, ABM, 元胞自动机, 交通流模型, 光线追踪 |
| numerical_PDE | 8 | 5.6% | 有限差分, 有限元, Saint-Venant |
| monte_carlo | 6 | 4.2% | MC模拟, 粒子滤波 |
| clustering | 4 | 2.8% | KMeans, 层次聚类 |
| numerical_ODE | 4 | 2.8% | RK4, 多体动力学 |
| DP_and_MDP | 3 | 2.1% | DP, MDP |
| dimensionality_reduction | 3 | 2.1% | PCA, LDA |
| graph_algorithm | 3 | 2.1% | BFS, Dijkstra, A* |

> 关键发现：当前 L4 标签集（numerical PDE, DP, Monte Carlo, GA, regression, clustering）仅覆盖 144 变体中的约 40%。analytical_methods(20.1%)、exact_optimizer(8.3%)、simulation(6.3%)、numerical_ODE(2.8%)、dimensionality_reduction(2.1%)、graph_algorithm(2.1%) 完全缺失。

---

## 7. method_selection=0 归因分析

### 7.1 2024_A — L1 motion/geometry 零覆盖导致级联失效

| 层 | 该题需要 | 补充后 taxonomy 是否覆盖 | 原 taxonomy 是否覆盖 |
|---|---|---|---|
| L1 | motion/geometry | ✓（KEEP） | ✗（标签存在但 0 卡覆盖） |
| L2 | geometric_constraint, temporal_recurrence | ✓（geometric_constraint 重命名扩展，temporal_recurrence 拆分获得） | ✗（distance/geometry 被 TOPSIS 窄化，state_transition 仅时序语境） |
| L3 | ODE, linear_algebra, optimization | ✓（ODE 拆分后明确） | △（differential equation 未拆分，grey DE 弱覆盖） |
| L4 | numerical_ODE, analytical_methods | ✓（新增 numerical_ODE, analytical_methods） | ✗（numerical PDE 不适用，无 numerical ODE） |

**归因结论**：2024_A 的 method_selection=0 **完全可以通过补充 L1/L2 知识结构得到解释**。根本原因是 L1 motion/geometry 标签虽存在但无任何方法卡覆盖，导致 LLM 无法从问题结构层面识别"这是运动学/几何问题"。L2 geometric_constraint 的语义窄化（仅 TOPSIS 使用）进一步加剧了路由失败。补充 L2 geometric_constraint（扩展到运动学/碰撞检测）和 L4 numerical_ODE 后，该题的知识路径完整闭合。

### 7.2 2020_B — L2 决策状态转移 + L4 DP 双重缺失

| 层 | 该题需要 | 补充后 taxonomy 是否覆盖 | 原 taxonomy 是否覆盖 |
|---|---|---|---|
| L1 | scheduling, competition/game | ✓（KEEP） | △（标签存在但 0 卡覆盖 scheduling/competition） |
| L2 | decision_state_transition, resource_constraint, interaction_game | ✓（拆分 state_transition 获得 decision_state_transition） | ✗（state_transition 仅时序语境，无 MDP 决策语境；resource_constraint/interaction_game 0 卡覆盖） |
| L3 | optimization, probability | ✓（KEEP） | ✓ |
| L4 | DP_and_MDP, monte_carlo, analytical_methods | ✓（DP KEEP，新增 analytical_methods） | △（DP 标签存在但 0 卡覆盖；monte_carlo 有卡） |

**归因结论**：2020_B 的 method_selection=0 **完全可以通过补充 L2/L4 得到解释**。最关键的缺失是 L2 decision_state_transition——原 state_transition 标签仅被时序预测卡(ARIMA/GM/LSTM)使用，完全不覆盖 MDP 决策语境。LLM 无法识别"这是一个序贯决策问题"，因此无法激活 DP 求解路径。补充 L2 拆分后，MDP 语境的 state transition 有了独立标签，LLM 可以从"天气状态→行动→资源消耗→收益"的决策链识别问题类型。

### 7.3 2018_A — L1+L2+L4 三层联动缺失

| 层 | 该题需要 | 补充后 taxonomy 是否覆盖 | 原 taxonomy 是否覆盖 |
|---|---|---|---|
| L1 | diffusion/heat_transfer | ✓（KEEP） | ✗（标签存在但 0 卡覆盖） |
| L2 | spatial_temporal_field, conservation_law, inverse_problem | ✓（新增 inverse_problem） | ✗（三个标签均 0 卡覆盖） |
| L3 | PDE, optimization | ✓（PDE 拆分后明确） | △（differential equation 未拆分，grey DE 弱覆盖） |
| L4 | numerical_PDE, exact_optimizer | ✓（numerical_PDE KEEP，新增 exact_optimizer） | △（numerical PDE 标签存在但 0 卡覆盖） |

**归因结论**：2018_A 是 5 题中缺失最严重的，**完全可以通过补充 L1/L2/L4 得到解释**。三层联动缺失：L1 diffusion 零覆盖→LLM 无法识别"热传导问题"；L2 spatial_temporal_field + conservation_law 零覆盖→LLM 无法建立"能量守恒→PDE"的建模路径；L4 numerical_PDE 零覆盖→即使建立了 PDE 也无对应求解器卡。补充 L2 inverse_problem 后，Q2（参数反演）也有了明确的建模模式标签。

### 7.4 三题归因总结

| 题目 | 最根本缺失层 | 补充后是否可解释 | 解释程度 |
|---|---|---|---|
| 2024_A | L1 motion/geometry (0卡) + L2 geometric_constraint (语义窄化) | **是** | 完全解释 |
| 2020_B | L2 decision_state_transition (无独立标签) + L4 DP (0卡) | **是** | 完全解释 |
| 2018_A | L1 diffusion (0卡) + L2 三标签 (0卡) + L4 numerical_PDE (0卡) | **是** | 完全解释 |

**核心结论**：三题 method_selection=0 的根本原因**不是"LLM 选错卡"，而是"知识架构在 L1/L2 层没有对应标签/覆盖，导致 LLM 无法从问题结构层面正确路由"**。补充后的 taxonomy 为三题提供了完整的 L1→L2→L3→L4 知识路径。

---

## 8. 2019_C 浅层命中/假阳性检查

### 8.1 命中分析

| 层 | 2019_C 需要 | 当前卡库覆盖 | 命中质量 |
|---|---|---|---|
| L1 | network/traffic, decision_evaluation | network/traffic **0卡**，decision 5卡 | 部分缺失 |
| L2 | queue, flow_balance, interaction_game | **全部 0 卡** | 完全缺失 |
| L3 | optimization, probability, statistics | optimization 5卡, probability 4卡, statistics 11卡 | 完整覆盖 |
| L4 | queuing, optimization, monte_carlo, decision | monte_carlo 1卡, optimization(GA) 2卡, decision(AHP) 1卡, queuing **0卡** | 部分覆盖 |

### 8.2 假阳性判定

**判定：2019_C 的 method_selection=100 是浅层命中/假阳性。**

证据链：
1. L1 network/traffic 零覆盖——LLM 未识别"这是交通/网络问题"
2. L2 queue/flow_balance/interaction_game 全部零覆盖——LLM 未建立排队论/流量平衡/博弈的建模路径
3. L3 optimization/probability/statistics 完整覆盖——这是"通用数学层"，几乎所有问题都能匹配
4. L4 monte_carlo/GA/AHP 碰巧匹配——这些是通用求解器，可用于多种问题
5. **核心缺失**：无 queuing_theory 卡。mc-monte-carlo 只是"用仿真近似排队"，不是真正的排队论建模（M/M/c 公式、Little定理、到达/服务过程建模）

### 8.3 假阳性的指标根源

当前 e2e_metrics 的 method_selection 仅检查 **L4 card family 是否匹配 benchmark core_methods**，完全不检查 L1-L3 层。这意味着：
- L1 识别错误（将交通问题判为通用决策）→ 不扣分
- L2 建模模式错误（无排队论建模）→ 不扣分
- L3 数学表述正确 → 加分
- L4 求解器碰巧匹配 → 得满分

**改进方向**：method_selection 应升级为四层语义对齐评分，检测"L4 命中但 L1/L2 错误"的浅层命中。

---

## 9. Non-overfitting 评估

### 9.1 新增标签是否只为当前 5 道题？

| 新增/修改标签 | 5题中使用 | 36题中使用 | 更广泛领域适用性 | overfitting 判定 |
|---|---|---|---|---|
| continuous_mechanics (L1) | 0/5 | 4/36 | 力学/振动/变形是数学建模经典领域，教材独立章节 | **否** |
| supply_chain/operations (L1) | 0/5 | 2/36 | 运筹学核心领域，MCM/ICM D题专门覆盖 | **否** |
| decision_state_transition (L2) | 1/5 (2020_B) | MDP/DP在调度/博弈中高频 | 马尔可夫决策过程是独立理论体系 | **否** |
| statistical_association (L2) | 1/5 (2022_C) | 11/36 数据分析题 | 统计建模是两大建模范式之一 | **否** |
| inverse_problem (L2) | 1/5 (2018_A) | 5/36 | 反问题是数学物理独立分支（不适定性+正则化） | **否** |
| geometric_constraint (L2 重命名) | 1/5 (2024_A) | 8/36 几何题 | 几何约束是运动学/机器人/CAD的核心 | **否** |
| ODE/PDE 拆分 (L3) | 3/5 | 11/36 | ODE/PDE是微分方程的基本分类 | **否** |
| metaheuristic (L4) | 0/5 直接 | 19/144 variants | 元启发式是优化的独立范式 | **否** |
| exact_optimizer (L4) | 1/5 (2018_A优化) | 12/144 variants | LP/IP是运筹学核心 | **否** |
| numerical_ODE (L4) | 1/5 (2024_A) | 4/36 + 广泛工程应用 | ODE数值解是数值分析基本内容 | **否** |
| simulation (L4) | 1/5 (2019_C) | 9/144 variants | 仿真是独立建模方法 | **否** |
| analytical_methods (L4) | 3/5 | 29/144 variants | 解析/闭式方法是数学计算基本类别 | **否** |
| dimensionality_reduction (L4) | 1/5 (2022_C) | 3/36 + 广泛ML应用 | PCA是多元统计基本方法 | **否** |
| graph_algorithm (L4) | 0/5 | 3/144 variants | 图算法是计算机科学核心 | **否**（但国赛低频） |

### 9.2 标签稳定性评估

**稳定标签**（在多个来源中独立出现，具有明确的理论边界）：
- continuous_mechanics：CUMCM-HMML 领域7.1、高教社力学建模、Wiley distributed/lumped 分类
- statistical_association：MOOC 统计模型、四大模型"分类/预测"、Wiley black-box/phenomenological
- inverse_problem：数学物理反问题是独立研究领域（Tarantola 1987, Kaipio & Somersalo 2005）
- ODE/PDE 拆分：所有微分方程教材的基本分类
- metaheuristic：CUMCM-HMML 2.5、进化计算是独立学科
- simulation：CUMCM-HMML 领域8、仿真学会独立存在

**较低稳定性标签**（需持续验证）：
- supply_chain/operations：国赛仅 2/36，但 MCM/ICM D 题和运筹学领域稳定
- graph_algorithm：国赛仅 1/36 纯图算法题，但网络问题常涉及
- rule_based：仅 1/36，暂不新增

### 9.3 Non-overfitting 结论

**所有新增/修改标签均通过 non-overfitting 检查**：
1. 没有任何标签是仅为 5 道题中的某一题创建的
2. 所有标签在 36 题 benchmark 中有 ≥2 题覆盖（graph_algorithm 除外，但它在网络问题中隐含使用）
3. 所有标签在跨来源比较中得到独立验证（教材/课程/竞赛分类）
4. 所有标签对应数学建模领域中稳定、可区分的知识模块

**特别说明**：L2 是最根本的缺失层（原覆盖率 25%），新增 statistical_association 和 inverse_problem 后，L2 从 8 标签扩展到 11 标签，但这不是标签爆炸——每个标签都对应明确的建模范式，且在 36 题中有稳定覆盖。

---

## 10. 证据记录

### 10.1 重要决策证据表

| ID | Claim | Evidence | Source | Source Type | Confidence | Reasoning |
|---|---|---|---|---|---|---|
| E01 | L1 motion/geometry 应保留 | 36题中8题涉及，高教社设"几何分析"独立类别，MCM A题为连续型 | CUMCM-Bench-v2 + 高教社教材 + MCM官方 | Tier 1 (benchmark数据) + Tier 2 (教材) | HIGH | 空间几何/运动学是国赛A题核心，跨来源一致 |
| E02 | L1 uncertainty 应降级为属性维度 | 36题仅1题以uncertainty为主要结构，Wiley教材将deterministic/stochastic列为模型属性而非问题类型 | CUMCM-Bench-v2 + Wiley教材 | Tier 1 + Tier 2 | HIGH | uncertainty是所有问题的共同属性，独立为L1导致分类冲突 |
| E03 | L1 data/evaluation 应拆分 | 11题内部异质性大（预测vs评价vs聚类），MOOC课程将统计模型与评价模型分开教学 | CUMCM-Bench-v2 + 中国大学MOOC | Tier 1 + Tier 2 | HIGH | data_analysis和decision_evaluation的建模目标/验证方法/失败模式完全不同 |
| E04 | L1 continuous_mechanics 应新增 | 36题中4题（锚链/振动），CUMCM-HMML设"物理/力学建模"子领域 | CUMCM-Bench-v2 + CUMCM-HMML 7.1 | Tier 1 + Tier 2 (内部知识库) | HIGH | 力平衡/变形/振动与纯运动学/几何有本质区别 |
| E05 | L2 state_transition 应拆分 | ARIMA/GM/LSTM(自治递推)与MDP/DP(决策依赖)有本质区别，2020_B核心是MDP但原标签无时序语境外的覆盖 | 方法卡modeling_patterns + CUMCM-Bench-v2 2020_B | Tier 1 (方法卡数据) + Tier 1 (benchmark) | HIGH | 自治系统vs决策系统的状态转移有不同的数学结构和验证方法 |
| E06 | L2 statistical_association 应新增 | 36题中11题数据驱动但L2无对应标签，regression/statistical_analysis在allowed_model_families中高频 | CUMCM-Bench-v2 allowed_model_families统计 | Tier 1 | HIGH | 数据驱动建模与机理驱动建模是两大并列范式，L2必须覆盖 |
| E07 | L2 inverse_problem 应新增 | 36题中5题涉及反演，反问题有独特的不适定性+正则化特征 | CUMCM-Bench-v2 + 反问题经典文献(Tarantola) | Tier 1 + Tier 3 (学术) | HIGH | 反问题的建模方向(输出→输入)与正问题(输入→输出)相反，验证方法不同 |
| E08 | L3 differential_equation 应拆分为ODE+PDE | 36题中11题涉及DE，ODE用RK4，PDE用有限差分/有限元，CUMCM-HMML将1.1和1.2分为两个子领域 | CUMCM-Bench-v2 + CUMCM-HMML + methodology/ode-pde.md | Tier 1 + Tier 2 | HIGH | ODE/PDE的数学性质/求解方法/验证方式完全不同 |
| E09 | L3 optimization 不应拆分 | LP/IP/NLP共享min f(x) s.t. constraints框架，子类型区别在L4 solver层 | 优化理论标准框架 | Tier 2 (教材) | HIGH | L3拆分optimization会导致标签爆炸且语义重叠 |
| E10 | L4 GA应扩展为metaheuristic | 36题variants中GA出现14次(最高频)，PSO/SA/tabu/NSGA共享随机搜索范式，16卡中有3张元启发式卡 | CUMCM-Bench-v2 variants + 方法卡mc-ga/pso/sa | Tier 1 | HIGH | GA/PSO/SA是并列关系，统一为metaheuristic更合理 |
| E11 | L4 analytical_methods应新增 | 36题variants中解析/闭式方法出现29次(20.1%)，AHP/TOPSIS/熵权/M-M-c/Nash均衡均属此类 | CUMCM-Bench-v2 variants统计 + 方法卡mc-ahp/topsis/entropy | Tier 1 | HIGH | 闭式计算方法与迭代搜索方法有本质区别，当前L4完全缺失 |
| E12 | L4 exact_optimizer应新增 | 36题variants中LP/IP出现5次+约束优化等共12次，CUMCM-HMML设2.1/2.2子领域 | CUMCM-Bench-v2 + CUMCM-HMML 2.1/2.2 | Tier 1 + Tier 2 | HIGH | 精确求解器与元启发式的区别是保证最优解vs近似解 |
| E13 | L4 simulation应新增 | 36题variants中DES/ABM/CA出现9次，CUMCM-HMML设领域8，methodology/simulation.md独立 | CUMCM-Bench-v2 + CUMCM-HMML + methodology/simulation.md | Tier 1 + Tier 2 | HIGH | 仿真关注系统动态演化，与Monte Carlo的随机抽样估计不同 |
| E14 | 2019_C是假阳性 | L1 network/traffic 0卡，L2 queue/flow/interaction 0卡，但L3/L4碰巧匹配得100分 | 审计报告§4.2 + 方法卡覆盖分析 | Tier 1 | HIGH | 当前指标仅查L4，无法区分系统覆盖与偶然匹配 |
| E15 | 三题method_selection=0根因在L1/L2 | 2024_A L1 motion 0卡，2020_B L2 MDP无标签，2018_A L1+L2+L4三层0卡 | 审计报告§4 + 本验证映射表 | Tier 1 | HIGH | 补充taxonomy后三题知识路径完整闭合 |

### 10.2 证据等级说明

- **Tier 1**：CUMCM-Bench-v2.json 结构化数据（36题 family/allowed_model_families/acceptable_solution_variants）、16张方法卡字段、5题 problem card
- **Tier 2**：CUMCM-HMML 内部知识库、methodology/ 目录文档、高教社教材目录、中国大学MOOC课程大纲、MCM/ICM官方分类
- **Tier 3**：Wiley教材分类、反问题学术文献(Tarantola 1987, Kaipio & Somersalo 2005)、CSDN/博客园流行分类（仅作参考，不作为主要证据）

---

## 11. 争议与不确定项

### 11.1 UNCERTAIN 决策列表

| ID | 决策 | 争议点 | 当前立场 | 需进一步验证 |
|---|---|---|---|---|
| U01 | diffusion 是否与 continuous_mechanics 合并 | 热传导(PDE)和连续力学(ODE/代数)都是物理建模，但求解方法不同 | **保持独立**。diffusion=PDE场问题，continuous_mechanics=ODE/力平衡。两者L3不同(PDE vs ODE) | 若未来国赛出现更多耦合问题（如热-力耦合），可考虑合并为 continuous_physics |
| U02 | supply_chain/operations 是否独立 L1 | 国赛仅2/36，与scheduling边界重叠 | **保持独立**，允许与scheduling多标。供应链是多环节协调，调度是单场景时间分配 | 积累更多benchmark题目后重新评估 |
| U03 | optical/inverse 放在 L1 还是 L2 | 2017_A(CT)和2025_B(光学)有独特的光学物理结构 | **放在 L2** (inverse_problem)。反问题通常与其他L1共存(diffusion/motion/geometry)，不是独立问题结构 | 若出现纯光学题（无反演），可考虑L1 optical |
| U04 | stochastic_process 是否独立 L3 | 马尔可夫链/排队论/布朗运动是否与probability分开 | **合并入 probability_and_stochastic**。两者共享概率空间基础 | 若随机过程方法卡数量增加，可考虑拆分 |
| U05 | graph_algorithm 是否独立 L4 | 国赛仅1/36纯图算法题 | **保持独立**。图算法(Dijkstra/BFS/A*)是独立求解范式 | 若benchmark扩展后图算法题仍<5%，可合并入exact_optimizer |
| U06 | rule_based 是否新增 L1 | 2015_C(农历历法)是唯一规则建模题 | **暂不新增**。单一题目不具备稳定地位 | 若出现≥3题规则建模，重新评估 |
| U07 | DP 属于 L3 还是 L4 | DP既是建模框架(MDP)也是求解算法 | **L4** (DP_and_MDP)，MDP建模部分在L2(decision_state_transition) | 与e2e_metrics的method_selection对齐方式需进一步设计 |
| U08 | analytical_methods 是否过于宽泛 | AHP/TOPSIS/排队公式/Nash均衡/静力平衡都归入此类 | **保持统一**。共同特征是闭式计算/无迭代搜索。具体方法在方法卡层面区分 | 若analytical_methods覆盖>30% variants，可考虑拆分为analytical_decision + analytical_physics |

### 11.2 分类争议记录

| 争议 | 多方立场 | 本验证折中 |
|---|---|---|
| 四层 vs 三层 taxonomy | 审计报告建议四层；CUMCM-HMML用三层(领域→子领域→方法) | 四层更精细，L2 Modeling Pattern是关键中间层，不可省略 |
| 方法卡=Constraint vs 方法卡=Answer | 治理原则明确Constraint/Prior；但实际使用中LLM倾向按卡选方法 | 保持Constraint定位，通过not_for字段约束资格审查 |
| benchmark用gold method vs allowed_families | 旧版用historical_core_methods作为gold；v2改用allowed_model_families | 支持v2的多解模型原则，allowed_families是唯一评分依据 |

---

## 12. 最终建议汇总

### 12.1 建议的四层 taxonomy v0.1

```
L1 Problem Structure (9 + 1属性)
├── motion/geometry
├── continuous_mechanics
├── diffusion/heat_transfer
├── network/traffic
├── scheduling
├── supply_chain/operations
├── competition/game
├── decision_evaluation
├── data_analysis
└── [属性] stochastic/deterministic (原uncertainty降级)

L2 Modeling Pattern (11)
├── temporal_recurrence
├── decision_state_transition
├── conservation_law
├── flow_balance
├── geometric_constraint
├── resource_constraint
├── queue
├── spatial_temporal_field
├── interaction_game
├── statistical_association
└── inverse_problem

L3 Mathematical Formulation (7)
├── optimization
├── ODE
├── PDE
├── graph
├── probability_and_stochastic
├── statistics
└── linear_algebra

L4 Solver/Algorithm (12)
├── numerical_PDE
├── numerical_ODE
├── DP_and_MDP
├── monte_carlo
├── metaheuristic_optimization
├── exact_optimizer
├── regression_and_supervised
├── clustering
├── dimensionality_reduction
├── simulation
├── analytical_methods
└── graph_algorithm
```

### 12.2 优先级

| 优先级 | 动作 | 理由 |
|---|---|---|
| **P0** | 建立 L2 标签体系（11标签），对现有16卡做 retro-tagging | L2是最根本缺失层(25%)，是连接问题与数学的关键中间层 |
| **P0** | 建立 L1 标签体系（9+1属性），对现有16卡做 retro-tagging | L1缺失直接导致A/B题路由失败 |
| **P1** | L4 标签集扩展（6→12），补充 metaheuristic/exact_optimizer/simulation/analytical_methods 等 | L4当前仅覆盖40% variants |
| **P1** | L3 ODE/PDE 拆分 | 与L2/L4的细化对齐 |
| **P2** | 新增方法卡：mc-dp, mc-pde-finite-difference, mc-queuing-theory, mc-kinematics | 填补核心求解器空白 |
| **P2** | e2e_metrics method_selection 升级为四层语义对齐评分 | 检测假阳性(如2019_C) |

### 12.3 治理红线

1. **不修改现有 core/knowledge 下的文件**——本报告仅为研究层校准建议
2. **不为覆盖率硬造标签**——所有新增标签均通过 36题+跨来源验证
3. **方法卡=Constraint/Prior/Validation**——四层标签用于约束"声称某方法适用"的资格，不用于指令LLM"必须用X"
4. **多解模型原则**——benchmark 用 allowed_model_families，不用 gold method
5. **Knowledge coverage constrains evaluation, not creativity**——LLM 提出卡库外方法时标记 alternative_method，不自动判错

---

*本报告为 research-layer calibration 文档，所有结论用于仪器校准方向参考，未执行任何修改操作。*
*研究代理：分类学元验证 + Benchmark 映射代理*
*完成日期：2026-09-08*
