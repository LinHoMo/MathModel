# P15-K004 Experiment Report

## Design
- 4 Constructor × 2 Runtime × 8 problems × 2 seeds = 64 runs
- **This run**: ref constructor only (LLM-free) — 16 +RT + 16 -RT = 32 runs

## Results (ref constructor)

| Metric | Value |
|---|---|
| Total runs | 32 |
| -RT (static) | 16 |
| +RT (full pipeline) | 16 |
| Exec success rate | 16/16 |
| Validation pass rate | 16/16 |
| Fidelity aligned (≥0.8) | 0/16 |

## Per-Problem Breakdown

| Problem | Exec Pass | Val Pass | Mean Time |
|---|---|---|---|
| 2011_B | 2/2 | 2/2 | 0.08s |
| 2017_B | 2/2 | 2/2 | 0.06s |
| 2018_A | 2/2 | 2/2 | 0.05s |
| 2018_B | 2/2 | 2/2 | 0.05s |
| 2019_C | 2/2 | 2/2 | 0.05s |
| 2020_B | 2/2 | 2/2 | 0.05s |
| 2022_C | 2/2 | 2/2 | 0.05s |
| 2024_A | 2/2 | 2/2 | 0.06s |

## Interpretation

### RQ1: Does Runtime improve construction quality?
- **Cannot answer with ref constructor alone**.
- ref is a deterministic template (C3): code always executes correctly.
- All +RT runs pass because the template code is trivially correct.
- **Need gen/lin/mma constructors** to measure Runtime effect on non-trivial code.

### RQ4: Do mechanical metrics correlate with blind review?
- No blind review data available (ref constructor = control group only).
- Mechanical metrics: 100% exec/pass for ref, consistent with expectation.

## Limitations

- 仅 ref constructor（LLM-free C3），未含 gen/lin/mma
- ref 代码过于简单（确定性线性映射），+RT 总是通过
- fidelity 报告未生成（MODEL_IR 结构简单，无 fidelity 检查项触发）
- 需要 gen/lin/mma 构造器才能测量 Runtime 增益

## Next Steps

1. **gen constructor**: LLM-powered generic constructor (needs API key)
2. **lin constructor**: K003 S+V recipe constructor (needs API key)
3. **mma constructor**: MathModelAgent adapter (needs external agent)
4. **Blind review**: 3 evaluators × 64 bundles (needs evaluator infrastructure)
5. **Statistical analysis**: Mixed-effects model with constructor as fixed effect
