"""P4 evaluation.scoring 桥接层测试：稳定 import 面 + 与 core/tools 单实例。

运行: python -m pytest tests/unit/test_evaluation_bridge.py -q
覆盖任务书: P4「evaluation/scoring 转发（原位或转发）」。
"""

import importlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest


class TestBridgeImports:
    def test_package_importable(self):
        from evaluation import scoring
        assert scoring is not None

    def test_four_modules_mapped(self):
        from evaluation import scoring
        for name in ("score_compute", "aggregate_scores",
                     "score_artifact", "weight_profiles"):
            assert hasattr(scoring, name), f"缺少转发: {name}"

    def test_key_apis_reexported(self):
        from evaluation import scoring
        # weight_profiles
        assert callable(scoring.get_weights)
        # aggregate_scores / score_artifact 公开函数
        for fn in ("load_cards", "build", "resolve_weights"):
            assert callable(getattr(scoring.aggregate_scores, fn, None)), \
                f"aggregate_scores.{fn} 缺失"
        for fn in ("compute", "decide", "merge_blocking"):
            assert callable(getattr(scoring.score_artifact, fn, None)), \
                f"score_artifact.{fn} 缺失"
        # score_compute 五维
        for fn in ("compute_academic", "compute_engineering", "compute_judge",
                   "compute_reader", "compute_adversarial"):
            assert callable(getattr(scoring.score_compute, fn, None)), \
                f"score_compute.{fn} 缺失"

    def test_get_weights_works(self):
        from evaluation import scoring
        w = scoring.get_weights("C")
        assert isinstance(w, dict) and w
        # 权重归一（±0.01 容差）
        assert abs(sum(w.values()) - 1.0) < 0.01


class TestSingleInstance:
    def test_bridge_reuses_tools_import(self):
        """若 core/tools 模块已按 sys.path 方式导入，桥接必须复用同一实例。"""
        sys.path.insert(0, str(REPO / "core" / "tools"))
        import weight_profiles as WP_direct
        from evaluation import scoring
        assert scoring.weight_profiles is WP_direct, \
            "桥接产生了双实例（core/tools 与 evaluation.scoring 各一份）"

    def test_cross_module_bare_import_resolved(self):
        """aggregate_scores 内部 `import weight_profiles` 裸名互引必须可用。"""
        from evaluation import scoring  # noqa: F401 — 触发桥接加载与 sys.path 就位
        tools_dir = str(REPO / "core" / "tools")
        assert tools_dir in sys.path
        import weight_profiles  # 裸名导入（aggregate_scores 内部同样写法）
        assert callable(weight_profiles.get_weights)
