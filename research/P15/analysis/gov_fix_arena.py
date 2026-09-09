# -*- coding: utf-8 -*-
"""arena_runner question=None 修正。"""
from pathlib import Path

p = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\arena\arena_runner.py")
s = p.read_text(encoding="utf-8")
old = 'adapter=LocalPythonAdapter(), question="Q001")'
new = "adapter=LocalPythonAdapter())"
assert old in s, "pattern not found"
p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("question=None OK")
