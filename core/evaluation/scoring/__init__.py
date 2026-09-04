"""evaluation.scoring — 评分工具稳定 import 面（P4 桥接层）。

四个评分模块的迁移映射（P4 原位桥接 → P5 实现迁入）:

    core/tools/score_compute.py     → evaluation.scoring.score_compute
    core/tools/aggregate_scores.py  → evaluation.scoring.aggregate_scores
    core/tools/score_artifact.py    → evaluation.scoring.score_artifact
    core/tools/weight_profiles.py   → evaluation.scoring.weight_profiles

P4: 实现不动，本包从 core/tools/ 动态加载并 re-export（若模块已按
    core/tools sys.path 方式导入则直接复用，避免双实例）。
P5: 实现迁入本包后，core/tools/<name>.py 变为 CLI 薄转发，
    下游 import 面不变。

用法:
    from evaluation.scoring import weight_profiles
    weights = weight_profiles.get_weights("C")
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_TOOLS = _REPO / "core" / "tools"

# 模块间存在裸名互引（aggregate_scores 内 `import weight_profiles`），
# 加载时须保证 core/tools 在 sys.path 上。
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

_MODULE_FILES = ("score_compute", "aggregate_scores",
                 "score_artifact", "weight_profiles")


def _load(name: str):
    """按文件路径加载 core/tools/<name>.py；已在 sys.modules 则复用。"""
    if name in sys.modules:
        return sys.modules[name]
    path = _TOOLS / f"{name}.py"
    if not path.is_file():
        raise ImportError(f"评分模块不存在: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


score_compute = _load("score_compute")
aggregate_scores = _load("aggregate_scores")
score_artifact = _load("score_artifact")
weight_profiles = _load("weight_profiles")

# 常用 API 直接挂到包面上（下游可不感知子模块）
get_weights = weight_profiles.get_weights

__all__ = [
    "score_compute", "aggregate_scores", "score_artifact", "weight_profiles",
    "get_weights",
]
