#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADR-0013 硬门 1 守卫：baseline 标签必须是执行的回执，不是计划声明的同义词。

回归目标（此前真实的静默失效）：
    planner 声明 baseline_comparison → handlers 给产物打 `baseline` 标签 →
    而 baseline_comparison() 从未被调用。结果：标签写着"做过对照"，实际没有。

本测试锁死新语义：
  * 产物含基线数值段 → 真跑对照、落结果、打标签；
  * 产物缺基线数值段 → 记 status=missing、**不打标签**（声明 ≠ 回执）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from modeling_harness.runtime.execution.handlers import DefaultNodeExecutor


@dataclass
class _Art:
    artifact_id: str = "R-1"
    data: dict = field(default_factory=dict)
    tags: list = field(default_factory=list)


def _executor():
    """绕开 __init__（本方法只消费 r_art 与 plan，不触碰 registry/图谱）。"""
    return DefaultNodeExecutor.__new__(DefaultNodeExecutor)


def test_without_declaration_nothing_happens():
    ex, art = _executor(), _Art(data={"outputs": {"t": 1.0}})
    ex._apply_baseline_comparison(art, {})
    assert art.tags == []
    assert "baseline_comparison" not in art.data


def test_declared_but_no_baseline_payload_records_missing_and_does_not_tag():
    """核心回归：声明了却拿不出基线数值 ⇒ 不得打标签。"""
    ex = _executor()
    art = _Art(data={"outputs": {"t": 6597.9}})
    ex._apply_baseline_comparison(art, {"baseline_comparison": ["朴素基线"]})
    assert art.tags == [], "缺少基线数值段时不得打 baseline 标签"
    bc = art.data["baseline_comparison"]
    assert bc["status"] == "missing"
    assert "未执行" in bc["reason"]


def test_declared_with_payload_runs_real_comparison():
    ex = _executor()
    art = _Art(data={"outputs": {"t": 6597.9, "baseline": {"t": 15361.8}}})
    ex._apply_baseline_comparison(art, {"baseline_comparison": ["朴素基线"]})
    assert "baseline" in art.tags, "真跑过对照才允许打标签"
    bc = art.data["baseline_comparison"]
    assert bc["better"] == "a"          # 模型 t 更小 ⇒ 更优（minimize）
    assert bc["detail"][0]["abs_gap"] == round(6597.9 - 15361.8, 8)


def test_direction_is_honoured_from_artifact():
    ex = _executor()
    art = _Art(data={"outputs": {"score": 0.97, "baseline": {"score": 0.90}},
                     "objective_direction": "maximize"})
    ex._apply_baseline_comparison(art, {"baseline_comparison": ["基线"]})
    assert art.data["baseline_comparison"]["better"] == "a"


def test_baseline_key_is_not_compared_against_itself():
    ex = _executor()
    art = _Art(data={"outputs": {"t": 10.0, "baseline": {"t": 20.0}}})
    ex._apply_baseline_comparison(art, {"baseline_comparison": ["基线"]})
    keys = [c["key"] for c in art.data["baseline_comparison"]["detail"]]
    assert keys == ["t"], "基线段自身不得进入比较键"


def test_idempotent_tagging():
    ex = _executor()
    art = _Art(data={"outputs": {"t": 1.0, "baseline": {"t": 2.0}}})
    plan = {"baseline_comparison": ["基线"]}
    ex._apply_baseline_comparison(art, plan)
    ex._apply_baseline_comparison(art, plan)
    assert art.tags.count("baseline") == 1
