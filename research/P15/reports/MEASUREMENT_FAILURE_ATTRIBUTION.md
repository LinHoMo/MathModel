# P15.1 Measurement & Failure Attribution Report

> **阶段**: P15.1 Phase 2 — Measurement & Failure Attribution（测量与失败归因）
> **日期**: 2026-09-08
> **性质**: 只诊断，不修复。不修改方法卡、不修改 evaluator、不做 Agent intervention。
> **前置阶段**: B0 accumulation（5 题跨模型家族 baseline，已完成）
> **后继阶段**: Research-layer calibration → Fresh B0 → 修正后的 capability baseline → 才允许 intervention

---

## 0. 研究纪律声明

### 0.1 核心判断

> **type-family misclassification 本身不是 Agent capability failure，而是"方法卡覆盖 → 方法选择器"的选择性测量失真。**

本阶段的核心任务是回答：B0 中哪些观测可以解释为能力缺陷，哪些观测是仪器缺陷，目前证据分别是什么。

### 0.2 三层模型定位

方法卡库**不是**"把所有数学建模方法做成卡片让 LLM 按卡片选方法"。正确定位是三层模型：

| 层 | 角色 | 说明 |
|---|---|---|
| **Layer 1** | LLM = Model Generator | 自由建模思考：理解题目→识别变量→提出假设→建立数学关系→生成候选模型→提出求解方案 |
| **Layer 2** | Modeling Knowledge = Constraint / Prior | 方法卡提供 requirements / supports / risks / verification，约束"你声称某方法适用"的资格，但不直接告诉 LLM "必须用 X" |
| **Layer 3** | Evidence | 实验和证据决定模型是否成立。Method Card 产生的是"候选方法先验"，Evidence 才产生"方法成立的证据" |

### 0.3 治理原则

> **Knowledge coverage must constrain evaluation, not constrain creativity.**

- 知识库可以限制"你声称某方法适用"的资格（evaluation gate）
- 知识库**不能**限制 LLM "提出一个新方法/新模型"的自由（creativity）
- 当 LLM 提出知识库中不存在的方法时，应标记为 `alternative_method`，进入人工审查，而非自动判错

> **Research-layer calibration ≠ Agent capability intervention**
> 方法卡修复后 method-selection 分数上涨 = measurement instrument validity ↑，≠ Agent capability ↑
> 真正的 capability improvement 要等仪器固定以后，再做 intervention/fresh comparison。

### 0.4 严格研究顺序

```
P15.1
  │
  ↓
B0 accumulation ✅ (已完成)
  │
  ↓
Measurement & Failure Attribution ← 当前阶段
  │
  ├─ Instrument failure → 记录为 calibration 清单（不修复）
  └─ Capability failure → 记录为 observation（不干预）
  │
  ↓
Research-layer calibration（下一阶段，才允许修复）
  │
  ↓
Fresh B0
  │
  ↓
修正后的 capability baseline
  │
  ↓
才允许 intervention
```

---

## 1. 执行摘要

### 1.1 一句话结论

**B0 全部 50 条可归因记录中，20 条为 measurement_failure（测量仪器失败），30 条为 not_applicable（B0 阶段限制），0 条为 capability_failure。当前 B0 低分不能作为 Agent 能力下降的证据。**

### 1.2 归因分布

| failure_attribution | 数量 | 占比 | 说明 |
|---|---|---|---|
| **measurement_failure** | 20 | 40% | 方法卡覆盖缺口 + artifact 粒度代理失真 + schema 通道缺失 + provenance 判据错配 |
| **not_applicable** | 30 | 60% | B0 阶段不产生该类 artifact（实验/论文/claim/rubric），非失败 |
| capability_failure | 0 | 0% | 无证据表明 Agent 真实能力缺失 |
| mixed | 0 | 0% | — |
| unresolved | 0 | 0% | — |

### 1.3 四类 measurement_failure 根因

| # | 指标 | 影响题数 | 根因 | 失真程度 |
|---|---|---|---|---|
| 1 | method_selection | 5（3题0分+2题100分虚高） | 方法卡库 L1/L2 层零覆盖，evaluator 只查 L4 card family | 三题假阴性，2019_C 假阳性 |
| 2 | decomposition_coverage | 5（20–33.3%） | evaluator 用 artifact 数量代理语义覆盖；Q001.payload.sub_questions 与 GT 逐字一致但被忽略 | 失真度 66.7%–80.0% |
| 3 | innovation | 5（0%） | 双重缺陷：① decision_log 无 knowledge_refs 字段；② 代码检查 `pat-` 前缀但 pattern 库 6/6 使用 `ip-` 前缀 | 测量通道不存在 |
| 4 | measurement_integrity | 5（0/5） | v1 判据 `created_by.startswith("agent")` 不适用于外部注册——实际 created_by 是角色名，但 provenance 中明确记录了 `executor_type=external_agent` | 判据与注册约定错配 |

### 1.4 关键发现

1. **B0 的 decomposition_coverage 低分几乎 100% 是测量失真**：所有 5 题的 Q001.payload.sub_questions 与 GT manifest 逐字一致，但 evaluator 只数 artifact 数量（恒为 1），不解析内容。语义覆盖率实际为 100%，count_ratio 仅为 20–33.3%。

2. **方法卡库的问题不是"卡太浅"，而是"覆盖面太窄"且"层级失衡"**：16 张卡全部具备 requires/supports/risks/verification 四字段（deep 或 deep+），但四层知识结构覆盖率呈 U 型：L3 83.3% > L4 66.7% > L1 37.5% > **L2 25%（最薄弱）**。当前卡库本质是"算法卡"，L1 Problem Structure 和 L2 Modeling Pattern 的骨架完全缺失。

3. **2019_C 的 method_selection=100 是假阳性**：L1（network/traffic）和 L2（queue/flow balance/interaction）全部缺失，仅在 L3/L4 solver 层面碰巧匹配。当前指标无法区分"系统覆盖"与"偶然匹配"。

4. **innovation=0 是前缀不匹配 bug**：e2e_metrics.py 检查 `pat-` 前缀，但 `core/knowledge/patterns/` 下全部 6 个 pattern 使用 `ip-` 前缀。同时 B0 的 decision_log 不含 knowledge_refs 字段，测量通道在 B0 阶段不存在。

5. **model_correctness 的 structural check 五题全 PASS**：M001 的 objective/constraints/variables 三要素齐全，说明 Agent 在 B0 约定范围内交付了结构完整的模型 artifact。

---

## 2. B0 观测总览

### 2.1 五题 B0 分数矩阵

| Problem | 模型家族 | method_selection | decomposition | innovation | model_correctness | experiment | validation | writing | e2e |
|---|---|---|---|---|---|---|---|---|---|
| 2024_A | 运动学/几何 | 0.0 | 20.0 | 0.0 | None | None | None | None | None |
| 2022_C | 统计/分类 | 100.0 | 25.0 | 0.0 | None | None | None | None | None |
| 2020_B | 动态规划/博弈 | 0.0 | 33.3 | 0.0 | None | None | None | None | None |
| 2018_A | 热传导/PDE | 0.0 | 33.3 | 0.0 | None | None | None | None | None |
| 2019_C | 排队/决策 | 100.0 | 25.0 | 0.0 | None | None | None | None | None |

### 2.2 B0 artifact 集（五题一致）

每个 B0 项目 registry 中恰好 5 个 artifact：

| ID | 类型 | created_by | 说明 |
|---|---|---|---|
| Q001 | question | `problem_understanding` | 问题理解与分解（payload 含全部 GT 子问题） |
| M001 | model | `model_construction` | 模型构建（structural check PASS） |
| D001 | decision | `method_selection` | 方法选择决策 |
| D002 | decision | `solving_strategy` | 求解策略决策 |
| D003 | decision | `validation_plan` | 验证计划决策 |

**无** result / experiment / figure / assumption / claim / paper_section 类型 artifact。所有 artifact 通过 `register_external_artifact.py` 注册，`provenance.executor_type = "external_agent"`，`provenance.agent_identity = "doubao"`。

---

## 3. 完整归因表

> 机器可读版本：`research/P15/reports/failure_attribution.json`（50 条记录）
> 人类可读详版：`research/P15/reports/_attribution_table.md`（含逐条 observed_reason + evidence）

### 3.1 归因总表

| Problem | Metric | B0 | Attribution | Confidence | Action |
|---|---|---|---|---|---|
| 2024_A | method_selection | 0.0 | measurement_failure | high | calibrate_instrument |
| 2024_A | decomposition_coverage | 20.0 | measurement_failure | high | calibrate_instrument |
| 2024_A | innovation | 0.0 | measurement_failure | high | calibrate_instrument |
| 2024_A | model_correctness | None | not_applicable | high | no_action |
| 2024_A | experiment_validity | None | not_applicable | high | no_action |
| 2024_A | validation_reliability | None | not_applicable | high | no_action |
| 2024_A | writing_completeness | None | not_applicable | high | no_action |
| 2024_A | end_to_end | None | not_applicable | high | no_action |
| 2024_A | measurement_integrity | 0.0 | measurement_failure | high | calibrate_instrument |
| 2024_A | empty_artifact_filter | 0 | not_applicable | high | no_action |
| 2022_C | method_selection | 100.0 | measurement_failure | medium | calibrate_instrument |
| 2022_C | decomposition_coverage | 25.0 | measurement_failure | high | calibrate_instrument |
| 2022_C | innovation | 0.0 | measurement_failure | high | calibrate_instrument |
| 2022_C | model_correctness | None | not_applicable | high | no_action |
| 2022_C | experiment_validity | None | not_applicable | high | no_action |
| 2022_C | validation_reliability | None | not_applicable | high | no_action |
| 2022_C | writing_completeness | None | not_applicable | high | no_action |
| 2022_C | end_to_end | None | not_applicable | high | no_action |
| 2022_C | measurement_integrity | 0.0 | measurement_failure | high | calibrate_instrument |
| 2022_C | empty_artifact_filter | 0 | not_applicable | high | no_action |
| 2020_B | method_selection | 0.0 | measurement_failure | high | calibrate_instrument |
| 2020_B | decomposition_coverage | 33.3 | measurement_failure | high | calibrate_instrument |
| 2020_B | innovation | 0.0 | measurement_failure | high | calibrate_instrument |
| 2020_B | model_correctness | None | not_applicable | high | no_action |
| 2020_B | experiment_validity | None | not_applicable | high | no_action |
| 2020_B | validation_reliability | None | not_applicable | high | no_action |
| 2020_B | writing_completeness | None | not_applicable | high | no_action |
| 2020_B | end_to_end | None | not_applicable | high | no_action |
| 2020_B | measurement_integrity | 0.0 | measurement_failure | high | calibrate_instrument |
| 2020_B | empty_artifact_filter | 0 | not_applicable | high | no_action |
| 2018_A | method_selection | 0.0 | measurement_failure | high | calibrate_instrument |
| 2018_A | decomposition_coverage | 33.3 | measurement_failure | high | calibrate_instrument |
| 2018_A | innovation | 0.0 | measurement_failure | high | calibrate_instrument |
| 2018_A | model_correctness | None | not_applicable | high | no_action |
| 2018_A | experiment_validity | None | not_applicable | high | no_action |
| 2018_A | validation_reliability | None | not_applicable | high | no_action |
| 2018_A | writing_completeness | None | not_applicable | high | no_action |
| 2018_A | end_to_end | None | not_applicable | high | no_action |
| 2018_A | measurement_integrity | 0.0 | measurement_failure | high | calibrate_instrument |
| 2018_A | empty_artifact_filter | 0 | not_applicable | high | no_action |
| 2019_C | method_selection | 100.0 | measurement_failure | medium | calibrate_instrument |
| 2019_C | decomposition_coverage | 25.0 | measurement_failure | high | calibrate_instrument |
| 2019_C | innovation | 0.0 | measurement_failure | high | calibrate_instrument |
| 2019_C | model_correctness | None | not_applicable | high | no_action |
| 2019_C | experiment_validity | None | not_applicable | high | no_action |
| 2019_C | validation_reliability | None | not_applicable | high | no_action |
| 2019_C | writing_completeness | None | not_applicable | high | no_action |
| 2019_C | end_to_end | None | not_applicable | high | no_action |
| 2019_C | measurement_integrity | 0.0 | measurement_failure | high | calibrate_instrument |
| 2019_C | empty_artifact_filter | 0 | not_applicable | high | no_action |

### 3.2 归因判定规则

- **measurement_failure**: 低分因为 evaluator 用了错误代理变量、catalog 不覆盖、schema 通道缺失、或判据与注册约定错配
- **capability_failure**: 低分因为 Agent 真实没有产生有效内容或真实漏掉关键约束（本阶段未发现）
- **not_applicable**: B0 阶段本就不产生该类 artifact（实验/论文/claim/rubric），非失败
- **mixed / unresolved**: 本阶段未出现

---

## 4. Measurement Audit A: Modeling Knowledge Architecture（四层知识结构覆盖）

> 详版：`research/P15/reports/_knowledge_architecture_audit.md`

### 4.1 当前方法卡库现状

16 张方法卡全部具备 `requires` / `good_for(supports)` / `risks` / `validation` 四字段，结构上全部扮演 Constraint/Prior 角色。4 张（mc-ahp, mc-arima, mc-topsis, mc-xgboost）额外具备 P8 竞争智能字段，评级 deep+；其余 12 张评级 deep。**无 shallow/medium 卡——问题不是卡太浅，而是覆盖面太窄。**

family 分布：metaheuristics(3), decision_analysis(2), classical_timeseries(2), composite_evaluation(2), 其余各 1。

### 4.2 四层知识结构覆盖率

| 层 | 标签数 | 已覆盖 | 覆盖率 | 缺失标签 |
|---|---|---|---|---|
| L1 Problem Structure | 8 | 3 | **37.5%** | motion/geometry, network/traffic, scheduling, diffusion, competition/game |
| L2 Modeling Pattern | 8 | 2 | **25.0%** | conservation law, flow balance, resource constraint, queue, spatial-temporal field, interaction/game |
| L3 Mathematical Formulation | 6 | 5(含1弱) | **83.3%** | graph; differential equation 仅 grey DE 弱覆盖 |
| L4 Solver/Algorithm | 6 | 4 | **66.7%** | numerical PDE, DP |

**U 型失衡**：L3/L4 覆盖较好（当前卡库本质是"算法卡"），L1/L2 覆盖极差（没有任何卡从问题结构或建模机理角度组织知识）。**最根本的缺失在 L2 Modeling Pattern（25%）**——这是连接"问题是什么"和"用什么数学"的中间层，当前完全断裂。

### 4.3 五题知识结构映射

| Problem | L1 Structure | L2 Pattern | L3 Formulation | L4 Solver | method_selection |
|---|---|---|---|---|---|
| **2024_A** | motion/geometry ✗ | trajectory/collision/geometric constraint ✗ | ODE + optimization + linear algebra (ODE弱) | numerical optimization + kinematics ✗ | **0** |
| **2022_C** | data/evaluation ✓ decision ✓ | N/A (data-driven) | statistics ✓ linear algebra ✓ | clustering ✓ regression ✓ PCA ✓ | **100** |
| **2020_B** | competition/game ✗ scheduling ✗ decision ✓ | state transition(MDP) ✗ resource constraint ✗ interaction/game ✗ | optimization ✓ probability ✓ | DP ✗ game theory ✗ Monte Carlo ✓ | **0** |
| **2018_A** | diffusion ✗ | spatial-temporal field ✗ conservation law ✗ | PDE(弱) + optimization ✓ | numerical PDE ✗ optimization ✓ | **0** |
| **2019_C** | network/traffic ✗ decision ✓ | queue ✗ flow balance ✗ interaction/game ✗ | optimization ✓ probability ✓ statistics ✓ | queuing ✗ optimization ✓ Monte Carlo ✓ decision ✓ | **100** |

### 4.4 缺失层定位

| Problem | method_selection | 最根本缺失层 | 级联效应 |
|---|---|---|---|
| 2024_A | 0 | **L1**（motion/geometry 零覆盖） | L1 缺失 → L2 无法激活 trajectory/collision → L3 无法选择 ODE → L4 无法选择运动学求解器 |
| 2020_B | 0 | **L4 + L2**（求解器+建模模式双缺） | 无 DP/game theory 卡 + 无 resource constraint/interaction 模式 → LLM 退选 mc-ga |
| 2018_A | 0 | **L1+L2+L4 三层联动** | 缺失最严重的一题：diffusion ✗ + spatial-temporal/conservation ✗ + numerical PDE ✗ |
| 2022_C | 100 | 无（舒适区） | L1/L3/L4 完整覆盖，纯数据驱动问题无 L2 物理模式 |
| 2019_C | 100 | **假阳性** | L1/L2 完全缺失，仅 L3/L4 solver 层面碰巧匹配；无法区分"系统覆盖"与"偶然匹配" |

### 4.5 evaluator 的测量盲区

e2e_metrics.py 的 method_selection 仅检查 L4 card family 是否匹配 benchmark core_methods（归一化+紧凑匹配），**完全不检查 L1-L3 层**。这意味着：
- 即使 LLM 在 L1/L2 层完全错误，只要 L4 碰巧选了一个 family 匹配的卡，也能得 100 分（2019_C 假阳性）
- 即使 LLM 在 L1/L2/L3 层完全正确，只要 L4 没有对应卡，就得 0 分（2024_A/2020_B/2018_A 假阴性）

---

## 5. Measurement Audit B: Decomposition Coverage 指标

> 详版：`research/P15/reports/_decomposition_audit.md`

### 5.1 当前公式

`core/tools/e2e_metrics.py` 第 270–284 行：当 `response.decomposition_aligned` 为 None 时（B0 恒为 None），退化为：

```python
aligned = min(len(questions), len(sub_qs))  # artifact 数量代理
value = 100 * min(aligned, gt_count) / gt_count
```

隐含假设：**一个 question artifact 恰好对应一个 GT 子问题**。这个假设在 B0 中完全不成立。

### 5.2 语义覆盖验证

对 5 题的 Q001 artifact 与 GT sub_questions 做语义对齐：

| Problem | GT count | Produced count | count_ratio | semantic_coverage | 失真度 |
|---|---|---|---|---|---|
| 2024_A | 5 | 1 | 20.0% | **100.0%** | 80.0% |
| 2022_C | 4 | 1 | 25.0% | **100.0%** | 75.0% |
| 2020_B | 3 | 1 | 33.3% | **100.0%** | 66.7% |
| 2018_A | 3 | 1 | 33.3% | **100.0%** | 66.7% |
| 2019_C | 4 | 1 | 25.0% | **100.0%** | 75.0% |

**关键证据**：所有 5 题的 Q001.payload.sub_questions 与 GT manifest 逐字一致（含任务描述、类型、关键变量、方法族），但 evaluator 只数 `len(questions) = 1`，从不读取 Q001 内部内容。

### 5.3 附加发现：data/payload 字段分裂

| 项目 | Q001.data | Q001.payload.sub_questions |
|---|---|---|
| 全部 5 题 | `{}`（空） | 完整，与 GT 逐字一致 |

即使未来 evaluator 改为解析 `data.sub_questions`，在当前注册 schema 下也会读到空。evaluator 需要同时检查 `payload.sub_questions` 和 `data.sub_questions`。

### 5.4 改进方向（未实现）

```
Gold sub-question
    ↓
semantic alignment (Embedding similarity 为主 + Keyword 快速路径 + LLM judge 边界仲裁)
    ↓
coverage matrix (covered/partial/missing per gold sub-question × produced artifact)
    ↓
weighted semantic coverage = Σ weight_i × coverage_i / Σ weight_i
```

- 对齐方法：Embedding similarity 为主路径，Keyword matching 为快速路径，LLM judge 处理边界 case
- 粒度：GT 子问题 × produced artifact 的矩阵
- 权重：默认等权 + 难度加权 sensitivity analysis
- 防偏差：calibration set、多方法一致性、LLM 去偏、可审计性、blind evaluation

---

## 6. Measurement Audit C: 其他指标

> 详版：`research/P15/reports/_other_metrics_audit.md`

### 6.1 innovation = 0（全部五题）— measurement_failure

**双重缺陷**：

1. **字段缺失**：B0 的 `register_external_artifact.py` 写 decision_log 时不含 `knowledge_refs` 字段。5 题的 decision_log 中 3 个 decision（D001/D002/D003）均无此字段。
2. **前缀不匹配**：e2e_metrics.py 第 418-431 行检查 `pat-` 前缀，但 `core/knowledge/patterns/` 下全部 6 个 pattern 使用 `ip-` 前缀（如 `ip-xxx`）。即使 decision_log 有 knowledge_refs，也永远匹配不到。

**结论**：innovation 指标的测量通道在 B0 阶段不存在，0 分不代表 Agent 没有创新。

### 6.2 model_correctness = None（全部五题）— not_applicable + measurement_gap

- 外部语义评分缺失 → UNAVAILABLE
- 但 **structural check 五题全 PASS**：M001 的 objective（str 非空）、constraints（list 非空）、variables（list 非空）三要素齐全
- structural PASS 说明 Agent 在 B0 约定范围内交付了结构完整的模型 artifact
- None 是因为 B0 不做实验所以无法语义评分，不是 Agent 建模失败

### 6.3 experiment_validity = None — not_applicable

B0 无 result artifact（0/5 题有实验结果）。B0 仅执行 DAG 前 5 节点（problem_understanding → model_construction → method_selection → solving_strategy → validation_plan），不包含实验执行。

### 6.4 validation_reliability = None — not_applicable

无 status.json（外部注册不经过 runtime 状态机），claims_total=0, claims_supported=0。无 paper/main.tex。

### 6.5 writing_completeness = None / end_to_end = None — not_applicable

- writing_completeness: 无 main.tex → None
- end_to_end: 无 rubric 评分响应 → None
- 这两个指标在 B0 阶段应明确标记为 `out_of_scope`，避免 None 语义模糊

### 6.6 measurement_integrity = 0/5（全部五题）— measurement_failure

- v1 判据：`created_by.startswith("agent")`
- 实际 created_by：角色名（`problem_understanding` / `model_construction` / `method_selection` 等），均不以 "agent" 开头
- 真实 agent provenance 在 `provenance.executor_type = "external_agent"` + `provenance.agent_identity = "doubao"` 子文档中
- 判据与注册约定不匹配，0/5 不代表 artifact 不是 agent 产生的

### 6.7 empty_artifact_filter — 无问题

全部 25 个 artifact（5 题 × 5 artifact）均有实质内容，0 个空壳被排除。

---

## 7. Research-layer Calibration 清单

> **声明**：以下为下一阶段（Research-layer calibration）的仪器校准方向，**不是 Agent 干预方案**。本阶段不执行任何修复。

### 7.1 优先级排序

| 优先级 | 校准项 | 类型 | 预期效果 |
|---|---|---|---|
| **P0** | 建立 L1 Problem Structure + L2 Modeling Pattern 标签体系 | 知识架构 | 解决 method_selection 假阴性的根本原因 |
| **P0** | 修复 decomposition evaluator：从 count_ratio 改为 semantic coverage | 测量仪器 | decomposition 分数从 20-33% 修正到实际语义覆盖率 |
| **P1** | 修复 innovation 指标：pat- → ip- 前缀 + decision_log knowledge_refs 通道 | 测量仪器 | innovation 从恒为 0 变为可测量 |
| **P1** | 修复 measurement_integrity：created_by 判据扩展为检查 provenance.executor_type | 测量仪器 | measurement_integrity 从 0/5 修正为实际值 |
| **P1** | 补充 L4 Solver 标签：numerical PDE, DP, game theory, queuing | 知识架构 | 减少 method_selection 假阴性 |
| **P2** | method_selection 升级为四层语义对齐（不只查 L4 card family） | 测量仪器 | 区分"系统覆盖"与"偶然匹配"，消除 2019_C 假阳性 |
| **P2** | 补充 L3 graph 标签，强化 differential equation（ODE/PDE） | 知识架构 | 完善数学表述层覆盖 |
| **P2** | B0 报告模板显式标记 out_of_scope 指标 | 报告规范 | 避免 None 语义模糊 |

### 7.2 知识架构校准方向（非"补方法卡"）

**不要**只做"缺 kinematics card → 加 kinematics card"。正确做法是：

1. **P0：建立 Modeling Knowledge Architecture v0.1**
   - 优先覆盖 L1 Problem Structure（10 标签）+ L2 Modeling Pattern（8 标签）
   - 对现有 16 张卡做 retro-tagging，映射到新的 L1/L2 标签
   - 不急于新建方法卡

2. **P1：补充 L4 Solver 标签和卡片**
   - numerical PDE（finite difference / finite element）
   - dynamic programming（确定性 DP + stochastic DP/MDP）
   - game theory
   - queuing theory

3. **P2：完善 L3 Mathematical Formulation**
   - graph 标签
   - 强化 ODE/PDE（非 grey DE 弱形式）

### 7.3 L1 Problem Structure 标签体系建议（10 标签）

| 标签 | 说明 | benchmark 对应题目 |
|---|---|---|
| motion/geometry | 运动学、几何建模、空间定位 | 2024_A, 2015_A, 2017_A, 2021_A, 2022_B, 2023_B, 2025_A, 2025_B |
| continuous_mechanics | 连续力学、振动、动力学 | 2016_A, 2019_A, 2019_B, 2022_A |
| diffusion/heat_transfer | 热传导、扩散、温度场 | 2018_A, 2020_A |
| network/traffic | 交通流、网络、路网 | 2016_B, 2019_C, 2024_E |
| scheduling/discrete | 离散调度、生产计划 | 2018_B, 2021_C, 2024_C |
| competition/game | 博弈、多玩家竞争、机制设计 | 2020_B, 2025_D |
| decision/evaluation | 多准则决策、综合评价、排序 | 2015_B, 2017_B, 2018_C, 2020_C, 2022_C, 2023_C, 2025_C, 2025_E |
| uncertainty/data | 不确定性传播、数据分析、统计建模 | 2015_C, 2016_C, 2017_C, 2021_B, 2024_B |
| supply_chain/operations | 供应链、运营、库存 | 2021_C, 2024_C |
| optical/inverse | 光学、反演、图像重建 | 2017_A, 2025_B |

### 7.4 L2 Modeling Pattern 标签体系建议（8 标签）

| 标签 | 说明 | 典型对应 |
|---|---|---|
| state_transition | 状态转移（MDP/递推/时序） | 2020_B (MDP), ARIMA/GM/LSTM |
| conservation_law | 守恒律（能量/质量/动量） | 2018_A (能量守恒) |
| flow_balance | 流量平衡（交通流/水流/物流） | 2019_C (出租车流) |
| distance_geometry | 距离/几何约束（轨迹/碰撞/定位） | 2024_A (螺线/碰撞) |
| resource_constraint | 资源约束（负重/预算/容量/时间窗） | 2020_B (水/食物/资金) |
| queue | 排队（到达/服务/等待） | 2019_C (出租车排队) |
| spatial_temporal_field | 时空场（温度场/浓度场/压力场） | 2018_A (温度场) |
| interaction_game | 交互/博弈（多玩家/双边匹配/机制设计） | 2020_B (多玩家), 2019_C (司机-乘客) |

---

## 8. 修正后的 Capability Baseline 预估

在测量仪器修复后（Research-layer calibration 完成后），B0 各指标的预期变化：

| 指标 | 当前 B0 观测 | 仪器修复后预期 | 变化原因 |
|---|---|---|---|
| method_selection (2024_A) | 0.0 | 待 fresh B0 测定 | L1/L2 标签建立后，LLM 可正确路由到 kinematics/geometric 家族；但需补 L4 卡才能命中 |
| method_selection (2020_B) | 0.0 | 待 fresh B0 测定 | 补 DP/MDP/game theory 卡 + L2 resource constraint 标签 |
| method_selection (2018_A) | 0.0 | 待 fresh B0 测定 | 补 PDE/finite difference 卡 + L1 diffusion + L2 spatial-temporal 标签 |
| method_selection (2022_C) | 100.0 | 可能维持 100 或微调 | 舒适区题目，四层对齐后分数应稳定 |
| method_selection (2019_C) | 100.0 | **可能下降** | 四层语义对齐后，2019_C 的浅层命中可能被识别为 L1/L2 缺失，分数可能从 100 下调 |
| decomposition_coverage | 20.0–33.3% | **接近 100%** | semantic coverage 替代 count_ratio 后，Q001 内部完整覆盖被识别 |
| innovation | 0.0 | 待 fresh B0 测定 | 修复前缀+通道后可测量，但 B0 阶段可能仍为 0（不要求创新声明） |
| measurement_integrity | 0/5 | **5/5** | 判据扩展为检查 provenance.executor_type 后，外部注册 artifact 被正确识别 |
| model_correctness | None | 待 fresh B0 测定 | 需引入语义评分器或扩大 structural check |
| experiment/validation/writing/e2e | None | 仍为 None（B0 范围外） | B0 不产生这些 artifact，需后续阶段评估 |

**关键提醒**：以上预估是"仪器修复后测量值可能如何变化"，不是"Agent 能力如何变化"。method_selection 分数上涨只能证明 measurement instrument validity ↑，不能直接证明 Agent capability ↑。

---

## 9. 本阶段成功标准核对

| 标准 | 状态 | 证据 |
|---|---|---|
| 1. B0 中每个低分指标，是测量仪器失败还是 Agent 能力失败？ | ✅ | 50 条归因记录，20 measurement_failure + 30 not_applicable + 0 capability_failure |
| 2. 方法卡库对 5 道题的覆盖情况如何？哪些 method_selection=0 是假阴性？ | ✅ | 四层覆盖审计：L1 37.5%, L2 25%, L3 83.3%, L4 66.7%；三题 0 分均为假阴性 |
| 3. decomposition_coverage 的当前公式有什么问题？Q001 内部实际覆盖了多少子问题？ | ✅ | count_ratio 代理失真；Q001.payload.sub_questions 与 GT 逐字一致，语义覆盖 100%，失真度 66.7-80% |
| 4. 修正测量仪器后，capability baseline 可能如何变化？ | ✅ | 第 8 节预估表 |
| 5. 后续 research-layer calibration 的明确清单是什么？ | ✅ | 第 7 节 8 项校准清单，标注仪器校准 ≠ Agent 干预 |

---

## 10. 交付物清单

| 文件 | 说明 |
|---|---|
| `research/P15/reports/MEASUREMENT_FAILURE_ATTRIBUTION.md` | 本报告（主交付物） |
| `research/P15/reports/failure_attribution.json` | 机器可读归因数据（50 条记录） |
| `research/P15/reports/_attribution_table.md` | 归因表人类可读详版（含逐条 evidence） |
| `research/P15/reports/_knowledge_architecture_audit.md` | 四层知识结构覆盖审计详版 |
| `research/P15/reports/_decomposition_audit.md` | Decomposition 指标审计详版 |
| `research/P15/reports/_other_metrics_audit.md` | 其他指标审计详版 |

---

## 11. 非回归声明

本阶段仅产生文档和数据分析文件，未修改：
- `core/` 下任何代码（包括 e2e_metrics.py、方法卡、runtime）
- `projects/` 下任何 B0 项目数据
- `.gitignore` / `.git/`
- 任何 evaluator 或 validator 逻辑

所有子任务严格遵守"只诊断，不修复"的边界。
