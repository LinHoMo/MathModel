"""诊断 Q4 v6：允许 phi 穿过 0，把手跨越到盘入螺线。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_point,
                    spiral_r, spiral_tangent, spiral_tangent_norm)

B = 0.55; V1 = 1.0; THETA_0 = 32 * np.pi
N_BENCH = 222; L_HEAD = 3.41; L_BODY = 2.20; W = 0.30
L_list = [L_HEAD] + [L_BODY] * (N_BENCH - 1)
a = B / (2.0 * np.pi)

t_star = 412.83
s0 = spiral_arc_length(THETA_0, B)
theta_head_at_tstar = inverse_arc_length(s0 - V1 * t_star, B)
r_collision = spiral_r(theta_head_at_tstar, B)
phi_start = r_collision / a
s0_out = spiral_arc_length(phi_start, B)

def spiral_point_unified(phi, b=0.55):
    """统一螺线点：phi > 0 在盘出侧，phi < 0 在盘入侧。
    
    P(phi) = (a*phi*cos(phi), a*phi*sin(phi))  对所有 phi
    
    盘出螺线（phi > 0）: P_out = (a*phi*cos(phi), a*phi*sin(phi))
    但盘出螺线应该是中心对称的...
    
    实际上：盘入 r = a*theta (theta > 0)
    盘出 r = a*phi (phi > 0)，但方向相反（绕原点旋转180度）
    P_in(theta) = (a*theta*cos(theta), a*theta*sin(theta))
    P_out(phi) = (-a*phi*cos(phi), -a*phi*sin(phi)) = -P_in(phi)
    
    当 phi 从正穿过 0 变负时：
    P_out(phi<0) = -P_in(phi<0) = -P_in(-|phi|) 
    P_in(-|phi|) = (a*(-|phi|)*cos(-|phi|), a*(-|phi|)*sin(-|phi|))
                 = (-a*|phi|*cos(|phi|), a*|phi|*sin(|phi|))
    P_out(phi<0) = (a*|phi|*cos(|phi|), -a*|phi|*sin(|phi|))
    
    这不等于 P_in(|phi|) = (a*|phi|*cos(|phi|), a*|phi|*sin(|phi|))
    
    所以 phi 穿过 0 后在盘出螺线的延伸部分，不是盘入螺线。
    """
    aa = b / (2.0 * np.pi)
    # P_out(phi) = -P_in(phi) = (-a*phi*cos(phi), -a*phi*sin(phi))
    return (-aa * phi * np.cos(phi), -aa * phi * np.sin(phi))

def spiral_tangent_unified(phi, b=0.55):
    """盘出螺线切向 T(phi) = dP_out/dphi = (-a*(cos(phi)-phi*sin(phi)), -a*(sin(phi)+phi*cos(phi)))"""
    aa = b / (2.0 * np.pi)
    tx = -aa * (np.cos(phi) - phi * np.sin(phi))
    ty = -aa * (np.sin(phi) + phi * np.cos(phi))
    return (tx, ty)

def tangent_norm_unified(phi, b=0.55):
    tx, ty = spiral_tangent_unified(phi, b)
    return np.hypot(tx, ty)

def solve_chain_unified(phi_head, L_list, b=0.55, delta=0.5, tol=1e-10):
    """统一链递推：phi 递减，允许穿过 0 变负。"""
    n = len(L_list)
    phi_arr = np.zeros(n + 1)
    phi_arr[0] = phi_head
    for i in range(1, n + 1):
        phi_prev = phi_arr[i - 1]
        L_i = L_list[i - 1]
        hi = phi_prev - 1e-12
        lo = phi_prev - delta
        # 扩大下界
        for _ in range(200):
            p_hi = spiral_point_unified(hi, b)
            p_lo = spiral_point_unified(lo, b)
            if np.hypot(p_hi[0]-p_lo[0], p_hi[1]-p_lo[1]) >= L_i:
                break
            lo -= delta
        # 二分
        for _ in range(200):
            mid = (lo + hi) / 2.0
            p_mid = spiral_point_unified(mid, b)
            p_prev = spiral_point_unified(phi_prev, b)
            dist = np.hypot(p_mid[0]-p_prev[0], p_mid[1]-p_prev[1])
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                hi = mid
            else:
                lo = mid
        phi_arr[i] = (lo + hi) / 2.0
    return phi_arr

def chain_vel_unified(phi_arr, dphi_head, b=0.55):
    n = len(phi_arr) - 1
    dphi = np.zeros(n + 1)
    dphi[0] = dphi_head
    for i in range(1, n + 1):
        p_i = spiral_point_unified(phi_arr[i], b)
        p_prev = spiral_point_unified(phi_arr[i-1], b)
        ux = p_i[0] - p_prev[0]
        uy = p_i[1] - p_prev[1]
        tx_prev, ty_prev = spiral_tangent_unified(phi_arr[i-1], b)
        tx_i, ty_i = spiral_tangent_unified(phi_arr[i], b)
        num = ux * tx_prev + uy * ty_prev
        den = ux * tx_i + uy * ty_i
        if abs(den) < 1e-12:
            den = 1e-12
        dphi[i] = (num / den) * dphi[i-1]
    speed = np.zeros(n + 1)
    for i in range(n + 1):
        speed[i] = abs(dphi[i]) * tangent_norm_unified(phi_arr[i], b)
    return speed

# 测试 t_out=407
t_out = 407
s_target = s0_out + V1 * t_out
phi_head = inverse_arc_length(s_target, B)
phi_arr = solve_chain_unified(phi_head, L_list, B)

# 检查 handle 185-200
print("handle | phi      | r(m)    | dphi    | x(m)     | y(m)")
for i in range(185, min(200, len(phi_arr))):
    p = spiral_point_unified(phi_arr[i], B)
    r = a * abs(phi_arr[i])
    dphi = phi_arr[i] - phi_arr[i-1] if i > 0 else 0
    print("{:6d} | {:8.4f} | {:7.4f} | {:8.4f} | {:8.4f} | {:8.4f}".format(
        i, phi_arr[i], r, dphi, p[0], p[1]))

# 速度
dphi_head = V1 / tangent_norm_unified(phi_head, B)
speeds = chain_vel_unified(phi_arr, dphi_head, B)
idx_max = np.argmax(speeds)
print("\nv_max = {:.6f} @ handle {}".format(speeds[idx_max], idx_max))
print("speed[0] = {:.6f}".format(speeds[0]))
print("speed[189] = {:.6f}".format(speeds[189]))
print("speed[190] = {:.6f}".format(speeds[190]))

# 冻结值参考
print("\n冻结值: v_max=2.414211 @ handle 189")
print("冻结值: speed[188]=1.1626, speed[189]=2.4142, speed[190]=2.4126")
