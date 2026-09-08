#!/usr/bin/env python3
"""validate_schema.py — P15.0 gate: schema validation for CUMCM-Bench-v2.json."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark" / "CUMCM-Bench-v2.json"
SCHEMA = ROOT / "schemas" / "p15_capability_tags.schema.json"


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _validate_entry(entry: dict, idx: int) -> list[str]:
    errors = []
    qid = entry.get("question_id", f"<index {idx}>")

    required = [
        "question_id", "year", "family", "sub_questions",
        "required_deliverables", "core_methods", "key_variables",
        "key_constraints", "evaluation_targets",
        "capability_dimensions", "failure_modes",
    ]
    for field in required:
        if field not in entry:
            errors.append(f"  {qid}: missing required field '{field}'")
        elif entry[field] is None or entry[field] == "":
            errors.append(f"  {qid}: null/empty field '{field}'")

    cd = entry.get("capability_dimensions", {})
    if isinstance(cd, dict):
        for dim in ["alignment", "construction", "consistency", "solving", "validation"]:
            if dim not in cd:
                errors.append(f"  {qid}: capability_dimensions missing '{dim}'")
            elif cd[dim] not in ("low", "medium", "high"):
                errors.append(f"  {qid}: capability_dimensions.{dim} = '{cd[dim]}' (must be low/medium/high)")

    import re
    for fm in entry.get("failure_modes", []):
        if not re.match(r"^FM-(PA|MC|FC|SV|VA|CS)-\d{2}$", fm):
            errors.append(f"  {qid}: invalid failure_mode '{fm}'")

    if isinstance(entry.get("year"), int) and not (2015 <= entry["year"] <= 2025):
        errors.append(f"  {qid}: year {entry['year']} out of range [2015,2025]")

    return errors


def main() -> int:
    bench = _load(BENCH)
    problems = bench.get("problems", [])
    all_errors = []
    for i, p in enumerate(problems):
        all_errors.extend(_validate_entry(p, i))

    if all_errors:
        print(f"FAIL: {len(all_errors)} schema errors")
        for e in all_errors:
            print(e)
        return 1

    print(f"OK: {len(problems)} problems passed schema validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
