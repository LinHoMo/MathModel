"""精确诊断：用完整非相邻板凳距离检查整个时间范围内的最小距离。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import spiral_arc_length, inverse_arc_length, spiral_point, spiral_r
from chain import solve_chain_thetas

B = 0.55
V1 = 1.0
THETA_0 = 32 * np.pi
N_BENCH = 222
L_HEAD = 3.41
L_BODY = 2.20
W = 0.30

L_list = [L_HEAD] + [L_BODY] * (N_BENCH - 1)
s0 = spiral_arc_length(THETA_0, B)

# 在整个时间范围内找最小非相邻距离
global_min_dist = float('inf')
global_min_t = 0
global_min_pair = None

for t in range(0, 443, 10):
    s_target = s0 - V1 * t
    if s_target <= 0:
        break
    theta_head = inverse_arc_length(s_target, B)
    r_head = spiral_r(theta_head, B)
    
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = np.array([spiral_point(th, B) for th in theta_array])
    
    # 使用 KD-tree 加速
    # 板凳中心距离矩阵（手动计算）
    centers = (positions[:-1] + positions[1:]) / 2.0
    # 非相邻板凳距离直接用端点距离估计
    for i in range(N_BENCH):
        for j in range(i+2, N_BENCH):
            d_est = np.hypot(centers[i,0]-centers[j,0], centers[i,1]-centers[j,1])
            if d_est > 1.0:
                continue
                # 精确距离
                p1 = positions[i]; p2 = positions[i+1]
                p3 = positions[j]; p4 = positions[j+1]
                # 线段距离
                d = (p2[0]-p1[0], p2[1]-p1[1])
                e = (p4[0]-p3[0], p4[1]-p3[1])
                dd = d[0]*d[0]+d[1]*d[1]
                ee = e[0]*e[0]+e[1]*e[1]
                de = d[0]*e[0]+d[1]*e[1]
                denom = dd*ee - de*de
                if abs(denom) < 1e-18:
                    exact_d = min(np.hypot(p1[0]-p3[0], p1[1]-p3[1]),
                                  np.hypot(p2[0]-p4[0], p2[1]-p4[1]))
                else:
                    dp = (p3[0]-p1[0], p3[1]-p1[1])
                    t_par = (de*(dp[0]*e[0]+dp[1]*e[1]) - ee*(dp[0]*d[0]+dp[1]*d[1])) / denom
                    s_par = (dd*(dp[0]*e[0]+dp[1]*e[1]) - de*(dp[0]*d[0]+dp[1]*d[1])) / denom
                    t_par = max(0, min(1, t_par)); s_par = max(0, min(1, s_par))
                    exact_d = np.hypot(p1[0]+t_par*d[0]-p3[0]-s_par*e[0],
                                       p1[1]+t_par*d[1]-p3[1]-s_par*e[1])
                if exact_d < global_min_dist:
                    global_min_dist = exact_d
                    global_min_t = t
                    global_min_pair = (i, j)
    
    print("t={:4d}s  r_head={:6.3f}m  current_global_min={:.4f}m".format(
        t, r_head, global_min_dist))

print()
print("=" * 60)
print("Global minimum non-adjacent distance: {:.4f} m at t={}s pair={}".format(
    global_min_dist, global_min_t, global_min_pair))
print("Threshold (w): {} m".format(W))
print("Collision occurs: {}".format(global_min_dist < W))
