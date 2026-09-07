#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容 shim：实现位于 core/tools/evaluation/run_p13_3d.py。

- CLI:  python core/tools/run_p13_3d.py ...
"""
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parent / "evaluation" / "run_p13_3d.py"

if __name__ == "__main__":
    import runpy
    runpy.run_path(str(_TARGET), run_name="__main__")
else:
    globals()["__file__"] = str(_TARGET)
    exec(compile(_TARGET.read_text(encoding="utf-8"), str(_TARGET), "exec"), globals())
