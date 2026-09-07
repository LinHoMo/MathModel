#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""artifact_persist.py — Artifact Persistence & Provenance Layer（P13-3D 新增）。

解决 P13-3C 的工程事故：artifact 未持久化。
以后任何进入正式实验的 artifact 必须经过：
  Generate → Validate → Persist → Hash → Freeze → Evaluate

用法:
  python artifact_persist.py freeze --artifact <artifact.json> --manifest <manifest.json>
  python artifact_persist.py validate --artifact <artifact.json> --manifest <manifest.json>
  python artifact_persist.py verify --artifact <artifact.json> --manifest <manifest.json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_content_hash(data: dict) -> str:
    """Compute SHA256 of JSON content (deterministic ordering)."""
    content = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def create_manifest(
    artifact: dict,
    artifact_path: Path,
    arm: str,
    question_id: str,
    experiment_id: str,
    generation_config: dict | None = None,
) -> dict:
    """Create a manifest for an artifact."""
    now = datetime.now(timezone.utc).isoformat()
    artifact_hash = compute_content_hash(artifact)

    return {
        "manifest_version": "1.0",
        "experiment_id": experiment_id,
        "created_at": now,
        "frozen_at": None,  # Set by freeze
        "artifact": {
            "path": str(artifact_path.name),
            "hash": artifact_hash,
            "schema_version": "model_artifact_v1",
        },
        "provenance": {
            "arm": arm,
            "question_id": question_id,
            "reconstruction_set": "P13-3D-R0",
            "is_reconstruction": True,
            "original_experiment": "P13-3C",
            "original_artifact_status": "not_persisted",
        },
        "generation_config": generation_config or {},
        "validation": {
            "schema_valid": None,
            "validated_at": None,
            "validator_version": None,
        },
        "freezing": {
            "status": "pending",  # pending → frozen → evaluated
            "frozen_by": None,
            "freeze_hash": None,
        },
    }


def freeze_artifact(artifact_path: Path, manifest_path: Path) -> dict:
    """Freeze an artifact with its manifest.

    Pipeline: Generate → Validate → Persist → Hash → **FREEZE** → Evaluate
    Once frozen, neither artifact nor manifest can be modified.
    """
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Check preconditions
    if manifest["validation"]["schema_valid"] is not True:
        return {"error": "Cannot freeze: schema validation not passed"}

    if manifest["freezing"]["status"] == "frozen":
        return {"error": "Already frozen", "frozen_at": manifest["frozen_at"]}

    # Freeze
    now = datetime.now(timezone.utc).isoformat()
    artifact_hash = compute_content_hash(artifact)

    manifest["frozen_at"] = now
    manifest["freezing"]["status"] = "frozen"
    manifest["freezing"]["frozen_by"] = "artifact_persist.py"
    manifest["freezing"]["freeze_hash"] = artifact_hash

    # Verify hash matches
    if manifest["artifact"]["hash"] != artifact_hash:
        return {"error": "Artifact modified since manifest creation",
                "expected": manifest["artifact"]["hash"],
                "actual": artifact_hash}

    # Write frozen manifest
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "status": "frozen",
        "frozen_at": now,
        "artifact_hash": artifact_hash,
        "manifest_path": str(manifest_path),
    }


def verify_integrity(artifact_path: Path, manifest_path: Path) -> dict:
    """Verify artifact integrity against frozen manifest."""
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest["freezing"]["status"] != "frozen":
        return {"error": "Artifact not frozen"}

    current_hash = compute_content_hash(artifact)
    frozen_hash = manifest["freezing"]["freeze_hash"]

    if current_hash != frozen_hash:
        return {
            "tampered": True,
            "expected": frozen_hash,
            "actual": current_hash,
            "message": "Artifact has been modified after freezing!",
        }

    return {
        "tampered": False,
        "hash": current_hash,
        "frozen_at": manifest["frozen_at"],
        "message": "Artifact integrity verified.",
    }


def main():
    parser = argparse.ArgumentParser(description="Artifact Persistence & Provenance")
    sub = parser.add_subparsers(dest="command")

    freeze_p = sub.add_parser("freeze", help="Freeze artifact + manifest")
    freeze_p.add_argument("--artifact", required=True)
    freeze_p.add_argument("--manifest", required=True)

    verify_p = sub.add_parser("verify", help="Verify artifact integrity")
    verify_p.add_argument("--artifact", required=True)
    verify_p.add_argument("--manifest", required=True)

    args = parser.parse_args()

    if args.command == "freeze":
        result = freeze_artifact(Path(args.artifact), Path(args.manifest))
    elif args.command == "verify":
        result = verify_integrity(Path(args.artifact), Path(args.manifest))
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
