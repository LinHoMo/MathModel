"""诊断 Q4 v8：盘出链 = 反转的盘入链。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_point,
                    spiral_r, spiral_tangent, spiral_tangent_norm)
from chain import solve_chain_thetas, chain_velocities

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

# 盘出链 = 反转的盘入链
# 盘入链: solve_chain_thetas(theta_head, L_list) -> theta[0]=head(小), theta[n]=tail(大)
# 反转: phi[0]=theta[n](大,龙头), phi[n]=theta[0](小,龙尾)
# 但反转后 phi[0] = theta[n] 不一定等于 phi_head...
#
# 更准确的理解：
# 盘入链 theta 递增: head 在内侧(小theta), tail 在外侧(大theta)
# 盘出链 phi 递减: head 在外侧(大phi), tail 在内侧(小phi)
# 如果直接用 solve_chain_thetas(phi_head, L_list)，得到 phi[0]=phi_head, phi[i]>phi_head
# 这是把手在龙头外侧——物理上不对
#
# 正确方法：盘出链中 phi_head 是最大的 phi（龙头最外），
# 把手 1 的 phi < phi_head。等价于盘入链中 theta_tail 是最大的 theta，
# 把手 i 的 theta < theta_tail。
# 
# 所以：用 solve_chain_thetas 求解时，从龙尾端（最内侧, 最小 phi）开始递推
# 龙尾 phi_tail 是未知的，但龙尾在螺线上，phi_tail > 0
# 
# 或者：直接用 solve_chain_thetas(phi_head, L_list) 但反转头尾
# solve_chain_thetas 让 theta 递增，theta[0]=phi_head, theta[i]>phi_head
# 这在盘入中是正确的（把手在外侧大 theta）
# 但盘出中把手在龙头内侧（小 phi），方向相反
# 
# 换一种思路：盘出螺线 P_out(phi) = -P_in(phi)
# 距离 |P_out(phi1)-P_out(phi2)| = |P_in(phi1)-P_in(phi2)|
# 所以链约束方程完全一样
# 盘入: theta[0]=head, theta[i] > theta[0]（递增, 向外）
# 盘出: phi[0]=head, phi[i] < phi[0]（递减, 向内）
# 
# 两者都是"相邻 phi/theta 差约 dphi ≈ L/|T| > 0"
# 盘入递增，盘出递减
# solve_chain_thetas 递增——不能直接用
# 
# 但如果反转 L_list 的顺序呢？
# 盘出链: phi[0]=head(大), phi[1]<phi[0], ..., phi[n]<phi[n-1]
# 等价于: psi[i] = phi[n-i], psi[0]=phi[n](小), psi[i]>psi[0](递增)
# psi 是一个"盘入链"，head=psi[0]=phi[n]（龙尾）
# L_list 反转: L'[i] = L_list[n-i]
# solve_chain_thetas(psi[0], L'_list) -> psi[0]<psi[1]<...<psi[n]
# 然后 phi[i] = psi[n-i]
# 
# 但 psi[0]=phi[n] 是未知的！
# 
# 另一种方法：直接用盘入链递推但从 phi_head 出发递减
# 等价于：设 psi = -phi，则 P_out(phi) = -P_in(phi) = P_in(-phi) 不对
# 
# 最终方案：直接实现 phi 递减的链递推
# 但用弧长制导初值 + 穿过 0 时的连续性约束

# 方案：用 "前一步 phi + dphi_est" 作为二分初值
# dphi_est 从前一步的 dphi 外推

def solve_chain_out_robust(phi_head, L_list, b=0.55, tol=1e-10):
    """稳健盘出链递推：弧长制导 + 前步外推。"""
    n = len(L_list)
    phi_arr = np.zeros(n + 1)
    phi_arr[0] = phi_head
    
    for i in range(1, n + 1):
        phi_prev = phi_arr[i - 1]
        L_i = L_list[i - 1]
        
        # 估计 dphi
        norm_prev = spiral_tangent_norm(abs(phi_prev), b)
        dphi_est = L_i / norm_prev
        
        # 前步外推
        if i >= 2:
            dphi_prev = phi_arr[i-1] - phi_arr[i-2]
            dphi_est = 0.5 * dphi_est + 0.5 * dphi_prev
        
        phi_est = phi_prev - dphi_est
        
        # 搜索区间 [phi_est - 1.0, phi_est + 0.5]
        lo = phi_est - 1.0
        hi = min(phi_est + 0.5, phi_prev - 1e-12)
        
        # 确保区间内有解
        p_prev = spiral_point(abs(phi_prev), b)  # P_in(|phi|)
        # P_out(phi) = -P_in(phi), |P_out(phi1)-P_out(phi2)| = |P_in(phi1)-P_in(phi2)|
        # 所以直接用 P_in 计算距离
        def dist(phi_a, phi_b):
            pa = spiral_point(abs(phi_a), b)
            pb = spiral_point(abs(phi_b), b)
            return np.hypot(pa[0]-pb[0], pa[1]-pb[1])
        
        d_lo = dist(lo, phi_prev)
        d_hi = dist(hi, phi_prev)
        
        # 扩大区间
        expand = 0
        while d_lo < L_i and d_hi < L_i and expand < 100:
            lo -= 1.0
            d_lo = dist(lo, phi_prev)
            expand += 1
        while d_lo > L_i and d_hi > L_i and expand < 100:
            hi = min(hi + 0.5, phi_prev - 1e-12)
            d_hi = dist(hi, phi_prev)
            expand += 1
        
        # 二分
        for _ in range(200):
            mid = (lo + hi) / 2.0
            d_mid = dist(mid, phi_prev)
            if abs(d_mid - L_i) < tol:
                break
            # 距离随 phi 减小而增大（在远离 phi_prev 方向）
            if d_mid < L_i:
                hi = mid  # 需要更小 phi
            else:
                lo = mid  # 需要更大 phi
        phi_arr[i] = (lo + hi) / 2.0
    
    return phi_arr

# 测试
t_out = 407
s_target = s0_out + V1 * t_out
phi_head = inverse_arc_length(s_target, B)
phi_arr = solve_chain_out_robust(phi_head, L_list, B)

# 检查
print("handle | phi      | r(m)    | dphi    ")
for i in range(185, min(200, len(phi_arr))):
    r = a * abs(phi_arr[i])
    dphi = phi_arr[i] - phi_arr[i-1] if i > 0 else 0
    print("{:6d} | {:8.4f} | {:7.4f} | {:8.4f}".format(i, phi_arr[i], r, dphi))

# 速度（用盘入链的 chain_velocities，因为距离/切向等价）
dphi_head = V1 / spiral_tangent_norm(phi_head, B)
speeds = chain_velocities(phi_arr, dphi_head, B)
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
    phi_arr = solve_chain_out_robust(phi_head, L_list, B)
    dphi_head = V1 / spiral_tangent_norm(phi_head, B)
    speeds = chain_velocities(phi_arr, dphi_head, B)
    idx = np.argmax(speeds)
    if speeds[idx] > v_g:
        v_g = float(speeds[idx]); t_g = t_out; h_g = int(idx)
print("v_max={:.6f} @ t={}s handle={}".format(v_g, t_g, h_g))
print("冻结值: v_max=2.414211 @ t=407s handle=189")
