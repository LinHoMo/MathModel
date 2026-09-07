#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""input_freeze_gate.py — P13-3D G0 Input Freeze Gate。

Writer 只能读取 freeze manifest 指定的 artifact，不能读取：
- P13-3C report / 历史 scorecard
- 任何可能泄漏 arm 信息的文件
- 任何可能泄漏 prior evaluation results 的文件

Pipeline: G0 Input Freeze → Generate → Fidelity → Blind Eval → Aggregate

用法:
  python input_freeze_gate.py --project P13-3D
  python input_freeze_gate.py --project P13-3D --lock
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2024_A", "2021_C", "2022_B"]


def compute_sha256(data: dict) -> str:
    content = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=str(ROOT),
            timeout=5,
        )
        return result.stdout.strip()[:12] if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def check_info_leak(project_dir: Path) -> list[str]:
    """Check that no arm-identifying or evaluation result files exist in writer input area."""
    leaks = []

    # Check for P13-3C report in writer area
    writer_dir = project_dir / "output" / "papers"
    if writer_dir.exists():
        for f in writer_dir.rglob("*"):
            if f.suffix == ".md" and "P13_3C" in f.name:
                leaks.append(f"Info leak: {f.name} contains P13-3C reference")
            if f.suffix == ".json" and "scorecard" in f.name.lower():
                leaks.append(f"Info leak: {f.name} contains scorecard data")

    return leaks


def run_gate(project_dir: Path, lock: bool = False) -> dict:
    """Run the G0 Input Freeze Gate."""
    artifacts_dir = project_dir / "output" / "artifacts"
    gate_report = {
        "gate": "G0-Input-Freeze",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "artifacts": {},
        "errors": [],
        "warnings": [],
        "passed": True,
    }

    for q in QUESTIONS:
        for arm in ARMS:
            key = f"{q}_{arm}"
            artifact_path = artifacts_dir / f"{key}.json"
            manifest_path = artifacts_dir / f"{key}_manifest.json"

            entry = {
                "question_id": q,
                "arm": arm,
                "artifact_exists": artifact_path.exists(),
                "manifest_exists": manifest_path.exists(),
                "schema_version": None,
                "artifact_hash": None,
                "manifest_hash": None,
                "hash_match": None,
                "frozen": None,
                "schema_valid": None,
            }

            if not artifact_path.exists():
                gate_report["errors"].append(f"Missing artifact: {key}.json")
                gate_report["passed"] = False
                gate_report["artifacts"][key] = entry
                continue

            if not manifest_path.exists():
                gate_report["errors"].append(f"Missing manifest: {key}_manifest.json")
                gate_report["passed"] = False
                gate_report["artifacts"][key] = entry
                continue

            # Load and verify
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            entry["schema_version"] = manifest.get("artifact", {}).get("schema_version")
            entry["artifact_hash"] = compute_sha256(artifact)
            entry["manifest_hash"] = manifest.get("artifact", {}).get("hash")
            entry["hash_match"] = entry["artifact_hash"] == entry["manifest_hash"]
            entry["frozen"] = manifest.get("freezing", {}).get("status") == "frozen"

            # Schema check (manual)
            required = ["problem_id", "problem_interpretation", "assumptions", "variables",
                        "parameters", "constraints", "objective", "mechanism",
                        "candidate_models", "selected_model", "selection_reason",
                        "uncertainties", "sensitivity_plan"]
            missing = [f for f in required if f not in artifact]
            entry["schema_valid"] = len(missing) == 0

            if not entry["hash_match"]:
                gate_report["errors"].append(
                    f"Hash mismatch: {key} — artifact={entry['artifact_hash'][:16]}... "
                    f"manifest={entry['manifest_hash'][:16]}...")
                gate_report["passed"] = False

            if not entry["frozen"]:
                gate_report["errors"].append(f"Not frozen: {key}")
                gate_report["passed"] = False

            if not entry["schema_valid"]:
                gate_report["errors"].append(f"Schema invalid: {key} missing {missing}")
                gate_report["passed"] = False

            gate_report["artifacts"][key] = entry

    # Check info leaks
    leaks = check_info_leak(project_dir)
    if leaks:
        gate_report["warnings"].extend(leaks)

    # Lock: mark gate as passed and record
    if lock and gate_report["passed"]:
        gate_report["locked_at"] = datetime.now(timezone.utc).isoformat()
        gate_report["lock_status"] = "LOCKED"

        # Save gate report
        gate_file = project_dir / "state" / "g0_freeze_gate.json"
        gate_file.write_text(json.dumps(gate_report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Gate locked: {gate_file}")

    return gate_report


def main():
    parser = argparse.ArgumentParser(description="P13-3D G0 Input Freeze Gate")
    parser.add_argument("--project", default="P13-3D")
    parser.add_argument("--lock", action="store_true", help="Lock gate on pass")
    args = parser.parse_args()

    project_dir = ROOT / "projects" / args.project
    report = run_gate(project_dir, lock=args.lock)

    # Print summary
    n_total = len(report["artifacts"])
    n_ok = sum(1 for a in report["artifacts"].values()
               if a.get("hash_match") and a.get("frozen") and a.get("schema_valid"))

    print(f"\n{'='*60}")
    print(f"G0 Input Freeze Gate — {args.project}")
    print(f"{'='*60}")
    print(f"Artifacts: {n_ok}/{n_total} passed")
    print(f"Git commit: {report['git_commit']}")

    if report["errors"]:
        print(f"\nERRORS ({len(report['errors'])}):")
        for e in report["errors"]:
            print(f"  ✗ {e}")

    if report["warnings"]:
        print(f"\nWARNINGS ({len(report['warnings'])}):")
        for w in report["warnings"]:
            print(f"  ⚠ {w}")

    if report["passed"]:
        print(f"\n✓ Gate PASSED")
        if args.lock:
            print(f"✓ Gate LOCKED — Writer inputs can now be generated")
    else:
        print(f"\n✗ Gate FAILED — Fix errors before generating Writer inputs")

    # Print per-artifact table
    print(f"\n{'Key':<20} {'Hash':<8} {'Frozen':<8} {'Schema':<8}")
    print("-" * 44)
    for key, entry in sorted(report["artifacts"].items()):
        h = "✓" if entry.get("hash_match") else "✗"
        f = "✓" if entry.get("frozen") else "✗"
        s = "✓" if entry.get("schema_valid") else "✗"
        print(f"{key:<20} {h:<8} {f:<8} {s:<8}")


if __name__ == "__main__":
    main()
