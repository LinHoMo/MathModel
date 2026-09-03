import sys, os, numpy as np
sys.path.insert(0, r'C:\Users\Lin\Desktop\Programs\MathModel\projects\cumcm2024a\code')
from spiral import spiral_point
from solve import B

# Check distance function for second bench at t=412.83
theta1 = 27.6167  # bench 1 handle
L = 2.20  # body bench length
a = B / (2*np.pi)

print(f'theta1={theta1:.4f}, L={L}')
print('theta2    r2      dist')
for theta2 in np.arange(theta1 + 0.1, theta1 + 10, 0.2):
    r1 = a * theta1
    r2 = a * theta2
    dtheta = theta2 - theta1
    dist = a * np.sqrt(theta1**2 + theta2**2 - 2*theta1*theta2*np.cos(dtheta))
    mark = ">=L" if dist >= L else ""
    print(f'{theta2:.2f}  {r2:.4f}  {dist:.4f}  {mark}')

# Check for multiple crossings
print('\nChecking for multiple solutions...')
prev_dist = 0
for theta2 in np.arange(theta1 + 0.01, theta1 + 20, 0.01):
    r1 = a * theta1
    r2 = a * theta2
    dtheta = theta2 - theta1
    dist = a * np.sqrt(theta1**2 + theta2**2 - 2*theta1*theta2*np.cos(dtheta))
    if (dist - L) * (prev_dist - L) < 0:
        print(f'  Crossing near theta2={theta2:.4f}, dist={dist:.4f}')
    prev_dist = dist