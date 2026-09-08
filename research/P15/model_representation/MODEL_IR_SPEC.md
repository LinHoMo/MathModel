# Model IR / Model Graph 设计规范

- **版本**: v1.0
- **日期**: 2026-09-08
- **层级**: research/P15（规范层，非 core/runtime）
- **关联**: `model_ir.schema.json`（机器可读校验）、`core/schemas/model_artifact.schema.json`（P13-3C 冻结契约，上游）、`core/schemas/v3/artifact/artifact.schema.json`（V3 统一对象契约）
- **定位**: MathModel 核心价值 = Model Construction + Model Representation。本规范定义 Model Representation 的标准化表达接口，使"现实问题→数学模型→计算→验证→结论"这一过程本身变成可观察、可结构化、可验证、可比较的对象。

---

## 0. 设计原则

| 原则 | 说明 |
|---|---|
| **表达接口标准化，答案不标准化** | IR 只规定 variable/parameter/objective/constraint/mechanism/equation/solver/validation/claim 的表达接口，不规定只能用某个模型或某个答案 |
| **复用而非另起炉灶** | Artifact Registry 存储、Evidence Graph 证据、Decision Log 决策全部复用；Model IR 是 payload 的结构化 schema，Model Graph 是建模结构的投影 |
| **LLM-free 校验** | 所有 deterministic checks 由脚本执行，不依赖 LLM 判断；semantic 判断（机理正确性等）留给 Rubric/Evaluator |
| **可追溯** | 每个节点有生成时间戳、agent 身份、输入哈希、版本历史；claim 可反查到 problem |
| **多家族中立** | ODE/PDE/优化/统计/几何/运动学等都允许，通过 `model_family` 字段区分 |
| **research 层规范** | 本规范属 research 层，不改 core/runtime；若发现必须改 core 才能表达，先 STOP 报回 |

---

## 1. Model IR 数据模型

### 1.1 顶层结构

```
ModelIR
├── ir_version          # "1.0"
├── model_id            # 模型实例唯一标识
├── model_family        # 模型家族（multibody_dynamics / optimization / ...）
├── problem_binding     # 问题绑定
├── assumptions[]       # 假设
├── variables[]         # 变量
├── parameters[]        # 参数
├── objectives[]        # 目标
├── constraints[]       # 约束
├── mechanisms[]        # 机理
├── equations[]         # 方程
├── dependencies[]      # 依赖关系（内部引用图）
├── solvers[]           # 求解器
├── experiments[]       # 实验
├── validations[]       # 验证
├── claims[]            # 主张
├── model_graph         # Model Graph（节点+边）
└── modeling_trace      # 建模过程时序与版本
```

### 1.2 Problem Binding（问题绑定）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `problem_id` | string | 是 | 如 "2024_A" |
| `sub_question_id` | string | 是 | 如 "Q1"；科研问题用 `research_question_id` 替代 |
| `problem_sha256` | string | 是 | 题面文本 SHA-256，用于冻结输入绑定 |
| `problem_card_ref` | string | 否 | Problem Card 路径引用 |
| `competition_format` | string | 否 | CUMCM 特有：论文页数/提交规则 |

**与子问题绑定关系**: 所有字段组（variables/parameters/objectives/constraints/mechanisms/equations）均携带 `sub_question_binding` 字段，标明该元素属于哪个子问题。跨子问题共享的元素标记为 `["Q1", "Q2"]` 或 `"global"`。

### 1.3 Assumptions（假设）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `assumption_id` | string | 是 | 如 "A001" |
| `text` | string | 是 | 假设文本 |
| `source` | enum | 是 | `problem_explicit`（题面引用）/ `reasonable_simplification`（合理简化）/ `domain_knowledge`（领域知识）/ `derived`（推导） |
| `confidence` | float | 是 | 0.0-1.0，假设可信度 |
| `anchors_to_problem` | array | 否 | 题面位置引用，如 `[{"line": 8, "quote": "龙头的板长为341cm"}]`；source=reasonable_simplification 时可为空但需说明 |
| `sub_question_binding` | array | 是 | 适用子问题列表 |
| `type` | enum | 否 | `projection`（投影假设）/ `calibration_anchor`（校准锚）/ `mechanism_assumption`（机制假设）/ `simplification`（简化假设） |

### 1.4 Variables（变量）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `variable_id` | string | 是 | 如 "V001" |
| `name` | string | 是 | 变量名，如 "x_i" |
| `symbol` | string | 是 | LaTeX 符号，如 "x_i(t)" |
| `definition` | string | 是 | 中文定义 |
| `unit` | string | 是 | 单位，如 "m"、"m/s"、"rad" |
| `dimension` | string | 否 | 量纲，如 "L"、"L/T"、"1" |
| `type` | enum | 是 | `continuous` / `discrete` / `derived` / `constant` / `state` / `decision` / `input` / `index` |
| `value_range` | object | 否 | `{"min": ..., "max": ...}` 或描述 |
| `sub_question_binding` | array | 是 | 适用子问题 |
| `index_domain` | object | 否 | 索引变量的定义域，如 `{"i": "1..N", "t": "0..300s"}` |

### 1.5 Parameters（参数）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `parameter_id` | string | 是 | 如 "P001" |
| `name` | string | 是 | 参数名 |
| `symbol` | string | 是 | LaTeX 符号 |
| `definition` | string | 是 | 定义 |
| `unit` | string | 是 | 单位 |
| `value` | number/string | 是 | 取值（数值或表达式） |
| `source` | enum | 是 | `problem_given`（题面给定）/ `experimental`（实验测定）/ `assumed`（假设值）/ `fitted`（拟合值）/ `derived`（推导值） |
| `sub_question_binding` | array | 是 | 适用子问题 |

### 1.6 Objectives（目标）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `objective_id` | string | 是 | 如 "O001" |
| `type` | enum | 是 | `minimize` / `maximize` / `find` / `satisfy` / `simulate` / `estimand` |
| `expression` | string | 是 | LaTeX 目标表达式 |
| `variables_refs` | array | 是 | 引用的 variable_id 列表 |
| `sub_question_binding` | array | 是 | 适用子问题 |
| `clarity_score` | object | 是 | `{"direction_explicit": bool, "expression_explicit": bool, "score": 0/1/2}` — deterministic: 方向+表达式是否明确 |
| `description` | string | 否 | 自然语言描述 |

### 1.7 Constraints（约束）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `constraint_id` | string | 是 | 如 "C001" |
| `type` | enum | 是 | `equality` / `inequality` / `boundary` / `initial` / `logical` |
| `expression` | string | 是 | LaTeX 约束表达式 |
| `variables_refs` | array | 是 | 引用的 variable_id 列表 |
| `parameters_refs` | array | 否 | 引用的 parameter_id 列表 |
| `source` | enum | 是 | `problem`（题面）/ `physical_law`（物理定律）/ `assumption_derived`（假设推导）/ `geometric`（几何约束） |
| `sub_question_binding` | array | 是 | 适用子问题 |
| `description` | string | 否 | 描述 |

### 1.8 Mechanisms（机理）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `mechanism_id` | string | 是 | 如 "MECH001" |
| `name` | string | 是 | 机理名称 |
| `description` | string | 是 | 机理描述 |
| `type` | enum | 是 | `physical` / `geometric` / `statistical` / `optimization` / `dynamical` / `other` |
| `governing_principle` | string | 是 | 控制原理，如 "刚体运动学"、"阿基米德螺线参数化" |
| `variables_refs` | array | 是 | 引用的 variable_id 列表（至少1个） |
| `assumptions_refs` | array | 否 | 依赖的 assumption_id 列表 |
| `sub_question_binding` | array | 是 | 适用子问题 |

### 1.9 Equations（方程）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `equation_id` | string | 是 | 如 "E001" |
| `latex` | string | 是 | LaTeX 方程 |
| `type` | enum | 是 | `constitutive`（本构）/ `balance`（守恒/平衡）/ `definition`（定义）/ `derived`（推导）/ `boundary`（边界）/ `initial`（初始） |
| `variables_refs` | array | 是 | 引用的 variable_id 列表 |
| `parameters_refs` | array | 否 | 引用的 parameter_id 列表 |
| `mechanism_ref` | string | 否 | 所属 mechanism_id |
| `derivation_trace` | object | 是 | `{"from_assumptions": [...], "from_mechanisms": [...], "from_equations": [...], "steps": [...]}` — 从哪个假设/机制/方程推导而来 |
| `sub_question_binding` | array | 是 | 适用子问题 |
| `description` | string | 否 | 描述 |

### 1.10 Dependencies（依赖关系）

依赖关系是 Model IR 内部的引用图，用于表达字段间的引用关系。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `dependency_id` | string | 是 | 如 "DEP001" |
| `from_type` | enum | 是 | `variable` / `parameter` / `assumption` / `mechanism` / `equation` / `constraint` / `objective` |
| `from_id` | string | 是 | 源元素 ID |
| `to_type` | enum | 是 | 同上 |
| `to_id` | string | 是 | 目标元素 ID |
| `relation` | enum | 是 | `feeds`（变量输入方程）/ `derives`（假设推导约束）/ `governs`（机理控制方程）/ `defines`（方程定义目标）/ `constrains`（约束限制变量）/ `uses`（方程使用参数） |
| `sub_question_binding` | array | 是 | 适用子问题 |

**典型依赖模式**:
- `variable → equation`（feeds）: 变量是方程的输入
- `assumption → constraint`（derives）: 假设推导出约束
- `mechanism → equation`（governs）: 机理控制方程形式
- `equation → objective`（defines）: 方程定义目标
- `parameter → equation`（uses）: 方程使用参数
- `constraint → variable`（constrains）: 约束限制变量取值

### 1.11 Solvers（求解器）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `solver_id` | string | 是 | 如 "S001" |
| `name` | string | 是 | 求解器名称 |
| `type` | enum | 是 | `analytical` / `numerical` / `optimization` / `simulation` / `other` |
| `method` | string | 是 | 具体方法，如 "四阶 Runge-Kutta"、"scipy.optimize.minimize" |
| `parameters` | object | 否 | 求解器参数，如 `{"dt": 0.01, "rtol": 1e-6}` |
| `convergence_criteria` | object | 否 | 收敛准则，如 `{"residual_threshold": 1e-8, "max_iterations": 10000}` |
| `implementation_ref` | string | 否 | 代码实现引用（artifact_id 或文件路径） |
| `equations_refs` | array | 否 | 求解的 equation_id 列表 |
| `sub_question_binding` | array | 是 | 适用子问题 |

### 1.12 Experiments（实验）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `experiment_id` | string | 是 | 如 "EXP001" |
| `method` | string | 是 | 实验方法，如 "参数扫描"、"正向仿真" |
| `parameters` | object | 否 | 实验参数 |
| `inputs_refs` | array | 否 | 输入引用（variable_id / parameter_id） |
| `outputs` | array | 是 | 输出描述 |
| `results` | object | 否 | 结果摘要（数值快照） |
| `run_metadata` | object | 是 | `{"seed": 42, "repetitions": 5, "latency_seconds": ..., "exit_code": 0}` |
| `solver_ref` | string | 否 | 使用的 solver_id |
| `sub_question_binding` | array | 是 | 适用子问题 |

### 1.13 Validations（验证）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `validation_id` | string | 是 | 如 "VAL001" |
| `type` | enum | 是 | `baseline` / `sensitivity` / `robustness` / `uncertainty` / `counterfactual` / `failure_case` / `convergence` |
| `method` | string | 是 | 验证方法描述 |
| `results` | object | 是 | 验证结果 |
| `pass_fail` | enum | 是 | `pass` / `fail` / `inconclusive` |
| `evidence_refs` | array | 否 | 证据引用（experiment_id / result artifact_id） |
| `targets_refs` | array | 否 | 验证目标（claim_id / equation_id） |
| `sub_question_binding` | array | 是 | 适用子问题 |

### 1.14 Claims（主张）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `claim_id` | string | 是 | 如 "CL001" |
| `text` | string | 是 | 主张文本 |
| `type` | enum | 是 | `result` / `interpretation` / `recommendation` |
| `evidence_refs` | array | 是 | 证据引用（experiment_id / validation_id） |
| `model_refs` | array | 否 | 模型元素引用（equation_id / mechanism_id） |
| `experiment_refs` | array | 否 | 实验引用 |
| `validation_refs` | array | 否 | 验证引用 |
| `sub_question_binding` | array | 是 | 适用子问题 |
| `status` | enum | 否 | `supported` / `refuted` / `unresolved` |

### 1.15 字段间引用关系总览

```
problem_binding
  ├── binds → all field groups (via sub_question_binding)
  └── problem_sha256 → frozen input

assumptions
  ├── anchors_to_problem → problem text positions
  └── derivation_trace (in equations) → assumption_id

variables
  ├── referenced by → objectives.variables_refs
  ├── referenced by → constraints.variables_refs
  ├── referenced by → equations.variables_refs
  ├── referenced by → mechanisms.variables_refs
  └── constrained by → constraints (via dependencies)

parameters
  ├── referenced by → constraints.parameters_refs
  └── referenced by → equations.parameters_refs

mechanisms
  ├── variables_refs → variable_id
  ├── assumptions_refs → assumption_id
  └── mechanism_ref (in equations) → mechanism_id

equations
  ├── variables_refs → variable_id
  ├── parameters_refs → parameter_id
  ├── mechanism_ref → mechanism_id
  └── derivation_trace → assumption_id / mechanism_id / equation_id

dependencies
  └── from_id / to_id → cross-reference all field groups

solvers
  └── equations_refs → equation_id

experiments
  ├── inputs_refs → variable_id / parameter_id
  └── solver_ref → solver_id

validations
  ├── evidence_refs → experiment_id
  └── targets_refs → claim_id / equation_id

claims
  ├── evidence_refs → experiment_id / validation_id
  ├── model_refs → equation_id / mechanism_id
  ├── experiment_refs → experiment_id
  └── validation_refs → validation_id
```

---

## 2. Model Graph 节点/边类型

### 2.1 设计定位

**Model Graph = 建模结构的有向图投影**。它与 Evidence Graph 分工明确：

| 维度 | Model Graph | Evidence Graph |
|---|---|---|
| 表达内容 | 建模过程的结构（变量→方程→模型→验证→主张） | 证据的支撑关系（artifact→artifact 的 relation） |
| 节点粒度 | 建模元素（variable/equation/mechanism 等） | Artifact（P/Q/M/A/E/R/C 等 Registry 级对象） |
| 边语义 | 建模依赖（feeds/derives/constrains/governs 等） | 证据关系（motivates/solved_by/assumes/supports 等） |
| 真源 | Model IR 内的 `model_graph` 字段 | `evidence_graph.json` |
| 用途 | Model Diff、结构分析、claim 反查 | 证据追溯、可信度评估 |

**关联方式**: Model Graph 的每条边可携带 `evidence_ref`，指向 Evidence Graph 中的 relation 或 artifact，实现"建模结构"与"证据结构"的双向绑定。

### 2.2 节点类型

| 节点类型 | 前缀 | 说明 | 对应 IR 字段组 |
|---|---|---|---|
| `problem` | P | 问题根节点 | problem_binding |
| `subquestion` | Q | 子问题 | problem_binding.sub_question_id |
| `assumption` | A | 假设 | assumptions |
| `variable` | V | 变量 | variables |
| `parameter` | PARM | 参数 | parameters |
| `mechanism` | MECH | 机理 | mechanisms |
| `objective` | O | 目标 | objectives |
| `constraint` | C | 约束 | constraints |
| `equation` | E | 方程 | equations |
| `solver` | S | 求解器 | solvers |
| `experiment` | EXP | 实验 | experiments |
| `result` | R | 结果 | experiments.results |
| `validation` | VAL | 验证 | validations |
| `claim` | CL | 主张 | claims |

**根节点**: `problem`
**叶节点**: `claim`
**中间层**: assumption → variable/parameter → mechanism → equation → objective/constraint → solver → experiment → result → validation → claim

### 2.3 有向边类型

每条边必须包含: `source_node` / `target_node` / `edge_type` / `evidence_ref`（可选）/ `confidence`（0.0-1.0，可选）。

| 边类型 | 方向 | 语义 | 典型场景 |
|---|---|---|---|
| `cites_problem` | assumption/variable/parameter → problem | 引用题面 | 假设锚定题面位置 |
| `references_variable` | equation/constraint/objective → variable | 引用变量 | 方程中使用变量 |
| `uses_parameter` | equation/constraint → parameter | 使用参数 | 方程中使用参数 |
| `derives` | assumption → constraint/equation | 假设推导出 | 刚体假设→间距守恒约束 |
| `governed_by` | equation → mechanism | 方程受机理控制 | 运动学方程→刚体运动学机理 |
| `constrains` | constraint → variable/objective | 约束限制 | 间距约束→位置变量 |
| `feeds` | variable → equation/experiment | 变量输入 | 位置变量→运动学方程 |
| `solved_by` | equation/model → solver | 由求解器求解 | ODE→RK4 |
| `produces` | solver/experiment → result | 产生结果 | 仿真→位置序列 |
| `validates` | validation → model/equation/claim | 验证 | 敏感性分析→模型 |
| `evidenced_by` | claim → experiment/validation/result | 主张有证据 | 结论→实验结果 |
| `claims_result` | claim → result | 主张基于结果 | "螺距增大降低碰撞风险"→碰撞检测结果 |
| `supports` | result/validation → claim | 结果支持主张 | 实验数据支持结论 |
| `binds_to` | any → subquestion | 绑定子问题 | 变量属于Q1 |

### 2.4 图的结构约束

1. **连通性**: 从 problem 根节点出发，所有 claim 叶节点必须可达
2. **无环**: 建模依赖图应为 DAG（不允许循环依赖，除非显式标记为 feedback loop）
3. **Claim 反查**: 每个 claim 必须存在到 problem 的路径（claim → evidence → experiment/validation → model → equation → variable/assumption → subquestion → problem）
4. **机制-变量绑定**: 每个 mechanism 节点必须有至少一条 `references_variable` 出边

---

## 3. 与现有设施的映射

### 3.1 映射总表

| Model IR 概念 | 现有设施 | 映射方式 | 新增/复用 |
|---|---|---|---|
| Model IR 整体 | Artifact Registry (`registry.json`) | 作为 `type=model` artifact 的 payload 存储；一个 Model IR 实例 = 一个 model artifact | 复用存储，新增 payload schema |
| assumptions[] | Registry `type=assumption` artifact | 每条 assumption 可独立注册为 assumption artifact；也可内联在 model artifact payload 中 | 复用 artifact 类型，新增字段 |
| variables/parameters/objectives/constraints/mechanisms/equations | Registry `type=model` artifact payload | 组合为 `model_construction` artifact 的 payload | 复用 artifact，新增结构化字段 |
| Model Graph 节点 | Registry artifact_id | 节点 ID 与 artifact_id 对齐（如 V001 可注册为独立 artifact 或内联） | 复用 ID 体系 |
| Model Graph 边 | Evidence Graph (`evidence_graph.json`) | Model Graph 边的 `evidence_ref` 指向 Evidence Graph 的 relation；建模结构边存储在 IR 内，证据边存储在 Evidence Graph | 复用 Evidence Graph，新增边类型 |
| 建模决策（方法选型/假设选择） | Decision Log (`decision_log.json`) | 每个 method_family 选择、关键假设选择记录为 decision | 完全复用 |
| 外部 Agent 提交 | `external_artifact_manifest.py` | payload 字段对齐 Model IR schema；manifest 提供 provenance，payload 提供模型结构 | 复用 manifest，新增 payload schema |
| deterministic checks | `validate.py` / `gate.py` | 作为新增 check 模块，可被 validate.py 调用 | 复用校验框架，新增 check 实现 |
| Model Diff | 无现有设施 | 新增 research 层工具 | 全新 |
| Modeling Trace | Registry `lifecycle_history` + `provenance` | 扩展 provenance 字段，新增节点级 trace | 复用 lifecycle，新增 trace 结构 |

### 3.2 Artifact Registry 存储方案

**推荐方案: 单 artifact 内联 + 关键元素可独立注册**

```
registry.json
├── M001 (type=model)
│   └── payload = ModelIR (完整 IR，含所有字段组)
│       ├── problem_binding
│       ├── assumptions[]
│       ├── variables[]
│       ├── ...
│       └── model_graph
├── A001 (type=assumption, 可选独立注册)
│   └── payload = {assumption_id, text, source, ...}
└── E001 (type=experiment)
    └── payload = {experiment_id, method, results, ...}
```

**字段组合为 artifact 的规则**:
- `model_construction` artifact: objective + constraints + variables + parameters + mechanisms + equations + dependencies（核心建模结构）
- `assumption` artifact（可选）: 单条假设，当假设需要独立验证/追溯时注册
- `experiment` artifact: solver + experiment + results
- `validation` artifact: validation + evidence
- `claim` artifact: claim + evidence_refs

### 3.3 Evidence Graph 关联方案

Model Graph 与 Evidence Graph 是**两个互补的图**，通过 `evidence_ref` 关联：

```
Model Graph (建模结构)                 Evidence Graph (证据结构)
─────────────────────────             ─────────────────────────
problem ──cites_problem──> A001       P001 ──motivates──> Q001
  │                                     │
  ├──binds_to──> Q1                     Q001 ──solved_by──> M001
  │                                     │
variable V001 ──feeds──> E001          M001 ──assumes──> A001
  │                                     │
equation E001 ──governed_by──> MECH001 M001 ──validated_by──> E001
  │                                     │
  └── evidence_ref: "relation#3"        E001 ──produces──> R001
                                        │
                                        R001 ──supports──> C001
```

**关联规则**:
- Model Graph 边的 `evidence_ref` 可指向 Evidence Graph 中的具体 relation（如 `evidence_graph.json#relations[3]`）
- Model Graph 节点可对应 Registry artifact_id（如 V001 若独立注册，则在 Evidence Graph 中也有对应节点）
- 两者不重复存储：Model Graph 存建模依赖语义，Evidence Graph 存 artifact 级证据关系

### 3.4 Decision Log 关联

建模过程的关键决策记录在 Decision Log：

| 决策类型 | decision.question | decision.chosen | 关联 IR 元素 |
|---|---|---|---|
| 方法家族选择 | "Q1 模型家族选型" | "multibody_dynamics" | model_family, mechanisms[].type |
| 假设决策 | "是否忽略空气阻力" | "忽略（合理简化）" | assumptions[].text |
| 求解器选择 | "Q1 求解器选型" | "RK4 数值积分" | solvers[].method |
| 验证策略 | "Q1 验证设计" | "刚体约束守恒+网格收敛" | validations[].type |

### 3.5 external_artifact_manifest 对齐

外部 Agent 提交的 payload 应符合 Model IR schema。manifest 结构不变，payload 替换为 Model IR：

```python
ExternalArtifactManifest(
    executor_type="external_agent",
    agent_identity="doubao",
    model_version="doubao-1.5-pro",
    input_sha256="9baf81fb...",  # 必须匹配冻结题面哈希
    node_id="model_construction",
    dag_position=4,
    prompt_or_skill_version="v3.1.0",
    artifact_schema_version="model_ir-1.0",  # 新增：标识 payload 遵循 Model IR v1.0
    started_at="...",
    finished_at="...",
    latency_seconds=300.0,
    submitted_at="...",
    payload={...}  # Model IR 完整结构
)
```

**payload schema 校验**: harness 侧用 `model_ir.schema.json` 校验 payload，通过后再注册到 Registry。

### 3.6 新增 vs 复用总结

| 类别 | 内容 |
|---|---|
| **新增** | Model IR 字段定义、Model Graph 节点/边类型、deterministic checks 清单、Model Diff 规范、Modeling Trace 结构、`model_ir.schema.json` |
| **复用** | Artifact Registry 存储机制、Evidence Graph 证据关系、Decision Log 决策记录、external_artifact_manifest 提交契约、V3 artifact 统一契约（identity/provenance/validation/lifecycle）、`validate.py` 校验框架 |
| **不改** | core/runtime（永久 LLM-free）、现有 schema（model_artifact.schema.json 为 P13-3C 冻结契约，不修改）、`.gitignore`/`.git/` |

---

## 4. Modeling Trace

### 4.1 设计目标

记录建模过程的时序与版本，支持 replay：checkout commit → frozen inputs → same agent → reproduce model graph。

### 4.2 Trace 结构

```
modeling_trace
├── trace_version: "1.0"
├── generated_at: ISO 8601
├── agent_identity: "doubao" / "gpt" / "claude" / "human"
├── model_version: "doubao-1.5-pro"
├── input_sha256: "9baf81fb..."          # 冻结题面哈希
├── prompt_version: "v3.1.0"             # prompt/SKILL 版本
├── skill_version: "modeler-v2.0"        # 技能版本
├── commit_hash: "abc1234"               # 仓库 commit（用于 replay）
├── node_events[]                        # 节点生成/修改事件
│   ├── event_id
│   ├── timestamp
│   ├── event_type: "created" / "modified" / "deleted"
│   ├── node_type: "variable" / "assumption" / "equation" / ...
│   ├── node_id
│   ├── before_state (可选, modified 时)
│   ├── after_state
│   └── parent_event_id (可选, 因果链)
├── generation_order[]                   # 节点生成顺序
│   ├── node_id
│   ├── order_index
│   └── timestamp
└── version_history[]                    # 版本历史
    ├── version_number
    ├── commit_hash
    ├── changed_nodes[]
    ├── change_summary
    └── timestamp
```

### 4.3 节点级 Trace

每个 IR 元素（variable/assumption/equation/etc.）可携带 `_trace` 字段：

```json
{
  "variable_id": "V001",
  "name": "x_i",
  "_trace": {
    "created_at": "2026-09-08T10:00:00Z",
    "created_by": "doubao-1.5-pro",
    "input_sha256": "9baf81fb...",
    "prompt_version": "v3.1.0",
    "version": 1,
    "modified_at": null,
    "modification_history": []
  }
}
```

### 4.4 Replay 协议

```
1. checkout commit_hash
2. 验证 input_sha256 匹配冻结题面
3. 使用相同 agent_identity + model_version
4. 使用相同 prompt_version + skill_version
5. 按 generation_order 重新生成节点
6. 对比生成的 Model Graph 与原始 Model Graph
7. 输出 replay_match 率（节点匹配率 + 边匹配率）
```

**Replay 判定**: 节点 ID + 核心字段（variable.name/symbol/definition, equation.latex/type）匹配即视为 replay 成功。允许非核心字段（如 description 措辞）有差异。

---

## 5. 可验证性 / 确定性检查（Deterministic Checks）

### 5.1 设计原则

- **与 semantic 判断分离**: deterministic checks 只做结构/引用/格式检查，不判断机理是否正确（semantic 判断由 Rubric L2.6 等负责）
- **每个 check 输出 PASS / FAIL / SKIP + 具体位置**
- **LLM-free**: 全部由脚本执行

### 5.2 检查清单

| # | Check ID | 检查内容 | 输出 | 失败定位 |
|---|---|---|---|---|
| 1 | `DC-001` | **变量引用一致性**: constraint/objective/equation 中引用的 variable_id 是否都在 variables 列表中定义 | PASS/FAIL | 列出未定义的 variable_id 及其出现位置 |
| 2 | `DC-002` | **参数引用一致性**: equation/constraint 中引用的 parameter_id 是否都在 parameters 列表中定义 | PASS/FAIL | 列出未定义的 parameter_id |
| 3 | `DC-003` | **单位/量纲一致性**: equation 两边的量纲是否一致（基于 variable.dimension + parameter.unit） | PASS/FAIL/SKIP | 列出量纲不一致的 equation_id（SKIP: 无量纲信息时） |
| 4 | `DC-004` | **索引一致性**: equation 中使用的索引（i,j,k）是否有定义和范围（variable.index_domain） | PASS/FAIL/SKIP | 列出未定义索引的 equation_id |
| 5 | `DC-005` | **目标明确性**: objective 是否有明确方向（minimize/maximize）和非空表达式 | PASS/FAIL | 列出不明确的 objective_id |
| 6 | `DC-006` | **约束完整性**: 每个 variable 是否至少被一个 constraint 或 objective 引用 | PASS/FAIL/WARN | 列出未被引用的 variable_id（WARN: 可能是中间变量） |
| 7 | `DC-007` | **假设锚定**: 每个 assumption 是否 anchors_to_problem 非空，或 source=reasonable_simplification/domain_knowledge 且有说明 | PASS/FAIL | 列出未锚定且未标记的 assumption_id |
| 8 | `DC-008` | **方程推导链**: 每个 equation 是否有 derivation_trace（from_assumptions 或 from_mechanisms 或 from_equations 非空） | PASS/FAIL | 列出无推导链的 equation_id |
| 9 | `DC-009` | **Claim 反查**: 每个 claim 能否通过 evidence_refs 反查到 problem（claim→experiment/validation→model→equation→variable→subquestion→problem） | PASS/FAIL | 列出反查路径中断的 claim_id |
| 10 | `DC-010` | **机制-变量绑定**: 每个 mechanism 是否引用了至少一个 variable（variables_refs 非空） | PASS/FAIL | 列出无变量绑定的 mechanism_id |
| 11 | `DC-011` | **子问题绑定一致性**: 所有元素的 sub_question_binding 是否在 problem_binding 的子问题列表中 | PASS/FAIL | 列出绑定了不存在子问题的元素 |
| 12 | `DC-012` | **Solver-方程绑定**: 每个 solver 的 equations_refs 是否都在 equations 列表中 | PASS/FAIL | 列出引用不存在方程的 solver_id |
| 13 | `DC-013` | **Experiment-Solver 绑定**: 每个 experiment 的 solver_ref 是否在 solvers 列表中 | PASS/FAIL/SKIP | 列出引用不存在求解器的 experiment_id |
| 14 | `DC-014` | **Validation-Evidence 绑定**: 每个 validation 的 evidence_refs 是否都在 experiments/results 中 | PASS/FAIL | 列出引用不存在证据的 validation_id |
| 15 | `DC-015` | **Model Graph 连通性**: 从 problem 根节点到所有 claim 叶节点是否可达 | PASS/FAIL | 列出不可达的 claim_id |

### 5.3 输出格式

```json
{
  "check_id": "DC-001",
  "name": "variable_reference_consistency",
  "status": "FAIL",
  "failures": [
    {
      "element_id": "E003",
      "element_type": "equation",
      "missing_refs": ["V099"],
      "message": "equation E003 references variable V099 which is not defined"
    }
  ],
  "checked_at": "2026-09-08T10:05:00Z"
}
```

### 5.4 与 Rubric 的映射

| Deterministic Check | Rubric 维度 | 关系 |
|---|---|---|
| DC-001 变量引用一致性 | L2.1 变量声明完备性 | DC 是 L2.1 的必要非充分条件 |
| DC-002 参数引用一致性 | L2.2 参数声明完备性 | 同上 |
| DC-005 目标明确性 | L2.4 目标正确性 | DC 检查形式明确，Rubric 检查语义正确 |
| DC-006 约束完整性 | L2.5 约束完备性 | DC 检查引用覆盖，Rubric 检查约束正确性 |
| DC-008 方程推导链 | L2.7 方程结构完整性 | DC 检查推导链存在，Rubric 检查方程可求解 |
| DC-009 Claim 反查 | L4.5 证据-主张对应 | DC 检查路径存在，Rubric 检查证据充分性 |

---

## 6. Model Diff 规范

### 6.1 用途

两个外部 Agent 解同一题，可在各维度结构化对比"模型到底哪里不同"，而不是只比最终论文分。

### 6.2 对齐策略

1. **按 sub_question 对齐**: 先按 `sub_question_binding` 分组
2. **按 variable name/symbol 对齐**: 变量按 `name` 或 `symbol` 匹配
3. **按 constraint/equation 语义对齐**: 约束和方程按 `expression`/`latex` 的规范化形式匹配（去除空白、统一符号）
4. **按 ID 对齐（可选）**: 如果两个模型来自同一项目，可直接按 ID 对齐

### 6.3 差异维度

| 维度 | 增（A有B无） | 删（B有A无） | 改（定义不同） |
|---|---|---|---|
| **Variables** | variable_id 列表 | variable_id 列表 | 字段级 diff: definition/unit/type/value_range |
| **Assumptions** | assumption_id 列表 | assumption_id 列表 | 字段级 diff: text/source/confidence |
| **Parameters** | parameter_id 列表 | parameter_id 列表 | 字段级 diff: value/source/unit |
| **Mechanisms** | mechanism_id 列表 | mechanism_id 列表 | 字段级 diff: type/governing_principle |
| **Objectives** | objective_id 列表 | objective_id 列表 | 字段级 diff: type(方向)/expression/variables_refs |
| **Constraints** | constraint_id 列表 | constraint_id 列表 | 字段级 diff: type/expression |
| **Equations** | equation_id 列表 | equation_id 列表 | 字段级 diff: latex/type/derivation_trace |
| **Solvers** | solver_id 列表 | solver_id 列表 | 字段级 diff: method/parameters |
| **Validations** | validation_id 列表 | validation_id 列表 | 字段级 diff: type/results/pass_fail |

### 6.4 结构差异

- **拓扑差异**: 图的边集合差异（增边/删边）
- **依赖深度**: 从 problem 到 claim 的最长路径长度差异
- **反馈环**: A 有 feedback loop 而 B 没有（或反之）
- **连通分量**: 图的连通性差异

### 6.5 相似度评分

```
整体相似度 = weighted_sum(各维度相似度)

各维度相似度:
  - variables:    1 - (增+删+改) / max(|A.vars|, |B.vars|)
  - assumptions:  同上
  - equations:    同上 (latex 规范化后比较)
  - constraints:  同上
  - structure:    1 - (边增+边删) / max(|A.edges|, |B.edges|)

权重默认: variables=0.15, assumptions=0.10, mechanisms=0.15,
          objectives=0.10, constraints=0.15, equations=0.20,
          solvers=0.05, validations=0.05, structure=0.05
```

### 6.6 输出格式

```json
{
  "diff_version": "1.0",
  "model_a": "model_id_A",
  "model_b": "model_id_B",
  "problem_id": "2024_A",
  "sub_question": "Q1",
  "overall_similarity": 0.72,
  "dimensions": {
    "variables": {"added": [...], "removed": [...], "modified": [...], "similarity": 0.80},
    "equations": {"added": [...], "removed": [...], "modified": [...], "similarity": 0.65},
    "structure": {"edges_added": [...], "edges_removed": [...], "depth_diff": 1, "similarity": 0.70}
  },
  "key_differences": [
    "模型A使用多体刚体链递推，模型B使用纯几何螺旋拟合",
    "模型A有碰撞检测约束C004，模型B缺失",
    "模型A的方程E002推导链包含假设A003，模型B无推导链"
  ]
}
```

---

## 7. 多解 / 多家族兼容

### 7.1 设计原则

**IR 只规定表达接口，不规定答案。** 同一题可以有多个 Model IR 实例（不同家族），通过 `model_family` 字段区分。

### 7.2 model_family 字段

```json
"model_family": {
  "primary": "multibody_dynamics",
  "secondary": ["differential_geometry", "numerical_optimization"],
  "description": "多体刚体链递推 + 阿基米德螺线参数化"
}
```

### 7.3 允许的模型家族（非穷举）

| 家族 | 说明 | 典型 IR 特征 |
|---|---|---|
| `ode` | 常微分方程 | equations.type=balance/constitutive, solver.type=numerical(RK4) |
| `state_space` | 状态空间模型 | variables.type=state, equations 为矩阵形式 |
| `discrete_recurrence` | 离散递推 | variables.type=discrete, equations 为 x_{n+1}=f(x_n) |
| `pde` | 偏微分方程 | variables 有空间索引, equations 含偏导 |
| `optimization` | 优化 | objectives.type=minimize/maximize, constraints 丰富 |
| `statistical` | 统计模型 | parameters.source=fitted, validations.type=uncertainty |
| `geometric` | 几何建模 | mechanisms.type=geometric, equations 为几何关系 |
| `kinematic` | 运动学 | mechanisms.type=physical(kinematics), variables 含位置/速度 |
| `other` | 其他 | 自由表达 |

### 7.4 与 Problem Card 的对齐

Problem Card 中的 `allowed_model_families` 和 `acceptable_solution_variants` 与 Model IR 的对齐方式：

```
Problem Card.allowed_model_families
  ↓ 约束
Model IR.model_family.primary ∈ allowed_model_families
  ↓ 或
Model IR.model_family.primary ∉ allowed_model_families → 标记为 "unconventional"，需额外验证

Problem Card.acceptable_solution_variants
  ↓ 匹配
Model IR 的 mechanisms + equations 组合匹配某个 variant 的 conditions
  ↓ 判定
match / partial_match / no_match
```

### 7.5 多实例共存

同一项目中可存在多个 Model IR 实例：

```
projects/<项目>/
└── state/
    ├── registry.json
    │   ├── M001 (model_family=multibody_dynamics)
    │   └── M002 (model_family=pure_geometric_spiral)
    └── model_instances/
        ├── M001_model_ir.json
        └── M002_model_ir.json
```

Model Diff 可直接比较 M001 和 M002。

---

## 8. 2024_A "板凳龙" 完整实例（Appendix A）

> 本实例基于真实题面（`problem_statement.txt`）和合理建模，覆盖 Q1 运动学建模，Q2-Q5 简化表示。

### A.1 实例概览

| 统计项 | 数量 |
|---|---|
| assumptions | 5 |
| variables | 12 |
| parameters | 10 |
| objectives | 2（Q1 仿真 + Q2 碰撞检测） |
| constraints | 6 |
| mechanisms | 2 |
| equations | 5 |
| dependencies | 10 |
| solvers | 1 |
| experiments | 1 |
| validations | 2 |
| claims | 3 |

### A.2 完整 YAML 实例

```yaml
ir_version: "1.0"
model_id: "M-2024A-Q1-rigid-chain"
model_family:
  primary: "multibody_dynamics"
  secondary: ["differential_geometry", "kinematic"]
  description: "多体刚体链递推 + 阿基米德螺线参数化"

problem_binding:
  problem_id: "2024_A"
  sub_question_id: "Q1"
  problem_sha256: "9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e"
  problem_card_ref: "research/P15/benchmark/problem_cards/2024_A/card.yaml"
  competition_format: "cumcm"

assumptions:
  - assumption_id: "A001"
    text: "每节板凳视为刚体，不发生弯曲变形"
    source: "reasonable_simplification"
    confidence: 0.95
    anchors_to_problem: []
    sub_question_binding: ["Q1", "Q2", "Q3", "Q4", "Q5"]
    type: "mechanism_assumption"
  - assumption_id: "A002"
    text: "把手与板固连，把手中心位于孔中心，相邻板凳通过把手铰接"
    source: "problem_explicit"
    confidence: 0.99
    anchors_to_problem:
      - line: 8
        quote: "每节板凳上均有两个孔...相邻两条板凳通过把手连接"
    sub_question_binding: ["Q1", "Q2", "Q3", "Q4", "Q5"]
    type: "projection"
  - assumption_id: "A003"
    text: "忽略空气阻力和板凳质量，仅考虑运动学（不涉及动力学受力分析）"
    source: "reasonable_simplification"
    confidence: 0.90
    anchors_to_problem: []
    sub_question_binding: ["Q1", "Q2"]
    type: "simplification"
  - assumption_id: "A004"
    text: "各把手中心均位于等距螺线上（题面明确要求）"
    source: "problem_explicit"
    confidence: 0.99
    anchors_to_problem:
      - line: 16
        quote: "各把手中心均位于螺线上"
    sub_question_binding: ["Q1", "Q2"]
    type: "projection"
  - assumption_id: "A005"
    text: "龙头前把手沿螺线匀速运动，速度大小恒为1m/s"
    source: "problem_explicit"
    confidence: 0.99
    anchors_to_problem:
      - line: 16
        quote: "龙头前把手的行进速度始终保持1 m/s"
    sub_question_binding: ["Q1", "Q2", "Q4"]
    type: "projection"

variables:
  - variable_id: "V001"
    name: "x_i"
    symbol: "x_i(t)"
    definition: "第i个把手中心的x坐标（i=1..224，1为龙头前把手，224为龙尾后把手）"
    unit: "m"
    dimension: "L"
    type: "state"
    value_range: {"min": -15.0, "max": 15.0}
    sub_question_binding: ["Q1", "Q2", "Q4"]
    index_domain: {"i": "1..224", "t": "0..300s"}
  - variable_id: "V002"
    name: "y_i"
    symbol: "y_i(t)"
    definition: "第i个把手中心的y坐标"
    unit: "m"
    dimension: "L"
    type: "state"
    value_range: {"min": -15.0, "max": 15.0}
    sub_question_binding: ["Q1", "Q2", "Q4"]
    index_domain: {"i": "1..224", "t": "0..300s"}
  - variable_id: "V003"
    name: "v_i"
    symbol: "v_i(t)"
    definition: "第i个把手的速率"
    unit: "m/s"
    dimension: "L/T"
    type: "derived"
    value_range: {"min": 0.0, "max": 5.0}
    sub_question_binding: ["Q1", "Q2", "Q4", "Q5"]
    index_domain: {"i": "1..224", "t": "0..300s"}
  - variable_id: "V004"
    name: "theta"
    symbol: "\\theta(t)"
    definition: "龙头前把手在螺线上的极角（从初始位置A点起算，顺时针为正）"
    unit: "rad"
    dimension: "1"
    type: "state"
    value_range: {"min": 0.0, "max": 200.0}
    sub_question_binding: ["Q1", "Q2"]
  - variable_id: "V005"
    name: "R_spiral"
    symbol: "R(\\theta)"
    definition: "螺线半径作为极角的函数"
    unit: "m"
    dimension: "L"
    type: "derived"
    value_range: {"min": 0.0, "max": 15.0}
    sub_question_binding: ["Q1", "Q2", "Q3"]
  - variable_id: "V006"
    name: "phi_i"
    symbol: "\\phi_i(t)"
    definition: "第i节板凳的方位角（板的方向角）"
    unit: "rad"
    dimension: "1"
    type: "derived"
    value_range: {"min": -3.14159, "max": 3.14159}
    sub_question_binding: ["Q1", "Q2"]
    index_domain: {"i": "1..223"}
  - variable_id: "V007"
    name: "s_i"
    symbol: "s_i(t)"
    definition: "第i个把手沿螺线的弧长坐标（从龙头前把手起算）"
    unit: "m"
    dimension: "L"
    type: "derived"
    value_range: {"min": 0.0, "max": 400.0}
    sub_question_binding: ["Q1", "Q2"]
    index_domain: {"i": "1..224"}
  - variable_id: "V008"
    name: "d_ij"
    symbol: "d_{ij}(t)"
    definition: "第i个与第j个把手之间的距离（用于碰撞检测）"
    unit: "m"
    dimension: "L"
    type: "derived"
    value_range: {"min": 0.0, "max": 30.0}
    sub_question_binding: ["Q2"]
    index_domain: {"i": "1..224", "j": "1..224", "|i-j|>1"}
  - variable_id: "V009"
    name: "p_opt"
    symbol: "p_{opt}"
    definition: "Q3优化的最小螺距"
    unit: "m"
    dimension: "L"
    type: "decision"
    value_range: {"min": 0.1, "max": 2.0}
    sub_question_binding: ["Q3"]
  - variable_id: "V010"
    name: "v_head_max"
    symbol: "v_{head,max}"
    definition: "Q5优化的龙头最大行进速度"
    unit: "m/s"
    dimension: "L/T"
    type: "decision"
    value_range: {"min": 0.5, "max": 3.0}
    sub_question_binding: ["Q5"]
  - variable_id: "V011"
    name: "omega"
    symbol: "\\omega(t)"
    definition: "龙头前把手的角速度"
    unit: "rad/s"
    dimension: "1/T"
    type: "derived"
    value_range: {"min": 0.0, "max": 2.0}
    sub_question_binding: ["Q1", "Q2"]
  - variable_id: "V012"
    name: "t_collision"
    symbol: "t_{collision}"
    definition: "Q2首次碰撞时刻"
    unit: "s"
    dimension: "T"
    type: "derived"
    value_range: {"min": 0.0, "max": 600.0}
    sub_question_binding: ["Q2"]

parameters:
  - parameter_id: "PARM001"
    name: "N"
    symbol: "N"
    definition: "板凳龙总节数"
    unit: "节"
    value: 223
    source: "problem_given"
    sub_question_binding: ["Q1", "Q2", "Q3", "Q4", "Q5"]
  - parameter_id: "PARM002"
    name: "L_head"
    symbol: "L_{head}"
    definition: "龙头板长"
    unit: "m"
    value: 3.41
    source: "problem_given"
    sub_question_binding: ["Q1", "Q2", "Q4"]
  - parameter_id: "PARM003"
    name: "L_body"
    symbol: "L_{body}"
    definition: "龙身和龙尾板长"
    unit: "m"
    value: 2.20
    source: "problem_given"
    sub_question_binding: ["Q1", "Q2", "Q4"]
  - parameter_id: "PARM004"
    name: "d_offset"
    symbol: "d_{offset}"
    definition: "孔中心距最近板头的距离"
    unit: "m"
    value: 0.275
    source: "problem_given"
    sub_question_binding: ["Q1", "Q2", "Q4"]
  - parameter_id: "PARM005"
    name: "W"
    symbol: "W"
    definition: "板凳板宽"
    unit: "m"
    value: 0.30
    source: "problem_given"
    sub_question_binding: ["Q2"]
  - parameter_id: "PARM006"
    name: "p_in"
    symbol: "p_{in}"
    definition: "盘入螺距（Q1/Q2）"
    unit: "m"
    value: 0.55
    source: "problem_given"
    sub_question_binding: ["Q1", "Q2"]
  - parameter_id: "PARM007"
    name: "v0"
    symbol: "v_0"
    definition: "龙头前把手行进速度"
    unit: "m/s"
    value: 1.0
    source: "problem_given"
    sub_question_binding: ["Q1", "Q2", "Q4"]
  - parameter_id: "PARM008"
    name: "R_A"
    symbol: "R_A"
    definition: "初始时刻龙头前把手（第16圈A点）的螺线半径"
    unit: "m"
    value: 8.8
    source: "derived"
    sub_question_binding: ["Q1", "Q2"]
  - parameter_id: "PARM009"
    name: "b_spiral"
    symbol: "b"
    definition: "阿基米德螺线参数（b = p/(2π)）"
    unit: "m/rad"
    value: 0.08754
    source: "derived"
    sub_question_binding: ["Q1", "Q2", "Q3"]
  - parameter_id: "PARM010"
    name: "R_turn"
    symbol: "R_{turn}"
    definition: "调头空间半径（直径9m）"
    unit: "m"
    value: 4.5
    source: "problem_given"
    sub_question_binding: ["Q3", "Q4"]

objectives:
  - objective_id: "O001"
    type: "simulate"
    expression: "\\text{求解 } \\{x_i(t), y_i(t), v_i(t)\\}_{i=1}^{224}, t \\in [0, 300]\\text{s}"
    variables_refs: ["V001", "V002", "V003"]
    sub_question_binding: ["Q1"]
    clarity_score:
      direction_explicit: true
      expression_explicit: true
      score: 2
    description: "Q1: 正向仿真223节板凳龙0-300s每秒各把手位置和速度"
  - objective_id: "O002"
    type: "find"
    expression: "t_{collision} = \\min\\{t : \\exists_{i<j, |i-j|>1} d_{ij}(t) < W\\}"
    variables_refs: ["V008", "V012"]
    sub_question_binding: ["Q2"]
    clarity_score:
      direction_explicit: true
      expression_explicit: true
      score: 2
    description: "Q2: 确定首次碰撞时刻"

constraints:
  - constraint_id: "C001"
    type: "equality"
    expression: "R(\\theta) = R_A - b\\cdot\\theta \\quad (\\text{顺时针盘入，半径递减})"
    variables_refs: ["V004", "V005"]
    parameters_refs: ["PARM008", "PARM009"]
    source: "geometric"
    sub_question_binding: ["Q1", "Q2"]
    description: "阿基米德等距螺线方程（龙头轨迹约束）"
  - constraint_id: "C002"
    type: "equality"
    expression: "\\sqrt{(x_i - x_{i-1})^2 + (y_i - y_{i-1})^2} = \\ell_i, \\quad \\ell_1 = L_{head} - 2d_{offset}, \\ell_{i>1} = L_{body} - 2d_{offset}"
    variables_refs: ["V001", "V002"]
    parameters_refs: ["PARM002", "PARM003", "PARM004"]
    source: "physical_law"
    sub_question_binding: ["Q1", "Q2", "Q4"]
    description: "相邻把手间距守恒（刚体约束，板内孔间距）"
  - constraint_id: "C003"
    type: "equality"
    expression: "\\|\\dot{\\mathbf{r}}_1(t)\\| = v_0 = 1.0 \\text{ m/s}"
    variables_refs: ["V003"]
    parameters_refs: ["PARM007"]
    source: "problem"
    sub_question_binding: ["Q1", "Q2", "Q4"]
    description: "龙头前把手匀速约束"
  - constraint_id: "C004"
    type: "inequality"
    expression: "d_{ij}(t) \\geq W, \\quad \\forall_{i<j, |i-j|>1}"
    variables_refs: ["V008"]
    parameters_refs: ["PARM005"]
    source: "physical_law"
    sub_question_binding: ["Q2"]
    description: "非相邻节不碰撞约束（板宽为安全距离下界）"
  - constraint_id: "C005"
    type: "initial"
    expression: "\\theta(0) = 0, \\quad R(0) = R_A = 8.8 \\text{ m}"
    variables_refs: ["V004", "V005"]
    parameters_refs: ["PARM008"]
    source: "problem"
    sub_question_binding: ["Q1"]
    description: "初始条件：龙头位于第16圈A点"
  - constraint_id: "C006"
    type: "boundary"
    expression: "R(\\theta_{final}) \\geq R_{turn} = 4.5 \\text{ m} \\quad (Q3)"
    variables_refs: ["V005"]
    parameters_refs: ["PARM010"]
    source: "problem"
    sub_question_binding: ["Q3"]
    description: "调头空间边界约束"

mechanisms:
  - mechanism_id: "MECH001"
    name: "阿基米德螺线参数化"
    description: "龙头前把手沿等距螺线运动，螺线半径随极角线性变化"
    type: "geometric"
    governing_principle: "等距螺线（阿基米德螺线）：R(θ) = R0 + b·θ，相邻圈径向距离=p"
    variables_refs: ["V004", "V005", "V011"]
    assumptions_refs: ["A004"]
    sub_question_binding: ["Q1", "Q2", "Q3"]
  - mechanism_id: "MECH002"
    name: "刚体链运动学递推"
    description: "板凳龙视为多节刚体铰接链，后节位置由前节约束递推；各把手均在螺线上"
    type: "physical"
    governing_principle: "刚体运动学：板的长度不变，相邻把手间距守恒；速度由位置对时间求导得到"
    variables_refs: ["V001", "V002", "V003", "V006", "V007"]
    assumptions_refs: ["A001", "A002", "A003"]
    sub_question_binding: ["Q1", "Q2", "Q4"]

equations:
  - equation_id: "E001"
    latex: "R(\\theta) = R_A - b\\theta, \\quad b = \\frac{p_{in}}{2\\pi}"
    type: "constitutive"
    variables_refs: ["V004", "V005"]
    parameters_refs: ["PARM006", "PARM008", "PARM009"]
    mechanism_ref: "MECH001"
    derivation_trace:
      from_assumptions: ["A004"]
      from_mechanisms: ["MECH001"]
      from_equations: []
      steps:
        - "等距螺线定义：相邻圈径向距离=螺距p"
        - "阿基米德螺线标准形式 R(θ)=R0+bθ，其中 b=p/(2π)"
        - "顺时针盘入时半径递减，故取负号"
    sub_question_binding: ["Q1", "Q2"]
    description: "阿基米德等距螺线参数方程"
  - equation_id: "E002"
    latex: "\\mathbf{r}_i(t) = \\mathbf{r}_{i-1}(t) + \\ell_i \\cdot \\hat{\\mathbf{u}}_i(t), \\quad \\hat{\\mathbf{u}}_i = \\frac{\\mathbf{r}_{i-1} - \\mathbf{r}_{i-2}}{\\|\\mathbf{r}_{i-1} - \\mathbf{r}_{i-2}\\|}"
    type: "balance"
    variables_refs: ["V001", "V002", "V006"]
    parameters_refs: ["PARM002", "PARM003", "PARM004"]
    mechanism_ref: "MECH002"
    derivation_trace:
      from_assumptions: ["A001", "A002"]
      from_mechanisms: ["MECH002"]
      from_equations: []
      steps:
        - "刚体假设→板长不变→相邻把手间距=ℓ_i"
        - "铰接假设→后节方向沿前两节连线方向"
        - "递推：已知龙头位置，逐节计算后续把手位置"
    sub_question_binding: ["Q1", "Q2"]
    description: "刚体链递推方程（后节位置=前节位置+板长×方向单位向量）"
  - equation_id: "E003"
    latex: "\\mathbf{v}_i(t) = \\frac{d\\mathbf{r}_i}{dt}, \\quad v_i = \\|\\mathbf{v}_i\\|"
    type: "definition"
    variables_refs: ["V001", "V002", "V003"]
    parameters_refs: []
    mechanism_ref: "MECH002"
    derivation_trace:
      from_assumptions: []
      from_mechanisms: ["MECH002"]
      from_equations: ["E002"]
      steps:
        - "速度定义为位置对时间的导数"
        - "由E002递推得到位置后，数值微分得到速度"
    sub_question_binding: ["Q1", "Q2", "Q4"]
    description: "速度定义方程"
  - equation_id: "E004"
    latex: "\\frac{d\\theta}{dt} = \\frac{v_0}{\\sqrt{R(\\theta)^2 + b^2}}, \\quad \\omega = \\frac{d\\theta}{dt}"
    type: "derived"
    variables_refs: ["V004", "V011"]
    parameters_refs: ["PARM007", "PARM009"]
    mechanism_ref: "MECH001"
    derivation_trace:
      from_assumptions: ["A005"]
      from_mechanisms: ["MECH001"]
      from_equations: ["E001"]
      steps:
        - "螺线弧长元 ds = √(R² + (dR/dθ)²) dθ = √(R² + b²) dθ"
        - "龙头速度 v0 = ds/dt = √(R² + b²) · dθ/dt"
        - "解得角速度 dθ/dt = v0 / √(R² + b²)"
    sub_question_binding: ["Q1", "Q2"]
    description: "龙头角速度方程（由匀速约束和螺线几何推导）"
  - equation_id: "E005"
    latex: "d_{ij}(t) = \\sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}"
    type: "definition"
    variables_refs: ["V001", "V002", "V008"]
    parameters_refs: []
    mechanism_ref: "MECH002"
    derivation_trace:
      from_assumptions: []
      from_mechanisms: ["MECH002"]
      from_equations: []
      steps:
        - "欧几里得距离定义：二维平面中两点间距离"
        - "在刚体链运动学框架下，用于碰撞检测的把手间距计算"
    sub_question_binding: ["Q2"]
    description: "把手间距离定义（碰撞检测用）"

dependencies:
  - dependency_id: "DEP001"
    from_type: "variable"
    from_id: "V004"
    to_type: "equation"
    to_id: "E001"
    relation: "feeds"
    sub_question_binding: ["Q1"]
  - dependency_id: "DEP002"
    from_type: "assumption"
    from_id: "A001"
    to_type: "constraint"
    to_id: "C002"
    relation: "derives"
    sub_question_binding: ["Q1"]
  - dependency_id: "DEP003"
    from_type: "mechanism"
    from_id: "MECH001"
    to_type: "equation"
    to_id: "E001"
    relation: "governs"
    sub_question_binding: ["Q1"]
  - dependency_id: "DEP004"
    from_type: "mechanism"
    from_id: "MECH002"
    to_type: "equation"
    to_id: "E002"
    relation: "governs"
    sub_question_binding: ["Q1"]
  - dependency_id: "DEP005"
    from_type: "equation"
    from_id: "E002"
    to_type: "equation"
    to_id: "E003"
    relation: "feeds"
    sub_question_binding: ["Q1"]
  - dependency_id: "DEP006"
    from_type: "variable"
    from_id: "V001"
    to_type: "constraint"
    to_id: "C002"
    relation: "constrains"
    sub_question_binding: ["Q1"]
  - dependency_id: "DEP007"
    from_type: "parameter"
    from_id: "PARM006"
    to_type: "equation"
    to_id: "E001"
    relation: "uses"
    sub_question_binding: ["Q1"]
  - dependency_id: "DEP008"
    from_type: "equation"
    from_id: "E001"
    to_type: "equation"
    to_id: "E004"
    relation: "feeds"
    sub_question_binding: ["Q1"]
  - dependency_id: "DEP009"
    from_type: "variable"
    from_id: "V008"
    to_type: "objective"
    to_id: "O002"
    relation: "feeds"
    sub_question_binding: ["Q2"]
  - dependency_id: "DEP010"
    from_type: "constraint"
    from_id: "C004"
    to_type: "variable"
    to_id: "V008"
    relation: "constrains"
    sub_question_binding: ["Q2"]

solvers:
  - solver_id: "S001"
    name: "刚体链递推数值仿真器"
    type: "simulation"
    method: "时间步进 + 刚体链几何递推 + 数值微分（中心差分）"
    parameters:
      dt: 0.01
      output_interval: 1.0
      integration: "analytical_theta + geometric_recursion"
    convergence_criteria:
      rigid_body_constraint_tolerance: 1e-6
      time_step_halving_change_threshold: 0.001
    implementation_ref: "CODE001"
    equations_refs: ["E001", "E002", "E003", "E004"]
    sub_question_binding: ["Q1", "Q2"]

experiments:
  - experiment_id: "EXP001"
    method: "Q1正向运动学仿真：0-300s每秒输出224个把手的位置和速度"
    parameters:
      time_range: [0, 300]
      output_interval: 1.0
      sections_to_report: [1, 2, 52, 102, 152, 202, 224]
    inputs_refs: ["V001", "V002", "V003", "V004"]
    outputs:
      - "result1.xlsx: 224把手×301时刻的位置速度"
      - "论文表1: 6个时刻7个特定节的位置"
      - "论文表2: 6个时刻7个特定节的速度"
    results:
      status: "computed"
      note: "数值结果由代码执行产生，此处为结构实例不填充具体数值"
    run_metadata:
      seed: 42
      repetitions: 5
      latency_seconds: 120.0
      exit_code: 0
    solver_ref: "S001"
    sub_question_binding: ["Q1"]

validations:
  - validation_id: "VAL001"
    type: "convergence"
    method: "刚体约束守恒验证：逐帧检查相邻把手间距与ℓ_i的相对误差"
    results:
      max_relative_error: 1e-7
      threshold: 1e-6
    pass_fail: "pass"
    evidence_refs: ["EXP001"]
    targets_refs: ["E002", "C002"]
    sub_question_binding: ["Q1"]
  - validation_id: "VAL002"
    type: "sensitivity"
    method: "敏感性分析：板长L_body ±10%对碰撞时刻t_collision的影响"
    results:
      L_body_plus_10pct_collision_time: "t+Δt1"
      L_body_minus_10pct_collision_time: "t-Δt2"
      elasticity_coefficient: 0.15
    pass_fail: "pass"
    evidence_refs: ["EXP001"]
    targets_refs: ["O002", "V012"]
    sub_question_binding: ["Q2"]

claims:
  - claim_id: "CL001"
    text: "板凳龙各把手的位置由龙头前把手的螺线位置和各节板长通过刚体链递推唯一确定"
    type: "interpretation"
    evidence_refs: ["EXP001", "VAL001"]
    model_refs: ["E002", "MECH002"]
    experiment_refs: ["EXP001"]
    validation_refs: ["VAL001"]
    sub_question_binding: ["Q1"]
    status: "supported"
  - claim_id: "CL002"
    text: "在螺距55cm、龙头速度1m/s条件下，舞龙队盘入过程中非相邻节会发生碰撞，碰撞时刻由最小把手间距首次小于板宽确定"
    type: "result"
    evidence_refs: ["EXP001", "VAL002"]
    model_refs: ["E005", "C004"]
    experiment_refs: ["EXP001"]
    validation_refs: ["VAL002"]
    sub_question_binding: ["Q2"]
    status: "supported"
  - claim_id: "CL003"
    text: "增大螺距可增加相邻圈径向距离，从而降低非相邻节碰撞风险并延后碰撞时刻"
    type: "recommendation"
    evidence_refs: ["VAL002"]
    model_refs: ["E001", "C004"]
    experiment_refs: []
    validation_refs: ["VAL002"]
    sub_question_binding: ["Q2", "Q3"]
    status: "supported"

model_graph:
  graph_version: "1.0"
  nodes:
    - node_id: "P001"
      node_type: "problem"
      label: "2024_A 板凳龙闹元宵"
    - node_id: "Q1"
      node_type: "subquestion"
      label: "Q1 正向运动学仿真"
    - node_id: "A001"
      node_type: "assumption"
      label: "板为刚体"
    - node_id: "A004"
      node_type: "assumption"
      label: "把手在螺线上"
    - node_id: "V001"
      node_type: "variable"
      label: "x_i(t) 把手x坐标"
    - node_id: "V004"
      node_type: "variable"
      label: "θ(t) 极角"
    - node_id: "MECH001"
      node_type: "mechanism"
      label: "阿基米德螺线参数化"
    - node_id: "MECH002"
      node_type: "mechanism"
      label: "刚体链运动学递推"
    - node_id: "E001"
      node_type: "equation"
      label: "螺线参数方程"
    - node_id: "E002"
      node_type: "equation"
      label: "刚体链递推方程"
    - node_id: "C002"
      node_type: "constraint"
      label: "间距守恒约束"
    - node_id: "O001"
      node_type: "objective"
      label: "Q1仿真目标"
    - node_id: "S001"
      node_type: "solver"
      label: "递推数值仿真器"
    - node_id: "EXP001"
      node_type: "experiment"
      label: "Q1正向仿真"
    - node_id: "VAL001"
      node_type: "validation"
      label: "刚体约束守恒验证"
    - node_id: "CL001"
      node_type: "claim"
      label: "位置由递推唯一确定"
  edges:
    - source_node: "P001"
      target_node: "Q1"
      edge_type: "binds_to"
      evidence_ref: null
      confidence: 1.0
    - source_node: "A004"
      target_node: "P001"
      edge_type: "cites_problem"
      evidence_ref: null
      confidence: 0.99
    - source_node: "A001"
      target_node: "C002"
      edge_type: "derives"
      evidence_ref: null
      confidence: 0.95
    - source_node: "V004"
      target_node: "E001"
      edge_type: "references_variable"
      evidence_ref: null
      confidence: 1.0
    - source_node: "E001"
      target_node: "MECH001"
      edge_type: "governed_by"
      evidence_ref: null
      confidence: 1.0
    - source_node: "E002"
      target_node: "MECH002"
      edge_type: "governed_by"
      evidence_ref: null
      confidence: 1.0
    - source_node: "C002"
      target_node: "V001"
      edge_type: "constrains"
      evidence_ref: null
      confidence: 1.0
    - source_node: "E002"
      target_node: "O001"
      edge_type: "defines"
      evidence_ref: null
      confidence: 1.0
    - source_node: "O001"
      target_node: "S001"
      edge_type: "solved_by"
      evidence_ref: null
      confidence: 1.0
    - source_node: "S001"
      target_node: "EXP001"
      edge_type: "produces"
      evidence_ref: null
      confidence: 1.0
    - source_node: "VAL001"
      target_node: "E002"
      edge_type: "validates"
      evidence_ref: null
      confidence: 1.0
    - source_node: "CL001"
      target_node: "EXP001"
      edge_type: "evidenced_by"
      evidence_ref: null
      confidence: 0.9
    - source_node: "CL001"
      target_node: "VAL001"
      edge_type: "evidenced_by"
      evidence_ref: null
      confidence: 0.9

modeling_trace:
  trace_version: "1.0"
  generated_at: "2026-09-08T10:00:00Z"
  agent_identity: "reference_exemplar"
  model_version: "N/A"
  input_sha256: "9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e"
  prompt_version: "model_ir_spec-v1.0"
  skill_version: "N/A"
  commit_hash: "reference"
  generation_order:
    - node_id: "A001"
      order_index: 1
      timestamp: "2026-09-08T10:00:01Z"
    - node_id: "A004"
      order_index: 2
      timestamp: "2026-09-08T10:00:02Z"
    - node_id: "V004"
      order_index: 3
      timestamp: "2026-09-08T10:00:03Z"
    - node_id: "MECH001"
      order_index: 4
      timestamp: "2026-09-08T10:00:04Z"
    - node_id: "E001"
      order_index: 5
      timestamp: "2026-09-08T10:00:05Z"
    - node_id: "V001"
      order_index: 6
      timestamp: "2026-09-08T10:00:06Z"
    - node_id: "MECH002"
      order_index: 7
      timestamp: "2026-09-08T10:00:07Z"
    - node_id: "E002"
      order_index: 8
      timestamp: "2026-09-08T10:00:08Z"
    - node_id: "C002"
      order_index: 9
      timestamp: "2026-09-08T10:00:09Z"
    - node_id: "O001"
      order_index: 10
      timestamp: "2026-09-08T10:00:10Z"
  version_history:
    - version_number: 1
      commit_hash: "reference"
      changed_nodes: ["ALL"]
      change_summary: "初始版本：Q1运动学建模完整实例"
      timestamp: "2026-09-08T10:00:00Z"
```

---

## 9. 科研迁移预留

### 9.1 CUMCM 特有 vs Domain-independent

| 类别 | 字段 | 说明 |
|---|---|---|
| **CUMCM 特有** | `problem_binding.sub_question_id` | 比赛题目编号（Q1-Q5） |
| **CUMCM 特有** | `problem_binding.problem_sha256` | 比赛题面冻结哈希 |
| **CUMCM 特有** | `problem_binding.competition_format` | 论文页数/提交规则 |
| **CUMCM 特有** | `model_family` 与 Problem Card `allowed_model_families` 对齐 | 比赛参考方法 |
| **CUMCM 特有** | `assumptions.anchors_to_problem` 的题面行号引用 | 比赛题面有明确文本 |
| **Domain-independent** | `variables` / `parameters` / `assumptions` / `mechanisms` / `objectives` / `constraints` / `equations` / `dependencies` / `solvers` / `experiments` / `validations` / `claims` | 核心建模结构，完全通用 |
| **Domain-independent** | `model_graph`（节点+边） | 建模结构图，完全通用 |
| **Domain-independent** | `modeling_trace` | 时序与版本，完全通用 |
| **Domain-independent** | `deterministic checks`（DC-001 至 DC-015） | 结构检查，完全通用 |
| **Domain-independent** | `model_diff` | 模型对比，完全通用 |

### 9.2 科研问题适配方案

科研问题与 CUMCM 的差异及适配：

| 维度 | CUMCM | 科研问题 | 适配方式 |
|---|---|---|---|
| 问题标识 | `sub_question_id` (Q1-Q5) | `research_question_id` (RQ1-RQn) | 字段重命名，语义不变 |
| 输入冻结 | `problem_sha256`（题面文本） | `literature_reference`（文献DOI/哈希）+ `dataset_sha256` | 扩展 problem_binding，增加文献/数据集引用 |
| 假设锚定 | 题面行号 | 文献引用 + 实验数据 | `anchors_to_problem` 扩展为 `anchors_to_source`，支持文献/数据 |
| 参数来源 | 题面给定为主 | 实验测定/文献值/拟合值 | `parameters.source` 已支持 `experimental`/`fitted` |
| 验证类型 | 基线/敏感性/收敛 | 复现实验/交叉验证/统计显著性 | `validations.type` 已支持扩展 |
| 模型家族 | 比赛参考方法 | 领域标准模型 | `model_family` 字段完全通用 |

### 9.3 核心建模结构的通用性证明

核心结构 `variable → equation → model → validation → claim` 在以下场景完全通用：

1. **物理实验**: variable（测量量）→ equation（物理定律）→ model（实验模型）→ validation（重复实验）→ claim（结论）
2. **社会科学**: variable（观测指标）→ equation（回归模型）→ model（统计模型）→ validation（交叉验证）→ claim（因果推断）
3. **工程设计**: variable（设计变量）→ equation（工程公式）→ model（设计模型）→ validation（仿真验证）→ claim（设计方案）
4. **生命科学**: variable（生物标志物）→ equation（动力学方程）→ model（系统生物学模型）→ validation（扰动实验）→ claim（机制解释）

### 9.4 CUMCM 作为第一阶段的理由

CUMCM 只是第一阶段最适合做能力工程的受控实验场，不是最终目的：

- **边界明确**: 题面固定、子问题明确、交付物规范
- **历史题多**: 历年题目可构建 benchmark
- **范式稳定**: 数学建模竞赛的方法论相对稳定
- **优秀论文多**: 有金标准/优秀论文可对照
- **可 benchmark**: 同一题多 Agent 可比较
- **可反复实验**: 题面不变，可重复运行
- **可比较 Agent**: 不同 Agent 解同一题，Model Diff 可结构化对比
- **可做 intervention**: 可控制输入/方法/验证策略，做因果干预实验

---

## 10. 设计决策记录

| # | 决策点 | 选择 | 理由 |
|---|---|---|---|
| D1 | Model IR 作为独立文件还是 Registry payload | 两者并存：IR 是完整规范，注册时作为 model artifact 的 payload | 复用 Registry 存储，同时 IR 可独立交换/校验 |
| D2 | Model Graph 与 Evidence Graph 合并还是分离 | 分离，通过 evidence_ref 关联 | Model Graph 是建模结构（细粒度），Evidence Graph 是证据结构（artifact 级），语义不同 |
| D3 | equation.type 枚举值 | constitutive / balance / definition / derived / boundary / initial | 覆盖数学建模中常见方程类型，与 Rubric L2.7 对齐 |
| D4 | objective.type 包含 simulate/find | 是 | CUMCM 中 Q1 是正向仿真（不是优化），需要 simulate 类型；Q2 是 find（求碰撞时刻） |
| D5 | assumptions.source 枚举 | problem_explicit / reasonable_simplification / domain_knowledge / derived | 与 Rubric L2.3 的假设分类对齐 |
| D6 | deterministic checks 与 semantic checks 分离 | 是 | DC 只做结构/引用检查（LLM-free），semantic 留给 Rubric |
| D7 | 2024_A 实例中把手数量 | 224个（223前把手+1龙尾后把手） | 题面明确要求"龙头、龙身和龙尾各前把手及龙尾后把手" |
| D8 | 板内孔间距计算 | ℓ = L - 2×d_offset（头: 2.86m, 身/尾: 1.65m） | 孔中心距最近板头27.5cm，两孔间距=板长-2×27.5cm |
| D9 | 螺线半径递减方向 | R(θ) = R_A - bθ（顺时针盘入向中心） | 顺时针盘入意味着半径减小 |
| D10 | R_A 取值 | 8.8m = 16 × 0.55m | 第16圈处半径≈16倍螺距（假设螺线从中心起算） |
| D11 | variables.type 包含 state/derived/decision/input | 是 | 区分状态变量、导出变量、决策变量、输入变量，有助于模型分析 |
| D12 | Modeling Trace 放在 IR 内还是独立文件 | IR 内 modeling_trace 字段 + 节点级 _trace | 保证 IR 自包含，同时支持细粒度追溯 |

---

## 附录 B: 与现有 schema 的关系

| Schema | 状态 | 与 Model IR 的关系 |
|---|---|---|
| `core/schemas/model_artifact.schema.json` | P13-3C 冻结，不修改 | Model IR 是其超集：增加了 mechanisms/equations/dependencies/solvers/experiments/validations/claims/model_graph/modeling_trace；字段更细粒度 |
| `core/schemas/model_spec.schema.json` | legacy，不修改 | Model IR 吸收了其 symbols/sub_problems/verification 的概念，重新组织为标准化字段 |
| `core/schemas/v3/artifact/artifact.schema.json` | V3 活跃 | Model IR 作为 type=model artifact 的 payload，外层遵循 V3 artifact 契约 |
| `research/P15/model_representation/model_ir.schema.json` | **本规范新增** | Model IR 的机器可读校验，draft 2020-12 |

---

*本规范为 MathModel Model Representation 层 v1.0 设计。所有新增文件位于 `research/P15/model_representation/`，不改 core/runtime。*
