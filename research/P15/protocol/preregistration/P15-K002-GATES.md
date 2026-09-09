# P15-K002 — Measurement Gate 证据归档（G1–G5）

- 日期：2026-09-09
- 状态：**G3/G4/G5 PASS；G1 映射表冻结（v1）；G2 与区分度预检正在由外部 Organizer 执行（PREREGISTERED 前置）**
- 关联：P15-K002-DRAFT v0.6 §7.5；冻结时本文件连同 rubric/题面/schema 一并 hash 锁定
- 工具链状态（本地可建部分已全部就绪，2026-09-09 更新）：
  - `research/P15/scripts/k002_{common,state,gen_bundles,register,freeze,blind_pack}.py`
  - `research/P15/analysis/scripts/k002_analysis.py`（三臂配对 + DATA FREEZE，--selftest PASS）
  - prompt 模板 F/S/SV 已定稿（F/S 长度差 5.9% < 10%）
  - register 三 gate 实测：COVERAGE_FAIL（Q1-only）/ validation_plan FAIL（n_runs<3）/ REGISTERED（3/3 覆盖）

## G1 — Construct validity：评分维度 ↔ 产物字段映射（v1，冻结）

规则：每个评分维度至少 1 个产物字段可支撑（评分项可被产物字段触发）。

### L1 Problem Understanding（产物来源：MODEL_IR 18 字段 + 外部 problem_analysis）

| 维度 | 支撑字段 | 触发方式 |
|---|---|---|
| L1.1 显式条件提取 | `problem_binding`（problem_sha256 绑定冻结题面）+ `assumptions`（从题面数字派生） | 对照冻结题面逐条核条件 |
| L1.2 隐式条件识别 | `assumptions[].derivation`（推导依据） | 隐式条件须显式说明推导 |
| L1.3 交付要求识别 | `problem_binding.problem_card_ref` + `claims` 覆盖子问题 | 交付物在 claims/experiments 中有对应 |
| L1.4 歧义点标注 | `assumptions[].ambiguity_handling`（S+V 臂 validation_plan.ambiguity_handling） | 有歧义则必须有处理方案字段 |
| L1.5 问题类型判定 | `model_family`（primary/secondary/mechanism/solver，受控词表解析） | 解析到 canonical family 与 gold 有交集 |

### L2 Model Construction（产物来源：MODEL_IR 结构化字段）

| 维度 | 支撑字段 |
|---|---|
| L2.1 变量声明 | `variables[]`（variable_id/name/symbol/definition/unit/type/sub_question_binding） |
| L2.2 参数声明 | `parameters[]`（来源 source + 取值 value） |
| L2.3 假设合理性 | `assumptions[]`（每条含合理性说明） |
| L2.4 目标正确性 | `objectives[]`（type/expression/variables_refs） |
| L2.5 约束完备性 | `constraints[]`（constraint_id/type/expression/variables_refs/source） |
| L2.6 机理正确性 | `mechanisms[]` + `model_family`（受控词表） |
| L2.7 方程结构完整性 | `equations[]`（latex/type/边界初始条件声明） |

### L3 Solving（产物来源：执行级 artifacts + MODEL_IR.solvers）

| 维度 | 支撑字段 |
|---|---|
| L3.1 求解策略匹配 | `solvers[]`（solver_id/method/implementation_ref→CODE） |
| L3.2 代码可执行性 | `execution_result.status`（六态，真实执行非声称） |
| L3.3 结果收敛性 | `execution_result.outputs` + 残差记录 |
| L3.4 可复现性 | `execution_result.seed/multi_run`（S+V 臂 validation_plan.multi_seed）+ replay 记录 |
| L3.5 结果合理性 | `execution_result.outputs` 数值物理/逻辑范围检查 |

### L4 Validation（产物来源：validations[] + S+V 臂 validation_plan + execution_result）

| 维度 | 支撑字段 |
|---|---|
| L4.1 对照基线 | `validations[].type=baseline`（S+V 臂强制） |
| L4.2 灵敏度分析 | `validations[].type=sensitivity` / validation_plan.sensitivity |
| L4.3 极限/边界检验 | `validation_plan.limit_tests`（S+V 臂强制；S 臂无此字段→如实低分） |
| L4.4 验证目标正确性 | `validations[].targets_refs` ↔ `objectives[].objective_id` 对应 |
| L4.5 证据-主张对应 | `claims[].evidence_refs` ↔ `validations[]`/`experiments[]` 全部可解析 |

> G1 结论：全部 26 个评分维度均有 ≥1 个可机械触发的产物字段。S 臂与 S+V 臂的差异只在
> validation_plan 强制字段（L4.1/4.2/4.3/4.5 的触发强度不同）——这正是实验要测的对比。

## G2 — Instrument validity（待 PREREGISTERED 前执行）

- 设计：5 份盲评样例（覆盖 3 臂 × 代表性强弱）由 3 个独立 evaluator 各自评分，
  计算维度级 Cohen's κ。
- 通过标准：κ ≥ 0.6，或分歧可归因于模糊声明（逐条记录）。
- 现状：K001 的 55 份盲评已由 3 个独立 evaluator 完成（Generator ≠ Evaluator 隔离），
  可复用其 evaluator 池；G2 样例评分在 PREREGISTERED 前完成并归档此处。
- 风险声明：若 κ < 0.6 且分歧不可归因 → 修 rubric 后重测（不降标准）。

## G3 — Vocabulary validity：词表统一（PASS）

- 单一词表：`catalog/model_families.yaml` v1.0（18 canonical families，frozen: false 待 K002 FROZEN 置 true）。
- 解析测试（K001 词表错位回归）：`tests/integration/test_vocabulary_alias.py`
  - `dynamic_programming` ← `discrete_recurrence/dp/bellman_recurrence`（K001 错位对）
  - `numerical_pde` ← `pde_transient_heat_conduction/heat_transfer`（B0-R2 对）
  - `queuing_theory` ← `queueing_threshold_decision`（K001 2019_C 对）
  - `kinematic_geometry` ← `hybrid_geometry_optimization`（K001 2024_A 对）
  - `optimization` ← `resource_allocation_optimization`（2020_B 对）
  - 解析失败 → OUT_OF_CATALOG（不自动判错，盲评语义判断）
- 三源一致：schema 建议词 / cards family / benchmark allowed_modeling_structures /
  生成侧自由命名 全部可解析到 canonical（回归测试通过）。
- **命中判定规则（v1）**：族命中只用命名层（canonical id / aliases）解析；
  mechanism/method/solver 是跨族共享的语义原语（如 state_transition 同时是
  dynamic_programming 与 markov_decision_process 的机制），仅用于"机制覆盖"
  报告，不做族判别——避免共享机制导致双族命中模糊（G3 测试锁定）。
- K002 冻结时 `frozen: true` 写入，此后词表修改走修订流程。

## G4 — Execution validity：真实执行支撑（PASS）

- 证据：`research/P15/dryrun/K002_DRYRUN_REPORT.md`（P0-E8）
- 5 场景判定全部符合：aligned/misaligned 语义在真实 2019_C MODEL_IR 上可区分、
  防作弊（mapping 撒谎检测）；execution_success_rate / model_fidelity /
  evidence_completeness 机械可测。
- L3.2/L3.4/L4 类评分的数值必须来自 execution_result（真实执行状态六态），
  无占位 result（P0 工程项①已治理：result.status="not_executed" 不再伪装）。

## G5 — Statistical validity：block 功效（PASS，诚实声明）

- 证据：`research/P15/analysis/k002_power.py`（Monte Carlo 模拟 200k，无依赖）
- 设计：block=6、臂内 5 rep、配对差检验（双侧 α=0.05、df=5、t_crit=2.571）
- 基线方差：K001 per-block 差值 sd=4.62 → 块内均值 sd=2.07（rep 独立假设）

| 效应量 Δ | 功效 | 判断 |
|---|---|---|
| 1.00 | 0.16 | 不足 |
| 2.14（K001 观测） | 0.54 | 不足 |
| 3.00 | 0.81 | ≥0.80 |
| 3.50 | 0.91 | ≥0.80 |
| 3.90 | 0.95 | ≥0.80 |

- 诚实结论：本设计可检出 ≥3.0 的效应（80% 功效）；K001 观测效应量级（2.14）下
  功效约 0.5。预注册口径维持"效应量 + 95% CI 为主、假设检验为辅助"（与 K001 同决策门）。
- 题目区分度预检（§3.5）：主检验 6 题各 1 个预检 rep（2 臂 × 6 题 = 12 runs），
  预先声明"条件内方差=0 且条件间差=0 → 无区分度 block 剔除单列；≥2 题无区分度 → STOP"。

## 汇总

| Gate | 状态 | 证据 |
|---|---|---|
| G1 Construct | 映射表 v1 冻结 | 本文件 §G1 |
| G2 Instrument | 待执行（PREREGISTERED 前） | 本文件 §G2 设计 |
| G3 Vocabulary | PASS | model_families.yaml + 解析回归测试 |
| G4 Execution | PASS | K002_DRYRUN_REPORT.md |
| G5 Statistical | PASS | k002_power.py |
