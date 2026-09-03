"""诊断：检查非相邻板凳的最小距离。"""
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
    """两线段最短距离（暴力采样近似）。"""
    min_d = float('inf')
    for s in np.linspace(0, 1, 20):
        x1 = p1[0] + s*(p2[0]-p1[0])
        y1 = p1[1] + s*(p2[1]-p1[1])
        for t in np.linspace(0, 1, 20):
            x2 = p3[0] + t*(p4[0]-p3[0])
            y2 = p3[1] + t*(p4[1]-p3[1])
            d = np.hypot(x1-x2, y1-y2)
            if d < min_d:
                min_d = d
    return min_d

for t in [0, 100, 200, 300, 350, 400, 410, 420, 430, 440]:
    s_target = s0 - V1 * t
    if s_target <= 0:
        break
    theta_head = inverse_arc_length(s_target, B)
    r_head = spiral_r(theta_head, B)
    
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = [spiral_point(th, B) for th in theta_array]
    
    # 检查所有非相邻板凳对的最小距离（跨圈检测）
    min_nonadj = float('inf')
    min_pair = None
    for i in range(N_BENCH):
        for j in range(i+2, N_BENCH):
            # 快速距离估计：两端点距离
            d_est = min(
                np.hypot(positions[i][0]-positions[j][0], positions[i][1]-positions[j][1]),
                np.hypot(positions[i+1][0]-positions[j+1][0], positions[i+1][1]-positions[j+1][1]),
            )
            if d_est > 2.0:  # 超过2米跳过
                continue
            d = seg_dist(positions[i], positions[i+1], positions[j], positions[j+1])
            if d < min_nonadj:
                min_nonadj = d
                min_pair = (i, j)
    
    print("t={:4d}s  r_head={:6.3f}m  min_nonadj_dist={:.4f}m pair={}  collision={}".format(
        t, r_head, min_nonadj, min_pair, min_nonadj < W))
