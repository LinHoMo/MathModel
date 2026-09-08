# PART C: Knowledge Units — 新增知识单元定义集

> **综合代理**：Research-layer Calibration 综合代理
> **日期**：2026-09-08
> **基于**：4份领域研究报告的定义、机理、适用条件提取
> **覆盖**：所有新增的 L1/L2/L3/L4 知识单元

---

## L1 新增知识单元

### KU-L1-01: continuous_mechanics

```
id: KU-L1-01
name: continuous_mechanics（连续力学/振动/动力学）
layer: L1 Problem Structure
definition: 描述连续介质（刚体/弹性体/流体）在力作用下的平衡、变形、振动和运动动力学问题。核心是力平衡/力矩平衡/本构关系/运动方程，与纯运动学（不考虑力）有本质区别。
core_mechanism:
  - 静力平衡：ΣF=0, ΣM=0（力和力矩平衡）
  - 动力学：牛顿第二定律 m·d²x/dt² = F（或拉格朗日方程）
  - 本构关系：应力-应变关系（胡克定律等）
  - 振动：简谐振动/受迫振动/阻尼振动
typical_problem_structures:
  - 系泊系统静力平衡（锚链悬链线+浮体姿态）
  - 机械振动分析（车床振动、弹性梁振动）
  - 碰撞动力学（碰撞周期映射）
  - 结构变形/应力分析
mathematical_formulations:
  - ODE：牛顿第二定律 m·x'' + c·x' + k·x = F(t)（振动方程）
  - 代数方程：静力平衡 ΣF=0, ΣM=0
  - PDE：弹性力学方程（Navier方程）、波动方程
common_solvers:
  - numerical_ODE：RK4、odeint、打靶法（边值问题）
  - exact_optimizer：非线性方程求解（fsolve）
  - analytical_methods：解析解（简谐振动、悬链线方程）
  - numerical_PDE：有限元（复杂几何弹性问题）
good_for:
  - 涉及力/力矩/能量的物理系统
  - 振动/动力学/静力平衡问题
  - 有明确力学方程可推导的系统
bad_for:
  - 纯运动学问题（不涉及力，如板凳龙的位置递推）
  - 纯数据驱动问题（无力学机理）
  - 离散调度/博弈问题
assumptions:
  - 连续介质假设（物质连续分布，无微观间隙）
  - 小变形假设（线性弹性范围内）或大变形几何非线性
  - 材料本构关系已知或可假设
risks:
  - 忽略阻尼导致振动分析失真
  - 静力平衡假设不适用于动态过程
  - 本构关系选择错误（线性 vs 非线性）
  - 边界条件/约束条件遗漏
validation:
  - 能量守恒检查（无源/汇时总能量守恒）
  - 平衡残差检查（ΣF≈0, ΣM≈0）
  - 量纲一致性检查
  - 与解析解对比（简单情形）
  - 网格/步长收敛性测试（数值解）
relations:
  - L2: conservation_law（动量/能量守恒）, geometric_constraint（变形约束）
  - L3: ODE（运动方程）, PDE（弹性力学）, optimization（参数优化）
  - L4: numerical_ODE, exact_optimizer, analytical_methods
evidence:
  - taxonomy §1.3.1 (36题中4题: 2016_A, 2019_A, 2019_B, 2022_A)
  - CUMCM-HMML领域7.1"物理/力学建模"
  - continuous_physics §6.4 (2016_A系泊系统: 悬链线+静力平衡+多目标优化)
```

---

### KU-L1-02: supply_chain/operations

```
id: KU-L1-02
name: supply_chain/operations（供应链/运营管理）
layer: L1 Problem Structure
definition: 描述涉及多环节（采购-生产-库存-运输-配送）协调的运营管理问题。核心是多周期、多节点、多资源的协调优化，与单一场景的scheduling（如RGV调度）有不同的问题结构。
core_mechanism:
  - 库存平衡：库存_{t+1} = 库存_t + 生产_t - 需求_t
  - 产能约束：每期生产量 ≤ 产能上限
  - 运输约束：运输量 ≤ 运输能力，运输时间延迟
  - 多目标：成本最小化 + 服务水平最大化
typical_problem_structures:
  - 原材料订购与运输计划（多周期、多供应商）
  - 生产调度与库存协调
  - 供应链网络设计（选址+分配）
mathematical_formulations:
  - optimization：多周期混合整数规划（MILP）
  - graph：供应链网络（节点=工厂/仓库，边=运输路线）
  - DP formulation：多周期库存决策（Wagner-Whitin模型）
common_solvers:
  - exact_optimizer：MILP求解器（Gurobi/CPLEX/scipy.milp）
  - DP_and_MDP：多周期库存DP
  - metaheuristic_optimization：大规模问题的GA/SA
  - graph_algorithm：最小费用流
good_for:
  - 多环节、多周期的协调优化
  - 库存-生产-运输联合决策
  - 有明确成本结构和需求预测的运营问题
bad_for:
  - 单一场景的实时调度（应归scheduling）
  - 纯博弈问题（应归competition/game）
  - 无明确运营结构的通用优化问题
assumptions:
  - 需求可预测或已知分布
  - 成本结构稳定（采购/生产/运输/库存成本）
  - 供应链成员行为可预测（非策略性互动）
risks:
  - 需求预测误差导致库存积压或缺货
  - 忽略供应链中断风险
  - 模型规模过大导致求解超时
  - 多目标权重设定主观
validation:
  - 库存平衡约束验证（每期库存非负且满足平衡方程）
  - 产能约束验证
  - 成本核算验证（与手工计算对比）
  - 灵敏度分析（需求/成本扰动±10%）
relations:
  - L2: resource_constraint（产能/库存/预算）, flow_balance（物流平衡）, decision_state_transition（库存水平演化）
  - L3: optimization, graph, probability_and_stochastic
  - L4: exact_optimizer, DP_and_MDP, graph_algorithm, metaheuristic_optimization
evidence:
  - taxonomy §1.3.2 (36题中2题: 2021_C, 2024_C)
  - MCM/ICM D题定义为"Operations Research/Network Science"
  - CUMCM-HMML领域10"运筹与调度"
  - discrete_optimization §6.3 (2021_C供应链: 多周期生产-库存-配送)
```

---

## L2 新增知识单元

### KU-L2-01: decision_state_transition

```
id: KU-L2-01
name: decision_state_transition（决策状态转移/MDP）
layer: L2 Modeling Pattern
definition: 将问题建模为马尔可夫决策过程（MDP）或多阶段决策过程时，系统状态随决策动作演化的建模机理。核心是"动作驱动的状态演化 + 累积奖励优化"，与时序预测中的自治递推（temporal_recurrence）有本质区别。
core_mechanism:
  - MDP五元组：(S状态空间, A动作空间, P转移概率, R奖励函数, γ折扣因子)
  - Bellman最优性方程：V*(s) = max_a [R(s,a) + γ·Σ_{s'} P(s'|s,a)·V*(s')]
  - 马尔可夫性：给定当前状态，未来与过去条件独立
  - 确定性DP：V_t(s) = max_a [r_t(s,a) + V_{t+1}(s')]
typical_problem_structures:
  - 资源约束下的多阶段序贯决策（穿越沙漠：每日行动选择）
  - 动态调度（RGV实时调度：系统状态随加工完成事件演化）
  - 库存控制（多周期生产-库存决策）
  - 随机动态规划（天气随机下的行动决策）
mathematical_formulations:
  - optimization（Bellman方程作为递归优化表述）
  - probability_and_stochastic（转移概率矩阵）
  - graph（状态转移图：节点=状态，边=决策转移）
common_solvers:
  - DP_and_MDP：值迭代、策略迭代、自底向上表格递推、自顶向下记忆化
  - monte_carlo：策略评估（当状态空间过大或转移概率未知时）
  - simulation：滚动时域优化、强化学习
  - analytical_methods：小规模问题的解析解
good_for:
  - 多阶段序贯决策（按时间/逻辑顺序的决策序列）
  - 有限/可数状态空间（状态变量离散且数量可管理）
  - 满足最优子结构和无后效性的问题
  - 确定性或随机性的动态决策
bad_for:
  - 单阶段静态优化（应直接用optimization）
  - 连续状态/动作空间（需离散化或用变分法/最优控制）
  - 状态空间爆炸（维数灾难：多维资源状态导致10^20状态）
  - 后效性无法消除（历史影响无法压缩到当前状态）
  - 纯时序预测（无决策变量，应归temporal_recurrence）
assumptions:
  - 马尔可夫性成立（当前状态包含所有决策相关历史信息）
  - 状态空间有限或可离散化
  - 转移概率已知（随机性MDP）或转移确定（确定性DP）
  - 奖励函数可定义
risks:
  - 状态定义不完整导致马尔可夫性不成立（最常见错误）
  - 状态维度过高导致维数灾难
  - 转移方程错误（未正确建模动作对状态的影响）
  - 忽略动作空间约束（天气/资源限制下某些动作不可行但未排除）
  - 边界条件错误（终端奖励/初始状态设定错误）
validation:
  - 最优子结构证明（cut-and-paste论证）
  - 小规模brute-force对比（n≤10时枚举所有策略对比DP结果）
  - 收敛性检验（值迭代/策略迭代的价值函数变化<ε）
  - 策略可行性检验（DP输出策略满足所有约束）
  - 回溯一致性（从DP表回溯最优策略，手动模拟验证累积奖励=DP表最优值）
relations:
  - L1: scheduling, supply_chain/operations, competition/game
  - L3: optimization, probability_and_stochastic, graph
  - L4: DP_and_MDP, monte_carlo, simulation
  - 与temporal_recurrence的区别：decision_state_transition有决策变量a_t，temporal_recurrence是自治递推x_{t+1}=f(x_t)
evidence:
  - discrete_optimization §2.2 (MDP五元组, Bellman方程, 马尔可夫性)
  - discrete_optimization §4.1 (DP五要素: 阶段/状态/决策/转移/目标)
  - taxonomy §2.2.1 (拆分state_transition: 自治递推vs决策依赖)
  - Stanford CME 241, INRIA Lille, PKU BICMR讲义（MDP标准定义）
  - Bellman R. Dynamic Programming. Princeton University Press, 1957
```

---

### KU-L2-02: statistical_association

```
id: KU-L2-02
name: statistical_association（统计关联/数据驱动建模）
layer: L2 Modeling Pattern
definition: 通过统计方法（回归/分类/聚类/相关/降维）发现变量间关联关系的建模模式。这是与机理驱动建模（conservation_law/flow_balance）并列的两大建模范式之一。核心是从数据中提取模式，而非从物理第一性原理推导方程。
core_mechanism:
  - 回归：建立自变量→因变量的映射关系（参数/非参数）
  - 分类：建立特征→类别的判别边界
  - 聚类：发现数据中的自然分组结构
  - 相关分析：量化变量间的线性/非线性关联强度
  - 降维：高维数据的低维表示（保留主要变异）
typical_problem_structures:
  - 电池放电曲线预测（时序回归）
  - 定价因素分析（多元回归）
  - 颜色-浓度标定（回归标定）
  - 古代玻璃成分分类（聚类+判别）
  - 销量预测（时序+回归）
  - 运动数据分析（相关分析+降维）
mathematical_formulations:
  - statistics：回归模型（OLS/Logistic/非参数）、假设检验、方差分析
  - linear_algebra：SVD/特征值分解（PCA）、距离矩阵（KMeans）
  - probability_and_stochastic：概率模型（贝叶斯、混合模型）
common_solvers:
  - regression_and_supervised：OLS、Logistic、随机森林、XGBoost、ARIMA、LSTM
  - clustering：KMeans、层次聚类
  - dimensionality_reduction：PCA、LDA
  - analytical_methods：相关系数、ANOVA闭式计算
good_for:
  - 数据丰富但物理机理不明确的问题
  - 预测/分类/聚类任务
  - 变量间关联关系探索
  - 数据驱动的决策支持
bad_for:
  - 有明确物理机理的问题（应优先用机理建模conservation_law等）
  - 外推预测（数据范围外的预测不可靠）
  - 因果推断（统计关联≠因果关系）
  - 小样本问题（统计方法需要足够数据量）
assumptions:
  - 数据质量可靠（无系统偏差、缺失值已处理）
  - 训练集与测试集同分布
  - 特征选择合理（无遗漏关键变量）
  - 模型假设满足（如OLS的线性性、独立性、同方差性）
risks:
  - 过拟合（模型复杂度超过数据支持）
  - 伪相关（混淆变量导致虚假关联）
  - 数据泄露（训练集包含测试信息）
  - 忽略因果方向（将相关当因果）
  - 外推失效（模型在数据范围外不可靠）
validation:
  - 交叉验证（k-fold CV）
  - 残差分析（回归残差的正态性/同方差性检验）
  - 混淆矩阵/ROC曲线（分类）
  - 轮廓系数/肘部法则（聚类）
  - 多种子稳定性（随机算法的多次运行一致性）
relations:
  - L1: data_analysis, decision_evaluation
  - L3: statistics, linear_algebra, probability_and_stochastic
  - L4: regression_and_supervised, clustering, dimensionality_reduction, analytical_methods
  - 与conservation_law的区别：statistical_association是数据驱动，conservation_law是机理驱动
evidence:
  - taxonomy §2.3.1 (36题中11题数据驱动但L2无对应标签; regression 7次, statistical_analysis 8次)
  - 中国大学MOOC"一元统计模型""多元统计分析模型"独立课程
  - CSDN流行"四大模型"将评价与预测/分类分开
  - Wiley教材分类：phenomenological（数据驱动）vs mechanistic（机理驱动）
```

---

### KU-L2-03: inverse_problem

```
id: KU-L2-03
name: inverse_problem（反问题/参数反演/图像重建）
layer: L2 Modeling Pattern
definition: "已知观测输出，反求输入/参数/初始条件"的建模模式，与正问题"已知输入求输出"的建模方向相反。核心特征是通常不适定（ill-posed），需要正则化处理，验证方法也不同（需要真值对比或扰动稳定性分析）。
core_mechanism:
  - 正问题：输入/参数 → 模型 → 输出（适定，Hadamard三条件满足）
  - 反问题：观测输出 → 反演 → 输入/参数（通常不适定）
  - 不适定性表现：解不存在、解不唯一、解不连续依赖于数据
  - 正则化：Tikhonov正则化、截断奇异值、全变分正则化
  - 目标函数：min_θ ||F(θ) - y_obs||² + λ·R(θ)（数据拟合项+正则化项）
typical_problem_structures:
  - 热参数反演（已知温度数据反求热扩散系数/导热系数）
  - CT图像重建（已知投影数据反求内部断层图像，Radon变换逆）
  - 光学干涉厚度反演
  - 经纬度反演（已知影子长度/角度反求地理位置）
  - 模型参数标定（已知输出数据反求模型参数）
mathematical_formulations:
  - optimization（残差最小化：min ||F(θ) - y_obs||²）
  - PDE（正问题算子F通常是PDE求解器）
  - linear_algebra（线性反问题：Ax=b，用SVD/伪逆）
  - probability_and_stochastic（贝叶斯反演：后验分布p(θ|y)）
common_solvers:
  - exact_optimizer：最小二乘（Levenberg-Marquardt）、梯度下降、网格搜索
  - numerical_PDE：正问题求解器（反问题的每次迭代需要求解正问题）
  - monte_carlo：MCMC（贝叶斯反演的后验采样）
  - analytical_methods：线性反问题的解析解（SVD伪逆）
good_for:
  - 已知输出观测数据，需要反求物理参数/初始条件/系统输入
  - 有明确正问题模型（PDE/ODE/代数方程）可作为前向算子
  - 系统辨识/参数标定/图像重建任务
bad_for:
  - 正问题模型未知或无法形式化
  - 观测数据噪声极大且无正则化手段
  - 纯预测问题（已知输入求输出，应归正问题）
assumptions:
  - 正问题模型F(θ)已知且可计算
  - 观测数据y_obs包含噪声（测量误差）
  - 参数空间有物理意义的约束范围
  - 正则化参数λ可选择（L曲线/广义交叉验证）
risks:
  - 不适定性导致解对噪声极度敏感（反向热方程是经典不适定问题）
  - 非唯一性：多组参数可产生相同输出
  - 正则化过度导致解偏离真值（欠拟合）
  - 正则化不足导致解被噪声主导（过拟合）
  - 正问题模型误差被误归因于参数误差
validation:
  - 扰动稳定性分析（输入数据扰动ε，观察解的变化是否有界）
  - 与真值对比（合成数据实验：已知真值θ*，生成y=F(θ*)+noise，反演θ是否接近θ*）
  - 残差分析（拟合残差是否为白噪声）
  - L曲线分析（选择最优正则化参数）
  - 交叉验证（留出部分观测数据验证反演结果的预测能力）
relations:
  - L1: diffusion/heat_transfer, motion/geometry, data_analysis, decision_evaluation
  - L2: 通常与其他L2标签共存（如diffusion的conservation_law + inverse_problem）
  - L3: optimization, PDE, linear_algebra, probability_and_stochastic
  - L4: exact_optimizer, numerical_PDE, monte_carlo, analytical_methods
evidence:
  - taxonomy §2.3.2 (36题中5题涉及反演; allowed_model_families中inverse_problem出现5次)
  - continuous_physics §8.2 (2018_A参数反演: 反向热方程是经典不适定问题)
  - continuous_physics §2.2 (Hadamard适定性三条件: 存在性/唯一性/连续依赖性)
  - KTH Royal Institute of Technology PDE Notes ("'Backward' heat equation ⇒ ill-posed")
  - 反问题经典文献: Tarantola 1987, Kaipio & Somersalo 2005
```

---

### KU-L2-04: geometric_constraint（扩展定义）

```
id: KU-L2-04
name: geometric_constraint（几何约束/距离约束/空间约束）
layer: L2 Modeling Pattern
definition: 通过定义距离/几何/空间约束来构建模型的建模模式。涵盖：(1)空间距离/轨迹约束（运动学、碰撞检测、刚体约束）；(2)几何投影/变换（CT标定、空间定位、球面三角）；(3)评价空间中的距离度量（TOPSIS距离理想点）。原distance/geometry标签仅被TOPSIS窄化，现扩展到运动学/几何建模语境。
core_mechanism:
  - 刚体距离约束：|P_i - P_{i+1}| = d（相邻节间距恒定）
  - 碰撞避免约束：|P_i - P_j| ≥ w_min（非相邻节不穿透）
  - 几何参数化：螺线r(θ)=R₀+pθ、悬链线y=a·cosh(x/a)+b
  - 坐标变换：旋转矩阵/平移向量/DH参数
  - 距离度量：欧氏距离/曼哈顿距离/马氏距离（评价空间）
typical_problem_structures:
  - 多刚体链运动学（板凳龙：224节板凳的位置递推+碰撞检测）
  - 空间定位（太阳影子定位：经纬度反演）
  - CT标定（投影几何/Radon变换）
  - 悬链线静力平衡（系泊系统锚链形状）
  - TOPSIS评价（距离理想点/负理想点）
mathematical_formulations:
  - linear_algebra（坐标变换、距离矩阵、旋转矩阵）
  - ODE（运动学方程、悬链线边值ODE）
  - optimization（约束优化：min目标 s.t. 距离/碰撞约束）
  - graph（拓扑结构：多体链的连接图）
common_solvers:
  - numerical_ODE（多体递推、RK4积分）
  - analytical_methods（螺线几何解析、悬链线方程、球面三角公式）
  - exact_optimizer（约束优化：SQP/内点法）
  - metaheuristic_optimization（轨迹优化：GA/PSO）
good_for:
  - 涉及空间位置/距离/形状/姿态的问题
  - 刚体运动学/碰撞检测/轨迹规划
  - 几何投影/坐标变换/空间定位
  - 评价空间中的距离度量
bad_for:
  - 纯场问题（无几何约束，如均匀介质热传导）
  - 纯调度问题（无空间维度）
  - 纯数据驱动问题（无几何结构）
assumptions:
  - 几何模型可参数化（螺线/圆弧/悬链线等）
  - 刚体假设（运动学问题中物体不变形）
  - 坐标系定义明确（全局/局部坐标系的变换关系已知）
risks:
  - 碰撞检测简化过度（用中心线距离代替实际几何体碰撞）
  - 几何参数化选择不当（螺线假设不匹配实际路径）
  - 坐标系变换错误（旋转/平移矩阵错误）
  - 忽略碰撞的时间维度（静态碰撞检测 vs 动态碰撞）
validation:
  - 刚体约束残差检查（相邻节间距≈d，误差<1e-6）
  - 碰撞检查（所有非相邻节距离≥w_min）
  - 对称性检查（对称问题的解应满足对称性）
  - 与解析解对比（简单几何情形）
relations:
  - L1: motion/geometry, continuous_mechanics, decision_evaluation, network/traffic
  - L3: linear_algebra, ODE, optimization, graph
  - L4: numerical_ODE, analytical_methods, exact_optimizer, metaheuristic_optimization
evidence:
  - continuous_physics §2.3 (刚体约束/碰撞检测/螺线参数化/悬链线几何)
  - continuous_physics §6.2 (2024_A板凳龙: 多体递推+碰撞检测+螺线参数化)
  - taxonomy §2.2.4 (当前仅TOPSIS使用, 需扩展到运动学/几何建模)
  - audit §2.3 (distance/geometry仅在TOPSIS的"距离理想点"语境下被覆盖)
  - IEEE Technology Navigator (Forward Kinematics, Denavit-Hartenberg convention)
```

---

### KU-L2-05: temporal_recurrence（拆分定义）

```
id: KU-L2-05
name: temporal_recurrence（时序递推/自治递推）
layer: L2 Modeling Pattern
definition: 时间序列的自治递推结构 x_{t+1} = f(x_t, x_{t-1}, ...)，无决策变量。核心是数据驱动的预测，系统状态随时间自演化，与decision_state_transition（动作驱动的状态演化+累积奖励优化）有本质区别。
core_mechanism:
  - 自回归：x_t = c + Σφ_i·x_{t-i} + ε_t（ARIMA的AR部分）
  - 移动平均：x_t = μ + Σθ_i·ε_{t-i}（MA部分）
  - 差分：∇x_t = x_t - x_{t-1}（I部分，使序列平稳）
  - 灰色微分：x^(1)(k)的白化微分方程（GM(1,1)）
  - 非线性递推：LSTM门控递推/状态空间模型
typical_problem_structures:
  - 电池放电曲线预测（时序回归）
  - 销量预测（时序+回归）
  - 人口/经济预测（灰色预测GM(1,1)）
  - 信号预测（LSTM/GRU）
mathematical_formulations:
  - statistics（时序模型：ARIMA/指数平滑）
  - probability_and_stochastic（随机过程：马尔可夫链/随机游走）
  - ODE（连续时间递推的极限形式）
common_solvers:
  - regression_and_supervised（ARIMA/LSTM/GM/指数平滑）
  - analytical_methods（闭式预测公式）
  - monte_carlo（随机时序模拟）
good_for:
  - 纯时序预测（无决策变量）
  - 数据驱动的趋势外推
  - 平稳/可平稳化的时间序列
bad_for:
  - 多阶段决策（应归decision_state_transition）
  - 因果推断（时序相关≠因果）
  - 非平稳且无变换手段的序列
assumptions:
  - 序列平稳或可通过差分/变换平稳化
  - 历史模式在未来持续（平稳性假设）
  - 无外生决策变量影响序列
risks:
  - 过拟合（模型阶数过高）
  - 非平稳性导致预测失效
  - 忽略结构性突变
validation:
  - 回测（walk-forward validation）
  - 残差白噪声检验（Ljung-Box检验）
  - 平稳性检验（ADF检验）
relations:
  - L1: data_analysis, motion/geometry
  - L3: statistics, probability_and_stochastic
  - L4: regression_and_supervised, analytical_methods, monte_carlo
  - 与decision_state_transition的区别：temporal_recurrence无决策变量a_t，是自治系统
evidence:
  - taxonomy §2.2.1 (拆分state_transition: 自治递推vs决策依赖)
  - audit §2.2 (state transition仅被ARIMA/GM/LSTM时序卡使用)
  - discrete_optimization §2.2.6 (决策语境vs时序语境的区分表)
```

---

## L3 新增知识单元

### KU-L3-01: ODE

```
id: KU-L3-01
name: ODE（常微分方程）
layer: L3 Mathematical Formulation
definition: 含有一个自变量（通常是时间t）的未知函数及其导数的方程。描述集中参数系统（lumped parameter system）的整体演化，解是曲线（curve）。与PDE（多变量、分布参数系统、解是曲面）有本质区别。
core_mechanism:
  - 初值问题（IVP）：y' = f(t,y), y(t₀) = y₀（给定初始条件）
  - 边值问题（BVP）：y'' = f(t,y,y'), y(a)=α, y(b)=β（给定两端边界条件）
  - 高阶ODE可化为一阶方程组：y' = F(t,y)
  - 线性ODE：y' = A(t)y + g(t)（有解析解理论）
  - 非线性ODE：通常无解析解，需数值求解
typical_problem_structures:
  - 运动学/动力学（牛顿第二定律m·x''=F）
  - 振动分析（m·x''+c·x'+k·x=F(t)）
  - 静力平衡（悬链线方程：两点边值ODE）
  - 多体递推（板凳龙：运动学递推关系）
  - 种群动力学（Lotka-Volterra方程）
  - 电路分析（RLC电路方程）
mathematical_formulations:
  - 一阶ODE：dy/dt = f(t,y)
  - 二阶ODE：d²y/dt² = f(t,y,dy/dt)
  - 方程组：dY/dt = F(t,Y), Y∈ℝⁿ
  - 线性系统：dY/dt = AY + g(t)
common_solvers:
  - numerical_ODE：Euler、RK4、odeint（scipy.integrate.odeint）、BDF（刚性问题）
  - numerical_ODE：打靶法（shooting method，边值问题）、有限差分法（边值问题）
  - analytical_methods：解析解（可积情形：分离变量/积分因子/特征值法）
  - exact_optimizer：参数估计（ODE中的未知参数拟合）
good_for:
  - 集中参数系统（状态由有限个变量描述）
  - 单自变量（通常时间）的演化问题
  - 初值问题或边值问题
  - 有明确力学/物理方程可推导的系统
bad_for:
  - 分布参数系统（场变量依赖空间+时间，应归PDE）
  - 纯代数问题（无导数，应归optimization/linear_algebra）
  - 离散事件系统（状态在离散事件跳跃，应归simulation/queue）
assumptions:
  - 系统可由有限个状态变量描述（集中参数假设）
  - 状态变量连续可微（光滑性假设）
  - 方程右端函数f满足Lipschitz条件（保证解的存在唯一性）
risks:
  - 刚性问题（stiff ODE）：显式方法不稳定，需用隐式方法（BDF）
  - 初值敏感性（混沌系统：初值微小扰动导致解的巨大偏差）
  - 边值问题多解/无解
  - 数值耗散（数值方法引入的人工阻尼）
validation:
  - 初值敏感性分析（扰动初值±1%观察解的变化）
  - 平衡点稳定性分析（Jacobian矩阵特征值）
  - 守恒量检查（无源/汇时能量/质量守恒）
  - 步长收敛性测试（Δt减半比较关键输出变化<1%）
  - 与解析解对比（可积情形）
relations:
  - L1: motion/geometry, continuous_mechanics, competition/game（复制子动力学）
  - L2: conservation_law, geometric_constraint, decision_state_transition
  - L3: optimization（参数估计）, linear_algebra（线性ODE系统）
  - L4: numerical_ODE, analytical_methods, exact_optimizer
  - 与PDE的区别：ODE单自变量+集中参数，PDE多自变量+分布参数
evidence:
  - continuous_physics §3.2 (ODE与PDE的本质区别表: 自变量数量/未知函数/解的几何/系统类型/定解条件/数值方法)
  - continuous_physics §3.4 (拆分PDE/ODE为独立L3标签的6项论据)
  - taxonomy §3.2.2 (36题中11题涉及DE, ODE用RK4, PDE用有限差分)
  - IEEE Technology Navigator ("Distributed parameter systems... requiring PDEs rather than ODEs. In a lumped parameter system, the entire state is captured by a finite set of variables")
  - University of Alberta PDE Notes ("ODE solution is a curve, PDE solution is a surface/hypersurface")
```

---

### KU-L3-02: PDE

```
id: KU-L3-02
name: PDE（偏微分方程）
layer: L3 Mathematical Formulation
definition: 含有多个自变量（空间x + 时间t，或多空间维度）的未知函数及其偏导数的方程。描述分布参数系统（distributed parameter system）的场演化，解是曲面/超曲面（surface/hypersurface）。与ODE（单变量、集中参数、解是曲线）有本质区别。
core_mechanism:
  - 抛物型（Parabolic）：B²-AC=0，热方程u_t=αu_xx，扩散/热传导
  - 椭圆型（Elliptic）：B²-AC<0，Laplace Δu=0, Poisson Δu=f，稳态场/静力学
  - 双曲型（Hyperbolic）：B²-AC>0，波动方程u_tt=c²u_xx，波动/振动/交通流
  - 定解条件：初始条件u(x,0)=u₀(x) + 边界条件（Dirichlet/Neumann/Robin）
  - 多层介质：界面条件（温度连续+热流连续）
typical_problem_structures:
  - 热传导（高温作业服装：多层一维非稳态热传导）
  - 回流焊炉温曲线（一维非稳态热传导+对流辐射边界）
  - 流体力学（Navier-Stokes方程）
  - 弹性力学（Navier方程/波动方程）
  - 交通流宏观模型（LWR模型：守恒律PDE）
  - 污染物扩散（对流扩散方程）
mathematical_formulations:
  - 通用守恒形式：∂u/∂t + ∇·F(u) = S(u)
  - 热方程：∂u/∂t = α∇²u + S
  - 波动方程：∂²u/∂t² = c²∇²u
  - Laplace/Poisson：∇²u = 0 / ∇²u = f
  - Navier-Stokes：ρ(∂u/∂t + u·∇u) = -∇p + μ∇²u + f
common_solvers:
  - numerical_PDE：FDM（有限差分法，竞赛首选）、FEM（有限元）、FVM（有限体积）
  - numerical_PDE：时间积分（Crank-Nicolson推荐、隐式Euler、Du Fort-Frankel）
  - analytical_methods：分离变量法（简单几何+线性方程）、特征线法（双曲型）
  - exact_optimizer：参数反演（PDE约束优化）
good_for:
  - 分布参数系统（场变量依赖空间+时间）
  - 连续介质中的物理过程（热/质量/动量传递）
  - 有明确守恒律+本构定律可推导PDE的系统
  - 时空场问题（温度场/浓度场/速度场/压力场）
bad_for:
  - 集中参数系统（应归ODE）
  - 纯离散/调度问题（无连续场）
  - 几何尺寸极小（热传导极快，可近似为集中参数）
assumptions:
  - 连续介质假设
  - 本构定律已知（Fourier/Fick/牛顿粘性）
  - 边界条件和初始条件可定义
  - 介质属性（热导率/扩散系数）已知或可反演
risks:
  - 边界条件类型错误（将对流当Dirichlet）
  - 多层介质界面条件缺失（温度连续+热流连续）
  - 数值不稳定（显式格式违反CFL条件）
  - 网格分辨率不足（边界层/界面处需加密）
  - 源/汇项遗漏（化学反应/内热源）
validation:
  - 网格收敛性测试（Δx减半、Δt减半，关键输出变化<1%）
  - 守恒量检查（无源项时总能量/总质量守恒，变化<2%）
  - 与解析解对比（简单情形：半无限大物体/稳态线性分布，相对误差<1%）
  - 物理合理性检查（温度在边界值之间、单调趋近稳态）
  - 参数敏感性（扰动输入参数±10%，输出变化平滑无突变）
relations:
  - L1: diffusion/heat_transfer, continuous_mechanics, network/traffic（交通流PDE）
  - L2: conservation_law, spatial_temporal_field, inverse_problem
  - L3: optimization（参数反演/设计优化）, linear_algebra（离散后线性系统）
  - L4: numerical_PDE, exact_optimizer, analytical_methods
  - 与ODE的区别：PDE多自变量+分布参数+需初始+边界条件，ODE单自变量+集中参数
evidence:
  - continuous_physics §3.2 (PDE与ODE的本质区别表)
  - continuous_physics §3.5 (PDE三类型分类: 椭圆/抛物/双曲, 判别式B²-AC)
  - continuous_physics §4 (numerical PDE: FDM/FEM/FVM九维对比, Lax等价定理, Crank-Nicolson)
  - continuous_physics §6.1 (2018_A: 四层一维非稳态热传导PDE + 界面条件)
  - taxonomy §3.2.2 (CUMCM-HMML将1.1常微分方程和1.2偏微分方程分为两个子领域)
  - UC Davis Math PDE Notes (Hunter): "Conservation of energy implies... lead to the parabolic PDE (cρ)u_t = ∇·(k∇u) + g"
  - Lax Equivalence Theorem: "For a consistent linear approximation, stability is the necessary and sufficient condition for convergence"
```

---

## L4 新增知识单元

### KU-L4-01: exact_optimizer

```
id: KU-L4-01
name: exact_optimizer（精确优化求解器）
layer: L4 Solver/Algorithm
definition: 保证全局最优解（在凸问题中）或在时间限制内给出最优性间隙的优化求解器类别。涵盖线性规划（LP）、整数规划（IP/MILP）、非线性规划（NLP）的精确求解方法。与metaheuristic_optimization（近似解、无最优性保证）有本质区别。
core_mechanism:
  - LP：单纯形法（Simplex）、内点法（Interior Point）
  - IP/MILP：分支定界（Branch-and-Bound, Land and Doig 1960）、分支切割（Branch-and-Cut）、割平面法
  - NLP：SQP（序列二次规划）、内点法、信赖域法
  - 预处理（Presolve）：简化模型、消除冗余约束和变量
  - 启发式（Heuristic）：在搜索树中快速找可行解以改进下界
typical_problem_structures:
  - 调度问题（RGV调度：0-1规划建模）
  - 资源分配（背包问题、多维背包）
  - 供应链优化（多周期MILP）
  - 参数反演（最小二乘优化）
  - 网络流（最大流/最小费用流，可转化为LP）
mathematical_formulations:
  - LP：min cᵀx s.t. Ax ≤ b, x ≥ 0
  - MILP：min cᵀx + dᵀy s.t. Ax + By ≤ b, x∈ℤⁿ, y≥0
  - NLP：min f(x) s.t. g(x) ≤ 0, h(x) = 0
common_solvers:
  - 商业：Gurobi、CPLEX（IBM）
  - 开源学术：SCIP、CBC (COIN-OR)、HiGHS
  - Python内置：scipy.optimize.milp（基于HiGHS）、scipy.optimize.minimize（SLSQP/L-BFGS-B）
  - 建模语言：PuLP、Pyomo、cvxpy
good_for:
  - 结构化线性/整数约束问题
  - 中小规模（变量数/约束数在求解器能力范围内）
  - 需要全局最优性保证的场景
  - 有明确数学规划模型的问题
bad_for:
  - 大规模NP-hard问题（求解时间指数增长）
  - 黑盒目标函数（无梯度信息）
  - 高度非线性/非凸问题（全局最优困难）
  - 实时性要求高的场景（求解时间不可控）
assumptions:
  - 目标函数和约束可形式化为数学规划
  - 变量类型明确（连续/整数/二进制）
  - 模型规模在求解器能力范围内
risks:
  - 大M取值不当导致数值不稳定
  - 非线性约束未线性化导致MILP模型错误
  - 变量过多导致求解超时
  - 整数约束导致非凸性（LP松弛界宽松）
  - 数值精度问题（接近0的约束被违反）
validation:
  - 最优性间隙检查（MIPGap < 设定阈值，如1%）
  - 约束违反检查（所有约束满足，容差内）
  - 目标值下界验证（LP松弛是下界，MILP最优值≥LP松弛值）
  - 多种子/多求解器对比（不同求解器结果一致）
  - 小规模枚举验证（n≤10时枚举所有解对比）
relations:
  - L1: scheduling, supply_chain/operations, diffusion/heat_transfer（参数反演）, decision_evaluation
  - L2: resource_constraint, inverse_problem, geometric_constraint, flow_balance
  - L3: optimization, graph, linear_algebra
  - L4: 与metaheuristic_optimization并列（精确vs近似）
evidence:
  - taxonomy §4.3.1 (36题variants中LP 2次, IP 3次, 约束优化等共12次; CUMCM-HMML领域2.1/2.2)
  - discrete_optimization §4.2-4.3 (B&B由Land and Doig 1960提出; MILP求解器基于B&B+割平面+启发式)
  - discrete_optimization §3.2 (数学规划层级: LP/NLP/IP/MILP)
  - arXiv 2511.09219 ("Modern MILP solvers are built upon the branch-and-bound (B&B) paradigm (Land and Doig 1960)")
  - IEEE Technology Navigator (Optimization Methods + Mathematical Programming)
```

---

### KU-L4-02: numerical_ODE

```
id: KU-L4-02
name: numerical_ODE（常微分方程数值求解）
layer: L4 Solver/Algorithm
definition: 将连续常微分方程在离散时间步上近似求解的算法类别。与numerical_PDE（空间离散+时间积分）有本质区别：numerical_ODE不需要空间离散（刚体位置是有限维向量），核心是时间积分。
core_mechanism:
  - 单步法：Euler（显式/隐式）、Runge-Kutta（RK2/RK4）
  - 多步法：Adams-Bashforth（显式）、Adams-Moulton（隐式）、BDF（刚性问题）
  - 边值问题：打靶法（Shooting）、有限差分法、配点法（Collocation）
  - 多体递推：正向运动学递推（串行链逐节计算）
  - 刚性检测：自动选择显式/隐式方法
typical_problem_structures:
  - 运动学/动力学仿真（板凳龙多体递推、机械振动）
  - 静力平衡边值问题（悬链线方程、系泊系统）
  - 电路仿真（RLC电路瞬态分析）
  - 种群动力学仿真（Lotka-Volterra）
mathematical_formulations:
  - 初值问题：y_{n+1} = y_n + h·Φ(t_n, y_n, h)（一般单步法）
  - RK4：k₁=f(t_n,y_n), k₂=f(t_n+h/2,y_n+hk₁/2), k₃=f(t_n+h/2,y_n+hk₂/2), k₄=f(t_n+h,y_n+hk₃), y_{n+1}=y_n+h(k₁+2k₂+2k₃+k₄)/6
  - 打靶法：将BVP转化为IVP，调整初始斜率使终端边界满足
common_solvers:
  - scipy.integrate.odeint（LSODA，自动刚性检测）
  - scipy.integrate.solve_ivp（RK45/RK23/BDF/Radau）
  - 自定义RK4（教学/竞赛实现）
  - 多体递推（自定义正向运动学）
good_for:
  - ODE初值问题/边值问题
  - 集中参数系统的时间演化仿真
  - 运动学/动力学/振动分析
  - 多体系统递推计算
bad_for:
  - PDE问题（应归numerical_PDE）
  - 离散事件系统（应归simulation/DES）
  - 纯代数问题（无导数）
assumptions:
  - ODE右端函数f光滑且可计算
  - 初始条件/边界条件已知
  - 时间步长h在稳定性范围内
risks:
  - 刚性问题用显式方法导致不稳定（需BDF/隐式方法）
  - 步长过大导致精度不足或不稳定
  - 混沌系统的初值敏感性（长期预测不可靠）
  - 边值问题的打靶法对初始斜率敏感
validation:
  - 步长收敛性测试（h减半，关键输出变化<1%）
  - 守恒量检查（无源/汇时能量/质量守恒）
  - 与解析解对比（可积情形）
  - 平衡点稳定性分析（Jacobian特征值）
  - 刚体约束残差检查（多体系统：相邻间距≈d）
relations:
  - L1: motion/geometry, continuous_mechanics, competition/game（复制子动力学）
  - L2: conservation_law, geometric_constraint, decision_state_transition
  - L3: ODE, optimization（参数估计）
  - L4: 与numerical_PDE并列（ODE vs PDE）
evidence:
  - continuous_physics §4.7 (运动学数值求解与numerical PDE的本质区别表)
  - continuous_physics §3.2 (ODE求解用RK4/Euler/BDF，PDE求解用FDM/FEM/FVM)
  - taxonomy §4.3.2 (36题variants中Runge_Kutta 2次, multi_body_dynamics 2次; methodology/ode-pde.md决策树: ODE→Euler/RK4/odeint)
  - taxonomy §3.2.2 ("ODE求解用RK4/odeint，PDE求解用有限差分/有限元")
```

---

### KU-L4-03: simulation

```
id: KU-L4-03
name: simulation（仿真/模拟）
layer: L4 Solver/Algorithm
definition: 通过计算机时间步进模拟系统演化的求解范式，不追求解析解。涵盖离散事件仿真（DES）、基于Agent的仿真（ABM）、元胞自动机（CA）、系统动力学（SD）。与monte_carlo（随机抽样的统计估计）的区别：simulation关注系统动态演化过程，monte_carlo关注随机抽样的统计估计。
core_mechanism:
  - 离散事件仿真（DES）：事件驱动——维护事件队列（到达事件/离开事件），按时间顺序处理事件，更新系统状态
  - 基于Agent的仿真（ABM）：多智能体——每个Agent有独立状态和行为规则，Agent间交互产生系统级行为
  - 元胞自动机（CA）：空间离散+时间步进——每个元胞状态由邻居状态决定
  - 系统动力学（SD）：存量-流量图+反馈回路——宏观反馈系统的时间演化
  - 时间步进：固定时间步（Δt）或事件跳跃（下一事件时间）
typical_problem_structures:
  - 排队系统仿真（机场出租车：到达-服务-离开事件链）
  - 交通流微观仿真（跟驰模型/多智能体）
  - 演化博弈仿真（多智能体学习/重复博弈）
  - 调度系统仿真（RGV调度：加工完成事件驱动）
  - 网络性能仿真（随机容量/随机需求下的网络性能）
mathematical_formulations:
  - 状态转移：s(t_{n+1}) = f(s(t_n), event_n)
  - 事件调度：event_list = {(time, type, parameters)}，按time排序处理
  - Agent规则：action_i = rule_i(state_i, neighbors_state)
common_solvers:
  - SimPy（Python DES库）
  - AnyLogic、Arena（商业仿真平台）
  - 自定义Python/MATLAB实现（竞赛常用）
  - Mesa（ABM库）
good_for:
  - 解析方法不可行的复杂系统（非标准分布/复杂拓扑/动态路由）
  - 需要瞬态行为/分布/极端事件分析
  - 多智能体交互系统
  - 离散事件驱动系统
  - 验证解析模型的假设合理性
bad_for:
  - 简单系统有解析解（应优先用analytical_methods）
  - 需要精确最优解（仿真只能给出统计估计）
  - 计算资源有限（仿真需多次运行取统计）
assumptions:
  - 系统规则/行为可形式化
  - 输入分布/参数可估计
  - 仿真模型已验证（与真实系统/解析模型一致）
risks:
  - 仿真模型未验证（"垃圾进垃圾出"）
  - Warm-up period未删除（初始瞬态数据污染稳态统计）
  - 运行次数不足（统计置信区间过宽）
  - 随机种子未固定（结果不可复现）
  - 仿真时间不足（未达到稳态）
validation:
  - Warm-up period分析（删除初始瞬态数据）
  - 多次独立运行（≥5次，种子固定为42及变体），报告均值±标准差
  - 置信区间报告
  - 与解析解对比（在可解析的场景下）
  - 模型验证（与真实系统数据/历史数据对比）
  - Little's Law自检（排队系统：L=λW）
relations:
  - L1: network/traffic, scheduling, competition/game, supply_chain/operations
  - L2: queue, decision_state_transition, interaction_game, resource_constraint
  - L3: probability_and_stochastic, optimization, graph
  - L4: 与monte_carlo并列（仿真演化vs随机抽样估计）
evidence:
  - taxonomy §4.3.3 (36题variants中DES 3次, ABM 2次, CA 1次等共9次; CUMCM-HMML领域8; methodology/simulation.md)
  - network_game §4.4 (DES/ABS/MC/SD分类; simulation在网络与博弈域的双重角色: 求解器+验证器)
  - network_game §4.2 (排队系统仿真: 事件队列驱动, warm-up period)
  - Minitab仿真对比文章 ("DES适用于重新设计/改进流程，Monte Carlo适用于评估风险/不确定性")
  - 项目AGENTS.md: "随机种子固定为42，多种子运行≥5次，报告均值与标准差"
```

---

### KU-L4-04: analytical_methods

```
id: KU-L4-04
name: analytical_methods（解析/闭式方法）
layer: L4 Solver/Algorithm
definition: 有明确计算公式/步骤、无需迭代搜索的计算方法类别。涵盖：(1)解析推导（静力平衡方程求解、球面三角）；(2)闭式统计方法（M/M/c排队公式、ANOVA、相关系数）；(3)决策分析方法（AHP/TOPSIS/熵权）。共同特征是有明确的公式/步骤，无需迭代搜索。
core_mechanism:
  - 解析求解：直接代入公式计算（如M/M/c的P₀/L_q/W_q公式）
  - 特征值/特征向量：AHP的判断矩阵特征向量法
  - 距离计算：TOPSIS的欧氏距离/相对贴近度
  - 熵计算：熵权法的信息熵公式
  - 统计检验：ANOVA的F统计量、相关系数的t检验
typical_problem_structures:
  - 排队论稳态分析（M/M/c闭式公式）
  - 决策分析（AHP/TOPSIS/熵权综合评价）
  - 静力平衡解析解（悬链线方程、简支梁挠度）
  - 统计分析（ANOVA、相关系数、假设检验）
  - 博弈均衡计算（2×2博弈的Nash均衡解析解、Shapley值）
  - 几何计算（球面三角、坐标变换）
mathematical_formulations:
  - M/M/c：P₀=[Σ_{k=0}^{c-1}(cρ)^k/k! + (cρ)^c/(c!(1-ρ))]⁻¹, L_q=P₀(cρ)^cρ/(c!(1-ρ)²)
  - TOPSIS：D⁺=√Σ(w_j(x_ij-x_j⁺)²), D⁻=√Σ(w_j(x_ij-x_j⁻)²), C_i=D⁻/(D⁺+D⁻)
  - AHP：Aw=λ_max·w, w为特征向量（权重）
  - 熵权：e_j=-kΣp_ij ln(p_ij), w_j=(1-e_j)/Σ(1-e_j)
common_solvers:
  - 直接公式计算（Python/MATLAB/Excel）
  - 特征值求解（numpy.linalg.eig）
  - 统计函数（scipy.stats）
good_for:
  - 有明确解析公式的简单/标准问题
  - 决策分析/综合评价
  - 排队论稳态指标计算
  - 统计检验/相关分析
  - 需要可解释性的计算
bad_for:
  - 复杂系统无解析解（应归simulation/numerical方法）
  - 大规模优化问题（应归exact_optimizer/metaheuristic）
  - 非线性/非标准分布问题
assumptions:
  - 问题满足解析方法的前提条件（如M/M/c的泊松到达/指数服务假设）
  - 输入参数已知且确定
risks:
  - 假设条件不满足（如非泊松到达用M/M/c公式）
  - 公式应用错误（边界条件/参数范围错误）
  - 数值精度（接近0/无穷大时的数值不稳定）
validation:
  - 前提条件检验（分布拟合检验K-S/χ²）
  - 与仿真/数值解对比（在可对比的场景下）
  - 量纲一致性检查
  - 边界行为验证（如ρ→1时W→∞）
relations:
  - L1: decision_evaluation, network/traffic, motion/geometry, competition/game
  - L2: queue, geometric_constraint, statistical_association, interaction_game
  - L3: statistics, linear_algebra, probability_and_stochastic, ODE
  - L4: 与exact_optimizer/metaheuristic并列（闭式计算vs迭代搜索）
evidence:
  - taxonomy §4.3.4 (36题variants中解析/闭式方法出现29次20.1%; AHP/TOPSIS/熵权/M-M-c/Nash均衡/ANOVA均属此类)
  - taxonomy §4.5 (AHP/TOPSIS/熵权归入L4 analytical_methods: 闭式计算无迭代搜索)
  - network_game §2.2 (M/M/c闭式解: P₀/L/L_q/W/W_q公式; Little's Law L=λW)
  - audit §1.1 (mc-ahp/mc-topsis/mc-entropy-weight三张决策分析卡均为闭式计算)
  - Kendall 1953, Little 1961（排队论经典公式）
```

---

### KU-L4-05: graph_algorithm

```
id: KU-L4-05
name: graph_algorithm（图算法）
layer: L4 Solver/Algorithm
definition: 在图/网络结构上求解特定问题的算法类别。涵盖最短路径、最大流/最小割、最小费用流、最小生成树、匹配、图着色、拓扑排序等。是L3 graph的求解层，也是L2 flow_balance的计算实现。
core_mechanism:
  - 最短路径：Dijkstra（非负权单源）、Bellman-Ford（允许负权）、Floyd-Warshall（全源）、A*（启发式）
  - 最大流：Ford-Fulkerson（增广路）、Edmonds-Karp（BFS选最短增广路）、Dinic（BFS分层+DFS阻塞流）、Push-Relabel
  - 最小费用流：连续最短路法、消圈法、网络单纯形法
  - 最小生成树：Kruskal（按边权排序+并查集）、Prim（从顶点扩展）
  - 匹配：匈牙利算法（二部图最大匹配/最优匹配）、Gale-Shapley（稳定匹配）
  - 最大流-最小割定理：最大流的值=最小割的容量
typical_problem_structures:
  - 路径规划/导航（最短路径）
  - 网络容量分析（最大流）
  - 物流配送/供应链（最小费用流）
  - 交通网络分析（最短路+流量分配）
  - 任务分配/匹配（二部图匹配）
mathematical_formulations:
  - 最短路LP：min Σc_ij x_ij s.t. 流量平衡约束
  - 最大流LP：max |f| s.t. 容量约束0≤f_ij≤c_ij + 流量平衡
  - 最小费用流：min Σc_ij f_ij s.t. 容量约束 + 流量平衡 + 供需约束
common_solvers:
  - NetworkX（Python图库：shortest_path/max_flow/min_cost_flow）
  - 自定义实现（竞赛：Dijkstra/Dinic/匈牙利算法）
  - scipy.sparse.csgraph（最短路径/最小生成树）
good_for:
  - 图/网络结构明确的问题
  - 路径/流量/匹配/生成树问题
  - 有明确图论算法可应用的场景
bad_for:
  - 无图结构的问题（纯连续/纯统计）
  - 图规模极大（需近似算法）
  - 动态图（边/节点随时间变化，需动态图算法）
assumptions:
  - 图结构（顶点/边/权重）可定义
  - 边权重/容量已知
  - 图规模在算法能力范围内
risks:
  - 负权环（Bellman-Ford检测，Dijkstra不适用）
  - 图规模过大导致内存/时间不足
  - 边权重估计错误
  - 忽略图的动态变化
validation:
  - 对偶验证（最大流=最小割，检查割容量）
  - 流量守恒检验（每个中间节点净流入=0）
  - 容量约束检验（每条边流量≤容量）
  - 与LP解对比（小规模问题用exact_optimizer验证）
relations:
  - L1: network/traffic, supply_chain/operations, scheduling
  - L2: flow_balance, resource_constraint
  - L3: graph, optimization（图算法的LP表述）
  - L4: 与exact_optimizer交叉（最大流/最小费用流可转化为LP）
evidence:
  - taxonomy §4.3.5 (36题variants中BFS/Dijkstra/A*出现在2025_D; CUMCM-HMML领域4.1; methodology/graph-theory.md)
  - discrete_optimization §3.1 (图论有独立算法体系: Dijkstra/Bellman-Ford/Ford-Fulkerson/Edmonds-Karp/Dinic/Kruskal/Prim/匈牙利算法)
  - network_game §4.1 (最短路径/最大流/最小费用流/交通分配算法详细分类)
  - network_game §1.1 (最大流-最小割定理: Ford-Fulkerson 1956)
  - CLRS《算法导论》第24-26章
```

---

### KU-L4-06: dimensionality_reduction

```
id: KU-L4-06
name: dimensionality_reduction（降维）
layer: L4 Solver/Algorithm
definition: 将高维数据映射到低维空间的算法类别，保留主要变异/结构。涵盖PCA（主成分分析）、LDA（线性判别分析）、t-SNE、UMAP等。是独立的数据变换算法（特征值分解/SVD），既不是回归（无监督），也不是聚类（不分组）。
core_mechanism:
  - PCA：对数据协方差矩阵做特征值分解（或SVD），取前k个主成分
  - LDA：最大化类间散度/类内散度比（有监督降维）
  - SVD：X = UΣVᵀ，取前k个奇异值
  - 方差解释率：Σ_{i=1}^k λ_i / Σ_{i=1}^d λ_i ≥ 阈值（如85%）
typical_problem_structures:
  - 高维数据可视化（将高维降到2D/3D）
  - 特征提取/去噪（去除噪声维度）
  - 多重共线性处理（回归前降维）
  - 数据压缩
mathematical_formulations:
  - PCA：Σ = (1/n)XᵀX, Σv_i = λ_i v_i, Y = X·V_k（V_k为前k个特征向量矩阵）
  - 累计方差贡献率：η(k) = Σ_{i=1}^k λ_i / Σ_{i=1}^d λ_i
common_solvers:
  - sklearn.decomposition.PCA / LDA
  - numpy.linalg.svd / eig
  - 自定义实现
good_for:
  - 高维数据（维度>样本数或维度间高度相关）
  - 数据可视化（2D/3D投影）
  - 回归前的多重共线性处理
  - 特征提取/去噪
bad_for:
  - 低维数据（无需降维）
  - 需要保留原始特征可解释性的场景（PCA主成分通常不可直接解释）
  - 非线性结构（线性PCA可能失效，需用t-SNE/UMAP）
assumptions:
  - 数据已标准化（各维度量纲一致）
  - 线性结构假设（PCA/LDA是线性方法）
  - 主成分正交假设
risks:
  - 未标准化导致量纲大的维度主导方差
  - 保留维度k选择不当（过多→未有效降维，过少→信息损失）
  - 非线性结构用线性PCA导致信息丢失
  - 主成分可解释性差
validation:
  - 累计方差贡献率检查（≥85%或90%）
  - 特征值碎石图（elbow method选择k）
  - 重构误差检查（||X - YV_kᵀ||² / ||X||² < 阈值）
  - 与原始数据的统计量对比（均值/方差保留情况）
relations:
  - L1: data_analysis, decision_evaluation
  - L2: statistical_association
  - L3: linear_algebra（SVD/特征值分解）, statistics
  - L4: 与regression_and_supervised/clustering并列（降维vs预测vs分组）
evidence:
  - taxonomy §4.3.6 (36题variants中PCA 2次, LDA 1次; mc-pca卡存在但L4无对应标签)
  - audit §1.1 (mc-pca卡: family=dimensionality_reduction)
  - methodology/dimensionality-reduction.md (项目内方法论)
  - 2022_C古代玻璃: PCA降维+聚类+判别
```

---

### KU-L4-07: DP_and_MDP（扩展定义）

```
id: KU-L4-07
name: DP_and_MDP（动态规划与马尔可夫决策过程）
layer: L4 Solver/Algorithm
definition: 通过将复杂问题分解为重叠子问题并利用最优子结构自底向上或自顶向下求解的算法范式。涵盖确定性DP（值迭代/表格递推/记忆化）和随机MDP（值迭代/策略迭代）。原DP标签扩展为DP_and_MDP以涵盖随机动态规划。
core_mechanism:
  - Bellman最优性原理：最优策略的剩余决策必须构成相对于第一个决策所产生状态的最优策略
  - 最优子结构：原问题的最优解包含其子问题的最优解
  - 重叠子问题：同一子问题在递归求解中被反复访问
  - 无后效性/马尔可夫性：当前状态包含所有决策相关历史信息
  - 确定性DP：V_t(s) = max_a {r_t(s,a) + V_{t+1}(s')}
  - 随机MDP：V*(s) = max_a {R(s,a) + γΣ_{s'} P(s'|s,a)V*(s')}
typical_problem_structures:
  - 资源约束下的多阶段决策（穿越沙漠：水/食物/资金约束下的每日行动）
  - 背包类问题（0-1背包/多维背包/无限背包）
  - 最短路径（DAG上的最短路/Bellman-Ford）
  - 生产计划/库存（多周期生产-库存决策）
  - 设备更新（保留vs更换的多阶段决策）
  - 项目调度（小型RCPSP）
mathematical_formulations:
  - 状态定义：s = (阶段, 资源水平1, 资源水平2, ...)
  - 动作空间：A(s) = {可行动作}
  - 转移方程：s' = f(s, a)（确定性）或P(s'|s,a)（随机性）
  - 奖励函数：r(s, a, s')
  - Bellman方程：如上
common_solvers:
  - 值迭代（Value Iteration）：反复更新V(s)直到收敛
  - 策略迭代（Policy Iteration）：策略评估+策略改进交替
  - 自底向上表格递推（Tabulation）：从边界条件开始正向计算
  - 自顶向下记忆化递归（Memoization）：递归+缓存
  - Dijkstra（特殊DP：非负权图的最短路）
good_for:
  - 多阶段序贯决策
  - 有限/可数状态空间（状态变量离散且数量可管理）
  - 满足最优子结构和无后效性
  - 重叠子问题（避免指数级重复计算）
bad_for:
  - 状态空间爆炸（维数灾难：多维资源状态导致10^20状态）
  - 无最优子结构（博弈均衡问题不由子博弈最优简单构成）
  - 连续状态/动作空间（需离散化或用变分法/最优控制/RL）
  - 后效性无法消除（历史影响无法压缩到当前状态）
  - 问题规模过大（即使多项式但n太大）
  - 实时性要求高（DP离线计算完整策略表）
assumptions:
  - 马尔可夫性成立
  - 状态空间有限或可离散化
  - 转移概率/转移函数已知
  - 奖励函数可定义
  - 最优子结构可证明（cut-and-paste论证）
risks:
  - 状态定义不完整（最常见错误：遗漏关键状态变量导致马尔可夫性不成立）
  - 状态维度过高（维数灾难）
  - 转移方程错误（未正确建模动作对状态的影响）
  - 忽略动作空间约束（天气/资源限制下某些动作不可行但未排除）
  - 边界条件错误（终端奖励/初始状态设定错误）
  - 将DP当黑盒（只写代码不验证最优子结构）
  - 连续变量不离散化（直接对连续资源量做DP导致状态空间不可数）
validation:
  - 最优子结构证明（cut-and-paste论证）
  - 小规模brute-force对比（n≤10枚举所有策略对比DP结果）
  - 收敛性检验（值迭代/策略迭代的||V_{k+1}-V_k||_∞ < 1e-6）
  - 策略可行性检验（DP输出策略满足所有约束）
  - 回溯一致性（从DP表回溯最优策略，手动模拟验证累积奖励=DP表最优值）
  - 下界验证（用松弛问题的最优值作为下界，DP最优值≥松弛下界）
relations:
  - L1: scheduling, supply_chain/operations, competition/game
  - L2: decision_state_transition, resource_constraint
  - L3: optimization, probability_and_stochastic, graph
  - L4: 与exact_optimizer/metaheuristic并列（DP是特定结构的精确算法）
  - 注意：DP formulation是L2/L3概念（Bellman方程作为数学表述），DP algorithm是L4概念（值迭代/表格递推作为计算方法）
evidence:
  - discrete_optimization §4.1 (DP核心深入研究: Bellman原理/最优子结构/重叠子问题/无后效性/6条适用+6条不适用+8类常见错误+7种验证方法)
  - discrete_optimization §4.1.9 (DP与Greedy/GA/MILP的区别表)
  - discrete_optimization §4.1.10 (DP formulation L3 vs DP algorithm L4区分)
  - taxonomy §4.2.2 (36题variants中dynamic_programming 1次, MDP 2次; CUMCM-HMML子领域2.3)
  - Bellman R. Dynamic Programming. Princeton University Press, 1957
  - Stanford CS 161, Princeton COS 226, IEEE Technology Navigator (DP标准定义)
```

---

### KU-L4-08: metaheuristic_optimization（扩展定义）

```
id: KU-L4-08
name: metaheuristic_optimization（元启发式优化）
layer: L4 Solver/Algorithm
definition: 基于种群/邻域的随机搜索算法类别，不保证全局最优，需要多种子运行统计。涵盖GA（遗传算法）、PSO（粒子群优化）、SA（模拟退火）、DE（差分进化）、tabu search（禁忌搜索）、ACO（蚁群算法）、NSGA-II（多目标遗传算法）。原GA标签扩展为metaheuristic_optimization以涵盖所有元启发式方法。
core_mechanism:
  - 遗传算法（GA）：选择+交叉+变异，种群进化
  - 粒子群优化（PSO）：粒子位置/速度更新，个体最优+全局最优引导
  - 模拟退火（SA）：Metropolis准则，以概率接受劣解，温度递减
  - 禁忌搜索（TS）：短期记忆（禁忌表）+中期记忆（强化）+长期记忆（多样化）
  - NSGA-II：非支配排序+拥挤度距离，多目标Pareto前沿
  - 共同特征：随机搜索+多种子运行+统计报告
typical_problem_structures:
  - 大规模NP-hard优化问题（调度序列优化、组合优化）
  - 黑盒目标函数（无梯度信息）
  - 非凸/非线性优化
  - 多目标优化（NSGA-II）
  - 2018_B RGV调度（GA优化调度序列）
mathematical_formulations:
  - 通用形式：min f(x) s.t. x∈X（X为可行域，可能非凸/离散）
  - GA编码：x→染色体（二进制/实数/排列）
  - PSO更新：v_{t+1}=ωv_t+c₁r₁(p_best-x_t)+c₂r₂(g_best-x_t), x_{t+1}=x_t+v_{t+1}
  - SA接受概率：P(接受劣解)=exp(-ΔE/T)，T递减
common_solvers:
  - DEAP（Python GA框架）
  - pyswarm（PSO）
  - scipy.optimize.differential_evolution（DE）
  - 自定义实现（竞赛常用）
  - pymoo（多目标优化：NSGA-II）
good_for:
  - 大规模NP-hard问题（精确求解器超时）
  - 黑盒/非凸/非线性目标
  - 不需要精确最优解，接受近优解
  - 多目标优化（Pareto前沿）
bad_for:
  - 小规模凸问题（应优先用exact_optimizer，保证全局最优）
  - 需要精确最优性保证的场景
  - 计算资源极有限（元启发式需要多种子运行）
  - 有明确解析解的问题
assumptions:
  - 目标函数可计算（黑盒即可，无需梯度）
  - 可行域可定义（约束处理方法可用）
  - 多种子运行可接受（计算时间充足）
risks:
  - 陷入局部最优（参数设置不当）
  - 过早收敛（种群多样性丧失）
  - 参数敏感（种群大小/迭代次数/交叉率/变异率选择不当）
  - 结果不可复现（随机种子未固定）
  - 多种子运行不足（统计置信区间过宽）
validation:
  - 多种子运行（≥5次，种子固定为42及变体），报告均值±标准差
  - 收敛曲线分析（目标值随迭代次数的变化）
  - 与精确解对比（小规模问题有精确解时）
  - 约束违反检查（所有约束满足）
  - 参数敏感性分析（扰动关键参数±20%观察结果变化）
  - 多样性分析（种群/解的分布广度）
relations:
  - L1: scheduling, supply_chain/operations, motion/geometry（轨迹优化）, diffusion/heat_transfer（设计优化）
  - L2: resource_constraint, geometric_constraint, decision_state_transition
  - L3: optimization
  - L4: 与exact_optimizer并列（近似vs精确），与analytical_methods并列（迭代搜索vs闭式计算）
evidence:
  - taxonomy §4.2.4 (36题variants中GA出现14次最高频; PSO 1次, tabu 1次, NSGA_II 1次; 16卡中有mc-ga/mc-pso/mc-sa三张元启发式卡)
  - taxonomy §4.4 (metaheuristic作为L4一级标签替代原GA标签: GA/PSO/SA/DE/tabu共享随机搜索范式)
  - discrete_optimization §4.4 (元启发式分类: 构造启发式/局部搜索/元启发式/超启发式)
  - discrete_optimization §6.2 (2018_B获奖方案使用GA优化调度序列: GitHub Hecate2国一方案)
  - CUMCM-HMML子领域2.5"组合优化与元启发式"
  - 项目AGENTS.md: "随机种子固定为42，多种子运行≥5次，报告均值与标准差"
```

---

## 知识单元索引

| ID | 名称 | 层 | 类型 |
|---|---|---|---|
| KU-L1-01 | continuous_mechanics | L1 | ADD |
| KU-L1-02 | supply_chain/operations | L1 | ADD |
| KU-L2-01 | decision_state_transition | L2 | SPLIT-NEW |
| KU-L2-02 | statistical_association | L2 | ADD |
| KU-L2-03 | inverse_problem | L2 | ADD |
| KU-L2-04 | geometric_constraint | L2 | REVISE-EXPANDED |
| KU-L2-05 | temporal_recurrence | L2 | SPLIT-NEW |
| KU-L3-01 | ODE | L3 | SPLIT-NEW |
| KU-L3-02 | PDE | L3 | SPLIT-NEW |
| KU-L4-01 | exact_optimizer | L4 | ADD |
| KU-L4-02 | numerical_ODE | L4 | ADD |
| KU-L4-03 | simulation | L4 | ADD |
| KU-L4-04 | analytical_methods | L4 | ADD |
| KU-L4-05 | graph_algorithm | L4 | ADD |
| KU-L4-06 | dimensionality_reduction | L4 | ADD |
| KU-L4-07 | DP_and_MDP | L4 | REVISE-EXPANDED |
| KU-L4-08 | metaheuristic_optimization | L4 | REVISE-EXPANDED |

**合计**：17个新增/扩展知识单元（L1: 2, L2: 5, L3: 2, L4: 8）

---

*本文件定义了所有新增知识单元的完整schema（id/name/layer/definition/core_mechanism/typical_problem_structures/mathematical_formulations/common_solvers/good_for/bad_for/assumptions/risks/validation/relations/evidence）。所有定义从4份领域研究报告中提取，经综合代理冲突裁决后形成自洽体系。*
