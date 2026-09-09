# -*- coding: utf-8 -*-
"""audit Batch7 P2（续）：supersedes 单一真源。

_register_mir 的 rev_of 分支只登记 revision_of 谱系边；
supersedes 边与状态迁移由 finalize_revision（registry.supersede 配套）
唯一负责——避免双路径重复加边（GraphError: 关系已存在）。
"""
from pathlib import Path

p = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\core\runtime\execution\handlers.py")
s = p.read_text(encoding="utf-8")

old = """        self.graph.add_relation(art.artifact_id, "instantiates", mid)
        if rev_of:
            target = self.registry.get(rev_of)
            if target is not None and target.type == "model_ir":
                # audit Batch7 P2：supersedes 方向统一为「新 → 旧」
                # （FIX-6.3：registry.supersede(M1, replacement=M2) 语义），
                # 旧实现 (rev_of, supersedes, art) 方向矛盾，已修正。
                self.graph.add_relation(art.artifact_id, "revision_of", rev_of)
                self.graph.add_relation(art.artifact_id, "supersedes", rev_of)
        return art.artifact_id"""

new = """        self.graph.add_relation(art.artifact_id, "instantiates", mid)
        if rev_of:
            target = self.registry.get(rev_of)
            if target is not None and target.type == "model_ir":
                # audit Batch7 P2：本处只登记 revision_of 谱系边；
                # supersedes 边 + 旧模型状态迁移由修订收口唯一负责
                # （vs001_driver.finalize_revision：registry.supersede(M1,
                # replacement=M2) + graph.add_relation(M2, supersedes, M1)）
                # ——单一真源，避免双路径重复加边（GraphError）。
                self.graph.add_relation(art.artifact_id, "revision_of", rev_of)
        return art.artifact_id"""

assert old in s, "pattern not found"
p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("supersedes single-source OK")
