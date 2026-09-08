# PART D: Method Card Candidates — 候选方法卡

> **综合代理**：Research-layer Calibration 综合代理
> **日期**：2026-09-08
> **声明**：本文件仅生成候选方法卡内容，不修改现有 `core/knowledge/methods/cards/` 下任何 YAML 文件
> **治理原则**：方法卡 = Constraint/Prior/Validation，不是答案库
> **status 枚举**：NEW / RETRO-TAG / REVISE

---

## 0. 候选卡总览

| ID | name | family | layer_coverage | status | 优先级 |
|---|---|---|---|---|---|
| mc-dp | 动态规划与MDP | dynamic_programming | L2 decision_state_transition + L3 optimization + L4 DP_and_MDP | NEW | P0 |
| mc-numerical-pde | PDE数值求解 | numerical_pde | L2 conservation_law/spatial_temporal_field + L3 PDE + L4 numerical_PDE | NEW | P0 |
| mc-queuing-theory | 排队论分析 | queuing_theory | L2 queue + L3 probability_and_stochastic + L4 analytical_methods/simulation | NEW | P0 |
| mc-game-theory | 博弈论与均衡分析 | game_theory | L2 interaction_game + L3 optimization/probability/ODE + L4 analytical_methods/simulation | NEW | P1 |
| mc-network-flow | 网络流优化 | network_flow | L2 flow_balance + L3 graph/optimization + L4 graph_algorithm/exact_optimizer | NEW | P1 |
| mc-milp | 混合整数规划 | exact_optimization | L2 resource_constraint + L3 optimization + L4 exact_optimizer | NEW | P1 |
| mc-ode-modeling | ODE建模与数值求解 | ode_modeling | L2 conservation_law/geometric_constraint + L3 ODE + L4 numerical_ODE | NEW | P1 |
| mc-ga | 遗传算法（RETRO-TAG） | metaheuristic_optimization | L3 optimization + L4 metaheuristic_optimization | RETRO-TAG | P0 |
| mc-pso | 粒子群优化（RETRO-TAG） | metaheuristic_optimization | L3 optimization + L4 metaheuristic_optimization | RETRO-TAG | P0 |
| mc-sa | 模拟退火（RETRO-TAG） | metaheuristic_optimization | L3 optimization + L4 metaheuristic_optimization | RETRO-TAG | P0 |
| mc-monte-carlo | 蒙特卡洛模拟（REVISE） | uncertainty_propagation | L1 [属性]stochastic + L3 probability + L4 monte_carlo | REVISE | P1 |

---

## 1. NEW 候选卡

### 1.1 mc-dp（动态规划与MDP）— P0

```yaml
id: mc-dp
name: 动态规划与马尔可夫决策过程
family: dynamic_programming
layer_coverage:
  l1_problem_structures: [scheduling, supply_chain/operations, competition/game]
  l2_modeling_patterns: [decision_state_transition, resource_constraint]
  l3_formulations: [optimization, probability_and_stochastic, graph]
  l4_solver_type: [DP_and_MDP]
problem_types:
  - 多阶段序贯决策
  - 资源约束下的序列优化
  - 背包问题
  - 最短路径（DAG/Bellman-Ford）
  - 库存控制
  - 设备更新
  - 随机动态规划（MDP）
modeling_patterns:
  - Bellman最优性原理
  - 最优子结构 + 重叠子问题
  - 无后效性/马尔可夫性
  - 状态-动作-转移-奖励五元组
formulations:
  - 确定性DP: V_t(s) = max_a {r_t(s,a) + V_{t+1}(s')}
  - 随机MDP: V*(s) = max_a {R(s,a) + γ·Σ_{s'} P(s'|s,a)·V*(s')}
  - 动作价值: Q*(s,a) = R(s,a) + γ·Σ_{s'} P(s'|s,a)·V*(s')
solvers:
  - 值迭代（Value Iteration）
  - 策略迭代（Policy Iteration）
  - 自底向上表格递推（Tabulation）
  - 自顶向下记忆化递归（Memoization）
  - Dijkstra（非负权图特殊DP）
requires:
  - 问题可划分为多阶段序贯决策
  - 状态空间有限或可离散化（多项式级可管理）
  - 最优子结构可证明（cut-and-paste论证）
  - 无后效性成立（当前状态包含所有决策相关历史信息）
  - 重叠子问题存在（递归求解中反复访问相同子问题）
good_for:
  - 资源约束下的多阶段决策（如2020_B穿越沙漠）
  - 背包类问题（0-1背包/多维背包）
  - DAG上的最短路径
  - 多周期生产-库存决策（Wagner-Whitin）
  - 小型项目调度（RCPSP，状态=已完成活动集合）
  - 随机环境下的序贯决策（MDP值迭代）
bad_for:
  - 状态空间爆炸（维数灾难：多维资源状态导致10^20状态）
  - 无最优子结构（博弈均衡问题不由子博弈最优简单构成）
  - 连续状态/动作空间（需离散化或用变分法/最优控制/RL）
  - 后效性无法消除（历史影响无法压缩到当前状态）
  - 问题规模过大（即使多项式但n太大）
  - 实时性要求高（DP离线计算完整策略表）
  - 单阶段静态优化（应直接用optimization/MILP）
risks:
  - 状态定义不完整（最常见错误：遗漏关键状态变量导致马尔可夫性不成立）
  - 状态维度过高（维数灾难）
  - 转移方程错误（未正确建模动作对状态的影响）
  - 忽略动作空间约束（天气/资源限制下某些动作不可行但未排除）
  - 边界条件错误（终端奖励/初始状态设定错误）
  - 将DP当黑盒（只写代码不验证最优子结构）
  - 连续变量不离散化（直接对连续资源量做DP导致状态空间不可数）
  - 混淆DP formulation（L3 Bellman方程）与DP algorithm（L4值迭代/表格递推）
validation:
  - 最优子结构证明（cut-and-paste论证：假设子问题非最优，替换后矛盾）
  - 小规模brute-force对比（n≤10时枚举所有策略对比DP结果，DP结果=枚举最优值）
  - 收敛性检验（值迭代/策略迭代的||V_{k+1}-V_k||_∞ < 1e-6）
  - 策略可行性检验（DP输出策略满足所有约束：资源不耗尽、天气规则遵守、到达终点）
  - 回溯一致性（从DP表回溯最优策略，手动模拟验证累积奖励=DP表最优值）
  - 下界验证（用松弛问题的最优值作为下界，DP最优值≥松弛下界）
  - 多种子/多实例稳定性（对不同参数实例运行DP，检查结果合理性）
evidence:
  - discrete_optimization §4.1 (Bellman原理/最优子结构/重叠子问题/无后效性/6条适用+6条不适用+8类常见错误)
  - discrete_optimization §6.1 (2020_B穿越沙漠: DP/MDP核心求解器, 当前无DP卡导致LLM误选mc-ga)
  - taxonomy §4.2.2 (36题variants中DP 1次, MDP 2次; CUMCM-HMML子领域2.3)
  - Bellman R. Dynamic Programming. Princeton University Press, 1957
  - Stanford CS 161, Princeton COS 226, IEEE Technology Navigator
  - audit §4.1 (2020_B method_selection=0根因: L4 DP 0卡 + L2 decision_state_transition无标签)
status: NEW
```

---

### 1.2 mc-numerical-pde（PDE数值求解）— P0

```yaml
id: mc-numerical-pde
name: 偏微分方程数值求解
family: numerical_pde
layer_coverage:
  l1_problem_structures: [diffusion/heat_transfer, continuous_mechanics, network/traffic]
  l2_modeling_patterns: [conservation_law, spatial_temporal_field, inverse_problem]
  l3_formulations: [PDE, optimization]
  l4_solver_type: [numerical_PDE]
problem_types:
  - 热传导/扩散问题
  - 流体力学（Navier-Stokes）
  - 弹性力学/结构力学
  - 波动/振动
  - 交通流宏观模型（LWR）
  - 污染物扩散
modeling_patterns:
  - 守恒律（积分形式→微分形式）
  - 时空场（u(x,t) + 初始条件 + 边界条件）
  - 本构定律（Fourier/Fick/牛顿粘性）
  - 多层介质界面条件（温度连续+热流连续）
formulations:
  - 通用守恒形式: ∂u/∂t + ∇·F(u) = S(u)
  - 热方程: ∂u/∂t = α∇²u + S
  - 波动方程: ∂²u/∂t² = c²∇²u
  - Laplace/Poisson: ∇²u = 0 / ∇²u = f
  - 边界条件: Dirichlet (u=g), Neumann (∂u/∂n=g), Robin (αu+β∂u/∂n=g)
solvers:
  - 有限差分法（FDM）：竞赛首选，实现简单
    - 显式Euler (FTCS)：条件稳定（r=αΔt/Δx²≤0.5）
    - 隐式Euler (BTCS)：无条件稳定
    - Crank-Nicolson：无条件稳定+二阶精度，热传导首选
    - Du Fort-Frankel：无条件稳定（2018_A优秀论文使用）
    - ADI（交替方向隐式）：二维/三维抛物型问题
  - 有限元法（FEM）：复杂几何，竞赛中极少使用
  - 有限体积法（FVM）：守恒性优，流体/多物理场
requires:
  - 问题可表述为PDE（守恒律+本构定律+时空场）
  - 边界条件和初始条件可定义
  - 计算域可离散化（结构化网格FDM或非结构化网格FEM/FVM）
  - 介质属性（热导率/扩散系数）已知或可反演
good_for:
  - 热传导/扩散问题（2018_A高温服装, 2020_A回流焊）
  - 一维/二维规则网格的抛物型/椭圆型PDE
  - 多层介质的界面条件建模
  - 参数反演（PDE约束优化）
bad_for:
  - 集中参数系统（应归ODE）
  - 纯离散/调度问题（无连续场）
  - 复杂三维几何（FEM实现复杂度过高，竞赛时间不现实）
  - 几何尺寸极小（热传导极快，可近似为集中参数）
  - 纯运动学问题（不涉及力/场，应归kinematics simulation）
risks:
  - 边界条件类型错误（将对流当Dirichlet）
  - 多层介质界面条件缺失（温度连续+热流连续）
  - 数值不稳定（显式格式违反CFL条件r≤0.5）
  - 网格分辨率不足（边界层/界面处需加密）
  - 源/汇项遗漏（化学反应/内热源）
  - 将守恒律当PDE（混淆L2建模机理和L3数学表述）
  - FEM在竞赛中过度复杂（一维/简单二维问题FDM足够）
  - 忽略反问题的不适定性（参数反演需正则化）
validation:
  - 网格收敛性测试（Δx减半、Δt减半，关键输出变化<1%或符合理论收敛阶）
  - 守恒量检查（无源项时总能量/总质量守恒，变化<2%）
  - 与解析解对比（简单情形：半无限大物体/稳态线性分布，相对误差<1%）
  - 物理合理性检查（温度在边界值之间、单调趋近稳态）
  - 参数敏感性（扰动输入参数±10%，输出变化平滑无突变）
  - 多种子/多格式对比（用两种不同差分格式求解同一问题，结果一致）
  - Lax等价定理验证（一致性+稳定性⟺收敛性，线性问题）
evidence:
  - continuous_physics §4 (FDM/FEM/FVM九维对比, Lax等价定理, Crank-Nicolson, 6种时间积分方法)
  - continuous_physics §6.1 (2018_A: 四层一维非稳态热传导PDE + Du Fort-Frankel格式 + 最小二乘反演)
  - continuous_physics §6.3 (2020_A: 一维非稳态热传导+对流辐射边界)
  - taxonomy §4.2.1 (36题variants中finite_difference 3次, finite_element 3次)
  - Lax Equivalence Theorem (Semantic Scholar): "For a consistent linear approximation, stability is the necessary and sufficient condition for convergence"
  - UC Davis Math PDE Notes (Hunter): 热传导方程由能量守恒+Fourier定律导出
  - audit §4.1 (2018_A method_selection=0根因: L4 numerical PDE 0卡 + L1 diffusion 0卡 + L2 conservation_law/spatial_temporal_field 0卡)
status: NEW
```

---

### 1.3 mc-queuing-theory（排队论分析）— P0

```yaml
id: mc-queuing-theory
name: 排队论与随机服务系统分析
family: queuing_theory
layer_coverage:
  l1_problem_structures: [network/traffic, scheduling]
  l2_modeling_patterns: [queue, flow_balance]
  l3_formulations: [probability_and_stochastic, optimization]
  l4_solver_type: [analytical_methods, simulation, monte_carlo]
problem_types:
  - 随机服务系统（到达-等待-服务-离开）
  - 机场/车站出租车调度
  - 通信网络拥塞
  - 生产线节拍平衡
  - 服务台排班/容量规划
  - 库存系统（需求到达+补货服务）
modeling_patterns:
  - 到达过程（泊松到达/指数间隔/一般分布）
  - 服务过程（指数服务/一般服务时间）
  - 排队规则（FIFO/优先级/LIFO）
  - 服务台数量（单服务台/多服务台）
  - 系统容量（无限/有限）
formulations:
  - Kendall记号: A/B/c/K/m/Z
  - M/M/1: ρ=λ/μ, P₀=1-ρ, L=ρ/(1-ρ), W=1/(μ-λ)
  - M/M/c: P₀=[Σ_{k=0}^{c-1}(cρ)^k/k! + (cρ)^c/(c!(1-ρ))]⁻¹, L_q=P₀(cρ)^cρ/(c!(1-ρ)²)
  - M/G/1 (Pollaczek-Khinchine): L_q = [λ²Var(S)+(λE[S])²]/[2(1-λE[S])]
  - Little's Law: L=λW（模型无关，适用于任何稳定排队系统）
  - 生灭过程稳态方程: λ_n P_n = μ_{n+1} P_{n+1}
solvers:
  - 解析求解：M/M/1, M/M/c, M/G/1, M/M/1/K闭式公式
  - 近似公式：G/G/1的Kingman界
  - 排队网络：Jackson定理（产品形式解）
  - 离散事件仿真（DES）：SimPy/自定义，复杂系统
  - 蒙特卡洛仿真：随机抽样到达和服务时间
requires:
  - 到达和服务具有随机性（非确定性）
  - 存在"等待"现象（服务能力不足时顾客排队）
  - 关注稳态性能指标（平均等待时间/队列长度/利用率）
  - 系统可近似为Markov过程（指数分布假设合理），或可用仿真处理一般分布
good_for:
  - 随机服务系统分析（2019_C机场出租车）
  - 服务台容量规划（需要多少服务台使等待时间<阈值）
  - 系统利用率与等待时间的权衡分析
  - 简单排队网络（Jackson网络）
  - 泊松到达+指数服务的标准场景（M/M/c闭式解）
bad_for:
  - 纯确定性调度（无随机到达，如生产线节拍固定）
  - 服务时间高度非平稳（到达率随时间剧烈变化，需非稳态排队或仿真）
  - 顾客行为复杂（批量到达/放弃/重试/优先级动态变化）
  - 强相关的到达/服务过程（非独立同分布）
  - 纯流量平衡问题（无等待/随机，应归network_flow）
risks:
  - 泊松到达假设不满足（机场到达有航班批次性，非平稳）
  - 忽略顾客放弃行为（实际系统中等待过久的顾客会离开）
  - ρ→1时解析解不稳定（利用率接近1时等待时间趋于无穷）
  - 有限容量系统的拒绝概率未建模
  - 将排队论当仿真（M/M/c公式是稳态解析，不是仿真）
  - 忽略排队规则的影响（优先级队列与FIFO有不同的等待时间分布）
  - 仿真warm-up period未删除（初始瞬态数据污染稳态统计）
validation:
  - 分布拟合检验（χ²检验或K-S检验验证到达间隔是否为指数分布）
  - Little's Law验证（仿真输出的L、λ、W是否满足L=λW）
  - 解析-仿真对比（在简单场景下对比解析公式与仿真结果）
  - 灵敏度分析（扰动λ和μ，观察指标变化是否符合理论预期，如ρ→1时W→∞）
  - 稳态检验（确认仿真运行足够长时间达到稳态，warm-up period分析）
  - 多次独立运行（≥5次，种子固定为42及变体），报告均值±标准差
  - 置信区间报告
evidence:
  - network_game §2.2 (Kendall记号, Little定理, M/M/c/M/G/1公式, 解析vs仿真选择边界)
  - network_game §4.2 (排队求解器: 解析求解+仿真求解, warm-up period, 多次运行)
  - network_game §6.1 (2019_C机场出租车: M/M/c排队模型+司机决策博弈)
  - taxonomy §2.2.6 (2019_C典型排队论; 高教社教材设"排队论"独立章节; CUMCM-HMML子领域5.3)
  - Kendall D.G. (1953) "Stochastic processes occurring in the theory of queues"
  - Little J.D.C. (1961) "A proof for the queuing formula L=λW" Operations Research
  - Cooper R.B. Introduction to Queueing Theory. North-Holland, 1981
  - audit §4.2 (2019_C method_selection=100是假阳性: 无queuing_theory卡, mc-monte-carlo只是"用仿真近似排队")
status: NEW
```

---

### 1.4 mc-game-theory（博弈论与均衡分析）— P1

```yaml
id: mc-game-theory
name: 博弈论与均衡分析
family: game_theory
layer_coverage:
  l1_problem_structures: [competition/game, network/traffic]
  l2_modeling_patterns: [interaction_game, resource_constraint, decision_state_transition]
  l3_formulations: [optimization, probability_and_stochastic, ODE]
  l4_solver_type: [analytical_methods, simulation, monte_carlo]
problem_types:
  - 多玩家策略互动（收益交叉依赖）
  - 定价博弈/寡头竞争
  - 公共资源博弈（公地悲剧）
  - 交通分配（用户均衡Wardrop UE=Nash均衡）
  - 拍卖/机制设计
  - 稳定匹配（Gale-Shapley）
  - 演化博弈/合作演化
  - 多玩家穿越沙漠（2020_B Q3）
modeling_patterns:
  - 策略互动（固定他方策略时本方最优解是否变化）
  - 收益交叉依赖（u_i依赖所有玩家策略组合）
  - 均衡概念（Nash/ESS/子博弈精炼/Core）
  - 信息结构（完全/不完全、完美/不完美）
formulations:
  - 标准式博弈: G=(N, {S_i}, {u_i}), Nash均衡: u_i(s_i*,s_{-i}*)≥u_i(s_i,s_{-i}*) ∀i,s_i
  - 扩展式博弈: 博弈树+信息集，逆向归纳法求子博弈精炼Nash均衡
  - 混合策略: σ_i∈Δ(S_i), 期望收益u_i(σ)=Σ_{s∈S} (Π_j σ_j(s_j))·u_i(s)
  - 合作博弈: 特征函数v(S), Shapley值 φ_i(v)=Σ_{S⊆N\{i}} |S|!(n-|S|-1)!/n!·[v(S∪{i})-v(S)]
  - 演化博弈: 复制子动力学 dx_i/dt = x_i(f_i(x)-φ(x))
  - Nash均衡↔互补问题(NCP)/变分不等式(VI)
solvers:
  - 支持枚举法（两人有限博弈，枚举所有可能支持集解线性方程组）
  - 迭代删除劣策略（IESDS）
  - 最优反应动态（势博弈收敛到纯策略Nash）
  - 虚构博弈（Fictitious Play）
  - 逆向归纳法（扩展式博弈）
  - 同伦延拓法（一般有限博弈）
  - Gale-Shapley算法（稳定匹配，O(n²)）
  - 复制子动力学数值积分（演化博弈）
  - 蒙特卡洛模拟（策略评估/随机博弈）
requires:
  - ≥2个独立决策主体（players/agents）
  - 收益函数具有交叉依赖性（payoff interdependence）
  - 可定义策略空间和收益函数
  - 判定测试通过：固定其他主体策略时，本主体最优解会随其他主体策略变化而变化
good_for:
  - 多玩家竞争/合作（2020_B Q3多玩家穿越沙漠）
  - 交通分配用户均衡（Wardrop UE=Nash均衡，Braess悖论分析）
  - 定价博弈/寡头竞争
  - 公共资源博弈（公地悲剧/资源外部性）
  - 拍卖设计/机制设计（激励相容）
  - 稳定匹配（双边匹配Gale-Shapley）
  - 演化博弈/合作演化（复制子动力学+ESS）
bad_for:
  - 单玩家优化（其他主体只是外部环境参数，应归optimization/MILP）
  - 多主体但无策略互动（如多个独立库存优化，需求互不影响，仍是多个optimization并行）
  - 单主体面对随机环境（MDP，是optimization随机优化，不是game）
  - 先到先得的资源分配（可能是queue+optimization，不一定是game）
  - 大规模博弈的精确Nash求解（PPAD-complete，n≥3时计算不可行，需近似方法）
risks:
  - 误将单玩家优化当博弈（其他主体行为可视为固定外部环境时不是博弈）
  - 多均衡选择问题（多个Nash均衡时如何选择，payoff dominance/risk dominance/focal point）
  - 收益矩阵设定无依据（博弈的关键输入是收益函数，需有数据/理论支撑）
  - 有限理性假设下Nash不适用（实际玩家可能不理性，需演化博弈/有限理性模型）
  - 计算复杂度（一般Nash均衡求解是PPAD-complete，大规模需近似）
  - 忽略信息结构（完全信息vs不完全信息对应不同均衡概念）
  - 将博弈论当优化（Nash均衡不是单目标最优，是互为最优反应）
validation:
  - 单边偏离检验（对求得的均衡，检查每个玩家是否有激励偏离）
  - 多均衡检测（用不同初始点/方法求解，确认是否找到所有均衡）
  - 稳定性分析（对演化博弈，分析均衡点的Jacobian矩阵特征值）
  - 与解析解对比（在可解析的简单博弈如囚徒困境上验证算法正确性）
  - 策略互动判定验证（固定他方策略，检查本方最优解是否变化）
  - 蒙特卡洛策略评估（多次模拟验证均衡策略的平均收益）
evidence:
  - network_game §1.2 (博弈论定义/分类体系/Nash均衡/合作博弈/机制设计)
  - network_game §2.3 (interaction_game判定测试/子模式/与optimization边界)
  - network_game §3.2 (game-theoretic formulation: 标准式/扩展式/特征函数/演化博弈, 与optimization/probability/ODE交叉)
  - network_game §4.3 (均衡求解算法: 支持枚举/IESDS/最优反应/虚构博弈/同伦延拓/Gale-Shapley/复制子动力学)
  - network_game §6.2 (2020_B Q3博弈部分: 多玩家策略互动+纳什均衡)
  - discrete_optimization §6.1 (2020_B Q3: k人同行消耗2k倍, k人同矿收益1/k→策略外部性)
  - taxonomy §2.2.8 (2020_B/2019_C/2025_D; CUMCM-HMML子领域6.3)
  - Nash J.F. (1950) "Equilibrium points in n-person games" PNAS
  - Gibbons R. Game Theory for Applied Economists. Princeton University Press, 1992
  - Braess D. (1968) "Über ein Paradoxon aus der Verkehrsplanung"（交通网络博弈经典反直觉结果）
  - audit §4.1 (2020_B method_selection=0根因: L4 game theory 0卡 + L2 interaction_game 0卡)
status: NEW
```

---

### 1.5 mc-network-flow（网络流优化）— P1

```yaml
id: mc-network-flow
name: 网络流与图优化
family: network_flow
layer_coverage:
  l1_problem_structures: [network/traffic, supply_chain/operations, scheduling]
  l2_modeling_patterns: [flow_balance, resource_constraint]
  l3_formulations: [graph, optimization]
  l4_solver_type: [graph_algorithm, exact_optimizer]
problem_types:
  - 最短路径（路径规划/导航）
  - 最大流/最小割（网络容量分析）
  - 最小费用流（物流配送/供应链）
  - 交通分配（用户均衡/系统最优）
  - 最小生成树
  - 二部图匹配/稳定匹配
  - 网络设计（拓扑/容量扩展）
modeling_patterns:
  - 节点流量平衡（除源汇外净流为零）
  - 边容量约束（0≤f_ij≤c_ij）
  - 源汇设定/OD对
  - 拥堵扩展（边的旅行时间是流量的函数，BPR函数）
formulations:
  - 流量平衡: Σ_{j:(j,i)∈E} f_{ji} - Σ_{j:(i,j)∈E} f_{ij} = b_i, ∀i∈V
  - 最大流: max |f| s.t. 0≤f_ij≤c_ij + 流量平衡
  - 最小费用流: min Σc_ij f_ij s.t. 容量约束 + 流量平衡 + 供需约束
  - 最短路LP: min Σc_ij x_ij s.t. 流量平衡约束
  - 最大流-最小割定理: max flow = min cut capacity
solvers:
  - 最短路径: Dijkstra（非负权）, Bellman-Ford（负权）, Floyd-Warshall（全源）, A*（启发式）
  - 最大流: Ford-Fulkerson, Edmonds-Karp（BFS）, Dinic（BFS分层+DFS阻塞流）, Push-Relabel
  - 最小费用流: 连续最短路法, 消圈法, 网络单纯形法
  - 最小生成树: Kruskal, Prim
  - 匹配: 匈牙利算法, Gale-Shapley
  - 交通分配: Frank-Wolfe（用户均衡UE）, MSA, 系统最优SO
requires:
  - 问题可表述为节点-边网络（图结构明确）
  - 流量有容量约束或费用结构
  - 存在源点/汇点或OD对
good_for:
  - 路径规划/导航（最短路径）
  - 网络容量分析（最大流/最小割）
  - 物流配送/供应链优化（最小费用流）
  - 交通分配（用户均衡Wardrop UE）
  - 任务分配/匹配（二部图匹配/稳定匹配）
  - 网络设计（拓扑/容量扩展）
bad_for:
  - 无图结构的问题（纯连续/纯统计）
  - 纯排队问题（无流量平衡，应归queuing_theory）
  - 纯调度问题（无网络流结构，应归scheduling/MILP）
  - 动态图（边/节点随时间变化，需动态图算法或仿真）
  - 大规模网络的精确最大流（需近线性算法或近似）
risks:
  - 负权环（Bellman-Ford检测，Dijkstra不适用）
  - 图规模过大导致内存/时间不足
  - 边权重/容量估计错误
  - 忽略拥堵效应（交通分配中边权不随流量变化，应使用BPR函数）
  - 整数流假设（实际流量可能是连续的，最大流整数性仅在整数容量时成立）
  - 将flow_balance当conservation_law（连续场微分守恒vs离散网络代数平衡，二者不同）
validation:
  - 对偶验证（最大流=最小割，检查割容量）
  - 流量守恒检验（每个中间节点净流入=0）
  - 容量约束检验（每条边流量≤容量）
  - 与LP解对比（小规模问题用exact_optimizer验证）
  - 路径可行性检验（最短路径的每条边存在且权重正确）
  - Braess悖论检验（增加道路是否可能降低整体效率，交通网络博弈）
evidence:
  - network_game §1.1 (网络问题核心机理: 拓扑约束下的流动与分配, 5种典型子问题)
  - network_game §2.1 (flow_balance定义/与conservation_law区别/扩展形式)
  - network_game §4.1 (flow algorithms: 最短路径/最大流/最小费用流/交通分配算法详细分类)
  - discrete_optimization §3.1 (graph独立数学范式, 图论问题不一定是优化问题, 独立算法体系)
  - taxonomy §4.3.5 (36题variants中BFS/Dijkstra/A*出现在2025_D; CUMCM-HMML领域4.1)
  - Ahuja R.K., Magnanti T.L., Orlin J.B. Network Flows: Theory, Algorithms, and Applications. Prentice Hall, 1993
  - Ford L.R., Fulkerson D.R. (1956) "Maximal flow through a network"
  - Sheffi Y. Urban Transportation Networks: Equilibrium Analysis with Mathematical Programming Methods. Prentice-Hall, 1985
  - Braess D. (1968) 交通网络博弈经典反直觉结果
status: NEW
```

---

### 1.6 mc-milp（混合整数规划）— P1

```yaml
id: mc-milp
name: 混合整数线性规划
family: exact_optimization
layer_coverage:
  l1_problem_structures: [scheduling, supply_chain/operations, decision_evaluation]
  l2_modeling_patterns: [resource_constraint, flow_balance]
  l3_formulations: [optimization, graph]
  l4_solver_type: [exact_optimizer]
problem_types:
  - 调度问题（任务-机器指派/排序，0-1变量）
  - 资源分配（背包/多维背包/选址）
  - 供应链优化（多周期生产-库存-运输）
  - 网络设计（拓扑/容量扩展，0-1选址变量）
  - 生产计划（产能/批量/班次）
  - 组合优化（旅行商/集合覆盖）
modeling_patterns:
  - 资源约束（容量/预算/时间窗/人力）
  - 离散决策（0-1变量：是否选择/是否指派/是否开工）
  - 线性目标+线性约束
  - 大M法（线性化逻辑约束/析取约束）
formulations:
  - 标准形式: min cᵀx + dᵀy s.t. Ax + By ≤ b, x∈ℤⁿ, y≥0
  - 0-1指派: x_ij∈{0,1}, Σ_j x_ij=1（每个任务指派一台机器）
  - 析取约束（调度资源互斥）: s_{i,j}+p_{i,j}≤s_{i',j}+M(1-x_{(i,j),(i',j)}), s_{i',j}+p_{i',j}≤s_{i,j}+M·x_{(i,j),(i',j)}
  - 背包: Σw_i x_i ≤ W, max Σv_i x_i, x_i∈{0,1}
solvers:
  - 商业: Gurobi, CPLEX（IBM）
  - 开源学术: SCIP, CBC (COIN-OR), HiGHS
  - Python内置: scipy.optimize.milp（基于HiGHS，中小规模）
  - 建模语言: PuLP, Pyomo, cvxpy
  - 核心算法: 分支定界（B&B, Land and Doig 1960）+ 割平面（Cutting Planes）+ 启发式 + 预处理（Presolve）
requires:
  - 目标函数和约束可线性化（或可合理线性近似）
  - 离散决策可表示为整数/0-1变量
  - 模型规模在求解器能力范围内（变量数/约束数）
  - 大M常数取值合理（不过大导致数值不稳定，不过小导致约束失效）
good_for:
  - 结构化线性/整数约束问题（调度/资源分配/供应链）
  - 中小规模（变量数/约束数在求解器能力范围内）
  - 需要全局最优性保证的场景
  - 有明确数学规划模型的问题
  - 0-1指派/背包/选址问题
  - 多周期生产-库存-运输联合优化
bad_for:
  - 大规模NP-hard问题（求解时间指数增长，需metaheuristic）
  - 黑盒目标函数（无梯度信息，需metaheuristic/simulation）
  - 高度非线性/非凸问题（全局最优困难，需NLP求解器或全局优化）
  - 实时性要求高的场景（求解时间不可控）
  - 纯连续线性规划（LP，不需要整数变量，求解更简单）
  - 纯非线性规划（NLP，应归NLP求解器）
risks:
  - 大M取值不当导致数值不稳定或约束失效
  - 非线性约束未线性化导致MILP模型错误
  - 变量过多导致求解超时（需分解/聚合/启发式）
  - 整数约束导致非凸性（LP松弛界宽松）
  - 数值精度问题（接近0的约束被违反）
  - 模型规模估计不足（实际求解时间远超预期）
  - 将MILP求解器当建模方法（建模核心是决策变量定义+约束线性化+目标构造，不是调用求解器）
validation:
  - 最优性间隙检查（MIPGap < 设定阈值，如1%）
  - 约束违反检查（所有约束满足，容差内）
  - 目标值下界验证（LP松弛是下界，MILP最优值≥LP松弛值）
  - 多种子/多求解器对比（不同求解器结果一致）
  - 小规模枚举验证（n≤10时枚举所有解对比）
  - 灵敏度分析（扰动目标系数/约束右端项，观察最优值变化）
  - 模型验证（与手工计算/已知最优解对比）
evidence:
  - discrete_optimization §1.3 (调度的整数规划表述: 大M析取约束, Dartmouth CO 454)
  - discrete_optimization §3.2 (数学规划层级: LP/NLP/IP/MILP, IP因整数约束引入非凸性)
  - discrete_optimization §4.2-4.3 (B&B由Land and Doig 1960提出; MILP求解器基于B&B+割平面+启发式+预处理; Gurobi/CPLEX/SCIP/CBC/scipy.milp)
  - discrete_optimization §6.2 (2018_B RGV调度: 0-1规划建模, 获奖论文使用)
  - taxonomy §4.3.1 (36题variants中LP 2次, IP 3次, 约束优化等共12次; CUMCM-HMML领域2.1/2.2)
  - IEEE Technology Navigator (Optimization Methods + Mathematical Programming)
  - Land H., Doig A.G. (1960) "An Automatic Method of Solving Discrete Programming Problems" Econometrica
  - arXiv 2511.09219 ("Modern MILP solvers are built upon the branch-and-bound (B&B) paradigm")
status: NEW
```

---

### 1.7 mc-ode-modeling（ODE建模与数值求解）— P1

```yaml
id: mc-ode-modeling
name: 常微分方程建模与数值求解
family: ode_modeling
layer_coverage:
  l1_problem_structures: [motion/geometry, continuous_mechanics, competition/game]
  l2_modeling_patterns: [conservation_law, geometric_constraint, decision_state_transition]
  l3_formulations: [ODE, optimization]
  l4_solver_type: [numerical_ODE, analytical_methods]
problem_types:
  - 运动学/动力学（牛顿第二定律/多体递推）
  - 振动分析（简谐/受迫/阻尼振动）
  - 静力平衡边值问题（悬链线/系泊系统）
  - 种群动力学（Lotka-Volterra/SIR模型）
  - 电路分析（RLC电路瞬态）
  - 演化博弈（复制子动力学）
  - 化学动力学（反应速率方程）
modeling_patterns:
  - 守恒律（动量/能量/质量守恒导出ODE）
  - 几何约束（刚体约束/变形约束导出代数方程或边值ODE）
  - 集中参数系统（状态由有限个变量描述）
  - 初值问题/边值问题
formulations:
  - 一阶ODE: dy/dt = f(t,y)
  - 二阶ODE: d²y/dt² = f(t,y,dy/dt)（牛顿第二定律m·x''=F）
  - 方程组: dY/dt = F(t,Y), Y∈ℝⁿ
  - 线性系统: dY/dt = AY + g(t)
  - 边值问题: y''=f(t,y,y'), y(a)=α, y(b)=β（悬链线方程）
  - 振动方程: m·x''+c·x'+k·x=F(t)
solvers:
  - 初值问题: Euler（显式/隐式）, Runge-Kutta（RK4）, odeint（LSODA自动刚性检测）, BDF（刚性问题）
  - 边值问题: 打靶法（Shooting）, 有限差分法, 配点法（Collocation）
  - 多体递推: 正向运动学递推（串行链逐节计算）
  - 解析解: 分离变量法/积分因子/特征值法（可积情形）
requires:
  - 系统可由有限个状态变量描述（集中参数假设）
  - 状态变量连续可微（光滑性假设）
  - 方程右端函数f满足Lipschitz条件（保证解的存在唯一性）
  - 初始条件或边界条件已知
good_for:
  - 集中参数系统的时间演化（运动学/动力学/振动）
  - 单自变量（通常时间）的演化问题
  - 初值问题或边值问题
  - 有明确力学/物理方程可推导的系统
  - 多体系统递推计算（板凳龙运动学）
  - 静力平衡边值问题（悬链线/系泊系统）
bad_for:
  - 分布参数系统（场变量依赖空间+时间，应归PDE）
  - 纯代数问题（无导数，应归optimization/linear_algebra）
  - 离散事件系统（状态在离散事件跳跃，应归simulation/queue）
  - 纯几何问题（无时间演化/无导数，应归geometric_constraint+linear_algebra）
  - 刚性问题用显式方法（需隐式BDF）
risks:
  - 刚性问题用显式方法导致不稳定（需BDF/隐式方法）
  - 初值敏感性（混沌系统：初值微小扰动导致解的巨大偏差）
  - 边值问题多解/无解
  - 数值耗散（数值方法引入的人工阻尼）
  - 步长过大导致精度不足或不稳定
  - 将ODE当PDE（集中参数vs分布参数混淆）
  - 多体递推中碰撞检测简化过度
validation:
  - 步长收敛性测试（h减半，关键输出变化<1%）
  - 守恒量检查（无源/汇时能量/质量守恒）
  - 与解析解对比（可积情形）
  - 平衡点稳定性分析（Jacobian矩阵特征值）
  - 刚体约束残差检查（多体系统：相邻间距≈d，误差<1e-6）
  - 初值敏感性分析（扰动初值±1%观察解的变化）
  - 多种求解器对比（RK4 vs odeint vs BDF结果一致）
evidence:
  - continuous_physics §3.2 (ODE与PDE本质区别表: 自变量数量/未知函数/解的几何/系统类型/定解条件/数值方法)
  - continuous_physics §3.4 (拆分PDE/ODE为独立L3标签的6项论据)
  - continuous_physics §4.7 (运动学数值求解与numerical PDE的本质区别表)
  - continuous_physics §6.2 (2024_A板凳龙: 多体递推+运动学ODE)
  - continuous_physics §6.4 (2016_A系泊: 悬链线边值ODE+静力平衡)
  - taxonomy §3.2.2 (36题中11题涉及DE, ODE用RK4, PDE用有限差分; CUMCM-HMML将1.1和1.2分为两个子领域)
  - taxonomy §4.3.2 (36题variants中Runge_Kutta 2次, multi_body_dynamics 2次)
  - IEEE Technology Navigator ("Distributed parameter systems... requiring PDEs rather than ODEs. In a lumped parameter system, the entire state is captured by a finite set of variables")
  - University of Alberta PDE Notes ("ODE solution is a curve, PDE solution is a surface/hypersurface")
status: NEW
```

---

## 2. RETRO-TAG 建议（现有卡重新标注四层标签）

### 2.1 mc-ga / mc-pso / mc-sa — 标注 metaheuristic_optimization

**现有状态**：三张卡的 family 分别为 metaheuristics，但 L4 标签体系中只有 `GA`，PSO/SA 无对应 L4 标签。

**RETRO-TAG 建议**：

| 字段 | 当前值 | 建议值 |
|---|---|---|
| family | metaheuristics | **metaheuristic_optimization** |
| l4_solver_type | （缺失） | **[metaheuristic_optimization]** |
| l3_formulations | （隐含optimization） | **[optimization]** |
| l1_problem_structures | （缺失） | **[scheduling, motion/geometry, diffusion/heat_transfer, supply_chain/operations]**（solver-agnostic，适用范围广） |
| l2_modeling_patterns | （缺失） | **[resource_constraint, geometric_constraint]**（solver-agnostic） |
| not_for | （缺失） | **小规模凸问题（应优先用exact_optimizer保证全局最优）; 需要精确最优性保证的场景** |

**理由**：
- GA/PSO/SA 共享同一求解范式：基于种群/邻域的随机搜索，不保证全局最优，需要多种子运行统计
- 原 L4 标签 `GA` 过于狭窄，PSO/SA 无家可归
- 统一为 `metaheuristic_optimization` 后，三张卡的 L4 归属明确
- 这三张卡是 solver-agnostic 的（可用于多种 L1/L2 问题），因此 l1/l2 标注应宽泛但需加 not_for 约束

**证据**：
- taxonomy §4.2.4 (36题variants中GA出现14次最高频; PSO 1次, tabu 1次, NSGA_II 1次; 16卡中有mc-ga/mc-pso/mc-sa三张元启发式卡)
- taxonomy §4.4 (metaheuristic作为L4一级标签替代原GA标签)
- discrete_optimization §4.4 (元启发式分类: 构造启发式/局部搜索/元启发式/超启发式)
- audit §2.2 (mc-pso/mc-sa是重要的元启发式求解器，但当前L4标签集未包含"metaheuristic optimization"类别)

---

### 2.2 mc-monte-carlo — REVISE（扩展 L4 标签归属）

**现有状态**：family=uncertainty_propagation，L4 标签为 Monte Carlo。

**REVISE 建议**：

| 字段 | 当前值 | 建议值 |
|---|---|---|
| l4_solver_type | Monte Carlo | **[monte_carlo, simulation]**（扩展：MC既可作为独立随机抽样方法，也可作为仿真的随机引擎） |
| l1_problem_structures | uncertainty（已降级） | **[属性] stochastic**（uncertainty降级为跨层属性后，MC适用于所有stochastic属性的问题） |
| l2_modeling_patterns | （缺失） | **[queue, decision_state_transition, interaction_game]**（MC常用于排队仿真/MDP策略评估/博弈策略评估） |
| l3_formulations | probability, statistics | **[probability_and_stochastic, statistics]** |
| not_for | （缺失） | **确定性系统的精确求解（应归exact_optimizer/numerical方法）; 需要解析解的场景** |

**理由**：
- uncertainty 从 L1 降级为跨层属性后，mc-monte-carlo 的 L1 归属需要调整
- Monte Carlo 不仅是不确定性传播方法，也是仿真（simulation）的随机引擎
- 在排队论/MDP/博弈中，MC 常用于策略评估和随机模拟

**证据**：
- taxonomy §1.2.7 (uncertainty降级为跨层属性)
- network_game §4.4 (simulation中Monte Carlo的角色: 随机抽样到达和服务时间)
- discrete_optimization §4.1 (MDP中Monte Carlo用于策略评估: 当状态空间过大或转移概率未知时)

---

### 2.3 其他现有卡的 RETRO-TAG 摘要

| Card | 当前 L4 | 建议 L4 | 建议 L2 | 变更原因 |
|---|---|---|---|---|
| mc-ols | regression | regression_and_supervised | statistical_association | L2新增statistical_association，OLS是核心回归方法 |
| mc-arima | regression | regression_and_supervised | temporal_recurrence | state_transition拆分为temporal_recurrence+decision_state_transition，ARIMA属temporal_recurrence |
| mc-grey-gm11 | regression | regression_and_supervised | temporal_recurrence | 同上，GM(1,1)是时序递推 |
| mc-lstm | regression | regression_and_supervised | temporal_recurrence | 同上，LSTM是时序深度学习 |
| mc-xgboost | regression | regression_and_supervised | statistical_association | XGBoost是监督学习（回归+分类），属statistical_association |
| mc-kmeans | clustering | clustering | statistical_association | 聚类是无监督学习，属statistical_association |
| mc-pca | （无L4标签） | dimensionality_reduction | statistical_association | L4新增dimensionality_reduction，PCA是核心降维方法 |
| mc-ahp | （无L4标签） | analytical_methods | geometric_constraint | AHP是闭式计算（特征向量法），属analytical_methods；距离/比较属geometric_constraint |
| mc-topsis | （无L4标签，原distance/geometry） | analytical_methods | geometric_constraint | TOPSIS是闭式计算（距离公式+排序），属analytical_methods；距离理想点属geometric_constraint |
| mc-entropy-weight | （无L4标签） | analytical_methods | statistical_association | 熵权法是闭式计算（熵公式+归一化），属analytical_methods |
| mc-fuzzy-evaluation | （无L4标签） | analytical_methods | statistical_association | 模糊综合评价是闭式计算，属analytical_methods |
| mc-nsga2 | GA | metaheuristic_optimization | resource_constraint | NSGA-II是多目标元启发式，属metaheuristic_optimization |

---

## 3. 候选卡优先级与实施建议

| 优先级 | 候选卡 | 理由 | 预期影响 |
|---|---|---|---|
| P0 | mc-dp | 2020_B method_selection=0直接原因; DP是离散优化域核心求解器; 当前完全缺失 | 解决2020_B路由失败 |
| P0 | mc-numerical-pde | 2018_A method_selection=0直接原因; PDE数值求解是连续物理域核心; 当前完全缺失 | 解决2018_A路由失败 |
| P0 | mc-queuing-theory | 2019_C假阳性根因（无排队论卡只用MC仿真近似）; 排队论是独立理论体系; 当前完全缺失 | 解决2019_C浅层命中 |
| P0 | RETRO-TAG (mc-ga/pso/sa) | L4标签体系从GA扩展为metaheuristic_optimization; 三张卡需重新标注 | 修复L4标签归属 |
| P1 | mc-game-theory | 2020_B Q3博弈部分; 博弈论是独立理论体系; 当前完全缺失 | 补充博弈分析能力 |
| P1 | mc-network-flow | 网络/交通问题核心求解器; graph L3零覆盖; 当前完全缺失 | 补充网络流分析能力 |
| P1 | mc-milp | 调度/资源分配标准精确求解工具; scipy内置可直接使用; 当前无对应卡 | 补充精确优化能力 |
| P1 | mc-ode-modeling | 2024_A运动学核心; ODE与PDE拆分后需独立卡; 当前无ODE卡 | 解决2024_A路由失败 |
| P1 | REVISE (mc-monte-carlo) | uncertainty降级后需调整L1归属; 扩展simulation标签 | 修复属性维度归属 |
| P2 | 其他卡RETRO-TAG | 16张卡全部重新标注四层标签 | 完善标签体系覆盖 |

---

*本文件为候选方法卡设计，不修改现有 core/knowledge/methods/cards/ 下任何 YAML 文件。所有候选卡基于4份领域研究报告的证据提取，经综合代理冲突裁决后形成自洽体系。候选卡需通过 Architecture Gate 审核后方可进入正式知识库。*
