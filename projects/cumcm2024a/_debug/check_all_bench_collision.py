import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

def compute_sagitta(theta_a, theta_b, b):
    r_a = b * theta_a / (2 * np.pi)
    r_b = b * theta_b / (2 * np.pi)
    r_mid = (r_a + r_b) / 2.0
    dtheta = abs(theta_b - theta_a)
    sag = r_mid * (1.0 - np.cos(dtheta / 2.0))
    return sag

# For each bench, find the bench on the next outer turn at similar angular position
# and check sagitta_i + sagitta_j + w > b
print("Time scan for first rectangular collision (any bench pair on adjacent turns):")
for t in np.arange(300, 450, 5):
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    collision = False
    coll_pair = (-1, -1)
    min_gap = 1e9
    
    # For each bench i, find bench j on next outer turn
    for i in range(len(L_list)):
        turn_i = theta_array[i] / (2 * np.pi)
        target_turn = turn_i + 1
        
        # Find bench j whose turn is closest to target_turn
        best_j = -1
        best_diff = 1e9
        for j in range(i+2, len(L_list)):
            turn_j = theta_array[j] / (2 * np.pi)
            diff = abs(turn_j - target_turn)
            if diff < best_diff:
                best_diff = diff
                best_j = j
            if turn_j > target_turn + 0.5:
                break
        
        if best_j >= 0 and best_diff < 0.2:  # well-aligned
            sag_i = compute_sagitta(theta_array[i], theta_array[i+1], B)
            sag_j = compute_sagitta(theta_array[best_j], theta_array[best_j+1], B)
            gap = B - sag_i - sag_j - W
            if gap < min_gap:
                min_gap = gap
                coll_pair = (i, best_j)
            if gap < 0:
                collision = True
                coll_pair = (i, best_j)
                break
    
    r_head = B * theta_array[0] / (2 * np.pi)
    status = "COLLIDE" if collision else f"gap={min_gap:.4f}"
    print(f"  t={t:4.0f}: r_head={r_head:.4f}, {status}, pair={coll_pair}")
    
    if collision:
        print(f"  First collision at t≈{t}s")
        break

# Fine search around first collision
print("\nFine search:")
for t in np.arange(300, 370, 1):
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    collision = False
    for i in range(len(L_list)):
        turn_i = theta_array[i] / (2 * np.pi)
        target_turn = turn_i + 1
        best_j = -1
        best_diff = 1e9
        for j in range(i+2, len(L_list)):
            turn_j = theta_array[j] / (2 * np.pi)
            diff = abs(turn_j - target_turn)
            if diff < best_diff:
                best_diff = diff
                best_j = j
            if turn_j > target_turn + 0.5:
                break
        
        if best_j >= 0 and best_diff < 0.2:
            sag_i = compute_sagitta(theta_array[i], theta_array[i+1], B)
            sag_j = compute_sagitta(theta_array[best_j], theta_array[best_j+1], B)
            gap = B - sag_i - sag_j - W
            if gap < 0:
                collision = True
                r_i = B * theta_array[i] / (2 * np.pi)
                r_j = B * theta_array[best_j] / (2 * np.pi)
                print(f"  t={t}: COLLIDE pair=({i},{best_j}), r_i={r_i:.4f}, r_j={r_j:.4f}, sag_i={sag_i:.4f}, sag_j={sag_j:.4f}, gap={gap:.4f}")
                break
    if collision:
        break