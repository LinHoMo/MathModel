import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from collision import check_collision
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

print('Testing new collision detection:')
print('t(s)    r_head    collision_type    pair    gap')
for t in [300, 350, 360, 365, 370, 380, 390, 400, 410, 412.83, 415, 420]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    is_col, info = check_collision(theta_array, L_list, B, W)
    head_r = B * theta_array[0] / (2 * np.pi)
    if is_col:
        ctype = info["type"]
        pair = info["pair"]
        gap = info["gap"]
        print(f'{t:7.2f}  {head_r:.4f}  {ctype:20s}  ({pair[0]:3d},{pair[1]:3d})  {gap:.6f}')
    else:
        print(f'{t:7.2f}  {head_r:.4f}  no collision')