# -*- coding: utf-8 -*-
"""问题 3：调头空间为直径 9 m 的圆（半径 R_t = 4.5 m），确定**最小螺距** p_min，
使得龙头前把手能沿该螺距的等距螺线盘入到调头空间边界（r = R_t）而不发生板凳碰撞。

关键结构性事实（使本问与"从何处开始盘入"无关）：
    整链构型由 (螺距 p, 龙头弧长坐标) 唯一确定 —— 与盘入历史无关。
    且链越往内盘、局部曲率越大 ⇒ 最危险构型必为**龙头半径最小**的时刻，即 r_0 = R_t。
    本脚本对 r_0 ∈ [R_t, 20 m] 扫描验证该单调性，再对 p 二分。
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
from results_io import write_result

R_TURN = 4.5                 # 调头空间半径 (m)
W = dc.BOARD_WIDTH
R_HEAD_SCAN = np.array([4.5, 5.0, 6.0, 8.0, 11.0, 15.0, 20.0])   # 龙头半径扫描点


def config_at(pitch: float, r_head: float):
    """给定螺距与龙头半径，返回整队把手位置 (224,2)。"""
    sp = dc.Spiral(pitch)
    theta_head = r_head / sp.b
    arc_head = float(sp.arc(np.array(theta_head)))
    theta_outer = tu.theta_of_arc(sp, arc_head + dc.CHAIN_LEN * 1.15) + 1.0
    path = dc.spiral_inward_path(pitch, theta_outer, 0.0)
    sig_head = path.length - arc_head
    sig = dc.chain_sigma(path, np.array([sig_head]))
    return path.point_at(sig.ravel()).reshape(1, -1, 2)[0]


def clearance(pitch: float, r_scan=R_HEAD_SCAN):
    """该螺距下、龙头由外向内盘入至 R_TURN 全程的最小板距 (m)。"""
    vals = []
    for r in r_scan:
        try:
            vals.append(dc.min_board_distance(config_at(pitch, float(r))))
        except dc.ChainInfeasible:
            vals.append(0.0)
    return float(np.min(vals)), dict(zip(r_scan.tolist(), [round(v, 6) for v in vals]))


def main():
    t0 = time.time()
    lo, hi = 0.305, 1.20          # p ≤ W 必然相碰；p=1.2 已足够宽松
    c_hi, _ = clearance(hi)
    print(f"[bracket] p={hi}: clearance={c_hi:.6f} m")
    if c_hi < W:
        print("[bracket] 上界仍不满足，需扩大")
        return
    c_lo, _ = clearance(lo)
    print(f"[bracket] p={lo}: clearance={c_lo:.6f} m")
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        c, _ = clearance(mid)
        if c >= W:
            hi = mid
        else:
            lo = mid
        if hi - lo < 1e-5:
            break
    p_min = 0.5 * (lo + hi)
    c, detail = clearance(p_min)
    print(f"\n[p_min] 最小螺距 = {p_min:.6f} m = {p_min*100:.3f} cm   "
          f"临界最小板距 = {c:.6f} m")
    print("[detail] 各龙头半径处的最小板距 (m):", detail)

    # 单调性核验：给出 p_min 附近的敏感性
    sens = [(round(p, 4), round(clearance(p)[0], 6))
            for p in (p_min - 0.02, p_min - 0.005, p_min, p_min + 0.005, p_min + 0.02)]
    print("[sensitivity] (p, clearance):", sens)

    meta = pd.DataFrame([
        ("p_min_m", p_min), ("p_min_cm", p_min * 100),
        ("turnaround_radius_m", R_TURN), ("collision_threshold_m", W),
        ("clearance_at_pmin_m", c), ("bisect_tol_m", 1e-5),
        ("r_head_scan_m", ", ".join(f"{v:g}" for v in R_HEAD_SCAN)),
        ("clearance_by_r_m", str(detail)),
        ("sensitivity", str(sens)),
    ], columns=["key", "value"])
    df = pd.DataFrame(sens, columns=["pitch_m", "min_board_distance_m"])
    out = write_result("result3.xlsx", df, None, meta)
    print(f"[out] {out}  ({time.time()-t0:.1f}s)")
    return p_min


if __name__ == "__main__":
    main()
