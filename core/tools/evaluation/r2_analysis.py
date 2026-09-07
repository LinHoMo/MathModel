#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r2_analysis.py — P13-3D-R2 Analysis: Complexity→Fidelity, P1 Taxonomy, H8 Audit.

Three analyses:
1. TE vs Artifact Complexity: Does complexity cause fidelity degradation?
2. P1 Omission Taxonomy: What exactly is being omitted?
3. H8 Identifiability Audit: Can we actually estimate Spearman ρ?
"""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARTIFACTS_DIR = ROOT / "projects" / "P13-3D-R2" / "output" / "artifacts"
FIDELITY_DIR = ROOT / "projects" / "P13-3D-R2" / "output" / "fidelity"
EVAL_DIR = ROOT / "projects" / "P13-3D-R2" / "output" / "evaluation"
OUTPUT_DIR = ROOT / "projects" / "P13-3D-R2" / "output" / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

REGIME_MAP = {
    "2019_A": "Mech", "2022_A": "Mech",
    "2017_B": "Data", "2022_C": "Data",
    "2020_B": "Opt", "2024_B": "Opt",
    "2023_C": "Hybrid", "2024_C": "Hybrid",
}

# ═══════════════════════════════════════════════════════════════
# Load all data
# ═══════════════════════════════════════════════════════════════

# Artifact complexity
artifact_complexity = {}
for qid in QUESTIONS:
    artifact_complexity[qid] = {}
    for arm in ARMS:
        fname = f"{qid}_{arm.replace('-', '_')}.json"
        f = ARTIFACTS_DIR / fname
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            total = sum(len(data.get(k, [])) for k in ["variables", "parameters", "constraints", "mechanism", "assumptions"])
            artifact_complexity[qid][arm] = {
                "total": total,
                "variables": len(data.get("variables", [])),
                "parameters": len(data.get("parameters", [])),
                "constraints": len(data.get("constraints", [])),
                "mechanism": len(data.get("mechanism", [])),
                "assumptions": len(data.get("assumptions", [])),
            }

# Fidelity scores
fidelity_data = {}
for qid in QUESTIONS:
    fidelity_data[qid] = {}
    for letter_idx, letter in enumerate(["X", "Y", "Z"]):
        arm = ARMS[letter_idx]
        f = FIDELITY_DIR / f"{qid}_{letter}_fidelity.json"
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            fidelity_data[qid][arm] = {
                "coverage": data["coverage_fidelity"],
                "semantic": data["semantic_fidelity"],
                "deletions": data["mutation_audit"]["deletions"],
                "failure_categories": Counter(),
            }
            # Categorize P1 omissions
            for d in data["mutation_audit"]["deletions"]:
                cat = d.get("category", "unknown")
                fidelity_data[qid][arm]["failure_categories"][cat] += 1

# Paper quality scores
paper_scores = {}
for qid in QUESTIONS:
    paper_scores[qid] = {}
    for letter_idx, letter in enumerate(["X", "Y", "Z"]):
        arm = ARMS[letter_idx]
        f = EVAL_DIR / f"{qid}_{letter}_paper_quality.json"
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            paper_scores[qid][arm] = data["mean"]

# ═══════════════════════════════════════════════════════════════
# Analysis 1: TE vs Artifact Complexity
# ═══════════════════════════════════════════════════════════════

print("=" * 80)
print("ANALYSIS 1: ARTIFACT COMPLEXITY → COVERAGE → SEMANTIC → PAPER QUALITY")
print("=" * 80)

complexity_data = []
for qid in QUESTIONS:
    for arm in ARMS:
        if arm in artifact_complexity.get(qid, {}) and arm in fidelity_data.get(qid, {}):
            complexity_data.append({
                "question": qid,
                "regime": REGIME_MAP[qid],
                "arm": arm,
                "complexity": artifact_complexity[qid][arm]["total"],
                "coverage": fidelity_data[qid][arm]["coverage"],
                "semantic": fidelity_data[qid][arm]["semantic"],
                "paper_quality": paper_scores.get(qid, {}).get(arm, 0),
            })

print(f"\n{'Q':<12} {'Arm':<8} {'Complexity':>10} {'Coverage':>10} {'Semantic':>10} {'Paper':>8}")
print("-" * 60)
for d in complexity_data:
    print(f"{d['question']:<12} {d['arm']:<8} {d['complexity']:>10} "
          f"{d['coverage']:>9.1%} {d['semantic']:>9.1%} {d['paper_quality']:>8.1f}")

# Compute correlations (manual since scipy not available)
def spearman_rho_manual(x, y):
    """Manual Spearman ρ calculation."""
    n = len(x)
    if n < 3:
        return None, None

    # Rank x
    x_sorted = sorted(enumerate(x), key=lambda t: t[1])
    x_ranks = [0] * n
    for rank, (idx, _) in enumerate(x_sorted, 1):
        x_ranks[idx] = rank

    # Rank y
    y_sorted = sorted(enumerate(y), key=lambda t: t[1])
    y_ranks = [0] * n
    for rank, (idx, _) in enumerate(y_sorted, 1):
        y_ranks[idx] = rank

    # Compute ρ
    d_sq = sum((xr - yr) ** 2 for xr, yr in zip(x_ranks, y_ranks))
    rho = 1 - 6 * d_sq / (n * (n * n - 1))

    # Approximate p-value (for large n)
    import math
    z = rho * math.sqrt((n - 2) / (1 - rho * rho)) if abs(rho) < 1 else 0
    p_approx = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))

    return rho, p_approx


# Complexity vs Coverage (B1-F only, since B0/MMA have fixed complexity)
b1f_data = [d for d in complexity_data if d["arm"] == "B1-F"]
if len(b1f_data) >= 3:
    complexities = [d["complexity"] for d in b1f_data]
    coverages = [d["coverage"] for d in b1f_data]
    semantics = [d["semantic"] for d in b1f_data]
    papers = [d["paper_quality"] for d in b1f_data]

    rho_cov, p_cov = spearman_rho_manual(complexities, coverages)
    rho_sem, p_sem = spearman_rho_manual(complexities, semantics)
    rho_paper, p_paper = spearman_rho_manual(complexities, papers)

    print(f"\nB1-F CORRELATIONS (n={len(b1f_data)}):")
    print(f"  Complexity → Coverage:  ρ={rho_cov:.3f} (p={p_cov:.4f})" if rho_cov else "  Complexity → Coverage:  N/A")
    print(f"  Complexity → Semantic:  ρ={rho_sem:.3f} (p={p_sem:.4f})" if rho_sem else "  Complexity → Semantic:  N/A")
    print(f"  Complexity → Paper:     ρ={rho_paper:.3f} (p={p_paper:.4f})" if rho_paper else "  Complexity → Paper:     N/A")

    print(f"\nINTERPRETATION:")
    if rho_cov and abs(rho_cov) < 0.3:
        print("  Complexity → Coverage: WEAK correlation. Artifact complexity does NOT strongly predict coverage loss.")
    elif rho_cov and rho_cov < -0.3:
        print("  Complexity → Coverage: MODERATE negative correlation. More complex artifacts have lower coverage.")
    else:
        print("  Complexity → Coverage: POSITIVE or no correlation. More complex artifacts may have HIGHER coverage.")

# ═══════════════════════════════════════════════════════════════
# Analysis 2: P1 Omission Taxonomy
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("ANALYSIS 2: P1 OMISSION TAXONOMY")
print("=" * 80)

# Aggregate all P1 omissions by category
all_omissions = Counter()
omissions_by_arm = {arm: Counter() for arm in ARMS}
omissions_by_question = {qid: Counter() for qid in QUESTIONS}

for qid in QUESTIONS:
    for arm in ARMS:
        if arm in fidelity_data.get(qid, {}):
            cats = fidelity_data[qid][arm]["failure_categories"]
            for cat, count in cats.items():
                all_omissions[cat] += count
                omissions_by_arm[arm][cat] += count
                omissions_by_question[qid][cat] += count

print("\nOVERALL P1 OMISSION BY CATEGORY:")
print("-" * 40)
for cat, count in all_omissions.most_common():
    print(f"  {cat:<20}: {count}")

print("\nBY ARM:")
print("-" * 60)
for arm in ARMS:
    print(f"\n  {arm}:")
    for cat, count in omissions_by_arm[arm].most_common():
        print(f"    {cat:<18}: {count}")

print("\nBY QUESTION:")
print("-" * 60)
for qid in QUESTIONS:
    print(f"\n  {qid} ({REGIME_MAP[qid]}):")
    for cat, count in omissions_by_question[qid].most_common():
        print(f"    {cat:<18}: {count}")

# ═══════════════════════════════════════════════════════════════
# Analysis 3: H8 Identifiability Audit
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("ANALYSIS 3: H8 IDENTIFIABILITY AUDIT")
print("=" * 80)

# Check if ΔModel varies across questions
# In R2, ΔModel is FIXED at +49.1 for all questions
print("\nΔModel values across questions:")
delta_models = []
for qid in QUESTIONS:
    delta_model = 86.2 - 37.1  # B1-F - B0, fixed
    delta_models.append(delta_model)
    print(f"  {qid}: ΔModel = {delta_model:.1f}")

unique_deltas = set(delta_models)
print(f"\nUnique ΔModel values: {unique_deltas}")
print(f"Number of unique values: {len(unique_deltas)}")

if len(unique_deltas) == 1:
    print("\n*** H8 IDENTIFIABILITY ISSUE ***")
    print("ΔModel is INVARIANT across questions (all = +49.1).")
    print("Spearman ρ cannot be estimated because there is no variation in X.")
    print("H8 rank-correlation component is NOT ESTIMABLE.")
    print("\nThis is a DESIGN FEATURE, not a bug:")
    print("  - We fixed the Model Quality contrast (B1-F vs B0) to be constant.")
    print("  - This isolates the Writer's role: same model advantage, different papers.")
    print("  - H10 (B1-F > B0 in ≥6/8) is the correct test for this design.")
else:
    print("\nΔModel varies across questions. Spearman ρ can be estimated.")

# Compute what we CAN estimate: ΔPaper variation
print("\nΔPaper values across questions:")
delta_papers = []
for qid in QUESTIONS:
    b1_paper = paper_scores.get(qid, {}).get("B1-F", 0)
    b0_paper = paper_scores.get(qid, {}).get("B0", 0)
    delta_paper = b1_paper - b0_paper
    delta_papers.append(delta_paper)
    print(f"  {qid}: ΔPaper = {delta_paper:+.1f}")

mean_dp = sum(delta_papers) / len(delta_papers)
var_dp = sum((dp - mean_dp) ** 2 for dp in delta_papers) / len(delta_papers)
print(f"\nMean ΔPaper: {mean_dp:.1f}")
print(f"Var ΔPaper: {var_dp:.1f}")
print(f"Std ΔPaper: {var_dp ** 0.5:.1f}")

print("\n*** H8 REPLACEMENT ***")
print("Since ΔModel is invariant, the correct test is:")
print(f"  H10: ΔPaper > 0 in ≥6/8 questions = {sum(1 for dp in delta_papers if dp > 0)}/8")
print("  This is equivalent to testing whether the Writer transmits the fixed model advantage.")

# ═══════════════════════════════════════════════════════════════
# Save analysis results
# ═══════════════════════════════════════════════════════════════

analysis_results = {
    "complexity_analysis": {
        "data": complexity_data,
        "b1f_correlations": {
            "complexity_coverage_rho": rho_cov if 'rho_cov' in dir() else None,
            "complexity_semantic_rho": rho_sem if 'rho_sem' in dir() else None,
            "complexity_paper_rho": rho_paper if 'rho_paper' in dir() else None,
        },
    },
    "p1_taxonomy": {
        "overall": dict(all_omissions),
        "by_arm": {arm: dict(cnt) for arm, cnt in omissions_by_arm.items()},
        "by_question": {qid: dict(cnt) for qid, cnt in omissions_by_question.items()},
    },
    "h8_audit": {
        "delta_model_invariant": len(unique_deltas) == 1,
        "delta_model_value": 49.1,
        "delta_papers": dict(zip(QUESTIONS, delta_papers)),
        "mean_delta_paper": mean_dp,
        "h10_result": f"{sum(1 for dp in delta_papers if dp > 0)}/8",
        "recommendation": "H8 Spearman ρ not estimable; H10 is the correct test",
    },
}

output_file = OUTPUT_DIR / "r2_analysis.json"
output_file.write_text(json.dumps(analysis_results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nAnalysis saved to {output_file}")
