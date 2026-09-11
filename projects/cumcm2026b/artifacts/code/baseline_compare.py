#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""baseline_compare.py —— 策略对照实验：模型策略 vs 朴素基线。

为什么需要
----------
此前所有结果都只报绝对值（如「平均总任务时间 6131.94 s」），**没有任何参照**，
因此回答不了「这个数到底好不好」。本脚本给出第一个可运行的对照，把
「模型策略 vs 朴素基线」的差距量化成 ΔT 与相对改进 G：

    ΔT = T_model − T_baseline          （负值 = 模型更快）
    G  = (T_baseline − T_model) / T_baseline

对照的公平性约束（只替换 strategy，其余完全相同）
------------------------------------------------
* 同一协议客户端（SimulatorHTTP）与同一 Mock 服务端（MockSimulatorServer）
* 同一清除规则、同一时间计价、同一随机种子（42 起连续）
* 同一检测点集合（**同样的点**，只改遍历顺序）
* 同一目标区域 / 接收半径 / 频道数等题面常量

基线的定义（刻意"简单但可行"）
----------------------------
**B0 朴素策略**：把优化前的两项策略选择退回朴素版本，其余不动 ——
  1. 覆盖点按**环生成顺序**遍历（不做最近邻路线排序）；
  2. 归航用**固定步长**步进 + 示向度反转缩步长（不做交会几何逼近）。
这正是本仓 297ba6d 之前的策略形态，因此它既是「朴素基线」，也是「我们优化掉了什么」
的实测记录。两份策略都要求达到相同的清除比例，只比时间——否则比的就不是"多快"。

运行：``py -3.12 -X utf8 -m baseline_compare --trials 5``
输出：``artifacts/results/baseline_comparison.json``
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from simulator_http import (  # noqa: E402
    MockSimulatorServer, N_CHANNEL, SEED, SimulatorHTTP,
)
import solve_b as B  # noqa: E402
import solve_b_http as M  # noqa: E402


# --------------------------------------------------------------------------
# 基线策略：与模型策略共用 sweep/clear，只在「遍历顺序」与「归航方式」上退回朴素
# --------------------------------------------------------------------------
def baseline_points(has_directional: bool = False):
    """与模型同一点集，但保持**环生成顺序**（不做最近邻排序）。"""
    radii = B.COVER_RADII_DIR if has_directional else B.COVER_RADII_OMNI
    pts = []
    for r in radii:
        pts += B.ring_detection_points(r, B._cover_ring_step(r))
    return pts


def naive_home(sim, ch, obs, step0: float = 400.0, n_iter: int = 16):
    """朴素归航：固定步长沿示向度步进，仅在示向度反转时缩步长（不做交会定位）。"""
    step = step0
    px, py = sim.pos
    r = sim.measure(px, py, ch)
    for _ in range(n_iter):
        res = r["measure_result"]
        if res == "near":
            return sim.clear(px, py, ch) == "success"
        if res != "direction":
            return False
        b = r["svd_deg"]
        obs.append(((px, py), b))
        nx, ny = M._step_along((px, py), b, step)
        r2 = sim.measure(nx, ny, ch)
        res2 = r2["measure_result"]
        if res2 == "near":
            return sim.clear(nx, ny, ch) == "success"
        if res2 == "direction":
            obs.append(((nx, ny), r2["svd_deg"]))
            if M._bearing_diff(b, r2["svd_deg"]) > 90.0:
                step = max(step * 0.5, 4.0)
            else:
                step = min(step * 1.6, 600.0)
            px, py, r = nx, ny, r2
        else:
            step = max(step * 0.5, 4.0)
            r = sim.measure(px, py, ch)
    return ch in sim.cleared


def baseline_engage(sim, ch, obs, max_iter: int = 8):
    """朴素逐频道清除：不做交会定位直达，直接靠朴素归航逼近。"""
    for _ in range(max_iter):
        if ch in sim.cleared:
            return True
        if naive_home(sim, ch, obs):
            return True
        if ch in sim.cleared:
            return True
        # 盲区回退：从已知可测观测点重试
        if obs:
            p = obs[len(obs) // 2][0]
            sim.measure(p[0], p[1], ch)
            if naive_home(sim, ch, obs):
                return True
    return ch in sim.cleared


def dog_strategy_baseline(sim, has_directional: bool = False):
    """朴素基线策略：环生成顺序扫描 + 朴素归航。返回统计 dict（口径同模型策略）。"""
    obs = {ch: [] for ch in range(1, N_CHANNEL + 1)}
    det_time: dict[int, float] = {}
    clear_time: dict[int, float] = {}

    M.sweep_http(sim, baseline_points(has_directional), obs, det_time)

    pending = [ch for ch in obs if obs[ch] and ch not in sim.cleared]

    def _anchor(ch):
        return obs[ch][0][0] if obs[ch] else (0.0, 0.0)

    while pending:
        ch = min(pending, key=lambda c: math.dist(sim.pos, _anchor(c)))
        pending.remove(ch)
        if ch in sim.cleared:
            continue
        if baseline_engage(sim, ch, obs[ch]):
            clear_time[ch] = sim.virtual_time

    residual = [ch for ch in obs if obs[ch] and ch not in sim.cleared]
    if residual:
        M.sweep_http(sim, B.ring_detection_points(900.0, 400.0), obs, det_time)
        for ch in [c for c in obs if obs[c] and c not in sim.cleared]:
            if baseline_engage(sim, ch, obs[ch]):
                clear_time[ch] = sim.virtual_time

    per_src = [clear_time[ch] - det_time[ch] for ch in clear_time if ch in det_time]
    return {
        "virtual_time_s": sim.virtual_time,
        "n_cleared": len(sim.cleared),
        "mean_locate_clear_time_s": (
            float(sum(per_src) / len(per_src)) if per_src else float("inf")),
    }


# --------------------------------------------------------------------------
# 对照执行
# --------------------------------------------------------------------------
def _run(strategy, kind_mix: bool, seed: int, port: int):
    srv = MockSimulatorServer(port=port, seed=seed, kind_mix=kind_mix)
    srv.start()
    try:
        sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{port}",
                            robot_id="BASELINE-CMP", timeout=30.0)
        sim.enter()
        st = strategy(sim, kind_mix)
        sim.exit()
        summ = srv.summary()
        n_src = summ["total_sources"]
        n_clr = summ["cleared"]
        return {
            "seed": seed,
            "n_sources": n_src,
            "n_cleared": n_clr,
            "cleared_fraction": (n_clr / n_src) if n_src else 1.0,
            "total_time_s": st["virtual_time_s"],
            # 摊薄口径（ADR-0012）：总虚拟时间 / 已清除源数
            "avg_locate_clear_time_s": (st["virtual_time_s"] / n_clr) if n_clr else None,
        }
    finally:
        srv.stop()


def compare(n_trials: int = 5, base_port: int = 2300) -> dict:
    out: dict = {"n_trials": n_trials, "seed_start": SEED, "questions": {}}
    for label, kind_mix in (("q3_omni", False), ("q4_mix", True)):
        rows = []
        for i in range(n_trials):
            sd = SEED + i
            base = _run(dog_strategy_baseline, kind_mix, sd, base_port)
            model = _run(M.dog_strategy_http, kind_mix, sd, base_port)
            tb, tm = base["total_time_s"], model["total_time_s"]
            rows.append({
                "seed": sd,
                "cleared_fraction_baseline": base["cleared_fraction"],
                "cleared_fraction_model": model["cleared_fraction"],
                "T_baseline_s": tb,
                "T_model_s": tm,
                "delta_T_s": tm - tb,
                "G": ((tb - tm) / tb) if tb else None,
            })
        Tb = [r["T_baseline_s"] for r in rows]
        Tm = [r["T_model_s"] for r in rows]
        cf_b = [r["cleared_fraction_baseline"] for r in rows]
        cf_m = [r["cleared_fraction_model"] for r in rows]
        mean_tb, mean_tm = statistics.fmean(Tb), statistics.fmean(Tm)
        out["questions"][label] = {
            "rows": rows,
            "T_baseline_mean_s": mean_tb,
            "T_model_mean_s": mean_tm,
            "delta_T_mean_s": mean_tm - mean_tb,
            "G_mean": ((mean_tb - mean_tm) / mean_tb) if mean_tb else None,
            "cleared_fraction_baseline_mean": statistics.fmean(cf_b),
            "cleared_fraction_model_mean": statistics.fmean(cf_m),
            "fair_comparison": all(abs(a - b) < 1e-9 for a, b in zip(cf_b, cf_m)),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="策略对照实验：模型策略 vs 朴素基线")
    ap.add_argument("--trials", type=int, default=5, help="每问组数（种子自 42 起连续）")
    ap.add_argument("--port", type=int, default=2300)
    args = ap.parse_args()

    res = compare(args.trials, args.port)
    for label in ("q3_omni", "q4_mix"):
        q = res["questions"][label]
        print(f"[{label}] 组数={args.trials}")
        print(f"  T_baseline = {q['T_baseline_mean_s']:.1f} s   "
              f"T_model = {q['T_model_mean_s']:.1f} s")
        print(f"  ΔT = {q['delta_T_mean_s']:+.1f} s   G = {q['G_mean']:+.2%}")
        print(f"  清除比例 baseline={q['cleared_fraction_baseline_mean']:.4f}  "
              f"model={q['cleared_fraction_model_mean']:.4f}  "
              f"公平对照={q['fair_comparison']}")

    out = HERE.parent / "results" / "baseline_comparison.json"
    os.makedirs(out.parent, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
