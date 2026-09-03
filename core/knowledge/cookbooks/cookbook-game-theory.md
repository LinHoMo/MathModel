# Cookbook: 博弈论类模型

> 适用场景：多主体决策、利益冲突/合作、机制设计、拍卖、谈判、进化动力学。CUMCM E题、MCM F题、机制设计题高频。

---

## 1. 静态完全信息博弈 (Normal Form Games)

| 概念 | 定义/求解 | 代码模板 |
|------|-----------|----------|
| **纳什均衡 (纯/混合)** | 最佳响应互为最佳响应：$u_i(s_i^*, s_{-i}^*) \ge u_i(s_i, s_{-i}^*)$ | `nash_pure.py`, `nash_mixed.py` (支持向量/线性互补/序列最佳响应) |
| **严格/弱优势策略** | 严格：$u_i(s_i', s_{-i}) > u_i(s_i, s_{-i}) \forall s_{-i}$ | `dominance.py` |
| **迭代删除优势策略 (IDSDS/IDWDS)** | 循环删除严格/弱优势策略 | `iterated_dominance.py` |
| **有理化策略** | 公知有理性下可被合理化的策略 | `rationalizability.py` |
| **相关均衡** | 中介器推荐、无偏离动机 | `correlated_equilibrium.py` (线性规划) |
| **粗相关均衡** | 无条件相关设备 | `coarse_correlated.py` |

**计算工具**：`nashpy` (2人小博弈)、`gambit` (通用)、`pypng`、自实现 Lemke-Howson/支撑枚举/单纯形

---

## 2. 动态完全信息博弈 (Extensive Form Games)

| 概念 | 定义/求解 | 代码模板 |
|------|-----------|----------|
| **子博弈完美均衡 (SPE)** | 逆向归纳法：每个子博弈都是纳什均衡 | `spe_backward_induction.py` |
| **完全信息精炼** | 完美贝叶斯均衡 (PBE) 前身 | `perfect_equilibrium.py` |
| **重复博弈** | 有限/无限重复、民间定理、触发策略 | `repeated_games.py` |
| **随机博弈** | 状态转移、马尔可夫完美均衡 (MPE) | `stochastic_games.py` |

---

## 3. 不完全/不完全信息博弈 (Bayesian Games)

| 概念 | 定义/求解 | 代码模板 |
|------|-----------|----------|
| **贝叶斯纳什均衡 (BNE)** | 类型空间、先验信念、策略映射类型→行动、期望效用最大化 | `bne_template.py` |
| **完美贝叶斯均衡 (PBE)** | 顺序有理(最优性) + 贝叶斯更新(一致性) | `pbe_template.py` |
| **信号/筛选模型** | 发送者/接收者、分离/混合/半分离均衡 | `signaling_screening.py` |
| **机制设计/启示原则** | 直接机制、激励相容(IC)、个体理性(IR)、收入等价 | `mechanism_design.py` |

---

## 4. 合作博弈

| 概念 | 定义/求解 | 代码模板 |
|------|-----------|----------|
| **特征函数形式** | $v: 2^N \to \mathbb{R}$, $v(\emptyset)=0$ | `characteristic_function.py` |
| **核** | 无阻塞联盟：$x(S) \ge v(S) \forall S \subseteq N$, $x(N)=v(N)$ | `core_solution.py` (线性规划/极点枚举) |
| **夏普利值** | $\phi_i = \sum_{S \subseteq N\setminus\{i\}} \frac{|S|!(n-|S|-1)!}{n!} [v(S\cup\{i\}) - v(S)]$ | `shapley_value.py` (采样近似/精确) |
| ** nucleolus** | 字典序最小化超额 | `nucleolus.py` |
| **博弈论指数** | Shapley-Shubik / Banzhaf 权力指数 | `power_indices.py` |
| **NTU 博弈 / 交换经济** | 效用可转移/不可转移 | `ntu_games.py` |

---

## 5. 演化博弈论

| 模型 | 方程/规则 | 适用场景 | 代码模板 |
|------|-----------|----------|----------|
| **复制子动力学** | $\dot{x}_i = x_i [f_i(x) - \bar{f}(x)]$ | 种群策略演化、ESS 分析 | `replicator_dynamics.py` |
| **最佳响应动力学** | 策略向当前最佳响应调整 | 有限有理、学习 | `best_response_dynamics.py` |
| **模仿/费米动力学** | 概率模仿高收益邻居 | 网络/空间结构 | `imitation_dynamics.py` |
| **演化稳定策略 (ESS)** | 抗入侵：$u(ESS, ESS) > u(mutant, ESS)$ 或 = 且 $u(ESS, mutant) > u(mutant, mutant)$ | 长期稳定均衡预测 | `ess_analysis.py` |
| **空间/网络演化博弈** | 图上局部交互、簇形成 | 合作演化/结构影响 | `spatial_evolutionary.py` |

---

## 6. 经典博弈模型与应用

| 模型 | 结构 | 均衡/洞察 | 应用场景 | 代码模板 |
|------|------|-----------|----------|----------|
| **囚徒困境** | $T>R>P>S$, $2R>T+S$ | 唯一 NE (背叛,背叛)、重复下合作可维持 | 合作演化、公地悲剧、军备竞赛 | `prisoners_dilemma.py` |
| **协调博弈** | 两纯策略 NE、风险/收益占优 | 多重均衡、焦点/风险占优选择 | 技术标准、会面、规范形成 | `coordination_game.py` |
| **鹰鸽/鸡博弈** | 两纯 NE (鹰,鸽) 和 (鸽,鹰)、混合 NE | 冲突升级/退让、资源争夺 | 領土争夺、谈判僵局 | `hawk_dove.py` |
| **公共物品博弈** | 贡献成本 c、收益 r·Σc/n | 纳什零贡献、惩罚/奖励/声誉可维持合作 | 团队激励、众筹、环保 | `public_goods.py` |
| **最后通牒/独裁者博弈** | 提议者分割、响应者接受/拒 | 理性 NE 接受任意>0、实验显示公平偏好 | 谈判、分配公平 | `ultimatum_dictator.py` |
| **拍卖 (一价/二价/英式/荷式)** | 独立私有价值/共同价值、风险中性 | 收入等价定理、最优保留价 | 广告位/频谱/艺术品/电商 | `auctions.py` |
| **伯努利工厂/信息设计** | 发送者设计信息结构、接收者最优响应 | 贝叶斯劝说、最优信息披露 | 监管披露、推荐系统、说服 | `bayesian_persuasion.py` |
| **Stackelberg 领导者-跟随者** | 领导者先动、跟随者最佳响应、子博弈完美 | 先发优势/劣势、承诺力量 | 市场准入、监管、平台定价 | `stackelberg.py` |
| ** Colonel Blotto / 资源分配博弈** | 多战场分配资源、赢得多数战场 | 混合策略、对称/不对称 | 广告预算/竞选/军事/研发分配 | `blotto.py` |

---

## 7. 机制设计 / 拍卖理论 (进阶)

| 问题 | 核心结果 | 代码模板 |
|------|----------|----------|
| **最优单物品拍卖 (Myerson)** | 虚拟价值 $\phi(v) = v - \frac{1-F(v)}{f(v)}$、铁律：单调性+个体理性 | `myerson_optimal.py` |
| **多物品/组合拍卖** | VCG 机制、效率最优、计算复杂(赢家确定 NP-hard) | `combinatorial_auction.py` (整数规划/启发式) |
| **双边市场/匹配机制** | Gale-Shapley 延迟接受算法、稳定匹配、策略免疫(提议方) | `matching_mechanisms.py` |
| **公共项目/公共品机制** | VCG/AGV/预算平衡/激励相容不可能三角 | `public_project_mechanisms.py` |
| **鲁棒机制设计** | 模型误设定下性能保证、最大最小遗憾 | `robust_mechanism.py` |

---

## 8. 计算博弈论工具箱

| 库/工具 | 功能 | 安装 | 代码模板 |
|---------|------|------|----------|
| **Nashpy** | 2人矩阵博弈 NE (支撑枚举/顶点枚举/Lemke-Howson) | `pip install nashpy` | `nash_nashpy.py` |
| **Gambit** | 通用博弈 (树形/矩阵)、NE/精炼、命令行/图形 | `pip install gambit` (或源码) | `nash_gambit.py` |
| **Axelrod** | 重复囚徒困境策略库/锦标赛/演化 | `pip install axelrod` | `axelrod_tournament.py` |
| **EGTAOnline / PyEGTA** | 经验博弈论分析、模拟估计收益矩阵 | `pip install egta` | `egta_analysis.py` |
| **OpenSpiel** | 强化学习/博弈求解/AlphaZero/多智能体 | `pip install open_spiel` | `openspiel_rl.py` |
| **MARLlib / PettingZoo** | 多智能体 RL 环境/算法 | `pip install marllib pettingzoo` | `marl_training.py` |

---

## 9. 代码模板目录映射

```
core/Programmer/knowledge/code-templates/game-theory/
├── nash_pure.py
├── nash_mixed.py
├── dominance.py
├── iterated_dominance.py
├── rationalizability.py
├── correlated_equilibrium.py
├── coarse_correlated.py
├── spe_backward_induction.py
├── perfect_equilibrium.py
├── repeated_games.py
├── stochastic_games.py
├── bne_template.py
├── pbe_template.py
├── signaling_screening.py
├── mechanism_design.py
├── characteristic_function.py
├── core_solution.py
├── shapley_value.py
├── nucleolus.py
├── power_indices.py
├── ntu_games.py
├── replicator_dynamics.py
├── best_response_dynamics.py
├── imitation_dynamics.py
├── ess_analysis.py
├── spatial_evolutionary.py
├── prisoners_dilemma.py
├── coordination_game.py
├── hawk_dove.py
├── public_goods.py
├── ultimatum_dictator.py
├── auctions.py
├── bayesian_persuasion.py
├── stackelberg.py
├── blotto.py
├── myerson_optimal.py
├── combinatorial_auction.py
├── matching_mechanisms.py
├── public_project_mechanisms.py
├── robust_mechanism.py
├── nash_nashpy.py
├── nash_gambit.py
├── axelrod_tournament.py
├── egta_analysis.py
├── openspiel_rl.py
└── marl_training.py
```

---

## 10. 选型决策树 (博弈论类)

```
参与者/信息结构？
├─ 单阶段、完全信息、少人数 → 矩阵博弈 → 纳什均衡/优势策略/相关均衡 → 首选
├─ 多阶段、完全信息、序贯动作 → 树形博弈 → SPE/逆向归纳 → 首选
├─ 类型私有、同时动作 → 贝叶斯博弈 → BNE → 首选
├─ 类型私有、序贯动作/信号 → 信号/筛选/PBE → 首选
├─ 可转移效用、联盟形成 → 合作博弈 → 核/夏普利值/Nucleolus → 首选
├─ 种群/长期演化/学习 → 演化博弈 → 复制子/ESS/网络演化 → 首选
├─ 机制/规则设计者 → 机制设计 → IC/IR/收入等价/最优拍卖/VCG → 首选
├─ 拍卖/分配/匹配市场 → 拍卖理论/匹配机制 → 收入最大化/效率/稳定性 → 首选
└─ 复杂/大规模/仿真估计 → EGTA/模拟/强化学习 → 进阶
```

**铁律**：
- 博弈模型 **必须明确：参与者、策略空间、信息结构、收益函数、时序**
- 纳什均衡 **必须验证存在性 (Nash 定理: 有限博弈必存混合 NE) 并给出计算方法**
- 多重均衡 **必须给出精炼/选择依据** (SPE/PBE/风险占优/焦点/前瞻稳定性)
- 演化模型 **必须相图/分析稳定性/给出 ESS 条件**
- 机制设计 **必须检查 IC/IR/预算平衡/可行性**，并对比基线

---

## 11. 竞赛实战提示

| 竞赛 | 题型 | 推荐首选 | 避坑指南 |
|------|------|----------|----------|
| CUMCM E | 多利益相关者评价/分配 | 合作博弈 (Shapley/核) / 机制设计 | 收益分配公平性、IC/IR 验证 |
| MCM F | 政策/机制设计 | 信号/筛选/拍卖/VCG/鲁棒机制 | 激励相容性证明、预算平衡 |
| 电工杯 | 电力市场/需求响应 | Stackelberg/拍卖/均衡计算 | 物理约束嵌入收益、市场出清 |
| 通用 | 多方谈判/利益分配 | 纳什谈判解/夏普利值/序贯博弈 | 威胁点合理、公平公理 |

---

*版本：1.0 | 更新：2026-09-01 | 维护：Modeler 手*