#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""register_external_artifact.py — External-Agent artifact submission entry point.

This is the ONLY sanctioned way for an external agent (Doubao / GPT /
Claude / human) to register a node artifact into the MathModel harness.
External agents must NOT hand-edit registry.json or run records directly.

Pipeline:
  1. Read manifest JSON
  2. Validate manifest (schema + required fields + latency > 0 + payload non-empty)
  3. Verify input_sha256 matches the project's frozen problem input hash
  4. Write artifact into project registry.json (correct artifact format)
  5. Create/update run record with executor_type=external_agent
  6. Update evidence_graph and decision_log (if applicable)
  7. Output registration result

Exit codes:
  0 = success
  1 = manifest validation failure
  2 = input hash mismatch (wrong problem)
  3 = other error (IO, project not found, etc.)

Usage:
    py -3.12 register_external_artifact.py \
        --project p151-2024a-r3 \
        --manifest path/to/manifest.json \
        --input-sha256 9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e

    py -3.12 register_external_artifact.py --project p151-2024a-r3 --manifest manifest.json
    (input-sha256 auto-detected from project inputs if omitted)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Import manifest module from same directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from external_artifact_manifest import (  # noqa: E402
    ExternalArtifactManifest,
    ValidationResult,
    validate,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

# Exit codes
EXIT_SUCCESS = 0
EXIT_VALIDATION_FAIL = 1
EXIT_HASH_MISMATCH = 2
EXIT_OTHER_ERROR = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_directory(directory: Path, pattern: str = "*") -> str:
    """Hash all files in a directory (sorted by relative path)."""
    if not directory.exists():
        return _sha256_bytes(b"<missing-dir>")
    files = sorted(f for f in directory.rglob(pattern) if f.is_file())
    if not files:
        return _sha256_bytes(b"")
    h = hashlib.sha256()
    for f in files:
        h.update(str(f.relative_to(directory)).encode("utf-8"))
        h.update(_sha256_bytes(f.read_bytes()).encode("utf-8"))
    return h.hexdigest()


def _detect_frozen_input_hash(project_dir: Path) -> Optional[str]:
    """Detect the frozen problem input hash from a project directory.

    Looks for:
      1. inputs/*.txt (first .txt file)
      2. inputs/ directory hash
      3. existing run record input_hash
    """
    inputs_dir = project_dir / "inputs"

    # Try individual .txt files first (most common)
    if inputs_dir.exists():
        txt_files = sorted(inputs_dir.glob("*.txt"))
        if txt_files:
            return _sha256_bytes(txt_files[0].read_bytes())

        # Fall back to directory hash
        dir_hash = _hash_directory(inputs_dir)
        if dir_hash and dir_hash != _sha256_bytes(b""):
            return dir_hash

    # Fall back to existing run record
    runs_dir = project_dir / "state" / "runs"
    if runs_dir.exists():
        run_files = sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        if run_files:
            rec = _load_json(run_files[-1])
            ih = rec.get("input_hash")
            if ih:
                return ih

    return None


# ---------------------------------------------------------------------------
# Registry artifact construction
# ---------------------------------------------------------------------------

# Map node_id to artifact type prefix
NODE_TO_ARTIFACT_TYPE = {
    "problem_analysis": "problem",
    "question_decomposition": "question",
    "literature_search": "decision",
    "model_selection": "model",
    "model_construction": "model",
    "assumption_validation": "assumption",
    "experiment_design": "decision",
    "experiment_execution": "experiment",
    "result_analysis": "result",
    "evidence_build": "claim",
    "paper_sections": "paper_section",
    "figure_generation": "figure",
}


def _next_artifact_id(registry: dict[str, Any], artifact_type: str) -> str:
    """Generate the next artifact ID for a given type (e.g. M002)."""
    type_prefixes = {
        "problem": "P", "question": "Q", "model": "M", "assumption": "A",
        "decision": "D", "experiment": "E", "result": "R", "figure": "F",
        "claim": "C", "paper_section": "S",
    }
    prefix = type_prefixes.get(artifact_type, "X")
    existing = registry.get("artifacts", {})
    max_num = 0
    for aid in existing:
        if aid.startswith(prefix):
            try:
                num = int(aid[1:])
                max_num = max(max_num, num)
            except ValueError:
                pass
    return f"{prefix}{max_num + 1:03d}"


def _build_registry_artifact(
    manifest: ExternalArtifactManifest,
    artifact_id: str,
    artifact_type: str,
) -> dict[str, Any]:
    """Build a registry-compatible artifact dict from a manifest."""
    now = _now_iso()
    payload = manifest.payload

    # Extract title from payload if available
    title = payload.get("title", f"{manifest.node_id} output")
    question = payload.get("question", "Q001")

    return {
        "schema_version": "3.1",
        "artifact_id": artifact_id,
        "type": artifact_type,
        "version": 1,
        "status": "active",
        "title": title,
        "question": question,
        "created_by": manifest.node_id,
        "created_at": now,
        "updated_at": now,
        "payload": payload,
        "parent": [],
        "depends_on": payload.get("depends_on", []),
        "relations": [],
        "provenance": {
            "executor_type": "external_agent",
            "agent_identity": manifest.agent_identity,
            "model_version": manifest.model_version,
            "input_sha256": manifest.input_sha256,
            "node_id": manifest.node_id,
            "dag_position": manifest.dag_position,
            "prompt_or_skill_version": manifest.prompt_or_skill_version,
            "started_at": manifest.started_at,
            "finished_at": manifest.finished_at,
            "latency_seconds": manifest.latency_seconds,
            "submitted_at": manifest.submitted_at,
            "registered_at": now,
            "registered_by": "register_external_artifact.py",
        },
        "validation": {
            "manifest_validated": True,
            "input_hash_verified": True,
        },
        "lifecycle_history": [
            {
                "from": None,
                "to": "active",
                "at": now,
                "by": manifest.node_id,
                "reason": "created by external agent",
            },
            {
                "from": "draft",
                "to": "active",
                "at": now,
                "by": "register_external_artifact.py",
                "reason": "registered with payload via external artifact manifest",
            },
        ],
        "invalidation": {},
        "tags": payload.get("tags", []),
        "data": payload.get("data", {}),
    }


# ---------------------------------------------------------------------------
# Run record construction
# ---------------------------------------------------------------------------

def _build_or_update_run_record(
    project_dir: Path,
    manifest: ExternalArtifactManifest,
    artifact_id: str,
) -> Path:
    """Create or update a run record for this external-agent submission."""
    runs_dir = project_dir / "state" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    run_id = f"ext_{manifest.node_id}_{uuid.uuid4().hex[:12]}"
    run_file = runs_dir / f"{run_id}.json"

    now = _now_iso()

    # Compute artifact hash from payload
    artifact_hash = _sha256_bytes(
        json.dumps(manifest.payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    )

    record = {
        "schema_version": 1,
        "run_id": run_id,
        "parent_run_id": None,
        "project": str(project_dir),
        "questions": ["Q001"],
        "status": "completed",
        "workflow_version": manifest.prompt_or_skill_version,
        "skill_version": manifest.prompt_or_skill_version,
        "tool_version": "external-artifact-registry-v1",
        "model_provider": manifest.agent_identity,
        "model_version": manifest.model_version,
        "prompt_hash": _sha256_bytes(manifest.prompt_or_skill_version.encode("utf-8")),
        "input_hash": manifest.input_sha256,
        "artifact_hash": artifact_hash,
        "evidence_hash": _sha256_bytes(b"external-agent-evidence"),
        "decision_log_hash": _sha256_bytes(b"external-agent-decision-log"),
        "latency": {
            "started_at": manifest.started_at,
            "finished_at": manifest.finished_at,
            "seconds": manifest.latency_seconds,
        },
        "started_at": manifest.started_at,
        "token_cost": None,
        "execution_mode": "external_agent",
        "executor_type": "external_agent",
        "agent_identity": manifest.agent_identity,
        "node_id": manifest.node_id,
        "dag_position": manifest.dag_position,
        "registered_artifact": artifact_id,
        "engine": {
            "completed_nodes": 1,
            "retries": 0,
            "failures": [],
        },
        "decision": None,
        "provenance": {
            "executor_type": "external_agent",
            "agent_identity": manifest.agent_identity,
            "model_version": manifest.model_version,
            "submitted_at": manifest.submitted_at,
            "registered_at": now,
        },
    }

    if manifest.reproducibility:
        record["reproducibility"] = {
            "seed": manifest.reproducibility.seed,
            "temperature": manifest.reproducibility.temperature,
            "parameters": manifest.reproducibility.parameters,
        }

    _save_json(run_file, record)
    return run_file


# ---------------------------------------------------------------------------
# Evidence graph & decision log updates
# ---------------------------------------------------------------------------

def _update_evidence_graph(
    project_dir: Path,
    artifact_id: str,
    manifest: ExternalArtifactManifest,
) -> None:
    """Add evidence relations for the newly registered artifact."""
    graph_path = project_dir / "state" / "evidence_graph.json"
    now = _now_iso()

    if graph_path.exists():
        graph = _load_json(graph_path)
    else:
        graph = {
            "graph_schema_version": 3,
            "graph_version": 1,
            "project": project_dir.name,
            "updated_at": now,
            "relations": [],
        }

    relations = graph.setdefault("relations", [])
    depends_on = manifest.payload.get("depends_on", [])

    # Add "based_on" relations for dependencies
    for dep_id in depends_on:
        relations.append({
            "from": artifact_id,
            "relation": "based_on",
            "to": dep_id,
            "at": now,
        })

    graph["updated_at"] = now
    _save_json(graph_path, graph)


def _update_decision_log(
    project_dir: Path,
    artifact_id: str,
    manifest: ExternalArtifactManifest,
) -> None:
    """Add a decision log entry for model/decision-type artifacts."""
    dlog_path = project_dir / "state" / "decision_log.json"
    now = _now_iso()

    if dlog_path.exists():
        dlog = _load_json(dlog_path)
    else:
        dlog = {
            "schema_version": 3,
            "updated_at": now,
            "decisions": [],
        }

    # Only add decision entries for decision/model type artifacts
    artifact_type = NODE_TO_ARTIFACT_TYPE.get(manifest.node_id, "")
    if artifact_type not in ("decision", "model"):
        return

    decisions = dlog.setdefault("decisions", [])
    decision_entry = {
        "decision_id": artifact_id,
        "question": f"{manifest.node_id} output",
        "chosen": manifest.payload.get("model_type", manifest.payload.get("decision", artifact_id)),
        "alternatives": manifest.payload.get("alternatives", []),
        "criteria": manifest.payload.get("criteria", []),
        "evidence_ids": manifest.payload.get("depends_on", []),
        "reasoning": manifest.payload.get("reasoning", f"External agent {manifest.agent_identity} produced via {manifest.node_id}"),
        "confidence": manifest.payload.get("confidence", 0.8),
        "reversible": True,
        "created_by": manifest.node_id,
        "created_at": now,
        "status": "active",
        "executor_type": "external_agent",
        "agent_identity": manifest.agent_identity,
    }
    decisions.append(decision_entry)
    dlog["updated_at"] = now
    _save_json(dlog_path, dlog)


# ---------------------------------------------------------------------------
# Main registration
# ---------------------------------------------------------------------------

def register_artifact(
    project_dir: Path,
    manifest: ExternalArtifactManifest,
    frozen_input_hash: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Register an external-agent artifact into the project.

    Returns a result dict with status and details.
    """
    result: dict[str, Any] = {
        "status": "pending",
        "project": project_dir.name,
        "node_id": manifest.node_id,
        "artifact_id": None,
        "run_record": None,
        "errors": [],
        "warnings": [],
    }

    # Step 1: Validate manifest
    validation = validate(manifest)
    if not validation.ok:
        result["status"] = "validation_failed"
        result["errors"] = validation.errors
        return result
    result["warnings"].extend(validation.warnings)

    # Step 2: Verify input hash
    if not manifest.check_input_hash(frozen_input_hash):
        result["status"] = "hash_mismatch"
        result["errors"].append(
            f"input_sha256 mismatch: manifest={manifest.input_sha256[:16]}..., "
            f"frozen={frozen_input_hash[:16]}... — wrong problem, rejecting"
        )
        return result

    # Step 3: Determine artifact type
    artifact_type = NODE_TO_ARTIFACT_TYPE.get(manifest.node_id)
    if not artifact_type:
        # Fall back: infer from payload
        if "model_type" in manifest.payload:
            artifact_type = "model"
        elif "values" in manifest.payload:
            artifact_type = "result"
        elif "method" in manifest.payload:
            artifact_type = "experiment"
        elif "content" in manifest.payload:
            artifact_type = "paper_section"
        else:
            artifact_type = "decision"
        result["warnings"].append(
            f"node_id '{manifest.node_id}' not in standard mapping, inferred type={artifact_type}"
        )

    # Step 4: Load registry and generate artifact ID
    registry_path = project_dir / "state" / "registry.json"
    if registry_path.exists():
        registry = _load_json(registry_path)
    else:
        registry = {
            "registry_version": 3,
            "project": project_dir.name,
            "updated_at": _now_iso(),
            "counters": {},
            "artifacts": {},
            "history": {},
        }

    artifact_id = _next_artifact_id(registry, artifact_type)

    # Step 5: Build artifact
    artifact = _build_registry_artifact(manifest, artifact_id, artifact_type)

    if dry_run:
        result["status"] = "dry_run"
        result["artifact_id"] = artifact_id
        result["artifact_type"] = artifact_type
        result["message"] = "Dry run — no files were modified"
        return result

    # Step 6: Write to registry
    registry.setdefault("artifacts", {})[artifact_id] = artifact
    registry["updated_at"] = _now_iso()

    # Update counters
    counters = registry.setdefault("counters", {})
    counters[artifact_type] = counters.get(artifact_type, 0) + 1

    _save_json(registry_path, registry)

    # Step 7: Create run record
    run_file = _build_or_update_run_record(project_dir, manifest, artifact_id)
    result["run_record"] = str(run_file)

    # Step 8: Update evidence graph
    _update_evidence_graph(project_dir, artifact_id, manifest)

    # Step 9: Update decision log
    _update_decision_log(project_dir, artifact_id, manifest)

    result["status"] = "success"
    result["artifact_id"] = artifact_id
    result["artifact_type"] = artifact_type
    result["registry_path"] = str(registry_path)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register an external-agent artifact into the MathModel harness",
    )
    parser.add_argument("--project", type=str, required=True,
                        help="Project name (e.g. p151-2024a-r3) or path to project directory")
    parser.add_argument("--manifest", type=str, required=True,
                        help="Path to the ExternalArtifactManifest JSON file")
    parser.add_argument("--input-sha256", type=str, default=None,
                        help="Frozen problem input SHA-256 (auto-detected if omitted)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and show what would be registered without writing")
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
            project_dir = Path(args.project).resolve()
            if not project_dir.exists():
                print(f"ERROR: project not found: {args.project}", file=sys.stderr)
                return EXIT_OTHER_ERROR

    # Load manifest
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: manifest file not found: {args.manifest}", file=sys.stderr)
        return EXIT_OTHER_ERROR

    try:
        manifest = ExternalArtifactManifest.from_json(manifest_path)
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"ERROR: failed to parse manifest: {e}", file=sys.stderr)
        return EXIT_VALIDATION_FAIL

    # Detect or use provided input hash
    if args.input_sha256:
        frozen_hash = args.input_sha256.strip().lower()
    else:
        frozen_hash = _detect_frozen_input_hash(project_dir)
        if not frozen_hash:
            print("ERROR: cannot detect frozen input hash; provide --input-sha256", file=sys.stderr)
            return EXIT_OTHER_ERROR
        print(f"[INFO] Auto-detected frozen input hash: {frozen_hash[:16]}...")

    # Register
    result = register_artifact(project_dir, manifest, frozen_hash, dry_run=args.dry_run)

    # Output
    print()
    print("=" * 60)
    print("EXTERNAL ARTIFACT REGISTRATION RESULT")
    print("=" * 60)
    print(f"  Project   : {result['project']}")
    print(f"  Node ID   : {result['node_id']}")
    print(f"  Status    : {result['status']}")

    if result.get("artifact_id"):
        print(f"  Artifact  : {result['artifact_id']} ({result.get('artifact_type', '?')})")
    if result.get("run_record"):
        print(f"  Run record: {result['run_record']}")
    if result.get("registry_path"):
        print(f"  Registry  : {result['registry_path']}")

    if result["warnings"]:
        print()
        print("  Warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")

    if result["errors"]:
        print()
        print("  Errors:")
        for e in result["errors"]:
            print(f"    - {e}")

    print()

    # Map status to exit code
    if result["status"] == "success" or result["status"] == "dry_run":
        return EXIT_SUCCESS
    elif result["status"] == "validation_failed":
        return EXIT_VALIDATION_FAIL
    elif result["status"] == "hash_mismatch":
        return EXIT_HASH_MISMATCH
    else:
        return EXIT_OTHER_ERROR


if __name__ == "__main__":
    sys.exit(main())
