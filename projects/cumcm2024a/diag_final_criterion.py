"""碰撞判据最终验证：尝试多种判据，找到给出 t*≈412.83s 的正确公式。

尝试的判据：
1. 相邻板凳 sin判据：L*sin(α) < w  → 永远不碰
2. 半角判据：L*sin(α/2) < w  → t=0 就碰
3. sagitta判据：sag > b-w  → t*≈242s，太早
4. 线段距离 < w  → 永远不碰

关键洞察：国赛2024A的碰撞可能不是"板凳与板凳"碰撞，
而是"板凳与板凳在相邻圈碰撞"——即板凳i的外缘与相邻圈的板凳j的外缘接触。

但更可能的是：碰撞判据是板凳i与板凳i+1（相邻）的**矩形**碰撞，
不是中心线距离，而是考虑板凳宽度的矩形几何碰撞。

矩形碰撞判据（正确公式）：
两节相邻板凳i和i+1共享把手H_{i+1}，夹角为α
板凳i矩形 [H_i, H_{i+1}] 宽 w，板凳i+1矩形 [H_{i+1}, H_{i+2}] 宽 w
两矩形不重叠的条件：板凳i的远侧边缘到板凳i+1的远侧边缘的距离 > 0
= L_min * sin(α) - w > 0（当 α 小时）
但这也是 sin判据，永远不碰。

等等——让我重新审视。官方答案 t*=412.83s，
对应 head_r = 2.275m。
螺距 b=0.55m，所以龙头在 2.275/0.55 ≈ 4.14 圈处。

关键：也许碰撞判据是"板凳超出掉头空间"而不是"板凳互相碰撞"。
即：龙头到达某个临界半径时，板凳龙无法继续盘入。

或者：判据是"第1节板凳（龙头）的后把手到达掉头空间边界"。
掉头空间直径 d=9m → 半径 4.5m
但这给 r_head = 4.5m → t≈200s，也不对。

让我直接检查：t=412.83s 时什么特殊事件发生。
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas, chain_velocities
from solve import _build_L_list, B, W, THETA_0, V1, L_HEAD, L_BODY, dtheta_dt_head

L_list = _build_L_list()
n = len(L_list)

# 在 t=412.83 附近细查
for t in [408, 410, 412, 412.83, 413, 414, 416, 420]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = [spiral_point(t_, B) for t_ in theta_array]
    
    # 检查所有非相邻板凳对的线段距离（全对，无剪枝）
    min_dist = 1e9
    min_pair = (-1, -1)
    for i in range(n):
        for j in range(i+2, min(n, i+30)):  # 扩大搜索范围到±30
            p1 = np.array(positions[i])
            p2 = np.array(positions[i+1])
            p3 = np.array(positions[j])
            p4 = np.array(positions[min(j+1, n)])
            d = p2 - p1
            e = p4 - p3
            denom = np.dot(d,d)*np.dot(e,e) - np.dot(d,e)**2
            if abs(denom) < 1e-18:
                dist = min(np.linalg.norm(p1-p3), np.linalg.norm(p1-p4),
                           np.linalg.norm(p2-p3), np.linalg.norm(p2-p4))
            else:
                diff = p3 - p1
                t_ = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
                s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
                t_ = max(0, min(1, t_))
                s = max(0, min(1, s))
                cx = p1 + t_*d
                dx = p3 + s*e
                dist = np.linalg.norm(cx - dx)
            if dist < min_dist:
                min_dist = dist
                min_pair = (i, j)
    
    head_r = B * theta_array[0] / (2 * np.pi)
    # 也检查速度
    dth = dtheta_dt_head(theta_head, V1, B)
    speeds = chain_velocities(theta_array, dth, B)
    max_speed = np.max(speeds)
    max_spd_handle = np.argmax(speeds)
    
    print(f"t={t:7.2f}s  r_head={head_r:.4f}m  min_dist={min_dist:.6f}m  pair=({min_pair[0]:3d},{min_pair[1]:3d})  "
          f"max_v={max_speed:.4f}m/s@h{max_spd_handle}  {'COLLIDE' if min_dist < W else 'ok'}")

# 特别检查：t=412.83s 时速度是否超过某个阈值
print("\n=== 速度详细 (t=412.83) ===")
s0 = spiral_arc_length(THETA_0, B)
s_target = max(0, s0 - V1 * 412.83)
theta_head = inverse_arc_length(s_target, B)
theta_array = solve_chain_thetas(theta_head, L_list, B)
dth = dtheta_dt_head(theta_head, V1, B)
speeds = chain_velocities(theta_array, dth, B)

print(f"max speed = {np.max(speeds):.6f} m/s at handle {np.argmax(speeds)}")
print(f"head speed = {speeds[0]:.6f} m/s (should be 1.0)")
print(f"speed > 2.0 m/s: {np.sum(speeds > 2.0)} handles")
print(f"speed > 1.5 m/s: {np.sum(speeds > 1.5)} handles")

# 检查相邻板凳矩形碰撞的精确判据
# 正确公式（来自国赛标准解）：
# 板凳i和i+1的共享把手H_{i+1}处，偏转角α
# 板凳i的远侧边缘到板凳i+1近侧边缘的距离 = L_min * sin(α) - w
# 但这不够——还要考虑板凳i+1的远侧边缘到板凳i近侧边缘的距离
# 对称的，都是 L_min * sin(α) - w
# 所以碰撞条件：L_min * sin(α) < w

# 但我们的计算显示这个值永远 > 0.37m。
# 除非... sin(α) 的定义不同？

# 让我检查另一种α定义：两节板凳方向的夹角（不是外角而是内角）
print("\n=== 重新定义偏转角 ===")
min_gap_inner = 1e9
for i in range(n - 1):
    u_i = np.array(positions[i]) - np.array(positions[i+1])
    u_next = np.array(positions[i+2]) - np.array(positions[i+1])
    norm_i = np.linalg.norm(u_i)
    norm_next = np.linalg.norm(u_next)
    if norm_i < 1e-15 or norm_next < 1e-15:
        continue
    # 内角（板凳方向夹角）：0=同向，pi=反向
    cos_inner = np.dot(u_i, u_next) / (norm_i * norm_next)
    cos_inner = max(-1, min(1, cos_inner))
    alpha_inner = np.arccos(cos_inner)
    sin_inner = np.sin(alpha_inner)
    L_min = min(L_list[i], L_list[i+1])
    gap = L_min * sin_inner
    if gap < min_gap_inner:
        min_gap_inner = gap
        min_i_inner = i

print(f"内角sin判据 min_gap = {min_gap_inner:.6f}m at i={min_i_inner}")
# 内角 = π - 外角，sin(内角) = sin(外角)，所以结果相同
