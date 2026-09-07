---
name: scorer-reader
description: "可读性评分员：评估结构清晰度、语言质量、图表叙事、逻辑流畅度。权重 15%"
utg_layer: L4
stage: 1
hand: reviewer
inputs:
  - paper/main.tex
  - paper/figures/
  - paper/references.bib
outputs:
  - work/score_card_reader.json
---

# Reader Scorer Skill (可读性评分员)

## Role

5 人评审团之一：模拟**读者/评委阅读体验**，评估论文结构是否清晰、语言是否专业自然、图表是否服务叙事、逻辑是否流畅。

## Scoring Rubric (满分 10 分)

| 维度 | 权重 | 评分标准 |
|------|------|----------|
| 结构清晰度 | 30% | 章节顺序标准 (摘要→重述→假设→符号→建模→求解→检验→灵敏度→评价→参考)，层级分明 |
| 语言质量 | 25% | 无 AI 痕迹 (W6, forbidden-words.md)、无内部路径 (W7)、无占位符 (W8)、专业学术表达 |
| 图表叙事 | 25% | 每图表前 1-2 句引导、后 3-5 句分析 (W4)、图表非主语 (W12)、连续图表间有段落 |
| 逻辑流畅度 | 20% | 段落间过渡自然 (transition-phrases.md)、引用闭合 (W5)、符号首现即定义 (M4) |

## Procedure

1. **读取输入**：论文全文、图表目录、参考文献
2. **结构检查**：章节顺序、层级、完整性
3. **语言扫描**：禁用词、AI痕迹、内部路径、占位符、列表环境 (W11)
4. **图表叙事检查**：前引导、后分析、主语句式计数 (W12)
5. **逻辑流检查**：过渡词、引用闭合、符号定义
6. **输出**：`work/score_card_reader.json`

## Output Schema

```json
{
  "scorer": "scorer-reader",
  "dimension": "readability",
  "weight": 0.15,
  "sub_scores": {
    "structure_clarity": {"score": 9, "evidence": "章节顺序标准，层级清晰，附录规范"},
    "language_quality": {"score": 7, "evidence": "仅发现 2 处 '值得注意的是' (forbidden-words.md)，无内部路径/占位符，正文无列表环境"},
    "figure_narrative": {"score": 8, "evidence": "10 张图均有前引导后分析，图表主语句式 1 次 (<3)，连续图表间有段落"},
    "logic_flow": {"score": 8, "evidence": "过渡自然，引用全部闭合，符号首现即定义 (Table 1)"}
  },
  "weighted_score": 8.0,
  "evidence_refs": ["main.tex:1-50", "forbidden-words.md", "main.tex:fig references"],
  "verdict_contribution": "pass"
}
```

## Self-Check

- [ ] 输出文件存在且符合 schema
- [ ] 4 个子维度评分均在 0-10 区间
- [ ] 禁用词/AI痕迹有具体行号定位
- [ ] 图表主语句式计数准确
- [ ] 加权总分计算正确

## Iteration

- 语言质量 < 6：回退 Writer/section-writer 重写违规段落，Writer/guardrails-checker 复核
- 图表叙事 < 6：回退 Writer/section-writer 补全引导/分析，Writer/figure-generator 调整图表顺序
- 结构 < 6：回退 Writer/structure-planner 调整章节顺序
- 逻辑流 < 6：回退 Writer/section-writer 改写过渡、补全符号定义

## Env Bindings

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `review.figure_as_subject_max` | 3 | 图表主语句式容忍度 |
| `paper.min_equations` | 15 | 公式数下限 (结构完整性间接指标) |