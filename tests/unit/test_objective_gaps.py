#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADR-0016 Step 3 守卫测试：目标值差距可审计，且**不编造上界**。

背景：Harness 能回答「这个模型对不对」，但答不了「离这个问题可达到的上限还有多远」。
正确落点不是 core 凭空造一个 bound（组合/路径型问题的下界需问题特定松弛），
而是把**可算的**部分结构化落账：

  - chosen 与每个落选候选的 objective gap（复用 baseline_comparison，按方向判优）；
  - 双方任一方 objective_value 不可得 → 如实标 comparable=False（不猜）。

运行: python -m pytest tests/unit/test_objective_gaps.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.modeling.comparison import objective_gaps  # noqa: E402


def test_minimize_gap_sign_and_verdict():
    """chosen 目标值更小（minimize）⇒ abs_gap = chosen − alt < 0，判 chosen 更优。"""
    out = objective_gaps(
        {"objective_value": 900.0, "objective_direction": "minimize"},
        [("M-AAA", {"objective_value": 1200.0})])
    assert len(out) == 1
    g = out[0]
    assert g["model_id"] == "M-AAA"
    assert g["comparable"] is True
    assert g["abs_gap"] == -300.0
    assert g["better"] == "chosen"


def test_maximize_direction_flips_verdict():
    """同一组数字，方向反过来结论必须翻转（否则方向参数没生效）。"""
    out = objective_gaps(
        {"objective_value": 900.0, "objective_direction": "maximize"},
        [("M-AAA", {"objective_value": 1200.0})])
    assert out[0]["better"] == "alternative"
    assert out[0]["abs_gap"] == -300.0     # 仍是 chosen − alt，符号不随方向变


def test_missing_objective_is_incomparable_not_guessed():
    """任一侧 objective_value 不可得 ⇒ 如实标不可比，不得编造差距。"""
    out = objective_gaps(
        {"objective_value": 900.0},
        [("M-X", {}), ("M-Y", {"objective_value": None})])
    assert [g["comparable"] for g in out] == [False, False]
    assert all("objective_value" in g["reason"] for g in out)
    assert all(g["abs_gap"] is None for g in out)


def test_chosen_without_objective_makes_all_incomparable():
    out = objective_gaps({}, [("M-AAA", {"objective_value": 1.0})])
    assert out[0]["comparable"] is False


def test_no_upper_bound_is_fabricated():
    """ADR-0016 决策 4：core 不编造上界——gap 记录里不得出现凭空 bound。"""
    out = objective_gaps(
        {"objective_value": 900.0},
        [("M-AAA", {"objective_value": 1200.0})])
    assert "upper_bound" not in out[0]
    assert "lower_bound" not in out[0]


def test_default_direction_is_minimize():
    out = objective_gaps({"objective_value": 1.0},
                         [("M-AAA", {"objective_value": 2.0})])
    assert out[0]["better"] == "chosen"
    assert out[0]["direction"] == "minimize"


def test_empty_others_yields_empty():
    assert objective_gaps({"objective_value": 1.0}, []) == []
