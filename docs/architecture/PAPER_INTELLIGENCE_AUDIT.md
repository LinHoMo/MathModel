# Paper Intelligence Audit — P10-0（只读审计）

> 审计范围：core/runtime/writing、artifacts、execution、validators、schemas、
> knowledge、docs、tests。**本阶段零代码修改。**
> P10 定位：**Paper = Research State 的可验证投影**；LLM 降级为表达层。

## A. Claim 到底是什么（P10-A）

现状：claim 是 Registry artifact（type=claim，ID C*），字段仅
question / depends_on / title / data{statement?} / tags。P9 的 CQ 检查
（what/based/repro/baseline）已覆盖一部分。**缺口**：

| 目标字段 | 现状 | P10 落点 |
|---|---|---|
| question_id | ✅ artifact.question | — |
| claim_type | ❌ 无（comparative/descriptive/causal 未区分） | data.claim_type |
| statement | ⚠️ 可选，handlers 写 title 回退 | 必填化（构造时） |
| evidence_refs[] | ⚠️ 只能经 graph 反查（supports 入边） | 保持派生（不冗余存储） |
| model_refs / experiment_refs[] | ❌ 无直接链 | **由 Coverage Matrix 派生**（见 B） |
| figure_refs[] | ⚠️ visualized_by 反查 | 派生 |
| confidence | ❌ 无 | data.confidence（Finding 层给） |
| status | ✅ P7 生命周期（不新增状态） | — |
| provenance | ✅ lifecycle_history + created_by | — |

**裁决记录**：evidence_refs 等一律**派生而非冗余存储**——存储两处必然漂移
（P7 红队 B2 的教训）。Claim 的完整语义 = artifact + graph 邻域。

### SD-1 正式裁决（experiment 三义）

采纳拆分，落点如下（不新增 artifact type，不修 P7 契约）：

```text
ExperimentPlan  = decision artifact（已有，data.entries）
ExperimentRun   = experiment artifact（已有，P9.5 起携带 plan_ref/plan_entry/hypothesis_ref）
ExperimentResult= result artifact（已有，produces 边）
```

三者以 provenance 链（plan_ref → run → result）区分；命名沿用既有 ID 前缀
（D/E/R），避免破坏 P7 ID 契约。文档与代码注释统一用三义术语。

## B. Claim Coverage Matrix（P10-2）

现状：无矩阵。claim 的 evidence/model/experiment/figure 分散在四种边里
（supports / solved_by+validated_by / produces / visualized_by）。
P10 建 `claim_coverage(registry, graph, section_map) -> CoverageMatrix`：
每行 = claim，列 = evidence/experiment/model/figure/section，单元格 = artifact ids。
强制规则映射：C1 无 evidence → 不可发布（PaperIntegrity P2）；C2 hypothesis →
Finding 侧 UNKNOWN；C3/C4 已由 P7 失效传播覆盖（红队 R1/R2 验证）。

## C. Narrative IR / 推理图 / Finding（P10-1/3/4/5）

现状：Narrative(dataclass)+Outline(dict) 是唯一中间层；section 由
SECTION_ORDER 五段固定；无 finding 实体；无推理关系（contradicts/limits 等）。
缺口：claim→section 的归属已有 appears_in；**finding 与 interpretation 缺失**；
abstract/conclusion 靠投影规则拼装而非派生自 validated findings。
落点：`core/runtime/writing/narrative_ir.py`（ScientificNarrative IR +
NarrativeReasoningGraph）与 `core/runtime/writing/findings.py`（FindingGraph，
**派生式**——从 results/claims 计算，随失效传播自动更新，不新增 artifact type
= 不触 P7 契约）。

## D. Fact Check / 引用溯源 / Integrity（P10-8/9/10）

现状：legacy `writing_check.py`/`citation_check.py` 检查 tex 文本（占位符/
引用闭合），但**不回查 Registry**；数字/图表无 provenance 反查；
references.bib 只有文本闭合检查，无 used_by 映射；
abstract/一致性检查在 consistency-checker（legacy，all_results.json 口径）。
落点：`core/runtime/writing/fact_check.py`（PaperFactChecker：解析 LaTeX →
numbers/figures/tables/citations/claims 反查 Registry）+
`core/validators/quality/paper_integrity.py`（P1–P12 检查，产出 P9 QualityFinding，
复用四态——**不造 PaperScore**）。

## E. Abstract / Conclusion 派生（P10-11）

现状：abstract 无实体；conclusion section 由 projection 从 supported_arcs 拼列表。
落点：FindingGraph 的 validated findings → `derive_abstract()` /
`derive_conclusion()`（纯函数，写进 Narrative IR），禁止 LLM 先写正文后总结。

## F. LLM 边界（P10-7）

现状：Runtime 全确定性，LLM 未接入任何 writing 路径（诚实现状）。
P10 落点：表达层接口 `render_section(ir_section) -> str` 预留 LLM 实现，
但**默认实现为确定性模板渲染**；FactChecker 在渲染后仍全量回查——
LLM 无论是否接入都不可能绕过事实层（架构上无法绕过，而非约定）。

## G. 红队映射（P10-12）

A-L 攻击全部落 `tests/integration/test_paper_redteam.py`；
invalidation→projection 重建复用 P9.5 已验证的传播链 + 新增 narrative 级断言。

## H. 消费者与不修改清单

* 消费者：quality_evaluation 节点（PaperIntegrity 并入 P9 报告）、未来 Writer 层。
* **不修改**：P7 artifact 类型集与生命周期、P9 质量契约、Evidence Gate 判定本体、
  P8 打分规则；legacy writing_check/citation_check 保留但降级为文本层。
