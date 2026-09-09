# -*- coding: utf-8 -*-
t = open("README.md", encoding="utf-8").read()
old = "| benchmark（能力测量） | `core/tools/evaluation/`（能力层 8 件） | 长期；语料在仓库外（`MMBENCH_ROOT`） |"
new = "| benchmark（能力测量） | `core/tools/`（能力层 8 件：benchmark.py / e2e_metrics.py / bench_mmbench.py） | 长期；语料在仓库外（`MMBENCH_ROOT`） |"
assert old in t, "pattern not found in README.md"
open("README.md", "w", encoding="utf-8").write(t.replace(old, new))
print("[OK] README.md fixed")
