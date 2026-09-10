# -*- coding: utf-8 -*-
"""调头曲线（两段相切圆弧 S 形）的解析求解与最短化（问题 4 核心）。

几何设定
--------
* 盘入螺线  S_in : P(θ) = bθ(cosθ, sinθ)，行进方向 θ 递减（顺时针、向内）；
* 盘出螺线  S_out: -P(θ)（关于螺线中心的中心对称像），行进方向 θ 递增（逆时针、向外）；
* 两者在 θ 处的**行进切向**同为 u(θ) = -P'(θ)/|P'(θ)|
  （入：θ 递减取负号；出：点取负后 θ 递增，两个负号相消）。
* 调头空间：以螺线中心为圆心、半径 R_t = 4.5 m 的圆。龙头在 A（r=R_t）进入，
  沿 S 形曲线到 B ∈ S_out，再盘出。

两段弧的解析
------------
记 u 为 A 处切向，n = rot90(u) 为左法向，D = B - A。
"先右后左"（RL）且两端切向相同（ψ2 = ψ1 = ψ）时：

    D = (R1 + R2)·[ sinψ·u − (1−cosψ)·n ]                (1)

⇒  ψ 由 tan(ψ/2) = −(D·n)/(D·u) 唯一确定，S = R1+R2 = (D·u)/sinψ 唯一确定，
   **总弧长 L = (R1+R2)ψ 与半径分配无关**——这是"能否把调头曲线调短"的关键结论。

一般情形（B 可沿出螺线移动，两端切向不同）用 1-D 优化 min_{ψ1} L(ψ1)，
其中 (R1, R2) 由线性方程组 [g_r, g_l]·(R1,R2) = D 解出。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import dragon_core as dc


def rot(v, ang):
    c, s = np.cos(ang), np.sin(ang)
    return np.stack([c * v[..., 0] - s * v[..., 1],
                     c * v[..., 1] + s * v[..., 0]], axis=-1)


def travel_tangent(spiral: dc.Spiral, theta):
    """螺线上 θ 处的行进切向单位矢量（入螺线向内 / 出螺线向外，公式相同）。"""
    d = spiral.dpoint(np.asarray(theta, dtype=float))
    return -d / np.linalg.norm(d, axis=-1, keepdims=True)


def g_arc(psi, u, n, right: bool):
    """圆弧位移 / 半径：右转取 −(1−cosψ)n，左转取 +(1−cosψ)n。"""
    s, c = np.sin(psi), np.cos(psi)
    sign = -1.0 if right else 1.0
    return s * u + sign * (1.0 - c) * n


def solve_two_arc(A, uA, B, uB, n_grid: int = 720, sense: str = "RL"):
    """给定端点与两端切向，求最短的两段相切圆弧 S 形曲线。

    返回 dict(L, R1, R2, psi1, psi2, J, u1, ok)。
    """
    A = np.asarray(A, float)
    uA = np.asarray(uA, float)
    B = np.asarray(B, float)
    uB = np.asarray(uB, float)
    nA = np.array([-uA[1], uA[0]])
    D = B - A
    delta = float(np.arctan2(uA[0] * uB[1] - uA[1] * uB[0], float(uA @ uB)))
    first_right = (sense == "RL")
    best = None
    for psi1 in np.linspace(1e-3, 2 * np.pi - 1e-3, n_grid):
        psi2 = psi1 + delta if first_right else psi1 - delta
        if not (0.0 < psi2 < 2 * np.pi):
            continue
        u1 = rot(uA, -psi1 if first_right else psi1)
        n1 = np.array([-u1[1], u1[0]])
        g1 = g_arc(psi1, uA, nA, first_right)
        g2 = g_arc(psi2, u1, n1, not first_right)
        det = g1[0] * g2[1] - g1[1] * g2[0]
        if abs(det) < 1e-12:
            continue
        R1 = (D[0] * g2[1] - D[1] * g2[0]) / det
        R2 = (g1[0] * D[1] - g1[1] * D[0]) / det
        if R1 <= 1e-6 or R2 <= 1e-6:
            continue
        L = R1 * psi1 + R2 * psi2
        if best is None or L < best["L"]:
            best = dict(L=float(L), R1=float(R1), R2=float(R2),
                        psi1=float(psi1), psi2=float(psi2), J=A + R1 * g1,
                        u1=u1, sense=sense)
    return best


def solve_two_arc_best(A, uA, B, uB, n_grid: int = 720):
    """两种转向次序取更短者。"""
    out = [s for s in (solve_two_arc(A, uA, B, uB, n_grid, "RL"),
                       solve_two_arc(A, uA, B, uB, n_grid, "LR")) if s]
    return min(out, key=lambda d: d["L"]) if out else None


def arc_points(center, radius, ang0, ang1, n: int = 400):
    ang = np.linspace(ang0, ang1, n)
    return np.stack([center[0] + radius * np.cos(ang),
                     center[1] + radius * np.sin(ang)], axis=-1)


def curve_points(A, uA, sol, n: int = 400):
    """返回 S 形曲线采样点 (2n,2)，用于"是否在调头空间内"的机械校验。"""
    nA = np.array([-uA[1], uA[0]])
    first_right = sol["sense"] == "RL"
    R1, R2, p1, p2 = sol["R1"], sol["R2"], sol["psi1"], sol["psi2"]
    C1 = A + (R1 * (-nA) if first_right else R1 * nA)
    v1 = A - C1
    a10 = np.arctan2(v1[1], v1[0])
    sweep1 = -p1 if first_right else p1
    seg1 = arc_points(C1, R1, a10, a10 + sweep1, n)
    J = seg1[-1]
    u1 = sol["u1"] if sol.get("u1") is not None else rot(uA, sweep1)
    n1 = np.array([-u1[1], u1[0]])
    C2 = J + (R2 * n1 if first_right else R2 * (-n1))
    v2 = J - C2
    a20 = np.arctan2(v2[1], v2[0])
    sweep2 = p2 if first_right else -p2
    seg2 = arc_points(C2, R2, a20, a20 + sweep2, n)
    return np.vstack([seg1, seg2])


def theta_of_arc(spiral: dc.Spiral, s: float) -> float:
    """弧长反演的标量包装。"""
    return float(np.asarray(spiral.theta_at_arc(np.array(float(s)))).ravel()[0])


def build_turnaround_path(pitch: float, R_turn: float, sol: dict,
                          theta_outer: float | None = None,
                          tail_arc_in: float = 100.0, head_arc_out: float = 100.0):
    """拼装完整行进路径：入螺线 → 弧1 → 弧2 → 出螺线。

    返回 (path, sigma_A, info)。sigma_A 为 A 点（调头起点）弧长坐标。
    """
    sp_in = dc.Spiral(pitch, 0.0)
    sp_out = dc.Spiral(pitch, np.pi)
    theta_A = R_turn / sp_in.b
    A = sp_in.point(np.array(theta_A))[0] if sp_in.point(np.array(theta_A)).ndim > 1 \
        else sp_in.point(np.array(theta_A))
    A = np.asarray(A, float).reshape(2)
    uA = np.asarray(travel_tangent(sp_in, np.array(theta_A)), float).reshape(2)

    arc_in = float(sp_in.arc(np.array(theta_A)))
    if theta_outer is None:
        theta_outer = theta_of_arc(sp_in, arc_in + tail_arc_in + dc.CHAIN_LEN * 1.2) + 2.0
    theta_end = theta_of_arc(sp_out, arc_in + head_arc_out + sol["L"]) + 2.0

    u1 = rot(uA, -sol["psi1"] if sol["sense"] == "RL" else sol["psi1"])
    nA = np.array([-uA[1], uA[0]])
    R1, R2 = sol["R1"], sol["R2"]
    g1 = g_arc(sol["psi1"], uA, nA, sol["sense"] == "RL")
    J = A + R1 * g1

    tracks = [
        dc.SpiralTrack(sp_in, theta_outer, theta_A, direction=-1),
        dc.ArcTrack(A, uA, -1.0 / R1 if sol["sense"] == "RL" else 1.0 / R1,
                    R1 * sol["psi1"]),
        dc.ArcTrack(J, u1, 1.0 / R2 if sol["sense"] == "RL" else -1.0 / R2,
                    R2 * sol["psi2"]),
        dc.SpiralTrack(sp_out, theta_A, theta_end, direction=+1),
    ]
    path = dc.CompositePath(tracks)
    sigma_A = tracks[0].length
    info = dict(A=A, uA=uA, J=J, u1=u1, theta_A=theta_A, theta_outer=theta_outer,
                theta_end=theta_end, sp_in=sp_in, sp_out=sp_out)
    return path, sigma_A, info


def s_curve_fixed_B(pitch: float, R_turn: float, ratio: float = 2.0):
    """B = −A（出螺线在 r=R_turn 处的对称点）且 R1 = ratio·R2 的解析解。"""
    sp = dc.Spiral(pitch, 0.0)
    theta_A = R_turn / sp.b
    A = np.asarray(sp.point(np.array(theta_A)), float).reshape(2)
    u = np.asarray(travel_tangent(sp, np.array(theta_A)), float).reshape(2)
    n = np.array([-u[1], u[0]])
    D = -2.0 * A
    du, dn = float(D @ u), float(D @ n)
    psi = 2.0 * np.arctan2(-dn, du)          # RL 次序
    if psi < 0:
        psi += 2 * np.pi
    s, c = np.sin(psi), np.cos(psi)
    S = du / s
    R1 = S * ratio / (1.0 + ratio)
    R2 = S / (1.0 + ratio)
    return dict(L=float(S * psi), R1=float(R1), R2=float(R2), psi1=float(psi),
                psi2=float(psi), sense="RL", J=A + R1 * (s * u - (1 - c) * n),
                u1=rot(u, -psi), psi=float(psi), S=float(S))
