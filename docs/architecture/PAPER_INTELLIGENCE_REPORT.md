# Paper Intelligence Report — P10 实施报告

> P10 定位：**Paper = Research State 的可验证投影**。LLM 的职责被架构性降级为
> 表达层——不是约定，而是任何投影产物都要经过 FactChecker 反向回查（无法绕过）。

## 1. 管线（已落地）

```text
Research State
  → Claim Coverage Matrix      （claim_coverage，全链回溯：evidence/experiment/model/figure/section）
  → Finding Graph              （findings.py，派生式：descriptive/comparative，四态随失效自动降级）
  → Scientific Narrative IR   （narrative_ir.py：六 purpose sections + 推理图七关系）
  → Abstract / Conclusion      （从 validated findings 派生，P10-11）
  → Paper Projection           （handlers.do_paper_projection 已接线 IR+Findings）
  → [LLM 表达层——预留接口，默认确定性渲染]
  → Paper Fact Checker         （fact_check.py：反向回查 Registry）
  → PASS / REVISE
```

## 2. SD-1 正式裁决（experiment 三义）

```text
ExperimentPlan   = decision artifact（data.entries）
ExperimentRun   = experiment artifact（plan_ref/plan_entry/hypothesis_ref provenance）
ExperimentResult = result artifact（produces 边）
```
以 provenance 链区分，ID 前缀沿用 D/E/R（不破坏 P7 ID 契约）。全库文档统一三义术语。

## 3. 红队 A–L 结果（12/12 通过）

| 攻击 | 结果 | 防线 |
|---|---|---|
| A 失效 claim 泄漏 | ✅ 拦截 | P11 FAIL |
| B superseded 实验支撑当前 claim | ✅ 拦截 | P7 谱系退役 + 断言 |
| C 无来源数字 | ✅ 拦截 | P3 UNSUPPORTED |
| D 无证据结论 | ✅ 拦截 | P2 FAIL |
| E 无来源图 | ✅ 拦截 | P4 |
| F 幻觉引用 | ✅ 拦截 | P7 |
| G/H 陈旧摘要/结论 | ✅ 消除 | 派生幂等（不存在旧文案载体）+ 非 PASS 不得进结论 |
| I/J/K 孤儿图/表/公式 | ✅ 标记 | P4 weak / P5 / P6 |
| L 跨问题污染 | ✅ 隔离 | Q002 findings 不受 Q001 失效影响 |
| 终局：M1 证伪 → E/C 判死 → 投影重建 | ✅ | 失效传播 + IR 重建 |

## 4. 硬约束回执（1–14）

1-2 零新 Agent / 零新顶层目录（writing/ 下三模块）✅；3-4 P7/P9 契约未改
（Finding 为派生层、PaperIntegrity 独立报告结构）✅；5-7 LLM 无法创建 Research
State（管线中无此通道）✅；6 Paper=projection ✅（do_paper_projection 已产出
IR+Findings）；8-10 全事实可追溯 ✅（FactChecker）；11-12 失效传播与谱系 ✅
（红队 A/B）；13 Abstract/Conclusion 派生 ✅；14 红队完成 ✅。

## 5. 验收

pytest 677 passed / validate 57/57 / catalog OK / doctor 0 blocking /
V3 execute 16/16（projection 产出 findings 指标）。

## 6. 留给 P11 的接缝

1. `render_section(ir_section) -> str` 表达层接口已预留：默认确定性模板，
   LLM 实现接入后仍受 FactChecker 全量回查约束。
2. Reference.used_by 目前只在 bib↔tex 层；与 Claim 级溯源（这句话是文献结论
   还是实验结论）需要 claim.data.citation_keys 字段落库。
3. Finding 的数值比较（comparative 的"凭什么"数值化）依赖真实实验执行
   （P8/P9 已留 decision_rule 占位）。
