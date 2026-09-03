import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from collision import check_collision
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

def compute_sagitta(theta_a, theta_b, b):
    r_a = b * theta_a / (2 * np.pi)
    r_b = b * theta_b / (2 * np.pi)
    r_mid = (r_a + r_b) / 2.0
    dtheta = abs(theta_b - theta_a)
    return r_mid * (1.0 - np.cos(dtheta / 2.0))

# Test the sagitta criterion: sagitta + w/2 > b for ANY bench
print("Sagitta criterion (sagitta + w/2 > b):")
for t in [240, 250, 300, 350, 360, 365, 370, 380, 390, 400, 410, 412.83, 420]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    max_sag = 0
    max_i = -1
    for i in range(len(L_list)):
        sag = compute_sagitta(theta_array[i], theta_array[i+1], B)
        if sag > max_sag:
            max_sag = sag
            max_i = i
    
    head_r = B * theta_array[0] / (2 * np.pi)
    total = max_sag + W/2
    collides = total > B
    print(f'  t={t:7.2f}: r_head={head_r:.4f}, max_sag={max_sag:.6f} at i={max_i}, total={total:.6f} {"COLLIDE" if collides else "ok"}')

# Test the criterion: sagitta_i + sagitta_j + w > b for adjacent-turn pairs
print("\nAdjacent-turn bench pair sagitta sum criterion:")
for t in [240, 250, 300, 350, 360, 365, 370, 380, 390, 400, 410, 412.83, 420]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    collision = False
    min_gap = 1e9
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
            if gap < min_gap:
                min_gap = gap
            if gap < 0:
                collision = True
    
    head_r = B * theta_array[0] / (2 * np.pi)
    print(f'  t={t:7.2f}: r_head={head_r:.4f}, min_gap={min_gap:.6f} {"COLLIDE" if collision else "ok"}')

# What about the criterion: max over all benches of (sagitta * something)?
# Let's check the exact value at t=412.83
print("\n=== Detailed at t=412.83 ===")
s0 = spiral_arc_length(THETA_0, B)
s_target = max(0, s0 - V1 * 412.83)
theta_head = inverse_arc_length(s_target, B)
theta_array = solve_chain_thetas(theta_head, L_list, B)

for i in range(min(10, len(L_list))):
    sag = compute_sagitta(theta_array[i], theta_array[i+1], B)
    r = B * theta_array[i] / (2 * np.pi)
    dtheta = theta_array[i+1] - theta_array[i]
    print(f'  bench {i}: r={r:.4f}, dtheta={dtheta:.4f}, sag={sag:.6f}, sag+w/2={sag+W/2:.6f}')