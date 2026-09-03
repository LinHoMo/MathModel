"""SAT 碰撞有 bug：没碰撞时 min_clear 不该是 1e9。
修正：无论是否碰撞都计算 min_clear。
而且 SAT 对所有板凳对太慢，用更高效的策略：
只检查圈层差=1 的板凳对。
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()
n = len(L_list)

def seg_dist(p1, p2, p3, p4):
    d = np.array(p2) - np.array(p1)
    e = np.array(p4) - np.array(p3)
    denom = np.dot(d,d)*np.dot(e,e) - np.dot(d,e)**2
    if abs(denom) < 1e-18:
        return min(np.linalg.norm(np.array(p1)-np.array(p3)),
                   np.linalg.norm(np.array(p1)-np.array(p4)),
                   np.linalg.norm(np.array(p2)-np.array(p3)),
                   np.linalg.norm(np.array(p2)-np.array(p4)))
    diff = np.array(p3) - np.array(p1)
    t = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
    s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
    t = max(0, min(1, t))
    s = max(0, min(1, s))
    cx = np.array(p1) + t*d
    dx = np.array(p3) + s*e
    return np.linalg.norm(cx - dx)

# 在每个时间点，只检查"可能碰撞"的板凳对
# 策略：板凳i 和 j 可能碰撞的条件是它们的把手在相邻圈
# 即 theta_i 和 theta_j 差约 2*pi
print("t(s)    r_head  min_seg_dist  min_clear  pair       collides?")
print("-" * 75)

for t in list(range(380, 430, 2)) + [412.83]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = [spiral_point(t_, B) for t_ in theta_array]
    
    min_dist = 1e9
    min_pair = (-1, -1)
    
    # 对每个板凳i，找到相邻圈上最近的板凳j
    for i in range(n):
        # theta_i 对应的圈层
        turn_i = theta_array[i] / (2 * np.pi)
        for j in range(i+2, n):
            turn_j = theta_array[j] / (2 * np.pi)
            turn_diff = abs(turn_j - turn_i)
            # 相邻圈：圈层差在 [0.8, 1.2] 之间
            if turn_diff < 0.8 or turn_diff > 1.2:
                continue
            dist = seg_dist(positions[i], positions[i+1],
                           positions[j], positions[min(j+1, n)])
            if dist < min_dist:
                min_dist = dist
                min_pair = (i, j)
    
    head_r = B * theta_array[0] / (2 * np.pi)
    clear = min_dist - W
    collides = clear < 0
    flag = " <<<" if collides else ""
    print(f"{t:7.2f}  {head_r:.4f}  {min_dist:12.6f}  {clear:10.6f}  ({min_pair[0]:3d},{min_pair[1]:3d})  {'YES' if collides else 'no'}{flag}")
