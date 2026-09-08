#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mark_executor_type.py — Batch-annotate executor_type on run records and artifacts.

Injects the `executor_type` field into:
  - run record JSON files under projects/<project>/state/runs/*.json
  - artifact provenance in projects/<project>/state/registry.json
    (as provenance.executor_type)

This is a research-layer tool.  It does NOT modify core/ architecture.
It is needed because legacy projects (B0 dry-run, B0-R2 mock) were
created before executor_type was introduced, and the Execution
Authenticity Gate needs this field to distinguish real external-agent
runs from synthetic stubs.

Executor types:
  - dry_run      : DefaultNodeExecutor deterministic stub (流程演练)
  - synthetic    : mock executor generated artifacts (模拟数据)
  - external_agent: real external agent (Doubao/GPT/Claude/human)

Usage:
    py -3.12 mark_executor_type.py --project p151-2024a --type dry_run
    py -3.12 mark_executor_type.py --project p151-2024a-r2 --type synthetic
    py -3.12 mark_executor_type.py --project p151-2024a --type dry_run --dry-run
    py -3.12 mark_executor_type.py --project p151-2024a --list
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_TYPES = {"dry_run", "synthetic", "external_agent"}

REPO_ROOT = Path(__file__).resolve().parents[3]  # research/P15/measurement_recovery -> repo root


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_run_records(project_dir: Path, executor_type: str, dry_run: bool = False) -> list[str]:
    """Annotate executor_type on all run records in a project."""
    runs_dir = project_dir / "state" / "runs"
    changed: list[str] = []

    if not runs_dir.exists():
        print(f"  [WARN] runs directory not found: {runs_dir}", file=sys.stderr)
        return changed

    for run_file in sorted(runs_dir.glob("*.json")):
        rec = _load_json(run_file)
        old_type = rec.get("executor_type")
        if old_type == executor_type:
            print(f"  [SKIP] {run_file.name}: already executor_type={executor_type}")
            continue

        rec["executor_type"] = executor_type
        # Also annotate provenance-style fields for consistency
        if "provenance" not in rec or not isinstance(rec.get("provenance"), dict):
            rec["provenance"] = {}
        rec["provenance"]["executor_type"] = executor_type
        rec["provenance"]["marked_at"] = _now_iso()
        rec["provenance"]["marked_by"] = "mark_executor_type.py"

        if dry_run:
            print(f"  [DRY] {run_file.name}: {old_type} -> {executor_type}")
        else:
            _save_json(run_file, rec)
            print(f"  [OK]   {run_file.name}: {old_type} -> {executor_type}")
        changed.append(run_file.name)

    return changed


def mark_registry_artifacts(project_dir: Path, executor_type: str, dry_run: bool = False) -> tuple[int, int]:
    """Annotate provenance.executor_type on all artifacts in registry.json."""
    registry_path = project_dir / "state" / "registry.json"
    if not registry_path.exists():
        print(f"  [WARN] registry.json not found: {registry_path}", file=sys.stderr)
        return 0, 0

    reg = _load_json(registry_path)
    artifacts = reg.get("artifacts", {})
    total = len(artifacts)
    updated = 0

    for aid, art in artifacts.items():
        prov = art.get("provenance")
        if not isinstance(prov, dict):
            prov = {}
            art["provenance"] = prov

        old_type = prov.get("executor_type")
        if old_type == executor_type:
            continue

        prov["executor_type"] = executor_type
        prov["marked_at"] = _now_iso()
        prov["marked_by"] = "mark_executor_type.py"
        updated += 1

    if updated > 0:
        reg["updated_at"] = _now_iso()
        if dry_run:
            print(f"  [DRY] registry.json: would update {updated}/{total} artifacts")
        else:
            _save_json(registry_path, reg)
            print(f"  [OK]   registry.json: updated {updated}/{total} artifacts")
    else:
        print(f"  [SKIP] registry.json: all {total} artifacts already executor_type={executor_type}")

    return updated, total


def list_project_types(project_dir: Path) -> None:
    """List current executor_type annotations for a project."""
    print(f"Project: {project_dir.name}")
    print(f"Path:    {project_dir}")
    print()

    # Run records
    runs_dir = project_dir / "state" / "runs"
    if runs_dir.exists():
        print("Run records:")
        for rf in sorted(runs_dir.glob("*.json")):
            rec = _load_json(rf)
            et = rec.get("executor_type", "(unset)")
            rid = rec.get("run_id", "?")
            print(f"  {rf.name}: run_id={rid}, executor_type={et}")
    else:
        print("Run records: (none)")
    print()

    # Registry
    registry_path = project_dir / "state" / "registry.json"
    if registry_path.exists():
        reg = _load_json(registry_path)
        artifacts = reg.get("artifacts", {})
        type_counts: dict[str, int] = {}
        unset = 0
        for art in artifacts.values():
            prov = art.get("provenance", {})
            et = prov.get("executor_type") if isinstance(prov, dict) else None
            if et:
                type_counts[et] = type_counts.get(et, 0) + 1
            else:
                unset += 1
        print(f"Registry artifacts: {len(artifacts)} total")
        for et, cnt in sorted(type_counts.items()):
            print(f"  executor_type={et}: {cnt}")
        if unset:
            print(f"  (unset): {unset}")
    else:
        print("Registry: (not found)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch-annotate executor_type on run records and artifact provenance",
    )
    parser.add_argument("--project", type=str, required=True,
                        help="Project name (e.g. p151-2024a) or path to project directory")
    parser.add_argument("--type", type=str, choices=sorted(VALID_TYPES),
                        help="Executor type to annotate")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing files")
    parser.add_argument("--list", action="store_true",
                        help="List current executor_type annotations without modifying")
    args = parser.parse_args()

    # Resolve project directory
    project_arg = Path(args.project)
    if project_arg.is_absolute() and project_arg.exists():
        project_dir = project_arg
    else:
        candidate = REPO_ROOT / "projects" / args.project
        if candidate.exists():
            project_dir = candidate
        else:
            # Try as relative path
            project_dir = Path(args.project).resolve()
            if not project_dir.exists():
                print(f"ERROR: project not found: {args.project}", file=sys.stderr)
                return 1

    if args.list:
        list_project_types(project_dir)
        return 0

    if not args.type:
        parser.error("--type is required unless --list is specified")

    executor_type = args.type
    print(f"Marking project: {project_dir.name}")
    print(f"Executor type:   {executor_type}")
    print(f"Dry run:         {args.dry_run}")
    print()

    print("[1/2] Run records:")
    run_changed = mark_run_records(project_dir, executor_type, args.dry_run)
    print()

    print("[2/2] Registry artifacts:")
    reg_updated, reg_total = mark_registry_artifacts(project_dir, executor_type, args.dry_run)
    print()

    print("=" * 50)
    print(f"Summary: {len(run_changed)} run records, {reg_updated}/{reg_total} artifacts")
    if args.dry_run:
        print("(dry run — no files were modified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
