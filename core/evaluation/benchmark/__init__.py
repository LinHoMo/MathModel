"""evaluation.benchmark — 引擎演练与题库工具稳定 import 面（P5 桥接层）。

两个模块的迁移映射（P5 原位桥接，实现暂留 core/tools/）:

    core/tools/benchmark.py      → evaluation.benchmark.benchmark
    core/tools/bench_mmbench.py  → evaluation.benchmark.bench_mmbench

P5 阶段为桥接（动态加载 + 单实例复用）；后续实现迁入本包时
core/tools/ 侧退化为 CLI 薄转发，import 面不变。

用法:
    from evaluation.benchmark import benchmark
    benchmark.main(["pipeline", "--competition", "cumcm"])
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_TOOLS = _REPO / "core" / "tools"

if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

_MODULE_FILES = ("benchmark", "bench_mmbench")


def _load(name: str):
    """按文件路径加载 core/tools/<name>.py；已在 sys.modules 则复用。"""
    if name in sys.modules:
        return sys.modules[name]
    path = _TOOLS / f"{name}.py"
    if not path.is_file():
        raise ImportError(f"benchmark 模块不存在: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


benchmark = _load("benchmark")
bench_mmbench = _load("bench_mmbench")

__all__ = ["benchmark", "bench_mmbench"]
