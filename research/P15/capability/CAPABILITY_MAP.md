# Capability Map — MathModel Harness 能力地图

- 版本：v1.1（战略定位更新）
- 日期：2026-09-08
- 上游：`research/REPOSITORY_AUDIT/04_MODELING_CAPABILITY_AUDIT.md`（C0–C15 审计）
- 原则：Method correctness ≠ Model correctness；能力 ≠ 可观察行为 ≠ 失败模式 ≠ 测量仪器 ≠ 证据
- 状态枚举：MEASURED / PARTIALLY_MEASURED / UNMEASURED / MEASUREMENT_INVALID
- 置信度枚举：HIGH / MEDIUM / LOW
- 泛化状态：CROSS_PROBLEM_VALIDATED / SINGLE_PROBLEM / UNTESTED
- 科研迁移：DIRECTLY_TRANSFERABLE / NEEDS_ADAPTATION / COMPETITION_SPECIFIC

---

## ⚠️ 战略定位更新（2026-09-08）

### 核心对象收束

**MathModel 核心价值 = Model Construction（What）+ Model Representation（How）**，Harness（How do we know）是底座。

- **Model Construction = What**：Agent 能不能把现实问题构造成正确、完整、自洽、可求解、可验证的数学模型？（整条链核心，P15.2）
- **Model Representation = How**：Model IR / Model Graph / Model Trace / Model Diff（核心标准化对象，规范已交付 `research/P15/model_representation/`）
- **Harness = How do we know**：Freeze Input / Execution / Artifact / Evidence / Provenance / Replay / Evaluator（底座，保证可信）

### P15 更名重排为 "Competition Model Construction Program"

| 阶段 | 重点 | 能力维度 |
|---|---|---|
| P15.0 | Modeling Ontology + Benchmark Freeze | 本体 |
| P15.1 | Problem → Model Structure | Problem Understanding / Alignment |
| **P15.2** | **Model Construction（整条链核心）** | **Model Construction / Formal Consistency** |
| P15.3 | Formal Consistency | 数学自洽性 |
| P15.4 | Computational Solving | Solving |
| P15.5 | Validation | Validation / Sensitivity-Robustness |
| P15.6 | Model → Paper Transmission | Communication |
| P15.7 | Competition Model Construction Benchmark | 全维度 benchmark |

### 架构边界

- **Harness ≠ Agent**：core/runtime 永久 LLM-free，认知工作由外部 Agent 完成
- **External-Agent Execution Interface**：外部 Agent 通过 register_external_artifact.py 提交产物，executor_type=external_agent 才可评分
- **synthetic/dry_run 永不进能力结论**：DefaultNodeExecutor 是演练器，不是 Agent
- **Model IR 是能力测量的结构化基础**：所有 capability evaluator 最终应消费 Model IR，而非自由文本

---

## 0. 总览表

| # | Capability | Current Status | Confidence | Generalization | Research Transfer |
|---|---|---|---|---|---|
| 1 | Problem Understanding | UNMEASURED | LOW | UNTESTED | NEEDS_ADAPTATION |
| 2 | Problem Alignment | MEASURED | HIGH | CROSS_PROBLEM_VALIDATED | NEEDS_ADAPTATION |
| 3 | Model Construction | MEASURED | HIGH | CROSS_PROBLEM_VALIDATED | DIRECTLY_TRANSFERABLE |
| 4 | Formal Consistency | PARTIALLY_MEASURED | MEDIUM | SINGLE_PROBLEM | DIRECTLY_TRANSFERABLE |
| 5 | Method Selection | MEASURED | HIGH | CROSS_PROBLEM_VALIDATED | DIRECTLY_TRANSFERABLE |
| 6 | Solving | PARTIALLY_MEASURED | MEDIUM | CROSS_PROBLEM_VALIDATED | DIRECTLY_TRANSFERABLE |
| 7 | Validation | MEASURED | HIGH | CROSS_PROBLEM_VALIDATED | DIRECTLY_TRANSFERABLE |
| 8 | Sensitivity-Robustness | PARTIALLY_MEASURED | LOW | SINGLE_PROBLEM | DIRECTLY_TRANSFERABLE |
| 9 | Evidence | PARTIALLY_MEASURED | MEDIUM | SINGLE_PROBLEM | DIRECTLY_TRANSFERABLE |
| 10 | Claim Support | MEASUREMENT_INVALID | LOW | UNTESTED | DIRECTLY_TRANSFERABLE |
| 11 | Communication | MEASURED | MEDIUM | CROSS_PROBLEM_VALIDATED | NEEDS_ADAPTATION |

**测量覆盖率**：MEASURED 5/11（45%），PARTIALLY_MEASURED 3/11（27%），UNMEASURED 1/11（9%），MEASUREMENT_INVALID 1/11（9%）。

---

## 1. Problem Understanding（问题理解）

### Capability
正确解析题目文本、数据附件、隐含约束与交付要求。包括：识别题面中的显式/隐式条件、区分已知量与未知量、理解交付物格式要求。这是建模管线的入口，失败会污染所有下游能力的测量。

### Observable behavior
- 产出结构化的 problem_analysis artifact，包含题目类型、已知条件、隐含约束、交付要求
- 能指认题面中每个数字/参数的来源和物理意义
- 能识别题面中的歧义点并显式标注
- 交付物格式要求（如 result1.xlsx 模板、6 位小数）被正确提取

### Failure modes
- FM-PA-003 wrong_problem_interpretation（理解了文本但误解题意）
- FM-ME-003 empty_artifact_passing（problem_analysis 为空壳但通过门禁）

### Measurement instrument
- 当前：`problem-parser` agent（legacy）产出定性 artifact，**无独立量化 evaluator**
- 计划：基于 CUMCM-Bench `required_deliverables` + `key_constraints` 的提取命中率（deterministic checklist）
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Problem Understanding（待建立）

### Evidence type
- artifact（problem_analysis DTO）
- human judgment（题面逐条对照）

### Current status
**UNMEASURED**。legacy problem-parser 存在但产出无量化评分；P15.1 2024_A 的 Q001 空壳（payload=[]）暴露了解析失败，但该失败未被独立量化，仅作为下游 decomposition UNRESOLVED 的间接表现。

### Confidence
**LOW**。无量化仪器，当前仅有定性判断。

### Generalization status
**UNTESTED**。未在多题上系统测量 Problem Understanding 独立得分。

### Research transfer status
**NEEDS_ADAPTATION**。科研问题没有明确的子问题编号和交付物格式要求，需要从"提取题目给定条件"泛化为"从研究目标和文献中自发生成问题分解"。理解问题域、识别关键约束、确定研究范围是通用部分。

---

## 2. Problem Alignment（问题对齐）

### Capability
子问题分解覆盖率 + 题目要求→模型元素的强制映射。衡量模型是否回答了题目要求的每个子问题，每个对齐点是否在模型中有对应的变量/方程/约束承载。**注意：Alignment 测"是否回答了题目"，不测"回答得对不对"——后者属于 Model Construction 和 Formal Consistency。**

### Observable behavior
- 产出的子问题列表覆盖题目全部子问（count-ratio ≥ 阈值）
- 每个子问题能指认模型中承载它的具体变量/方程/约束（alignment_hit）
- 无"文字有映射、模型无通道"的虚对齐点
- 优化目标/估计量与题目要求一致

### Failure modes
- FM-PA-001 wrong_abstraction（问题类型/建模范式误判，如运动学→评价）
- FM-PA-002 wrong_objective（优化目标/估计量与题目要求不一致）
- FM-PA-003 wrong_problem_interpretation（题意误解导致对齐方向错误）

### Measurement instrument
- `e2e_metrics.py: decomposition_coverage`（produced 子问题 vs GT 子问题 count-ratio）
- `model_construction.py: alignment` 维度（alignment_hit 检查）
- CUMCM-Bench-v2 `sub_questions[]` 作为金标准（36 题）
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Problem Alignment

### Evidence type
- artifact（produced sub_questions list + model_construction 评分明细）
- run manifest（decomposition_coverage 数值）
- replay（子问题分解可重放）

### Current status
**MEASURED**。有 evaluator（decomposition_coverage + alignment 维度）+ benchmark（36 题 GT 子问题）+ evidence（P13-3C-R5：B0 alignment 9.3 vs B1 92.9；P15.1 2024_A：UNRESOLVED）。

### Confidence
**HIGH**。decomposition_coverage 是 deterministic 计数；alignment 维度有 rubric 支撑；多题多臂交叉验证。

### Generalization status
**CROSS_PROBLEM_VALIDATED**。P13-3C 3 题三 regime + R5 7 题均验证了 alignment 维度的区分度。

### Research transfer status
**NEEDS_ADAPTATION**。比赛 alignment = 覆盖题目子问（有 GT 可比对）；科研 alignment = 覆盖研究问题的各个方面 + 与文献对话（无 GT，需研究者自定研究目标）。测量方法需从"与金标准子问题比对"变为"与研究目标的逐条映射"。

---

## 3. Model Construction（模型构建）

### Capability
从问题到数学模型的完整构造：变量→参数→假设→目标→约束→机制→方程。衡量模型结构的完整性和机制选择的正确性。**这是整个 Harness 的质量上限决定因素**（P13-3D-R3 证明：Writer 无法补偿构件质量缺陷）。

### Observable behavior
- 所有关键变量已声明并区分类型（状态/决策/观测/常量）
- 所有参数已声明来源与取值
- 假设集显式、合理、可检验
- 目标函数明确且与题目一致
- 约束集完备（物理/工程/逻辑/边界）
- 机理选择与问题物理/现实一致（不是方法名正确但不适合）
- 方程结构完整

### Failure modes
- FM-MC-001 wrong_mechanism（机理选择错误，如用评价方法解动力学）
- FM-MC-002 wrong_causal_structure（因果方向错误、混淆相关与因果）
- FM-MC-003 wrong_constraints（约束方向错误/约束了错误的量）
- FM-MC-004 missing_variables（关键变量遗漏）

### Measurement instrument
- `model_construction.py`（structural + mathematical + alignment 三维评分）
- `model_construction_checklist.md`（7 类干预清单：校准/约束/不确定性/口径/声明/符号/主张-支持配对）
- P13-3C rubric（mc_2024A.json 等逐题评分标准）
- CUMCM-Bench `key_variables[]` + `key_constraints[]` 参考
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Model Construction + MODEL_CONSTRUCTION_RUBRIC L2

### Evidence type
- artifact（MODEL_ARTIFACT + rubric 扣分明细）
- run manifest（三维分数 + math_deductions 列表）
- human judgment（盲评交叉验证）
- replay（模型构造可重放）

### Current status
**MEASURED**。有 evaluator（model_construction.py 三维）+ benchmark（P13-3C rubric + CUMCM-Bench）+ 强 evidence（P13-3C：B1 93.9 > MMA 83.9 > B0 50.0；R5：B1 86.2 > MMA 69.5 > B0 37.1；P13-3B：math 55→95 干预）。

### Confidence
**HIGH**。多轮实验交叉验证；structural/mathematical/alignment 三维拆分已证明能区分不同失败类型；盲评与自评方向一致。

### Generalization status
**CROSS_PROBLEM_VALIDATED**。P13-3C 3 题三 regime（机理/数据/优化）+ R5 7 题扩展均验证了 Model Construction 评分的区分度。

### Research transfer status
**DIRECTLY_TRANSFERABLE**。从问题到数学模型的完整构造能力是通用科学建模能力。`model_construction_checklist.md` 的 7 类检查完全通用。科研中更强调机理的创新性和与已有模型的对话，但构造能力本身无需适配。

---

## 4. Formal Consistency（形式一致性）

### Capability
方程推导正确性、量纲一致、符号/索引/边界正确。衡量模型的数学形式是否自洽——**这是 Support Surface 的核心**（模型能兑现什么）。与 Model Construction 的区别：Model Construction 测"结构是否完整、机理是否选对"，Formal Consistency 测"已有的结构在数学上是否自洽"。

### Observable behavior
- 所有方程引用的参数已在 parameters 中声明
- 方程两边量纲一致（如米 + 秒不会出现）
- 符号使用一致（同一符号不表示不同量）
- 索引范围正确（无越界、无 off-by-one）
- 边界条件正确声明
- 约束方向正确（短缺变量不以正号进入上界）

### Failure modes
- FM-FC-001 dimension_inconsistency（量纲不一致）
- FM-FC-002 symbol_inconsistency（符号不一致/复用）
- FM-FC-003 unit_inconsistency（单位不一致，如 cm 与 m 混用）
- FM-FC-004 index_inconsistency（索引越界/off-by-one/步长口径错误）

### Measurement instrument
- `model_construction.py: mathematical` 维度（错误分类学扣分制：量纲/索引/符号/边界/校准/缺失约束/未陈述假设）
- 当前**无自动化形式一致性检查器**，依赖 rubric 人工/LLM 评分
- 计划：参数声明完备性 deterministic 检查（方程中出现的符号 ⊆ parameters 声明集）
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Formal Consistency

### Evidence type
- artifact（math_deductions 列表：tag/count/evidence）
- human judgment（量纲/符号需语义判断）
- run manifest（mathematical 维度分数）

### Current status
**PARTIALLY_MEASURED**。mathematical 维度覆盖了形式一致性，但：(1) 无自动化检查器，依赖语义评分；(2) 量纲检查未独立量化；(3) P13-3C-R4 暴露对齐干预可导致 math 暴跌（65→45），说明 mathematical 维度受上游污染，不完全独立。

### Confidence
**MEDIUM**。错误分类学扣分制有明确 rubric，但量纲/符号判断需要语义理解，存在评分者方差；无 deterministic 兜底。

### Generalization status
**SINGLE_PROBLEM**。mathematical 维度在 P13-3C 多题上使用，但形式一致性的独立测量（分离于 Model Construction）仅在 2024_A 等单题上有深度分析。

### Research transfer status
**DIRECTLY_TRANSFERABLE**。数学形式一致性是领域无关的。参数声明检查、量纲检查、符号方向检查在任何科研领域都适用。

---

## 5. Method Selection（方法选择）

### Capability
选择正确的模型家族（运动学/优化/统计/评价/机理…）和具体方法。**独立维度，不是 Problem Alignment 的代理**：Alignment 测"是否回答了题目"，Method Selection 测"选的工具是否适合问题类型"。一个模型可以 Alignment 很好（覆盖了所有子问）但 Method Selection 错误（用 TOPSIS 解运动学）。

### Observable behavior
- 选择的模型家族与题目 gold family 有交集
- 方法选择有明确依据（不是关键词匹配）
- 能区分"方法名正确"和"方法适合问题"
- 备选方法有对比分析

### Failure modes
- FM-MS-001 wrong_model_family（模型家族与问题类型不匹配）
- FM-MS-002 method_name_trap（方法名正确但不适合问题，如 TOPSIS 数学正确但用于运动学）

### Measurement instrument
- `e2e_metrics.py: method_selection`（top-3 GT hit，基于 CUMCM-Bench `core_methods[]` + `family[]`）
- `method-matcher` agent（legacy）+ 方法卡 retriever（53 个 methodology .md）
- **FAMILY_MISMATCH 二元判定**（计划）：selected_model.family ∩ gold_family = ∅ → 直接标记，此时 mathematical correctness 仅作参考
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Method Selection

### Evidence type
- artifact（selected_method 标签 + confidence score）
- run manifest（method_selection 百分比 + family mismatch flag）
- replay（方法选择可重放）

### Current status
**MEASURED**。有 evaluator（method_selection top-3 hit）+ benchmark（19 个家族标签 + core_methods）+ evidence（P15.1 2024_A：TOPSIS for kinematics，method_selection=0%；P13-1/P13-2 retriever 消融）。

### Confidence
**HIGH**。method_selection 是 deterministic 的标签匹配；family 标签有 36 题基准；P15.1 提供了教科书级的错配案例。

### Generalization status
**CROSS_PROBLEM_VALIDATED**。19 个家族覆盖 36 题，method_selection 在多题上可计算。

### Research transfer status
**DIRECTLY_TRANSFERABLE**。根据问题类型选择合适的建模范式是通用能力。科研中模型家族选择需要文献依据（不是"选对方法"而是"选择最适合研究问题的范式"），但选择正确性的判断逻辑通用。

---

## 6. Solving（求解）

### Capability
选择合适的求解算法（解析/数值/优化/模拟），处理可解性，代码执行确定性。包含两个子维度：(1) Solving Strategy——求解策略是否与模型口径匹配；(2) Computational Reliability——代码执行确定性、多 seed 稳定性、数值收敛。

### Observable behavior
- 求解算法与模型类型匹配（刚性 ODE 不用显式欧拉）
- 求解步长与参数口径一致（年率不按月复利）
- 代码可执行无崩溃
- 多 seed（≥5）结果可复现（replay match ≥ 95%）
- 数值结果收敛（网格收敛检验通过）
- 结果在物理合理范围内

### Failure modes
- FM-SV-001 infeasible_solution（模型不可解/求解器返回 infeasible）
- FM-SV-002 non_convergence（迭代不收敛/数值发散）
- FM-SV-003 numerical_instability（数值不稳定/多 seed 方差过大）

### Measurement instrument
- `e2e_metrics.py: experiment_validity`（multi_run≥5 + robustness tags + 执行成功率）
- P14 replay match（21/21 Execution replay match）
- env `code.random_seed=42`, `multi_run_count=5`
- **Solving Strategy 无独立 evaluator**（当前仅 qualitative）
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Solving

### Evidence type
- artifact（Execution artifact + code sha256）
- run manifest（执行日志 + 多 seed 方差 + replay match 率）
- replay（求解可重放，P14 已验证 21/21）

### Current status
**PARTIALLY_MEASURED**。Computational Reliability 子维度有完整测量（experiment_validity + replay match）；但 Solving Strategy 子维度（策略是否与模型匹配）无独立 evaluator，仅靠定性判断。P13-3C 2022_B B1 的"年率 g 按月复利"是策略层失败的真实案例，但无法被当前仪器自动捕获。

### Confidence
**MEDIUM**。Computational Reliability 部分 HIGH（deterministic 执行检查 + replay）；Solving Strategy 部分 LOW（无量化）。综合 MEDIUM。

### Generalization status
**CROSS_PROBLEM_VALIDATED**。experiment_validity 在 P14 6 spec / 21 execution 上验证；replay match 跨题可用。

### Research transfer status
**DIRECTLY_TRANSFERABLE**。求解策略选择和计算可靠性是通用科学计算能力。科研更强调可复现性和计算效率（可能需要 HPC），但方法论无需适配。

---

## 7. Validation（验证）

### Capability
模型验证充分性：对照基线、灵敏度分析、残差分析、交叉验证、极限检验。衡量"有没有做验证"和"验证是否针对正确的目标"。**与 Evidence 的区别**：Validation 测验证行为的充分性，Evidence 测验证结果是否支持结论。

### Observable behavior
- 至少 1 个对照基线（如零模型/随机基线/文献基准）
- 至少 1 个灵敏度分析（参数扰动下结论稳定性）
- 至少 1 个极限检验（边界条件/极端参数）
- 验证目标与模型主张对应（不是验证了错误的东西）
- 残差分析/交叉验证（如适用）

### Failure modes
- FM-VA-001 missing_validation（完全未做验证或验证类型不足）
- FM-VA-002 wrong_validation_target（验证了错误的目标，如做了灵敏度但扰动的是不敏感参数）
- FM-VA-003 overfitting（模型过拟合训练数据/验证集泄漏）

### Measurement instrument
- `e2e_metrics.py: experiment_validity` + `validation_reliability`（claims_supported/total）
- robustness tags 检查（验证类型存在性）
- CUMCM-Bench `evaluation_targets[]` 参考
- P14 Evidence→Claim 链（6 spec / 21 execution / 9 claim）
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Validation

### Evidence type
- artifact（Evidence artifact + robustness tags）
- run manifest（validation_reliability 分数 + evaluation_targets 覆盖率）
- human judgment（验证目标是否正确需语义判断）
- replay（验证实验可重放）

### Current status
**MEASURED**。有 evaluator（experiment_validity + validation_reliability）+ benchmark（evaluation_targets 36 题）+ evidence（P14：5 supported / 4 refuted；FM-VA-01 覆盖 29/36 题）。

### Confidence
**HIGH**。验证存在性是 deterministic 检查（robustness tags）；validation_reliability 有 P14 完整证据链支撑。

### Generalization status
**CROSS_PROBLEM_VALIDATED**。FM-VA-01 在 29/36 题上标注，说明验证测量跨题可用。

### Research transfer status
**DIRECTLY_TRANSFERABLE**。验证方法论（对照/灵敏度/极限/交叉验证）是通用科学方法。科研验证更严格（需要外部数据验证、与已有结果对比），但方法论无需适配。

---

## 8. Sensitivity-Robustness（敏感性-鲁棒性）

### Capability
参数扰动下的结论稳定性、鲁棒性边界、不确定性传播。衡量模型结论是否对参数选择敏感，以及不确定性是否从上游传播到下游。**与 Validation 的区别**：Validation 是 broader 的验证充分性，Sensitivity-Robustness 专门聚焦参数扰动和不确定性传播。

### Observable behavior
- 有明确的灵敏度分析计划（扰动范围、步长、参数选择依据）
- 扰动了敏感参数（不是只扰动不敏感参数）
- 不确定性从上游参数传播到下游结论（如 λ 锚区间传播至全部下游）
- 报告了鲁棒性边界（结论在什么参数范围内成立）
- 多 seed 下结论稳定

### Failure modes
- FM-VA-002 wrong_validation_target（灵敏度分析扰动了不敏感参数——与 Validation 共享）
- FM-MC-003 wrong_constraints（约束过紧导致鲁棒性虚假）

### Measurement instrument
- `e2e_metrics.py` robustness tags（验证类型存在性检查，**非质量评分**）
- P15 PRE_REG sensitivity plan（±20%, 10 steps, relative——默认配置）
- P13-3B 不确定性传播干预（λ 锚区间 [1.0545, 1.0727] 传播至下游）
- **无独立的灵敏度质量评分**（当前只检查"有没有做"，不检查"做得好不好"）
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Sensitivity-Robustness

### Evidence type
- artifact（sensitivity analysis 结果 + 弹性系数）
- run manifest（robustness tags + 扰动配置）
- human judgment（扰动参数选择是否合理需语义判断）

### Current status
**PARTIALLY_MEASURED**。有标签检查（robustness tags 检测灵敏度分析是否存在），但：(1) 无独立质量评分；(2) 不检查扰动参数是否敏感；(3) 不确定性传播的完整性无量化。P13-3B 证明了不确定性传播的重要性，但未形成标准化测量。

### Confidence
**LOW**。仅有存在性检查，无质量评估；±20% 默认配置是否适合所有题目未经验证。

### Generalization status
**SINGLE_PROBLEM**。灵敏度分析在 P13-3B（2000C）和 P14 上有深度案例，但跨题的标准化测量未建立。

### Research transfer status
**DIRECTLY_TRANSFERABLE**。参数扰动下的结论稳定性分析是通用科学方法。科研中不确定性量化（UQ）是独立领域，比比赛的 ±20% 扰动更复杂，但基础方法论通用。

---

## 9. Evidence（证据）

### Capability
结果可追溯到已验证的实验，每个数值有明确的来源（artifact / run / 参数配置）。衡量证据链的完整性和可追溯性——**这是 Claim Support 的前提**。与 Claim Support 的区别：Evidence 测"证据是否存在且可追溯"，Claim Support 测"证据是否支持主张"。

### Observable behavior
- 每个数值结果可追溯到具体的 Execution artifact（hash 链闭合）
- Evidence→Result→Execution→Spec 哈希链完整
- 证据类型明确（实验结果/文献/推导）
- 无合成证据（synthetic evidence）
- 随机种子固定，多 seed 结果有均值与标准差

### Failure modes
- FM-EV-002 missing_provenance（结果无法追溯到实验/来源不明）
- FM-EV-003 synthetic_evidence（伪造/合成的证据，非真实实验产出）

### Measurement instrument
- P14 `p14_integrity_gate.py`（G0–G7 门禁，Evidence Graph 闭合检查）
- hash_chain.verify_chain()（哈希链验证）
- Artifact Registry（状态真源）
- **P14 能力仍在 research/ 轨道，未迁入 core/evaluation/**
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Evidence

### Evidence type
- artifact（Evidence artifact + Result artifact + Execution artifact）
- run manifest（hash 链 + artifact registry 条目）
- replay（证据链可重放验证）

### Current status
**PARTIALLY_MEASURED**。P14 建立了完整的 6 实体链（Model→ExperimentSpec→Execution→Result→Evidence→Claim）和 integrity gate，但：(1) 仍在 research/ 轨道，未固化为 core evaluator；(2) P15 benchmark 未接入 Evidence 测量；(3) 仅在 P14 单实验上验证。

### Confidence
**MEDIUM**。P14 integrity gate 是 deterministic 的哈希链检查，设计严谨；但未跨题验证，未迁入核心。

### Generalization status
**SINGLE_PROBLEM**。P14 在单个实验（6 spec / 21 execution / 9 claim）上验证了 Evidence 链，未在多题上系统测量。

### Research transfer status
**DIRECTLY_TRANSFERABLE**。结果可追溯性是科学方法的基石。P14 的 6 实体链完全通用，是科研迁移的核心基础设施。

---

## 10. Claim Support（主张支撑）

### Capability
每个结论/主张必须有可追溯的 Evidence 支持，区分 supported / refuted / unresolved。衡量论文中的主张是否有证据支撑，证据是否与主张一致。**这是科研迁移的核心能力**——科研论文的核心就是 claim-evidence 对应关系。

### Observable behavior
- 每个 Claim 绑定 ≥1 条 Evidence
- Claim 判定为 supported 或 refuted（非 unresolved）
- 无 unsupported claim（论文结论与实验结果矛盾）
- Claim 类型与模型结构相容（不是大主张 + 弱支持）
- Claim-Support Gap 可量化（Claim Coverage − Support Coverage）

### Failure modes
- FM-EV-001 unsupported_claim（主张无证据支持或证据与主张矛盾）

### Measurement instrument
- P14 `p14_integrity_gate.py`（Claim 判定：supported/refuted/unresolved）
- `e2e_metrics.py: validation_reliability`（claims_supported/total）
- P13-3C Claim Coverage × Support Coverage 框架
- **P15 FM-CS-01/02/03 全部为空（0 题标注）**——benchmark 标注失效
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Claim Support

### Evidence type
- artifact（Claim artifact + Evidence artifact + 判定结果）
- human judgment（Claim-Evidence 对应需语义判断）
- run manifest（claims_supported/total 比率）

### Current status
**MEASUREMENT_INVALID**。P14 有完整的 Claim 判定能力（5 supported / 4 refuted / 0 unresolved），但 P15 benchmark 的 FM-CS 三类全部为 0 题标注——不是没有 Claim Support 失败，而是标注体系失效。evaluator 存在但 benchmark  annotation 无效，导致该能力在 P15 框架下无法被有效测量。

### Confidence
**LOW**。P14 evaluator 本身设计合理，但 P15 标注全空说明测量链路断裂；Claim-Evidence 对应需要语义判断，存在评分者方差。

### Generalization status
**UNTESTED**。P14 仅在单实验上验证 Claim 判定；未在多题上建立 Claim Support 的标准化测量。

### Research transfer status
**DIRECTLY_TRANSFERABLE**。claim-evidence 对应关系是科学方法的核心。P14 的 supported/refuted/unresolved 三分法直接可用，是科研迁移的最高优先级能力。

---

## 11. Communication（沟通/论文传输）

### Capability
模型构件到论文的结构传输、内容忠实度、无未授权变异。衡量模型→论文的传输质量——**不是论文写得好不好，而是论文是否忠实地承载了模型构件**。P13-3D-R3 证明：Writer 不能提升质量上限，但没有 Communication 模型无法交付。

### Observable behavior
- 模型构件（变量/方程/约束/结果）在论文中有对应章节
- 论文数值与 Result Artifact 一致（无未授权变异）
- 结构传输完整（STC ≥ 阈值）
- 无 critical mutation（模型结论在论文中被改变）
- 论文格式符合比赛规范

### Failure modes
- （当前无独立 FM 编号；论文传输失败归因为 F9 Paper transmission failure）
- FM-EV-001 unsupported_claim（论文主张无模型承载——与 Claim Support 共享）

### Measurement instrument
- P13-3D STC v2（Structure Transfer Coefficient，元素提及式）
- P13-3D Fidelity v2（内容忠实度）
- `r32_eval.py`（论文评估）
- Blind PQ（盲评论文质量）
- **STC v2 为元素提及式，不含组织质量维度**（已知缺陷，H13 FAIL 的根因）
- 引用：EVALUATOR_VALIDITY_PROTOCOL §Communication

### Evidence type
- artifact（论文 .tex/.pdf + MODEL_ARTIFACT）
- human judgment（Blind PQ 盲评）
- run manifest（STC/Fidelity 分数 + mutation log）

### Current status
**MEASURED**。有 evaluator（STC v2 + Fidelity v2 + Blind PQ）+ benchmark（P13-3D-R3 48 篇论文语料，8 题 × 3 arm × 2 condition）+ evidence（H13/H14 FAIL，ΔPQ=−0.01；arm 间 PQ 差 ~18 分）。

### Confidence
**MEDIUM**。STC/Fidelity 有量化分数，但 STC v2 已知为元素提及式（不含组织质量），测量有效性有限；Blind PQ 有评分者方差。P13-3D 的结论（映射无效果但无害）是 negative but informative。

### Generalization status
**CROSS_PROBLEM_VALIDATED**。48 篇论文覆盖 8 题，STC/Fidelity 跨题可计算。

### Research transfer status
**NEEDS_ADAPTATION**。比赛论文有固定结构（问题重述/假设/模型/求解/结果），科研论文结构不同（IMRAD）。但"模型构件到论文的忠实传输、无未授权变异"原则通用，需要适配论文结构模板。

---

## 附录 A：能力依赖关系

```
Problem Understanding (1)
  ↓ 输入：正确理解的问题
Problem Alignment (2) ─── Method Selection (5)  [并行：对齐方向 + 方法选择]
  ↓ 输入：对齐的子问题 + 选对的模型家族
Model Construction (3)
  ↓ 输入：构造好的模型结构
Formal Consistency (4)
  ↓ 输入：形式化一致的方程
Solving (6)
  ↓ 输入：可求解的模型
Validation (7) ─── Sensitivity-Robustness (8)  [验证 + 敏感性分析]
  ↓ 输入：验证结果
Evidence (9)
  ↓ 输入：可追溯的证据
Claim Support (10)
  ↓ 输入：有证据支撑的结论
Communication (11)
  输出：可审计的论文/报告
```

**关键依赖规则**：
- 前级失败会污染后级测量（如 Problem Alignment 失败时，Model Construction 的高分无意义）
- Method Selection 与 Problem Alignment 并行但独立：Alignment 失败时 Method Selection 可能正确（如正确识别了运动学但未分解子问题），反之亦然
- Claim Support 依赖 Evidence，Evidence 依赖 Validation，Validation 依赖 Solving——链式依赖

## 附录 B：与 legacy C0–C15 的映射

| 本能力 | legacy C 编号 | 说明 |
|---|---|---|
| Problem Understanding | C0 | 直接对应 |
| Problem Alignment | C1 + C2 | C1 对齐 + C2 子问题分解合并 |
| Model Construction | C3 + C4 + C5 | 变量/参数/假设 + 模型构造合并 |
| Formal Consistency | C6 | 直接对应 |
| Method Selection | C7 | 直接对应，提升为独立维度 |
| Solving | C9 + C10 | 求解策略 + 计算可靠性合并 |
| Validation | C11 | 直接对应 |
| Sensitivity-Robustness | C12 | 直接对应 |
| Evidence | （C14 的子部分） | 从 Claim Support 中分离出证据链完整性 |
| Claim Support | C13 + C14 | 结果解释 + 主张支撑合并 |
| Communication | C15 | 直接对应 |
| （未保留） | C8 | Cross-question Model Interface 降为 Model Construction 的子维度 |

## 附录 C：测量仪器有效性汇总

| 能力 | 测量仪器 | 类型 | 已知缺陷 |
|---|---|---|---|
| Problem Understanding | 无 | — | 完全缺失 |
| Problem Alignment | decomposition_coverage + alignment 维度 | deterministic + semantic | 空壳 artifact 导致 UNRESOLVED |
| Model Construction | model_construction.py 三维 | semantic + rubric | 对齐干预可污染 mathematical 维度 |
| Formal Consistency | mathematical 维度 | semantic | 无自动化检查器，量纲未独立量化 |
| Method Selection | method_selection top-3 hit | deterministic | 标签匹配不等于方法适合 |
| Solving | experiment_validity + replay | deterministic | Solving Strategy 无独立测量 |
| Validation | experiment_validity + validation_reliability | deterministic + semantic | FM-VA-01 定义过宽（81% 题标注） |
| Sensitivity-Robustness | robustness tags | deterministic（存在性） | 无质量评分，不检查参数敏感性 |
| Evidence | P14 integrity gate | deterministic（hash 链） | 未迁入 core，未跨题验证 |
| Claim Support | P14 Claim 判定 | semantic | P15 FM-CS 全空，标注失效 |
| Communication | STC v2 + Fidelity v2 | deterministic + semantic | STC 为元素提及式，不含组织质量 |

---

*本文件为 Phase 4 能力本体重建产出。所有 current_status 基于实际测量仪器有效性，不做乐观估计。*
