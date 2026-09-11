#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M-SELECT-003 守卫测试：候选池的边际价值 —— 「先验锁死一个候选」要付多少代价。

动机：ADR-0016 核验出 `handlers.py:1876-1879` 只取 `cands[0]`（先验分第 0 名），
其余候选从未执行。本模块用 M-SELECT-002 的真实逐 seed 数据量化**这个机制的代价**：
若候选池被先验锁死为单一候选，与「全池都跑过、按期望选」相比差多少。

口径（ADR-0012：跨实现比较前必须归一口径）
------------------------------------------
真实场景必须在**看到 seed 之前**选定一个候选，故可比量是候选的**期望 T_total**
（mean over seeds）；per-seed 最优是信息泄漏下的下界，**不得**当作成绩。
（M-SELECT-002 数据里 Q4 seed42 最快的候选与聚合后最优的候选并不是同一个，
正是这条口径重要性的实证。）

显著性：差距必须与配对 95% CI 比。落在 CI 内 ⇒ 如实标 inconclusive，
不得把噪声报成「损失」。

运行: python -m pytest test_pool_value.py -q
"""
from __future__ import annotations

import pytest

from pool_value import pool_value


def _q(cands: dict, paired: dict | None = None) -> dict:
    """构造单个问题的 M-SELECT-002 风格数据。"""
    return {
        "candidates": {n: {"T_total_s": t, "cleared_fraction": 1.0}
                       for n, t in cands.items()},
        "paired": paired or {},
    }


def test_best_candidate_is_argmin_of_mean_not_per_seed_oracle():
    """最优候选按**期望**取，不看 per-seed 最优。"""
    q = _q({"RING": 10622.9, "SPIRAL": 8593.7, "AIFIX": 10137.0})
    out = pool_value({"q4_mix": q})
    assert out["q4_mix"]["best_candidate"] == "SPIRAL"
    assert out["q4_mix"]["best_mean_T"] == pytest.approx(8593.7)


def test_single_pool_penalty_computed_and_significant():
    """锁定为最差候选时的代价：绝对/相对（两个口径都要）与显著性。"""
    q = _q({"RING": 10622.9, "SPIRAL": 8593.7, "AIFIX": 10137.0},
           paired={"RING|SPIRAL": {"delta_mean_s": 2029.2,
                                   "delta_ci95_halfwidth_s": 663.1}})
    out = pool_value({"q4_mix": q})["q4_mix"]
    w = out["worst_single_pool"]
    assert w["candidate"] == "RING"
    assert w["abs_loss_s"] == pytest.approx(2029.2)
    assert w["rel_loss_vs_best"] == pytest.approx(2029.2 / 8593.7, rel=1e-6)
    assert w["rel_loss_vs_self"] == pytest.approx(2029.2 / 10622.9, rel=1e-6)
    assert w["significant"] is True


def test_loss_within_ci_is_marked_inconclusive():
    """差距落在配对 CI 内 ⇒ 如实标不显著，不得报成「损失」。"""
    q = _q({"RING": 6597.9, "SPIRAL": 7132.9},
           paired={"RING|SPIRAL": {"delta_mean_s": -535.0,
                                   "delta_ci95_halfwidth_s": 1022.2}})
    out = pool_value({"q3_omni": q})["q3_omni"]
    w = out["worst_single_pool"]
    assert w["candidate"] == "SPIRAL"
    assert w["abs_loss_s"] == pytest.approx(535.0)
    assert w["significant"] is False, "535.0 落在 ±1022.2 内，必须标不显著"


def test_subsets_enumerated_with_gap_vs_full_pool():
    """全部子集枚举（3 候选 → 7 个子集），每个给出相对全池的差距。"""
    q = _q({"RING": 10622.9, "SPIRAL": 8593.7, "AIFIX": 10137.0},
           paired={"RING|SPIRAL": {"delta_mean_s": 2029.2,
                                   "delta_ci95_halfwidth_s": 663.1},
                   "AIFIX|SPIRAL": {"delta_mean_s": 1543.3,
                                    "delta_ci95_halfwidth_s": 1700.2}})
    out = pool_value({"q4_mix": q})["q4_mix"]
    pools = {"|".join(s["pool"]): s for s in out["subsets"]}
    assert len(out["subsets"]) == 7
    assert pools["RING"]["abs_gap_vs_full_s"] == pytest.approx(2029.2)
    assert pools["RING"]["significant"] is True
    assert pools["AIFIX"]["significant"] is False, "1543.3 落在 ±1700.2 内"
    assert pools["SPIRAL"]["abs_gap_vs_full_s"] == pytest.approx(0.0)


def test_empty_input_is_safe():
    assert pool_value({}) == {}
