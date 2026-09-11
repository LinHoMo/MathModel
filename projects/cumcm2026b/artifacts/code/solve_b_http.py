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


# ---------------------------------------------------------------------------
# 归航：几何驱动逼近（方向取实时示向度、距离取交会估计点）
# ---------------------------------------------------------------------------
def home_http(sim, ch, obs, n_iter=HOME_N_ITER, ratio=APPROACH_RATIO,
              target=UNCERT_TARGET):
    """几何驱动归航。每轮用示向度交会得估计点 P̂，沿实时测向线按 `ratio` 比例
    逼近 P̂，直到定位不确定度 R* 压到 `target` 内（或估计点已入清除半径）再 /clear。

    与盲目步进的差别：步长由「到估计点的距离」决定而非固定 `step0`，
    `ratio < 1` 使落点恒在 P̂ 之前、不会越过目标，收敛单调，不靠示向度反转
    被动缩步长。落点不可测（定向盲区）时回退到最近可测观测点重试。
    收敛后清除非返回 True。
    """
    px, py = sim.pos
    r = sim.measure(px, py, ch)
    for _ in range(n_iter):
        res = r["measure_result"]
        if res == "near":
            if sim.clear(px, py, ch) == "success":
                return True
            # near 但 clear 未成功（不应发生：near 即 ≤5 m，clear 半径 20 m）：
            # 立即交回上层兜底，不在原地空转 n_iter 次。
            return False
        elif res == "direction":
            obs.append(((px, py), r["svd_deg"]))
            g = best_single_fix(obs)
            if g is None:
                # 观测不足以交会：垂向探测一步建立基线（只耗移动，不耗额外检测）
                px, py = _step_along((px, py), r["svd_deg"] + 90.0, PROBE_STEP)
                r = sim.measure(px, py, ch)
                continue
            est, phi, _base = g
            d = math.dist((px, py), est)
            if _uncertainty(d, phi) <= target or d <= D_CLEAR:
                if sim.clear(est[0], est[1], ch) == "success":
                    return True
                px, py = est
                r = sim.measure(px, py, ch)
                continue
            px, py = _step_along((px, py), r["svd_deg"],
                                 max(ratio * d, MIN_APPROACH_STEP))
            r = sim.measure(px, py, ch)
        else:
            # 不可测（定向盲区 / 出接收半径）：回到最近可测观测点重试
            p = _nearest_obs_point(obs, (px, py))
            if p is None or math.dist(p, (px, py)) < 1e-6:
                return False
            px, py = p
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
                obs.append((est, r["svd_deg"]))
        if home_http(sim, ch, obs):
            return True
        if local_search_http(sim, ch, obs):
            return True
    return ch in sim.cleared


# ---------------------------------------------------------------------------
# 覆盖扫描
# ---------------------------------------------------------------------------
def sweep_http(sim, points, obs, det_time):
    """在给定检测点上 sweep 未清除频道，记录首次探测时刻。返回本点发现数。"""
    found_total = 0
    for (px, py) in points:
        channels = [c for c in range(1, N_CHANNEL + 1) if c not in sim.cleared]
        if not channels:
            return found_total
        for ch in channels:
            r = sim.measure(px, py, ch)
            if r["measure_result"] == "direction":
                obs[ch].append(((px, py), r["svd_deg"]))
                det_time.setdefault(ch, sim.virtual_time)
                found_total += 1
            elif r["measure_result"] == "near":
                sim.clear(px, py, ch)
    return found_total


def dog_strategy_http(sim, has_directional=False):
    """完整策略：覆盖扫描 → 逐频道定位清除 → 残余局部搜索。返回统计 dict。"""
    obs = {ch: [] for ch in range(1, N_CHANNEL + 1)}
    det_time: dict[int, float] = {}
    clear_time: dict[int, float] = {}

    # 阶段A：同心环覆盖扫描
    pts = coverage_detection_points(has_directional)
    sweep_http(sim, pts, obs, det_time)

    # 阶段B：逐频道定位清除（已发现频道按最近优先）
    def _anchor(ch):
        return obs[ch][0][0] if obs[ch] else (0.0, 0.0)

    pending = [ch for ch in obs if obs[ch] and ch not in sim.cleared]
    while pending:
        ch = min(pending, key=lambda c: math.dist(sim.pos, _anchor(c)))
        pending.remove(ch)
        if ch in sim.cleared:
            continue
        if engage_http(sim, ch, obs[ch]):
            clear_time[ch] = sim.virtual_time

    # 阶段C：残余重试（对已探测未清除频道补扫环 r=900）
    residual = [ch for ch in obs if obs[ch] and ch not in sim.cleared]
    if residual:
        sweep_http(sim, ring_detection_points(900.0, 400.0), obs, det_time)
        for ch in [c for c in obs if obs[c] and c not in sim.cleared]:
            if engage_http(sim, ch, obs[ch]):
                clear_time[ch] = sim.virtual_time

    n_clear = len(sim.cleared)
    per_src = [clear_time[ch] - det_time[ch]
               for ch in clear_time if ch in det_time]
    return {
        "n_cleared": n_clear,
        "virtual_time_s": sim.virtual_time,
        "mean_locate_clear_time_s": (
            float(sum(per_src) / len(per_src)) if per_src else float("inf")),
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
    return {
        "n_trials": n_trials,
        "mean_cleared_fraction": float(sum(fr) / len(fr)),
        "min_cleared_fraction": float(min(fr)),
        "all_cleared": all(f > 0.999 for f in fr),
        "mean_total_time_s": float(sum(tt) / len(tt)),
        "mean_locate_clear_time_s": float(sum(lc) / len(lc)),
    }, recs


def main():
    print("B 题真实协议策略 —— 本地 Mock 端到端演练")
    print("=" * 60)
    s, recs = run_trials_mock(n_trials=5, kind_mix=False)
    print(f"[Q3 全向] 组数={s['n_trials']} 清除比例 均值={s['mean_cleared_fraction']:.4f} "
          f"最小={s['min_cleared_fraction']:.4f} 全清除={s['all_cleared']}")
    print(f"          平均虚拟总时间={s['mean_total_time_s']:.1f} s "
          f"平均定位清除时间={s['mean_locate_clear_time_s']:.1f} s")
    for r in recs:
        print(f"    seed={r['seed']} 源={r['total_sources']} 清除={r['n_cleared']} "
              f"f={r['cleared_fraction']:.3f} t={r['virtual_time_s']:.0f}s")
    s4, recs4 = run_trials_mock(n_trials=5, kind_mix=True, base_port=2110)
    print(f"[Q4 混合] 组数={s4['n_trials']} 清除比例 均值={s4['mean_cleared_fraction']:.4f} "
          f"最小={s4['min_cleared_fraction']:.4f} 全清除={s4['all_cleared']}")
    print(f"          平均虚拟总时间={s4['mean_total_time_s']:.1f} s "
          f"平均定位清除时间={s4['mean_locate_clear_time_s']:.1f} s")
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
        "q4_mean_cleared_fraction": s4["mean_cleared_fraction"],
        "q4_min_cleared_fraction": s4["min_cleared_fraction"],
        "q4_mean_total_time_s": s4["mean_total_time_s"],
        "q4_mean_locate_clear_time_s": s4["mean_locate_clear_time_s"],
    }
    with open(allres, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已并入 {os.path.normpath(allres)} 的 real_protocol_mock 段")


if __name__ == "__main__":
    main()
