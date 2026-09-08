#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_fidelity_gate_v2.py — Run Fidelity Gate v2 on all P13-3D papers.

Outputs three metrics:
  1. Coverage Fidelity: % of artifact elements in paper
  2. Unauthorized Mutation: additions/deletions/modifications
  3. Semantic Fidelity: semantic consistency

Plus Writer Failure Taxonomy (P1-P8).
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]
sys.path.insert(0, str(ROOT / "core" / "tools"))
from evaluation.fidelity_gate import compute_fidelity, WRITER_FAILURE_TAXONOMY

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

        audit_file = fidelity_dir / f"{q}_{arm}_fidelity_v2.json"
        audit_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        results.append(result)
        ma = result["mutation_audit"]
        cf = result["coverage_fidelity"]
        sf = result["semantic_fidelity"]
        print(f"{q}/{arm}: Coverage={cf:.1%} Semantic={sf:.1%} "
              f"Del={len(ma['deletions'])} Add={len(ma['additions'])} "
              f"Failures={[f['code'] for f in result['writer_failures']]}")

# Summary table
print()
print("P13-3D FIDELITY GATE v2 SUMMARY")
print("=" * 70)
print(f"{'Arm':<8} {'Coverage':>10} {'Semantic':>10} {'Del':>5} {'Add':>5} {'Failures'}")
print("-" * 55)
for arm in ARMS:
    arm_results = [r for r in results if r["arm"] == arm]
    if arm_results:
        mean_cov = sum(r["coverage_fidelity"] for r in arm_results) / len(arm_results)
        mean_sem = sum(r["semantic_fidelity"] for r in arm_results) / len(arm_results)
        total_del = sum(len(r["mutation_audit"]["deletions"]) for r in arm_results)
        total_add = sum(len(r["mutation_audit"]["additions"]) for r in arm_results)
        all_failures = set()
        for r in arm_results:
            for f in r["writer_failures"]:
                all_failures.add(f["code"])
        print(f"{arm:<8} {mean_cov:>9.1%} {mean_sem:>9.1%} {total_del:>5} {total_add:>5} {sorted(all_failures)}")

# Per-question breakdown
print()
print("PER-QUESTION BREAKDOWN")
print("=" * 70)
for q in QUESTIONS:
    print(f"\n--- {q} ---")
    print(f"{'Arm':<8} {'Cov':>8} {'Sem':>8} {'Del':>5} {'Add':>5} {'Crit':>5}")
    print("-" * 45)
    for arm in ARMS:
        r = next((r for r in results if r["problem_id"] == q and r["arm"] == arm), None)
        if r:
            ma = r["mutation_audit"]
            n_crit = sum(1 for m in ma["deletions"] if m["severity"] == "critical")
            print(f"{arm:<8} {r['coverage_fidelity']:>7.1%} {r['semantic_fidelity']:>7.1%} "
                  f"{len(ma['deletions']):>5} {len(ma['additions']):>5} {n_crit:>5}")

# Save summary
summary_file = fidelity_dir / "fidelity_summary_v2.json"
summary_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nSummary saved to {summary_file}")
