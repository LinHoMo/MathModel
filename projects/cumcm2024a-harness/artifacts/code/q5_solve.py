# -*- coding: utf-8 -*-
"""问题 5：沿问题 4 设定的路径行进，龙头匀速，求龙头最大行进速度 v_max，
使全队各把手速率均不超过 2 m/s。

关键结构性简化（可证明）：
    整链构型仅由龙头弧长坐标 σ_0 决定（与速度无关），且
        v_k(t) = |dσ_k/dt| = |dσ_k/dσ_0| · v_head
    ⇒ 速率比 r_k(σ_0) = |dσ_k/dσ_0| 是**仅与龙头位置有关**的几何量。
    ⇒ 约束 max_{k,t} v_k ≤ 2 等价于 v_head ≤ 2 / max_{k,σ_0} r_k。
    因此只需沿路径扫描一次 r_k 的最大值，无需对速度做搜索。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import dragon_core as dc
from results_io import write_result
from q4_solve import build, T_LO, T_HI

V_LIMIT = 2.0
H_ARC = 1e-3          # 弧长中心差分步长 (m)
STEP = 0.1            # 时间扫描步长（峰值尖峰，1 s 网格会漏掉）


def speed_ratio(path, sig_head, h: float = H_ARC):
    """返回 (T, K) 速率比 |dσ_k/dσ_0|。"""
    s_plus = dc.chain_sigma(path, np.asarray(sig_head) + h)
    s_minus = dc.chain_sigma(path, np.asarray(sig_head) - h)
    return np.abs(s_plus - s_minus) / (2.0 * h)


def main():
    t0 = time.time()
    sol, path, sigma_A, info = build()
    t_grid = np.arange(T_LO, T_HI + 0.5 * STEP, STEP)
    sig_head = sigma_A + t_grid

    ratio = speed_ratio(path, sig_head)
    r_max = float(ratio.max())
    i_max, k_max = np.unravel_index(int(np.argmax(ratio)), ratio.shape)
    v_max = V_LIMIT / r_max
    print(f"[ratio] 全队速率比上界 max|dσ_k/dσ_0| = {r_max:.6f}  "
          f"@ t={t_grid[i_max]:.2f}s, 第 {k_max} 号把手")
    print(f"[ratio] 速率比范围 [{ratio.min():.6f}, {ratio.max():.6f}]；龙头自身 = 1")
    print(f"\n[v_max] 龙头最大行进速度 = {v_max:.6f} m/s")
    print(f"        校验：此时最大把手速率 = {v_max * r_max:.6f} m/s "
          f"（应 = {V_LIMIT}）")

    # 网格收敛性：0.5 / 0.1 / 0.05 s 三档一致才算收敛
    conv = []
    for st in (0.5, 0.1, 0.05):
        tg = np.arange(T_LO, T_HI + 0.5 * st, st)
        conv.append((st, round(float(speed_ratio(path, sigma_A + tg).max()), 6)))
    print(f"[converge] 时间网格 → max ratio：{conv}")
    # 峰值邻域平滑性（排除求根跳支）
    nb = ratio[max(0, i_max - 4):i_max + 5, k_max]
    print(f"[smooth] 峰值邻域 r(t)：{[round(float(x), 5) for x in nb]}")

    df = pd.DataFrame({
        "t_s": t_grid,
        "max_ratio": np.round(ratio.max(axis=1), 6),
        "min_ratio": np.round(ratio.min(axis=1), 6),
        "argmax_handle": np.argmax(ratio, axis=1),
        "tail_ratio": np.round(ratio[:, -1], 6),
    })
    meta = pd.DataFrame([
        ("v_max_ms", v_max), ("v_limit_ms", V_LIMIT),
        ("max_speed_ratio", r_max),
        ("argmax_t_s", float(t_grid[i_max])), ("argmax_handle", int(k_max)),
        ("h_arc_m", H_ARC), ("t_range_s", f"[{T_LO:g}, {T_HI:g}]"),
        ("time_step_s", STEP), ("grid_convergence", str(conv)),
        ("peak_neighborhood", str([round(float(x), 5) for x in nb])),
        ("pitch_m", 1.7), ("R_turn_m", 4.5), ("S_len_m", sol["L"]),
    ], columns=["key", "value"])
    out = write_result("result5.xlsx", df, None, meta)
    print(f"[out] {out}  ({time.time()-t0:.1f}s)")
    return v_max


if __name__ == "__main__":
    main()
