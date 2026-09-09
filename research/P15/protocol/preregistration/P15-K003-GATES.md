# P15-K003 — 五 Gate 证据归档（DRAFT 阶段）

> 日期：2026-09-09 ｜ 设计真源：`P15-K003-DRAFT.md`（v0.1）
> 词表：复用 K002 frozen `catalog/model_families.yaml`（18 canonical，冻结未动）
> 题面：复用 K002 verified 8 题（`input_manifest.json` 全 verified）
> 状态：G1/G3/G5 已 PASS（本文件归档）；G2/G4 设计待 PREREGISTERED 前执行

## G1 — 评分维度 ↔ 产物字段映射表（v1.2，L3 判据切换到执行事实）

Rubric v1.1 22 维度（L1=9/L2=15/L3=9/L4=9，PASS=70% 且关键维度不全 0，L2.6 权重 3）。
**v1.2 唯一修订：L3 各维度评分对象 = 盲评包中的真实 ExecutionResult / VR 数值，
禁止以"声明执行/声称验证"为评分依据；无执行产物 → 该维度 0 分。**
（K002 教训：纯表示实验下 S 臂因"无执行证据"系统性低分、F 臂可叙述性声称——
K003 三臂执行地位平等，L3 不再依赖声明。）

| 维度 | 评分对象（盲评包产物字段） |
|---|---|
| L1.1 显式条件 | `problem_statement.txt`（题面全文，评估者对照） |
| L1.2 隐式条件 | `assumptions[]`（type=projection/mechanism_assumption 覆盖题面隐含前提） |
| L1.3 交付要求 | `problem_binding.sub_question_id` + `claims[].sub_question_binding` |
| L1.4 歧义点标注 | `assumptions[]` 中的歧义声明（v1.1 两档制） |
| L1.5 问题类型判定 | `model_family.primary`（catalog canonical 唯一词表） |
| L2.1 变量声明 | `variables[]`（type/unit/value_range/definition） |
| L2.2 参数声明 | `parameters[]`（source=题目/校准/文献/假设/推导） |
| L2.3 假设合理性 | `assumptions[]`（type + 与题面/机理一致性） |
| L2.4 目标正确性 | `objectives[]`（type=min/max/estimate/satisfy/simulate/find + 三角一致性） |
| L2.5 约束完备性 | `constraints[]`（与题面显式+隐式约束逐条对照） |
| L2.6 机理正确性 | `mechanisms[]`（四要素：题面/方程/目标约束/候选对比）+ `equations[]` |
| L2.7 方程结构 | `equations[]`（符号一致性 + 与 mechanisms 对齐） |
| **L3.1 求解策略匹配** | `solvers[]`（声明）+ `execution_result.status`（真实） |
| **L3.2 代码可执行性** | `execution_result.status`（**真实六态，只来自 returncode**） |
| **L3.3 结果收敛性** | `execution_result.outputs` + VR 数值（真实输出） |
| **L3.4 可复现性** | `code_hash` / `environment_hash` / replay（P1） |
| **L3.5 结果合理性** | VR（constraint_violation_max / 可行性 / 残差，机械判定） |
| L4.1 对照基线 | `validation_plan.limit_tests`（SV 强制；S/F 无此字段 → 如实低分） |
| L4.2 灵敏度分析 | `validation_plan.sensitivity`（同上） |
| L4.3 极限/边界检验 | `validations[].type=limit`（≥2 类 + 结果-主张关联） |
| L4.4 验证目标正确性 | `validations[]` 与 `objectives[]` 一一对应 |
| L4.5 证据-主张对应 | `claims[].evidence_refs` 全部可解析到真实产物（execution_result/VR） |

**G1 结论：PASS**（每个维度 ≥1 个可机械触发的盲评包字段；L3 判据切换为执行事实已落盘）。

## G3 — 词表统一（复用 K002 frozen）

- 单一词表：`catalog/model_families.yaml`（18 canonical，K002 FROZEN 未动）
- 别名回归测试：`tests/integration/test_vocabulary_alias.py`（25 用例，PASS）
- K003 生成侧要求：`model_family.primary` 必须取自 canonical 词表；
  机制层允许共享原语（state_transition 属 DP+MDP），机制层不做族判别
- **G3 结论：PASS**（词表 frozen:true 已锁定，K002 实验全程使用同一词表）

## G5 — 统计功效（PASS，k003_power.py）

- 输入：K002 实测 per-block sd=4.62；主检验 6 题 × 3 rep（块内均值 sd=2.667，
  配对差 SE=1.089）；配对 t 双侧 α=0.05 df=5（t_crit=2.571）；Monte Carlo 200k
- 结果：Δ=2.14→0.273 / 3.0→0.571 / 3.3→0.676 / 3.9→0.845 / 4.5→0.940
- **power≥0.8 需 Δ≥3.7**（如实声明：rep=3 为成本—功效权衡，功效边界写入 DRAFT §5；
  区分度预检后观测效应不支持 → 如实报告低功效，不做事后提 rep）
- **G5 结论：PASS**（功效计算完成，边界已声明；无设计外调参）

## G2 — Instrument validity（设计，待 PREREGISTERED 前执行）

- Anchored Protocol **v1.2**：校准集 8 份（覆盖 3 臂 × 代表性强弱，**每份含真实
  执行产物**——与 K002 的"无执行产物"校准集不同，L3 判据有事实对象）
- 通过标准：维度级 Cohen's κ ≥ 0.6，或分歧可归因（逐条记录）
- K002 锚定澄清保留：证据缺位判据显式化、L3.5/L4.3 二档、格式中立
- evaluator 池：复用 K002 3 独立 evaluator（GENERATOR≠EVALUATOR 隔离）

## G4 — 执行有效性（设计，待 PREREGISTERED 前执行）

- dry-run：run_code_pipeline 在 6 题（主检验）× 3 臂的预检产物上真实跑通
- 5 场景 fidelity 校验（复用 K002 dry-run 模式）：对齐 1.0 / 私有命名空间无
  mapping 0.0 / 私有+mapping 1.0 / 跑通但模型错 0.0 / mapping 撒谎 0.16
- output_mapping 契约：外部 Agent 交付 code 必须声明 {声明名→输出 key}，
  随 CODE artifact 登记（可审计），经 EXEC provenance 透传
- 通过标准：execution_success_rate=1.00（6 题全部真实执行）+ fidelity 报告落盘
