#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""solve_b.py 覆盖扫描优化回归测试（RED→GREEN 证据）。

工单目标：
  1. 覆盖扫描点加入最近邻路线排序，减少点间行程；
  2. 在覆盖完备性不劣化前提下放大弧向步长以减少检测点数；
  3. coverage_validation（20000 随机源）漏检率：全向必须为 0，定向不劣于基线。

运行：`py -3.12 -X utf8 -m pytest test_solve_b_cover_opt.py -q`

为何放在产物目录而非 harness `tests/`：solve_b.py 依赖 numpy，而 harness CI
测试环境仅装 ruff/pytest/pyyaml/jsonschema（零运行时依赖边界），放进 tests/ 会
令 CI 采集失败。此处与产物同目录，按需显式运行。
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solve_b as S  # noqa: E402

# 优化前基线（实测，seed=7）：全向 27 点 / 定向 69 点；定向漏检 2.5e-4（=5/20000）
BASE_OMNI_PTS = 27
BASE_DIR_PTS = 69
BASE_DIR_MISS_MAX = 0.00025


def _path_len(pts, start=(0.0, 0.0)):
    """按给定顺序从 start 依次经过的累计行程。"""
    cur, d = start, 0.0
    for p in pts:
        d += math.dist(cur, p)
        cur = p
    return d


def _nn_len(pts, start=(0.0, 0.0)):
    """贪心最近邻排序后的行程（作为「最短可达」参照）。"""
    rem, cur, d = list(pts), start, 0.0
    while rem:
        j = min(range(len(rem)), key=lambda i: math.dist(cur, rem[i]))
        d += math.dist(cur, rem[j])
        cur = rem.pop(j)
    return d


@pytest.mark.parametrize("has_dir,limit,base", [
    (False, 20, BASE_OMNI_PTS),
    (True, 52, BASE_DIR_PTS),
])
def test_cover_point_count_reduced(has_dir, limit, base):
    """放大弧向步长后检测点数必须显著下降（当前基线 27/69）。"""
    n = len(S.coverage_detection_points(has_dir))
    assert n < base, f"点数未下降：{n} >= 基线 {base}"
    assert n <= limit


@pytest.mark.parametrize("has_dir", [False, True])
def test_cover_route_is_nearest_neighbour(has_dir):
    """返回点序的行程应≈最近邻最优（优化前按环原始顺序，行程偏高）。"""
    pts = S.coverage_detection_points(has_dir)
    given = _path_len(pts)
    best = _nn_len(pts)
    assert given <= best * 1.02, (
        f"扫描路线未做最近邻排序：行程 {given:.1f} 远高于最近邻 {best:.1f}")


def test_coverage_completeness_omni_zero_and_dir_not_worse():
    """覆盖完备性：20000 随机源，全向漏检必须为 0，定向不劣于基线。"""
    v = S.coverage_validation(n=20000, seed=7)
    assert v["omni_miss_ratio"] == 0.0
    assert v["dir_miss_ratio"] <= BASE_DIR_MISS_MAX


def test_ring_detection_points_contract_unchanged():
    """ring_detection_points / coverage_detection_points 返回 list[(x,y)]。"""
    for pts in (S.ring_detection_points(450.0, 500.0),
                S.coverage_detection_points(False),
                S.coverage_detection_points(True)):
        assert isinstance(pts, list)
        assert all(isinstance(p, tuple) and len(p) == 2 for p in pts)
