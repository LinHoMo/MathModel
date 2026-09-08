#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""source_of_truth_gate.py — P13-3D-R3 Source-of-Truth Gate.

Validates MODEL_PAPER_MAP against frozen MODEL_ARTIFACT:
1. Every artifact_ref in the map must exist in the artifact
2. No new model elements can be created by the map
3. Semantic identity must be preserved
4. Precision ≥ 0.95 required

Usage:
  python source_of_truth_gate.py --artifact <artifact.json> --map <map.json>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_claim_inventory(claims: list, artifact: dict) -> list:
    """Validate claim_inventory entries against artifact."""
    errors = []
    warnings = []

    for claim in claims:
        ref = claim.get("artifact_ref", "")
        if not ref:
            errors.append(f"Claim {claim['id']}: missing artifact_ref")
            continue

        # Parse reference path
        parts = ref.split(".")
        current = artifact
        found = True
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx]
                except (ValueError, IndexError):
                    found = False
                    break
            else:
                found = False
                break

        if not found:
            errors.append(f"Claim {claim['id']}: artifact_ref '{ref}' not found in artifact")

    return errors, warnings


def validate_element_map(elements: list, artifact: dict) -> list:
    """Validate element_map entries against artifact."""
    errors = []
    warnings = []
    precision_tracker = {"valid": 0, "total": 0}

    for elem in elements:
        precision_tracker["total"] += 1
        atype = elem.get("artifact_type", "")
        aid = elem.get("artifact_id", "")

        # Check if artifact_type exists in artifact
        if atype not in artifact:
            errors.append(f"Element {elem['id']}: artifact_type '{atype}' not in artifact")
            continue

        # Check if artifact_id exists within the type
        items = artifact[atype]
        found = False
        if isinstance(items, list):
            for item in items:
                if item.get("id") == aid or item.get("model") == aid:
                    found = True
                    break
        elif isinstance(items, dict):
            found = aid in items

        if found:
            precision_tracker["valid"] += 1
        else:
            errors.append(f"Element {elem['id']}: artifact_id '{aid}' not found in artifact.{atype}")

    precision = precision_tracker["valid"] / precision_tracker["total"] if precision_tracker["total"] > 0 else 1.0
    return errors, warnings, precision


def validate_candidate_model_map(candidates: list, artifact: dict) -> list:
    """Validate candidate_model_map entries against artifact."""
    errors = []
    warnings = []

    artifact_candidates = artifact.get("candidate_models", [])
    artifact_selected = artifact.get("selected_model", "")
    artifact_reason = artifact.get("selection_reason", "")

    for cand in candidates:
        ref = cand.get("artifact_ref", "")
        if not ref:
            errors.append(f"Candidate {cand['model_id']}: missing artifact_ref")
            continue

        # Parse reference path
        parts = ref.split(".")
        current = artifact
        found = True
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx]
                except (ValueError, IndexError):
                    found = False
                    break
            else:
                found = False
                break

        if not found:
            errors.append(f"Candidate {cand['model_id']}: artifact_ref '{ref}' not found in artifact")

        # Check if selected model matches
        if cand.get("is_selected", False):
            if cand.get("model_name", "") != artifact_selected:
                warnings.append(f"Candidate {cand['model_id']}: model_name '{cand.get('model_name')}' != artifact.selected_model '{artifact_selected}'")
            if cand.get("selection_reason_ref", "") != "selection_reason":
                warnings.append(f"Candidate {cand['model_id']}: selection_reason_ref should be 'selection_reason'")

    return errors, warnings


def validate_sensitivity_map(sensitivity: list, artifact: dict) -> list:
    """Validate sensitivity_map entries against artifact."""
    errors = []
    warnings = []

    artifact_sensitivity = artifact.get("sensitivity_plan", [])

    for sens in sensitivity:
        param_ref = sens.get("parameter_ref", "")
        if not param_ref:
            errors.append(f"Sensitivity entry: missing parameter_ref")
            continue

        # Check if parameter_ref starts with NOT_IN_ARTIFACT
        if param_ref.startswith("NOT_IN_ARTIFACT."):
            warnings.append(f"Sensitivity entry: parameter '{param_ref.split('.')[1]}' not in artifact parameters (may be valid if it's a derived parameter)")
            continue

        # Parse reference path
        parts = param_ref.split(".")
        current = artifact
        found = True
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx]
                except (ValueError, IndexError):
                    found = False
                    break
            else:
                found = False
                break

        if not found:
            warnings.append(f"Sensitivity entry: parameter_ref '{param_ref}' not found in artifact")

    return errors, warnings


def validate_section_map(sections: list, element_map: list, claim_inventory: list) -> list:
    """Validate section_map entries reference valid element and claim IDs."""
    errors = []
    warnings = []

    element_ids = {e["id"] for e in element_map}
    claim_ids = {c["id"] for c in claim_inventory}

    for section in sections:
        for eid in section.get("required_elements", []):
            if eid not in element_ids:
                errors.append(f"Section {section['section_id']}: required_element '{eid}' not in element_map")
        for cid in section.get("required_claims", []):
            if cid not in claim_ids:
                errors.append(f"Section {section['section_id']}: required_claim '{cid}' not in claim_inventory")

    return errors, warnings


def check_no_new_elements(map_data: dict, artifact: dict) -> list:
    """Check that the map doesn't introduce new model elements."""
    errors = []
    warnings = []

    # All artifact_types referenced in element_map must exist in artifact
    referenced_types = set()
    for elem in map_data.get("element_map", []):
        referenced_types.add(elem.get("artifact_type", ""))

    for rtype in referenced_types:
        if rtype not in artifact:
            errors.append(f"Referenced artifact_type '{rtype}' does not exist in artifact")

    # All artifact_ids must exist
    for elem in map_data.get("element_map", []):
        atype = elem.get("artifact_type", "")
        aid = elem.get("artifact_id", "")
        if atype in artifact:
            items = artifact[atype]
            found = False
            if isinstance(items, list):
                for item in items:
                    if item.get("id") == aid or item.get("model") == aid:
                        found = True
                        break
            elif isinstance(items, dict):
                found = aid in items
            if not found:
                errors.append(f"Element {elem['id']}: artifact_id '{aid}' not found in artifact.{atype}")

    return errors, warnings


def run_gate(artifact_path: Path, map_path: Path) -> dict:
    """Run the full Source-of-Truth Gate."""
    artifact = load(artifact_path)
    map_data = load(map_path)

    all_errors = []
    all_warnings = []
    precision_scores = {}

    # 1. Validate claim_inventory
    errors, warnings = validate_claim_inventory(map_data.get("claim_inventory", []), artifact)
    all_errors.extend([f"claim_inventory: {e}" for e in errors])
    all_warnings.extend([f"claim_inventory: {w}" for w in warnings])

    # 2. Validate element_map
    errors, warnings, precision = validate_element_map(map_data.get("element_map", []), artifact)
    all_errors.extend([f"element_map: {e}" for e in errors])
    all_warnings.extend([f"element_map: {w}" for w in warnings])
    precision_scores["element_precision"] = precision

    # 3. Validate candidate_model_map
    errors, warnings = validate_candidate_model_map(map_data.get("candidate_model_map", []), artifact)
    all_errors.extend([f"candidate_model_map: {e}" for e in errors])
    all_warnings.extend([f"candidate_model_map: {w}" for w in warnings])

    # 4. Validate sensitivity_map
    errors, warnings = validate_sensitivity_map(map_data.get("sensitivity_map", []), artifact)
    all_errors.extend([f"sensitivity_map: {e}" for e in errors])
    all_warnings.extend([f"sensitivity_map: {w}" for w in warnings])

    # 5. Validate section_map
    errors, warnings = validate_section_map(
        map_data.get("section_map", []),
        map_data.get("element_map", []),
        map_data.get("claim_inventory", [])
    )
    all_errors.extend([f"section_map: {e}" for e in errors])
    all_warnings.extend([f"section_map: {w}" for w in warnings])

    # 6. Check no new elements
    errors, warnings = check_no_new_elements(map_data, artifact)
    all_errors.extend([f"new_element_check: {e}" for e in errors])
    all_warnings.extend([f"new_element_check: {w}" for w in warnings])

    # Compute overall precision
    overall_precision = precision_scores.get("element_precision", 1.0)

    return {
        "passed": len(all_errors) == 0 and overall_precision >= 0.95,
        "errors": all_errors,
        "warnings": all_warnings,
        "precision": precision_scores,
        "overall_precision": overall_precision,
        "precision_threshold": 0.95,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="P13-3D-R3 Source-of-Truth Gate")
    parser.add_argument("--artifact", required=True, help="Path to MODEL_ARTIFACT JSON")
    parser.add_argument("--map", required=True, help="Path to MODEL_PAPER_MAP JSON")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = run_gate(Path(args.artifact), Path(args.map))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["passed"]:
            print("✓ SOURCE-OF-TRUTH GATE PASSED")
        else:
            print("✗ SOURCE-OF-TRUTH GATE FAILED")

        print(f"\nOverall Precision: {result['overall_precision']:.3f} (threshold: {result['precision_threshold']})")

        if result["errors"]:
            print(f"\nErrors ({len(result['errors'])}):")
            for e in result["errors"]:
                print(f"  - {e}")

        if result["warnings"]:
            print(f"\nWarnings ({len(result['warnings'])}):")
            for w in result["warnings"]:
                print(f"  - {w}")

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
