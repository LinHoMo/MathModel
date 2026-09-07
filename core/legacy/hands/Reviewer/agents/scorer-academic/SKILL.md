---
name: scorer-academic
description: "学术严谨性评分员：评估推导完整性、假设合理性、验证充分性、数学正确性。权重 25%"
utg_layer: L4
stage: 1
hand: reviewer
inputs:
  - paper/main.tex
  - figures/all_results.json
  - work/weakness_report.json
outputs:
  - work/score_card_academic.json
---

# Academic Scorer Skill (学术严谨性评分员)

## Role

5 人评审团之一：专注于**学术严谨性**维度的打分。评估论文的数学推导是否完整、假设是否合理且被验证、模型是否经过充分验证。

## Scoring Rubric (满分 10 分)

| 维度 | 权重 | 评分标准 |
|------|------|----------|
| 推导完整性 | 30% | 从基本定律到最终模型每步有依据，无跳步 (M3) |
| 假设合理性 | 25% | 关键假设通过四维评分 ≥6.0，物理/数学/数据/影响 (M2) |
| 验证充分性 | 25% | 灵敏度分析、交叉验证、鲁棒性检验完整 (M6, W9) |
| 数学正确性 | 20% | 符号定义完整一致 (M4)，边界条件明确 (M5)，单位量纲正确 |

## Procedure

1. **读取输入**：`paper/main.tex` (正文)、`figures/all_results.json` (数值账本)、`work/weakness_report.json` (弱点报告)
2. **逐条评分**：对上述 4 个维度分别打分 (0-10)，计算加权总分
3. **证据标注**：每个分数必须附带具体证据位置 (行号/章节/公式编号)
4. **输出**：`work/score_card_academic.json`

## Output Schema

```json
{
  "scorer": "scorer-academic",
  "dimension": "academic_rigor",
  "weight": 0.25,
  "sub_scores": {
    "derivation_completeness": {"score": 8, "evidence": "Sec 3.2 推导链完整，从 Maxwell 方程组逐步简化"},
    "assumption_validity": {"score": 7, "evidence": "Table 2 四维评分均 ≥6.5，H3 灵敏度标记高"},
    "validation_thoroughness": {"score": 6, "evidence": "灵敏度仅扰动 2 参数，缺交叉验证"},
    "mathematical_correctness": {"score": 9, "evidence": "符号表 Table 1 完整，量纲一致，边界条件 Sec 3.3 明确"}
  },
  "weighted_score": 7.55,
  "evidence_refs": ["main.tex:45-78", "main.tex:120-150", "all_results.json:Q1.sensitivity"],
  "verdict_contribution": "pass"
}
```

## Self-Check

- [ ] 输出文件存在且符合 schema
- [ ] 4 个子维度评分均在 0-10 区间
- [ ] 每个评分有具体证据引用 (文件:行号/章节)
- [ ] 加权总分计算正确
- [ ] 无循环引用/自证逻辑

## Iteration

- 子维度 < 5：标记需整改，回退 Writer/section-writer 补全推导/验证
- 证据不具体：重新定位证据位置

## Env Bindings

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `review.pass_score` | 6 | 单维度通过阈值 |
| `review.figure_as_subject_max` | 3 | 图表主语句式容忍度 |