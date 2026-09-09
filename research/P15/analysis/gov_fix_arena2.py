# -*- coding: utf-8 -*-
"""arena_runner 报告追加验证语义说明。"""
from pathlib import Path

p = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\arena\arena_runner.py")
s = p.read_text(encoding="utf-8")

anchor = '        lines += [""]\n    return "\\n".join(lines)'
addition = (
    '        lines += [""]\n'
    '    lines += [\n'
    '        "## 验证语义说明",\n'
    '        "",\n'
    '        "- `valid` = 通用确定性检查（FIX-5.2：MODEL_IR 声明变量/目标键出现在真实",\n'
    '        "  执行输出 + output_mapping 输出键解析）——**结构级检查，不是数值正确性**；",\n'
    '        "- `cvm`（constraint_violation_max）与 `fidelity_score` 为机械判定（VR/",\n'
    '        "  fidelity 管线）；本 benchmark 不绑定题目特制参考值（无 ground-truth",\n'
    '        "  数值对照），数值正确性验证属于 K003 盲评与题卡 gt 的职责；",\n'
    '        "- 选型决策只基于上表机械证据，无证据不选型（UNSELECTED 如实报告）。",\n'
    '        "",\n'
    "    ]\n"
    '    return "\\n".join(lines)'
)
assert anchor in s, "anchor not found"
p.write_text(s.replace(anchor, addition, 1), encoding="utf-8")
print("verification semantics note added")
