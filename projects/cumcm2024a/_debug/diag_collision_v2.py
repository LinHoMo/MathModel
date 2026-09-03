"""深度诊断：检查螺距方向（径向）的板凳间距是否 < 板凳宽。
板凳宽 w=0.30m，螺距 b=0.55m。相邻圈板凳如果径向投影距离 < w 则碰撞。
但题目原始碰撞判据不是线段距离——而是板凳几何体（矩形）碰撞。

标准国赛2024A碰撞判据：两节板凳（矩形 w×L）不重叠的最小条件是
相邻圈径向间距 >= w。由于 b=0.55 > w=0.30，径向永远不碰撞。

但真正的碰撞发生在：当板凳弯曲到一定程度时，同一圈内相邻板凳的
**板凳侧面**接触。判据应为：
  两侧把手间距的垂直分量 = L_min * sin(deflection_angle) <= w

让我检查正确的判据：code偏转角的物理意义。
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point
from solve import _build_L_list, _solve_kinematics, B, W

L_list = _build_L_list()
n = len(L_list)

# 国赛2024A标准碰撞判据：
# 板凳 i 和板凳 i+1 在共享把手 H_{i+1} 处的夹角为 alpha（code偏转角）
# 板凳不碰撞的条件：L_min * sin(alpha) >= w  （相邻板凳侧面不接触）
# 但这其实是错的——正确的几何关系是：
# 两节板凳在铰接处的最小间距 = L_min * sin(alpha)
# 其中 alpha 是两节板凳方向的夹角（0=平行，pi=对折）
# 当 alpha 很小（板凳几乎平行），sin(alpha)≈0，间距≈0 → 碰撞
# 当 alpha=pi/2，sin=1，间距=L_min → 不碰撞

# 真正的碰撞判据应该是：
# gap = L_min * sin(alpha) < w  → 碰撞
# 但 sin(alpha) 当 alpha→0 时趋近 0，这意味着板凳几乎平行时碰撞

# 让我们检查是否还有另一种判据：
# 在国赛2024A中，真正的碰撞是**非相邻**板凳之间的碰撞
# 具体是：第i节板凳和第i+2节板凳（隔一节）的距离

# 让我检查隔一节的板凳对
print("=== 隔节板凳距离（i, i+2）===")
for t_test in [400, 410, 412, 413, 415, 420, 440]:
    _, _, theta_array = _solve_kinematics(t_test)
    positions = [spiral_point(t, B) for t in theta_array]
    
    min_dist = 1e9
    min_pair = (-1, -1)
    
    # 检查 i 和 i+2 的板凳中线段最短距离
    for i in range(n - 2):
        # 板凳 i: H_i -> H_{i+1}
        # 板凳 i+2: H_{i+2} -> H_{i+3}
        p1 = positions[i]
        p2 = positions[i+1]
        p3 = positions[i+2]
        p4 = positions[min(i+3, n)]
        
        # 线段距离
        d = np.array(p2) - np.array(p1)
        e = np.array(p4) - np.array(p3)
        denom = np.dot(d,d)*np.dot(e,e) - np.dot(d,e)**2
        if abs(denom) < 1e-18:
            dist = min(np.linalg.norm(np.array(p1)-np.array(p3)),
                       np.linalg.norm(np.array(p1)-np.array(p4)),
                       np.linalg.norm(np.array(p2)-np.array(p3)),
                       np.linalg.norm(np.array(p2)-np.array(p4)))
        else:
            diff = np.array(p3) - np.array(p1)
            t = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
            s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
            t = max(0, min(1, t))
            s = max(0, min(1, s))
            cx = np.array(p1) + t*d
            dx = np.array(p3) + s*e
            dist = np.linalg.norm(cx - dx)
        
        if dist < min_dist:
            min_dist = dist
            min_pair = (i, i+2)
    
    head_r = B * theta_array[0] / (2 * np.pi)
    print(f"t={t_test:4d}s  head_r={head_r:.4f}m  min_dist={min_dist:.6f}m  pair=({min_pair[0]},{min_pair[1]})  "
          f"{'COLLIDE' if min_dist < W else 'ok'}")

# 真正的问题：2024A题碰撞判据是"板凳之间发生碰撞"
# 板凳是矩形 w=0.30 x L，当龙头越来越靠近中心，螺线越来越紧
# 同一圈内相邻板凳的侧边距离 = L * sin(alpha) 其中 alpha 是偏转角
# 当 alpha 小到一定程度，sin(alpha) * L < w → 侧边接触

print("\n=== 相邻板凳偏转角判据 L*sin(alpha) ===")
for t_test in [0, 100, 200, 300, 400, 410, 412, 413, 415, 420, 440]:
    _, _, theta_array = _solve_kinematics(t_test)
    positions = [spiral_point(t, B) for t in theta_array]
    
    min_gap = 1e9
    min_i = -1
    
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
        sin_a = np.sin(alpha)
        L_min = min(L_list[i], L_list[i+1])
        gap = L_min * sin_a
        if gap < min_gap:
            min_gap = gap
            min_i = i
    
    head_r = B * theta_array[0] / (2 * np.pi)
    print(f"t={t_test:4d}s  head_r={head_r:.4f}m  min_gap={min_gap:.6f}m  i={min_i}  "
          f"{'COLLIDE' if min_gap < W else 'ok'}")
