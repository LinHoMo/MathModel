"""诊断碰撞判据随时间的变化。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import spiral_arc_length, inverse_arc_length, spiral_point, spiral_r
from chain import solve_chain_thetas
from collision import check_collision

B = 0.55
V1 = 1.0
THETA_0 = 32 * np.pi
N_BENCH = 222
L_HEAD = 3.41
L_BODY = 2.20
W = 0.30

L_list = [L_HEAD] + [L_BODY] * (N_BENCH - 1)

s0 = spiral_arc_length(THETA_0, B)
print("s0 (theta_0=32pi) = {:.2f} m".format(s0))
print("theta_0 = {:.4f} rad = {:.1f} * pi".format(THETA_0, THETA_0 / np.pi))
print("r_0 = {:.2f} m".format(spiral_r(THETA_0, B)))
print("Total time to reach center: {:.1f} s".format(s0 / V1))
print()

# 扫描关键时间点，查看碰撞判据
for t in [0, 50, 100, 150, 200, 250, 300, 350, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500]:
    s_target = s0 - V1 * t
    if s_target <= 0:
        print("t={}: 龙头到达中心".format(t))
        break
    theta_head = inverse_arc_length(s_target, B)
    r_head = spiral_r(theta_head, B)
    
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    # 检查相邻板凳最小间隙
    positions = [spiral_point(th, B) for th in theta_array]
    min_gap = float('inf')
    min_gap_idx = -1
    for i in range(N_BENCH - 1):
        u_i = (positions[i][0] - positions[i+1][0], positions[i][1] - positions[i+1][1])
        u_next = (positions[i+2][0] - positions[i+1][0], positions[i+2][1] - positions[i+1][1])
        norm_i = np.hypot(u_i[0], u_i[1])
        norm_next = np.hypot(u_next[0], u_next[1])
        if norm_i < 1e-15 or norm_next < 1e-15:
            continue
        cos_a = -(u_i[0]*u_next[0] + u_i[1]*u_next[1]) / (norm_i * norm_next)
        cos_a = max(-1, min(1, cos_a))
        sin_a = np.sqrt(1 - cos_a**2)
        L_min = min(L_list[i], L_list[i+1])
        gap = L_min * sin_a
        if gap < min_gap:
            min_gap = gap
            min_gap_idx = i
    
    is_col, info = check_collision(theta_array, L_list, B, W)
    print("t={:4d}s  r_head={:6.3f}m  min_gap={:6.4f}m (idx={})  collision={}".format(
        t, r_head, min_gap, min_gap_idx, is_col))
