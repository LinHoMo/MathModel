#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_r2_paired_analysis.py — P13-3D-R2 Phase 3: Paired Analysis.

Computes per-question ΔModel/ΔPaper/TE and hypothesis tests.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

# P13-3C model quality scores (frozen)
P13C_MODEL_SCORES = {
    "B0": 37.1,
    "MMA": 69.5,
    "B1-F": 86.2,
}

# Load R2 paper quality scores
eval_dir = ROOT / "research" / "P13-3D-R2" / "output" / "evaluation"
paper_scores = {}
for qid in QUESTIONS:
    paper_scores[qid] = {}
    for letter in ["X", "Y", "Z"]:
        f = eval_dir / f"{qid}_{letter}_paper_quality.json"
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            arm = data["arm"]
            paper_scores[qid][arm] = data["mean"]

# Load R2 fidelity scores
fidelity_dir = ROOT / "research" / "P13-3D-R2" / "output" / "fidelity"
fidelity_scores = {}
for qid in QUESTIONS:
    fidelity_scores[qid] = {}
    for letter in ["X", "Y", "Z"]:
        f = fidelity_dir / f"{qid}_{letter}_fidelity.json"
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            arm = data["arm"]
            fidelity_scores[qid][arm] = {
                "coverage": data["coverage_fidelity"],
                "semantic": data["semantic_fidelity"],
                "additions": len(data["mutation_audit"]["additions"]),
                "deletions": len(data["mutation_audit"]["deletions"]),
                "failures": [f["code"] for f in data["writer_failures"]],
            }

# Compute paired analysis
print("P13-3D-R2 PAIRED ANALYSIS")
print("=" * 90)
print(f"{'Q':<12} {'Regime':<10} {'ΔModel':>8} {'ΔPaper':>8} {'TE':>6} {'Cov':>6} {'Sem':>6} {'Add':>4}")
print("-" * 70)

paired_data = []
for qid in QUESTIONS:
    # Get regime from question ID
    regime_map = {
        "2019_A": "Mech", "2022_A": "Mech",
        "2017_B": "Data", "2022_C": "Data",
        "2020_B": "Opt", "2024_B": "Opt",
        "2023_C": "Hybrid", "2024_C": "Hybrid",
    }
    regime = regime_map.get(qid, "Unknown")

    # ΔModel = B1-F model score - B0 model score
    delta_model = P13C_MODEL_SCORES["B1-F"] - P13C_MODEL_SCORES["B0"]

    # ΔPaper = B1-F paper score - B0 paper score
    b1_paper = paper_scores.get(qid, {}).get("B1-F", 0)
    b0_paper = paper_scores.get(qid, {}).get("B0", 0)
    delta_paper = b1_paper - b0_paper

    # TE = ΔPaper / ΔModel
    te = delta_paper / delta_model if delta_model != 0 else 0

    # Fidelity
    b1_fidelity = fidelity_scores.get(qid, {}).get("B1-F", {})
    cov = b1_fidelity.get("coverage", 0)
    sem = b1_fidelity.get("semantic", 0)
    additions = b1_fidelity.get("additions", 0)

    paired_data.append({
        "question": qid,
        "regime": regime,
        "delta_model": delta_model,
        "delta_paper": delta_paper,
        "te": te,
        "coverage": cov,
        "semantic": sem,
        "additions": additions,
    })

    print(f"{qid:<12} {regime:<10} {delta_model:>+7.1f} {delta_paper:>+7.1f} "
          f"{te:>5.2f} {cov:>5.1%} {sem:>5.1%} {additions:>4}")

# Summary statistics
print()
print("SUMMARY STATISTICS")
print("=" * 60)

te_values = [p["te"] for p in paired_data]
mean_te = sum(te_values) / len(te_values)
te_variance = sum((te - mean_te) ** 2 for te in te_values) / len(te_values)

print(f"Mean TE: {mean_te:.3f} (var: {te_variance:.4f})")
print(f"TE Min: {min(te_values):.3f}, TE Max: {max(te_values):.3f}")

# Regime breakdown
print()
print("REGIME BREAKDOWN")
print("=" * 60)
regimes = ["Mech", "Data", "Opt", "Hybrid"]
for regime in regimes:
    regime_data = [p for p in paired_data if p["regime"] == regime]
    if regime_data:
        mean_te_regime = sum(p["te"] for p in regime_data) / len(regime_data)
        mean_cov_regime = sum(p["coverage"] for p in regime_data) / len(regime_data)
        print(f"{regime:<8}: TE={mean_te_regime:.3f}, Coverage={mean_cov_regime:.1%}")

# Hypothesis tests
print()
print("HYPOTHESIS TESTS")
print("=" * 60)

# H10: B1-F > B0 in ≥6/8 questions
h10_count = sum(1 for p in paired_data if p["delta_paper"] > 0)
print(f"H10 (B1-F > B0 in ≥6/8): {h10_count}/8 {'✓ PASS' if h10_count >= 6 else '✗ FAIL'}")

# H11: Hybrid TE < Data/Opt TE
hybrid_te = [p["te"] for p in paired_data if p["regime"] == "Hybrid"]
data_te = [p["te"] for p in paired_data if p["regime"] == "Data"]
opt_te = [p["te"] for p in paired_data if p["regime"] == "Opt"]
mean_hybrid_te = sum(hybrid_te) / len(hybrid_te) if hybrid_te else 0
mean_data_te = sum(data_te) / len(data_te) if data_te else 0
mean_opt_te = sum(opt_te) / len(opt_te) if opt_te else 0
h11_pass = mean_hybrid_te < mean_data_te or mean_hybrid_te < mean_opt_te
print(f"H11 (Hybrid TE < Data/Opt): Hybrid={mean_hybrid_te:.3f}, Data={mean_data_te:.3f}, Opt={mean_opt_te:.3f} {'✓ PASS' if h11_pass else '✗ FAIL'}")

# H8: Spearman ρ (ΔModel, ΔPaper) > 0.6
try:
    from scipy import stats
    delta_models = [p["delta_model"] for p in paired_data]
    delta_papers = [p["delta_paper"] for p in paired_data]
    rho, p_val = stats.spearmanr(delta_models, delta_papers)
    h8_pass = rho > 0.6
    print(f"H8 (Spearman ρ > 0.6): ρ={rho:.3f}, p={p_val:.4f} {'✓ PASS' if h8_pass else '✗ FAIL'}")
except ImportError:
    print("H8: scipy not installed, cannot compute Spearman ρ")

# Save paired analysis
output_file = ROOT / "research" / "P13-3D-R2" / "output" / "paired_analysis.json"
output_file.write_text(json.dumps(paired_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nPaired analysis saved to {output_file}")
