# -*- coding: utf-8 -*-
"""摸底 4：codegen 是否被 handlers/orchestrator 引用 + Revision 环节存在性"""
import os
from pathlib import Path

print("== handlers.py 中与 code/exec/fidelity 相关的引用 ==")
t = Path("src/modeling_harness/runtime/execution/handlers.py").read_text(encoding="utf-8", errors="ignore")
for kw in ["codegen", "register_code", "execute_code", "run_code_pipeline", "fidelity", "ExecutionPlan"]:
    n = t.count(kw)
    print(f"  {kw}: {n} 处")

print("\n== orchestrator/DAG 节点定义中是否有 codegen 类节点 ==")
for f in ["src/modeling_harness/cli/orchestrator.py", "catalog/v3.yaml"]:
    p = Path(f)
    if not p.exists():
        print(f"  [缺失] {f}")
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    hits = [kw for kw in ["codegen", "fidelity", "implement", "execute_code", "validation"] if kw in t]
    print(f"  {f}: 命中 {hits}")

print("\n== Revision 环节（grep revision/revise/model_version）==")
for root in ["src/modeling_harness/runtime", "src/modeling_harness/tools"]:
    for dp, dns, fns in os.walk(root):
        if "__pycache__" in dp:
            continue
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            try:
                t = Path(p).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for kw in ["revision", "revise", "model_version", "iteration"]:
                if kw in t.lower():
                    # 只列含关键语句的行
                    for line in t.splitlines():
                        if kw in line.lower() and any(c.isalpha() for c in line):
                            print(f"  {p}: {line.strip()[:100]}")
                    break

print("\n== orchestrator 节点类型（V3 DAG 干跑看到的节点）==")
t = Path("src/modeling_harness/cli/orchestrator.py").read_text(encoding="utf-8", errors="ignore")
# 找节点 type 枚举
import re
for m in re.finditer(r"(model_construction|model_selection|experiment_design|code_implement|execution|validation|revision|critique)[\"']", t):
    pass
types = set(re.findall(r"[\"'](model_construction|model_selection|experiment_design|implementation|execution|validation|revision|critique)[\"']", t))
print("  orchestrator 引用节点类型:", sorted(types))
