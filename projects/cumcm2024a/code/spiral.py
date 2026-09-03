"""等距螺线弧长参数化模块。

提供等距螺线 r = b*theta/(2*pi) 的几何参数化：
极径、位置向量、切向向量、弧长闭式积分、弧长反解（二分法）。

模板来源: code-templates/optimization/differential_evolution.py（借鉴无梯度求根骨架）
"""

import numpy as np


def spiral_r(theta: float, b: float = 0.55) -> float:
    """等距螺线极径 r = a*theta，其中 a = b/(2*pi)。

    Args:
        theta: 极角（rad）。
        b: 螺距系数（m），默认 0.55。

    Returns:
        极径 r（m）。
    """
    a = b / (2.0 * np.pi)
    return a * theta


def spiral_point(theta: float, b: float = 0.55) -> tuple:
    """螺线位置向量 P(theta) = (r*cos(theta), r*sin(theta))。

    Args:
        theta: 极角（rad）。
        b: 螺距系数（m）。

    Returns:
        (x, y) 位置坐标（m）。
    """
    a = b / (2.0 * np.pi)
    r = a * theta
    return (r * np.cos(theta), r * np.sin(theta))


def spiral_tangent(theta: float, b: float = 0.55) -> tuple:
    """螺线切向向量 T(theta) = dP/dtheta。

    T = a*(cos(theta) - theta*sin(theta), sin(theta) + theta*cos(theta))

    Args:
        theta: 极角（rad）。
        b: 螺距系数（m）。

    Returns:
        (Tx, Ty) 切向向量（m/rad）。
    """
    a = b / (2.0 * np.pi)
    tx = a * (np.cos(theta) - theta * np.sin(theta))
    ty = a * (np.sin(theta) + theta * np.cos(theta))
    return (tx, ty)


def spiral_tangent_norm(theta: float, b: float = 0.55) -> float:
    """螺线切向向量的模长 |T(theta)| = a*sqrt(1+theta^2)。

    Args:
        theta: 极角（rad）。
        b: 螺距系数（m）。

    Returns:
        切向模长（m/rad）。
    """
    a = b / (2.0 * np.pi)
    return a * np.sqrt(1.0 + theta * theta)


def spiral_arc_length(theta: float, b: float = 0.55) -> float:
    """等距螺线弧长闭式积分 s(theta)。

    s(theta) = (a/2) * [theta*sqrt(1+theta^2) + ln(theta + sqrt(1+theta^2))]
    其中 a = b/(2*pi)。

    Args:
        theta: 极角（rad），须 >= 0。
        b: 螺距系数（m）。

    Returns:
        弧长 s（m）。
    """
    a = b / (2.0 * np.pi)
    sq = np.sqrt(1.0 + theta * theta)
    return (a / 2.0) * (theta * sq + np.log(theta + sq))


def inverse_arc_length(s_target: float, b: float = 0.55,
                       theta_lo: float = 1e-8,
                       theta_hi: float = 200.0,
                       tol: float = 1e-10) -> float:
    """弧长反解：给定目标弧长 s_target，求对应的 theta。

    s(theta) 在 theta > 0 严格单调递增，用二分法反解。

    Args:
        s_target: 目标弧长（m）。
        b: 螺距系数（m）。
        theta_lo: 二分下界（rad）。
        theta_hi: 二分上界（rad）。
        tol: 收敛精度（m）。

    Returns:
        对应的极角 theta（rad）。

    Raises:
        ValueError: 当 s_target 超出 [s(theta_lo), s(theta_hi)] 时。
    """
    s_lo = spiral_arc_length(theta_lo, b)
    s_hi = spiral_arc_length(theta_hi, b)
    if s_target <= 0:
        return theta_lo
    if s_target < s_lo - 1e-12 or s_target > s_hi + 1e-12:
        raise ValueError(
            "s_target={} 超出二分区间 [{}, {}]".format(s_target, s_lo, s_hi))

    for _ in range(200):
        theta_mid = (theta_lo + theta_hi) / 2.0
        s_mid = spiral_arc_length(theta_mid, b)
        if abs(s_mid - s_target) < tol:
            return theta_mid
        if s_mid < s_target:
            theta_lo = theta_mid
        else:
            theta_hi = theta_mid
    return (theta_lo + theta_hi) / 2.0


def dtheta_dt_head(theta_head: float, v1: float = 1.0,
                   b: float = 0.55) -> float:
    """龙头角速度 dtheta_head/dt = -v1 / (a*sqrt(1+theta_head^2))。

    盘入阶段 theta 单调减小，故取负号。

    Args:
        theta_head: 龙头当前极角（rad）。
        v1: 龙头弧长速度（m/s），默认 1.0。
        b: 螺距系数（m）。

    Returns:
        龙头角速度（rad/s），盘入为负。
    """
    norm = spiral_tangent_norm(theta_head, b)
    return -v1 / norm
