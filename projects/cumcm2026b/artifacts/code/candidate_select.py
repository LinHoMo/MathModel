#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""candidate_select.py —— M-SELECT-001：真实任务上的自动模型淘汰。

这轮**不是为了证明螺旋更聪明**，而是为了证明
「提出候选 → 执行 → 取 objective → 比较 → 淘汰」这条机制能在真实任务上跑通。

候选结构（Baseline 与 Candidate 的角色不混）
-------------------------------------------
    baseline_compare（上一轮）: 模型 vs **朴素基线**（B0 = 预优化形态）—— 回答"好多少"
    本脚本（M-SELECT-001）    : RING vs **SPIRAL**（同为合理候选）—— 回答"选哪个"

两个候选**除 coverage geometry 外全同**：同一协议客户端、同一 Mock 服务端、同一清除
规则与时间计价、同一随机种子、同一交会归航代码路径（`dog_strategy_http(points=...)`）。
只把覆盖几何从同心环换成阿基米德螺线。

选择器（顺序不可换）
-------------------
1. **feasibility gate**：清除比例 ≥ 1−α 才进入比较（不满足者直接淘汰，不参与目标比较）
2. **objective**：在可行候选间比 J = E[T_total]（minimize），用 harness 的
   `baseline_comparison()`（ADR-0013：它能按方向判定谁更优并给出 gap）
3. **secondary**：n_measure / move_dist 作为并列观测，不参与胜负判定

刻意**不读 checks_passed** 作为胜负依据（ADR-0013）。

统计口径
--------
paired evaluation：两候选跑**同一组 seeds**，逐对求 Δ_i = T_A(s_i) − T_B(s_i)，
报告 mean ± std、95% CI、win rate —— 以区分"稳定优势"与"随机波动"。

运行：``py -3.12 -X utf8 -m candidate_select --trials 5``
输出：``artifacts/results/candidate_selection.json``
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
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from simulator_http import MockSimulatorServer, SEED, SimulatorHTTP  # noqa: E402
import solve_b as B  # noqa: E402
import solve_b_http as M  # noqa: E402


# ---------------------------------------------------------------- 候选 A：同心环
def ring_points(has_directional: bool = False):
    """候选 A 的覆盖几何 = 现模型的同心环（最近邻排序后遍历）。"""
    return B.coverage_detection_points(has_directional)


# ---------------------------------------------------------------- 候选 B：螺旋
SPIRAL_PITCH = 900.0   # 相邻圈径向间距 / m（< r_rec_min = 1000）
SPIRAL_STEP = 900.0    # 沿弧长的采样间隔 / m（< r_rec_min = 1000）


def spiral_points(radius: float = B.R_AREA, pitch: float = SPIRAL_PITCH,
                  step: float = SPIRAL_STEP, start: tuple = (0.0, 0.0)):
    """候选 B 的覆盖几何 = 阿基米德螺线（等弧长采样）。

    ρ(θ) = c·θ，c = pitch/(2π)：径向相邻圈间距恒为 pitch。沿弧长按 ``step`` 采样，
    使环向相邻检测点的弧距 ≤ step。两者都取 900 m < r_rec_min = 1000 m，
    故螺旋与同心环一样**覆盖完备**（数值验证见 verify_spiral_coverage）。

    与同心环的机制差异：路径连续（无环间跳跃），但大半径处同样角度间隔对应的弧长更长
    —— 这正是本仓早期螺旋方案漏检的根因；本实现用**等弧长采样**消掉了该缺陷，
    因此它是一个**合理的**对照候选，不是刻意做弱的陪跑。
    """
    c = pitch / (2.0 * math.pi)
    theta_max = 2.0 * math.pi * radius / pitch    # 细采样求累计弧长，再按弧长等距取点（解析 ∫√(θ²+1)dθ 直接可用，此处用数值更稳）
    n_fine = 20000
    thetas = [theta_max * i / n_fine for i in range(n_fine + 1)]
    cum = [0.0]
    for i in range(1, n_fine + 1):
        t0, t1 = thetas[i - 1], thetas[i]
        r0, r1 = c * t0, c * t1
        ds = math.hypot(r1 - r0, ((r0 + r1) / 2.0) * (t1 - t0))
        cum.append(cum[-1] + ds)
    total = cum[-1]
    n_pts = max(1, int(round(total / step)))
    pts = []
    j = 0
    for k in range(n_pts + 1):
        target = k * step
        while j < n_fine and cum[j + 1] < target:
            j += 1
        t = thetas[j]
        rho = c * t
        pts.append((start[0] + rho * math.cos(t), start[1] + rho * math.sin(t)))
    return pts


def spiral_for(has_directional: bool):
    """按场景给出螺旋几何：含定向源时把螺线**延伸到 r=2000 m**。

    与同心环的 {450, 1350, 2000} 平行 —— 朝外定向源的前向半盘在分布区之外，
    只扫到 1800 m 会**结构性漏掉**它们。不给这一条，螺旋在 Q4 就是陪跑而不是候选；
    本函数存在的意义就是保证两个候选只差"覆盖几何的形态"，不差"是否考虑了定向源"。
    """
    return spiral_points(radius=2000.0 if has_directional else B.R_AREA)


def coverage_radius(points, radius: float = B.R_AREA, n_theta: int = 721,
                    n_rho: int = 361) -> float:
    """圆域内「到最近检测点」的最大距离（覆盖完备性判据，越小越好）。"""
    worst = 0.0
    for i in range(n_theta):
        th = 2.0 * math.pi * i / n_theta
        for j in range(n_rho):
            rho = radius * (j + 1) / n_rho
            p = (rho * math.cos(th), rho * math.sin(th))
            d = min(math.dist(p, q) for q in points)
            if d > worst:
                worst = d
    return worst


# ---------------------------------------------------------------- 执行
def _run(points, kind_mix: bool, seed: int, port: int):
    srv = MockSimulatorServer(port=port, seed=seed, kind_mix=kind_mix)
    srv.start()
    try:
        sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{port}",
                            robot_id="M-SELECT-001", timeout=30.0)
        sim.enter()
        st = M.dog_strategy_http(sim, has_directional=kind_mix, points=points)
        sim.exit()
        summ = srv.summary()
        n_src, n_clr = summ["total_sources"], summ["cleared"]
        return {
            "seed": seed,
            "cleared_fraction": (n_clr / n_src) if n_src else 1.0,
            "T_total_s": st["virtual_time_s"],
            "n_measure": st.get("n_measure"),
            "move_dist_m": st.get("move_dist_m"),
            "n_points": len(points),
        }
    finally:
        srv.stop()


def paired_eval(cand_a, cand_b, kind_mix: bool, n_trials: int, base_port: int):
    """同一组 seeds 逐对评估，返回逐 seed 行与配对统计。"""
    rows = []
    for i in range(n_trials):
        sd = SEED + i
        a = _run(cand_a, kind_mix, sd, base_port)
        b = _run(cand_b, kind_mix, sd, base_port)
        rows.append({"seed": sd, "A": a, "B": b,
                     "delta_T_s": a["T_total_s"] - b["T_total_s"]})
    d = [r["delta_T_s"] for r in rows]
    mean_d = statistics.fmean(d)
    sd_d = statistics.stdev(d) if len(d) > 1 else 0.0
    half = 1.96 * sd_d / math.sqrt(len(d)) if len(d) > 1 else 0.0
    return {
        "rows": rows,
        "delta_mean_s": mean_d,
        "delta_std_s": sd_d,
        "delta_ci95_halfwidth_s": half,
        "A_win_rate": sum(1 for x in d if x < 0) / len(d),
        "B_win_rate": sum(1 for x in d if x > 0) / len(d),
    }


# ---------------------------------------------------------------- 选择器
def select(cand_a_name: str, a: dict, cand_b_name: str, b: dict, *,
           alpha: float = 0.05, paired: dict | None = None) -> dict:
    """顺序固定：feasibility gate → objective（harness baseline_comparison）→ secondary。"""
    from modeling_harness.runtime.evaluation.deterministic_metrics import (
        baseline_comparison,
    )
    thr = 1.0 - alpha
    feasible = {cand_a_name: a["cleared_fraction"] >= thr,
                cand_b_name: b["cleared_fraction"] >= thr}
    gate = {"threshold": thr, "feasible": feasible,
            "rejected": [k for k, v in feasible.items() if not v]}
    live = [k for k, v in feasible.items() if v]
    if not live:
        return {"stage": "feasibility", "winner": "NONE",
                "reason": "两候选均未通过可行性闸门（清除比例 < 1−α）", "gate": gate}
    if len(live) == 1:
        return {"stage": "feasibility", "winner": live[0],
                "reason": "另一候选未通过可行性闸门", "gate": gate}

    out_a = {k: v for k, v in a.items() if isinstance(v, (int, float))}
    out_b = {k: v for k, v in b.items() if isinstance(v, (int, float))}
    cmp_res = baseline_comparison(
        out_a, out_b, direction="minimize",
        directions={"cleared_fraction": "maximize"},
        keys=["T_total_s"],
    )
    better = cmp_res["better"]
    winner = {"a": cand_a_name, "b": cand_b_name}.get(
        better, "TIE" if better == "tie" else "NONE")
    # 配对显著性：均值差落在 95% CI 内 ⇒ 与噪声不可分，**不得宣布胜出**。
    # 只比均值会把「A 平均快 535 s」当成稳定优势，而它其实完全在波动范围内。
    d_mean = (paired or {}).get("delta_mean_s")
    d_ci = (paired or {}).get("delta_ci95_halfwidth_s")
    within_noise = (d_mean is not None and d_ci is not None
                    and abs(d_mean) <= d_ci)
    if within_noise:
        winner = "INCONCLUSIVE"
    return {
        "stage": "objective",
        "winner": winner,
        "gate": gate,
        "objective": {
            "metric": "T_total_s",
            "direction": "minimize",
            "A": a["T_total_s"], "B": b["T_total_s"],
            "abs_gap": cmp_res["detail"][0]["abs_gap"] if cmp_res.get("detail") else None,
            "rel_gap": cmp_res["detail"][0]["rel_gap"] if cmp_res.get("detail") else None,
            "better": better,
            "paired_delta_mean_s": d_mean,
            "paired_ci95_halfwidth_s": d_ci,
            "within_noise": within_noise,
        },
        "secondary": {k: {"A": a.get(k), "B": b.get(k)}
                      for k in ("n_measure", "move_dist_m", "n_points")},
        "reason": ("配对均值差 ±95%CI 跨 0，两候选与噪声不可分 ⇒ 不下胜负结论"
                   if within_noise else
                   f"按 objective {cmp_res['detail'][0]['abs_gap']:+.1f} s 判定 {winner} 胜出")
                  if cmp_res.get("detail") else "objective 不可比",
        "checks_passed_used": False,   # ADR-0013：验证检查数不作胜负依据
    }


def _mean_row(rows, key):
    vals = [r[key]["cleared_fraction"] for r in rows]
    ts = [r[key]["T_total_s"] for r in rows]
    return {"cleared_fraction": statistics.fmean(vals),
            "T_total_s": statistics.fmean(ts)}


def main() -> int:
    ap = argparse.ArgumentParser(description="M-SELECT-001：候选自动淘汰")
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--port", type=int, default=2400)
    ap.add_argument("--alpha", type=float, default=0.05)
    args = ap.parse_args()

    out: dict = {"milestone": "M-SELECT-001", "n_trials": args.trials,
                 "seed_start": SEED, "questions": {}}
    for label, kind_mix in (("q3_omni", False), ("q4_mix", True)):
        pe = paired_eval(ring_points(kind_mix), spiral_for(kind_mix), kind_mix,
                         args.trials, args.port)
        rows = pe["rows"]
        a_agg, b_agg = _mean_row(rows, "A"), _mean_row(rows, "B")
        dec = select("RING", a_agg, "SPIRAL", b_agg, alpha=args.alpha, paired=pe)
        out["questions"][label] = {
            "paired": {k: v for k, v in pe.items() if k != "rows"}, "rows": rows,
            "candidate_A": {"name": "RING", **a_agg},
            "candidate_B": {"name": "SPIRAL", **b_agg},
            "decision": dec,
        }
        print(f"[{label}] paired ΔT(A−B) = {pe['delta_mean_s']:+.1f} ± "
              f"{pe['delta_std_s']:.1f} s (95%CI ±{pe['delta_ci95_halfwidth_s']:.1f}), "
              f"win rate A={pe['A_win_rate']:.0%} B={pe['B_win_rate']:.0%}")
        print(f"  T_A={a_agg['T_total_s']:.1f}s  T_B={b_agg['T_total_s']:.1f}s  "
              f"→ winner = {dec['winner']} (stage={dec['stage']})")

    p = HERE.parent / "results" / "candidate_selection.json"
    os.makedirs(p.parent, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
