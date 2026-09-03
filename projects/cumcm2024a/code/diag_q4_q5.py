"""诊断 Q4/Q5 数值差异。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import spiral_arc_length, inverse_arc_length, spiral_tangent_norm, spiral_point, spiral_r
from chain import solve_chain_thetas, chain_velocities
from solve import (B, V1, R0, THETA_0, N_BENCH, L_HEAD, L_BODY, W,
                   _build_L_list, solve_problem_3, _solve_chain_out_abs)

a = B / (2.0 * np.pi)

print("========== Q4 诊断 ==========")
q3 = solve_problem_3({})
r_start = q3["values"]["r_collision"]
th_start = r_start / a
L_list = _build_L_list()
s0_out = spiral_arc_length(th_start, B)
print("r_start = {:.6f}, th_start = {:.6f}, s0_out = {:.6f}".format(r_start, th_start, s0_out))

vmax = 0.0
vmax_t = 0
vmax_h = 0
for t in range(0, 600, 1):
    s_target = s0_out + V1 * t
    thh = inverse_arc_length(s_target, B)
    ta = _solve_chain_out_abs(thh, L_list, B)
    dth = V1 / spiral_tangent_norm(thh, B)
    sp = chain_velocities(ta, dth, B)
    i = int(np.argmax(sp))
    if sp[i] > vmax:
        vmax = float(sp[i]); vmax_t = t; vmax_h = i

print("vmax = {:.8f}  t = {}  handle = {}  (参考: 2.41421143688806, t=407, handle=189)".format(vmax, vmax_t, vmax_h))

# 在 t = vmax_t 时刻看各把手速度分布
s_target = s0_out + V1 * vmax_t
thh = inverse_arc_length(s_target, B)
ta = _solve_chain_out_abs(thh, L_list, B)
dth = V1 / spiral_tangent_norm(thh, B)
sp = chain_velocities(ta, dth, B)
print("t={}: head_r={:.4f}, head_speed={:.6f}, tail_speed={:.6f}, max_speed={:.6f}@handle{}".format(
    vmax_t, spiral_r(thh, B), sp[0], sp[-1], sp.max(), int(np.argmax(sp))))
print("speed[0..10] =", np.round(sp[:11], 6))
print("speed[180..190] =", np.round(sp[180:191], 6))

print()
print("========== Q5 诊断：p' 搜索 ==========")
d_turn = 9.0
r_turn = d_turn / 2.0
best_R = 0.0; best_p = 0.0; best_res = float('inf')
for p_prime in np.arange(0.50, 1.50, 0.005):
    ap = p_prime / (2.0 * np.pi)
    theta_in = r_turn / ap
    x_in = ap * theta_in * np.cos(theta_in)
    y_in = ap * theta_in * np.sin(theta_in)
    tx = ap * (np.cos(theta_in) - theta_in * np.sin(theta_in))
    ty = ap * (np.sin(theta_in) + theta_in * np.cos(theta_in))
    tn = np.hypot(tx, ty)
    if tn < 1e-15:
        continue
    nx = -ty / tn; ny = tx / tn
    pin_dot_nin = x_in * nx + y_in * ny
    pin_sq = x_in**2 + y_in**2
    if abs(pin_dot_nin) < 1e-15:
        continue
    R = -pin_sq / (2.0 * pin_dot_nin)
    if R <= 0 or R > r_turn:
        continue
    ox = x_in + R * nx; oy = y_in + R * ny
    dist_O1 = np.hypot(ox, oy)
    residual = abs(dist_O1 - R)
    if residual < best_res:
        best_res = residual; best_R = R; best_p = p_prime
print("best_R = {:.6f}, best_p = {:.6f}, best_res = {:.6e}".format(best_R, best_p, best_res))
print("参考: R=1.9373506171516905, p'=0.6265822784810127")

# 参考值附近的 theta_in
th_ref = 38.84150917165562
print("theta_in@ref = {:.6f}, r = a'*theta = {:.6f}".format(th_ref, (best_p/(2*np.pi))*th_ref))