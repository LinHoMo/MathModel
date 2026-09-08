#!/usr/bin/env python3
"""duplicate_gate.py — P15.0 gate: no duplicate question_ids + content sha256 manifest."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark" / "CUMCM-Bench-v2.json"


def _content_hash(entry: dict) -> str:
    stable = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def main() -> int:
    bench = json.loads(BENCH.read_text(encoding="utf-8"))
    problems = bench.get("problems", [])

    seen: dict[str, int] = {}
    dupes = []
    for i, p in enumerate(problems):
        qid = p.get("question_id", f"<index {i}>")
        if qid in seen:
            dupes.append(f"  {qid} appears at index {seen[qid]} and {i}")
        else:
            seen[qid] = i

    if dupes:
        print(f"FAIL: {len(dupes)} duplicate question_ids")
        for d in dupes:
            print(d)
        return 1

    print(f"OK: {len(problems)} unique question_ids")

    # Hash manifest
    manifest = {}
    for p in problems:
        qid = p["question_id"]
        manifest[qid] = _content_hash(p)

    out = ROOT / "benchmark" / "manifests" / "content_hashes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Hash manifest written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
