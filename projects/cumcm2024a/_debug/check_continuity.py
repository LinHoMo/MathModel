import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

# Check continuity of theta_array over time
print("Continuity check: theta_i at consecutive times")
prev_theta = None
for t in [0, 10, 50, 100, 200, 300, 350, 360, 370, 380, 390, 400, 410, 412.83]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    if prev_theta is not None:
        # Check max change in theta_i
        diff = np.abs(theta_array - prev_theta)
        max_diff = np.max(diff)
        max_diff_idx = np.argmax(diff)
        print(f'  t={t:7.2f}: max theta change = {max_diff:.6f} at i={max_diff_idx}')
    else:
        print(f'  t={t:7.2f}: initial')
    prev_theta = theta_array.copy()

# Check if any bench ever has dtheta > 2π
print("\n=== Max dtheta over time ===")
for t in [0, 100, 200, 300, 350, 360, 370, 380, 390, 400, 410, 412.83]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    dtheta = np.diff(theta_array)
    max_dtheta = np.max(dtheta)
    max_idx = np.argmax(dtheta)
    print(f'  t={t:7.2f}: max_dtheta={max_dtheta:.4f} ({max_dtheta/(2*np.pi):.4f} turns) at bench {max_idx}')

# The chain solver might be missing the fact that at tight radii,
# the distance function |P(theta) - P(theta_prev)| can have the FIRST solution
# with dtheta > 2π (bench wraps more than once)
# Let's check the distance function at very small r
print("\n=== Distance function at small r ===")
from spiral import spiral_point
a = B / (2*np.pi)
for r_head in [2.0, 1.5, 1.0, 0.8, 0.6, 0.5]:
    theta1 = r_head / a
    L = 3.41  # head bench
    # Find first crossing
    for theta2 in np.arange(theta1 + 0.01, theta1 + 20, 0.01):
        dtheta = theta2 - theta1
        dist = a * np.sqrt(theta1**2 + theta2**2 - 2*theta1*theta2*np.cos(dtheta))
        if dist >= L:
            print(f'  r={r_head:.2f}: first crossing at dtheta={dtheta:.4f} ({dtheta/(2*np.pi):.4f} turns)')
            break