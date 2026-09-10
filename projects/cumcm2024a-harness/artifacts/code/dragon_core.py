# -*- coding: utf-8 -*-
"""板凳龙（2024 CUMCM A）运动学核心库 —— 项目内唯一的几何/运动学真源。

模型定位（对应 MODEL_IR 的 L2 mathematical / L3 computational）
------------------------------------------------------------------
1. 板凳是**刚体**：同一条板凳上两个孔（把手）的中心距固定
      龙头  L_head = 341 - 2*27.5 = 286 cm
      龙身/龙尾 L_body = 220 - 2*27.5 = 165 cm
   把手序列 P_0..P_223（224 个）：P_0 龙头前把手，P_k 第 k 节板的前把手
   （与前一节的后把手铰接重合），P_223 龙尾后把手。
   ⇒ 约束是**弦长约束** |P_k - P_{k+1}| = L_k，不是弧长约束。
2. 全链沿一条给定路径 Γ（等距螺线 / 圆弧 / 组合曲线）伸展：把手中心均在 Γ 上。
   由于把手数固定、链路不可伸长，整链构型由龙头前把手的弧长坐标 σ_0 唯一确定：
       σ_{k+1} = σ_k - δ_k，  s.t. |Γ(σ_{k+1}) - Γ(σ_k)| = L_k   （向后递推）
3. 速度：v_k = Γ'(σ_k) · dσ_k/dt，其中 dσ_k/dt = (dσ_k/dσ_0) · v_head
   （链式法则 + 中心差分，h = 1e-3 s）。因链路不可伸长但**弧长间隔随曲率变化**，
   各把手速率并不严格等于龙头速率——这是本模型区别于"弧长等分"近似解的关键。

单位：内部一律 SI（m, m/s, rad）。角度 rad。
"""
from __future__ import annotations

import numpy as np

# ---- 题面常量（problem_given） ----------------------------------------------
N_BOARDS = 223                      # 板凳节数：1 龙头 + 221 龙身 + 1 龙尾
N_HANDLES = N_BOARDS + 1            # 把手点数 224
HEAD_BOARD_LEN = 3.41               # 龙头板长 (m)
BODY_BOARD_LEN = 2.20               # 龙身/龙尾板长 (m)
BOARD_WIDTH = 0.30                  # 板宽 (m)
HOLE_D = 0.055                      # 孔径 (m)
HOLE_TO_EDGE = 0.275                # 孔心到最近板头 (m)
STUB = HOLE_TO_EDGE                 # 把手外侧板体伸出长度 (m)

# 第 j 条板的板长（j=0 龙头）
BOARD_LEN = np.concatenate([[HEAD_BOARD_LEN], np.full(N_BOARDS - 1, BODY_BOARD_LEN)])
# 相邻把手连杆长度 |P_k P_{k+1}|（= 同一板两孔中心距 = 板长 - 2*孔边距）
LINK_LEN = np.concatenate([[HEAD_BOARD_LEN - 2 * STUB],
                           np.full(N_HANDLES - 2, BODY_BOARD_LEN - 2 * STUB)])
CHAIN_LEN = float(LINK_LEN.sum())   # 链路总长 ≈ 369.16 m

KEY_BODY_IDX = [1, 51, 101, 151, 201]      # 论文表中要求的龙身编号
KEY_IDX = [0] + KEY_BODY_IDX + [223]       # + 龙头 + 龙尾（后）


def handle_names() -> list[str]:
    """把手命名（对齐官方 result 模板顺序）。"""
    names = ["龙头"]
    names += [f"第{k}节龙身" for k in range(1, 222)]   # 第 1..221 节龙身前把手
    names.append("龙尾（前）")
    names.append("龙尾（后）")
    return names


# --------------------------------------------------------------------------
# 路径原语
# --------------------------------------------------------------------------
class Spiral:
    """等距螺线（阿基米德螺线）r = b·θ，θ ≥ 0；phase 为整体旋转角。

    phase=0 为盘入螺线；phase=π 即其关于原点的中心对称像（盘出螺线）。
    """

    def __init__(self, pitch: float, phase: float = 0.0):
        self.pitch = float(pitch)
        self.b = self.pitch / (2.0 * np.pi)
        self.phase = float(phase)

    def point(self, theta):
        theta = np.asarray(theta, dtype=float)
        r = self.b * theta
        a = theta + self.phase
        return np.stack([r * np.cos(a), r * np.sin(a)], axis=-1)

    def dpoint(self, theta):
        """dP/dθ。"""
        theta = np.asarray(theta, dtype=float)
        b = self.b
        a = theta + self.phase
        return np.stack([b * (np.cos(a) - theta * np.sin(a)),
                         b * (np.sin(a) + theta * np.cos(a))], axis=-1)

    def ds_dtheta(self, theta):
        """|dP/dθ| = b·sqrt(1+θ²)。"""
        return self.b * np.sqrt(1.0 + np.asarray(theta, dtype=float) ** 2)

    def arc(self, theta):
        """从 θ=0 起的弧长 s(θ) = b/2·(θ√(1+θ²) + asinh θ)。"""
        theta = np.asarray(theta, dtype=float)
        return 0.5 * self.b * (theta * np.sqrt(1.0 + theta * theta)
                               + np.arcsinh(theta))

    def theta_at_arc(self, s, iters: int = 40, tol: float = 1e-14):
        """弧长反演（向量化 Newton，自上界单调下降；残差达 tol 提前退出）。"""
        s = np.atleast_1d(np.asarray(s, dtype=float))
        th = np.sqrt(2.0 * s / self.b) + 1.0
        for _ in range(iters):
            f = self.arc(th) - s
            step = f / self.ds_dtheta(th)
            th = np.maximum(th - step, 0.0)
            if float(np.max(np.abs(f))) < tol:
                break
        return th


class SpiralTrack:
    """沿螺线的一段**行进轨道**：以行进方向为正的弧长 a ∈ [0, length] 参数化。

    direction = -1：θ 递减（向内盘入，极角递减 ⇒ 顺时针）
    direction = +1：θ 递增（向外盘出，极角递增 ⇒ 逆时针）
    """

    def __init__(self, spiral: Spiral, theta_a: float, theta_b: float,
                 direction: int | None = None):
        self.spiral = spiral
        self.theta_start = float(theta_a)          # 轨道起点参数
        self.theta_end = float(theta_b)            # 轨道终点参数
        if direction is None:
            direction = 1 if theta_b > theta_a else -1
        self.direction = int(direction)
        self.s0 = float(spiral.arc(np.array(self.theta_start)))
        self.length = abs(float(spiral.arc(np.array(self.theta_end)) - self.s0))

    def theta_at(self, a):
        a = np.asarray(a, dtype=float)
        s = self.s0 + self.direction * a
        return self.spiral.theta_at_arc(s)

    def point_at(self, a):
        return self.spiral.point(self.theta_at(a))

    def tangent_at(self, a):
        th = self.theta_at(a)
        d = self.spiral.dpoint(th)
        n = np.linalg.norm(d, axis=-1, keepdims=True)
        return self.direction * d / n


class ArcTrack:
    """圆弧轨道：起点 P0、起始切向 u、有符号曲率 k（k>0 左转 / k<0 右转）、弧长 length。

    P(a) = P0 + (1/k)·[I - Rot(k·a)]·n，  T(a) = Rot(k·a)·u，  n = rot90(u)。
    """

    def __init__(self, p0, u, curvature: float, length: float):
        self.p0 = np.asarray(p0, dtype=float)
        u = np.asarray(u, dtype=float)
        self.u = u / np.linalg.norm(u)
        self.n = np.array([-self.u[1], self.u[0]])     # 左法向
        self.k = float(curvature)
        self.length = float(length)

    def point_at(self, a):
        a = np.atleast_1d(np.asarray(a, dtype=float))
        phi = self.k * a
        c, s = np.cos(phi), np.sin(phi)
        rn = np.stack([c * self.n[0] - s * self.n[1],
                       c * self.n[1] + s * self.n[0]], axis=-1)
        return self.p0 + (self.n - rn) / self.k

    def tangent_at(self, a):
        a = np.atleast_1d(np.asarray(a, dtype=float))
        phi = self.k * a
        c, s = np.cos(phi), np.sin(phi)
        return np.stack([c * self.u[0] - s * self.u[1],
                         c * self.u[1] + s * self.u[0]], axis=-1)


class CompositePath:
    """按行进顺序拼接的多段轨道，统一弧长坐标 σ ∈ [0, total_length]。"""

    def __init__(self, tracks):
        self.tracks = list(tracks)
        self.breaks = np.cumsum([0.0] + [t.length for t in self.tracks])
        self.length = float(self.breaks[-1])

    def _split(self, sigma):
        sigma = np.clip(np.asarray(sigma, dtype=float), 0.0, self.length)
        idx = np.clip(np.searchsorted(self.breaks, sigma, side="right") - 1,
                      0, len(self.tracks) - 1)
        return idx, sigma - self.breaks[idx]

    def point_at(self, sigma):
        sigma = np.atleast_1d(np.asarray(sigma, dtype=float))
        idx, a = self._split(sigma)
        out = np.empty((*sigma.shape, 2))
        for i, tr in enumerate(self.tracks):
            m = idx == i
            if np.any(m):
                out[m] = tr.point_at(a[m])
        return out

    def tangent_at(self, sigma):
        sigma = np.atleast_1d(np.asarray(sigma, dtype=float))
        idx, a = self._split(sigma)
        out = np.empty((*sigma.shape, 2))
        for i, tr in enumerate(self.tracks):
            m = idx == i
            if np.any(m):
                out[m] = tr.tangent_at(a[m])
        return out


def spiral_inward_path(pitch: float, theta_outer: float, theta_inner: float = 0.0,
                       phase: float = 0.0) -> CompositePath:
    """盘入轨道：由外向内（θ 递减，顺时针）。"""
    sp = Spiral(pitch, phase)
    return CompositePath([SpiralTrack(sp, theta_outer, theta_inner, direction=-1)])


# --------------------------------------------------------------------------
# 刚性链递推
# --------------------------------------------------------------------------
class ChainInfeasible(RuntimeError):
    """链无法在给定路径上布置（局部曲率半径 < L/2），即物理上必然发生碰撞/卡死。"""


def _solve_backward_grid(path: CompositePath, s_in: np.ndarray, link: float,
                         span: float = 2.6, n_grid: int = 64, n_bisect: int = 48):
    """稳健兜底：网格扫描首个穿零点 + 二分（Newton 失败时调用）。"""
    s_in = np.asarray(s_in, dtype=float)
    hi = span * link
    d = np.linspace(hi / n_grid, hi, n_grid)
    lo_b = np.zeros_like(s_in)
    hi_b = np.full_like(s_in, np.nan)
    found = np.zeros(s_in.shape, dtype=bool)
    p_in = path.point_at(s_in)
    target = link * link
    prev_d = 0.0
    for di in d:
        s_probe = s_in - di
        ok = s_probe >= 0.0
        g = np.where(ok, np.sum((path.point_at(np.where(ok, s_probe, 0.0)) - p_in) ** 2,
                                axis=-1) - target, -1.0)
        cross = (~found) & (g >= 0.0)
        if np.any(cross):
            lo_b = np.where(cross, prev_d, lo_b)
            hi_b = np.where(cross, di, hi_b)
            found = found | cross
        prev_d = di
    if not np.all(found):
        bad = np.where(~found)[0][:5]
        raise ChainInfeasible(
            f"在 s_in={np.round(s_in[bad], 3)} 处向后 {hi:.3f} m 内找不到弦长 {link} 的解")
    for _ in range(n_bisect):
        mid = 0.5 * (lo_b + hi_b)
        s_probe = s_in - mid
        ok = s_probe >= 0.0
        g = np.where(ok, np.sum((path.point_at(np.where(ok, s_probe, 0.0)) - p_in) ** 2,
                                axis=-1) - target, -1.0)
        go_hi = g < 0.0
        lo_b = np.where(go_hi, mid, lo_b)
        hi_b = np.where(go_hi, hi_b, mid)
    return 0.5 * (lo_b + hi_b)


def _solve_backward(path: CompositePath, s_in: np.ndarray, link: float,
                    delta_init: np.ndarray | None = None, newton: int = 8,
                    tol: float = 1e-13):
    """给定把手弧长坐标 s_in（(T,)），求后方把手坐标 s_out = s_in - δ，
    使 |Γ(s_out) - Γ(s_in)| = link。返回 δ（(T,)）。

    主解：Newton（F(δ)=|Γ(s-δ)-Γ(s)|²-L²，F'(δ)=-2·w·Γ'(s-δ)），
    以上一连杆的 δ 为热启动 ⇒ 每连杆 3~4 次迭代即达机器精度。
    兜底：收敛失败/越界时改用网格+二分区间法。
    """
    s_in = np.asarray(s_in, dtype=float)
    p_in = path.point_at(s_in)
    target = link * link
    d = np.full(s_in.shape, link * 1.03) if delta_init is None else np.array(delta_init, float)
    for _ in range(newton):
        s_out = np.maximum(s_in - d, 0.0)
        w = path.point_at(s_out) - p_in
        t = path.tangent_at(s_out)
        F = np.sum(w * w, axis=-1) - target
        Fp = -2.0 * np.sum(w * t, axis=-1)
        Fp = np.where(np.abs(Fp) < 1e-14, -1e-14, Fp)
        step = F / Fp
        d = np.maximum(d - step, 1e-9)
        if float(np.max(np.abs(F))) < tol:
            break
    s_out = s_in - d
    if np.any(s_out < 0.0):
        raise ChainInfeasible(
            f"路径起点不足：s_in-d 最小值 {float(np.min(s_out)):.3f} < 0，需延长轨道")
    w = path.point_at(s_out) - p_in
    bad = np.abs(np.sum(w * w, axis=-1) - target) > 1e-12
    if np.any(bad):
        d[bad] = _solve_backward_grid(path, s_in[bad], link)
    return d


def chain_sigma(path: CompositePath, sigma_head: np.ndarray,
                links: np.ndarray = LINK_LEN) -> np.ndarray:
    """整链弧长坐标 (T, N_HANDLES)。sigma_head 为 (T,) 龙头弧长坐标。"""
    sigma_head = np.atleast_1d(np.asarray(sigma_head, dtype=float))
    if float(np.max(sigma_head)) > path.length or float(np.min(sigma_head)) < 0.0:
        raise ChainInfeasible(
            f"龙头弧长坐标越界：[{float(np.min(sigma_head)):.3f}, "
            f"{float(np.max(sigma_head)):.3f}] 超出路径 [0, {path.length:.3f}]")
    out = np.empty((sigma_head.size, N_HANDLES))
    out[:, 0] = sigma_head
    d_prev = None
    for k in range(N_HANDLES - 1):
        link = float(links[k])
        init = None if d_prev is None else d_prev * (link / float(links[k - 1]))
        d_prev = _solve_backward(path, out[:, k], link, delta_init=init)
        out[:, k + 1] = out[:, k] - d_prev
    return out


def chain_state(path: CompositePath, sigma_head: np.ndarray, v_head: float,
                t_grid: np.ndarray, h: float = 1e-3):
    """返回 (pos, vel, speed)，形状 (T, N_HANDLES, 2) / (T, N_HANDLES)。

    pos: 各把手位置；vel: 速度矢量；speed: 速率。
    速度用 v = (P(t+h) - P(t-h)) / (2h) 直接中心差分，避免切向公式误差。
    """
    t_grid = np.asarray(t_grid, dtype=float)
    # 龙头前向/后向微移后重算整链（δ 随位置变化），再中心差分
    sig_plus = chain_sigma(path, np.asarray(sigma_head) + v_head * h)
    sig_minus = chain_sigma(path, np.asarray(sigma_head) - v_head * h)
    p_plus = path.point_at(sig_plus.ravel()).reshape(*sig_plus.shape, 2)
    p_minus = path.point_at(sig_minus.ravel()).reshape(*sig_minus.shape, 2)
    sig0 = chain_sigma(path, sigma_head)
    pos = path.point_at(sig0.ravel()).reshape(*sig0.shape, 2)
    vel = (p_plus - p_minus) / (2.0 * h)
    speed = np.linalg.norm(vel, axis=-1)
    return pos, vel, speed


# --------------------------------------------------------------------------
# 碰撞检测（机械判定，非启发式）
# --------------------------------------------------------------------------
def board_segments(pos: np.ndarray):
    """把手位置 (...,K,2) → 各板**物理板体**中心线端点（含把手外 0.275 m 伸出）。

    返回 (a, b)，形状 (..., N_BOARDS, 2)。
    """
    d = np.diff(pos, axis=-2)                                  # (...,K-1,2)
    L = np.linalg.norm(d, axis=-1, keepdims=True)
    u = d / L
    a = pos[..., :-1, :] - STUB * u
    b = pos[..., 1:, :] + STUB * u
    return a, b


def _seg_seg_dist2(p1, d1, p2, d2):
    """两线段最小距离的平方（全向量化，凸二次函数精确解）。"""
    r = p1 - p2
    a = np.sum(d1 * d1, axis=-1)
    b = np.sum(d1 * d2, axis=-1)
    c = np.sum(d2 * d2, axis=-1)
    dd = np.sum(d1 * r, axis=-1)
    e = np.sum(d2 * r, axis=-1)
    denom = a * c - b * b

    def f(s, t):
        w = r + s[..., None] * d1 - t[..., None] * d2
        return np.sum(w * w, axis=-1)

    best = np.full(a.shape, np.inf)
    with np.errstate(divide="ignore", invalid="ignore"):
        si = (b * e - dd * c) / denom
        ti = (a * e - dd * b) / denom
    inside = (denom > 1e-14) & (si >= 0) & (si <= 1) & (ti >= 0) & (ti <= 1)
    best = np.where(inside, f(np.nan_to_num(si), np.nan_to_num(ti)), best)

    cand = [
        (np.zeros_like(a), np.clip(e / c, 0, 1)),
        (np.ones_like(a), np.clip((e + b) / c, 0, 1)),
        (np.clip(-dd / a, 0, 1), np.zeros_like(a)),
        (np.clip((b - dd) / a, 0, 1), np.ones_like(a)),
    ]
    for s, t in cand:
        best = np.minimum(best, f(s, t))
    return best


def min_board_distance(pos: np.ndarray, exclude_adjacent: bool = True,
                       chunk: int = 4_000_000) -> float:
    """整队板凳（非相邻）中心线间的最小距离 (m)。

    判定口径：板体视为宽 0.30 m 的矩形，用中心线最小距离 < 0.30 m 判碰
    （等价于"两板体矩形相交"，保守端以胶囊近似，量级 0.15 m 差以内）。
    """
    pos = np.asarray(pos, dtype=float)
    a, b = board_segments(pos)                       # (B,2)
    nb = a.shape[0]
    d1 = b - a
    ctr = 0.5 * (a + b)
    half = 0.5 * np.linalg.norm(d1, axis=-1)
    i0, j0 = np.triu_indices(nb, k=2 if exclude_adjacent else 1)
    # 粗筛：中心距 > 半长和 + 板宽 的配对，其矩形必不相交（保守剔除）
    rough = (np.linalg.norm(ctr[i0] - ctr[j0], axis=-1)
             - (half[i0] + half[j0] + BOARD_WIDTH))
    keep = rough <= 0.0
    if not np.any(keep):
        # 全部剔除 ⇒ 真实最小距离 ≥ min(rough) + 板宽 > 板宽，返回下界
        return float(np.min(rough) + BOARD_WIDTH)
    i, j = i0[keep], j0[keep]
    best = np.inf
    for st in range(0, i.size, chunk):
        sl = slice(st, st + chunk)
        d2 = _seg_seg_dist2(a[i[sl]], d1[i[sl]], a[j[sl]], d1[j[sl]])
        best = min(best, float(np.sqrt(np.min(d2))))
    return float(best)


def min_board_distance_pair(pos: np.ndarray, exclude_adjacent: bool = True):
    """返回 (最小距离, 板号 i, 板号 j)。"""
    pos = np.asarray(pos, dtype=float)
    a, b = board_segments(pos)
    nb = a.shape[0]
    d1 = b - a
    ctr = 0.5 * (a + b)
    half = 0.5 * np.linalg.norm(d1, axis=-1)
    i, j = np.triu_indices(nb, k=2 if exclude_adjacent else 1)
    rough = np.linalg.norm(ctr[i] - ctr[j], axis=-1) - (half[i] + half[j] + BOARD_WIDTH)
    keep = rough <= 0.0
    if np.any(keep):
        i, j = i[keep], j[keep]
    d2 = _seg_seg_dist2(a[i], d1[i], a[j], d1[j])
    m = int(np.argmin(d2))
    return float(np.sqrt(d2[m])), int(i[m]), int(j[m])
