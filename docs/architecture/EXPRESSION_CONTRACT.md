# Expression Contract — P11 契约文档

> 代码真源：`core/runtime/writing/expression.py`（边界/校准/失败语义）、
> `paragraphs.py`（ParagraphPlan/ArgumentUnit/Renderer）、`patterns.py`、
> `redundancy.py`。与 P7/P9/P10 契约同级；冲突时以更早契约为准。

## 1. Research Layer ≠ Expression Layer（P11-18 冻结）

```text
Research Layer : Claim / Finding / Evidence / Model / Experiment / Decision
Expression Layer: Sentence / Paragraph / Transition / Explanation / Style
```

**Research FAIL → P9 已有 workflow feedback（rerun/recompute）。
Expression FAIL → 只 regenerate paragraph。两者禁止混淆。**

## 2. LLM 边界（P11 硬约束 5–12 的可执行形态）

* MAY CHANGE：wording / sentence_structure / paragraph_ordering（IR 允许内）/
  transition / explanation_phrasing / concision / terminology_consistency。
* MAY NOT CHANGE：claim_meaning / numeric_value / evidence_relation /
  model_identity / experiment_result / decision_outcome / citation_identity /
  finding_status。
* 架构性封死：LLM 渲染器只收到 `ExpressionContext`（最小权限——当前段落的
  allowed_claims/numbers/references，无全项目、无 invalidated 历史）；输出必过
  `_post_validate`（数字 ⊆ 允许集 / 引用 ⊆ bib / 措辞校准）→ hard_reject /
  deterministic_repair / rerender（P11-19）。
* 本仓库不内置任何 LLM：`ControlledRenderer(llm_fn=...)` 由宿主注入；
  `llm_fn=None` 时退化为确定性渲染——**删除 Renderer 后 P10 确定性投影照常运行**。

## 3. 段落 IR（P11-2）

`ParagraphPlan`：paragraph_id / purpose（17 项枚举冻结）/ section_id /
claim·finding·evidence·figure·table·equation_refs / required_content /
forbidden_claims / transition_from·to / cross_question_from / argument_units。
派生自 P10 IR + FindingGraph + question_dependencies（P11-12 跨问题过渡）。

## 4. ArgumentUnit（P11-3）

claim → {support[], comparison, interpretation(标 fact|hypothesis), limitation,
implication, evidence_level}。结果段自动派生；机制解释无证据时
`interpretation_status="hypothesis"`，表达为 "（possible explanation）"。

## 5. Comparative Finding 数值化（P11-4）

`MetricComparison{metric, baseline_value, candidate_value, unit, uncertainty,
direction}`；direction ∈ better/comparable/worse/uncertain **由 decision rule
裁决**（阈值 3% + robustness）；无测量值 → finding 保持 UNKNOWN。禁止未测量的
"显著"（W4：`check_wording(text, level, significance=False)` 拦截）。

## 6. 措辞校准（P11-10）

| 证据强度 | 允许 | 禁止 |
|---|---|---|
| strong（baseline+robustness） | "结果表明/实验证据支持"；"显著"仅当 significance=True | best/最优/证明/optimal/generalizable（任何级别） |
| moderate | "结果显示/在当前实验设置下表现更好" | 同上 + "显著" |
| weak | "提示/可能/初步表明" | 同上 + 无限定断言 |
| unknown | 不得写成结论 | 一切断言 |

## 7. Claim 引用溯源（P11-5）

claim.data：`experiment_refs[]`（Research Evidence）与 `literature_refs[]`
（Literature Evidence）分离；Reference 增 `usage_type`（background/method_origin/
parameter_source/comparison/external_validation）+ `supports_claims[]`。
W9 检查：文献支撑的结论不得表述为本项目实验结果，反之亦然。

## 8. 最终门禁（P11-20）

`最终可交付 = PaperIntegrity ∧ ResearchQuality（任一 FAIL 即阻断）`。
FactChecker/Integrity 不可跳过；LLM 自评 / JudgeCritic PASS 不构成豁免。
