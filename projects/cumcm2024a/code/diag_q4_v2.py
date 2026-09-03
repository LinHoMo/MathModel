"""诊断 Q4 v2：盘出链递减(phi_i < phi_head)，复用盘入几何。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_point,
                    spiral_r, spiral_tangent, spiral_tangent_norm)
from chain import chain_velocities

B = 0.55; V1 = 1.0; THETA_0 = 32 * np.pi
N_BENCH = 222; L_HEAD = 3.41; L_BODY = 2.20; W = 0.30
L_list = [L_HEAD] + [L_BODY] * (N_BENCH - 1)

t_star = 412.83
s0 = spiral_arc_length(THETA_0, B)
theta_head_at_tstar = inverse_arc_length(s0 - V1 * t_star, B)
r_collision = spiral_r(theta_head_at_tstar, B)
a = B / (2.0 * np.pi)

phi_start = r_collision / a
s0_out = spiral_arc_length(phi_start, B)

def solve_chain_out(phi_head, L_list, b=0.55, delta=0.5, tol=1e-10):
    """盘出链式约束递推：phi 递减（把手在龙头内侧）。
    
    几何等价于盘入（|P_out(phi1)-P_out(phi2)| = |P_in(phi1)-P_in(phi2)|），
    但方向相反：phi_i < phi_{i-1}。
    """
    n = len(L_list)
    phi_arr = np.zeros(n + 1)
    phi_arr[0] = phi_head
    
    for i in range(1, n + 1):
        phi_prev = phi_arr[i - 1]
        L_i = L_list[i - 1]
        
        # phi_i < phi_prev（递减），二分区间 [max(1e-8, phi_prev-delta), phi_prev]
        hi = phi_prev - 1e-12
        lo = max(1e-8, phi_prev - delta)
        
        # 扩大下界
        for _ in range(100):
            x_hi, y_hi = spiral_point(hi, b)
            x_lo, y_lo = spiral_point(lo, b)
            dist = np.sqrt((x_hi - x_lo)**2 + (y_hi - y_lo)**2)
            if dist >= L_i:
                break
            lo -= delta
            if lo < 1e-8:
                lo = 1e-8
                break
        
        # 二分：phi 越小，距离越大
        for _ in range(200):
            mid = (lo + hi) / 2.0
            x_mid, y_mid = spiral_point(mid, b)
            x_prev, y_prev = spiral_point(phi_prev, b)
            dist = np.sqrt((x_mid - x_prev)**2 + (y_mid - y_prev)**2)
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                hi = mid  # 需要更小 phi -> 更大距离
            else:
                lo = mid  # 需要更大 phi -> 更小距离
        phi_arr[i] = (lo + hi) / 2.0
    
    return phi_arr

# 测试 t_out=407s
t_out = 407
s_target = s0_out + V1 * t_out
phi_head = inverse_arc_length(s_target, B)
print("t_out={}s: phi_head={:.2f}, r_head={:.3f}m".format(
    t_out, phi_head, spiral_r(phi_head, B)))

phi_arr = solve_chain_out(phi_head, L_list, B)
print("phi range: [{:.2f}, {:.2f}]".format(phi_arr.min(), phi_arr.max()))
print("r range: [{:.3f}, {:.3f}] m".format(
    spiral_r(phi_arr.min(), B), spiral_r(phi_arr.max(), B)))

# 速度递推：phi 递减方向
# dphi_head = +v1 / norm (向外, phi 递增)
# 但 phi_array 是递减的，所以 dphi_0 = +v1/norm
# chain_velocities 中的递推公式不依赖方向，只依赖几何
dphi_head = V1 / spiral_tangent_norm(phi_head, B)
speeds = chain_velocities(phi_arr, dphi_head, B)

idx_max = np.argmax(speeds)
print("\nv_max = {:.6f} @ handle {}".format(speeds[idx_max], idx_max))
print("speed[0] = {:.6f}".format(speeds[0]))
print("speed[189] = {:.6f}".format(speeds[189] if len(speeds) > 189 else -1))
print("speed[222] = {:.6f}".format(speeds[222] if len(speeds) > 222 else -1))

# 全局扫描
print("\n--- 全局扫描 ---")
v_max_global = 0.0
t_at_vmax = 0.0
handle_at_vmax = 0

for t_out in range(0, 600 + 1, 1):
    s_target = s0_out + V1 * t_out
    try:
        phi_head = inverse_arc_length(s_target, B)
    except ValueError:
        continue
    
    phi_arr = solve_chain_out(phi_head, L_list, B)
    dphi_head = V1 / spiral_tangent_norm(phi_head, B)
    speeds = chain_velocities(phi_arr, dphi_head, B)
    
    idx_max = np.argmax(speeds)
    if speeds[idx_max] > v_max_global:
        v_max_global = float(speeds[idx_max])
        t_at_vmax = float(t_out)
        handle_at_vmax = int(idx_max)

print("v_max = {:.6f} @ t={}s, handle={}".format(v_max_global, t_at_vmax, handle_at_vmax))
print("冻结值: v_max=2.414211 @ t=407s, handle=189")
