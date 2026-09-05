#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容 shim：本脚本已迁至 core/tools/knowledge/catalog_check.py；保留旧命令路径。"""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "knowledge" / "catalog_check.py"), run_name="__main__")
