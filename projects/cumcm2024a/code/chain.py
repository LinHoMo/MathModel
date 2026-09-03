"""链式约束递推模块。

从龙头极角 theta_head 出发，利用相邻把手间距 = 板凳长度的约束，
逐节二分求出全部把手极角 theta_array，再解析递推求速度。

模板来源: code-templates/optimization/differential_evolution.py（二分求根骨架）
"""

import numpy as np
from spiral import spiral_point, spiral_tangent, spiral_tangent_norm


def solve_chain_thetas(theta_head: float, L_list: list,
                       b: float = 0.55,
                       delta: float = 0.5,
                       tol: float = 1e-10) -> np.ndarray:
    """链式约束递推：给定龙头极角，求全部把手极角。

    对每节板凳 i，约束 |P(theta_i) - P(theta_{i-1})| = L_i。
    盘入阶段 theta_i > theta_{i-1}（向内排列，theta 递增），
    在区间 [theta_{i-1}, theta_{i-1} + delta] 上二分求根。

    Args:
        theta_head: 龙头前把手极角（rad）。
        L_list: 板凳长度列表 [L1, L2, ..., Ln]（m）。
        b: 螺距系数（m）。
        delta: 二分区间上界（rad）。
        tol: 收敛精度（m）。

    Returns:
        theta_array: 长度 n+1 的极角数组（rad），theta_array[0] = theta_head。
    """
    n = len(L_list)
    theta_array = np.zeros(n + 1)
    theta_array[0] = theta_head

    for i in range(1, n + 1):
        theta_prev = theta_array[i - 1]
        L_i = L_list[i - 1]

        # 二分区间 [theta_prev, theta_prev + delta]
        lo = theta_prev + 1e-12
        hi = theta_prev + delta

        # 扩大上界直到距离超过 L_i
        for _ in range(50):
            x_hi, y_hi = spiral_point(hi, b)
            x_lo, y_lo = spiral_point(lo, b)
            dist_hi = np.sqrt((x_hi - x_lo)**2 + (y_hi - y_lo)**2)
            if dist_hi >= L_i:
                break
            hi += delta

        # 二分求根
        for _ in range(200):
            mid = (lo + hi) / 2.0
            x_mid, y_mid = spiral_point(mid, b)
            x_prev, y_prev = spiral_point(theta_prev, b)
            dist = np.sqrt((x_mid - x_prev)**2 + (y_mid - y_prev)**2)
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                lo = mid
            else:
                hi = mid
        theta_array[i] = (lo + hi) / 2.0

    return theta_array


def chain_velocities(theta_array: np.ndarray, dtheta_head: float,
                     b: float = 0.55) -> np.ndarray:
    """速度线性递推：dot_theta_i = (u_i . T_{i-1}) / (u_i . T_i) * dot_theta_{i-1}。

    Args:
        theta_array: 全部把手极角数组（rad）。
        dtheta_head: 龙头角速度（rad/s）。
        b: 螺距系数（m）。

    Returns:
        speed_array: 全部把手速度大小数组（m/s）。
    """
    n = len(theta_array) - 1
    dtheta = np.zeros(n + 1)
    dtheta[0] = dtheta_head

    for i in range(1, n + 1):
        x_i, y_i = spiral_point(theta_array[i], b)
        x_prev, y_prev = spiral_point(theta_array[i - 1], b)
        ux = x_i - x_prev
        uy = y_i - y_prev

        tx_prev, ty_prev = spiral_tangent(theta_array[i - 1], b)
        tx_i, ty_i = spiral_tangent(theta_array[i], b)

        numerator = ux * tx_prev + uy * ty_prev
        denominator = ux * tx_i + uy * ty_i
        if abs(denominator) < 1e-12:
            denominator = 1e-12 if denominator >= 0 else -1e-12

        dtheta[i] = (numerator / denominator) * dtheta[i - 1]

    # 速度大小 = |dtheta_i| * |T(theta_i)|
    speed = np.zeros(n + 1)
    for i in range(n + 1):
        norm = spiral_tangent_norm(theta_array[i], b)
        speed[i] = abs(dtheta[i]) * norm

    return speed
