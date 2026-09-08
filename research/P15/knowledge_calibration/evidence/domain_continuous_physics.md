# 连续物理域（Continuous Physics）知识架构校准研究

> **研究代理**：连续物理域领域研究代理
> **研究范围**：L1 diffusion / motion-geometry；L2 conservation law / spatial-temporal field / distance-geometry；L3 differential equation（PDE/ODE 拆分研究）；L4 numerical PDE / 运动学数值求解
> **研究日期**：2026-09-08
> **治理定位**：方法卡 = Constraint / Prior / Validation，不是答案库。Knowledge coverage must constrain evaluation, not constrain creativity.
> **输出路径**：`research/P15/knowledge_calibration/evidence/domain_continuous_physics.md`

---

## 0. 研究范围与方法论声明

### 0.1 本域覆盖的标签边界

| 层 | 本域覆盖标签 | 不覆盖（由其他域代理负责） |
|---|---|---|
| L1 Problem Structure | `diffusion`, `motion/geometry` | network/traffic, scheduling, competition/game, decision, uncertainty, data/evaluation |
| L2 Modeling Pattern | `conservation law`, `spatial-temporal field`, `distance/geometry` | state transition, flow balance, resource constraint, queue, interaction/game |
| L3 Mathematical Formulation | `differential equation`（含 PDE/ODE/stochastic 子层级研究） | optimization, graph, probability, statistics, linear algebra |
| L4 Solver/Algorithm | `numerical PDE`（FDM/FEM/FVM）, 运动学数值求解/仿真 | DP, Monte Carlo, GA, regression, clustering |

### 0.2 证据等级定义

| 等级 | 来源类型 | 本研究中的使用 |
|---|---|---|
| **Tier 1** | 大学课程/教材/同行评审论文/SIAM/ACM/IEEE/Springer/Elsevier/Cambridge/Oxford/MIT/Stanford/Berkeley/COMAP官方/CUMCM官方 | 关键知识定义、方法适用性、数学关系的主证据 |
| **Tier 2** | 高质量专业资料（NIST、COMSOL、Wolfram、大学公开课讲义、期刊论文） | 补充验证、应用场景 |
| **Tier 3** | Wikipedia/blog/StackExchange/tutorial/CSDN | 仅用于发现关键词，不作为关键结论的唯一依据 |

### 0.3 四层严格区分原则

- **L1 Problem Structure** ≠ L2 Modeling Pattern ≠ L3 Mathematical Formulation ≠ L4 Solver/Algorithm
- **PDE ≠ numerical PDE**：PDE 是数学表述（L3），numerical PDE 是求解算法（L4）
- 不能把算法名（如"有限差分法"）当 Modeling Pattern
- 守恒律（L2）是物理建模机理，PDE（L3）是其数学表述，numerical PDE（L4）是其求解手段

---

## 1. L1 标签研究

### 1.1 diffusion（扩散/热传导/浓度场）

#### 定义

**diffusion** 描述物理量（热量、质量、浓度、动量）在空间中的传播与分布演化过程。其核心特征是：场变量同时依赖空间坐标和时间，且传播由梯度驱动。

**核心机理**：
- 微观层面：粒子/能量的随机布朗运动导致宏观扩散
- 宏观层面：Fick 第一定律（扩散通量与浓度梯度成正比）或 Fourier 导热定律（热通量与温度梯度成正比）
- 数学表现：抛物型偏微分方程（parabolic PDE）

#### 典型问题类型

| 子类型 | 场变量 | 驱动定律 | 典型竞赛题 |
|---|---|---|---|
| 热传导 | 温度 T(x,t) | Fourier 定律 q = -k∇T | 2018_A（高温作业服装）、2020_A（回流焊炉温） |
| 质量扩散 | 浓度 C(x,t) | Fick 定律 J = -D∇C | 环境污染扩散、药物释放 |
| 动量扩散 | 速度 u(x,t) | 牛顿粘性定律 τ = μ∇u | 流体边界层、润滑 |
| 种群扩散 | 种群密度 u(x,t) | 随机游走 + 繁殖 | 生态入侵、流行病空间传播 |

#### 与 L2/L3/L4 的自然映射

```
diffusion (L1)
  → conservation law (L2: 能量/质量守恒)
  → spatial-temporal field (L2: 温度场/浓度场)
  → PDE (L3: 抛物型 ∂u/∂t = α∇²u + 源项)
  → numerical PDE (L4: FDM 显式/隐式/Crank-Nicolson)
```

#### 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 扩散过程由守恒律 + 本构定律（Fourier/Fick）导出抛物型 PDE | "Conservation of energy implies... the use of the divergence theorem and the same constitutive assumptions... lead to the parabolic PDE (cρ)u_t = ∇·(k∇u) + g" | UC Davis Math PDE Notes (Hunter) | Tier 1 | high |
| 热传导方程是抛物型 PDE 的典型代表 | "The three well known classical PDEs are Laplace equation, heat equation, and wave equation, representing elliptic, parabolic and hyperbolic equations" | 中国科学院数学研究所 | Tier 1 | high |
| 扩散问题的场变量同时依赖空间和时间 | "A state field is a quantity defined over a domain. Instead of one population, temperature, concentration... the model represents a value at each point or grid cell" | Sustainable Catalyst (PDE intro) | Tier 2 | medium-high |
| 2018_A 的核心是多层一维非稳态热传导 PDE | "基于 Fourier 定律和能量守恒定律，建立的基于热传导方程的温度分布模型"；控制方程 ρ_j c_j ∂T/∂t = ∂/∂x(λ_j ∂T/∂x) | CUMCM 2018_A 官方优秀论文 A401/A440/A466 | Tier 1 (COMAP官方) | high |

---

### 1.2 motion/geometry（运动学/几何建模/空间定位/轨迹）

#### 定义

**motion/geometry** 描述物体（刚体/多体系统/质点）在空间中的位置、姿态、速度、加速度及其随时间的演化，以及几何约束（距离、角度、碰撞、轨迹形状）对运动的限制。

**核心机理**：
- 运动学（Kinematics）：不考虑力，仅研究位置-速度-加速度的几何关系
- 正运动学（Forward Kinematics）：给定关节/驱动参数 → 末端位姿
- 逆运动学（Inverse Kinematics）：给定期望位姿 → 关节参数
- 几何约束：刚体约束（距离不变）、关节约束（角度范围）、碰撞约束（不穿透）
- 轨迹规划：在约束空间中寻找满足条件的路径

#### 典型问题类型

| 子类型 | 核心变量 | 关键约束 | 典型竞赛题 |
|---|---|---|---|
| 多刚体链运动学 | 各节位置 (x_i(t), y_i(t)) | 相邻间距恒定 d | 2024_A（板凳龙） |
| 悬链线/柔性体几何 | 链条形状 y(x) | 静力平衡、边界固定 | 2016_A（系泊系统） |
| 空间定位/影子 | 太阳高度角、方位角 | 几何投影关系 | 2015_A（太阳影子定位） |
| 轨迹优化 | 路径参数 | 碰撞避免、时间最短 | 机器人路径规划、无人机 |
| 振动/动力学 | 位移 u(t) | 牛顿第二定律 | 2019_A（车床振动） |

#### 与 L2/L3/L4 的自然映射

```
motion/geometry (L1)
  → distance/geometry (L2: 轨迹约束、碰撞检测、刚体距离)
  → ODE (L3: 运动方程 d²x/dt² = F/m, 或运动学递推)
  → optimization (L3: 约束优化 min 路径长度 s.t. 不碰撞)
  → numerical ODE / kinematics simulation (L4: RK4、多体递推、数值优化)
```

#### 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 正运动学由关节参数计算末端位姿，是多体系统的核心 | "Forward kinematics computes the position and orientation of a robot's end-effector given a set of joint values... For serial manipulators, the Denavit-Hartenberg convention provides a standardized way" | IEEE Technology Navigator | Tier 1 (IEEE) | high |
| 多体递推是板凳龙的核心建模方法 | "每节板凳视为刚体，后节位置由前节约束递推：x_{i+1} = x_i - d cosθ_i" | CUMCM 2024_A 官方优秀论文 + playbook | Tier 1 (COMAP官方) | high |
| 碰撞检测分 broad-phase（包围盒/SAT）和 narrow-phase（GJK） | "Collision Detection... broad-phase consists of detecting intersections between oriented bounding boxes (OBB) using the Separating Axis Theorem (SAT)... narrow-phase detects intersections using the GJK algorithm" | GitHub ARB (基于 Featherstone 刚体动力学) | Tier 2 | medium |
| 2024_A 的碰撞检测利用刚性特征简化为距离判定 | "若第i节与第j节（|i-j|≥3）的中心线距离小于板凳宽度w=0.4m，则判定自交" | CUMCM 2024_A 实现方案 (CSDN) | Tier 3（仅作竞赛实践参考） | medium |
| 悬链线是系泊系统锚链的标准几何模型 | "将锚链简化为悬链线... y = (T₁cosα₁/σg)cosh(σg x/(T₁cosα₁) + sinh⁻¹(tanα₁)) - ..." | CUMCM 2016_A 官方优秀论文 + 《实验科学与技术》期刊 | Tier 1 | high |
| 运动学与动力学的区别：运动学不涉及力 | "Kinematics: FK/IK/collision/workspace... Dynamics modeling extends this by accounting for gravity, inertia, and Coriolis effects" | IEEE Technology Navigator / PyPI fieldpilot-urdf | Tier 1 (IEEE) | high |

---

## 2. L2 标签研究

### 2.1 conservation law（守恒律）

#### 定义

**守恒律**是物理学的基本原理：在一个封闭系统中，某些物理量（质量、能量、动量）的总量不随时间变化，其变化仅由通过边界的通量和内部源/汇决定。守恒律是从物理现象导出 PDE 的**标准桥梁**。

#### 通用守恒方程

**积分形式**（对任意控制体 V）：
```
d/dt ∫_V u dV = -∮_{∂V} F(u)·n dS + ∫_V S(u) dV
```
- 左边：控制体内物理量的累积率
- 右边第一项：通过边界的净通量（流出为正）
- 右边第二项：内部源/汇

**微分形式**（利用散度定理 ∮F·n dS = ∫∇·F dV，令 V→0）：
```
∂u/∂t + ∇·F(u) = S(u)
```

#### 三大守恒律与对应 PDE

| 守恒量 | 积分形式 | 微分形式（PDE） | 本构定律 | 典型方程 |
|---|---|---|---|---|
| **质量** | d/dt∫ρdV = -∮ρu·n dS | ∂ρ/∂t + ∇·(ρu) = 0 | — | 连续性方程 |
| **动量** | d/dt∫ρu dV = -∮ρu(u·n)dS + ∮σ·n dS + ∫ρf dV | ρ(∂u/∂t + u·∇u) = -∇p + ∇·τ + ρf | 牛顿粘性定律 | Navier-Stokes |
| **能量** | d/dt∫ρe dV = -∮(ρe+p)u·n dS + ... | ρc_p(∂T/∂t + u·∇T) = ∇·(k∇T) + Φ + q | Fourier 定律 | 热传导方程 |

#### 守恒律 → PDE 的推导路径

```
物理现象（热传导/扩散/流动）
  → 识别守恒量（能量/质量/动量）
  → 写出积分守恒方程（控制体分析）
  → 引入本构定律（Fourier/Fick/牛顿粘性）
  → 应用散度定理 → 微分形式 PDE
  → 确定边界条件和初始条件 → 定解问题
```

**关键洞察**：守恒律本身不是 PDE，它是物理原理（L2）。PDE 是守恒律在微分形式下的数学表述（L3）。二者是"机理→形式"的关系，不是同一层。

#### 数学建模中的典型应用

| 应用领域 | 守恒量 | 导出的 PDE | 竞赛题实例 |
|---|---|---|---|
| 热传导 | 能量 | 热方程 ∂T/∂t = α∇²T | 2018_A, 2020_A |
| 流体 | 质量+动量 | Navier-Stokes | 2019_A（部分） |
| 扩散 | 质量 | 扩散方程 ∂C/∂t = D∇²C | 环境问题 |
| 交通流 | 车辆数 | 交通流 PDE ∂ρ/∂t + ∂(ρv)/∂x = 0 | 交通建模 |
| 电磁 | 电荷 | Maxwell 方程 | — |

#### 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 守恒律的积分形式通过散度定理转化为微分形式 PDE | "d/dt∫_V ρ dV = -∮_{∂V} ρu·n dS → ∂ρ/∂t + ∇·(ρu) = 0 (continuity equation)" | University of Toronto Math (Spiegelman) | Tier 1 | high |
| 三大守恒律（质量/动量/能量）分别导出连续性方程、NS方程、能量方程 | 完整表格：质量→连续性方程，动量→Navier-Stokes，能量→能量方程 | 大连理工大学 (张博) NS方程概览 | Tier 1 (大学课程) | high |
| 热传导方程由能量守恒 + Fourier 定律导出 | "Conservation of energy implies... d/dt∫e dV = -∮(q+ev)·ν dS + ∫g dV... lead to the parabolic PDE (cρ)u_t = ∇·(k∇u) + g" | UC Davis Math PDE Notes (Hunter) | Tier 1 | high |
| 通用守恒方程的标准形式为 ∂u/∂t + ∇·F(u) = S(u) | "Every problem... expressed as: ∂u/∂t + ∇·F(u,∇u) = S(u,x,t), where u is primary field (concentration, temperature, velocity), F is flux tensor, S is source" | GitHub oxiflow Equations (基于标准 PDE 形式) | Tier 2 | high |
| 守恒律是 L2 建模模式，PDE 是 L3 数学表述，二者不同层 | 本研究综合多来源推导路径分析 | 本研究综合 | — | high（概念区分） |
| 2018_A 明确以能量守恒为建模起点 | "以 Fourier 定律和能量守恒定律为理论依据，建立了基于热传导方程的温度分布模型" | CUMCM 2018_A 官方论文 A401 | Tier 1 (COMAP官方) | high |

---

### 2.2 spatial-temporal field（时空场）

#### 定义

**时空场**是定义在空间域 Ω ⊂ ℝ^d 和时间域 t ∈ [0,T] 上的函数 u(x,t)，描述某物理量在空间中的分布及其随时间的演化。它是 diffusion 类问题的**标准数学对象**。

#### 核心要素

| 要素 | 定义 | 作用 |
|---|---|---|
| **空间变量 x** | x ∈ Ω ⊂ ℝ^d（d=1,2,3） | 描述场的空间分布 |
| **时间变量 t** | t ∈ [0,T] | 描述场的时间演化 |
| **场变量 u(x,t)** | 标量场（温度/浓度）或矢量场（速度/力） | 建模的未知量 |
| **初始条件** | u(x,0) = u₀(x), ∀x ∈ Ω | 给定 t=0 时的场分布 |
| **边界条件** | u 或 ∂u/∂n 在 ∂Ω 上的约束 | 给定域边界上的行为 |

#### 边界条件的三种基本类型

| 类型 | 数学形式 | 物理含义 | 热传导实例 |
|---|---|---|---|
| **Dirichlet（第一类）** | u(x,t) = g(x,t), x ∈ ∂Ω | 边界上场值已知 | 外壁温度固定 75°C |
| **Neumann（第二类）** | ∂u/∂n = g(x,t), x ∈ ∂Ω | 边界上通量已知 | 绝热壁 ∂T/∂n = 0 |
| **Robin（第三类/混合）** | αu + β∂u/∂n = g(x,t) | 场值与通量的线性组合已知 | 对流换热 -k∂T/∂n = h(T - T_env) |

#### 场变量类型

| 场类型 | 变量 | 守恒律 | 典型 PDE |
|---|---|---|---|
| 温度场 | T(x,t) | 能量守恒 | 热方程 |
| 浓度场 | C(x,t) | 质量守恒 | 扩散方程 |
| 速度场 | u(x,t) | 动量守恒 | Navier-Stokes |
| 压力场 | p(x,t) | 动量守恒（不可压条件） | Poisson 方程 |
| 种群密度场 | u(x,t) | 个体数守恒+繁殖 | 反应扩散方程 |
| 污染浓度场 | C(x,t) | 质量守恒+衰减 | 对流扩散方程 |

#### 与 conservation law 的关系

时空场是守恒律的**数学载体**：守恒律描述"场的总量如何变化"，时空场描述"场在每一点的值"。二者结合构成完整的分布参数系统模型：
```
守恒律（机理） + 时空场（载体） + 本构定律（通量-梯度关系）
  → PDE（数学表述）
  → 初始条件 + 边界条件（定解条件）
  → 适定性问题（Hadamard 三条件：存在性、唯一性、连续依赖性）
```

#### 适定性（Well-posedness）

Hadamard 三条件：
1. **存在性**：解存在
2. **唯一性**：解唯一
3. **连续依赖性**：解连续依赖于初始/边界数据

不适定的例子：反向热方程（backward heat equation）——从终态反推初态，对噪声极度敏感。2018_A 的参数反演本质上是**反问题（inverse problem）**，通常不适定，需要正则化。

#### 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 时空场是定义在空间+时间上的函数，是分布参数系统的标准对象 | "Distributed parameter systems are dynamical systems whose state variables depend on both time and spatial position, requiring PDEs rather than ODEs" | IEEE Technology Navigator (Distributed Parameter Systems) | Tier 1 (IEEE) | high |
| 三种边界条件：Dirichlet/Neumann/Robin | "1. Dirichlet: u = g on ∂Ω. 2. Neumann: ∂u/∂ν = g on ∂Ω. 3. Robin (mixed): αu + β∂u/∂ν = g on ∂Ω" | PDE Lecture Notes (Master M1, gabayae.github.io) | Tier 1 (大学课程) | high |
| 初始条件定义 t=0 时的场分布，边界条件定义域边缘行为 | "The initial condition defines the field at the starting time. Boundary conditions define how the field behaves at the edge of the domain" | Sustainable Catalyst PDE Introduction | Tier 2 | medium-high |
| Hadamard 适定性三条件 | "A problem is well-posed if: 1. A solution exists. 2. The solution is unique. 3. The solution depends continuously on the data" | KTH Royal Institute of Technology PDE Notes | Tier 1 | high |
| 反向热方程是经典不适定问题 | "'Backward' heat equation, t→-t ⇒ ill-posed" | KTH Royal Institute of Technology PDE Notes | Tier 1 | high |
| 2018_A 涉及多层介质界面条件（温度连续+热流连续） | "分别建立各层一维非稳态导热方程，并严格施加界面连续性条件（温度连续、热流密度连续）与边界条件" | CUMCM 2018_A 解题思路汇总 | Tier 2 | high |
| 时空场的标量/矢量分类 | "u(x,t) — primary field (concentration, temperature, velocity…)" | oxiflow canonical form | Tier 2 | high |

---

### 2.3 distance/geometry（距离/几何约束）

#### 定义

**distance/geometry** 描述通过空间距离、几何形状和拓扑约束来建模的模式。核心是：物体的位置和姿态由几何关系（距离、角度、曲率、包围盒）约束，而非由场的偏微分方程描述。

**注意**：此标签在当前知识库中仅被 mc-topsis（距离理想点）弱覆盖，**完全不覆盖几何建模中的空间距离/轨迹约束**。本研究重点强化运动学/几何语境。

#### 核心几何约束类型

| 约束类型 | 数学形式 | 物理含义 | 竞赛实例 |
|---|---|---|---|
| **刚体距离约束** | \|P_i - P_{i+1}\| = d（常数） | 相邻节间距不变 | 2024_A 板凳龙 |
| **碰撞避免约束** | \|P_i - P_j\| ≥ w_min, ∀\|i-j\|>1 | 非相邻节不穿透 | 2024_A Q3 |
| **悬链线几何** | y(x) = a·cosh(x/a) + b | 柔性链条在重力下的形状 | 2016_A 系泊系统 |
| **螺旋线参数化** | r(θ) = R₀ + p·θ | 阿基米德螺线路径 | 2024_A 螺旋进场 |
| **角度约束** | θ_min ≤ θ ≤ θ_max | 关节转动范围 | 机器人、机械臂 |
| **包围盒距离** | OBB/SAT 距离判定 | broad-phase 碰撞检测 | 通用碰撞检测 |

#### 与 ODE 和 optimization 的关系

```
distance/geometry (L2)
  → 运动学方程（代数约束 + 微分关系）→ ODE/DAE (L3)
  → 约束优化问题 min f(x) s.t. g(x) ≥ 0 (L3)
  → 数值求解：多体递推、SQP、遗传算法 (L4)
```

**关键区分**：
- 纯几何问题（如悬链线静力平衡）可能导出**代数方程**或**两点边值 ODE**，不一定是 PDE
- 运动学问题（如板凳龙）的核心是**递推关系**（后节位置由前节决定），本质是**差分方程/ODE 初值问题**
- 碰撞检测是**几何判定**（距离比较），不是微分方程

#### 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 碰撞检测分 broad-phase（包围盒/SAT）和 narrow-phase（GJK）两阶段 | "broad-phase consists of detecting intersections between oriented bounding boxes (OBB) using the Separating Axis Theorem (SAT)... narrow-phase detects intersections using GJK algorithm" | Articulated Rigid Body (基于 Featherstone) | Tier 2 | medium-high |
| 板凳龙的刚体约束是相邻间距恒定 | "验证刚体约束：相邻节间距恒为 d，相对误差 < 1e-6" | CUMCM 2024_A playbook + 官方论文 | Tier 1 | high |
| 悬链线方程是柔性链条静力平衡的标准解 | "y = (T₁cosα₁/σg)cosh(σg x/(T₁cosα₁) + sinh⁻¹(tanα₁)) - ..." | CUMCM 2016_A 官方论文 + 《实验科学与技术》 | Tier 1 | high |
| 距离/几何约束通常导出约束优化问题而非 PDE | "目标函数 min T_turn，约束：不碰撞 d_min(t) ≥ w_min，螺距连续，边界 R_min ≤ R ≤ R_max" | CUMCM 2024_A playbook | Tier 1 | high |
| 当前 distance/geometry 标签仅被 TOPSIS 弱覆盖，不覆盖几何建模 | 审计报告："distance/geometry 仅在 TOPSIS 的'距离理想点'语境下被覆盖，不覆盖几何建模中的空间距离/轨迹约束" | P15 knowledge architecture audit | 本项目内部 | high |

---

## 3. L3 标签研究：differential equation 是否应拆分为 PDE/ODE？

### 3.1 核心问题

当前 L3 标签 `differential equation` 是一个笼统标签。本研究需要判断：是否应将其拆分为 `PDE` 和 `ODE` 两个独立的一级标签？是否需要 `stochastic process` 作为子层级？

### 3.2 PDE 与 ODE 的本质区别

| 维度 | ODE（常微分方程） | PDE（偏微分方程） |
|---|---|---|
| 自变量数量 | 1 个（通常是时间 t） | ≥2 个（空间 x + 时间 t，或多空间维度） |
| 未知函数 | y(t)：一元函数 | u(x,t)：多元函数（场） |
| 解的几何 | 曲线（curve） | 曲面/超曲面（surface/hypersurface） |
| 系统类型 | 集中参数系统（lumped parameter） | 分布参数系统（distributed parameter） |
| 导数类型 | 常导数 dy/dt | 偏导数 ∂u/∂t, ∂u/∂x |
| 定解条件 | 初始条件（初值问题）或边界条件（边值问题） | 初始条件 + 边界条件（必须同时有） |
| 典型方程 | 牛顿第二定律 m·d²x/dt² = F | 热方程 ∂u/∂t = α∇²u |
| 数值求解 | RK4、Euler、BDF（时间积分） | FDM/FEM/FVM（空间离散 + 时间积分） |
| 竞赛题实例 | 2024_A（运动学递推）、2016_A（悬链线 ODE） | 2018_A（热传导）、2020_A（炉温曲线） |

### 3.3 拆分的论据

#### 支持拆分的证据

1. **物理本质不同**：ODE 描述集中参数系统的整体演化，PDE 描述分布参数系统的场演化。这是建模思路的根本分野——"追踪一个物体的状态" vs "描述一个场的分布"。

2. **定解条件结构不同**：ODE 初值问题只需初始条件；PDE 必须同时有初始条件和边界条件。边界条件的类型（Dirichlet/Neumann/Robin）是 PDE 独有的建模决策。

3. **数值求解方法完全不同**：ODE 用时间积分法（RK/Euler/BDF），PDE 用空间离散+时间积分（FDM/FEM/FVM）。L4 标签 `numerical PDE` 仅对应 PDE，不对应 ODE。

4. **竞赛题分布明确**：
   - PDE 类：2018_A（热传导）、2020_A（回流焊）→ 需要 spatial-temporal field + conservation law
   - ODE 类：2024_A（运动学递推）、2016_A（悬链线边值）→ 需要 distance/geometry + 运动学
   - 二者的 L1→L2→L4 路径完全不同

5. **当前审计发现**：`differential equation` 仅有灰色微分方程的弱覆盖，无 ODE/PDE 卡。拆分后可以分别建立针对性的 Constraint/Prior。

6. **IEEE 定义**："Distributed parameter systems... requiring PDEs rather than ODEs. In a lumped parameter system, the entire state is captured by a finite set of variables that evolve in time."——明确区分了两种系统类型和对应的方程类型。

#### 反对拆分的论据

1. **统一的微分方程理论**：ODE 和 PDE 共享微积分基础，某些方法（如特征线法）可以统一处理。
2. **标签数量膨胀**：拆分后 L3 标签从 6 个增至 7 个，增加管理复杂度。
3. **随机微分方程（SDE）的归属**：如果拆分 PDE/ODE，SDE 应放在哪里？

### 3.4 结论与建议

**建议：将 `differential equation` 拆分为 `PDE` 和 `ODE` 两个独立的 L3 一级标签。**

理由：
- 二者的建模思路、定解条件、数值方法、竞赛题路径完全不同，合并为一个标签会导致 L3 层语义模糊
- L4 的 `numerical PDE` 标签天然只对应 PDE，ODE 需要独立的求解器标签（如 `numerical ODE` 或归入 `numerical methods`）
- 拆分后可以精确标注：2018_A → PDE，2024_A → ODE，避免笼统的 "differential equation" 标注

**关于 stochastic process**：
- 随机过程（Markov 链、SDE、随机游走）应作为**独立的 L3 标签**，不应归入 differential equation
- 理由：随机过程的数学基础是概率论/测度论，不是确定性微积分；其建模模式（state transition with probability）与确定性 DE 有本质区别
- 当前知识库已有 `mc-monte-carlo`（不确定性传播）和 `mc-arima`（时序），但无随机过程方法卡
- 建议 L3 标签：`PDE`, `ODE`, `stochastic process` 三者并列

### 3.5 PDE 子类型（L3 下的细分，非独立标签）

PDE 可按二阶线性方程的判别式分类（对 A u_xx + 2B u_xy + C u_yy + ... = 0）：

| 类型 | 判别式 B²-AC | 典型方程 | 物理现象 | 定解条件 |
|---|---|---|---|---|
| **椭圆型（Elliptic）** | < 0 | Laplace Δu=0, Poisson Δu=f | 稳态场、静电势、静力学 | 仅边界条件（边值问题） |
| **抛物型（Parabolic）** | = 0 | 热方程 u_t = αu_xx | 扩散、热传导、渗流 | 初始条件 + 边界条件 |
| **双曲型（Hyperbolic）** | > 0 | 波动方程 u_tt = c²u_xx | 波动、振动、交通流 | 初始条件（位移+速度）+ 边界条件 |

**注意**：此分类是 PDE 的**子类型**，用于方法卡的 `supports`/`not_for` 字段，不建议提升为 L3 独立标签（因为竞赛题中 PDE 类型通常由物理现象直接决定，不需要 LLM 在 L3 层做类型选择）。

### 3.6 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| ODE 与 PDE 的根本区别是自变量数量和系统类型 | "ODE only one independent variable (time), describes lumped parameter system; PDE has ≥2 independent variables, describes distributed parameter system (field)" | IEEE Distributed Parameter Systems + University of Alberta PDE Notes | Tier 1 (IEEE) | high |
| ODE 解是曲线，PDE 解是曲面/超曲面 | "The geometry of the solution to an ODE is a curve, while for a PDE it is a surface in space or generally a hypersurface" | University of Alberta PDE Chapter 1 | Tier 1 (大学课程) | high |
| PDE 必须同时有初始条件和边界条件 | "PDEs require more than an equation. They need initial conditions and boundary conditions" | Sustainable Catalyst PDE Introduction | Tier 2 | medium-high |
| PDE 三类型分类（椭圆/抛物/双曲）由判别式决定 | "Hyperbolic if b²-4ac>0; Parabolic if b²-4ac=0; Elliptic if b²-4ac<0" | AMATH 453 PDE II (大学课程) + 中国科学院数学所 | Tier 1 | high |
| 三大经典 PDE 分别对应三种类型 | "Laplace equation (elliptic), heat equation (parabolic), wave equation (hyperbolic), representing the three types with rather distinct properties" | 中国科学院数学与系统科学研究院 | Tier 1 | high |
| 建议拆分 PDE/ODE 为独立 L3 标签 | 本研究综合 6 项论据 | 本研究综合 | — | high |
| stochastic process 应独立于 differential equation | 随机过程基于概率论，与确定性 DE 数学基础不同；当前已有 monte-carlo 卡但无随机过程卡 | 本研究综合 + 审计报告 | — | medium-high |

---

## 4. L4 标签研究：numerical PDE

### 4.1 定义

**numerical PDE** 是将连续偏微分方程在离散网格上近似求解的算法类别。核心挑战：空间离散化、时间积分、稳定性控制、边界处理、验证与确认。

### 4.2 三大空间离散方法对比

| 维度 | 有限差分法 (FDM) | 有限元法 (FEM) | 有限体积法 (FVM) |
|---|---|---|---|
| **核心思想** | 用差分商近似微分商，在网格节点上直接离散 | 将域分解为单元，用分段多项式基函数近似解，基于变分/加权残值 | 将域分解为控制体，在每个控制体上应用积分守恒律 |
| **数学基础** | Taylor 展开截断误差 | 变分原理 / Galerkin 方法 | 积分守恒律 + 散度定理 |
| **网格要求** | 结构化网格（矩形/立方体） | 非结构化网格（三角形/四面体/六面体） | 非结构化网格（任意多边形控制体） |
| **复杂几何** | 差（需坐标变换或浸入边界） | 优（天然适应复杂边界） | 良（控制体可任意形状） |
| **守恒性** | 差（差分格式不一定保持守恒） | 中（Galerkin 格式的守恒性需特殊处理） | **优**（天然满足积分守恒律） |
| **实现复杂度** | 低（公式直观，代码简单） | 高（网格生成、矩阵组装、求解器） | 中（通量计算是核心难点） |
| **计算效率** | 高（稀疏矩阵结构简单） | 中（矩阵组装开销大） | 中高 |
| **典型精度** | 1-2 阶（高阶需紧凑格式） | 2-(p+1) 阶（p 次单元） | 1-2 阶（高阶需 WENO/重建） |
| **稳定性** | 受 CFL 条件限制（显式）；隐式无条件稳定 | 天然稳定（扩散问题），对流问题需稳定化 | 良好（守恒格式+数值通量） |
| **主导领域** | 热传导、波动、简单 CFD | 结构力学、固体力学、电磁场 | CFD、流体、多物理场 |
| **竞赛适用性** | ★★★★★（国赛 A 题首选，实现快） | ★★☆☆☆（过于复杂，不现实） | ★★★☆☆（流体题可用） |

### 4.3 时间积分方法（针对抛物型/双曲型 PDE）

| 方法 | 类型 | 稳定性 | 精度 | 适用场景 |
|---|---|---|---|---|
| **显式 Euler (FTCS)** | 显式 | 条件稳定（r ≤ 0.5） | O(Δt) + O(Δx²) | 简单教学、短时间 |
| **隐式 Euler (BTCS)** | 隐式 | 无条件稳定 | O(Δt) + O(Δx²) | 刚性问题、大时间步 |
| **Crank-Nicolson** | 隐式（梯形） | 无条件稳定 | O(Δt²) + O(Δx²) | **热传导首选**，精度与稳定性平衡 |
| **Du Fort-Frankel** | 显式（三层） | 无条件稳定 | O(Δt²) + O(Δx²)，但需 τ/h→0 | 2018_A 优秀论文使用 |
| **ADI（交替方向隐式）** | 隐式（分裂） | 无条件稳定 | O(Δt²) + O(Δx²) | 二维/三维抛物型问题 |
| **Lax-Wendroff** | 显式 | CFL ≤ 1 | O(Δt²) + O(Δx²) | 双曲型守恒律 |

### 4.4 数值分析三大支柱 + Lax 等价定理

#### 一致性（Consistency）
差分格式在网格步长 → 0 时，截断误差 → 0，即离散方程趋近于原 PDE。
- 衡量：截断误差 τ(Δx, Δt) = O(Δx^p) + O(Δt^q)

#### 稳定性（Stability）
数值误差在计算过程中不被无界放大。是算法的全局性质。
- 分析方法：von Neumann 稳定性分析（傅里叶模态法）
- 热方程显式格式：r = αΔt/Δx² ≤ 0.5
- 波动方程：CFL 条件 cΔt/Δx ≤ 1

#### 收敛性（Convergence）
数值解在网格细化时趋近于真解。

#### Lax 等价定理
> **对于线性初值问题的相容差分格式，稳定性是收敛性的充分必要条件。**
> 即：Consistency + Stability ⟺ Convergence（线性问题）

这是 numerical PDE 的**理论基石**。竞赛中验证数值解正确性时，应至少做网格收敛性测试（mesh refinement study）。

### 4.5 边界处理

| 边界类型 | FDM 处理方式 | 注意事项 |
|---|---|---|
| Dirichlet | 直接赋值 u[0] = g(t) | 最简单 |
| Neumann | 单边差分或镜像法 ∂u/∂x ≈ (u[1]-u[0])/Δx | 一阶精度，可用虚拟点提至二阶 |
| Robin | 联立边界方程与内部差分 | 需修改矩阵第一行/最后一行 |
| 界面条件（多层介质） | 温度连续 T₁=T₂，热流连续 k₁∂T₁/∂x = k₂∂T₂/∂x | 2018_A 核心难点，需在界面处特殊处理 |
| 周期性 | u[N] = u[0]，u[N+1] = u[1] | 循环矩阵 |

### 4.6 验证方法（Validation）

| 验证方法 | 做法 | 通过标准 |
|---|---|---|
| **网格收敛性测试** | Δx 减半、Δt 减半，比较关键输出变化 | 变化 < 1%（或符合理论收敛阶） |
| **与解析解对比** | 对简单情形（如半无限大物体、稳态线性分布）求解析解 | 相对误差 < 1% |
| **守恒量检查** | 检查总能量/总质量是否守恒（无源项时） | 变化 < 2% |
| **物理合理性检查** | 温度是否在边界值之间、是否单调趋近稳态 | 定性正确 |
| **参数敏感性** | 扰动输入参数 ±10%，观察输出变化 | 变化平滑、无突变 |
| **多种子/多格式对比** | 用两种不同差分格式（显式 vs Crank-Nicolson）求解同一问题 | 结果一致 |

### 4.7 运动学数值求解/仿真

运动学问题（motion/geometry L1）的数值求解与 numerical PDE 有本质区别：

| 维度 | 运动学数值求解 | numerical PDE |
|---|---|---|
| 方程类型 | ODE / 代数递推 / 约束优化 | PDE |
| 空间离散 | 不需要（刚体位置是有限维向量） | 需要（FDM/FEM/FVM） |
| 时间积分 | RK4、Euler、多体递推 | 空间离散 + 时间积分 |
| 核心挑战 | 碰撞检测、约束满足、轨迹优化 | 稳定性、边界处理、网格质量 |
| 典型算法 | 正向运动学递推、SQP、遗传算法、A* | Crank-Nicolson、FEM、FVM |
| 验证方法 | 刚体约束残差、碰撞检查、能量守恒 | 网格收敛、守恒量检查 |

**建议**：L4 标签应区分 `numerical PDE` 和 `numerical ODE / kinematics simulation`，因为二者的算法集合完全不同。

### 4.8 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| Lax 等价定理：一致性+稳定性⟺收敛性（线性问题） | "The celebrated Lax Equivalence Theorem: For a consistent linear approximation, stability is the necessary and sufficient condition for convergence" | Semantic Scholar (Computational Methods for DE) + Preprints.org | Tier 1 (同行评审) | high |
| FDM 适合规则网格，FEM 适合复杂几何，FVM 天然守恒 | 对比表：FDM "efficient on structured grids, poor with complex geometry"; FEM "geometry flexibility"; FVM "conservative flux formulations" | rjsaonline.org Numerical Methods for PDE + HAL CFD paper | Tier 1/Tier 2 | high |
| Crank-Nicolson 是热传导的首选时间积分格式 | "Crank-Nicolson... unconditional stability, second-order accuracy in time and space"；2019_A playbook 推荐 | 多来源 + 本项目 playbook | Tier 1/Tier 2 | high |
| 显式热方程稳定性条件 r = αΔt/Δx² ≤ 0.5 | "稳定性条件：r <= 0.5"（FTCS 格式） | 本项目 ode-pde.md + 标准数值分析教材 | Tier 1 | high |
| 2018_A 优秀论文使用 Du Fort-Frankel 格式（无条件稳定） | "利用 Du Fort-Frankel 差分格式的有限差分法... 此差分格式是无条件稳定的" | CUMCM 2018_A 优秀论文 (lucajiang) | Tier 1 (COMAP优秀论文) | high |
| 网格收敛性测试是数值解验证的标准方法 | "网格收敛 Δx 减半 → 结果变化 < 1%" | 本项目 playbook-2019A-heat + 标准 CFD 验证实践 | Tier 2 | high |
| 运动学数值求解与 numerical PDE 应区分 L4 标签 | 本研究对比分析：方程类型、空间离散、核心挑战均不同 | 本研究综合 | — | high |

---

## 5. L1→L2→L3→L4 映射表：本域完整知识链

### 5.1 diffusion 分支

```
L1: diffusion
  │
  ├─ L2: conservation law (能量守恒/质量守恒)
  │    └─ 机理：控制体分析 → 积分守恒方程
  │
  ├─ L2: spatial-temporal field (温度场/浓度场)
  │    └─ 载体：u(x,t) + 初始条件 + 边界条件
  │
  └─ 二者结合 + 本构定律（Fourier/Fick）
       │
       ▼
  L3: PDE (抛物型 ∂u/∂t = α∇²u + S)
       │
       ├─ 子类型：抛物型（热/扩散）、椭圆型（稳态）、双曲型（对流）
       ├─ 定解条件：初始条件 + Dirichlet/Neumann/Robin 边界
       └─ 多层介质：界面条件（温度连续+热流连续）
       │
       ▼
  L4: numerical PDE
       ├─ 空间离散：FDM（竞赛首选）/ FEM / FVM
       ├─ 时间积分：Crank-Nicolson（推荐）/ 隐式 Euler / Du Fort-Frankel
       ├─ 稳定性：CFL / von Neumann 分析
       ├─ 验证：网格收敛 + 守恒量检查 + 解析解对比
       └─ 反问题：参数反演（最小二乘 + 正则化）
```

### 5.2 motion/geometry 分支

```
L1: motion/geometry
  │
  ├─ L2: distance/geometry (刚体约束/碰撞/轨迹几何)
  │    ├─ 刚体距离约束：|P_i - P_{i+1}| = d
  │    ├─ 碰撞避免：|P_i - P_j| ≥ w_min
  │    └─ 几何参数化：螺旋线/悬链线/圆弧
  │
  └─ (可选) L2: conservation law (动量守恒——若涉及动力学)
       └─ 纯运动学问题不需要守恒律
       │
       ▼
  L3: ODE (运动方程/运动学递推) + optimization (约束优化)
       ├─ ODE：d²x/dt² = F/m（动力学）或 dx/dt = v(t)（运动学）
       ├─ 代数递推：x_{i+1} = x_i - d·cosθ_i（多体链）
       ├─ 边值 ODE：悬链线方程（两点边界）
       └─ 约束优化：min 路径长度 s.t. 不碰撞、角度限制
       │
       ▼
  L4: numerical ODE / kinematics simulation / numerical optimization
       ├─ 正向运动学递推（多体链逐节计算）
       ├─ ODE 求解：RK4 / Euler / BDF（刚性）
       ├─ 碰撞检测：broad-phase (OBB/SAT) + narrow-phase (GJK) / 简化距离判定
       ├─ 轨迹优化：SQP / 遗传算法 / 网格搜索
       └─ 验证：刚体约束残差 + 碰撞检查 + 对称性检查
```

### 5.3 完整映射矩阵

| L1 Problem Structure | L2 Modeling Pattern | L3 Mathematical Formulation | L4 Solver/Algorithm | 典型竞赛题 |
|---|---|---|---|---|
| **diffusion** | conservation law + spatial-temporal field | PDE (抛物型) | numerical PDE (FDM + Crank-Nicolson) | 2018_A, 2020_A |
| **diffusion** | conservation law + spatial-temporal field | PDE (椭圆型, 稳态) | numerical PDE (FDM 迭代/有限元) | 稳态热传导 |
| **diffusion** | conservation law + inverse problem | PDE + optimization | numerical PDE + 最小二乘反演 | 2018_A Q2/Q3 |
| **motion/geometry** | distance/geometry (刚体约束) | ODE (递推) + linear algebra | kinematics simulation (多体递推) | 2024_A Q1 |
| **motion/geometry** | distance/geometry (碰撞) | optimization (约束) | numerical optimization + collision detection | 2024_A Q2/Q3 |
| **motion/geometry** | distance/geometry (悬链线) | ODE (边值) + optimization | numerical ODE (打靶法/有限差分) + 优化 | 2016_A |
| **motion/geometry** | distance/geometry (轨迹) | optimization + ODE | trajectory planning (A*/SQP/GA) | 路径规划类 |

---

## 6. 真实竞赛题映射

### 6.1 2018_A（高温作业服装）

#### 问题概述
高温环境下专用服装的设计：四层介质（I层织物、II层纤维、III层衬里、IV层空气）的一维非稳态热传导，已知假人皮肤外侧温度数据，求温度分布、反演热物性参数、优化保温层厚度。

#### 四层映射

| 层 | 标注 | 详细说明 |
|---|---|---|
| **L1 Problem Structure** | `diffusion` | 热量在四层介质中的传导与分布，是典型的热扩散问题 |
| **L2 Modeling Pattern** | `conservation law`（能量守恒）+ `spatial-temporal field`（温度场 T(x,t)）+ `inverse problem`（参数反演） | 能量守恒导出热传导方程；温度场是时空函数；Q2/Q3 是从温度数据反演参数 |
| **L3 Mathematical Formulation** | `PDE`（抛物型，多层一维）+ `optimization`（参数反演/厚度优化） | ρ_j c_j ∂T/∂t = ∂/∂x(λ_j ∂T/∂x), j=1,2,3,4；界面条件 T 连续、热流连续；反演 min_α Σ(T_model - T_meas)² |
| **L4 Solver/Algorithm** | `numerical PDE`（FDM，Du Fort-Frankel 或 Crank-Nicolson）+ `optimization`（最小二乘/网格搜索） | 有限差分法逐层求解；追赶法解三对角矩阵；二分/网格搜索反演参数和厚度 |

#### 为什么这种建模路线是合理的

1. **物理本质决定 PDE**：服装厚度方向（~mm 级）的热传导远快于平面方向，一维假设合理；非稳态（时间变化）需要抛物型 PDE。
2. **守恒律是唯一正确起点**：热传导方程只能从能量守恒 + Fourier 定律导出，不存在其他等价的建模路径。
3. **多层介质需要界面条件**：四层材料的热物性参数不同，必须在界面处施加温度连续和热流连续条件，这是 PDE 建模的关键技术点。
4. **FDM 是竞赛最优选择**：一维规则网格，FDM 实现简单、计算快；Du Fort-Frankel 格式无条件稳定，避免了显式格式的 CFL 限制。
5. **参数反演是反问题**：已知输出（皮肤温度）反求输入（热扩散系数/厚度），本质是不适定问题，用最小二乘+网格搜索是竞赛中可行的正则化手段。

#### 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 2018_A 控制方程为四层一维非稳态热传导 PDE | "ρ_j c_j ∂T/∂t = ∂/∂x(λ_j ∂T/∂x) (j=1,2,3,4)" | CUMCM 2018_A 官方论文 (dxs.moe.gov.cn) | Tier 1 (COMAP官方) | high |
| 优秀论文使用 Du Fort-Frankel 差分格式 | "利用 Du Fort-Frankel 差分格式的有限差分法... 无条件稳定" | CUMCM 2018_A 优秀论文 (lucajiang.github.io) | Tier 1 (优秀论文) | high |
| 参数反演用最小二乘拟合 | "基于最小二乘原理，建立最优化模型，拟合实测温度求解未知参数的最优估计" | CUMCM 2018_A 官方论文 A440 | Tier 1 (COMAP官方) | high |
| 边界条件包括对流换热（第三类） | "外侧为对流边界 -k∂T/∂x = h(T-T_env)，皮肤侧为实测温度（第一类）" | CUMCM 2018_A 解题思路汇总 | Tier 2 | high |
| 2018_A method_selection=0 的根本原因是 L1+L2+L4 三层联动缺失 | 审计报告详细分析 | P15 audit | 本项目内部 | high |

---

### 6.2 2024_A（板凳龙）

#### 问题概述
224 节板凳组成的"板凳龙"沿阿基米德螺线盘入，在有限区域内调头并盘出。需要：计算各节把手位置/速度（Q1）、确定调头螺旋参数（Q2）、分析碰撞风险（Q3）、优化调头路径（Q4）。

#### 四层映射

| 层 | 标注 | 详细说明 |
|---|---|---|
| **L1 Problem Structure** | `motion/geometry` | 多刚体链的运动学 + 螺旋几何 + 碰撞检测，是典型的运动学/几何建模问题 |
| **L2 Modeling Pattern** | `distance/geometry`（刚体约束 + 碰撞避免 + 螺旋参数化） | 相邻节间距恒定 d（刚体约束）；非相邻节距离 ≥ w_min（碰撞避免）；龙头沿阿基米德螺线运动（几何参数化） |
| **L3 Mathematical Formulation** | `ODE`（运动学递推/微分关系）+ `optimization`（约束优化）+ `linear algebra`（坐标变换） | 递推 x_{i+1} = x_i - d·cosθ_i；优化 min T_turn s.t. d_min(t) ≥ w_min；螺线参数化 r(θ) = R₀ + pθ |
| **L4 Solver/Algorithm** | `kinematics simulation`（多体递推）+ `collision detection`（距离判定）+ `numerical optimization`（网格搜索/SQP/GA） | 时间步进 + 逐节递推；O(N²) 距离比较；参数空间搜索最优螺距/半径 |

#### 为什么这种建模路线是合理的

1. **运动学而非动力学**：题目只要求位置/速度/碰撞，不涉及力和加速度，因此不需要牛顿第二定律（动力学 ODE），纯运动学递推即可。
2. **多体递推是最自然的建模方式**：后节跟随前节运动，间距恒定，这是一个典型的串联运动学链（serial kinematic chain），与机器人正运动学同构。
3. **阿基米德螺线是合理的路径参数化**：盘入/盘出需要半径连续变化的曲线，阿基米德螺线 r = R₀ + pθ 是最简单的等距螺线，参数少（仅 R₀, p），便于优化。
4. **碰撞检测可简化为距离判定**：板凳是细长刚体，在俯视平面上可简化为线段，碰撞等价于线段间距离 < 宽度。利用刚性特征可以避免复杂的 GJK 算法。
5. **优化是约束优化而非最优控制**：Q2/Q4 的决策变量是螺旋参数（静态参数），不是时间函数 u(t)，因此用参数优化（网格搜索/SQP）比最优控制（Pontryagin）更合适。

#### 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 板凳龙是 224 节多刚体链，核心是运动学递推 | "由224节板凳组成的板凳龙沿阿基米德螺线盘入... 多刚体运动学问题" | CUMCM 2024_A 题目 + 《实验科学与技术》期刊论文 | Tier 1 (期刊) | high |
| 正运动学递推：后节位置由前节约束 | "x_{i+1} = x_i - d cosθ_i, y_{i+1} = y_i - d sinθ_i" | CUMCM 2024_A playbook + 官方论文 | Tier 1 | high |
| 碰撞检测简化为中心线距离判定 | "若第i节与第j节（|i-j|≥3）的中心线距离小于板凳宽度w=0.4m，则判定自交" | CUMCM 2024_A 实现方案 | Tier 2/Tier 3 | medium-high |
| 首次碰撞发生在龙头与龙身之间（最内圈） | "龙头板凳比龙身板凳更长，且更靠近螺旋线的中心... 首次碰撞应发生在龙头与龙身之间" | 《实验科学与技术》板凳龙论文 (SciEngine) | Tier 1 (期刊) | high |
| 2024_A method_selection=0 的根本原因是 L1 motion/geometry 零覆盖 | 审计报告："motion/geometry 标签零覆盖，导致 LLM 无法从问题结构层面识别" | P15 audit | 本项目内部 | high |

---

### 6.3 2020_A（回流焊炉温曲线）

#### 问题概述
电路板通过回流焊炉，炉内分多个温区，各温区温度不同。需要：计算电路板温度随时间变化（Q1）、优化传送带速度使温升率/峰值温度/时间满足工艺要求（Q2/Q3）、确定最大生产效率（Q4）。

#### 四层映射

| 层 | 标注 | 详细说明 |
|---|---|---|
| **L1 Problem Structure** | `diffusion` | PCB 板在炉内的非稳态热传导，温度场随时间和空间演化 |
| **L2 Modeling Pattern** | `conservation law`（能量守恒）+ `spatial-temporal field`（温度场） | 能量守恒 + Fourier 定律导出热传导方程；PCB 温度是时空函数 |
| **L3 Mathematical Formulation** | `PDE`（一维非稳态热传导，含对流边界）+ `optimization`（速度/温区优化） | ρc_p ∂T/∂t = k ∂²T/∂x² + h(T_env - T) + εσ(T_env⁴ - T⁴)；第三类边界条件（对流+辐射） |
| **L4 Solver/Algorithm** | `numerical PDE`（FDM，隐式/Crank-Nicolson）+ `optimization`（遍历/搜索） | 有限差分法求解；传送带速度作为参数，遍历搜索最优值 |

#### 为什么这种建模路线是合理的

1. **一维简化合理**：PCB 厚度远小于长宽，热流主要沿厚度方向，可简化为一维热传导。
2. **边界条件是核心**：炉内不同温区的环境温度不同，PCB 表面与环境之间通过对流+辐射换热，这是第三类（Robin）边界条件。
3. **优化变量是传送带速度**：速度决定 PCB 在每个温区的停留时间，从而影响温度曲线。这是一个参数优化问题，不是 PDE 控制的最优控制问题。
4. **与 2018_A 的区别**：2018_A 是多层介质（空间多层），2020_A 是多温区（时间分段的边界条件），但核心都是一维抛物型 PDE + FDM。

#### 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 2020_A 核心是一维非稳态热传导 PDE | "采用一维非稳态热传导方程描述温度分布：ρc_p ∂T/∂t = k∂²T/∂x² + h(T_env-T) + εσ(T_env⁴-T⁴)" | CUMCM 2020_A 解题思路汇总 + 学术报告 | Tier 1/Tier 2 | high |
| 官方讲评确认热传导方程建模 | 蔡志杰教授官方讲评："炉温曲线"专题 | CUMCM 2020_A 官方讲评 (dxs.moe.gov.cn) | Tier 1 (COMAP官方) | high |
| 边界条件包括对流和辐射 | "前三项分别对应热传导、对流换热和辐射换热" | CUMCM 2020_A 建模思路 | Tier 2 | medium-high |

---

### 6.4 2016_A（系泊系统设计）

#### 问题概述
海洋观测站的系泊系统设计：浮标、钢管、钢桶、重物球、锚链组成的系统，在风和水流作用下保持稳定。需要：计算系统吃水深度和倾斜角（Q1）、优化锚链型号/长度/重物球质量（Q2/Q3）。

#### 四层映射

| 层 | 标注 | 详细说明 |
|---|---|---|
| **L1 Problem Structure** | `motion/geometry` | 系泊系统的静力平衡几何（悬链线）+ 刚体姿态，是几何建模+静力学问 题 |
| **L2 Modeling Pattern** | `distance/geometry`（悬链线几何 + 刚体约束） | 锚链形状为悬链线；浮标/钢管/钢桶为刚体，力和力矩平衡 |
| **L3 Mathematical Formulation** | `ODE`（悬链线方程，两点边值）+ `optimization`（多目标优化）+ `linear algebra`（力的分解） | 悬链线 y(x) = a·cosh(x/a)+b（由静力平衡 ODE 导出）；力平衡 ΣF=0, ΣM=0；多目标优化 min(吃水深度, 游动区域, 倾斜角) |
| **L4 Solver/Algorithm** | `numerical ODE`（打靶法/有限差分解边值）+ `numerical optimization`（遍历/多目标搜索） | 对不同锚链型号遍历求解静力平衡方程；搜索最优参数组合 |

#### 为什么这种建模路线是合理的

1. **静力平衡而非动力学**：系统在稳定状态下保持静止，不需要时间演化，是静力学问 题。锚链的悬链线形状由静力平衡 ODE 描述。
2. **悬链线是标准模型**：均匀柔性链条在重力下的平衡形状是悬链线，这是经典力学的标准结果，有解析解。
3. **刚体+柔性体混合**：浮标/钢管/钢桶是刚体（用力和力矩平衡），锚链是柔性体（用悬链线），需要分段建模再在连接处耦合。
4. **优化是多目标参数优化**：决策变量是锚链型号（离散）、长度（连续）、重物球质量（连续），目标是吃水深度/游动区域/倾斜角最小化。

#### 证据

| claim | evidence | source | source_type | confidence |
|---|---|---|---|---|
| 锚链简化为悬链线，由静力平衡导出 | "将锚链简化为悬链线... 使用微积分方法求出锚链垂向投影长度与锚链长的关系式" | CUMCM 2016_A 官方优秀论文 + 人人文库点评 | Tier 1 | high |
| 系统建模基于力和力矩平衡 | "利用静力平衡和力矩平衡，分别对浮标、钢管、钢桶和重物球进行静力学分析" | CUMCM 2016_A 优秀论文 (豆丁网) | Tier 1/Tier 2 | high |
| Q3 是多目标优化问题 | "以锚链型号、锚链长度、重物球配重作为决策变量，建立了多目标非线性规划模型" | CUMCM 2016_A 优秀论文 | Tier 1 | high |
| 悬链线方程有解析形式 | "y = (T₁cosα₁/σg)cosh(σg x/(T₁cosα₁) + sinh⁻¹(tanα₁)) - ..." | CUMCM 2016_A 官方论文 (dxs.moe.gov.cn) | Tier 1 (COMAP官方) | high |

---

### 6.5 竞赛题四层映射汇总表

| 题目 | L1 | L2 | L3 | L4 | 核心物理量 |
|---|---|---|---|---|---|
| **2018_A** 高温服装 | diffusion | conservation law + spatial-temporal field + inverse problem | PDE (抛物型, 多层) + optimization | numerical PDE (FDM) + 最小二乘反演 | 温度 T(x,t) |
| **2024_A** 板凳龙 | motion/geometry | distance/geometry (刚体+碰撞+螺线) | ODE (递推) + optimization + linear algebra | kinematics simulation + collision detection + optimization | 位置 (x_i(t), y_i(t)) |
| **2020_A** 回流焊 | diffusion | conservation law + spatial-temporal field | PDE (抛物型, 对流边界) + optimization | numerical PDE (FDM) + 参数搜索 | 温度 T(t) |
| **2016_A** 系泊系统 | motion/geometry | distance/geometry (悬链线+刚体) | ODE (边值) + optimization + linear algebra | numerical ODE + 多目标优化 | 链条形状 y(x), 倾角 |

---

## 7. 证据记录

### 7.1 守恒律与 PDE 关系

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E01 | 守恒律积分形式通过散度定理转化为微分形式 PDE | "d/dt∫ρdV = -∮ρu·n dS → ∂ρ/∂t + ∇·(ρu) = 0" | Univ. Toronto (Spiegelman) | Tier 1 | high | 标准推导，多来源交叉验证 |
| E02 | 三大守恒律分别导出连续性/NS/能量方程 | 完整表格对应关系 | 大连理工大学 (张博) | Tier 1 | high | 大学课程讲义，结构清晰 |
| E03 | 热传导方程由能量守恒+Fourier定律导出 | "Conservation of energy... lead to the parabolic PDE (cρ)u_t = ∇·(k∇u)+g" | UC Davis (Hunter) | Tier 1 | high | PDE 标准教材推导 |
| E04 | 通用守恒方程 ∂u/∂t + ∇·F = S | "Every problem expressed as ∂u/∂t + ∇·F(u,∇u) = S(u,x,t)" | oxiflow | Tier 2 | high | 标准形式，多教材一致 |
| E05 | 2018_A 以能量守恒为建模起点 | "以 Fourier 定律和能量守恒定律为理论依据" | CUMCM 2018_A A401 | Tier 1 | high | 官方优秀论文原文 |

### 7.2 时空场与边界条件

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E06 | 分布参数系统需要 PDE，集中参数系统用 ODE | "Distributed parameter systems... requiring PDEs rather than ODEs" | IEEE | Tier 1 | high | IEEE 权威定义 |
| E07 | 三种边界条件 Dirichlet/Neumann/Robin | 完整数学形式定义 | PDE Master M1 Notes | Tier 1 | high | 标准分类 |
| E08 | Hadamard 适定性三条件 | "existence, uniqueness, continuous dependence on data" | KTH | Tier 1 | high | 经典定义 |
| E09 | 反向热方程是不适定问题 | "'Backward' heat equation ⇒ ill-posed" | KTH | Tier 1 | high | 经典反问题 |
| E10 | PDE 必须同时有初始条件和边界条件 | "PDEs require initial conditions and boundary conditions" | Sustainable Catalyst | Tier 2 | medium-high | 与多教材一致 |

### 7.3 PDE 分类与 PDE/ODE 拆分

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E11 | PDE 三类型由判别式 b²-4ac 决定 | 完整分类标准 | AMATH 453 + 中科院 | Tier 1 | high | 标准分类 |
| E12 | Laplace/heat/wave 分别对应椭圆/抛物/双曲 | "representing the three types with rather distinct properties" | 中科院数学所 | Tier 1 | high | 权威表述 |
| E13 | ODE 解是曲线，PDE 解是曲面 | "ODE solution is a curve, PDE solution is a surface/hypersurface" | Univ. Alberta | Tier 1 | high | 几何直观区分 |
| E14 | 建议拆分 PDE/ODE 为独立 L3 标签 | 6 项论据综合 | 本研究 | — | high | 建模思路/定解条件/数值方法均不同 |
| E15 | stochastic process 应独立于 DE | 数学基础不同（概率论 vs 微积分） | 本研究综合 | — | medium-high | 需进一步研究确认 |

### 7.4 Numerical PDE

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E16 | Lax 等价定理：一致性+稳定性⟺收敛性 | "For a consistent linear approximation, stability is necessary and sufficient for convergence" | Semantic Scholar | Tier 1 | high | 数值分析基石 |
| E17 | FDM/FEM/FVM 各有适用场景 | 对比表：FDM 规则网格, FEM 复杂几何, FVM 守恒 | rjsaonline + HAL | Tier 1/Tier 2 | high | 多来源一致 |
| E18 | 热方程显式格式稳定性 r≤0.5 | "r = αΔt/Δx² ≤ 0.5" | 本项目+标准教材 | Tier 1 | high | 经典结果 |
| E19 | Crank-Nicolson 是热传导首选 | 无条件稳定+二阶精度 | 多来源 | Tier 1 | high | 竞赛实践验证 |
| E20 | 2018_A 用 Du Fort-Frankel 格式 | "无条件稳定" | CUMCM 2018_A 优秀论文 | Tier 1 | high | 官方优秀论文 |
| E21 | 网格收敛性测试是标准验证方法 | "Δx 减半 → 变化 < 1%" | playbook+CFD标准 | Tier 2 | high | 工程标准实践 |

### 7.5 运动学/几何

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E22 | 正运动学由关节参数计算末端位姿 | "Forward kinematics computes position... DH convention" | IEEE | Tier 1 | high | IEEE 权威定义 |
| E23 | 碰撞检测分 broad/narrow phase | "OBB/SAT broad-phase, GJK narrow-phase" | ARB (Featherstone) | Tier 2 | medium-high | 标准机器人学 |
| E24 | 板凳龙用多体递推建模 | "x_{i+1} = x_i - d cosθ_i" | CUMCM 2024_A | Tier 1 | high | 官方论文 |
| E25 | 系泊系统锚链为悬链线 | "y = a·cosh(x/a)+b 形式" | CUMCM 2016_A | Tier 1 | high | 官方论文+期刊 |
| E26 | 运动学不需要力，动力学才需要 | "Kinematics: FK/IK/collision... Dynamics accounts for gravity, inertia, Coriolis" | IEEE + fieldpilot | Tier 1 | high | 标准区分 |

### 7.6 竞赛题

| ID | claim | evidence | source | source_type | confidence | reasoning |
|---|---|---|---|---|---|---|
| E27 | 2018_A 控制方程为四层热传导 PDE | "ρ_j c_j ∂T/∂t = ∂/∂x(λ_j ∂T/∂x)" | CUMCM 2018_A 官方 | Tier 1 | high | 官方论文原文 |
| E28 | 2018_A 参数反演用最小二乘 | "基于最小二乘原理... 拟合实测温度" | CUMCM 2018_A A440 | Tier 1 | high | 官方论文 |
| E29 | 2024_A 是 224 节多刚体运动学 | "由224节板凳组成... 多刚体运动学问题" | 《实验科学与技术》 | Tier 1 (期刊) | high | 同行评审期刊 |
| E30 | 2024_A 首次碰撞在龙头与龙身之间 | "龙头更靠近中心... 首次碰撞应发生在龙头与龙身之间" | SciEngine 期刊 | Tier 1 | high | 期刊论文分析 |
| E31 | 2020_A 是一维热传导+对流辐射边界 | "ρc_p ∂T/∂t = k∂²T/∂x² + h(T_env-T) + εσ(...)" | CUMCM 2020_A 汇总 | Tier 1/Tier 2 | high | 多来源一致 |
| E32 | 2016_A 是悬链线+静力平衡+多目标优化 | "多目标非线性规划模型" | CUMCM 2016_A | Tier 1 | high | 官方论文 |

---

## 8. 争议与不确定项

### 8.1 UNCERTAIN：stochastic process 是否应作为 L3 独立标签

**现状**：本研究建议将 stochastic process 作为独立于 differential equation 的 L3 标签，但存在以下不确定性：

- **支持独立**：随机过程的数学基础是概率论/测度论，SDE（随机微分方程）同时涉及微分和随机积分，与确定性 DE 有本质区别。Markov 链、排队论等完全不涉及微分。
- **反对独立**：SDE 可以视为 ODE 的推广（加噪声项），某些分类体系将其归入 differential equation 的子类型。
- **竞赛相关性**：国赛 A 题（连续物理域）中纯随机过程题较少，但 B/C 题中 Markov 链、排队论有出现。本域（连续物理）是否需要覆盖 stochastic process 取决于标签体系的域划分策略。
- **建议**：将 stochastic process 列为 L3 独立标签，但在本域（连续物理）的方法卡中仅覆盖与物理相关的 SDE/随机游走（如扩散的微观解释），Markov 链/排队论归其他域。

**置信度**：medium。需要与其他域代理（离散/随机域）协调标签边界。

### 8.2 UNCERTAIN：inverse problem 应放在 L2 还是 L3

**现状**：2018_A 的参数反演是核心环节。当前 L2 标签集不含 inverse_problem（审计报告建议新增），L3 也没有对应标签。

- **放 L2 的理由**：反问题是一种建模模式——"已知输出反求输入/参数"，与正问题（已知输入求输出）相对，是问题的结构特征。
- **放 L3 的理由**：反问题通常表述为优化问题（min 残差），数学形式是 optimization + PDE 约束。
- **建议**：inverse_problem 作为 L2 标签（建模模式），其数学表述用 L3 的 optimization + PDE 组合标注。这与审计报告的建议一致。

**置信度**：medium-high。

### 8.3 UNCERTAIN：2024_A 是否涉及 ODE

**现状**：板凳龙的多体递推 x_{i+1} = x_i - d·cosθ_i 本质是**代数递推关系**，不是严格意义上的 ODE。但方位角 θ_i(t) 由位置差分 θ_i = arctan(Δy/Δx) 确定，隐含了微分关系。

- **严格 ODE 视角**：如果将运动学写成 dx_i/dt = v_i(t)，其中 v_i 由约束确定，则是 ODE 初值问题。
- **代数递推视角**：离散时间步的递推公式是差分方程，不是 ODE。
- **建议**：L3 标注为 ODE（运动学方程的连续形式）+ linear algebra（坐标变换），数值求解用 kinematics simulation（离散递推）。这在概念上是自洽的：连续模型是 ODE，数值实现是递推。

**置信度**：medium。

### 8.4 UNCERTAIN：FEM 在国赛中的适用性

**现状**：FEM（有限元）在学术和工业中是 PDE 求解的主流方法，但在数学建模竞赛中极少使用。

- **不适用的理由**：FEM 需要网格生成、矩阵组装、稀疏求解器，实现复杂度远高于 FDM，竞赛时间（3天）内不现实。
- **可能适用的场景**：复杂几何区域（如二维不规则域）的椭圆型问题，FDM 难以处理边界。
- **建议**：方法卡中 FEM 作为 `supports` 提及，但 `not_for` 应标注"竞赛时间限制下通常不推荐一维/简单二维问题"。FDM 是竞赛首选。

**置信度**：high（关于竞赛适用性），medium（关于是否应在方法卡中详细展开 FEM）。

### 8.5 UNCERTAIN：distance/geometry 是否需要拆分为 distance 和 geometry 两个标签

**现状**：当前 L2 标签 distance/geometry 合并了"距离约束"和"几何建模"两个概念。

- **distance**：碰撞检测、刚体约束、定位（核心是距离计算）
- **geometry**：螺旋线参数化、悬链线、坐标变换（核心是几何形状/变换）
- **合并的理由**：二者高度交织，碰撞检测需要几何表示，几何建模最终导出距离约束。
- **拆分的理由**：2024_A 同时涉及螺线几何（geometry）和碰撞距离（distance），但二者的建模方法不同（参数化 vs 距离判定）。
- **建议**：暂不拆分，保持 distance/geometry 合并标签，但在方法卡的 `supports` 字段中区分"几何参数化"和"距离/碰撞约束"两个子能力。

**置信度**：medium。

### 8.6 已确认无争议项

以下结论经多来源交叉验证，无争议：

1. ✅ 守恒律通过散度定理从积分形式导出微分形式 PDE
2. ✅ 热传导方程是抛物型 PDE，由能量守恒+Fourier 定律导出
3. ✅ PDE 分椭圆/抛物/双曲三类，定解条件结构不同
4. ✅ Lax 等价定理：一致性+稳定性⟺收敛性（线性问题）
5. ✅ FDM 是国赛 PDE 题的首选数值方法
6. ✅ 2018_A 是多层一维热传导 PDE + 参数反演
7. ✅ 2024_A 是多刚体运动学 + 几何建模 + 碰撞检测
8. ✅ ODE 与 PDE 应拆分为独立 L3 标签
9. ✅ 运动学（kinematics）不涉及力，动力学（dynamics）才涉及
10. ✅ 当前知识库 L2 conservation law / spatial-temporal field 零覆盖是 2018_A method_selection=0 的根本原因之一

---

## 9. 对知识架构校准的建议

### 9.1 L1 层

- `diffusion`：保留，定义需明确包含热传导、质量扩散、动量扩散
- `motion/geometry`：保留，定义需明确包含运动学、几何建模、空间定位、轨迹规划

### 9.2 L2 层（本域核心缺失层）

**必须新增/强化的标签**：
- `conservation law`：当前零覆盖，需建立方法卡。核心字段：守恒量类型（质量/能量/动量）、积分vs微分形式、本构定律要求、导出PDE的路径
- `spatial-temporal field`：当前零覆盖，需建立方法卡。核心字段：场变量类型、边界条件类型、初始条件要求、适定性检查
- `distance/geometry`：当前仅 TOPSIS 弱覆盖，需新增运动学/几何语境的方法卡。核心字段：刚体约束、碰撞检测、几何参数化、轨迹约束

### 9.3 L3 层

- **将 `differential equation` 拆分为 `PDE` 和 `ODE`** 两个独立标签
- `PDE` 子类型（椭圆/抛物/双曲）作为方法卡字段，不提升为标签
- `stochastic process` 建议作为独立标签（需与其他域协调）
- `inverse problem` 建议放在 L2（建模模式），不放在 L3

### 9.4 L4 层

- `numerical PDE`：保留，需建立方法卡。核心字段：FDM/FEM/FVM 选择指南、稳定性条件、验证方法
- **新增 `numerical ODE / kinematics simulation`**：与 numerical PDE 区分，覆盖 RK4、多体递推、碰撞检测
- 现有 `mc-grey-gm11` 的灰色微分方程是弱覆盖，不能替代 PDE/ODE 卡

### 9.5 方法卡设计原则（Constraint/Prior/Validation）

以 conservation law 方法卡为例（仅设计方向，不实现）：

```yaml
card_id: mc-conservation-law
name: 守恒律建模
family: physical_modeling
l1_problem_structures: [diffusion]
l2_modeling_patterns: [conservation law, spatial-temporal field]
l3_formulations: [PDE]
l4_solver_type: [numerical PDE]

requires:
  - 可识别守恒量（质量/能量/动量）
  - 可定义控制体和边界通量
  - 已知本构定律（Fourier/Fick/牛顿粘性）或可假设

supports:
  - 热传导/扩散问题的 PDE 推导
  - 流体连续性方程
  - 多层介质界面条件建模
  - 积分形式→微分形式的标准推导

risks:
  - 遗漏源/汇项（化学反应、内热源）
  - 边界条件类型错误（将对流当 Dirichlet）
  - 多层介质界面条件缺失
  - 将守恒律当 PDE（混淆 L2 和 L3）

verification:
  - 检查无源项时总守恒量是否守恒
  - 检查量纲一致性
  - 检查边界条件数量是否足够（PDE 阶数决定）

not_for:
  - 纯离散/调度问题（无连续场）
  - 纯运动学问题（无守恒量）
  - 数据驱动问题（无物理机理）
```

---

## 10. 参考文献索引

### Tier 1（大学/教材/同行评审/官方）

1. University of Toronto, Spiegelman, "Conservation Laws" — http://www.math.toronto.edu/nhoell/spiegelman_conservation.pdf
2. UC Davis Math, Hunter, "PDE Notes: Heat Flow" — https://www.math.ucdavis.edu/~hunter/pdes/ch4A.pdf
3. KTH Royal Institute of Technology, "PDEs: Introduction and Elliptic PDEs" — https://www.csc.kth.se/utbildning/kth/kurser/DN2266/matmod12/PDE1_2p.pdf
4. 中国科学院数学与系统科学研究院, "Fully Nonlinear PDEs" — http://www.math.ac.cn/english/xshd/sxsjz/202212/W020221207671080405580.pdf
5. Radboud University, "An Introduction to Partial Differential Equations" — https://www.math.ru.nl/~ssonner/PDEs_lecturenotes(2024_25).pdf
6. University of Alberta, "PDE Chapter 1" — https://sites.ualberta.ca/~niksirat/PDE/chapter-1pde.html
7. Stanford University Math, "PDE and Diffusion Processes" — http://math.stanford.edu/~ryzhik/STANFORD/STANF227-11/notes227-09.pdf
8. IEEE Technology Navigator, "Distributed Parameter Systems" — https://technav.ieee.org/topic/distributed-parameter-systems/
9. IEEE Technology Navigator, "Robot Motion" — https://technav.ieee.org/topic/robot-motion/
10. Northwestern University, Park & Lynch, "Introduction to Robotics: Mechanics, Planning, and Control" — https://hades.mech.northwestern.edu/images/archive/2/2a/20151203165353!Park-lynch.pdf
11. MIT CSAIL, "Robotic Manipulation: Basic Pick and Place" — https://manipulation.csail.mit.edu/pick.html
12. CUMCM 2018_A 官方优秀论文 A401/A440/A466 — https://dxs.moe.gov.cn/
13. CUMCM 2024_A 官方优秀论文 A016/A053/A163/A178 — https://dxs.moe.gov.cn/
14. CUMCM 2020_A 官方讲评（蔡志杰） — https://dxs.moe.gov.cn/zx/a/qkt_sxjm_sxjmstjp/201203/1601195.shtml
15. CUMCM 2016_A 官方优秀论文 — https://dxs.moe.gov.cn/
16. 《实验科学与技术》, "民俗活动'板凳龙'行进状态建模与路径优化研究" — https://t4.sciengine.com/doi/10.12179/1672-4550.20240676
17. 《实验科学与技术》, "基于受力分析的系泊系统优化模型" — http://www.sy.uestc.edu.cn/en/article/pdf/preview/10.3969/j.issn.1672-4550.2017.06.002.pdf
18. Semantic Scholar, "Computational Methods for Differential Equations" — https://pdfs.semanticscholar.org/f16b/9a850d198507c3514a1f59d454537f3b661d.pdf
19. Wiley, "Comparative Study of FDM and FEM for 2D Parabolic CDR Equations" — https://onlinelibrary.wiley.com/doi/full/10.1155/ijde/2126609
20. 大连理工大学, "Navier-Stokes 方程概览" — http://faculty.dlut.edu.cn/ejector/zh_CN/article/738076/content/6459.htm

### Tier 2（高质量专业资料）

21. NIST, "PF Recommended Practices: Model Formulation" — https://pages.nist.gov/pf-recommended-practices/bp-guide-gh/ch1-model-formulation.html
22. Wolfram, "Heat Transfer PDE Models" — https://reference.wolfram.com/language/PDEModels/tutorial/HeatTransfer/HeatTransfer.html
23. COMSOL, "Modeling with PDEs: Diffusion-Type Equations" — https://www.comsol.com/support/learning-center/article/Modeling-with-Partial-Differential-Equations-Diffusion-Type-Equations-43711
24. Oregon State University Physics, "Initial and Boundary Conditions on PDEs" — https://books.physics.oregonstate.edu/GCF/pdethms.html
25. Sustainable Catalyst, "Introduction to PDEs" — https://sustainablecatalyst.com/introduction-to-partial-differential-equations/
26. Sustainable Catalyst, "Diffusion, Transport, and Spatial Dynamics" — https://sustainablecatalyst.com/diffusion-transport-and-spatial-dynamics/
27. Mathematics LibreTexts (Sayama), "Continuous Field Models" — https://math.libretexts.org/Bookshelves/Scientific_Computing_Simulations_and_Modeling/
28. HAL Archive, "Numerical Methods for Nonlinear PDEs in Fluid Dynamics" — https://hal.science/hal-05094230v1
29. Preprints.org, "Numerical Methods for Incompressible Viscous Flows" — https://www.preprints.org/manuscript/202604.0558
30. CUMCM 2018_A 优秀论文 (lucajiang) — https://lucajiang.github.io/images/cumcm2018.pdf
31. CUMCM 2020_A 学术报告 (peterkam) — https://academic.peterkam.top/files/report/CUMCM_2020_Report.pdf

### Tier 3（仅用于关键词发现）

32. CSDN 相关解题思路（不作为关键结论唯一依据）
33. GitHub 相关实现仓库（用于验证竞赛实践做法）

---

*本研究文档为 research-layer calibration 证据文件，所有结论用于知识架构校准，不涉及修改 core/knowledge 下的任何现有文件。方法卡设计仅为方向建议，未实现。*
