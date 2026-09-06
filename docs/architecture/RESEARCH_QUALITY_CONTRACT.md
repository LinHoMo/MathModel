# Research Quality Contract — P9 契约文档

> 代码真源：`core/validators/quality/`（contract.py / evaluators.py / aggregator.py）。
> 与 `RUNTIME_CONTRACTS.md`（P7）同级约束；冲突时以 P7 生命周期语义为准。

## 1. 状态与维度（冻结）

* **四态**：`PASS / WEAK / FAIL / UNKNOWN`——与 Evidence Gate、JudgeCritic 同集。
  禁止新增第五种状态；Innovation 的 HYPOTHESIS 映射为 UNKNOWN。
* **七维**：problem / model / experiment / evidence / decision / innovation /
  reproducibility。每维产生 `findings[]`，维度状态由 findings 推导
  （任一 fail→FAIL，weak→WEAK，unknown→UNKNOWN，否则 PASS）。**无维度分数**。

## 2. QualityFinding 契约

```text
dimension / severity(fail|weak|unknown|info) / status / subject_type / subject_id
reason（人可读）
evidence_refs / artifact_refs / knowledge_refs / decision_refs   ← 全量可追溯
recommended_action ∈ {none, rerun_model_selection, refine_experiment_plan,
                      rerun_experiment, rebuild_evidence, request_evidence,
                      recompute, reset_question, record_failure, review_decision}
check_id（M1/E5/I3/D4… 规则编号，审计用）
```

## 3. 评估规则总表

| 维度 | 检查 | 级别 |
|---|---|---|
| problem | P-Q1 motivates 来源缺失 / P-Q2 draft 搁置 | fail / weak |
| model | M1 card_id 缺失或不存在 / M2 无 assumes 假设 / M3 无计划或无 baseline 或无 metrics / M4 选型决策未登记 | fail/weak |
| experiment | E1 purpose / E2 hypothesis / E3 decision rule 可执行 / E4 information gain 越界或与优先级不匹配 / E5 baseline / E7 实验无活跃 result / E8 失效后无重建且无重跑决策 | fail/weak |
| evidence | EQ-independence 同源双 claim / EQ-coverage 覆盖率 / EQ-gate-* GateReport fail 项委托引用 | weak/fail |
| claim(∈evidence 维) | CQ-what / CQ-based（gate 未提供时）/ CQ-repro 支撑链无产出实验 / CQ-baseline 对照未记录 | fail/weak |
| decision | D1 知识引用存在 / D2 失败引用存在 / D3 required_validation / D4 **决策不得引用已失效事实**（deprecated 知识 / 全死结果链）/ D5 score_breakdown | fail/weak |
| innovation | I2 修改显式 / I4 baseline / I6 风险检测信号 / I3+I5 未测量改进 → UNKNOWN（hypothesis） | fail/weak/unknown |
| reproducibility | R1 artifact 无 created_by / R2 图表无来源归属 | weak |

**防重复计算**：传入 GateReport 时 evidence/claim 维自动跳过 Gate 已覆盖的
E1/E2/E3；Capability Matching 的 applicability 规则被 M1 复用不重写。

## 4. 反馈语义（P9-10，映射 P7 冻结四分）

```text
FAIL(fail)  → rerun_model_selection / rerun_experiment / recompute /
              rebuild_evidence / review_decision（workflow_feedback() 映射）
WEAK        → advisory refine（记录在案，不阻断确定性流程）
UNKNOWN     → request_evidence（显式要求补证据）
PASS        → 放行进入 Research State
```

Workflow 集成：`quality_evaluation` 验证节点（evidence_gate 之后、
research_direction 之前；on_fail→evidence_build 复用 P7 反馈环）。
**方向红线：Quality → Research State，不是 Quality → Paper。**

## 5. Pack 优先级（P9-13）

`CompetitionPack.judging_preferences / evaluation_dimensions` → `report.priorities`
（处置顺序排序）。**红线：Pack 不得改变任何 finding 的 severity/status**
（`test_q14` 锚定：有无 pack，overall_status 必须一致）。

## 6. Quality Memory（P9-12）

* 报告落盘 `state/quality_report.json`（state 资产，非知识文件）。
* FAIL blockers 显式登记进 DecisionLog（`question_type="quality"`，去重）——
  写回既有记忆体系，与 FailureMemory → risk penalty → 推荐形成
  Research Learning Loop；**禁止平行 memory**。

## 7. 不变量（测试锚定）

* INV-1（CQ/D4）：失效证据/废弃知识不得作为当前依据。
* INV-2（CI-08 延续）：Pack 只读，只影响处置顺序。
* INV-3：QualityReport 无任何数值总分字段。
* INV-4：同一语义只计算一次（Gate 委托、M1 复用 P8 规则）。
* INV-5（P9-11）：Quality 是 Workflow 验证节点，不是 Agent。
