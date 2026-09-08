# Architecture Gate Report — 新增知识单元与候选方法卡架构审核

> **综合代理**：Research-layer Calibration 综合代理
> **日期**：2026-09-08
> **审核标准**：5条Gate Criteria，全部满足方可进入正式 core/knowledge
> **审核范围**：17个新增/扩展知识单元 + 7张NEW候选方法卡 + 3张RETRO-TAG卡 + 1张REVISE卡

---

## 0. Gate Criteria 定义

| # | 标准 | 定义 | 通过条件 |
|---|---|---|---|
| 1 | **定义清晰** | 有明确的、不模糊的定义 | 定义中无歧义术语，边界条件明确，与相邻概念的区分清晰 |
| 2 | **层级归属明确** | 能清晰归入 L1/L2/L3/L4 中的某一层，不跨层混淆 | 严格区分 Problem Structure ≠ Modeling Pattern ≠ Mathematical Formulation ≠ Solver/Algorithm |
| 3 | **跨来源支持** | 至少 2 个 Tier 1/Tier 2 来源支持 | 来源包括：4份领域研究报告、外部权威文献、benchmark数据、CUMCM-HMML、教材 |
| 4 | **能映射真实题目** | 至少能映射 1 道真实 CUMCM/MCM 问题 | 有明确的题目编号和映射路径 |
| 5 | **与现有标签不重叠** | 与现有 16 张卡和已确认标签无语义重叠 | 语义边界清晰，不与现有标签的核心定义重复 |

**Gate Result 枚举**：
- **GATE_PASS**：5条全部满足，可进入正式知识库
- **CANDIDATE_PENDING_GATE**：至少1条不满足，暂不进入正式知识库，需修正后重审
- **GATE_PASS_WITH_NOTES**：5条基本满足，但有需注意的边界问题，可进入但需标注注意事项

---

## 1. 新增知识单元 Gate 审核

### 1.1 L1 知识单元

| Knowledge Unit | 定义清晰 | 层级明确 | 跨来源支持 | 映射真实题 | 不重叠 | Gate Result |
|---|---|---|---|---|---|---|
| KU-L1-01 continuous_mechanics | ✅ | ✅ L1 | ✅ taxonomy+continuous_physics+CUMCM-HMML (3来源) | ✅ 2016_A/2019_A/2019_B/2022_A (4题) | ✅ 与motion/geometry边界：纯运动学(无力)归motion/geometry，涉及力/变形/振动归continuous_mechanics | **GATE_PASS_WITH_NOTES** |
| KU-L1-02 supply_chain/operations | ✅ | ✅ L1 | ⚠️ taxonomy+MCM/ICM (2来源，但国赛仅2题) | ✅ 2021_C/2024_C (2题) | ✅ 与scheduling边界：单场景时间分配归scheduling，多环节协调归supply_chain | **CANDIDATE_PENDING_GATE** |

**continuous_mechanics Notes**：
- 与motion/geometry的边界需在实际标注中进一步验证（Tier 2证据）
- 允许两标签多标（运动学+动力学耦合问题）
- 定义清晰："力平衡/变形/振动动力学"与motion/geometry的"纯运动学/几何"有本质区别

**supply_chain/operations Pending原因**：
- 跨来源支持：虽有2个来源，但国赛benchmark中仅2题（Tier 2证据，MEDIUM置信度）
- 需下一轮扩展benchmark至50+题验证覆盖度
- 若未来国赛中此类题目持续<2题，可考虑降级为L2或合并入scheduling
- **修正建议**：暂作为CANDIDATE标签，不进入正式L1标签集，待benchmark扩展后重审

---

### 1.2 L2 知识单元

| Knowledge Unit | 定义清晰 | 层级明确 | 跨来源支持 | 映射真实题 | 不重叠 | Gate Result |
|---|---|---|---|---|---|---|
| KU-L2-01 decision_state_transition | ✅ | ✅ L2 | ✅ discrete_optimization+taxonomy+Bellman经典文献 (3来源) | ✅ 2020_B/2018_B/2021_C (3题) | ✅ 与temporal_recurrence边界：有决策变量a_t vs 自治递推 | **GATE_PASS** |
| KU-L2-02 statistical_association | ✅ | ✅ L2 | ✅ taxonomy+中国大学MOOC+CSDN (3来源) | ✅ 2016_C/2017_C/2022_C/2023_C (4题+) | ✅ 与conservation_law边界：数据驱动vs机理驱动 | **GATE_PASS** |
| KU-L2-03 inverse_problem | ✅ | ✅ L2 | ⚠️ taxonomy+continuous_physics (2来源，但通常与其他L2共存) | ✅ 2018_A/2017_A/2015_A (3题) | ✅ 与其他L2不重叠（反问题是建模方向，不是建模机理） | **GATE_PASS_WITH_NOTES** |
| KU-L2-04 geometric_constraint | ✅ | ✅ L2 | ✅ continuous_physics+taxonomy+audit (3来源) | ✅ 2024_A/2016_A/2015_A/TOPSIS类 (4题+) | ⚠️ 与L1 motion/geometry边界需验证 | **GATE_PASS_WITH_NOTES** |
| KU-L2-05 temporal_recurrence | ✅ | ✅ L2 | ✅ taxonomy+discrete_optimization+audit (3来源) | ✅ 2016_C/2023_C/ARIMA类 (3题+) | ✅ 与decision_state_transition边界清晰 | **GATE_PASS** |

**inverse_problem Notes**：
- 通常与其他L2标签共存（不是排他性标签），如2018_A同时标conservation_law+inverse_problem
- 这是合理的：inverse_problem描述"建模方向"（已知输出反求输入），其他L2描述"建模机理"
- 定义清晰：不适定性+正则化+验证方法不同是其核心特征

**geometric_constraint Notes**：
- 与L1 motion/geometry的边界：L1描述"问题是什么"，L2描述"怎么建模"
- 一个motion/geometry问题可以用geometric_constraint建模，也可以用temporal_recurrence建模
- 两者不重叠，是层间关系，但实际标注中需进一步验证

---

### 1.3 L3 知识单元

| Knowledge Unit | 定义清晰 | 层级明确 | 跨来源支持 | 映射真实题 | 不重叠 | Gate Result |
|---|---|---|---|---|---|---|
| KU-L3-01 ODE | ✅ | ✅ L3 | ✅ continuous_physics+taxonomy+CUMCM-HMML+IEEE (4来源) | ✅ 2024_A/2016_A/2019_A/2022_A (4题+) | ✅ 与PDE边界：单变量+集中参数 vs 多变量+分布参数 | **GATE_PASS** |
| KU-L3-02 PDE | ✅ | ✅ L3 | ✅ continuous_physics+taxonomy+CUMCM-HMML+UC Davis (4来源) | ✅ 2018_A/2020_A (2题) | ✅ 与ODE边界清晰 | **GATE_PASS** |

---

### 1.4 L4 知识单元

| Knowledge Unit | 定义清晰 | 层级明确 | 跨来源支持 | 映射真实题 | 不重叠 | Gate Result |
|---|---|---|---|---|---|---|
| KU-L4-01 exact_optimizer | ✅ | ✅ L4 | ✅ discrete_optimization+taxonomy+IEEE+arXiv (4来源) | ✅ 2018_B/2021_C/2024_C (3题+) | ✅ 与metaheuristic边界：精确最优vs近似解 | **GATE_PASS** |
| KU-L4-02 numerical_ODE | ✅ | ✅ L4 | ✅ continuous_physics+taxonomy+methodology (3来源) | ✅ 2024_A/2016_A/2019_A (3题+) | ✅ 与numerical_PDE边界：无需空间离散 vs 需空间离散 | **GATE_PASS** |
| KU-L4-03 simulation | ✅ | ✅ L4 | ✅ taxonomy+network_game+CUMCM-HMML+Minitab (4来源) | ✅ 2019_C/2020_B/2016_B (3题+) | ⚠️ 与monte_carlo边界模糊 | **GATE_PASS_WITH_NOTES** |
| KU-L4-04 analytical_methods | ✅ | ✅ L4 | ✅ taxonomy+network_game+audit (3来源) | ✅ 2019_C(M/M/c)/TOPSIS类/AHP类 (4题+) | ✅ 与exact_optimizer边界：闭式计算vs迭代搜索 | **GATE_PASS** |
| KU-L4-05 graph_algorithm | ✅ | ✅ L4 | ⚠️ discrete_optimization+network_game+taxonomy (3来源，但benchmark仅1题) | ⚠️ 2025_D (1题) | ⚠️ 与exact_optimizer边界：最大流可转化为LP | **CANDIDATE_PENDING_GATE** |
| KU-L4-06 dimensionality_reduction | ✅ | ✅ L4 | ✅ taxonomy+audit+methodology (3来源) | ✅ 2022_C/PCA类 (2题+) | ✅ 与regression/clustering边界：无监督变换vs预测vs分组 | **GATE_PASS** |
| KU-L4-07 DP_and_MDP | ✅ | ✅ L4 | ✅ discrete_optimization+taxonomy+Bellman+Stanford (4来源) | ✅ 2020_B/2018_B (2题+) | ✅ 与exact_optimizer边界：Bellman递归vs通用数学规划 | **GATE_PASS** |
| KU-L4-08 metaheuristic_optimization | ✅ | ✅ L4 | ✅ taxonomy+discrete_optimization+CUMCM-HMML (3来源) | ✅ 2018_B(GA)/多题 (4题+) | ✅ 与exact_optimizer边界清晰 | **GATE_PASS** |

**simulation Notes**：
- 与monte_carlo的边界模糊：MC是仿真的随机引擎，simulation是系统演化模拟
- 初步边界：simulation关注系统动态演化过程（事件驱动/Agent驱动），monte_carlo关注随机抽样的统计估计（风险评估/不确定性传播）
- 两者可多标
- 需制定详细标注指南，在10+题上进行双盲标注一致性检验

**graph_algorithm Pending原因**：
- 映射真实题：36题benchmark中仅1题（2025_D），不满足"至少1题"的最低要求虽勉强满足，但覆盖度极低
- 与exact_optimizer边界：最大流/最小费用流可转化为LP，语义有重叠
- 跨来源支持：虽有3个来源，但benchmark数据支持弱
- **修正建议**：暂作为CANDIDATE标签，图算法内容暂归入mc-network-flow候选卡（已涵盖最短路径/最大流/最小费用流），待benchmark扩展后重审是否需要独立L4标签+方法卡

---

### 1.5 知识单元 Gate 审核汇总

| Gate Result | 数量 | 知识单元 |
|---|---|---|
| GATE_PASS | 11 | decision_state_transition, statistical_association, temporal_recurrence, ODE, PDE, exact_optimizer, numerical_ODE, analytical_methods, dimensionality_reduction, DP_and_MDP, metaheuristic_optimization |
| GATE_PASS_WITH_NOTES | 4 | continuous_mechanics, inverse_problem, geometric_constraint, simulation |
| CANDIDATE_PENDING_GATE | 2 | supply_chain/operations, graph_algorithm |
| **合计** | **17** | |

---

## 2. 候选方法卡 Gate 审核

### 2.1 NEW 候选卡

| Method Card | 定义清晰 | 层级明确 | 跨来源支持 | 映射真实题 | 不重叠 | Gate Result |
|---|---|---|---|---|---|---|
| mc-dp | ✅ | ✅ L2+L3+L4 | ✅ discrete_optimization+taxonomy+Bellman+Stanford (4来源) | ✅ 2020_B (核心) | ✅ 与现有16卡无语义重叠（无DP卡） | **GATE_PASS** |
| mc-numerical-pde | ✅ | ✅ L2+L3+L4 | ✅ continuous_physics+taxonomy+Lax定理+UC Davis (4来源) | ✅ 2018_A (核心), 2020_A | ✅ 与现有16卡无语义重叠（无数值PDE卡） | **GATE_PASS** |
| mc-queuing-theory | ✅ | ✅ L2+L3+L4 | ✅ network_game+taxonomy+Kendall+Little (4来源) | ✅ 2019_C (核心) | ✅ 与现有16卡无语义重叠（无排队论卡，mc-monte-carlo只是仿真工具） | **GATE_PASS** |
| mc-game-theory | ✅ | ✅ L2+L3+L4 | ✅ network_game+discrete_optimization+taxonomy+Nash (4来源) | ✅ 2020_B Q3 (核心), 2025_D | ✅ 与现有16卡无语义重叠（无博弈论卡） | **GATE_PASS** |
| mc-network-flow | ✅ | ✅ L2+L3+L4 | ✅ network_game+discrete_optimization+taxonomy+Ford-Fulkerson (4来源) | ✅ 2016_B, 2025_D | ⚠️ 与mc-milp边界：最小费用流可转化为LP | **GATE_PASS_WITH_NOTES** |
| mc-milp | ✅ | ✅ L2+L3+L4 | ✅ discrete_optimization+taxonomy+IEEE+Land-Doig (4来源) | ✅ 2018_B, 2021_C | ✅ 与现有16卡无语义重叠（无MILP卡） | **GATE_PASS** |
| mc-ode-modeling | ✅ | ✅ L2+L3+L4 | ✅ continuous_physics+taxonomy+IEEE+UAlberta (4来源) | ✅ 2024_A (核心), 2016_A | ✅ 与现有16卡无语义重叠（无ODE建模卡） | **GATE_PASS** |

**mc-network-flow Notes**：
- 与mc-milp的边界：最小费用流可转化为LP（MILP的连续版本），但网络流有专门的高效算法（Dinic/Edmonds-Karp），且问题结构（节点-边-容量）与通用MILP不同
- 两者可多标：一个问题既可以用网络流算法求解，也可以用MILP求解器求解
- mc-network-flow侧重图结构+网络流算法，mc-milp侧重通用数学规划+分支定界

---

### 2.2 RETRO-TAG / REVISE 卡

| Method Card | 定义清晰 | 层级明确 | 跨来源支持 | 映射真实题 | 不重叠 | Gate Result |
|---|---|---|---|---|---|---|
| mc-ga (RETRO-TAG) | ✅ | ✅ L4 metaheuristic | ✅ taxonomy+discrete_optimization+CUMCM-HMML (3来源) | ✅ 2018_B (GA优化调度) | ✅ 与exact_optimizer边界清晰 | **GATE_PASS** |
| mc-pso (RETRO-TAG) | ✅ | ✅ L4 metaheuristic | ✅ taxonomy+audit (2来源) | ✅ 多题 (PSO优化) | ✅ 与exact_optimizer边界清晰 | **GATE_PASS** |
| mc-sa (RETRO-TAG) | ✅ | ✅ L4 metaheuristic | ✅ taxonomy+audit (2来源) | ✅ 多题 (SA优化) | ✅ 与exact_optimizer边界清晰 | **GATE_PASS** |
| mc-monte-carlo (REVISE) | ✅ | ✅ L4 monte_carlo | ✅ taxonomy+network_game+audit (3来源) | ✅ 2019_C (辅助仿真), 多题 | ⚠️ 与simulation边界模糊 | **GATE_PASS_WITH_NOTES** |

**mc-monte-carlo Notes**：
- 与simulation的边界模糊（同KU-L4-03 simulation Notes）
- REVISE内容：L1归属从uncertainty改为[属性]stochastic，L4扩展为[monte_carlo, simulation]
- 两者可多标

---

### 2.3 方法卡 Gate 审核汇总

| Gate Result | 数量 | 方法卡 |
|---|---|---|
| GATE_PASS | 9 | mc-dp, mc-numerical-pde, mc-queuing-theory, mc-game-theory, mc-milp, mc-ode-modeling, mc-ga(RETRO), mc-pso(RETRO), mc-sa(RETRO) |
| GATE_PASS_WITH_NOTES | 2 | mc-network-flow, mc-monte-carlo(REVISE) |
| CANDIDATE_PENDING_GATE | 0 | — |
| **合计** | **11** | |

---

## 3. 综合 Gate 审核结论

### 3.1 可进入正式知识库的内容

| 类别 | GATE_PASS | GATE_PASS_WITH_NOTES | 小计 |
|---|---|---|---|
| L1知识单元 | 0 | 1 (continuous_mechanics) | 1 |
| L2知识单元 | 3 (decision_state_transition, statistical_association, temporal_recurrence) | 2 (inverse_problem, geometric_constraint) | 5 |
| L3知识单元 | 2 (ODE, PDE) | 0 | 2 |
| L4知识单元 | 6 (exact_optimizer, numerical_ODE, analytical_methods, dimensionality_reduction, DP_and_MDP, metaheuristic_optimization) | 1 (simulation) | 7 |
| NEW方法卡 | 6 (mc-dp, mc-numerical-pde, mc-queuing-theory, mc-game-theory, mc-milp, mc-ode-modeling) | 1 (mc-network-flow) | 7 |
| RETRO-TAG/REVISE卡 | 3 (mc-ga, mc-pso, mc-sa) | 1 (mc-monte-carlo) | 4 |
| **合计** | **20** | **6** | **26** |

### 3.2 暂不进入正式知识库的内容（CANDIDATE_PENDING_GATE）

| 内容 | Pending原因 | 修正建议 | 重审条件 |
|---|---|---|---|
| KU-L1-02 supply_chain/operations | 国赛benchmark仅2题，跨来源支持为Tier 2（MEDIUM置信度） | 暂作为CANDIDATE标签，不进入正式L1标签集 | benchmark扩展至50+题后，supply_chain题数≥3 |
| KU-L4-05 graph_algorithm | benchmark仅1题，与exact_optimizer语义重叠（最大流可转化为LP） | 图算法内容暂归入mc-network-flow候选卡，不设独立L4标签 | benchmark扩展后图算法题数≥3，且与exact_optimizer边界清晰 |

### 3.3 GATE_PASS_WITH_NOTES 的注意事项

| 内容 | 注意事项 | 后续行动 |
|---|---|---|
| continuous_mechanics | 与motion/geometry边界需验证 | 制定标注指南，在5+力学题目上双盲标注 |
| inverse_problem | 通常与其他L2标签共存（非排他性） | 在标注指南中明确"可多标"规则 |
| geometric_constraint | 与L1 motion/geometry边界需验证 | 同上，制定层间区分指南 |
| simulation | 与monte_carlo边界模糊 | 制定详细边界指南，10+题双盲标注一致性检验 |
| mc-network-flow | 与mc-milp边界（最小费用流可转化为LP） | 在卡的not_for字段中明确边界 |
| mc-monte-carlo | 与simulation边界模糊 | 同simulation，制定边界指南 |

---

## 4. 进入正式知识库的实施建议

### 4.1 实施优先级

| 优先级 | 内容 | 理由 |
|---|---|---|
| P0（立即实施） | mc-dp, mc-numerical-pde, mc-queuing-theory 三张NEW卡 + L2 decision_state_transition + L3 ODE/PDE + L4 DP_and_MDP/numerical_PDE | 直接解决三题method_selection=0和2019_C假阳性 |
| P0（立即实施） | RETRO-TAG: mc-ga/mc-pso/mc-sa 标注metaheuristic_optimization | 修复L4标签归属，三张卡已有内容只需改标签 |
| P1（下一轮实施） | mc-game-theory, mc-milp, mc-ode-modeling, mc-network-flow 四张NEW卡 | 补充博弈/精确优化/ODE/网络流能力 |
| P1（下一轮实施） | L2 statistical_association/inverse_problem/geometric_constraint/temporal_recurrence + L4 exact_optimizer/numerical_ODE/analytical_methods/dimensionality_reduction/simulation | 完善L2/L4标签体系 |
| P1（下一轮实施） | L1 continuous_mechanics（GATE_PASS_WITH_NOTES） | 补充连续力学L1标签 |
| P2（待验证后实施） | REVISE: mc-monte-carlo扩展simulation标签 | 需先明确simulation/monte_carlo边界 |
| P2（待重审） | supply_chain/operations, graph_algorithm | CANDIDATE_PENDING_GATE，待benchmark扩展 |

### 4.2 实施步骤

1. **标签层更新**：在 `core/knowledge/taxonomy/` 中更新 L1-L4 标签定义（GATE_PASS + GATE_PASS_WITH_NOTES 的标签）
2. **方法卡新增**：在 `core/knowledge/methods/cards/` 中新增 7 张 NEW 卡（YAML格式）
3. **方法卡RETRO-TAG**：修改 mc-ga/mc-pso/mc-sa 的 family 和 layer_coverage 字段
4. **方法卡REVISE**：修改 mc-monte-carlo 的 L1/L4 归属
5. **标注指南**：制定 GATE_PASS_WITH_NOTES 标签的标注指南（边界说明+示例）
6. **验证**：用更新后的标签体系重新运行 benchmark 评分，检查三题 method_selection 是否>0
7. **回归测试**：运行 `py -3.12 core/tools/validate.py` 确保57项校验全绿

---

## 5. Gate 审核统计

| 指标 | 数值 |
|---|---|
| 审核知识单元总数 | 17 |
| GATE_PASS | 11 (64.7%) |
| GATE_PASS_WITH_NOTES | 4 (23.5%) |
| CANDIDATE_PENDING_GATE | 2 (11.8%) |
| 审核方法卡总数 | 11 |
| GATE_PASS | 9 (81.8%) |
| GATE_PASS_WITH_NOTES | 2 (18.2%) |
| CANDIDATE_PENDING_GATE | 0 (0%) |
| **综合通过率（PASS+PASS_WITH_NOTES）** | **26/28 = 92.9%** |
| **暂不通过率（PENDING_GATE）** | **2/28 = 7.1%** |

---

*本Architecture Gate Report对所有新增知识单元和候选方法卡执行了5条标准审核。20项GATE_PASS可立即进入正式知识库，6项GATE_PASS_WITH_NOTES可进入但需标注注意事项，2项CANDIDATE_PENDING_GATE暂不进入需修正后重审。综合通过率92.9%。*
