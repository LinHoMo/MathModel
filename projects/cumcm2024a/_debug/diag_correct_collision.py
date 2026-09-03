"""诊断碰撞判据：用正确公式扫描 0-600s，打印 gap 变化趋势。"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point, spiral_arc_length, inverse_arc_length, spiral_tangent_norm, dtheta_dt_head
from chain import solve_chain_thetas
from solve import _build_L_list, _solve_kinematics, B, W, THETA_0

L_list = _build_L_list()

def correct_gap(theta_array, L_list, b=0.55, w=0.30):
    """正确碰撞判据：L_min * cot(alpha/2) < w，alpha 为代码偏转角。"""
    n = len(L_list)
    positions = [spiral_point(t, b) for t in theta_array]
    min_gap = 1e9
    min_pair = (-1, -1)
    for i in range(n - 1):
        u_i = (positions[i][0] - positions[i+1][0], positions[i][1] - positions[i+1][1])
        u_next = (positions[i+2][0] - positions[i+1][0], positions[i+2][1] - positions[i+1][1])
        norm_i = np.hypot(u_i[0], u_i[1])
        norm_next = np.hypot(u_next[0], u_next[1])
        if norm_i < 1e-15 or norm_next < 1e-15:
            continue
        cos_alpha = -(u_i[0]*u_next[0] + u_i[1]*u_next[1]) / (norm_i * norm_next)
        cos_alpha = max(-1.0, min(1.0, cos_alpha))
        sin_alpha = np.sqrt(max(0, 1.0 - cos_alpha**2))
        L_min = min(L_list[i], L_list[i+1])
        # 正确公式: gap = L_min * (1+cos_alpha) / sin_alpha = L_min * cot(alpha/2)
        if sin_alpha < 1e-12:
            if cos_alpha > 0:  # collinear, no collision
                gap = 1e9
            else:  # folded back, collision
                gap = 0.0
        else:
            gap = L_min * (1.0 + cos_alpha) / sin_alpha
        if gap < min_gap:
            min_gap = gap
            min_pair = (i, i+1)
    return min_gap, min_pair

print("时间(s)  min_gap(m)  pair       head_r(m)  collides?")
print("-" * 70)
for t in range(0, 601, 20):
    _, _, theta_array = _solve_kinematics(t)
    gap, pair = correct_gap(theta_array, L_list, B, W)
    head_r = B * theta_array[0] / (2 * np.pi)
    collides = "YES" if gap < W else "no"
    print(f"  {t:4d}    {gap:10.6f}   ({pair[0]:3d},{pair[1]:3d})    {head_r:8.4f}    {collides}")

# 细扫碰撞区间
print("\n细扫 380-450s:")
for t in range(380, 451, 2):
    _, _, theta_array = _solve_kinematics(t)
    gap, pair = correct_gap(theta_array, L_list, B, W)
    head_r = B * theta_array[0] / (2 * np.pi)
    collides = "YES" if gap < W else "no"
    print(f"  {t:4d}    {gap:10.6f}   ({pair[0]:3d},{pair[1]:3d})    {head_r:8.4f}    {collides}")
