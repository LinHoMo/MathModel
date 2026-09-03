"""诊断 Q4 v5：反转 phi_array 后用盘入链递推。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_point,
                    spiral_r, spiral_tangent, spiral_tangent_norm)
from chain import solve_chain_thetas, chain_velocities

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

# 关键洞察：盘出螺线 P_out(phi) = -P_in(phi)
# 盘出阶段龙头在 phi_head（大），向外运动 phi 增大
# 把手链在盘出螺线上：phi_1 > phi_head, phi_2 > phi_1, ...（递增，向外排列）
# 但这意味着把手在龙头外侧——不对！
# 
# 重新理解：盘出时龙头向外运动，把手在龙头**后方**（内侧），
# 即 phi_i < phi_head（递减）
# 
# 但 P_out(phi) = -P_in(phi)，距离 |P_out(phi_i) - P_out(phi_{i-1})| = |P_in(phi_i) - P_in(phi_{i-1})|
# 完全等价于盘入链的距离方程
#
# 关键：盘入链中 solve_chain_thetas 让 theta 递增（把手在外侧，大 theta）
# 盘出链中 phi 递减（把手在内侧，小 phi）
# 
# 速度递推：chain_velocities 从 theta_array[0] 向 [n] 递推
# 盘入: theta[0]=head(小) → theta[n]=tail(大)，head 在内，tail 在外
# 盘出: phi[0]=head(大) → phi[n]=tail(小)，head 在外，tail 在内
# 
# 递推公式 dtheta[i] = (u_i·T_{i-1})/(u_i·T_i) * dtheta[i-1]
# u_i = P(theta_i) - P(theta_{i-1})
# 
# 盘入: u_i 指向外（大theta方向），T 指向外 → ratio > 0
# 盘出: u_i 指向内（小phi方向），T 指向外（大phi方向）→ u·T < 0
# 但 num 和 den 都变号，ratio 不变
# 
# 所以速度递推应该完全一样！
# 但问题是：盘出链在 phi 递减到接近 0 时会卡死

# 解决方案：盘出阶段不是全部把手都在盘出螺线上
# 当 phi 递减到某个值时，把手跨到盘入螺线
# 但更简单的理解：盘出螺线和盘入螺线关于原点对称
# 盘出链 = 盘入链的镜像（位置取负号）
# 所以盘出链的 phi 递推应该和盘入的 theta 递推完全同构
# 盘入: theta_i = theta_head + delta_i (递增, 向外)
# 盘出: phi_i = phi_head + delta_i (递增, 向外) -- 但这会让把手在龙头外侧！
#
# 等等！盘入时龙头向内运动（theta 减小），把手在龙头后方（外侧，theta 更大）
# 盘出时龙头向外运动（phi 增大），把手在龙头后方（内侧，phi 更小）
# 
# 所以上面的分析是对的：盘出 phi 递减
# 但 phi 递减到 0 会卡死
# 
# 新思路：盘出链 phi 递减时，当 phi 接近 0 时，
# 把手实际上绕过了原点，出现在螺线的另一侧
# 即 phi 从正变负（穿过原点）
# P_out(phi) = -a*phi*cos(phi), -a*phi*sin(phi)
# 当 phi < 0 时，P_out(phi) = -a*phi*cos(phi), -a*phi*sin(phi) = a*|phi|*cos(phi), a*|phi|*sin(phi)
# 但 phi < 0 时 cos(phi)=cos(-phi), sin(phi)=-sin(-phi)
# 所以 P_out(phi<0) = a*|phi|*cos(-phi), -a*|phi|*sin(-phi) = a*|phi|*cos|phi|, a*|phi|*sin|phi|
# 等等不对，让我直接计算
# P_in(theta) = a*theta*cos(theta), a*theta*sin(theta)
# P_out(phi) = -P_in(phi) = -a*phi*cos(phi), -a*phi*sin(phi)
# 当 phi < 0: P_out(phi) = -a*(-|phi|)*cos(-|phi|), -a*(-|phi|)*sin(-|phi|)
#           = a*|phi|*cos(|phi|), -a*|phi|*sin(|phi|)
# 这和 P_in(|phi|) = a*|phi|*cos(|phi|), a*|phi|*sin(|phi|) 差一个 y 符号
# 不太对...
# 
# 其实更简单的理解：
# 盘出螺线 r = -a*theta（theta < 0 侧）
# 设 phi = -theta > 0，则 r = a*phi
# P_out = (r*cos(theta), r*sin(theta)) = (a*phi*cos(-phi), a*phi*sin(-phi))
#       = (a*phi*cos(phi), -a*phi*sin(phi))
# 这和 P_in(phi) = (a*phi*cos(phi), a*phi*sin(phi)) 差一个 y 符号
# 即 P_out(phi) = (P_in_x(phi), -P_in_y(phi)) = 镜像反射
#
# 所以 |P_out(phi1) - P_out(phi2)| ≠ |P_in(phi1) - P_in(phi2)|（除非在 x 轴上）
# 之前的假设错了！

# 正确的盘出螺线参数化：
# P_out(phi) = (a*phi*cos(phi), -a*phi*sin(phi)), phi > 0
# 距离: |P_out(phi1) - P_out(phi2)|^2 = (a*phi1*cos(phi1) - a*phi2*cos(phi2))^2
#                                       + (-a*phi1*sin(phi1) + a*phi2*sin(phi2))^2
# = a^2 * [(phi1*cos(phi1) - phi2*cos(phi2))^2 + (phi1*sin(phi1) - phi2*sin(phi2))^2]
# = a^2 * [phi1^2 + phi2^2 - 2*phi1*phi2*(cos(phi1)*cos(phi2) + sin(phi1)*sin(phi2))]
# = a^2 * [phi1^2 + phi2^2 - 2*phi1*phi2*cos(phi1-phi2)]
# 
# 盘入: |P_in(theta1) - P_in(theta2)|^2 = a^2 * [theta1^2 + theta2^2 - 2*theta1*theta2*cos(theta1-theta2)]
# 完全一样！所以距离方程确实等价

# 但切向不同：
# T_out(phi) = dP_out/dphi = a*(cos(phi) - phi*sin(phi), -(sin(phi) + phi*cos(phi)))
# T_in(theta) = a*(cos(theta) - theta*sin(theta), sin(theta) + theta*cos(theta))
# T_out ≠ -T_in !!
# T_out = (T_in_x, -T_in_y)

# 所以速度递推公式不同！
# u_i = P_out(phi_i) - P_out(phi_{i-1}) = (u_in_x, -u_in_y) 如果 phi_i, phi_{i-1} 用 in 的公式
# 但 u_i 的方向取决于 phi_i vs phi_{i-1} 的大小关系

# 让我直接用正确的 P_out 和 T_out 重新实现速度递推

def spiral_point_out(phi, b=0.55):
    """盘出螺线点 P_out(phi) = (a*phi*cos(phi), -a*phi*sin(phi))"""
    a = b / (2.0 * np.pi)
    return (a * phi * np.cos(phi), -a * phi * np.sin(phi))

def spiral_tangent_out(phi, b=0.55):
    """盘出螺线切向 T_out(phi) = dP_out/dphi"""
    a = b / (2.0 * np.pi)
    tx = a * (np.cos(phi) - phi * np.sin(phi))
    ty = a * (-(np.sin(phi) + phi * np.cos(phi)))
    return (tx, ty)

def solve_chain_out_v2(phi_head, L_list, b=0.55, delta=0.5, tol=1e-10):
    """盘出链式约束递推（正确的 P_out 参数化，phi 递减）。"""
    n = len(L_list)
    phi_arr = np.zeros(n + 1)
    phi_arr[0] = phi_head
    for i in range(1, n + 1):
        phi_prev = phi_arr[i - 1]
        L_i = L_list[i - 1]
        hi = phi_prev - 1e-12
        lo = max(1e-8, phi_prev - delta)
        for _ in range(100):
            p_hi = spiral_point_out(hi, b)
            p_lo = spiral_point_out(lo, b)
            if np.hypot(p_hi[0]-p_lo[0], p_hi[1]-p_lo[1]) >= L_i:
                break
            lo -= delta
            if lo < 1e-8:
                lo = 1e-8
                break
        for _ in range(200):
            mid = (lo + hi) / 2.0
            p_mid = spiral_point_out(mid, b)
            p_prev = spiral_point_out(phi_prev, b)
            dist = np.hypot(p_mid[0]-p_prev[0], p_mid[1]-p_prev[1])
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                hi = mid
            else:
                lo = mid
        phi_arr[i] = (lo + hi) / 2.0
    return phi_arr

def chain_velocities_out(phi_arr, dphi_head, b=0.55):
    """盘出速度递推（正确的 T_out）。"""
    n = len(phi_arr) - 1
    dphi = np.zeros(n + 1)
    dphi[0] = dphi_head
    for i in range(1, n + 1):
        p_i = spiral_point_out(phi_arr[i], b)
        p_prev = spiral_point_out(phi_arr[i-1], b)
        ux = p_i[0] - p_prev[0]
        uy = p_i[1] - p_prev[1]
        tx_prev, ty_prev = spiral_tangent_out(phi_arr[i-1], b)
        tx_i, ty_i = spiral_tangent_out(phi_arr[i], b)
        num = ux * tx_prev + uy * ty_prev
        den = ux * tx_i + uy * ty_i
        if abs(den) < 1e-12:
            den = 1e-12
        dphi[i] = (num / den) * dphi[i-1]
    speed = np.zeros(n + 1)
    for i in range(n + 1):
        tx, ty = spiral_tangent_out(phi_arr[i], b)
        norm = np.hypot(tx, ty)
        speed[i] = abs(dphi[i]) * norm
    return speed

# 测试 t_out=407
t_out = 407
s_target = s0_out + V1 * t_out
phi_head = inverse_arc_length(s_target, B)
phi_arr = solve_chain_out_v2(phi_head, L_list, B)

# 检查 handle 185-195
print("handle | phi      | r(m)    | dphi    | x(m)     | y(m)")
for i in range(185, min(200, len(phi_arr))):
    p = spiral_point_out(phi_arr[i], B)
    r = a * phi_arr[i]
    dphi = phi_arr[i] - phi_arr[i-1] if i > 0 else 0
    print("{:6d} | {:8.4f} | {:7.4f} | {:8.4f} | {:8.4f} | {:8.4f}".format(
        i, phi_arr[i], r, dphi, p[0], p[1]))

# 速度
dphi_head = V1 / spiral_tangent_norm(phi_head, B)  # 龙头速度 = 1 m/s
speeds = chain_velocities_out(phi_arr, dphi_head, B)
idx_max = np.argmax(speeds)
print("\nv_max = {:.6f} @ handle {}".format(speeds[idx_max], idx_max))
print("speed[0] = {:.6f}".format(speeds[0]))
print("speed[189] = {:.6f}".format(speeds[189] if len(speeds) > 189 else -1))

# 全局扫描
print("\n--- 全局扫描 ---")
v_g = 0.0; t_g = 0; h_g = 0
for t_out in range(0, 600 + 1, 1):
    s_target = s0_out + V1 * t_out
    try:
        phi_head = inverse_arc_length(s_target, B)
    except ValueError:
        continue
    phi_arr = solve_chain_out_v2(phi_head, L_list, B)
    dphi_head = V1 / spiral_tangent_norm(phi_head, B)
    speeds = chain_velocities_out(phi_arr, dphi_head, B)
    idx = np.argmax(speeds)
    if speeds[idx] > v_g:
        v_g = float(speeds[idx]); t_g = t_out; h_g = int(idx)
print("v_max={:.6f} @ t={}s handle={}".format(v_g, t_g, h_g))
print("冻结值: v_max=2.414211 @ t=407s handle=189")
