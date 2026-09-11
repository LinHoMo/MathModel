#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v1（solve_b.py）缺陷审计 —— 把「v1 哪里错了」变成机器产出而非人工断言。

为什么要单独一个脚本：模型文档里要论证「v1 的算例不可行、反例手搓」。
这些论证本身就是数值（|S−G| = 2121.3 m、ρ = 0.5083 …），若手写进文档，
既无法追溯、又可能抄错。本脚本用 ast 直接解析 solve_b.py 源码取出字面量
（不重抄数字，源码改了审计跟着变），重算后落盘，供 model.md 引用。

审计项：
  D1 三个演示算例 |S−G| 是否落在有效接收半径内、站点是否在区域内
  D2 手搓反例三角形是否落在真实可达集之内（对比 v2 的 ρ 上确界）
  D3 v1 以「交会角 90°」为最优判据是否成立（对比垂线族 E[D] 单调性）

运行：python projects/cumcm2026b/artifacts/code/audit_v1_defects.py
输出：projects/cumcm2026b/artifacts/q1q2_v1_audit.json
"""
from __future__ import annotations

import ast
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "q1q2_v1_audit.json"

R_AREA = 1800.0
R_REC_MIN = 1000.0     # 保证可接收
R_REC_MAX = 1500.0     # 条件可行上界


def _literals_from_solve_b(src: Path):
    """从 solve_b.py 源码中取出 problem1_demo 里的 cases 与 tri 字面量。"""
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "problem1_demo")
    cases = tri = None
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "cases":
                    cases = ast.literal_eval(node.value)
                if isinstance(tgt, ast.Name) and tgt.id == "tri":
                    tri = ast.literal_eval(node.value)
    if cases is None or tri is None:
        raise RuntimeError("未能从 solve_b.py 解析出 cases / tri 字面量")
    return cases, tri


def main() -> int:
    import solve_q1q2_v2 as S2  # 复用 v2 的几何内核，保证口径一致

    src = HERE / "solve_b.py"
    cases, tri = _literals_from_solve_b(src)

    # ---- D1：演示算例可行性
    d1 = []
    for name, (stations, G) in cases.items():
        dists = [round(math.hypot(sx - G[0], sy - G[1]), 4) for sx, sy in stations]
        s_rad = [round(math.hypot(sx, sy), 4) for sx, sy in stations]
        d1.append({
            "case": name,
            "source": list(G),
            "stations": [list(s) for s in stations],
            "station_source_dist_m": dists,
            "station_radius_m": s_rad,
            "max_station_source_dist_m": round(max(dists), 4),
            "max_station_radius_m": round(max(s_rad), 4),
            "exceeds_recv_max": max(dists) > R_REC_MAX,
            "exceeds_area": max(s_rad) > R_AREA,
            "guaranteed": max(dists) <= R_REC_MIN and max(s_rad) <= R_AREA,
            "verdict": "不可行" if (max(dists) > R_REC_MAX or max(s_rad) > R_AREA)
                       else ("保证可行" if max(dists) <= R_REC_MIN else "条件可行"),
        })

    # ---- D2：手搓反例 vs 真实可达集
    D = S2.polygon_diameter(tri)
    _, r = S2.min_enclosing_circle(tri)
    rho_v1 = r / D
    sup = S2.q1_rho_supremum(n_chi=2000, n_ratio=40)
    rho_sup = sup["rho_sup_dense_scan"]
    d2 = {
        "triangle": [list(p) for p in tri],
        "diameter_m": round(D, 6),
        "mec_r_m": round(r, 6),
        "diam_circle_r_m": round(D / 2.0, 6),
        "rho_mec_over_D": round(rho_v1, 8),
        "required_enlarge_factor": round(2.0 * r / D, 8),
        "covers": S2.covers_by_diameter_circle(tri),
        "reachable_rho_sup": rho_sup,
        "reachable_argmax": sup["argmax"],
        "inside_reachable_set": rho_v1 <= rho_sup,
        "exaggeration_factor": round((rho_v1 - 0.5) / (rho_sup - 0.5), 2),
        "excess_over_half": round(rho_v1 - 0.5, 8),
        "reachable_excess_over_half": round(rho_sup - 0.5, 8),
        "verdict": ("落在真实可达集之外（手搓反例夸大失效）"
                    if rho_v1 > rho_sup else "可达但需说明"),
        "note": "该三角形是 solve_b.py 中的字面常量，不是由真源 + 站点经观测方程"
                "正向生成的；其 ρ 超出同类构型的可达上确界，故不能用作反例。",
    }

    # ---- D3：v1 的「交会角 90° 最优」判据
    rows = []
    R = 1200.0
    for off in (300.0, 600.0, 900.0, 1200.0, 1500.0):
        psi = math.degrees(math.atan2(off, R))
        d = math.hypot(R, off)
        e, f, w = S2._E_D((-500.0, 0.0), 20.0, psi, d, R)
        rows.append({"offset_m": off, "psi_deg": round(psi, 6), "d_m": round(d, 4),
                     "S2G_dist_m": round(off, 4), "E_D_m": round(e, 6),
                     "fail_prob": round(f, 8), "worst_D_m": round(w, 6)})
    d3 = {
        "claim": "v1 认为第二点应使交会角 φ = 90°（GDOP ∝ 1/sinφ 最小）",
        "closed_form": "垂线族（S₂ 落在过 G_est 且垂直 S₁→G_est 的直线上）上 "
                       "D = 2ε·√(R²+t²)，与 φ 无关；φ 在该族上恒为 90°",
        "rows": rows,
        "E_D_strictly_increasing": all(rows[i]["E_D_m"] < rows[i + 1]["E_D_m"]
                                       for i in range(len(rows) - 1)),
        "verdict": "φ=90° 无法区分该族上的点（全族同 φ），而 E[D] 随偏移严格递增，"
                   "故 φ 不是有效判据；v1 恰在该族上选了偏移最大的点",
    }

    out = {
        "schema_version": 1,
        "audit_target": "artifacts/code/solve_b.py::problem1_demo（v1）",
        "extraction": "ast.literal_eval 从源码解析 cases / tri，不重抄数字",
        "constants": {"R_AREA": R_AREA, "R_REC_MIN": R_REC_MIN, "R_REC_MAX": R_REC_MAX},
        "D1_case_feasibility": d1,
        "D2_counterexample_reachability": d2,
        "D3_optimality_criterion": d3,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"D1: " + "; ".join(f"{x['case']} → {x['verdict']}" for x in d1))
    print(f"D2: ρ_v1={d2['rho_mec_over_D']} vs 可达上确界 {rho_sup} → {d2['verdict']}"
          f"（夸大 {d2['exaggeration_factor']}×）")
    print(f"D3: E[D] 严格递增={d3['E_D_strictly_increasing']} → {d3['verdict']}")
    print(f"written -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
