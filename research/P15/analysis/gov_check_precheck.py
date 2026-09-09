# -*- coding: utf-8 -*-
import json
from pathlib import Path

base = Path("research/P15/experiments/P15-K002-precheck/runs")
for d in sorted(base.iterdir()):
    m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    files = sorted(x.name for x in d.iterdir() if x.is_file())
    print(f"{d.name[:8]}  arm={m.get('arm'):4s}  status={m.get('status'):12s}  files={files}")
