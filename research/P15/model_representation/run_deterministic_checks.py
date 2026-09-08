#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run deterministic checks (DC-001 to DC-015) on a Model IR instance."""
import json

INSTANCE_PATH = r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\model_representation\example_2024_A.json"

with open(INSTANCE_PATH, "r", encoding="utf-8") as f:
    ir = json.load(f)

# Build ID sets
var_ids = {v["variable_id"] for v in ir["variables"]}
parm_ids = {p["parameter_id"] for p in ir["parameters"]}
assum_ids = {a["assumption_id"] for a in ir["assumptions"]}
mech_ids = {m["mechanism_id"] for m in ir["mechanisms"]}
eq_ids = {e["equation_id"] for e in ir["equations"]}
constraint_ids = {c["constraint_id"] for c in ir["constraints"]}
obj_ids = {o["objective_id"] for o in ir["objectives"]}
solver_ids = {s["solver_id"] for s in ir["solvers"]}
exp_ids = {e["experiment_id"] for e in ir["experiments"]}
val_ids = {v["validation_id"] for v in ir["validations"]}
claim_ids = {c["claim_id"] for c in ir["claims"]}

results = []

# DC-001: variable reference consistency
def check_dc001():
    failures = []
    for c in ir["constraints"]:
        for ref in c.get("variables_refs", []):
            if ref not in var_ids:
                failures.append(f"constraint {c['constraint_id']} references undefined variable {ref}")
    for o in ir["objectives"]:
        for ref in o.get("variables_refs", []):
            if ref not in var_ids:
                failures.append(f"objective {o['objective_id']} references undefined variable {ref}")
    for e in ir["equations"]:
        for ref in e.get("variables_refs", []):
            if ref not in var_ids:
                failures.append(f"equation {e['equation_id']} references undefined variable {ref}")
    return ("DC-001", "PASS" if not failures else "FAIL", failures)

# DC-002: parameter reference consistency
def check_dc002():
    failures = []
    for c in ir["constraints"]:
        for ref in c.get("parameters_refs", []):
            if ref not in parm_ids:
                failures.append(f"constraint {c['constraint_id']} references undefined parameter {ref}")
    for e in ir["equations"]:
        for ref in e.get("parameters_refs", []):
            if ref not in parm_ids:
                failures.append(f"equation {e['equation_id']} references undefined parameter {ref}")
    return ("DC-002", "PASS" if not failures else "FAIL", failures)

# DC-005: objective clarity
def check_dc005():
    failures = []
    for o in ir["objectives"]:
        cs = o.get("clarity_score", {})
        if not cs.get("direction_explicit") or not cs.get("expression_explicit"):
            failures.append(f"objective {o['objective_id']} lacks clear direction or expression")
        if not o.get("expression", "").strip():
            failures.append(f"objective {o['objective_id']} has empty expression")
    return ("DC-005", "PASS" if not failures else "FAIL", failures)

# DC-006: constraint completeness (every variable referenced by at least one constraint/objective)
def check_dc006():
    referenced = set()
    for c in ir["constraints"]:
        referenced.update(c.get("variables_refs", []))
    for o in ir["objectives"]:
        referenced.update(o.get("variables_refs", []))
    unreferenced = var_ids - referenced
    # WARN only, not FAIL (intermediate variables may be legitimately unreferenced by constraints)
    return ("DC-006", "WARN" if unreferenced else "PASS", [f"variable {v} not referenced by any constraint/objective" for v in sorted(unreferenced)])

# DC-007: assumption anchoring
def check_dc007():
    failures = []
    for a in ir["assumptions"]:
        has_anchor = len(a.get("anchors_to_problem", [])) > 0
        is_simplification = a["source"] in ("reasonable_simplification", "domain_knowledge")
        if not has_anchor and not is_simplification:
            failures.append(f"assumption {a['assumption_id']} has no problem anchor and is not marked as simplification/domain knowledge")
    return ("DC-007", "PASS" if not failures else "FAIL", failures)

# DC-008: equation derivation trace
def check_dc008():
    failures = []
    for e in ir["equations"]:
        dt = e.get("derivation_trace", {})
        has_from = (dt.get("from_assumptions") or dt.get("from_mechanisms") or dt.get("from_equations"))
        if not has_from:
            failures.append(f"equation {e['equation_id']} has empty derivation_trace")
    return ("DC-008", "PASS" if not failures else "FAIL", failures)

# DC-010: mechanism-variable binding
def check_dc010():
    failures = []
    for m in ir["mechanisms"]:
        if len(m.get("variables_refs", [])) == 0:
            failures.append(f"mechanism {m['mechanism_id']} references no variables")
    return ("DC-010", "PASS" if not failures else "FAIL", failures)

# DC-012: solver-equation binding
def check_dc012():
    failures = []
    for s in ir["solvers"]:
        for ref in s.get("equations_refs", []):
            if ref not in eq_ids:
                failures.append(f"solver {s['solver_id']} references undefined equation {ref}")
    return ("DC-012", "PASS" if not failures else "FAIL", failures)

# DC-013: experiment-solver binding
def check_dc013():
    failures = []
    for e in ir["experiments"]:
        ref = e.get("solver_ref")
        if ref and ref not in solver_ids:
            failures.append(f"experiment {e['experiment_id']} references undefined solver {ref}")
    return ("DC-013", "PASS" if not failures else "FAIL", failures)

# DC-014: validation-evidence binding
def check_dc014():
    failures = []
    for v in ir["validations"]:
        for ref in v.get("evidence_refs", []):
            if ref not in exp_ids:
                failures.append(f"validation {v['validation_id']} references undefined evidence {ref}")
    return ("DC-014", "PASS" if not failures else "FAIL", failures)

# DC-009: claim reverse lookup (simplified: check evidence_refs non-empty and point to existing)
def check_dc009():
    failures = []
    for c in ir["claims"]:
        ev_refs = c.get("evidence_refs", [])
        if not ev_refs:
            failures.append(f"claim {c['claim_id']} has no evidence_refs")
        for ref in ev_refs:
            if ref not in exp_ids and ref not in val_ids:
                failures.append(f"claim {c['claim_id']} references non-existent evidence {ref}")
    return ("DC-009", "PASS" if not failures else "FAIL", failures)

for check_fn in [check_dc001, check_dc002, check_dc005, check_dc006, check_dc007, check_dc008, check_dc009, check_dc010, check_dc012, check_dc013, check_dc014]:
    cid, status, failures = check_fn()
    symbol = {"PASS": "+", "FAIL": "x", "WARN": "!", "SKIP": "-"}.get(status, "?")
    print(f"[{symbol}] {cid}: {status}")
    for f in failures:
        print(f"      {f}")

print("\nDeterministic checks complete.")
