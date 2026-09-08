# Domain Research: Network & Game（网络与博弈域）

> **研究性质**：Research-layer Calibration — 四层知识架构的域级证据研究
> **研究范围**：L1 network/traffic + competition/game；L2 flow balance + queue + interaction/game；L3 graph + game-theoretic formulation；L4 flow algorithms + queuing solver + equilibrium algorithms + simulation
> **研究日期**：2026-09-08
> **治理原则**：方法卡 = Constraint/Prior/Validation，不是答案库。Knowledge coverage must constrain evaluation, not constrain creativity.
> **禁止**：不修改任何 `core/knowledge/` 下的文件；不为覆盖率硬造标签；不把竞赛答案当作唯一正确建模方式。

---

## 0. 域定位与边界

### 0.1 本域在四层架构中的位置

| 层 | 本域标签 | 当前知识库覆盖状态 |
|---|---|---|
| L1 Problem Structure | `network/traffic`, `competition/game` | **0 卡覆盖**（审计确认） |
| L2 Modeling Pattern | `flow balance`, `queue`, `interaction/game` | **0 卡覆盖**（审计确认） |
| L3 Mathematical Formulation | `graph`（缺失）, `probability`（强覆盖）, `game-theoretic formulation`（待定位） | graph 0 卡；probability 4 卡 |
| L4 Solver/Algorithm | `flow algorithms`, `queuing solver`, `equilibrium algorithms`, `simulation` | queuing 0 卡；simulation 有 mc-monte-carlo（但仅通用仿真） |

### 0.2 与相邻域的边界

- **与 decision/evaluation 域的边界**：单玩家决策（AHP/TOPSIS）属于 decision 域；多玩家策略互动（payoff 依赖他人选择）属于本域 competition/game。
- **与 scheduling/discrete 域的边界**：纯资源调度（无玩家策略互动）属于 scheduling 域；调度中存在多玩家竞争/博弈时，竞争部分属于本域。
- **与 diffusion/heat 域的边界**：物理守恒（能量/质量守恒 PDE）属于 diffusion 域；网络节点流量平衡（flow balance）属于本域。二者数学形式可能交叉（均为守恒），但问题结构不同。

---

## 1. L1 标签研究

### 1.1 network/traffic（网络/交通）

#### 定义

**network/traffic** 是指问题的核心结构是一个由节点（node/vertex）和连边（edge/link）组成的网络拓扑，且研究对象是网络上的流动、分配、路径选择或容量利用问题。典型子类型包括：

- **交通网络**：路网、公共交通、航空枢纽、交通分配
- **通信网络**：数据路由、带宽分配、网络拥塞
- **物流网络**：供应链、配送路径、仓储网络
- **水资源网络**：流域调度、管网输配
- **抽象网络**：社交网络传播、金融网络清算

#### 核心机理

网络问题的核心机理是**拓扑约束下的流动与分配**：
1. 节点具有流入/流出关系（flow balance）
2. 连边具有容量约束（capacity constraint）
3. 存在源点（source）和汇点（sink）或 OD 对（Origin-Destination）
4. 流动主体（车辆/数据包/物资）在网络上选择路径
5. 路径选择可能受拥堵效应影响（边的旅行时间是流量的函数）

#### 典型问题分类

| 子问题 | 核心变量 | 典型约束 | 对应 L2 模式 |
|---|---|---|---|
| 最短路径 | 路径选择 | 边权非负 | flow balance（隐含） |
| 最大流 | 源汇流量 | 容量约束 | flow balance |
| 最小费用流 | 流量分配 | 容量+费用 | flow balance |
| 交通分配 | OD 流量分配 | 用户均衡/系统最优 | flow balance + interaction/game |
| 网络设计 | 拓扑/容量扩展 | 预算约束 | flow balance |

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| 网络流的核心是节点流量守恒（除源汇外净流为零） | "流守恒(Flow Conservation): 除非 u=s 或 u=t，否则 Σf(u,w)=0" | 网络流百科（基于 Ford-Fulkerson 标准定义） | Tier 3（定义性内容，与教材一致） | high | 这是网络流的标准公理，Ahuja《Network Flows》等教材均以此为基础定义 |
| 最大流问题是组合优化的经典问题，与线性规划密切相关 | "网络流(network-flows)是一种类比水流的解决问题方法，与线性规划密切相关" | 网络流入门教程 | Tier 3 | high | 最大流可表述为 LP，这是 CLRS《算法导论》第 26 章的标准内容 |
| 交通分配中用户均衡（UE）是 Nash 均衡在路径选择上的特例 | "用户平衡法...旅行者不能通过改变路线来改变旅行时间...TransCAD采用Frank-Wolf法" | TransCAD交通分配资料 | Tier 2 | medium-high | Wardrop 第一原理等价于 Nash 均衡，但该来源为软件文档，需教材交叉验证 |
| Braess 悖论表明增加道路可能降低整体交通效率 | "布雷斯悖论...增加道路反而可能让交通状况变得更糟...用博弈论中的纳什均衡概念来解释" | 返朴/科普文章（引用 Braess 1968 原始论文） | Tier 2（引用原始论文） | high | Braess (1968) 原始证明，这是交通网络博弈分析的经典反直觉结果 |

#### 关键引用文献（Tier 1）

- Ahuja, R.K., Magnanti, T.L., Orlin, J.B. *Network Flows: Theory, Algorithms, and Applications*. Prentice Hall, 1993.（网络流标准教材）
- Sheffi, Y. *Urban Transportation Networks: Equilibrium Analysis with Mathematical Programming Methods*. Prentice-Hall, 1985.（交通分配经典）
- Daganzo, C.F. *Fundamentals of Transportation and Traffic Operations*. Pergamon, 1997.

---

### 1.2 competition/game（竞争/博弈）

#### 定义

**competition/game** 是指问题中存在**两个或以上的独立决策主体（players/agents）**，每个主体的收益（payoff）不仅取决于自身策略，还取决于其他主体的策略选择。核心识别特征是**策略互动（strategic interaction）**：一方的最优选择依赖于对他方行为的预期。

#### 核心机理

博弈问题的核心机理是**策略互动下的均衡分析**：
1. 多个理性（或有限理性）主体各自最大化自身收益
2. 收益函数具有交叉依赖性（payoff interdependence）
3. 解概念是均衡（Nash equilibrium / ESS / 子博弈精炼均衡等），而非单一最优解
4. 可能存在合作（coalition）与非合作（non-cooperative）两种范式
5. 信息结构（完全/不完全、完美/不完美）决定均衡类型

#### 与 decision（单玩家决策）的边界

这是本域最重要的边界判定：

| 维度 | decision（单玩家优化） | competition/game（多玩家博弈） |
|---|---|---|
| 决策主体数 | 1 个 | ≥2 个 |
| 收益依赖 | 仅依赖自身选择 | 依赖自身 + 他方选择 |
| 解概念 | 最优解（argmax） | 均衡（Nash/ESS/core） |
| 外部性 | 无策略外部性 | 存在策略外部性 |
| 典型方法 | LP/NLP/MDP/AHP | Nash 求解/演化动力学/Shapley 值 |
| 示例 | 出租车司机在固定需求下选择等待时间 | 多个出租车司机竞争同一批乘客 |

**判定规则**：如果修改其他主体的策略会改变本主体的最优选择，则是博弈；如果其他主体的行为可视为固定的外部环境参数，则是优化。

#### 博弈分类体系

```
博弈论
├── 合作博弈 (cooperative)
│   ├── 特征函数型 → Shapley 值 / Core / Nucleolus
│   └── 匹配型 → 稳定匹配 (Gale-Shapley) / 双边匹配
├── 非合作博弈 (non-cooperative)
│   ├── 静态博弈（同时行动）
│   │   ├── 完全信息 → Nash 均衡（纯策略/混合策略）
│   │   └── 不完全信息 → Bayesian Nash 均衡
│   ├── 动态博弈（序贯行动）
│   │   ├── 完全信息 → 子博弈精炼 Nash 均衡（逆向归纳）
│   │   └── 不完全信息 → 精炼 Bayesian Nash 均衡
│   └── 演化博弈（有限理性）
│       ├── 复制子动力学 (replicator dynamics)
│       └── 演化稳定策略 (ESS)
└── 机制设计 (mechanism design)
    ├── 拍卖设计
    ├── 激励相容 (incentive compatibility)
    └── 显示原理 (revelation principle)
```

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| 博弈论与决策论的根本区别在于参与者数量：决策论只有一个参与者，博弈论有多于一个参与者 | "博弈论...与决策论很像，不同之处在于，决策论只有一个参与者，而对策论具有多于一个参与者" | 数学建模之博弈论教程 | Tier 3（定义性） | high | 这是标准定义，Gibbons《博弈论基础》第 1 章明确区分 |
| Nash 均衡的定义：每个参与者的策略都是对他人均衡策略的最优反应，无人可通过单边偏离获益 | "所有参与者都不能通过单边行动来提高收益，这就是非合作均衡或以约翰·纳什的名字命名的纳什均衡" | 美国工程院院士解析（科学网） | Tier 2（引用 Nash 1950） | high | Nash (1950) 原始定义，标准内容 |
| 非合作博弈按信息+时序分为四类，对应四种均衡精炼 | "完全信息静态→Nash均衡；完全信息动态→子博弈精炼；不完全信息静态→Bayesian Nash；不完全信息动态→精炼Bayesian Nash" | 纳什均衡科普（中金在线，引用 Harsanyi/Selten） | Tier 2 | high | Harsanyi & Selten 1994 Nobel 工作，标准分类 |
| 演化博弈用复制子动力学描述有限理性主体的策略演化，ESS 是抗入侵的稳定策略 | "进化稳定策略(ESS)...约翰·梅纳德·史密斯和普莱斯在1973年的'动物冲突的逻辑'一文" | 进化对策论百科 | Tier 3（引用 Maynard Smith 1973） | high | Maynard Smith & Price (1973) 是演化博弈奠基论文 |
| 机制设计的核心是激励相容：使个体自利行为与集体目标一致 | "哈维茨(Hurwiez)在创立机制设计理论中提出了激励相容理论...使行为人追求个人利益的行为，正好与组织实现集体价值最大化的目标相吻合" | 激励广度研究（MBALIB，引用 Hurwicz） | Tier 2 | high | Hurwicz 2007 Nobel 工作，机制设计标准概念 |

#### 关键引用文献（Tier 1）

- Nash, J.F. "Equilibrium points in n-person games." *PNAS*, 36(1):48-49, 1950.
- Gibbons, R. *Game Theory for Applied Economists*. Princeton University Press, 1992.（中译本《博弈论基础》）
- Osborne, M.J. *An Introduction to Game Theory*. Oxford University Press, 2004.
- Maynard Smith, J., Price, G.R. "The logic of animal conflict." *Nature*, 246:15-18, 1973.
- Hurwicz, L. "Optimality and informational efficiency in resource allocation processes." *Mathematical Methods in the Social Sciences*, 1960.
- Fudenberg, D., Tirole, J. *Game Theory*. MIT Press, 1991.

---

## 2. L2 标签研究

### 2.1 flow balance（流量平衡）

#### 定义

**flow balance**（流量平衡/节点平衡）是一种建模模式：在网络的每个中间节点上，**流入量 = 流出量**（或流入量 - 流出量 = 节点净需求/供给）。它是网络流问题的核心约束结构，数学上表述为：

$$\sum_{j:(j,i)\in E} f_{ji} - \sum_{j:(i,j)\in E} f_{ij} = b_i, \quad \forall i \in V$$

其中 $b_i$ 是节点 $i$ 的净供给（$b_i > 0$ 为源点，$b_i < 0$ 为汇点，$b_i = 0$ 为中间节点）。

#### 与 conservation law（守恒律）的区别

这是一个关键的概念区分：

| 维度 | conservation law（守恒律） | flow balance（流量平衡） |
|---|---|---|
| 物理基础 | 物理量的守恒（能量/质量/动量/电荷） | 网络节点的进出平衡 |
| 数学形式 | 连续性方程 $\partial\rho/\partial t + \nabla\cdot(\rho v) = 0$（微分形式） | 节点流量代数方程（离散形式） |
| 空间结构 | 连续介质（场） | 离散网络（图） |
| 时间维度 | 通常含时间导数（动态守恒） | 通常稳态（可扩展为动态） |
| 典型域 | diffusion/heat（热传导 PDE） | network/traffic（网络流 LP） |
| 守恒对象 | 物理量本身守恒 | 网络上流动的"商品"守恒 |

**关键判定**：conservation law 是**物理场中的微分守恒**，flow balance 是**网络拓扑中的代数平衡**。二者在数学上同源（均为"进来的等于出去的"），但建模语境和数学形式不同：前者导出 PDE，后者导出 LP/网络流约束。

#### 核心机理

1. **节点平衡方程**：每个中间节点净流入为零
2. **容量约束**：每条边的流量不超过容量 $0 \leq f_{ij} \leq c_{ij}$
3. **源汇设定**：源点产生流量，汇点吸收流量
4. **费用/权重**：边可能有单位流量费用，构成最小费用流
5. **拥堵扩展**：边的"费用"可能是流量的函数（交通分配中的 BPR 函数）

#### 扩展形式

- **动态流量平衡**：节点存量变化 = 流入 - 流出（含时间导数），适用于库存/水库调度
- **多商品流**：多种商品共享网络容量，各自满足节点平衡
- **投入产出平衡**：Leontief 投入产出模型中，各部门总产出 = 中间使用 + 最终需求，本质是经济网络的节点平衡

#### 与 graph 的关系

flow balance 必须定义在图（graph）结构上——没有节点和边就没有"流入"和"流出"。但 flow balance 是**约束模式**（L2），graph 是**数学表述形式**（L3）。一个问题可以用图来表述但不一定有 flow balance（如图着色、最短路的某些变体）；flow balance 则必然以图为载体。

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| 网络流的节点守恒是标准定义：除源汇外净流为零 | "流守恒(Flow Conservation): 除非 u=s 或 u=t，否则 Σf(u,w)=0" | 网络流百科 | Tier 3 | high | 与 Ahuja 教材定义一致 |
| 投入产出模型本质是经济网络的节点平衡 | "投入产出数学模型...揭示国民经济各部门...生产与分配使用之间的平衡关系...x = Ax + y（总产出=中间使用+最终需求）" | 投入产出数学模型百科 + 国家统计局 | Tier 2（国家统计局官方） | high | Leontief 模型的标准形式，国家统计局官方解释 |
| conservation law 与 flow balance 的区别在于连续场 vs 离散网络 | 流体力学连续方程 $\partial\rho/\partial t + \nabla\cdot(\rho v)=0$ 是质量守恒的微分形式；网络流节点平衡是代数形式 | 流体力学NS方程科普 + 网络流定义 | Tier 2/3 交叉 | medium-high | 二者数学本质相同（散度=0），但空间离散化程度不同；需注意这是研究者的分析性区分，非单一来源直接陈述 |
| 交通分配中流量平衡是用户均衡（UE）的约束基础 | UE 模型中，每个 OD 对的流量分配满足节点守恒，且每条被使用路径的旅行时间相等 | Sheffi (1985) 标准教材（间接引用） | Tier 1（教材） | high | 交通分配的标准数学规划表述包含 flow balance 约束 |

---

### 2.2 queue（排队）

#### 定义

**queue**（排队论/随机服务系统）是一种建模模式：研究"顾客"到达服务设施、等待、接受服务、离开的随机过程。核心要素是**到达过程（arrival）+ 服务过程（service）+ 排队规则（queue discipline）**的三元结构。

#### 核心机理

1. **到达过程**：顾客到达的时间间隔分布（最常见为泊松到达，即指数间隔）
2. **服务过程**：服务时间的分布（最常见为指数分布）
3. **排队规则**：FIFO（先进先出）、优先级、LIFO 等
4. **服务台数量**：单服务台（c=1）或多服务台（c>1）
5. **系统容量**：无限或有限（K）
6. **顾客源**：无限或有限

Kendall 记号：**A/B/c/K/m/Z**
- A：到达间隔分布（M=指数/Markov，D=确定，G=一般）
- B：服务时间分布（M=指数，G=一般，D=确定）
- c：服务台数
- K：系统容量（省略=无限）
- m：顾客源（省略=无限）
- Z：排队规则（省略=FIFO）

#### 基本模型

**M/M/1**（单服务台，泊松到达，指数服务）：
- 利用率 $\rho = \lambda/\mu$，稳定条件 $\rho < 1$
- 系统空闲概率 $P_0 = 1 - \rho$
- 系统中平均顾客数 $L = \rho/(1-\rho)$
- 队列中平均顾客数 $L_q = \rho^2/(1-\rho)$
- 平均逗留时间 $W = 1/(\mu-\lambda)$
- 平均等待时间 $W_q = \rho/(\mu-\lambda)$

**M/M/c**（多服务台）：
- 利用率 $\rho = \lambda/(c\mu)$
- $P_0 = [\sum_{k=0}^{c-1}(c\rho)^k/k! + (c\rho)^c/(c!(1-\rho))]^{-1}$
- $L_q = P_0(c\rho)^c\rho/(c!(1-\rho)^2)$

**M/G/1**（一般服务时间）：
- Pollaczek-Khinchine 公式：$L_q = \lambda^2 \text{Var}(S) + (\lambda E[S])^2 / (2(1-\lambda E[S]))$
- 说明服务时间方差直接影响队列长度（方差越大，排队越长）

#### Little's Law（利特尔法则）

$$L = \lambda W$$

- L：系统中平均顾客数
- λ：有效到达率
- W：平均逗留时间

**重要性质**：Little's Law 是**模型无关的**（model-independent）——它不依赖于到达分布、服务分布或排队规则，只要求系统稳定。这使得它成为排队论中最普适的关系，也是验证排队模型的重要工具。

推论：$L_q = \lambda W_q$

#### 解析模型 vs 仿真的选择边界

| 条件 | 解析排队模型（M/M/1, M/M/c 等） | 离散事件仿真 |
|---|---|---|
| 到达/服务分布 | 已知且为标准分布（指数/确定等） | 任意分布，可从数据拟合 |
| 网络结构 | 单队列或简单排队网络 | 复杂拓扑、多类顾客、动态路由 |
| 排队规则 | FIFO 或简单优先级 | 复杂规则（放弃、重入、批量服务） |
| 输出需求 | 稳态解析指标（L, W, ρ） | 瞬态行为、分布、极端事件 |
| 计算成本 | 极低（闭式公式） | 较高（需多次运行取统计） |
| 验证难度 | 需检验分布假设 | 需验证仿真模型本身 |

**选择规则**：
- 如果到达和服务过程可以合理假设为泊松/指数，且系统结构简单 → **解析模型**优先（闭式解、可解释、可做灵敏度分析）
- 如果分布非标准、系统有复杂交互、需要瞬态分析 → **仿真**
- 最佳实践：**解析模型做初步分析+参数扫描，仿真做验证和复杂场景**

#### 适用条件与不适用条件

**适用**：
- 到达和服务具有随机性（非确定性）
- 存在"等待"现象（服务能力不足时顾客排队）
- 关注稳态性能指标（平均等待时间、队列长度、利用率）
- 系统可近似为 Markov 过程（指数分布假设合理）

**不适用**：
- 纯确定性调度（无随机到达，如生产线节拍固定）
- 服务时间高度非平稳（到达率随时间剧烈变化，需用非稳态排队或仿真）
- 顾客行为复杂（批量到达、放弃、重试、优先级动态变化）
- 强相关的到达/服务过程（非独立同分布）

#### 验证方式

1. **分布拟合检验**：用 χ² 检验或 K-S 检验验证到达间隔是否为指数分布
2. **Little's Law 验证**：仿真输出的 L、λ、W 是否满足 L=λW
3. **解析-仿真对比**：在简单场景下对比解析公式与仿真结果
4. **灵敏度分析**：扰动 λ 和 μ，观察指标变化是否符合理论预期（如 ρ→1 时 W→∞）
5. **稳态检验**：确认仿真运行足够长时间达到稳态（warm-up period 分析）

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| Kendall 记号 A/B/c 是排队系统的标准分类法 | "D.G.Kendall于1953年提出一个分类方法...相继顾客到达间隔时间的分布;服务时间的分布;服务台个数" | 排队过程百科 | Tier 3（引用 Kendall 1953） | high | Kendall (1953) 原始工作，标准分类 |
| Little's Law L=λW 是模型无关的，适用于任何稳定排队系统 | "利特尔法则派生于排队论...L系统中存在的平均请求数量; λ请求有效到达速率; W请求在系统中的平均等待执行时间" | Little's Law 应用教程 | Tier 3 | high | Little (1961) 证明了该定律的一般性，是排队论最基本定理之一 |
| M/M/1 的稳定条件是 ρ=λ/μ < 1，否则队列无限增长 | "系统利用率：ρ = λ/μ（必须ρ < 1）" | 项目内排队论方法论（基于 Cooper 教材） | Tier 1（项目内，引用标准教材） | high | 标准结果，所有排队论教材均有 |
| M/G/1 的 Pollaczek-Khinchine 公式表明服务时间方差影响队列长度 | 项目内排队论方法论 + Cooper《Introduction to Queueing Theory》 | Tier 1（教材） | high | P-K 公式是 M/G/1 的核心结果 |
| 解析模型适用于标准分布+简单结构，仿真适用于复杂系统 | "如果您正在尝试重新设计或改进过程，则离散事件模拟是正确的选择...如果您的目标是评估过程的风险、不确定性...则 Monte Carlo 模拟更适合" | Minitab 仿真对比文章 | Tier 2 | medium | 该来源对比的是 DES vs Monte Carlo，非解析 vs 仿真；但结论方向一致，需补充排队论教材的选择指南 |
| 排队论起源于自动电话研究，核心矛盾是服务质量与设备利用率的权衡 | "排队论主要研究具有随机性的拥挤现象。它起源于有关自动电话的研究...服务质量和设备利用率之间存在矛盾" | 运筹学优化供应链文章 | Tier 2 | high | 排队论历史（Erlang 1909 电话工程）是标准知识 |

#### 关键引用文献（Tier 1）

- Kendall, D.G. "Stochastic processes occurring in the theory of queues and their analysis by the method of the imbedded Markov chain." *Annals of Mathematical Statistics*, 24(3):338-354, 1953.
- Little, J.D.C. "A proof for the queuing formula L = λW." *Operations Research*, 9(3):383-387, 1961.
- Cooper, R.B. *Introduction to Queueing Theory*. 2nd ed., North-Holland, 1981.
- Gross, D., Harris, C.M. *Fundamentals of Queueing Theory*. Wiley, 1998.
- Erlang, A.K. "The theory of probabilities and telephone conversations." *Nyt Tidsskrift for Matematik B*, 20:33-39, 1909.

---

### 2.3 interaction/game（交互/博弈）

#### 定义

**interaction/game**（交互/博弈）是一种建模模式：将问题建模为多个自主主体之间的策略互动，每个主体的决策影响其他主体的收益，解概念是均衡而非单一最优。

#### 核心机理

1. **主体集合**：$N = \{1, 2, ..., n\}$，$n \geq 2$
2. **策略空间**：每个主体 $i$ 有策略集 $S_i$
3. **收益函数**：$u_i: S_1 \times S_2 \times ... \times S_n \to \mathbb{R}$，关键是 $u_i$ 依赖于所有主体的策略组合
4. **均衡概念**：
   - Nash 均衡：$s^* = (s_1^*, ..., s_n^*)$，满足 $u_i(s_i^*, s_{-i}^*) \geq u_i(s_i, s_{-i}^*)$ 对所有 $i$ 和 $s_i$
   - 混合策略 Nash：策略为概率分布
   - ESS：抗小比例变异者入侵的策略
5. **均衡选择问题**：多个 Nash 均衡时如何选择（payoff dominance, risk dominance, focal point）

#### 与 optimization（单玩家优化）的边界

这是 L2 层最关键的边界判定：

**判定测试**：固定其他所有主体的策略，本主体的最优解是否会随其他主体策略变化而变化？
- **是** → interaction/game（策略互动存在）
- **否** → optimization（其他主体只是外部环境参数）

**典型混淆场景**：
- 多个主体但无策略互动（如多个独立的库存优化，需求互不影响）→ 仍是 optimization，只是多个 optimization 并行
- 单主体但面对随机环境（如 MDP）→ 是 optimization（随机优化），不是 game
- 主体间有资源竞争但无策略预期（如先到先得的资源分配）→ 可能是 queue + optimization，不一定是 game
- 交通分配中驾驶员选择路径 → 是 game（Wardrop UE = Nash 均衡），因为每个人的路径选择影响拥堵，进而影响他人的旅行时间

#### 子模式

| 子模式 | 描述 | 典型 L3 表述 | 典型 L4 求解 |
|---|---|---|---|
| 静态非合作博弈 | 同时行动，完全信息 | 标准式博弈（收益矩阵） | 最优反应/迭代删除劣策略 |
| 动态非合作博弈 | 序贯行动 | 扩展式博弈（博弈树） | 逆向归纳法 |
| 不完全信息博弈 | 收益/类型私有 | Bayesian 博弈 | Bayesian Nash 均衡 |
| 演化博弈 | 有限理性，种群动态 | 复制子方程（ODE） | 数值积分/ESS 分析 |
| 合作博弈 | 有约束力协议 | 特征函数 v(S) | Shapley 值/Core 计算 |
| 机制设计 | 逆向博弈：设计规则实现目标 | 激励相容约束 | 拍卖设计/匹配算法 |
| 双边匹配 | 两方主体互相选择 | 偏好排序 | Gale-Shapley 算法 |

#### 与 queue 和 flow balance 的组合

interaction/game 经常与其他 L2 模式组合出现：
- **queue + interaction/game**：服务台竞争（如多个出租车司机竞争乘客）、排队中的策略性放弃（join-or-balk 博弈）
- **flow balance + interaction/game**：交通分配（用户均衡）、网络拥塞博弈、路由博弈
- **resource constraint + interaction/game**：公共资源博弈（公地悲剧）、竞争下的资源分配

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| 博弈的核心是策略互动：参与者的决策相互依存 | "策略博弈的精髓在于参与者的决策相互依存" | 博弈论思考教程（经理人分享） | Tier 3 | high | 标准定义，Gibbons 教材第 1 章 |
| 交通分配中的用户均衡（Wardrop 第一原理）等价于 Nash 均衡 | "在所有人都是理性人的前提下，将执行自身利益最大化的决策，因此将达到一个均衡点...布雷斯悖论可以用博弈论中的纳什均衡概念来解释" | 布雷斯悖论科普（返朴，引用 Braess 1968） | Tier 2 | high | Wardrop (1952) + Braess (1968) 经典结果，交通网络博弈的标准分析 |
| 演化博弈描述有限理性主体通过学习/模仿达到均衡的动态过程 | "现有的博弈理论尚无法描述纳什均衡这样一个动态调整的实现过程...演化博弈已经成为生物种群和人类社会中主体间复杂交互行为分析的有效工具" | 演化博弈与合作机制研究（中国经济学人） | Tier 2 | high | 演化博弈的标准定位，Weibull《Evolutionary Game Theory》教材内容 |
| 机制设计是"逆向博弈论"：给定目标设计博弈规则 | "机制设计理论...激励相容...使行为人追求个人利益的行为，正好与组织实现集体价值最大化的目标相吻合" | 激励相容研究（引用 Hurwicz） | Tier 2 | high | Hurwicz 机制设计理论的核心思想 |
| 排队系统中顾客的 join-or-balk 决策构成策略性博弈 | （项目内 2019_C 问题卡标注："忽略司机与乘客的双边匹配（只建模一方）"为常见 LLM 错误） | 项目内 P15 benchmark 2019_C card.yaml | Tier 1（项目内研究） | high | 2019_C 的 GT 明确包含 game_theory，说明出租车-乘客互动具有博弈结构 |

---

## 3. L3 标签研究

### 3.1 graph（图论）—— 是否应成为一级标签？

#### 当前状态

在现有四层标签体系中，`graph` 被定位为 **L3 Mathematical Formulation**（数学表述形式），与 optimization、differential equation、probability、statistics、linear algebra 并列。当前知识库中 graph 的 L3 覆盖率为 **0 卡**（审计确认）。

#### 研究问题：graph 是否应该提升为 L1（Problem Structure）？

**论点 A：graph 应保持在 L3**
- 图是一种**数学表述工具**，如同矩阵、微分方程。一个问题可以用图来表述，但"用图表述"本身不决定问题的物理结构。
- 同一图结构可以承载完全不同的问题：最短路径（network/traffic）、图着色（scheduling）、社交网络分析（data/evaluation）。
- 保持 graph 在 L3 符合"数学表述形式"的定位：它描述的是"用什么数学语言写"，而非"问题是什么结构"。

**论点 B：graph 应提升为 L1**
- 许多竞赛问题的**第一识别特征**就是"这是一个图/网络问题"——拓扑结构是问题的骨架。
- CUMCM 中 2016_B（小区开放交通）、2019_C（机场出租车）、2021_D（连铸切割）等题，识别出"图结构"是建模的第一步。
- 如果 graph 只在 L3，LLM 可能在 L1 层无法激活"网络思维"，导致直接跳到 optimization/probability。

**论点 C：graph 应拆分为两个概念**
- `graph` 作为 L3 数学形式（邻接矩阵/邻接表/图论定理）
- `network/traffic` 作为 L1 问题结构（网络上的流动问题）
- 二者不重复：graph 是表述工具，network/traffic 是问题类型

#### 研究结论

**graph 应保持在 L3，但需要与 L1 network/traffic 明确区分和关联。**

理由：
1. graph 是**表述形式**，不是问题结构。图着色问题用 graph 表述，但属于 scheduling 域而非 network/traffic 域。
2. 当前 L1 已有 `network/traffic` 标签覆盖"网络上的流动问题"，这已经捕捉了"图结构+流动"的问题特征。
3. 真正的缺失不是"graph 不在 L1"，而是 **L1 network/traffic 和 L3 graph 均无卡覆盖**——需要的是补卡，而非调整层级。
4. graph 在 L3 的正确定位是：**所有需要用节点-边拓扑表述的问题的数学形式层**，包括但不限于 network/traffic。

**关联关系**：
```
L1 network/traffic ──必然──→ L3 graph（网络问题必须用图表述）
L3 graph ──不一定──→ L1 network/traffic（图可用于着色、匹配、调度等非流动问题）
```

#### graph 作为 L3 的核心内容

| 子领域 | 核心概念 | 对应 L4 算法 |
|---|---|---|
| 最短路 | 单源/全源最短路 | Dijkstra, Bellman-Ford, Floyd-Warshall |
| 网络流 | 最大流/最小割/最小费用流 | Ford-Fulkerson, Edmonds-Karp, Dinic |
| 匹配 | 二部图匹配/稳定匹配 | 匈牙利算法, Gale-Shapley |
| 生成树 | 最小生成树 | Kruskal, Prim |
| 图着色 | 顶点着色/区间调度 | 贪心/回溯 |
| 拓扑排序 | DAG 排序 | Kahn 算法/DFS |

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| 图论是离散数学的分支，研究顶点和边组成的图结构 | 项目内 graph-theory.md 方法论（基于 West《图论导引》和 CLRS《算法导论》） | Tier 1（项目内，引用标准教材） | high | 标准定义 |
| 网络流问题可表述为线性规划，图是其约束结构 | "网络流...与线性规划密切相关" | 网络流入门 | Tier 3 | high | CLRS 第 29 章证明最大流是 LP 的特例 |
| 同一图结构可用于不同问题类型（最短路/着色/匹配） | 项目内 graph-theory.md 涵盖最短路径、网络流、最小生成树、图着色等多种问题 | Tier 1（项目内） | high | 说明 graph 是跨问题类型的表述工具，不应提升为单一 L1 |
| Dijkstra 算法适用于非负权图的单源最短路径 | "Dijkstra算法用于求单源、无负权的最短路" | 算法入门教程 | Tier 3 | high | Dijkstra (1959) 标准结果 |
| 最大流-最小割定理：最大流的值等于最小割的容量 | "最小割最大流定理指出，最大流的值等于最小割的容量" | 网络流问题百科 | Tier 3 | high | Ford-Fulkerson 1956 经典定理 |

---

### 3.2 game-theoretic formulation（博弈论表述）—— 是否需要独立层级？

#### 当前状态

现有 L3 标签集为：optimization, differential equation, graph, probability, statistics, linear algebra。**没有 game-theoretic formulation 标签**。博弈论的数学表述目前隐含在 optimization（Nash 均衡可转化为互补问题/数学规划）和 probability（混合策略）中。

#### 研究问题：game-theoretic formulation 是否应成为独立的 L3 标签？

**论点 A：应独立为 L3 标签**
- 博弈论有独特的数学对象：收益矩阵、策略空间、均衡条件、特征函数。这些不是 optimization 的特例（虽然 Nash 均衡可通过 KKT 条件转化为数学规划，但概念框架不同）。
- 合作博弈的特征函数 $v(S)$ 和 Shapley 值完全不在 optimization 的标准框架内。
- 演化博弈的复制子动力学是 ODE 系统，但语义是博弈的，不应仅标记为 differential equation。
- 如果不独立，L3 层无法表达"这个问题的数学核心是博弈均衡"这一关键信息。

**论点 B：不需要独立，可归入 optimization**
- Nash 均衡的求解本质上是求解互补问题（complementarity problem）或变分不等式（variational inequality），这些是数学规划的扩展。
- 有限博弈的混合策略 Nash 可通过线性规划（两人零和）或非线性规划（一般和）求解。
- 保持 L3 标签简洁，避免标签膨胀。

**论点 C：分层处理**
- L3 主标签仍为 optimization（因为均衡求解最终是优化/互补问题）
- 增加 `game-theoretic` 作为 L3 的**修饰子标签**或 L2 interaction/game 的**必填 L3 映射**
- 即：L2 interaction/game → L3 optimization (game-theoretic) + probability (mixed strategy)

#### 研究结论

**game-theoretic formulation 应作为 L3 的独立标签（或至少是 optimization 的强修饰子标签）。**

理由：
1. **概念独立性**：博弈论的核心对象（收益函数、策略互动、均衡）与标准优化（单目标函数、约束）有本质区别。将博弈仅标记为 optimization 会丢失"多玩家策略互动"这一关键数学结构。
2. **求解器区分**：Nash 均衡求解器（如 Gambit、nashpy 的支持枚举法、同伦延拓法）与标准优化求解器（LP/NLP 求解器）是不同的算法族，需要在 L4 区分。L3 不独立则 L4 的 equilibrium algorithms 缺乏上层锚点。
3. **合作博弈无法归入 optimization**：Shapley 值、Core、Nucleolus 是公理化解概念，不是优化问题的解。
4. **与 L2 的映射完整性**：L2 有 interaction/game，L3 应有对应的数学表述标签，否则知识链断裂。

**建议的 L3 标签定位**：
```
L3: game-theoretic formulation
  ├── 标准式博弈 (normal form): 收益矩阵/多维数组
  ├── 扩展式博弈 (extensive form): 博弈树/信息集
  ├── 特征函数博弈 (coalitional form): v(S)
  ├── 演化博弈 (evolutionary): 复制子方程 (ODE)
  └── 机制设计: 激励相容约束 + 社会选择函数
```

**与其他 L3 标签的交叉**：
- game-theoretic + optimization：Nash 均衡转化为数学规划（互补问题）
- game-theoretic + probability：混合策略、Bayesian 博弈
- game-theoretic + differential equation：复制子动力学
- game-theoretic + linear algebra：收益矩阵运算、Shapley 值计算

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| Nash 均衡可转化为非线性互补问题（NCP）或变分不等式（VI） | （标准博弈论计算结果，McKelvey et al. 2006 的 Gambit 软件文档） | Tier 1（学术软件/论文） | high | 计算博弈论的标准方法，Nash 求解的数学基础 |
| 两人零和博弈的混合策略 Nash 均衡可通过线性规划求解 | （von Neumann 极小极大定理，1928） | Tier 1（经典定理） | high | von Neumann 的原始结果，LP 与博弈论的深刻联系 |
| 合作博弈的 Shapley 值是公理化解，不是优化问题的解 | "Shapley值：公平分配合作收益的唯一解...φᵢ(v) = Σ(|S|!(n-|S|-1)!/n!) × [v(S∪{i}) - v(S)]" | 项目内 game-theory.md | Tier 1（项目内） | high | Shapley (1953) 公理化定义，满足效率/对称/线性/哑元四条公理 |
| 演化博弈的复制子动力学是微分方程系统 | "演化博弈...复制子动力学...区域环境保护行动的演化路径具有初始敏感性" | 演化博弈分析（管理学年鉴） | Tier 2 | medium-high | 复制子方程 dx/dt = x_i(f_i(x) - φ(x)) 是标准 ODE 系统 |
| 博弈论计算需要专用求解器（Gambit, nashpy），与标准优化求解器不同 | 项目内 game-theory.md 推荐 "nashpy：Nash均衡计算; gambit：博弈论工具箱" | Tier 1（项目内） | high | 说明 L4 需要独立的 equilibrium algorithms 类别 |

---

## 4. L4 标签研究

### 4.1 flow algorithms（流算法）

#### 定位

flow algorithms 是 L4 Solver/Algorithm 层的标签，涵盖在图/网络上求解流动相关问题的算法族。它是 L3 graph 的求解层，也是 L2 flow balance 的计算实现。

#### 算法分类与详细研究

##### 4.1.1 最短路径算法

| 算法 | 适用条件 | 时间复杂度 | 核心思想 |
|---|---|---|---|
| Dijkstra | 非负权图，单源 | O((V+E)log V)（斐波那契堆） | 贪心：每次选最近未访问节点松弛 |
| Bellman-Ford | 允许负权，单源，可检负环 | O(VE) | 动态规划：松弛 V-1 轮 |
| Floyd-Warshall | 全源最短路，允许负权（无负环） | O(V³) | 动态规划：d[i][j] = min(d[i][j], d[i][k]+d[k][j]) |
| A* | 非负权，有启发函数 | 取决于启发式 | 贪心+启发：f(n)=g(n)+h(n) |

**适用场景**：路径规划、导航、网络路由、关键路径分析。

##### 4.1.2 最大流算法

| 算法 | 时间复杂度 | 核心思想 |
|---|---|---|
| Ford-Fulkerson | O(E·f_max)（整数容量） | 反复找增广路，直到无增广路 |
| Edmonds-Karp | O(VE²) | Ford-Fulkerson + BFS 选最短增广路 |
| Dinic | O(V²E) | BFS 分层 + DFS 阻塞流 |
| ISAP | O(V²E)（实践更快） | Dinic 的改进版，持续重标号 |
| Push-Relabel | O(V²√E) | 预流推进+重标号 |

**最大流-最小割定理**：最大流的值 = 最小割的容量。这是网络流的核心定理，建立了"流动"与"分割"的对偶关系。

##### 4.1.3 最小费用流算法

| 算法 | 核心思想 |
|---|---|
| 连续最短路法 | 每次找费用最小的增广路（SPFA/Bellman-Ford 处理负权） |
| 消圈法 | 先求最大流，再消负费用圈 |
| 网络单纯形法 | 线性规划单纯形法的网络特化版 |

**适用场景**：物流配送、供应链优化、交通分配（系统最优）。

##### 4.1.4 交通分配算法

| 算法 | 对应均衡 | 核心思想 |
|---|---|---|
| All-or-Nothing | 无拥堵 | 全部分配到最短路 |
| Frank-Wolfe | 用户均衡 (UE) | 凸优化的线性近似+线性搜索 |
| Method of Successive Averages (MSA) | 用户均衡 | 迭代加权平均 |
| 系统最优 (SO) | 系统最优 | 最小化总旅行时间（非均衡） |

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| Dijkstra 算法时间复杂度 O(V²)（朴素）或 O((V+E)log V)（堆优化） | "迪杰斯特拉算法...时间复杂度为O(V×V+E)...O(V×lgV+E×lgV)" | 算法入门教程 | Tier 3 | high | CLRS 第 24 章标准结果 |
| 最大流问题从 1950 年代 Ford-Fulkerson 开始研究，近年有近线性时间突破 | "从1950...最大流问题...新算法'快得离谱'" | 澎湃新闻（引用 2022 年突破） | Tier 2 | high | Ford & Fulkerson (1956) 开创，2022 年 Chen et al. 近线性时间算法是重大突破 |
| Frank-Wolfe 算法是交通分配用户均衡的标准求解方法 | "用户平衡法...TransCAD采用的是Frank-Wolf法" | TransCAD 资料 | Tier 2 | high | Frank-Wolfe (1956) 在交通分配中的应用是标准实践（Sheffi 1985） |
| 最小费用流可转化为线性规划，网络单纯形法是高效求解器 | （Ahuja 1993 教材标准内容） | Tier 1（教材） | high | 最小费用流的 LP 表述是标准结果 |

---

### 4.2 queuing solver（排队求解器）

#### 定位

queuing solver 是 L4 层标签，涵盖排队系统的求解方法，分为**解析求解**和**仿真求解**两大类。

#### 解析求解器

| 模型 | 求解方法 | 输出 |
|---|---|---|
| M/M/1 | 生灭过程稳态方程（闭式解） | P_n, L, Lq, W, Wq |
| M/M/c | 生灭过程稳态方程（含 Erlang C 公式） | P_0, Lq, Wq |
| M/M/1/K | 有限容量生灭过程 | P_n（含拒绝概率） |
| M/G/1 | Pollaczek-Khinchine 公式 | Lq（需 E[S] 和 Var[S]） |
| M/D/1 | M/G/1 特例（Var[S]=0） | Lq = λ²/(2μ(μ-λ)) |
| G/G/1 | 无闭式解，用近似公式（Kingman 界） | Wq ≈ (λ² Var(S) + Var(A)) / (2(1-ρ))（上界） |
| 排队网络 | Jackson 定理（产品形式解） | 各节点独立 M/M/1 分析 |

**解析求解的验证**：
- 生灭过程的稳态方程：$\lambda_n P_n = \mu_{n+1} P_{n+1}$
- 归一化条件：$\sum P_n = 1$
- Little's Law 交叉验证

#### 仿真求解器

| 方法 | 描述 | 工具 |
|---|---|---|
| 离散事件仿真 (DES) | 事件驱动：到达事件/离开事件，维护事件队列 | SimPy, AnyLogic, Arena |
| 蒙特卡洛仿真 | 随机抽样到达和服务时间，统计稳态指标 | 自定义 Python/MATLAB |
| 连续时间马尔可夫链 (CTMC) 仿真 | Gillespie 算法 | 自定义 |

**仿真验证要点**：
1. Warm-up period：删除初始瞬态数据
2. 多次独立运行（≥5 次，种子固定为 42 及变体）
3. 置信区间报告（均值 ± 标准差）
4. 与解析解对比（在可解析的场景下）
5. Little's Law 自检

#### 解析 vs 仿真的选择决策树

```
排队问题求解
├── 到达/服务是否为标准分布？
│   ├── 是（M/M/1, M/M/c, M/G/1）
│   │   ├── 系统结构简单？
│   │   │   ├── 是 → 解析公式（闭式解）
│   │   │   └── 否（排队网络/复杂规则）→ Jackson 定理 或 仿真
│   └── 否（G/G/1, 非平稳, 复杂行为）
│       ├── 可否用近似公式？→ Kingman 界/扩散近似
│       └── 否 → 离散事件仿真
└── 需要瞬态/分布/极端事件分析？
    ├── 是 → 仿真
    └── 否（仅稳态均值）→ 解析优先
```

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| M/M/1 通过生灭过程稳态方程求解，有闭式解 | 项目内 queueing-theory.md 完整推导 P_n, L, Lq, W, Wq | Tier 1（项目内） | high | 标准结果 |
| G/G/1 无闭式解，Kingman 公式给出上界近似 | （Gross & Harris 1998 教材标准内容） | Tier 1（教材） | high | Kingman (1962) 的经典近似 |
| Jackson 定理证明了开放排队网络具有产品形式稳态解 | （Jackson 1957，标准排队网络理论） | Tier 1（经典论文） | high | 排队网络的基础定理 |
| 离散事件仿真通过事件队列驱动，适用于复杂排队系统 | "随机服务系统即排队系统...要描述一个排队系统需要描述三个方面的内容：输入过程、服务时间、排队方式" | 中国科技论文在线（基于 MATLAB 的 DES 建模） | Tier 2 | high | DES 的标准建模方法 |
| 仿真需要多次运行取平均并报告置信区间 | 项目内 env 配置：multi_run_count=5, random_seed=42 | Tier 1（项目内规范） | high | 项目 AGENTS.md 明确要求多种子运行≥5次 |

---

### 4.3 equilibrium algorithms（均衡求解算法）

#### 定位

equilibrium algorithms 是 L4 层标签，涵盖博弈均衡的计算方法。这是当前知识库**完全缺失**的 L4 类别（审计确认：无任何 game theory 卡）。

#### 算法分类

##### 4.3.1 有限博弈 Nash 均衡求解

| 算法 | 适用博弈 | 核心思想 |
|---|---|---|
| 支持枚举法 (Support Enumeration) | 两人有限博弈 | 枚举所有可能的支持集，解线性方程组 |
| 迭代删除劣策略 (IESDS) | 任意有限博弈 | 反复删除严格劣策略，缩小策略空间 |
| 最优反应动态 (Best Response Dynamics) | 势博弈 (potential games) | 每轮各玩家选最优反应，收敛到纯策略 Nash |
| 虚构博弈 (Fictitious Play) | 两人零和/某些博弈 | 每轮对对手历史平均策略做最优反应 |
| 同伦延拓法 (Homocontinuation) | 一般有限博弈 | 从简单博弈的已知均衡连续变形到目标博弈 |
| 全局 Newton 法 | 一般 n 人博弈 | 求解 Nash 均衡的 KKT/互补条件 |

##### 4.3.2 连续策略博弈

| 方法 | 描述 |
|---|---|
| KKT 条件转化 | Nash 均衡 ↔ 非线性互补问题 (NCP) ↔ 变分不等式 (VI) |
| 变分不等式求解 | 投影梯度法、超平面梯度法 |
| 数学规划 with 均衡约束 (MPEC) | 双层优化：上层优化，下层 Nash 均衡 |

##### 4.3.3 演化博弈动力学

| 方法 | 描述 |
|---|---|
| 复制子动力学数值积分 | 求解 ODE 系统 dx/dt = x_i(f_i(x) - φ(x)) |
| ESS 检验 | 验证策略是否满足 Maynard Smith 的 ESS 两个条件 |
| 多智能体强化学习 | Q-learning / 策略梯度收敛到 Nash（在特定条件下） |

##### 4.3.4 合作博弈求解

| 解概念 | 求解方法 | 复杂度 |
|---|---|---|
| Shapley 值 | 枚举所有联盟（O(2^n)），或近似采样 | #P-complete（一般） |
| Core | 线性规划可行性检验 | 多项式（LP） |
| Nucleolus | 序列线性规划 | 多项式 |
| 稳定匹配 | Gale-Shapley 算法 | O(n²) |

#### 均衡求解的验证

1. **单边偏离检验**：对求得的均衡，检查每个玩家是否有激励偏离
2. **多均衡检测**：用不同初始点/方法求解，确认是否找到所有均衡
3. **稳定性分析**：对演化博弈，分析均衡点的 Jacobian 矩阵特征值
4. **与解析解对比**：在可解析的简单博弈（如囚徒困境）上验证算法正确性

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| 有限博弈的 Nash 均衡可通过支持枚举法精确求解 | 项目内 game-theory.md 实现了 find_pure_nash() 和 mixed_strategy_nash_2p() | Tier 1（项目内） | high | 标准计算博弈论方法 |
| 势博弈中最优反应动态收敛到纯策略 Nash 均衡 | （Monderer & Shapley 1996 势博弈理论） | Tier 1（经典论文） | high | 势博弈的核心定理 |
| Nash 均衡计算是 PPAD-complete（一般情况） | （Daskalakis, Goldberg, Papadimitriou 2009） | Tier 1（经典论文） | high | 计算复杂性结果，说明一般 Nash 求解困难 |
| Gale-Shapley 算法在 O(n²) 时间内求稳定匹配 | （Gale & Shapley 1962） | Tier 1（经典论文） | high | 2012 Nobel 经济学奖工作 |
| 演化博弈的复制子动力学可用 ODE 数值积分求解 | "演化博弈...复制子动力学...系统具有异常复杂的演进动态" | 演化博弈分析（管理学年鉴） | Tier 2 | medium-high | 复制子方程是标准 ODE 系统，可用 Runge-Kutta 等方法积分 |

---

### 4.4 simulation（仿真）

#### 定位

simulation 是 L4 层标签，涵盖通过计算机模拟来求解/验证模型的方法。在本域中，simulation 主要用于：
- 排队系统的仿真（当解析模型不适用时）
- 交通流的微观仿真（跟驰模型、多智能体仿真）
- 博弈的演化仿真（多智能体学习、重复博弈模拟）
- 网络流的随机仿真（随机容量/随机需求下的网络性能）

#### 仿真方法分类

| 方法 | 时间推进 | 适用场景 | 本域应用 |
|---|---|---|---|
| 离散事件仿真 (DES) | 事件跳跃 | 排队系统、调度 | 机场出租车排队、物流 |
| 基于 Agent 的仿真 (ABS) | 时间步进/事件 | 多智能体系统 | 交通流微观仿真、演化博弈 |
| 蒙特卡洛仿真 | 独立抽样 | 不确定性传播 | 随机网络性能、排队指标 |
| 系统动力学 (SD) | 时间步进 | 宏观反馈系统 | 交通流宏观模型、人口流 |

#### 仿真在本域的特殊角色

simulation 在网络与博弈域中具有**双重角色**：
1. **求解器**：当解析方法不可行时（G/G/1 排队、复杂交通网络、大规模博弈），仿真是主要求解手段
2. **验证器**：当解析模型给出结果后，仿真用于验证假设的合理性和模型的鲁棒性

**项目规范要求**：random_seed=42，multi_run_count≥5，报告均值与标准差。

#### 与 mc-monte-carlo 卡的关系

当前知识库有 `mc-monte-carlo` 卡（family=uncertainty_propagation），但它定位为**通用不确定性传播**，不专门覆盖：
- 离散事件仿真的事件调度机制
- 基于 Agent 的多智能体交互仿真
- 排队系统的稳态分析（warm-up、batch means）

因此，即使有 mc-monte-carlo 卡，本域仍需要**专门的排队仿真/网络仿真知识**。

#### 证据

| claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|
| 离散事件仿真适用于重新设计/改进流程，蒙特卡洛适用于评估风险/不确定性 | "如果您正在尝试重新设计或改进过程，则离散事件模拟是正确的选择...如果您的目标是评估过程的风险、不确定性或找到最佳设置，则 Monte Carlo 模拟更适合您" | Minitab 仿真对比 | Tier 2 | medium-high | 该区分在仿真领域是标准实践 |
| 基于 Agent 的仿真是交通流微观仿真的主流方法 | "基于智能代理的交通分配建模...微观交通分配从驾驶员个体出发挖掘交通流内在特性" | 基于智能代理的交通分配（电子技术应用） | Tier 2 | medium-high | ABS 在交通仿真中的应用是活跃研究方向 |
| 仿真需要 warm-up period 分析以消除初始瞬态 | （项目内 env 配置 + 排队论方法论中的 simulate() 方法） | Tier 1（项目内规范） | high | 仿真方法论的标准要求（Law & Kelton 2000） |
| 项目要求随机种子固定 42，多运行≥5次 | AGENTS.md: "随机种子固定为42：多种子运行≥5次，报告均值与标准差" | Tier 1（项目宪法） | high | 项目铁律 |

---

## 5. L1→L2→L3→L4 映射表

### 5.1 本域完整知识链

| L1 Problem Structure | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 典型问题 |
|---|---|---|---|---|
| **network/traffic** | flow balance | graph + optimization | Dijkstra / Bellman-Ford | 最短路径、导航 |
| **network/traffic** | flow balance | graph + optimization (LP) | Edmonds-Karp / Dinic | 最大流、网络容量 |
| **network/traffic** | flow balance | graph + optimization (LP) | 最小费用流算法 / 网络单纯形 | 物流配送、供应链 |
| **network/traffic** | flow balance + interaction/game | graph + game-theoretic + optimization | Frank-Wolfe (UE) / 变分不等式 | 交通分配、路径选择博弈 |
| **network/traffic** | queue | probability (生灭过程) | M/M/c 解析 / DES | 机场出租车、通信网络 |
| **network/traffic** | flow balance + queue | graph + probability | 排队网络 (Jackson) / DES | 物流网络、多级服务系统 |
| **network/traffic** | flow balance | graph + differential equation | LWR 模型数值解 / 微观跟驰仿真 | 交通流宏观/微观模型 |
| **competition/game** | interaction/game | game-theoretic (标准式) | 支持枚举 / IESDS / 最优反应 | 定价博弈、寡头竞争 |
| **competition/game** | interaction/game | game-theoretic (扩展式) | 逆向归纳法 | 动态博弈、序贯决策 |
| **competition/game** | interaction/game | game-theoretic + probability | Bayesian Nash 求解 | 拍卖、不完全信息竞争 |
| **competition/game** | interaction/game | game-theoretic + differential equation | 复制子动力学数值积分 / ESS 检验 | 演化博弈、合作演化 |
| **competition/game** | interaction/game | game-theoretic (特征函数) | Shapley 值 / Core (LP) / Gale-Shapley | 合作分配、稳定匹配 |
| **competition/game** | interaction/game + resource constraint | game-theoretic + optimization | MPEC / 双层优化 | 竞争下的资源分配 |
| **competition/game** | interaction/game + queue | game-theoretic + probability | 排队博弈 / DES + 均衡迭代 | 策略性排队、服务台竞争 |
| **network/traffic + competition/game** | flow balance + interaction/game | graph + game-theoretic | 网络拥塞博弈求解 / Braess 分析 | 交通网络博弈、路由博弈 |

### 5.2 跨域映射（本域标签与其他域的组合）

| 组合 | L1 | L2 | L3 | L4 | 说明 |
|---|---|---|---|---|---|
| 网络+决策 | network/traffic + decision | flow balance | graph + optimization + linear algebra | 最短路 + AHP | 路径选择+多准则评价 |
| 博弈+不确定性 | competition/game + uncertainty | interaction/game | game-theoretic + probability | Bayesian Nash + Monte Carlo | 不完全信息博弈 |
| 排队+调度 | network/traffic + scheduling | queue + resource constraint | probability + optimization | 排队解析 + 调度算法 | 服务台排班 |
| 网络+扩散 | network/traffic + diffusion | flow balance + conservation law | graph + differential equation | 网络 PDE 数值解 | 网络上的扩散/传播 |

---

## 6. 真实竞赛题映射

### 6.1 2019_C（机场出租车）

#### 题目概述

机场出租车调度问题：研究机场到达大厅出租车排队系统的运行规律，分析出租车司机在"等待载客"与"空驶返回市区"之间的决策行为，优化调度策略以提高系统效率。

#### 四层映射

| 层 | 标签 | 具体内容 |
|---|---|---|
| **L1 Problem Structure** | network/traffic + decision | 出租车-乘客构成服务网络；司机在等待/返回间做决策 |
| **L2 Modeling Pattern** | queue + flow balance + interaction/game | 乘客到达排队（queue）；出租车流的进出平衡（flow balance）；司机与乘客的双边匹配/博弈（interaction/game） |
| **L3 Mathematical Formulation** | probability + optimization + game-theoretic | 排队的生灭过程（probability）；调度优化（optimization）；司机决策博弈（game-theoretic） |
| **L4 Solver/Algorithm** | queuing solver + optimization + simulation + equilibrium | M/M/c 解析排队；成本收益优化；蒙特卡洛/DES 仿真；Nash 均衡分析 |

#### 子问题分解

| 子问题 | 核心建模路线 | 为什么合理 |
|---|---|---|
| Q1: 建立排队模型 | M/M/c 排队模型（乘客泊松到达，出租车指数服务，多服务台=多辆出租车同时上客） | 机场到达具有随机性，出租车服务时间（装行李+上车）近似指数分布，多辆出租车并行服务 → M/M/c 是标准选择 |
| Q2: 司机决策分析 | 决策论/MDP：比较"等待的期望收益"与"空驶返回的期望收益"；或博弈论：多司机竞争下的均衡策略 | 司机是理性决策者，其选择影响排队长度，排队长度又影响后续司机的选择 → 存在策略互动，博弈论比纯决策论更准确 |
| Q3: 调度优化 | 优化模型：最小化平均等待时间/最大化系统吞吐量，约束为排队平衡+司机理性 | 调度目标是系统级优化，但需考虑司机的个体理性（激励相容）→ 机制设计视角 |
| Q4: 仿真验证 | 离散事件仿真/蒙特卡洛：模拟乘客到达-出租车服务-司机决策的完整过程 | 解析模型有分布假设限制，仿真可处理复杂场景（非平稳到达、司机异质性），并验证解析结果 |

#### 为什么这种建模路线是合理的

1. **queue 是核心**：题目本质是"乘客等车+车等乘客"的双边排队系统，排队论是最直接的建模工具。M/M/c 的假设（泊松到达、指数服务）在机场场景下有经验支持（航班到达批次内乘客近似泊松到达）。
2. **flow balance 隐含其中**：出租车从市区→机场（流入），从机场→市区（流出），机场蓄车池是节点存量。动态流量平衡描述蓄车池长度的变化。
3. **interaction/game 不可忽略**：多个出租车司机的决策相互影响——如果所有人都选择等待，排队变长，等待时间增加，个体收益下降；如果所有人都选择返回，等待的司机获得更高收益。这是典型的策略互动，纯优化（假设司机行为固定）会遗漏均衡分析。
4. **simulation 是必要验证**：解析排队模型假设平稳到达，但机场到达有明显的航班批次性（非平稳），仿真可以处理这种复杂性。

#### 现有知识库的覆盖缺口

| 层 | 需要 | 现有 | 缺口 |
|---|---|---|---|
| L1 | network/traffic | 0 卡 | **完全缺失** |
| L2 | queue, flow balance, interaction/game | 0 卡 | **完全缺失** |
| L3 | probability, optimization, game-theoretic | probability ✓ (4卡), optimization ✓ (5卡), game-theoretic ✗ | game-theoretic 缺失 |
| L4 | queuing solver, simulation, equilibrium | simulation ✓ (mc-monte-carlo, 通用), queuing ✗, equilibrium ✗ | queuing 和 equilibrium 缺失 |

**审计结论**：2019_C 的 method_selection=100 是**浅层命中/假阳性**——仅在 L3/L4 的 optimization 和 Monte Carlo 层面碰巧匹配，L1/L2 完全缺失。

---

### 6.2 2020_B（穿越沙漠）—— 博弈部分

#### 题目概述

穿越沙漠问题：玩家在沙漠地图上行走，消耗水和食物资源，天气随机（晴朗/高温/沙暴），可在村庄购买资源、在矿山挖矿赚钱。Q3 涉及多个玩家同时穿越沙漠的竞争场景。

#### 四层映射（聚焦博弈部分）

| 层 | 标签 | 具体内容 |
|---|---|---|
| **L1 Problem Structure** | competition/game + scheduling + decision | 多玩家竞争（Q3）；资源调度；单玩家序贯决策 |
| **L2 Modeling Pattern** | interaction/game + state transition + resource constraint | 多玩家策略互动（Q3）；MDP 状态转移（位置/资源/天气）；资源约束（水/食物/资金） |
| **L3 Mathematical Formulation** | game-theoretic + optimization + probability | 博弈均衡（Q3）；动态规划/整数规划；天气随机（Markov 链） |
| **L4 Solver/Algorithm** | equilibrium algorithms + DP + Monte Carlo | Nash 均衡求解；值迭代/策略迭代；蒙特卡洛模拟 |

#### 博弈部分（Q3）的建模路线

| 要素 | 建模选择 | 为什么合理 |
|---|---|---|
| 玩家 | 2-3 个独立决策者 | 题目明确多玩家场景 |
| 策略 | 每日行动选择（行走/停留/挖矿）+ 资源购买 | 策略空间是离散的行动序列 |
| 收益 | 最终资金（扣除资源消耗） | 题目目标是最大化收益 |
| 互动 | 资源购买竞争（村庄资源有限？）、挖矿收益分配、到达顺序奖励 | 如果村庄资源或矿山收益有竞争性，则玩家收益交叉依赖 → 博弈 |
| 均衡 | Nash 均衡：没有玩家可通过单方面改变策略提高收益 | 多玩家竞争的标准解概念 |
| 求解 | 扩展式博弈逆向归纳（如果行动有序贯性），或标准式博弈 Nash 求解 | 沙漠穿越是序贯决策，扩展式更自然 |

#### 为什么博弈建模是合理的

1. **多玩家 + 收益交叉依赖 = 博弈**：如果多个玩家共享有限资源（村庄补给、矿山收益），则一个玩家的购买/挖矿决策影响其他玩家的可获得资源 → 策略互动存在。
2. **序贯决策 = 扩展式博弈**：每日行动有先后（或同时但有状态依赖），适合用博弈树+逆向归纳。
3. **天气随机 = 不完全信息/随机博弈**：天气是公共随机变量，所有玩家观察到相同天气，构成随机博弈（stochastic game）。
4. **与单玩家 DP 的关系**：Q1/Q2 的单玩家最优策略是 Q3 博弈分析的基础——每个玩家的单玩家最优策略构成博弈的"威胁点"或基准。

#### 现有知识库的覆盖缺口

| 层 | 需要 | 现有 | 缺口 |
|---|---|---|---|
| L1 | competition/game, scheduling, decision | decision ✓ (5卡), competition/game ✗, scheduling ✗ | competition/game 和 scheduling 缺失 |
| L2 | interaction/game, state transition, resource constraint | state transition ✓ (时序语境, 3卡), interaction/game ✗, resource constraint ✗ | interaction/game 和 resource constraint 缺失；state transition 无决策语境 |
| L3 | game-theoretic, optimization, probability | optimization ✓, probability ✓, game-theoretic ✗ | game-theoretic 缺失 |
| L4 | equilibrium, DP, Monte Carlo | Monte Carlo ✓ (mc-monte-carlo), DP ✗, equilibrium ✗ | DP 和 equilibrium 缺失 |

**审计结论**：2020_B 的 method_selection=0，根本原因是 L2 interaction/game + L4 DP/equilibrium 双重缺失。LLM 选择了 mc-ga 作为通用优化器替代，但 GA 与 DP/MDP/game_theory 是不同求解范式。

---

### 6.3 2016_B（小区开放交通）

#### 题目概述

小区开放对周边道路通行的影响研究：分析封闭小区开放后，城市路网结构变化对交通流量、通行效率的影响。

#### 四层映射

| 层 | 标签 | 具体内容 |
|---|---|---|
| **L1 Problem Structure** | network/traffic | 城市路网是典型网络结构，研究流量分配 |
| **L2 Modeling Pattern** | flow balance + interaction/game | 路网节点流量平衡；驾驶员路径选择构成用户均衡（Nash 均衡） |
| **L3 Mathematical Formulation** | graph + optimization + game-theoretic | 路网图论表述；交通分配数学规划；用户均衡博弈 |
| **L4 Solver/Algorithm** | flow algorithms + equilibrium algorithms | 最短路/最小费用流；Frank-Wolfe (UE)；Braess 悖论分析 |

#### 建模路线合理性

1. **小区开放 = 路网拓扑变化**：开放小区内部道路为公共道路，增加了网络的边和节点，改变了 OD 对之间的可选路径。
2. **流量重新分配 = 用户均衡**：开放后驾驶员重新选择路径，达到新的 Wardrop 用户均衡。这是 Nash 均衡在交通网络上的特例。
3. **Braess 悖论的警示**：增加道路不一定提高通行效率（Braess 1968），需要通过均衡分析验证开放效果。
4. **flow balance 是约束基础**：无论开放前后，每个路口的流量都满足节点平衡。

#### 证据

| claim | evidence | source | confidence |
|---|---|---|---|
| 大型封闭小区是城市交通微循环的"栓塞"，开放可增加路网密度 | "大型小区是阻碍城市交通微循环的顽固'栓塞'，必须逐步打开" | 新民周刊（2016） | medium |
| 街区制/密路网是国际城市规划的主流模式 | "西方城市...常见的小街区、密路网的街区制模式" | 澎湃新闻（2016） | medium |
| 增加道路可能降低效率（Braess 悖论），需用 Nash 均衡分析 | "布雷斯悖论...增加道路反而可能让交通状况变得更糟...用博弈论中的纳什均衡概念来解释" | 返朴（引用 Braess 1968） | high |

---

### 6.4 竞赛题映射汇总

| 题目 | L1 | L2 | L3 | L4 | 核心缺失层 |
|---|---|---|---|---|---|
| 2019_C 机场出租车 | network/traffic + decision | queue + flow balance + interaction/game | probability + optimization + game-theoretic | queuing + optimization + simulation + equilibrium | L1 + L2（全缺） |
| 2020_B 穿越沙漠(博弈) | competition/game + scheduling | interaction/game + state transition + resource constraint | game-theoretic + optimization + probability | equilibrium + DP + Monte Carlo | L2 interaction + L4 DP/equilibrium |
| 2016_B 小区开放 | network/traffic | flow balance + interaction/game | graph + optimization + game-theoretic | flow algorithms + equilibrium (Frank-Wolfe) | L1 + L2 + L3 graph |

---

## 7. 证据记录

### 7.1 高置信度结论（confidence = high）

| ID | claim | evidence | source | source_type |
|---|---|---|---|---|
| E01 | 网络流的核心约束是节点流量守恒（除源汇外净流为零） | Ford-Fulkerson 标准定义，Ahuja 教材 | Tier 1 |
| E02 | 博弈论与决策论的根本区别是参与者数量≥2 且收益交叉依赖 | Gibbons 教材第1章，Nash 1950 | Tier 1 |
| E03 | Nash 均衡：无人可通过单边偏离提高收益 | Nash 1950 PNAS | Tier 1 |
| E04 | Kendall 记号 A/B/c 是排队系统标准分类 | Kendall 1953 | Tier 1 |
| E05 | Little's Law L=λW 模型无关，适用于任何稳定系统 | Little 1961 OR | Tier 1 |
| E06 | M/M/1 稳定条件 ρ<1，有闭式稳态解 | Cooper 1981 教材 | Tier 1 |
| E07 | 最大流-最小割定理 | Ford-Fulkerson 1956 | Tier 1 |
| E08 | Dijkstra 适用于非负权单源最短路 | Dijkstra 1959, CLRS | Tier 1 |
| E09 | Wardrop 用户均衡等价于 Nash 均衡 | Wardrop 1952, Braess 1968 | Tier 1 |
| E10 | Braess 悖论：增加道路可能降低整体效率 | Braess 1968 | Tier 1 |
| E11 | Shapley 值是合作博弈的公理化解 | Shapley 1953 | Tier 1 |
| E12 | 演化稳定策略 ESS 由 Maynard Smith & Price 1973 提出 | Maynard Smith 1973 Nature | Tier 1 |
| E13 | 机制设计核心是激励相容（Hurwicz） | Hurwicz 1960, 2007 Nobel | Tier 1 |
| E14 | 投入产出模型（Leontief）是经济网络的节点平衡 | Leontief 1936, 国家统计局 | Tier 1 |
| E15 | 2019_C 的 GT 包含 queuing_theory + game_theory + optimization + simulation | 项目内 gt.json + card.yaml | Tier 1（项目内） |
| E16 | 2020_B 的 GT 包含 game_theory + dynamic_programming + MDP | 项目内 gt.json + card.yaml | Tier 1（项目内） |
| E17 | 当前知识库 L1 network/traffic 和 competition/game 均 0 卡覆盖 | 项目内知识架构审计 | Tier 1（项目内） |
| E18 | 当前知识库 L2 queue/flow balance/interaction 均 0 卡覆盖 | 项目内知识架构审计 | Tier 1（项目内） |
| E19 | 2019_C method_selection=100 是浅层命中（L1/L2 全缺） | 项目内审计第 4.2 节 | Tier 1（项目内） |
| E20 | 项目要求随机种子 42，多运行≥5次 | AGENTS.md 铁律 | Tier 1（项目宪法） |

### 7.2 中等置信度结论（confidence = medium-high / medium）

| ID | claim | evidence | source | source_type |
|---|---|---|---|---|
| E21 | conservation law 与 flow balance 的区别是连续场微分守恒 vs 离散网络代数平衡 | 流体力学 NS 方程 + 网络流定义的分析性对比 | Tier 2/3 交叉 |
| E22 | G/G/1 无闭式解，Kingman 公式给出上界近似 | Gross & Harris 1998 | Tier 1（教材，但未直接引用原文） |
| E23 | Frank-Wolfe 是交通分配 UE 的标准求解器 | TransCAD 文档 + Sheffi 1985 | Tier 2 |
| E24 | 基于 Agent 的仿真是交通流微观仿真的主流方法 | 电子技术应用期刊文章 | Tier 2 |
| E25 | 演化博弈的复制子动力学是 ODE 系统，可用数值积分求解 | 管理学年鉴文章 + Weibull 教材 | Tier 2 |
| E26 | 排队博弈（join-or-balk）中顾客的策略性决策构成博弈 | 项目内 2019_C card 标注的常见错误 | Tier 1（项目内，间接推断） |
| E27 | 小区开放可增加路网密度、改善微循环 | 新民周刊/澎湃新闻（2016） | Tier 2（新闻评论，非学术证据） |

### 7.3 证据来源统计

| source_type | 数量 | 占比 |
|---|---|---|
| Tier 1（教材/经典论文/项目内研究/官方） | 20+ | ~65% |
| Tier 2（专业期刊/大学出版社/高质量文章） | 8+ | ~25% |
| Tier 3（百科/博客/教程，仅用于定义和关键词发现） | 3+ | ~10% |

---

## 8. 争议与不确定项

### 8.1 UNCERTAIN: graph 是否应提升为 L1

**状态**：研究结论为"保持 L3"，但存在合理争议。

- **支持提升的论点**：图结构是许多竞赛问题的第一识别特征，L1 缺失 graph 可能导致 LLM 无法激活"网络思维"。
- **反对提升的论点**：graph 是表述工具，同一图可用于多种问题类型（着色/匹配/最短路），提升为 L1 会与现有 L1 标签（network/traffic, scheduling）重叠。
- **折中方案**：保持 graph 在 L3，但在 L1 network/traffic 的定义中明确"必须以 graph 为 L3 表述"，建立强关联。
- **需要进一步研究**：分析 CUMCM 历年题中"用图表述但不属于 network/traffic"的题目比例，量化 graph 作为 L1 的边际价值。

### 8.2 UNCERTAIN: game-theoretic formulation 作为 L3 独立标签的粒度

**状态**：研究结论为"应独立"，但具体粒度待定。

- **粗粒度**：L3 仅增加一个 `game-theoretic` 标签，覆盖所有博弈表述。
- **细粒度**：L3 增加 `game-theoretic-normal-form`, `game-theoretic-extensive-form`, `game-theoretic-coalitional`, `game-theoretic-evolutionary` 四个子标签。
- **建议**：v0.1 先用粗粒度（一个 `game-theoretic` 标签），后续根据覆盖需求细化。

### 8.3 UNCERTAIN: 2019_C 中 interaction/game 的强度

**状态**：GT 标注包含 game_theory，但博弈在题目中的核心程度存在争议。

- **强博弈解读**：多个出租车司机竞争乘客，司机的等待/返回决策相互影响 → 非合作博弈。
- **弱博弈解读**：司机决策主要基于排队长度（可视为外部状态），如果假设司机是价格接受者（不考虑自身决策对排队的影响），则是决策论/MDP 而非博弈。
- **影响**：如果博弈是弱的，则 L2 interaction/game 在 2019_C 中的权重应降低，核心 L2 是 queue + flow balance。
- **需要**：阅读 2019_C 完整题面，确认 Q2/Q3 是否明确涉及多司机竞争。

### 8.4 UNCERTAIN: 解析排队模型在机场场景的适用性

**状态**：M/M/c 是标准选择，但机场到达的非平稳性可能违反假设。

- 机场乘客到达具有明显的航班批次性（航班到达后短时间内大量乘客涌出），这不是平稳泊松过程。
- 可能需要用非平稳排队模型（Mt/M/c）或批次到达模型（M[x]/M/c）。
- 但在竞赛时间限制下，M/M/c + 仿真验证是合理的工程近似。
- **建议**：方法卡应明确标注"泊松到达假设需检验，非平稳场景需仿真补充"。

### 8.5 UNCERTAIN: simulation 作为 L4 标签的范围

**状态**：simulation 是跨域 L4 标签，在本域的具体范围需界定。

- simulation 涵盖 DES、ABS、Monte Carlo、SD 等多种方法，是否应全部归入一个 L4 标签？
- 当前 mc-monte-carlo 卡定位为 uncertainty_propagation，是否应重新标注为覆盖 simulation 的更多子类型？
- **建议**：L4 simulation 作为顶层标签，子类型（DES/ABS/MC）在方法卡内部区分。

### 8.6 UNCERTAIN: flow balance 与 conservation law 的边界在实际问题中的判定

**状态**：理论区分清晰（连续场 vs 离散网络），但实际问题可能模糊。

- 例如：城市交通流的宏观 LWR 模型是 PDE（conservation law），但同一问题的网络级交通分配是 flow balance。
- 同一问题可能同时需要两种模式（微观用 LWR，网络用 flow balance）。
- **建议**：方法卡应提供"判定流程图"：问题的空间结构是连续场还是离散网络？连续→conservation law；离散→flow balance。

---

## 9. 对知识架构校准的建议

### 9.1 本域优先级排序

| 优先级 | 动作 | 理由 |
|---|---|---|
| **P0** | 建立 L1 network/traffic 和 competition/game 标签定义 | 当前 0 覆盖，是路由缺失的根源 |
| **P0** | 建立 L2 queue, flow balance, interaction/game 标签定义 | L2 是全库覆盖率最低层（25%），本域三个标签全缺 |
| **P1** | L3 增加 game-theoretic 标签 | L2 interaction/game 需要 L3 锚点 |
| **P1** | L4 增加 queuing solver 和 equilibrium algorithms 标签 | 2019_C 和 2020_B 的核心求解器缺失 |
| **P2** | L3 graph 保持但补卡 | graph 是 network/traffic 的必要表述形式 |
| **P2** | L4 simulation 子类型细化 | DES/ABS 与通用 Monte Carlo 区分 |

### 9.2 方法卡设计方向（Constraint/Prior/Validation）

> 以下为设计方向，不创建实际卡片。

#### 潜在卡 1：mc-queuing-analysis（排队分析）
- **L1**：network/traffic
- **L2**：queue
- **L3**：probability（生灭过程）
- **L4**：queuing solver（解析 + DES）
- **requires**：到达/服务随机性可观测；系统可近似为 Markov
- **supports**：M/M/1, M/M/c, M/G/1 稳态分析；Little's Law 验证
- **risks**：泊松假设不满足（非平稳到达）；ρ→1 时解析解不稳定；忽略顾客放弃行为
- **verification**：分布拟合检验（K-S/χ²）；Little's Law 自检；解析-仿真对比；灵敏度分析

#### 潜在卡 2：mc-network-flow（网络流）
- **L1**：network/traffic
- **L2**：flow balance
- **L3**：graph + optimization (LP)
- **L4**：flow algorithms（Dijkstra/Edmonds-Karp/最小费用流）
- **requires**：问题可表述为节点-边网络；流量有容量约束
- **supports**：最短路/最大流/最小费用流/交通分配
- **risks**：忽略拥堵效应（边权不随流量变化）；整数流假设；多商品流复杂度
- **verification**：流量守恒检验；容量约束检验；对偶验证（最大流=最小割）

#### 潜在卡 3：mc-game-equilibrium（博弈均衡分析）
- **L1**：competition/game
- **L2**：interaction/game
- **L3**：game-theoretic
- **L4**：equilibrium algorithms（支持枚举/逆向归纳/复制子动力学）
- **requires**：≥2 个独立决策者；收益交叉依赖可建模
- **supports**：Nash 均衡求解；ESS 分析；Shapley 值；稳定匹配
- **risks**：多均衡选择问题；收益矩阵设定无依据；有限理性假设下 Nash 不适用；计算复杂度（PPAD-complete）
- **verification**：单边偏离检验；多均衡检测；与解析解对比；演化稳定性分析

### 9.3 not_for 约束设计

| 卡 | not_for（不适用的 L1/L2） | 理由 |
|---|---|---|
| mc-queuing-analysis | L1: scheduling（纯确定性调度无随机排队）；L2: conservation law（物理守恒非排队） | 排队论需要随机到达/服务，纯调度不适用 |
| mc-network-flow | L1: competition/game（纯博弈无网络流）；L2: queue（排队不是网络流） | 网络流需要图拓扑+流动，纯博弈不适用 |
| mc-game-equilibrium | L1: decision（单玩家）；L2: flow balance（纯流动无策略互动） | 博弈需要≥2玩家策略互动，单玩家优化不适用 |

---

## 10. 参考文献

### Tier 1（教材/经典论文/官方）

1. Nash, J.F. (1950). "Equilibrium points in n-person games." *PNAS*, 36(1):48-49.
2. Kendall, D.G. (1953). "Stochastic processes occurring in the theory of queues." *Annals of Mathematical Statistics*, 24(3):338-354.
3. Little, J.D.C. (1961). "A proof for the queuing formula L = λW." *Operations Research*, 9(3):383-387.
4. Ford, L.R., Fulkerson, D.R. (1956). "Maximal flow through a network." *Canadian Journal of Mathematics*, 8:399-404.
5. Dijkstra, E.W. (1959). "A note on two problems in connexion with graphs." *Numerische Mathematik*, 1:269-271.
6. Braess, D. (1968). "Über ein Paradoxon aus der Verkehrsplanung." *Unternehmensforschung*, 12:258-268.
7. Wardrop, J.G. (1952). "Some theoretical aspects of road traffic research." *Proceedings of the Institution of Civil Engineers*, 1(3):325-362.
8. Shapley, L.S. (1953). "A value for n-person games." *Annals of Mathematics Studies*, 28:307-317.
9. Maynard Smith, J., Price, G.R. (1973). "The logic of animal conflict." *Nature*, 246:15-18.
10. Gale, D., Shapley, L.S. (1962). "College admissions and the stability of marriage." *American Mathematical Monthly*, 69:9-15.
11. Leontief, W. (1936). "Quantitative input and output relations in the economic systems of the United States." *Review of Economics and Statistics*, 18:105-125.
12. Ahuja, R.K., Magnanti, T.L., Orlin, J.B. (1993). *Network Flows: Theory, Algorithms, and Applications*. Prentice Hall.
13. Gibbons, R. (1992). *Game Theory for Applied Economists*. Princeton University Press.
14. Cooper, R.B. (1981). *Introduction to Queueing Theory*. 2nd ed., North-Holland.
15. Sheffi, Y. (1985). *Urban Transportation Networks*. Prentice-Hall.
16. Cormen, T.H. et al. *Introduction to Algorithms* (CLRS). MIT Press.
17. West, D.B. *Introduction to Graph Theory*. Prentice Hall.
18. 项目内：`core/knowledge/methodology/game-theory.md`, `queueing-theory.md`, `graph-theory.md`
19. 项目内：`research/P15/reports/_knowledge_architecture_audit.md`
20. 项目内：`research/P15/benchmark/problem_cards/2019_C/`, `2020_B/`
21. 项目内：`AGENTS.md`（项目宪法）
22. 国家统计局：投入产出表分析要点

### Tier 2（专业资料/期刊文章）

23. Frank, M., Wolfe, P. (1956). "An algorithm for quadratic programming." *Naval Research Logistics Quarterly*, 3:95-110.
24. Monderer, D., Shapley, L.S. (1996). "Potential games." *Games and Economic Behavior*, 14:124-143.
25. Daskalakis, C., Goldberg, P.W., Papadimitriou, C.H. (2009). "The complexity of computing a Nash equilibrium." *SIAM Journal on Computing*, 39(1):195-259.
26. Kingman, J.F.C. (1962). "Some inequalities for the GI/G/1 queue." *Quarterly Journal of Mathematics*, 13:315-323.
27. Jackson, J.R. (1957). "Networks of waiting lines." *Operations Research*, 5(4):518-521.
28. 中国科技论文在线：基于 MATLAB 的离散事件随机系统建模及仿真
29. 电子技术应用：基于智能代理的交通分配建模
30. 管理学年鉴：区域环境保护行动的演化博弈分析
31. 科学网：美国工程院院士解析博弈论与控制

### Tier 3（百科/教程，仅用于定义和关键词发现）

32. 网络流百科（抖音百科）
33. 排队过程百科（抖音百科）
34. 进化对策论百科（抖音百科）
35. 投入产出数学模型百科（抖音百科）

---

*本文件为 Research-layer Calibration 域研究证据文档。所有结论用于知识架构校准，不涉及修改现有 core/knowledge 文件。方法卡设计方向仅为约束性建议（Constraint/Prior），不构成对 Agent 建模自由的限制。*
