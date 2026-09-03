"""终极诊断：碰撞判据不是几何距离，而是螺线参数约束。

2024A题碰撞定义："盘入过程中，板凳会发生碰撞"
真实含义：板凳i在螺线上的位置与板凳i在相邻圈的位置重叠
即：板凳i的螺线极角 theta_i 与 theta_i + 2π 处的螺线位置，
板凳宽度导致矩形碰撞。

关键公式：螺线 r=a*θ，相邻圈径向间距 = b = 2πa
板凳i中心线弦的两个端点在 theta_i 和 theta_{i+1}
弦的中点到相邻圈螺线弧的最短距离 < w/2 → 碰撞

但更根本的：问题可能在于链式求解器把所有板凳排在同一条螺线上，
而真实物理是每节板凳是独立刚体，不严格在螺线上。

让我用完全不同的方法验证：
直接检查相邻圈板凳中线段到线段的距离，考虑板凳宽度。
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from solve import _build_L_list, B, W, THETA_0, V1, L_HEAD, L_BODY

L_list = _build_L_list()
n = len(L_list)
a = B / (2 * np.pi)

# 螺线上两点之间的弦，弦到相邻圈弧的最小距离
# 弦中点 M = (P(theta_i) + P(theta_{i+1})) / 2
# 弦中点处的径向距离 r_M = |M|
# 相邻内圈螺线在相同角度处的径向距离 = r_M - b
# 距离 = b - sagitta - w/2 ... 不对

# 让我换个思路：直接计算所有板凳对的最小距离
# 但用正确的矩形碰撞模型：SAT (Separating Axis Theorem)

def rect_collision(p1, p2, p3, p4, w):
    """检查两条线段（宽度w）构成的矩形是否碰撞。
    使用SAT（分离轴定理）。
    """
    # 矩形1: p1->p2, 宽w
    # 矩形2: p3->p4, 宽w
    d1 = np.array(p2) - np.array(p1)
    d2 = np.array(p4) - np.array(p3)
    
    l1 = np.linalg.norm(d1)
    l2 = np.linalg.norm(d2)
    if l1 < 1e-15 or l2 < 1e-15:
        return False
    
    # 方向和法向
    dir1 = d1 / l1
    dir2 = d2 / l2
    
    # 4个分离轴：dir1, dir2, normal1, normal2
    axes = [dir1, dir2, np.array([-dir1[1], dir1[0]]), np.array([-dir2[1], dir2[0]])]
    
    # 矩形角点
    n1 = np.array([-dir1[1], dir1[0]]) * w / 2
    n2 = np.array([-dir2[1], dir2[0]]) * w / 2
    
    rect1 = [np.array(p1)+n1, np.array(p2)+n1, np.array(p2)-n1, np.array(p1)-n1]
    rect2 = [np.array(p3)+n2, np.array(p4)+n2, np.array(p4)-n2, np.array(p3)-n2]
    
    for axis in axes:
        proj1 = [np.dot(v, axis) for v in rect1]
        proj2 = [np.dot(v, axis) for v in rect2]
        if max(proj1) < min(proj2) or max(proj2) < min(proj1):
            return False  # 分离
    return True  # 碰撞

# 全对扫描（限制圈层差 <= 1）
print("=== SAT矩形碰撞扫描 ===")
print("t(s)    r_head(m)  collisions  min_clear   pair")
print("-" * 60)

for t in range(400, 425, 1):
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = [spiral_point(t_, B) for t_ in theta_array]
    
    collisions = 0
    min_clear = 1e9
    min_pair = (-1, -1)
    
    for i in range(n):
        for j in range(i+2, min(n, i+50)):  # 限制搜索范围
            if rect_collision(positions[i], positions[i+1],
                             positions[j], positions[min(j+1, n)], W):
                collisions += 1
                if (i, j) == (-1, -1) or True:
                    # 计算净空
                    p1, p2 = np.array(positions[i]), np.array(positions[i+1])
                    p3, p4 = np.array(positions[j]), np.array(positions[min(j+1, n)])
                    d = p2 - p1
                    e = p4 - p3
                    denom = np.dot(d,d)*np.dot(e,e) - np.dot(d,e)**2
                    if abs(denom) > 1e-18:
                        diff = p3 - p1
                        t_ = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
                        s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
                        t_ = max(0, min(1, t_))
                        s = max(0, min(1, s))
                        cx = p1 + t_*d
                        dx = p3 + s*e
                        dist = np.linalg.norm(cx - dx)
                        clear = dist - W
                        if clear < min_clear:
                            min_clear = clear
                            min_pair = (i, j)
    
    head_r = B * theta_array[0] / (2 * np.pi)
    flag = f"{'<<<' if collisions > 0 else ''}"
    print(f"{t:4d}    {head_r:8.4f}    {collisions:5d}      {min_clear:10.6f}   ({min_pair[0]:3d},{min_pair[1]:3d})  {flag}")
    
    if collisions > 0 and t > 413:
        break  # 找到首次碰撞后停止
