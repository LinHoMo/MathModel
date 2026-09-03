"""诊断 Q4 v7：弧长制导初值，避免跨圈跳跃。"""
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

def P_out(phi, b=0.55):
    aa = b / (2.0 * np.pi)
    return (-aa * phi * np.cos(phi), -aa * phi * np.sin(phi))

def T_out(phi, b=0.55):
    aa = b / (2.0 * np.pi)
    return (-aa * (np.cos(phi) - phi * np.sin(phi)),
            -aa * (np.sin(phi) + phi * np.cos(phi)))

def T_norm_out(phi, b=0.55):
    tx, ty = T_out(phi, b)
    return np.hypot(tx, ty)

def s_out(phi, b=0.55):
    """盘出螺线弧长 = 盘入螺线弧长（因为 |T_out| = |T_in|）"""
    return spiral_arc_length(abs(phi), b)

def solve_chain_arc_guided(phi_head, L_list, b=0.55, tol=1e-10):
    """弧长制导链递推：用弧长估计初值，避免跨圈跳跃。
    
    对每节板凳 i，从 phi_{i-1} 出发，沿螺线弧长方向递减约 L_i，
    得到 phi_i 的初始估计，再精确二分。
    """
    n = len(L_list)
    phi_arr = np.zeros(n + 1)
    phi_arr[0] = phi_head
    
    for i in range(1, n + 1):
        phi_prev = phi_arr[i - 1]
        L_i = L_list[i - 1]
        
        # 弧长估计：phi_prev 处的切向模长 * dphi ≈ L_i
        # dphi_est = L_i / |T(phi_prev)|
        norm_prev = T_norm_out(phi_prev, b)
        dphi_est = L_i / norm_prev
        
        # 初值：phi_est = phi_prev - dphi_est（递减）
        phi_est = phi_prev - dphi_est
        
        # 在 phi_est 附近搜索 [phi_est - 0.3, phi_est + 0.3]
        lo = phi_est - 0.3
        hi = phi_est + 0.3
        # 确保 hi < phi_prev（递减方向）
        if hi >= phi_prev:
            hi = phi_prev - 1e-12
        
        # 检查区间内是否有解
        p_prev = P_out(phi_prev, b)
        p_lo = P_out(lo, b)
        p_hi = P_out(hi, b)
        d_lo = np.hypot(p_lo[0]-p_prev[0], p_lo[1]-p_prev[1])
        d_hi = np.hypot(p_hi[0]-p_prev[0], p_hi[1]-p_prev[1])
        
        if d_lo < L_i and d_hi < L_i:
            # 区间内都太小，需要扩大
            for _ in range(50):
                lo -= 0.3
                p_lo = P_out(lo, b)
                d_lo = np.hypot(p_lo[0]-p_prev[0], p_lo[1]-p_prev[1])
                if d_lo >= L_i:
                    break
        elif d_lo > L_i and d_hi > L_i:
            for _ in range(50):
                hi += 0.1
                if hi >= phi_prev:
                    hi = phi_prev - 1e-12
                    break
                p_hi = P_out(hi, b)
                d_hi = np.hypot(p_hi[0]-p_prev[0], p_hi[1]-p_prev[1])
                if d_hi <= L_i:
                    break
        
        # 二分
        for _ in range(200):
            mid = (lo + hi) / 2.0
            p_mid = P_out(mid, b)
            dist = np.hypot(p_mid[0]-p_prev[0], p_mid[1]-p_prev[1])
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                hi = mid  # 需要更小 phi -> 更大距离
            else:
                lo = mid  # 需要更大 phi -> 更小距离
        phi_arr[i] = (lo + hi) / 2.0
    
    return phi_arr

def chain_vel_out(phi_arr, dphi_head, b=0.55):
    n = len(phi_arr) - 1
    dphi = np.zeros(n + 1)
    dphi[0] = dphi_head
    for i in range(1, n + 1):
        p_i = P_out(phi_arr[i], b)
        p_prev = P_out(phi_arr[i-1], b)
        ux = p_i[0] - p_prev[0]
        uy = p_i[1] - p_prev[1]
        tx_prev, ty_prev = T_out(phi_arr[i-1], b)
        tx_i, ty_i = T_out(phi_arr[i], b)
        num = ux * tx_prev + uy * ty_prev
        den = ux * tx_i + uy * ty_i
        if abs(den) < 1e-12:
            den = 1e-12
        dphi[i] = (num / den) * dphi[i-1]
    speed = np.zeros(n + 1)
    for i in range(n + 1):
        speed[i] = abs(dphi[i]) * T_norm_out(phi_arr[i], b)
    return speed

# 测试 t_out=407
t_out = 407
s_target = s0_out + V1 * t_out
phi_head = inverse_arc_length(s_target, B)
phi_arr = solve_chain_arc_guided(phi_head, L_list, B)

# 检查 handle 185-200
print("handle | phi      | r(m)    | dphi    | x(m)     | y(m)")
for i in range(185, min(200, len(phi_arr))):
    p = P_out(phi_arr[i], B)
    r = a * abs(phi_arr[i])
    dphi = phi_arr[i] - phi_arr[i-1] if i > 0 else 0
    print("{:6d} | {:8.4f} | {:7.4f} | {:8.4f} | {:8.4f} | {:8.4f}".format(
        i, phi_arr[i], r, dphi, p[0], p[1]))

# 速度
dphi_head = V1 / T_norm_out(phi_head, B)
speeds = chain_vel_out(phi_arr, dphi_head, B)
idx_max = np.argmax(speeds)
print("\nv_max = {:.6f} @ handle {}".format(speeds[idx_max], idx_max))
print("speed[0] = {:.6f}".format(speeds[0]))
print("speed[188] = {:.6f}".format(speeds[188]))
print("speed[189] = {:.6f}".format(speeds[189]))
print("speed[190] = {:.6f}".format(speeds[190]))

# 全局扫描
print("\n--- 全局扫描 ---")
v_g = 0.0; t_g = 0; h_g = 0
for t_out in range(0, 500 + 1, 1):
    s_target = s0_out + V1 * t_out
    try:
        phi_head = inverse_arc_length(s_target, B)
    except ValueError:
        continue
    phi_arr = solve_chain_arc_guided(phi_head, L_list, B)
    dphi_head = V1 / T_norm_out(phi_head, B)
    speeds = chain_vel_out(phi_arr, dphi_head, B)
    idx = np.argmax(speeds)
    if speeds[idx] > v_g:
        v_g = float(speeds[idx]); t_g = t_out; h_g = int(idx)
print("v_max={:.6f} @ t={}s handle={}".format(v_g, t_g, h_g))
print("冻结值: v_max=2.414211 @ t=407s handle=189")
