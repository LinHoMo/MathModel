# -*- coding: utf-8 -*-
"""治理修复：批量替换 src/modeling_harness/cli/evaluation/xxx.py -> src/modeling_harness/cli/xxx.py
仅当目标文件存在于 src/modeling_harness/cli/ 根时替换（纯路径迁移）；否则保留原样（历史事实）。
"""
import re
from pathlib import Path

ROOT = Path(".").resolve()
MIGRATED = {
    "e2e_metrics.py": "src/modeling_harness/cli/e2e_metrics.py",
    "benchmark.py": "src/modeling_harness/cli/benchmark.py",
    "bench_mmbench.py": "src/modeling_harness/cli/bench_mmbench.py",
    "citation_check.py": "src/modeling_harness/cli/citation_check.py",
}
# 确认目标存在
for f, dest in MIGRATED.items():
    assert (ROOT / dest).exists(), f"target missing: {dest}"

pat = re.compile(r"src/modeling_harness/cli/evaluation/([A-Za-z0-9_]+\.py)")

changed = []
for p in list((ROOT / "docs").rglob("*.md")) + list(ROOT.glob("*.md")) \
        + list((ROOT / "src").rglob("*.py")):
    try:
        t = p.read_text(encoding="utf-8")
    except Exception:
        continue
    def repl(m):
        name = m.group(1)
        if name in MIGRATED:
            return MIGRATED[name]
        return m.group(0)
    nt, n = pat.subn(repl, t)
    if n:
        p.write_text(nt, encoding="utf-8")
        changed.append((str(p.relative_to(ROOT)).replace("\\", "/"), n))

for c, n in sorted(changed):
    print(f"  {n:2d}  {c}")
print(f"\ntotal files changed: {len(changed)}")
