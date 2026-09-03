"""验证盘出正确链方向（theta 从龙头向龙尾递减）下的速度与最大速度。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_tangent_norm,
                    spiral_point, spiral_r)
from chain import chain_velocities
from solve import (B, V1, THETA_0, N_BENCH, _build_L_list, solve_problem_3)


def solve_chain_out_decreasing(theta_head, L_list, b=B, delta=0.5, tol=1e-10):
    """盘出：从龙头向龙尾 theta 递减（龙尾在更小极径处）。"""
    n = len(L_list)
    theta_array = np.zeros(n + 1)
    theta_array[0] = theta_head
    for i in range(1, n + 1):
        theta_prev = theta_array[i - 1]
        L_i = L_list[i - 1]
        hi = theta_prev - 1e-12
        lo = theta_prev - delta
        for _ in range(50):
            x_hi, y_hi = spiral_point(lo, b)
            x_lo, y_lo = spiral_point(hi, b)
            dist = np.hypot(x_hi - x_lo, y_hi - y_lo)
            if dist >= L_i:
                break
            lo -= delta
        for _ in range(200):
            mid = (lo + hi) / 2.0
            x_mid, y_mid = spiral_point(mid, b)
            x_prev, y_prev = spiral_point(theta_prev, b)
            dist = np.hypot(x_mid - x_prev, y_mid - y_prev)
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                hi = mid
            else:
                lo = mid
        theta_array[i] = (lo + hi) / 2.0
    return theta_array


def solve_chain_out_increasing(theta_head, L_list, b=B, delta=0.5, tol=1e-10):
    """盘出：theta 递增（龙尾在更大极径处）。"""
    n = len(L_list)
    theta_array = np.zeros(n + 1)
    theta_array[0] = theta_head
    for i in range(1, n + 1):
        theta_prev = theta_array[i - 1]
        L_i = L_list[i - 1]
        lo = theta_prev + 1e-12
        hi = theta_prev + delta
        for _ in range(50):
            x_hi, y_hi = spiral_point(hi, b)
            x_lo, y_lo = spiral_point(lo, b)
            dist = np.hypot(x_hi - x_lo, y_hi - y_lo)
            if dist >= L_i:
                break
            hi += delta
        for _ in range(200):
            mid = (lo + hi) / 2.0
            x_mid, y_mid = spiral_point(mid, b)
            x_prev, y_prev = spiral_point(theta_prev, b)
            dist = np.hypot(x_mid - x_prev, y_mid - y_prev)
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                lo = mid
            else:
                hi = mid
        theta_array[i] = (lo + hi) / 2.0
    return theta_array


a = B / (2.0 * np.pi)
q3 = solve_problem_3({})
r_start = q3["values"]["r_collision"]
th_start = r_start / a
L_list = _build_L_list()
s0 = spiral_arc_length(th_start, B)

print("r_start={:.6f}  th_start={:.6f}".format(r_start, th_start))

for name, fn in [("decreasing", solve_chain_out_decreasing),
                 ("increasing", solve_chain_out_increasing)]:
    vmax = 0.0; vmax_t = 0; vmax_h = 0
    for t in range(0, 650, 1):
        st = s0 + V1 * t
        thh = inverse_arc_length(st, B)
        ta = fn(thh, L_list, B)
        dth = V1 / spiral_tangent_norm(thh, B)
        sp = chain_velocities(ta, dth, B)
        i = int(np.argmax(sp))
        if sp[i] > vmax:
            vmax = float(sp[i]); vmax_t = t; vmax_h = i
    print("{}: vmax={:.8f} t={} handle={}".format(name, vmax, vmax_t, vmax_h))

# 详细查看 decreasing 配置在 t=407 附近
thh = inverse_arc_length(s0 + V1 * 407, B)
ta = solve_chain_out_decreasing(thh, L_list, B)
sp = chain_velocities(ta, V1 / spiral_tangent_norm(thh, B), B)
print("\n[t=407 decreasing] head_r={:.4f} head_speed={:.6f}".format(spiral_r(thh, B), sp[0]))
print("speed[0..10] =", np.round(sp[:11], 6))
print("speed[185..195] =", np.round(sp[185:196], 6))
print("max_speed={:.6f} @ handle {}".format(sp.max(), int(np.argmax(sp))))
print("tail_r={:.4f}".format(spiral_r(ta[-1], B)))
print("r[0]={:.4f} r[189]={:.4f}".format(spiral_r(ta[0], B), spiral_r(ta[189], B)))