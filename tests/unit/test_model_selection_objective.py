#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADR-0013 守卫测试：模型选择必须比目标函数值，且基线对照要能判定优劣、量化 gap。

覆盖三件事：
1. `baseline_comparison` 的目标方向与 gap 量化（此前只返回 tie/different，无法回答谁更好）；
2. `compare_models` 在两侧都有 objective_value 时**不得**用 checks_passed 代偿；
3. 目标值不可得时按验证质量回退，但必须显式标注回退（不得静默）。
"""
from __future__ import annotations

import pytest

from modeling_harness.runtime.evaluation.deterministic_metrics import baseline_comparison
from modeling_harness.runtime.modeling.comparison import compare_models


# ----------------------------------------------------------- baseline_comparison
def test_minimize_direction_picks_smaller():
    r = baseline_comparison({"t": 900.0}, {"t": 1200.0}, direction="minimize")
    assert r["better"] == "a"          # a 更小 ⇒ 更好
    d = r["detail"][0]
    assert d["abs_gap"] == -300.0
    assert d["rel_gap"] == pytest.approx(-0.25)


def test_maximize_direction_picks_larger():
    r = baseline_comparison({"f": 0.99}, {"f": 0.90}, direction="maximize")
    assert r["better"] == "a"
    assert r["detail"][0]["abs_gap"] == pytest.approx(0.09)


def test_direction_flips_verdict_on_same_numbers():
    """同一组数字，方向不同 ⇒ 结论相反。没有方向就回答不了「谁更好」。"""
    out_a, out_b = {"v": 10.0}, {"v": 20.0}
    assert baseline_comparison(out_a, out_b, direction="minimize")["better"] == "a"
    assert baseline_comparison(out_a, out_b, direction="maximize")["better"] == "b"


def test_per_key_direction_override():
    """time 越小越好、cleared 越大越好；本例两侧各胜一项 ⇒ 如实报 mixed。"""
    a = {"time": 900.0, "cleared": 0.90}
    b = {"time": 1000.0, "cleared": 0.95}
    r = baseline_comparison(a, b, direction="minimize",
                            directions={"cleared": "maximize"})
    assert r["better"] == "mixed"      # 时间 a 胜、清除率 b 胜
    by = {c["key"]: c for c in r["detail"]}
    assert by["time"]["better"] == "a"
    assert by["time"]["direction"] == "minimize"
    assert by["cleared"]["direction"] == "maximize"
    assert by["cleared"]["better"] == "b"


def test_per_key_override_can_agree():
    a = {"time": 900.0, "cleared": 0.97}
    b = {"time": 1000.0, "cleared": 0.95}
    r = baseline_comparison(a, b, direction="minimize",
                            directions={"cleared": "maximize"})
    assert r["better"] == "a"          # 时间更短且清除率更高


def test_tie_within_tolerance():
    r = baseline_comparison({"x": 1.0}, {"x": 1.0 + 1e-12})
    assert r["better"] == "tie"


def test_disagreement_reports_mixed_not_majority():
    a = {"p": 0.9, "q": 100.0}
    b = {"p": 0.8, "q": 90.0}
    r = baseline_comparison(a, b, direction="minimize",
                            directions={"p": "maximize"})
    assert r["better"] == "mixed"


def test_incomparable_when_no_shared_keys():
    r = baseline_comparison({"a": 1.0}, {"b": 2.0})
    assert r["better"] == "incomparable"
    assert r["compared_keys"] == 0


@pytest.mark.parametrize("bad", ["min", "minimizee", "", "MAX"])
def test_invalid_direction_fails_closed(bad):
    with pytest.raises(ValueError, match="direction"):
        baseline_comparison({"a": 1.0}, {"a": 2.0}, direction=bad)


def test_invalid_per_key_direction_fails_closed():
    with pytest.raises(ValueError, match="directions"):
        baseline_comparison({"a": 1.0}, {"a": 2.0}, directions={"a": "less"})


def test_zero_baseline_rel_gap_is_none_not_inf():
    r = baseline_comparison({"x": 5.0}, {"x": 0.0}, direction="minimize")
    assert r["detail"][0]["rel_gap"] is None


# --------------------------------------------------------------- compare_models
class _Art:
    def __init__(self, aid: str, data: dict):
        self.artifact_id = aid
        self.data = data


class _Reg:
    """最小 registry 桩：只实现 compare_models 用到的两个查询。"""

    def __init__(self, codes, execs, vrs):
        self._d = {"code": codes, "execution_result": execs,
                   "verification_result": vrs}

    def list_by_type(self, t):
        return self._d.get(t, [])

    def get(self, aid):  # pragma: no cover - 本测试路径不触发
        return None


def _reg_for(model_id: str, *, valid: bool, checks: int,
             objective: float | None = None):
    code = _Art(f"C-{model_id}", {"model_id": model_id, "code_hash": f"H-{model_id}"})
    ex = _Art(f"X-{model_id}", {"code_hash": f"H-{model_id}", "status": "success"})
    vdata = {"status": "passed" if valid else "failed",
             "checks": [{"passed": True} for _ in range(checks)],
             "execution_id": f"X-{model_id}"}
    if objective is not None:
        vdata["objective_value"] = objective
    vr = _Art(f"V-{model_id}", vdata)
    return _Reg([code], [ex], [vr])


def test_objective_beats_more_checks():
    """核心回归：M2 检查数更多但目标值更差 ⇒ 仍应判 M1 更优。"""
    reg = _Reg([_Art("C1", {"model_id": "M1", "code_hash": "H1"}),
                _Art("C2", {"model_id": "M2", "code_hash": "H2"})],
               [_Art("X1", {"code_hash": "H1", "status": "success"}),
                _Art("X2", {"code_hash": "H2", "status": "success"})],
               [_Art("V1", {"status": "passed", "execution_id": "X1",
                            "checks": [{"passed": True}] * 3,
                            "objective_value": 900.0}),
                _Art("V2", {"status": "passed", "execution_id": "X2",
                            "checks": [{"passed": True}] * 50,
                            "objective_value": 1200.0})])
    r = compare_models(reg, "M1", "M2")
    assert r["better_model"] == "M1", r
    assert r["recommendation"] == "keep"
    assert "目标值" in r["reasoning"]


def test_objective_accepts_strictly_better_model():
    reg = _Reg([_Art("C1", {"model_id": "M1", "code_hash": "H1"}),
                _Art("C2", {"model_id": "M2", "code_hash": "H2"})],
               [_Art("X1", {"code_hash": "H1", "status": "success"}),
                _Art("X2", {"code_hash": "H2", "status": "success"})],
               [_Art("V1", {"status": "passed", "execution_id": "X1",
                            "checks": [{"passed": True}] * 50,
                            "objective_value": 1200.0}),
                _Art("V2", {"status": "passed", "execution_id": "X2",
                            "checks": [{"passed": True}] * 3,
                            "objective_value": 900.0})])
    r = compare_models(reg, "M1", "M2")
    assert r["better_model"] == "M2"
    assert r["recommendation"] == "accept"


def test_fallback_to_checks_is_flagged():
    """目标值不可得时按验证质量回退，但必须显式标注回退（不得静默）。"""
    reg = _Reg([_Art("C1", {"model_id": "M1", "code_hash": "H1"}),
                _Art("C2", {"model_id": "M2", "code_hash": "H2"})],
               [_Art("X1", {"code_hash": "H1", "status": "success"}),
                _Art("X2", {"code_hash": "H2", "status": "success"})],
               [_Art("V1", {"status": "passed", "execution_id": "X1",
                            "checks": [{"passed": True}] * 3}),
                _Art("V2", {"status": "passed", "execution_id": "X2",
                            "checks": [{"passed": True}] * 9})])
    r = compare_models(reg, "M1", "M2")
    assert r["better_model"] == "M2"
    assert r["deltas"].get("objective_fallback") is True
    assert "退化" in r["reasoning"]
