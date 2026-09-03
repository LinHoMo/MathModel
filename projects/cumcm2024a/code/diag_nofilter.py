"""精确诊断：非相邻板凳最小距离（无过滤）。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import spiral_arc_length, inverse_arc_length, spiral_point, spiral_r
from chain import solve_chain_thetas

B = 0.55; V1 = 1.0; THETA_0 = 32 * np.pi
N_BENCH = 222; L_HEAD = 3.41; L_BODY = 2.20; W = 0.30
L_list = [L_HEAD] + [L_BODY] * (N_BENCH - 1)
s0 = spiral_arc_length(THETA_0, B)

def seg_dist(p1, p2, p3, p4):
    d = (p2[0]-p1[0], p2[1]-p1[1])
    e = (p4[0]-p3[0], p4[1]-p3[1])
    dd = d[0]*d[0]+d[1]*d[1]; ee = e[0]*e[0]+e[1]*e[1]; de = d[0]*e[0]+d[1]*e[1]
    denom = dd*ee - de*de
    if abs(denom) < 1e-18:
        return min(np.hypot(p1[0]-p3[0], p1[1]-p3[1]), np.hypot(p2[0]-p4[0], p2[1]-p4[1]))
    dp = (p3[0]-p1[0], p3[1]-p1[1])
    t_par = (de*(dp[0]*e[0]+dp[1]*e[1]) - ee*(dp[0]*d[0]+dp[1]*d[1])) / denom
    s_par = (dd*(dp[0]*e[0]+dp[1]*e[1]) - de*(dp[0]*d[0]+dp[1]*d[1])) / denom
    t_par = max(0, min(1, t_par)); s_par = max(0, min(1, s_par))
    return np.hypot(p1[0]+t_par*d[0]-p3[0]-s_par*e[0], p1[1]+t_par*d[1]-p3[1]-s_par*e[1])

# 只检查几个关键时间点，全部非相邻对
for t in [0, 200, 400, 420]:
    s_target = s0 - V1 * t
    if s_target <= 0: break
    theta_head = inverse_arc_length(s_target, B)
    r_head = spiral_r(theta_head, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = [spiral_point(th, B) for th in theta_array]
    
    min_d = float('inf')
    min_p = None
    # 全扫描，无过滤
    for i in range(N_BENCH):
        for j in range(i+2, N_BENCH):
            d = seg_dist(positions[i], positions[i+1], positions[j], positions[j+1])
            if d < min_d:
                min_d = d
                min_p = (i, j)
    
    print("t={:4d}s  r_head={:6.3f}m  min_dist={:.4f}m pair={}  col={}".format(
        t, r_head, min_d, min_p, min_d < W))
