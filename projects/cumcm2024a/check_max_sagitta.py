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

# Find max sagitta over all benches at different times
print("t(s)    r_head    max_sag    bench_i    r_bench    sag+w/2>b?")
for t in [360, 370, 380, 390, 400, 410, 412.83, 415, 420]:
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
    
    r_bench = B * theta_array[max_i] / (2 * np.pi)
    r_head = B * theta_array[0] / (2 * np.pi)
    collides = (max_sag + W/2) > B
    print(f"{t:7.2f}    {r_head:.4f}    {max_sag:.6f}    {max_i:3d}    {r_bench:.4f}    {'YES' if collides else 'no'}")

# Check when max_sag + w/2 = b for each bench
print("\n=== Per-bench collision times (sag+w/2 > b) ===")
for i in range(0, min(10, len(L_list))):
    print(f"\nBench {i} (L={L_list[i]}):")
    for t in np.arange(300, 450, 5):
        s0 = spiral_arc_length(THETA_0, B)
        s_target = max(0, s0 - V1 * t)
        theta_head = inverse_arc_length(s_target, B)
        theta_array = solve_chain_thetas(theta_head, L_list, B)
        if i < len(theta_array) - 1:
            sag = compute_sagitta(theta_array[i], theta_array[i+1], B)
            if sag + W/2 > B:
                r = B * theta_array[i] / (2 * np.pi)
                print(f"  t={t}: sag={sag:.4f}, r={r:.4f}, total={sag+W/2:.4f} > b")
                break