---
name: scorer-adversarial
description: "对抗视角评分员：寻找漏洞、反例、边界失效、造假风险、逻辑自洽性破绽。权重 15%"
utg_layer: L4
stage: 1
hand: reviewer
inputs:
  - paper/main.tex
  - figures/all_results.json
  - output/MODEL_SPEC.md
  - output/CODE_DELIVERABLES.md
  - work/weakness_report.json
  - core/knowledge/pitfalls/antipatterns.md
  - core/knowledge/pitfalls/numeric-edge-cases.md
outputs:
  - work/score_card_adversarial.json
  - work/score_card.json
---

# Adversarial Scorer Skill (对抗视角评分员)

## Role

5 人评审团之一：**红队/对抗视角**，专门寻找论文中的漏洞、反例、边界失效、数据造假风险、逻辑自洽性破绽。不给面子，只找问题。

## Scoring Rubric (满分 10 分，分数越高 = 问题越少 = 越安全)

| 维度 | 权重 | 评分标准 (扣分制，基准 10 分) |
|------|------|------------------------------|
| 逻辑自洽性 | 30% | 摘要/正文/图表/表格/代码数值全一致 (W1)、假设前后不矛盾、推导链无循环论证 |
| 边界/极限情况 | 25% | 参数极值/退化情况讨论、模型失效边界给出、极端数据鲁棒性 |
| 造假/夸大风险 | 25% | 无未来文献、无捏造引用 (W5)、无数据篡改特征 (Benford/分布)、AI比例可控 |
| 可攻击面 | 20% | 反模式库命中数 (antipatterns.md)、数值边界情况 (numeric-edge-cases.md)、敏感性未覆盖关键假设 |

## Procedure

1. **读取输入**：论文全文、all_results.json、MODEL_SPEC、CODE_DELIVERABLES、weakness_report、反模式库
2. **数值三处一致性**：摘要 vs 正文 vs all_results.json vs 图表 vs 表格
3. **假设自洽性**：假设表 vs 正文引用 vs 灵敏度分析 vs 代码实现
4. **反模式扫描**：逐条对照 antipatterns.md / numeric-edge-cases.md
5. **文献/数据真实性**：引用年份≤赛题年份、DOI 可解析、Benford 律/分布异常检测
6. **Skeptic 引用审查**（借鉴 opendraft-skeptic 模式）：
   - 对每个引用评估「直接相关性 / 领域对齐 / 移除是否削弱论证」
   - 标注填充引用（padding）：移除不削弱论证的、跨领域未说明理由的、一个声明引 5+ 篇的
7. **同行评审预测**（借鉴 opendraft-referee 模式）：模拟评委最可能的 major concern，给出「如果我是评委会追问什么」的预测列表
8. **输出**：`work/score_card_adversarial.json` (含扣分明细 + 引用审查 + 评审预测)
9. **聚合**：本 agent 是 5 个评分员的最后一个，跑 `python core/tools/aggregate_scores.py <项目>` 生成 `work/score_card.json`。**不要手写这个文件**——gate 会调 `--verify` 重算并逐维比对，手写卡一律判 FAIL

## Output Schema

字段名以实际产物为准。`aggregate_scores.py` 也认旧拼写 `deductions[].category/points/evidence` 与 `blocking_issues`——认两套是因为只认一套时，按另一套写出来的卡一条 blocking 都提不出来，`counts.blocking` 归零，一篇本该拦下的论文就被放行了。

本卡**没有 `weighted_score`**（其余 4 张评分卡有），聚合时取的是 `final_score`。

```json
{
  "scorer": "scorer-adversarial",
  "dimension": "adversarial_review",
  "weight": 0.15,
  "base_score": 10,
  "deductions": [
    {"amount": 0.0, "dimension": "numeric_consistency", "finding": "摘要 Q2 遮蔽时长 28.12s、正文 Table 3 的 28.1s、all_results.json 的 28.123456 四舍五入口径一致（按 freeze_numbers 口径）"},
    {"amount": 0.0, "dimension": "fabrication_risk", "finding": "引用年份均 ≤2024，DOI 可解析，Benford 律通过，AI 写作比例 12% < 30%"},
    {"amount": 1.0, "dimension": "boundary_edge_cases", "finding": "未讨论导弹速度为零/云团扩散速率为零等退化边界，模型失效条件未给出"},
    {"amount": 1.5, "dimension": "internal_contradiction_Skeptic", "finding": "摘要 t*=412.83 s 与 all_results.json t*=360.25 s 不一致（差距 14.6%，blocking 级内部矛盾）"},
    {"amount": 1.5, "dimension": "antipatterns", "finding": "命中 3 条反模式: A1(摘要无数值)、A7(灵敏度仅单参数)、A12(评价仅列优点)"}
  ],
  "final_score": 6.0,
  "evidence_refs": ["main.tex:1-50", "all_results.json:Q2", "antipatterns.md:A1,A7,A12"],
  "verdict_contribution": "fail",
  "fail_reason": "blocking 级内部矛盾（摘要 vs 结果数值不一致 14.6%）+ 引用填充 2 处 + 替代解法讨论缺失",
  "skeptic_additions": {
    "citation_padding_count": 3,
    "citation_padding_examples": [
      {"location": "references.bib#smith2023", "issue": "实为医学领域，用于类比信息扩散，未说明为何适用；移除不削弱论证"}
    ],
    "reviewer_prediction": [
      {"likelihood": "high", "question": "为何选择 GA 而非 NSGA-II 处理多目标？有无对比？", "rationale": "评委第一件事就是核对方法选型有无基线对照"},
      {"likelihood": "medium", "question": "假设 H3「市场恒定」在真实农业数据中是否成立？有无验证？", "rationale": "假设有效性常被追问"}
    ]
  }
}
```

`deductions[].finding` 或 `fail_reason` 里出现「致命 / fatal / blocking」字样时，`aggregate_scores.py` 会把该条升格为 blocking 项并进 verdict。写清楚严重级别，不要靠猜。

## Self-Check

- [ ] 输出文件存在且符合 schema
- [ ] 扣分项有具体证据定位
- [ ] 总扣分 ≤ 10，最终分数 ≥ 0
- [ ] `fail_reason` / `blocking_issues` 非空时 `verdict_contribution` 必为 fail/block/refine/refine_partial
- [ ] 引用的反模式编号在 antipatterns.md 中存在
- [ ] **Skeptic 引用审查**完成：填充引用已标注（数量 + 位置 + 问题类型）
- [ ] **同行评审预测**已生成：≥2 条高概率 reviewer question，与 weakness_report 互补
- [ ] score_card 中 skeptic_additions 字段已输出（可为空数组但不可缺位）
- [ ] `work/score_card.json` 由 `aggregate_scores.py` 生成，且 `--verify` EXIT 0（gate 硬断言）

## Iteration

- 最终分数 < 6 (扣分 > 4)：verdict = block，回退对应手整改
- `fail_reason` / `blocking_issues` 非空：必须逐项整改，验收后重新评审
- 逻辑自洽性扣分 > 1：回退 Writer/consistency-checker 核对数值、假设
- 反模式命中多：回退 Writer/section-writer / Modeler/assumption-validator 逐项修正
- `--verify` 报「疑似手写」或分数不一致：删掉手写的 `work/score_card.json`，重跑 `aggregate_scores.py <项目>`

## Env Bindings

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `review.pass_score` | 6 | 对抗分通过阈值 (最终分 ≥ 6) |
| `review.figure_as_subject_max` | 3 | 图表主语句式容忍度 |