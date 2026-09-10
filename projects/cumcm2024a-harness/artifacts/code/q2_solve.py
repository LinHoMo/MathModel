# -*- coding: utf-8 -*-
"""问题 2：确定盘入终止时刻（板凳间首次发生碰撞的时刻）。

判定口径（机械、可复现）：
  * 每条板凳视为**含把手外 0.275 m 伸出**的刚性矩形（长 3.41 / 2.20 m，宽 0.30 m）；
  * 相邻两条板凳在共用把手处铰接（物理上必然重叠），故只检查 |i-j| ≥ 2 的板对；
  * 用中心线线段最小距离 < 板宽 0.30 m 判"板体相交"（胶囊保守近似）；
  * "链在螺线上无解"（局部曲率半径 < L/2 ⇒ 物理上必然卡死）单独标记。

注意：最小板距随龙头推进**非单调振荡**——链是离散多边形，板体相对相位周期性变化
（量级≈板长²/(8r)），故必须细扫定位首次接触，不能用粗扫+单调二分。
终止时刻 t*：min_dist(t) 首次降至 W 的时刻（细扫 0.05 s + 二分到 1e-4 s）。
产出 artifacts/results/result2.xlsx。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import dragon_core as dc
from results_io import write_result, frame_rows
from q1_solve import build_path, PITCH, V_HEAD, THETA_START

W = dc.BOARD_WIDTH
COARSE_STEP = 1.0        # 0~380 s 粗扫步长
FINE_FROM = 360.0        # 细扫起点
FINE_STEP = 0.05         # 细扫步长


def team_positions(path, times, block: int = 200):
    """分块递推；单块失败则逐帧重试，无解帧返回 None。"""
    out = [None] * len(times)
    i = 0
    while i < len(times):
        j = min(i + block, len(times))
        try:
            sig = dc.chain_sigma(path, np.asarray(times[i:j]))
            pos = path.point_at(sig.ravel()).reshape(*sig.shape, 2)
            for k in range(i, j):
                out[k] = pos[k - i]
            i = j
        except dc.ChainInfeasible:
            for k in range(i, j):
                try:
                    s = dc.chain_sigma(path, np.array([times[k]]))
                    out[k] = path.point_at(s.ravel()).reshape(1, -1, 2)[0]
                except dc.ChainInfeasible:
                    out[k] = None
            i = j
    return out


def main():
    t0 = time.time()
    path = build_path()
    sig0 = path.length - float(dc.Spiral(PITCH).arc(np.array(THETA_START)))
    t_max = path.length - sig0                     # 龙头到达螺线中心所需时间
    print(f"[path] 长度 {path.length:.2f} m；龙头 t=0 弧长 {sig0:.2f} m；"
          f"到达中心上限 t={t_max:.2f} s")

    def sig(t):
        return sig0 + V_HEAD * np.asarray(t, dtype=float)

    # ---- 粗扫 0 ~ FINE_FROM ------------------------------------------------
    tc = np.arange(0.0, FINE_FROM + 1e-9, COARSE_STEP)
    pos_c = team_positions(path, sig(tc))
    dc_c = np.array([np.nan if p is None else dc.min_board_distance(p) for p in pos_c])
    print(f"[coarse] 0~{FINE_FROM:.0f}s 最小板距 = {np.nanmin(dc_c):.5f} m "
          f"@ t={tc[int(np.nanargmin(dc_c))]:.1f}s")

    # ---- 细扫 FINE_FROM ~ t_max -------------------------------------------
    tf = np.arange(FINE_FROM, t_max - 0.5, FINE_STEP)
    pos_f = team_positions(path, sig(tf))
    dc_f = np.array([np.nan if p is None else dc.min_board_distance(p) for p in pos_f])
    hit = np.where(dc_f < W)[0]
    if hit.size:
        k = int(hit[0])
        lo, hi = float(tf[k - 1]), float(tf[k])
        print(f"[fine] 首次 < W 区间 ({lo:.3f}, {hi:.3f}] s；"
              f"d={dc_f[k-1]:.6f} → {dc_f[k]:.6f}")
    else:
        lo, hi = float(tf[-1]), None
        print(f"[fine] 细扫未触发碰撞，最小 {np.nanmin(dc_f):.5f}")

    # ---- 连续性校验（排除求根跳支）-----------------------------------------
    ok = [p for p in pos_f[:400] if p is not None]
    step_move = np.max([np.abs(np.linalg.norm(ok[i + 1][0] - ok[i][0]))
                        for i in range(len(ok) - 1)])
    print(f"[check] 细扫相邻帧龙头位移上限 = {step_move:.5f} m "
          f"（应 ≈ v·Δt = {V_HEAD*FINE_STEP:.5f} m）")

    # ---- 二分到 1e-4 s -----------------------------------------------------
    if hi is not None:
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            p = team_positions(path, sig([mid]))[0]
            d = np.nan if p is None else dc.min_board_distance(p)
            if d < W:
                hi = mid
            else:
                lo = mid
            if hi - lo < 1e-4:
                break
        t_star = 0.5 * (lo + hi)
    else:
        t_star = lo
    p_star = team_positions(path, sig([t_star]))[0]
    d_star, bi, bj = dc.min_board_distance_pair(p_star)
    print(f"\n[t*] 终止时刻 = {t_star:.4f} s   临界最小板距 = {d_star:.6f} m   "
          f"临界板对 = 第 {bi} 条 / 第 {bj} 条板凳")

    # ---- 终止时刻整队位置速度 ----------------------------------------------
    p, v, sp = dc.chain_state(path, np.array([sig0 + V_HEAD * t_star]), V_HEAD,
                              np.array([t_star]), h=1e-3)
    names = dc.handle_names()
    df = frame_rows([t_star], p, v, sp, names)
    kp = df[df.handle_idx.isin(dc.KEY_IDX)].copy()
    meta = pd.DataFrame([
        ("t_star_s", t_star), ("min_board_distance_m", d_star),
        ("critical_pair", f"{bi}-{bj}"), ("pitch_m", PITCH), ("v_head_ms", V_HEAD),
        ("collision_threshold_m", W), ("exclude_adjacent", True),
        ("coarse_step_s", COARSE_STEP), ("fine_step_s", FINE_STEP),
        ("bisect_tol_s", 1e-4), ("t_center_limit_s", t_max),
        ("coarse_min_dist_m", float(np.nanmin(dc_c))),
        ("max_handle_speed_ms", float(sp.max())),
        ("continuity_check_max_move_m", float(step_move)),
    ], columns=["key", "value"])
    out = write_result("result2.xlsx", df, kp, meta)
    print(f"[out] {out}  ({time.time()-t0:.1f}s)")

    print("\n=== 终止时刻关键点位置/速度 ===")
    print(kp[["handle", "x_m", "y_m", "vx_ms", "vy_ms", "speed_ms"]]
          .round(6).to_string(index=False))

    # 附：临界邻域板距曲线（供证据表）
    nb = [(round(float(tf[i]), 3), round(float(dc_f[i]), 6))
          for i in range(max(0, k - 6), min(len(tf), k + 7))] if hit.size else []
    print("[curve] 临界邻域 (t, minD):", nb)
    return t_star, d_star


if __name__ == "__main__":
    main()
