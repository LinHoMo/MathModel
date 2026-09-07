#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r3_phase3_evaluate.py — P13-3D-R3 Phase 3: STC + Paper Quality + Mutation Evaluation.

Evaluates all 48 papers (24 W0 + 24 W1) on:
1. Structural Transmission Coverage (STC)
2. Paper Quality (4 dimensions)
3. Unauthorized Mutation

Then computes W0 vs W1 comparison for H13-H17.
"""
import json
import re
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Import Fidelity Gate v2
spec = importlib.util.spec_from_file_location("fidelity_gate", str(ROOT / "core" / "tools" / "evaluation" / "fidelity_gate.py"))
fidelity_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fidelity_gate)

# Directories
R2_ARTIFACTS = ROOT / "projects" / "P13-3D-R2" / "output" / "artifacts"
R2_PAPERS = ROOT / "projects" / "P13-3D-R2" / "output" / "papers"
R2_EVAL = ROOT / "projects" / "P13-3D-R2" / "output" / "evaluation"
R3_PAPERS = ROOT / "projects" / "P13-3D-R3" / "output" / "papers"
R3_MAPS = ROOT / "projects" / "P13-3D-R3" / "output" / "maps"
R3_EVAL = ROOT / "projects" / "P13-3D-R3" / "output" / "evaluation"
R3_STATE = ROOT / "projects" / "P13-3D-R3" / "state"

R3_EVAL.mkdir(parents=True, exist_ok=True)

# Configuration
ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

STC_COMPONENTS = [
    "candidate_model",
    "selected_model",
    "sensitivity_plan",
    "variables",
    "parameters",
    "mechanism",
    "objective",
    "constraints",
    "assumptions",
]


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def evaluate_stc(paper_text: str, artifact: dict) -> dict:
    """Evaluate Structural Transmission Coverage for a paper."""
    results = {}

    # Candidate Model: paper mentions candidate models
    cand_models = artifact.get("candidate_models", [])
    if cand_models:
        paper_has_candidate = bool(re.search(r"候选模型|模型对比|model comparison|优缺点", paper_text))
        results["candidate_model"] = 1 if paper_has_candidate else 0
    else:
        results["candidate_model"] = -1  # N/A

    # Selected Model: paper mentions selected model
    selected = artifact.get("selected_model", "")
    if selected:
        paper_has_selected = bool(re.search(r"选定模型|选择模型|selected model", paper_text))
        results["selected_model"] = 1 if paper_has_selected else 0
    else:
        results["selected_model"] = -1

    # Sensitivity Plan: paper mentions sensitivity analysis
    sens_plan = artifact.get("sensitivity_plan", [])
    if sens_plan:
        paper_has_sensitivity = bool(re.search(r"灵敏度|sensitivity|参数.*范围|±", paper_text))
        results["sensitivity_plan"] = 1 if paper_has_sensitivity else 0
    else:
        results["sensitivity_plan"] = -1

    # Variables: paper mentions variables
    variables = artifact.get("variables", [])
    if variables:
        paper_has_vars = any(
            re.search(rf"{v.get('name', '')}|{v.get('id', '')}", paper_text)
            for v in variables[:3]
        )
        results["variables"] = 1 if paper_has_vars else 0
    else:
        results["variables"] = -1

    # Parameters: paper mentions parameters
    params = artifact.get("parameters", [])
    if params:
        paper_has_params = any(
            re.search(rf"{p.get('name', '')}|{p.get('id', '')}", paper_text)
            for p in params[:3]
        )
        results["parameters"] = 1 if paper_has_params else 0
    else:
        results["parameters"] = -1

    # Mechanism: paper mentions mechanism
    mechanisms = artifact.get("mechanism", [])
    if mechanisms:
        paper_has_mechanism = bool(re.search(r"model|建模|公式|方程|equation|\\begin{equation}", paper_text))
        results["mechanism"] = 1 if paper_has_mechanism else 0
    else:
        results["mechanism"] = -1

    # Objective: paper mentions objective
    objectives = artifact.get("objective", [])
    if objectives:
        paper_has_objective = bool(re.search(r"目标|objective|优化|minimize|maximize", paper_text))
        results["objective"] = 1 if paper_has_objective else 0
    else:
        results["objective"] = -1

    # Constraints: paper mentions constraints
    constraints = artifact.get("constraints", [])
    if constraints:
        paper_has_constraints = bool(re.search(r"约束|constraint|subject to|s.t.", paper_text))
        results["constraints"] = 1 if paper_has_constraints else 0
    else:
        results["constraints"] = -1

    # Assumptions: paper mentions assumptions
    assumptions = artifact.get("assumptions", [])
    if assumptions:
        paper_has_assumptions = bool(re.search(r"假设|assumption", paper_text))
        results["assumptions"] = 1 if paper_has_assumptions else 0
    else:
        results["assumptions"] = -1

    # Compute STC scores
    applicable = [k for k, v in results.items() if v >= 0]
    present = [k for k, v in results.items() if v == 1]

    stc_overall = len(present) / max(len(applicable), 1)
    stc_core = sum(1 for k in ["variables", "parameters", "mechanism", "objective", "constraints", "assumptions"] if results.get(k) == 1) / 6
    stc_meta = sum(1 for k in ["candidate_model", "selected_model", "sensitivity_plan"] if results.get(k) == 1) / 3

    return {
        "components": results,
        "stc_overall": stc_overall,
        "stc_core": stc_core,
        "stc_meta": stc_meta,
    }


def evaluate_paper_quality(paper_text: str) -> dict:
    """Evaluate paper quality on 4 dimensions."""
    dimensions = {}

    # 1. Mathematical Correctness
    has_equations = bool(re.search(r"\\begin{equation}|\\begin{align}", paper_text))
    has_symbols = bool(re.search(r"\\section.*符号|\\section.*符号说明", paper_text))
    dimensions["mathematical_correctness"] = min(10, 5 + 3 * has_equations + 2 * has_symbols)

    # 2. Problem Alignment
    has_problem_restate = bool(re.search(r"问题重述|problem restatement", paper_text))
    has_assumptions = bool(re.search(r"假设|assumption", paper_text))
    dimensions["problem_alignment"] = min(10, 5 + 3 * has_problem_restate + 2 * has_assumptions)

    # 3. Completeness
    sections = ["摘要", "问题重述", "模型假设", "符号说明", "模型建立", "候选模型", "灵敏度", "模型评价"]
    present = sum(1 for s in sections if re.search(s, paper_text))
    dimensions["completeness"] = min(10, 2 + 8 * (present / len(sections)))

    # 4. Communication
    has_references = bool(re.search(r"参考文献|\\cite|\\bibitem", paper_text))
    has_figures = bool(re.search(r"图|figure|\\includegraphics", paper_text))
    has_tables = bool(re.search(r"表|table|\\begin{table}", paper_text))
    dimensions["communication"] = min(10, 4 + 2 * has_references + 2 * has_figures + 2 * has_tables)

    # Overall
    dimensions["overall"] = sum(dimensions.values()) / len(dimensions)

    return dimensions


def evaluate_mutation(paper_text: str, artifact: dict) -> dict:
    """Evaluate unauthorized model mutation."""
    mutations = []

    # Check if paper introduces new variables not in artifact
    artifact_vars = {v.get("name", "") for v in artifact.get("variables", [])}
    artifact_params = {p.get("name", "") for p in artifact.get("parameters", [])}
    all_artifact_names = artifact_vars | artifact_params

    # Find potential new variables in paper
    paper_vars = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*", paper_text)
    new_vars = [v for v in paper_vars if v not in all_artifact_names and len(v) > 2]

    if new_vars:
        mutations.append({
            "type": "addition",
            "description": f"New variables not in artifact: {new_vars[:3]}",
            "severity": "low"
        })

    # Check for unauthorized model changes
    selected_model = artifact.get("selected_model", "")
    if selected_model and selected_model not in paper_text:
        mutations.append({
            "type": "deletion",
            "description": f"Selected model '{selected_model}' not mentioned",
            "severity": "medium"
        })

    return {
        "mutations": mutations,
        "mutation_count": len(mutations),
        "has_unauthorized": any(m["severity"] in ["medium", "high"] for m in mutations),
    }


# ═══════════════════════════════════════════════════════════════
# Step 1: Evaluate all 48 papers
# ═══════════════════════════════════════════════════════════════

print("=" * 70)
print("STEP 1: EVALUATE ALL 48 PAPERS")
print("=" * 70)

all_results = []

# Load R2 arm mapping
r2_manifest = json.loads((R2_PAPERS / "manifest.json").read_text(encoding="utf-8"))
r2_arm_mapping = {}
for paper in r2_manifest["papers"]:
    qid = paper["problem_id"]
    letter = paper["letter"]
    arm = paper["arm"]
    r2_arm_mapping[f"{qid}_{letter}"] = arm

for qid in QUESTIONS:
    for arm in ARMS:
        # === W0 Paper ===
        # Find which letter corresponds to this arm
        w0_letter = None
        for letter in ["X", "Y", "Z"]:
            key = f"{qid}_{letter}"
            if key in r2_arm_mapping and r2_arm_mapping[key] == arm:
                w0_letter = letter
                break
        
        if w0_letter:
            w0_file = R2_PAPERS / f"{qid}_{w0_letter}.md"
            if w0_file.exists():
                w0_text = w0_file.read_text(encoding="utf-8")
                artifact_file = R2_ARTIFACTS / f"{qid}_{arm.replace('-', '_')}.json"
                artifact = json.loads(artifact_file.read_text(encoding="utf-8"))

                stc_w0 = evaluate_stc(w0_text, artifact)
                pq_w0 = evaluate_paper_quality(w0_text)
                mut_w0 = evaluate_mutation(w0_text, artifact)

                all_results.append({
                    "problem_id": qid,
                    "arm": arm,
                    "writer": "W0",
                    "letter": w0_letter,
                    "stc": stc_w0,
                    "paper_quality": pq_w0,
                    "mutation": mut_w0,
                })

        # === W1 Paper ===
        w1_file = R3_PAPERS / f"{qid}_{arm.replace('-', '_')}_W1.md"
        if w1_file.exists():
            w1_text = w1_file.read_text(encoding="utf-8")
            artifact_file = R2_ARTIFACTS / f"{qid}_{arm.replace('-', '_')}.json"
            artifact = json.loads(artifact_file.read_text(encoding="utf-8"))

            stc_w1 = evaluate_stc(w1_text, artifact)
            pq_w1 = evaluate_paper_quality(w1_text)
            mut_w1 = evaluate_mutation(w1_text, artifact)

            all_results.append({
                "problem_id": qid,
                "arm": arm,
                "writer": "W1",
                "stc": stc_w1,
                "paper_quality": pq_w1,
                "mutation": mut_w1,
            })

# Save all results
results_path = R3_EVAL / "all_evaluation_results.json"
results_path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"  Saved: {results_path}")
print(f"  Total evaluations: {len(all_results)}")

# ═══════════════════════════════════════════════════════════════
# Step 2: Compute W0 vs W1 Comparison
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 2: W0 vs W1 COMPARISON")
print("=" * 70)

# Group by writer
w0_results = [r for r in all_results if r["writer"] == "W0"]
w1_results = [r for r in all_results if r["writer"] == "W1"]

# Compute mean STC by writer
def mean_stc(results, component):
    vals = [r["stc"]["components"].get(component, 0) for r in results if r["stc"]["components"].get(component, -1) >= 0]
    return sum(vals) / max(len(vals), 1)

print("\n--- STC Comparison (W0 vs W1) ---")
for comp in STC_COMPONENTS:
    w0_mean = mean_stc(w0_results, comp)
    w1_mean = mean_stc(w1_results, comp)
    delta = w1_mean - w0_mean
    print(f"  {comp:20s}: W0={w0_mean:.3f}, W1={w1_mean:.3f}, Δ={delta:+.3f}")

# Overall STC
w0_stc_overall = sum(r["stc"]["stc_overall"] for r in w0_results) / len(w0_results)
w1_stc_overall = sum(r["stc"]["stc_overall"] for r in w1_results) / len(w1_results)
print(f"\n  {'STC_overall':20s}: W0={w0_stc_overall:.3f}, W1={w1_stc_overall:.3f}, Δ={w1_stc_overall - w0_stc_overall:+.3f}")

# Core STC
w0_stc_core = sum(r["stc"]["stc_core"] for r in w0_results) / len(w0_results)
w1_stc_core = sum(r["stc"]["stc_core"] for r in w1_results) / len(w1_results)
print(f"  {'STC_core':20s}: W0={w0_stc_core:.3f}, W1={w1_stc_core:.3f}, Δ={w1_stc_core - w0_stc_core:+.3f}")

# Meta STC (H13 target)
w0_stc_meta = sum(r["stc"]["stc_meta"] for r in w0_results) / len(w0_results)
w1_stc_meta = sum(r["stc"]["stc_meta"] for r in w1_results) / len(w1_results)
print(f"  {'STC_meta':20s}: W0={w0_stc_meta:.3f}, W1={w1_stc_meta:.3f}, Δ={w1_stc_meta - w0_stc_meta:+.3f}")

print("\n--- Paper Quality Comparison (W0 vs W1) ---")
dims = ["mathematical_correctness", "problem_alignment", "completeness", "communication", "overall"]
for dim in dims:
    w0_mean = sum(r["paper_quality"][dim] for r in w0_results) / len(w0_results)
    w1_mean = sum(r["paper_quality"][dim] for r in w1_results) / len(w1_results)
    delta = w1_mean - w0_mean
    print(f"  {dim:30s}: W0={w0_mean:.2f}, W1={w1_mean:.2f}, Δ={delta:+.2f}")

print("\n--- Mutation Comparison (W0 vs W1) ---")
w0_mut = sum(r["mutation"]["mutation_count"] for r in w0_results)
w1_mut = sum(r["mutation"]["mutation_count"] for r in w1_results)
print(f"  Total mutations: W0={w0_mut}, W1={w1_mut}, Δ={w1_mut - w0_mut:+d}")

# ═══════════════════════════════════════════════════════════════
# Step 3: Per-Arm Comparison (H15)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 3: PER-ARM COMPARISON (H15)")
print("=" * 70)

for arm in ARMS:
    w0_arm = [r for r in w0_results if r["arm"] == arm]
    w1_arm = [r for r in w1_results if r["arm"] == arm]

    if w0_arm and w1_arm:
        w0_pq = sum(r["paper_quality"]["overall"] for r in w0_arm) / len(w0_arm)
        w1_pq = sum(r["paper_quality"]["overall"] for r in w1_arm) / len(w1_arm)
        print(f"  {arm:6s}: W0={w0_pq:.2f}, W1={w1_pq:.2f}, Δ={w1_pq - w0_pq:+.2f}")

# ═══════════════════════════════════════════════════════════════
# Step 4: H13-H17 Evaluation
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 4: HYPOTHESIS EVALUATION (H13-H17)")
print("=" * 70)

# H13: Meta-model STC improvement
h13_candidate = mean_stc(w1_results, "candidate_model") - mean_stc(w0_results, "candidate_model")
h13_selected = mean_stc(w1_results, "selected_model") - mean_stc(w0_results, "selected_model")
h13_sensitivity = mean_stc(w1_results, "sensitivity_plan") - mean_stc(w0_results, "sensitivity_plan")
h13_pass = h13_candidate >= 0.15 and h13_selected >= 0.15 and h13_sensitivity >= 0.15
print(f"\n  H13 — Meta-model STC Improvement:")
print(f"    Candidate model: Δ={h13_candidate:+.3f} (threshold: +0.15)")
print(f"    Selected model:  Δ={h13_selected:+.3f} (threshold: +0.15)")
print(f"    Sensitivity:     Δ={h13_sensitivity:+.3f} (threshold: +0.15)")
print(f"    Result: {'PASS' if h13_pass else 'FAIL'}")

# H14: Paper Quality Recovery
h14_w0_pq = sum(r["paper_quality"]["overall"] for r in w0_results) / len(w0_results)
h14_w1_pq = sum(r["paper_quality"]["overall"] for r in w1_results) / len(w1_results)
h14_delta = h14_w1_pq - h14_w0_pq
h14_pass = h14_delta >= 0.5
print(f"\n  H14 — Paper Quality Recovery:")
print(f"    W0 mean: {h14_w0_pq:.2f}")
print(f"    W1 mean: {h14_w1_pq:.2f}")
print(f"    Δ: {h14_delta:+.2f} (threshold: +0.5)")
print(f"    Result: {'PASS' if h14_pass else 'FAIL'}")

# H15: Capability Transmission Recovery
h15_w0_b0 = sum(r["paper_quality"]["overall"] for r in w0_results if r["arm"] == "B0") / max(len([r for r in w0_results if r["arm"] == "B0"]), 1)
h15_w0_b1f = sum(r["paper_quality"]["overall"] for r in w0_results if r["arm"] == "B1-F") / max(len([r for r in w0_results if r["arm"] == "B1-F"]), 1)
h15_w1_b0 = sum(r["paper_quality"]["overall"] for r in w1_results if r["arm"] == "B0") / max(len([r for r in w1_results if r["arm"] == "B0"]), 1)
h15_w1_b1f = sum(r["paper_quality"]["overall"] for r in w1_results if r["arm"] == "B1-F") / max(len([r for r in w1_results if r["arm"] == "B1-F"]), 1)
h15_delta_w0 = h15_w0_b1f - h15_w0_b0
h15_delta_w1 = h15_w1_b1f - h15_w1_b0
h15_pass = h15_delta_w1 > h15_delta_w0
print(f"\n  H15 — Capability Transmission Recovery:")
print(f"    W0: B0={h15_w0_b0:.2f}, B1-F={h15_w0_b1f:.2f}, Δ={h15_delta_w0:+.2f}")
print(f"    W1: B0={h15_w1_b0:.2f}, B1-F={h15_w1_b1f:.2f}, Δ={h15_delta_w1:+.2f}")
print(f"    Result: {'PASS' if h15_pass else 'FAIL'}")

# H16: No Unauthorized Mutation
h16_pass = w1_mut <= w0_mut + 2
print(f"\n  H16 — No Unauthorized Mutation:")
print(f"    W0 mutations: {w0_mut}")
print(f"    W1 mutations: {w1_mut}")
print(f"    Result: {'PASS' if h16_pass else 'FAIL'}")

# H17: Mechanistic Mediation (simplified)
print(f"\n  H17 — Mechanistic Mediation:")
print(f"    (Requires per-question ΔSTC vs ΔPaper correlation)")
print(f"    (Simplified: check if STC improvement aligns with Paper improvement)")

# Save hypothesis results
hypo_results = {
    "H13": {"pass": h13_pass, "details": {"candidate": h13_candidate, "selected": h13_selected, "sensitivity": h13_sensitivity}},
    "H14": {"pass": h14_pass, "details": {"w0": h14_w0_pq, "w1": h14_w1_pq, "delta": h14_delta}},
    "H15": {"pass": h15_pass, "details": {"w0_delta": h15_delta_w0, "w1_delta": h15_delta_w1}},
    "H16": {"pass": h16_pass, "details": {"w0": w0_mut, "w1": w1_mut}},
}

hypo_path = R3_EVAL / "hypothesis_results.json"
hypo_path.write_text(json.dumps(hypo_results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nSaved: {hypo_path}")

# ═══════════════════════════════════════════════════════════════
# Step 5: Final State
# ═══════════════════════════════════════════════════════════════

final_state = {
    "project": "P13-3D-R3",
    "current_phase": "Phase 4: Reporting",
    "phases_completed": [
        "Phase 1: Mapping Layer Design",
        "Phase 2: Mapping + Paper Generation",
        "Phase 3: Evaluation",
    ],
    "hypotheses": {
        "H13": "PASS" if h13_pass else "FAIL",
        "H14": "PASS" if h14_pass else "FAIL",
        "H15": "PASS" if h15_pass else "FAIL",
        "H16": "PASS" if h16_pass else "FAIL",
    },
    "total_evaluations": len(all_results),
}
state_path = R3_STATE / "status.json"
state_path.write_text(json.dumps(final_state, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nState: {state_path}")
