# -*- coding: utf-8 -*-
import os, json

DEST = r"C:/Users/Lin/Desktop/Programs/MathModel/research/REPOSITORY_AUDIT/src"

total_lines = 0
total_bytes = 0
md_lines = 0
py_lines = 0
skill_md = []
for root, dirs, files in os.walk(DEST):
    for fn in files:
        p = os.path.join(root, fn)
        try:
            with open(p, encoding='utf-8', errors='ignore') as f:
                n = sum(1 for _ in f)
            b = os.path.getsize(p)
        except Exception:
            continue
        total_lines += n
        total_bytes += b
        if fn.endswith('.md'):
            md_lines += n
        if fn.endswith('.py'):
            py_lines += n
        if fn == 'SKILL.md':
            rel = os.path.relpath(p, DEST)
            skill_md.append((rel, n))

print("text files lines total:", total_lines)
print("md lines:", md_lines)
print("py lines:", py_lines)
print("total bytes (text subset):", total_bytes)
print("--- SKILL.md files (unique dirs, excluding dupes):")
seen = set()
for rel, n in sorted(skill_md):
    # mark duplicates by basename+size heuristic
    print("%6d  %s" % (n, rel))
