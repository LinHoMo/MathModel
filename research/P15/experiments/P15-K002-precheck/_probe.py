#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe: list all 12 precheck runs with manifest info + statement existence."""
import json
from pathlib import Path

base = Path(__file__).resolve().parent
cmap = json.loads((base / "key/condition_map.json").read_text(encoding="utf-8"))["map"]
for sid, info in cmap.items():
    m = json.loads((base / "runs" / sid / "manifest.json").read_text(encoding="utf-8"))
    pid = info["problem_id"]
    stmt = Path(f"research/P15/benchmark/problem_cards/{pid}/problem_statement.txt")
    gt = Path(f"research/P15/benchmark/problem_cards/{pid}/gt.json")
    gt_data = json.loads(gt.read_text(encoding="utf-8")) if gt.exists() else {}
    print(f"{sid}  {pid:6}  arm={info['arm']}  "
          f"sha={m['statement_sha256']}  "
          f"sqs={gt_data.get('sub_questions', [])}  "
          f"stmt_exists={stmt.exists()}")
