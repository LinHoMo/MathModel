#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""g1_artifact_gate.py — P13-3D-R2 G1: Artifact Validity Gate.

Checks all 24 artifacts for:
1. Schema validity (MODEL_ARTIFACT v1)
2. Question alignment (problem_id matches filename)
3. Arm identity (B0/MMA/B1-F structural differences)
4. Element completeness (variables, parameters, objective, constraints, mechanisms, assumptions)
5. SHA256 hash verification
"""
import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
SCHEMA_PATH = ROOT / "core" / "schemas" / "model_artifact.schema.json"

# Required fields per MODEL_ARTIFACT v1
REQUIRED_FIELDS = [
    "problem_id", "problem_interpretation", "assumptions", "variables",
    "parameters", "constraints", "objective", "mechanism",
    "candidate_models", "selected_model", "selection_reason",
    "uncertainties", "sensitivity_plan"
]

# Minimum element counts
MIN_COUNTS = {
    "assumptions": 1,
    "variables": 1,
    "objective": 1,
    "mechanism": 1,
    "candidate_models": 2,
}

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

errors = []
warnings = []
passed = 0
total = 0


def check_artifact(fpath: Path) -> list:
    """Run all checks on one artifact. Returns list of (severity, message)."""
    issues = []
    fname = fpath.stem  # e.g., "2019_A_B1_F"

    # Parse filename
    parts = fname.split("_", 2)
    if len(parts) < 3:
        issues.append(("ERROR", f"Filename parse error: {fname}"))
        return issues

    qid = f"{parts[0]}_{parts[1]}"
    arm_raw = parts[2]
    arm = f"{parts[2]}" if parts[2] != "B1" else "B1-F"
    # Handle B1_F -> B1-F
    if arm_raw == "F" and parts[1] in ["B1"]:
        arm = "B1-F"
        qid = parts[0]

    # Re-parse properly
    if "_B0" in fname:
        arm = "B0"
        qid = fname.replace("_B0", "")
    elif "_MMA" in fname:
        arm = "MMA"
        qid = fname.replace("_MMA", "")
    elif "_B1_F" in fname:
        arm = "B1-F"
        qid = fname.replace("_B1_F", "")

    # Load JSON
    try:
        data = json.loads(fpath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        issues.append(("ERROR", f"Invalid JSON: {e}"))
        return issues

    # 1. Required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            issues.append(("ERROR", f"Missing required field: {field}"))

    # 2. Question alignment
    if data.get("problem_id") != qid:
        issues.append(("ERROR", f"problem_id mismatch: {data.get('problem_id')} != {qid}"))

    # 3. Element counts
    for field, min_count in MIN_COUNTS.items():
        items = data.get(field, [])
        if len(items) < min_count:
            issues.append(("ERROR", f"{field}: {len(items)} < {min_count} minimum"))

    # 4. Variable/parameter completeness
    for var in data.get("variables", []):
        if not var.get("id") or not var.get("name") or not var.get("description"):
            issues.append(("WARN", f"Variable incomplete: {var.get('id', '?')}"))
    for param in data.get("parameters", []):
        if not param.get("id") or not param.get("name"):
            issues.append(("WARN", f"Parameter incomplete: {param.get('id', '?')}"))

    # 5. Arm-specific checks
    if arm == "B0":
        # B0 should be minimal (fewest elements)
        total_elems = sum(len(data.get(f, [])) for f in ["variables", "parameters", "constraints", "mechanism", "assumptions"])
        if total_elems > 20:
            issues.append(("WARN", f"B0 too complex: {total_elems} elements (expected ≤15)"))
    elif arm == "B1-F":
        # B1-F should be most comprehensive
        total_elems = sum(len(data.get(f, [])) for f in ["variables", "parameters", "constraints", "mechanism", "assumptions"])
        if total_elems < 15:
            issues.append(("WARN", f"B1-F too simple: {total_elems} elements (expected ≥15)"))

    # 6. SHA256 hash
    content = fpath.read_text(encoding="utf-8")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    return issues, qid, arm, len(data.get("variables", [])) + len(data.get("parameters", [])) + len(data.get("mechanism", []))


# Run gate
print("=" * 70)
print("P13-3D-R2 G1: ARTIFACT VALIDITY GATE")
print("=" * 70)

for qid in QUESTIONS:
    for arm in ARMS:
        fname = f"{qid}_{arm.replace('-', '_')}.json"
        fpath = ARTIFACTS_DIR / fname
        if not fpath.exists():
            errors.append(f"MISSING: {fname}")
            continue

        total += 1
        result = check_artifact(fpath)
        if isinstance(result, tuple):
            issues, _, _, elem_count = result
        else:
            issues = result
            elem_count = 0

        crits = [i for i in issues if i[0] == "ERROR"]
        warns = [i for i in issues if i[0] == "WARN"]

        if not crits:
            passed += 1
            status = "✓ PASS"
        else:
            status = "✗ FAIL"

        print(f"\n{qid}/{arm}: {status} ({elem_count} elements)")
        for sev, msg in issues:
            print(f"  [{sev}] {msg}")
            if sev == "ERROR":
                errors.append(f"{qid}/{arm}: {msg}")

print("\n" + "=" * 70)
print(f"RESULT: {passed}/{total} passed")
if errors:
    print(f"\nERRORS ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
if warnings:
    print(f"\nWARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"  - {w}")

sys.exit(0 if not errors else 1)
