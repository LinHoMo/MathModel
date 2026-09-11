#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""travel_audit.py —— 行程审计：移动花在哪，以及归航段离下界多远。

为什么需要它：实测总时间 **69–73% 是移动**、measure 只占 22–25%，所以判断"还能优化
什么"必须先知道移动怎么分配。本工具把一局的移动拆成两段，并给出归航段的**严格下界**：

  - **扫描段** = 点集的最近邻路径长度（纯几何量，与运行无关，可事先算）
  - **归航段** = 实测总移动 − 扫描段
  - **下界** = 源位置的 **MST 权重**（TSP 的经典下界：清除行程至少要连通所有源；
    真实所需只会更多，因为还要走到每源 20 m 内并可能重试）
  - **冗余倍数** = 归航段 / 下界

这个倍数是**判据**而非描述：接近 1 说明清除行程已接近必需；远大于 1 说明有可归因的
浪费（例如归航不准导致反复试探）。cumcm2026b 首测即用它定位到 Q4 的 3.45× 冗余。

运行：``py -3.12 -X utf8 -m travel_audit``
"""
from __future__ import annotations

import math


def nn_route_length(points: list, start: tuple = (0.0, 0.0)) -> float:
    """最近邻遍历给定点集的路径长度（点集顺序由最近邻贪心决定）。"""
    rem = list(points)
    cur = start
    total = 0.0
    while rem:
        j = min(range(len(rem)), key=lambda i: math.dist(cur, rem[i]))
        nxt = rem.pop(j)
        total += math.dist(cur, nxt)
        cur = nxt
    return total


def mst_weight(points: list) -> float:
    """Prim 最小生成树权重（TSP 的经典下界，零依赖朴素 O(n²)）。"""
    n = len(points)
    if n < 2:
        return 0.0
    inside = {0}
    total = 0.0
    while len(inside) < n:
        best = None
        for i in inside:
            pi = points[i]
            for j in range(n):
                if j in inside:
                    continue
                d = math.dist(pi, points[j])
                if best is None or d < best[1]:
                    best = (j, d)
        inside.add(best[0])
        total += best[1]
    return total


def audit_travel(total_move_m: float, points: list, sources: list) -> dict:
    """把实测总移动拆成扫描段 / 归航段，并给出归航段的 MST 下界与冗余倍数。"""
    scan = nn_route_length(points, (0.0, 0.0))
    engage = float(total_move_m) - scan
    lower = mst_weight(sources)
    total = float(total_move_m)
    return {
        "total_move_m": total,
        "scan_m": scan,
        "engage_m": engage,
        "scan_share": (scan / total) if total else None,
        "engage_share": (engage / total) if total else None,
        "sources_mst_lower_bound_m": lower,
        # 单个源 / 无源时 MST=0，倍数不可比 —— 返回 None，不报 inf 冒充数值
        "engage_over_lower_bound": (engage / lower) if lower > 0 else None,
    }


def main() -> int:
    import sys
    from pathlib import Path

    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    from simulator_http import MockSimulatorServer, SimulatorHTTP
    import solve_b as B
    import solve_b_http as M

    for port, (km, tag) in enumerate(((False, "Q3 全向"), (True, "Q4 混合")), start=2481):
        srv = MockSimulatorServer(port=port, seed=42, kind_mix=km)
        srv.start()
        try:
            sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{port}",
                                robot_id="TRAVEL-AUDIT", timeout=30.0)
            sim.enter()
            pts = B.coverage_detection_points(km)
            st = M.dog_strategy_http(sim, has_directional=km, points=pts)
            sim.exit()
            srcs = [(s.x, s.y) for s in srv.sources]
            a = audit_travel(st["move_dist_m"], pts, srcs)
            print(f"[{tag}] 源={len(srcs)} 点={len(pts)} clear动作={st['n_clear_actions']}")
            print(f"    总移动 {a['total_move_m']:.0f} m = 扫描段 {a['scan_m']:.0f} m"
                  f"（{a['scan_share']:.0%}）+ 归航段 {a['engage_m']:.0f} m"
                  f"（{a['engage_share']:.0%}）")
            ratio = a["engage_over_lower_bound"]
            print(f"    源 MST 下界 {a['sources_mst_lower_bound_m']:.0f} m"
                  f" → 归航冗余 {ratio:.2f}×" if ratio else "    下界为 0（源不足）")
        finally:
            srv.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
