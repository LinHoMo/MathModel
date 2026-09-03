"""诊断 Q4：对比盘出链递增 vs 递减方向的速度。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_point,
                    spiral_r, spiral_tangent, spiral_tangent_norm)
from chain import chain_velocities

B = 0.55; V1 = 1.0; THETA_0 = 32 * np.pi
N_BENCH = 222; L_HEAD = 3.41; L_BODY = 2.20; W = 0.30
L_list = [L_HEAD] + [L_BODY] * (N_BENCH - 1)

# Q2 的 t* 和 r_collision
t_star = 412.83
s0 = spiral_arc_length(THETA_0, B)
theta_head_at_tstar = inverse_arc_length(s0 - V1 * t_star, B)
r_collision = spiral_r(theta_head_at_tstar, B)
print("r_collision =", r_collision)

# 盘出起点
a = B / (2.0 * np.pi)
theta_start_abs = r_collision / a
s0_out = spiral_arc_length(theta_start_abs, B)
print("theta_start_abs =", theta_start_abs, " s0_out =", s0_out)

# 在 t=400s 盘出时
t_out = 400
s_target = s0_out + V1 * t_out
theta_head_abs = inverse_arc_length(s_target, B)
print("\nt_out={}s: theta_head_abs={:.2f}, r_head={:.3f}m".format(
    t_out, theta_head_abs, spiral_r(theta_head_abs, B)))

# --- 方向 A: 递增（当前代码，错误） ---
def chain_out_increasing(theta_head_abs, L_list, b, delta=0.5, tol=1e-10):
    n = len(L_list)
    theta_array = np.zeros(n + 1)
    theta_array[0] = theta_head_abs
    for i in range(1, n + 1):
        theta_prev = theta_array[i - 1]
        L_i = L_list[i - 1]
        lo = theta_prev + 1e-12
        hi = theta_prev + delta
        for _ in range(50):
            x_hi, y_hi = spiral_point(hi, b)
            x_lo, y_lo = spiral_point(lo, b)
            if np.sqrt((x_hi-x_lo)**2+(y_hi-y_lo)**2) >= L_i:
                break
            hi += delta
        for _ in range(200):
            mid = (lo + hi) / 2.0
            x_mid, y_mid = spiral_point(mid, b)
            x_prev, y_prev = spiral_point(theta_prev, b)
            dist = np.sqrt((x_mid-x_prev)**2+(y_mid-y_prev)**2)
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                lo = mid
            else:
                hi = mid
        theta_array[i] = (lo + hi) / 2.0
    return theta_array

# --- 方向 B: 递减（正确，龙头大theta，龙尾小theta） ---
def chain_out_decreasing(theta_head_abs, L_list, b, delta=0.5, tol=1e-10):
    n = len(L_list)
    theta_array = np.zeros(n + 1)
    theta_array[0] = theta_head_abs
    for i in range(1, n + 1):
        theta_prev = theta_array[i - 1]
        L_i = L_list[i - 1]
        hi = theta_prev - 1e-12
        lo = max(theta_prev - delta, 1e-8)
        for _ in range(100):
            x_lo, y_lo = spiral_point(lo, b)
            x_hi, y_hi = spiral_point(hi, b)
            if np.sqrt((x_lo-x_hi)**2+(y_lo-y_hi)**2) >= L_i:
                break
            lo -= delta
            if lo < 1e-8:
                lo = 1e-8
                break
        for _ in range(200):
            mid = (lo + hi) / 2.0
            x_mid, y_mid = spiral_point(mid, b)
            x_prev, y_prev = spiral_point(theta_prev, b)
            dist = np.sqrt((x_mid-x_prev)**2+(y_mid-y_prev)**2)
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                hi = mid  # 需要更大距离 -> 更小 theta
            else:
                lo = mid  # 需要更小距离 -> 更大 theta
        theta_array[i] = (lo + hi) / 2.0
    return theta_array

dtheta_head = V1 / spiral_tangent_norm(theta_head_abs, B)

# 方向 A
theta_A = chain_out_increasing(theta_head_abs, L_list, B)
speeds_A = chain_velocities(theta_A, dtheta_head, B)
print("\n方向A (递增): v_max={:.4f} @ handle={}".format(
    np.max(speeds_A), np.argmax(speeds_A)))
print("  theta range: [{:.2f}, {:.2f}]".format(theta_A.min(), theta_A.max()))

# 方向 B
theta_B = chain_out_decreasing(theta_head_abs, L_list, B)
speeds_B = chain_velocities(theta_B, dtheta_head, B)
print("\n方向B (递减): v_max={:.4f} @ handle={}".format(
    np.max(speeds_B), np.argmax(speeds_B)))
print("  theta range: [{:.2f}, {:.2f}]".format(theta_B.min(), theta_B.max()))
print("  r range: [{:.3f}, {:.3f}] m".format(
    spiral_r(theta_B.min(), B), spiral_r(theta_B.max(), B)))

# 多个时间点
print("\n--- 多时间点扫描 (方向B) ---")
for t_out in [0, 100, 200, 300, 400, 407, 500]:
    s_target = s0_out + V1 * t_out
    try:
        theta_head_abs = inverse_arc_length(s_target, B)
    except ValueError:
        print("t={:4d}s: s_target 超界".format(t_out))
        continue
    dtheta_head = V1 / spiral_tangent_norm(theta_head_abs, B)
    theta_B = chain_out_decreasing(theta_head_abs, L_list, B)
    speeds_B = chain_velocities(theta_B, dtheta_head, B)
    idx_max = np.argmax(speeds_B)
    print("t={:4d}s  r_head={:6.2f}m  v_max={:.4f} @ handle={}  r_at_vmax={:.3f}m".format(
        t_out, spiral_r(theta_head_abs, B),
        speeds_B[idx_max], idx_max, spiral_r(theta_B[idx_max], B)))
