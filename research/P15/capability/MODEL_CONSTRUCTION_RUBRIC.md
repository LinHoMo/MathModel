# Model Construction Rubric — 模型构建评分标准

- 版本：v1.0（Phase 4 重建）
- 日期：2026-09-08
- 上游：`research/REPOSITORY_AUDIT/04_MODELING_CAPABILITY_AUDIT.md` §2（Model Construction 层级分解）
- 关联：`CAPABILITY_MAP.md`（能力定义）、`FAILURE_TAXONOMY.md`（失败模式）
- 原则：本 Rubric 定义**能力维度的评分标准**，Evaluator 实现细节引用 EVALUATOR_VALIDITY_PROTOCOL
- 评分层级：L1 Problem Understanding → L2 Model Construction → L3 Solving → L4 Validation

---

## 0. 评分总则

### 0.1 层级依赖

```
L1 Problem Understanding（输入：题面文本）
  ↓ 输出：结构化问题分析
L2 Model Construction（输入：L1 输出 + 方法选择）
  ↓ 输出：MODEL_ARTIFACT（变量/参数/假设/目标/约束/机制/方程）
L3 Solving（输入：L2 输出的形式化模型）
  ↓ 输出：Result Artifact（数值结果/代码/执行记录）
L4 Validation（输入：L3 输出 + 验证设计）
  ↓ 输出：Evidence Artifact + Claim 判定
```

**前级 FAIL 时后级评分仅作参考**：L1 FAIL 的模型，L2-L4 的高分不能补偿整体判定。这是 Method correctness ≠ Model correctness 原则的层级化体现。

### 0.2 评分维度

每个层级包含若干评分维度，每个维度：
- 0 分：完全缺失/错误
- 1 分：部分存在但有明显缺陷
- 2 分：完整且正确

层级总分 = 各维度得分之和。PASS 阈值 = 总分 ≥ 总分的 70%，且无关键维度（标 ★）为 0 分。

### 0.3 证据要求

每个维度的评分必须附带证据指针（artifact 路径 / run manifest 字段 / 人工评审记录），不允许无证据的评分。

---

## L1: Problem Understanding（问题理解）

### 评分维度

| # | 维度 | 权重 | 关键? | 说明 |
|---|---|---|---|---|
| L1.1 | 显式条件提取 | 2 | ★ | 题面中的数字、参数、约束是否被完整提取 |
| L1.2 | 隐式条件识别 | 2 | | 题面未明说但可推导的条件（如物理约束、边界） |
| L1.3 | 交付要求识别 | 2 | ★ | 题目要求的交付物（文件格式、精度、时间范围） |
| L1.4 | 歧义点标注 | 1 | | 题面中的歧义是否被显式识别和处理 |
| L1.5 | 问题类型判定 | 2 | ★ | 问题的数学类型/建模范式是否正确判定 |

**总分**：9 分。PASS = ≥ 6.3 分，且 L1.1/L1.3/L1.5 不全为 0。

### L1.1 显式条件提取

- **0 分**：题面中的关键参数/数字未被提取，或提取错误率 > 30%
- **1 分**：提取了大部分显式条件，但有遗漏或错误（错误率 10%-30%）
- **2 分**：题面中所有数字、参数、约束被完整提取且正确（错误率 < 10%）
- **通过标准**：≥ 1 分
- **证据要求**：problem_analysis artifact 中的 extracted_conditions 列表 vs 题面原文逐条对照
- **关联 FM**：FM-PA-003 wrong_problem_interpretation

### L1.2 隐式条件识别

- **0 分**：未识别任何隐式条件
- **1 分**：识别了部分隐式条件，但有明显遗漏（如物理边界、守恒律）
- **2 分**：识别了主要隐式条件并显式说明推导依据
- **通过标准**：≥ 1 分（非关键维度，允许 0 分但扣分）
- **证据要求**：problem_analysis artifact 中的 implicit_conditions 列表 + 推导说明
- **关联 FM**：FM-MC-004 missing_variables（隐式条件对应的变量遗漏）

### L1.3 交付要求识别

- **0 分**：未识别交付要求（如不知道需要输出 result1.xlsx、6 位小数）
- **1 分**：识别了部分交付要求，但格式/精度/范围有遗漏
- **2 分**：完整识别所有交付要求（文件格式、精度、时间范围、特定时刻输出）
- **通过标准**：≥ 1 分
- **证据要求**：problem_analysis artifact 中的 deliverables 列表 vs CUMCM-Bench required_deliverables
- **关联 FM**：FM-PA-003（交付要求误解）

### L1.4 歧义点标注

- **0 分**：题面有歧义但未标注
- **1 分**：标注了歧义但未给出处理方案
- **2 分**：标注了歧义并给出了合理的假设/处理方案
- **通过标准**：≥ 0 分（非关键维度，无题面歧义时默认 2 分）
- **证据要求**：problem_analysis artifact 中的 ambiguities 列表
- **关联 FM**：无直接 FM（歧义处理是 Assumption Construction 的前置）

### L1.5 问题类型判定

- **0 分**：问题类型判定错误（如运动学判定为评价类）
- **1 分**：判定部分正确（综合题只识别了一个类型）
- **2 分**：问题类型/建模范式判定正确，与 gold family 有交集
- **通过标准**：≥ 1 分
- **证据要求**：type-classifier 输出的 problem_type vs CUMCM-Bench family[]
- **关联 FM**：FM-PA-001 wrong_abstraction、FM-MS-001 wrong_model_family

### L1 整体通过标准

- 总分 ≥ 6.3/9
- L1.1（显式条件）≥ 1
- L1.3（交付要求）≥ 1
- L1.5（问题类型）≥ 1
- 若 L1.5 = 0（问题类型完全错误），整体 L1 = FAIL，无论其他维度得分

---

## L2: Model Construction（模型构建）

### 评分维度

| # | 维度 | 权重 | 关键? | 说明 |
|---|---|---|---|---|
| L2.1 | 变量声明完备性 | 2 | ★ | 所有关键变量已声明并区分类型 |
| L2.2 | 参数声明完备性 | 2 | ★ | 方程中引用的所有参数已声明来源与取值 |
| L2.3 | 假设合理性 | 2 | | 假设集显式、合理、可检验 |
| L2.4 | 目标正确性 | 2 | ★ | 优化目标/估计量与题目要求一致 |
| L2.5 | 约束完备性 | 2 | ★ | 所有关键约束已形式化且方向正确 |
| L2.6 | 机理正确性 | 3 | ★★ | 机理选择与问题物理/现实一致 |
| L2.7 | 方程结构完整性 | 2 | | 方程结构完整，可求解 |

**总分**：15 分。PASS = ≥ 10.5 分，且 L2.1/L2.2/L2.4/L2.5/L2.6 不全为 0。

### L2.1 变量声明完备性

- **0 分**：关键变量未声明（CUMCM-Bench key_variables 缺失率 > 30%）
- **1 分**：大部分变量已声明，但有遗漏或类型未区分（缺失率 10%-30%）
- **2 分**：所有关键变量已声明，区分状态/决策/观测/常量类型（缺失率 < 10%）
- **通过标准**：≥ 1 分
- **证据要求**：MODEL_ARTIFACT variables 列表 vs CUMCM-Bench key_variables[]；变量类型标注
- **关联 FM**：FM-MC-004 missing_variables

### L2.2 参数声明完备性

- **0 分**：方程中引用的参数 > 30% 未在 parameters 中声明
- **1 分**：大部分参数已声明，但有未声明参数（10%-30%）
- **2 分**：方程中引用的所有参数已声明，每个参数有来源（题面/校准/文献/假设）和取值
- **通过标准**：≥ 1 分
- **证据要求**：方程符号集 ⊆ parameters 声明集；每个参数有 source 字段
- **关联 FM**：FM-MC-004 missing_variables、FM-FC-002 symbol_inconsistency

### L2.3 假设合理性

- **0 分**：无假设声明，或假设与题面矛盾
- **1 分**：有假设声明但部分不合理（如校准锚导致生物不合理结果）
- **2 分**：假设集显式、合理、可检验，区分投影假设/校准锚/机制假设/简化假设
- **通过标准**：≥ 1 分
- **证据要求**：MODEL_ARTIFACT assumptions 列表；每条假设的合理性说明
- **关联 FM**：FM-PA-003（假设与题面矛盾）

### L2.4 目标正确性

- **0 分**：优化目标/估计量与题目要求完全不一致
- **1 分**：目标部分正确（多目标问题只优化了部分目标）
- **2 分**：目标函数与题目要求一致，输出类型匹配
- **通过标准**：≥ 1 分
- **证据要求**：MODEL_ARTIFACT objective 描述 vs 题目 sub_questions 中的目标描述
- **关联 FM**：FM-PA-002 wrong_objective

### L2.5 约束完备性

- **0 分**：关键约束缺失（CUMCM-Bench key_constraints 缺失率 > 30%），或约束方向错误
- **1 分**：大部分约束已形式化，但有遗漏或方向错误（10%-30%）
- **2 分**：所有关键约束已形式化，方向正确，无符号错误
- **通过标准**：≥ 1 分
- **证据要求**：MODEL_ARTIFACT constraints 列表 vs CUMCM-Bench key_constraints[]；约束方向检查
- **关联 FM**：FM-MC-003 wrong_constraints

### L2.6 机理正确性（核心维度，权重 3）

- **0 分**：机理完全错误（如用评价方法解动力学，FM-MS-002 method_name_trap）
- **1 分**：机理家族正确但具体形式有缺陷（如 ODE 家族但方程形式不当）
- **2 分**：机理选择正确，控制方程与问题物理机制一致
- **3 分**：机理正确且有对比分析（候选模型对比 + 选择依据）
- **通过标准**：≥ 1 分（若 = 0，整体 L2 = FAIL）
- **证据要求**：MODEL_ARTIFACT mechanism 描述；控制方程；候选模型对比（如有）
- **关联 FM**：FM-MC-001 wrong_mechanism、FM-MS-002 method_name_trap、FM-MC-002 wrong_causal_structure

### L2.7 方程结构完整性

- **0 分**：无方程，或方程不可求解
- **1 分**：有方程但结构不完整（缺少边界条件/初始条件）
- **2 分**：方程结构完整，包含控制方程 + 边界条件 + 初始条件，可求解
- **通过标准**：≥ 1 分
- **证据要求**：MODEL_ARTIFACT equations 列表；边界/初始条件声明
- **关联 FM**：FM-FC-004 index_inconsistency（边界/索引错误）

### L2 整体通过标准

- 总分 ≥ 10.5/15
- L2.1（变量）≥ 1
- L2.2（参数）≥ 1
- L2.4（目标）≥ 1
- L2.5（约束）≥ 1
- L2.6（机理）≥ 1
- 若 L2.6 = 0（机理完全错误），整体 L2 = FAIL——这是 Method correctness ≠ Model correctness 的核心门禁

---

## L3: Solving（求解）

### 评分维度

| # | 维度 | 权重 | 关键? | 说明 |
|---|---|---|---|---|
| L3.1 | 求解策略匹配 | 2 | ★ | 求解算法与模型类型/口径匹配 |
| L3.2 | 代码可执行性 | 2 | ★ | 代码无崩溃，可完整运行 |
| L3.3 | 结果收敛性 | 2 | | 数值结果收敛，无发散 |
| L3.4 | 可复现性 | 2 | ★ | 多 seed 结果稳定，replay match |
| L3.5 | 结果合理性 | 1 | | 结果在物理/逻辑合理范围内 |

**总分**：9 分。PASS = ≥ 6.3 分，且 L3.1/L3.2/L3.4 不全为 0。

### L3.1 求解策略匹配

- **0 分**：求解策略与模型不匹配（如刚性 ODE 用显式欧拉、年率按月复利）
- **1 分**：策略基本匹配但有口径问题（步长/精度设置不当）
- **2 分**：求解策略与模型类型、参数口径完全匹配
- **通过标准**：≥ 1 分
- **证据要求**：代码中的求解器配置；步长/精度设置；与模型口径的一致性说明
- **关联 FM**：FM-SV-001 infeasible_solution、FM-FC-004 index_inconsistency（口径错误）

### L3.2 代码可执行性

- **0 分**：代码崩溃，无法产生任何结果
- **1 分**：代码可运行但有警告/部分输出缺失
- **2 分**：代码完整运行，无错误，产出所有要求的结果
- **通过标准**：≥ 1 分
- **证据要求**：执行日志；exit code；Result Artifact 完整性
- **关联 FM**：FM-SV-001 infeasible_solution

### L3.3 结果收敛性

- **0 分**：结果发散/不收敛/含 NaN
- **1 分**：结果收敛但收敛慢/残差较大
- **2 分**：结果收敛，残差低于阈值，网格收敛检验通过
- **通过标准**：≥ 0 分（非关键维度，解析解问题默认 2 分）
- **证据要求**：残差序列；收敛标志；网格收敛检验（如有）
- **关联 FM**：FM-SV-002 non_convergence

### L3.4 可复现性

- **0 分**：多 seed 结果方差 > 20%，或 replay match < 80%
- **1 分**：多 seed 方差 10%-20%，或 replay match 80%-95%
- **2 分**：多 seed（≥5）方差 < 10%，replay match ≥ 95%，seed 固定为 42
- **通过标准**：≥ 1 分
- **证据要求**：多 seed 运行记录；replay match 率；seed 配置
- **关联 FM**：FM-SV-003 numerical_instability

### L3.5 结果合理性

- **0 分**：结果明显不合理（负概率、负密度、超光速等）
- **1 分**：结果基本合理但有边界异常
- **2 分**：结果在物理/逻辑合理范围内，量级正确
- **通过标准**：≥ 0 分（非关键维度）
- **证据要求**：Result Artifact 数值；物理合理性检查记录
- **关联 FM**：FM-SV-003 numerical_instability（非物理值）

### L3 整体通过标准

- 总分 ≥ 6.3/9
- L3.1（策略）≥ 1
- L3.2（可执行）≥ 1
- L3.4（可复现）≥ 1

---

## L4: Validation（验证）

### 评分维度

| # | 维度 | 权重 | 关键? | 说明 |
|---|---|---|---|---|
| L4.1 | 对照基线 | 2 | ★ | 有对照基线（零模型/随机/文献） |
| L4.2 | 灵敏度分析 | 2 | ★ | 有参数扰动分析，扰动了敏感参数 |
| L4.3 | 极限/边界检验 | 1 | | 有极端参数/边界条件检验 |
| L4.4 | 验证目标正确性 | 2 | ★ | 验证了模型的核心主张，而非无关目标 |
| L4.5 | 证据-主张对应 | 2 | ★ | 每个 Claim 有 Evidence 支持，无 unsupported claim |

**总分**：9 分。PASS = ≥ 6.3 分，且 L4.1/L4.2/L4.4/L4.5 不全为 0。

### L4.1 对照基线

- **0 分**：无任何对照基线
- **1 分**：有基线但基线选择不当（如过于简单/不相关）
- **2 分**：有合理的对照基线（零模型/随机基线/文献基准），并报告了对比结果
- **通过标准**：≥ 1 分
- **证据要求**：baseline 配置 + 对比结果；robustness tags 中的 baseline 标签
- **关联 FM**：FM-VA-001 missing_validation

### L4.2 灵敏度分析

- **0 分**：无灵敏度分析
- **1 分**：有灵敏度分析但扰动了不敏感参数（弹性系数 ≈ 0）
- **2 分**：有灵敏度分析，扰动了敏感参数，报告了弹性系数和鲁棒性边界
- **通过标准**：≥ 1 分
- **证据要求**：sensitivity analysis 结果；扰动参数列表；弹性系数
- **关联 FM**：FM-VA-002 wrong_validation_target（扰动不敏感参数）

### L4.3 极限/边界检验

- **0 分**：无极限检验
- **1 分**：有极限检验但覆盖不全
- **2 分**：有极限/边界条件检验（极端参数、边界值），并报告了结果
- **通过标准**：≥ 0 分（非关键维度）
- **证据要求**：limit test 配置 + 结果
- **关联 FM**：FM-VA-001 missing_validation

### L4.4 验证目标正确性

- **0 分**：验证了与模型主张无关的目标（如主张精度高但验证速度快）
- **1 分**：验证了部分核心主张，但有遗漏
- **2 分**：验证了模型的所有核心主张，验证指标与 evaluation_targets 对应
- **通过标准**：≥ 1 分
- **证据要求**：validation_targets vs 模型 claims vs CUMCM-Bench evaluation_targets[]
- **关联 FM**：FM-VA-002 wrong_validation_target

### L4.5 证据-主张对应

- **0 分**：存在 unsupported claim（主张无证据或证据与主张矛盾）
- **1 分**：大部分主张有证据支持，但有 unresolved claim
- **2 分**：所有 Claim 有 ≥1 条 Evidence 支持，判定为 supported 或 refuted（无 unresolved）
- **通过标准**：≥ 1 分
- **证据要求**：Evidence Graph；Claim 判定列表（supported/refuted/unresolved）
- **关联 FM**：FM-EV-001 unsupported_claim、FM-EV-002 missing_provenance

### L4 整体通过标准

- 总分 ≥ 6.3/9
- L4.1（基线）≥ 1
- L4.2（灵敏度）≥ 1
- L4.4（验证目标）≥ 1
- L4.5（证据-主张）≥ 1

---

## 跨层级规则

### 规则 1：前级 FAIL 阻断

- L1 FAIL → L2-L4 评分仅作参考，整体判定为 FAIL
- L2 FAIL（尤其 L2.6 机理 = 0）→ L3-L4 评分仅作参考
- 这确保了"方法正确但模型错误"不会被下游高分掩盖

### 规则 2：Claim-Support Gap 监控

- Claim Coverage = L2 中模型声称回答的对齐点比例
- Support Coverage = L2 中有正式数学承载的主张比例
- Gap = Claim Coverage − Support Coverage
- 若 Gap > 30%，触发 L2.6（机理）和 L4.5（证据-主张）的复审
- P13-3C-R5 实测：B1-F Gap = +37.0%，说明即使最强臂也有主张-支持缺口

### 规则 3：Method Correctness 独立报告

- L3（Solving）中的数学正确性必须独立报告
- 一个模型可以 L3 = PASS（数学正确）但 L2 = FAIL（机理错误）——这正是 method_name_trap
- 评分报告中必须同时展示 L2 和 L3 分数，不得合并为一个 composite

### 规则 4：验证类型最小集

- L4 PASS 要求至少包含：1 个对照基线 + 1 个灵敏度分析
- 极限检验为加分项（L4.3），非必须
- 这修正了旧 FM-VA-01 定义过宽（81% 题标注）的问题

---

## 评分报告模板

```yaml
problem_id: 2024_A
arm: B0
timestamp: ...
L1:
  total: 3/9
  pass: false
  dimensions:
    L1.1_explicit_conditions: {score: 1, evidence: "..."}
    L1.2_implicit_conditions: {score: 0, evidence: "..."}
    L1.3_deliverables: {score: 1, evidence: "..."}
    L1.4_ambiguities: {score: 0, evidence: "..."}
    L1.5_problem_type: {score: 0, evidence: "TOPSIS for kinematics → FM-PA-001"}
L2:
  total: ...
  pass: false
  note: "L2.6 mechanism = 0 (FM-MS-002 method_name_trap), overall L2 FAIL"
L3:
  total: ...
  note: "TOPSIS implementation mathematically correct but model misaligned"
L4:
  total: ...
overall: FAIL
root_cause: "L1.5 problem_type = 0 → L2.6 mechanism = 0 → method_name_trap"
failure_modes: [FM-PA-001, FM-MS-001, FM-MS-002, FM-ME-003]
```

---

## 与现有 evaluator 的映射

| Rubric 层级 | 现有 evaluator | 覆盖状态 |
|---|---|---|
| L1 Problem Understanding | problem-parser（legacy，定性） | 部分覆盖，无量化 |
| L2 Model Construction | model_construction.py（structural + mathematical + alignment） | 三维覆盖，但机理正确性未独立量化 |
| L3 Solving | experiment_validity + replay | Computational Reliability 覆盖，Solving Strategy 未覆盖 |
| L4 Validation | experiment_validity + validation_reliability + P14 integrity gate | 覆盖验证存在性，证据-主张对应在 P14 中可用 |

**评估实现细节**：引用 EVALUATOR_VALIDITY_PROTOCOL（Evaluator-Auditor 子代理产出），本 Rubric 不重复实现细节。

---

*本文件为 Phase 4 Model Construction Rubric 产出。重点是能力维度的定义和评分标准，evaluator 实现引用 EVALUATOR_VALIDITY_PROTOCOL。*
