"""runtime.adapters — 跨运行时适配工具稳定 import 面（P5 桥接层）。

三个模块的迁移映射（P5 原位桥接，实现暂留 core/tools/）:

    core/tools/gen_runtime_manifest.py  → runtime.adapters.manifest
    core/tools/cloud_sandbox.py         → runtime.adapters.cloud_sandbox
    core/tools/test_runtime_compat.py   → runtime.adapters.runtime_compat

P5 阶段为桥接（动态加载 + 单实例复用）；后续实现迁入本包时
core/tools/ 侧退化为 CLI 薄转发，import 面不变。

注意: gen_runtime_manifest 保留原名加载（`manifest` 仅为别名属性，
其内部以 `gen_runtime_manifest` 名注册 sys.modules，与
tests/unit/test_openai_manifest.py 的 `import gen_runtime_manifest` 单实例一致）。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_TOOLS = _REPO / "core" / "tools"

if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

_MODULE_FILES = ("gen_runtime_manifest", "cloud_sandbox", "test_runtime_compat")


def _load(name: str):
    """按文件路径加载 core/tools/<name>.py；已在 sys.modules 则复用。"""
    if name in sys.modules:
        return sys.modules[name]
    path = _TOOLS / f"{name}.py"
    if not path.is_file():
        raise ImportError(f"adapter 模块不存在: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


manifest = _load("gen_runtime_manifest")
cloud_sandbox = _load("cloud_sandbox")
runtime_compat = _load("test_runtime_compat")

__all__ = ["manifest", "cloud_sandbox", "runtime_compat"]
