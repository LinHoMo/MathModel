# PART F: Research Gaps — 证据分级与研究缺口

> **综合代理**：Research-layer Calibration 综合代理
> **日期**：2026-09-08
> **原则**：不强行得出结论。证据不足的标记为 UNCERTAIN，需要下一轮实验验证的明确列出。

---

## 0. 证据分级标准

| 等级 | 定义 | 要求 |
|---|---|---|
| **Tier 1** | 强证据 | ≥3个独立来源支持（领域研究报告 + 外部权威文献 + benchmark数据），结论一致无矛盾 |
| **Tier 2** | 中等证据 | 2个来源支持，或1个来源+benchmark数据验证，结论基本一致但有细节争议 |
| **Tier 3** | 弱证据 | 仅1个来源支持，或多来源但结论有矛盾，需进一步验证 |
| **UNCERTAIN** | 不确定 | 证据不足或来源间存在不可调和的矛盾，当前无法得出可靠结论 |

---

## 1. Tier 1 强证据结论（多来源一致支持）

以下结论有≥3个独立来源支持，可视为当前研究阶段的可靠结论：

### 1.1 L3 differential equation 应拆分为 ODE + PDE

| 来源 | 证据 |
|---|---|
| continuous_physics §3.4 | 6项论据：物理本质/定解条件/数值方法/竞赛题分布均不同 |
| taxonomy §3.2.2 | 36题中11题涉及DE，ODE用RK4，PDE用有限差分，求解方法完全不同 |
| CUMCM-HMML | 将1.1常微分方程和1.2偏微分方程分为两个独立子领域 |
| IEEE Technology Navigator | "Distributed parameter systems requiring PDEs rather than ODEs" |
| University of Alberta PDE Notes | "ODE solution is a curve, PDE solution is a surface/hypersurface" |

**结论**：✅ Tier 1 强证据，ODE/PDE拆分可冻结。

### 1.2 graph 应保持 L3 一级标签（不提升为 L1）

| 来源 | 证据 |
|---|---|
| discrete_optimization §3.1 | graph是独立数学范式，图论问题不一定是优化问题，有独立算法体系 |
| network_game §3.1 | graph保持L3，不提升L1（网络问题的独特性在L2 flow_balance/queue） |
| taxonomy §3.2.3 | 36题中4题，CUMCM-HMML领域4，与optimization/DE/statistics并列 |
| CLRS《算法导论》 | 图算法是独立算法类别（第24-26章） |

**结论**：✅ Tier 1 强证据，graph L3地位可冻结。

### 1.3 L1 uncertainty 应降级为跨层属性

| 来源 | 证据 |
|---|---|
| taxonomy §1.2.7 | 36题仅1题以uncertainty为主要结构，作为L1标签导致分类冲突 |
| Wiley教材分类 | deterministic/stochastic是模型属性维度，不是问题结构 |
| continuous_physics | 热传导题涉及随机参数应标diffusion而非uncertainty |
| discrete_optimization | MDP的随机性是转移概率，不是独立问题结构 |

**结论**：✅ Tier 1 强证据，uncertainty降级可冻结。

### 1.4 L1 data/evaluation 应拆分为 data_analysis + decision_evaluation

| 来源 | 证据 |
|---|---|
| taxonomy §1.2.8 | 11题内部异质性大，data_analysis核心是模式提取，decision_evaluation核心是指标体系+排序 |
| 中国大学MOOC | "一元统计模型""多元统计分析模型"与"评价模型"分开教学 |
| CSDN流行"四大模型" | 将评价与预测/分类分开 |
| audit §2.3 | data/evaluation有10卡覆盖，但卡内部分为统计类(7张)和评价类(3张) |

**结论**：✅ Tier 1 强证据，data/evaluation拆分可冻结。

### 1.5 L2 state_transition 应拆分为 temporal_recurrence + decision_state_transition

| 来源 | 证据 |
|---|---|
| taxonomy §2.2.1 | ARIMA/GM/LSTM自治递推 vs MDP/DP决策依赖，验证方法不同 |
| discrete_optimization §2.2 | MDP五元组，Bellman方程，与时序预测有本质区别 |
| discrete_optimization §2.2.6 | 决策语境vs时序语境的区分表 |
| audit §2.2 | state_transition仅被ARIMA/GM/LSTM时序卡使用，决策语境零覆盖 |

**结论**：✅ Tier 1 强证据，state_transition拆分可冻结。

### 1.6 conservation_law ≠ flow_balance（连续场微分守恒 vs 离散网络代数平衡）

| 来源 | 证据 |
|---|---|
| continuous_physics §2.1 | conservation law是积分形式→微分形式PDE，适用于连续介质 |
| network_game §2.1 | flow balance是节点流量守恒方程（入流=出流+累积），适用于离散网络 |
| taxonomy §2.2.2/§2.2.3 | 两个标签分别映射不同题目（conservation→2018_A/2016_A，flow_balance→2019_C/2016_B） |
| 数学形式差异 | conservation: ∮F·dS = d/dt∫u dV（积分守恒）→ PDE; flow_balance: Σ入流=Σ出流（代数方程） |

**结论**：✅ Tier 1 强证据，conservation_law与flow_balance区分可冻结。

### 1.7 三题 method_selection=0 完全可归因于 L1/L2 缺失

| 来源 | 证据 |
|---|---|
| taxonomy §6.1 | 2024_A/2020_B/2018_A的L1/L2标签在原卡库中零覆盖 |
| continuous_physics §6 | 2018_A三层联动缺失（L1 diffusion + L2 conservation/spatial-temporal + L4 numerical PDE） |
| discrete_optimization §6 | 2020_B双重缺失（L2 resource/interaction + L4 DP/game theory） |
| audit §4.1 | 三题method_selection=0的根因分析 |

**结论**：✅ Tier 1 强证据，三题归因可冻结。

### 1.8 2019_C 100分是假阳性/浅层命中

| 来源 | 证据 |
|---|---|
| network_game §6.1 | 2019_C核心是M/M/c排队模型+司机决策博弈，MC只是辅助仿真 |
| taxonomy §2.2.6 | 排队论有独立理论体系（Kendall记号/M-M-c公式/Little's Law/生灭过程） |
| audit §4.2 | mc-monte-carlo只是"用仿真近似排队"，不是排队论本身 |
| 05_BENCHMARK_MAPPING §3 | 假阳性深度确认：正确核心卡应为mc-queuing-theory |

**结论**：✅ Tier 1 强证据，2019_C假阳性可冻结。

---

## 2. Tier 2 中等证据结论（2来源支持或有细节争议）

以下结论有2个来源支持，或1个来源+benchmark数据验证，但存在细节争议或需要更多验证：

### 2.1 L1 continuous_mechanics 应新增

| 来源 | 证据 | 争议点 |
|---|---|---|
| taxonomy §1.3.1 | 36题中4题（2016_A/2019_A/2019_B/2022_A），CUMCM-HMML领域7.1 | 与motion/geometry的边界：纯运动学（不涉及力）归motion/geometry，涉及力/变形/振动归continuous_mechanics |
| continuous_physics §6.4 | 2016_A系泊系统是静力平衡+悬链线，与2024_A纯运动学不同 | 部分题目可能同时涉及两者（如运动学+动力学耦合） |

**结论**：Tier 2 中等证据，continuous_mechanics新增可采纳，但与motion/geometry的边界需在实际标注中进一步明确。允许两标签多标。

### 2.2 L1 supply_chain/operations 应新增（MEDIUM置信度）

| 来源 | 证据 | 争议点 |
|---|---|---|
| taxonomy §1.3.2 | 36题中2题（2021_C/2024_C），MCM/ICM D题定义 | 国赛中此类题目较少（2/36），是否值得独立L1标签？ |
| MCM/ICM D题 | "Operations Research/Network Science"是独立题目类型 | 与scheduling的边界：scheduling=单场景时间分配，supply_chain=多环节协调 |

**结论**：Tier 2 中等证据，supply_chain/operations新增可采纳（MEDIUM置信度），允许与scheduling多标。若未来国赛中此类题目持续<2题，可考虑降级为L2或合并入scheduling。

### 2.3 L2 inverse_problem 应新增

| 来源 | 证据 | 争议点 |
|---|---|---|
| taxonomy §2.3.2 | 36题中5题涉及反演，allowed_model_families中inverse_problem出现5次 | 反问题通常与其他L1标签共存（2018_A同时是diffusion），是否应独立L2？ |
| continuous_physics §8.2 | 2018_A参数反演是经典不适定问题，需正则化 | 反问题的独特性（不适定性+正则化+验证方法不同）是否足以独立L2？ |

**结论**：Tier 2 中等证据，inverse_problem新增可采纳。反问题的独特性（不适定性+正则化+验证方法）足以独立L2，但需注意它通常与其他L2标签共存（不是排他性标签）。

### 2.4 L2 statistical_association 应新增

| 来源 | 证据 | 争议点 |
|---|---|---|
| taxonomy §2.3.1 | 36题中11题数据驱动但L2无对应标签 | 这是"补标签"还是"真新增"？原卡库已有11张统计类卡，只是L2层无标签 |
| 中国大学MOOC | 统计模型独立课程 | 与conservation_law/flow_balance等机理驱动标签的并列关系是否合理？ |

**结论**：Tier 2 中等证据，statistical_association新增可采纳。这是对原L2标签集的补全（数据驱动建模范式与机理驱动建模范式并列），不是为覆盖率硬造标签。

### 2.5 L3 optimization 不拆分（子类型留L4）

| 来源 | 证据 | 争议点 |
|---|---|---|
| taxonomy §3.3.3 | LP/IP/NLP共享min f(x) s.t. constraints框架，区别在变量类型和约束性质 | discrete_optimization §3.2建议optimization下设LP/IP/NLP/DP_formulation子标签 |
| L3定义 | L3是"数学表述形式"层，optimization作为统一表述形式是稳定的 | 子标签放在L3还是L4？ |

**裁决**：本审计采纳 taxonomy 的立场（不拆分），discrete_optimization 的子标签建议归入 L4 exact_optimizer 的子类型。理由：L3是数学表述形式层，min f(x) s.t. g(x)≤0是统一框架；变量类型差异是求解器层的事。

**结论**：Tier 2 中等证据（来源间有分歧，本审计已裁决），optimization不拆分可采纳。但需在L4 exact_optimizer中明确LP/IP/NLP子类型。

### 2.6 L3 game-theoretic formulation 不独立（归入optimization+probability组合）

| 来源 | 证据 | 争议点 |
|---|---|---|
| taxonomy §3.3.2 | 博弈论本质是多目标优化+概率，Nash求解可转化为优化问题 | network_game §3.2建议game-theoretic独立L3标签 |
| L3定义 | 博弈的独特性在L2（interaction_game建模模式），不在L3 | 合作博弈Shapley值是公理化解，不归入optimization |

**裁决**：本审计采纳 taxonomy 的立场（不独立），network_game 的独立建议被否决。理由：博弈的独特性在L2 interaction_game；L3用optimization（Nash↔互补问题）+ probability（混合策略）+ ODE（复制子动力学）组合标注。合作博弈Shapley值归入L4 analytical_methods。

**结论**：Tier 2 中等证据（来源间有分歧，本审计已裁决），game-theoretic不独立可采纳。

### 2.7 L4 metaheuristic_optimization 替代原 GA 标签

| 来源 | 证据 | 争议点 |
|---|---|---|
| taxonomy §4.2.4 | 36题variants中GA出现14次最高频，PSO/tabu/NSGA_II也有出现 | 原GA标签是否需要保留为子标签？ |
| discrete_optimization §4.4 | 元启发式分类：构造启发式/局部搜索/元启发式/超启发式 | GA/PSO/SA是否应各自独立L4标签？ |
| audit §2.2 | mc-pso/mc-sa是重要的元启发式求解器，但当前L4标签集未包含"metaheuristic optimization"类别 | — |

**结论**：Tier 2 中等证据，metaheuristic_optimization替代GA可采纳。GA/PSO/SA作为子类型在方法卡family字段中区分，L4层统一为metaheuristic_optimization。

---

## 3. Tier 3 弱证据 / UNCERTAIN 结论

以下结论证据不足或来源间存在不可调和的矛盾，当前无法得出可靠结论：

### 3.1 L1 optical/inverse 是否应新增 — UNCERTAIN

| 来源 | 证据 | 问题 |
|---|---|---|
| taxonomy §1.3.3 | 36题中3+2题涉及反演/光学 | 反问题通常与其他L1标签共存（2018_A同时是diffusion），不是独立问题结构 |
| continuous_physics §8.2 | 建议inverse problem放L2而非L1 | 已裁决放L2 inverse_problem |

**结论**：UNCERTAIN → 已裁决为 REJECT（移至L2 inverse_problem）。L1 optical/inverse不新增。

### 3.2 L1 rule_based 是否应新增 — UNCERTAIN

| 来源 | 证据 | 问题 |
|---|---|---|
| taxonomy §1.3.4 | 36题仅1题（2015_C农历历法） | 单一题目不具备稳定、可区分、可复用的地位 |

**结论**：UNCERTAIN → 已裁决为 REJECT。将2015_C归入data_analysis或作为outlier处理。若未来出现≥3题规则建模，重新评估。

### 3.3 L4 graph_algorithm 的优先级 — UNCERTAIN

| 来源 | 证据 | 问题 |
|---|---|---|
| taxonomy §4.3.5 | 36题variants中BFS/Dijkstra/A*仅出现在2025_D（1题） | 国赛中纯图算法题不多，是否值得独立L4标签+方法卡？ |
| discrete_optimization §3.1 | 图论有独立算法体系 | 图算法是否应归入exact_optimizer（最大流/最小费用流可转化为LP）？ |
| network_game §4.1 | 最短路径/最大流/最小费用流详细分类 | — |

**结论**：UNCERTAIN。graph_algorithm作为L4标签保留（MEDIUM置信度），但方法卡 mc-network-flow 已涵盖图算法+网络流，是否需要独立的 mc-graph-algorithm 卡待下一轮验证。若未来benchmark中图算法题≥3题，可考虑独立卡。

### 3.4 L3 stochastic_process 是否独立 — UNCERTAIN（已裁决合并）

| 来源 | 证据 | 问题 |
|---|---|---|
| continuous_physics §8.1 | 建议stochastic process独立L3（置信度medium） | 随机过程与probability共享概率空间基础，拆分意义不大 |
| taxonomy §3.3.1 | CUMCM-HMML将概率建模与随机过程放在同一领域 | 已裁决合并入probability_and_stochastic |

**结论**：UNCERTAIN → 已裁决为 MERGE（并入probability_and_stochastic）。continuous_physics的独立建议被否决。

### 3.5 L4 simulation 与 monte_carlo 的边界 — UNCERTAIN

| 来源 | 证据 | 问题 |
|---|---|---|
| taxonomy §4.3.3 | simulation（DES/ABM/CA）出现9次，monte_carlo出现3次 | 两者边界模糊：MC是仿真的随机引擎，simulation是系统演化模拟 |
| network_game §4.4 | DES/ABS/MC/SD分类 | MC是否应归入simulation的子类型？ |
| Minitab文章 | "DES适用于重新设计/改进流程，Monte Carlo适用于评估风险/不确定性" | 两者有不同的适用场景 |

**结论**：UNCERTAIN。simulation与monte_carlo作为并列L4标签保留，但边界需在实际标注中进一步明确。初步边界：simulation关注系统动态演化过程（事件驱动/Agent驱动），monte_carlo关注随机抽样的统计估计（风险评估/不确定性传播）。两者可多标。

### 3.6 L2 geometric_constraint 与 L1 motion/geometry 的边界 — UNCERTAIN

| 来源 | 证据 | 问题 |
|---|---|---|
| continuous_physics §2.3 | 刚体约束/碰撞检测/螺线参数化 | geometric_constraint是L2建模模式，motion/geometry是L1问题结构，两者边界在哪？ |
| taxonomy §2.2.4 | 原distance/geometry仅被TOPSIS使用，需扩展 | 扩展后是否会与L1 motion/geometry语义重叠？ |

**结论**：UNCERTAIN。初步边界：L1 motion/geometry描述"问题是什么"（运动学/几何建模问题），L2 geometric_constraint描述"怎么建模"（通过定义距离/几何/空间约束来构建模型）。一个motion/geometry问题可以用geometric_constraint建模，也可以用temporal_recurrence建模。两者不重叠，是层间关系。但实际标注中需进一步验证。

### 3.7 新增标签的 non-overfitting 长期验证 — UNCERTAIN

| 来源 | 证据 | 问题 |
|---|---|---|
| taxonomy §7 | 所有新增标签在36题中≥2题覆盖，通过non-overfitting检查 | 36题是有限样本，未来新题目是否仍满足≥2题覆盖？ |
| 国赛题目分布 | A题多为连续物理，C题多为数据分析 | 某些标签（如diffusion/competition/game）在国赛中天然低频 |

**结论**：UNCERTAIN。当前36题基准通过non-overfitting检查，但长期需在更多题目（包括MCM/ICM题目）上验证。建议下一轮研究扩展benchmark至50+题（含MCM/ICM），重新验证所有标签的覆盖度。

---

## 4. 不能现在冻结的 taxonomy 决策

以下决策证据不足或存在争议，**不能现在冻结**，需下一轮研究验证：

| 决策 | 当前状态 | 不能冻结的原因 | 下一轮验证计划 |
|---|---|---|---|
| L1 supply_chain/operations | ADD（MEDIUM置信度） | 国赛中仅2题，长期覆盖度不确定 | 扩展benchmark至50+题，检查supply_chain题数是否≥3 |
| L2 inverse_problem | ADD | 通常与其他L2标签共存，排他性不确定 | 在更多反问题题目上验证inverse_problem的独立标注价值 |
| L4 graph_algorithm | ADD（MEDIUM置信度） | 36题中仅1题，长期覆盖度不确定 | 扩展benchmark，检查图算法题数是否≥3；考虑是否合并入exact_optimizer |
| L4 simulation vs monte_carlo边界 | 并列保留 | 两者边界模糊，实际标注可能不一致 | 制定详细的标注指南，在10+题上进行双盲标注一致性检验 |
| L2 geometric_constraint vs L1 motion/geometry边界 | 层间关系 | 实际标注中可能出现语义重叠 | 制定标注指南，在5+运动学题目上验证层间区分 |
| L3 optimization子类型归属 | 不拆分（裁决） | discrete_optimization建议拆分，来源间有分歧 | 在更多优化题目上验证L4 exact_optimizer的子类型标注是否足够 |
| L3 game-theoretic不独立 | 不独立（裁决） | network_game建议独立，来源间有分歧 | 在更多博弈题目上验证optimization+probability组合标注是否足够 |
| 新增标签的长期non-overfitting | 当前通过 | 36题有限样本 | 扩展benchmark至50+题重新验证 |

---

## 5. 需要下一轮实验验证的知识

### 5.1 方法卡有效性验证

| 候选卡 | 验证内容 | 验证方法 |
|---|---|---|
| mc-dp | DP卡是否能正确引导LLM解决2020_B类问题 | 用mc-dp的constraint/prior/validation指导LLM解决2020_B，对比无卡指导的结果 |
| mc-numerical-pde | PDE卡是否能正确引导LLM解决2018_A类问题 | 同上，用2018_A验证 |
| mc-queuing-theory | 排队论卡是否能区分于MC仿真 | 用2019_C验证，检查LLM是否使用M/M/c公式而非仅MC仿真 |
| mc-game-theory | 博弈论卡是否能正确引导Nash均衡分析 | 用2020_B Q3验证 |
| mc-ode-modeling | ODE卡是否能正确引导2024_A类问题 | 用2024_A验证 |

### 5.2 标签标注一致性验证

| 验证内容 | 方法 |
|---|---|
| L1/L2/L3/L4四层标签的标注者间一致性 | 2名标注者独立标注10题，计算Cohen's Kappa |
| 新增标签（inverse_problem/statistical_association/geometric_constraint）的标注一致性 | 同上，重点检查新增标签 |
| L2 conservation_law vs flow_balance的区分一致性 | 在5+物理/网络题目上双盲标注 |
| L4 simulation vs monte_carlo的区分一致性 | 在5+仿真题目上双盲标注 |

### 5.3 Benchmark 扩展

| 扩展内容 | 目的 |
|---|---|
| 增加MCM/ICM题目（10+题） | 验证标签在国际竞赛题目的适用性 |
| 增加近年国赛题目（2023-2025，5+题） | 验证标签在新题目的适用性 |
| 总benchmark扩展至50+题 | 重新验证所有标签的non-overfitting和覆盖度 |

### 5.4 知识单元深度验证

| 知识单元 | 验证内容 |
|---|---|
| continuous_mechanics vs motion/geometry边界 | 在5+力学题目上验证两者的区分是否清晰 |
| supply_chain/operations vs scheduling边界 | 在3+供应链题目上验证 |
| inverse_problem的不适定性特征 | 在3+反问题题目上验证是否都需要正则化 |
| DP_and_MDP的适用/不适用条件 | 在5+DP可解/不可解问题上验证6条适用+6条不适用条件 |

---

## 6. 证据分级总览

| 结论类别 | Tier 1 | Tier 2 | Tier 3/UNCERTAIN | 合计 |
|---|---|---|---|---|
| L1标签决策 | 3（uncertainty降级, data/eval拆分, motion/geometry KEEP） | 2（continuous_mechanics, supply_chain） | 2（optical/inverse REJECT, rule_based REJECT） | 7 |
| L2标签决策 | 2（state_transition拆分, conservation≠flow_balance） | 3（inverse_problem, statistical_association, geometric_constraint扩展） | 1（geometric_constraint边界） | 6 |
| L3标签决策 | 2（ODE/PDE拆分, graph L3 KEEP） | 2（optimization不拆分, game-theoretic不独立） | 1（stochastic_process合并） | 5 |
| L4标签决策 | 0 | 1（metaheuristic替代GA） | 2（graph_algorithm, simulation/MC边界） | 3 |
| Benchmark归因 | 2（三题归因, 2019_C假阳性） | 0 | 0 | 2 |
| **合计** | **9** | **8** | **6** | **23** |

**关键发现**：
- 9项Tier 1强证据结论可冻结（占39%）
- 8项Tier 2中等证据结论可采纳但需关注细节（占35%）
- 6项Tier 3/UNCERTAIN结论不能冻结，需下一轮验证（占26%）
- 总体而言，核心架构决策（L1/L2/L3的主要拆分和KEEP）有强证据支持，但新增标签的边界和长期覆盖度需进一步验证

---

*本文件遵循"不强行得出结论"原则。所有Tier 1结论可冻结，Tier 2结论可采纳但需关注细节，UNCERTAIN结论不能冻结需下一轮验证。治理原则：Knowledge coverage must constrain evaluation, not constrain creativity。*
