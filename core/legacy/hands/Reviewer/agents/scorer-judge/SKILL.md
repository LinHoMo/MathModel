---
name: scorer-judge
description: "评委视角评分员：评估创新性、完整性、规范性、亮点度。权重 25%"
utg_layer: L4
stage: 1
hand: reviewer
inputs:
  - paper/main.tex
  - figures/all_results.json
  - output/MODEL_SPEC.md
  - output/CODE_DELIVERABLES.md
outputs:
  - work/score_card_judge.json
---

# Judge Scorer Skill (评委视角评分员)

## Role

5 人评审团之一：模拟**评委视角**，评估论文的创新性、完整性、规范性、亮点度——即"能不能拿奖"。

## Scoring Rubric (满分 10 分)

| 维度 | 权重 | 评分标准 |
|------|------|----------|
| 创新性 | 30% | 新模型/新应用/新算法改进/新验证方法 (INNOVATION-TAGS.md 标签匹配) |
| 完整性 | 25% | 全流程闭环：拆题→建模→求解→验证→写作→评审，无缺环 |
| 规范性 | 25% | 格式/页数/字数/图表/公式/引用/匿名/AI披露 全达标 |
| 亮点度 | 20% | 摘要含数值 (W2)、假设必要性 (W3)、图表有分析 (W4)、评价诚实 (W10) |

## Procedure

1. **读取输入**：论文全文、MODEL_SPEC、CODE_DELIVERABLES、all_results.json
2. **创新匹配**：对照 INNOVATION-TAGS.md 统计创新标签命中数
3. **完整性核查**：四手契约文件齐全、子问题全覆盖、依赖链闭环
4. **规范核查**：格式/页数/字数/图表/公式/引用/匿名/AI披露
5. **亮点检查**：摘要数值、假设必要性、图表分析、评价诚实
6. **输出**：`work/score_card_judge.json`

## Output Schema

```json
{
  "scorer": "scorer-judge",
  "dimension": "judge_perspective",
  "weight": 0.25,
  "sub_scores": {
    "innovation": {"score": 8, "evidence": "引入物理约束引导的 NSGA-III (INNOVATION-TAGS: physics-guided-MOEA)，验证方法创新 (adjoint sensitivity)"},
    "completeness": {"score": 9, "evidence": "MODEL_SPEC/CODE_DELIVERABLES/PAPER_SPEC 齐全，3 子问题全链路闭环，DAG 依赖清晰"},
    "compliance": {"score": 7, "evidence": "页数 28/25-30，字数 21k/18k，图表 10/6，公式 22/15，引用 14/10，匿名通过，AI披露完整"},
    "highlight": {"score": 8, "evidence": "摘要含 3 子问题数值，假设均有必要性，图表前后有分析，评价诚实列出局限"}
  },
  "weighted_score": 8.05,
  "evidence_refs": ["main.tex:1-50 (abstract)", "main.tex:200-250 (evaluation)", "INNOVATION-TAGS.md"],
  "verdict_contribution": "pass_with_review"
}
```

## Self-Check

- [ ] 输出文件存在且符合 schema
- [ ] 4 个子维度评分均在 0-10 区间
- [ ] 创新性有 INNOVATION-TAGS 佐证
- [ ] 规范性有具体指标对比
- [ ] 加权总分计算正确

## Iteration

- 创新性 < 6：回退 Modeler/method-matcher 增加创新点或 Modeler/model-builder 改进算法
- 完整性 < 6：回退对应手补全缺失环节
- 规范性 < 6：回退 Writer/final-validator 修正格式/页数/引用
- 亮点度 < 6：回退 Writer/section-writer 扩写摘要/假设/图表分析/评价

## Env Bindings

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `paper.min_pages` | 17 | 页数下限（TUNABLE 软目标，国赛 20 页硬上限） |
| `paper.min_words` | 13000 | 字数下限（DERIVED，17 页 x 800 字/页） |
| `paper.min_figures` | 6 | 图表下限 |
| `review.figure_as_subject_max` | 3 | 图表主语句式容忍度 |