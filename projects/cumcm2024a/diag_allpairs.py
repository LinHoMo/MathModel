"""全对碰撞诊断：在 t=412.83 附近检查所有板凳对的线段距离。"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point
from chain import solve_chain_thetas
from solve import _build_L_list, _solve_kinematics, B, W, THETA_0, V1
from spiral import spiral_arc_length, inverse_arc_length

L_list = _build_L_list()
n = len(L_list)

def segment_distance(p1, p2, p3, p4):
    d = np.array(p2) - np.array(p1)
    e = np.array(p4) - np.array(p3)
    denom = np.dot(d,d)*np.dot(e,e) - np.dot(d,e)**2
    if abs(denom) < 1e-18:
        cands = [np.linalg.norm(np.array(p1)-np.array(p3)),
                 np.linalg.norm(np.array(p1)-np.array(p4)),
                 np.linalg.norm(np.array(p2)-np.array(p3)),
                 np.linalg.norm(np.array(p2)-np.array(p4))]
        return min(cands)
    diff = np.array(p3) - np.array(p1)
    t = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
    s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
    t = max(0, min(1, t))
    s = max(0, min(1, s))
    cx = np.array(p1) + t*d
    dx = np.array(p3) + s*e
    return np.linalg.norm(cx - dx)

# 测试多个时间点
for t_test in [400, 410, 412, 413, 415, 420]:
    _, _, theta_array = _solve_kinematics(t_test)
    positions = [spiral_point(t, B) for t in theta_array]
    
    min_dist = 1e9
    min_pair = (-1, -1)
    # 全对扫描（跳过相邻对 i, i+1）
    for i in range(n):
        for j in range(i+2, n):
            p1, p2 = positions[i], positions[i+1]
            p3, p4 = positions[j], positions[min(j+1, n)]
            dist = segment_distance(p1, p2, p3, p4)
            if dist < min_dist:
                min_dist = dist
                min_pair = (i, j)
    
    head_r = B * theta_array[0] / (2 * np.pi)
    print(f"t={t_test:4d}s  head_r={head_r:.4f}m  min_dist={min_dist:.6f}m  pair=({min_pair[0]},{min_pair[1]})  "
          f"r_i={B*theta_array[min_pair[0]]/(2*np.pi):.3f}  r_j={B*theta_array[min_pair[1]]/(2*np.pi):.3f}  "
          f"{'COLLIDE' if min_dist < W else 'ok'}")
