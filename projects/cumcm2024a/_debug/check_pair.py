import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

# t=410
s0 = spiral_arc_length(THETA_0, B)
s_target = max(0, s0 - V1 * 410)
theta_head = inverse_arc_length(s_target, B)
theta_array = solve_chain_thetas(theta_head, L_list, B)
positions = [spiral_point(t, B) for t in theta_array]

n = len(L_list)

# Check turns for indices around 140-170
print('Turns for indices 130-170:')
for i in range(130, 171):
    turn = theta_array[i] / (2*np.pi)
    r = B * theta_array[i] / (2*np.pi)
    print(f'  {i}: theta={theta_array[i]:.4f}, turn={turn:.4f}, r={r:.4f}')

# Segment distance between 141 and 164
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
    t_ = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
    s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
    t_ = max(0, min(1, t_))
    s = max(0, min(1, s))
    cx = np.array(p1) + t_*d
    dx = np.array(p3) + s*e
    return np.linalg.norm(cx - dx)

print(f'\nSegment distance 141-164: {seg_dist(positions[141], positions[142], positions[164], positions[165]):.6f}')
print(f'Segment distance 141-163: {seg_dist(positions[141], positions[142], positions[163], positions[164]):.6f}')
print(f'Segment distance 140-164: {seg_dist(positions[140], positions[141], positions[164], positions[165]):.6f}')