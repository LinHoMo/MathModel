#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_fidelity_gate.py — Run Fidelity Gate on all P13-3D papers."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "tools"))
from evaluation.fidelity_gate import compute_fidelity

artifacts_dir = ROOT / "research" / "P13-3D" / "output" / "artifacts"
papers_dir = ROOT / "research" / "P13-3D" / "output" / "papers"
fidelity_dir = ROOT / "research" / "P13-3D" / "output" / "fidelity"
fidelity_dir.mkdir(parents=True, exist_ok=True)

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2024_A", "2021_C", "2022_B"]
results = []

for q in QUESTIONS:
    for arm in ARMS:
        af = artifacts_dir / f"{q}_{arm}.json"
        pf = papers_dir / f"{q}_{arm}.md"

        if not af.exists() or not pf.exists():
            print(f"SKIP {q}/{arm}: missing file")
            continue

        artifact = json.loads(af.read_text(encoding="utf-8"))
        paper = pf.read_text(encoding="utf-8")

        result = compute_fidelity(artifact, paper)
        result["problem_id"] = q
        result["arm"] = arm

        audit_file = fidelity_dir / f"{q}_{arm}_fidelity.json"
        audit_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        results.append(result)
        mc = result["mutation_count"]
        score = result["fidelity_score"]
        print(f"{q}/{arm}: Fidelity={score:.1%} mutations={mc['total']} (C={mc['critical']} M={mc['major']} m={mc['minor']})")

# Summary
print()
print("FIDELITY GATE SUMMARY")
print("=" * 60)
header = f"{'Arm':<8} {'Fidelity':>10} {'Critical':>10} {'Major':>8} {'Minor':>8}"
print(header)
print("-" * 40)
for arm in ARMS:
    arm_results = [r for r in results if r["arm"] == arm]
    if arm_results:
        mean_f = sum(r["fidelity_score"] for r in arm_results) / len(arm_results)
        total_c = sum(r["mutation_count"]["critical"] for r in arm_results)
        total_m = sum(r["mutation_count"]["major"] for r in arm_results)
        total_mi = sum(r["mutation_count"]["minor"] for r in arm_results)
        print(f"{arm:<8} {mean_f:>9.1%} {total_c:>10} {total_m:>8} {total_mi:>8}")

summary_file = fidelity_dir / "fidelity_summary.json"
summary_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nSummary saved to {summary_file}")
