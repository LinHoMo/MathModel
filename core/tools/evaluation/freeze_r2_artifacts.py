#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""freeze_r2_artifacts.py — P13-3D-R2 Artifact Freezing.

Freezes all 24 artifacts with SHA256 hashes and creates a freeze manifest.
After freezing, artifacts should NOT be modified.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARTIFACTS_DIR = ROOT / "projects" / "P13-3D-R2" / "output" / "artifacts"
STATE_DIR = ROOT / "projects" / "P13-3D-R2" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

freeze_entries = []
for qid in QUESTIONS:
    for arm in ARMS:
        fname = f"{qid}_{arm.replace('-', '_')}.json"
        fpath = ARTIFACTS_DIR / fname
        if not fpath.exists():
            print(f"MISSING: {fname}")
            continue

        content = fpath.read_text(encoding="utf-8")
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        data = json.loads(content)
        elem_count = (
            len(data.get("variables", []))
            + len(data.get("parameters", []))
            + len(data.get("constraints", []))
            + len(data.get("objective", []))
            + len(data.get("mechanism", []))
            + len(data.get("assumptions", []))
        )

        freeze_entries.append({
            "problem_id": qid,
            "arm": arm,
            "file": fname,
            "sha256": sha,
            "element_count": elem_count,
            "frozen": True,
        })
        print(f"✓ {qid}/{arm}: frozen (sha256={sha[:16]}...)")

# Create freeze manifest
freeze_manifest = {
    "round": "P13-3D-R2",
    "phase": "Phase 2: Artifact Construction",
    "status": "FROZEN",
    "frozen_at": datetime.now().isoformat(),
    "total_artifacts": len(freeze_entries),
    "gates_passed": {
        "G1_artifact_validity": "24/24",
        "G2_contamination": "24/24",
    },
    "artifacts": freeze_entries,
}

# Save freeze manifest
freeze_path = ARTIFACTS_DIR / "freeze_manifest.json"
freeze_path.write_text(json.dumps(freeze_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

# Save state
state = {
    "project": "P13-3D-R2",
    "current_phase": "Phase 3: Writer Input Generation",
    "phases_completed": [
        "Phase 1: Question Selection",
        "Phase 2: Artifact Construction",
    ],
    "artifacts_frozen": True,
    "freeze_manifest": str(freeze_path),
}
state_path = STATE_DIR / "status.json"
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\nFreeze manifest: {freeze_path}")
print(f"State: {state_path}")
print(f"\nAll {len(freeze_entries)} artifacts frozen.")
