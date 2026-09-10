#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""solve_a.py — CUMCM 2026 A 题「药材的烘干问题」数值求解器。

模型：圆柱形药材（长 25 cm、半径 2 cm）的热风烘干，长径比 12.5 视为无限长圆柱，
仅考虑径向（一维）耦合传热传质。控制方程为径向对称的瞬态热传导 + 水分扩散：

    ρ c_p ∂T/∂t = (1/r) ∂/∂r (r k ∂T/∂r)          （热）
    ∂C/∂t       = (1/r) ∂/∂r (r D ∂C/∂r)          （质）

边界（r=R 表面，对流换热 / 对流传质）：
    -k ∂T/∂r = h (T - T_air(t))
    -D ∂C/∂r = h_m (C - C_air(t))
中心（r=0）对称：∂T/∂r = ∂C/∂r = 0。

数值方法：向后 Euler 隐式格式（无条件稳定）+ 三对角 Thomas 求解；系数（ρ,c_p,k,D）
随 (C,T) 变化时取上一时步值（半隐式）。问题 4 用 Landau 变换 ξ=r/R(t) 处理移动边界，
R(t) 由干物质质量守恒给出。

零第三方运行时依赖（numpy 仅用于数组运算，属项目交付代码）。
"""
from __future__ import annotations

import json
import os
import math
from typing import Callable

import numpy as np

# ======================================================================
# 全局参数（源自赛题附录）
# ======================================================================
R0 = 0.02        # 初始半径 / m
L = 0.25         # 长度 / m
T0 = 28.0        # 初始温度 / °C
C0 = 2.55        # 初始干基含水率 / kg·kg⁻¹
H = 25.0         # 对流换热系数 / W·m⁻²·K⁻¹
HM = 8.0e-7      # 对流传质系数 / m·s⁻¹
C_TARGET = 0.15  # 烘干要求：各处水分浓度 < 0.15 kg/kg
T_TARGET = 50.0  # 恒温干燥目标温度（中药材低温热风干燥典型值，与题面"2-3 天"自洽）/ °C
SEED = 42        # 随机种子（铁律：固定 42；本求解器确定性，保留以通过校验）


# ======================================================================
# 物性函数（附录 2 / 3 / 4）
# ======================================================================
def props(C: np.ndarray, T: np.ndarray, mode: int):
    """返回 (rho, cp, k, D)。C 干基含水率 kg/kg，T 温度 K。

    mode=1 附录2（问题1，常物性，D=D(C)）；mode=2/3 附录3（问题2/3，变物性）；
    mode=4 附录4（问题4，变物性）。D 的 exp 项对 C 取下限防除零。
    """
    C = np.asarray(C, dtype=float)
    T = np.asarray(T, dtype=float)
    Cm = np.maximum(C, 1.0e-6)
    if mode == 1:
        rho = np.full_like(C, 820.0)
        cp = np.full_like(C, 2600.0)
        k = np.full_like(C, 0.36)
        D = 7.0e-9 * np.exp(-0.89 / Cm)
    elif mode in (2, 3):
        rho = 650.0 + 128.0 * C
        cp = 1450.0 + 2736.0 * C / (C + 1.0)
        k = 0.21 + 0.38 * C / (C + 1.0)
        D = 2.4e-3 * np.exp(-0.45 / Cm) * np.exp(-3850.0 / T)
    elif mode == 4:
        rho = 760.0 + 90.0 * C
        cp = 1850.0 + 2150.0 * C / (C + 1.0)
        k = 0.12 + 0.20 * C / (C + 1.0)
        D = 4.2e-4 * np.exp(-0.30 / Cm) * np.exp(-3850.0 / T)
    else:
        raise ValueError(f"未知物性模式 mode={mode}")
    return rho, cp, k, D


# ======================================================================
# 边界条件（附件缺失时的默认假设，可被 data/annex1.csv 覆盖）
# ======================================================================
def default_T_air(t: np.ndarray) -> np.ndarray:
    """烘房温度 / °C。预热阶段 28→60°C（指数趋近，时间常数 450 s），随后恒温。"""
    t = np.asarray(t, dtype=float)
    return T0 + (T_TARGET - T0) * (1.0 - np.exp(-t / 450.0))


def default_C_air(t: np.ndarray, mode: int) -> np.ndarray:
    """烘房空气水分浓度（表面平衡含水率代理）/ kg·kg⁻¹。

    问题1（预热平衡）取 0.10；问题2/3/4 两段：预热阶段湿度较高（0.15，防开裂），
    恒温干燥阶段干燥（0.05）。
    """
    t = np.asarray(t, dtype=float)
    if mode == 1:
        return np.full_like(t, 0.10)
    return np.where(t < 1800.0, 0.15, 0.05)


# ======================================================================
# 三对角 Thomas 求解
# ======================================================================
def thomas(lower: np.ndarray, diag: np.ndarray, upper: np.ndarray,
           rhs: np.ndarray) -> np.ndarray:
    """解三对角线性方程组 A x = rhs。lower[0]=upper[-1]=0 未使用。"""
    n = rhs.shape[0]
    cp = np.zeros(n)
    dp = np.zeros(n)
    x = np.zeros(n)
    cp[0] = upper[0] / diag[0]
    dp[0] = rhs[0] / diag[0]
    for i in range(1, n):
        denom = diag[i] - lower[i] * cp[i - 1]
        cp[i] = upper[i] / denom if i < n - 1 else 0.0
        dp[i] = (rhs[i] - lower[i] * dp[i - 1]) / denom
    x[n - 1] = dp[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


# ======================================================================
# 隐式径向扩散推进一步（Landau 变换 ξ=r/R(t) 上的有限体积）
# ======================================================================
def _implicit_step(u: np.ndarray, beta: np.ndarray, kappa: np.ndarray,
                   dt: float, R: float, dRdt: float, N: int,
                   heff: float, u_amb: float) -> np.ndarray:
    """在 ξ∈[0,1] 均匀网格上推进一个时步，返回 u^{n+1}。

    方程 β ∂u/∂t = (1/R²)(1/ξ)∂/∂ξ(ξ κ ∂u/∂ξ) + β (ξ R'/R) ∂u/∂ξ，
    Robin 边界 -κ/R ∂u/∂ξ = heff (u - u_amb)（对流）或 ∂u/∂ξ=0（绝热，heff=0）。
    β（容系数）、κ（扩散系数）为节点值（已按当前 u 计算并 lag）。
    """
    dxi = 1.0 / N
    lower = np.zeros(N + 1)
    diag = np.zeros(N + 1)
    upper = np.zeros(N + 1)
    xi = np.arange(N + 1) * dxi
    adv = dRdt / R  # 对流速度系数 (ξ R'/R) = adv * ξ

    # 界面扩散系数（调和平均，保守格式）：kh[i] = κ_{i+1/2}
    kh = 2.0 * kappa[:-1] * kappa[1:] / (kappa[:-1] + kappa[1:] + 1e-30)
    lam = dt / (beta * R * R * dxi * dxi)  # 逐节点

    rhs = u.copy()

    # 内部节点 i=1..N-1（向量化）
    i = np.arange(1, N)
    a_d = lam[i] * kh[i - 1] * (i - 0.5) * dxi / xi[i]
    c_d = lam[i] * kh[i] * (i + 0.5) * dxi / xi[i]
    s_adv = 0.5 * dt * adv * xi[i] / dxi
    lower[i] = -(a_d - s_adv)
    diag[i] = 1.0 + a_d + c_d
    upper[i] = -(c_d + s_adv)

    # 中心节点 i=0（对称：1/ξ·∂/∂ξ → 2 ∂²/∂ξ²）
    diag[0] = 1.0 + 4.0 * kappa[0] * lam[0]
    upper[0] = -4.0 * kappa[0] * lam[0]

    # 表面节点 i=N（ghost 消除 Robin：-κ/R ∂u/∂ξ = heff (u_N - u_amb)）
    A = lam[N] * kh[N - 1] * (N - 0.5) * dxi / xi[N]
    C = lam[N] * (1.0 + 0.5 * dxi) * kappa[N]
    B = 2.0 * dxi * R * heff / (kappa[N] + 1e-30)
    sN = 0.5 * dt * adv * xi[N] / dxi
    lower[N] = -(C + A) - sN
    diag[N] = 1.0 + C + A + B * (C + sN)
    upper[N] = 0.0
    rhs[N] = u[N] + B * (C + sN) * u_amb

    # 三对角求解：scipy 带状求解器（C 实现）优先，退回纯 Python Thomas
    try:
        from scipy.linalg import solve_banded
        ab = np.zeros((3, N + 1))
        ab[0, 1:] = upper[:-1]
        ab[1, :] = diag
        ab[2, :-1] = lower[1:]
        return solve_banded((1, 1), ab, rhs)
    except Exception:
        return thomas(lower, diag, upper, rhs)


# ======================================================================
# 主求解器
# ======================================================================
def solve(t_end: float, dt: float, mode: int, N: int = 40,
          T_air_fn: Callable | None = None, C_air_fn: Callable | None = None,
          moving: bool = False, C_stop: float | None = None,
          report_every: float | None = None):
    """径向耦合传热传质求解。

    返回 dict：{'times': np.array, 'r': np.array(米), 'T': 2D(时间×节点, °C),
               'C': 2D(时间×节点, kg/kg), 'R_hist': 半径历史(米)}。
    若 C_stop 给定，当全场 C 最大值 < C_stop 时提前停止（返回终点时间）。
    """
    T_air_fn = T_air_fn or default_T_air
    if C_air_fn is None:
        C_air_fn = lambda t: default_C_air(t, mode)

    # 初始场
    T = np.full(N + 1, T0)          # °C
    C = np.full(N + 1, C0)          # kg/kg
    R = R0
    dRdt = 0.0

    times = [0.0]
    T_hist = [T.copy()]
    C_hist = [C.copy()]
    R_hist = [R]

    n_steps = int(round(t_end / dt))
    step = 0
    t = 0.0
    while step < n_steps:
        # 计算下一时步的烘房环境
        t_next = (step + 1) * dt
        T_air = float(np.asarray(T_air_fn(t_next)).item())
        C_air = float(np.asarray(C_air_fn(t_next)).item())

        # 物性（lag 到当前 T,C）
        rho, cp, k, D = props(C, T + 273.15, mode)
        beta_T = rho * cp
        # 更新半径（问题4 移动边界：干物质质量守恒）
        if moving:
            Cbar = np.sum(C * np.arange(N + 1) * 2.0) / np.sum(np.arange(N + 1) * 2.0 + 1e-30)
            # 体积加权平均（径向）C̄ = ∫C r dr / ∫ r dr ≈ Σ C_i ξ_i / Σ ξ_i（固定 ξ 网格）
            Cbar = np.sum(C * (np.arange(N + 1) + 1e-30)) / np.sum(np.arange(N + 1) + 1e-30)
            rho0 = 760.0 + 90.0 * C0
            R_new = R0 * math.sqrt((rho0 / (1.0 + C0)) * (1.0 + Cbar) / (760.0 + 90.0 * Cbar))
            dRdt = (R_new - R) / dt
            R = R_new

        # 隐式推进：先热后质（半隐式耦合）
        T_new = _implicit_step(T, beta_T, k, dt, R, dRdt, N, H, T_air)
        C_new = _implicit_step(C, np.ones(N + 1), D, dt, R, dRdt, N, HM, C_air)
        # 物理截断
        C_new = np.clip(C_new, 0.0, C0)
        T = T_new
        C = C_new

        times.append(t_next)
        T_hist.append(T.copy())
        C_hist.append(C.copy())
        R_hist.append(R)

        step += 1

        # 烘干终点判断
        if C_stop is not None and C.max() < C_stop:
            break

    return {
        "times": np.array(times),
        "r": np.arange(N + 1) / N * R0,  # 初始网格（输出用，问题4 以 ξ 归一）
        "xi": np.arange(N + 1) / N,
        "T": np.array(T_hist),     # °C
        "C": np.array(C_hist),     # kg/kg
        "R_hist": np.array(R_hist),
    }


# ======================================================================
# 结果输出（xlsx + 控制台表格）
# ======================================================================
def _write_xlsx(path: str, times: np.ndarray, radii_cm: np.ndarray,
                T: np.ndarray | None, C: np.ndarray | None,
                time_unit_label: str = "s"):
    """写 result*.xlsx。温度/水分浓度各一个 sheet；A 列时间、第 1 行距离(cm)。"""
    from openpyxl import Workbook

    wb = Workbook()
    sheets = []
    if T is not None:
        sheets.append(("温度", T))
    if C is not None:
        sheets.append(("水分浓度", C))
    ws0 = wb.active
    ws0.title = sheets[0][0]
    for name, mat in sheets:
        ws = wb.create_sheet(title=name) if name != sheets[0][0] else ws0
        ws.cell(row=1, column=1, value=f"时间/{time_unit_label}")
        for j, rc in enumerate(radii_cm):
            ws.cell(row=1, column=j + 2, value=round(float(rc), 4))
        for i, tt in enumerate(times):
            ws.cell(row=i + 2, column=1, value=round(float(tt), 4))
            for j in range(mat.shape[1]):
                ws.cell(row=i + 2, column=j + 2, value=round(float(mat[i, j]), 4))
    wb.save(path)


def _fmt_table(times, radii_cm, mat, label):
    """打印论文用表格（四位小数）。"""
    print(f"\n[{label}]")
    header = "时间".ljust(9) + "".join(f"{r:>10.4f}" for r in radii_cm)
    print(header)
    for i, tt in enumerate(times):
        row = f"{tt:<9.4f}" + "".join(f"{mat[i, j]:>10.4f}" for j in range(len(radii_cm)))
        print(row)


def _summary(results: dict, label: str) -> dict:
    """把关键数值收集进 all_results.json 用的 dict。"""
    return {
        "label": label,
        "final_time_s": float(results["times"][-1]),
        "final_surface_T_C": float(results["T"][-1, -1]),
        "final_center_T_C": float(results["T"][-1, 0]),
        "final_surface_C": float(results["C"][-1, -1]),
        "final_center_C": float(results["C"][-1, 0]),
        "final_radius_m": float(results["R_hist"][-1]),
    }


# ======================================================================
# 各问题驱动
# ======================================================================
N_GRID = 1280        # 径向网格数（Δr = 0.0015625 cm）。
# 空间收敛实测（Q3, dt=20 s, mode=3）：N=160/320/640/1280/2560 → 烘干时长
# 63.5222/58.0944/57.5000/57.4278/57.4167 h。N=320 偏高约 1.2%，N=1280 已收敛到
# 外推值（≈57.42 h）的 0.02% 以内，故最终取 N=1280。
DR_CM = R0 * 100.0 / N_GRID  # 网格间距 / cm


def _ridx(rc_cm: float) -> int:
    """把「到药材中心距离 cm」映射到网格下标。"""
    return int(round(rc_cm / DR_CM))


def _hours_until(dry_time_s: float) -> list:
    """每 6 h 取点直到烘干结束，末尾追加实际烘干时间（h）。"""
    hours = list(range(6, int(dry_time_s // 3600) + 1, 6))
    hours.append(round(dry_time_s / 3600.0, 4))
    return hours


def problem1(out_dir: str) -> dict:
    """问题1：预热平衡阶段（0–1800 s），附录2 常物性。"""
    mode = 1
    res = solve(t_end=1800.0, dt=1.0, mode=mode, N=N_GRID)
    # 论文表格：t = 100..1800 s（每 300），r = 0,0.5,1,1.5,2 cm
    t_sel = [100, 300, 600, 900, 1200, 1500, 1800]
    r_sel_cm = [0.0, 0.5, 1.0, 1.5, 2.0]
    idx_t = [int(round(tt)) for tt in t_sel]  # dt=1s
    idx_r = [_ridx(rc) for rc in r_sel_cm]
    T_tab = res["T"][np.ix_(idx_t, idx_r)]
    C_tab = res["C"][np.ix_(idx_t, idx_r)]
    _fmt_table(t_sel, r_sel_cm, T_tab, "表1 温度/°C（问题1）")
    _fmt_table(t_sel, r_sel_cm, C_tab, "表2 水分浓度/(kg/kg)（问题1）")

    # result1.xlsx：每 1 s、每 0.1 cm
    r_out = np.arange(0.0, 2.0001, 0.1)
    idx_r_out = [_ridx(rc) for rc in r_out]
    T_out = res["T"][:, idx_r_out]
    C_out = res["C"][:, idx_r_out]
    _write_xlsx(os.path.join(out_dir, "result1.xlsx"),
                res["times"], r_out, T_out, C_out, time_unit_label="s")
    print(f"\n[问题1] result1.xlsx 已写出（{res['times'].shape[0]} 时间点 × {len(r_out)} 距离点）")
    return _summary(res, "problem1")


def problem2(out_dir: str) -> dict:
    """问题2：整个烘干过程（预热+恒温干燥），附录3 变物性；输出 3 h。"""
    mode = 2
    res = solve(t_end=3 * 3600.0, dt=1.0, mode=mode, N=N_GRID)
    # 论文表格：t = 0.5..3 h（每 0.5），r = 0..2 cm（每 0.5）
    t_sel_h = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    r_sel_cm = [0.0, 0.5, 1.0, 1.5, 2.0]
    idx_t = [int(round(h * 3600.0)) for h in t_sel_h]
    idx_r = [_ridx(rc) for rc in r_sel_cm]
    T_tab = res["T"][np.ix_(idx_t, idx_r)]
    C_tab = res["C"][np.ix_(idx_t, idx_r)]
    _fmt_table(t_sel_h, r_sel_cm, T_tab, "表3 温度/°C（问题2）")
    _fmt_table(t_sel_h, r_sel_cm, C_tab, "表4 水分浓度/(kg/kg)（问题2）")

    r_out = np.arange(0.0, 2.0001, 0.1)
    idx_r_out = [_ridx(rc) for rc in r_out]
    T_out = res["T"][:, idx_r_out]
    C_out = res["C"][:, idx_r_out]
    _write_xlsx(os.path.join(out_dir, "result2.xlsx"),
                res["times"], r_out, T_out, C_out, time_unit_label="s")
    print(f"\n[问题2] result2.xlsx 已写出（{res['times'].shape[0]} 时间点 × {len(r_out)} 距离点）")
    return _summary(res, "problem2")


def problem3(out_dir: str) -> dict:
    """问题3：烘干时间（各处 C < 0.15），附录3；输出每 6 h 表格 + 每 60 s 完整。"""
    mode = 3
    # 找到烘干时间（dt=10s，上限 8 天）
    res = solve(t_end=8 * 24 * 3600.0, dt=10.0, mode=mode, N=N_GRID, C_stop=C_TARGET)
    dry_time_s = float(res["times"][-1])
    print(f"\n[问题3] 烘干完成时间 ≈ {dry_time_s / 3600.0:.4f} h（{dry_time_s:.1f} s）")

    t_sel = _hours_until(dry_time_s)
    r_sel_cm = [0.0, 0.5, 1.0, 1.5, 2.0]
    idx_t = [int(round(tt * 3600.0 / 10.0)) for tt in t_sel]
    idx_r = [_ridx(rc) for rc in r_sel_cm]
    C_tab = res["C"][np.ix_(idx_t, idx_r)]
    _fmt_table(t_sel, r_sel_cm, C_tab, "表5 水分浓度/(kg/kg)（问题3）")

    # result3.xlsx：每 60 s、每 0.1 cm
    r_out = np.arange(0.0, 2.0001, 0.1)
    idx_r_out = [_ridx(rc) for rc in r_out]
    step60 = 6  # dt=10s → 每 60 s 取 1 点
    times_out = res["times"][::step60]
    C_out = res["C"][::step60][:, idx_r_out]
    _write_xlsx(os.path.join(out_dir, "result3.xlsx"),
                times_out, r_out, None, C_out, time_unit_label="s")
    print(f"[问题3] result3.xlsx 已写出（{times_out.shape[0]} 时间点 × {len(r_out)} 距离点）")

    summ = _summary(res, "problem3")
    summ["drying_time_h"] = dry_time_s / 3600.0
    return summ


def problem4(out_dir: str) -> dict:
    """问题4：移动边界（尺寸随水分流失收缩），附录4；求烘干时长。"""
    mode = 4
    res = solve(t_end=8 * 24 * 3600.0, dt=10.0, mode=mode, N=N_GRID,
                moving=True, C_stop=C_TARGET)
    dry_time_s = float(res["times"][-1])
    print(f"\n[问题4] 烘干完成时间 ≈ {dry_time_s / 3600.0:.4f} h（{dry_time_s:.1f} s）")
    print(f"[问题4] 最终半径 ≈ {res['R_hist'][-1] * 100.0:.4f} cm")

    # 论文表格：每 6 h 直到结束（距离按 ξ 映射到当前表面）
    t_sel = _hours_until(dry_time_s)
    idx_t = [int(round(tt * 3600.0 / 10.0)) for tt in t_sel]
    r_sel_cm = [0.0, 0.5, 1.0, 1.5, 2.0]
    C_tab = np.zeros((len(idx_t), len(r_sel_cm)))
    for a, it in enumerate(idx_t):
        Rt = res["R_hist"][it]
        for b, rc in enumerate(r_sel_cm):
            xi = min(rc / 100.0 / Rt, 1.0)
            C_tab[a, b] = res["C"][it, int(round(xi * N_GRID))]
    _fmt_table(t_sel, r_sel_cm, C_tab, "表6 水分浓度/(kg/kg)（问题4）")

    # result4.xlsx：每 60 s、每 0.1 cm（按当前半径归一化到实际距离）
    r_out = np.arange(0.0, 2.0001, 0.1)
    step60 = 6
    times_out = res["times"][::step60]
    C_out = np.zeros((times_out.shape[0], len(r_out)))
    for a, tt_idx in enumerate(range(0, res["C"].shape[0], step60)):
        Rt = res["R_hist"][tt_idx]
        for b, rc in enumerate(r_out):
            xi = min(rc / 100.0 / Rt, 1.0)
            C_out[a, b] = res["C"][tt_idx, int(round(xi * N_GRID))]
    _write_xlsx(os.path.join(out_dir, "result4.xlsx"),
                times_out, r_out, None, C_out, time_unit_label="s")
    print(f"[问题4] result4.xlsx 已写出（{times_out.shape[0]} 时间点 × {len(r_out)} 距离点）")

    summ = _summary(res, "problem4")
    summ["drying_time_h"] = dry_time_s / 3600.0
    summ["final_radius_cm"] = float(res["R_hist"][-1] * 100.0)
    return summ


# ======================================================================
# 收敛性/守恒性自检
# ======================================================================
def self_check():
    """网格收敛 + 稳态温度自检（问题1 简化）。"""
    print("=" * 60)
    print("自检：网格收敛性（问题1，t=1800s 中心温度）")
    for N in (20, 40, 80):
        res = solve(t_end=1800.0, dt=1.0, mode=1, N=N)
        print(f"  N={N:3d}  中心温度={res['T'][-1, 0]:.4f} °C  表面温度={res['T'][-1, -1]:.4f} °C  "
              f"表面水分={res['C'][-1, -1]:.4f} 中心水分={res['C'][-1, 0]:.4f}")
    print("=" * 60)


def validation_suite():
    """收敛性与敏感性验证套件（实测值写入结果台账，供数值追溯）。

    空间收敛（dt=20 s）、时间收敛（N=320）、恒温温度敏感性（N=320, dt=20 s）。
    """
    print("\n[验证] 空间收敛（Q3, dt=20 s）")
    spatial = []
    for N in (160, 320, 640, 1280, 2560):
        r = solve(t_end=8 * 24 * 3600.0, dt=20.0, mode=3, N=N, C_stop=C_TARGET)
        h = float(r["times"][-1]) / 3600.0
        spatial.append({"N": N, "dry_h": h})
        print(f"  N={N:5d}  烘干时长={h:.4f} h")
    print("[验证] 时间收敛（Q3, N=320）")
    temporal = []
    for dt in (20.0, 10.0, 5.0):
        r = solve(t_end=8 * 24 * 3600.0, dt=dt, mode=3, N=320, C_stop=C_TARGET)
        h = float(r["times"][-1]) / 3600.0
        temporal.append({"dt": dt, "dry_h": h})
        print(f"  dt={dt:5.1f} s  烘干时长={h:.4f} h")
    print("[验证] 恒温温度敏感性（Q3, N=320, dt=20 s）")
    global T_TARGET
    keep = T_TARGET
    sensitivity = []
    for Tt in (45.0, 50.0, 55.0, 60.0):
        T_TARGET = Tt
        r = solve(t_end=8 * 24 * 3600.0, dt=20.0, mode=3, N=320, C_stop=C_TARGET)
        h = float(r["times"][-1]) / 3600.0
        sensitivity.append({"T_target": Tt, "dry_h": h})
        print(f"  T_target={Tt:4.1f} °C  烘干时长={h:.4f} h")
    T_TARGET = keep
    return {"spatial_convergence": spatial,
            "temporal_convergence": temporal,
            "temperature_sensitivity": sensitivity}


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "results")
    os.makedirs(out_dir, exist_ok=True)

    self_check()

    summaries = {}
    summaries["problem1"] = problem1(out_dir)
    summaries["problem2"] = problem2(out_dir)
    summaries["problem3"] = problem3(out_dir)
    summaries["problem4"] = problem4(out_dir)
    validations = validation_suite()

    # all_results.json（供数值追溯校验）
    out_json = {
        "schema_version": 3,
        "problem": "CUMCM2026A",
        "random_seed": SEED,
        "summary": summaries,
        "validations": validations,
    }
    json_path = os.path.join(out_dir, "..", "..", "all_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] all_results.json 已写出: {json_path}")


if __name__ == "__main__":
    main()
