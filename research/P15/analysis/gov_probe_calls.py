# -*- coding: utf-8 -*-
"""摸底 3：调用关系——candidates/planner/selection/fidelity/codegen 被谁调用"""
import os
from pathlib import Path

targets = ["candidates", "planner", "MethodArena", "CandidateArena", "ExperimentPlanner",
           "verify_fidelity", "run_code_pipeline", "register_code", "execute_code"]

calls = {t: [] for t in targets}
for root in ["core", "tests"]:
    for dp, dns, fns in os.walk(root):
        if "__pycache__" in dp:
            continue
        for f in fns:
            if not f.endswith(".py"):
                continue
            p = os.path.join(dp, f)
            try:
                t = Path(p).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for tgt in targets:
                if tgt in t:
                    calls[tgt].append(p)

for t in targets:
    print(f"== {t} 被引用于 ==")
    for p in calls[t]:
        print(f"   {p}")
    if not calls[t]:
        print("   (无引用)")
