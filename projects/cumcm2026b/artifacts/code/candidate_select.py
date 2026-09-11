#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""candidate_select.py —— M-SELECT-002：候选机制策略对象化 + 信息感知第三候选。

承 M-SELECT-001（`a147a1d`：RING vs SPIRAL 的自动淘汰机制）之上，本轮做两件事：

1. **策略对象化**：候选不再是裸点集，而是 ``{"name", "points", "sweeper"?}``
   规格对象。``points`` 给覆盖几何，``sweeper``（可选）接管整个扫描阶段的调度
   ——这是「候选机制可替换」的接入点，也是 M-SELECT-001 遗留的"selector 是项目级
   函数、机制写死"的整改。RING / SPIRAL 是纯几何候选（无 sweeper）。

2. **信息感知第三候选 AIFIX**：几何与 RING 相同，差别只在**何时 engage**——
   ``solve_b_http.interleaved_sweeper`` 每测完一个站点，立刻对已具备交会条件
   （``best_single_fix`` 非空）的频道归航清除，而不是等整张覆盖网走完。
   **只对照"是否交错"，不夹带几何差异**——M-SELECT-001 的教训是给候选配不公平的
   几何会得出假结论，故 AIFIX 刻意复用 RING 点集，使对照单变量。

选择器（顺序不可换，两处共用同一套判据）
--------------------------------------
1. **feasibility gate**：清除比例 ≥ 1−α 才进入比较（不满足者直接淘汰）
2. **objective**：可行候选间比 J = E[T_total]（minimize），用 harness 的
   ``baseline_comparison``（ADR-0013/0014）
3. **secondary**：n_measure / move_dist / n_points 作为并列观测，不参与胜负判定

刻意**不读 checks_passed**（ADR-0013）。配对显著性：领先者与亚军均值差落在
95% CI 内 ⇒ 报 ``INCONCLUSIVE``，不宣布胜出。

统计口径
--------
paired evaluation：同一候选组跑**同一组 seeds**，逐 seed 求候选间 Δ，报告
mean ± std、95% CI、win rate。所有候选共用同一张覆盖网之外的一切代码路径。

运行：``py -3.12 -X utf8 -m candidate_select --trials 5``
输出：``artifacts/results/candidate_selection_m2.json``（M-SELECT-001 的
``candidate_selection.json`` 保留不动，便于对照两轮结论）。
"""
from __future__ import annotations

import argparse
import functools
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


def _run_cand(cand: dict, kind_mix: bool, seed: int, port: int):
    """按候选**规格对象**跑一局：points 给几何，sweeper（可选）接管扫描调度。"""
    srv = MockSimulatorServer(port=port, seed=seed, kind_mix=kind_mix)
    srv.start()
    try:
        sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{port}",
                            robot_id="M-SELECT-002", timeout=30.0)
        sim.enter()
        pts = cand["points"](kind_mix)
        swp = cand.get("sweeper")
        st = M.dog_strategy_http(
            sim, has_directional=kind_mix, points=pts,
            sweeper=(functools.partial(swp, points=pts) if swp else None))
        sim.exit()
        summ = srv.summary()
        n_src, n_clr = summ["total_sources"], summ["cleared"]
        return {
            "seed": seed,
            "cleared_fraction": (n_clr / n_src) if n_src else 1.0,
            "T_total_s": st["virtual_time_s"],
            "n_measure": st.get("n_measure"),
            "move_dist_m": st.get("move_dist_m"),
            "n_points": len(pts),
        }
    finally:
        srv.stop()


def paired_eval(cand_a, cand_b, kind_mix: bool, n_trials: int, base_port: int):
    """同一组 seeds 逐对评估，返回逐 seed 行与配对统计（M-SELECT-001 口径）。"""
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


def eval_candidates(cands: list[dict], kind_mix: bool, n_trials: int,
                    base_port: int) -> list[dict]:
    """N 候选逐 seed 配对评估：同一 seed 下所有候选跑同一 Mock 参数。"""
    rows = []
    for i in range(n_trials):
        sd = SEED + i
        per = {c["name"]: _run_cand(c, kind_mix, sd, base_port) for c in cands}
        rows.append({"seed": sd, **per})
    return rows


def paired_between(rows: list[dict], a: str, b: str) -> dict:
    """两候选的配对统计：Δ = T_a − T_b（同 seed 逐对）。"""
    d = [r[a]["T_total_s"] - r[b]["T_total_s"] for r in rows]
    mean_d = statistics.fmean(d)
    sd_d = statistics.stdev(d) if len(d) > 1 else 0.0
    half = 1.96 * sd_d / math.sqrt(len(d)) if len(d) > 1 else 0.0
    return {
        "delta_mean_s": mean_d,
        "delta_std_s": sd_d,
        "delta_ci95_halfwidth_s": half,
        "A_win_rate": sum(1 for x in d if x < 0) / len(d),
        "B_win_rate": sum(1 for x in d if x > 0) / len(d),
    }


# ---------------------------------------------------------------- 选择器
def select(cand_a_name: str, a: dict, cand_b_name: str, b: dict, *,
           alpha: float = 0.05, paired: dict | None = None) -> dict:
    """顺序固定（两候选版）：feasibility gate → objective → secondary。"""
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


def select_best(cands_agg: dict[str, dict], *, alpha: float = 0.05,
                paired: dict | None = None) -> dict:
    """N 候选选择器：同一套判据（feasibility → objective → 配对显著性）。

    ``paired``：``{(领先候选, 亚军候选): 配对统计}``；只对 top2 做噪声判定
    （多候选时逐对比 CI 会让"胜者"依赖比较顺序）。
    """
    thr = 1.0 - alpha
    feasible = {n: a["cleared_fraction"] >= thr for n, a in cands_agg.items()}
    gate = {"threshold": thr, "feasible": feasible,
            "rejected": sorted(n for n, ok in feasible.items() if not ok)}
    live = [n for n, ok in feasible.items() if ok]
    if not live:
        return {"stage": "feasibility", "winner": "NONE",
                "reason": "所有候选均未通过可行性闸门（清除比例 < 1−α）",
                "gate": gate}
    if len(live) == 1:
        return {"stage": "feasibility", "winner": live[0],
                "reason": "其余候选未通过可行性闸门", "gate": gate}

    ranked = sorted(live, key=lambda n: (cands_agg[n]["T_total_s"], n))
    best, second = ranked[0], ranked[1]
    best_t, second_t = cands_agg[best]["T_total_s"], cands_agg[second]["T_total_s"]
    pw = ((paired or {}).get((best, second))
          or (paired or {}).get((second, best)) or {})
    d_mean = pw.get("delta_mean_s")
    d_ci = pw.get("delta_ci95_halfwidth_s")
    # Δ 的符号取决于 tuple 顺序，统一取绝对值判噪声
    within_noise = (d_mean is not None and d_ci is not None
                    and abs(d_mean) <= d_ci)
    winner = "INCONCLUSIVE" if within_noise else best
    return {
        "stage": "objective",
        "winner": winner,
        "gate": gate,
        "ranked": ranked,
        "objective": {
            "metric": "T_total_s",
            "direction": "minimize",
            "best": best, "best_T_total_s": best_t,
            "runner_up": second, "runner_up_T_total_s": second_t,
            "abs_gap": best_t - second_t,
            "paired_delta_mean_s": d_mean,
            "paired_ci95_halfwidth_s": d_ci,
            "within_noise": within_noise,
        },
        "reason": ("领先者与亚军均值差落在 95% CI 内 ⇒ 与噪声不可分，不下胜负结论"
                   if within_noise else
                   f"{best} 以 T_total_s={best_t:.1f} s 领先 {second}"
                   f"（{second_t:.1f} s）"),
        "checks_passed_used": False,   # ADR-0013：验证检查数不作胜负依据
    }


def _mean_row(rows, key):
    vals = [r[key]["cleared_fraction"] for r in rows]
    ts = [r[key]["T_total_s"] for r in rows]
    return {"cleared_fraction": statistics.fmean(vals),
            "T_total_s": statistics.fmean(ts)}


# ---------------------------------------------------------------- 候选登记
RING_CAND = {"name": "RING", "points": ring_points}
SPIRAL_CAND = {"name": "SPIRAL", "points": spiral_for}
# AIFIX = RING 几何 + 交错扫描（唯一变量是"何时 engage"，见 interleaved_sweeper）
AIFIX_CAND = {"name": "AIFIX", "points": ring_points,
              "sweeper": M.interleaved_sweeper}
CANDIDATES = [RING_CAND, SPIRAL_CAND, AIFIX_CAND]


def _merge_into_all_results(out: dict) -> None:
    """把候选淘汰结果并入 ``all_results.json`` 的 candidate_selection 段。

    与 ``solve_b_http`` 并入 ``real_protocol_mock`` 同一惯例：模型描述文档引用的
    M-SELECT 数字必须能溯源到项目根结果台账（L4 数值追溯只认该台账 + 题面输入）。
    容差比较为相对 0.5%，故台账值与文档值须一致到该精度。
    """
    allres = HERE.parent.parent / "all_results.json"
    data: dict = {}
    if allres.exists():
        try:
            data = json.loads(allres.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    seg: dict = {"milestone": out["milestone"], "n_trials": out["n_trials"],
                 "seed_start": out["seed_start"], "candidates": out["candidates"]}
    for label, v in out["questions"].items():
        seg[f"{label}_decision"] = v["decision"]["winner"]
        for name, agg in v["candidates"].items():
            seg[f"{label}_{name}_mean_total_time_s"] = agg["T_total_s"]
            seg[f"{label}_{name}_cleared_fraction"] = agg["cleared_fraction"]
        for pair, st in v["paired"].items():
            k = pair.replace("|", "_")
            seg[f"{label}_dT_{k}_mean_s"] = st["delta_mean_s"]
            seg[f"{label}_dT_{k}_std_s"] = st["delta_std_s"]
            seg[f"{label}_dT_{k}_ci95_halfwidth_s"] = st["delta_ci95_halfwidth_s"]
            seg[f"{label}_dT_{k}_A_win_rate"] = st["A_win_rate"]
            seg[f"{label}_dT_{k}_B_win_rate"] = st["B_win_rate"]
    data["candidate_selection"] = seg
    allres.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"[OK] 已并入 {allres} 的 candidate_selection 段")


def main() -> int:
    ap = argparse.ArgumentParser(description="M-SELECT-002：策略对象化 + 信息感知第三候选")
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--port", type=int, default=2400)
    ap.add_argument("--alpha", type=float, default=0.05)
    args = ap.parse_args()

    names = [c["name"] for c in CANDIDATES]
    out: dict = {"milestone": "M-SELECT-002", "n_trials": args.trials,
                 "seed_start": SEED, "candidates": names, "questions": {}}
    for label, kind_mix in (("q3_omni", False), ("q4_mix", True)):
        rows = eval_candidates(CANDIDATES, kind_mix, args.trials, args.port)
        aggs = {n: _mean_row(rows, n) for n in names}
        pw = {}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                pw[(a, b)] = paired_between(rows, a, b)
        dec = select_best(aggs, alpha=args.alpha, paired=pw)
        out["questions"][label] = {
            "candidates": {n: aggs[n] for n in names},
            "paired": {f"{a}|{b}": {k: v for k, v in st.items()}
                       for (a, b), st in pw.items()},
            "rows": rows,
            "decision": dec,
        }
        line = "  ".join(f"{n}={aggs[n]['T_total_s']:.1f}s" for n in names)
        print(f"[{label}] {line}  → winner = {dec['winner']} (stage={dec['stage']})")
        for (a, b), st in pw.items():
            print(f"    ΔT({a}−{b}) = {st['delta_mean_s']:+.1f} ± "
                  f"{st['delta_std_s']:.1f} s (95%CI ±{st['delta_ci95_halfwidth_s']:.1f}), "
                  f"win rate {a}={st['A_win_rate']:.0%} {b}={st['B_win_rate']:.0%}")

    p = HERE.parent / "results" / "candidate_selection_m2.json"
    os.makedirs(p.parent, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {p}")
    _merge_into_all_results(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
