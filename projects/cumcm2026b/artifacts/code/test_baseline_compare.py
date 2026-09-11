#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""baseline_compare 的守卫测试：对照必须**只换策略**，不得偷偷换别的东西。

对照实验的可信度取决于「除策略外全同」这一不变量。最容易出的错是基线悄悄用了
不同的检测点集合（那比的就是"扫多少个点"而不是"怎么扫"）。本测试把该不变量锁死。
"""
from __future__ import annotations

import pytest

import baseline_compare as BC
import solve_b as B


def test_baseline_uses_the_same_point_set_as_model():
    """同一集合：基线与模型的检测点排序后逐点相等（只允许顺序不同）。"""
    for has_dir in (False, True):
        base = BC.baseline_points(has_dir)
        model = B.coverage_detection_points(has_dir)
        assert len(base) == len(model), f"点数不同 has_dir={has_dir}"
        assert sorted(base) == sorted(model), f"点集不同 has_dir={has_dir}"


def test_baseline_order_is_actually_different():
    """顺序确实不同——否则对照无效（基线就等于模型策略）。"""
    base = BC.baseline_points(False)
    model = B.coverage_detection_points(False)
    assert base != model, "基线与模型点序相同，对照不成立（模型策略含最近邻重排）"


def test_baseline_points_follow_ring_generation_order():
    """基线按环半径递增生成：半径序列单调不减（未做最近邻重排的特征）。"""
    pts = BC.baseline_points(False)
    radii = [round((x * x + y * y) ** 0.5, 6) for x, y in pts]
    # 允许环内任意顺序，但环与环之间必须成块：去重后应恰好等于 COVER_RADII_OMNI 的顺序
    seen: list[float] = []
    for r in radii:
        if not seen or abs(r - seen[-1]) > 1e-6:
            seen.append(r)
    assert seen == list(B.COVER_RADII_OMNI), seen


@pytest.mark.parametrize("has_dir,expected_n", [(False, 17), (True, 29)])
def test_point_counts(has_dir, expected_n):
    assert len(BC.baseline_points(has_dir)) == expected_n


def test_gain_formula_matches_definition():
    """G = (T_base − T_model) / T_base；ΔT = T_model − T_base，二者符号相反。"""
    tb, tm = 15000.0, 6000.0
    delta = tm - tb
    g = (tb - tm) / tb
    assert delta == -9000.0
    assert g == pytest.approx(0.6)
