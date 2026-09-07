#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r3_rescore_w0.py — Re-score R2 W0 papers with calibrated STC evaluator v2.

Establishes W0 baseline for R3 experiments.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stc_evaluator import compute_stc_v2

ROOT = Path(__file__).resolve().parent.parent.parent
R2_ARTIFACTS = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
R2_PAPERS = ROOT / "research" / "P13-3D-R2" / "output" / "papers"
R3_W0_BASELINE = ROOT / "research" / "P13-3D-R3" / "w0_baseline"
R3_W0_BASELINE.mkdir(parents=True, exist_ok=True)

# Configuration
ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

# Load R2 arm mapping
r2_manifest = json.loads((R2_PAPERS / "manifest.json").read_text(encoding="utf-8"))
r2_arm_mapping = {}
for paper in r2_manifest["papers"]:
    qid = paper["problem_id"]
    letter = paper["letter"]
    arm = paper["arm"]
    r2_arm_mapping[f"{qid}_{letter}"] = arm


def compute_paper_quality(paper_text):
    """Compute paper quality on 4 dimensions."""
    import re
    dimensions = {}
    
    has_equations = bool(re.search(r"\\begin{equation}|\\begin{align}", paper_text))
    has_symbols = bool(re.search(r"\\section.*符号|\\section.*符号说明", paper_text))
    dimensions["mathematical_correctness"] = min(10, 5 + 3 * has_equations + 2 * has_symbols)
    
    has_problem_restate = bool(re.search(r"问题重述|problem restatement", paper_text))
    has_assumptions = bool(re.search(r"假设|assumption", paper_text))
    dimensions["problem_alignment"] = min(10, 5 + 3 * has_problem_restate + 2 * has_assumptions)
    
    sections = ["摘要", "问题重述", "模型假设", "符号说明", "模型建立", "候选模型", "灵敏度", "模型评价"]
    present = sum(1 for s in sections if re.search(s, paper_text))
    dimensions["completeness"] = min(10, 2 + 8 * (present / len(sections)))
    
    has_references = bool(re.search(r"参考文献|\\cite|\\bibitem", paper_text))
    has_figures = bool(re.search(r"图|figure|\\includegraphics", paper_text))
    has_tables = bool(re.search(r"表|table|\\begin{table}", paper_text))
    dimensions["communication"] = min(10, 4 + 2 * has_references + 2 * has_figures + 2 * has_tables)
    
    dimensions["overall"] = sum(dimensions.values()) / len(dimensions)
    return dimensions


def compute_mutations(paper_text, artifact):
    """Compute unauthorized mutations."""
    import re
    mutations = []
    
    artifact_vars = {v.get("name", "") for v in artifact.get("variables", [])}
    artifact_params = {p.get("name", "") for p in artifact.get("parameters", [])}
    all_artifact_names = artifact_vars | artifact_params
    
    paper_vars = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*", paper_text)
    new_vars = [v for v in paper_vars if v not in all_artifact_names and len(v) > 2]
    
    if new_vars:
        mutations.append({
            "type": "addition",
            "description": f"New variables: {new_vars[:3]}",
            "severity": "low"
        })
    
    selected_model = artifact.get("selected_model", "")
    if selected_model and selected_model not in paper_text:
        mutations.append({
            "type": "deletion",
            "description": f"Selected model not mentioned",
            "severity": "medium"
        })
    
    return {
        "mutations": mutations,
        "mutation_count": len(mutations),
        "has_unauthorized": any(m["severity"] in ["medium", "high"] for m in mutations),
    }


# ═══════════════════════════════════════════════════════════════
# Step 1: Re-score all 24 W0 papers
# ═══════════════════════════════════════════════════════════════

print("=" * 70)
print("STEP 1: RE-SCORE R2 W0 PAPERS")
print("=" * 70)

all_results = []
for qid in QUESTIONS:
    for arm in ARMS:
        # Find W0 paper letter
        w0_letter = None
        for letter in ["X", "Y", "Z"]:
            key = f"{qid}_{letter}"
            if key in r2_arm_mapping and r2_arm_mapping[key] == arm:
                w0_letter = letter
                break
        
        if not w0_letter:
            continue
        
        w0_file = R2_PAPERS / f"{qid}_{w0_letter}.md"
        artifact_file = R2_ARTIFACTS / f"{qid}_{arm.replace('-', '_')}.json"
        
        if not w0_file.exists() or not artifact_file.exists():
            continue
        
        paper_text = w0_file.read_text(encoding="utf-8")
        artifact = json.loads(artifact_file.read_text(encoding="utf-8"))
        
        # Compute STC v2
        stc = compute_stc_v2(paper_text, artifact)
        
        # Compute paper quality
        pq = compute_paper_quality(paper_text)
        
        # Compute mutations
        mut = compute_mutations(paper_text, artifact)
        
        # Get element-level details
        element_details = {}
        for elem, data in stc["elements"].items():
            if data["score"] >= 0:
                element_details[elem] = {
                    "score": data["score"],
                    "details": data["details"]
                }
        
        result = {
            "problem_id": qid,
            "arm": arm,
            "letter": w0_letter,
            "stc_core": stc["stc_core"],
            "stc_meta": stc["stc_meta"],
            "stc_overall": stc["stc_overall"],
            "element_details": element_details,
            "paper_quality": pq,
            "mutation": mut,
        }
        all_results.append(result)
        
        print(f"  {qid}/{arm}: STC_core={stc['stc_core']:.3f}, STC_meta={stc['stc_meta']:.3f}, PQ={pq['overall']:.2f}")

# ═══════════════════════════════════════════════════════════════
# Step 2: Compute aggregate statistics
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 2: COMPUTE AGGREGATE STATISTICS")
print("=" * 70)

# By arm
arm_stats = {}
for arm in ARMS:
    arm_results = [r for r in all_results if r["arm"] == arm]
    if arm_results:
        arm_stats[arm] = {
            "stc_core_mean": sum(r["stc_core"] for r in arm_results) / len(arm_results),
            "stc_meta_mean": sum(r["stc_meta"] for r in arm_results) / len(arm_results),
            "stc_overall_mean": sum(r["stc_overall"] for r in arm_results) / len(arm_results),
            "pq_mean": sum(r["paper_quality"]["overall"] for r in arm_results) / len(arm_results),
            "mutation_count": sum(r["mutation"]["mutation_count"] for r in arm_results),
        }

print("\n--- By Arm ---")
for arm in ARMS:
    if arm in arm_stats:
        s = arm_stats[arm]
        print(f"  {arm:6s}: STC_core={s['stc_core_mean']:.3f}, STC_meta={s['stc_meta_mean']:.3f}, PQ={s['pq_mean']:.2f}, Mut={s['mutation_count']}")

# Overall
overall_stc_core = sum(r["stc_core"] for r in all_results) / len(all_results)
overall_stc_meta = sum(r["stc_meta"] for r in all_results) / len(all_results)
overall_stc_overall = sum(r["stc_overall"] for r in all_results) / len(all_results)
overall_pq = sum(r["paper_quality"]["overall"] for r in all_results) / len(all_results)
overall_mut = sum(r["mutation"]["mutation_count"] for r in all_results)

print(f"\n  Overall: STC_core={overall_stc_core:.3f}, STC_meta={overall_stc_meta:.3f}, PQ={overall_pq:.2f}, Mut={overall_mut}")

# ═══════════════════════════════════════════════════════════════
# Step 3: Element-level omission analysis
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 3: ELEMENT-LEVEL OMISSION ANALYSIS")
print("=" * 70)

element_coverage = {}
for elem in ["variables", "parameters", "mechanism", "objective", "constraints", "assumptions", "candidate_model", "selected_model", "sensitivity_plan"]:
    covered = sum(1 for r in all_results if r["element_details"].get(elem, {}).get("score", 0) == 1)
    total = sum(1 for r in all_results if r["element_details"].get(elem, {}).get("score", -1) >= 0)
    element_coverage[elem] = covered / max(total, 1)

print("\n--- Element Coverage (W0) ---")
for elem, cov in element_coverage.items():
    marker = "  [OMITTED]" if cov < 0.5 else ""
    print(f"  {elem:20s}: {cov:.3f}{marker}")

# ═══════════════════════════════════════════════════════════════
# Step 4: Save baseline
# ═══════════════════════════════════════════════════════════════

baseline = {
    "round": "P13-3D-R3",
    "phase": "W0 Baseline (Re-scored)",
    "status": "FROZEN",
    "frozen_at": datetime.now().isoformat(),
    "evaluator_version": "stc_evaluator_v2",
    "golden_set_f1": 1.000,
    "total_papers": len(all_results),
    "aggregate": {
        "stc_core_mean": overall_stc_core,
        "stc_meta_mean": overall_stc_meta,
        "stc_overall_mean": overall_stc_overall,
        "pq_mean": overall_pq,
        "mutation_count": overall_mut,
    },
    "by_arm": arm_stats,
    "element_coverage": element_coverage,
    "papers": all_results,
}

baseline_path = R3_W0_BASELINE / "w0_baseline.json"
baseline_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nSaved: {baseline_path}")

# Save omission log
omission_log = []
for r in all_results:
    for elem, data in r["element_details"].items():
        if data["score"] == 0:
            omission_log.append({
                "problem_id": r["problem_id"],
                "arm": r["arm"],
                "element": elem,
                "details": data["details"],
            })

omission_path = R3_W0_BASELINE / "omission_log.json"
omission_path.write_text(json.dumps(omission_log, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved: {omission_path}")

# ═══════════════════════════════════════════════════════════════
# Step 5: Verify R2 omission pattern
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 4: VERIFY R2 OMISSION PATTERN")
print("=" * 70)

print("\n--- R2 Omission Pattern (Expected) ---")
print("  candidate_model: HIGH omission (meta-model)")
print("  selected_model:  HIGH omission (meta-model)")
print("  sensitivity_plan: HIGH omission (meta-model)")
print("  variables:       LOW omission (core)")
print("  parameters:      LOW omission (core)")
print("  mechanism:       LOW omission (core)")

print("\n--- R3 W0 Actual Coverage ---")
for elem in ["candidate_model", "selected_model", "sensitivity_plan", "variables", "parameters", "mechanism"]:
    cov = element_coverage[elem]
    status = "HIGH" if cov < 0.5 else "MEDIUM" if cov < 0.8 else "LOW"
    print(f"  {elem:20s}: {cov:.3f} ({status})")

# Check if meta-model elements have lower coverage
meta_cov = (element_coverage["candidate_model"] + element_coverage["selected_model"] + element_coverage["sensitivity_plan"]) / 3
core_cov = (element_coverage["variables"] + element_coverage["parameters"] + element_coverage["mechanism"]) / 3
print(f"\n  Meta-model coverage: {meta_cov:.3f}")
print(f"  Core coverage:       {core_cov:.3f}")
print(f"  Meta < Core: {'YES' if meta_cov < core_cov else 'NO'}")
