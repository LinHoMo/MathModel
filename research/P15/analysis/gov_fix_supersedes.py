# -*- coding: utf-8 -*-
"""audit Batch7 P2：修正 _register_mir 中 supersedes 方向矛盾（新→旧）。"""
from pathlib import Path

p = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\core\runtime\execution\handlers.py")
s = p.read_text(encoding="utf-8")

old = """                self.graph.add_relation(art.artifact_id, "revision_of", rev_of)
                self.graph.add_relation(rev_of, "supersedes", art.artifact_id)"""

new = """                # audit Batch7 P2：supersedes 方向统一为「新 → 旧」
                # （FIX-6.3：registry.supersede(M1, replacement=M2) 语义），
                # 旧实现 (rev_of, supersedes, art) 方向矛盾，已修正。
                self.graph.add_relation(art.artifact_id, "revision_of", rev_of)
                self.graph.add_relation(art.artifact_id, "supersedes", rev_of)"""

assert old in s, "pattern not found"
p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("supersedes direction fixed")
