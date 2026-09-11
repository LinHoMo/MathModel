#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行程审计守卫测试：把总移动分解为扫描段 / 归航段，并给出归航段的严格下界。

动机（实测）：总时间的 69–73% 是移动，所以「移动花在哪」比「几何好不好」更根本。
审计口径：
  - 扫描段 = 点集的最近邻路径长度（纯几何量，与运行无关）；
  - 归航段 = 实测总移动 − 扫描段；
  - 下界   = 源位置的 **MST 权重**（TSP 的经典下界——清除行程至少要连通所有源）；
  - 冗余倍数 = 归航段 / 下界。
零依赖、纯计算，故可直接单测。

运行: python -m pytest test_travel_audit.py -q
"""
from __future__ import annotations

import pytest

from travel_audit import audit_travel, mst_weight, nn_route_length


def test_nn_route_length_simple():
    assert nn_route_length([(0.0, 0.0), (3000.0, 0.0)], (0.0, 0.0)) == pytest.approx(3000.0)
    assert nn_route_length([], (0.0, 0.0)) == 0.0


def test_mst_weight_simple():
    # 三点共线等距 1000 → MST = 2000
    assert mst_weight([(0.0, 0.0), (1000.0, 0.0), (2000.0, 0.0)]) == pytest.approx(2000.0)
    assert mst_weight([(0.0, 0.0)]) == 0.0
    assert mst_weight([]) == 0.0


def test_audit_splits_scan_and_engage():
    out = audit_travel(total_move_m=25878.0,
                       points=[(0.0, 0.0), (3000.0, 0.0)],
                       sources=[(1000.0, 0.0), (2000.0, 0.0)])
    assert out["scan_m"] == pytest.approx(3000.0)
    assert out["engage_m"] == pytest.approx(25878.0 - 3000.0)
    assert out["sources_mst_lower_bound_m"] == pytest.approx(1000.0)
    assert out["engage_over_lower_bound"] == pytest.approx((25878.0 - 3000.0) / 1000.0)


def test_zero_lower_bound_does_not_divide_by_zero():
    """单个源 → MST=0；此时倍数须为 None（不可比），不得抛异常或报 inf 冒充数值。"""
    out = audit_travel(total_move_m=100.0, points=[(0.0, 0.0)],
                       sources=[(5.0, 5.0)])
    assert out["sources_mst_lower_bound_m"] == 0.0
    assert out["engage_over_lower_bound"] is None


def test_share_of_total_reported():
    out = audit_travel(total_move_m=1000.0, points=[(0.0, 0.0), (400.0, 0.0)],
                       sources=[(0.0, 1.0)])
    assert out["scan_share"] == pytest.approx(0.4)
    assert out["engage_share"] == pytest.approx(0.6)
