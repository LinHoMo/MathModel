# -*- coding: utf-8 -*-
"""真正迁移：problem_cards/<题>/gt.json 的 allowed_model_families -> allowed_modeling_structures"""
import json
from pathlib import Path

ROOT = Path(".").resolve()
base = ROOT / "research" / "P15" / "benchmark" / "problem_cards"
n = 0
for d in sorted(base.iterdir()):
    gt = d / "gt.json"
    if not gt.exists():
        continue
    data = json.loads(gt.read_text(encoding="utf-8"))
    if "allowed_model_families" in data:
        data["allowed_modeling_structures"] = data.pop("allowed_model_families")
        gt.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [MIGRATED] {d.name}: {len(data['allowed_modeling_structures'])} structures")
        n += 1
    else:
        key = "allowed_modeling_structures" if "allowed_modeling_structures" in data else None
        print(f"  [OK] {d.name}: key={key}")
print(f"\ntotal migrated: {n}")
