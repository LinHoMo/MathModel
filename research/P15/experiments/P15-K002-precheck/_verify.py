#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify all 12 precheck artifacts exist and manifests are GENERATED."""
import json
from pathlib import Path

base = Path("research/P15/experiments/P15-K002-precheck")
cmap = json.loads((base / "key/condition_map.json").read_text(encoding="utf-8"))["map"]
ok = 0
fail = []
for sid, info in cmap.items():
    rd = base / "runs" / sid
    art = "model_ir.json" if info["arm"] == "S" else "model_doc.md"
    m = json.loads((rd / "manifest.json").read_text(encoding="utf-8"))
    exists = (rd / art).exists()
    size = (rd / art).stat().st_size if exists else 0
    print(f"{sid[:8]} {info['problem_id']:6} arm={info['arm']} status={m['status']:10} {art} exists={exists} size={size}")
    if exists and m["status"] == "GENERATED":
        ok += 1
    else:
        fail.append(sid)
print(f"\nOK={ok}/12  FAIL={fail}")
