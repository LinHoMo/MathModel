"""诊断 Q4：用 phi=-theta>0 盘出参数化，复用盘入链递推。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_point,
                    spiral_r, spiral_tangent, spiral_tangent_norm)
from chain import solve_chain_thetas, chain_velocities

B = 0.55; V1 = 1.0; THETA_0 = 32 * np.pi
N_BENCH = 222; L_HEAD = 3.41; L_BODY = 2.20; W = 0.30
L_list = [L_HEAD] + [L_BODY] * (N_BENCH - 1)

# 盘出起点：龙头从掉头出口开始，r_start = r_collision
# 用 phi 参数化：phi > 0, 盘出螺线 P_out(phi) = -P_in(phi) = (-r*cos(phi), -r*sin(phi))
# 其中 r = a*phi, phi > 0
# 盘出与盘入同构：链式约束完全复用 solve_chain_thetas(phi_head, L_list, b)
# 速度也复用 chain_velocities，但 dtheta_head = +v1 / (a*sqrt(1+phi^2))（向外，phi 递增）

t_star = 412.83
s0 = spiral_arc_length(THETA_0, B)
theta_head_at_tstar = inverse_arc_length(s0 - V1 * t_star, B)
r_collision = spiral_r(theta_head_at_tstar, B)
print("r_collision =", r_collision)

a = B / (2.0 * np.pi)
phi_start = r_collision / a  # 盘出起点 phi
s0_out = spiral_arc_length(phi_start, B)
print("phi_start =", phi_start, " s0_out =", s0_out)

# 扫描盘出过程
v_max_global = 0.0
t_at_vmax = 0.0
handle_at_vmax = 0
pos_at_vmax = (0.0, 0.0)

for t_out in range(0, 600 + 1, 1):
    s_target = s0_out + V1 * t_out
    try:
        phi_head = inverse_arc_length(s_target, B)
    except ValueError:
        continue

    # 链式约束（复用盘入递推，phi 递增）
    phi_array = solve_chain_thetas(phi_head, L_list, B)

    # 速度（phi 递增 => dphi_head = +v1 / norm）
    dphi_head = V1 / spiral_tangent_norm(phi_head, B)
    speeds = chain_velocities(phi_array, dphi_head, B)

    idx_max = np.argmax(speeds)
    if speeds[idx_max] > v_max_global:
        v_max_global = float(speeds[idx_max])
        t_at_vmax = float(t_out)
        handle_at_vmax = int(idx_max)
        # 盘出位置 = 中心对称（取负号）
        pos = spiral_point(phi_array[idx_max], B)
        pos_at_vmax = (-float(pos[0]), -float(pos[1]))

print("\n=== 结果 ===")
print("v_max = {:.6f} m/s".format(v_max_global))
print("t_at_vmax = {} s".format(t_at_vmax))
print("handle_at_vmax = {}".format(handle_at_vmax))
print("pos_at_vmax = ({:.6f}, {:.6f})".format(pos_at_vmax[0], pos_at_vmax[1]))
print("\n冻结值: v_max=2.414211, t=407, handle=189")
