# P15 Benchmark & Evaluator 深度审计报告

- **审计员**: Benchmark & Evaluator Auditor
- **审计日期**: 2026-09-08
- **审计范围**: P15 Benchmark 体系（CUMCM-Bench-v2、P15.1 B0 baseline、evaluator、workflow）
- **审计模式**: 只读（Phase A OBSERVE），未修改任何仓库文件
- **核心结论**: **当前测量仪器不可靠。B0 "运行"是 0.06 秒的模板初始化，非真实 agent 执行；输入题面与 gold standard 不匹配；evaluator 只能测量元数据而非内容。暂停能力训练，先修测量仪器。**

---

## 1. 2024_A B0 深度复盘（Root-Cause Decomposition）

### 1.1 观测事实

| 指标 | 观测值 | 来源 |
|---|---|---|
| decomposition_coverage | UNRESOLVED | `research/P15/reports/P15.1-2024A-B0.md` §4 |
| count-ratio (diagnostic) | 20% (1/5) | 同上 |
| method_selection | 0% (TOPSIS, wrong family) | 同上 §4 |
| DAG nodes completed | 16/16 | `p151-2024a-run.json` |
| Registry artifacts | 16 total, 1 question (Q001) | 同上 |
| Run latency | **0.06 秒** | `state/runs/5c98cd9911bc.json` |
| model_provider | **null** | 同上 |
| skill_version | **e3b0c44...（空字符串 SHA256）** | 同上 |
| token_cost | null | 同上 |

### 1.2 关键证据链

#### 证据 A：B0 "运行"不是真实 agent 执行

`state/runs/5c98cd9911bc.json` 显示：
- `latency.seconds = 0.06`——16 个 DAG 节点在 60 毫秒内"完成"
- `model_provider = null`，`model_version = null`，`token_cost = null`——没有调用任何 LLM
- `skill_version = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`——这是**空字符串的 SHA256**，意味着没有加载任何 skill 指令

`work/STATE.md` 显示 V2 进度为 **0/29（0%）**，"已完成：（无）"，当前 agent 停留在 `problem-parser`。`work/handoff.md` 同样显示"已完成步骤：（无）"。

**结论**：B0 是一次模板初始化 / dry-run，注册了 16 个空壳 artifact（payload=[]，data={}），但没有任何真实的 agent 推理、方法选型或建模执行。所谓"TOPSIS 方法选择"和"evaluation 分类"是模板默认值或方法卡推荐系统的确定性输出，**不是 agent 的真实决策**。

#### 证据 B：输入题面与 Gold Standard 不匹配

Gold standard（`CUMCM-Bench-v2.json` 2024_A 条目）描述：
- 标题："板凳龙"闹元宵
- family：几何运动 / 综合
- 5 个子问题：300s 坐标、碰撞检测、最小螺距、螺距变化方案、速度控制
- core_methods：kinematics, geometric_modeling, numerical_solution

但实际输入文件 `examples/problems/cumcm2024A.txt`（以及 `projects/p151-2024a/inputs/cumcm2024A.txt`）的内容是：
- 标题：某防空导弹拦截弹道目标的最优制导律设计
- 5 个子问题：六自由度模型、比例导引律、EKF 状态估计、最优制导律优化、蒙特卡洛仿真
- 这是一个完全不同的题目（控制/ODE/估计类）

Hash 验证：run manifest 记录 `text_sha256 = 90a3026e...`，与实际文件 hash **匹配**。这意味着 pipeline 确实收到了导弹题，而非板凳龙题。但 `content_hashes.json` 中 2024_A = `7b86fddb...`——这是 benchmark JSON 条目的内容 hash（由 `duplicate_gate.py` 计算），**不是输入文本的 hash**。两个 hash 指代不同对象，且**没有任何校验机制将输入文本 hash 与 benchmark 条目关联**。

`core/knowledge/problems/CUMCM-Bench.json` 中 2024_A 条目正确记录了 title="板凳龙"、topic_type="A-physical"、reference_results（q1_300s_head_pos 等），但 `examples/problems/cumcm2024A.txt` 的内容与该条目完全不符。

**结论**：存在 **input representation failure**——输入文件被错误的题面内容污染，且 benchmark 体系缺乏输入文本与题目标签的一致性校验。

#### 证据 C：Q001 是空壳，由 session 创建而非 problem_analysis

`state/registry.json` 中 Q001：
- `created_by = "session"`（不是 `problem_analysis` 或 `analyst`）
- `payload = []`，`data = {}`
- `title = "Q001"`（无实际问题描述）

`core/roles/analyst.yaml` 定义 analyst 角色具备 `question-decomposition` 能力，执行 `problem_analysis` 和 `literature_search`。但 Q001 由 session 创建，说明 **problem_analysis 节点从未实际执行子问题分解**。

P001（problem artifact）同样 `payload=[]`，`data={}`，`created_by="problem_analysis"`——即使 problem_analysis 创建了 P001，也没有填充任何内容。

#### 证据 D：所有 artifact 均为空壳

遍历 registry.json 中 16 个 artifact：
- A001/A002（assumption）：payload=[]，data={}
- C001（claim）：payload=[]，data 仅有 statement="Q001 结论"（模板文本）
- D001（decision）：payload=["mc-topsis","mc-ahp","mc-pca"]，data 包含方法卡推荐评分（fit=38, data=15...）——这是方法卡检索系统的确定性输出
- D002（decision）：包含 8 个实验计划条目（E-Q001-01 至 08），全部是 TOPSIS 方法卡的模板化实验要求
- E001（experiment）：payload=[]，data 仅有 card_id="mc-topsis"
- M001（model）：payload=[]，data 仅有 card_id="mc-topsis", family="composite_evaluation"
- R001（result）：payload=[]，data 仅有 card_id="mc-topsis"
- S001-S005（paper_section）：payload 仅为章节标题字符串（"问题重述与分析"等），无正文内容

**结论**：16 个 artifact 中没有任何一个包含实际的建模内容、数学公式、数值结果或分析文本。这是一次完整的"元数据注册"，而非"建模执行"。

#### 证据 E：quality_report 不可靠

`state/quality_report.json` 给出 `overall_status = "WEAK"`，但：
- problem 维度：PASS（findings=[]）——尽管 P001 是空壳
- model 维度：PASS（findings=[]）——尽管 M001 是空壳且方法族完全错误
- experiment 维度：PASS（findings=[]）——尽管 E001 是空壳
- 仅 evidence 维度：WEAK（claim 未记录对照物）

quality gate 只能检测结构化元数据的缺失（如 claim 的 compared_against 字段），**无法检测内容空洞或方法族错误**。

### 1.3 Root-Cause 判定

逐一判断七个假设：

| 假设 | 判定 | 证据 |
|---|---|---|
| **Agent capability failure** | **不成立（当前无法测量）** | B0 未真实执行 agent（0.06s, model_provider=null）。TOPSIS 选择是模板默认值，不是 agent 决策。无法从本次运行得出任何关于 agent 能力的结论。 |
| **Workflow failure** | **成立（主要根因）** | V3 DAG 16 节点全部"完成"但无实际内容。problem_analysis 节点未执行子问题分解（Q001 由 session 创建）。workflow 缺乏"非空 artifact"校验，允许空壳通过。V2 状态显示 0/29，V3 状态显示 Q001 validated——两套状态系统不一致。 |
| **Problem-analysis skill failure** | **不成立（未被调用）** | analyst 角色定义了 question-decomposition 能力，但 skill_version=空字符串 hash，说明 skill 未被加载执行。不是 skill 本身失败，而是没有被调用。 |
| **Evaluator limitation** | **成立（关键根因）** | e2e_metrics.py 的 decomposition_coverage 在无语义评分时退化为 count-ratio（20%），无法区分"未分解"和"分解错误"。method_selection 仅做 top-3 方法卡 ID 字符串匹配，不评估方法是否适用于题目。model_correctness 完全依赖外部 rubric 输入（本次为 n/a）。没有任何 evaluator 检测 artifact 内容是否为空。 |
| **Problem classifier failure** | **不成立（未被调用 / 输入错误）** | decision_log 显示 question_type="evaluation"，但这是方法卡推荐系统基于空输入的默认分类，不是真实 classifier 的输出。且输入本身是导弹题（即使 classifier 正常工作，也应该分类为 A-physical/ODE，而非 evaluation）。 |
| **Input representation failure** | **成立（严重根因）** | `examples/problems/cumcm2024A.txt` 包含导弹制导题而非板凳龙题。benchmark 体系缺乏输入文本 hash 与题目标签的一致性校验。content_hashes.json 记录的是 benchmark JSON 条目 hash，不是输入文本 hash，两者无关联校验。 |
| **Benchmark annotation failure** | **部分成立** | Gold standard 本身（板凳龙的 5 个子问题、kinematics 方法族）与 `CUMCM-Bench.json` 和 playbook 一致，标注质量可接受。但 gold standard 与实际输入不匹配这一事实未被任何 gate 检测到。此外，core_methods 字段的表述方式（"kinematics, geometric_modeling, numerical_solution"）容易被 evaluator 当作"唯一正确方法"而非"参考方法族"。 |

### 1.4 Root-Cause 结论

**2024_A B0 的三个观测指标（UNRESOLVED / 20% / wrong family）不能归因于"Harness 的 Alignment 很差"。** 真实根因按严重程度排序：

1. **输入污染（P0）**：输入文件是错误的题目（导弹制导 ≠ 板凳龙），且无一致性校验。这意味着 B0 baseline 的输入本身就不可信。
2. **未真实执行（P0）**：B0 是 0.06 秒的模板初始化，没有调用 LLM，没有加载 skill，没有产生任何实际内容。所有"观测值"都是模板元数据的投影，不是 agent 行为的测量。
3. **Evaluator 无法测量内容（P1）**：现有 evaluator 只能计数 artifact 数量、匹配方法卡 ID 字符串、检查结构化字段是否存在，无法判断 artifact 内容是否为空、方法是否适用于题目、模型是否回答了问题。
4. **Workflow 缺乏非空校验（P1）**：DAG 节点可以注册空壳 artifact 并标记为"完成"，没有任何 gate 阻止空内容向下游传播。

**因此，当前 B0 baseline 不具备任何测量效力。在修复输入、确保真实执行、升级 evaluator 之前，任何基于 B0 的能力结论都是无效的。**

---

## 2. P15 Benchmark Schema Audit

### 2.1 Schema 结构

`CUMCM-Bench-v2.json` 包含 36 个 problem（2015-2025），每题 9 个字段：
`question_id, year, family, sub_questions, required_deliverables, core_methods, key_variables, key_constraints, evaluation_targets` + `capability_dimensions` + `failure_modes` + `rationale`。

P15.0 有 4 个 gate 脚本（`research/P15/scripts/`）：
- `validate_schema.py`：检查必填字段存在性 + capability_dimensions 枚举值 + failure_modes 格式
- `benchmark_completeness.py`：检查 8 个 gold 字段非空
- `coverage_report.py`：family 覆盖 + failure-mode 类别覆盖
- `duplicate_gate.py`：question_id 去重 + 生成 content_hashes.json（hash 的是 benchmark JSON 条目，不是输入文本）

### 2.2 逐问题审计发现

#### 2.2.1 Gold Leakage / Solution-Method Leakage

**core_methods 字段存在方法泄露风险。** 例如：
- 2018_A：`["heat_equation_PDE", "parameter_inversion", "optimization"]`——直接指定了 PDE + 反演 + 优化，这几乎是完整的解法路线
- 2020_B：`["dynamic_programming", "MDP", "game_theory", "Monte_Carlo"]`——四种方法全部列出
- 2024_A：`["kinematics", "geometric_modeling", "numerical_solution"]`——相对抽象，泄露较轻

PRE_REGISTRATION.md §5 声称 `core_methods` 是"方法参考（非唯一答案）"，但：
- 字段名 `core_methods`（核心方法）而非 `reference_methods`（参考方法）或 `acceptable_method_families`（可接受方法族），语义上倾向于"正确答案"
- evaluator（e2e_metrics.py `_method_hit`）将 core_methods 作为 GT 进行 top-3 命中率计算，实际上把它当作了"正确答案"来匹配
- 没有 `acceptable_alternative_methods` 或 `invalid_method_families` 字段来表达多解性

**判定**：存在 solution-method leakage，且 evaluator 的使用方式加剧了这一问题。

#### 2.2.2 Over-Specification

`required_deliverables` 字段在某些题目中过度指定了交付物形式：
- 2018_A：`["PDE热传导模型", "参数反演算法", "优化设计", "灵敏度分析"]`——"PDE热传导模型"指定了模型类型（PDE），而非只指定"热传导模型"
- 2022_C：`["PCA降维", "聚类模型", "判别分析", "统计检验"]`——"PCA降维"指定了具体降维方法

**判定**：部分题目存在 over-specification，将实现手段写入了交付物要求。

#### 2.2.3 Hindsight Bias / Award-Paper Contamination

无法直接验证 gold standard 是否基于获奖论文反推，但有以下线索：
- `CUMCM-Bench.json` 中 2024_A 包含 `reference_results`（q1_300s_head_pos="(4.4203, 2.3204)" 等精确数值），这些数值可能来自参考解法
- `core/knowledge/playbooks/playbook-2024A-bench-dragon.md` 提供了详细的建模路线（多体递推 + 悬链线 + 微分几何），这是典型的"已知解法后写 playbook"模式
- 但 CUMCM-Bench-v2.json 本身不包含 reference_results，只包含 sub_questions / core_methods 等结构化字段，hindsight bias 的直接证据较弱

**判定**：CUMCM-Bench-v2.json 本身的 hindsight bias 风险中等。playbook 体系存在明显的 hindsight bias，但 playbook 不在 benchmark schema 内。

#### 2.2.4 Incomplete Problem Context / Missing Attachments

**严重问题**：baseline_snapshot.json 中 5 个题目有 4 个 `input_file = null`：

| question_id | title | input_file | 状态 |
|---|---|---|---|
| 2024_A | "板凳龙"闹元宵 | `examples/problems/cumcm2024A.txt` | 有文件但内容错误 |
| 2022_C | 古代玻璃制品 | null | BLOCKED |
| 2020_B | 穿越沙漠 | null | BLOCKED |
| 2018_A | 高温作业服装设计 | null | BLOCKED |
| 2019_C | 机场的出租车问题 | null | BLOCKED |

4/5 baseline 题目缺少真实题面文本，无法执行 B0。这意味着 P15.1 "5 题 B0 baseline" 的目标实际上只有 1 题可执行（且该题输入错误）。

此外，CUMCM 题目通常附带数据附件（如 2022_C 的玻璃成分数据、2023_C 的蔬菜销售数据），但 benchmark schema 中没有 `attachments` 字段，baseline_snapshot 中也没有 `data_files` 记录（2024_A 的 data_files=[]，但实际板凳龙题可能有几何参数附件）。

**判定**：incomplete problem context 和 missing attachments 是 P15.1 的主要阻塞因素。

#### 2.2.5 Ambiguity / Inconsistent Annotation

- `family` 字段在不同题目中粒度不一致：2024_A = `["几何运动", "综合"]`（中文 + "综合"兜底），2018_A = `["热传导/温度场"]`（英文斜杠），2015_B = `["数据+评价+决策"]`（加号连接）。没有统一的 family 枚举或分类体系。
- `sub_questions` 的粒度不一致：2024_A 有 5 个精确子问题，2015_B 只有 2 个宽泛子问题，2017_A 有 3 个。部分题目的 sub_questions 实际上是"任务方向"而非"可独立评分的子问题"。
- `capability_dimensions` 的赋值缺乏明确标准：2018_A 的 construction=high, solving=high, validation=high（全高），而 2015_C 的 construction=low, solving=low（全低）。没有标注者间一致性验证。

**判定**：存在 annotation inconsistency，主要体现在 family 命名、sub_questions 粒度和 capability_dimensions 赋值标准上。

### 2.3 BLOCKED 题目分析

2022_C / 2020_B / 2018_A / 2019_C 因缺真实题面 BLOCKED。影响：

1. **P15.1 目标无法达成**：预注册要求"5 题 B0 baseline"，实际只有 1 题可执行（且输入错误），完成率 0/5。
2. **家族覆盖不足**：5 题应覆盖 5 个 family（几何运动、数据+评价、离散调度、热传导、交通网络），实际只有 1 个 family 有数据。
3. **无法验证分类器泛化性**：只有 1 题数据，无法判断 type-classifier 误分类是系统性问题还是单题特例。
4. **BLOCKED 原因**：`examples/problems/` 目录下可能只有 cumcm2024A.txt，其他年份题面未导入。需要从官方渠道获取真实题面和附件数据。

---

## 3. 多解模型原则（核心方法论）

### 3.1 原则陈述

数学建模题不存在唯一正确模型。Benchmark 不应该是 `expected_method = TOPSIS` 或 `expected_method = kinematics` 的猜谜游戏。最终 evaluator 应该测量：**does the model answer the problem?** 而不是 **did the agent guess the reference solution?**

### 3.2 当前 Schema 是否违反该原则

**是，存在三处违反：**

#### 违反 1：core_methods 被当作"唯一正确答案"

如 §2.2.1 所述，`core_methods` 字段名和 evaluator 的使用方式（top-3 GT hit rate）都将其视为"正确方法"。e2e_metrics.py 第 138-170 行：

```python
# method selection: top-3 GT hit
methods_gt = gt.get("methods") or []  # 来自 core_methods
t1 = _method_hit([chosen], card_names, methods_gt)
t3 = _method_hit(top3, card_names, methods_gt)
method_value = round(100.0 * sum(t3_hits) / len(t3_hits), 1)
```

如果 agent 选择了一个完全合理但不在 core_methods 中的替代方法（例如用变分法求解板凳龙，而非运动学），method_selection 得分为 0，即使模型正确回答了问题。

#### 违反 2：evaluation_targets 不允许 alternative model families

`evaluation_targets` 字段描述的是"评价目标"（如"坐标精度"、"碰撞时间精度"），但没有定义**在什么模型族下这些目标有效**。如果 agent 用一个不同的模型族回答了问题并达到了相同的 evaluation_targets，当前 schema 没有机制认可这种替代方案。

#### 违反 3：缺少 known_invalid_model_patterns

当前 schema 只有 `failure_modes`（通用失败模式代码，如 FM-MC-03），但没有题目级别的 `known_invalid_model_patterns`（如"2024_A 中使用 TOPSIS/AHP 等评价类方法 = invalid"）。这导致 evaluator 无法主动检测方法族不匹配，只能被动匹配 core_methods。

### 3.3 设计建议

将 `core_methods` 重构为以下字段组：

```json
{
  "allowed_model_families": ["kinematics", "geometric_modeling", "variational_calculus", "optimal_control"],
  "acceptable_alternatives": [
    {"family": "differential_geometry", "conditions": "螺线参数化精度 ≥ 解析解"},
    {"family": "finite_element", "conditions": "仅当柔性体效应不可忽略时"}
  ],
  "required_constraints": ["螺线方程约束", "把手间距约束", "龙头匀速约束"],
  "required_relationships": ["龙头位置 → 各节位置的递推关系", "螺距 → 碰撞时间的函数关系"],
  "known_invalid_model_patterns": [
    {"pattern": "TOPSIS/AHP/PCA 等评价类方法", "reason": "题目要求正向运动学计算，非多方案评价"},
    {"pattern": "纯回归拟合无物理模型", "reason": "缺乏螺线几何约束，外推不可靠"}
  ],
  "evaluation_target": "模型是否正确回答了 5 个子问题（坐标/碰撞/螺距/方案/速度），而非是否使用了参考方法"
}
```

---

## 4. Benchmark 三层设计

### 4.1 当前是否有分层设计

**没有。** 当前 P15 只有一个端到端指标：题目 → 完整 pipeline → 8 项能力指标。没有分层设计，导致：
- 无法定位失败发生在哪一层（是问题理解错了？还是模型建错了？还是求解错了？）
- B0 的 UNRESOLVED 无法区分"problem_analysis 未执行"和"problem_analysis 执行了但分解错误"
- 能力训练缺乏针对性——不知道该训练 problem understanding 还是 model construction

### 4.2 三层设计方案

#### L1：Problem Understanding（问题理解层）

| 项 | 设计 |
|---|---|
| **输入** | 原始题面文本 + 附件数据 |
| **输出** | 结构化问题解析：sub_questions[]、key_variables[]、key_constraints[]、problem_family、required_deliverables[] |
| **Evaluator** | Deterministic：sub_questions 数量与 gold 的交集/并集（Jaccard）；key_variables 覆盖率；key_constraints 覆盖率。Semantic（LLM/expert）：子问题语义对齐度（是否正确理解了每个子问在问什么）；题型分类正确性。 |
| **通过标准** | sub_questions Jaccard ≥ 0.6；key_variables 覆盖率 ≥ 0.7；key_constraints 覆盖率 ≥ 0.7；题型分类正确。 |
| **与 L2 接口** | L1 输出的结构化问题解析作为 L2 的输入。L1 不通过则不进入 L2（避免垃圾进垃圾出）。 |

#### L2：Model Construction（模型构建层）

| 项 | 设计 |
|---|---|
| **输入** | L1 输出的结构化问题解析 + 原始题面 |
| **输出** | 模型规格：model_family、equations[]、variables[]、constraints[]、assumptions[]、solution_strategy |
| **Evaluator** | Deterministic：dimension consistency（方程左右维度一致）、symbol consistency（变量在方程中定义且使用）、constraint coverage（gold 约束是否全部建模）、variable coverage（gold 变量是否全部使用）、unit consistency（单位一致）。Semantic：problem alignment（模型是否回答了问题）、assumption plausibility（假设是否合理）、mechanism validity（机制是否正确）、model sufficiency（模型是否足够回答所有子问题）。 |
| **通过标准** | Deterministic checks 全绿；problem alignment ≥ 0.7；model sufficiency ≥ 0.7；方法族在 allowed_model_families 内。 |
| **与 L3 接口** | L2 输出的模型规格作为 L3 的输入。L2 不通过则不进入 L3。 |

#### L3：End-to-End Modeling（端到端建模层）

| 项 | 设计 |
|---|---|
| **输入** | L2 输出的模型规格 + 原始题面 + 附件数据 |
| **输出** | 完整可运行代码 + 数值结果 + 论文 + 验证报告 |
| **Evaluator** | Deterministic：代码可运行性（exit code 0）、结果可追溯性（数值结果可从代码复现）、hash/provenance 链完整。Semantic：结果正确性（与 reference_results 或物理约束对比）、验证充分性（敏感性分析/鲁棒性）、论文质量。 |
| **通过标准** | 代码可运行；结果可复现；关键数值在容差范围内；验证充分。 |
| **与其他层接口** | L3 是最终交付层。L3 失败可回溯到 L2（模型错了）或 L1（问题理解错了）。 |

### 4.3 分层的价值

- **可定位失败**：L1 fail = 问题理解问题；L2 fail = 建模能力问题；L3 fail = 工程/求解问题
- **可针对性训练**：先确保 L1 通过（problem understanding），再训练 L2（model construction），最后优化 L3
- **避免级联失败掩盖**：当前 B0 的问题可能同时出现在 L1（输入错误 + 未分解）和 L2（方法族错误），但端到端指标无法区分
- **当前 B0 的定位**：L1 未执行（Q001 空壳），L2 未执行（M001 空壳），L3 未执行（无代码/论文）——三层全部 fail，但 fail 原因是"未执行"而非"能力不足"

---

## 5. Model Card 设计

### 5.1 Model Card 规范

每个 benchmark problem 应有 Problem Card（注意：是 Problem Card 而非 Model Card，因为描述的是题目而非模型），包含以下字段：

```
problem_id, source, source_sha256, family, sub_questions
allowed_model_families
required_problem_elements
required_relationships
known_valid_model_patterns（不是唯一答案）
known_invalid_model_patterns
validation_requirements
sensitivity_requirements
common_human_errors
common_llm_errors
evidence_sources
```

### 5.2 2024_A 完整 Model Card 示例

```yaml
problem_id: 2024_A
title: "板凳龙"闹元宵
source: 2024年全国大学生数学建模竞赛 A 题
source_sha256: <真实题面文本的 SHA256，待修复输入后填入>
input_file: examples/problems/cumcm2024A.txt  # 必须修复为真实板凳龙题面
family: [几何运动, 连续建模]
difficulty: medium-high

sub_questions:
  - id: Q1
    desc: 建立板凳龙螺旋进场的运动学模型，计算 300s 时龙头把手位置坐标
    type: forward_simulation
    required_output: (x_head(300), y_head(300))
    reference_value: (4.4203, 2.3204)  # 来自 CUMCM-Bench.json，仅用于 L3 校验
  - id: Q2
    desc: 碰撞检测——确定螺线盘入和盘出过程中的碰撞时间
    type: collision_detection
    required_output: collision_time(s)
    reference_value: 412.4738s
  - id: Q3
    desc: 最小螺距设计——在不碰撞的约束下求最小螺距
    type: constrained_optimization
    required_output: min_pitch(m)
    reference_value: 0.450337m
  - id: Q4
    desc: 进入与盘出的螺距变化方案——设计螺距随时间变化的策略
    type: trajectory_planning
    required_output: pitch(t) profile
  - id: Q5
    desc: 速度控制——龙头匀速条件下各把手的最大速度
    type: kinematic_analysis
    required_output: max_speed_per_section(m/s)
    reference_value: 1.2465 m/s (龙头)

allowed_model_families:
  - kinematics (刚体运动学递推)
  - geometric_modeling (螺线几何参数化)
  - differential_geometry (微分几何曲线理论)
  - variational_calculus (变分法，用于最优螺距)
  - optimal_control (最优控制，用于速度规划)

acceptable_alternatives:
  - family: finite_element
    conditions: 仅当考虑板凳龙柔性变形时；需证明刚体近似误差 > 5%
  - family: pure_numerical_simulation
    conditions: 必须包含螺线几何约束的显式编码；不接受纯数据驱动无物理模型

required_problem_elements:
  - 龙头运动轨迹（螺线参数方程）
  - 各节把手位置递推关系（第 n 节 → 第 n+1 节）
  - 碰撞检测准则（相邻节/自身相交）
  - 螺距几何定义
  - 速度传递关系（龙头速度 → 各节速度）

required_relationships:
  - head_position(t) → section_i_position(t) 的递推函数
  - pitch → collision_time 的单调关系（螺距越小碰撞风险越高）
  - head_speed = const → section_i_speed ≤ head_speed 的运动学约束
  - 螺线曲率 → 把手间距的几何约束

known_valid_model_patterns:
  - pattern: 阿基米德螺线参数化 + 刚体链递推 + 数值碰撞检测
    evidence: playbook-2024A-bench-dragon.md 推荐方案
  - pattern: 微分几何曲线论 + 弧长参数化 + 约束优化
    evidence: 理论上等价，可验证
  - pattern: 多体动力学 + 铰约束 + 数值积分
    evidence: 更通用但计算量更大，竞赛中可行

known_invalid_model_patterns:
  - pattern: TOPSIS / AHP / PCA 等多方案评价方法
    reason: 题目要求正向运动学计算和约束优化，不是多方案评价排序
    evidence: B0 运行中 M001 选择了 TOPSIS，完全不适用于本题
  - pattern: 纯回归/插值拟合（无物理模型）
    reason: 缺乏螺线几何约束和运动学递推关系，外推不可靠
  - pattern: 静态几何分析（无时间维度）
    reason: Q1/Q2/Q5 均为时间相关问题，需要动态模型

validation_requirements:
  - Q1 坐标结果与 reference_value 误差 ≤ 1%
  - Q2 碰撞时间满足物理一致性（碰撞发生在盘入/盘出阶段）
  - Q3 最小螺距满足不碰撞约束（需验证：在该螺距下确实无碰撞）
  - Q4 螺距方案满足连续性和可行性
  - Q5 速度满足运动学约束（各节速度 ≤ 龙头速度，考虑传动比）

sensitivity_requirements:
  - 螺距 ±10% 对碰撞时间的影响
  - 龙头速度 ±10% 对各节最大速度的影响
  - 把手间距公差 ±5% 对最小螺距的影响
  - 初始位置扰动对 300s 坐标的影响

common_human_errors:
  - 缺少第 n 个到第 n+1 个把手的递推计算公式（扣 5-10 分，来自 CUMCM-Bench.json pitfalls_2024）
  - 碰撞检测只检查相邻节，忽略自身相交
  - 螺距定义不一致（螺距 vs 圈间距 vs 导程）
  - 速度分析忽略角加速度，只考虑线速度
  - 摘要未独立成页（格式扣分项）

common_llm_errors:
  - 将运动学问题误分类为"评价类"问题，选择 TOPSIS/AHP（B0 实际发生）
  - 生成空壳 artifact，payload=[]，无实际建模内容（B0 实际发生）
  - 不进行子问题分解，将 5 个子问题视为单一问题（B0 实际发生）
  - 编造几何参数（题目未给出的龙身节数、长度等）
  - 混淆螺线类型（阿基米德螺线 vs 对数螺线 vs 圆的渐开线）
  - 碰撞检测退化为"检查两个圆是否相交"，忽略龙身的连续曲线特性

evidence_sources:
  - core/knowledge/problems/CUMCM-Bench.json (2024_A 条目，含 reference_results)
  - core/knowledge/playbooks/playbook-2024A-bench-dragon.md
  - core/knowledge/bench/cumcm/rubric_2024a.json
  - core/knowledge/bench/e2e/mc_2024A.json
  - research/P15/benchmark/CUMCM-Bench-v2.json (2024_A 条目)
```

---

## 6. Human / Agent / Reference 三层比较

### 6.1 当前是否有 Human Baseline

**没有。** P15 体系中不存在任何 human baseline：
- `CUMCM-Bench-v2.json` 只有 gold standard（结构化标注），没有人类解法
- `core/knowledge/bench/e2e/artifacts/2024_A/` 下有 ARM_B0.json、ARM_B1.json、ARM_MMA.json 等，但这些是**agent 运行产物**（ARM = Agent Run Manifest），不是人类解法
- `core/knowledge/paper-cases/A-topic/` 下有论文案例，但这些是获奖论文的整理，不是受控的 human baseline 实验
- PRE_REGISTRATION.md 中没有提及 human baseline 的获取计划

### 6.2 为什么需要 Human Baseline

当前 benchmark 的隐含比较是 **Agent vs Answer Key**（agent 输出 vs gold standard）。这有两个根本问题：

1. **Answer Key 不是能力标尺**：gold standard 是结构化标注（sub_questions、core_methods），不是实际解法。Agent 与 answer key 的匹配度不能直接翻译为"建模能力"。
2. **缺乏能力上界**：没有 human baseline，就不知道"好的建模"长什么样，也无法判断 agent 的差距是"能力不足"还是"benchmark 设计不合理"。

合理的比较框架应该是：

```
Human solution → Expert rubric → 建立能力标尺（什么是好的建模）
Agent solution → Same rubric   → 测量 agent 能力（与人类同尺度量）
Reference solutions → Diversity / validity analysis → 理解多解空间
```

### 6.3 Human Baseline 获取方案

#### 方案 A：获奖论文分析（低成本，即时可用）

- 来源：CUMCM 官方获奖论文集（本科组一等奖/二等奖）
- 处理：对 2024_A 等题目，提取 3-5 篇获奖论文的建模部分，结构化提取：model_family、equations、assumptions、constraints、solution_strategy
- 用途：建立 `known_valid_model_patterns`（如 §5 所示），理解多解空间
- 局限：获奖论文经过评审筛选，存在 selection bias；不能代表"平均人类水平"

#### 方案 B：受控人类实验（高成本，长期）

- 设计：招募 5-10 名有数学建模经验的人类受试者（大学生/研究生），在受控条件下（相同时间、相同题面、允许使用工具）完成 2024_A 的建模部分（不需要完整论文）
- 采集：model_spec（equations/variables/constraints/assumptions）、解题过程录音/屏幕录制、自我反思
- 评分：由 2-3 名专家使用统一 rubric 评分
- 用途：建立 human capability distribution（均值/方差/分布），作为 agent 能力的参照
- 局限：成本高、样本量小、受试者动机和经验差异大

#### 方案 C：专家解法 + 专家 rubric（中成本，推荐）

- 设计：邀请 1-2 名数学建模专家（教练/评委/有竞赛经验的博士）为 2024_A 撰写一份"标准解法"（model_spec 级别，不需要完整论文），同时制定一份专家评分 rubric
- 用途：专家解法作为 `reference_model_spec`（不是唯一正确答案，而是"一个高质量的解法示例"）；专家 rubric 作为 L2 evaluator 的 semantic judgment 部分的评分标准
- 局限：单个专家解法可能有偏好；需要至少 2 名专家交叉验证

### 6.4 推荐实施路径

1. **立即（P15.1 修复阶段）**：使用方案 A，从获奖论文中提取 2024_A 的 3-5 个有效建模模式，填入 Model Card 的 `known_valid_model_patterns`
2. **短期（P15.2 前）**：使用方案 C，邀请专家为 2-3 个核心题目撰写 model_spec 和 rubric
3. **长期（P15.3+）**：使用方案 B，建立受控 human baseline 实验

---

## 7. Model Construction Evaluator 重设计

### 7.1 现有 Evaluator 审计

#### 7.1.1 core/tools/evaluation/e2e_metrics.py（八项能力指标）

| 指标 | 类型 | 实现方式 | 能否测量 Model Construction |
|---|---|---|---|
| decomposition_coverage | Deterministic (退化) | count-ratio = min(produced, gold)/gold；无语义对齐时退化 | 否。只能计数，不能判断分解质量 |
| method_selection | Deterministic | top-3 方法卡 ID 字符串匹配（`_method_hit`） | 部分。只能判断方法卡 ID 是否匹配，不能判断方法是否适用于题目 |
| model_correctness | External (LLM/expert) | 完全依赖 `response.model_correctness_pct` 外部输入 | 否。本次运行中为 n/a |
| experiment_validity | Deterministic | result artifact 是否有 sensitivity/baseline/multi_run tags | 否。只检查 tag，不检查实验内容 |
| validation_reliability | Deterministic | claim 支撑率 + paper 是否存在 | 否 |
| innovation | Deterministic | decision 中是否有 pat- 前缀的 knowledge_ref | 否 |
| writing_completeness | Deterministic | LaTeX 中 figure/table/equation/reference 数量 | 否 |
| end_to_end | External | 依赖 `response.total` 外部输入 | 否 |

**关键缺失**：
- 无 dimension consistency（方程左右维度检查）
- 无 symbol consistency（变量定义与使用一致性）
- 无 constraint coverage（gold 约束是否全部建模）
- 无 variable coverage（gold 变量是否全部使用）
- 无 unit consistency（单位一致性）
- 无 equation solvability（方程是否可求解）
- 无 problem alignment（模型是否回答了问题）——这是 LLM judgment，但当前完全缺失
- 无 artifact non-emptiness check（artifact 内容是否为空）——B0 的 16 个空壳全部通过

#### 7.1.2 core/tools/evaluation/score_compute.py（5 张评分卡）

基于 LaTeX 文本的关键词匹配和计数：
- Academic：推导完整性（关键词匹配）、假设合理性（章节标题匹配）、验证充分性（关键词匹配）、数学正确性（无实际检查）
- Engineering：可复现性（文件存在性）、计算性能（无实际测量）、鲁棒性（关键词匹配）
- Judge：创新性（关键词匹配）、完整性（章节计数）
- Reader：结构清晰度（章节计数）、语言质量（无实际检查）
- Adversarial：逻辑自洽性（关键词匹配）、边界极限（关键词匹配）

**全部是关键词/计数启发式，无任何数学正确性验证。** 且依赖 `paper/main.tex` 存在——B0 项目中没有 paper/ 目录，这些评分卡全部无法运行。

#### 7.1.3 core/tools/evaluation/score_artifact.py（评审判定）

消费 score_compute 的输出，计算加权均分和 verdict。本身不做独立评估。

#### 7.1.4 core/evaluation/（包结构）

只有 `__init__.py` 桥接层，动态加载 `core/tools/` 下的实现。没有独立的 evaluator 实现。

### 7.2 重设计方案

Model Construction Evaluator 应拆分为 **Deterministic Checks** + **Semantic Judgment** 两层。

#### 7.2.1 Deterministic Checks（确定性检查，零 LLM）

这些检查可以从 model artifact 的结构化内容（equations、variables、constraints）中自动计算：

| 检查项 | 实现方式 | 通过标准 |
|---|---|---|
| **dimension consistency** | 解析方程左右两侧的变量维度（需变量声明中包含 dimension 字段），检查加减项维度一致、等号两侧维度一致 | 所有方程通过 |
| **symbol consistency** | 收集 equations 中出现的所有符号，检查每个符号在 variables 中声明且被使用；检查未声明的符号、声明但未使用的符号 | 无未声明符号；未使用符号 ≤ 2 |
| **constraint coverage** | 将 model 的 constraints 与 gold 的 key_constraints 做语义匹配（关键词 + 结构），计算覆盖率 | ≥ 0.8 |
| **variable coverage** | 将 model 的 variables 与 gold 的 key_variables 做匹配，计算覆盖率 | ≥ 0.7 |
| **equation references** | 检查 model 的 equations 中是否引用了 constraints 和 variables（方程中使用了约束中定义的参数） | 关键约束均被引用 |
| **unit consistency** | 变量声明中包含 unit 字段，检查方程中单位运算一致性（如 m/s = m/s） | 所有方程通过 |
| **artifact non-emptiness** | 检查 model artifact 的 payload 和 data 非空；equations 列表非空；variables 列表非空 | 非空 |
| **hash/provenance** | 检查 model artifact 的 provenance 链完整（depends_on 指向存在的 artifact） | 链完整 |

**实现前提**：model artifact 的 data 字段需要包含结构化的 `equations`、`variables`、`constraints` 列表（当前 M001 的 data 只有 `{card_id, family, shortlist}`，完全不够）。

#### 7.2.2 Semantic Judgment（语义判断，LLM 或 Expert）

这些检查无法纯确定性计算，需要 LLM judge 或专家评分：

| 检查项 | 评分方式 | 通过标准 |
|---|---|---|
| **problem alignment** | LLM/expert 对照 sub_questions，判断模型是否回答了每个子问题。输出 per-question alignment score (0-1) + 理由 | 平均 ≥ 0.7；无任何子问题 = 0 |
| **assumption plausibility** | LLM/expert 评估每个假设是否合理、是否有依据、是否与题面一致 | 不合理假设 ≤ 1 |
| **mechanism validity** | LLM/expert 评估模型的核心机制（如运动学递推、碰撞检测准则）是否正确 | 核心机制正确 |
| **model sufficiency** | LLM/expert 评估模型是否足够回答所有子问题（是否缺少关键组件） | 不缺少关键组件 |
| **solvability** | LLM/expert 评估方程是否可求解（是否有足够的边界条件/初始条件、是否超定/欠定） | 可求解 |

**LLM Judge 设计原则**：
- 使用结构化 rubric（不是自由文本评分），每个维度有明确的评分标准和锚点
- 要求 LLM 输出 per-dimension score + evidence（引用 model artifact 中的具体内容）
- 多 judge 投票（≥3 个 judge），报告均值和标准差
- 与 deterministic checks 解耦：deterministic checks 全绿是 semantic judgment 的前提

#### 7.2.3 不要把所有东西交给 LLM Judge

当前体系的倾向是：能确定性计算的也不计算（如 model_correctness 完全依赖外部输入），不能确定性计算的也不设计 rubric（如 problem alignment 完全缺失）。重设计后：

- **Deterministic checks 应覆盖 60-70% 的评估维度**（结构正确性、约束完整性、符号一致性、单位一致性、可追溯性）
- **Semantic judgment 覆盖 30-40%**（问题对齐、假设合理性、机制有效性、模型充分性）
- **两者独立报告**，不合并为单一分数——deterministic fail 是硬阻塞（结构错误不可接受），semantic 低分是改进方向

### 7.3 实施优先级

| 优先级 | 检查项 | 理由 |
|---|---|---|
| P0 | artifact non-emptiness | 当前 B0 的 16 个空壳全部通过，这是最基本的质量门 |
| P0 | input-benchmark consistency | 输入文本 hash 与 benchmark 条目的一致性校验 |
| P1 | constraint coverage | 可从结构化 data 中计算，直接测量模型是否覆盖了题目约束 |
| P1 | variable coverage | 同上 |
| P1 | symbol consistency | 需要 model artifact 包含 equations/variables 结构化数据 |
| P2 | problem alignment (LLM judge) | 需要设计 rubric 和多 judge 机制 |
| P2 | dimension/unit consistency | 需要变量声明中包含 dimension/unit 字段 |
| P3 | mechanism validity, model sufficiency | 深度语义判断，需要专家 rubric |

---

## 8. Adversarial Modeling Benchmark 设计

### 8.1 设计原则

Adversarial test 的目的是验证 evaluator 能否检测出"数学推导正确但建模本质错误"的情况。每个 test case 构造一个**特定类型的错误模型**，evaluator 必须能正确识别错误类型并判 FAIL，而不是被"数学推导正确"的表象迷惑。

### 8.2 三个具体 Adversarial Test Case

#### Test Case 1：Wrong-Objective（优化目标错误）

**构造**：
- 题目：2024_A Q3（最小螺距设计——在不碰撞的约束下求最小螺距）
- 对抗模型：建立了完整的螺线几何模型 + 碰撞检测算法 + 约束优化框架，数学推导完全正确，数值求解收敛。但优化目标写成了"最大化螺距"（而非最小化），约束条件正确（不碰撞）。
- 结果：模型输出一个很大的螺距值，数学上是"最大化螺距 subject to 不碰撞"的正确解，但完全没有回答题目要求的"最小螺距"。

**Evaluator 必须判**：
- Deterministic checks：PASS（方程正确、约束完整、符号一致、可求解）
- Semantic judgment — problem alignment：**FAIL**（优化目标与题目要求相反）
- 最终判定：**mathematically valid BUT problem-alignment FAIL**

**检测机制**：semantic judge 对照 Q3 的 sub_question 描述（"最小螺距设计"），检查模型的 objective function 是否为最小化。这需要 model artifact 中显式声明 objective function（当前 M001 的 data 中没有这个字段）。

#### Test Case 2：Wrong-Model-Family（方法族错误，B0 实际发生的情况）

**构造**：
- 题目：2024_A（运动学/几何建模，5 个子问题）
- 对抗模型：使用 TOPSIS 方法，建立了完整的评价指标体系（指标包括"螺线美观度"、"碰撞安全性"、"速度合理性"等），计算了权重（熵权法 + AHP 组合赋权），进行了排序，输出了"最优方案"。TOPSIS 的每一步计算都正确（同向化、归一化、加权、距离计算），敏感性分析完整（权重扰动、指标增删）。
- 结果：TOPSIS 输出了一个"方案排序"，但没有回答任何一个子问题（没有 300s 坐标、没有碰撞时间、没有最小螺距、没有螺距方案、没有速度分析）。

**Evaluator 必须判**：
- Deterministic checks：部分 PASS（TOPSIS 计算正确），但 constraint coverage **FAIL**（螺线方程约束、把手间距约束、龙头匀速约束均未建模），variable coverage **FAIL**（head_position、collision_time、pitch 等关键变量未使用）
- Semantic judgment — problem alignment：**FAIL**（模型没有回答任何子问题）
- Semantic judgment — mechanism validity：**FAIL**（评价排序机制不适用于正向运动学计算）
- 最终判定：**computationally valid BUT fundamentally misaligned**

**检测机制**：
- Deterministic：constraint coverage 和 variable coverage 会直接 FAIL（因为 TOPSIS 模型中没有这些物理约束和变量）
- Semantic：problem alignment judge 检查模型输出是否包含每个子问题要求的 deliverable
- known_invalid_model_patterns：Model Card 中明确列出"TOPSIS/AHP/PCA = invalid for 2024_A"

#### Test Case 3：Missing-Constraint + Wrong-Unit（约束缺失 + 单位错误的复合错误）

**构造**：
- 题目：2024_A Q1（300s 时龙头把手位置坐标）+ Q5（龙头匀速条件下各把手最大速度）
- 对抗模型：建立了螺线参数化模型 + 刚体链递推，数学推导基本正确。但：
  1. **Missing constraint**：忽略了"把手间距约束"（相邻把手之间的距离必须等于板凳长度），导致递推时各节位置可以自由移动
  2. **Wrong unit**：螺线参数方程中，角度使用了度（degree）而非弧度（radian），但三角函数计算时没有转换。导致 300s 时的坐标计算错误（差了 π/180 的因子）
  3. 速度分析中，龙头速度输入为 1.5 m/s，但计算时误用了 1.5 km/h，导致各节速度偏小

**Evaluator 必须判**：
- Deterministic checks：
  - constraint coverage：**FAIL**（把手间距约束未建模）
  - unit consistency：**FAIL**（角度单位不一致、速度单位不一致）
  - dimension consistency：可能 PASS（如果变量声明中没有 unit 信息则无法检测）
- Semantic judgment：
  - problem alignment：部分 FAIL（Q1 坐标因单位错误而不正确；Q5 速度因单位错误而不正确）
  - mechanism validity：部分 FAIL（递推关系缺少间距约束，物理上不正确）
- 最终判定：**structurally incomplete + numerically incorrect**

**检测机制**：
- Deterministic：constraint coverage 检测把手间距约束是否在 model.constraints 中；unit consistency 检查变量声明中的 unit 字段与方程中的使用是否一致
- Semantic：problem alignment judge 检查 Q1 坐标结果是否在 reference_value 的容差范围内（单位错误会导致超出容差）

### 8.3 Adversarial Benchmark 的使用方式

1. **Evaluator 验证**：在修复 evaluator 后，用 adversarial test cases 验证 evaluator 能否正确检测各类错误。如果 evaluator 对 adversarial case 判 PASS，说明 evaluator 有盲区。
2. **Agent 训练**：将 adversarial cases 作为训练数据，让 agent 学会识别和避免这些错误模式。
3. **回归测试**：每次 evaluator 更新后，运行 adversarial benchmark 确保没有引入回归。

---

## 9. P15 后续路线重新评估

### 9.1 核心判断

**当前测量仪器不可靠，暂停能力训练，先修测量仪器。**

具体依据：
1. B0 "运行"是 0.06 秒的模板初始化，非真实 agent 执行——任何基于 B0 的能力结论无效
2. 输入题面错误（导弹题 ≠ 板凳龙题），且无一致性校验——benchmark 输入不可信
3. Evaluator 只能测量元数据（计数、ID 匹配、字段存在性），无法测量内容（模型是否回答了问题、方法是否适用、数学是否正确）
4. 4/5 baseline 题目 BLOCKED（缺真实题面）——P15.1 目标无法达成
5. 无 human baseline——缺乏能力标尺
6. 无 adversarial benchmark——无法验证 evaluator 的检测能力

### 9.2 逐项回答

#### P15.1 是否应该继续？

**暂停，先修复后重跑。**

P15.1 的目标是"建立 5 题 B0 baseline"，但当前状态：
- 1 题有输入但内容错误（2024_A）
- 4 题无输入（BLOCKED）
- 唯一的 B0 运行是模板初始化，非真实执行

**修复清单（必须全部完成才能重跑 P15.1）**：
1. 修复 `examples/problems/cumcm2024A.txt`——替换为真实的板凳龙题面
2. 获取 2022_C / 2020_B / 2018_A / 2019_C 的真实题面和附件数据
3. 实现 input-benchmark consistency gate（输入文本 hash 与 benchmark 条目关联校验）
4. 实现 artifact non-emptiness check（阻止空壳 artifact 通过）
5. 确保 V3 orchestrator 真实执行 agent（model_provider 非 null、skill_version 非空 hash、latency 合理）
6. 重跑 2024_A B0，验证产生真实内容

#### P15.2 是否应该拆分？

**是，拆分为 P15.2a（L1+L2 能力测量）和 P15.2b（L3 端到端）。**

P15.2 原计划"15 题 Model Construction 跨家族泛化验证"，但：
- 当前没有 L1/L2/L3 分层，无法定位失败
- Model Construction evaluator 尚未建立（当前 model_correctness = n/a）
- 15 题的输入题面和附件数据尚未获取

**拆分方案**：
- **P15.2a（L1+L2 Pilot）**：3-5 题，聚焦 Problem Understanding + Model Construction 两层。不要求完整论文/代码，只要求结构化 problem_analysis + model_spec。使用重设计后的 L1/L2 evaluator 评分。目标是验证分层评估体系可行。
- **P15.2b（L3 End-to-End）**：在 P15.2a 验证 L1/L2 可行后，扩展到 10-15 题，增加完整代码/论文/验证的端到端评估。

#### 是否需要 Model Construction Pilot？

**是，且必须在 P15.2a 中作为核心。**

Model Construction Pilot 的目标：
1. 验证 model artifact 的结构化 schema（equations/variables/constraints/assumptions/objective）
2. 验证 deterministic checks（constraint coverage、variable coverage、symbol consistency）可实现
3. 验证 semantic judgment（problem alignment rubric）可操作
4. 用 2-3 题建立"模型构建能力"的初步测量

Pilot 不需要 15 题，3 题足够验证体系。

#### 是否需要先修 evaluator？

**是，这是最高优先级。**

如 §7 所述，当前 evaluator 存在根本性缺陷：
- model_correctness 完全依赖外部输入（n/a）
- 无 constraint/variable coverage
- 无 artifact non-emptiness check
- 无 problem alignment
- method_selection 只是字符串匹配

**在 evaluator 能够可靠测量 Model Construction 之前，任何能力训练都是盲目的。** 你无法改进你无法测量的东西。

#### 是否需要补真实 benchmark？

**是，必须。**

当前 36 题的 benchmark schema 已冻结（P15.0），但：
- 只有 1 题有输入文件（且内容错误）
- 4/5 baseline 题目 BLOCKED
- 无附件数据（CUMCM 题目通常有数据附件）

**需要补的内容**：
1. 修复 2024_A 输入
2. 获取 2022_C / 2020_B / 2018_A / 2019_C 的题面 + 附件
3. 为所有 baseline 题目建立 input_file 引用和 sha256
4. 实现 input-benchmark consistency gate

#### 是否需要增加 human baseline？

**是，但分阶段。**

如 §6 所述，human baseline 分三阶段：
1. 立即：获奖论文分析（方案 A），提取 known_valid_model_patterns
2. 短期：专家解法 + 专家 rubric（方案 C），为 2-3 题建立 reference_model_spec
3. 长期：受控人类实验（方案 B）

不需要在 P15.1 修复阶段就做完整的 human baseline，但 P15.2a 至少需要方案 A 和 C。

#### 是否需要 adversarial benchmark？

**是，作为 evaluator 验证工具。**

如 §8 所述，adversarial benchmark 的首要用途是**验证 evaluator 的检测能力**，而非训练 agent。在 evaluator 修复后，必须用 adversarial test cases 验证：
- evaluator 能否检测 wrong-objective？
- evaluator 能否检测 wrong-model-family？
- evaluator 能否检测 missing-constraint + wrong-unit？

如果 evaluator 对 adversarial case 判 PASS，说明 evaluator 仍有盲区，需要继续修复。

#### 是否需要 expert annotation？

**是，用于 Model Card 和 evaluator rubric。**

Expert annotation 的用途：
1. 为每个 benchmark problem 撰写 Model Card（allowed_model_families、known_valid/invalid_patterns、common_human/llm_errors）
2. 为 L2 evaluator 的 semantic judgment 部分制定评分 rubric 和锚点
3. 为 adversarial test cases 构造错误模型并标注错误类型

不需要为全部 36 题做 expert annotation，先为 3-5 个核心题目（baseline 题目）做即可。

### 9.3 修订后的 P15 路线图

```
P15.1-FIX（当前，预计 1-2 周）
├── 修复 2024_A 输入题面
├── 获取 4 题 BLOCKED 题面 + 附件
├── 实现 input-benchmark consistency gate
├── 实现 artifact non-emptiness check
├── 确保 V3 orchestrator 真实执行 agent
├── 重跑 2024_A B0（验证产生真实内容）
└── Exit: 5 题有真实输入 + 1 题有真实 B0

P15.1-BASELINE（重跑，预计 1 周）
├── 5 题 B0 真实执行
├── 使用重设计后的 L1 evaluator（problem understanding）
├── 建立 5 题的 B0 baseline 数据
└── Exit: 5 题 B0 baseline + L1 能力分布

P15.2a（L1+L2 Pilot，预计 2-3 周）
├── 3-5 题，聚焦 Problem Understanding + Model Construction
├── 实现 model artifact 结构化 schema（equations/variables/constraints）
├── 实现 deterministic checks（constraint/variable coverage, symbol consistency）
├── 实现 semantic judgment（problem alignment rubric, LLM/expert）
├── 获奖论文分析 → known_valid_model_patterns
├── 专家解法 + rubric（2-3 题）
├── Adversarial benchmark 验证 evaluator
└── Exit: L1+L2 评估体系验证可行 + Model Construction 初步测量

P15.2b（L3 End-to-End，预计 3-4 周）
├── 10-15 题，完整端到端（代码+论文+验证）
├── L3 evaluator（可运行性、可复现性、结果正确性）
├── 跨家族泛化验证
└── Exit: 15 题端到端 baseline + 跨家族能力图谱

P15.3+（长期）
├── Human baseline 受控实验
├── 全部 36 题 Model Card
├── Adversarial benchmark 扩展
└── 能力训练闭环（测量 → 训练 → 再测量）
```

### 9.4 最终建议

**一句话总结：先修尺子，再量能力。**

1. **立即暂停**任何基于当前 B0 的能力结论和训练计划
2. **最高优先级**：修复输入 + 实现 non-emptiness + consistency gate + 确保真实执行
3. **第二优先级**：重设计 Model Construction evaluator（deterministic checks + semantic judgment）
4. **第三优先级**：P15.2a Pilot 验证分层评估体系
5. **并行**：补真实题面、获奖论文分析、专家 annotation、adversarial test cases

在测量仪器可靠之前，所有"能力提升"的努力都是在黑暗中射击。

---

## 附录 A：证据文件索引

| 证据 | 文件路径 | 关键内容 |
|---|---|---|
| Benchmark schema | `research/P15/benchmark/CUMCM-Bench-v2.json` | 36 题 × 9 字段 gold standard |
| B0 报告 | `research/P15/reports/P15.1-2024A-B0.md` | UNRESOLVED / 20% / wrong family |
| Run manifest | `research/P15/benchmark/manifests/p151-2024a-run.json` | 16/16 nodes, 1 question, TOPSIS |
| Baseline snapshot | `research/P15/benchmark/manifests/baseline_snapshot.json` | 5 题中 4 题 input_file=null |
| Content hashes | `research/P15/benchmark/manifests/content_hashes.json` | hash 的是 benchmark JSON 条目，非输入文本 |
| Pre-registration | `research/P15/PRE_REGISTRATION.md` | P15.0/1/2 计划，5 维能力，6 类失败模式 |
| 项目 Registry | `projects/p151-2024a/state/registry.json` | 16 个 artifact，全部空壳（payload=[]） |
| 项目 Status | `projects/p151-2024a/state/status.json` | Q001 validated, V3 状态 |
| 项目 Run | `projects/p151-2024a/state/runs/5c98cd9911bc.json` | 0.06s, model_provider=null, skill_version=空 hash |
| 输入题面（错误） | `projects/p151-2024a/inputs/cumcm2024A.txt` | 导弹制导题，非板凳龙 |
| 输入题面（错误，源） | `examples/problems/cumcm2024A.txt` | 同上 |
| V2 状态 | `projects/p151-2024a/work/STATE.md` | 0/29，已完成：无 |
| Handoff | `projects/p151-2024a/work/handoff.md` | 已完成步骤：无 |
| Quality report | `projects/p151-2024a/state/quality_report.json` | WEAK，但 problem/model/experiment 全 PASS |
| Decision log | `projects/p151-2024a/state/decision_log.json` | question_type=evaluation, chosen=mc-topsis |
| Evidence graph | `projects/p151-2024a/state/evidence_graph.json` | 12 relations, P001→Q001→M001→E001→R001→C001 |
| e2e metrics | `core/tools/evaluation/e2e_metrics.py` | 8 项指标，model_correctness 依赖外部输入 |
| score compute | `core/tools/evaluation/score_compute.py` | 5 张评分卡，关键词启发式 |
| score artifact | `core/tools/evaluation/score_artifact.py` | 评审判定，消费 score_compute |
| Analyst role | `core/roles/analyst.yaml` | 具备 question-decomposition 能力 |
| Modeler role | `core/roles/modeler.yaml` | model_selection + model_construction |
| 原始题库 | `core/knowledge/problems/CUMCM-Bench.json` | 2024_A 正确记录为板凳龙，含 reference_results |
| Playbook | `core/knowledge/playbooks/playbook-2024A-bench-dragon.md` | 板凳龙详细建模路线 |
| P15 gate 脚本 | `research/P15/scripts/` | validate_schema, completeness, coverage, duplicate |

## 附录 B：关键数字汇总

| 数字 | 含义 |
|---|---|
| 0.06 秒 | B0 "运行"耗时（16 个 DAG 节点） |
| 0/29 | V2  legacy 进度（0%） |
| 1/5 | B0 question artifacts / gold sub_questions（count-ratio = 20%） |
| 16/16 | DAG 节点"完成"数（但全部为空壳） |
| 4/5 | baseline 题目 BLOCKED 比例（缺真实题面） |
| 36 | CUMCM-Bench-v2 题目总数 |
| 0 | human baseline 数量 |
| 0 | adversarial test case 数量 |
| null | model_provider（B0 未调用 LLM） |
| e3b0c44... | skill_version（空字符串 SHA256，未加载 skill） |
| 90a3026e... | 实际输入文本 hash（导弹题），与 manifest 匹配 |
| 7b86fddb... | content_hashes.json 中 2024_A 的 hash（benchmark JSON 条目，非输入文本） |
