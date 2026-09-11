#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hex_spacing_sweep.py —— 三角格子的间距扫描（M-SELECT-006 的初筛实验）。

为什么需要它：覆盖几何由「点数 ↔ 覆盖半径」的权衡决定——覆盖半径小 ⇒ 源离检测点近
⇒ 归航段短；点数少 ⇒ measure 次数少。三角格子的**间距 d** 就是这个旋钮，但此前
只试过 d=1500 一个值。本工具按 d 扫描并落盘，使模型描述文档里的初筛数字可追溯。

结果用于**选参**；是否采纳由 `candidate_select --trials 10` 的配对 CI 裁决（初筛的
5 seeds 不构成结论——本项目已实测过 5 seeds 与 10 seeds 会给出不同判定）。

运行：``py -3.12 -X utf8 -m hex_spacing_sweep``
输出：``artifacts/results/hex_spacing_sweep.json`` + 并入 ``all_results.json``
"""
from __future__ import annotations

import json
import math
import os
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

SEEDS = (42, 43, 44, 45, 46)
SPACINGS = (900, 1000, 1200, 1500)
DIR_RADIUS = 2000.0


def hex_points_with_outer_ring(radius: float, spacing: float,
                               has_directional: bool) -> list:
    """三角格子；定向场景显式补外环（格子的下一环在 d·√3，无法自行外扩）。"""
    from candidate_select import hex_points

    pts = hex_points(radius, spacing)
    if not has_directional:
        return pts
    n = max(6, int(math.ceil(2.0 * math.pi * DIR_RADIUS / spacing)))
    return pts + [(DIR_RADIUS * math.cos(2.0 * math.pi * k / n),
                   DIR_RADIUS * math.sin(2.0 * math.pi * k / n))
                  for k in range(n)]


def sweep() -> dict:
    from simulator_http import MockSimulatorServer, SimulatorHTTP
    import solve_b_http as M
    from candidate_select import coverage_radius

    out: dict = {"milestone": "M-SELECT-006", "seeds": list(SEEDS),
                 "spacings_m": list(SPACINGS),
                 "method": "5 seeds 初筛（选参用；是否采纳由 10-seed 配对 CI 裁决）"}
    base_port = 2700
    for km, tag in ((False, "q3_omni"), (True, "q4_mix")):
        radius = DIR_RADIUS if km else 1800.0
        out[tag] = {}
        for d in SPACINGS:
            pts = hex_points_with_outer_ring(radius, float(d), km)
            rows = []
            for i, sd in enumerate(SEEDS):
                port = base_port + (0 if not km else 30) + i
                srv = MockSimulatorServer(port=port, seed=sd, kind_mix=km)
                srv.start()
                try:
                    sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{port}",
                                        robot_id="HEX-SWEEP", timeout=30.0)
                    sim.enter()
                    r = M.dog_strategy_http(sim, has_directional=km, points=pts)
                    sim.exit()
                    sm = srv.summary()
                    rows.append({
                        "T_total_s": r["virtual_time_s"],
                        "n_measure": r["n_measure"],
                        "move_dist_m": r["move_dist_m"],
                        "cleared_fraction": (sm["cleared"] / sm["total_sources"]
                                             if sm["total_sources"] else 1.0)})
                finally:
                    srv.stop()
            mean = lambda k: st.fmean([x[k] for x in rows])   # noqa: E731
            out[tag][f"d{d}"] = {
                "spacing_m": d,
                "n_points": len(pts),
                "coverage_radius_m": coverage_radius(
                    pts, radius=radius, n_theta=121, n_rho=61),
                "mean_total_time_s": mean("T_total_s"),
                "mean_n_measure": mean("n_measure"),
                "mean_move_dist_m": mean("move_dist_m"),
                "mean_cleared_fraction": mean("cleared_fraction"),
            }
            o = out[tag][f"d{d}"]
            print(f"[{tag}] d={d:4d} n={o['n_points']:3d} "
                  f"cov={o['coverage_radius_m']:6.1f}m "
                  f"T={o['mean_total_time_s']:8.1f}s "
                  f"nm={o['mean_n_measure']:6.1f} "
                  f"move={o['mean_move_dist_m']:9.1f}m "
                  f"f={o['mean_cleared_fraction']:.4f}")
    return out


def _merge(out: dict) -> None:
    allres = HERE.parent.parent / "all_results.json"
    data: dict = {}
    if allres.exists():
        try:
            data = json.loads(allres.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    seg: dict = {"milestone": out["milestone"], "seeds": out["seeds"],
                 "spacings_m": out["spacings_m"], "method": out["method"]}
    for tag in ("q3_omni", "q4_mix"):
        for key, o in out[tag].items():
            for field in ("spacing_m", "n_points", "coverage_radius_m",
                          "mean_total_time_s", "mean_n_measure",
                          "mean_move_dist_m", "mean_cleared_fraction"):
                seg[f"{tag}_{key}_{field}"] = o[field]
    data["hex_spacing_sweep"] = seg
    allres.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"[OK] 已并入 {allres} 的 hex_spacing_sweep 段")


def main() -> int:
    out = sweep()
    p = HERE.parent / "results" / "hex_spacing_sweep.json"
    os.makedirs(p.parent, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {p}")
    _merge(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
