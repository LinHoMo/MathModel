# -*- coding: utf-8 -*-
"""治理检查：research/P15 顶层与 protocol/model_representation 的 md 标注状态"""
from pathlib import Path

for d in ["research/P15", "research/P15/protocol", "research/P15/model_representation", "research/P15/capability"]:
    for p in sorted(Path(d).glob("*.md")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        marks = []
        for kw in ("SUPERSEDED", "ARCHIVAL-NOTE", "DRAFT", "PREREGISTERED"):
            if kw in t:
                marks.append(kw)
        flag = " ".join(marks) if marks else "-"
        print(f"{p.relative_to('.')}: {flag}")
