#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容 shim：实现位于 core/tools/runtime/replay.py。

- CLI:  python core/tools/replay.py <项目> [verify|list|diff]（命令入口不变）
- import: from core.tools.replay import main（转发生成，共享同一命名空间）
"""

import runpy
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parent / "runtime" / "replay.py"

if __name__ == "__main__":
    sys.exit(runpy.run_path(str(_TARGET), run_name="__main__"))


def main():
    return runpy.run_path(str(_TARGET), run_name="__main__")


__all__ = ["main"]