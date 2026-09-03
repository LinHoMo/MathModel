"""诊断 Q4：混合链——龙头在盘出螺线(phi)，龙尾在盘入螺线(theta)。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_point,
                    spiral_r, spiral_tangent, spiral_tangent_norm)

B = 0.55; V1 = 1.0; THETA_0 = 32 * np.pi
N_BENCH = 222; L_HEAD = 3.41; L_BODY = 2.20; W = 0.30
L_list = [L_HEAD] + [L_BODY] * (N_BENCH - 1)

t_star = 412.83
s0 = spiral_arc_length(THETA_0, B)
theta_head_at_tstar = inverse_arc_length(s0 - V1 * t_star, B)
r_collision = spiral_r(theta_head_at_tstar, B)
a = B / (2.0 * np.pi)

# 掉头过程：龙头从 r_collision 进入掉头圆弧，完成 S 形后进入盘出螺线
# 掉头结束时龙头在盘出螺线上 r = r_collision 处
# 盘出螺线: P_out(phi) = (-a*phi*cos(phi), -a*phi*sin(phi)), phi > 0
# phi_start = r_collision / a

phi_start = r_collision / a
s0_out = spiral_arc_length(phi_start, B)

# 混合链递推：龙头在盘出(phi 递增)，龙尾在盘入(theta 递减)
# 在某个时刻 t_out，龙头 phi_head = inverse(s0_out + v1*t_out)
# 把手 0..k 在盘出螺线(phi 递减: phi_0 > phi_1 > ... > phi_k)
# 把手 k..n 在盘入螺线(theta 递增: theta_k < theta_{k+1} < ... < theta_n)
# 交接点 k 处 |P_out(phi_k) - P_in(theta_k)| = L_k

def spiral_point_in(theta, b=0.55):
    """盘入螺线点 P(theta) = (a*theta*cos(theta), a*theta*sin(theta))"""
    return spiral_point(theta, b)

def spiral_point_out(phi, b=0.55):
    """盘出螺线点 P_out(phi) = -P_in(phi) = (-a*phi*cos(phi), -a*phi*sin(phi))"""
    p = spiral_point(phi, b)
    return (-p[0], -p[1])

def dist_out_out(phi1, phi2, b=0.55):
    p1 = spiral_point_out(phi1, b)
    p2 = spiral_point_out(phi2, b)
    return np.hypot(p1[0]-p2[0], p1[1]-p2[1])

def dist_out_in(phi, theta, b=0.55):
    p1 = spiral_point_out(phi, b)
    p2 = spiral_point_in(theta, b)
    return np.hypot(p1[0]-p2[0], p1[1]-p2[1])

def dist_in_in(theta1, theta2, b=0.55):
    p1 = spiral_point_in(theta1, b)
    p2 = spiral_point_in(theta2, b)
    return np.hypot(p1[0]-p2[0], p1[1]-p2[1])

# 在 t_out=407s 测试
t_out = 407
s_target = s0_out + V1 * t_out
phi_head = inverse_arc_length(s_target, B)
print("t_out={}s: phi_head={:.2f}, r_head={:.3f}m".format(
    t_out, phi_head, spiral_r(phi_head, B)))

# 混合链递推
phi_array = [phi_head]  # 盘出部分
theta_array = []         # 盘入部分
n_out = 0  # 盘出段把手数

for i in range(1, N_BENCH + 1):
    L_i = L_list[i - 1]
    phi_prev = phi_array[-1]

    # 尝试1：在盘出螺线上找 phi < phi_prev（向内递减）
    lo = 1e-8
    hi = phi_prev - 1e-12
    d_at_hiprev = dist_out_out(hi, phi_prev, B)
    
    if d_at_hiprev >= L_i:
        # 盘出螺线上可以找到解
        for _ in range(200):
            mid = (lo + hi) / 2.0
            d = dist_out_out(mid, phi_prev, B)
            if abs(d - L_i) < 1e-10:
                break
            if d < L_i:
                lo = mid  # 需要更小 phi -> 更大距离
            else:
                hi = mid
        phi_array.append((lo + hi) / 2.0)
        n_out = i
    else:
        # 盘出螺线上距离不够，需要跨到盘入螺线
        # 先尝试交接：在盘入螺线上找 theta 使得 dist_out_in(phi_prev, theta) = L_i
        found = False
        for theta_try in np.arange(0.1, 200, 0.5):
            d = dist_out_in(phi_prev, theta_try, B)
            if abs(d - L_i) < 0.01:
                # 精细二分
                lo_t = max(0.01, theta_try - 0.5)
                hi_t = theta_try + 0.5
                for _ in range(200):
                    mid_t = (lo_t + hi_t) / 2.0
                    d_t = dist_out_in(phi_prev, mid_t, B)
                    if abs(d_t - L_i) < 1e-10:
                        break
                    if d_t < L_i:
                        lo_t = mid_t
                    else:
                        hi_t = mid_t
                theta_array.append((lo_t + hi_t) / 2.0)
                n_out = i - 1  # i-1 个把手在盘出段
                found = True
                break
        
        if not found:
            print("  handle {}: 无法找到交接点".format(i))
            break
        
        # 后续把手在盘入螺线上递推（theta 递增）
        for j in range(i + 1, N_BENCH + 1):
            L_j = L_list[j - 1]
            theta_prev = theta_array[-1]
            lo_t = theta_prev + 1e-12
            hi_t = theta_prev + 0.5
            for _ in range(50):
                if dist_in_in(lo_t, hi_t, B) >= L_j:
                    break
                hi_t += 0.5
            for _ in range(200):
                mid_t = (lo_t + hi_t) / 2.0
                d_t = dist_in_in(theta_prev, mid_t, B)
                if abs(d_t - L_j) < 1e-10:
                    break
                if d_t < L_j:
                    lo_t = mid_t
                else:
                    hi_t = mid_t
            theta_array.append((lo_t + hi_t) / 2.0)
        break

print("n_out (盘出段把手数) =", n_out)
print("n_in (盘入段把手数) =", len(theta_array))
print("总把手数 =", n_out + 1 + len(theta_array))

# 计算速度
# 盘出段：dphi_head = +v1 / norm(phi_head)
dphi_head = V1 / spiral_tangent_norm(phi_head, B)

# 盘出段速度递推（phi 递减方向）
def chain_vel_out(phi_arr, dphi_head, b=0.55):
    n = len(phi_arr) - 1
    dphi = np.zeros(n + 1)
    dphi[0] = dphi_head
    for i in range(1, n + 1):
        x_i, y_i = spiral_point_out(phi_arr[i], b)
        x_prev, y_prev = spiral_point_out(phi_arr[i - 1], b)
        ux = x_i - x_prev
        uy = y_i - y_prev
        # 盘出切向 = -盘入切向
        tx_prev, ty_prev = spiral_tangent(phi_arr[i - 1], b)
        tx_i, ty_i = spiral_tangent(phi_arr[i], b)
        # T_out = -T_in
        numerator = ux * (-tx_prev) + uy * (-ty_prev)
        denominator = ux * (-tx_i) + uy * (-ty_i)
        if abs(denominator) < 1e-12:
            denominator = 1e-12
        dphi[i] = (numerator / denominator) * dphi[i - 1]
    speed = np.zeros(n + 1)
    for i in range(n + 1):
        norm = spiral_tangent_norm(phi_arr[i], b)
        speed[i] = abs(dphi[i]) * norm
    return speed

speeds_out = chain_vel_out(phi_array, dphi_head, B)
print("\n盘出段速度: handle 0..{}".format(n_out))
print("  speed[0] = {:.6f}".format(speeds_out[0]))
print("  speed[{}] = {:.6f}".format(n_out, speeds_out[-1]))
print("  max = {:.6f} @ handle {}".format(np.max(speeds_out), np.argmax(speeds_out)))

# 如果有盘入段，也计算
if theta_array:
    # 交接点速度：从盘出段最后一个把手传递
    dtheta交接 = dphi[-1] if len(dphi) > 0 else 0  # 简化
    # 盘入段：theta 递增，dtheta_head = 交接速度
    # 这里简化：只看盘出段
    pass

print("\n冻结值: v_max=2.414211 @ handle 189, t=407s")
print("当前盘出段把手数 =", len(phi_array) - 1, "(含龙头)")
