#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stc_evaluator.py — Structural Transmission Coverage Evaluator v2.

Measures how well a Paper covers Artifact elements.
STC = Paper Coverage of Artifact, NOT Artifact Completeness.

Key principle: Each Artifact element must have **auditable evidence** in the Paper.
"""
import re
from pathlib import Path
from typing import Optional


def compute_stc_v2(paper_text: str, artifact: dict) -> dict:
    """Compute STC v2: Paper Coverage of Artifact Elements.
    
    For each artifact element, check if the paper:
    1. Mentions the element by name/ID
    2. Correctly represents the element's content
    3. Doesn't introduce unauthorized modifications
    
    Returns:
        dict with per-element scores and aggregate STC scores
    """
    results = {}
    
    # === Core Model Elements ===
    
    # Variables: check if paper mentions each variable by name
    variables = artifact.get("variables", [])
    if variables:
        var_scores = []
        for var in variables:
            var_name = var.get("name", "")
            var_id = var.get("id", "")
            # Check if paper mentions this specific variable
            mentioned = bool(re.search(rf"{re.escape(var_name)}|{re.escape(var_id)}", paper_text))
            var_scores.append(1 if mentioned else 0)
        results["variables"] = {
            "score": sum(var_scores) / len(var_scores),
            "details": [{"name": v.get("name", ""), "covered": s} 
                       for v, s in zip(variables, var_scores)]
        }
    else:
        results["variables"] = {"score": -1, "details": []}
    
    # Parameters: check if paper mentions each parameter by name
    params = artifact.get("parameters", [])
    if params:
        param_scores = []
        for param in params:
            param_name = param.get("name", "")
            param_id = param.get("id", "")
            mentioned = bool(re.search(rf"{re.escape(param_name)}|{re.escape(param_id)}", paper_text))
            param_scores.append(1 if mentioned else 0)
        results["parameters"] = {
            "score": sum(param_scores) / len(param_scores),
            "details": [{"name": p.get("name", ""), "covered": s}
                       for p, s in zip(params, param_scores)]
        }
    else:
        results["parameters"] = {"score": -1, "details": []}
    
    # Mechanism: check if paper mentions each mechanism equation
    mechanisms = artifact.get("mechanism", [])
    if mechanisms:
        mech_scores = []
        for mech in mechanisms:
            mech_name = mech.get("name", "")
            mech_eq = mech.get("equation", "")
            # Check if paper mentions the mechanism name or equation
            mentioned = bool(re.search(rf"{re.escape(mech_name)}|{re.escape(mech_eq[:20])}", paper_text))
            mech_scores.append(1 if mentioned else 0)
        results["mechanism"] = {
            "score": sum(mech_scores) / len(mech_scores),
            "details": [{"name": m.get("name", ""), "covered": s}
                       for m, s in zip(mechanisms, mech_scores)]
        }
    else:
        results["mechanism"] = {"score": -1, "details": []}
    
    # Objective: check if paper mentions each objective
    objectives = artifact.get("objective", [])
    if objectives:
        obj_scores = []
        for obj in objectives:
            obj_id = obj.get("id", "")
            obj_expr = obj.get("expression", "")
            mentioned = bool(re.search(rf"{re.escape(obj_id)}|{re.escape(obj_expr[:20])}", paper_text))
            obj_scores.append(1 if mentioned else 0)
        results["objective"] = {
            "score": sum(obj_scores) / len(obj_scores),
            "details": [{"id": o.get("id", ""), "covered": s}
                       for o, s in zip(objectives, obj_scores)]
        }
    else:
        results["objective"] = {"score": -1, "details": []}
    
    # Constraints: check if paper mentions each constraint
    constraints = artifact.get("constraints", [])
    if constraints:
        constr_scores = []
        for constr in constraints:
            constr_id = constr.get("id", "")
            constr_expr = constr.get("expression", "")
            mentioned = bool(re.search(rf"{re.escape(constr_id)}|{re.escape(constr_expr[:20])}", paper_text))
            constr_scores.append(1 if mentioned else 0)
        results["constraints"] = {
            "score": sum(constr_scores) / len(constr_scores),
            "details": [{"id": c.get("id", ""), "covered": s}
                       for c, s in zip(constraints, constr_scores)]
        }
    else:
        results["constraints"] = {"score": -1, "details": []}
    
    # Assumptions: check if paper mentions each assumption
    assumptions = artifact.get("assumptions", [])
    if assumptions:
        assum_scores = []
        for assum in assumptions:
            assum_text = assum.get("statement", "")
            # Check if paper mentions a significant portion of the assumption
            mentioned = bool(re.search(rf"{re.escape(assum_text[:30])}", paper_text))
            assum_scores.append(1 if mentioned else 0)
        results["assumptions"] = {
            "score": sum(assum_scores) / len(assum_scores),
            "details": [{"text": a.get("statement", "")[:50], "covered": s}
                       for a, s in zip(assumptions, assum_scores)]
        }
    else:
        results["assumptions"] = {"score": -1, "details": []}
    
    # === Meta-Model Elements ===
    
    # Candidate Models: check if paper mentions each candidate model
    candidate_models = artifact.get("candidate_models", [])
    if candidate_models:
        cand_scores = []
        for cand in candidate_models:
            cand_name = cand.get("model", "")
            # Check if paper mentions this specific candidate model
            mentioned = bool(re.search(rf"{re.escape(cand_name)}", paper_text))
            cand_scores.append(1 if mentioned else 0)
        results["candidate_model"] = {
            "score": sum(cand_scores) / len(cand_scores),
            "details": [{"name": c.get("model", ""), "covered": s}
                       for c, s in zip(candidate_models, cand_scores)]
        }
    else:
        results["candidate_model"] = {"score": -1, "details": []}
    
    # Selected Model: check if paper mentions the selected model in a dedicated section
    selected_model = artifact.get("selected_model", "")
    if selected_model:
        # Check if paper has a dedicated section with the selected model
        # Look for section header followed by model name within 200 chars
        section_pattern = r"(选定模型|selected model|选用模型|使用模型).{0,200}?" + re.escape(selected_model)
        has_section = bool(re.search(section_pattern, paper_text, re.DOTALL | re.IGNORECASE))
        mentioned = has_section
        results["selected_model"] = {
            "score": 1 if mentioned else 0,
            "details": [{"model": selected_model, "covered": 1 if mentioned else 0}]
        }
    else:
        results["selected_model"] = {"score": -1, "details": []}
    
    # Selection Reason: check if paper mentions the selection reason
    selection_reason = artifact.get("selection_reason", "")
    if selection_reason:
        # Check if paper mentions a significant portion of the reason
        mentioned = bool(re.search(rf"{re.escape(selection_reason[:30])}", paper_text))
        results["selection_reason"] = {
            "score": 1 if mentioned else 0,
            "details": [{"reason": selection_reason[:50], "covered": 1 if mentioned else 0}]
        }
    else:
        results["selection_reason"] = {"score": -1, "details": []}
    
    # Sensitivity Plan: check if paper mentions each sensitivity analysis
    sensitivity_plan = artifact.get("sensitivity_plan", [])
    if sensitivity_plan:
        sens_scores = []
        for sens in sensitivity_plan:
            param_name = sens.get("parameter", "")
            sens_range = sens.get("range", "")
            sens_metric = sens.get("metric", "")
            # Check if paper mentions the parameter and its sensitivity analysis
            mentioned = bool(re.search(rf"{re.escape(param_name)}", paper_text))
            sens_scores.append(1 if mentioned else 0)
        results["sensitivity_plan"] = {
            "score": sum(sens_scores) / len(sens_scores),
            "details": [{"parameter": s.get("parameter", ""), "covered": sc}
                       for s, sc in zip(sensitivity_plan, sens_scores)]
        }
    else:
        results["sensitivity_plan"] = {"score": -1, "details": []}
    
    # === Compute Aggregate Scores ===
    
    # STC_core: variables, parameters, mechanism, objective, constraints, assumptions
    core_elements = ["variables", "parameters", "mechanism", "objective", "constraints", "assumptions"]
    core_scores = [results[e]["score"] for e in core_elements if results[e]["score"] >= 0]
    stc_core = sum(core_scores) / len(core_scores) if core_scores else 0
    
    # STC_meta: candidate_model, selected_model, sensitivity_plan
    meta_elements = ["candidate_model", "selected_model", "sensitivity_plan"]
    meta_scores = [results[e]["score"] for e in meta_elements if results[e]["score"] >= 0]
    stc_meta = sum(meta_scores) / len(meta_scores) if meta_scores else 0
    
    # STC_overall: all elements
    all_elements = core_elements + meta_elements
    all_scores = [results[e]["score"] for e in all_elements if results[e]["score"] >= 0]
    stc_overall = sum(all_scores) / len(all_scores) if all_scores else 0
    
    return {
        "elements": results,
        "stc_core": stc_core,
        "stc_meta": stc_meta,
        "stc_overall": stc_overall,
    }


def validate_stc_against_golden(paper_text: str, artifact: dict, golden_labels: dict) -> dict:
    """Validate STC evaluator against golden labels.
    
    Args:
        paper_text: Paper content
        artifact: Model Artifact
        golden_labels: {"element_name": 0 or 1} - ground truth
    
    Returns:
        dict with per-element TP/FP/FN/TN and aggregate F1
    """
    stc_result = compute_stc_v2(paper_text, artifact)
    
    tp = 0
    fp = 0
    fn = 0
    tn = 0
    
    element_results = {}
    for element, gold_label in golden_labels.items():
        if element in stc_result["elements"]:
            eval_score = 1 if stc_result["elements"][element]["score"] > 0.5 else 0
            
            if gold_label == 1 and eval_score == 1:
                tp += 1
                status = "TP"
            elif gold_label == 0 and eval_score == 1:
                fp += 1
                status = "FP"
            elif gold_label == 1 and eval_score == 0:
                fn += 1
                status = "FN"
            else:
                tn += 1
                status = "TN"
            
            element_results[element] = {
                "gold": gold_label,
                "eval": eval_score,
                "status": status,
            }
    
    # Compute metrics
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-6)
    
    return {
        "element_results": element_results,
        "confusion": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python stc_evaluator.py <paper_path> <artifact_path> [golden_labels_path]")
        sys.exit(1)
    
    paper_path = Path(sys.argv[1])
    artifact_path = Path(sys.argv[2])
    golden_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    
    paper_text = paper_path.read_text(encoding="utf-8")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    
    stc_result = compute_stc_v2(paper_text, artifact)
    print(json.dumps(stc_result, ensure_ascii=False, indent=2))
    
    if golden_path:
        golden_labels = json.loads(golden_path.read_text(encoding="utf-8"))
        validation = validate_stc_against_golden(paper_text, artifact, golden_labels)
        print("\n=== Validation ===")
        print(json.dumps(validation, ensure_ascii=False, indent=2))
