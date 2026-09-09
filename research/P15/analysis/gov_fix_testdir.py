# -*- coding: utf-8 -*-
"""修正 test_full_loop_persisted 中 supersedes 旧方向断言（FIX-6.3 新→旧）。"""
from pathlib import Path

p = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\tests\integration\test_p1_vs001_e2e.py")
s = p.read_text(encoding="utf-8")

old = '        assert ("MIR001", "supersedes", "MIR002") in rels'
new = '        assert ("MIR002", "supersedes", "MIR001") in rels  # FIX-6.3：新取代旧'

assert old in s, "pattern not found"
p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("test assertion direction fixed")
