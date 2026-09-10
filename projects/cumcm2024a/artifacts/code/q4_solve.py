# -*- coding: utf-8 -*-
"""问题 4：螺距 1.7 m，盘出螺线为盘入螺线的中心对称像，S 形调头曲线（R1 = 2R2，
与两条螺线均相切）。给出 -100 s ~ 100 s 每秒整队位置/速度（t=0 = 调头开始）。

并回答"能否调整圆弧，仍保持各部分相切，使调头曲线变短"——见 [invariance] 段。
产出 artifacts/results/result4.xlsx。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import dragon_core as dc
import turnaround as tu
from results_io import write_result, frame_rows

PITCH = 1.7
R_TURN = 4.5
V_HEAD = 1.0
T_LO, T_HI = -100.0, 100.0
KEY_T = [-100, -50, 0, 50, 100]
R_MIN = float(dc.LINK_LEN[0]) / 2.0      # 刚性链可跟随的最小曲率半径


def build(ratio: float = 2.0, tail_arc_in: float = 120.0, head_arc_out: float = 120.0):
    sol = tu.s_curve_fixed_B(PITCH, R_TURN, ratio)
    path, sigma_A, info = tu.build_turnaround_path(
        PITCH, R_TURN, sol, tail_arc_in=tail_arc_in, head_arc_out=head_arc_out)
    return sol, path, sigma_A, info


def invariance_study():
    """回答"能否调短"：①固定端点时 L 不变量；②允许切点 B 沿出螺线滑动的后果。"""
    sp, spo = dc.Spiral(PITCH, 0.0), dc.Spiral(PITCH, np.pi)
    thA = R_TURN / sp.b
    sA = float(sp.arc(np.array(thA)))
    A = np.asarray(sp.point(np.array(thA)), float).reshape(2)
    u = np.asarray(tu.travel_tangent(sp, np.array(thA)), float).reshape(2)

    # ① 固定端点：不同半径分配下 L 是否变化（数值验证 closed-form 不变性）
    rows = []
    for ratio in (1.0, 1.5, 2.0, 3.0, 5.0, 10.0):
        s = tu.s_curve_fixed_B(PITCH, R_TURN, ratio)
        pts = tu.curve_points(A, u, s, n=800)
        rows.append((ratio, round(s["R1"], 6), round(s["R2"], 6),
                     round(s["psi1"], 6), round(s["L"], 6),
                     round(float(np.max(np.linalg.norm(pts, axis=1))), 4)))

    # ② B 沿出螺线滑动：S 曲线长 / 出螺线回到边界的弧长 / 圆内总长
    slide = []
    for thB in np.linspace(2.0, thA - 0.002, 200):
        B = np.asarray(spo.point(np.array(thB)), float).reshape(2)
        uB = np.asarray(tu.travel_tangent(spo, np.array(thB)), float).reshape(2)
        g = tu.solve_two_arc_best(A, u, B, uB, n_grid=1500)
        if g is None or g["R1"] < R_MIN or g["R2"] < R_MIN:
            continue
        pts = tu.curve_points(A, u, g, n=600)
        if float(np.max(np.linalg.norm(pts, axis=1))) > R_TURN + 1e-9:
            continue
        s_out = sA - float(sp.arc(np.array(thB)))
        slide.append((round(float(thB), 4), round(float(np.linalg.norm(B)), 4),
                      round(g["L"], 4), round(s_out, 4), round(g["L"] + s_out, 4),
                      round(g["R1"], 3), round(g["R2"], 3)))
    slide.sort(key=lambda r: r[4])
    return rows, slide


def main():
    t0 = time.time()
    sol, path, sigma_A, info = build()
    print(f"[S-curve] R1={sol['R1']:.6f} m  R2={sol['R2']:.6f} m  "
          f"psi={sol['psi1']:.6f} rad ({np.degrees(sol['psi1']):.3f}°)  "
          f"L={sol['L']:.6f} m")
    print(f"[S-curve] 接点 J=({sol['J'][0]:.6f}, {sol['J'][1]:.6f})  "
          f"|J|={np.linalg.norm(sol['J']):.6f} m")
    pts = tu.curve_points(info["A"], info["uA"], sol, n=4000)
    rr = np.linalg.norm(pts, axis=1)
    print(f"[check] 调头曲线半径范围 [{rr.min():.6f}, {rr.max():.6f}] m "
          f"（调头空间 R={R_TURN} ⇒ {'全部在内' if rr.max() <= R_TURN+1e-9 else '越界!'}）")
    print(f"[check] 端点误差 |start-A|={np.linalg.norm(pts[0]-info['A']):.2e}  "
          f"|end-(-A)|={np.linalg.norm(pts[-1]+info['A']):.2e}")
    print(f"[path] 入螺线 {path.tracks[0].length:.3f} m + 弧1 {path.tracks[1].length:.3f} m "
          f"+ 弧2 {path.tracks[2].length:.3f} m + 出螺线 {path.tracks[3].length:.3f} m "
          f"= {path.length:.3f} m；A 点 σ={sigma_A:.3f} m")

    t_grid = np.arange(T_LO, T_HI + 0.5, 1.0)
    sig_head = sigma_A + V_HEAD * t_grid
    pos, vel, speed = dc.chain_state(path, sig_head, V_HEAD, t_grid, h=1e-3)
    links = np.linalg.norm(np.diff(pos, axis=1), axis=2)
    print(f"[check] 连杆弦长最大偏差 = {np.abs(links - dc.LINK_LEN[None, :]).max():.3e} m")
    print(f"[check] 把手速率范围 [{speed.min():.6f}, {speed.max():.6f}] m/s "
          f"（龙头 1 m/s）")

    names = dc.handle_names()
    df = frame_rows(t_grid, pos, vel, speed, names)
    kp = df[df.t_s.isin(KEY_T) & df.handle_idx.isin(dc.KEY_IDX)].copy()

    rows, slide = invariance_study()
    print("\n[invariance] 固定 A、B 于调头空间边界时，不同半径分配的 S 曲线：")
    print("  ratio      R1         R2        psi(rad)     L(m)     曲线最大半径")
    for r in rows:
        print(f"  {r[0]:<8} {r[1]:<10} {r[2]:<10} {r[3]:<12} {r[4]:<9} {r[5]}")
    print("  ⇒ L 与半径分配无关（不变量），R1=2R2 可不通过调半径缩短")
    if slide:
        print("\n[slide-B] 允许 B 沿出螺线内移后的最优若干解（L_S / 出螺线段 / 圆内总长）：")
        print("  theta_B   |B|      L_S      L_out    L_total   R1       R2")
        for r in slide[:5]:
            print("  " + "  ".join(f"{v}" for v in r))
        best = slide[0]
        print(f"  ⇒ 圆内总长最短仍为 B 在边界的 {sol['L']:.4f} m；"
              f"滑动后最优圆内总长 {best[4]} m（且第二弧半径 {best[6]} m 退化为直线）")

    meta = pd.DataFrame([
        ("pitch_m", PITCH), ("R_turn_m", R_TURN), ("v_head_ms", V_HEAD),
        ("R1_m", sol["R1"]), ("R2_m", sol["R2"]), ("psi_rad", sol["psi1"]),
        ("psi_deg", float(np.degrees(sol["psi1"]))),
        ("S_len_m", sol["L"]), ("R1_over_R2", 2.0),
        ("J_x_m", float(sol["J"][0])), ("J_y_m", float(sol["J"][1])),
        ("curve_r_min_m", float(rr.min())), ("curve_r_max_m", float(rr.max())),
        ("inside_turnaround", bool(rr.max() <= R_TURN + 1e-9)),
        ("endpoint_err_m", float(np.linalg.norm(pts[-1] + info["A"]))),
        ("sigma_A_m", sigma_A), ("path_len_m", path.length),
        ("max_link_error_m", float(np.abs(links - dc.LINK_LEN[None, :]).max())),
        ("speed_min_ms", float(speed.min())), ("speed_max_ms", float(speed.max())),
        ("t_range_s", f"[{T_LO:g}, {T_HI:g}]"),
        ("invariance_table", str(rows)),
        ("slide_B_best", str(slide[:5]) if slide else "none"),
        ("R_min_feasible_m", R_MIN),
    ], columns=["key", "value"])
    out = write_result("result4.xlsx", df, kp, meta)
    print(f"\n[out] {out}  rows={len(df)}  ({time.time()-t0:.1f}s)")

    print("\n=== 关键时刻位置 (m) ===")
    print(kp.pivot_table(index="handle", columns="t_s", values=["x_m", "y_m"],
                         aggfunc="first").round(6).to_string())
    print("\n=== 关键时刻速率 (m/s) ===")
    print(kp.pivot_table(index="handle", columns="t_s", values="speed_ms",
                         aggfunc="first").round(6).to_string())
    return sol, path, sigma_A


if __name__ == "__main__":
    main()
