import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

# Find exact t when sagitta_head + w/2 = b
def compute_sagitta(theta_a, theta_b, b):
    r_a = b * theta_a / (2 * np.pi)
    r_b = b * theta_b / (2 * np.pi)
    r_mid = (r_a + r_b) / 2.0
    dtheta = abs(theta_b - theta_a)
    sag = r_mid * (1.0 - np.cos(dtheta / 2.0))
    return sag

# Search for collision time
print("t(s)    r_head    dtheta_head    sagitta    sag+w/2    b    collides?")
for t in np.arange(360, 420, 2):
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    # Head bench sagitta
    sag = compute_sagitta(theta_array[0], theta_array[1], B)
    r_head = B * theta_array[0] / (2 * np.pi)
    dtheta = theta_array[1] - theta_array[0]
    total = sag + W/2
    collides = total > B
    print(f"{t:4.0f}    {r_head:.4f}    {dtheta:.4f}    {sag:.6f}    {total:.6f}    {B}    {'YES' if collides else 'no'}")

# Fine search
print("\nFine search 370-380:")
for t in np.arange(370, 380, 0.5):
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    sag = compute_sagitta(theta_array[0], theta_array[1], B)
    total = sag + W/2
    if total > B:
        print(f"  t={t:.1f}: sag={sag:.6f}, total={total:.6f} > b={B}")
        break

# Also check: maybe the collision is with the bench on the SAME turn but not adjacent?
# Or maybe the criterion is sagitta > b - w (not w/2)?
print("\n\nCriterion: sagitta > b - w = {:.4f}".format(B - W))
for t in np.arange(240, 250, 1):
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    sag = compute_sagitta(theta_array[0], theta_array[1], B)
    if sag > B - W:
        print(f"  t={t}: sag={sag:.6f} > b-w={B-W}")
        break