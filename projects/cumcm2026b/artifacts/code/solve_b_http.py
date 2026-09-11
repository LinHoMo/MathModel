#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""solve_b_http.py —— B 题「符合真实模拟器协议」的搜索-定位-清除策略。

与 solve_b.py（本地模型版）的区别：
  * 通过 SimulatorHTTP 走真实 HTTP+JSON 协议（arena_id/position/measure_result/svd_deg）。
  * 真实模拟器**不返回信号强度**，故不使用 d_est=rel·r_rec 估距；
    改用 **纯示向度交会 + 几何驱动归航**（准最优逼近，非盲目步进）。

策略（测量驱动，不假定真值）：
  阶段A  同心环覆盖扫描：逐检测点对未清除频道 sweep，记录示向度；
  阶段B  逐频道定位清除：两观测交会求估计点 → 几何驱动归航（沿测向线按
         approach_ratio 逼近估计点，把定位不确定度 R* 压到清除半径内再 /clear）→
         `near` 时清除；
  阶段C  残余局部搜索：对已探测未清除频道在当前位置做同心近邻 /clear 扫描。

零第三方依赖。可在本地 Mock 上端到端验证；连接真实模拟器时只需 change base_url +
robot_id（参赛队号）。
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulator_http import (  # noqa: E402
    SimulatorHTTP, MockSimulatorServer, N_CHANNEL, SEED,
    D_CLEAR, EPS_BEARING,
)
from solve_b import (  # noqa: E402
    coverage_detection_points, ring_detection_points,
    cross_fix, _bearing_diff,
)

# ---------------------------------------------------------------------------
# 交会定位与几何归航（仅用示向度）
# ---------------------------------------------------------------------------
MIN_FIX_BASELINE = 40.0       # 交会基线下限 / m
PHI_LO, PHI_HI = 30.0, 150.0  # 可用交会角区间 / °
APPROACH_RATIO = 0.45         # 几何逼近比例（<1 恒不过冲；参考组几何最优逼近）
UNCERT_TARGET = 8.0           # 定位不确定度目标 R* / m（压到清除半径内再 /clear）
PROBE_STEP = 250.0            # 无法交会时的垂向探测步长 / m
MIN_APPROACH_STEP = 12.0      # 最小逼近步长 / m
HOME_N_ITER = 10              # 单次归航 measure 上限（每轮至多 1 次）
DEFAULT_SWEEP_MAX_OBS = 6     # 覆盖扫描每频道保留的观测上限（实测 5 局清除率 1.0
#                               且 Q4 摊薄口径最优：1→1031 s、3→1080 s、6→897 s）


def best_single_fix(obs, phi_lo=PHI_LO, phi_hi=PHI_HI,
                    min_baseline=MIN_FIX_BASELINE):
    """从观测集 {(P,b)} 中取交会角最接近 90°、基线足够的两条射线求交。

    返回 (est, phi, baseline) 或 None。φ=90° 时位置误差最小（∝ 1/sinφ），
    故以 |φ−90°| 为判据；基线过短的近距交点会给出假解，故设基线下限。
    只用示向度，不用信号强度。
    """
    best = None
    n = len(obs)
    for i in range(n):
        for j in range(i + 1, n):
            p1, b1 = obs[i]
            p2, b2 = obs[j]
            base = math.dist(p1, p2)
            if base < min_baseline:
                continue
            phi = _bearing_diff(b1, b2)
            if not (phi_lo <= phi <= phi_hi):
                continue
            est = cross_fix(p1, b1, p2, b2)
            if est is None:
                continue
            score = abs(phi - 90.0)
            if best is None or score < best[0]:
                best = (score, est, phi, base)
    return (best[1], best[2], best[3]) if best else None


def _uncertainty(d, phi):
    """交会定位不确定度界 R* ≈ d·δ/sinφ（δ = 示向度误差界，弧度）。"""
    return d * math.radians(EPS_BEARING) / max(math.sin(math.radians(phi)), 1e-6)


def _step_along(pos, bearing_deg, step):
    a = math.radians(bearing_deg)
    return (pos[0] + step * math.cos(a), pos[1] + step * math.sin(a))


def _nearest_obs_point(obs, pos):
    if not obs:
        return None
    return min(obs, key=lambda o: math.dist(o[0], pos))[0]


class _MeteredClient:
    """透明代理客户端：统计 /measure 次数与 measure/clear 隐含的移动行程。

    题面口径「定位清除总时间」含移动、频道切换与检测（ADR-0012），虚拟时间由
    服务端给，但动作次数与行程须客户端自记（附件2 §12）。除 measure / clear
    外一律转发内部客户端，不改变协议语义。
    """

    def __init__(self, sim):
        self._sim = sim
        self.n_measure = 0
        self.n_clear = 0
        self.move_dist_m = 0.0

    def __getattr__(self, name):
        return getattr(self._sim, name)

    def measure(self, x, y, channel):
        p0 = self._sim.pos
        r = self._sim.measure(x, y, channel)
        self.n_measure += 1
        self.move_dist_m += math.dist(p0, self._sim.pos)
        return r

    def clear(self, x, y, channel):
        p0 = self._sim.pos
        r = self._sim.clear(x, y, channel)
        self.n_clear += 1
        self.move_dist_m += math.dist(p0, self._sim.pos)
        return r


# ---------------------------------------------------------------------------
# 归航：几何驱动逼近（方向取实时示向度、距离取交会估计点）
# ---------------------------------------------------------------------------
def _append_obs(obs, p, bearing):
    """追加观测；同一位置的重复观测会把交会基线压成 0（假解），故按位置去重。"""
    for q, _b in obs:
        if math.dist(q, p) < 1e-6:
            return
    obs.append((p, bearing))


def home_http(sim, ch, obs, n_iter=HOME_N_ITER, ratio=APPROACH_RATIO,
              target=UNCERT_TARGET):
    """几何驱动归航。每轮用示向度交会得估计点 P̂，沿实时测向线按 `ratio` 比例
    逼近 P̂，直到定位不确定度 R* 压到 `target` 内（或估计点已入清除半径）再 /clear。

    与盲目步进的差别：步长由「到估计点的距离」决定而非固定 `step0`，
    `ratio < 1` 使落点恒在 P̂ 之前、不会越过目标，收敛单调，不靠示向度反转
    被动缩步长。观测不足以交会时沿示向度右侧（固定一侧）探测一步建立基线——
    左右横跳会让行程翻倍；同一位置不重复测量（重复观测无新信息，且会把交会
    基线压成 0）。落点不可测（定向盲区）时回退到最近可测观测点重试，回到已测
    过的位置即放弃，交回上层兜底——否则会在可测区与盲区之间往返空转到 n_iter。
    收敛后清除非返回 True。
    """
    px, py = sim.pos
    r = sim.measure(px, py, ch)
    visited = {(round(px, 9), round(py, 9))}
    for _ in range(n_iter):
        res = r["measure_result"]
        if res == "near":
            if sim.clear(px, py, ch) == "success":
                return True
            # near 但 clear 未成功（不应发生：near 即 ≤5 m，clear 半径 20 m）：
            # 立即交回上层兜底，不在原地空转 n_iter 次。
            return False
        if res != "direction":
            # 不可测（定向盲区 / 出接收半径）：退回最近可测观测点重试
            p = _nearest_obs_point(obs, (px, py))
            q = (round(p[0], 9), round(p[1], 9)) if p is not None else None
            if p is None or math.dist(p, (px, py)) < 1e-6 or q in visited:
                return False
            px, py = p
            visited.add(q)
            r = sim.measure(px, py, ch)
            continue
        _append_obs(obs, (px, py), r["svd_deg"])
        g = best_single_fix(obs)
        if g is None:
            # 观测不足以交会：沿示向度右侧探测一步建立基线（固定侧，不横跳）
            q = _step_along((px, py), r["svd_deg"] + 90.0, PROBE_STEP)
            kq = (round(q[0], 9), round(q[1], 9))
            if kq in visited:
                return False
            px, py = q
            visited.add(kq)
            r = sim.measure(px, py, ch)
            continue
        est, phi, _base = g
        d = math.dist((px, py), est)
        if _uncertainty(d, phi) <= target or d <= D_CLEAR:
            if sim.clear(est[0], est[1], ch) == "success":
                return True
            px, py = est
            visited.add((round(px, 9), round(py, 9)))
            r = sim.measure(px, py, ch)
            continue
        px, py = _step_along((px, py), r["svd_deg"],
                             max(ratio * d, MIN_APPROACH_STEP))
        visited.add((round(px, 9), round(py, 9)))
        r = sim.measure(px, py, ch)
    return ch in sim.cleared


def local_search_http(sim, ch, obs, radii=(12.0, 25.0, 45.0)):
    """几何归航后的近邻兜底（3 环 × 4 向）。只在归航未触发 `near` 时使用。"""
    cx, cy = sim.pos
    for rad in radii:
        for k in range(4):
            a = math.radians(90.0 * k)
            nx, ny = cx + rad * math.cos(a), cy + rad * math.sin(a)
            m = sim.measure(nx, ny, ch)
            if m["measure_result"] == "near":
                if sim.clear(nx, ny, ch) == "success":
                    return True
            elif m["measure_result"] == "direction":
                obs.append(((nx, ny), m["svd_deg"]))
    return False


def engage_http(sim, ch, obs, max_iter=3):
    """交会定位直达 → 几何归航 → 近邻兜底，仅用可观测量。"""
    for _ in range(max_iter):
        if ch in sim.cleared:
            return True
        g = best_single_fix(obs)
        if g is not None:
            est = g[0]
            r = sim.measure(est[0], est[1], ch)     # 移动隐含于 measure
            if r["measure_result"] == "near":
                if sim.clear(est[0], est[1], ch) == "success":
                    return True
            elif r["measure_result"] == "direction":
                _append_obs(obs, est, r["svd_deg"])
        if home_http(sim, ch, obs):
            return True
        if local_search_http(sim, ch, obs):
            return True
    return ch in sim.cleared


# ---------------------------------------------------------------------------
# 覆盖扫描
# ---------------------------------------------------------------------------
def sweep_http(sim, points, obs, det_time, channels=None, max_obs=1,
               miss_limit=None):
    """在给定检测点上 sweep 频道，记录首次探测时刻。返回本阶段发现数。

    channels  ：候选频道（None = 全部未清除频道）；
    max_obs   ：同一频道本轮最多记录的观测数（None = 不限）。观测已足够时跳过该
                频道——重复测量只花 5 s 检测 + 1 s 切换而不带来新信息（Q4 单局
                曾因此白扫 ~700 次）；
    miss_limit：同一频道连续 no_signal 的容忍次数（None = 不限）。超过即在本轮
                跳过：覆盖设计下多个分散检测点仍无信号，说明该频道在本区域不可见，
                继续扫它只会拖长覆盖行程。direction / near 会重置计数（有信号即
                不算漏扫）。
    候选集为空时提前结束（剩余检测点不再访问，同时省去其行程）。
    """
    found_total = 0
    misses: dict[int, int] = {}
    for (px, py) in points:
        if channels is None:
            active = [c for c in range(1, N_CHANNEL + 1) if c not in sim.cleared]
        else:
            active = [c for c in channels if c not in sim.cleared]
        if max_obs is not None:
            active = [c for c in active if len(obs[c]) < max_obs]
        if miss_limit is not None:
            active = [c for c in active if misses.get(c, 0) < miss_limit]
        if not active:
            return found_total
        for ch in active:
            r = sim.measure(px, py, ch)
            if r["measure_result"] == "direction":
                obs[ch].append(((px, py), r["svd_deg"]))
                det_time.setdefault(ch, sim.virtual_time)
                found_total += 1
                misses[ch] = 0
            elif r["measure_result"] == "near":
                sim.clear(px, py, ch)
                misses[ch] = 0
            else:
                misses[ch] = misses.get(ch, 0) + 1
    return found_total


def dog_strategy_http(sim, has_directional=False, sweep_max_obs=DEFAULT_SWEEP_MAX_OBS,
                      sweep_miss_limit=None, points=None):
    """完整策略：覆盖扫描 → 逐频道定位清除 → 残余局部搜索。返回统计 dict。

    ``points``：覆盖扫描的检测点集。缺省用同心环（``coverage_detection_points``）；
    显式传入时**只替换覆盖几何**，其余阶段（sweep / 交会归航 / 清除）代码路径完全
    相同 —— 这是候选对照实验要求「除 coverage geometry 外全同」的实现入口（M-SELECT-001）。
    sweep_max_obs：覆盖扫描中每频道最多保留的示向度观测数（见 sweep_http）。
    sweep_miss_limit：覆盖扫描中每频道连续无信号的容忍次数（见 sweep_http）。
    统计同时给出两套口径（ADR-0012）：逐源 `mean_locate_clear_time_s`（= 该源
    清除时刻 − 首次探测时刻）与题面摊薄口径 `avg_locate_clear_time_s`
    （= 虚拟总时间 / 已清除源数）。二者不可混用，跨实现比较只用后者。
    """
    met = _MeteredClient(sim)
    obs = {ch: [] for ch in range(1, N_CHANNEL + 1)}
    det_time: dict[int, float] = {}
    clear_time: dict[int, float] = {}

    # 阶段A：覆盖扫描（点集可注入，用于候选对照；跳过多点重复测同一频道）
    pts = points if points is not None else coverage_detection_points(has_directional)
    sweep_http(met, pts, obs, det_time, max_obs=sweep_max_obs,
               miss_limit=sweep_miss_limit)

    # 阶段B：逐频道定位清除（已发现频道按最近优先）
    def _anchor(ch):
        """该频道离当前位置最近的观测点：自此处归航行程最短（观测点越多越省）。"""
        if not obs[ch]:
            return (0.0, 0.0)
        return min(obs[ch], key=lambda o: math.dist(met.pos, o[0]))[0]

    pending = [ch for ch in obs if obs[ch] and ch not in met.cleared]
    while pending:
        ch = min(pending, key=lambda c: math.dist(met.pos, _anchor(c)))
        pending.remove(ch)
        if ch in met.cleared:
            continue
        if engage_http(met, ch, obs[ch]):
            clear_time[ch] = met.virtual_time

    # 阶段C：残余重试——只对「已探测未清除」频道补扫环 r=900（不全频道重扫）
    residual = [ch for ch in obs if obs[ch] and ch not in met.cleared]
    if residual:
        sweep_http(met, ring_detection_points(900.0, 400.0), obs, det_time,
                   channels=residual, max_obs=None)
        for ch in [c for c in residual if c not in met.cleared]:
            if engage_http(met, ch, obs[ch]):
                clear_time[ch] = met.virtual_time

    n_clear = len(met.cleared)
    per_src = [clear_time[ch] - det_time[ch]
               for ch in clear_time if ch in det_time]
    return {
        "n_cleared": n_clear,
        "virtual_time_s": met.virtual_time,
        "mean_locate_clear_time_s": (
            float(sum(per_src) / len(per_src)) if per_src else float("inf")),
        "avg_locate_clear_time_s": (
            met.virtual_time / n_clear if n_clear else float("inf")),
        "n_measure": met.n_measure,
        "n_clear_actions": met.n_clear,
        "move_dist_m": met.move_dist_m,
        "n_obs_channels": sum(1 for ch in obs if obs[ch]),
    }


# ---------------------------------------------------------------------------
# 演练：对本地 Mock 跑 N 组
# ---------------------------------------------------------------------------
def run_trials_mock(n_trials=5, kind_mix=False, seed=SEED, base_port=2100):
    """对本地 Mock 端到端演练（每组一个独立 Mock，seed 连续）。"""
    recs = []
    for t in range(n_trials):
        srv = MockSimulatorServer(port=base_port, seed=seed + t, kind_mix=kind_mix)
        srv.start()
        try:
            sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{base_port}",
                                robot_id="TESTTEAM", timeout=30.0)
            sim.enter()
            st = dog_strategy_http(sim, has_directional=kind_mix)
            sim.exit()
            summ = srv.summary()
            st["seed"] = seed + t
            st["total_sources"] = summ["total_sources"]
            st["cleared_fraction"] = (summ["cleared"] / summ["total_sources"]
                                      if summ["total_sources"] else 1.0)
            st["mean_time_per_source_s"] = (
                st["virtual_time_s"] / summ["cleared"] if summ["cleared"] else float("inf"))
            recs.append(st)
        finally:
            srv.stop()
    fr = [r["cleared_fraction"] for r in recs]
    tt = [r["virtual_time_s"] for r in recs]
    lc = [r["mean_locate_clear_time_s"] for r in recs]
    nm = [r["n_measure"] for r in recs]
    md = [r["move_dist_m"] for r in recs]
    ac = [r["avg_locate_clear_time_s"] for r in recs]

    def _mean(v):
        return float(sum(v) / len(v))

    return {
        "n_trials": n_trials,
        "mean_cleared_fraction": _mean(fr),
        "min_cleared_fraction": float(min(fr)),
        "all_cleared": all(f > 0.999 for f in fr),
        "mean_total_time_s": _mean(tt),
        "mean_locate_clear_time_s": _mean(lc),
        "mean_avg_locate_clear_time_s": _mean(ac),
        "mean_n_measure": _mean(nm),
        "mean_move_dist_m": _mean(md),
    }, recs


def main():
    print("B 题真实协议策略 —— 本地 Mock 端到端演练")
    print("=" * 60)
    s, recs = run_trials_mock(n_trials=5, kind_mix=False)
    print(f"[Q3 全向] 组数={s['n_trials']} 清除比例 均值={s['mean_cleared_fraction']:.4f} "
          f"最小={s['min_cleared_fraction']:.4f} 全清除={s['all_cleared']}")
    print(f"          虚拟总时间={s['mean_total_time_s']:.1f} s "
          f"n_measure={s['mean_n_measure']:.0f} move={s['mean_move_dist_m']:.0f} m")
    print(f"          逐源口径={s['mean_locate_clear_time_s']:.1f} s "
          f"摊薄口径={s['mean_avg_locate_clear_time_s']:.1f} s")
    for r in recs:
        print(f"    seed={r['seed']} 源={r['total_sources']} 清除={r['n_cleared']} "
              f"f={r['cleared_fraction']:.3f} t={r['virtual_time_s']:.0f}s")
    s4, recs4 = run_trials_mock(n_trials=5, kind_mix=True, base_port=2110)
    print(f"[Q4 混合] 组数={s4['n_trials']} 清除比例 均值={s4['mean_cleared_fraction']:.4f} "
          f"最小={s4['min_cleared_fraction']:.4f} 全清除={s4['all_cleared']}")
    print(f"          虚拟总时间={s4['mean_total_time_s']:.1f} s "
          f"n_measure={s4['mean_n_measure']:.0f} move={s4['mean_move_dist_m']:.0f} m")
    print(f"          逐源口径={s4['mean_locate_clear_time_s']:.1f} s "
          f"摊薄口径={s4['mean_avg_locate_clear_time_s']:.1f} s")
    for r in recs4:
        print(f"    seed={r['seed']} 源={r['total_sources']} 清除={r['n_cleared']} "
              f"f={r['cleared_fraction']:.3f} t={r['virtual_time_s']:.0f}s")
    out = {"q3_mock": s, "q4_mock": s4}
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "results", "resultB_http_mock.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] {os.path.normpath(path)} 已写出")

    # 并入项目根结果台账（供数值追溯：模型描述文档引用的协议演练数字可溯源）
    proj = os.path.abspath(os.path.join(here, "..", ".."))
    allres = os.path.join(proj, "all_results.json")
    data = {}
    if os.path.exists(allres):
        try:
            with open(allres, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data["real_protocol_mock"] = {
        "protocol": "CUMCM2026B 附件2 HTTP+JSON",
        "n_trials": s["n_trials"],
        "q3_mean_cleared_fraction": s["mean_cleared_fraction"],
        "q3_min_cleared_fraction": s["min_cleared_fraction"],
        "q3_mean_total_time_s": s["mean_total_time_s"],
        "q3_mean_locate_clear_time_s": s["mean_locate_clear_time_s"],
        "q3_mean_avg_locate_clear_time_s": s["mean_avg_locate_clear_time_s"],
        "q3_mean_n_measure": s["mean_n_measure"],
        "q3_mean_move_dist_m": s["mean_move_dist_m"],
        "q4_mean_cleared_fraction": s4["mean_cleared_fraction"],
        "q4_min_cleared_fraction": s4["min_cleared_fraction"],
        "q4_mean_total_time_s": s4["mean_total_time_s"],
        "q4_mean_locate_clear_time_s": s4["mean_locate_clear_time_s"],
        "q4_mean_avg_locate_clear_time_s": s4["mean_avg_locate_clear_time_s"],
        "q4_mean_n_measure": s4["mean_n_measure"],
        "q4_mean_move_dist_m": s4["mean_move_dist_m"],
    }
    with open(allres, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已并入 {os.path.normpath(allres)} 的 real_protocol_mock 段")


if __name__ == "__main__":
    main()
