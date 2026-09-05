# Competition Intelligence Audit — P8-0 知识层全面审计

> 日期：2026-09-05。审计对象：`core/knowledge/`、`core/schemas/v3/knowledge/`、
> `core/runtime/knowledge/`、`core/runtime/modeling/`、`core/runtime/decisions/`。
> 方法：逐实体盘点 Current Entity / Location / Schema / Consumer / Missing Semantics /
> Required Change。重构决策全部基于本表，不凭感觉。

## 1. 实体清单与消费关系

### 1.1 MethodCard（16 张，`core/knowledge/methods/cards/mc-*.yaml`）

| 项 | 现状 |
|---|---|
| Schema | `core/schemas/v3/knowledge/method_card.schema.json`（required: card_id/name/family/version/problem_types/good_for/requires/risks/validation/often_combined_with/anti_patterns） |
| 消费者 | `KnowledgeRetriever.recommend`（problem_types 命中 +3/个；requires_data 硬过滤；sample_size 档过滤；time_series 加分）→ `MethodArena.select` → DecisionLog |
| 缺失语义 | ① **无结构化 applicability**（只有 free-text good_for/requires）→ 无法做 capability matching；② **score 是裸 int**（不可解释、无维度拆分）；③ **risks 无结构**（无 overfitting/data_sensitivity 等维度、无 severity）→ 无法产生 risk penalty；④ **无 evidence_requirements**（validation 是自由文本）→ ExperimentPlanner 无法反向生成实验；⑤ 无 typical_metrics / compatible/incompatible / prerequisites / source_refs / confidence |
| 有字段无消费者 | `match.multi_objective`、`match.handles_uncertainty`（loader 解析但 recommend 不打分）；`anti_patterns`（仅文档语义）；`reference`（仅人读） |
| Required Change | P8-1 扩 schema：`applicability{positive,negative}` / `risk{5 维}` / `evidence_requirements{minimum,recommended}` / `objective_types` / `typical_metrics` / `compatible_methods` / `incompatible_methods` / `prerequisites` / `costs{data,compute}` / `robustness` / `overfitting_risk` / `competition_suitability` / `innovation_potential` / `source_refs` / `confidence` / `status`。全部**可选字段 + 向后兼容**（旧卡缺省不炸）。 |

### 1.2 FailureMemory（10 条，`core/knowledge/failures/fm-*.yaml`）

| 项 | 现状 |
|---|---|
| Schema | `failure.schema.json`（failure_id/title/problem_context/method/method_family/failure_mode/symptom/root_cause/detection/fix/avoidance/applies_to/source） |
| 消费者 | `retriever.failures_for`（known_failures 显式引用 + family 匹配 + applies_to 反查）→ `Recommendation.related_failures`。**仅展示，不影响打分** |
| 缺失语义 | ① 无 severity/confidence 结构化（无 risk penalty 依据）；② 无 recovery 结构（fix/avoidance 是文本，不产生 required validation）；③ 与 Decision 无绑定（决策不记得踩过哪些失败） |
| Required Change | P8-1 增 `severity`（low/medium/high）/`confidence`/`detection_signal`/`recovery[]`/`version/status`；P8-5 接入打分（risk penalty + required_experiments） |

### 1.3 InnovationPattern（6 条，`core/knowledge/patterns/ip-*.yaml`）

| 项 | 现状 |
|---|---|
| Schema | `pattern.schema.json`（pattern_id/title/problem_types/baseline_method/innovation/required_evidence/risks/examples/cards） |
| 消费者 | `retriever.patterns_for(problem_types)`（交集排序）。**Arena / Planner / Critics 均未消费**——创新只被人读，从不进实验计划 |
| 缺失语义 | 无 expected_benefit / implementation_cost / novelty_level / validation_protocol / competition_fit 结构；candidate → experiment 的通道不存在 |
| Required Change | P8-1 增字段；P8-6 建 `InnovationCandidate`（candidate → required experiments → evidence），无证据的创新只能是 hypothesis |

### 1.4 Competition Pack（现状：**不存在结构化实体**）

| 项 | 现状 |
|---|---|
| 位置 | 分散三处：`core/knowledge/bench/cumcm/rubric_20xx.json`（22 年评分细则，仅 benchmark.py 消费）；`core/knowledge/data-sources/DATA-SOURCES.md`（美赛题型→数据源映射，markdown 表）；`docs/` 里 TEAM_GUIDE 等 |
| 缺失语义 | judging_preferences / time_constraints / high_risk_methods / typical_model_combinations 等完全无结构化实体；ModelArena / Planner / JudgeCritic 都消费不到 |
| Required Change | P8-1 新建 `competition_pack.schema.json` + `core/knowledge/competition/cumcm.yaml`、`mcm.yaml`（yaml 不是目录扩张——落在既有 `core/knowledge/` 下）；P8-2 loader 支持；P8-3 打分接入 competition 维度 |

### 1.5 决策与追踪（`core/runtime/decisions/log.py`）

| 项 | 现状 |
|---|---|
| 消费者 | `MethodArena.select(record=True)` 写入 chosen/alternatives/reasoning；`state.py decision-add`（legacy） |
| 缺失语义 | Decision **不绑定 knowledge_id + knowledge_version**（卡片升级后历史决策不可重现）；无 explain_decision API；无 knowledge_refs/failure_refs/required_validation 结构 |
| Required Change | P8-8：Decision 增 `knowledge_refs: [{id, version}]` / `required_validation` / `score_breakdown`；`explain_decision()` 输出完整链路 |

### 1.6 纯文档层（不升级为结构，明确边界）

`methodology/`（50 篇）、`paper-cases/`、`pitfalls/`、`playbooks/`、`empirical/`、`problems/`、`review/`：
LLM/人读资产，**P8 不结构化**（避免"堆 Markdown"）。仅 `pitfalls/` 中已被
FailureMemory 引用的条目维持 source 回指关系。

## 2. 审计十二问结论（对应任务书）

1. 实体：MethodCard / FailureMemory / InnovationPattern / CompetitionRubric(json) / DataSources(md) / DecisionLog（runtime）。
2. 纯文档：methodology、paper-cases、playbooks、problems、review。
3. 可程序消费：前三张卡 + rubric（仅 benchmark）。
4. 无消费者字段：match.multi_objective、match.handles_uncertainty、anti_patterns、reference（见 1.1）。
5. 重复：`risks`（card）与 `avoidance`（failure）语义重叠但载体不同——保留双层，card.risk 引结构化维度。
6. 冲突：现有 16 卡 × 10 失败 × 6 模式未见显式矛盾，但**无检测机制**（P8-9 建最小检测）。
7. 来源不可解释：卡片仅 `reference` 单字段；无 source_type/confidence（P8-1 补）。
8. 适用条件不可判定：good_for 是自然语言（P8-1 applicability 解决）。
9. 失败风险不可判定：risks 无 severity（P8-1 risk 五维解决）。
10. 无法参与模型选择：同 8（applicability 缺失导致只靠标签）。
11. 无法参与实验设计：validation 自由文本无法反向生成实验（P8-1 evidence_requirements 解决）。
12. 无法参与创新判断：pattern 无成本/收益/验证协议（P8-6 解决）。

## 3. 改造路线（后续阶段的依据）

```text
P8-1  Schema:        四实体 schema 升级（全部可选字段，向后兼容）
P8-2  Loader:        cards.py 解析新字段 + competition pack 加载 + 冲突检测 + 版本绑定
P8-3  Matching:      retriever → RecommendationScore（9 维拆分 + matched/missing/violations）
P8-4  Candidate:     core/runtime/modeling/candidates.py（baseline/改进/组合/创新候选生成排序）
P8-5  Failure:       failures_for → risk_penalty + required_validation（进打分与实验计划）
P8-6  Innovation:    patterns → InnovationCandidate → required experiments
P8-7  Planner:       ExperimentPlan 增 purpose/hypothesis/metrics/decision_rule/cost/information_gain
P8-8  Trace:         Decision 绑 knowledge_refs(version) + explain_decision()
P8-9  Conflict:      detect_knowledge_conflicts()（compatible×incompatible、recommended×high_risk）
P8-10 Tests:         CI-01~CI-10 不变量 + A1/A2/A3 场景（约束变化 → 推荐合理变化且可解释）
```

边界（硬约束回执）：不新增 Agent；不新增顶层目录（competition pack yaml 落在
`core/knowledge/competition/`——knowledge 内部子目录，非顶层）；不改 P7 契约；
不做论文语言优化；不批量新增知识文件（16 卡/10 失败/6 模式数量不变，只升级结构）。
