# -*- coding: utf-8 -*-
import re
from pathlib import Path

# 1. 修复 test_e2e_metrics.py 的 sys.path
p = Path("tests/integration/test_e2e_metrics.py")
t = p.read_text(encoding="utf-8")
old = 'sys.path.insert(0, str(REPO / "src" / "tools" / "evaluation"))'
new = 'sys.path.insert(0, str(REPO / "src" / "tools"))'
if old in t:
    p.write_text(t.replace(old, new), encoding="utf-8")
    print("[OK] test_e2e_metrics.py sys.path fixed")
else:
    print("[WARN] pattern not found in test_e2e_metrics.py")

# 2. 全库扫描 src/modeling_harness/cli/evaluation 引用（含 .py/.md/.json/.yaml）
pat = re.compile(r"core[\\/]+tools[\\/]+evaluation(?:[\\/][A-Za-z0-9_\-./]+)?")
n = 0
for root in ("core", "tests", "research", "docs"):
    for f in Path(root).rglob("*"):
        if f.is_file() and f.suffix in (".py", ".md", ".json", ".yaml", ".yml", ".txt"):
            try:
                t = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in pat.finditer(t):
                print(f"  {f}: {t[max(0,m.start()-60):m.end()+40]!r}")
                n += 1
print(f"\ntotal refs to src/modeling_harness/cli/evaluation: {n}")
