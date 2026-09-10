# -*- coding: utf-8 -*-
"""摸底：core 关键目录结构与链路环节代码存在性"""
import os

for root in ["src/modeling_harness/runtime", "core/adapters", "src/modeling_harness/tools", "src/modeling_harness/schemas/v3", "src/modeling_harness/knowledge"]:
    print(f"== {root} ==")
    for dp, dns, fns in os.walk(root):
        depth = dp.count(os.sep) - root.count(os.sep)
        if depth > 2:
            continue
        py = [f for f in fns if f.endswith(".py")]
        rel = dp.replace(root, "").lstrip(os.sep)
        if py or not dns:
            print(f"  {rel or '.'}/: {len(py)} py {py[:6]}")
