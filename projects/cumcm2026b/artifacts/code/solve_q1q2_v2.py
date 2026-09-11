#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026_B Q1/Q2 重建（v2）——修复 v1 的四处建模缺陷。

v1（solve_b.py）被证伪/修订的四点：
  D1 算例不可行：Q1 三个演示算例 |S−G| = 2121.3/1868.2/1920.9 m 均超有效接收半径上限
                 1500 m，站点自身距原点 3000/3002 m 超区域半径 1800 m。
                 → v2 从可行域内由真源反算生成算例，并逐条核对硬约束。
  D2 反例手搓：v1 反例用字面常量三角形 (0,0),(10,0),(5,6)，ρ=0.5083 远超该类构型
                 实际可达上确界 0.5002942（ρ 为相似不变量，2000×40 定向密集扫描），
                 夸大失效约 28.33 倍。
                 → v2 反例由正向模型生成（真源 + 站点 → 观测方程 → 反解），并同时
                   报告实测失效幅度与同类上确界。
  D3 决策变量错误：v1 把「交会角 φ=90°」当决策判据。φ 是 (ψ,d,R) 的因变量不是可控量；
                 且垂线族上 D = 2ε·√(R²+t²) 随偏移严格递增，v1 自己的权衡表
                 （43.19→67.08 m）已证明偏移越小越好，却仍推荐 offset=d_est。
                 → v2 以 (ψ,d) 为决策变量，目标为 E[D]。
  D4 不可观测量代入：v1 硬编码 d_est=1200（源距），但 /measure 只返回示向度。
                 → v2 不假设源距已知，对 R=|S₁G| 取期望，并在 ≥3 种先验下报
                   候选区与后悔值（不报单点最优）。

运行：python projects/cumcm2026b/artifacts/code/solve_q1q2_v2.py
输出：projects/cumcm2026b/q1q2_v2_results.json
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

# ---------------------------------------------------------------- 题面常量（硬约束单一来源）
R_AREA = 1800.0          # 圆形区域半径 / m
EPS_DEG = 1.0            # 示向度误差全局界 |δ| ≤ ε / °
R_REC_MIN = 1000.0       # 有效接收半径下界 / m —— 「保证可接收」半径：
#   赛题附录「有效接收半径 1000-1500 米」表示 r_rec 是未知参数、取值落在 [1000,1500]。
#   因此 |S−G| ≤ R_REC_MIN 时无论 r_rec 取何值都必然可接收（**保证可行**）；
#   R_REC_MIN < |S−G| ≤ R_REC_MAX 只在 r_rec 偏大时才可接收（**条件可行**，非保证）；
#   |S−G| > R_REC_MAX 恒不可接收（**不可行**）。
#   注意：不存在「太近不可接收」的下限（越近信号越强）；仅 |S−G| ≤ 5 m 时改用光学清除。
R_REC_MAX = 1500.0       # 有效接收半径上界 / m
R_OPTICAL = 5.0          # ≤5 m 改用光学定位+激光清除（不再测向）/ m
SEED = 42                # AGENTS.md：随机种子固定 42

EPS = math.radians(EPS_DEG)
BBOX = 4000.0            # 半平面交初始框（远大于区域，保证不截断真实交集）


# ---------------------------------------------------------------- 基础几何
def bearing(ax, ay, bx, by) -> float:
    """A→B 的示向度 / 度（0=+x 轴，逆时针）。"""
    return math.degrees(math.atan2(by - ay, bx - ax)) % 360.0


def ang_diff(a, b) -> float:
    """两方位角的最小夹角 / 度，取值 [0,180]。"""
    d = abs((a - b) % 360.0)
    return d if d <= 180.0 else 360.0 - d


def _clip(poly, a, c):
    """Sutherland–Hodgman 单半平面裁剪：保留 a·x ≤ c。"""
    if not poly:
        return []
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp = a[0] * p[0] + a[1] * p[1] - c
        fq = a[0] * q[0] + a[1] * q[1] - c
        if fp <= 0.0:
            out.append(p)
        if (fp < 0.0 < fq) or (fq < 0.0 < fp):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def wedge(S, b_deg):
    """示向度 b（含 ±ε 误差界）对应的两条半平面 a·x ≤ c。"""
    halfplanes = []
    for sign in (+1.0, -1.0):
        ang = math.radians(b_deg + sign * EPS_DEG)
        dx, dy = math.cos(ang), math.sin(ang)
        a = (-dy, dx) if sign > 0 else (dy, -dx)
        c = a[0] * S[0] + a[1] * S[1]
        halfplanes.append((a, c))
    return halfplanes


def location_region(stations, bearings_deg):
    """楔形交集 → 凸多边形顶点（逆时针）。空集返回 []。"""
    poly = [(-BBOX, -BBOX), (BBOX, -BBOX), (BBOX, BBOX), (-BBOX, BBOX)]
    for S, b in zip(stations, bearings_deg):
        for a, c in wedge(S, b):
            poly = _clip(poly, a, c)
            if not poly:
                return []
    return poly


def polygon_area(poly) -> float:
    if len(poly) < 3:
        return 0.0
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def polygon_diameter(poly) -> float:
    """凸多边形最远点对（顶点枚举 O(h²)）。"""
    if len(poly) < 2:
        return 0.0
    best = 0.0
    for i in range(len(poly)):
        for j in range(i + 1, len(poly)):
            d = math.hypot(poly[i][0] - poly[j][0], poly[i][1] - poly[j][1])
            if d > best:
                best = d
    return best


def _circle2(p, q):
    cx, cy = (p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0
    return (cx, cy), math.hypot(p[0] - q[0], p[1] - q[1]) / 2.0


def _circle3(p, q, r):
    ax, ay = p
    bx, by = q
    cx, cy = r
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay)
          + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx)
          + (cx * cx + cy * cy) * (bx - ax)) / d
    return (ux, uy), math.hypot(ax - ux, ay - uy)


def min_enclosing_circle(poly):
    """凸多边形顶点的最小包围圆（≤3 点定圆，暴力 O(h⁴) 足够，h 很小）。"""
    pts = poly[:]
    if not pts:
        return None, 0.0
    if len(pts) == 1:
        return pts[0], 0.0
    # 注意：best_r 必须从 +inf 起算。若用「不覆盖全部点的圆」作初值，
    # 后续三点定圆即使覆盖全部点也会因 r 更大而被错误丢弃。
    best_c, best_r = None, float("inf")
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            c, r = _circle2(pts[i], pts[j])
            if r < best_r and all(math.hypot(p[0] - c[0], p[1] - c[1]) <= r + 1e-9
                                  for p in pts):
                best_c, best_r = c, r
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            for k in range(j + 1, len(pts)):
                res = _circle3(pts[i], pts[j], pts[k])
                if res is None:
                    continue
                c, r = res
                if r < best_r and all(math.hypot(p[0] - c[0], p[1] - c[1]) <= r + 1e-9
                                      for p in pts):
                    best_c, best_r = c, r
    if best_c is None:                      # 退化：全部点重合
        return pts[0], 0.0
    return best_c, best_r


def covers_by_diameter_circle(poly) -> bool:
    """Thales 判据：Ω ⊆ C(A,B) ⟺ 所有顶点 P 满足 (P−A)·(P−B) ≤ 0。"""
    if len(poly) < 3:
        return True
    A, B = None, None
    dmax = -1.0
    for i in range(len(poly)):
        for j in range(i + 1, len(poly)):
            d = math.hypot(poly[i][0] - poly[j][0], poly[i][1] - poly[j][1])
            if d > dmax:
                dmax, A, B = d, poly[i], poly[j]
    for P in poly:
        if (P[0] - A[0]) * (P[0] - B[0]) + (P[1] - A[1]) * (P[1] - B[1]) > 1e-9:
            return False
    return True


def feasible_station(S, G, robust: bool = False) -> bool:
    """站点硬约束：在区域内 且 到源距离不超过有效接收半径。

    robust=False（默认）：|S−G| ≤ R_REC_MAX，即「可能存在某个 r_rec 使其可接收」。
    robust=True：|S−G| ≤ R_REC_MIN，即「无论 r_rec 取 [1000,1500] 内何值都可接收」。

    演示算例应取 robust=True：条件可行的算例在 r_rec 偏小时会整体失效，
    用它演示算法等于把结论建立在未知参数上。
    """
    lim = R_REC_MIN if robust else R_REC_MAX
    return (math.hypot(*S) <= R_AREA
            and R_OPTICAL < math.hypot(S[0] - G[0], S[1] - G[1]) <= lim)


# ---------------------------------------------------------------- Q1：可行算例 + 正向生成反例
def q1_case(name, stations, G, robust=True):
    """由真源 G 与站点正向生成观测（真示向度），再反解定位区域。"""
    bs = [bearing(s[0], s[1], G[0], G[1]) for s in stations]
    assert all(feasible_station(s, G, robust=robust) for s in stations), \
        f"{name}: 站点不满足硬约束（robust={robust}）"
    assert math.hypot(*G) <= R_AREA, f"{name}: 源不在区域内"
    poly = location_region(stations, bs)
    D = polygon_diameter(poly)
    c, r = min_enclosing_circle(poly)
    chi = None
    if len(stations) == 2:
        chi = ang_diff(bearing(G[0], G[1], stations[0][0], stations[0][1]),
                       bearing(G[0], G[1], stations[1][0], stations[1][1]))
    return {
        "name": name,
        "source": [round(G[0], 4), round(G[1], 4)],
        "stations": [[round(s[0], 4), round(s[1], 4)] for s in stations],
        "true_bearings_deg": [round(b, 6) for b in bs],
        "station_source_dist_m": [round(math.hypot(s[0] - G[0], s[1] - G[1]), 4)
                                  for s in stations],
        "crossing_angle_deg": round(chi, 6) if chi is not None else None,
        "n_vertices": len(poly),
        "diameter_m": round(D, 6),
        "area_m2": round(polygon_area(poly), 6),
        "diam_circle_r_m": round(D / 2.0, 6),
        "mec_r_m": round(r, 6),
        "rho_mec_over_D": round(r / D, 8) if D > 0 else None,
        "covers": covers_by_diameter_circle(poly),
        "feasible": True,
    }


def q1_rho_supremum(n_chi=2000, n_ratio=40):
    """定向密集扫描两站构型，求 ρ = r_MEC / D 的可达上确界。

    ρ 是相似不变量：整体缩放 (r₁,r₂)→(k r₁, k r₂) 时楔形角宽 2ε 不变、
    区域整体放大 k 倍，形状不变。故 ρ 只依赖 (χ, r₂/r₁)，扫描用这两个参数。
    随机采样只能给下界；上确界须在失效窗口 χ ∈ (90°, 90°+2ε) 内定向加密。
    """
    best = {"rho": 0.0}
    for i in range(1, n_chi):
        chi_deg = 90.0 + (2.0 * EPS_DEG) * i / n_chi
        chi = math.radians(chi_deg)
        for j in range(n_ratio):
            ratio = 10.0 ** (-1.0 + 2.0 * j / (n_ratio - 1))   # r₂/r₁ ∈ [0.1, 10]
            r1, r2 = 1000.0, 1000.0 * ratio
            G = (0.0, 0.0)
            S1 = (r1, 0.0)
            S2 = (r2 * math.cos(chi), r2 * math.sin(chi))
            poly = location_region([S1, S2],
                                   [bearing(S1[0], S1[1], G[0], G[1]),
                                    bearing(S2[0], S2[1], G[0], G[1])])
            if len(poly) < 3:
                continue
            D = polygon_diameter(poly)
            if D <= 0:
                continue
            c, r = min_enclosing_circle(poly)
            rho = r / D
            if rho > best["rho"]:
                best = {"rho": round(rho, 9), "chi_deg": round(chi_deg, 6),
                        "r2_over_r1": round(ratio, 6),
                        "diameter_m": round(D, 8), "mec_r_m": round(r, 8),
                        "required_enlarge_factor": round(2.0 * r / D, 9),
                        "covers": covers_by_diameter_circle(poly)}
    return {
        "rho_sup_dense_scan": best["rho"],
        "argmax": best,
        "n_chi": n_chi, "n_ratio": n_ratio,
        "invariance": "ρ 只依赖 (χ, r₂/r₁)，与绝对尺度无关（相似不变量）",
        "realizability": "扫描用 r₁=1000、r₂ 可到 10⁴ m（超出接收半径），但 ρ 是相似不变量："
                         "把 (r₁,r₂) 整体缩放到 max ≤ R_REC_MIN=1000 m 时楔形角宽 2ε 不变、"
                         "区域整体缩小、ρ 完全不变，且缩放后站点更靠近源、必在区域内。"
                         "故扫描给出的上确界可由「保证可行」的真实构型达到，不是空想上界。",
        "outside_window_rho": 0.5,
        "v1_synthetic_rho": 0.508333333,
        "v1_exaggeration_factor": round((0.508333333 - 0.5) / (best["rho"] - 0.5), 2),
        "note": "窗口外 ρ ≡ 1/2（直径两端点定圆）；窗口内略大于 1/2。"
                "v1 手搓反例 ρ=0.5083 超出可达上确界，落在真实可达集之外。",
    }


def q1_counterexample(n_scan=4000):
    """正向模型生成「直径圆不覆盖」反例，并给出该类构型 ρ 的实测上确界。

    失效窗口（已验证）：两站情形覆盖失败 ⟺ 源端交会角 χ ∈ (90°, 90°+2ε)。
    以真源 + 两站点正向生成，不写死任何几何常量。
    """
    rng = random.Random(SEED)
    fails, rho_max, best = [], 0.0, None
    n_accepted, n_window = 0, 0
    for _ in range(n_scan):
        Rg = R_AREA * math.sqrt(rng.random())
        th = rng.random() * 2 * math.pi
        G = (Rg * math.cos(th), Rg * math.sin(th))
        # 两站点：源端交会角 χ 均匀取遍 (85°, 100°)，距离落在「保证可接收」半径内
        # （取 robust：|S−G| ≤ 1000 m，使反例不依赖 r_rec 的实际取值）
        chi = math.radians(85.0 + 15.0 * rng.random())
        for _try in range(40):
            r1 = 600.0 + 400.0 * rng.random()
            r2 = 600.0 + 400.0 * rng.random()
            a0 = rng.random() * 2 * math.pi
            S1 = (G[0] + r1 * math.cos(a0), G[1] + r1 * math.sin(a0))
            S2 = (G[0] + r2 * math.cos(a0 + chi), G[1] + r2 * math.sin(a0 + chi))
            if (feasible_station(S1, G, robust=True)
                    and feasible_station(S2, G, robust=True)):
                break
        else:
            continue
        bs = [bearing(S1[0], S1[1], G[0], G[1]), bearing(S2[0], S2[1], G[0], G[1])]
        poly = location_region([S1, S2], bs)
        if len(poly) < 3:
            continue
        D = polygon_diameter(poly)
        if D <= 0:
            continue
        # 只在样本完整通过全部退化检查后才计数，保证 window_empirical_check 的分母与
        # 失效集合可比（否则「落入窗口」与「覆盖失败」两集合无法逐样本核对）。
        n_accepted += 1
        # 失效窗口是**开区间**：实测 χ=90.0° 覆盖成立、χ=90.0001° 起失败、
        # χ=91.9999° 仍失败、χ=92.0° 覆盖成立 ⇒ χ ∈ (90°, 90°+2ε)。右端必须用 <，
        # 用 <= 会把 χ=92.0°（覆盖成立）误计入失效窗口。
        if 90.0 < math.degrees(chi) < 90.0 + 2.0 * EPS_DEG:
            n_window += 1
        c, r = min_enclosing_circle(poly)
        chi_obs = ang_diff(bearing(G[0], G[1], S1[0], S1[1]),
                           bearing(G[0], G[1], S2[0], S2[1]))
        rho = r / D
        rho_max = max(rho_max, rho)
        if not covers_by_diameter_circle(poly):
            rec = {"source": [round(G[0], 4), round(G[1], 4)],
                   "stations": [[round(S1[0], 4), round(S1[1], 4)],
                                [round(S2[0], 4), round(S2[1], 4)]],
                   "crossing_angle_deg": round(chi_obs, 6),
                   "diameter_m": round(D, 6),
                   "area_m2": round(polygon_area(poly), 6),
                   "diam_circle_r_m": round(D / 2.0, 6),
                   "mec_r_m": round(r, 6),
                   "rho_mec_over_D": round(rho, 8),
                   "covers": False,
                   "required_enlarge_factor": round(2.0 * r / D, 8),
                   "generation": "forward_model(真源+站点→观测方程→反解)"}
            fails.append(rec)
            if best is None or rho > best["rho_mec_over_D"]:
                best = rec
    return {
        "window_theorem": "覆盖失败 ⟺ 源端交会角 χ ∈ (90°, 90°+2ε)（χ 取 min{Δ, 360−Δ}）",
        "n_scanned": n_scan,
        "n_accepted": n_accepted,
        "n_failures": len(fails),
        "window_empirical_check": {
            "sampling_range_deg": [85.0, 100.0],
            "theoretical_fail_rate": round(2.0 * EPS_DEG / 15.0, 6),
            "observed_fail_rate": round(len(fails) / n_accepted, 6) if n_accepted else None,
            "n_in_window_predicted": n_window,
            "agree": (n_window == len(fails)),
            "note": "χ ~ U(85°,100°) 时理论失效率 = 2ε/15°；"
                    "同时逐样本核对「落入窗口」与「覆盖失败」两个集合是否完全相等。",
        },
        "worst_case": best,
        "rho_sup_observed": round(rho_max, 8),
        "rho_sup_dense_scan": None,   # 由 q1_rho_supremum() 回填，见 main()
        "rho_sup_is_similarity_invariant": True,
        "jung_upper_bound": round(1.0 / math.sqrt(3.0), 8),
        "note": "真实失效幅度 = 需把直径圆放大到 2r_MEC/D 倍。上确界取 "
                "supremum_dense_scan.rho_sup_dense_scan（(χ, r₂/r₁) 定向密集扫描，"
                "ρ 为相似不变量故该扫描覆盖全部两站构型）；本函数随机采样只给下界，"
                "Jung 上界 1/√3 为严格但宽松的解析上界。",
    }


# ---------------------------------------------------------------- Q2：E[D] 决策
def _E_D(S1, b1_meas, psi_deg, d, R, nq=9, r_rec=None):
    """给定源距 R 与决策 (ψ,d)，对两次示向度误差 (δ₁,δ₂) 求 E[D] 与失效概率。

    决策只用可观测量 b1_meas；源距 R 不是观测量，由外层对先验取期望。
    r_rec：第二点能否收到信号的门限。赛题只给出 r_rec ∈ [1000,1500] 且机器狗
    不可先知，故 r_rec 是**第二个不确定维度**，须与源距先验一起进场景集；
    默认取乐观上界 R_REC_MAX（若只用它，等于隐含假设 r_rec=1500，是隐藏假设）。
    返回 (E[D], 失效概率, 最坏直径 F)。
    """
    if r_rec is None:
        r_rec = R_REC_MAX
    # Gauss–Legendre 9 点（nodes/weights 常量表，零依赖）
    GL_N = [-0.9681602395, -0.8360311073, -0.6133714327, -0.3242534234, 0.0,
            0.3242534234, 0.6133714327, 0.8360311073, 0.9681602395]
    GL_W = [0.0812743884, 0.1806481607, 0.2606106964, 0.3123470770, 0.3302393550,
            0.3123470770, 0.2606106964, 0.1806481607, 0.0812743884]
    if nq != 9:
        GL_N = [-1.0 + 2.0 * i / (nq - 1) for i in range(nq)]
        GL_W = [2.0 / nq] * nq
    tot = 0.0
    wsum = 0.0
    fail = 0.0
    worst = 0.0
    ang_dir = math.radians(b1_meas + psi_deg)
    S2 = (S1[0] + d * math.cos(ang_dir), S1[1] + d * math.sin(ang_dir))
    for i, xi in enumerate(GL_N):
        for j, xj in enumerate(GL_N):
            d1 = EPS * xi
            d2 = EPS * xj
            w = GL_W[i] * GL_W[j]
            beta1 = b1_meas - d1                      # 真示向度 = 测得 − 误差
            # 真源：位于 S1 的 beta1 方向、距离 R
            G = (S1[0] + R * math.cos(math.radians(beta1)),
                 S1[1] + R * math.sin(math.radians(beta1)))
            if math.hypot(S2[0] - G[0], S2[1] - G[1]) > r_rec:
                fail += w                              # 第二点收不到信号
                continue
            beta2 = bearing(S2[0], S2[1], G[0], G[1])
            poly = location_region([S1, S2], [b1_meas, beta2 + d2])
            if len(poly) < 3:
                fail += w
                continue
            D = polygon_diameter(poly)
            tot += w * D
            wsum += w
            worst = max(worst, D)
    if wsum <= 0:
        return float("inf"), 1.0, float("inf")
    return tot / wsum, fail / 4.0, worst


def q2_feasibility_envelope(R_lo, R_hi, r_rec, psi_grid):
    """第二检测点「必然可接收」的 (ψ,d) 闭式可行域。

    |S₂G|² = R² + d² − 2Rd·cos ψ，对 R 是凸二次函数，故在 R ∈ [R_lo, R_hi] 上的
    最大值必在端点取到。要求对全部 R 都有 |S₂G| ≤ r_rec，得

        d ∈ [ R_hi cosψ − √(R_hi²cos²ψ − R_hi² + r_rec²),
              R_lo cosψ + √(R_lo²cos²ψ − R_lo² + r_rec²) ]

    左端有解的条件是 R_hi cosψ ≥ √(R_hi² − r_rec²)，即

        **ψ ≤ ψ_max = arcsin(r_rec / R_hi)**

    这是可证的必要条件：ψ 超过 arcsin(r_rec/R_hi) 后，无论 d 取何值，
    远距源（R = R_hi）都必然超出接收半径，第二点收不到信号、策略整体失效。
    """
    rows = []
    for psi in psi_grid:
        cs = math.cos(math.radians(psi))
        lo_disc = R_hi * R_hi * cs * cs - R_hi * R_hi + r_rec * r_rec
        hi_disc = R_lo * R_lo * cs * cs - R_lo * R_lo + r_rec * r_rec
        if lo_disc < 0 or hi_disc < 0:
            rows.append({"psi_deg": psi, "feasible": False, "d_lo_m": None, "d_hi_m": None})
            continue
        d_lo = R_hi * cs - math.sqrt(lo_disc)
        d_hi = R_lo * cs + math.sqrt(hi_disc)
        rows.append({"psi_deg": psi, "feasible": d_lo <= d_hi,
                     "d_lo_m": round(d_lo, 3), "d_hi_m": round(d_hi, 3)})
    psi_max = math.degrees(math.asin(min(1.0, r_rec / R_hi)))
    return {
        "formula": "|S₂G|² = R² + d² − 2Rd·cos ψ；要求 ∀R∈[R_lo,R_hi]: |S₂G| ≤ r_rec",
        "R_lo_m": R_lo, "R_hi_m": R_hi, "r_rec_m": r_rec,
        "psi_max_deg": round(psi_max, 4),
        "psi_max_formula": "ψ_max = arcsin(r_rec / R_hi)",
        "rows": rows,
    }


def q2_decision(S1, b1_meas, priors, psi_grid, d_grid, alpha=0.05,
                r_recs=(R_REC_MAX, R_REC_MIN), fail_tol=0.02):
    """在 (ψ,d) 网格上对「源距先验 × 接收半径假设」的每个场景求 E[D] → 最小最大后悔。

    场景集 = 距离先验 × r_rec 假设。r_rec ∈ [1000,1500] 是机器狗不可先知的
    第二个不确定维度，只按乐观值 1500 m 选点 = 隐藏假设；把它并入场景集后，
    后悔值取全场景最大值，选出的点对 r_rec 也稳健。
    """
    scores = {}          # (ψ,d) -> {scenario: E[D]}
    fails, worsts = {}, {}
    scen = [(p, rr) for rr in r_recs for p in priors]
    for psi in psi_grid:
        for d in d_grid:
            row, fr, wr = {}, {}, {}
            for pname, rr in scen:
                Rs = priors[pname]
                acc = af = aw = 0.0
                for R in Rs:
                    e, f, w = _E_D(S1, b1_meas, psi, d, R, r_rec=rr)
                    acc += e
                    af += f
                    aw = max(aw, w)
                n = len(Rs)
                key = f"{pname}|r_rec={rr:g}"
                row[key] = acc / n
                fr[key] = af / n
                wr[key] = aw
            scores[(psi, d)] = row
            fails[(psi, d)] = fr
            worsts[(psi, d)] = wr
    # 可行性优先：失效概率超阈值的点直接剔除，不参与后悔值比较。
    # 否则一个「大多数时候收不到信号」的点可能靠条件期望 E[D|成功] 取胜，
    # 那是拿不可用的方案冒充最优。
    keys = list(scores[next(iter(scores))].keys())
    feasible = [g for g in scores if max(fails[g].values()) <= fail_tol]
    if not feasible:
        raise RuntimeError(f"网格内无可行点（fail_tol={fail_tol}）")
    # 每场景最优值 → 后悔值（全场景取最大；只在可行集上比）
    fstar = {k: min(scores[g][k] for g in feasible) for k in keys}
    regret = {g: max(row[k] - fstar[k] for k in keys)
              for g, row in scores.items() if g in feasible}
    rmin = min(regret.values())
    thr = rmin * (1.0 + alpha) if rmin > 0 else rmin + abs(rmin) * alpha + 1e-9
    cand = sorted([k for k, v in regret.items() if v <= thr])
    best_regret = min(regret, key=lambda k: regret[k])
    # 第二个判据：最小最大（绝对最坏）。后悔值只惩罚「相对最优的损失」，
    # 最小最大直接压最坏场景。两者常不一致，若不一致说明结论对判据敏感，
    # 必须同时报告而不是只挑一个好看的。
    worst_case = {g: max(row[k] for k in keys) for g, row in scores.items()
                  if g in feasible}
    best_minimax = min(worst_case, key=lambda g: worst_case[g])
    return {
        "S1": list(S1),
        "b1_measured_deg": b1_meas,
        "decision_vars": "ψ = 相对测得示向度的转角(°)，d = 沿该方向前进距离(m)",
        "observable": ["b1（第一个检测点的示向度）"],
        "not_observable": ["源距 R=|S₁G|（/measure 不返回距离，也不返回信号强度）",
                           "有效接收半径 r_rec ∈ [1000,1500]（赛题只给区间，机器狗不可先知）"],
        "scenarios": keys,
        "n_scenarios": len(keys),
        "per_scenario_best": {
            k: {"psi_deg": min(scores, key=lambda g: scores[g][k])[0],
                "d_m": min(scores, key=lambda g: scores[g][k])[1],
                "E_D_m": round(fstar[k], 6)}
            for k in keys},
        "minimax_regret_point": {"psi_deg": best_regret[0], "d_m": best_regret[1],
                                 "regret_m": round(regret[best_regret], 6),
                                 "E_D_by_scenario": {k: round(scores[best_regret][k], 6)
                                                     for k in keys},
                                 "fail_prob_by_scenario": {k: round(fails[best_regret][k], 8)
                                                           for k in keys},
                                 "worst_diameter_F_by_scenario":
                                     {k: round(worsts[best_regret][k], 6) for k in keys}},
        "minimax_point": {"psi_deg": best_minimax[0], "d_m": best_minimax[1],
                          "worst_E_D_m": round(worst_case[best_minimax], 6),
                          "E_D_by_scenario": {k: round(scores[best_minimax][k], 6)
                                              for k in keys},
                          "fail_prob_by_scenario": {k: round(fails[best_minimax][k], 8)
                                                    for k in keys}},
        "criteria_agree": (best_regret == best_minimax),
        "criteria_note": "最小最大后悔（相对损失）与最小最大（绝对最坏）是两个不同判据；"
                         "criteria_agree=false 时结论对判据敏感，须报候选区而非单点。",
        "candidate_region_alpha": alpha,
        "candidate_region": [{"psi_deg": k[0], "d_m": k[1],
                              "regret_m": round(regret[k], 6)} for k in cand],
        "n_candidates": len(cand),
        "fail_tol": fail_tol,
        "n_grid_points": len(scores),
        "n_feasible_points": len(feasible),
        "excluded_by_fail": sorted([{"psi_deg": g[0], "d_m": g[1],
                                     "max_fail_prob": round(max(fails[g].values()), 6)}
                                    for g in scores if g not in feasible],
                                   key=lambda x: -x["max_fail_prob"])[:12],
        "grid_size": {"psi": list(psi_grid), "d": list(d_grid)},
    }


def q2_vs_v1(S1=(-500.0, 0.0), b1=20.0):
    """与 v1 结论对拍：垂线族上 D 随偏移单调递增，v1 推荐的 offset=d_est 并非最优。"""
    R = 1200.0
    rows = []
    for off in (300.0, 600.0, 900.0, 1200.0, 1500.0):
        # 垂线族上 |S₂G| = off，故 S₂ 相对「S₁→G 方向」的极角 ψ = atan(off/R)，
        # 前进距离 d = √(R²+off²)。v1 用的 φ=90° 是 S₂ 处的交会角，不是 ψ。
        psi = math.degrees(math.atan2(off, R))
        d = math.hypot(R, off)
        e, f, w = _E_D(S1, b1, psi, d, R)
        rows.append({"offset_m": off, "psi_deg": round(psi, 6),
                     "d_m": round(d, 4), "S2G_dist_m": round(off, 4),
                     "E_D_m": round(e, 6), "fail_prob": round(f, 8),
                     "worst_D_m": round(w, 6)})
    return {
        "note": "v1 以「交会角 90°」为判据推荐 offset=d_est=1200（即 d=1697 m）。"
                "同一垂线族上 E[D] 随偏移严格递增，v1 自己的权衡表已显示该趋势，"
                "却以「对称平衡配置」为由选了更差的点。",
        "closed_form_check": "垂线族上 D = 2ε·√(R²+t²)，ε=1°、R=1200",
        "rows": rows,
        "v1_recommended_offset_m": 1200.0,
        "v2_better_offset_m": 300.0,
    }


# ---------------------------------------------------------------- 主流程
def build_all() -> dict:
    """纯构造：返回完整结果字典，不做任何 IO（供 verify 脚本重跑对拍）。"""
    # ---- Q1：可行域内由真源反算生成算例
    # 站点由「真源 + 极角 + 距离」正向布置，使源端交会角恰为预设值，
    # 再逐条核对硬约束（|S| ≤ R_AREA、|S−G| ≤ R_REC_MAX）。
    def place(G, ang_deg, dist):
        a = math.radians(ang_deg)
        return (G[0] + dist * math.cos(a), G[1] + dist * math.sin(a))

    # 演示算例一律取「保证可行」口径：|S−G| ≤ R_REC_MIN = 1000 m，
    # 使结论不依赖 r_rec 这个未知参数的实际取值。
    G_a = (220.0, -160.0)
    A = q1_case("A 两站正交交会（χ=90°）",
                [place(G_a, 150.0, 950.0), place(G_a, 60.0, 950.0)], G_a)
    G_b = (-360.0, 420.0)
    B = q1_case("B 两站钝角交会（χ=140°）",
                [place(G_b, 200.0, 950.0), place(G_b, 340.0, 1000.0)], G_b)
    G_c = (140.0, 300.0)
    C = q1_case("C 三站交会", [place(G_c, 175.0, 950.0), place(G_c, 55.0, 900.0),
                             place(G_c, 295.0, 980.0)], G_c)
    for rec in (A, B, C):
        rec["station_source_dist_guaranteed"] = all(
            R_OPTICAL < x <= R_REC_MIN for x in rec["station_source_dist_m"])
        rec["station_source_dist_ok"] = all(x <= R_REC_MAX for x in rec["station_source_dist_m"])
        rec["stations_in_area"] = all(math.hypot(*s) <= R_AREA for s in rec["stations"])
        rec["source_in_area"] = math.hypot(*rec["source"]) <= R_AREA

    ce = q1_counterexample(n_scan=4000)
    dense = q1_rho_supremum()
    ce["supremum_dense_scan"] = dense
    ce["rho_sup_dense_scan"] = dense["rho_sup_dense_scan"]
    ce["v1_exaggeration_factor"] = dense["v1_exaggeration_factor"]

    # ---- Q2：源距不可观测 → 多先验 + 后悔值
    S1 = (-500.0, 0.0)
    b1 = 20.0
    priors = {
        "P1_距离均匀[200,1500]": [200.0 + 1300.0 * (i + 0.5) / 24 for i in range(24)],
        "P2_面积均匀(盘内密度∝R)": [1500.0 * math.sqrt((i + 0.5) / 24) for i in range(24)],
        "P3_远距集中[1000,1500]": [1000.0 + 500.0 * (i + 0.5) / 24 for i in range(24)],
    }
    psi_grid = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 70.0, 80.0]
    d_grid = [300.0, 450.0, 600.0, 750.0, 900.0, 1050.0, 1200.0, 1350.0, 1500.0]
    q2 = q2_decision(S1, b1, priors, psi_grid, d_grid)
    q2["compare_v1"] = q2_vs_v1(S1, b1)
    # 闭式可行域（对源距取值区间的最坏情形），与数值失效扫描互为交叉验证。
    # R 区间取全部先验支撑集的并集端点，使闭式与数值口径一致。
    allR = [R for Rs in priors.values() for R in Rs]
    R_lo, R_hi = min(allR), max(allR)
    q2["feasibility_envelope"] = {
        "R_support_m": [round(R_lo, 3), round(R_hi, 3)],
        "r_rec_1000_guaranteed": q2_feasibility_envelope(R_lo, R_hi, R_REC_MIN, psi_grid),
        "r_rec_1500_optimistic": q2_feasibility_envelope(R_lo, R_hi, R_REC_MAX, psi_grid),
    }

    out = {
        "schema_version": 2,
        "revision": "v2（修复 v1 的 D1 算例不可行 / D2 反例手搓 / D3 决策变量错误 / D4 不可观测量代入）",
        "problem": "2026_B 无线电干扰源定位清除",
        "random_seed": SEED,
        "constants": {"R_AREA": R_AREA, "EPS_BEARING_DEG": EPS_DEG,
                      "R_REC_MIN": R_REC_MIN, "R_REC_MAX": R_REC_MAX},
        "problem1": {"cases": [A, B, C], "counterexample": ce},
        "problem2": q2,
    }
    return out


def main() -> dict:
    out = build_all()
    out_path = Path(__file__).resolve().parent.parent / "q1q2_v2_results.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    ce = out["problem1"]["counterexample"]
    q2 = out["problem2"]
    A, B, C = out["problem1"]["cases"]
    print(json.dumps({k: out[k] for k in ("schema_version", "revision")}, ensure_ascii=False))
    print("Q1 cases:")
    for rec in (A, B, C):
        print(f"  {rec['name']:16s} D={rec['diameter_m']:9.3f} m  ρ={rec['rho_mec_over_D']}"
              f"  covers={rec['covers']}  保证可行={rec['station_source_dist_guaranteed']}")
    print(f"  counterexample: n_fail={ce['n_failures']}  worst ρ={ce['worst_case']['rho_mec_over_D'] if ce['worst_case'] else None}"
          f"  ρ_sup_obs={ce['rho_sup_observed']}")
    print("Q2 per-scenario best:", json.dumps(q2["per_scenario_best"], ensure_ascii=False))
    print("Q2 minimax-regret:", json.dumps(q2["minimax_regret_point"], ensure_ascii=False))
    print(f"Q2 candidate region: n={q2['n_candidates']}")
    print(f"written -> {out_path}")
    return out


if __name__ == "__main__":
    main()
