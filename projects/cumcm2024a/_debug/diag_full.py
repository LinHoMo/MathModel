"""全面诊断：验证链式求解器正确性 + 搜索真正的碰撞时刻。

2024A题碰撞判据分析：
- 相邻板凳 sin判据：gap = L*sin(alpha)，alpha为偏转角
- 但所有时间的 min_gap 都 > 0.30m（在 i=220 尾部）
- 官方答案 t*=412.83s，说明判据可能不同

可能的正确判据：
1. 板凳几何体（矩形w×L）碰撞，不是中心线距离
2. 相邻圈板凳的边缘距离 < 0
3. 链式求解器在密集区域跳圈，导致位置错误

本脚本：验证链式距离 + 扫描所有板凳对的矩形碰撞
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point, spiral_tangent
from solve import _build_L_list, _solve_kinematics, B, W, L_HEAD, L_BODY

L_list = _build_L_list()
n = len(L_list)

def bench_rect_collision(pos, theta_arr, L_list, w, i, j):
    """检查板凳i和板凳j的矩形是否碰撞。
    板凳i: H_i -> H_{i+1}, 板凳j: H_j -> H_{j+1}
    简化为：两线段的距离减去宽度 < 0
    """
    p1, p2 = pos[i], pos[i+1]
    p3, p4 = pos[j], pos[min(j+1, len(pos)-1)]
    
    # 线段最短距离
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
    
    # 矩形碰撞近似：中心线距离 - w < 0 (两侧各 w/2)
    return dist - w

# 1. 验证链式距离
print("=== 链式距离验证 (t=412.83) ===")
_, _, theta_arr = _solve_kinematics(412.83)
pos = [spiral_point(t, B) for t in theta_arr]
max_err = 0
for i in range(n):
    dist = np.linalg.norm(np.array(pos[i]) - np.array(pos[i+1]))
    err = abs(dist - L_list[i])
    if err > max_err:
        max_err = err
print(f"最大链式距离误差: {max_err:.2e} m")
print(f"龙头 r = {B*theta_arr[0]/(2*np.pi):.4f} m, theta = {theta_arr[0]:.4f}")
print(f"龙尾 r = {B*theta_arr[-1]/(2*np.pi):.4f} m, theta = {theta_arr[-1]:.4f}")
print(f"theta 范围: [{theta_arr[0]:.2f}, {theta_arr[-1]:.2f}], 跨度 = {(theta_arr[-1]-theta_arr[0])/(2*np.pi):.2f} 圈")

# 2. 检查是否有跳圈：相邻把手 theta 差应 < 2*pi
print("\n=== 跳圈检查 ===")
jumps = []
for i in range(n):
    dtheta = theta_arr[i+1] - theta_arr[i]
    if dtheta > 2 * np.pi or dtheta < 0:
        jumps.append((i, dtheta))
if jumps:
    print(f"发现 {len(jumps)} 处跳圈:")
    for i, dtheta in jumps[:10]:
        print(f"  handle {i}->{i+1}: dtheta={dtheta:.4f} ({dtheta/(2*np.pi):.2f} 圈)")
else:
    print("无跳圈，链式求解连续")

# 3. 相邻板凳偏转角统计（全位置）
print("\n=== t=412.83 全位置偏转角统计 ===")
gaps = []
for i in range(n - 1):
    u_i = np.array(pos[i]) - np.array(pos[i+1])
    u_next = np.array(pos[i+2]) - np.array(pos[i+1])
    norm_i = np.linalg.norm(u_i)
    norm_next = np.linalg.norm(u_next)
    if norm_i < 1e-15 or norm_next < 1e-15:
        continue
    cos_a = -np.dot(u_i, u_next) / (norm_i * norm_next)
    cos_a = max(-1, min(1, cos_a))
    alpha = np.arccos(cos_a)
    sin_a = np.sin(alpha)
    L_min = min(L_list[i], L_list[i+1])
    gap = L_min * sin_a
    gaps.append((gap, i, alpha))

gaps.sort()
print("最小的 10 个 gap:")
for gap, i, alpha in gaps[:10]:
    r_i = B * theta_arr[i] / (2 * np.pi)
    print(f"  i={i:3d}  gap={gap:.6f}m  alpha={np.degrees(alpha):.3f}°  r={r_i:.3f}m  {'COLLIDE' if gap < W else ''}")

# 4. 全对扫描（仅相邻圈层）- 用圈层索引加速
print("\n=== 相邻圈层全对扫描 (t=412.83) ===")
# 计算每个把手的圈层
turns = [int(t / (2 * np.pi)) for t in theta_arr]
min_dist_all = 1e9
min_pair = (-1, -1)
for i in range(n):
    for j in range(i+2, n):
        # 只检查圈层差 <= 1 的对
        if abs(turns[j] - turns[i]) > 1:
            continue
        clearance = bench_rect_collision(pos, theta_arr, L_list, W, i, j)
        if clearance < min_dist_all:
            min_dist_all = clearance
            min_pair = (i, j)

print(f"最小净空: {min_dist_all:.6f}m  pair=({min_pair[0]},{min_pair[1]})  {'COLLIDE' if min_dist_all < 0 else 'ok'}")

# 5. 时间扫描：在 400-450s 区间找最小净空
print("\n=== 时间扫描 400-420s (步长 2s) ===")
print("t(s)   min_clearance(m)  pair         collides?")
for t in range(400, 421, 2):
    _, _, theta_arr = _solve_kinematics(t)
    pos = [spiral_point(t_, B) for t_ in theta_arr]
    turns = [int(t_ / (2 * np.pi)) for t_ in theta_arr]
    
    min_clr = 1e9
    min_p = (-1, -1)
    for i in range(n):
        for j in range(i+2, n):
            if abs(turns[j] - turns[i]) > 1:
                continue
            clr = bench_rect_collision(pos, theta_arr, L_list, W, i, j)
            if clr < min_clr:
                min_clr = clr
                min_p = (i, j)
    
    print(f"{t:4d}   {min_clr:14.6f}   ({min_p[0]:3d},{min_p[1]:3d})   {'YES' if min_clr < 0 else 'no'}")
