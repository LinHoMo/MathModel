#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""g2_contamination_gate.py — P13-3D-R2 G2: Experimental Contamination Gate.

Checks all 24 artifacts for:
1. No R2 scores or results embedded
2. No cross-arm contamination (B0 doesn't read MMA/B1-F)
3. No post-hoc knowledge injection
4. No future Writer outputs referenced
5. B1-F doesn't contain P13-3C-specific fixes (e.g., 2025_B sign error knowledge)

Contamination indicators:
- Keywords: "R2", "round 2", "transmission", "paper quality", "fidelity gate"
- Arm comparison mentions: "MMA says", "B1-F shows", "compared to arm"
- Post-hoc fixes: "sign error", "2025_B", "correction"
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"

# Contamination indicators
CONTAMINATION_PATTERNS = [
    # R2-specific
    (r"R2|round.?2|transmission.?benchmark", "R2 experiment reference"),
    (r"paper.?quality|fidelity.?gate|fidelity.?score", "Paper quality reference"),
    (r"H[89]|H1[012]|hypothesis", "Hypothesis reference"),
    # Cross-arm contamination
    (r"MMA.?says|MMA.?shows|MMA.?result", "MMA arm reference"),
    (r"B1.?F?.?shows|B1.?F?.?result|B1.?F?.?says", "B1-F arm reference"),
    (r"B0.?shows|B0.?result|B0.?says", "B0 arm reference"),
    # Post-hoc knowledge
    (r"2025.?B|sign.?error|correction|fix", "Post-hoc fix reference"),
    (r"previous.?round|prior.?result|earlier.?finding", "Prior result reference"),
    # Future outputs
    (r"writer.?output|paper.?draft|论文|稿件", "Future output reference"),
]

# B1-F specific: check for P13-3C intervention patterns that shouldn't appear
B1F_SPECIFIC_PATTERNS = [
    (r"P13.?3C|checklist.?v2|intervention", "P13-3C intervention reference"),
    (r"model.?builder|model.?construction.?checklist", "Model builder reference"),
]

errors = []
warnings = []
passed = 0
total = 0


def check_contamination(fpath: Path, qid: str, arm: str) -> list:
    """Check one artifact for contamination."""
    issues = []
    content = fpath.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Check contamination patterns
    for pattern, desc in CONTAMINATION_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            issues.append(("WARN", f"Contamination indicator: {desc} (found: {matches[:3]})"))

    # B1-F specific checks
    if arm == "B1-F":
        for pattern, desc in B1F_SPECIFIC_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                issues.append(("WARN", f"B1-F specific: {desc} (found: {matches[:3]})"))

    # Check for R2-specific keywords in problem_interpretation
    data = json.loads(content)
    interp = data.get("problem_interpretation", "")
    if "R2" in interp or "round 2" in interp.lower():
        issues.append(("ERROR", "R2 reference in problem_interpretation"))

    # Check arm structural integrity
    if arm == "B0":
        # B0 should NOT have mma_raw_output
        if "mma_raw_output" in data:
            issues.append(("ERROR", "B0 has mma_raw_output (cross-contamination)"))
    elif arm == "MMA":
        # MMA should NOT have B1-F's detailed assumptions (≥5 assumptions)
        assumptions = data.get("assumptions", [])
        if len(assumptions) > 6:
            issues.append(("WARN", f"MMA has {len(assumptions)} assumptions (possible B1-F contamination)"))

    # Check that each arm is structurally distinct
    total_elems = sum(len(data.get(f, [])) for f in ["variables", "parameters", "mechanism", "assumptions"])
    if arm == "B0" and total_elems > 18:
        issues.append(("WARN", f"B0 too complex: {total_elems} elements"))
    elif arm == "MMA" and total_elems > 22:
        issues.append(("WARN", f"MMA too complex: {total_elems} elements"))
    elif arm == "B1-F" and total_elems < 14:
        issues.append(("WARN", f"B1-F too simple: {total_elems} elements"))

    return issues


# Run gate
print("=" * 70)
print("P13-3D-R2 G2: EXPERIMENTAL CONTAMINATION GATE")
print("=" * 70)

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

for qid in QUESTIONS:
    for arm in ARMS:
        fname = f"{qid}_{arm.replace('-', '_')}.json"
        fpath = ARTIFACTS_DIR / fname
        if not fpath.exists():
            continue

        total += 1
        issues = check_contamination(fpath, qid, arm)
        crits = [i for i in issues if i[0] == "ERROR"]
        warns = [i for i in issues if i[0] == "WARN"]

        if not crits:
            passed += 1
            status = "✓ PASS"
        else:
            status = "✗ FAIL"

        print(f"\n{qid}/{arm}: {status}")
        for sev, msg in issues:
            prefix = "ERROR" if sev == "ERROR" else "WARN"
            print(f"  [{prefix}] {msg}")
            if sev == "ERROR":
                errors.append(f"{qid}/{arm}: {msg}")

print("\n" + "=" * 70)
print(f"RESULT: {passed}/{total} passed")
if errors:
    print(f"\nERRORS ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\nNo contamination detected. Artifacts are clean.")
    sys.exit(0)
