# P0 Fix Log — Measurement Instrument Recovery

**Date**: 2026-09-08
**Executor**: P0 Fix Executor
**Scope**: 5 P0-level measurement instrument fixes, all driven by confirmed failure modes from prior audit.
**Principles**: minimal patch + non-regression; no evaluator score manipulation; no v3.1.x architecture changes.

---

## P0-1: 2024_A Problem Statement Input Contamination

### Failure Mode
`examples/problems/cumcm2024A.txt` contained "防空导弹拦截弹道目标的最优制导律设计" (actually 2025_A problem), not the real 2024_A "板凳龙闹元宵". sha256 matched run manifest, confirming pipeline received wrong input.

### Before
| File | sha256 | Content |
|---|---|---|
| `examples/problems/cumcm2024A.txt` | `90a3026e5c58d87dc84ba60f0a72c4ec7617aac11645bc05b804b88841791713` | 防空导弹拦截弹道目标 (2025_A) |
| `projects/p151-2024a/inputs/cumcm2024A.txt` | `90a3026e5c58d87dc84ba60f0a72c4ec7617aac11645bc05b804b88841791713` | 防空导弹拦截弹道目标 (2025_A) |

### Fix
Copied verified real problem statement from `research/P15/benchmark/problem_cards/2024_A/problem_statement.txt` (4990 bytes) to both locations, overwriting contaminated content.

### After
| File | sha256 | Content |
|---|---|---|
| `examples/problems/cumcm2024A.txt` | `9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e` | 板凳龙闹元宵 (2024_A, verified) |
| `projects/p151-2024a/inputs/cumcm2024A.txt` | `9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e` | 板凳龙闹元宵 (2024_A, verified) |

### Verification
- Both files sha256 match `research/P15/benchmark/manifests/input_manifest.json` entry for 2024_A (`text_sha256: 9baf81fb40f82f77...`).
- Source authenticity: cross-verified against 2 independent sources (哈尔滨信息工程学院 PDF + CSDN blog).

---

## P0-2: e2e_metrics.py Empty Artifact PASS (EVAL-BUG-001)

### Failure Mode
`core/tools/evaluation/e2e_metrics.py` had no artifact non-emptiness filter. B0 measurement confirmed 16 empty-shell artifacts (payload=[]) all passed scoring.

### Fix (minimal patch)
1. Added `_is_empty_artifact(a)` helper: returns True when `payload` is None/[] AND `data` is None/{}/or contains only empty nested payload.
2. Filtered `questions`, `results`, `models` lists before scoring to exclude empty artifacts.
3. Added `empty_artifact_count` tracking per type (question/result/model) plus full-registry empty count.
4. Added `empty_artifact_filter` section to report output: `total_excluded`, `registry_empty_total`, `per_type`, `note`.
5. `render_report()` now renders "Artifact Non-Emptiness Filter" section when empty artifacts exist.
6. If all relevant artifacts are empty, dependent metrics return `null` (not 0 or 100).

### Verification (p151-2024a实测)
- 1 scoring-relevant empty artifact (Q001 question) excluded from scoring.
- Full registry: 5 empty artifacts (A001, A002, F001, P001, Q001).
- method_selection correctly returns `null` (no non-empty question artifacts to evaluate).

---

## P0-3: method_selection Pure String Matching (EVAL-BUG-003)

### Failure Mode
`e2e_metrics.py:64-82` `_method_hit` was pure normalized substring matching. Method card ID string match was treated as "method selection correct" without family-level applicability check.

### Fix (minimal patch)
1. Added `_load_card_families()`: extracts `{card_id: family}` from method card YAMLs.
2. Added `_load_benchmark_reference(problem_id)`: loads `core_methods` and `allowed_model_families` from `research/P15/benchmark/CUMCM-Bench-v2.json`.
3. Added `_infer_problem_id(project_dir, gt)`: infers problem_id from gt or project name (e.g., p151-2024a → 2024_A).
4. Added `_method_family_hit(card_id, card_families, reference_methods)`: returns `(hit, is_alternative)` — family match = hit; card exists but family outside reference = alternative_method.
5. method_selection now uses family check as primary, with original `_method_hit` as backward-compatible fallback.
6. Reports `method_selection_basis`: `"allowed_model_families"` if field exists, `"core_methods_reference"` if benchmark core_methods used, `"gt_methods_fallback"` otherwise.
7. Alternative methods marked explicitly with `alternative_method_count` and explanatory note — not auto-judged wrong.
8. Original `_method_hit` preserved unchanged (existing test `test_method_hit_compact_canonicalization` passes).

### Verification (p151-2024a实测)
- `method_selection_basis = core_methods_reference`
- `reference_methods = ['kinematics', 'geometric_modeling', 'numerical_solution']` (from CUMCM-Bench-v2.json 2024_A entry)
- Agent chose `mc-topsis` (family: composite_evaluation) — correctly identified as outside reference family.

---

## P0-4: model_correctness Complete External Input Dependency (EVAL-BUG-002)

### Failure Mode
`e2e_metrics.py:177` `response.get("model_correctness_pct")` had no validation. External input n/a was silently skipped, and no structural verification of model artifact content existed.

### Fix (minimal patch)
1. Added validation: if `model_correctness_pct` is null/n/a/na/null-string/missing → `model_correctness = UNAVAILABLE`, value=`null`, explicitly excluded from total score.
2. Added `_model_structural_check(models)`: checks each model artifact for `objective` (non-empty string), `constraints` (non-empty list), `variables` (non-empty list).
3. Reports `model_correctness_structural`: PASS/FAIL, with per-model field breakdown.
4. Explicitly noted as "structural check only, not semantic correctness".
5. Invalid numeric input (TypeError/ValueError) also → UNAVAILABLE with source annotation.
6. Missing model_correctness already excluded from `summary.mean_of_available` via null filtering (unchanged behavior, now explicitly documented).

### Verification (p151-2024a实测)
- No external `model_correctness_pct` → `model_correctness = UNAVAILABLE`, value=null.
- Model M001 has data={card_id, family, shortlist} but no objective/constraints/variables → `model_correctness_structural = FAIL`.
- Correctly excluded from mean_of_available (summary: 4 computed, 4 absent).

---

## P0-5: Artifact Non-Emptiness Gate (research-layer orchestration)

### Failure Mode
`execution_gate.py` existed at `research/P15/measurement_recovery/execution_gate.py` but was not integrated into any evaluation workflow. No mechanism gated capability scoring on execution authenticity.

### Fix
Created two files (research-layer only, no core/ modifications):

1. **`research/P15/measurement_recovery/run_evaluation.ps1`** — PowerShell orchestration script:
   - Step 1: Runs `execution_gate.py --project <dir> --json <report>`
   - Step 2a: If gate returns INVALID (exit code 2) → prints "EXECUTION INVALID - skip capability scoring", lists possible causes, writes `evaluation_skipped.json`, exits 2.
   - Step 2b: If gate returns PASS (exit 0) → runs e2e_metrics via `_metrics_runner.py`, outputs JSON + Markdown reports.
   - Step 2c: If gate returns FAIL (exit 1) → warns but still runs scoring (results flagged for caution).
   - Supports `-GtPath`, `-ResponsePath`, `-OutputDir` parameters.

2. **`research/P15/measurement_recovery/_metrics_runner.py`** — Python runner invoked by the PS1 script via environment variables (`EVAL_PROJECT`, `EVAL_REPO`, `EVAL_GT`, `EVAL_RESPONSE`, `EVAL_OUTPUT`). Calls `compute_e2e_metrics()` and writes JSON + rendered Markdown.

### Verification (p151-2024a实测)
- execution_gate returns exit code 2, verdict INVALID (empty artifacts, no real execution).
- Script correctly skips e2e_metrics, outputs skip report, exits 2.
- Exit code contract: 0=PASS/scored, 1=FAIL/scored-with-warning, 2=INVALID/skipped.

---

## Files Modified

| File | Change |
|---|---|
| `examples/problems/cumcm2024A.txt` | Overwritten with real 2024_A 板凳龙 problem statement |
| `projects/p151-2024a/inputs/cumcm2024A.txt` | Overwritten with real 2024_A 板凳龙 problem statement |
| `core/tools/evaluation/e2e_metrics.py` | Minimal patch: P0-2 empty filter, P0-3 family check, P0-4 structural validation |
| `research/P15/measurement_recovery/run_evaluation.ps1` | New: evaluation orchestration script |
| `research/P15/measurement_recovery/_metrics_runner.py` | New: Python metrics runner (env-var driven) |
| `research/P15/measurement_recovery/FIX_LOG.md` | This file |

## Files NOT Modified (per constraints)
- No `.gitignore` changes
- No `core/` architecture changes (only e2e_metrics.py bug fixes)
- No evaluator scoring logic manipulation (only measurement validity fixes)
- No research evidence deletion
- No v3.1.x schema/contract changes

---

## Verification Results

| Check | Result |
|---|---|
| `py -3.12 -m pytest tests -q` | **781 passed, 11 skipped** (baseline match, zero regression) |
| `py -3.12 core/tools/catalog_check.py --check` | **PASS** — v3 dual-view + legacy 29 agent consistent |
| `py -3.12 core/tools/validate.py` | **56 passed, 1 failed** — only failure: "未找到用户创建的.tex文件" (expected, no user project) |
| `import core.tools.evaluation.e2e_metrics` | **import OK** (no syntax errors) |
| sha256 `examples/problems/cumcm2024A.txt` | `9baf81fb...` matches input_manifest.json |
| sha256 `projects/p151-2024a/inputs/cumcm2024A.txt` | `9baf81fb...` matches input_manifest.json |
| `run_evaluation.ps1` p151 test | INVALID correctly detected, scoring skipped, exit 2 |
| e2e_metrics p151实测 | empty filter works, method_selection family basis correct, model_correctness UNAVAILABLE+structural FAIL |

## Issues Encountered
1. **PowerShell here-string parsing**: Initial `run_evaluation.ps1` used double-quoted here-string (`@"..."@`) for embedded Python code, which PowerShell parsed incorrectly. Fixed by extracting Python to separate `_metrics_runner.py` driven by environment variables.
2. **PowerShell encoding**: Chinese characters in .ps1 without BOM caused garbled text on Chinese Windows (GBK default). Fixed by using English messages in the PS1 script (FIX_LOG.md remains in Chinese as Markdown).
3. **Join-Path 3-argument**: `Join-Path $PSScriptRoot "runs" "$ProjectName`_$Timestamp"` failed because Join-Path only accepts 2 positional args. Fixed with nested Join-Path.
