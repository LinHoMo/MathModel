import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

def rect_collision(p1, p2, p3, p4, w):
    d1 = np.array(p2) - np.array(p1)
    d2 = np.array(p4) - np.array(p3)
    l1 = np.linalg.norm(d1)
    l2 = np.linalg.norm(d2)
    if l1 < 1e-15 or l2 < 1e-15:
        return False, 0
    dir1 = d1 / l1
    dir2 = d2 / l2
    axes = [dir1, dir2, np.array([-dir1[1], dir1[0]]), np.array([-dir2[1], dir2[0]])]
    n1 = np.array([-dir1[1], dir1[0]]) * w / 2
    n2 = np.array([-dir2[1], dir2[0]]) * w / 2
    rect1 = [np.array(p1)+n1, np.array(p2)+n1, np.array(p2)-n1, np.array(p1)-n1]
    rect2 = [np.array(p3)+n2, np.array(p4)+n2, np.array(p4)-n2, np.array(p3)-n2]
    min_overlap = 1e9
    for axis in axes:
        proj1 = [np.dot(v, axis) for v in rect1]
        proj2 = [np.dot(v, axis) for v in rect2]
        if max(proj1) < min(proj2) or max(proj2) < min(proj1):
            return False, 0
        overlap = min(max(proj1), max(proj2)) - max(min(proj1), min(proj2))
        if overlap < min_overlap:
            min_overlap = overlap
    return True, min_overlap

# Check head bench vs opposing bench with SAT at various times
for t in [360, 370, 380, 390, 400, 410, 412.83]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = [spiral_point(t_, B) for t_ in theta_array]
    
    r_head = B * theta_array[0] / (2 * np.pi)
    head_turn = theta_array[0] / (2 * np.pi)
    target_turn = head_turn + 1
    opp_idx = -1
    for i in range(1, len(L_list)):
        turn_i = theta_array[i] / (2 * np.pi)
        if turn_i >= target_turn - 0.1:
            opp_idx = i
            break
    
    if opp_idx > 0:
        coll, overlap = rect_collision(positions[0], positions[1], positions[opp_idx], positions[opp_idx+1], W)
        print(f"t={t:4.0f}: head vs bench {opp_idx}, SAT_collide={coll}, overlap={overlap:.6f}")

# Also check ALL non-adjacent pairs for SAT collision at t=412.83
print("\n=== Full SAT scan at t=412.83 ===")
s0 = spiral_arc_length(THETA_0, B)
s_target = max(0, s0 - V1 * 412.83)
theta_head = inverse_arc_length(s_target, B)
theta_array = solve_chain_thetas(theta_head, L_list, B)
positions = [spiral_point(t_, B) for t_ in theta_array]

min_overlap = 1e9
min_pair = (-1, -1)
for i in range(len(L_list)):
    for j in range(i+2, min(len(L_list), i+30)):  # limit range for speed
        coll, overlap = rect_collision(positions[i], positions[i+1], positions[j], positions[min(j+1, len(L_list))], W)
        if coll and overlap < min_overlap:
            min_overlap = overlap
            min_pair = (i, j)

if min_pair[0] >= 0:
    print(f"Min overlap: {min_overlap:.6f} at pair {min_pair}")
else:
    print("No SAT collisions found")