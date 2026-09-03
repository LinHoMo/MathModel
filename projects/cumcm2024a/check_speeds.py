import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point, spiral_arc_length, inverse_arc_length, spiral_tangent, spiral_tangent_norm, dtheta_dt_head
from chain import solve_chain_thetas, chain_velocities
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

# t=412.83
s0 = spiral_arc_length(THETA_0, B)
s_target = max(0, s0 - V1 * 412.83)
theta_head = inverse_arc_length(s_target, B)
theta_array = solve_chain_thetas(theta_head, L_list, B)
dth_head = dtheta_dt_head(theta_head, V1, B)
speeds = chain_velocities(theta_array, dth_head, B)

print(f"dtheta_head = {dth_head:.6f}")
print(f"theta_head = {theta_head:.4f}")
print(f"theta_tail = {theta_array[-1]:.4f}")

print("\nSpeeds at t=412.83:")
for i in range(min(10, len(speeds))):
    print(f"  handle {i}: speed={speeds[i]:.6f} m/s, theta={theta_array[i]:.4f}")

print(f"\nMax speed = {np.max(speeds):.6f} at handle {np.argmax(speeds)}")
print(f"Min speed = {np.min(speeds):.6f} at handle {np.argmin(speeds)}")

# Check t=407 (where max speed occurs according to solve.py)
print("\n\n=== t=407 (unwinding max speed reference) ===")
# For unwinding, different kinematics
# But let's check winding speeds at various times
print("\nWinding max speeds over time:")
for t in [0, 100, 200, 300, 350, 360, 370, 380, 390, 400, 410, 412.83, 420]:
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    dth_head = dtheta_dt_head(theta_head, V1, B)
    speeds = chain_velocities(theta_array, dth_head, B)
    max_spd = np.max(speeds)
    max_h = np.argmax(speeds)
    print(f"  t={t:4d}: max_speed={max_spd:.6f} at handle {max_h}, head_speed={speeds[0]:.6f}")