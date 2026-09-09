# -*- coding: utf-8 -*-
"""提取两份 audit 报告的『差距』段落与结论"""
from pathlib import Path
import re

for name in ["_audit_A_upstream.md", "_audit_B_downstream.md"]:
    t = Path(f"research/P15/analysis/{name}").read_text(encoding="utf-8")
    print(f"\n{'='*70}\n== {name} （{len(t)} 字符）\n{'='*70}")
    # 抓取每个环节标题和它下面的第 10 问（差距）或任何“差”字结论
    # 环节标题：## 环节N xxx
    for m in re.finditer(r"## 环节(\d+)\s+([^\n]+)", t):
        num, title = m.group(1), m.group(2).strip()
        seg_end = t.find("\n## ", m.end())
        seg = t[m.end():seg_end if seg_end != -1 else len(t)]
        # 找“差距”或“结论”行
        gap_lines = []
        for line in seg.splitlines():
            if re.search(r"差距|缺|not demonstrated|not found|无 |不存在|仅|空壳|死代码|硬编码|占位", line):
                gap_lines.append(line.strip()[:130])
        print(f"\n--- 环节{num} {title}")
        for g in gap_lines[:6]:
            print(f"    {g}")
