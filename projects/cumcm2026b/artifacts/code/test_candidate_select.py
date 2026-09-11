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
import solve_b_http as M


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


# ------------------------------------------ M-SELECT-002：策略对象化 + 信息感知候选
def test_candidate_registry_has_three_strategy_objects():
    """候选注册表是三件**规格对象**（各有 points 几何入口），不再是裸点集。"""
    names = [c["name"] for c in C.CANDIDATES]
    assert names == ["RING", "SPIRAL", "AIFIX"]
    for c in C.CANDIDATES:
        assert callable(c["points"])


def test_aifix_shares_ring_geometry_single_variable_contrast():
    """AIFIX 必须复用 RING 点集：对照的唯一变量是「何时 engage」。

    M-SELECT-001 的教训——给候选配不同的几何会得出假结论（spiral 首版忽略
    has_directional 导致 Q4 假淘汰）。AIFIX 用同一份 ring_points 消除该风险。
    """
    assert C.AIFIX_CAND["points"] is C.RING_CAND["points"]
    assert C.AIFIX_CAND.get("sweeper") is M.interleaved_sweeper
    assert C.RING_CAND.get("sweeper") is None


def test_interleaved_sweeper_signature_matches_hook():
    """sweeper 策略对象的形参必须与 dog_strategy_http 的调用点一致。"""
    import inspect
    swp = inspect.signature(M.interleaved_sweeper).parameters
    for p in ("sim", "obs", "det_time", "clear_time", "has_directional", "points"):
        assert p in swp, f"interleaved_sweeper 缺形参 {p}"
    assert "sweeper" in inspect.signature(M.dog_strategy_http).parameters


# ------------------------------------------------------------- select_best 语义
def _agg2(cleared, t):
    return {"cleared_fraction": cleared, "T_total_s": t}


def test_select_best_feasibility_filters_before_objective():
    """最快的候选若不可行，必须被淘汰、不参与目标比较。"""
    aggs = {"RING": _agg2(1.0, 10000.0), "SPIRAL": _agg2(1.0, 8000.0),
            "AIFIX": _agg2(0.5, 1.0)}
    dec = C.select_best(aggs, paired={("SPIRAL", "RING"):
                                      {"delta_mean_s": -2000.0,
                                       "delta_ci95_halfwidth_s": 100.0}})
    assert dec["gate"]["rejected"] == ["AIFIX"]
    assert dec["winner"] == "SPIRAL"


def test_select_best_inconclusive_when_within_noise():
    aggs = {"RING": _agg2(1.0, 10000.0), "SPIRAL": _agg2(1.0, 9600.0)}
    dec = C.select_best(aggs, paired={("RING", "SPIRAL"):
                                      {"delta_mean_s": 400.0,
                                       "delta_ci95_halfwidth_s": 900.0}})
    assert dec["winner"] == "INCONCLUSIVE"
    assert dec["objective"]["within_noise"] is True
    assert dec["checks_passed_used"] is False


def test_select_best_ranks_and_picks_significant_winner():
    aggs = {"RING": _agg2(1.0, 10000.0), "SPIRAL": _agg2(1.0, 8000.0),
            "AIFIX": _agg2(1.0, 9000.0)}
    dec = C.select_best(aggs, paired={("SPIRAL", "RING"):
                                      {"delta_mean_s": -2000.0,
                                       "delta_ci95_halfwidth_s": 100.0}})
    assert dec["ranked"] == ["SPIRAL", "AIFIX", "RING"]
    assert dec["winner"] == "SPIRAL"
    assert dec["objective"]["abs_gap"] == pytest.approx(-1000.0)


def test_select_best_all_infeasible_yields_none():
    dec = C.select_best({"A": _agg2(0.5, 10.0), "B": _agg2(0.6, 9.0)})
    assert dec["winner"] == "NONE" and dec["stage"] == "feasibility"


def test_paired_between_sign_and_winrate():
    rows = [{"seed": 42, "A": {"T_total_s": 100.0}, "B": {"T_total_s": 90.0}},
            {"seed": 43, "A": {"T_total_s": 110.0}, "B": {"T_total_s": 100.0}}]
    st = C.paired_between(rows, "A", "B")
    assert st["delta_mean_s"] == pytest.approx(10.0)   # Δ = A − B > 0 ⇒ A 更慢
    assert st["B_win_rate"] == 1.0
    assert st["A_win_rate"] == 0.0
