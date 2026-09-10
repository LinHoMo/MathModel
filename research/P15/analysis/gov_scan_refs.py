# -*- coding: utf-8 -*-
"""治理扫描：核对 src/modeling_harness/cli/evaluation 引用方式"""
import re

for f in ["src/modeling_harness/cli/benchmark.py", "AGENTS.md", "README.md"]:
    t = open(f, encoding="utf-8").read()
    print(f"=== {f} ===")
    for m in re.finditer(r"src/modeling_harness/cli/evaluation[^\s`\"']*", t):
        s = max(0, m.start() - 70)
        e = m.end() + 40
        print("   ", repr(m.group(0)))
        print("    ctx:", repr(t[s:e]))
    for m in re.finditer(r"projects/my-problem", t):
        print("   my-problem ctx:", repr(t[max(0, m.start()-80):m.end()+40]))
    print()
