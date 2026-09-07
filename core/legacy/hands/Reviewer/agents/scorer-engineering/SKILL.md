---
name: scorer-engineering
description: "工程落地评分员：评估代码可复现性、计算性能、鲁棒性、工程规范。权重 20%"
utg_layer: L4
stage: 1
hand: reviewer
inputs:
  - paper/main.tex
  - figures/all_results.json
  - code/main.py
  - output/CODE_DELIVERABLES.md
  - work/test_report.json
outputs:
  - work/score_card_engineering.json
---

# Engineering Scorer Skill (工程落地评分员)

## Role

5 人评审团之一：专注于**工程落地**维度的打分。评估代码是否可复现、计算是否高效稳定、是否遵循工程规范。

## Scoring Rubric (满分 10 分)

| 维度 | 权重 | 评分标准 |
|------|------|----------|
| 可复现性 | 30% | 固定种子 42 (P1)、多次运行 CV≤10% (P6)、环境/参数/入口哈希完整 |
| 计算性能 | 20% | 求解器超时分级 (P11)、大规模问题可行、内存/时间可控 |
| 鲁棒性 | 30% | 约束重验证 (P10)、软惩罚处理不可行域 (P7)、异常处理 (P5) |
| 工程规范 | 20% | 目录结构 (P3)、docstring (P4)、数据校验 (P8)、运行说明 (P9) |

## Procedure

1. **读取输入**：代码文件、测试报告、CODE_DELIVERABLES、all_results.json
2. **静态检查**：目录结构、docstring、异常处理、数据校验代码
3. **动态验证**：运行测试报告、多次运行统计、约束重验证结果
4. **输出**：`work/score_card_engineering.json`

## Output Schema

```json
{
  "scorer": "scorer-engineering",
  "dimension": "engineering_quality",
  "weight": 0.20,
  "sub_scores": {
    "reproducibility": {"score": 8, "evidence": "main.py:15 固定种子 42，test_report.json 显示 30 次运行 CV=3.2%"},
    "performance": {"score": 7, "evidence": "求解器超时配置合理 (600s/1000变量)，内存峰值 2.1GB"},
    "robustness": {"score": 6, "evidence": "约束重验证通过 95%，软惩罚 λ=1e4 自适应增加，但异常处理仅基础 try-except"},
    "code_quality": {"score": 8, "evidence": "code/ figures/ tables/ 目录规范，所有函数含 docstring，CODE_DELIVERABLES 运行说明完整"}
  },
  "weighted_score": 7.4,
  "evidence_refs": ["code/main.py:15", "work/test_report.json", "output/CODE_DELIVERABLES.md"],
  "verdict_contribution": "pass"
}
```

## Self-Check

- [ ] 输出文件存在且符合 schema
- [ ] 4 个子维度评分均在 0-10 区间
- [ ] 每个评分有具体证据 (文件:行号/测试用例)
- [ ] 加权总分计算正确
- [ ] 引用的代码行/测试用例真实存在

## Iteration

- 可复现性 < 6：回退 Programmer/code-implementer 补全种子/多次运行/哈希
- 鲁棒性 < 6：回退 Programmer/result-verifier 补全约束重验证/软惩罚
- 规范性 < 6：回退 Programmer/code-implementer 补全 docstring/目录/数据校验

## Env Bindings

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `code.random_seed` | 42 | 种子基准值 |
| `code.multi_run_count` | 5 | 多次运行次数基准 |
| `code.cv_threshold` | 0.10 | CV 通过阈值 |