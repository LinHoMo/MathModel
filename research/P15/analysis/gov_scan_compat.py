# -*- coding: utf-8 -*-
"""治理扫描：历史兼容性 + 命名问题"""
import re, collections
from pathlib import Path

ROOT = Path(".").resolve()

print("=== 1. allowed_model_families 残留位置（生产/研究）===")
for p in list((ROOT / "src").rglob("*")) + list((ROOT/"research").rglob("*")) + list((ROOT/"catalog").rglob("*")):
    if p.is_file() and p.suffix in (".py", ".yaml", ".json", ".md"):
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in re.finditer(r"allowed_model_families", t):
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            print(f"  {rel}: {m.start()}")

print("\n=== 2. method_family / method_selection 旧键残留（生产 core 内）===")
for p in list((ROOT / "src").rglob("*.py")):
    try:
        t = p.read_text(encoding="utf-8")
    except Exception:
        continue
    for key in ("method_family_identified", "\"method_family\"", "'method_family'"):
        for m in re.finditer(re.escape(key), t):
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            print(f"  {rel}: {key} @{m.start()}")

print("\n=== 3. K001 三臂协议 SUPERSEDED 状态 ===")
for p in (ROOT/"research/P15/protocol").rglob("*.md"):
    t = p.read_text(encoding="utf-8")
    if "SUPERSEDED" in t:
        print(f"  [SUPERSEDED] {p.relative_to(ROOT)}")
    if "three_arm" in str(p).lower():
        print(f"  [three-arm] {p.relative_to(ROOT)}")

print("\n=== 4. analysis 目录命名 ===")
a = ROOT/"research/P15/analysis"
for d in sorted(x.name for x in a.iterdir() if x.is_dir()):
    print(f"  {d}")

print("\n=== 5. catalog/model_families.yaml 状态 ===")
t = (ROOT/"catalog/model_families.yaml").read_text(encoding="utf-8")
print("  frozen 字段:", re.findall(r"frozen:\s*\w+", t))
print("  canonical families:", len(re.findall(r"^  - id:", t, re.M)))
