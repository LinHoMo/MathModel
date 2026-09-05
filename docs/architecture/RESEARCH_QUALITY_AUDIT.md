# Research Quality Audit — P9-0 全面审计

> 日期：2026-09-06。审计范围：core/runtime、core/knowledge、core/validators、
> core/evaluation、core/roles、core/schemas、handlers、docs、tests。
> 结论先行：**Quality 判断已存在六处，但互相不通气、部分对象零约束、
> 且无统一出口与反馈通道。** P9 的职责是"接线与补缺"，不是再造一套评分。

## 1. Quality Capability Matrix（现状）

| 维度 | 现有实现 | 位置 | 输入 | 输出 | 可追溯 | 缺陷 |
|---|---|---|---|---|---|---|
| Evidence Quality（部分） | EvidenceGate E1–E8 | `core/validators/evidence/evidence_gate.py` | Registry+Graph | GateReport(verdict+findings 带 artifact_ids) | ✅ findings 携带 subject | 只回答"过不过"，不回答"为什么够/不够"（coverage/independence/provenance 无 finding）；**independence 未检查** |
| Narrative Quality | NarrativeCritic N1–N7 | `core/runtime/writing/narrative_critic.py` | Narrative+Outline | NarrativeReport | ✅ finding.items | 只管投影层；不管研究层 |
| 总判 | JudgeCritic | `core/runtime/writing/judge_critic.py` | nar+outline+gate | JudgeReport(PASS/WEAK/FAIL/UNKNOWN) | ⚠️ risks 无 subject_id | 聚合层，无独立事实 |
| Model Quality（选型侧） | P8 Capability Matching | `core/runtime/knowledge/retriever.py` | Profile+Cards | RecommendationScore 9 维+violations | ✅ knowledge_refs | **只管"选之前"**；选后（假设声明、对比证据、选择 trace 闭环）无检查 |
| Experiment Quality（计划侧） | ExperimentPlanner | `core/runtime/modeling/planner.py` | Cards+Failures | ExperimentEntry(purpose/hypothesis/decision_rule/gain) | ✅ data.entries | **执行侧零检查**：E1–E8 无消费者；result 从不回填 decision_rule 判定 |
| Innovation Quality（候选侧） | CandidateArena | `core/runtime/modeling/candidates.py` | Pattern+Recs | InnovationCandidate(status=hypothesis) | ✅ required_evidence | **I1–I7 无评估器**；hypothesis 永远不会晋级/被否 |
| Decision Quality | DecisionLog（仅记录） | `core/runtime/decisions/log.py` | — | Decision(knowledge_refs…) | ✅ 追踪字段 | **无审查器**：引用的知识/证据死亡后决策仍 active；required_validation 无人验收 |
| Problem Quality | **无** | — | — | — | — | question/problem artifacts 无任何质量检查 |
| Reproducibility | 无 V3 检查（legacy 有 repro_checklist） | `core/tools/validation/repro_checklist.py`（legacy） | — | — | — | V3 路径无确定性重放检查 |
| 文本/格式护栏 | guardrails + validate.py 57 项 | `core/validators/modules/` | 文件 | 检查项 | ✅ | 与研究质量正交，不在 P9 范围 |
| 5 维评分卡（legacy） | score_compute/aggregate_scores | `core/tools/evaluation/` | 项目产物 | 分数卡 | ⚠️ | V2 遗产，黑箱总分味道浓；P9 不扩展它，也不对接（避免双头分数） |

## 2. 重复计算识别（Q2）

* **Gate vs Quality**：Evidence Gate 判"链是否可用"（fail-closed 终局），Quality 判
  "为什么够/不够 + 怎么补"。P9 的 Evidence Quality **复用 GateReport 作为输入**，
  在其上派生 coverage/independence/provenance finding——不重算 E1–E8。
* **Capability Matching vs Model Quality**：选型侧 violations 已在 Recommendation；
  Model Quality M1 复用同一 applicability 判定（经 DecisionTrace 的 score_breakdown
  与 knowledge_refs），不重写规则。
* **禁止新增任何"总分"**：现有 JudgeCritic verdict（四态）是唯一聚合出口；
  P9 QualityReport 的 overall_status 同样是四态，且两者语义分区（研究过程 vs 投影层）。

## 3. 缺失矩阵（Q3，七类对象）

| 对象 | 质量约束现状 | P9 补齐 |
|---|---|---|
| Problem | 无 | P-Q：question 有 motivates 来源、非 pending 搁置、依赖完整 |
| Model | 仅选型前 | M1 兼容性复核（复用 P8 applicability）/ M2 假设声明存在 / M3 对比证据存在 / M4 选择 trace 可回答 |
| Experiment | 仅计划侧 | E1–E8：purpose/hypothesis 可测/decision rule 可执行/信息增益合理/baseline/对照/结果回填判定/失败产生决策 |
| Evidence | 仅 Gate | coverage（复用）/ **independence**（共享产出链不得计独立证据）/ provenance / freshness（invalidation 后未重建） |
| Claim | 仅隐式 | Claim 闭包六问（What/Why/Based on/Compared/Reproducible/Still valid），复用 P7 生命周期四态 |
| Decision | 仅记录 | 证据存活 / 知识存在 / failure_memory 已考虑 / required_validation 已验收 / **不得引用 invalidated/superseded 作为当前依据（P9 核心不变量）** |
| Innovation | 仅候选 | I1–I7：novelty 有依据 / 修改显式 / 改进可测量 / baseline 存在 / 非偶然 / 风险已评估 / 可复现；hypothesis 未验证不得 PASS |

## 4. 语义冲突与红线

* **状态集合**：P7 冻结 draft/active/validated/published/blocked/superseded/
  invalidated/deprecated + Gate 四态 PASS/WEAK/FAIL/UNKNOWN。P9 一律复用，
  **不新增第五种状态**；Innovation 的 HYPOTHESIS 映射为 UNKNOWN（缺证据）。
* **Gate 与 Quality 的反馈通道**：Gate FAIL 已有反馈环（on_fail→experiment_design）。
  Quality FAIL 复用同一机制（P9-10），禁止新造 rerun 语义（Resume/Retry/Rerun/
  Recompute 四分已冻结）。
* **Pack 优先级**（P8 留白）：judging_preferences → Quality 检查**优先级排序**，
  不得把 FAIL 改成 PASS（P9-13 红线）。
* **Quality Memory**：写回 DecisionLog（quality 类决策）+ state/quality_report.json
  落盘；**禁止平行 memory**（P9-12）。

## 5. 建议修改位置 / 不应修改的位置

| 动作 | 位置 |
|---|---|
| ✅ 新增 Quality Contract + 评估器 + 聚合器 | `core/validators/quality/`（复用既有 validators 目录——evidence gate 已在此，不新增顶层目录） |
| ✅ 新增 quality_evaluation 工作流节点 | `core/workflows/stages/evidence.yaml`（插在 evidence_gate 之后）+ `handlers.do_quality_evaluation` |
| ✅ 反馈闭环 | 复用 engine 既有 on_fail/reset_question/recompute |
| ✅ Quality 记忆 | DecisionLog（新增 quality 类条目）+ `state/quality_report.json` |
| ❌ 不改 | P7 lifecycle 状态机、P6 引擎语义、P8 打分规则、EvidenceGate E1–E8 判定本体 |
| ❌ 不做 | 论文语言优化、LLM 评估器、新 Agent |
