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

# Check head bench vs bench on next outer turn at various times
print("t    r_head   head_sag  opp_idx  opp_sag  sum_sag+w  b  gap=b-sum-w  seg_dist")
for t in [360, 365, 370, 380, 390, 400, 410, 412.83]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    positions = [spiral_point(t_, B) for t_ in theta_array]
    
    r_head = B * theta_array[0] / (2 * np.pi)
    head_turn = theta_array[0] / (2 * np.pi)
    head_sag = compute_sagitta(theta_array[0], theta_array[1], B)
    
    # Find bench on next outer turn (turn = head_turn + 1)
    target_turn = head_turn + 1
    opp_idx = -1
    for i in range(1, len(L_list)):
        turn_i = theta_array[i] / (2 * np.pi)
        if turn_i >= target_turn - 0.1:
            opp_idx = i
            break
    
    if opp_idx > 0:
        opp_sag = compute_sagitta(theta_array[opp_idx], theta_array[opp_idx+1], B)
        sum_sag_w = head_sag + opp_sag + W
        gap = B - sum_sag_w
        d = seg_dist(positions[0], positions[1], positions[opp_idx], positions[opp_idx+1])
        print(f"{t:4.0f}  {r_head:.4f}  {head_sag:.4f}  {opp_idx:3d}  {opp_sag:.4f}  {sum_sag_w:.4f}  {B:.2f}  {gap:.4f}  {d:.4f}")
    else:
        print(f"{t:4.0f}  {r_head:.4f}  {head_sag:.4f}  no opp bench found")

# Also check: maybe the collision is when the head bench's sagitta exceeds the radial distance to the CENTER?
# i.e., the bench hits the center pole?
print("\n\nHead bench inner edge distance from center:")
for t in [360, 365, 370, 380, 390, 400, 410, 412.83]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    r_head = B * theta_array[0] / (2 * np.pi)
    head_sag = compute_sagitta(theta_array[0], theta_array[1], B)
    # Inner edge distance from center = r_mid - sagitta - w/2
    r_mid = (B*theta_array[0]/(2*np.pi) + B*theta_array[1]/(2*np.pi)) / 2
    inner_edge_r = r_mid - head_sag - W/2
    print(f"  t={t}: r_head={r_head:.4f}, r_mid={r_mid:.4f}, sag={head_sag:.4f}, inner_edge_r={inner_edge_r:.4f}")