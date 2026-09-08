#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""external_artifact_manifest.py — External-Agent Artifact Manifest contract.

Defines the data contract that every external-agent-submitted node artifact
must carry.  The harness side performs schema validation + non-empty /
structural / semantic gate + hash binding + provenance persistence.

This module is LLM-free: it never imports openai / anthropic / any LLM
client.  It only defines, validates, and (de)serialises the manifest.

Usage:
    from external_artifact_manifest import ExternalArtifactManifest, validate

    m = ExternalArtifactManifest.from_json("manifest.json")
    result = validate(m)
    if not result.ok:
        for err in result.errors:
            print(err)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_EXECUTOR_TYPES = {"external_agent", "dry_run", "synthetic"}
VALID_AGENT_IDENTITIES = {"doubao", "gpt", "claude", "human", "other"}
MANIFEST_SCHEMA_VERSION = "1.0"

# Minimum latency (seconds) below which we treat the run as template
# initialisation rather than real external-agent execution.
MIN_LATENCY_SECONDS = 1.0


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of manifest validation."""
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


# ---------------------------------------------------------------------------
# Reproducibility (optional)
# ---------------------------------------------------------------------------

@dataclass
class Reproducibility:
    """Optional reproducibility metadata for the external-agent run."""
    seed: Optional[int] = None
    temperature: Optional[float] = None
    parameters: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Manifest dataclass
# ---------------------------------------------------------------------------

@dataclass
class ExternalArtifactManifest:
    """External-Agent Artifact Manifest.

    Every artifact submitted by an external agent (Doubao / GPT / Claude /
    human) must carry this manifest so the harness can verify authenticity,
    bind to the frozen problem input, and persist provenance.
    """

    # --- Required fields ---
    executor_type: str                       # must be "external_agent"
    agent_identity: str                      # doubao / gpt / claude / human / other
    model_version: str                       # model version; "N/A" for human
    input_sha256: str                        # must match frozen problem hash
    node_id: str                             # DAG node ID, e.g. "model_construction"
    dag_position: int                        # DAG position (0-indexed)
    prompt_or_skill_version: str             # prompt or SKILL version
    artifact_schema_version: str             # artifact schema version
    started_at: str                          # ISO 8601
    finished_at: str                         # ISO 8601
    latency_seconds: float                   # real > 0
    submitted_at: str                        # ISO 8601
    payload: dict[str, Any]                  # non-empty, schema-valid

    # --- Optional fields ---
    reproducibility: Optional[Reproducibility] = None

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.reproducibility is None:
            d.pop("reproducibility", None)
        return d

    def to_json(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExternalArtifactManifest":
        repro_data = data.get("reproducibility")
        repro = Reproducibility(**repro_data) if repro_data else None
        # Filter to known fields to be forward-compatible
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        filtered["reproducibility"] = repro
        return cls(**filtered)

    @classmethod
    def from_json(cls, path: str | Path) -> "ExternalArtifactManifest":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    # ------------------------------------------------------------------
    # Hash binding
    # ------------------------------------------------------------------

    def check_input_hash(self, frozen_input_sha256: str) -> bool:
        """Verify that the manifest's input_sha256 matches the frozen
        problem input hash.  A mismatch means the agent worked on the
        wrong problem and the artifact must be rejected."""
        if not self.input_sha256 or not frozen_input_sha256:
            return False
        return self.input_sha256.strip().lower() == frozen_input_sha256.strip().lower()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _parse_iso(ts: str) -> Optional[datetime]:
    if not ts or not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def validate(manifest: ExternalArtifactManifest) -> ValidationResult:
    """Validate an ExternalArtifactManifest.

    Checks:
      1. All required fields non-empty
      2. executor_type == "external_agent"
      3. agent_identity in known set (or "other")
      4. model_version non-empty ("N/A" allowed for human)
      5. input_sha256 is a 64-char hex string
      6. node_id non-empty
      7. dag_position >= 0
      8. started_at / finished_at / submitted_at parseable ISO 8601
      9. latency_seconds > MIN_LATENCY_SECONDS
      10. payload non-empty dict
      11. finished_at >= started_at
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. executor_type
    if manifest.executor_type != "external_agent":
        errors.append(
            f"executor_type must be 'external_agent', got '{manifest.executor_type}'"
        )

    # 2. agent_identity
    if not manifest.agent_identity or not isinstance(manifest.agent_identity, str):
        errors.append("agent_identity is required and must be a non-empty string")
    elif manifest.agent_identity not in VALID_AGENT_IDENTITIES:
        warnings.append(
            f"agent_identity '{manifest.agent_identity}' not in standard set "
            f"{sorted(VALID_AGENT_IDENTITIES)}; treating as 'other'"
        )

    # 3. model_version
    if not manifest.model_version or not isinstance(manifest.model_version, str):
        errors.append("model_version is required (use 'N/A' for human)")
    elif manifest.agent_identity == "human" and manifest.model_version != "N/A":
        warnings.append("human agent should use model_version='N/A'")

    # 4. input_sha256 format
    if not manifest.input_sha256 or not isinstance(manifest.input_sha256, str):
        errors.append("input_sha256 is required")
    elif len(manifest.input_sha256) != 64 or not all(
        c in "0123456789abcdef" for c in manifest.input_sha256.lower()
    ):
        errors.append(
            f"input_sha256 must be 64-char hex, got length={len(manifest.input_sha256)}"
        )

    # 5. node_id
    if not manifest.node_id or not isinstance(manifest.node_id, str):
        errors.append("node_id is required")

    # 6. dag_position
    if not isinstance(manifest.dag_position, int) or manifest.dag_position < 0:
        errors.append(f"dag_position must be int >= 0, got {manifest.dag_position}")

    # 7. prompt_or_skill_version
    if not manifest.prompt_or_skill_version:
        errors.append("prompt_or_skill_version is required")

    # 8. artifact_schema_version
    if not manifest.artifact_schema_version:
        errors.append("artifact_schema_version is required")

    # 9. Timestamps
    started = _parse_iso(manifest.started_at)
    finished = _parse_iso(manifest.finished_at)
    submitted = _parse_iso(manifest.submitted_at)
    if started is None:
        errors.append(f"started_at not parseable ISO 8601: {manifest.started_at}")
    if finished is None:
        errors.append(f"finished_at not parseable ISO 8601: {manifest.finished_at}")
    if submitted is None:
        errors.append(f"submitted_at not parseable ISO 8601: {manifest.submitted_at}")

    # 10. latency
    if not isinstance(manifest.latency_seconds, (int, float)):
        errors.append("latency_seconds must be numeric")
    elif manifest.latency_seconds <= 0:
        errors.append(f"latency_seconds must be > 0, got {manifest.latency_seconds}")
    elif manifest.latency_seconds < MIN_LATENCY_SECONDS:
        warnings.append(
            f"latency_seconds={manifest.latency_seconds} < {MIN_LATENCY_SECONDS}s "
            f"— may indicate template initialisation rather than real execution"
        )

    # 11. finished >= started
    if started and finished and finished < started:
        errors.append("finished_at is earlier than started_at")

    # 12. payload non-empty
    if not isinstance(manifest.payload, dict):
        errors.append(f"payload must be a dict, got {type(manifest.payload).__name__}")
    elif len(manifest.payload) == 0:
        errors.append("payload must be non-empty")

    return ValidationResult(ok=len(errors) == 0, errors=errors, warnings=warnings)


# ---------------------------------------------------------------------------
# Convenience: compute file hash
# ---------------------------------------------------------------------------

def sha256_file(path: str | Path) -> str:
    """Compute SHA-256 of a file's bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Minimal valid manifest
    m = ExternalArtifactManifest(
        executor_type="external_agent",
        agent_identity="doubao",
        model_version="doubao-1.5-pro",
        input_sha256="9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e",
        node_id="model_construction",
        dag_position=4,
        prompt_or_skill_version="v3.1.0",
        artifact_schema_version="1.0",
        started_at="2026-09-08T10:00:00Z",
        finished_at="2026-09-08T10:05:00Z",
        latency_seconds=300.0,
        submitted_at="2026-09-08T10:05:01Z",
        payload={"model_type": "TOPSIS", "objective": "rank alternatives"},
    )
    r = validate(m)
    print(f"Self-test validate: ok={r.ok}, errors={r.errors}, warnings={r.warnings}")
    print(f"check_input_hash (match): {m.check_input_hash(m.input_sha256)}")
    print(f"check_input_hash (mismatch): {m.check_input_hash('deadbeef' * 8)}")

    # Round-trip
    tmp = Path("_self_test_manifest.json")
    m.to_json(tmp)
    m2 = ExternalArtifactManifest.from_json(tmp)
    print(f"Round-trip equal: {m.to_dict() == m2.to_dict()}")
    tmp.unlink()

    sys.exit(0 if r.ok else 1)
