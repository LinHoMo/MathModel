#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""execution_gate.py — Research-layer Execution Authenticity & Artifact Integrity Gate.

Implements the deterministic checks defined in:
  - research/P15/measurement_recovery/EXECUTION_AUTHENTICITY_PROTOCOL.md
  - research/P15/measurement_recovery/ARTIFACT_INTEGRITY_PROTOCOL.md

Layer coverage:
  - Execution Authenticity Gate: all 13 checks (deterministic)
  - Artifact Integrity Gate: Layer 1 (non-empty) + Layer 2 (structurally valid)
  - Layer 3 (semantic) is NOT implemented here (requires LLM judge)

Usage:
  py -3.12 execution_gate.py --project projects/p151-2024a
  py -3.12 execution_gate.py --run-manifest projects/p151-2024a/state/runs/5c98cd9911bc.json
  py -3.12 execution_gate.py --project projects/p151-2024a --json report.json
  py -3.12 execution_gate.py --project projects/p151-2024a --artifact-only

This script is READ-ONLY: it never modifies any file under core/ or projects/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SHA256_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

VALID_TYPES = {
    "problem", "question", "model", "assumption", "decision",
    "experiment", "result", "figure", "claim", "paper_section",
}

VALID_STATUSES = {"active", "draft", "superseded", "invalidated", "deprecated"}

# Placeholder patterns that do NOT count as "non-empty content"
PLACEHOLDER_SECTION_TITLES = {
    "问题重述与分析", "模型建立", "结果与分析", "灵敏度与稳健性",
    "结论", "问题分析", "模型假设", "符号说明", "模型求解",
    "模型检验", "参考文献", "附录",
}

PLACEHOLDER_TITLES = {
    "赛题", "Q001", "Q001 实验", "Q001 结果", "Q001 结论",
    "Q001 结果图", "TOPSIS 逼近理想解排序",
}

PLACEHOLDER_TOKENS = {"todo", "tbd", "待填写", "placeholder", "n/a", "none"}

METHOD_CARD_RE = re.compile(r"^mc-[a-z][a-z0-9-]*$")
ARTIFACT_ID_RE = re.compile(r"^[A-Z]\d{3}$")

# Minimum latency threshold (seconds): below this is almost certainly
# pure in-memory template initialization, not real execution.
MIN_LATENCY_SECONDS = 1.0

# Minimum paper section content length (chars)
MIN_SECTION_CONTENT_CHARS = 200

# Minimum problem text length (chars)
MIN_PROBLEM_TEXT_CHARS = 50

# Minimum statement length (chars) for assumption/claim
MIN_STATEMENT_CHARS = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check(cid: str, name: str, passed: bool, actual: Any = None,
           expected: Any = None, message: str = "") -> dict:
    """Build a uniform check result dict."""
    return {
        "id": cid,
        "name": name,
        "pass": bool(passed),
        "expected": expected,
        "actual": actual,
        "message": message,
    }


def _skip_check(cid: str, name: str, reason: str = "") -> dict:
    """Build a SKIPPED check result (used for synthetic/dry_run projects)."""
    return {
        "id": cid,
        "name": name,
        "pass": False,
        "skipped": True,
        "expected": "N/A (synthetic)",
        "actual": "N/A (synthetic)",
        "message": reason or "SKIPPED: executor_type is synthetic/dry_run — not a capability result",
    }


def _detect_executor_type(run_record: Optional[dict], registry: Optional[dict] = None) -> str:
    """Detect executor_type from run record and artifact provenance.

    Returns one of: 'external_agent', 'dry_run', 'synthetic', 'unknown'.
    Priority: run_record.executor_type > run_record.provenance.executor_type
    > registry artifact provenance majority > 'unknown'.
    """
    # 1. Run record top-level field
    if run_record:
        et = run_record.get("executor_type")
        if et in ("external_agent", "dry_run", "synthetic"):
            return et
        # 2. Run record provenance
        prov = run_record.get("provenance")
        if isinstance(prov, dict):
            et = prov.get("executor_type")
            if et in ("external_agent", "dry_run", "synthetic"):
                return et
        # 3. execution_mode / mock_execution hints (legacy)
        if run_record.get("mock_execution") is True or run_record.get("execution_mode") == "mock":
            return "synthetic"
        if run_record.get("model_provider") is None and run_record.get("execution_mode") != "external_agent":
            return "dry_run"

    # 4. Registry artifact provenance majority
    if registry:
        artifacts = registry.get("artifacts", {})
        type_counts: dict[str, int] = {}
        for art in artifacts.values():
            prov = art.get("provenance", {})
            if isinstance(prov, dict):
                et = prov.get("executor_type")
                if et in ("external_agent", "dry_run", "synthetic"):
                    type_counts[et] = type_counts.get(et, 0) + 1
        if type_counts:
            return max(type_counts, key=type_counts.get)

    return "unknown"


def _parse_iso(ts: str) -> Optional[datetime]:
    """Parse ISO 8601 timestamp; return None on failure."""
    if not ts or not isinstance(ts, str):
        return None
    try:
        # Handle both 'Z' suffix and '+00:00'
        s = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _is_placeholder_string(s: str) -> bool:
    """Check if a string is a known placeholder."""
    if not isinstance(s, str):
        return False
    stripped = s.strip()
    if not stripped:
        return True
    if stripped.lower() in PLACEHOLDER_TOKENS:
        return True
    if stripped in PLACEHOLDER_SECTION_TITLES:
        return True
    if stripped in PLACEHOLDER_TITLES:
        return True
    if METHOD_CARD_RE.match(stripped):
        return True
    if re.match(r"^Q\d+\s+结论$", stripped):
        return True
    return False


def _is_placeholder_payload(payload: Any) -> bool:
    """Check if payload consists entirely of placeholders."""
    if payload is None or payload == [] or payload == {} or payload == "":
        return True
    if isinstance(payload, list):
        if len(payload) == 0:
            return True
        # All elements are placeholder strings?
        return all(_is_placeholder_string(item) if isinstance(item, str) else False
                   for item in payload)
    if isinstance(payload, str):
        return _is_placeholder_string(payload)
    if isinstance(payload, dict):
        if len(payload) == 0:
            return True
    return False


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except Exception:
        return _sha256_bytes(b"<missing>")


def _hash_directory(directory: Path, pattern: str = "*") -> str:
    """Hash all files in a directory (sorted by relative path)."""
    if not directory.exists():
        return _sha256_bytes(b"<missing-dir>")
    files = sorted(f for f in directory.rglob(pattern) if f.is_file())
    if not files:
        return SHA256_EMPTY
    h = hashlib.sha256()
    for f in files:
        h.update(str(f.relative_to(directory)).encode("utf-8"))
        h.update(_hash_file(f).encode("utf-8"))
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Artifact Integrity Gate — Layer 1: Non-Empty
# ---------------------------------------------------------------------------

def _layer1_problem(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    text = ""
    if isinstance(payload, dict):
        text = payload.get("text", "")
    elif isinstance(payload, str):
        text = payload
    checks.append(_check(
        "L1-P-01", "problem payload has text field",
        isinstance(payload, dict) and "text" in payload,
        expected="dict with 'text' field", actual=type(payload).__name__,
    ))
    checks.append(_check(
        "L1-P-02", "problem text non-trivial",
        isinstance(text, str) and len(text) >= MIN_PROBLEM_TEXT_CHARS,
        expected=f"length >= {MIN_PROBLEM_TEXT_CHARS}",
        actual=len(text) if isinstance(text, str) else 0,
    ))
    return checks


def _layer1_question(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    sub_qs = []
    if isinstance(payload, dict):
        sub_qs = payload.get("sub_questions", [])
    checks.append(_check(
        "L1-Q-01", "question payload has sub_questions",
        isinstance(payload, dict) and isinstance(sub_qs, list) and len(sub_qs) > 0,
        expected="non-empty sub_questions list",
        actual=len(sub_qs) if isinstance(sub_qs, list) else 0,
    ))
    if isinstance(sub_qs, list):
        for i, sq in enumerate(sub_qs):
            checks.append(_check(
                f"L1-Q-02-{i}", f"sub_question[{i}] has id+text",
                isinstance(sq, dict) and sq.get("id") and sq.get("text"),
                expected="dict with id and text",
                actual=type(sq).__name__,
            ))
    return checks


def _layer1_model(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    if not isinstance(payload, dict):
        checks.append(_check(
            "L1-M-00", "model payload is dict",
            False, expected="dict", actual=type(payload).__name__,
        ))
        return checks
    for field, label in [("objective", "目标"), ("constraints", "约束"),
                          ("variables", "变量")]:
        val = payload.get(field)
        if field == "objective":
            ok = isinstance(val, str) and len(val.strip()) > 0 and not _is_placeholder_string(val)
        else:
            ok = isinstance(val, list) and len(val) > 0
        checks.append(_check(
            f"L1-M-{field}", f"model payload has {field} ({label})",
            ok, expected=f"non-empty {field}", actual=type(val).__name__,
        ))
    return checks


def _layer1_assumption(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    statement = ""
    if isinstance(payload, dict):
        statement = payload.get("statement", "")
    elif isinstance(payload, str):
        statement = payload
    checks.append(_check(
        "L1-A-01", "assumption has statement",
        isinstance(statement, str) and len(statement.strip()) >= MIN_STATEMENT_CHARS
        and not _is_placeholder_string(statement),
        expected=f"statement length >= {MIN_STATEMENT_CHARS}",
        actual=len(statement) if isinstance(statement, str) else 0,
    ))
    return checks


def _layer1_decision(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    # Decision payload must be a structured dict, not a list of method card IDs
    if isinstance(payload, list):
        checks.append(_check(
            "L1-D-01", "decision payload is structured (not ID list)",
            False, expected="dict with decision/alternatives",
            actual=f"list of {len(payload)} items (likely method card IDs)",
        ))
        return checks
    if not isinstance(payload, dict):
        checks.append(_check(
            "L1-D-01", "decision payload is dict",
            False, expected="dict", actual=type(payload).__name__,
        ))
        return checks
    checks.append(_check(
        "L1-D-02", "decision has decision content",
        bool(payload.get("decision")) and not _is_placeholder_string(str(payload.get("decision"))),
        expected="non-empty decision string", actual=payload.get("decision"),
    ))
    checks.append(_check(
        "L1-D-03", "decision has alternatives",
        isinstance(payload.get("alternatives"), list) and len(payload["alternatives"]) > 0,
        expected="non-empty alternatives list",
        actual=len(payload.get("alternatives", [])) if isinstance(payload.get("alternatives"), list) else 0,
    ))
    return checks


def _layer1_experiment(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    if not isinstance(payload, dict):
        checks.append(_check(
            "L1-E-00", "experiment payload is dict",
            False, expected="dict", actual=type(payload).__name__,
        ))
        return checks
    for field in ["method", "parameters", "results"]:
        val = payload.get(field)
        if field == "method":
            ok = isinstance(val, str) and len(val.strip()) > 0 and not _is_placeholder_string(val)
        else:
            ok = isinstance(val, (dict, list)) and len(val) > 0
        checks.append(_check(
            f"L1-E-{field}", f"experiment payload has {field}",
            ok, expected=f"non-empty {field}", actual=type(val).__name__,
        ))
    return checks


def _layer1_result(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    values = {}
    if isinstance(payload, dict):
        values = payload.get("values", {})
    has_numeric = isinstance(values, dict) and any(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in values.values()
    )
    checks.append(_check(
        "L1-R-01", "result payload has values dict",
        isinstance(values, dict) and len(values) > 0,
        expected="non-empty values dict", actual=len(values) if isinstance(values, dict) else 0,
    ))
    checks.append(_check(
        "L1-R-02", "result values contain numeric data",
        has_numeric, expected="at least one numeric value",
        actual="numeric present" if has_numeric else "no numeric values",
    ))
    return checks


def _layer1_figure(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    has_data = False
    has_file = False
    if isinstance(payload, dict):
        has_data = bool(payload.get("data")) and len(payload["data"]) > 0
        fp = payload.get("file_path", "")
        has_file = isinstance(fp, str) and len(fp) > 0 and Path(fp).exists()
    checks.append(_check(
        "L1-F-01", "figure has data or valid file_path",
        has_data or has_file,
        expected="non-empty data OR existing file_path",
        actual=f"data={has_data}, file={has_file}",
    ))
    return checks


def _layer1_claim(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    claim_text = ""
    evidence_ref = []
    if isinstance(payload, dict):
        claim_text = payload.get("claim", "")
        evidence_ref = payload.get("evidence_ref", [])
    # Also check data field (B0 stores statement in data, not payload)
    if not claim_text and isinstance(art.get("data"), dict):
        claim_text = art["data"].get("statement", "")
    checks.append(_check(
        "L1-C-01", "claim has statement",
        isinstance(claim_text, str) and len(claim_text.strip()) >= MIN_STATEMENT_CHARS
        and not _is_placeholder_string(claim_text),
        expected=f"claim length >= {MIN_STATEMENT_CHARS}",
        actual=len(claim_text) if isinstance(claim_text, str) else 0,
    ))
    checks.append(_check(
        "L1-C-02", "claim has evidence_ref",
        isinstance(evidence_ref, list) and len(evidence_ref) > 0,
        expected="non-empty evidence_ref list",
        actual=len(evidence_ref) if isinstance(evidence_ref, list) else 0,
    ))
    return checks


def _layer1_paper_section(art: dict) -> list[dict]:
    checks = []
    payload = art.get("payload")
    content = ""
    if isinstance(payload, dict):
        content = payload.get("content", "")
    elif isinstance(payload, list) and len(payload) > 0:
        content = payload[0] if isinstance(payload[0], str) else ""
    elif isinstance(payload, str):
        content = payload
    checks.append(_check(
        "L1-S-01", "paper_section has actual content (not just title)",
        isinstance(content, str) and len(content.strip()) >= MIN_SECTION_CONTENT_CHARS
        and not _is_placeholder_string(content),
        expected=f"content length >= {MIN_SECTION_CONTENT_CHARS}",
        actual=len(content) if isinstance(content, str) else 0,
    ))
    return checks


_LAYER1_TYPE_DISPATCH = {
    "problem": _layer1_problem,
    "question": _layer1_question,
    "model": _layer1_model,
    "assumption": _layer1_assumption,
    "decision": _layer1_decision,
    "experiment": _layer1_experiment,
    "result": _layer1_result,
    "figure": _layer1_figure,
    "claim": _layer1_claim,
    "paper_section": _layer1_paper_section,
}


def layer1_non_empty(artifact: dict) -> dict:
    """Layer 1: Non-Empty check for a single artifact."""
    checks = []
    atype = artifact.get("type", "unknown")
    payload = artifact.get("payload")

    # Generic checks
    checks.append(_check("L1-00", "artifact exists", artifact is not None))
    checks.append(_check("L1-01", "payload field exists", "payload" in artifact))
    checks.append(_check(
        "L1-02", "payload non-empty (not []/{}/None/empty str)",
        payload is not None and payload != [] and payload != {} and payload != "",
        expected="non-None, non-empty", actual=repr(payload)[:80],
    ))
    checks.append(_check(
        "L1-03", "payload is not pure placeholder",
        not _is_placeholder_payload(payload),
        expected="not placeholder",
        actual="placeholder detected" if _is_placeholder_payload(payload) else "ok",
    ))

    # Type-specific checks
    type_fn = _LAYER1_TYPE_DISPATCH.get(atype)
    if type_fn:
        checks.extend(type_fn(artifact))
    else:
        checks.append(_check(
            "L1-04", f"known artifact type '{atype}'",
            False, expected="one of known types", actual=atype,
        ))

    passed = all(c["pass"] for c in checks)
    return {
        "layer": 1,
        "name": "non_empty",
        "verdict": "PASS" if passed else "FAIL",
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Artifact Integrity Gate — Layer 2: Structurally Valid
# ---------------------------------------------------------------------------

def _check_field_types(artifact: dict) -> list[dict]:
    """Check that required fields have correct types (simplified schema check)."""
    checks = []
    atype = artifact.get("type", "")
    payload = artifact.get("payload")

    expected_payload_types = {
        "problem": (dict, str),
        "question": (dict,),
        "model": (dict,),
        "assumption": (dict, str),
        "decision": (dict,),
        "experiment": (dict,),
        "result": (dict,),
        "figure": (dict,),
        "claim": (dict,),
        "paper_section": (dict, str, list),
    }
    expected_types = expected_payload_types.get(atype)
    if expected_types:
        checks.append(_check(
            "L2-07", f"payload type correct for {atype}",
            isinstance(payload, expected_types),
            expected=" or ".join(t.__name__ for t in expected_types),
            actual=type(payload).__name__,
        ))
    return checks


def _check_reference_consistency(artifact: dict, registry: dict) -> list[dict]:
    """Check that all referenced artifact IDs exist in the registry."""
    checks = []
    all_ids = set(registry.get("artifacts", {}).keys())

    # depends_on
    deps = artifact.get("depends_on", [])
    if isinstance(deps, list):
        missing = [d for d in deps if d not in all_ids]
        checks.append(_check(
            "L2-08", "depends_on references exist in registry",
            len(missing) == 0,
            expected="all referenced IDs exist",
            actual=f"missing: {missing}" if missing else "all exist",
        ))

    # relations
    relations = artifact.get("relations", [])
    if isinstance(relations, list):
        missing_rel = []
        for rel in relations:
            if isinstance(rel, dict):
                for key in ("from", "to"):
                    rid = rel.get(key)
                    if rid and rid not in all_ids:
                        missing_rel.append(f"{key}={rid}")
        checks.append(_check(
            "L2-09", "relations references exist in registry",
            len(missing_rel) == 0,
            expected="all from/to IDs exist",
            actual=f"missing: {missing_rel}" if missing_rel else "all exist",
        ))

    return checks


def layer2_structurally_valid(artifact: dict, registry: dict) -> dict:
    """Layer 2: Structurally Valid check for a single artifact."""
    checks = []

    checks.append(_check("L2-00", "artifact is valid dict", isinstance(artifact, dict)))
    checks.append(_check(
        "L2-01", "schema_version is 3.1",
        artifact.get("schema_version") == "3.1",
        expected="3.1", actual=artifact.get("schema_version"),
    ))
    checks.append(_check(
        "L2-02", "artifact_id format (A+3 digits)",
        bool(ARTIFACT_ID_RE.match(artifact.get("artifact_id", ""))),
        expected="e.g. P001, M001", actual=artifact.get("artifact_id"),
    ))
    checks.append(_check(
        "L2-03", "type is valid",
        artifact.get("type") in VALID_TYPES,
        expected=f"one of {sorted(VALID_TYPES)}", actual=artifact.get("type"),
    ))
    checks.append(_check(
        "L2-04", "status is valid",
        artifact.get("status") in VALID_STATUSES,
        expected=f"one of {sorted(VALID_STATUSES)}", actual=artifact.get("status"),
    ))
    checks.append(_check(
        "L2-05", "created_at is parseable ISO8601",
        _parse_iso(artifact.get("created_at", "")) is not None,
        expected="ISO8601", actual=artifact.get("created_at"),
    ))
    checks.append(_check(
        "L2-06", "lifecycle_history non-empty",
        len(artifact.get("lifecycle_history", [])) > 0,
        expected=">= 1 event",
        actual=len(artifact.get("lifecycle_history", [])),
    ))

    # Field type checks
    checks.extend(_check_field_types(artifact))

    # Reference consistency
    checks.extend(_check_reference_consistency(artifact, registry))

    passed = all(c["pass"] for c in checks)
    return {
        "layer": 2,
        "name": "structurally_valid",
        "verdict": "PASS" if passed else "FAIL",
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Artifact Integrity Gate — combined
# ---------------------------------------------------------------------------

def check_artifact(artifact: dict, registry: dict) -> dict:
    """Run Layer 1 + Layer 2 on a single artifact. Layer 3 is not implemented."""
    aid = artifact.get("artifact_id", "unknown")
    atype = artifact.get("type", "unknown")

    l1 = layer1_non_empty(artifact)
    if l1["verdict"] != "PASS":
        return {
            "artifact_id": aid,
            "type": atype,
            "overall": "INVALID",
            "layer1": l1,
            "layer2": None,
            "layer3": None,
        }

    l2 = layer2_structurally_valid(artifact, registry)
    overall = "PASS" if l2["verdict"] == "PASS" else "FAIL"
    return {
        "artifact_id": aid,
        "type": atype,
        "overall": overall,
        "layer1": l1,
        "layer2": l2,
        "layer3": None,
    }


def check_registry(registry_path: Path) -> dict:
    """Check all artifacts in a registry file."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    artifacts = registry.get("artifacts", {})

    results = []
    for aid in sorted(artifacts.keys()):
        art = artifacts[aid]
        results.append(check_artifact(art, registry))

    summary = Counter(r["overall"] for r in results)
    total = len(results)
    pass_count = summary.get("PASS", 0)
    pass_rate = pass_count / total if total > 0 else 0.0

    if any(r["overall"] == "INVALID" for r in results):
        overall = "INVALID"
    elif pass_rate >= 0.8:
        overall = "PASS"
    else:
        overall = "FAIL"

    return {
        "gate": "artifact_integrity",
        "registry_path": str(registry_path),
        "total_artifacts": total,
        "summary": dict(summary),
        "pass_rate": round(pass_rate, 4),
        "overall": overall,
        "artifacts": results,
    }


# ---------------------------------------------------------------------------
# Execution Authenticity Gate (13 checks)
# ---------------------------------------------------------------------------

def _load_run_record(project_dir: Path) -> Optional[dict]:
    """Load the latest run record from a project directory."""
    runs_dir = project_dir / "state" / "runs"
    if not runs_dir.exists():
        return None
    files = sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    return json.loads(files[-1].read_text(encoding="utf-8"))


def execution_authenticity_gate(project_dir: Path, run_record: Optional[dict] = None) -> dict:
    """Run all Execution Authenticity Gate checks with executor_type awareness.

    For synthetic/dry_run executor_type:
      - Report header marks "SYNTHETIC / NOT A CAPABILITY RESULT"
      - All capability-related checks are SKIPPED
      - Overall verdict = INVALID (exit code 2)

    For external_agent executor_type:
      - Additional checks: agent_identity, model_version, input_sha256 binding
      - All 13 EAG checks run normally

    For unknown executor_type (legacy unannotated):
      - Warning emitted, checks run normally but verdict includes UNKNOWN flag
    """
    checks = []

    if run_record is None:
        run_record = _load_run_record(project_dir)

    if run_record is None:
        checks.append(_check(
            "EAG-00", "run record exists",
            False, expected="run record file", actual="not found",
        ))
        return {
            "gate": "execution_authenticity",
            "project": project_dir.name,
            "run_id": None,
            "executor_type": "unknown",
            "overall": "INVALID",
            "summary": {"pass": 0, "fail": 0, "invalid": 1, "skipped": 0, "total": 1},
            "checks": checks,
        }

    run_id = run_record.get("run_id", "unknown")

    # Load registry for executor_type detection and artifact checks
    registry_path = project_dir / "state" / "registry.json"
    registry = None
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

    # Detect executor_type
    executor_type = _detect_executor_type(run_record, registry)

    # --- EAG-EX: executor_type detection (always runs) ---
    if executor_type == "unknown":
        checks.append(_check(
            "EAG-EX", "executor_type annotated",
            False, expected="external_agent/dry_run/synthetic", actual="unknown",
            message="executor_type not annotated — cannot confirm execution authenticity. "
                    "Run mark_executor_type.py to annotate.",
        ))
    elif executor_type in ("dry_run", "synthetic"):
        checks.append(_check(
            "EAG-EX", "executor_type annotated",
            True, expected="annotated", actual=executor_type,
            message=f"EXECUTOR_TYPE: {executor_type.upper()} / NOT A CAPABILITY RESULT",
        ))
    else:
        checks.append(_check(
            "EAG-EX", "executor_type annotated",
            True, expected="external_agent", actual=executor_type,
        ))

    # --- For synthetic/dry_run: skip all capability checks ---
    if executor_type in ("dry_run", "synthetic"):
        capability_check_ids = [
            "EAG-01", "EAG-02", "EAG-03", "EAG-04", "EAG-05", "EAG-06",
            "EAG-07", "EAG-08", "EAG-09", "EAG-10", "EAG-11", "EAG-12", "EAG-13",
        ]
        capability_check_names = {
            "EAG-01": "model_provider non-empty",
            "EAG-02": "model_version non-empty",
            "EAG-03": "skill_version is non-empty hash",
            "EAG-04": "execution timestamps reasonable",
            "EAG-05": f"latency >= {MIN_LATENCY_SECONDS}s (real execution)",
            "EAG-06": "input_hash matches recomputed inputs hash",
            "EAG-07": "workflow_version is valid non-empty hash",
            "EAG-08": "real execution artifacts exist",
            "EAG-09": "registry has artifacts",
            "EAG-10": "artifact payloads non-empty",
            "EAG-11": "decision_log has decisions with evidence",
            "EAG-12": "artifacts have execution provenance",
            "EAG-13": "execution_mode is llm or hybrid",
        }
        for cid in capability_check_ids:
            checks.append(_skip_check(cid, capability_check_names[cid]))

        return {
            "gate": "execution_authenticity",
            "version": "2.0",
            "project": project_dir.name,
            "run_id": run_id,
            "executor_type": executor_type,
            "synthetic": True,
            "capability_result": False,
            "overall": "INVALID",
            "summary": {
                "pass": 1,  # EAG-EX
                "fail": 0,
                "invalid": 0,
                "skipped": 13,
                "total": 14,
            },
            "checks": checks,
            "root_causes": [
                f"EXECUTOR_TYPE: {executor_type.upper()} / NOT A CAPABILITY RESULT — "
                "DefaultNodeExecutor/mock deterministic stub, capability scoring INVALID"
            ],
        }

    # --- For external_agent or unknown: run all 13 EAG checks ---

    # EAG-01: model_provider non-empty
    mp = run_record.get("model_provider")
    checks.append(_check(
        "EAG-01", "model_provider non-empty",
        isinstance(mp, str) and len(mp.strip()) > 0,
        expected="non-empty string (e.g. 'openai')", actual=mp,
        message="null indicates zero-LLM deterministic execution" if mp is None else "",
    ))

    # EAG-02: model_version non-empty
    mv = run_record.get("model_version")
    checks.append(_check(
        "EAG-02", "model_version non-empty",
        isinstance(mv, str) and len(mv.strip()) > 0,
        expected="non-empty string (e.g. 'gpt-4o-2024-05-13')", actual=mv,
    ))

    # EAG-03: skill_version non-empty hash (not SHA256 of empty string)
    sv = run_record.get("skill_version", "")
    checks.append(_check(
        "EAG-03", "skill_version is non-empty hash",
        isinstance(sv, str) and len(sv) == 64 and sv != SHA256_EMPTY
        and all(c in "0123456789abcdef" for c in sv),
        expected="64-char hex, not empty-string SHA256",
        actual=sv[:16] + "..." if len(sv) > 16 else sv,
        message="empty hash = no .yaml files in src/modeling_harness/skills/" if sv == SHA256_EMPTY else "",
    ))

    # EAG-04: execution timestamp reasonable
    started = _parse_iso(run_record.get("started_at", ""))
    latency_info = run_record.get("latency", {})
    lat_started = _parse_iso(latency_info.get("started_at", ""))
    lat_finished = _parse_iso(latency_info.get("finished_at", ""))
    now = datetime.now(timezone.utc)
    ts_ok = (started is not None and lat_started is not None and lat_finished is not None
             and started <= now)
    checks.append(_check(
        "EAG-04", "execution timestamps reasonable",
        ts_ok,
        expected="parseable, not in future",
        actual=f"started={run_record.get('started_at')}",
    ))

    # EAG-05: latency > threshold
    latency_sec = latency_info.get("seconds", 0)
    checks.append(_check(
        "EAG-05", f"latency >= {MIN_LATENCY_SECONDS}s (real execution)",
        isinstance(latency_sec, (int, float)) and latency_sec >= MIN_LATENCY_SECONDS,
        expected=f">= {MIN_LATENCY_SECONDS}s",
        actual=f"{latency_sec}s",
        message="below threshold = template initialization speed" if isinstance(latency_sec, (int, float)) and latency_sec < MIN_LATENCY_SECONDS else "",
    ))

    # EAG-06: input_hash consistent (recompute)
    input_hash = run_record.get("input_hash", "")
    inputs_dir = project_dir / "inputs"
    if inputs_dir.exists() and any(inputs_dir.iterdir()):
        recomputed = _hash_directory(inputs_dir)
    else:
        recomputed = _sha256_bytes(b"<empty-inputs>")
    checks.append(_check(
        "EAG-06", "input_hash matches recomputed inputs hash",
        input_hash == recomputed,
        expected=recomputed[:16] + "...",
        actual=input_hash[:16] + "..." if input_hash else "missing",
    ))

    # EAG-07: workflow_hash consistent (recompute roles+workflows)
    wf_hash = run_record.get("workflow_version", "")
    repo_root = project_dir.parent.parent  # projects/<name> -> repo root
    roles_hash = _hash_directory(repo_root / "core" / "roles", "*.yaml")
    wf_dir_hash = _hash_directory(repo_root / "core" / "workflows", "*.yaml")
    combined = _sha256_bytes((roles_hash + wf_dir_hash).encode("utf-8"))
    # Note: the actual hash_globs implementation may differ; we check non-empty and format
    checks.append(_check(
        "EAG-07", "workflow_version is valid non-empty hash",
        isinstance(wf_hash, str) and len(wf_hash) == 64 and wf_hash != SHA256_EMPTY,
        expected="64-char non-empty hex",
        actual=wf_hash[:16] + "..." if len(wf_hash) > 16 else wf_hash,
    ))

    # EAG-08: tool invocation records exist (code/output/artifacts directories with FILES)
    # Note: empty directories / scaffolding subdirs do NOT count as real execution artifacts.
    def _dir_has_files(d: Path) -> bool:
        """Return True only if directory contains at least one actual file (not just subdirs)."""
        if not d.exists():
            return False
        for f in d.rglob("*"):
            if f.is_file():
                return True
        return False

    has_code = _dir_has_files(project_dir / "code")
    has_output = _dir_has_files(project_dir / "output")
    has_artifacts = _dir_has_files(project_dir / "artifacts")
    checks.append(_check(
        "EAG-08", "real execution artifacts exist (code/output/artifacts with files)",
        has_code or has_output or has_artifacts,
        expected="at least one of code/, output/, artifacts/ containing actual files",
        actual=f"code(has_files)={has_code}, output(has_files)={has_output}, artifacts(has_files)={has_artifacts}",
    ))

    # EAG-09: artifact count > 0
    artifact_count = 0
    if registry:
        artifact_count = len(registry.get("artifacts", {}))
    checks.append(_check(
        "EAG-09", "registry has artifacts",
        artifact_count > 0,
        expected=">= 1 artifact",
        actual=artifact_count,
    ))

    # EAG-10: artifact payload non-empty (delegate to Artifact Integrity Gate Layer 1)
    if artifact_count > 0 and registry_path.exists():
        art_report = check_registry(registry_path)
        art_pass = art_report["summary"].get("PASS", 0)
        art_invalid = art_report["summary"].get("INVALID", 0)
        checks.append(_check(
            "EAG-10", "artifact payloads non-empty (>=80% pass Layer 1)",
            art_report["pass_rate"] >= 0.8 and art_invalid == 0,
            expected="pass_rate >= 0.8, no INVALID",
            actual=f"pass_rate={art_report['pass_rate']}, INVALID={art_invalid}",
        ))
    else:
        checks.append(_check(
            "EAG-10", "artifact payloads non-empty",
            False, expected="artifacts to check", actual="no registry or no artifacts",
        ))

    # EAG-11: decision_log non-empty with evidence
    decision_path = project_dir / "state" / "decision_log.json"
    decision_count = 0
    decision_with_evidence = 0
    if decision_path.exists():
        dlog = json.loads(decision_path.read_text(encoding="utf-8"))
        decisions = dlog.get("decisions", [])
        decision_count = len(decisions)
        for d in decisions:
            ev_ids = d.get("evidence_ids", [])
            reasoning = d.get("reasoning", "")
            if (isinstance(ev_ids, list) and len(ev_ids) > 0) or \
               (isinstance(reasoning, str) and len(reasoning) > 50 and "template" not in reasoning.lower()):
                decision_with_evidence += 1
    checks.append(_check(
        "EAG-11", "decision_log has decisions with evidence",
        decision_count > 0 and decision_with_evidence == decision_count,
        expected="all decisions have evidence_ids or substantive reasoning",
        actual=f"{decision_with_evidence}/{decision_count} decisions have evidence",
    ))

    # EAG-12: execution-result binding (provenance non-empty)
    provenance_count = 0
    external_provenance_count = 0
    if artifact_count > 0 and registry:
        for art in registry.get("artifacts", {}).values():
            prov = art.get("provenance", {})
            if isinstance(prov, dict) and len(prov) > 0:
                provenance_count += 1
                if prov.get("executor_type") == "external_agent":
                    external_provenance_count += 1
    checks.append(_check(
        "EAG-12", "artifacts have execution provenance (>=90%)",
        artifact_count > 0 and provenance_count / artifact_count >= 0.9,
        expected=">= 90% artifacts with non-empty provenance",
        actual=f"{provenance_count}/{artifact_count} have provenance",
    ))

    # EAG-13: execution_mode标识
    exec_mode = run_record.get("execution_mode")
    checks.append(_check(
        "EAG-13", "execution_mode is llm or hybrid",
        exec_mode in ("llm", "hybrid", "external_agent"),
        expected="'llm', 'hybrid', or 'external_agent'",
        actual=exec_mode if exec_mode else "(field missing — core schema gap)",
        message="'deterministic' or missing = template initialization, not real execution"
        if exec_mode not in ("llm", "hybrid", "external_agent") else "",
    ))

    # --- EAG-14/15/16: external_agent-specific checks (only for external_agent) ---
    if executor_type == "external_agent":
        # EAG-14: agent_identity non-empty
        agent_id = run_record.get("agent_identity")
        if not agent_id:
            # Try provenance
            prov = run_record.get("provenance", {})
            if isinstance(prov, dict):
                agent_id = prov.get("agent_identity")
        checks.append(_check(
            "EAG-14", "external agent_identity non-empty",
            isinstance(agent_id, str) and len(agent_id.strip()) > 0,
            expected="non-empty (doubao/gpt/claude/human)",
            actual=agent_id,
        ))

        # EAG-15: model_version non-empty (N/A for human)
        checks.append(_check(
            "EAG-15", "external model_version non-empty (N/A for human)",
            isinstance(mv, str) and len(mv.strip()) > 0,
            expected="non-empty or 'N/A'",
            actual=mv,
        ))

        # EAG-16: input_sha256 binding — verify at least one artifact has matching provenance
        input_bound = False
        if registry:
            for art in registry.get("artifacts", {}).values():
                prov = art.get("provenance", {})
                if isinstance(prov, dict):
                    art_input_hash = prov.get("input_sha256", "")
                    if art_input_hash and input_hash and art_input_hash == input_hash:
                        input_bound = True
                        break
        checks.append(_check(
            "EAG-16", "artifact input_sha256 bound to run input_hash",
            input_bound,
            expected="at least one artifact provenance.input_sha256 == run input_hash",
            actual="bound" if input_bound else "not bound",
        ))

    # Summarize
    pass_count = sum(1 for c in checks if c.get("pass") and not c.get("skipped"))
    skip_count = sum(1 for c in checks if c.get("skipped"))
    fail_count = sum(1 for c in checks if not c.get("pass") and not c.get("skipped"))
    # INVALID checks: EAG-01,02,03,05,08,10,12,13 are hard INVALID; others are FAIL
    invalid_ids = {"EAG-01", "EAG-02", "EAG-03", "EAG-05", "EAG-08",
                    "EAG-10", "EAG-12", "EAG-13", "EAG-14", "EAG-15", "EAG-16"}
    invalid_count = sum(1 for c in checks if not c.get("pass") and not c.get("skipped") and c["id"] in invalid_ids)

    if executor_type == "unknown":
        overall = "UNKNOWN"
    elif invalid_count > 0:
        overall = "INVALID"
    elif fail_count > 0:
        overall = "FAIL"
    else:
        overall = "PASS"

    return {
        "gate": "execution_authenticity",
        "version": "2.0",
        "project": project_dir.name,
        "run_id": run_id,
        "executor_type": executor_type,
        "synthetic": executor_type in ("dry_run", "synthetic"),
        "capability_result": executor_type == "external_agent",
        "overall": overall,
        "summary": {
            "pass": pass_count,
            "fail": fail_count - invalid_count,
            "invalid": invalid_count,
            "skipped": skip_count,
            "total": len(checks),
        },
        "checks": checks,
        "root_causes": _derive_root_causes(checks),
    }


def _derive_root_causes(checks: list[dict]) -> list[str]:
    """Derive human-readable root causes from failed checks."""
    causes = []
    failed_ids = {c["id"] for c in checks if not c["pass"]}
    if "EAG-01" in failed_ids or "EAG-02" in failed_ids:
        causes.append("model_provider/model_version is null — DefaultNodeExecutor is zero-LLM deterministic pipeline")
    if "EAG-05" in failed_ids:
        causes.append("latency below threshold — execution completed in template-initialization time, no real LLM/code execution")
    if "EAG-10" in failed_ids:
        causes.append("artifact payloads are empty — handlers create registry entries with payload=[] and only metadata in data field")
    if "EAG-08" in failed_ids:
        causes.append("no code/output/artifacts directories — no real execution artifacts on disk")
    if "EAG-03" in failed_ids:
        causes.append("skill_version is empty-string SHA256 — src/modeling_harness/skills/ has no .yaml files")
    if "EAG-12" in failed_ids:
        causes.append("artifact provenance is empty — no execution traceability (run_id/node_id/executor)")
    if "EAG-13" in failed_ids:
        causes.append("execution_mode missing or 'deterministic' — orchestrator --execute triggers template init, not LLM execution")
    if not causes:
        causes.append("no root causes identified")
    return causes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execution Authenticity & Artifact Integrity Gate (research-layer, deterministic)",
    )
    parser.add_argument("--project", type=str, default=None,
                        help="Path to project directory (e.g. projects/p151-2024a)")
    parser.add_argument("--run-manifest", type=str, default=None,
                        help="Path to a specific run manifest JSON file")
    parser.add_argument("--registry", type=str, default=None,
                        help="Path to a specific registry.json file")
    parser.add_argument("--artifact-only", action="store_true",
                        help="Only run Artifact Integrity Gate (skip Execution Authenticity)")
    parser.add_argument("--json", type=str, default=None,
                        help="Write full report to this JSON file")
    parser.add_argument("--quiet", action="store_true",
                        help="Only print overall verdict, not per-check details")
    args = parser.parse_args()

    if not args.project and not args.run_manifest and not args.registry:
        parser.error("At least one of --project, --run-manifest, or --registry is required")

    report = {}

    # Determine project directory
    project_dir = None
    if args.project:
        project_dir = Path(args.project).resolve()
        if not project_dir.exists():
            print(f"ERROR: project directory not found: {project_dir}", file=sys.stderr)
            return 2
    elif args.run_manifest:
        # Try to infer project dir from manifest path
        manifest_path = Path(args.run_manifest).resolve()
        if "state" in manifest_path.parts:
            idx = manifest_path.parts.index("state")
            project_dir = Path(*manifest_path.parts[:idx])
    elif args.registry:
        reg_path = Path(args.registry).resolve()
        if "state" in reg_path.parts:
            idx = reg_path.parts.index("state")
            project_dir = Path(*reg_path.parts[:idx])

    # Execution Authenticity Gate
    if not args.artifact_only:
        run_record = None
        if args.run_manifest:
            run_record = json.loads(Path(args.run_manifest).read_text(encoding="utf-8"))
        if project_dir:
            print("=" * 70)
            print("EXECUTION AUTHENTICITY GATE")
            print("=" * 70)
            eag_report = execution_authenticity_gate(project_dir, run_record)
            report["execution_authenticity"] = eag_report
            _print_eag(eag_report, quiet=args.quiet)
        else:
            print("WARNING: cannot run Execution Authenticity Gate without --project", file=sys.stderr)

    # Artifact Integrity Gate
    registry_path = None
    if args.registry:
        registry_path = Path(args.registry).resolve()
    elif project_dir:
        candidate = project_dir / "state" / "registry.json"
        if candidate.exists():
            registry_path = candidate

    if registry_path and registry_path.exists():
        print()
        print("=" * 70)
        print("ARTIFACT INTEGRITY GATE (Layer 1 + Layer 2)")
        print("=" * 70)
        art_report = check_registry(registry_path)
        report["artifact_integrity"] = art_report
        _print_artifact_report(art_report, quiet=args.quiet)
    else:
        print("WARNING: no registry.json found, skipping Artifact Integrity Gate", file=sys.stderr)

    # Overall
    print()
    print("=" * 70)
    print("OVERALL")
    print("=" * 70)
    verdicts = []
    if "execution_authenticity" in report:
        verdicts.append(report["execution_authenticity"]["overall"])
    if "artifact_integrity" in report:
        verdicts.append(report["artifact_integrity"]["overall"])

    if "INVALID" in verdicts:
        overall = "INVALID"
    elif "FAIL" in verdicts:
        overall = "FAIL"
    elif verdicts:
        overall = "PASS"
    else:
        overall = "UNKNOWN"

    print(f"  Overall verdict: {overall}")
    for gate_name, gate_report in report.items():
        print(f"  - {gate_name}: {gate_report['overall']}")
    report["overall"] = overall

    # Write JSON report
    if args.json:
        json_path = Path(args.json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nFull report written to: {json_path.resolve()}")

    # Exit code: 0=PASS, 1=FAIL, 2=INVALID
    if overall == "PASS":
        return 0
    elif overall == "FAIL":
        return 1
    else:
        return 2


def _print_eag(report: dict, quiet: bool = False) -> None:
    print(f"  Project      : {report.get('project', '?')}")
    print(f"  Run ID       : {report.get('run_id', '?')}")
    print(f"  Executor Type: {report.get('executor_type', '?')}")
    if report.get("synthetic"):
        print(f"  *** SYNTHETIC / NOT A CAPABILITY RESULT ***")
    print(f"  Verdict      : {report['overall']}")
    s = report["summary"]
    summary_parts = [f"PASS={s['pass']}", f"FAIL={s['fail']}",
                      f"INVALID={s['invalid']}", f"TOTAL={s['total']}"]
    if s.get("skipped", 0) > 0:
        summary_parts.insert(3, f"SKIPPED={s['skipped']}")
    print(f"  Summary      : {'  '.join(summary_parts)}")
    print()
    if not quiet:
        for c in report["checks"]:
            if c.get("skipped"):
                status = "SKIP"
            else:
                status = "PASS" if c["pass"] else "FAIL"
            line = f"  [{status:4s}] {c['id']:8s} {c['name']}"
            if not c.get("skipped") and not c["pass"]:
                line += f"  (actual: {str(c['actual'])[:60]})"
                if c.get("message"):
                    line += f"\n          → {c['message']}"
            elif c.get("skipped") and c.get("message"):
                line += f"  ({c['message'][:50]})"
            print(line)
    print()
    print("  Root causes:")
    for cause in report.get("root_causes", []):
        print(f"    - {cause}")


def _print_artifact_report(report: dict, quiet: bool = False) -> None:
    print(f"  Registry : {report.get('registry_path', '?')}")
    print(f"  Total    : {report['total_artifacts']} artifacts")
    print(f"  Verdict  : {report['overall']}")
    print(f"  Pass rate: {report['pass_rate']:.1%}")
    s = report["summary"]
    print(f"  Summary  : " + "  ".join(f"{k}={v}" for k, v in sorted(s.items())))
    print()
    if not quiet:
        for art in report.get("artifacts", []):
            status = art["overall"]
            line = f"  [{status:7s}] {art['artifact_id']:5s} ({art['type']})"
            if status != "PASS":
                # Show first failed check
                l1 = art.get("layer1")
                if l1 and l1["verdict"] != "PASS":
                    failed = [c for c in l1["checks"] if not c["pass"]]
                    if failed:
                        line += f"  L1 fail: {failed[0]['id']} {failed[0]['name']}"
                elif art.get("layer2") and art["layer2"]["verdict"] != "PASS":
                    failed = [c for c in art["layer2"]["checks"] if not c["pass"]]
                    if failed:
                        line += f"  L2 fail: {failed[0]['id']} {failed[0]['name']}"
            print(line)


if __name__ == "__main__":
    sys.exit(main())
