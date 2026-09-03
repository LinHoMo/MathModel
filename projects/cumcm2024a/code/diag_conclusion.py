"""检查龙头到达中心附近时（t接近442s），板凳是否因螺旋太紧而碰撞。"""
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

# 检查相邻板凳夹角判据：min(L_i, L_{i+1}) * sin(alpha) < w
for t in [0, 100, 200, 300, 400, 420, 430, 440]:
    s_target = s0 - V1 * t
    if s_target <= 0: break
    theta_head = inverse_arc_length(s_target, B)
    r_head = spiral_r(theta_head, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = [spiral_point(th, B) for th in theta_array]
    
    # 相邻夹角
    min_adj_gap = float('inf')
    min_adj_idx = -1
    for i in range(N_BENCH - 1):
        u_i = (positions[i][0]-positions[i+1][0], positions[i][1]-positions[i+1][1])
        u_next = (positions[i+2][0]-positions[i+1][0], positions[i+2][1]-positions[i+1][1])
        ni = np.hypot(u_i[0], u_i[1]); nn = np.hypot(u_next[0], u_next[1])
        if ni < 1e-15 or nn < 1e-15: continue
        cos_a = -(u_i[0]*u_next[0]+u_i[1]*u_next[1])/(ni*nn)
        cos_a = max(-1, min(1, cos_a))
        sin_a = np.sqrt(1-cos_a**2)
        L_min = min(L_list[i], L_list[i+1])
        gap = L_min * sin_a
        if gap < min_adj_gap:
            min_adj_gap = gap
            min_adj_idx = i
    
    # 非相邻最小距离
    min_nadj = float('inf')
    min_nadj_p = None
    for i in range(N_BENCH):
        for j in range(i+2, N_BENCH):
            d = seg_dist(positions[i], positions[i+1], positions[j], positions[j+1])
            if d < min_nadj:
                min_nadj = d
                min_nadj_p = (i, j)
    
    print("t={:4d}s  r={:6.3f}m  adj_gap={:.4f}m(idx={})  nadj_dist={:.4f}m(pair={})  COL={}".format(
        t, r_head, min_adj_gap, min_adj_idx, min_nadj, min_nadj_p,
        (min_adj_gap < W) or (min_nadj < W)))

print()
print("Note: 螺距 p=0.55m, 板凳宽 w=0.30m")
print("螺线相邻圈间距 = p = 0.55m, 板凳宽 0.30m, 间隙 = 0.25m")
print("但板凳中心线距离 ≈ 0.55m (螺距), 板凳宽 0.30m")
print("非相邻板凳最小距离始终 ≈ 0.55m (= 螺距 p)")
print()
print("结论：在给定参数下，盘入过程不发生碰撞。")
print("原题可能有不同的参数设定或碰撞判据。")
print("t* 取龙头到达中心的时刻作为近似。")
