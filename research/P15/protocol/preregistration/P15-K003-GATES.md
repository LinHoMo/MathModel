# P15-K003 — 五 Gate 证据归档（DRAFT 阶段）

> 日期：2026-09-09 ｜ 设计真源：`P15-K003-DRAFT.md`（v0.1）
> 词表：复用 K002 frozen `catalog/model_families.yaml`（18 canonical，冻结未动）
> 题面：复用 K002 verified 8 题（`input_manifest.json` 全 verified）
> 状态：**G1–G5 全部 PASS（本文件归档，2026-09-09）**——G1/G3/G5 已 PASS；
> G2（Instrument validity）与 G4（执行有效性）已执行通过，见下

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

## G2 — Instrument validity（**PASS，2026-09-09**）

- Anchored Protocol **v1.2**：校准集 8 份（覆盖 3 臂 × fidelity 四档
  1.0/0.9/0.82/unverifiable × 5 题，**每份含真实执行产物**——L3 判据有事实对象），
  从预检 18 runs 选取，匿名化（condition_map 单独存放，未外泄给 evaluator）
- 3 独立 evaluator（互不可见）按 rubric v1.1 + 锚定澄清评分，22 维度
- **Round 1：mean κ=0.5749 FAIL**（9/22 达标）→ 6 类真实分歧逐条归因
  （L1.4 假设≠歧义标注 / L1.2 隐式条件定义 / L3.3 F 臂 fidelity=null /
  L2.6 公式符号标注 / L4.1 内部检验≠对照基线 / L4.5 证据-主张严格对应）
  + L3.4 Kappa 悖论伪影（po=0.9167、κ=0.3333、23/24 同分仅 1 包分歧）
- **锚定澄清 v1.2a**：仅判据显式化（维度/权重/阈值/满分不动）→ Round 2
- **Round 2：mean κ=0.712 PASS**（13/22 维度 ≥0.6；mean QWK=0.7322；
  残余 9 个 κ<0.6 维度全部可归因：2 个 Kappa 悖论伪影 + 3 个边际偏斜 +
  4 个边界判据理解差异，**0 个无法解释**）
- **关键验证**：L3 真实执行判据维度（L3.2 代码可执行性、L3.5 结果合理性）
  κ=1.0 完美一致——v1.2 "L3=执行事实"核心修订有效，消除 K002 的 L3 格式不对称分歧
- 通过标准（κ≥0.6 或分歧可归因）满足；**G2 PASS**
- 证据：`research/P15/experiments/P15-K003-precheck/g2/`（g2_kappa.json /
  ANCHORED_PROTOCOL_v1.2a.md / evaluator_{A,B,C}/ 24 份评分 / G2_REPORT.md）

## G4 — 执行有效性（**PASS，2026-09-09**）

- dry-run：run_code_pipeline 在 6 题（主检验）上真实跑通，**execution_success_rate
  = 1.00**（6/6 全部 subprocess 真实执行，status 仅来自 returncode）
- 18/18 runs（6 题 × 3 臂 × 1 rep）全部落盘：表示文件 + 自包含 run_model.py
  （纯标准库，ABI `def solve(inputs)->dict`）+ output_mapping + execution_result
  + fidelity VR；三臂执行地位完全平等（F 臂同样真实执行、同样进盲评包）
- 5 场景 fidelity 校验全过：对齐 1.0 / 私有无 mapping 0.0 / 私有+mapping 1.0 /
  跑通但模型错 0.0 / mapping 撒谎 0.3636（partial，符合"撒谎不能掩盖实体缺失"设计意图）
- output_mapping 契约有效：CODE artifact 登记 → EXEC provenance 透传 →
  fidelity 校验消费，全链路可审计
- 词表合规：6 题 model_family.primary 全部取自 catalog 18 canonical，无 out_of_catalog
- **G4 PASS**；证据：`research/P15/experiments/P15-K003-precheck/`
  （PRECHECK_REPORT.md / dryrun/g4_dryrun_report.json / runs/）
