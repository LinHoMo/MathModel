#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q1 定位区域直径的独立交叉验证（verifier 产出，不改被测代码）。

背景 / 为什么需要
-----------------
对比组 b_win 的验证强度自述含「318 组算例双算法交叉验证」，而本实例 Q1 的定位区域
直径此前只有**单一路径**给出：solve_b.location_region（Sutherland–Hodgman 半平面
逐条裁剪求顶点）+ solve_b.polygon_diameter（凸包上 O(h²) 枚举顶点对求最远距离）。
单一实现的自证不构成交叉验证——一个共用的几何假设（例如半平面朝向、裁剪容差）
出错时，两条「都基于同一裁剪器」的路径会一起错。

本脚本用**与主算法不同的两条独立路径**复核同一批 Q1 算例的定位区域直径：

  路径 MAIN（基准，被测实现）：
      solve_b.location_region（S-H 裁剪）+ solve_b.polygon_diameter（凸包暴力 O(h²)）。

  路径 A（射线两两求交枚举顶点对）：
      每个站点示向度 b 的 ±ε 误差界给出 2 条边界线 ⇒ 全部 2m 条约束线。
      枚举全部 C(2m,2) 对边界线求交，保留满足**全部** 2m 个半平面约束的交点，
      即区域的顶点集合（不裁剪、不凸包）。直径 = 顶点对最大距离。
      —— 与 MAIN 在区域构造与直径计算两处都不共享代码。

  路径 B（凸包 + 旋转卡壳）：
      对路径 A 得到的顶点集做 Andrew 单调链凸包，再用旋转卡壳（O(h)）求最远点对。
      —— 与路径 A 只共享顶点集，直径算法完全不同（线性 vs 二次）。

判据 / 报告
-----------
对同一批算例（v2 三个 Q1 算例 + 反例三角形 + N 组随机可行构型）分别取三路直径，
报告：
  rel_dev_A_vs_MAIN = max |D_A − D_MAIN| / D_MAIN  （区域构造+直径双重独立）
  rel_dev_B_vs_A    = max |D_B − D_A|    / D_A     （直径算法独立）
  两路最大相对偏差 = max(rel_dev_A_vs_MAIN, rel_dev_B_vs_A)
阈值 REL_DEV_TOL：两点裁剪/求交的数值容差量级，取 1e-6（相对）即视为一致。

运行：py -3.12 -X utf8 -m verify_q1_diameter_xcheck [--n-random 200]
输出：projects/cumcm2026b/artifacts/q1_diameter_xcheck.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import solve_b as B  # noqa: E402  被测主算法（只读调用，不修改）

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.abspath(os.path.join(HERE, "..", "q1_diameter_xcheck.json"))

EPS_DEG = 1.0            # 示向度误差界 / °
REL_DEV_TOL = 1e-6       # 两路一致性阈值（相对）
SEED = 42                # AGENTS.md 铁律：随机种子固定 42


# --------------------------------------------------------------------------
# 路径 A：射线两两求交 —— 半平面约束的构造与顶点枚举
# --------------------------------------------------------------------------
def _halfplanes(stations, bearings_deg, eps_deg=EPS_DEG):
    """每站点 ±ε 两条边界线 → 全部约束 a·P ≥ c（统一为「大于等于」形式）。

    示向度 b：P 相对 S 的方位落在 [b−ε, b+ε]。
      下界 u=unit(b−ε)：cross(u, P−S) ≥ 0 ⇒ (−u_y)·Px + u_x·Py ≥ (−u_y·Sx + u_x·Sy)
      上界 v=unit(b+ε)：cross(v, P−S) ≤ 0 ⇒ v_y·Px + (−v_x)·Py ≥ v_y·Sx + (−v_x)·Sy
    """
    out = []
    for (sx, sy), b in zip(stations, bearings_deg):
        for ang, lo in ((b - eps_deg, True), (b + eps_deg, False)):
            dx = math.cos(math.radians(ang))
            dy = math.sin(math.radians(ang))
            if lo:
                a, bb = -dy, dx
            else:
                a, bb = dy, -dx
            c = a * sx + bb * sy
            out.append((a, bb, c))
    return out


def _line_intersection(l1, l2, tol=1e-12):
    """边界线 a·x + b·y = c 两两求交；近平行（|det| 极小）返回 None。"""
    a1, b1, c1 = l1
    a2, b2, c2 = l2
    det = a1 * b2 - a2 * b1
    if abs(det) < tol:
        return None
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    return (x, y)


def _feasible(pt, halfplanes, tol=1e-7):
    x, y = pt
    return all(a * x + b * y >= c - tol for (a, b, c) in halfplanes)


def region_vertices_by_ray_intersection(stations, bearings_deg, eps_deg=EPS_DEG):
    """路径 A：枚举全部边界线两两求交，保留可行交点 = 区域顶点集（无序）。"""
    hps = _halfplanes(stations, bearings_deg, eps_deg)
    verts = []
    n = len(hps)
    for i in range(n):
        for j in range(i + 1, n):
            p = _line_intersection(hps[i], hps[j])
            if p is None:
                continue
            if _feasible(p, hps):
                verts.append(p)
    # 去重（容差内视为同一点）
    dedup = []
    for p in verts:
        if not any(math.dist(p, q) < 1e-7 for q in dedup):
            dedup.append(p)
    return dedup


def diameter_bruteforce(pts):
    """顶点对最大距离（O(h²)）——路径 A 的直径。"""
    best = 0.0
    pair = None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = math.dist(pts[i], pts[j])
            if d > best:
                best, pair = d, (pts[i], pts[j])
    return best, pair


# --------------------------------------------------------------------------
# 路径 B：Andrew 单调链凸包 + 旋转卡壳
# --------------------------------------------------------------------------
def convex_hull_andrew(pts):
    pts = sorted(set((round(x, 9), round(y, 9)) for x, y in pts))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def rotating_calipers_diameter(pts):
    """旋转卡壳求凸多边形直径（O(h)）。输入可为任意点集，内部先求凸包。"""
    hull = convex_hull_andrew(pts)
    n = len(hull)
    if n < 2:
        return 0.0, None
    if n == 2:
        return math.dist(hull[0], hull[1]), (hull[0], hull[1])

    def area2(a, b, c):
        return abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))

    best = 0.0
    pair = None
    k = 1
    for i in range(n):
        ni = (i + 1) % n
        while area2(hull[i], hull[ni], hull[(k + 1) % n]) > \
                area2(hull[i], hull[ni], hull[k]):
            k = (k + 1) % n
        for (p, q) in ((hull[i], hull[k]), (hull[ni], hull[k])):
            d = math.dist(p, q)
            if d > best:
                best, pair = d, (p, q)
    return best, pair


# --------------------------------------------------------------------------
# 三路对拍
# --------------------------------------------------------------------------
BBOX = 8000.0   # 与 solve_b.location_region 默认 bbox 一致


def _is_bounded(reg, bbox=BBOX, tol=1e-6):
    """区域是否有界：MAIN 用 ±bbox 初始框，若某顶点贴在 bbox 边界则该区域无界。

    无界区域的「直径」是 bbox 人为截断的产物（≈bbox 对角线），不是几何量，
    不参与直径一致性对拍（Q1 的真实交会构型均为有界凸多边形）。
    """
    return not any(abs(v[0]) >= bbox - tol or abs(v[1]) >= bbox - tol for v in reg)


def compare_case(name, stations, bearings_deg):
    """对单个算例跑三条路径，返回直径与相对偏差。"""
    # MAIN：被测实现
    reg = B.location_region(stations, bearings_deg, eps=EPS_DEG)
    base = {"name": name,
            "stations": [[round(sx, 4), round(sy, 4)] for sx, sy in stations],
            "bearings_deg": [round(b, 6) for b in bearings_deg]}
    if len(reg) < 3:
        return {**base, "degenerate": True, "n_vertices_main": len(reg)}
    if not _is_bounded(reg):
        return {**base, "unbounded": True, "n_vertices_main": len(reg)}
    d_main, pair_main, hull_main = B.polygon_diameter(reg)

    # A：射线两两求交
    vA = region_vertices_by_ray_intersection(stations, bearings_deg)
    d_A, pair_A = diameter_bruteforce(vA)

    # B：凸包 + 旋转卡壳（喂路径 A 的顶点集）
    d_B, pair_B = rotating_calipers_diameter(vA)

    def rel(x, ref):
        return abs(x - ref) / ref if ref > 0 else 0.0

    dev_A = rel(d_A, d_main)
    dev_B = rel(d_B, d_A)
    return {
        **base,
        "n_vertices_main": len(reg),
        "n_vertices_rayA": len(vA),
        "diameter_main_m": d_main,
        "diameter_rayA_m": d_A,
        "diameter_calipersB_m": d_B,
        "rel_dev_A_vs_MAIN": dev_A,
        "rel_dev_B_vs_A": dev_B,
        "agree": max(dev_A, dev_B) <= REL_DEV_TOL,
    }


def random_cases(n, seed=SEED):
    """随机可行构型：m∈{2,3} 站点 + 区域内源，真示向度 → 观测方程。"""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        m = rng.choice((2, 2, 3))
        G = (rng.uniform(-1200.0, 1200.0), rng.uniform(-1200.0, 1200.0))
        if math.hypot(*G) > 1700.0:
            continue
        stations = []
        ok = True
        for _s in range(m):
            S = (rng.uniform(-1700.0, 1700.0), rng.uniform(-1700.0, 1700.0))
            if math.hypot(*S) > 1750.0 or math.dist(S, G) < 100.0:
                ok = False
                break
            stations.append(S)
        if not ok:
            continue
        bears = [B._bearing(sx, sy, G[0], G[1]) for (sx, sy) in stations]
        out.append((f"random#{len(out)}", stations, bears))
    return out


def main(n_random=200):
    import solve_q1q2_v2 as V  # 复用 v2 的 Q1 算例定义（只读取常量坐标）

    # 1) v2 的三个 Q1 算例（站点/示向度直接取结果 JSON 的输入坐标）
    results = []
    for c in V.build_all()["problem1"]["cases"]:
        results.append(compare_case(c["name"], c["stations"],
                                    c["true_bearings_deg"]))
    # 2) 反例三角形
    tri = [(0.0, 0.0), (10.0, 0.0), (5.0, 6.0)]
    b_tri = [B._bearing(0.0, 0.0, 5.0, 6.0),
             B._bearing(10.0, 0.0, 5.0, 6.0)]
    results.append(compare_case("反例(锐角三角形)", tri[:2], b_tri))
    # 3) 随机可行构型
    for name, st, br in random_cases(n_random):
        results.append(compare_case(name, st, br))

    valid = [r for r in results if not r.get("degenerate")
             and not r.get("unbounded")]
    n_unbounded = sum(1 for r in results if r.get("unbounded"))
    n_degenerate = sum(1 for r in results if r.get("degenerate"))
    dev_A = max((r["rel_dev_A_vs_MAIN"] for r in valid), default=0.0)
    dev_B = max((r["rel_dev_B_vs_A"] for r in valid), default=0.0)
    all_agree = all(r["agree"] for r in valid)

    out = {
        "script": "verify_q1_diameter_xcheck.py",
        "seed": SEED,
        "n_cases_total": len(results),
        "n_cases_valid": len(valid),
        "n_cases_unbounded_excluded": n_unbounded,
        "n_cases_degenerate_excluded": n_degenerate,
        "paths": {
            "MAIN": "solve_b.location_region (S-H 裁剪) + solve_b.polygon_diameter (凸包暴力 O(h²))",
            "A": "射线两两求交枚举顶点对 + 顶点对最大距离",
            "B": "Andrew 凸包 + 旋转卡壳 O(h)",
        },
        "wrong_basis_diff": 0.0,
        "rel_dev_A_vs_MAIN": dev_A,
        "rel_dev_B_vs_A": dev_B,
        "max_rel_dev_two_paths": max(dev_A, dev_B),
        "rel_dev_tol": REL_DEV_TOL,
        "all_agree": all_agree,
        "cases": results,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"[Q1 直径交叉验证] 有效算例 {len(valid)}/{len(results)}")
    print(f"  A(射线求交) vs MAIN : max rel_dev = {dev_A:.3e}")
    print(f"  B(旋转卡壳) vs A    : max rel_dev = {dev_B:.3e}")
    print(f"  两路最大相对偏差    : {max(dev_A, dev_B):.3e}  "
          f"(tol {REL_DEV_TOL:.0e}, all_agree={all_agree})")
    for r in valid[:6]:
        print(f"    {r['name']:24s} MAIN={r['diameter_main_m']:.6f} "
              f"A={r['diameter_rayA_m']:.6f} B={r['diameter_calipersB_m']:.6f} m")
    print(f"[OK] {OUT_PATH}")
    return 0 if all_agree else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-random", type=int, default=200)
    a = ap.parse_args()
    raise SystemExit(main(n_random=a.n_random))
