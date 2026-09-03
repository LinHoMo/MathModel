"""全链路诊断：盘入速度放大 + 盘出方向 + Q5 几何。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_tangent_norm,
                    spiral_point, spiral_r, spiral_tangent)
from chain import solve_chain_thetas, chain_velocities
from solve import B, V1, THETA_0, N_BENCH, L_HEAD, L_BODY, W, _build_L_list

a = B / (2.0 * np.pi)
L_list = _build_L_list()
s0 = spiral_arc_length(THETA_0, B)

print("========== 盘入：速度分布诊断 ==========")
print("a = {:.8f}, s0 = {:.6f} m".format(a, s0))

for t in [0, 100, 200, 300, 419]:
    s_target = s0 - V1 * t
    thh = inverse_arc_length(s_target, B)
    ta = solve_chain_thetas(thh, L_list, B)
    dth = -V1 / spiral_tangent_norm(thh, B)  # 盘入：theta 减小
    sp = chain_velocities(ta, dth, B)
    print("t={:4d}s  head_r={:6.3f}(th={:6.2f})  tail_r={:6.3f}(th={:6.2f})  "
          "head_v={:.4f}  tail_v={:.4f}  max_v={:.4f}@h{}".format(
        t, spiral_r(thh, B), thh, spiral_r(ta[-1], B), ta[-1],
        sp[0], sp[-1], sp.max(), int(np.argmax(sp))))

# 全时间扫描盘入最大速度
vmax_in = 0.0; vmax_t = 0; vmax_h = 0
for t in range(0, 600, 1):
    s_target = s0 - V1 * t
    if s_target < 0:
        break
    thh = inverse_arc_length(s_target, B)
    ta = solve_chain_thetas(thh, L_list, B)
    dth = -V1 / spiral_tangent_norm(thh, B)
    sp = chain_velocities(ta, dth, B)
    i = int(np.argmax(sp))
    if sp[i] > vmax_in:
        vmax_in = float(sp[i]); vmax_t = t; vmax_h = i
print("盘入全扫描: vmax={:.6f} @ t={}s handle={}".format(vmax_in, vmax_t, vmax_h))