# -*- coding: utf-8 -*-
"""Capability Validation（Δscore）固化测试。

验证：P1 执行级指标统计是机器事实（VR failed 被计为 FAIL、修订谱系边存在），
八项指标对比表 schema 正确（None = 该期无对应产物，如实不估算）。
"""

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from research.P15.analysis.capability_delta import (  # noqa: E402
    _load_gt,
    _p1_loop_metrics,
    eight_metric_delta,
)


def test_p1_loop_metrics_are_mechanical():
    """P1 执行级指标必须来自 registry/graph 真实统计（vs001 产物）。"""
    loop = _p1_loop_metrics()
    assert loop["execution_success_rate"] == 1.0
    assert loop["validation_total"] == 3
    # M1 缺陷模型被真实数值验证拦截（VR002=failed），不得被计为 0
    assert loop["validation_fail_observed"] == 1
    # 修订谱系：M2 revision_of M1 + supersede 边存在
    assert loop["revision_lineage_edges"] >= 1
    assert loop["supersede_edges"] >= 1


def test_eight_metric_delta_schema():
    """八项指标表：None 表示该期无对应产物，不估算为 0。"""
    delta = eight_metric_delta()
    assert len(delta["rows"]) == 8
    for r in delta["rows"]:
        assert r["metric"] and r["label"]
        if r["pre"] is not None and r["post"] is not None:
            assert r["delta"] is not None
        # None 保持 None（诚实口径），不得被替换成 0
        assert r["pre"] is None or isinstance(r["pre"], (int, float))
        assert r["post"] is None or isinstance(r["post"], (int, float))


def test_gt_2024a_loads():
    """gt 载入正常（Δscore 与 2024_A 题卡绑定）。"""
    gt = _load_gt()
    assert gt.get("problem_id") == "2024_A"
    assert "allowed_modeling_structures" in gt
