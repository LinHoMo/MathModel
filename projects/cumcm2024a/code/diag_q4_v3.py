"""诊断 Q4 v3：测试 dphi_head 正负号。"""
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

# 测试两种 dphi_head 符号
norm_head = spiral_tangent_norm(phi_head, B)

for sign, label in [(1.0, "+v1/norm"), (-1.0, "-v1/norm")]:
    dphi_head = sign * V1 / norm_head
    speeds = chain_velocities(phi_arr, dphi_head, B)
    idx_max = np.argmax(speeds)
    print("{}: v_max={:.6f} @ handle={}, speed[0]={:.6f}, speed[189]={:.6f}".format(
        label, speeds[idx_max], idx_max, speeds[0],
        speeds[189] if len(speeds) > 189 else -1))

# 关键：chain_velocities 中 dtheta[0] = dphi_head
# 如果 dphi_head > 0（phi 递增），但 phi_array 递减...
# 递推公式: dtheta[i] = (u_i . T_{i-1}) / (u_i . T_i) * dtheta[i-1]
# 这与方向无关，只取决于几何
# 所以 v_max 不变，只是整体速度乘以 |dphi_head| 的比例

# 尝试：盘出链实际上就是盘入链的镜像
# P_out(phi) = -P_in(phi), 所以 T_out(phi) = -T_in(phi)
# u_i = P_out(phi_i) - P_out(phi_{i-1}) = -(P_in(phi_i) - P_in(phi_{i-1})) = -u_in_i
# 递推: dphi_i = (u_out_i . T_out_{i-1}) / (u_out_i . T_out_i) * dphi_{i-1}
#      = ((-u_in) . (-T_in_{i-1})) / ((-u_in) . (-T_in_i)) * dphi_{i-1}
#      = (u_in . T_in_{i-1}) / (u_in . T_in_i) * dphi_{i-1}
# 完全一样！所以 chain_velocities 直接复用是对的

# 问题可能在 phi_array 的方向
# 盘入: theta_array[0] = theta_head (小), theta_array[i] > theta_head (大, 外侧)
# 盘出: phi_array[0] = phi_head (大, 外侧), phi_array[i] < phi_head (小, 内侧)
# 递推方向反了！盘入中 i 递增 = theta 递增（向外），
# 盘出中 i 递增 = phi 递减（向内）
# 速度递推从 head 向 tail 传递，但几何关系方向反了

# 解决：反转 phi_array 后用 chain_velocities
phi_rev = phi_arr[::-1]  # 现在从小到大，类似盘入
dphi_tail = V1 / spiral_tangent_norm(phi_rev[0], B)  # 最内圈把手的速度

# 但龙头在最外圈（phi 最大），不是最内圈
# 所以需要从龙头端递推

# 另一种思路：盘出链等价于"反向盘入链"
# 反转后 phi_rev[0] = phi_min (最内圈把手), phi_rev[-1] = phi_head (龙头)
# 这就像盘入链的镜像，龙头变成了"龙尾"
# 速度从 phi_rev[0] 递推到 phi_rev[-1]

# 但实际上龙头速度 = 1 m/s 是约束，不是龙尾
# 所以应该从 phi_head 端（大 phi）向内递推

# 让我直接看 chain_velocities 的递推公式是否方向无关
# dtheta[i] = ratio_i * dtheta[i-1]
# 如果 phi_array 递减，那么 i 增加时 phi 减小
# u_i = P(phi_i) - P(phi_{i-1}), 方向从大phi到小phi（向内）
# T_i = dP/dphi(phi_i), 方向是 phi 增加方向（向外）
# u_i . T_{i-1}: u 向内，T 向外，点积可能为负
# 这意味着 dphi_i / dphi_{i-1} 可能为负 -> 速度方向反转

# 检查 ratio 的符号
for i in [1, 2, 100, 189, 190, 200]:
    if i >= len(phi_arr):
        continue
    x_i, y_i = spiral_point(phi_arr[i], B)
    x_prev, y_prev = spiral_point(phi_arr[i-1], B)
    ux = x_i - x_prev
    uy = y_i - y_prev
    tx_prev, ty_prev = spiral_tangent(phi_arr[i-1], B)
    tx_i, ty_i = spiral_tangent(phi_arr[i], B)
    num = ux * tx_prev + uy * ty_prev
    den = ux * tx_i + uy * ty_i
    ratio = num / den if abs(den) > 1e-15 else float('inf')
    print("handle {}: ratio={:.6f} (num={:.4f}, den={:.4f})".format(i, ratio, num, den))
