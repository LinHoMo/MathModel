#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容 shim：本脚本已迁至 core/tools/rendering/render_ai_usage.py；保留旧命令路径。"""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "rendering" / "render_ai_usage.py"), run_name="__main__")
