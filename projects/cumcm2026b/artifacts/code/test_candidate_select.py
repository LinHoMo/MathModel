#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M-SELECT-001 守卫测试：候选淘汰机制的九条验收标准。

这轮实验的目的不是"证明螺旋更聪明"，而是证明
「提出候选 → 执行 → 取 objective → 比较 → 淘汰」这条机制真的能在真实任务上工作。
本测试把该机制的**判定语义**锁死（几何与执行部分由 candidate_select 的运行产物负责）。
"""
from __future__ import annotations

import pytest

import candidate_select as C
import solve_b as B


# ------------------------------------------------------- 独立性 / 同一协议
def test_two_candidates_are_genuinely_different_geometry():
    """候选 A/B 必须是机制不同的覆盖几何，而不是同一套换个名字。"""
    ring = C.ring_points(False)
    spiral = C.spiral_for(False)
    assert sorted(ring) != sorted(spiral), "两候选点集相同，不构成两个模型候选"
    # 螺旋是连续路径（相邻点半径单调递增）；同心环不是
    radii = [(x * x + y * y) ** 0.5 for x, y in spiral]
    assert all(b >= a - 1e-6 for a, b in zip(radii, radii[1:])), "螺旋应沿半径单调外扩"


def test_both_candidates_are_coverage_complete():
    """两个候选都必须**合理**：覆盖完备（到最近检测点 < r_rec_min），不得是陪跑。"""
    for label, pts in (("RING", C.ring_points(False)),
                       ("SPIRAL", C.spiral_for(False))):
        r = C.coverage_radius(pts, radius=B.R_AREA, n_theta=121, n_rho=61)
        assert r < 1000.0, f"{label} 覆盖不完备（{r:.1f} m ≥ 1000 m）"


def test_directional_variants_both_extend_beyond_source_disk():
    """含定向源时两候选都要有分布区之外的几何，否则比较对其中一方不公平。"""
    for label, pts in (("RING", C.ring_points(True)),
                       ("SPIRAL", C.spiral_for(True))):
        assert max((x * x + y * y) ** 0.5 for x, y in pts) > B.R_AREA, \
            f"{label} 在定向场景没有外扩几何"


# --------------------------------------------------------------- 选择器语义
def _agg(cleared: float, t: float, n_measure: int = 100, move: float = 1000.0):
    return {"cleared_fraction": cleared, "T_total_s": t,
            "n_measure": n_measure, "move_dist_m": move, "n_points": 10}


def _paired(delta, ci, win_a=0.5):
    return {"delta_mean_s": delta, "delta_ci95_halfwidth_s": ci,
            "A_win_rate": win_a, "B_win_rate": 1 - win_a}


def test_feasibility_gate_rejects_before_objective():
    """清除比例不达标的候选直接淘汰，**不参与目标比较**（再快也不能赢）。"""
    dec = C.select("RING", _agg(1.0, 10000.0), "SPIRAL", _agg(0.80, 4500.0),
                   paired=_paired(-5500.0, 100.0))
    assert dec["stage"] == "feasibility"
    assert dec["winner"] == "RING"
    assert dec["gate"]["rejected"] == ["SPIRAL"]


def test_both_infeasible_yields_none():
    dec = C.select("A", _agg(0.5, 100.0), "B", _agg(0.6, 90.0), paired=_paired(-10, 1))
    assert dec["winner"] == "NONE" and dec["stage"] == "feasibility"


def test_objective_picks_lower_time_when_significant():
    dec = C.select("RING", _agg(1.0, 10622.9), "SPIRAL", _agg(1.0, 8593.7),
                   paired=_paired(2029.2, 663.1))
    assert dec["winner"] == "SPIRAL"
    # abs_gap = A − B（正的 2029.2 表示 A 更慢）；winner 取更小者
    assert dec["objective"]["abs_gap"] == pytest.approx(2029.2)
    assert dec["objective"]["better"] == "b"


def test_inconclusive_when_difference_within_noise():
    """核心：均值差落在 95% CI 内 ⇒ 与噪声不可分 ⇒ 不得宣布胜出。"""
    dec = C.select("RING", _agg(1.0, 6597.9), "SPIRAL", _agg(1.0, 7132.9),
                   paired=_paired(-535.0, 1022.2))
    assert dec["winner"] == "INCONCLUSIVE"
    assert dec["objective"]["within_noise"] is True
    assert "跨 0" in dec["reason"]


def test_direction_swap_flips_winner():
    """把目标方向反过来，胜者必须翻转（证明判定真的按方向走，而不是看大小）。"""
    a, b = _agg(1.0, 10000.0), _agg(1.0, 8000.0)
    dec_min = C.select("A", a, "B", b, paired=_paired(2000.0, 100.0))
    assert dec_min["winner"] == "B"          # minimize：时间小者胜
    from modeling_harness.runtime.evaluation.deterministic_metrics import (
        baseline_comparison,
    )
    flipped = baseline_comparison({"T_total_s": a["T_total_s"]},
                                  {"T_total_s": b["T_total_s"]},
                                  direction="maximize")
    assert flipped["better"] == "a"          # maximize：时间大者胜 ⇒ 方向确实生效


def test_selector_does_not_use_checks_passed():
    """ADR-0013：验证检查数不得作为胜负依据，且须在产物中显式声明。"""
    dec = C.select("A", _agg(1.0, 10000.0), "B", _agg(1.0, 8000.0),
                   paired=_paired(2000.0, 100.0))
    assert dec["checks_passed_used"] is False
    assert "checks_passed" not in dec["objective"]


def test_decision_is_machine_readable():
    dec = C.select("A", _agg(1.0, 10000.0), "B", _agg(1.0, 8000.0),
                   paired=_paired(2000.0, 100.0))
    for key in ("stage", "winner", "gate", "objective", "secondary", "reason"):
        assert key in dec
    assert dec["objective"]["paired_ci95_halfwidth_s"] == 100.0
