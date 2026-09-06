# Cross-Question Synthesis Audit — P12-0（只读审计）

> 审计范围：Question/Dependency 的真实落点、Finding↔Claim 关系、Research State
> 与 projection 边界、跨问题失效传播的实际情况。**本阶段零代码修改、零顺手修。**
> 发现的问题全部记录于 §5，留给 P12-1 及后续阶段处理。

## 1. Ontology（问 1–4）

### Q1 Question 当前是什么实体？

三处存在、三种形态：

| 层 | 形态 | ID/键 |
|---|---|---|
| Registry | artifact（type=question，ID Q*） | artifact_id 即 Q001…；`question` 字段为空（不能自指） |
| State | `state.questions[qid]` 字典条目 | status/models/experiments/claims/dependencies/retry_count |
| DAG | per_question 节点实例 `<node>@<qid>` | 不存在 question 级节点 |

**语义缺口**：三处中没有任何一处携带"科学依赖"信息（见 Q5/Q6）。

### Q2 depends_on 的真正来源在哪里？

| 层 | 现状 |
|---|---|
| Composer | `expand_questions`（dag.py:199）把 question_ids **并行展开**——`*` 引用展开为**全部**问题，不存在"Q002 依赖 Q001"的声明机制 |
| Registry | question artifact 创建时**未写 depends_on**（session.py:76 `create("question", title=q)`） |
| State | `ensure_question(dependencies=…)` **支持依赖参数**（model.py:145）且已有 `blocked_by_dependencies()`（model.py:189，依赖未 complete/validated 则阻塞）——**但 session 调用（session.py:74）从不传依赖** |
| Finding 层 | `question_dependencies()`（paragraphs.py）从 registry question artifact 的 depends_on 派生——因上游为空，恒返回 [] |

结论：**执行依赖只存在于 DAG 模板节点间（且无问题间链），科学依赖在全栈不存在。**
State 层的依赖机制是现成插座，插头从未插上。

### Q3 Finding 与 Claim 的关系？

* Claim = Registry artifact（C*），支撑来自 supports 入边（result→claim）。
* Finding = **派生对象**（findings.py），从 result 聚合：descriptive（每活跃结果一条）
  与 comparative（同 question ≥2 结果时可比较，否则 UNKNOWN 假设态）。
* 两者**无直接引用**：Finding 不引用 Claim，Claim 不知道 Finding。它们是同一
  证据链的两个独立派生视图（Claim 经 supports 边；Finding 经 produces/supported_by）。
  P12 需要裁决：synthesis 引用 Finding 时是否要求其对应 Claim 存在且 active。

### Q4 哪些属于 Research State，哪些只是 projection？

| Research State（事实层） | Derived/Projection（派生层） |
|---|---|
| Registry artifacts + lifecycle + invalidation 标记 | FindingGraph（每次重算） |
| Evidence Graph relations | Claim Coverage Matrix |
| State（问题状态/维度/workflow） | ScientificNarrative IR / Reasoning edges |
| DecisionLog（含 knowledge_refs 版本绑定） | CrossQuestionSynthesis（P12 将新增，派生式） |
| quality_report.json（落盘快照） | ArgumentUnit / ParagraphPlan / Renderer 输出 |

判定标准（沿用 P10 裁决）：**存储且参与失效传播 = State；每次从 State 重算 = 派生**。
Synthesis 按任务书归右列。

## 2. Dependency（问 5–8）

### Q5 Question dependency 是 DAG 还是普通引用？

都不是——**三种半成品并存**：DAG 只有聚合级耦合（evidence_build 依赖
experiment_critique*@all）；State 有依赖插座（未接线）；Registry 无依赖字段。
问题间**执行顺序**目前由 question_ids 列表顺序隐含表达，无显式语义。

### Q6 dependency 是否会进入 Registry？

**不会。** question artifact 无 depends_on；DecisionLog 的 knowledge_refs 绑定
方法卡而非问题；跨问题产物继承关系（Q1 产物被 Q2 消费）在事实层零记录。

### Q7 invalidation 如何跨 question 传播？

**当前完全隔离**（红队 L 已验证为污染防线）：
* 传播沿图边走；确定性管线的所有边（produces/supports/visualized_by/validated_by/
  assumes）都在同 question 链内。
* 图层唯一的跨问题合法通道是 `derived_from`（RELATION_TYPES 中 from/to 为 None）
  ——**通道存在但无生产者**。
* `reset_question` 明确排除其他 question 的节点。

结论：P12 的跨问题失效传播**不是修 bug 而是新增语义**——必须与 P7 的
kill/reval 分档和 P12-0 的隔离红线共存（传播只能沿**显式声明的科学依赖**走，
不能因 derived_from 弱边洪水填充）。

### Q8 哪些关系被错误限制在同 question？

| 位置 | 限制 | 是否错误 |
|---|---|---|
| `FindingGraph.compares_with` | 要求同 question | ✅ 限制合理但**缺少合法跨问题路径**——应按依赖声明+度量兼容放行，而非删除限制 |
| NarrativeReasoningGraph 的 compares | findings 同 question 才产生 | 同上 |
| EvidenceGraph RELATION_TYPES | derived_from 无类型限制 | 不是限制，是**无语义的自由边**——P12 需要给它科学依赖的准入规则 |
| `_plan_for`（quality evaluators） | 按 depends_on 找计划 | 中性 |
| evidence_build/research_direction | 天然聚合全部问题 | **顺序问题**：projection 层已在 synthesis 缺位时混合多问题 claim（S1/S4 把所有问题 claims 平铺）——P12-10 需要 re-projection |

## 3. Synthesis（问 9–12）

### Q9 哪些已有 Finding 可以合法跨问题组合？

前提（全部可在现有数据上判定）：
1. 问题间存在**显式声明的依赖**（P12-1 落地后：State dependencies / Registry depends_on，
   dependency_type ∈ 冻结枚举）；
2. 组合的 Finding status 均 ≠ FAIL/UNKNOWN（descriptive PASS/WEAK 或
   comparative 已数值化）；
3. 证据独立（P9 EQ-independence 规则跨问题扩展：同源不得因数量升级）。

### Q10 哪些组合只能是 hypothesis？

* 无依赖声明但结构上可比（例如同为 evaluation 类结果）；
* metrics 缺失/单位不一致/人群不兼容（P12-8 的 UNKNOWN 分支）；
* extends 关系缺"new evidence"要件。

### Q11 哪些组合可以形成 supported synthesis？

任务书 S1 等级：**全部组件 finding PASS（或 moderate+）+ 依赖链显式 +
证据相互独立 + decision rule 可裁决**。qualified（S2）= 支撑成立但存在
limitations（如单问题强、另一问题 weak——bottleneck 规则见任务书 §七）。

### Q12 synthesis 的最小 provenance 集合？

```text
{question_refs, finding_refs（含其 result/experiment 反查链）, claim_refs,
 dependency_refs（QuestionDependency 记录）, relations, decision_rule,
 state_version（registry/graph 版本号）, limitations}
```
其中 state_version 是失效重派生的对账基础（P12-7）。

## 4. 其他与 P12 相关的实况

* **SD-1 三义**：provenance 链已就位（experiment.data.plan_ref/plan_entry/
  hypothesis_ref，P9.5 B2 修复）——ExperimentPlan(D*)/Run(E*)/Result(R*) 可区分。
* **SD-2**：refresh_from 的 validated 晋级不读 quality findings——P12 synthesis
  聚合时须**同时读取** evidence validity 与 quality findings（任务书 §十八），
  但不得把 WEAK 转成 invalidated。
* **Literature**：claim.data.literature_refs 字段已在 evidence_build 写入（恒 []）；
  Reference 有 usage_type/supports_claims 字段（fact_check.py）——ingestion
  contract 的插座已留。
* **Projection 顺序问题**：research_direction/paper_projection 目前在无 synthesis
  的情况下混合全部问题 claims——P12-10 需要决定 synthesis 缺位时是否降级投影
  （建议：保持现状 + narrative 标注 `synthesis: absent`，不硬失败）。

## 5. 记录在案的问题（P12-0 不修，按任务书移交后续阶段）

| # | 发现 | 类别 | 移交 |
|---|---|---|---|
| D-1 | Registry question artifact 不携带 depends_on；session 不传 State dependencies | 缺口 | P12-1 |
| D-2 | State.dependencies / blocked_by_dependencies 插座未接线 | 缺口 | P12-1 |
| D-3 | expand_questions 无问题间依赖机制（`*` ≠ 依赖） | 设计缺口 | P12-1/2 |
| D-4 | FindingGraph.compares_with 硬编码同 question，无跨问题合法路径 | 缺口 | P12-2 |
| D-5 | derived_from 边无科学语义准入规则（自由通道） | 语义风险 | P12-2 |
| D-6 | 无 synthesis 层；projection 在无综合语义时混合多问题 claims | 缺口 | P12-3/10 |
| D-7 | literature_refs 恒为空，ingestion 无通道 | 缺口 | P12-9 |
| D-8 | 跨问题失效传播不存在（隔离是安全面也是能力缺失面） | 缺口 | P12-7 |
| D-9 | comparative metrics 数值来源不存在（依赖真实实验执行，P12-8 范围） | 已知边界 | P12-8 |

## 6. P12-1 起的实现输入（设计输入汇总）

1. QuestionDependency 的存储位置：建议 **State（现有插座）+ Registry artifact
   depends_on（轻量镜像）** 双写，dependency_type 冻结枚举
   （execution/methodological/evidential/comparative/extension）。
2. 跨问题失效传播的准入：仅沿 `evidential`/`extension` 类型依赖传播 reval 档；
   `execution` 依赖只影响调度不传播失效。
3. Synthesis 聚合用**离散瓶颈规则**（任务书 §七表），不实现连续加权。
4. derived_from 的跨问题使用必须挂 dependency_refs，否则 quality finding
   （P12-2 的准入规则在 fact/quality 侧的体现）。
