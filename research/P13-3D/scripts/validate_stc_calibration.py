#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_stc_calibration.py — Validate STC Evaluator on Golden Set."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stc_evaluator import compute_stc_v2, validate_stc_against_golden

ROOT = Path(__file__).resolve().parent.parent.parent
golden_dir = ROOT / "research" / "P13-3D-R3" / "golden_set"
artifact = json.loads((golden_dir / "artifact_2019_A_MMA.json").read_text(encoding="utf-8"))

test_cases = ["full_coverage", "partial_coverage", "mutation"]

print("=" * 70)
print("STC EVALUATOR CALIBRATION")
print("=" * 70)

all_f1 = []

for tc in test_cases:
    paper = (golden_dir / f"{tc}_paper.md").read_text(encoding="utf-8")
    golden = json.loads((golden_dir / f"{tc}_golden.json").read_text(encoding="utf-8"))
    
    print(f"\n--- {tc.upper()} ---")
    
    stc = compute_stc_v2(paper, artifact)
    print(f"STC_core: {stc['stc_core']:.3f}")
    print(f"STC_meta: {stc['stc_meta']:.3f}")
    print(f"STC_overall: {stc['stc_overall']:.3f}")
    
    validation = validate_stc_against_golden(paper, artifact, golden)
    print(f"Precision: {validation['precision']:.3f}")
    print(f"Recall: {validation['recall']:.3f}")
    print(f"F1: {validation['f1']:.3f}")
    print(f"Confusion: {validation['confusion']}")
    
    print("Per-element:")
    for elem, result in validation["element_results"].items():
        print(f"  {elem}: gold={result['gold']}, eval={result['eval']}, status={result['status']}")
    
    all_f1.append(validation["f1"])

mean_f1 = sum(all_f1) / len(all_f1)
print(f"\n{'=' * 70}")
print(f"OVERALL: Mean F1 = {mean_f1:.3f}")
print(f"Threshold: F1 >= 0.90")
if mean_f1 >= 0.90:
    print("Result: PASS")
else:
    print("Result: FAIL")
