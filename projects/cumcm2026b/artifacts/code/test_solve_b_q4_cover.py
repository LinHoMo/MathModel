#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q4（混合定向源）覆盖检测点重构回归测试 —— RED→GREEN 证据。

工单目标：在「环绕完备性不劣化」前提下，把 Q4 覆盖检测点从 50 降到 33 站量级。

RED（改动前）：`test_q4_cover_points_within_target` 与
`test_boundary_outward_directional_source_covered` 失败——旧定向覆盖环
{1200, 1799} 共 33 点（合计 50）；且贴区域边界、波束朝圆外的定向源在旧策略下无解，
因为「检测点落在源环内侧时不可能落进朝外波束」。

GREEN（改动后）：定向覆盖环改为 {450, 1350, 2000}，外侧环 2000 m 位于源分布环之外，
朝外波束在该环上有宽得多的角接受窗，弧向步长可按角色分级放大；合计 29 点，
20000 随机源定向漏检 0。

运行：`py -3.12 -X utf8 -m pytest test_solve_b_q4_cover.py -q`
（与 solve_b 同目录：solve_b 依赖 numpy，不进 harness CI 测试目录。）
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solve_b as S  # noqa: E402

BASE_DIR_PTS = 50        # 改动前实测（coverage_detection_points(True)）
TARGET_DIR_PTS = 33      # b_win 参照量级
DIR_MISS_MAX = 0.00025   # 工单给定的定向漏检率上限


def _visible(pts, x, y, rrec, hd):
    """按 coverage_validation 的可测判据判定：距离 ≤ rrec 且落在波束 ±90° 内。"""
    for (px, py) in pts:
        if math.dist((px, py), (x, y)) <= rrec:
            a = math.degrees(math.atan2(py - y, px - x)) % 360.0
            if abs(((a - hd + 180.0) % 360.0) - 180.0) <= 90.0:
                return True
    return False


def test_q4_cover_points_within_target():
    """Q4 覆盖检测点数必须降到 33 站量级，且少于改动前的 50。"""
    n = len(S.coverage_detection_points(True))
    assert n < BASE_DIR_PTS, f"Q4 覆盖检测点未下降：{n} >= {BASE_DIR_PTS}"
    assert n <= TARGET_DIR_PTS, f"Q4 覆盖检测点 {n} 高于目标 {TARGET_DIR_PTS}"


def test_boundary_outward_directional_source_covered():
    """贴区域边界、波束朝圆外的定向源必须被覆盖（仅能从源分布环外侧测向）。"""
    pts = S.coverage_detection_points(True)
    for rho in (1780.0, 1795.0, 1799.5, 1800.0):
        for k in range(0, 360, 5):
            ang = math.radians(float(k))
            x, y = rho * math.cos(ang), rho * math.sin(ang)
            assert _visible(pts, x, y, S.R_REC_MIN, float(k)), (
                f"朝外定向源 (rho={rho}, 径向={k}°) 未被任何检测点覆盖")


def test_omni_rings_unchanged_and_complete():
    """全向覆盖环不变、全向漏检为 0（定向改造不得动摇全向完备性定理）。"""
    assert tuple(S.COVER_RADII_OMNI) == (450.0, 1350.0)
    v = S.coverage_validation(n=20000, seed=7)
    assert v["omni_miss_ratio"] == 0.0


def test_dir_coverage_not_worse_than_spec():
    """20000 随机源（seed=7）定向漏检率不劣于 0.00025。"""
    v = S.coverage_validation(n=20000, seed=7)
    assert v["dir_miss_ratio"] <= DIR_MISS_MAX


def test_public_signatures_unchanged():
    """solve_b_http.py import 的公共函数签名与返回类型不得改变。"""
    import inspect
    assert str(inspect.signature(S.coverage_detection_points)) == "(has_directional=False)"
    assert str(inspect.signature(S.ring_detection_points)) == "(radius, step)"
    assert str(inspect.signature(S.nn_route)) == "(points, start=(0.0, 0.0))"
    for pts in (S.ring_detection_points(450.0, 500.0),
                S.coverage_detection_points(False),
                S.coverage_detection_points(True)):
        assert isinstance(pts, list)
        assert all(isinstance(p, tuple) and len(p) == 2 for p in pts)
