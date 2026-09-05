#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容 shim：实现位于 core/tools/runtime/gen_runtime_manifest.py。

- CLI:  python core/tools/gen_runtime_manifest.py ...      （AGENTS.md 协议命令不受影响）
- import: from core.tools.gen_runtime_manifest import x  （转发到新位置）
"""
import runpy
from pathlib import Path

_TARGET = Path(__file__).resolve().parent / "runtime" / "gen_runtime_manifest.py"

if __name__ == "__main__":
    runpy.run_path(str(_TARGET), run_name="__main__")
else:
    _g = runpy.run_path(str(_TARGET), run_name=__name__)
    for _k, _v in _g.items():
        globals().setdefault(_k, _v)
