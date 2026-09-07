#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容 shim：实现位于 core/tools/evaluation/fidelity_gate.py。

- CLI:  python core/tools/fidelity_gate.py ...      （AGENTS.md 协议命令不受影响）
- import: from core.tools.fidelity_gate import x  （转发到新位置）
"""
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parent / "evaluation" / "fidelity_gate.py"

if __name__ == "__main__":
    import runpy
    runpy.run_path(str(_TARGET), run_name="__main__")
else:
    globals()["__file__"] = str(_TARGET)
    exec(compile(_TARGET.read_text(encoding="utf-8"), str(_TARGET), "exec"), globals())
