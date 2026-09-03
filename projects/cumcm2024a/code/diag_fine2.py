"""更密集的碰撞搜索，包括非相邻板凳距离 < 0.35 的时刻。"""
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

def seg_dist(p1, p2, p3, p4):
    d = (p2[0]-p1[0], p2[1]-p1[1])
    e = (p4[0]-p3[0], p4[1]-p3[1])
    dd = d[0]*d[0]+d[1]*d[1]
    ee = e[0]*e[0]+e[1]*e[1]
    de = d[0]*e[0]+d[1]*e[1]
    denom = dd*ee - de*de
    if abs(denom) < 1e-18:
        return min(np.hypot(p1[0]-p3[0], p1[1]-p3[1]),
                   np.hypot(p2[0]-p4[0], p2[1]-p4[1]))
    dp = (p3[0]-p1[0], p3[1]-p1[1])
    t = (de*(dp[0]*e[0]+dp[1]*e[1]) - ee*(dp[0]*d[0]+dp[1]*d[1])) / denom
    s = (dd*(dp[0]*e[0]+dp[1]*e[1]) - de*(dp[0]*d[0]+dp[1]*d[1])) / denom
    t = max(0, min(1, t)); s = max(0, min(1, s))
    return np.hypot(p1[0]+t*d[0]-p3[0]-s*e[0], p1[1]+t*d[1]-p3[1]-s*e[1])

# 密集扫描 400-442s
for t in np.arange(400, 443, 1.0):
    s_target = s0 - V1 * t
    if s_target <= 0:
        print("t={:.0f}: 龙头到达中心".format(t))
        break
    theta_head = inverse_arc_length(s_target, B)
    r_head = spiral_r(theta_head, B)
    
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = [spiral_point(th, B) for th in theta_array]
    
    # 所有非相邻板凳对
    min_nonadj = float('inf')
    min_pair = None
    for i in range(N_BENCH):
        for j in range(i+2, N_BENCH):
            # 端点距离快速过滤
            d_est = np.hypot(positions[i][0]-positions[j][0], positions[i][1]-positions[j][1])
            if d_est > 1.0:
                continue
            d = seg_dist(positions[i], positions[i+1], positions[j], positions[j+1])
            if d < min_nonadj:
                min_nonadj = d
                min_pair = (i, j)
    
    col = " *** COLLISION ***" if min_nonadj < W else ""
    print("t={:6.1f}s  r_head={:6.3f}m  min_dist={:.4f}m pair={}{}".format(
        t, r_head, min_nonadj, min_pair, col))
