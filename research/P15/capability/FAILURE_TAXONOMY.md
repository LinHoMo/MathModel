# Failure Taxonomy — MathModel Harness 失败分类学

- 版本：v1.0（Phase 4 重建）
- 日期：2026-09-08
- 上游：`research/REPOSITORY_AUDIT/04_MODELING_CAPABILITY_AUDIT.md` §3（FM-PA/MC/FC/SV/VA/CS 审查）
- 原则：只包含可测量的 failure mode；每个 FM 必须满足 definition / observable evidence / counterexample / measurement rule
- 核心铁律：**Method correctness ≠ Model correctness**（FM-MS-002 method_name_trap 是教科书级案例）

---

## 0. 三类失败严格区分

| 类别 | 代号 | 定义 | 典型根因 | 修复方向 |
|---|---|---|---|---|
| **A. Agent Capability Failure** | A | Agent 真的不会——给定正确的输入、完整的 workflow、准确的指令，Agent 仍然产出错误 | 模型能力不足、推理缺陷、知识缺口 | 升级模型、增强知识卡、针对性训练 |
| **B. Workflow-Skill Failure** | B | Workflow 没让 Agent 做，或 skill 缺失/有缺陷——Agent 有能力但没有被要求执行 | 流程缺步骤、skill 指令不完整、门禁不检查 | 补 workflow 步骤、完善 skill、加门禁 |
| **C. Measurement-Evaluator Failure** | C | 尺子不准——不是 Agent 的问题，是 evaluator 本身有 bug、阈值不合理、或空壳 artifact 通过了检查 | evaluator bug、金标准错误、评分逻辑缺陷 | 修复 evaluator、交叉验证、人工抽检 |

**归因优先级**：必须从 C（尺子准不准）→ B（流程有没有让做）→ A（Agent 会不会）依次排查，不能跳过。看到低分直接归 A 是最常见的反模式。

---

## 1. 总览

| ID | Name | Category | Primary Class | Related Capability | Measurable? |
|---|---|---|---|---|---|
| FM-PA-001 | wrong_abstraction | Problem Alignment | A | Problem Alignment | Yes (semantic) |
| FM-PA-002 | wrong_objective | Problem Alignment | A | Problem Alignment | Yes (semantic) |
| FM-PA-003 | wrong_problem_interpretation | Problem Alignment | A | Problem Understanding | Yes (semantic) |
| FM-MC-001 | wrong_mechanism | Model Construction | A | Model Construction | Yes (deterministic + semantic) |
| FM-MC-002 | wrong_causal_structure | Model Construction | A | Model Construction | Yes (semantic) |
| FM-MC-003 | wrong_constraints | Model Construction | A+B | Model Construction | Yes (semantic) |
| FM-MC-004 | missing_variables | Model Construction | A+B | Model Construction | Yes (deterministic) |
| FM-FC-001 | dimension_inconsistency | Formal Consistency | A | Formal Consistency | Yes (deterministic + semantic) |
| FM-FC-002 | symbol_inconsistency | Formal Consistency | A | Formal Consistency | Yes (deterministic) |
| FM-FC-003 | unit_inconsistency | Formal Consistency | A | Formal Consistency | Yes (deterministic + semantic) |
| FM-FC-004 | index_inconsistency | Formal Consistency | A | Formal Consistency | Yes (deterministic) |
| FM-MS-001 | wrong_model_family | Method Compatibility Assessment | A | Method Compatibility Assessment | Yes (deterministic) |
| FM-MS-002 | method_name_trap | Method Compatibility Assessment | A | Method Compatibility Assessment | Yes (deterministic + semantic) |
| FM-SV-001 | infeasible_solution | Solving | A+B | Solving | Yes (deterministic) |
| FM-SV-002 | non_convergence | Solving | A+B | Solving | Yes (deterministic) |
| FM-SV-003 | numerical_instability | Solving | A+B | Solving | Yes (deterministic) |
| FM-VA-001 | missing_validation | Validation | B | Validation | Yes (deterministic) |
| FM-VA-002 | wrong_validation_target | Validation | A | Validation + Sensitivity | Yes (semantic) |
| FM-VA-003 | overfitting | Validation | A | Validation | Yes (deterministic + semantic) |
| FM-EV-001 | unsupported_claim | Evidence/Claim | A | Claim Support | Yes (semantic) |
| FM-EV-002 | missing_provenance | Evidence | B | Evidence | Yes (deterministic) |
| FM-EV-003 | synthetic_evidence | Evidence | A | Evidence | Yes (deterministic + semantic) |
| FM-ME-001 | evaluator_bug | Measurement-Evaluator | C | (all) | Yes (deterministic) |
| FM-ME-002 | threshold_manipulation | Measurement-Evaluator | C | (all) | Yes (deterministic) |
| FM-ME-003 | empty_artifact_passing | Measurement-Evaluator | C | (all) | Yes (deterministic) |

**总计**：25 个可测量 failure mode。A 类 16 个，B 类 2 个（另有 5 个 A+B 混合），C 类 3 个。

---

## 2. Problem Alignment Failures

### FM-PA-001 wrong_abstraction

- **Name**: Wrong Abstraction（抽象错误/问题类型误判）
- **Definition**: 将问题的数学类型/建模范式误判。例如将运动学/几何问题误分类为评价类问题，将机理问题误分类为数据驱动问题。抽象错误会导致整个 pipeline 方向错误，下游所有努力都建立在错误的范式上。
- **Observable evidence**:
  - type-classifier 输出的 problem_type 与题目 allowed_model_families 无交集
  - 选择的方法族（如 TOPSIS/AHP/PCA）与问题物理本质（如运动学方程）不匹配
  - 模型中没有与问题物理机制对应的方程结构
- **Counterexample**: 一个综合题同时包含评价和机理两个子问题，Agent 选择了评价方法处理评价子问题——这不是 wrong_abstraction，而是正确的分而治之。只有当整体范式误判时才是 FM-PA-001。
- **Measurement rule**: semantic。对比 type-classifier 输出的 problem_type / selected_method family 与 CUMCM-Bench `family[]` 金标准。若无交集 → FM-PA-001 = true。可部分自动化（family 标签匹配），但"综合题的子问题级判定"需语义判断。
- **Related capability**: Problem Alignment（CAP-02）
- **Research transferability**: DIRECTLY_TRANSFERABLE。科研中问题范式误判是常见的评审拒稿理由（如用统计方法处理机理问题）。
- **Class**: A（Agent 误判）。若 type-classifier skill 本身有缺陷则为 B，但误判行为本身是 Agent 输出。
- **Real example**: P15.1 2024_A B0：运动学题被 type-classifier 误分类为评价类，选择 TOPSIS，method_selection=0%。

### FM-PA-002 wrong_objective

- **Name**: Wrong Objective（目标错误）
- **Definition**: 优化目标/估计量/预测目标与题目要求不一致。例如题目要求"最小化成本"，模型优化"最大化产出"；题目要求"估计参数"，模型做了"假设检验"。目标错误不等于方法错误——方法可能正确但优化了错误的量。
- **Observable evidence**:
  - 模型的 objective function 与题目要求的交付目标不对应
  - 子问题要求的输出类型（数值/分类/排序）与模型输出类型不匹配
  - alignment_hit 检查中"目标对齐点"缺失
- **Counterexample**: 题目要求"最小化成本"，模型同时优化成本和质量（多目标），成本是其中一个目标——这不是 wrong_objective，而是多目标扩展。只有当题目要求的目标完全不在模型目标集中时才是 FM-PA-002。
- **Measurement rule**: semantic。对比模型 objective function 描述与题目 sub_questions 中的目标描述。需语义判断目标是否等价（如"最小化时间"和"最大化速度"在特定条件下等价）。
- **Related capability**: Problem Alignment（CAP-02）
- **Research transferability**: DIRECTLY_TRANSFERABLE。科研中研究问题与模型目标不匹配是常见问题。
- **Class**: A（Agent 设定了错误的目标）
- **Real example**: P13-3C 2022_B B0：四问对齐 0，目标函数完全偏离题目要求。

### FM-PA-003 wrong_problem_interpretation

- **Name**: Wrong Problem Interpretation（题意误解）
- **Definition**: Agent 正确读取了题面文本，但误解了题意。与 wrong_abstraction 的区别：wrong_abstraction 是范式级误判（运动学→评价），wrong_problem_interpretation 是语义级误读（如将"螺距 55cm"理解为"半径 55cm"，将"顺时针"理解为"逆时针"）。
- **Observable evidence**:
  - problem_analysis artifact 中的关键参数/条件与题面原文不一致
  - 模型中使用的参数值与题面给定值不符（且不是校准/假设的合理偏离）
  - 方向/顺序/时间范围等语义关键信息被颠倒
- **Counterexample**: Agent 对题面歧义点做了合理假设并显式标注——这不是误解，而是 assumption construction。只有当 Agent 认为自己理解正确但实际与题面矛盾时才是 FM-PA-003。
- **Measurement rule**: semantic。逐条对照 problem_analysis artifact 与题面原文（problem_statement.txt）。关键参数值、方向、时间范围、约束条件的一致性检查。可部分自动化（数值比对），语义判断需人工/LLM。
- **Related capability**: Problem Understanding（CAP-01）
- **Research transferability**: NEEDS_ADAPTATION。科研问题通常没有唯一"正确理解"，但"与文献/数据矛盾的理解"仍是可检测的失败。
- **Class**: A（Agent 理解错误）
- **Real example**: （待标注——当前 P15 benchmark 未独立标注此 FM，需 Input Authenticity Recovery 后系统检测）

---

## 3. Model Construction Failures

### FM-MC-001 wrong_mechanism

- **Name**: Wrong Mechanism（机理选择错误）
- **Definition**: 选择的机理/动态方程与问题物理/现实本质不一致。例如用静态评价方法（TOPSIS）处理连续动力学问题；用马尔可夫链处理确定性微分方程问题；用线性回归处理强非线性机理。**与 FM-MS-001 wrong_model_family 的区别**：wrong_model_family 是家族级标签不匹配（可 deterministic 检测），wrong_mechanism 是机理级语义错误（家族可能正确但具体机理选错，如在 ODE 家族中选了错误的方程形式）。
- **Observable evidence**:
  - 模型的控制方程与问题物理机制不对应
  - 家族标签可能正确（如都标为"微分方程"），但具体方程形式错误
  - 模型无法产生题目要求的动态行为（如振荡/扩散/传播）
- **Counterexample**: 对一个复杂问题使用简化机理（如用线性近似处理弱非线性问题）并显式讨论了近似误差——这不是 wrong_mechanism，而是合理简化。只有当机理与问题本质根本不相容时才是 FM-MC-001。
- **Measurement rule**: deterministic + semantic。第一步：family 标签匹配（detect wrong_model_family）。第二步：在正确家族内，检查控制方程是否能产生题目要求的行为类型（semantic）。P15.1 TOPSIS for kinematics 同时触发 FM-MS-001 和 FM-MC-001。
- **Related capability**: Model Construction（CAP-03）
- **Research transferability**: DIRECTLY_TRANSFERABLE。科研中机理选错是最常见的评审拒稿理由之一。
- **Class**: A（Agent 选择了错误的机理）
- **Real example**: P15.1 2024_A B0：TOPSIS for 运动学——方法本身数学正确，但机理完全错误。

### FM-MC-002 wrong_causal_structure

- **Name**: Wrong Causal Structure（因果结构错误）
- **Definition**: 因果方向错误、混淆相关与因果、将结果当原因。例如在传染病模型中把"感染人数增加"作为"治愈率提高"的原因（实际是反向）；在分类问题中标签极性定义与使用矛盾。
- **Observable evidence**:
  - 模型中的因果箭头方向与物理/逻辑常识相反
  - 变量定义为 A 但按 B 的方向使用（如 p_hat 定义为误报概率却按降序优先选择）
  - 反馈循环方向错误
- **Counterexample**: 相关性模型（如回归）不声称因果关系——这不是 wrong_causal_structure，而是非因果建模。只有当模型声称或隐含了错误的因果方向时才是 FM-MC-002。
- **Measurement rule**: semantic。检查模型中变量间的依赖关系方向是否与问题描述一致。需要理解变量的物理意义，无法纯 deterministic 检测。
- **Related capability**: Model Construction（CAP-03）
- **Research transferability**: DIRECTLY_TRANSFERABLE。因果推断是科研核心能力，因果结构错误是严重缺陷。
- **Class**: A（Agent 建立了错误的因果结构）
- **Real example**: P13-3C 2021_C B0：标签极性矛盾（p_hat 定义为误报概率却按降序优先）。

### FM-MC-003 wrong_constraints

- **Name**: Wrong Constraints（约束错误）
- **Definition**: 约束方向错误、约束了错误的量、或约束符号错误导致约束失效。例如短缺变量以正号进入上界约束（短缺越大约束越松）；将"≥"写成"≤"；约束了非关键变量而遗漏了关键约束。**与 FM-MC-004 missing_variables 的区别**：missing_variables 是变量完全没出现，wrong_constraints 是变量出现了但约束方向/对象错误。
- **Observable evidence**:
  - 约束不等式方向与物理/逻辑要求相反
  - 约束中变量的符号错误导致约束越松而非越紧
  - 约束了与问题无关的量
- **Counterexample**: 约束 intentionally relaxed（如松弛变量法）并显式说明——这不是 wrong_constraints，而是标准优化技术。只有当约束方向错误是无意的且导致模型失效时才是 FM-MC-003。
- **Measurement rule**: semantic。检查每个约束的方向、符号、变量是否与问题描述一致。符号方向可部分自动化（如检查短缺变量的系数符号），但需语义理解"哪个变量是短缺变量"。
- **Related capability**: Model Construction（CAP-03）
- **Research transferability**: DIRECTLY_TRANSFERABLE。约束建模是通用优化能力。
- **Class**: A+B。A：Agent 判断约束方向错误。B：model_construction_checklist §6"符号方向"如果未覆盖该场景则 workflow 有缺陷。
- **Real example**: P13-3C 2022_B B1：s_e 以正号进入发电上界（短缺越大约束越松）。

### FM-MC-004 missing_variables

- **Name**: Missing Variables（变量遗漏）
- **Definition**: 题目中的关键变量/参数未在模型中声明或使用。包括：状态变量遗漏、决策变量遗漏、关键参数未声明、边界条件变量缺失。**与 FM-MC-003 wrong_constraints 的区别**：missing_variables 是变量完全不存在，wrong_constraints 是变量存在但约束错误。
- **Observable evidence**:
  - CUMCM-Bench `key_variables[]` 中的变量不在模型 variables/parameters 声明中
  - 方程中引用了未声明的参数（undeclared parameter）
  - 题目明确要求的输出变量在模型中无对应
- **Counterexample**: 模型通过合理假设消去了某个变量（如稳态假设消去时间变量）并显式说明——这不是 missing_variables，而是模型降阶。只有当关键变量被无意遗漏时才是 FM-MC-004。
- **Measurement rule**: deterministic。对比 CUMCM-Bench `key_variables[]` 与模型 variables/parameters 声明集，计算缺失率。未声明参数检查：方程中出现的符号 ⊆ parameters 声明集？若不是 → missing_variables（或 FM-FC-002 symbol_inconsistency，取决于是否是同一符号的不同用法）。
- **Related capability**: Model Construction（CAP-03）
- **Research transferability**: DIRECTLY_TRANSFERABLE。变量识别是通用建模能力。
- **Class**: A+B。A：Agent 未能识别关键变量。B：workflow 无独立的 variable identification 步骤（C3 仅部分包含在 structural 维度中）。
- **Real example**: P13-3C 盲评实锤：B1 多题存在未声明参数（μ/ω/η/δ/φ/R0 等）。

---

## 4. Formal Consistency Failures

### FM-FC-001 dimension_inconsistency

- **Name**: Dimension Inconsistency（量纲不一致）
- **Definition**: 方程两边或加减项的物理量纲不一致。例如将长度（m）与时间（s）相加；将计数（无量纲）与质心坐标（m）相加；导数的量纲未正确传递。
- **Observable evidence**:
  - 方程中存在不同量纲的加减运算
  - 函数参数的量纲与函数定义不匹配
  - 导数/积分后量纲未正确更新
- **Counterexample**: 无量纲化后的方程（所有量已归一化）——这不是 dimension_inconsistency，而是标准操作。只有当未做无量纲化且量纲确实不一致时才是 FM-FC-001。
- **Measurement rule**: deterministic + semantic。第一步：为每个变量标注量纲（需语义理解物理意义）。第二步：检查方程中加减项的量纲是否一致（deterministic 树遍历）。当前无自动化量纲检查器，依赖 rubric 人工/LLM 评分。
- **Related capability**: Formal Consistency（CAP-04）
- **Research transferability**: DIRECTLY_TRANSFERABLE。量纲分析是通用科学方法。
- **Class**: A（Agent 推导时量纲出错）
- **Real example**: P13-3C 2021_C MMA：M1 计数与质心相加，量纲不一致。

### FM-FC-002 symbol_inconsistency

- **Name**: Symbol Inconsistency（符号不一致）
- **Definition**: 同一符号在模型不同位置表示不同的量；或不同符号表示同一个量但未说明等价关系；或符号在声明与使用中不一致（如声明 x∈[0,1] 但使用时 x 取负值）。
- **Observable evidence**:
  - 同一符号在不同方程中表示不同物理量
  - 参数声明中的符号与方程中使用的符号不匹配
  - 符号的域声明与实际使用范围矛盾
- **Counterexample**: 下标区分的同名符号（如 x_i 和 x_j 表示不同节点的同一物理量）——这不是 symbol_inconsistency，而是索引的正确使用。只有当无区分标记的同一符号表示不同量时才是 FM-FC-002。
- **Measurement rule**: deterministic。构建符号表（symbol → 定义/域/首次出现位置），检查同一符号是否有多个不兼容的定义。可自动化为符号引用一致性检查。
- **Related capability**: Formal Consistency（CAP-04）
- **Research transferability**: DIRECTLY_TRANSFERABLE。符号一致性是通用数学写作规范。
- **Class**: A（Agent 符号使用不一致）
- **Real example**: （常见于多子问题模型，子问题间复用符号但未重新声明）

### FM-FC-003 unit_inconsistency

- **Name**: Unit Inconsistency（单位不一致）
- **Definition**: 同一物理量使用不同单位且未换算。例如 cm 与 m 混用、小时与秒混用、百分比与小数混用。**与 FM-FC-001 dimension_inconsistency 的区别**：量纲不一致是不同物理量相加（m + s），单位不一致是同一物理量的不同单位未换算（cm + m，量纲都是长度但数值差 100 倍）。
- **Observable evidence**:
  - 题面给定参数单位（如 cm）与模型中使用的单位（如 m）不一致且无换算因子
  - 时间参数（小时）与时间步长（秒）混用
  - 百分比（55%）与小数（0.55）混用
- **Counterexample**: 显式标注了单位换算因子（如 "d = 30 cm = 0.3 m"）——这不是 unit_inconsistency，而是正确的单位处理。只有当未换算且导致数值错误时才是 FM-FC-003。
- **Measurement rule**: deterministic + semantic。提取每个参数的单位标注，检查同一物理量的单位是否一致。需语义理解"哪些量是同一物理量"。
- **Related capability**: Formal Consistency（CAP-04）
- **Research transferability**: DIRECTLY_TRANSFERABLE。单位一致性是通用工程/科学规范。
- **Class**: A（Agent 单位处理错误）
- **Real example**: 2024_A 题面参数为 cm（板长 341cm、螺距 55cm），速度为 m/s——若模型未做 cm→m 换算则触发此 FM。

### FM-FC-004 index_inconsistency

- **Name**: Index Inconsistency（索引不一致）
- **Definition**: 数组/序列索引越界、off-by-one 错误、索引范围与声明不一致、步长口径错误（如年率参数在月步长上按期复利）。**与 FM-SV-003 numerical_instability 的区别**：index_inconsistency 是形式化层面的索引错误（可能导致代码崩溃或逻辑错误），numerical_instability 是数值层面的不稳定。
- **Observable evidence**:
  - 索引超出声明的数组范围
  - 循环边界 off-by-one（如应迭代 N 次但迭代了 N-1 次）
  - 时间步长与参数时间口径不匹配（年率按月复利）
  - 子问题间索引用法不一致（Q1 用 0-indexed，Q2 用 1-indexed）
- **Counterexample**: 不同子问题使用不同索引约定但显式说明转换关系——这不是 index_inconsistency，而是合理的接口设计。只有当未说明且导致错误时才是 FM-FC-004。
- **Measurement rule**: deterministic。代码静态分析（索引范围检查）+ 模型声明中的索引范围比对。时间口径检查：参数的时间单位 vs 求解器的时间步长。
- **Related capability**: Formal Consistency（CAP-04）
- **Research transferability**: DIRECTLY_TRANSFERABLE。索引/口径一致性是通用计算规范。
- **Class**: A（Agent 索引/口径处理错误）
- **Real example**: P13-3C 2022_B B1：年率 g 按月复利（index_error / 口径不匹配）。

---

## 5. Method Compatibility Assessment Failures

### FM-MS-001 wrong_model_family

- **Name**: Wrong Model Family（模型家族错误）
- **Definition**: 选择的模型家族与题目 allowed_model_families 无交集。这是 family 标签级的确定性错误，不涉及家族内具体方法的正确性。**与 FM-MC-001 wrong_mechanism 的区别**：wrong_model_family 是标签级（detectable by string matching），wrong_mechanism 是机理级（需语义判断）。一个模型可能 family 标签正确但机理仍然错误（如在 ODE 家族中选了错误的方程形式）。
- **Observable evidence**:
  - selected_model.family ∩ CUMCM-Bench allowed_model_families = ∅
  - 方法卡 retriever 返回的 top-k 方法全部属于错误家族
- **Counterexample**: 综合题选择了多个家族中的一个（如综合题有机理和评价两个家族，选了评价家族处理评价子问题）——这不是 wrong_model_family，只要与 allowed_model_families 有交集即可。
- **Measurement rule**: deterministic。selected_model.family 与 allowed_model_families 的集合交集检查。FAMILY_MISMATCH = (intersection == ∅)。
- **Related capability**: Method Compatibility Assessment（CAP-05）
- **Research transferability**: DIRECTLY_TRANSFERABLE。模型家族选择是通用建模决策。
- **Class**: A（Agent 选择了错误的家族）。若 method-matcher skill 的检索逻辑有缺陷则为 B。
- **Real example**: P15.1 2024_A：选择评价族（TOPSIS/AHP/PCA），allowed_model_families = 几何运动/综合，无交集。

### FM-MS-002 method_name_trap

- **Name**: Method Name Trap（方法名陷阱）
- **Definition**: 方法本身在数学上完全正确（公式、计算、逻辑无误），但该方法不适合当前问题。**这是 Method correctness ≠ Model correctness 原则的核心体现**。与 wrong_model_family 的区别：wrong_model_family 是家族标签不匹配，method_name_trap 强调"方法名正确且数学正确，但问题错配"——即使家族标签碰巧匹配（如都标为"优化"），具体方法仍可能不适合。
- **Observable evidence**:
  - 方法的数学实现无错误（公式正确、计算可复现）
  - 但方法的假设前提与问题条件矛盾（如 TOPSIS 假设独立评价指标，但运动学问题的变量是时空耦合的）
  - 方法的输出类型与问题要求不匹配（如排序方法输出排名，但问题要求坐标数值）
  - method_selection 分数可能为 0%，但 mathematical correctness 分数可能很高
- **Counterexample**: 方法不适合但 Agent 显式说明了局限性并作为辅助方法使用（如用 TOPSIS 做方案初筛，再用机理模型精算）——这不是 method_name_trap，而是方法组合。只有当 Agent 将不适合的方法作为主方法且未意识到错配时才是 FM-MS-002。
- **Measurement rule**: deterministic + semantic。第一步：检查方法数学正确性（deterministic：公式可复现、代码可运行）。第二步：检查方法假设前提与问题条件的一致性（semantic）。关键判定：mathematically_valid = true AND problem_alignment = fail → method_name_trap = true。
- **Related capability**: Method Compatibility Assessment（CAP-05）
- **Research transferability**: DIRECTLY_TRANSFERABLE。"方法正确但不适合问题"是科研中最常见的方法论错误之一。
- **Class**: A（Agent 未能识别方法与问题的错配）
- **Real example**: P15.1 2024_A B0：TOPSIS 数学完全正确，但用于运动学问题 = 完全错配。method_selection=0%，但如果只看 mathematical correctness 可以得高分。

---

## 6. Solving Failures

### FM-SV-001 infeasible_solution

- **Name**: Infeasible Solution（不可行解）
- **Definition**: 模型在给定约束下无可行解，或求解器返回 infeasible。可能原因：约束过紧、约束矛盾、变量域设置错误。**与 FM-MC-003 wrong_constraints 的区别**：wrong_constraints 是约束建模错误（可能仍有可行解但解是错的），infeasible_solution 是求解结果层面的不可行（可能约束本身合理但组合后无可行域）。
- **Observable evidence**:
  - 求解器返回 status = infeasible / no solution found
  - 优化问题的可行域为空
  - 模型输出 NaN / 无结果
- **Counterexample**:  Agent 检测到不可行后主动放松约束并重新求解——这不是 infeasible_solution（最终有解），而是合理的约束松弛策略。只有当最终交付时模型仍不可行时才是 FM-SV-001。
- **Measurement rule**: deterministic。检查求解器返回状态、输出是否包含 NaN、可行域是否非空。
- **Related capability**: Solving（CAP-06）
- **Research transferability**: DIRECTLY_TRANSFERABLE。可行性分析是通用优化能力。
- **Class**: A+B。A：模型构造导致不可行（约束过紧/矛盾）。B：求解器配置错误（如容差设置过严）。
- **Real example**: （常见于约束过紧的优化问题）

### FM-SV-002 non_convergence

- **Name**: Non-Convergence（不收敛）
- **Definition**: 迭代求解算法在最大迭代次数内未收敛，或残差未降至阈值以下。包括：优化算法不收敛、ODE 求解器步长过小导致超时、固定点迭代发散。
- **Observable evidence**:
  - 求解器返回 max_iter_reached / did_not_converge
  - 残差曲线未趋于平稳
  - 结果随迭代次数持续变化（无稳定值）
- **Counterexample**: 收敛到局部最优（而非全局最优）——这不是 non_convergence，而是局部最优问题（属于 FM-MC-001 wrong_mechanism 或求解策略问题）。只有当迭代完全不收敛时才是 FM-SV-002。
- **Measurement rule**: deterministic。检查求解器收敛标志、残差序列、迭代次数 vs 最大迭代次数。
- **Related capability**: Solving（CAP-06）
- **Research transferability**: DIRECTLY_TRANSFERABLE。收敛性分析是通用数值计算能力。
- **Class**: A+B。A：模型刚性/病态导致不收敛。B：求解器选择不当（如刚性 ODE 用显式欧拉）。
- **Real example**: （常见于刚性 ODE / 病态优化问题）

### FM-SV-003 numerical_instability

- **Name**: Numerical Instability（数值不稳定）
- **Definition**: 数值结果对初始条件/参数/舍入误差过度敏感，多 seed 下方差过大，或出现非物理的振荡/发散。**与 FM-SV-002 non_convergence 的区别**：non_convergence 是迭代不收敛（算法层面），numerical_instability 是收敛结果的方差过大（数值层面）。
- **Observable evidence**:
  - 多 seed（≥5）结果的变异系数 CV > 阈值（如 10%）
  - 微小参数扰动导致结果跳变
  - 出现非物理值（如负的概率、负的密度）
  - replay match 率 < 95%
- **Counterexample**: 混沌系统对初始条件敏感（这是物理特性，不是数值错误）——若 Agent 显式识别为混沌并使用合适的集合方法，则不是 numerical_instability。只有当不稳定是数值方法导致而非系统物理特性时才是 FM-SV-003。
- **Measurement rule**: deterministic。多 seed 方差计算、replay match 率、结果物理合理性检查（如概率 ∈ [0,1]、密度 ≥ 0）。
- **Related capability**: Solving（CAP-06）
- **Research transferability**: DIRECTLY_TRANSFERABLE。数值稳定性是通用科学计算能力。
- **Class**: A+B。A：模型选择导致数值刚性。B：求解器/精度配置不当。
- **Real example**: P13-3C 2024_A B1：ε~N(0,σ²) 可产生 R<0，与 R≥0 边界冲突（数值不稳定 + 边界错误）。

---

## 7. Validation Failures

### FM-VA-001 missing_validation

- **Name**: Missing Validation（验证缺失）
- **Definition**: 完全未做验证，或验证类型不足（如只有灵敏度分析但无对照基线、无极限检验）。当前 P15 中此 FM 覆盖 29/36 题（81%），说明定义可能过宽——需细化为"验证类型不满足最小集"。
- **Observable evidence**:
  - robustness tags 中缺少 required validation types
  - 无对照基线（零模型/随机基线/文献基准）
  - 无灵敏度分析
  - 无极限检验/边界检验
- **Counterexample**: 解析解问题（有闭式解，数值验证即精确验证）——这不是 missing_validation，解析解本身就是最强验证。只有当既无解析解又无数值验证时才是 FM-VA-001。
- **Measurement rule**: deterministic。robustness tags 检查：是否包含 baseline + sensitivity + limit_test 三类中的至少阈值数量。当前 env 默认要求 multi_run≥5，但未明确要求验证类型最小集。
- **Related capability**: Validation（CAP-07）
- **Research transferability**: DIRECTLY_TRANSFERABLE。验证是通用科学方法。
- **Class**: B（primary）。Workflow 未强制要求验证类型最小集 → Agent 自然跳过。若 workflow 有要求但 Agent 未执行则为 A。
- **Real example**: P15 benchmark 中 29/36 题标注 FM-VA-01——大部分是 workflow 层面的验证要求不明确导致。

### FM-VA-002 wrong_validation_target

- **Name**: Wrong Validation Target（验证目标错误）
- **Definition**: 做了验证但验证了错误的目标。例如：做了灵敏度分析但扰动的是不敏感参数（结论自然"稳定"）；验证了模型内部一致性但未验证与题目的对应关系；用训练数据验证模型（过拟合的温床）。
- **Observable evidence**:
  - 灵敏度分析扰动的参数对结果无影响（弹性系数 ≈ 0）
  - 验证指标与模型主张不对应（主张"精度高"但验证的是"速度快"）
  - 验证集与训练集重叠
- **Counterexample**: 验证了非主要目标但作为辅助分析（如主要验证精度，辅助验证速度）——这不是 wrong_validation_target，而是补充验证。只有当主要主张缺乏对应验证时才是 FM-VA-002。
- **Measurement rule**: semantic。对比 validation_targets 与模型 claims/evaluation_targets。检查灵敏度分析的参数是否为敏感参数（弹性系数阈值）。需语义理解"模型主张什么"。
- **Related capability**: Validation（CAP-07）+ Sensitivity-Robustness（CAP-08）
- **Research transferability**: DIRECTLY_TRANSFERABLE。"验证了错误的东西"是科研常见问题。
- **Class**: A（Agent 选择了错误的验证目标）
- **Real example**: （构造案例：做了 ±20% 灵敏度分析但扰动的是 scale 参数，对结论无影响）

### FM-VA-003 overfitting

- **Name**: Overfitting（过拟合）
- **Definition**: 模型在训练/拟合数据上表现好但在未见数据上表现差，或模型参数过多导致拟合了噪声。包括：验证集泄漏、参数数量接近数据点数量、交叉验证 folds 不独立。
- **Observable evidence**:
  - 训练误差远小于验证误差
  - 参数数量 ≥ 数据点数量
  - 交叉验证 folds 间有数据泄漏
  - 模型对训练数据的微小扰动过度敏感
- **Counterexample**: 高维小样本问题使用了正则化/降维（如 PCA + 聚类）——这不是 overfitting，而是合理的复杂度控制。只有当未做正则化且模型明显拟合噪声时才是 FM-VA-003。
- **Measurement rule**: deterministic + semantic。训练/验证误差比、参数数量 vs 样本数量、交叉验证独立性检查。需语义判断模型复杂度是否合理。
- **Related capability**: Validation（CAP-07）
- **Research transferability**: DIRECTLY_TRANSFERABLE。过拟合是通用机器学习/统计建模问题。
- **Class**: A（Agent 未控制模型复杂度）
- **Real example**: 2022_C 古代玻璃制品：高维小样本（化学成分多但样本少），若不做 PCA/正则化则容易过拟合。

---

## 8. Evidence Failures

### FM-EV-001 unsupported_claim

- **Name**: Unsupported Claim（主张无支撑）
- **Definition**: 论文/模型中的结论性主张没有可追溯的 Evidence 支持，或证据与主张矛盾。包括：大主张 + 弱支持（Claim Coverage >> Support Coverage）、论文结论与实验结果矛盾、主张类型与模型结构不相容。
- **Observable evidence**:
  - Claim 未绑定任何 Evidence artifact
  - Evidence 与 Claim 矛盾（实验结果不支持结论）
  - Claim-Support Gap > 阈值（Claim Coverage − Support Coverage 过大）
  - 论文中出现"模型表明 X"但模型中无生成 X 的机制
- **Counterexample**: 推测性主张明确标注为"假设"或"未来工作"——这不是 unsupported_claim，而是合理的讨论。只有当 Agent 将其作为已验证结论陈述时才是 FM-EV-001。
- **Measurement rule**: semantic。Claim-Evidence 对应关系检查：每个 Claim 是否有 ≥1 条支持性 Evidence？Evidence 是否与 Claim 一致？需语义理解主张内容和证据含义。P14 的 supported/refuted/unresolved 三分法可自动化部分流程。
- **Related capability**: Claim Support（CAP-10）
- **Research transferability**: DIRECTLY_TRANSFERABLE。claim-evidence 对应是科研论文的核心。
- **Class**: A（Agent 提出了无证据支撑的主张）
- **Real example**: P13-3C-R4 B1-A：对齐干预扩大了主张面但支持面未跟上，math 暴跌 65→45，major 缺陷 4→6。P14：4 条 refuted claim。

### FM-EV-002 missing_provenance

- **Name**: Missing Provenance（来源缺失）
- **Definition**: 结果/数值无法追溯到具体的实验执行、参数配置或数据源。包括：论文中数值无法在 Result Artifact 中找到、参数值无来源说明、哈希链断裂。
- **Observable evidence**:
  - 论文中的数值在 all_results.json 中无对应条目
  - 参数值无来源（题面/校准/文献/假设）
  - hash_chain.verify_chain() == False
  - Artifact Registry 中无对应条目
- **Counterexample**: 常识性常量（如 π、g=9.8）无需追溯来源——这不是 missing_provenance，而是标准常量。只有当非常量数值无来源时才是 FM-EV-002。
- **Measurement rule**: deterministic。哈希链验证、Artifact Registry 条目检查、论文数值与 Result Artifact 的比对（数值匹配 + 容差）。
- **Related capability**: Evidence（CAP-09）
- **Research transferability**: DIRECTLY_TRANSFERABLE。可追溯性是科研诚信的基础。
- **Class**: B（primary）。Workflow 未强制要求 provenance tracking → 数值自然无来源。若 workflow 有要求但 Agent 未记录则为 A。
- **Real example**: P15.1 2024_A：Q001 空壳 payload=[]，结果无法追溯到任何执行。

### FM-EV-003 synthetic_evidence

- **Name**: Synthetic Evidence（合成证据/伪造证据）
- **Definition**: 证据不是真实实验产出，而是人工合成/编造/修改的。包括：直接编造数值、修改实验结果使其符合预期、用其他实验的结果冒充当前实验的结果。**这是最严重的失败类别**——涉及学术诚信。
- **Observable evidence**:
  - Result Artifact 中的数值无法通过 replay 复现
  - 代码执行结果与报告结果不一致
  - 证据的时间戳/哈希与执行记录矛盾
  - 多 seed 结果完全一致（无方差，可疑）
- **Counterexample**: 合成数据用于测试（如 mock data for unit test）并明确标注——这不是 synthetic_evidence，而是合理的测试实践。只有当合成数据被冒充为真实实验结果时才是 FM-EV-003。
- **Measurement rule**: deterministic + semantic。replay 复现检查（执行代码 → 比对结果）、哈希链验证、多 seed 方差检查（方差为 0 可疑但不充分）。需结合多种检测手段。
- **Related capability**: Evidence（CAP-09）
- **Research transferability**: DIRECTLY_TRANSFERABLE。学术诚信是通用原则。
- **Class**: A（Agent 故意或无意地生成了非真实证据）
- **Real example**: （当前仓库未发现确认案例，但 P14 的 replay match 机制就是为了检测此类失败）

---

## 9. Measurement-Evaluator Failures（C 类——尺子不准）

### FM-ME-001 evaluator_bug

- **Name**: Evaluator Bug（评测工具缺陷）
- **Definition**: Evaluator 本身有代码 bug、逻辑错误或金标准错误，导致评分不可信。这不是 Agent 的问题——是尺子本身不准。
- **Observable evidence**:
  - Evaluator 对已知正确的输入返回错误评分
  - Evaluator 崩溃或返回 NaN
  - 同一输入多次运行评分不一致（非确定性）
  - 金标准（CUMCM-Bench 标签）本身有错误
- **Counterexample**: Evaluator 评分与人工判断不一致但人工判断有误——这不是 evaluator_bug，而是需要复核。只有当 evaluator 的逻辑/代码确有错误时才是 FM-ME-001。
- **Measurement rule**: deterministic。单元测试（对已知输入断言预期输出）、复现评测、交叉验证（多 evaluator 对比）、人工抽检。
- **Related capability**: （所有能力——evaluator 失效影响所有测量）
- **Research transferability**: N/A（这是测量基础设施问题，不是建模能力）
- **Class**: C（尺子不准）
- **Real example**: P15.1 2024_A：decomposition_coverage = UNRESOLVED——不是 Agent 未分解，而是 evaluator 无法从空壳 artifact 中提取子问题（evaluator gap）。

### FM-ME-002 threshold_manipulation

- **Name**: Threshold Manipulation（阈值操纵）
- **Definition**: Evaluator 的通过阈值被设置得不合理（过松或过严），导致评分失去区分度。包括：阈值设为 0（一切通过）、阈值设为 100（一切失败）、阈值根据已知结果反向调整（post-hoc thresholding）。
- **Observable evidence**:
  - 所有被测对象全部 PASS 或全部 FAIL（无区分度）
  - 阈值在看到结果后被修改
  - 阈值与 env/config.yaml 中的声明不一致
- **Counterexample**: 阈值根据预实验校准（在看到正式结果之前确定）——这不是 threshold_manipulation，而是合理的阈值校准。只有当阈值在看到结果后反向调整时才是 FM-ME-002。
- **Measurement rule**: deterministic。检查阈值配置的 git history（是否在结果产出后修改）、评分分布（全 PASS/全 FAIL 可疑）、阈值与 env 声明的一致性。
- **Related capability**: （所有能力）
- **Research transferability**: N/A
- **Class**: C（尺子刻度被篡改）
- **Real example**: （当前仓库未发现确认案例，但 P13-3C 的 difficulty 标签必须前置锁定就是为了防止此类问题）

### FM-ME-003 empty_artifact_passing

- **Name**: Empty Artifact Passing（空壳产物通过）
- **Definition**: Evaluator 接受了空壳/无实质内容的 artifact 并给出非零评分。例如：problem_analysis 为 Q001 空壳（payload=[]）但 evaluator 未检测到；MODEL_ARTIFACT 中 variables=[] 但 structural 分数 > 0。
- **Observable evidence**:
  - Artifact 的核心字段为空（payload=[]、variables=[]、equations=[]）
  - 但 evaluator 给出了 > 0 的分数
  - 或 evaluator 直接跳过该 artifact（标记为 n/a 而非 FAIL）
- **Counterexample**: Artifact  intentionally minimal（如纯解析问题无需数值结果）——这不是 empty_artifact，而是合理的精简。只有当 artifact 缺少题目要求的核心内容时才是 FM-ME-003。
- **Measurement rule**: deterministic。Artifact 非空检查：核心字段（sub_questions、variables、equations、results）的长度 > 0。若为空但评分 > 0 → FM-ME-003 = true。
- **Related capability**: （所有能力——空壳产物污染所有下游测量）
- **Research transferability**: N/A
- **Class**: C（尺子无法识别空壳）
- **Real example**: P15.1 2024_A：Q001 空壳 payload=[]，decomposition_coverage = UNRESOLVED（evaluator 无法处理空壳，既不 PASS 也不 FAIL，而是 UNRESOLVED——这本身就是 evaluator 缺陷）。

---

## 10. 与旧 P15 Taxonomy 的映射

| 旧 FM | 旧名称 | 新 FM | 变化说明 |
|---|---|---|---|
| FM-PA-01 | （未明确） | FM-PA-003 | 重新定义为 wrong_problem_interpretation |
| FM-PA-02 | 子问题分解失败 | FM-PA-001 + FM-PA-002 | 拆分为 wrong_abstraction 和 wrong_objective |
| FM-PA-03 | （空） | — | 旧定义不可测量，移除 |
| FM-MC-01 | （未明确） | FM-MC-004 | 重新定义为 missing_variables |
| FM-MC-02 | （未明确） | FM-MC-002 | 重新定义为 wrong_causal_structure |
| FM-MC-03 | 模型结构不完整 | FM-MC-001 + FM-MC-004 | 拆分为 wrong_mechanism 和 missing_variables |
| FM-MC-04 | 约束缺失 | FM-MC-003 | 重新定义为 wrong_constraints（含方向错误） |
| FM-MC-05 | （空） | — | 旧定义不可测量，移除 |
| FM-FC-01 | 形式不一致 | FM-FC-001 + FM-FC-002 | 拆分为 dimension 和 symbol |
| FM-FC-02 | （未明确） | FM-FC-004 | 重新定义为 index_inconsistency |
| FM-FC-03 | （未明确） | FM-FC-003 | 重新定义为 unit_inconsistency |
| FM-FC-04 | （空） | — | 旧定义不可测量，移除 |
| FM-SV-01 | 求解失败 | FM-SV-001 | 保留，精确定义为 infeasible_solution |
| FM-SV-02 | 数值发散 | FM-SV-002 + FM-SV-003 | 拆分为 non_convergence 和 numerical_instability |
| FM-SV-03 | （空） | — | 旧定义不可测量，移除 |
| FM-VA-01 | 验证不充分 | FM-VA-001 | 保留，需细化验证类型最小集 |
| FM-VA-02 | （未明确） | FM-VA-002 | 重新定义为 wrong_validation_target |
| FM-VA-03 | （空） | FM-VA-003 | 新增 overfitting |
| FM-VA-04 | （未明确） | — | 合并入 FM-VA-001 |
| FM-CS-01/02/03 | （全空） | FM-EV-001 | 重新定义为 unsupported_claim，接入 P14 Claim 判定 |

**关键变化**：
1. 新增 Method Compatibility Assessment 独立类别（FM-MS-001/002），体现 Method correctness ≠ Model correctness
2. 新增 Measurement-Evaluator 类别（FM-ME-001/002/003），严格区分 C 类失败
3. 旧 7 个空 FM（PA-03, MC-05, FC-04, SV-03, VA-03, CS-01/02/03）全部移除或重新定义
4. 所有 FM 均有明确的 measurement rule（deterministic 或 semantic），无不可测量的 FM
5. 每个 FM 标注了 A/B/C 分类，归因从"Agent 不行"变为"先查尺子、再查流程、最后查 Agent"

---

## 11. 归因决策树

```
观察到失败/低分
  │
  ├─ C1: Evaluator 是否能正确处理该 artifact？
  │    ├─ 否（空壳/崩溃/UNRESOLVED）→ FM-ME-001/003（C 类）
  │    └─ 是 ↓
  │
  ├─ C2: 阈值是否合理（有区分度、前置锁定）？
  │    ├─ 否（全 PASS/全 FAIL/post-hoc）→ FM-ME-002（C 类）
  │    └─ 是 ↓
  │
  ├─ B1: Workflow 是否要求了该步骤？
  │    ├─ 否（无 validation 步骤、无 variable ID 步骤）→ B 类 Workflow-Skill Failure
  │    └─ 是 ↓
  │
  ├─ B2: Skill 指令是否完整覆盖该场景？
  │    ├─ 否（checklist 未覆盖约束方向）→ B 类（需补 skill）
  │    └─ 是 ↓
  │
  └─ A: Agent 在正确输入+完整流程+准确指令下仍失败 → A 类 Agent Capability Failure
```

**铁律**：不得跳过 C1/C2/B1/B2 直接归 A。看到低分就说"Agent 不行"是最常见的归因反模式。

---

*本文件为 Phase 4 失败分类学重建产出。所有 FM 均可测量（deterministic 或 semantic），无空壳 FM。*
