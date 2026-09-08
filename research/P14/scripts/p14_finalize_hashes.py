#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""p14_finalize_hashes.py — 为 run 目录中 content_sha256 缺失/为 null 的实体计算并写入规范 hash。

只做机械计算，不定义语义（约定见 RUNBOOK_P14_1.md §4）。
用法: python p14_finalize_hashes.py <run_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p14_integrity_gate import TYPE_DIRS, canonical_hash  # noqa: E402


def main() -> None:
    run = Path(sys.argv[1])
    n = 0
    for sub in TYPE_DIRS.values():
        d = run / sub
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            e = json.loads(f.read_text(encoding="utf-8"))
            if e.get("content_sha256") is None:
                e["content_sha256"] = canonical_hash(e)
                f.write_text(json.dumps(e, ensure_ascii=False, indent=2), encoding="utf-8")
                n += 1
                print(f"  + {f.relative_to(run)}")
    print(f"finalized {n} entity hashes in {run}")


if __name__ == "__main__":
    main()
