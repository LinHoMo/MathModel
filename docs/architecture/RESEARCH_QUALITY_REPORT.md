# Research Quality Report — P9 实施报告

> P9 目标：让"**研究质量开始改变研究流程**"。与 P8（知识改变决策）合起来，
> V3 具备科研 Agent Runtime 的雏形，而非"串联 Agent 自动生成论文的 pipeline"。

## 1. 交付物

| 交付物 | 位置 | 状态 |
|---|---|---|
| Quality Contract | `core/validators/quality/contract.py` + `docs/architecture/RESEARCH_QUALITY_CONTRACT.md` | ✅ |
| Quality Evaluators（七维） | `core/validators/quality/evaluators.py` | ✅ |
| Quality Aggregator | `core/validators/quality/aggregator.py`（`ResearchQuality.evaluate`） | ✅ |
| Workflow 集成 | `core/workflows/stages/evidence.yaml`（quality_evaluation 节点）+ `handlers.do_quality_evaluation` | ✅ |
| Quality Memory | `state/quality_report.json` + DecisionLog（question_type=quality，去重） | ✅ |
| Competition 优先级集成 | `aggregator._pack_priorities`（只排序，不改判定） | ✅ |
| 测试矩阵 | `tests/integration/test_research_quality.py`（22 项：Q-01~15 + 对抗 A–G） | ✅ |
| 审计 / 契约 / 本报告 | `docs/architecture/RESEARCH_QUALITY_{AUDIT,CONTRACT,REPORT}.md` | ✅ |

## 2. 架构红线执行回执

* **零新 Agent**：quality_evaluation 是 Workflow 验证节点（type=validation，
  role=critic，validator=research-quality），不是 Agent。
* **零新顶层目录**：落在既有 `core/validators/`（evidence gate 同体系）。
* **P7 契约未改**：反馈闭环复用 rerun/recompute/reset_question/on_fail 反馈环；
  四态复用 PASS/WEAK/FAIL/UNKNOWN；superseded≠invalidated 保持。
* **确定性**：全部评估器为显式规则（check_id 编号 M1/E5/I3/D4…），零 LLM。
* **无黑箱总分**：QualityReport 仅 overall_status + findings + actions
  （测试断言无 score 字段）。

## 3. 质量闭环（P9-15 验收的完整链路）

```text
Knowledge → Capability Match → Candidate → Plan → Decision
    → Experiment → Artifact → Evidence Graph
    → quality_evaluation（七维，四态）
        PASS      → Research State → Paper Projection
        WEAK      → advisory（refine 记录在案）
        FAIL      → blockers → recommended_action
                    （rerun/recompute/rebuild → 复用 P7 反馈环）
                    → DecisionLog quality 记录（Learning Loop）
        UNKNOWN   → request_evidence
```

实测（V3 execute，16/16 节点）：健康运行 overall=WEAK（claim 未记录对照物
的 advisory），七维中 6 PASS + evidence WEAK——**质量系统对健康运行给出
非空发现，证明它真的在检查而不是橡皮图章**。

## 4. 对抗测试要点（全部通过）

* A：证据失效 → Quality ≠ PASS
* C：实验成功但无 baseline → M3/E5 FAIL
* D：创新未测量 → UNKNOWN（hypothesis），不得 PASS
* E：同源双 claim → EQ-independence 发现
* F：crash→resume 后质量状态可从 Registry/Evidence 重建且一致
* G：rerun 新谱系与旧 quality 报告隔离，落盘为新评估
* Q-14：Pack 有无 → overall_status 恒等（只改处置优先级）

## 5. 验收指标（P9-15）

| 指标 | 结果 |
|---|---|
| pytest | 630 passed, 11 skipped, 0 failed |
| validate.py | 57/57，0 warning |
| catalog_check | 双视图一致 OK（v3 节点 15→16 已同步） |
| doctor | 0 blocking |
| V3 dry-run | PASS（16 波 / 16 节点） |
| V3 execute | PASS（16/16，quality 报告落盘） |

## 6. 已知边界与 P10 建议

1. `claim.data.compared_against` 目前无人写入 → CQ-baseline 是常驻 advisory；
   P10 应在 evidence_build/claim 生成时回填对照物。
2. 创新测量（I3/I5）需要实验结果数值回填 decision rule 判定（ACCEPT/REJECT
   落库）——确定性 handler 无真实数值，P10 接入真实实验执行时补。
3. P9-14 建议的下一阶段：**V3 全系统红队审计**——攻击
   Plan→Evidence→Decision→Quality→Rerun 闭环，确认无"模块各自正确、组合
   语义谬误"；通过后再进入 P10 论文投影质量。
