# -*- coding: utf-8 -*-
"""定位清除预算门禁：cumcm2026b HTTP 策略归航的「动作数 / 移动距离」回归。

背景（问题复现）
----------------
`solve_b_http.dog_strategy_http` 的定位清除阶段（阶段 B）早期用**纯示向度盲目
步进归航**：`home_http(step0=400, n_iter=16)` 沿示向度按 400→600 m 盲走、示向度
反转才把步长减半，收敛靠阻尼振荡；`local_search_http` 再叠加 5 环 × 6 向 = 30 次
近邻尝试；`engage_http(max_iter=8)` 最多把上面两件事各做 8 遍。结果是每源动作次数
与移动距离都偏大（真实协议的测量动作是 5 s/次，是主要时间成本）。

修复方向（几何驱动归航）
------------------------
改「盲目步进」为「几何逼近」：每轮用示向度交会得估计点 P̂，沿实时测向线按比例
`approach_ratio` 逼近（<1 恒不过冲），把定位不确定度 R* ≈ d·δ/sinφ 压到清除半径
以内再 `/clear`。观测量只有示向度（真实 API 不返回信号强度）。

本测试断言（对本地 Mock 端到端跑 Q3 全向 / Q4 全向+定向）
----------------------------------------------------------
1. **清除完备性**：每个实例全部清除 —— 效率不得以完备性为代价；
2. **效率预算**：每实例的 measure 次数 / 移动距离 / 虚拟时间不超过预算。

预算由「几何归航之前」的实测值标定（见文件末注释），旧实现必然超限 → RED；
几何归航后低于预算 → GREEN。所有数字来自本地 Mock 实跑（种子固定 42 起连续
整数，逐次可复现），非转述。
"""

import math
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_CODE = _REPO / "projects" / "cumcm2026b" / "artifacts" / "code"
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

import solve_b_http as sbh  # noqa: E402
from simulator_http import MockSimulatorServer, SimulatorHTTP  # noqa: E402

SEEDS = (42, 43, 44)

# 预算（每实例，按 3 个种子取均值）——旧实现超限，几何归航后有余量。
BUDGET = {
    "q3_n_measure": 440.0,
    "q3_move_dist": 34000.0,
    "q3_virtual_time": 9500.0,
    "q4_move_dist": 55000.0,
    "q4_virtual_time": 17500.0,
}


class CountingSim(SimulatorHTTP):
    """给 measure / clear 计数并累计位移（measure 兼作移动）。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n_measure = 0
        self.n_clear = 0
        self.move_dist = 0.0

    def measure(self, x, y, ch):
        self.move_dist += math.dist(self.pos, (float(x), float(y)))
        self.n_measure += 1
        return super().measure(x, y, ch)

    def clear(self, x, y, ch):
        self.move_dist += math.dist(self.pos, (float(x), float(y)))
        self.n_clear += 1
        return super().clear(x, y, ch)


def _run_trial(seed: int, kind_mix: bool, port: int) -> dict:
    """一个随机实例：本地 Mock + 真实协议客户端端到端跑一遍完整策略。"""
    server = MockSimulatorServer(port=port, seed=seed, kind_mix=kind_mix)
    server.start()
    try:
        sim = CountingSim(base_url=f"http://127.0.0.1:{port}",
                          robot_id="TESTTEAM", timeout=30.0)
        sim.enter()
        sbh.dog_strategy_http(sim, has_directional=kind_mix)
        sim.exit()
        summ = server.summary()
        return {
            "seed": seed,
            "n_measure": sim.n_measure,
            "n_clear": sim.n_clear,
            "move_dist": sim.move_dist,
            "virtual_time": sim.virtual_time,
            "cleared": summ["cleared"],
            "total_sources": summ["total_sources"],
        }
    finally:
        server.stop()


@pytest.fixture(scope="module")
def q3_trials():
    return [_run_trial(seed, False, 3200 + i) for i, seed in enumerate(SEEDS)]


@pytest.fixture(scope="module")
def q4_trials():
    return [_run_trial(seed, True, 3220 + i) for i, seed in enumerate(SEEDS)]


def _mean(rows, key):
    return sum(r[key] for r in rows) / len(rows)


@pytest.mark.parametrize("question", ["q3", "q4"])
def test_all_sources_cleared(question, q3_trials, q4_trials):
    """效率不得以完备性为代价：每个实例必须全部清除。"""
    rows = q3_trials if question == "q3" else q4_trials
    for r in rows:
        assert r["cleared"] == r["total_sources"], (
            f"{question} seed={r['seed']} 未全部清除 "
            f"({r['cleared']}/{r['total_sources']})")


def test_q3_measure_budget(q3_trials):
    """Q3（全向）：measure 次数预算（盲目步进归航超限）。"""
    got = _mean(q3_trials, "n_measure")
    assert got <= BUDGET["q3_n_measure"], (
        f"Q3 平均 measure={got:.1f} 超预算 {BUDGET['q3_n_measure']}")


def test_q3_move_dist_budget(q3_trials):
    """Q3（全向）：移动距离预算（盲目步进 + 30 次近邻尝试超限）。"""
    got = _mean(q3_trials, "move_dist")
    assert got <= BUDGET["q3_move_dist"], (
        f"Q3 平均 move_dist={got:.0f} m 超预算 {BUDGET['q3_move_dist']}")


def test_q3_virtual_time_budget(q3_trials):
    """Q3（全向）：虚拟任务时间预算（动作 5 s/次 + 移动 |Δp|/5 s）。"""
    got = _mean(q3_trials, "virtual_time")
    assert got <= BUDGET["q3_virtual_time"], (
        f"Q3 平均 virtual_time={got:.0f} s 超预算 {BUDGET['q3_virtual_time']}")


def test_q4_move_dist_budget(q4_trials):
    """Q4（全向+定向）：移动距离预算（定向盲区回退使盲目步进代价更高）。"""
    got = _mean(q4_trials, "move_dist")
    assert got <= BUDGET["q4_move_dist"], (
        f"Q4 平均 move_dist={got:.0f} m 超预算 {BUDGET['q4_move_dist']}")


def test_q4_virtual_time_budget(q4_trials):
    """Q4（全向+定向）：虚拟任务时间预算。"""
    got = _mean(q4_trials, "virtual_time")
    assert got <= BUDGET["q4_virtual_time"], (
        f"Q4 平均 virtual_time={got:.0f} s 超预算 {BUDGET['q4_virtual_time']}")


# ---------------------------------------------------------------------------
# 预算标定依据（本地 Mock，种子 42/43/44，2026 会话实测）：
#   几何归航之前（盲目步进 + 5×6 近邻 + engage max_iter=8）：
#     Q3  n_measure 均值 500.7 / move_dist 均值 42887 m / virtual_time 均值 11496 s
#     Q4  n_measure 均值 1161  / move_dist 均值 59876 m / virtual_time 均值 18855 s
#   几何归航之后：见 tests 运行输出（均值低于上述预算）。
# ---------------------------------------------------------------------------
