# CUMCM 层次化数学建模知识库（CUMCM-HMML）

> 借鉴 MM-Agent 的 HMML（Hierarchical Mathematical Modeling Library）三级知识结构，
> 为国赛（CUMCM）场景定制的层次化方法检索与选型知识库。
>
> 三级结构：**领域（Domain）→ 子领域（Subdomain）→ 方法节点（Method Node）**
> 共覆盖 12 大领域、38 个子领域、96 个方法节点。
>
> 消费方：type-classifier（题型→领域映射）、method-matcher（方法检索与选型）、model-builder（方法细节参考）。

## 一、设计原则

1. **题型对齐**：每个节点标注适用题型（A/B/C/D/E），与 CUMCM 出题规律对齐
2. **评分对齐**：每个节点的「常见扣分点」直接来自 `core/knowledge/review/scoring-criteria.md`
3. **时效对齐**：标注近三年（2023-2025）使用频率与趋势，避免推荐已降档的方法（如AHP、灰色预测）
4. **证据对齐**：关键节点引用 `core/knowledge/empirical/cumcm-empirical.json` 的统计分位

## 二、三级结构总览

```
CUMCM-HMML
├── 1. 连续系统与微分方程（Differential Equations）
│   ├── 1.1 常微分方程建模
│   ├── 1.2 偏微分方程与场问题
│   ├── 1.3 动力系统稳定性
│   └── 1.4 参数反演与数据同化
├── 2. 优化理论与方法（Optimization）
│   ├── 2.1 线性与整数规划
│   ├── 2.2 非线性规划
│   ├── 2.3 动态规划与多阶段决策
│   ├── 2.4 多目标优化
│   └── 2.5 组合优化与元启发式
├── 3. 数据科学与统计学习（Data Science & Statistical Learning）
│   ├── 3.1 回归分析与拟合
│   ├── 3.2 分类与识别
│   ├── 3.3 聚类与降维
│   ├── 3.4 时间序列分析
│   └── 3.5 深度学习与神经网络
├── 4. 图论与网络（Graph Theory & Networks）
│   ├── 4.1 最短路径与网络流
│   ├── 4.2 图优化与覆盖
│   └── 4.3 复杂网络分析
├── 5. 概率建模与随机过程（Probability & Stochastic Processes）
│   ├── 5.1 蒙特卡洛模拟
│   ├── 5.2 马尔可夫链
│   ├── 5.3 排队论
│   └── 5.4 随机规划
├── 6. 评价与决策分析（Evaluation & Decision Analysis）
│   ├── 6.1 综合评价方法
│   ├── 6.2 多属性决策
│   └── 6.3 博弈论
├── 7. 机理建模（Mechanistic Modeling）
│   ├── 7.1 物理/力学建模
│   ├── 7.2 传热传质
│   ├── 7.3 几何与光学建模
│   └── 7.4 微分方程机理
├── 8. 仿真与数值方法（Simulation & Numerical Methods）
│   ├── 8.1 数值微积分
│   ├── 8.2 有限元与有限差分
│   └── 8.3 系统仿真
├── 9. 灰色系统与模糊数学（Grey System & Fuzzy Mathematics）
│   ├── 9.1 灰色预测 GM
│   └── 9.2 模糊综合评价
├── 10. 运筹与调度（Operations Research & Scheduling）
│   ├── 10.1 生产调度
│   ├── 10.2 路径规划
│   └── 10.3 资源分配
├── 11. 预测与预测方法论（Forecasting Methodology）
│   ├── 11.1 统计预测
│   ├── 11.2 机器学习预测
│   └── 11.3 组合预测
└── 12. 交叉与新兴方法（Interdisciplinary & Emerging）
    ├── 12.1 机器学习+机理混合
    ├── 12.2 Agent-Based 建模
    └── 12.3 鲁棒优化
```

---

## 领域 1：连续系统与微分方程（Differential Equations）

### 子领域 1.1：常微分方程建模

- **方法节点 1.1.1：Lotka-Volterra / 种群竞争模型**
  - 核心思想：用一阶常微分方程群描述种群数量的演化，捕食-竞争-共生关系由耦合项刻画
  - 题型适配：A 题（生态/生物）、E 题（人口/社会）
  - 近三年使用频率：稳定在 8-12%
  - 常见扣分点：参数物理意义不明确、未验证平衡点稳定性、初值敏感性未分析
  - 评分对齐：2025 A 题评阅强调「模型须有明确公式，参数须有物理意义」
  - 推荐工具：Python scipy.integrate.solve_ivp、MATLAB ode45
  - 详细文档：`core/knowledge/methodology/ode-pde.md`

- **方法节点 1.1.2：传染病模型（SIR/SEIR/SIRS）**
  - 核心思想：按仓室划人口，流率=转移概率×仓室人数
  - 题型适配：A 题（流行病）、E 题（公共卫生）
  - 近三年使用频率：疫情后降档（5-8%），但仍是机理建模训练的核心载体
  - 常见扣分点：基本再生数 R0 推导不严谨、未讨论参数敏感性、未验证模型 Regimed 现实区间
  - 评分对齐：结果须落在现实合理区间（可泛化规则 8）
  - 详细文档：`core/knowledge/methodology/ode-pde.md`

- **方法节点 1.1.3：能量/守恒律模型**
  - 核心思想：从物理守恒（能量、动量、质量）出发的 ODE 建模
  - 题型适配：A 题（力学、热学、运动学）
  - 近三年使用频率：稳定在 10-15%，2024 A 「板凳龙」、2025 A 烟幕弹均涉及
  - 常见扣分点：守恒律引用不完整、能量/动量摩擦耗散遗漏、坐标系选择不统一
  - 评分对齐：2024 A 评阅必须有「第 n 个把手到第 n+1 个把手的计算公式」
  - 详细文档：`core/Modeler/knowledge/domain/heat-transfer.md`、`core/Modeler/knowledge/domain/aerospace-dynamics.md`

### 子领域 1.2：偏微分方程与场问题

- **方法节点 1.2.1：热传导方程**
  - 核心思想：∂T/∂t = α ∇²T，扩散系数 α = k/(ρc)
  - 题型适配：A 题（温度场、热防护）
  - 常见扣分点：边界条件不完整、参数单位不匹配、网格划分未做无关性检验
  - 详细文档：`core/Modeler/knowledge/domain/heat-transfer.md`、`core/Modeler/knowledge/domain/protective-design.md`

- **方法节点 1.2.2：扩散方程与传质**
  - 核心思想：∂C/∂t = D ∇²C ± 反应项
  - 题型适配：A 题（污染扩散、化学反应）
  - 常见扣分点：扩散系数取值无依据、边界条件简化为 Dirichlet 而未论证
  - 详细文档：`core/knowledge/methodology/ode-pde.md`

- **方法节点 1.2.3：波动方程**
  - 核心思想：∂²u/∂t² = c²∇²u
  - 题型适配：A 题（声学、振动、电磁）
  - 详细文档：`core/knowledge/methodology/ode-pde.md`

### 子领域 1.3：动力系统稳定性

- **方法节点 1.3.1：平衡点与线性化**
  - 核心思想：Jacobi 矩阵的特征值判定局部稳定性
  - 题型适配：A 题（涉及演化、平衡的物理系统）
  - 常见扣分点：仅在平衡点做线性化而未讨论全局行为、高阶项截断未做残差估计

### 子领域 1.4：参数反演与数据同化

- **方法节点 1.4.1：最小二乘参数估计**
  - 核心思想：min Σ(y_i - f(x_i;θ))²，对参数θ求最优
  - 题型适配：A/B/C 题（含实验或观测数据的参数标定）
  - 常见扣分点：目标函数形式未说明、初值敏感性未分析、残差非正态未处理
  - 评分对齐：2025 B 评阅「用估计值反算并与原始数据对比」（可靠性验证）

- **方法节点 1.4.2：贝叶斯参数推断**
  - 核心思想：P(θ|Data) ∝ P(Data|θ)P(θ)，MCMC 采样
  - 题型适配：小样本物理/反演问题
  - 详细文档：`core/knowledge/methodology/bayesian-methods.md`

---

## 领域 2：优化理论与方法（Optimization）

### 子领域 2.1：线性与整数规划

- **方法节点 2.1.1：线性规划（LP）**
  - 核心思想：单纯形法/内点法解 min cᵀx s.t. Ax ≤ b
  - 题型适配：B 题（资源分配）、D 题（供应链）
  - 近三年使用频率：缓慢下降至 15%，但仍是基础方法
  - 常见扣分点：决策变量定义模糊、约束条件遗漏、对偶价格未解释

- **方法节点 2.1.2：整数/混合整数规划（IP/MIP）**
  - 核心思想：分支定界/分枝切割，变量含整数约束
  - 题型适配：B 题（选址、指派、调度）、D 题（工程决策）
  - 常见扣分点：LP 松弛与整数解差距未分析、大规模问题未给出下界/可行解质量
  - 评分对齐：启发式算法须说明理由与复杂度依据（可泛化规则 9）
  - 推荐工具：PuLP、Gurobi、OR-Tools
  - 详细文档：`core/knowledge/methodology/integer-programming.md`、`core/knowledge/methodology/optimization.md`

### 子领域 2.2：非线性规划

- **方法节点 2.2.1：凸规划（QP/SOCP/SDP）**
  - 核心思想：局部最优=全局最优的保证
  - 题型适配：B 题（小规模非线性优化）
  - 详细文档：`core/knowledge/methodology/numerical-optimization.md`

- **方法节点 2.2.2：非凸规划与全局搜索**
  - 核心思想：多起点、分支定界、空间分割
  - 题型适配：B 题（非凸、多峰）
  - 常见扣分点：未做全局性验证，仅单起点解即宣称最优（违反铁律 M6）
  - 评分对齐：启发式算法须多起点+多种子验证（可泛化规则 9）

### 子领域 2.3：动态规划与多阶段决策

- **方法节点 2.3.1：经典 DP（阶段-状态-决策）**
  - 核心思想：Bellman 最优性原理，逆序/顺序递推
  - 题型适配：B 题（多阶段调度、资源分配）
  - 近三年使用频率：稳定在 22-25%
  - 常见扣分点：状态空间设计不合理、边界条件缺失、递推方向错误
  - 详细文档：`core/knowledge/methodology/dynamic-programming.md`

### 子领域 2.4：多目标优化

- **方法节点 2.4.1：NSGA-II / NSGA-III**
  - 核心思想：Pareto 前沿 + 拥挤度排序
  - 题型适配：D 题（多目标权衡）、E 题（工程师+经济双目标）
  - 近三年使用频率：快速增长至 38%
  - 常见扣分点：Pareto 前沿未可视化、解的选取标准不明确、目标归一化不当
  - 评分对齐：多模型/多方案结果对比是加分点（2023 C 出题人评阅）
  - 推荐工具：pymoo、PlatEMO
  - 详细文档：`core/knowledge/methodology/multi-objective.md`

### 子领域 2.5：组合优化与元启发式

- **方法节点 2.5.1：遗传算法（GA）**
  - 核心思想：选择-交叉-变异，种群演化
  - 题型适配：B 题（NP-hard 组合优化）
  - 近三年使用频率：上升至 51%
  - 常见扣分点：未说明参数设置理由、未做多起点验证、收敛性未分析、直接宣称全局最优
  - 评分对齐：违反铁律 M6（启发式不能宣称全局最优）
  - 详细文档：`core/knowledge/methodology/genetic-algorithms.md`

- **方法节点 2.5.2：粒子群优化（PSO）**
  - 核心思想：个体历史最优+全局最优引导的速度更新
  - 题型适配：B 题（连续/离散均可）
  - 常见扣分点：早熟收敛未处理、速度/位置更新公式抄错
  - 详细文档：`core/knowledge/methodology/swarm-intelligence.md`

- **方法节点 2.5.3：模拟退火（SA）**
  - 核心思想：Metropolis 接受准则 + 温度衰减
  - 题型适配：B 题（组合优化）
  - 常见扣分点：温度衰减策略未论证、马尔可夫链长度设置不合理

- **方法节点 2.5.4：禁忌搜索（TS）**
  - 核心思想：避免循环的禁忌表 + 解禁准则
  - 题型适配：B 题（序列优化、TSP）
  - 详细文档：`core/knowledge/methodology/global-optimization.md`

---

## 领域 3：数据科学与统计学习（Data Science & Statistical Learning）

### 子领域 3.1：回归分析与拟合

- **方法节点 3.1.1：多元线性回归**
  - 核心思想：Y = Xβ + ε，OLS/MLE 估计
  - 题型适配：C 题（因素影响分析、预测）
  - 常见扣分点：未做正态性/异方差/多重共线性检验、R² 过拟合未识别
  - 评分对齐：Pearson 需线性/正态/数据差距不大前提（可泛化规则 2）
  - 详细文档：`core/knowledge/methodology/regression.md`

- **方法节点 3.1.2：逻辑回归 / Logit 模型**
  - 核心思想：ln(p/(1-p)) = βᵀx
  - 题型适配：C 题（分类/概率预测）
  - 评分对齐：比例型因变量 [0,1] 直接用线性回归降档（可泛化规则 3），Logit 变换正确做法
  - 常见扣分点：未做 Hosmer-Lemeshow 拟合优度、自变量筛选不充分

- **方法节点 3.1.3：广义线性模型 / 广义加性模型**
  - 题型适配：C 题（非线性关系、混合变量类型）
  - 详细文档：`core/knowledge/methodology/regression.md`

### 子领域 3.2：分类与识别

- **方法节点 3.2.1：随机森林（RF）**
  - 核心思想：Bagging + 随机特征子集
  - 题型适配：C 题（分类/预测/特征重要性）
  - 近三年使用频率：上升至 48%
  - 常见扣分点：未做交叉验证、过拟合未识别（test<<train 精度）、特征重要性未解读
  - 评分对齐：2025 C NIPT「直接套聚类不是好方法」（可泛化规则 4）
  - 详细文档：`core/knowledge/methodology/machine-learning.md`

- **方法节点 3.2.2：XGBoost / LightGBM**
  - 核心思想：Boosting，序贯残差拟合
  - 题型适配：C 题（结构化数据预测）
  - 常见扣分点：超参数未调优、早停轮次不合理
  - 推荐 SHAP 提供可解释性（铁律 M9：黑盒模型须提供特征重要性）
  - 详细文档：`core/knowledge/methodology/machine-learning.md`、`core/knowledge/methodology/ensemble-learning.md`

- **方法节点 3.2.3：支持向量机（SVM）**
  - 核心思想：最大间隔超平面 + 核技巧
  - 题型适配：C 题（分类）、小样本问题
  - 详细文档：`core/knowledge/methodology/machine-learning.md`

### 子领域 3.3：聚类与降维

- **方法节点 3.3.1：K-Means 聚类**
  - 核心思想：类内方差最小化
  - 题型适配：C 题（分组/分档）
  - 评分对齐：2025 C「直接聚类不是好分组方法，宜建优化/决策模型」（可泛化规则 4）
  - 常见扣分点：K 值选取无依据、未做轮廓系数验证、分组后未与业务目标挂钩

- **方法节点 3.3.2：层次聚类**
  - 题型适配：C 题（样本少，树状可解释）
  - 详细文档：`core/knowledge/methodology/clustering.md`

- **方法节点 3.3.3：PCA / 因子分析**
  - 核心思想：方差最大化投影 / 潜在因子提取
  - 题型适配：C 题（降维、消除共线性、构造综合指标）
  - 常见扣分点：KMO/Bartlett 检验未做、主成分含义解释不清
  - 详细文档：`core/knowledge/methodology/dimensionality-reduction.md`

### 子领域 3.4：时间序列分析

- **方法节点 3.4.1：ARIMA / SARIMA**
  - 核心思想：差分平稳 + ARMA 建模
  - 题型适配：C 题（中短期预测）
  - 三年使用频率：被 ML 部分替代，但仍是时序基础
  - 常见扣分点：ADF 平稳性检验未做、p/d/q 选择无信息准则依据、未做残差白噪声检验
  - 评分对齐：时间效应（季节性、节假日、工作日/周末）是常见给分点（可泛化规则 6）
  - 详细文档：`core/knowledge/methodology/time-series.md`

- **方法节点 3.4.2：指数平滑（Holt-Winters）**
  - 题型适配：C 题（趋势+季节时序）
  - 详细文档：`core/knowledge/methodology/time-series.md`

- **方法节点 3.4.3：LSTM / GRU**
  - 核心思想：门控循环单元捕获长程依赖
  - 题型适配：C 题（大数据量时序预测）
  - 常见扣分点：过拟合严重（参数量>>样本量/10，违反铁律 M8）、缺乏可解释性
  - 评分对齐：小样本(<200)不宜用 LSTM，应走经典时序族
  - 详细文档：`core/knowledge/methodology/deep-learning.md`

### 子领域 3.5：深度学习与神经网络

- **方法节点 3.5.1：CNN / 图像建模**
  - 题型适配：A/C 题（图像分类、目标检测）
  - 评分对齐：模型复杂度须匹配数据规模（铁律 M8）
  - 详细文档：`core/knowledge/methodology/deep-learning.md`、`core/Modeler/knowledge/domain/image-processing.md`

- **方法节点 3.5.2：Transformer / Attention**
  - 题型适配：C/NLP、时序
  - 常见扣分点：参数量远超样本量、推理成本与精度提升不匹配
  - 详细文档：`core/knowledge/methodology/deep-learning.md`

---

## 领域 4：图论与网络（Graph Theory & Networks）

### 子领域 4.1：最短路径与网络流

- **方法节点 4.1.1：Dijkstra / Floyd-Warshall**
  - 核心思想：贪心/动态规划求最短路径
  - 题型适配：B 题（路径优化）、D 题（网络设计）
  - 详细文档：`core/knowledge/methodology/graph-theory.md`、`core/knowledge/methodology/graph-network-vrp.md`

- **方法节点 4.1.2：最小费用最大流**
  - 核心思想：线性规划对偶/网络单纯形
  - 题型适配：B 题（资源传输、物流网络）
  - 详细文档：`core/knowledge/methodology/graph-theory.md`

### 子领域 4.2：图优化与覆盖

- **方法节点 4.2.1：最小生成树（MST）**
  - 题型适配：B/D 题（管网、路网设计）
  - 详细文档：`core/Modeler/knowledge/domain/pipeline-routing.md`、`core/Modeler/knowledge/domain/mooring-system.md`

- **方法节点 4.2.2：旅行商问题（TSP）**
  - 核心思想：访问所有点的最短回路（NP-hard）
  - 题型适配：B 题（配送、巡检）
  - 详细文档：`core/knowledge/methodology/graph-network-vrp.md`

### 子领域 4.3：复杂网络分析

- **方法节点 4.3.1：复杂网络特征与社群发现**
  - 核心思想：度分布、聚类系数、介数中心性
  - 题型适配：E 题（社交网络、信息传播）
  - 详细文档：`core/knowledge/methodology/complex-networks.md`

---

## 领域 5：概率建模与随机过程

### 子领域 5.1：蒙特卡洛模拟

- **方法节点 5.1.1：蒙特卡洛积分与概率估计**
  - 核心思想：大数定律，用样本均值逼近期望
  - 题型适配：A/D/E 题（含不确定性的系统仿真）
  - 近三年使用频率：上升至 32%
  - 常见扣分点：模拟次数不足、收敛性未验证、伪随机数质量未评估
  - 详细文档：`core/knowledge/methodology/monte-carlo.md`、`core/knowledge/methodology/simulation.md`

### 子领域 5.2：马尔可夫链

- **方法节点 5.2.1：离散时间马尔可夫链**
  - 题型适配：E 题（状态转移预测）
  - 详细文档：`core/knowledge/methodology/markov-chain.md`、`core/knowledge/methodology/stochastic-processes.md`

### 子领域 5.3：排队论

- **方法节点 5.3.1：M/M/1 / M/M/c / M/G/1**
  - 核心思想：Poisson 到达 + 指数服务
  - 题型适配：D 题（服务系统设计）
  - 近三年使用频率：下降至 1%，仅在匹配时选用
  - 详细文档：`core/knowledge/methodology/queueing-theory.md`

### 子领域 5.4：随机规划

- **方法节点 5.4.1：两阶段随机规划**
  - 题型适配：D 题（需求/供应不确定下的决策）
  - 评分对齐：时间效应与不确定性须同时建模（可泛化规则 6）
  - 详细文档：`core/knowledge/methodology/robust-optimization.md`

---

## 领域 6：评价与决策分析（Evaluation & Decision Analysis）

### 子领域 6.1：综合评价方法

- **方法节点 6.1.1：熵权法 + TOPSIS**
  - 核心思想：客观赋权 + 距离排序
  - 题型适配：C/D 题（多指标排序）
  - 评分对齐：至少两种赋权口径做灵敏度
  - 常见扣分点：未做无量纲化、权重直接赋而不解释、灵敏度分析缺失
  - 详细文档：`core/knowledge/methodology/evaluation-methods.md`、`core/knowledge/methodology/evaluation-model-family.md`

- **方法节点 6.1.2：主成分综合评价**
  - 题型适配：C/D 题
  - 常见扣分点：贡献率累积未达 85%、主成分含义解释不清

### 子领域 6.2：多属性决策

- **方法节点 6.2.1：AHP（层次分析法）**
  - ⚠️ 降档警告：近三年使用率从 32% 降至 4%，评阅已明确倾向淘汰
  - 仅在特定主观判断场景可用，须配合客观赋权做组合
  - 评分 Alignment：AHP 单独使用评分上限受控
  - 详细文档：`core/knowledge/methodology/evaluation-methods.md`

### 子领域 6.3：博弈论

- **方法节点 6.3.1：纳什均衡**
  - 题型适配：B/E 题（竞争决策）
  - 使用频率：稳定偏升（8-15%）
  - 详细文档：`core/knowledge/methodology/game-theory.md`、`core/Modeler/knowledge/domain/game-strategy.md`

- **方法节点 6.3.2：Stackelberg 博弈 / 双层规划**
  - 题型适配：B 题（领导-跟随决策）
  - 详细文档：`core/knowledge/methodology/multi-objective.md`

---

## 领域 7：机理建模（Mechanistic Modeling）

### 子领域 7.1：物理/力学建模

- **方法节点 7.1.1：牛顿力学 + 运动学**
  - 题型适配：A 题（刚体运动、碰撞、轨道）
  - 评分对齐：2024 A 必须有把手间位置/速度计算公式
  - 详细文档：`core/Modeler/knowledge/domain/aerospace-dynamics.md`、`core/Modeler/knowledge/domain/cooperative-control.md`

### 子领域 7.2：传热传质

- **方法节点 7.2.1：热传导与对流**
  - 题型适配：A 题（温度场、防护服）
  - 详细文档：`core/Modeler/knowledge/domain/heat-transfer.md`、`core/Modeler/knowledge/domain/protective-design.md`

### 子领域 7.3：几何与光学建模

- **方法节点 7.3.1：几何光学与反射定律**
  - 题型适配：A 题（定日镜、望远镜）
  - 详细文档：`core/Modeler/knowledge/domain/optical-systems.md`、`core/Modeler/knowledge/domain/telescope-optics.md`、`core/Modeler/knowledge/domain/solar-energy.md`

- **方法节点 7.3.2：空间几何与坐标系变换**
  - 题型适配：A 题（无人机定位、编队）
  - 详细文档：`core/Modeler/knowledge/domain/drone-positioning.md`

### 子领域 7.4：微分方程机理

- 同领域 1，此处强化机理→数据的推理链

---

## 领域 8：仿真与数值方法

### 子领域 8.1：数值微积分

- **方法节点 8.1.1：有限差分求导 / 数值积分**
  - 题型适配：A 题（无解析解的非线性系统）
  - 详细文档：`core/knowledge/methodology/numerical-methods.md`

### 子领域 8.2：有限元与有限差分

- **方法节点 8.2.1：FDM 求解 PDE**
  - 题型适配：A 题（场问题）
  - 常见扣分点：网格无关性未验证、稳定性条件（CFL）未检查
  - 详细文档：`core/knowledge/methodology/numerical-methods.md`、`core/Modeler/knowledge/domain/fluid-mechanics.md`

### 子领域 8.3：系统仿真

- **方法节点 8.3.1：系统动力学仿真**
  - 题型适配：D/E 题（反馈系统、时延效应）
  - 详细文档：`core/knowledge/methodology/system-dynamics.md`

---

## 领域 9：灰色系统与模糊数学

> ⚠️ 降档警告：灰色预测与模糊综合评价近三年使用率持续下降，评阅明确倾向淘汰。仅在以下场景可用：
> - 灰色预测：数据量极少（<30）且无其他合适方法时
> - 模糊数学：评价指标确实存在模糊性（如"美观""舒适"）
> - 两种方法必须搭配主流方法做对照，不得单独使用

- **详细文档**：`core/knowledge/methodology/grey-system.md`、`core/Modeler/knowledge/domain/composition-analysis.md`

---

## 领域 10：运筹与调度

### 子领域 10.1：生产调度

- **方法节点 10.1.1：Job-Shop / Flow-Shop 调度**
  - 题型适配：B 题（工序排序）
  - 详细文档：`core/Modeler/knowledge/domain/scheduling.md`

### 子领域 10.2：路径规划

- **方法节点 10.2.1：VRP / 路径优化**
  - 题型适配：B 题（物流配送）
  - 详细文档：`core/knowledge/methodology/graph-network-vrp.md`、`core/Modeler/knowledge/domain/traffic-operations.md`

### 子领域 10.3：资源分配

- **方法节点 10.3.1：指派 / 任务分配**
  - 题型适配：B/D 题
  - 评分 Alignment：报童思想优化模型优于简单回归（2023 C 评阅）
  - 详细文档：`core/knowledge/methodology/optimization.md`

---

## 领域 11：预测方法论

### 子领域 11.1：统计预测

- 覆盖 ARIMA、指数平滑、回归预测（见领域 3.4）

### 子领域 11.2：机器学习预测

- 覆盖 XGBoost、LSTM、RF（见领域 3）

### 子领域 11.3：组合预测

- **方法节点 11.3.1：加权 / 堆叠组合预测**
  - 题型适配：C 题（高精度要求场景）
  - 评分 Alignment：多模型/多方案结果对比是加分点（2023 C 出题人评阅）
  - 详细文档：`core/knowledge/methodology/ensemble-learning.md`

---

## 领域 12：交叉与新兴方法

### 子领域 12.1：机器学习 + 机理混合建模

- **方法节点 12.1.1：物理信息神经网络（PINN）**
  - 题型适配：A+C 题（机理+数据同时存在时）
  - 评分 Alignment：2023 C 出题人「数据建模须融合机理分析」
  - 详细文档：`core/knowledge/methodology/deep-learning.md`

### 子领域 12.2：Agent-Based 建模

- **方法节点 12.2.1：多智能体仿真（ABM）**
  - 题型适配：E 题（异质个体交互）
  - 详细文档：`core/knowledge/methodology/agent-based-simulation.md`

### 子领域 12.3：鲁棒优化

- **方法节点 12.3.1：分布鲁棒优化**
  - 题型适配：D 题（最坏场景保障）
  - 详细文档：`core/knowledge/methodology/robust-optimization.md`

---

## 附录 A：选型速查矩阵

| 题型 | 首选领域 | 备选领域 | 慎选/禁选领域 |
|---|---|---|---|
| A 物理/连续机理 | 1（微分方程）、7（机理建模）、8（数值方法） | 2（优化） | 3（纯数据学习）、9（灰色/模糊） |
| B 离散/组合优化 | 2（优化）、4（图论）、10（调度） | 5（随机） | 3.5（深度学习，除非特征复杂） |
| C 数据驱动/统计 | 3（数据科学）、11（预测） | 5（蒙特卡洛）、6（评价） | 9（灰色/模糊，已降档） |
| D 多目标/工程 | 2.4（多目标优化）、6（决策）、12（鲁棒） | 4（图论）、8（仿真） | 9（灰色/模糊） |
| E 交叉学科 | 12（交叉方法）、5（随机过程）、7（机理） | 全部视问题组合 | 单一方法无法覆盖 |

## 附录 B：五维评分法使用说明

method-matcher 在候选方法评估时使用五维评分法（借鉴 MM-Agent）：

| 维度 | 权重 | 评估要点 |
|---|---|---|
| 假设适配度（Assumptions） | 30% | 方法的数学假设是否与问题内在特性匹配 |
| 结构适配度（Structure） | 25% | 方法框架能否刻画问题的逻辑/层次/时空关系 |
| 变量适配度（Variables） | 20% | 方法处理的变量类型与问题是否兼容 |
| 动力学适配度（Dynamics） | 15% | 方法的时间/动态特性是否匹配问题演化行为 |
| 可解性（Solvability） | 10% | 在现实资源约束下是否可解 |

总分加权计算，≥6.0 分为推荐候选，<4.0 分为不推荐。
