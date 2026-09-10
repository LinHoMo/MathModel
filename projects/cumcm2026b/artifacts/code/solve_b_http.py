#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""solve_b_http.py —— B 题「符合真实模拟器协议」的搜索-定位-清除策略。

与 solve_b.py（本地模型版）的区别：
  * 通过 SimulatorHTTP 走真实 HTTP+JSON 协议（arena_id/position/measure_result/svd_deg）。
  * 真实模拟器**不返回信号强度**，故不使用 d_est=rel·r_rec 估距；
    改用 **纯示向度交会 + 越界检测归航**（bearing-flip / overshoot detection）。

策略（测量驱动，不假定真值）：
  阶段A  同心环覆盖扫描：逐检测点对未清除频道 sweep，记录示向度；
  阶段B  逐频道定位清除：两观测交会求估计点 → 移动（measure 隐含移动）→ 交会重估 →
         beam-safe 归航（沿示向度步进，示向度反转判越界并缩减步长）→ `near` 时清除；
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
    SimulatorHTTP, MockSimulatorServer, N_CHANNEL, SEED, R_AREA,
)
from solve_b import (  # noqa: E402
    coverage_detection_points, ring_detection_points,
    cross_fix, _bearing_diff,
)

# ---------------------------------------------------------------------------
# 交会定位（仅用示向度）
# ---------------------------------------------------------------------------
def best_single_fix(obs, phi_lo=30.0, phi_hi=150.0, min_baseline=60.0):
    """从观测集 {(P,b)} 中取交会角最接近 90°、基线足够的两条求交。返回估计点或 None。"""
    best = None
    n = len(obs)
    for i in range(n):
        for j in range(i + 1, n):
            p1, b1 = obs[i]
            p2, b2 = obs[j]
            if math.dist(p1, p2) < min_baseline:
                continue
            phi = _bearing_diff(b1, b2)
            if not (phi_lo <= phi <= phi_hi):
                continue
            est = cross_fix(p1, b1, p2, b2)
            if est is None:
                continue
            score = abs(phi - 90.0)
            if best is None or score < best[0]:
                best = (score, est)
    return best[1] if best else None


def _step_along(pos, bearing_deg, step):
    a = math.radians(bearing_deg)
    return (pos[0] + step * math.cos(a), pos[1] + step * math.sin(a))


# ---------------------------------------------------------------------------
# 归航：沿示向度步进 + 越界检测（不依赖距离）
# ---------------------------------------------------------------------------
def home_http(sim, ch, obs, step0=400.0, n_iter=16):
    """beam-safe 归航。沿示向度步进；失联即回退到最近可测点并缩步长。

    不依赖距离（真实 API 无信号强度），仅用示向度 + 越界检测（示向度反转）。
    收敛后清除非返回 True。
    """
    step = step0
    r = sim.measure(sim.pos[0], sim.pos[1], ch)
    if r["measure_result"] != "direction" and obs:
        # 当前不可测（落入定向盲区）：从最近观测点重启归航
        p = obs[-1][0]
        r = sim.measure(p[0], p[1], ch)
    for _ in range(n_iter):
        px, py = sim.pos
        res = r["measure_result"]
        if res == "near":
            return sim.clear(px, py, ch) == "success"
        if res != "direction":
            return False
        b = r["svd_deg"]
        obs.append(((px, py), b))
        nx, ny = _step_along((px, py), b, step)
        r2 = sim.measure(nx, ny, ch)
        res2 = r2["measure_result"]
        if res2 == "near":
            return sim.clear(nx, ny, ch) == "success"
        if res2 == "direction":
            b2 = r2["svd_deg"]
            obs.append(((nx, ny), b2))
            if _bearing_diff(b, b2) > 90.0:      # 越界：步长减半
                step = max(step * 0.5, 4.0)
            else:                                 # 仍朝源
                step = min(step * 1.6, 600.0)
            r = r2
        else:
            # 移动后失联：退回 (px,py) 已知可测点，缩步长再试
            step = max(step * 0.5, 4.0)
            r = sim.measure(px, py, ch)
    return ch in sim.cleared


def local_search_http(sim, ch, obs, radii=(8.0, 15.0, 25.0, 40.0, 60.0)):
    """当前位置附近的同心近邻尝试清除（覆盖 ≤20 m 但未触发 near 的情形）。"""
    cx, cy = sim.pos
    for rad in radii:
        for k in range(6):
            a = math.radians(60.0 * k)
            nx, ny = cx + rad * math.cos(a), cy + rad * math.sin(a)
            if sim.clear(nx, ny, ch) == "success":
                return True
            m = sim.measure(nx, ny, ch)
            if m["measure_result"] == "direction":
                obs.append(((nx, ny), m["svd_deg"]))
            elif m["measure_result"] == "near":
                if sim.clear(nx, ny, ch) == "success":
                    return True
    return False


def engage_http(sim, ch, obs, max_iter=8):
    """对频道 ch 执行 交会定位 → 越界检测归航 → 局部搜索，仅用可观测量。"""
    for _ in range(max_iter):
        if ch in sim.cleared:
            return True
        est = best_single_fix(obs)
        if est is not None:
            r = sim.measure(est[0], est[1], ch)   # 移动隐含于 measure
            if r["measure_result"] == "near":
                if sim.clear(est[0], est[1], ch) == "success":
                    return True
            elif r["measure_result"] == "direction":
                obs.append((est, r["svd_deg"]))
        if home_http(sim, ch, obs):
            return True
        # 盲区回退：从已知可测观测点重新逼近（定向源专用）
        if obs:
            p = obs[len(obs) // 2][0]
            sim.measure(p[0], p[1], ch)
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

    n_src = len(sim.sources) if hasattr(sim, "sources") else None
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