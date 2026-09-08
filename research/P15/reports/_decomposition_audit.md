# Decomposition Coverage 指标深度审计报告

> **审计性质**：只诊断，不修复。不修改 `e2e_metrics.py`、不实现新 evaluator、不修改任何 artifact 数据。
> **审计范围**：B0 baseline 5 道题（2024_A / 2022_C / 2020_B / 2018_A / 2019_C）
> **审计日期**：2026-09-08

---

## 1. 当前公式代码审查

### 1.1 确切实现（`core/tools/e2e_metrics.py` 第 270–284 行）

```python
# 1 decomposition：语义对齐数优先来自 response（agent 对照 GT 判定），
#   否则退化为数量比（确定性代理，detail 中注明口径）
sub_qs = gt.get("sub_questions") or []
decomp_value = None
decomp_detail: dict = {"gt_sub_questions": len(sub_qs),
                       "produced_questions": len(questions)}
if sub_qs:
    aligned = response.get("decomposition_aligned")
    if aligned is None:
        aligned = min(len(questions), len(sub_qs))
        decomp_detail["mode"] = "count_ratio（无语义对齐评分，退化口径）"
    else:
        decomp_detail["mode"] = "aligned（agent 对照 GT 判定）"
    decomp_value = round(100.0 * min(int(aligned), len(sub_qs))
                         / len(sub_qs), 1)
```

### 1.2 关键逻辑拆解

| 环节 | 代码行为 | 后果 |
|---|---|---|
| GT 子问题数 | `sub_qs = gt.get("sub_questions")` | 从 GT manifest 读取，B0 全部有值 |
| produced 计数 | `len(questions)` | **只数 question-type artifact 的数量**，不解析任何 artifact 内部内容 |
| aligned 口径 | `response.get("decomposition_aligned")` | 需要外部传入一个整数，表示 agent 判定的对齐子问题数 |
| 退化触发 | `aligned is None` | 当 response 中无 `decomposition_aligned` 字段时触发 |
| 退化公式 | `aligned = min(len(questions), len(sub_qs))` | 取 artifact 数与 GT 数的较小值 |
| 最终值 | `100 * min(aligned, gt_count) / gt_count` | 百分比 |

### 1.3 B0 为什么全部走退化口径

B0 pipeline 的 `response` 对象中**不包含 `decomposition_aligned` 字段**。该字段设计为由一个独立的"agent 对照 GT 判定"环节产出，但 B0 baseline 未实现该环节，因此 `response.get("decomposition_aligned")` 恒为 `None`，全部触发退化口径。

### 1.4 根本缺陷：artifact cardinality ≠ semantic decomposition coverage

当前退化公式的隐含假设是：**一个 question artifact 恰好对应一个 GT 子问题**。这个假设在 B0 中完全不成立：

- B0 的 `problem_understanding` 节点产出**唯一一个** Q001 artifact
- Q001 的 `payload.sub_questions` 字段中**完整列出了全部 GT 子问题**
- evaluator 只数 `len(questions) = 1`，从不读取 Q001 内部的 `sub_questions` 列表

因此，无论 Q001 内部分解得多么完整，count_ratio 永远等于 `1 / gt_sub_question_count`。

### 1.5 附加发现：data 与 payload 的字段分裂

任务描述预期 Q001 的 `data` 字段包含 `sub_questions`，但实际审计发现：

| 项目 | Q001.data | Q001.payload.sub_questions |
|---|---|---|
| 2024_A | `{}`（空） | 完整 5 条，与 GT 逐字一致 |
| 2022_C | `{}`（空） | 完整 4 条，与 GT 逐字一致 |
| 2020_B | `{}`（空） | 完整 3 条，与 GT 逐字一致 |
| 2018_A | `{}`（空） | 完整 3 条，与 GT 逐字一致 |
| 2019_C | `{}`（空） | 完整 4 条，与 GT 逐字一致 |

Q001 的分解内容全部存储在 `payload` 中，`data` 为空。这意味着即使未来 evaluator 改为解析 `data.sub_questions`，在当前注册 schema 下也会读到空。evaluator 需要同时检查 `payload.sub_questions` 和 `data.sub_questions`。

---

## 2. 五题 Coverage Matrix

### 判定标准说明

- **✓ (covered)**：Q001 内容中明确提及该子问题的核心任务/变量/方法
- **partial**：Q001 提及了相关内容但不完整
- **✗ (missing)**：Q001 完全没有涉及该子问题

> 注：由于 Q001.data 为空，以下判定基于 Q001.payload 的完整内容（sub_questions + key_variables + model_family_hint + difficulty_assessment）。这是 Q001 artifact 实际承载分解信息的位置。

### 2.1 2024_A（板凳龙闹元宵）

**GT 子问题数**：5 | **Produced artifact 数**：1 | **count_ratio**：20.0%

| GT 子问题 | 类型 | Q001 覆盖 | 判定依据 |
|---|---|---|---|
| Q1 | forward_simulation | ✓ | payload.sub_questions[0] 逐字列出："沿螺距55cm等距螺线顺时针盘入…求0-300s每秒各把手位置和速度"；key_variables 含 v0、n_handles |
| Q2 | collision_detection | ✓ | payload.sub_questions[1] 逐字列出："确定盘入终止时刻使得板凳间不发生碰撞"；key_variables 含 W（板宽，碰撞判据） |
| Q3 | geometric_optimization | ✓ | payload.sub_questions[2] 逐字列出："确定最小螺距使龙头能盘入到调头空间边界"；key_variables 含 R_turn=4.5m |
| Q4 | curve_optimization_and_simulation | ✓ | payload.sub_questions[3] 逐字列出："S形调头曲线由两段相切圆弧组成…能否调整圆弧使调头曲线变短" |
| Q5 | velocity_constrained_optimization | ✓ | payload.sub_questions[4] 逐字列出："确定龙头最大行进速度使各把手速度均不超过2m/s" |

**semantic coverage = (5 + 0.5×0) / 5 × 100 = 100.0%**

### 2.2 2022_C（古代玻璃制品成分分析）

**GT 子问题数**：4 | **Produced artifact 数**：1 | **count_ratio**：25.0%

| GT 子问题 | 类型 | Q001 覆盖 | 判定依据 |
|---|---|---|---|
| Q1 | statistical_analysis_and_regression_prediction | ✓ | payload.sub_questions[0] 逐字列出风化与类型/纹饰/颜色关系、风化前成分预测 |
| Q2 | classification_and_clustering | ✓ | payload.sub_questions[1] 逐字列出高钾/铅钡分类规律、亚类划分、合理性和敏感性分析 |
| Q3 | supervised_classification | ✓ | payload.sub_questions[2] 逐字列出未知类别玻璃文物鉴别、敏感性分析 |
| Q4 | correlation_analysis | ✓ | payload.sub_questions[3] 逐字列出化学成分关联关系、类别间差异比较 |

**semantic coverage = (4 + 0.5×0) / 4 × 100 = 100.0%**

### 2.3 2020_B（穿越沙漠）

**GT 子问题数**：3 | **Produced artifact 数**：1 | **count_ratio**：33.3%

| GT 子问题 | 类型 | Q001 覆盖 | 判定依据 |
|---|---|---|---|
| Q1 | deterministic_optimization | ✓ | payload.sub_questions[0] 逐字列出：天气全已知、确定性动态规划、第一关和第二关 |
| Q2 | stochastic_optimization | ✓ | payload.sub_questions[1] 逐字列出：仅知当日天气、MDP/随机动态规划、第三关和第四关 |
| Q3 | game_theory | ✓ | payload.sub_questions[2] 逐字列出：n名玩家竞争/协作、开环博弈+闭环博弈、第五关和第六关 |

**semantic coverage = (3 + 0.5×0) / 3 × 100 = 100.0%**

### 2.4 2018_A（高温作业专用服装设计）

**GT 子问题数**：3 | **Produced artifact 数**：1 | **count_ratio**：33.3%

| GT 子问题 | 类型 | Q001 覆盖 | 判定依据 |
|---|---|---|---|
| Q1 | forward_simulation | ✓ | payload.sub_questions[0] 逐字列出：75°C、II层6mm、IV层5mm、90分钟、温度分布、problem1.xlsx；含完整 boundary_conditions |
| Q2 | single_variable_optimization | ✓ | payload.sub_questions[1] 逐字列出：65°C、IV层5.5mm、II层最优厚度、60分钟≤47°C、超44°C≤5min；含 decision_variable |
| Q3 | multi_variable_optimization | ✓ | payload.sub_questions[2] 逐字列出：80°C、II层+IV层最优厚度、30分钟约束；含 decision_variables 数组 |

**semantic coverage = (3 + 0.5×0) / 3 × 100 = 100.0%**

### 2.5 2019_C（机场出租车）

**GT 子问题数**：4 | **Produced artifact 数**：1 | **count_ratio**：25.0%

| GT 子问题 | 类型 | Q001 覆盖 | 判定依据 |
|---|---|---|---|
| Q1 | driver_decision | ✓ | payload.sub_questions[0] 逐字列出：司机决策因素影响机理、A进蓄车池vs B放空回市区、选择策略；含 core_task + key_challenge |
| Q2 | data_calibration | ✓ | payload.sub_questions[1] 逐字列出：收集机场+城市出租车数据、选择方案、模型合理性和因素依赖性 |
| Q3 | layout_optimization | ✓ | payload.sub_questions[2] 逐字列出：两条并行车道、上车点设置、安全条件、乘车效率最高 |
| Q4 | priority_mechanism | ✓ | payload.sub_questions[3] 逐字列出：短途载客优先权、收益均衡、优先安排方案 |

**semantic coverage = (4 + 0.5×0) / 4 × 100 = 100.0%**

---

## 3. Semantic Coverage 估算与对比

### 3.1 失真量化总表

| Problem | GT count | Produced count | count_ratio | semantic_coverage | 失真度 |
|---|---|---|---|---|---|
| 2024_A | 5 | 1 | 20.0% | 100.0% | **80.0%** |
| 2022_C | 4 | 1 | 25.0% | 100.0% | **75.0%** |
| 2020_B | 3 | 1 | 33.3% | 100.0% | **66.7%** |
| 2018_A | 3 | 1 | 33.3% | 100.0% | **66.7%** |
| 2019_C | 4 | 1 | 25.0% | 100.0% | **75.0%** |

**失真度定义**：`|count_ratio - semantic_coverage| / semantic_coverage`

### 3.2 关键观察

1. **5 题 semantic_coverage 均为 100%**：Q001.payload.sub_questions 与 GT manifest 的 sub_questions 逐字一致（同一 `problem_understanding` agent 运行的产物，共享相同 `input_sha256`）。

2. **失真度与 GT 子问题数负相关**：GT 子问题越多，count_ratio 越低，失真越大。2024_A（5 个子问题）失真最严重（80%），2020_B/2018_A（3 个子问题）失真相对较小（66.7%）。这意味着 count_ratio 指标对"题目本身有多少个子问题"极度敏感，而非对"系统分解得好不好"敏感。

3. **count_ratio 的变异完全由 GT 结构驱动**：5 题的 produced count 均为 1，因此 count_ratio = 1/gt_count。指标的横截面差异 100% 来自 GT 子问题数的差异，与系统表现无关。

4. **semantic coverage 100% 的局限性**：由于 GT manifest 与 Q001 来自同一 agent 运行，100% coverage 存在"自证"（self-fulfilling）性质——GT 不是独立标注的金标准，而是 agent 自身输出的副本。这是 benchmark 设计层面的问题，不影响"count_ratio 测量了错误的东西"这一结论。

---

## 4. 反例分析

### 反例 1：低 count 但高 semantic coverage —— 2024_A 板凳龙

**现象**：
- count_ratio = 20.0%（1 个 artifact / 5 个 GT 子问题）
- semantic_coverage = 100.0%

**具体证据**：
Q001.payload 中包含：
- `sub_questions`：5 条，每条含 `id`、`text`（完整题目原文）、`type`（forward_simulation / collision_detection / geometric_optimization / curve_optimization_and_simulation / velocity_constrained_optimization）
- `key_variables`：10 个变量，覆盖全部 5 个子问题的核心参数（N=223 节、L_head=3.41m、p_in=0.55m、v0=1.0m/s、R_turn=4.5m 等）
- `model_family_hint`：`multibody_dynamics + differential_geometry + numerical_optimization`，覆盖 Q1–Q5 的方法族
- `difficulty_assessment.sub_question_difficulty`：对 Q1–Q5 逐一给出难度评级

**结论**：Q001 一个 artifact 内部完整承载了 5 个 GT 子问题的分解信息，包括任务描述、类型标注、关键变量、方法族提示和难度评估。count_ratio 给 20% 严重低估了实际分解覆盖率。

### 反例 2：高 count 但可能低 semantic coverage —— B0 中不存在，但理论风险明确

**B0 实际情况**：5 道题全部只有 1 个 question artifact（Q001），不存在"高 count"案例。所有 M001 model artifact 的 `question` 字段均指向 Q001，进一步确认了单 artifact 模式。

**理论反例构造**：
假设某 pipeline 将 2024_A 拆成 5 个 question artifact（Q001–Q005），但：
- Q001–Q004 全部只重复 Q1（forward_simulation）的内容（因为 agent 反复生成同一个子问题）
- Q005 涉及 Q2

此时 count_ratio = min(5, 5)/5 = 100%，但 semantic coverage 仅覆盖 Q1（✓）和 Q2（✓），Q3/Q4/Q5 全部 ✗，实际 semantic coverage = 2/5 = 40%。

**count_ratio 无法检测的失效模式**：
- **冗余拆分**：多个 artifact 内容重复，对应同一个 GT 子问题
- **错误拆分**：artifact 数量够但内容偏离 GT 子问题
- **粒度不匹配**：一个 artifact 覆盖多个 GT 子问题（B0 的实际情况），或一个 GT 子问题被拆到多个 artifact 中

**为什么 B0 没有暴露这个方向的问题**：B0 的 `problem_understanding` 节点设计为产出单一聚合 artifact，天然避免了"冗余拆分"和"错误拆分"。但这恰恰意味着 count_ratio 在 B0 中只暴露了"粒度不匹配"这一种失效模式，且全部表现为系统性低估。

---

## 5. 改进方向设计（不实现）

### 5.1 架构总览

```
Gold sub_questions (GT manifest)
    │
    ▼
┌─────────────────────────────────┐
│  Semantic Alignment Engine      │
│  (keyword / embedding / LLM)    │
│  输入：GT sub_q + produced      │
│        sub_questions (从 Q001   │
│        payload/data 解析)        │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Coverage Matrix                │
│  行：GT sub_questions           │
│  列：Produced sub_questions     │
│  单元格：covered / partial /    │
│          missing + confidence   │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Weighted Semantic Coverage     │
│  = Σ w_i × coverage_i / Σ w_i  │
│  + 冗余惩罚（多个 produced      │
│    sub_q 映射到同一 GT sub_q）  │
└─────────────────────────────────┘
```

### 5.2 Semantic Alignment 方法选择

| 方法 | 原理 | 优点 | 缺点 | 适用场景 |
|---|---|---|---|---|
| **Keyword matching** | 提取 GT sub_q 的核心术语（名词短语、方法名、变量名），在 produced 内容中做精确/模糊匹配 | 确定性、可复现、零成本、可审计 | 无法捕捉语义等价（"碰撞检测" vs "碰撞判定"）、对表述变化敏感 | 初筛、快速回归测试 |
| **Embedding similarity** | 用 sentence embedding 模型（如 BGE-M3、text-embedding-3）将 GT sub_q 文本和 produced sub_q 文本编码为向量，计算 cosine similarity，设阈值判定 covered（≥0.85）/ partial（0.65–0.85）/ missing（<0.65） | 捕捉语义等价、对表述变化鲁棒、中等成本 | 阈值需要校准、对专业术语可能不够精准、embedding 模型本身有偏差 | 主力对齐方法 |
| **LLM judge** | 构造 prompt："判断以下 produced 子问题是否覆盖了 GT 子问题的核心任务，输出 covered/partial/missing 和理由" | 最灵活、能理解复杂语义、能给出判定理由 | 非确定性（需多次运行取众数）、成本高、存在 LLM 自身偏差、可审计性弱 | 边界案例仲裁、embedding 分数在阈值附近时的二次判定 |
| **混合（推荐）** | 1) Keyword matching 做初筛（高置信命中直接判 covered）；2) Embedding similarity 做主判定；3) LLM judge 仅对 embedding 分数在 partial 区间（0.65–0.85）的边界案例做仲裁 | 兼顾效率、准确性和可审计性；LLM 调用量最小化 | 实现复杂度较高、需要三层阈值校准 | 生产级 evaluator |

**推荐方案**：Embedding similarity 为主 + Keyword matching 为快速路径 + LLM judge 为边界仲裁。具体阈值需要在一个人工标注的小型 calibration set（建议 20–30 个 GT-produced 对子）上校准。

### 5.3 Coverage Matrix 粒度设计

**矩阵维度**：
- **行**：GT sub_questions（来自 `gt.payload.sub_questions`，数量固定）
- **列**：Produced sub_questions，来源优先级：
  1. 每个 question artifact 的 `payload.sub_questions`（B0 的实际情况）
  2. 每个 question artifact 的 `data.sub_questions`（schema 预期位置）
  3. 如果 artifact 内部无 sub_questions 列表，则将整个 artifact 作为一个 produced sub_q（退化到当前行为，但至少解析内容）

**单元格内容**：
```json
{
  "gt_id": "Q1",
  "produced_id": "Q001#sub1",
  "status": "covered | partial | missing",
  "confidence": 0.0-1.0,
  "alignment_method": "keyword | embedding | llm",
  "alignment_score": 0.0-1.0,
  "evidence": "匹配到的关键词/文本片段"
}
```

**行级聚合**：对每个 GT sub_q，取所有 produced sub_q 中的最高 status（covered > partial > missing），作为该 GT 子问题的覆盖状态。这避免了"一个 GT 子问题被多个 produced 部分覆盖"时的信息丢失。

**冗余检测**：如果多个 produced sub_q 都映射到同一个 GT sub_q 且 status=covered，标记为"冗余拆分"，在 detail 中报告但不扣分（冗余不影响覆盖率，但影响分解质量的另一维度——granularity alignment）。

### 5.4 Weighted Coverage 权重设计

| 权重方案 | 公式 | 优点 | 缺点 | 推荐度 |
|---|---|---|---|---|
| **等权（默认）** | `w_i = 1` | 简单、无偏、可复现 | 不反映子问题难度/重要性差异 | ★★★★★ 作为 baseline |
| **按难度加权** | `w_i = difficulty_score_i`（从 GT manifest 的 difficulty_assessment 读取，或由 LLM 评定） | 难的子问题覆盖更有价值 | 难度评定主观、GT manifest 中难度字段格式不统一 | ★★★ 作为 sensitivity analysis |
| **按分值加权** | `w_i = official_points_i`（如果竞赛题目有公开分值分布） | 客观、与竞赛评分对齐 | 国赛题目通常不公开各小题分值 | ★★ 仅当分值可获取时 |
| **按信息含量加权** | `w_i = len(variables_i) + len(constraints_i)` | 客观、可自动计算 | 变量数不等于重要性 | ★★ 辅助参考 |

**推荐**：默认等权，同时输出按难度加权的结果作为 sensitivity analysis。在 detail 中同时报告两个分数，让使用者了解权重选择对结论的影响。

### 5.5 防止 Evaluator 本身引入新的测量偏差

1. **Calibration set 强制要求**：在正式使用前，必须在一个 ≥20 个 GT-produced 对子的人工标注集上校准阈值（embedding 的 covered/partial/missing 分界点）。报告 calibration set 上的准确率、混淆矩阵。

2. **多方法一致性报告**：同时运行 keyword matching 和 embedding similarity，报告两者的一致率。如果一致率 < 80%，说明对齐不稳定，需要人工审查分歧案例。

3. **LLM judge 的去偏**：
   - 每次判定运行 ≥3 次，取众数（降低随机性）
   - 使用 ≥2 个不同模型（如 doubao-pro + gpt-4o），报告跨模型一致率
   - Prompt 中明确要求"只基于文本内容判定，不要因为来源是 B0 baseline 就放宽或加严标准"
   - 对 LLM judge 的输入做顺序随机化（GT 在前还是 produced 在前），检测顺序偏差

4. **可审计性**：每个 coverage 判定必须存储 evidence（匹配到的关键词、embedding 分数、LLM 判定理由），使得任何分数都可以追溯到具体的文本依据。禁止只输出一个数字。

5. **Blind evaluation**：evaluator 不应知道 produced 内容来自哪个 run（B0 / B1 / B2），避免对已知 baseline 的预期偏差。在输入 evaluator 前，剥离 artifact 的 provenance 信息。

6. **与人工标注的对标**：定期（如每 10 个新项目）抽取 10% 的 coverage 判定由人工复核，计算 evaluator 与人工的一致率。如果一致率 < 90%，触发阈值重新校准。

7. **GT 独立性问题**：当前 GT manifest 与 Q001 来自同一 agent 运行，导致 semantic coverage 天然偏高。长期应建立**独立人工标注的 GT sub_questions**，或至少在 GT 生成时使用与 problem_understanding 不同的模型/ prompt，减少自证偏差。

---

## 6. 结论：当前 Decomposition Coverage 低分在多大程度上是测量失真

### 6.1 核心结论

**B0 的 decomposition_coverage 低分（20.0%–33.3%）几乎 100% 是测量失真，而非系统分解能力不足。**

具体证据链：

1. **5 题的 Q001 artifact 内部均完整列出了全部 GT 子问题**（payload.sub_questions 与 GT 逐字一致），semantic coverage 估算为 100%。

2. **count_ratio 的横截面变异 100% 由 GT 子问题数驱动**：5 题 produced count 均为 1，count_ratio = 1/gt_count。指标不反映任何系统表现差异。

3. **evaluator 完全不解析 question artifact 的内部内容**：只数 `len(questions)`，不读取 `payload.sub_questions` 或 `data.sub_questions`。这是一个纯 cardinality 指标，被命名为 "decomposition_coverage" 属于指标定义错误。

4. **失真度范围 66.7%–80.0%**：GT 子问题越多的题目，失真越严重。2024_A（5 个子问题）的 20% 分数意味着测量值仅为真实值的 1/5。

### 6.2 但需要注意的保留意见

1. **100% semantic coverage 存在自证偏差**：GT manifest 与 Q001 来自同一 agent 运行（相同 input_sha256），GT 不是独立金标准。如果使用独立人工标注的 GT，coverage 可能低于 100%。但无论独立 GT 的 coverage 是 80% 还是 60%，都远高于 count_ratio 的 20%–33%，测量失真的结论不变。

2. **"列出子问题"不等于"解决子问题"**：decomposition_coverage 衡量的是分解的完整性，不是求解的完整性。Q001 列出了全部子问题 = 分解完整。下游的 model/result artifact 是否真正求解了每个子问题，是其他指标（如 result_coverage、method_selection）的职责。当前 decomposition_coverage 不应承担求解质量的测量。

3. **count_ratio 作为退化口径有其设计意图**：在没有 semantic alignment 的情况下，count_ratio 是一个确定性的下界代理。问题不在于退化口径本身，而在于 **B0 永远走退化口径**（因为 `decomposition_aligned` 字段从未被填充），且退化口径的隐含假设（1 artifact = 1 sub_question）与 B0 的实际 artifact 结构（1 artifact = N sub_questions）根本冲突。

### 6.3 优先级建议

| 优先级 | 行动 | 预期效果 |
|---|---|---|
| **P0** | evaluator 解析 Q001.payload.sub_questions（和 data.sub_questions），与 GT 做逐条匹配 | B0 decomposition_coverage 从 20–33% 提升至 ≥90%，消除系统性低估 |
| **P1** | 实现 embedding-based semantic alignment，替代纯字符串匹配 | 支持跨表述的语义对齐，为 B1/B2 多 artifact 场景做准备 |
| **P2** | 建立独立人工标注的 GT sub_questions calibration set | 消除自证偏差，校准 embedding 阈值 |
| **P3** | 增加 granularity alignment 维度（检测冗余拆分和过粗/过细分解） | 补全 decomposition 质量的多维评估 |

### 6.4 一句话总结

> 当前 decomposition_coverage 在 B0 上测量的不是"问题分解的语义覆盖率"，而是"GT 子问题数的倒数"。5 题的低分全部是指标定义与 artifact 结构不匹配导致的系统性测量失真，失真度 66.7%–80.0%。

---

*审计完成。本报告仅做诊断，未修改任何代码或数据。*
