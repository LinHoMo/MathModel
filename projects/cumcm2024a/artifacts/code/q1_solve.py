# -*- coding: utf-8 -*-
"""问题 1：螺距 0.55 m 等距螺线顺时针盘入，龙头前把手 1 m/s，0~300 s 每秒整队位置/速度。

产出 artifacts/results/result1.xlsx（all_handles 长表 + key_points + meta）。
自洽校验：①连杆弦长恒等于 2.86/1.65；②把手速率与"弧长等分"近似的偏差量级。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import dragon_core as dc
from results_io import write_result, frame_rows, key_points

PITCH = 0.55
V_HEAD = 1.0
THETA_START = 16 * 2 * np.pi          # 第 16 圈（A 点，取极角 0）
THETA_OUTER = 138.0                    # 轨道外端（保证 t=0 时龙尾在轨道内）
T_END = 300
KEY_T = [0, 60, 120, 180, 240, 300]


def build_path(pitch: float = PITCH, theta_outer: float = THETA_OUTER):
    return dc.spiral_inward_path(pitch, theta_outer, 0.0)


def main():
    t0 = time.time()
    path = build_path()
    sp = dc.Spiral(PITCH)
    sigma0 = path.length - float(sp.arc(np.array(THETA_START)))

    t_grid = np.arange(0, T_END + 1, dtype=float)
    sig_head = sigma0 + V_HEAD * t_grid
    pos, vel, speed = dc.chain_state(path, sig_head, V_HEAD, t_grid, h=1e-3)

    # --- 自洽校验 -----------------------------------------------------------
    links = np.linalg.norm(np.diff(pos, axis=1), axis=2)             # (T,223)
    link_err = float(np.abs(links - dc.LINK_LEN[None, :]).max())
    sp_dev = float(np.abs(speed - V_HEAD).max())
    print(f"[check] 连杆弦长最大偏差 = {link_err:.3e} m")
    print(f"[check] 把手速率相对龙头最大偏差 = {sp_dev:.6f} m/s "
          f"（弧长等分近似会给出恒 0，本模型给出真实差异）")

    names = dc.handle_names()
    df = frame_rows(t_grid, pos, vel, speed, names)
    kp = key_points(df, KEY_T, dc.KEY_IDX)
    meta = pd.DataFrame([
        ("pitch_m", PITCH), ("v_head_ms", V_HEAD),
        ("theta_start_rad", THETA_START), ("turn_start", 16),
        ("n_handles", dc.N_HANDLES), ("t_end_s", T_END),
        ("link_len_head_m", dc.LINK_LEN[0]), ("link_len_body_m", dc.LINK_LEN[1]),
        ("chain_len_m", dc.CHAIN_LEN),
        ("max_link_error_m", link_err),
        ("max_speed_dev_from_head_ms", sp_dev),
        ("model", "rigid-chord chain on Archimedean spiral"),
    ], columns=["key", "value"])
    out = write_result("result1.xlsx", df, kp, meta)
    print(f"[out] {out}  rows={len(df)}  ({time.time()-t0:.1f}s)")

    print("\n=== 表 1 位置 (x, y) / m ===")
    print(kp.pivot_table(index="handle", columns="t_s", values=["x_m", "y_m"],
                         aggfunc="first").round(6).to_string())
    print("\n=== 表 2 速率 / (m/s) ===")
    print(kp.pivot_table(index="handle", columns="t_s", values="speed_ms",
                         aggfunc="first").round(6).to_string())
    return pos, vel, speed


if __name__ == "__main__":
    main()
