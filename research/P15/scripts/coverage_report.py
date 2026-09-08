#!/usr/bin/env python3
"""coverage_report.py — P15.0 gate: family + failure-mode coverage check.

Family policy: every family must have ≥1 problem (single-topic families are valid).
FM-CS is excluded from the gate — competition problems don't have claim support
failures by definition (this category becomes relevant in P15.6 Paper phase).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark" / "CUMCM-Bench-v2.json"

FAMILY_MIN = 1
FM_CATEGORIES = {
    "FM-PA": "Problem Alignment",
    "FM-MC": "Model Construction",
    "FM-FC": "Formal Consistency",
    "FM-SV": "Solving",
    "FM-VA": "Validation",
}
FM_CATEGORIES_NA = {
    "FM-CS": "Claim Support (N/A for competition problems)",
}
FM_MIN = 1


def main() -> int:
    bench = json.loads(BENCH.read_text(encoding="utf-8"))
    problems = bench.get("problems", [])
    fail = 0

    # Family coverage
    family_counts: dict[str, int] = {}
    for p in problems:
        for f in p.get("family", []):
            family_counts[f] = family_counts.get(f, 0) + 1

    print("=== Family Coverage ===")
    for fam, count in sorted(family_counts.items(), key=lambda x: -x[1]):
        status = "OK" if count >= FAMILY_MIN else "WARN"
        if count < FAMILY_MIN:
            fail += 1
        print(f"  {fam}: {count} problems [{status}]")

    # Failure-mode category coverage (active categories)
    fm_cat_counts: dict[str, set[str]] = {cat: set() for cat in FM_CATEGORIES}
    for p in problems:
        qid = p.get("question_id", "")
        for fm in p.get("failure_modes", []):
            cat = fm[:5]
            if cat in fm_cat_counts:
                fm_cat_counts[cat].add(qid)

    print("\n=== Failure-Mode Category Coverage (active) ===")
    for cat, desc in FM_CATEGORIES.items():
        ids = fm_cat_counts[cat]
        status = "OK" if len(ids) >= FM_MIN else "WARN"
        if len(ids) < FM_MIN:
            fail += 1
        print(f"  {cat} ({desc}): {len(ids)} problems [{status}]")

    print("\n=== Failure-Mode Category Coverage (N/A) ===")
    for cat, desc in FM_CATEGORIES_NA.items():
        ids = fm_cat_counts.get(cat, set())
        print(f"  {cat} ({desc}): {len(ids)} problems [EXCLUDED]")

    if fail:
        print(f"\nFAIL: {fail} coverage thresholds not met")
        return 1

    print(f"\nOK: all coverage thresholds met ({len(problems)} problems)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
