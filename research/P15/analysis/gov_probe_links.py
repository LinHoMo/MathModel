# -*- coding: utf-8 -*-
"""摸底 2：链路连通性 + 测试覆盖"""
import os
from pathlib import Path

# 1. core/adapters 实况
print("== core/adapters ==")
if Path("core/adapters").exists():
    for dp, dns, fns in os.walk("core/adapters"):
        print("  ", dp, dns, fns)
else:
    print("  [不存在]")
# 也看 src/modeling_harness/runtime/adapters
print("== src/modeling_harness/runtime/adapters ==")
for dp, dns, fns in os.walk("src/modeling_harness/runtime/adapters"):
    print("  ", dp, dns, fns)

# 2. 关键模块的测试覆盖
print("\n== 测试覆盖（modeling/execution/fidelity/codegen/candidates/selection）==")
for pat in ["candidates", "selection", "planner", "fidelity", "codegen", "decision", "knowledge"]:
    hits = []
    for dp, dns, fns in os.walk("tests"):
        for f in fns:
            if pat in f.lower():
                hits.append(os.path.join(dp, f))
    print(f"  {pat}: {hits}")

# 3. 端到端入口：orchestrator 与 tools 里是否有把整链串起来的脚本
print("\n== core/tools 中可能的入口 ==")
for f in sorted(Path("src/modeling_harness/tools").glob("*.py")):
    t = f.read_text(encoding="utf-8", errors="ignore")[:200]
    if any(k in t for k in ["pipeline", "run_project", "model_ir", "construct", "fidelity", "codegen"]):
        print(f"  {f.name}")

# 4. 是否存在 MODEL_IR schema 与 model 构造相关 schema
print("\n== schemas/v3 文件 ==")
for dp, dns, fns in os.walk("src/modeling_harness/schemas/v3"):
    for f in fns:
        print("  ", os.path.join(dp, f).replace("src/modeling_harness/schemas/v3", ""))
