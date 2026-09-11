#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADR-0014 守卫测试：候选选型必须比目标函数值（ADR-0013 延伸到 P1-M3 路径）。

背景（缺口）：ADR-0013 只改了 `runtime/modeling/comparison.py::compare_models`，
而真正跑生产的选型节点 `model_selection_decision`（handlers.do_model_selection_decision）
走的是 `DefaultNodeExecutor._rank_candidates` —— 其排序键为
`mathematical_valid → constraint_violation_max → execution_valid → 域合规 →
empirical_valid → mir_id`，**完全不读 `objective_value`**。

后果：两个都合规（constraint_violation_max=0）的候选，由 `mir_id` 字典序决胜，
目标函数值更优者可能落选 —— 即 ADR-0013 想根除的「模型质量被验证质量替代」
在生产选型路径上仍然存在。

运行: python -m pytest tests/unit/test_selection_objective_rank.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.execution.handlers import DefaultNodeExecutor  # noqa: E402


def _metrics(**over) -> dict:
    m = {
        "mathematical_valid": True,
        "constraint_violation_max": 0.0,
        "execution_valid": True,
        "variable_domain_violation": 0,
        "empirical_valid": True,
    }
    m.update(over)
    return m


def _table(pairs: dict) -> dict:
    return {mid: {"vr_id": f"VR-{mid}", "metrics": m}
            for mid, m in pairs.items()}


# --------------------------------------------------------------- objective-first
def test_minimize_prefers_smaller_objective():
    """同可行性、同 cv 下，目标值更小者（minimize）必须排前，而非按 id 字典序。"""
    table = _table({
        "M-AAA": _metrics(objective_value=1200.0),
        "M-BBB": _metrics(objective_value=900.0),
    })
    ranked = DefaultNodeExecutor._rank_candidates(table)
    assert ranked[0] == "M-BBB", f"目标值 900 应优于 1200，得到 {ranked}"


def test_maximize_prefers_larger_objective():
    """direction=maximize 时，目标值更大者排前。"""
    table = _table({
        "M-AAA": _metrics(objective_value=0.90, objective_direction="maximize"),
        "M-BBB": _metrics(objective_value=0.95, objective_direction="maximize"),
    })
    ranked = DefaultNodeExecutor._rank_candidates(table)
    assert ranked[0] == "M-BBB", f"maximize 下 0.95 应优于 0.90，得到 {ranked}"


def test_objective_beats_validation_quality():
    """可行候选间，目标值优先于 constraint_violation_max（ADR-0013 精神）。

    A 的目标值更优但 cv 略大（仍远低于容差）；旧实现按 cv 升序会把 B 判前。
    """
    table = _table({
        "M-AAA": _metrics(constraint_violation_max=1e-9, objective_value=900.0),
        "M-BBB": _metrics(constraint_violation_max=0.0, objective_value=1200.0),
    })
    ranked = DefaultNodeExecutor._rank_candidates(table)
    assert ranked[0] == "M-AAA", f"目标值优先：900 应胜 1200，得到 {ranked}"


def test_missing_objective_ranks_after_present():
    """可行候选：有目标值的排在无目标值之前（不可比者不得抢先）。"""
    table = _table({
        "M-AAA": _metrics(constraint_violation_max=5.0, objective_value=900.0),
        "M-BBB": _metrics(constraint_violation_max=0.0),   # 无 objective_value
    })
    ranked = DefaultNodeExecutor._rank_candidates(table)
    assert ranked[0] == "M-AAA", f"有目标值者优先，得到 {ranked}"


# ------------------------------------------------------------------- 守卫（既有语义）
def test_infeasible_ranks_last_even_with_better_objective():
    """mathematical_valid=False 恒排最后，即使目标值更好（可行性先于最优性）。"""
    table = _table({
        "M-AAA": _metrics(mathematical_valid=False, objective_value=1.0),
        "M-BBB": _metrics(mathematical_valid=True, objective_value=1000.0),
    })
    assert DefaultNodeExecutor._rank_candidates(table) == ["M-BBB", "M-AAA"]


def test_no_evidence_ranks_last():
    """无 VR 证据的候选（metrics=None）恒排最后。"""
    table = {
        "M-AAA": {"vr_id": None, "metrics": None},
        "M-BBB": {"vr_id": "VR-BBB", "metrics": _metrics(objective_value=100.0)},
    }
    assert DefaultNodeExecutor._rank_candidates(table) == ["M-BBB", "M-AAA"]


def test_nan_objective_treated_as_missing():
    """NaN 目标值视为缺失（不可比），不得因比较 NaN 产生非确定性顺序。"""
    table = _table({
        "M-AAA": _metrics(objective_value=float("nan")),
        "M-BBB": _metrics(objective_value=500.0),
    })
    ranked = DefaultNodeExecutor._rank_candidates(table)
    assert ranked[0] == "M-BBB"
    # 确定性：重复调用同序
    assert ranked == DefaultNodeExecutor._rank_candidates(table)


def test_empty_table_is_empty():
    assert DefaultNodeExecutor._rank_candidates({}) == []
