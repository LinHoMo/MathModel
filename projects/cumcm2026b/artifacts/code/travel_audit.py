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


def _merge_into_all_results(report: dict) -> None:
    """并入项目根结果台账（供数值追溯：模型描述文档引用的审计数字可溯源）。"""
    import json
    from pathlib import Path

    allres = Path(__file__).resolve().parent.parent.parent / "all_results.json"
    data: dict = {}
    if allres.exists():
        try:
            data = json.loads(allres.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    seg: dict = {"milestone": "M-SELECT-004",
                 "method": "5 seeds × 2 场景，报均值（铁律：多种子 ≥5 次）"}
    # 改前基线：home_http 加 clear 尝试上限之前（commit 9ca95c8）的机器实测值。
    # 保留在台账里，使模型描述文档的「改前 → 改后」对照数字同样可追溯。
    seg["before_clear_budget_change"] = {
        "q3_omni_total_move_m": 22745, "q3_omni_scan_m": 11151,
        "q3_omni_engage_m": 11594, "q3_omni_sources_mst_lower_bound_m": 7641,
        "q3_omni_engage_over_lower_bound": 1.52,
        "q3_omni_engage_over_lower_bound_sd": 0.07,
        "q3_omni_n_clear_actions": 16.0,
        "q4_mix_total_move_m": 37351, "q4_mix_scan_m": 20629,
        "q4_mix_engage_m": 16723, "q4_mix_sources_mst_lower_bound_m": 6864,
        "q4_mix_engage_over_lower_bound": 2.42,
        "q4_mix_engage_over_lower_bound_sd": 0.64,
        "q4_mix_n_clear_actions": 28.0,
    }
    for tag, a in report.items():
        for k in ("total_move_m", "scan_m", "engage_m",
                  "sources_mst_lower_bound_m", "engage_over_lower_bound"):
            seg[f"{tag}_{k}"] = a.get(k)
        seg[f"{tag}_n_clear_actions"] = a.get("n_clear_actions")
        seg[f"{tag}_engage_over_lower_bound_sd"] = a.get("ratio_sd")
    data["travel_audit"] = seg
    allres.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"[OK] 已并入 {allres} 的 travel_audit 段")


def main() -> int:
    import statistics as st_mod
    import sys
    from pathlib import Path

    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    from simulator_http import MockSimulatorServer, SimulatorHTTP
    import solve_b as B
    import solve_b_http as M

    seeds = (42, 43, 44, 45, 46)   # 铁律：多种子 ≥5 次
    report: dict = {}
    for base_port, (km, tag) in enumerate(((False, "q3_omni"), (True, "q4_mix")),
                                          start=2481):
        pts = B.coverage_detection_points(km)
        rows = []
        for i, sd in enumerate(seeds):
            port = base_port + i * 3
            srv = MockSimulatorServer(port=port, seed=sd, kind_mix=km)
            srv.start()
            try:
                sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{port}",
                                    robot_id="TRAVEL-AUDIT", timeout=30.0)
                sim.enter()
                stt = M.dog_strategy_http(sim, has_directional=km, points=pts)
                sim.exit()
                srcs = [(s.x, s.y) for s in srv.sources]
                row = audit_travel(stt["move_dist_m"], pts, srcs)
                row["n_clear_actions"] = stt["n_clear_actions"]
                rows.append(row)
            finally:
                srv.stop()
        agg = {}
        for k in ("total_move_m", "scan_m", "engage_m",
                  "sources_mst_lower_bound_m", "engage_over_lower_bound",
                  "n_clear_actions"):
            vals = [r[k] for r in rows if r.get(k) is not None]
            agg[k] = (st_mod.fmean(vals) if vals else None)
        report[tag] = agg
        sd_ratio = (st_mod.stdev([r["engage_over_lower_bound"] for r in rows])
                    if len(rows) > 1 else 0.0)
        agg["ratio_sd"] = sd_ratio
        print(f"[{tag}] {len(seeds)} seeds 均值（点={len(pts)}）")
        print(f"    总移动 {agg['total_move_m']:.0f} m"
              f" = 扫描段 {agg['scan_m']:.0f} m + 归航段 {agg['engage_m']:.0f} m")
        print(f"    源 MST 下界 {agg['sources_mst_lower_bound_m']:.0f} m"
              f" → 归航冗余 {agg['engage_over_lower_bound']:.2f}×（±{sd_ratio:.2f}）"
              f" | clear 动作 {agg['n_clear_actions']:.1f}")

    _merge_into_all_results(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
