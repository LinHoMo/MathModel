import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

# t=412.83
s0 = spiral_arc_length(THETA_0, B)
s_target = max(0, s0 - V1 * 412.83)
theta_head = inverse_arc_length(s_target, B)
theta_array = solve_chain_thetas(theta_head, L_list, B)
positions = [spiral_point(t_, B) for t_ in theta_array]

# Find pairs with theta difference close to 2*pi
print("Pairs with theta diff ≈ 2π:")
for i in range(len(L_list)):
    for j in range(i+2, len(L_list)):
        dtheta = theta_array[j] - theta_array[i]
        if abs(dtheta - 2*np.pi) < 0.5:  # within 0.5 rad of 2π
            # segment distance
            d = np.array(positions[i+1]) - np.array(positions[i])
            e = np.array(positions[min(j+1, len(L_list))]) - np.array(positions[j])
            denom = np.dot(d,d)*np.dot(e,e) - np.dot(d,e)**2
            if abs(denom) > 1e-18:
                diff = np.array(positions[j]) - np.array(positions[i])
                t_ = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
                s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
                t_ = max(0, min(1, t_))
                s = max(0, min(1, s))
                cx = np.array(positions[i]) + t_*d
                dx = np.array(positions[j]) + s*e
                dist = np.linalg.norm(cx - dx)
                print(f"  ({i},{j}): theta_i={theta_array[i]:.4f}, theta_j={theta_array[j]:.4f}, dtheta={dtheta:.4f}, seg_dist={dist:.6f}")

# Also check theta diff ≈ 4π, 6π etc
print("\nPairs with theta diff ≈ 4π:")
for i in range(len(L_list)):
    for j in range(i+2, len(L_list)):
        dtheta = theta_array[j] - theta_array[i]
        if abs(dtheta - 4*np.pi) < 0.5:
            d = np.array(positions[i+1]) - np.array(positions[i])
            e = np.array(positions[min(j+1, len(L_list))]) - np.array(positions[j])
            denom = np.dot(d,d)*np.dot(e,e) - np.dot(d,e)**2
            if abs(denom) > 1e-18:
                diff = np.array(positions[j]) - np.array(positions[i])
                t_ = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
                s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
                t_ = max(0, min(1, t_))
                s = max(0, min(1, s))
                cx = np.array(positions[i]) + t_*d
                dx = np.array(positions[j]) + s*e
                dist = np.linalg.norm(cx - dx)
                print(f"  ({i},{j}): dtheta={dtheta:.4f}, seg_dist={dist:.6f}")