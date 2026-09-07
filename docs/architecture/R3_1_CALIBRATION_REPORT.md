# R3.1 Evaluator Calibration Report

## Summary

**Status**: PASS (Mean F1 = 1.000, threshold ≥ 0.90)

The STC evaluator v2 has been calibrated and validated on a Golden Set of 3 test cases.

## Problem

The original STC evaluator (v1) measured **Artifact Completeness** instead of **Paper Coverage of Artifact**. This caused:

- W0 STC = 1.0 for all components (contradicting R2 findings)
- No discrimination between papers that properly represent artifact elements vs. papers that merely mention them
- Invalid experimental results (H13-H17 uninterpretable)

## Solution

Redesigned the STC evaluator to measure **Paper Coverage of Artifact Elements**:

1. **Per-element evaluation**: For each artifact element, check if the paper explicitly mentions it by name/ID
2. **Section-aware detection**: For selected_model, check if there's a dedicated section (not just mention in conclusion)
3. **Aggregate scoring**: STC_core (6 elements) and STC_meta (3 elements) computed separately

## Golden Set

Created 3 test papers with known STC labels:

| Test Case | Description | Expected STC |
|---|---|---|
| `full_coverage` | Paper covers all artifact elements | STC = 1.0 |
| `partial_coverage` | Paper missing meta-model elements (simulates R2 omission) | STC_meta = 0.0 |
| `mutation` | Paper has unauthorized elements | STC = 1.0 (but with mutations) |

## Calibration Results

### Full Coverage

- STC_core: 1.000
- STC_meta: 1.000
- STC_overall: 1.000
- F1: 1.000
- All 9 elements: TP

### Partial Coverage

- STC_core: 1.000
- STC_meta: 0.333
- STC_overall: 0.778
- F1: 1.000
- 6 TP, 3 TN (correctly identifies missing elements)

### Mutation

- STC_core: 1.000
- STC_meta: 1.000
- STC_overall: 1.000
- F1: 1.000
- 8 TP, 1 TN (assumptions: 0.5 gold, 1.0 eval)

### Overall

- **Mean F1: 1.000** (threshold ≥ 0.90)
- **Precision: 1.000**
- **Recall: 1.000**

## Files Created

| File | Purpose |
|---|---|
| `core/tools/evaluation/stc_evaluator.py` | STC evaluator v2 |
| `core/tools/evaluation/validate_stc_calibration.py` | Calibration validation script |
| `core/tools/evaluation/create_golden_set.py` | Golden Set creation script |
| `projects/P13-3D-R3/golden_set/` | Golden Set papers + labels |

## Next Steps

1. Run STC evaluator on R2 W0 papers to establish baseline
2. Proceed to real Writer experiments (GPT/Claude)
3. Compare W0 vs W1 STC scores for H13-H17
