#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aggregate_results.py — P13-3D Round 1 Aggregate Results."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]
eval_dir = ROOT / "research" / "P13-3D" / "output" / "evaluation"
fidelity_dir = ROOT / "research" / "P13-3D" / "output" / "fidelity"

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2024_A", "2021_C", "2022_B"]

# Load arm mappings
mappings = {}
for q in QUESTIONS:
    mf = eval_dir / f"{q}_arm_mapping.json"
    if mf.exists():
        mappings[q] = json.loads(mf.read_text(encoding="utf-8"))

# Load paper quality results
pq = {}
for q in QUESTIONS:
    pf = eval_dir / f"{q}_paper_quality.json"
    if pf.exists():
        pq[q] = json.loads(pf.read_text(encoding="utf-8"))

# Load fidelity results
fidelity = {}
for q in QUESTIONS:
    for arm in ARMS:
        ff = fidelity_dir / f"{q}_{arm}_fidelity.json"
        if ff.exists():
            fidelity[f"{q}_{arm}"] = json.loads(ff.read_text(encoding="utf-8"))

# De-anonymize and aggregate
print("P13-3D Round 1 — Aggregate Results")
print("=" * 70)

for q in QUESTIONS:
    mapping = mappings.get(q, {})
    reverse_map = {v: k for k, v in mapping.items()}

    pq_data = pq.get(q, {})
    papers = pq_data.get("papers", [])

    print(f"\n--- {q} ---")
    print(f"{'Arm':<8} {'Math':>6} {'Align':>6} {'Comp':>6} {'Comm':>6} {'Mean':>6} {'Fidel':>8}")
    print("-" * 50)

    for paper in papers:
        anon_id = paper["id"]
        arm = reverse_map.get(anon_id, "?")
        scores = paper["scores"]
        mean_score = sum(scores.values()) / len(scores)

        fid_key = f"{q}_{arm}"
        fid = fidelity.get(fid_key, {})
        fid_score = fid.get("fidelity_score", 0)

        print(f"{arm:<8} {scores['math_correctness']:>6} {scores['problem_alignment']:>6} "
              f"{scores['completeness']:>6} {scores['communication']:>6} "
              f"{mean_score:>6.1f} {fid_score:>7.1%}")

# Arm means
print(f"\n--- Arm Means (3 questions) ---")
for arm in ARMS:
    arm_pq = []
    arm_fid = []
    for q in QUESTIONS:
        mapping = mappings.get(q, {})
        reverse_map = {v: k for k, v in mapping.items()}

        pq_data = pq.get(q, {})
        for paper in pq_data.get("papers", []):
            if reverse_map.get(paper["id"]) == arm:
                scores = paper["scores"]
                arm_pq.append(sum(scores.values()) / len(scores))

        fid_key = f"{q}_{arm}"
        fid = fidelity.get(fid_key, {})
        if fid:
            arm_fid.append(fid.get("fidelity_score", 0))

    if arm_pq and arm_fid:
        pq_mean = sum(arm_pq) / len(arm_pq)
        fid_mean = sum(arm_fid) / len(arm_fid)
        print(f"{arm}: Paper Quality = {pq_mean:.1f}, Fidelity = {fid_mean:.1%}")

# Transmission analysis
print(f"\n--- Model Quality → Paper Quality Transmission ---")
# Model quality from P13-3C R5 (reported in P13_3C_REPORT.md)
model_scores = {"B0": 37.1, "MMA": 69.5, "B1-F": 86.2}

for arm in ARMS:
    arm_pq = []
    arm_fid = []
    for q in QUESTIONS:
        mapping = mappings.get(q, {})
        reverse_map = {v: k for k, v in mapping.items()}

        pq_data = pq.get(q, {})
        for paper in pq_data.get("papers", []):
            if reverse_map.get(paper["id"]) == arm:
                scores = paper["scores"]
                arm_pq.append(sum(scores.values()) / len(scores))

        fid_key = f"{q}_{arm}"
        fid = fidelity.get(fid_key, {})
        if fid:
            arm_fid.append(fid.get("fidelity_score", 0))

    if arm_pq and arm_fid:
        pq_mean = sum(arm_pq) / len(arm_pq)
        fid_mean = sum(arm_fid) / len(arm_fid)
        model_mean = model_scores.get(arm, 0)
        print(f"{arm}: Model={model_mean:.1f} -> Paper={pq_mean:.1f} (Fidelity={fid_mean:.1%})")
