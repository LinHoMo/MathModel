# MODELING_KNOWLEDGE_GOVERNANCE — Modeling Knowledge 治理规范（方向锁定 v1.1）

> 生效日期：2026-09-08 ｜ 状态：**ARCHITECTURE FROZEN**（架构已冻结，变更需走 RFC）
> 适用范围：MathModel Harness 全系统（V3 runtime + V2 legacy 兼容层 + benchmark + evaluation）
> 核心命题：方法卡 = Constraint / Prior / Validation，**不是答案库**。
> 核心哲学（v1.1 增补）：
> **The LLM constructs models. Knowledge constrains and informs construction. Evidence decides whether the construction survives.**

## 1. 文档定位

本文档锁定 Modeling Knowledge（方法卡体系）在 MathModel Harness 中的**角色定位与治理边界**。
自生效之日起，任何对三层模型定位、方法卡语义、benchmark 评估字段的解释均以本文档为准；
与本文档冲突的既有表述（如 `core_methods` 作为评估字段、`reference_method` 匹配评分）
视为历史遗留，按第 8 节历史更正记录逐步迁移。

## 2. 三层模型定义（核心）

```
Layer 1: LLM = Model Generator
  - 自由建模思考，不是方法卡的执行器
  - 可以提出任何新方法/新模型，不受 catalog 限制
  - 创造力不受 Knowledge coverage 约束

Layer 2: Modeling Knowledge = Constraint / Prior
  - 方法卡不告诉 LLM "必须用 X"
  - 方法卡告诉 LLM "如果你考虑 X，需要满足这些条件"
  - 提供 requirements / supports / risks / verification / anti_patterns
  - Knowledge coverage constrains evaluation, not constrain creativity

Layer 3: Evidence = Adjudication
  - 实验和证据才决定模型是否成立
  - Method Card 产生候选先验（candidate prior）
  - Evidence 产生成立证据（validated evidence）
  - 没有证据支撑的模型声明不可信
```

三层之间的关系：**Layer 1 产出候选 → Layer 2 提供约束与先验 → Layer 3 裁决成立与否**。
Knowledge 永远不替代 Evidence 做最终裁决。

## 2.1 方法卡 = 可调用的建模知识单元（v1.1 锁定）

方法卡不是"算法说明书"（步骤/公式罗列），而是 **Model Construction Knowledge
（建模决策基础设施）**——一组可调用的建模知识单元，回答"这个问题怎么从现实结构走到
数学模型"：

| 知识维度 | 对应字段 | 作用 |
|---|---|---|
| 适用问题结构 | `problem_structures` + `problem_types` | 判断问题是否属于该建模结构族 |
| 建模机理 | `mechanism` | 该方法成立所依赖的问题内在结构/因果机制（Bellman 原理 / 守恒律 / 到达-服务过程）——供 LLM 判断"这个问题是否具有该结构" |
| 数学结构 | `formulations` + `mathematical_forms` | 典型数学表述，帮助评估结构匹配，不是强制实现清单 |
| 求解策略 | `solvers` | 常用求解器（与数学形式严格区分：PDE ≠ numerical_PDE） |
| 适用/不适用 | `good_for` + `anti_patterns` | 什么时候该用、什么时候不该用 |
| 可验证证据 | `validation` | 必做验证步骤——产生成立证据 |

方法卡允许 LLM **不使用它**：LLM 可自由提出 catalog 外的新模型（`out_of_catalog`），
只要给出数学合理性与结构证据。方法卡是"约束/启发/可验证知识"，不是"菜单"。

## 3. 关键治理原则

### 原则 1：Knowledge coverage must constrain evaluation, not constrain creativity.

- 知识库可以限制"你声称某方法适用"的资格（如果你说用了 TOPSIS，必须满足 TOPSIS 的 requires）
- 知识库不能限制 LLM"提出一个新方法/新模型"的自由（LLM 可以提出 catalog 中没有的方法）
- catalog 外的方法标记为 `out_of_catalog`，不自动判错，需检查数学合理性

### 原则 2：Research-layer calibration ≠ Agent capability intervention

- 方法卡修复后 method-selection 分数上涨 = measurement instrument validity ↑（测量工具效度提升）
- ≠ Agent capability ↑（不是 Agent 能力提升）
- 指标定义的变更属于 measurement calibration，不是架构变更
- 评估指标的改进不应被解读为 Agent 能力的改进

### 原则 3：多解模型原则（Multiple Acceptable Solution Families）

- 每道题有多个 allowed_model_families，不是一个 gold method
- benchmark 定义 `allowed_model_families` + `acceptable_solution_variants`
- 不指定"核心方法"（core_methods 仅保留为 historical_core_methods 用于追溯）
- Agent 选择任何 allowed family 中的方法都算兼容

### 原则 4：结构覆盖优先于算法覆盖（v1.1 修正）

- **覆盖单位是"建模结构"，不是"算法数量"**。问"覆盖了多少种典型建模结构（dynamic
  systems / optimization / field / network / queue / game...）"，不问"有多少张卡"。
- 方法卡数量**不是核心 KPI**；追求结构覆盖的正确性、适用性精度与验证有用性。
- 知识覆盖评价指标：

| 指标 | 含义 |
|---|---|
| family coverage | 覆盖多少建模结构族 |
| applicability precision | 方法被正确使用的比例 |
| applicability recall | 应该想到的方法是否被想到 |
| construction usefulness | 是否帮助构造模型（而非只命中名字） |
| misuse detection | 是否能阻止错误套用 |
| validation usefulness | 是否提供可验证结构 |
| downstream success | 是否真正改善下游实验/论文 |

- P0 三张卡（mc-dp / mc-numerical-pde / mc-queuing-theory）定位为**知识架构校准样本**，
  分别覆盖离散序贯决策 / 连续时空场 / 随机服务系统三个不同的 model construction regime，
  用于验证 Method Card Schema 是否真正表达"建模知识"，而非"又加了三张算法卡"。

### 原则 5：三层知识体系（v1.1 新增）

```
Model Construction Knowledge
  ├── Ontology      — 问题是什么结构（L1 Problem Structure → L2 Modeling Pattern）
  ├── Method Cards  — 怎么建模型（建模机理/结构/验证知识）
  └── Cases         — 别人怎么做过（真实题面→建模路线的实例化）
```

三者不混：paper-case ≠ problem statement，paper-case ≠ method card。Case 是 Method Card
在真实问题中的实例化证据，不能反向变成唯一 gold。

### 原则 6：Tier 0-3 核心覆盖策略（不追求全方法覆盖）

- 不追求穷尽所有数学建模方法（那是不可能的，也限制创造力）
- 采用 Tier 分级覆盖：

| Tier | 类别 | 覆盖要求 | 示例 |
|---|---|---|---|
| Tier 0 | 基础方法 | 必须有完整方法卡 | 评价、回归、优化、仿真 |
| Tier 1 | 高频竞赛方法 | 必须有完整方法卡 | TOPSIS / AHP / ARIMA / GA / PSO / Monte Carlo |
| Tier 2 | 中频方法 | 应有方法卡 | LSTM / XGBoost / NSGA-II / 灰色预测 |
| Tier 3 | 低频/前沿方法 | 可选，不强制 | — |

- 覆盖目标：Tier 0-1 100%，Tier 2 ≥80%，Tier 3 按需
- **先做校准样本证明知识架构有效 → Fresh B0 看真实 failure → 再决定下一批知识覆盖**；
  不预先堆 100 张卡。

## 4. 方法卡定位规范

### 必填字段

方法卡必须包含：

- `requires`: 使用前提（数据/假设/规模条件）
- `risks`: 已知风险
- `validation`: 必做验证步骤
- `anti_patterns`: 误用形态

### 可选字段

方法卡可以包含：

- `problem_structures`: 适配的问题结构
- `modeling_patterns`: 建模模式
- `mathematical_forms`: 数学形式
- `mechanism`: 建模机理（该方法成立所依赖的问题内在结构/因果机制）
- `formulations`: 典型数学表述/核心公式
- `solvers`: 常用求解器/求解策略

### 禁止事项

方法卡**禁止**：

- 使用"推荐使用"、"最佳选择"等排他性表述
- 指定某道题"必须使用"某方法
- 作为自动选方法的硬过滤依据（match 字段仅用于检索排序）
- 把算法步骤当卡主体（方法卡是建模知识单元，不是算法说明书）

## 5. Benchmark 规范

### 必填字段

每道 benchmark 题必须包含：

- `allowed_model_families`: 允许的模型族列表（评分依据）
- `acceptable_solution_variants`: 可接受的具体方法列表
- `historical_core_methods`: 历史追溯字段（原 core_methods，不参与评估）

### 可选字段

- `forbidden_misinterpretations`: 明显不适合的方法族

### 禁止事项

Benchmark **禁止**：

- 使用 `core_methods` 作为评估字段
- 指定单一 gold method
- 限制 LLM 提出新方法

## 6. 评估指标规范

### method_selection（已更名为"方法兼容性评估"）

- **定义**：检查 Agent 选择的方法族是否在 benchmark `allowed_model_families` 中
- **评分**：兼容性评分 0-100（家族命中 + 方法卡 requirements 满足度）
- **catalog 外方法**：标记 `out_of_catalog`，不直接判 0，检查数学合理性
- **不使用**：参考方法匹配（reference_method matching）、核心方法命中（core_methods hit）

## 7. 变更管理

- 本文档为架构冻结文档（ARCHITECTURE FROZEN）
- 任何对三层模型定位的变更需走 RFC 流程
- 方法卡内容的增删改属于常规维护，不需 RFC
- benchmark 字段的变更需更新本文档的对应章节

## 8. 历史更正记录

- **2026-09-08**: 方向锁定 v1.0 发布。从"方法卡=答案库"彻底改正为"方法卡=约束/先验/验证"。
  - `core_methods` → `allowed_model_families`
  - `reference_method` → 方法兼容性检查
  - 方法卡定位从"推荐/答案"改为"约束/先验/验证"
- **2026-09-08**: 方向锁定 v1.1（本轮）。核心哲学明确为
  "The LLM constructs models. Knowledge constrains and informs construction.
  Evidence decides whether the construction survives."。
  - 方法卡升级为"可调用的建模知识单元（Model Construction Knowledge）"：新增
    `mechanism` / `formulations` / `solvers` 三个建模知识字段（schema 同步扩展）
  - 结构覆盖优先于算法覆盖；方法卡数量不再作为核心 KPI
  - 允许 LLM 不用方法卡（out_of_catalog 合法通道，需结构证据）
  - 新增三层知识体系 Ontology / Method Cards / Cases
  - P0 三张卡（mc-dp / mc-numerical-pde / mc-queuing-theory）落地为知识架构校准样本，
    对应题 allowed_model_families 同步补齐（2020_B +dynamic_programming /
    2018_A +numerical_pde / 2019_C +queuing_theory）
