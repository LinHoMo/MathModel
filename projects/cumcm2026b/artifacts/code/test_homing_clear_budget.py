#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""归航 clear 预算守卫测试：反复 clear 失败时须放弃并交上层小半径兜底。

动机（travel_audit 5 seeds 实测）：
  Q3 全向 归航冗余 1.52×（±0.07）、clear 16.0 次（15 源，几乎 1 次/源）
  Q4 混合 归航冗余 2.42×（±0.64）、clear 28.0 次 —— 波动大且明显更高
零侵入插桩定位机理：多出的 clear 全在 `home_http` 内部——定向源归航不准时
`d <= D_CLEAR` 分支反复 clear 失败、每次跳到估计点再测。原先只受 `n_iter=16`
兜底，单局最高见过 65 次 clear 对 15 个源。

本测试锁的是**判定逻辑**（该不该放弃）；端到端效果由 5 seeds 对照实验验收，
不靠这条单测冒充。

运行: python -m pytest test_homing_clear_budget.py -q
"""
from __future__ import annotations

import solve_b_http as M


def test_budget_constant_is_small_and_positive():
    assert isinstance(M.MAX_CLEAR_TRIES, int)
    assert 1 <= M.MAX_CLEAR_TRIES <= 8, "上限应在个位数，n_iter=16 的兜底太宽松"


def test_exhausted_only_after_limit_reached():
    n = M.MAX_CLEAR_TRIES
    assert M.clear_budget_exhausted(0) is False
    assert M.clear_budget_exhausted(n - 1) is False
    assert M.clear_budget_exhausted(n) is True
    assert M.clear_budget_exhausted(n + 5) is True


def test_q3_path_never_hits_the_budget():
    """Q3 实测 15 源 / 16 次 clear（≈1 次/源）⇒ 正常路径不该触发上限。

    这条是回归护栏：若哪天 Q3 也开始反复试探，上限设置就失去了意义。
    """
    assert M.clear_budget_exhausted(1) is False, \
        "正常归航（1 次 clear 即成功）不得被判为超预算"


def test_custom_limit_supported():
    assert M.clear_budget_exhausted(2, limit=3) is False
    assert M.clear_budget_exhausted(3, limit=3) is True
