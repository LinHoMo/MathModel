"""诊断 Q4 v4：检查 phi_array 中 handle 189 附近的 phi 跳变。"""
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
    n = len(L_list)
    phi_arr = np.zeros(n + 1)
    phi_arr[0] = phi_head
    for i in range(1, n + 1):
        phi_prev = phi_arr[i - 1]
        L_i = L_list[i - 1]
        hi = phi_prev - 1e-12
        lo = max(1e-8, phi_prev - delta)
        for _ in range(100):
            x_hi, y_hi = spiral_point(hi, b)
            x_lo, y_lo = spiral_point(lo, b)
            if np.sqrt((x_hi-x_lo)**2+(y_hi-y_lo)**2) >= L_i:
                break
            lo -= delta
            if lo < 1e-8:
                lo = 1e-8
                break
        for _ in range(200):
            mid = (lo + hi) / 2.0
            x_mid, y_mid = spiral_point(mid, b)
            x_prev, y_prev = spiral_point(phi_prev, b)
            dist = np.sqrt((x_mid-x_prev)**2+(y_mid-y_prev)**2)
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                hi = mid
            else:
                lo = mid
        phi_arr[i] = (lo + hi) / 2.0
    return phi_arr

t_out = 407
s_target = s0_out + V1 * t_out
phi_head = inverse_arc_length(s_target, B)
phi_arr = solve_chain_out(phi_head, L_list, B)

# 打印 handle 185-195 的 phi, r, 位置
print("handle | phi      | r(m)    | dphi(m)  | x(m)     | y(m)")
for i in range(185, min(200, len(phi_arr))):
    r = spiral_r(phi_arr[i], B)
    x, y = spiral_point(phi_arr[i], B)
    dphi = phi_arr[i] - phi_arr[i-1] if i > 0 else 0
    print("{:6d} | {:8.4f} | {:7.4f} | {:8.4f} | {:8.4f} | {:8.4f}".format(
        i, phi_arr[i], r, dphi, x, y))

# 检查圈数跳变
print("\n圈数分析:")
for i in range(185, min(200, len(phi_arr))):
    r = spiral_r(phi_arr[i], B)
    dphi = phi_arr[i] - phi_arr[i-1] if i > 0 else 0
    圈数 = phi_arr[i] / (2 * np.pi)
    print("handle {}: phi={:.2f}, 圈={:.2f}, dphi={:.4f} ({:.4f}圈)".format(
        i, phi_arr[i], 圈数, dphi, d圈))

# 检查是否在螺线相邻圈上
# 如果 dphi ≈ 2*pi，说明跨了一整圈
print("\n2*pi =", 2*np.pi, "rad")
print("如果 dphi 接近 2*pi，说明把手跨越了一个螺线圈")
