# Cookbook: 优化类模型

> 适用场景：目标函数明确、有约束条件、寻找最优决策变量。CUMCM A题、MCM B/D题高频。

---

## 1. 线性规划 / 整数线性规划 (LP / ILP / MILP)

| 项目 | 内容 |
|------|------|
| **适用场景** | 目标函数与约束均为线性；决策变量连续/整数/混合；规模中等（变量<1000，约束<500） |
| **核心公式** | min $c^T x$ s.t. $Ax \le b, x \ge 0, x_i \in \mathbb{Z}$ |
| **求解器** | `pulp` (CBC), `ortools` (SCIP/GLOP), `gurobi`/`cplex` (商业), `scipy.optimize.linprog` |
| **代码模板** | `core/Programmer/knowledge/code-templates/optimization/lp_template.py` |
| **参数敏感性** | 影子价格（对偶变量）指示约束松紧；基变量退化需防循环 |
| **常见坑** | 1) 大M法数值不稳 → 用指示约束/分段线性<br>2) 对称性导致分支定界慢 → 加对称性打破约束<br>3) 整数可行域为空 → 软约束惩罚+松弛变量 |
| **验证清单** | ✅ 可行解存在 ✅ 对偶间隙=0 (LP) / <1% (MILP) ✅ 约束回代满足 ✅ 多种子稳定 |
| **文献支撑示例** | [1] CUMCM2024A 国一：多目标 MILP + ε-约束法<br>[2] MCM2023B O奖：网络流 MILP + 柱生成 |

---

## 2. 非线性规划 (NLP)

| 项目 | 内容 |
|------|------|
| **适用场景** | 目标/约束非线性但可微；连续变量；局部最优可接受或凸问题 |
| **核心公式** | min $f(x)$ s.t. $g_i(x) \le 0, h_j(x) = 0$ |
| **求解器** | `scipy.optimize.minimize` (SLSQP/trust-constr), `ipopt` (via `cyipopt`), `casadi` |
| **代码模板** | `core/Programmer/knowledge/code-templates/optimization/nlp_template.py` |
| **参数敏感性** | 初始点对局部最优影响大 → 多起点；梯度精度影响收敛 → 用自动微分 |
| **常见坑** | 1) 非凸多局部最优 → 全局搜索/多起点<br>2) 约束资格不满足 (KKT 失效) → 正则化/松弛<br>3) 尺度差异大 → 变量归一化 |
| **验证清单** | ✅ KKT 条件满足 ✅ 多起点收敛同值 ✅ 约束满足 ✅ 二阶充分条件 |
| **文献支撑示例** | [1] CUMCM2021A 国二：化工工艺 NLP + IPOPT<br>[2] MCM2020A F奖：流行病参数反演 NLP |

---

## 3. 多目标优化

| 项目 | 内容 |
|------|------|
| **适用场景** | 多个冲突目标（成本/时间/风险/排放）；需给出 Pareto 前沿供决策者权衡 |
| **核心方法** | ε-约束法、加权和法、Tchebycheff、正规边界交叉 (NBI)、NSGA-II/III、MOEA/D |
| **代码模板** | `core/Programmer/knowledge/code-templates/optimization/moo_nsga2.py`, `moo_epsilon.py` |
| **关键指标** | HV (超体积)、IGD (倒代际距离)、Spread (分布均匀性) |
| **常见坑** | 1) 目标量纲/量级差异 → 归一化<br>2) Pareto 前沿断裂/稀疏 → 增加种群/迭代/引入参考点<br>3) 决策者偏好未量化 → 事后交互式选择/膝点识别 |
| **验证清单** | ✅ 非支配排序正确 ✅ HV 收敛稳定 ✅ 前沿覆盖目标空间 ✅ 膝点/极值点识别 |
| **文献支撑示例** | [1] CUMCM2023A 国一：NSGA-III + 参考点生成<br>[2] MCM2022D O奖：MOEA/D + 分解策略 |

---

## 4. 启发式/元启发式算法 (GA/PSO/SA/ACO/DE/HS)

| 算法 | 适用场景 | 关键参数 | 代码模板 | 必做验证 |
|------|----------|----------|----------|----------|
| **GA** | 离散/混合变量、非凸、多模态 | 种群100-500、交叉0.8-0.9、变异0.01-0.1、精英保留 | `ga_template.py` | ≥30次独立运行、收敛曲线、最优/均值/标准差 |
| **PSO** | 连续高维、可微/不可微均可 | 惯性0.4-0.9、认知/社会1.5-2.0、速度钳制 | `pso_template.py` | 同 GA + 粒子轨迹可视化 |
| **SA** | 组合优化、大邻域、易陷局部 | 初始温度、冷却0.95-0.99、终止温度、马尔可夫链长 | `sa_template.py` | 多轨迹、接受率监控 |
| **ACO** | 图路径/排序/调度 | 信息素挥发0.1-0.5、启发式因子、蚂蚁数 | `aco_template.py` | 收敛性、多次运行 |
| **DE** | 连续全局优化、鲁棒性强 | F∈[0.5,1]、CR∈[0.1,0.9]、种群10D | `de_template.py` | 同 GA |

**铁律 P6 强制**：所有启发式算法 **必须 ≥5次独立运行（建议 30 次）**，报告均值±标准差，CV ≤ 10% 否则加大种群/迭代。

---

## 5. 动态规划 (DP) / 马尔可夫决策过程 (MDP)

| 项目 | 内容 |
|------|------|
| **适用场景** | 多阶段决策、最优子结构、无后效性；库存/调度/路径/资源分配 |
| **核心公式** | $V_t(s) = \max_a \{ r(s,a) + \gamma \mathbb{E}[V_{t+1}(s')] \}$ |
| **代码模板** | `core/Programmer/knowledge/code-templates/optimization/dp_template.py`, `mdp_template.py` |
| **维度灾难** | 状态空间 >10^6 → 近似 DP / 强化学习 / 状态聚合 |
| **常见坑** | 1) 状态定义冗余 → 精简状态<br>2) 转移概率未知 → 模型免强化学习 (Q-learning/DQN)<br>3) 连续状态/动作 → 离散化/函数逼近 |
| **验证清单** | ✅ Bellman 方程残差小 ✅ 策略收敛 ✅ 与贪心/启发式基线对比 |
| **文献支撑示例** | [1] CUMCM2019B 国一：车辆路径 DP+列生成<br>[2] 电工杯2021：储能调度 MDP+近似价值迭代 |

---

## 6. 鲁棒优化 / 随机规划

| 方法 | 适用场景 | 核心思想 | 代码模板 |
|------|----------|----------|----------|
| **鲁棒优化** | 参数不确定、集合描述 (区间/椭球/多面体) | 最坏情况保护：$\min_x \max_{u\in\mathcal{U}} f(x,u)$ | `robust_template.py` |
| **两阶段随机规划** | 不确定参数有分布、可观测实现后补救 | $\min_x c^T x + \mathbb{E}_\xi[Q(x,\xi)]$ | `stochastic_2stage.py` |
| **机会约束** | 允许小概率违反约束 | $\mathbb{P}(g(x,\xi)\le 0) \ge 1-\alpha$ | `chance_constrained.py` |

**常见坑**：不确定性集过保守 → 调整 $\Gamma$/置信度；场景树爆炸 → 场景缩减/采样平均近似 (SAA)。

---

## 7. 代码模板目录映射

```
core/Programmer/knowledge/code-templates/optimization/
├── lp_template.py           # LP/MILP (pulp/ortools)
├── nlp_template.py          # NLP (scipy/ipopt)
├── moo_nsga2.py             # NSGA-II (platypus/pymoo)
├── moo_epsilon.py           # ε-约束法
├── ga_template.py           # 遗传算法
├── pso_template.py          # 粒子群
├── sa_template.py           # 模拟退火
├── aco_template.py          # 蚁群
├── de_template.py           # 差分进化
├── dp_template.py           # 动态规划
├── mdp_template.py          # 马尔可夫决策
├── robust_template.py       # 鲁棒优化
├── stochastic_2stage.py     # 两阶段随机规划
└── chance_constrained.py    # 机会约束
```

---

## 8. 选型决策树 (优化类)

```
目标函数/约束线性？
├─ 是 → 变量整数？
│   ├─ 全连续 → LP (pulp/ortools) → 首选
│   └─ 有整数 → MILP (pulp/ortools/SCIP) → 首选
└─ 否 → 可微？
    ├─ 是 → 凸？
    │   ├─ 是 → NLP (IPOPT/SLSQP) → 首选
    │   └─ 否 → 多目标？
    │       ├─ 是 → NSGA-II/III (pymoo) → 首选
    │       └─ 否 → 多起点 NLP + 全局搜索 (DE/PSO) → 备选
    └─ 不可微/离散/黑盒 → 启发式 (GA/PSO/SA/DE/ACO) → 备选
        └─ 有序列/路径结构 → ACO → 首选
```

---

## 9. 竞赛实战提示

| 竞赛 | 题型 | 推荐首选 | 避坑指南 |
|------|------|----------|----------|
| CUMCM A | 优化 | MILP/NSGA-II | 变量上界=物理上界；硬约束软化 |
| CUMCM B | 实验/机理+优化 | NLP/DP | 先机理拟合参数，再优化 |
| CUMCM D | 运筹/网络 | 网络流/MLP/ACO | 图规模大→列生成/启发式 |
| MCM B | 离散优化 | MILP/ACO/GA | Memo 中明确模型命名 |
| MCM D | 网络/运筹 | 网络流/列生成 | Letter 量化政策建议 |
| 电工杯 | 工程优化 | MILP/鲁棒 | 物理约束硬、工程可行性优先 |

---

*版本：1.0 | 更新：2026-09-01 | 维护：Modeler 手*