#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggregate blind evaluation scores by arm."""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent.parent
scores_dir = ROOT / "research/P15/analysis/raw/scores"
cmap_path = ROOT / "research/P15/experiments/P15-K001/key/condition_map.json"

json_files = list(scores_dir.glob("*.json"))
template_files = [f for f in json_files if f.name.endswith(".template.json")]
filled = [f for f in json_files if not f.name.endswith(".template.json")]
print(f"评分文件(已填): {len(filled)}")
print(f"模板文件(.template): {len(template_files)}")

cmap = json.load(open(cmap_path, encoding="utf-8"))["map"]

arm_stats = defaultdict(list)
for f in filled:
    sid = f.stem
    d = json.load(open(f, encoding="utf-8"))
    arm = cmap.get(sid, {}).get("arm", "?")
    v = d.get("vector", {})
    arm_stats[arm].append({
        "sid": sid[:8],
        "overall": v.get("overall", 0),
        "L1": v.get("L1", 0),
        "L2": v.get("L2", 0),
        "L3": v.get("L3", 0),
        "L4": v.get("L4", 0),
    })

print()
print("=== 按臂聚合 ===")
for arm in ["A", "B", "C", "D", "E"]:
    runs = arm_stats[arm]
    if not runs:
        continue
    overalls = [r["overall"] for r in runs]
    l2s = [r["L2"] for r in runs]
    l1s = [r["L1"] for r in runs]
    print(
        f"Arm {arm}: n={len(runs)}, "
        f"overall mean={sum(overalls)/len(overalls):.1f}/42 "
        f"(min={min(overalls)}, max={max(overalls)}), "
        f"L2 mean={sum(l2s)/len(l2s):.1f}/15, "
        f"L1 mean={sum(l1s)/len(l1s):.1f}/9"
    )

print()
print("=== FAIL 样本（任一层 <70%）===")
fail_count = 0
for arm in ["A", "B", "C", "D", "E"]:
    for r in arm_stats[arm]:
        l1p = r["L1"] >= 6.3
        l2p = r["L2"] >= 10.5
        l3p = r["L3"] >= 6.3
        l4p = r["L4"] >= 6.3
        if not (l1p and l2p and l3p and l4p):
            fail_count += 1
            print(
                f"  Arm {arm}: {r['sid']} "
                f"L1={r['L1']} L2={r['L2']} L3={r['L3']} L4={r['L4']} "
                f"overall={r['overall']}"
            )
print(f"FAIL 总数: {fail_count}/55")

print()
all_overall = [r["overall"] for arm in arm_stats for r in arm_stats[arm]]
print(f"全体: n={len(all_overall)}, mean={sum(all_overall)/len(all_overall):.1f}/42")

# Per-problem breakdown
print()
print("=== 按题目聚合 ===")
prob_stats = defaultdict(list)
for f in filled:
    sid = f.stem
    d = json.load(open(f, encoding="utf-8"))
    prob = cmap.get(sid, {}).get("problem_id", "?")
    v = d.get("vector", {})
    prob_stats[prob].append(v.get("overall", 0))
for prob in sorted(prob_stats):
    vals = prob_stats[prob]
    print(f"  {prob}: n={len(vals)}, mean={sum(vals)/len(vals):.1f}/42 (min={min(vals)}, max={max(vals)})")
