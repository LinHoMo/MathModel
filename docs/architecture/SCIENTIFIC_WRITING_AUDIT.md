# Scientific Writing Audit — P11-0（只读审计）

> 审计对象：core/runtime/writing/、validators、knowledge、templates、Writer SKILL、
> PaperProjection、Narrative IR、Finding Graph、FactChecker、paper-cases、packs。
> 结论先行：**事实层已可信，表达层只有一个"列表拼装器"——论文差的根因不是
> LLM 不会写，而是 IR 粒度太粗（section 级）且无论证结构。**

## 1. 现状管线与缺口（12 问逐答）

| # | 问题 | 结论 |
|---|---|---|
| 1 | Projection→LaTeX 缺什么 | 缺 ParagraphPlan/ArgumentUnit 两级 IR：现在 outline 直接到 section 标题+claim 列表，无段落语义，LaTeX 渲染无从谈起 |
| 2 | 章节是否只是"把 Finding 排进去" | 是。S4 results = evidence ids + claim ids 列表，无论证结构（support/comparison/interpretation/limitation） |
| 3 | 段落是否有显式语义 | 无。段落概念不存在 |
| 4 | definition/motivation/derivation/… 区分 | 无。仅有 6 个 section purpose |
| 5 | 同一事实重复 | 结构性风险：claim 同时进 S1/S2/S4/S6 四个 section.claims，无去重/分工约束 |
| 6 | 结果堆积 | 是。S4 = evidence 列表，无 interpretation |
| 7 | 模型介绍多、选型理由少 | 选型理由在 P8 Recommendation.reasoning / Decision 里，但 IR 不携带 → 表达层拿不到 |
| 8 | 有图无解释 | 图只有 visualized_by 边；无 why_exists/what_to_observe 绑定 |
| 9 | 有结果无讨论 | S5 discussion 的 limitations 是假设标题拼接，非真实讨论 |
| 10 | 章节间无因果推进 | 无 transition 概念；Q1→Q2 依赖在 DAG 里但不在叙事里 |
| 11 | 优秀论文案例影响 Narrative？ | 否。paper-cases 是人读文档，无结构化消费 |
| 12 | Pack 影响 paper emphasis？ | 否。judging_preferences 只进 P9 处置排序，写作层未消费 |

## 2. 与 legacy Writer 的关系

`Writer/agents/section-writer` 等 SKILL.md 是 LLM 提示词资产；`core/templates/`
是 LaTeX 骨架。P11 把它们的"表达知识"沉淀为**确定性结构**
（WritingPattern/StyleConstraints），LLM 只在 Expression 层作为可插拔渲染器，
输出必过 FactChecker + 后验校验。

## 3. 落点（不新增顶层目录）

| 新能力 | 位置 |
|---|---|
| Expression Contract（ExpressionInput/Output、最小权限 Context、校准词表、失败语义） | `core/runtime/writing/expression.py` |
| ParagraphPlan / ArgumentUnit / ParagraphPlanner / 图表·公式绑定 / 跨问题 transition | `core/runtime/writing/paragraphs.py` |
| WritingPattern（7 类论证模式蒸馏） | `core/runtime/writing/patterns.py` |
| Comparative Finding 数值化（P11-4） | `core/runtime/writing/findings.py` 扩展 |
| Deterministic Renderer + 可插拔 LLM + 后验校验 | `core/runtime/writing/renderer.py` |
| 冗余 / AI 模式检测（P11-17） | `core/runtime/writing/redundancy.py` |
| Abstract/Conclusion 结构化升级（P11-15/16） | `narrative_ir.py` 扩展 |
| 红队 W1–W15 | `tests/integration/test_writing_redteam.py` |

## 4. 边界与红线回执

* Research Layer（Claim/Finding/Evidence/Model/Experiment/Decision）≠ Expression
  Layer（Sentence/Paragraph/Transition/Style）——P11-18 分离，Expression FAIL 只
  regenerate，不触发研究 rerun。
* FactChecker/Integrity 是不可跳过的最终门禁（P11-20）；LLM 自评/JudgeCritic
  PASS 均不豁免。
* 不以字数/学术腔为质量指标；A/B 用确定性指标（证据密度/解释密度/冗余率/
  unsupported 数）。
* `paper.min_equations` 类软目标与 P11-14 冲突：公式必须绑定 model_ref 与用途，
  堆公式由 EquationBinding 暴露（orphan equation 已有 P6 检查）。
