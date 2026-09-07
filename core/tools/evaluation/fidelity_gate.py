#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fidelity_gate.py — P13-3D Model Fidelity Gate v2（三仪表 + Writer 失败分类）。

v2 更新（P13-3D-R1 Consolidation）：
  - 拆分为三个独立仪表：Coverage / Mutation / Semantic
  - 新增 Writer Failure Taxonomy (P1-P8)
  - 不再压缩为单一 Fidelity Score

三个仪表：
  1. Coverage Fidelity：artifact 元素在论文中的覆盖率（有没有漏掉）
  2. Unauthorized Mutation：论文新增/修改/重命名模型元素（有没有乱改）
  3. Semantic Fidelity：论文与 artifact 的语义一致性（含义有没有漂移）

Writer Failure Taxonomy：
  P1: Model omission（遗漏模型组件）
  P2: Model mutation（修改模型组件）
  P3: Unsupported claim（声称无支持的结论）
  P4: Equation corruption（方程错误）
  P5: Constraint corruption（约束错误）
  P6: Parameter corruption（参数错误）
  P7: Interpretation drift（解释漂移）
  P8: Experiment/model mismatch（实验与模型不匹配）

用法:
  python fidelity_gate.py --artifact <artifact.json> --paper <paper.md> [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# --- Mutation types ---
MUTATION_TYPES = ("addition", "deletion", "modification", "renaming", "semantic_drift")

# --- Artifact element categories (from MODEL_ARTIFACT v1 schema) ---
ARTIFACT_ELEMENTS = {
    "variables": {"key": "id", "fields": ["id", "name", "description", "unit", "role", "domain"]},
    "parameters": {"key": "id", "fields": ["id", "name", "value_or_source", "unit", "source"]},
    "constraints": {"key": "id", "fields": ["id", "expression", "rationale"]},
    "objective": {"key": "id", "fields": ["id", "expression", "kind", "rationale"]},
    "mechanism": {"key": "id", "fields": ["id", "name", "equation", "derivation_notes"]},
    "assumptions": {"key": "id", "fields": ["id", "statement", "justification"]},
    "candidate_models": {"key": "model", "fields": ["model", "pros", "cons"]},
    "selected_model": {"key": None, "fields": ["selected_model"]},
    "uncertainties": {"key": "source", "fields": ["source", "handling", "effect"]},
    "sensitivity_plan": {"key": "parameter", "fields": ["parameter", "range", "metric"]},
}

# --- Severity weights ---
SEVERITY_WEIGHTS = {"critical": 1.0, "major": 0.5, "minor": 0.1}

# --- Writer Failure Taxonomy ---
WRITER_FAILURE_TAXONOMY = {
    "P1": {"name": "Model omission", "description": "Paper omits model components from artifact"},
    "P2": {"name": "Model mutation", "description": "Paper modifies model components"},
    "P3": {"name": "Unsupported claim", "description": "Paper makes claims not supported by model"},
    "P4": {"name": "Equation corruption", "description": "Paper presents corrupted equations"},
    "P5": {"name": "Constraint corruption", "description": "Paper presents corrupted constraints"},
    "P6": {"name": "Parameter corruption", "description": "Paper presents corrupted parameters"},
    "P7": {"name": "Interpretation drift", "description": "Paper misinterprets model semantics"},
    "P8": {"name": "Experiment/model mismatch", "description": "Paper claims experiments not in model"},
}


def _load(path: Path) -> dict | str:
    """Load JSON or text file."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    return text


def _build_artifact_index(artifact: dict) -> dict[str, dict[str, Any]]:
    """Build a searchable index of all artifact elements."""
    index = {}
    for category, spec in ARTIFACT_ELEMENTS.items():
        items = artifact.get(category, [])
        if spec["key"] is None:
            val = artifact.get(category, "")
            if val:
                index[f"{category}:{val}"] = {
                    "category": category,
                    "content": val,
                    "raw": val,
                }
        else:
            for item in items:
                key_val = item.get(spec["key"], "")
                idx_key = f"{category}:{key_val}"
                index[idx_key] = {
                    "category": category,
                    "key_value": key_val,
                    "content": _element_to_text(item),
                    "raw": item,
                }
    return index


def _element_to_text(element: dict) -> str:
    """Convert an artifact element to searchable text."""
    parts = []
    for k, v in element.items():
        if v:
            parts.append(f"{k}: {v}")
    return " | ".join(parts)


def _paper_to_text(paper: str | dict) -> str:
    """Normalize paper content to text."""
    if isinstance(paper, dict):
        return json.dumps(paper, ensure_ascii=False, indent=2)
    return paper


def _find_mentions(text: str, element: dict) -> list[dict]:
    """Find mentions of an artifact element in paper text."""
    mentions = []
    for field in ["id", "name", "model", "equation", "expression", "statement", "_value"]:
        val = element.get(field, "")
        if val and len(str(val)) > 2:
            if str(val).lower() in text.lower():
                mentions.append({
                    "match_type": "exact_id",
                    "field": field,
                    "context": _find_context(text, str(val)),
                })
    if "equation" in element:
        eq = element["equation"]
        vars_in_eq = re.findall(r'[a-zA-Z_]\w*', eq)
        for var in vars_in_eq:
            if var in text and var not in ["d", "dt", "dx", "sum", "max", "min"]:
                mentions.append({
                    "match_type": "variable_in_text",
                    "field": "equation_variable",
                    "variable": var,
                })
    return mentions


def _find_context(text: str, query: str, window: int = 100) -> str:
    """Find surrounding context for a query in text."""
    idx = text.lower().find(query.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(query) + window)
    return text[start:end].strip()


def _detect_additions(artifact: dict, paper_text: str) -> list[dict]:
    """Detect paper elements not present in artifact (Additions)."""
    additions = []
    artifact_vars = set()
    for v in artifact.get("variables", []):
        vid = v.get("id", "")
        if vid:
            artifact_vars.add(vid)
            artifact_vars.add(vid.lower())

    paper_vars = set(re.findall(r'\$([A-Za-z][A-Za-z0-9_]*)\$', paper_text))
    new_vars = paper_vars - artifact_vars - {
        "N", "t", "R", "K", "P", "r", "d", "dt", "dx",
        "min", "max", "sum", "prod", "lim", "inf", "sup",
    }

    for var in new_vars:
        if len(var) <= 1:
            continue
        additions.append({
            "type": "addition",
            "severity": "major",
            "category": "variables",
            "affected_object": var,
            "artifact_ref": "NOT_IN_ARTIFACT",
            "paper_ref": "mentioned_in_paper",
            "description": f"Variable '{var}' appears in paper but not in artifact",
        })

    return additions


def _classify_writer_failures(mutations: list, additions: list) -> list[dict]:
    """Classify mutations into Writer Failure Taxonomy (P1-P8)."""
    failures = []
    for m in mutations:
        mtype = m.get("type", "")
        category = m.get("category", "")
        severity = m.get("severity", "")

        if mtype == "deletion":
            if category in ("objective", "mechanism"):
                failures.append({"code": "P1", "detail": m.get("description", "")})
            elif category == "constraints":
                failures.append({"code": "P5", "detail": m.get("description", "")})
            elif category == "parameters":
                failures.append({"code": "P6", "detail": m.get("description", "")})
            else:
                failures.append({"code": "P1", "detail": m.get("description", "")})

        elif mtype == "modification":
            if category == "mechanism":
                failures.append({"code": "P4", "detail": m.get("description", "")})
            elif category == "constraints":
                failures.append({"code": "P5", "detail": m.get("description", "")})
            elif category == "parameters":
                failures.append({"code": "P6", "detail": m.get("description", "")})
            else:
                failures.append({"code": "P2", "detail": m.get("description", "")})

        elif mtype == "semantic_drift":
            failures.append({"code": "P7", "detail": m.get("description", "")})

        elif mtype == "renaming":
            failures.append({"code": "P2", "detail": m.get("description", "")})

    for a in additions:
        failures.append({"code": "P3", "detail": a.get("description", "")})

    seen = set()
    unique_failures = []
    for f in failures:
        key = (f["code"], f["detail"])
        if key not in seen:
            seen.add(key)
            unique_failures.append(f)

    return unique_failures


def compute_fidelity(artifact: dict, paper_text: str) -> dict:
    """Compute three fidelity metrics between artifact and paper.

    Returns:
        {
            "coverage_fidelity": float (0-1),  # What % of artifact elements appear in paper
            "mutation_audit": {                 # Unauthorized mutations
                "additions": [...],
                "deletions": [...],
                "modifications": [...],
                "renamings": [...],
                "total": int,
            },
            "semantic_fidelity": float (0-1),  # Semantic consistency
            "element_coverage": {category: {total: n, found: n, missing: [...]}},
            "writer_failures": [...],          # P1-P8 taxonomy
            "summary": str,
        }
    """
    paper = _paper_to_text(paper_text)

    # --- 1. Coverage Fidelity ---
    element_coverage = {}
    total_elements = 0
    found_elements = 0
    deletions = []

    for category, spec in ARTIFACT_ELEMENTS.items():
        items = artifact.get(category, [])
        if spec["key"] is None:
            items = [{"_value": artifact.get(category, "")}] if artifact.get(category) else []

        cat_total = len(items)
        cat_found = 0
        cat_missing = []

        for item in items:
            total_elements += 1
            key_val = item.get(spec["key"], "") if spec["key"] else item.get("_value", "")
            mentions = _find_mentions(paper, item)

            if mentions:
                found_elements += 1
                cat_found += 1
            else:
                cat_missing.append(key_val)
                severity = "major"
                if category in ("objective", "mechanism"):
                    severity = "critical"
                elif category in ("assumptions", "uncertainties"):
                    severity = "minor"

                deletions.append({
                    "type": "deletion",
                    "severity": severity,
                    "category": category,
                    "affected_object": str(key_val),
                    "artifact_ref": f"{category}.{key_val}",
                    "paper_ref": "NOT_FOUND",
                    "description": f"Artifact element '{key_val}' not found in paper",
                })

        element_coverage[category] = {
            "total": cat_total,
            "found": cat_found,
            "missing": cat_missing,
        }

    coverage_fidelity = found_elements / total_elements if total_elements > 0 else 1.0

    # --- 2. Unauthorized Mutation ---
    additions = _detect_additions(artifact, paper)

    mutation_audit = {
        "additions": additions,
        "deletions": deletions,
        "modifications": [],  # TODO: LLM-based detection
        "renamings": [],      # TODO: LLM-based detection
        "total": len(additions) + len(deletions),
    }

    # --- 3. Semantic Fidelity ---
    # Simplified: based on coverage + mutation ratio
    if total_elements == 0:
        semantic_fidelity = 1.0
    else:
        weighted_mutations = sum(
            SEVERITY_WEIGHTS.get(m["severity"], 0.5)
            for m in deletions + mutation_audit["modifications"]
        )
        semantic_fidelity = max(0.0, 1.0 - weighted_mutations / total_elements)

    # --- 4. Writer Failure Classification ---
    all_mutations = deletions + mutation_audit["modifications"] + mutation_audit["renamings"]
    writer_failures = _classify_writer_failures(all_mutations, additions)

    # --- Summary ---
    n_del = len(deletions)
    n_add = len(additions)
    n_crit = sum(1 for m in deletions if m["severity"] == "critical")
    n_major = sum(1 for m in deletions if m["severity"] == "major")
    n_minor = sum(1 for m in deletions if m["severity"] == "minor")

    failure_codes = set(f["code"] for f in writer_failures)
    failure_str = ", ".join(sorted(failure_codes)) if failure_codes else "none"

    summary = (
        f"Coverage: {coverage_fidelity:.1%} ({found_elements}/{total_elements}). "
        f"Mutations: {n_del} deletions ({n_crit}C/{n_major}M/{n_minor}m), "
        f"{n_add} additions. "
        f"Writer failures: {failure_str}. "
        f"Semantic: {semantic_fidelity:.1%}."
    )

    return {
        "coverage_fidelity": round(coverage_fidelity, 3),
        "mutation_audit": mutation_audit,
        "semantic_fidelity": round(semantic_fidelity, 3),
        "element_coverage": element_coverage,
        "total_elements": total_elements,
        "found_elements": found_elements,
        "writer_failures": writer_failures,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="P13-3D Model Fidelity Gate v2")
    parser.add_argument("--artifact", required=True, help="Path to MODEL_ARTIFACT JSON")
    parser.add_argument("--paper", required=True, help="Path to paper (.md or .json)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--audit-log", help="Write detailed audit log to file")
    args = parser.parse_args()

    artifact = _load(Path(args.artifact))
    paper = _load(Path(args.paper))

    if isinstance(artifact, dict) and "_error" in artifact:
        print(f"Error loading artifact: {artifact['_error']}", file=sys.stderr)
        sys.exit(1)

    result = compute_fidelity(artifact, paper)

    if args.audit_log:
        Path(args.audit_log).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Audit log written to {args.audit_log}")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["summary"])


if __name__ == "__main__":
    main()
