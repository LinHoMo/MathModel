#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_r2_fidelity.py — P13-3D-R2 Phase 3: Fidelity Gate v2 on 24 papers.

Runs Coverage/Mutation/Semantic fidelity + Writer Failure Taxonomy.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]
sys.path.insert(0, str(ROOT / "core" / "tools"))
from evaluation.fidelity_gate import compute_fidelity

ARTIFACTS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
PAPERS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "papers"
FIDELITY_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "fidelity"
FIDELITY_DIR.mkdir(parents=True, exist_ok=True)

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

# Load arm mapping
arm_mapping = json.loads((ROOT / "research" / "P13-3D-R2" / "output" / "writer_inputs" / "arm_mapping.json").read_text(encoding="utf-8"))

results = []

for qid in QUESTIONS:
    mapping = arm_mapping[qid]
    for letter in ["X", "Y", "Z"]:
        arm = mapping[letter]

        # Load artifact and paper
        af = ARTIFACTS_DIR / f"{qid}_{arm.replace('-', '_')}.json"
        pf = PAPERS_DIR / f"{qid}_{letter}.md"

        if not af.exists() or not pf.exists():
            print(f"SKIP {qid}/{letter}: missing file")
            continue

        artifact = json.loads(af.read_text(encoding="utf-8"))
        paper = pf.read_text(encoding="utf-8")

        # Run fidelity gate
        result = compute_fidelity(artifact, paper)
        result["problem_id"] = qid
        result["arm"] = arm
        result["letter"] = letter

        # Save audit log
        audit_file = FIDELITY_DIR / f"{qid}_{letter}_fidelity.json"
        audit_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        results.append(result)
        ma = result["mutation_audit"]
        cf = result["coverage_fidelity"]
        sf = result["semantic_fidelity"]
        print(f"{qid}/{letter} ({arm}): Cov={cf:.1%} Sem={sf:.1%} "
              f"Del={len(ma['deletions'])} Add={len(ma['additions'])} "
              f"Failures={[f['code'] for f in result['writer_failures']]}")

# Summary table
print()
print("P13-3D-R2 FIDELITY GATE SUMMARY")
print("=" * 80)
print(f"{'Q':<12} {'Letter':>6} {'Arm':<8} {'Cov':>8} {'Sem':>8} {'Del':>5} {'Add':>5} {'Failures'}")
print("-" * 70)
for r in results:
    ma = r["mutation_audit"]
    failures_str = ",".join(sorted(set(f["code"] for f in r["writer_failures"])))
    print(f"{r['problem_id']:<12} {r['letter']:>6} {r['arm']:<8} "
          f"{r['coverage_fidelity']:>7.1%} {r['semantic_fidelity']:>7.1%} "
          f"{len(ma['deletions']):>5} {len(ma['additions']):>5} {failures_str}")

# Arm means
print()
print("ARM MEANS (across 8 questions)")
print("=" * 60)
print(f"{'Arm':<8} {'Cov':>8} {'Sem':>8} {'Del':>5} {'Add':>5} {'Failures'}")
print("-" * 50)
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
        print(f"{arm:<8} {mean_cov:>7.1%} {mean_sem:>7.1%} {total_del:>5} {total_add:>5} {sorted(all_failures)}")

# Save summary
summary_file = FIDELITY_DIR / "fidelity_summary.json"
summary_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nSummary saved to {summary_file}")
