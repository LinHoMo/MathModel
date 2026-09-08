#!/usr/bin/env python3
"""benchmark_completeness.py — P15.0 gate: all 7 gold fields non-empty for every problem."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark" / "CUMCM-Bench-v2.json"

GOLD_FIELDS = [
    "sub_questions", "required_deliverables", "allowed_model_families",
    "key_variables", "key_constraints", "evaluation_targets",
    "capability_dimensions", "failure_modes",
]


def main() -> int:
    bench = json.loads(BENCH.read_text(encoding="utf-8"))
    problems = bench.get("problems", [])
    missing = []

    for p in problems:
        qid = p.get("question_id", "<unknown>")
        for field in GOLD_FIELDS:
            val = p.get(field)
            if val is None:
                missing.append(f"  {qid}: {field} is null")
            elif isinstance(val, (list, dict)) and len(val) == 0:
                missing.append(f"  {qid}: {field} is empty")

    if missing:
        print(f"FAIL: {len(missing)} completeness issues")
        for m in missing:
            print(m)
        return 1

    print(f"OK: {len(problems)} problems × {len(GOLD_FIELDS)} fields = all complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
