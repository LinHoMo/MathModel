#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容 shim：实现位于 core/tools/validation/writing_check.py。

- CLI:  python core/tools/writing_check.py ...      （AGENTS.md 协议命令不受影响）
- import: from core.tools.writing_check import x  （转发到新位置，共享同一命名空间）
"""
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parent / "validation" / "writing_check.py"

if __name__ == "__main__":
    import runpy
    runpy.run_path(str(_TARGET), run_name="__main__")
else:
    # import 转发：把实现文件 exec 进本模块的 globals ——
    # 函数的 __globals__ 与本模块同一命名空间，monkeypatch / 属性访问全部生效；
    # __file__ 必须指向实现文件，否则实现里基于 __file__ 的 ROOT 推导会错位
    globals()["__file__"] = str(_TARGET)
    exec(compile(_TARGET.read_text(encoding="utf-8"), str(_TARGET), "exec"), globals())
