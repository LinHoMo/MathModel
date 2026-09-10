# -*- coding: utf-8 -*-
"""结果落盘工具：统一 results/*.xlsx 结构（长表 + key_points + 元信息）。"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RESULTS = Path(__file__).resolve().parents[1] / "results"


def write_result(name: str, df: pd.DataFrame, key: pd.DataFrame | None = None,
                 meta: pd.DataFrame | None = None) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / name
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="all_handles", index=False)
        if key is not None:
            key.to_excel(w, sheet_name="key_points", index=False)
        if meta is not None:
            meta.to_excel(w, sheet_name="meta", index=False)
    return out


def frame_rows(t_grid, pos, vel, speed, names):
    """(T,K) 数组 → 长表 DataFrame（6 位小数）。"""
    rows = []
    for i, t in enumerate(t_grid):
        for k in range(pos.shape[1]):
            rows.append((int(t), k, names[k],
                         round(float(pos[i, k, 0]), 6), round(float(pos[i, k, 1]), 6),
                         round(float(vel[i, k, 0]), 6), round(float(vel[i, k, 1]), 6),
                         round(float(speed[i, k]), 6)))
    return pd.DataFrame(rows, columns=["t_s", "handle_idx", "handle",
                                       "x_m", "y_m", "vx_ms", "vy_ms", "speed_ms"])


def key_points(df, times, idxs):
    return df[df.t_s.isin(times) & df.handle_idx.isin(idxs)].copy()
