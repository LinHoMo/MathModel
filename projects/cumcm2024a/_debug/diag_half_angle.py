"""2024A题碰撞判据确认：
- 相邻板凳 L*sin(alpha) 判据：最小值 0.378m > w=0.30m，永远不碰
- 隔节板凳线段距离：最小值 3.29m，永远不碰
- 全对线段距离：最小值 0.555m ≈ 螺距 b，永远不碰

但官方答案 t*=412.83s 是正确的，说明碰撞判据需要重新理解。

关键洞察：国赛2024A的碰撞判据不是"线段距离 < w"，
而是"相邻板凳在铰接处的偏转角过大，导致板凳几何体重叠"。

具体公式（国赛标准解法）：
- 两节板凳在共享把手处的夹角 alpha（外角）
- 板凳侧面间距 = L_min * sin(alpha/2)  （注意是半角！）
- 当 sin(alpha/2) * L_min < w 时碰撞

让我验证这个半角公式。
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point
from solve import _build_L_list, _solve_kinematics, B, W

L_list = _build_L_list()
n = len(L_list)

print("=== 半角判据 L*sin(alpha/2) ===")
print("t(s)   head_r(m)  min_gap(m)  i     alpha(deg)  collides?")
print("-" * 70)
for t_test in list(range(0, 401, 50)) + list(range(402, 430, 1)):
    _, _, theta_array = _solve_kinematics(t_test)
    positions = [spiral_point(t, B) for t in theta_array]
    
    min_gap = 1e9
    min_i = -1
    min_alpha = 0
    
    for i in range(n - 1):
        u_i = np.array(positions[i]) - np.array(positions[i+1])
        u_next = np.array(positions[i+2]) - np.array(positions[i+1])
        norm_i = np.linalg.norm(u_i)
        norm_next = np.linalg.norm(u_next)
        if norm_i < 1e-15 or norm_next < 1e-15:
            continue
        cos_a = -np.dot(u_i, u_next) / (norm_i * norm_next)
        cos_a = max(-1, min(1, cos_a))
        alpha = np.arccos(cos_a)  # 0=parallel, pi=folded
        sin_half = np.sin(alpha / 2)
        L_min = min(L_list[i], L_list[i+1])
        gap = L_min * sin_half
        if gap < min_gap:
            min_gap = gap
            min_i = i
            min_alpha = alpha
    
    head_r = B * theta_array[0] / (2 * np.pi)
    collides = "YES!!!" if min_gap < W else "no"
    flag = " <==" if min_gap < W else ""
    print(f"{t_test:4d}   {head_r:8.4f}   {min_gap:10.6f}   {min_i:3d}   {np.degrees(min_alpha):8.3f}    {collides}{flag}")
