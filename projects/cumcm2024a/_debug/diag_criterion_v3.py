"""确认碰撞判据：题目原文说"相邻板凳夹角判据"和"非相邻板凳中心线距离判据"。

相邻板凳夹角判据：
  两节相邻板凳在铰接处的偏转角 α
  板凳侧面间距 = L_min * sin(α) 
  碰撞条件: L_min * sin(α) <= w

非相邻板凳中心线距离判据：
  两节非相邻板凳的中心线段最短距离
  碰撞条件: 距离 <= w

但我们的计算显示这两个判据都不触发碰撞！
- sin判据最小值 0.378m > 0.30m（在t=0时尾部i=220）
- 线段距离最小值 0.555m > 0.30m（恒定≈螺距）

问题出在哪里？

可能性1: 链式求解器把板凳排成"向外"方向，但盘入时龙头向内运动
  → 当龙头深入内圈时，最内圈的板凳可能"反向缠绕"
  → 我们的求解器只搜索 theta_i > theta_prev，但物理上 theta_i 可能 < theta_prev

可能性2: 碰撞发生在"同一圈"内不同板凳之间，不是相邻圈
  → 螺线弯曲处，同一圈内的板凳弯曲到一定程度时侧边接触

让我验证可能性1：当龙头到达极小半径时，链式求解是否应该允许 theta_i < theta_prev
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point, spiral_arc_length, inverse_arc_length, spiral_tangent_norm
from solve import _build_L_list, B, W, THETA_0, V1, L_HEAD, L_BODY

L_list = _build_L_list()
n = len(L_list)

# 检查 t=412.83s 时，龙头附近的板凳位置
s0 = spiral_arc_length(THETA_0, B)
s_target = max(0, s0 - V1 * 412.83)
theta_head = inverse_arc_length(s_target, B)

# 用现有求解器
from chain import solve_chain_thetas
theta_array = solve_chain_thetas(theta_head, L_list, B)
positions = [spiral_point(t, B) for t in theta_array]

# 打印龙头附近10节板凳的详细信息
print("=== 龙头附近板凳详情 (t=412.83s) ===")
print(f"{'handle':>6} {'theta':>10} {'r(m)':>8} {'x(m)':>10} {'y(m)':>10} {'dtheta':>10} {'turns':>8}")
for i in range(15):
    r = B * theta_array[i] / (2 * np.pi)
    x, y = positions[i]
    dtheta = theta_array[i+1] - theta_array[i] if i < n else 0
    turns = theta_array[i] / (2 * np.pi)
    print(f"{i:6d} {theta_array[i]:10.4f} {r:8.4f} {x:10.4f} {y:10.4f} {dtheta:10.4f} {turns:8.4f}")

# 关键检查：龙头板凳(L=3.41m)在 r=2.275m 处
# 螺线弧长 = a*sqrt(1+θ²)*dθ ≈ r*dθ (当θ大时)
# dθ ≈ L / (a*sqrt(1+θ²)) = L / (r*sqrt(1+1/θ²)) ≈ L/r
# 对于龙头: dθ ≈ 3.41/2.275 ≈ 1.499 rad ≈ 85.9°
# 这意味着龙头板凳跨越约 1.5 rad ≈ 0.24 圈！

# 检查龙头板凳的偏转角
print("\n=== 龙头板凳偏转角 ===")
for i in range(5):
    u_i = np.array(positions[i]) - np.array(positions[i+1])
    u_next = np.array(positions[i+2]) - np.array(positions[i+1])
    norm_i = np.linalg.norm(u_i)
    norm_next = np.linalg.norm(u_next)
    cos_a = -np.dot(u_i, u_next) / (norm_i * norm_next)
    cos_a = max(-1, min(1, cos_a))
    alpha = np.arccos(cos_a)
    sin_a = np.sin(alpha)
    L_min = min(L_list[i], L_list[i+1])
    gap = L_min * sin_a
    print(f"  bench {i}-{i+1}: alpha={np.degrees(alpha):.2f}°, sin={sin_a:.6f}, gap={gap:.6f}m, L_min={L_min}")

# 检查龙头板凳是否跨越多圈
print(f"\n龙头板凳 theta 跨度: {theta_array[1]-theta_array[0]:.4f} rad = {(theta_array[1]-theta_array[0])/(2*np.pi):.4f} 圈")
print(f"龙头板凳 theta_head={theta_array[0]:.4f}, theta_next={theta_array[1]:.4f}")
print(f"r_head={B*theta_array[0]/(2*np.pi):.4f}, r_next={B*theta_array[1]/(2*np.pi):.4f}")

# 检查偏转角最小的位置在哪里（不是头部，是哪里？）
print("\n=== 全链偏转角扫描 ===")
gaps = []
for i in range(n - 1):
    u_i = np.array(positions[i]) - np.array(positions[i+1])
    u_next = np.array(positions[i+2]) - np.array(positions[i+1])
    norm_i = np.linalg.norm(u_i)
    norm_next = np.linalg.norm(u_next)
    if norm_i < 1e-15 or norm_next < 1e-15:
        continue
    cos_a = -np.dot(u_i, u_next) / (norm_i * norm_next)
    cos_a = max(-1, min(1, cos_a))
    alpha = np.arccos(cos_a)
    sin_a = np.sin(alpha)
    L_min = min(L_list[i], L_list[i+1])
    gap = L_min * sin_a
    r_i = B * theta_array[i] / (2 * np.pi)
    gaps.append((gap, i, alpha, r_i))

gaps.sort()
print("最小 gap 的 20 个位置:")
for gap, i, alpha, r_i in gaps[:20]:
    print(f"  i={i:3d}  gap={gap:.6f}m  alpha={np.degrees(alpha):.3f}°  r={r_i:.4f}m  L={L_list[i]}")

# 问题核心：当龙头 r=2.275m, dθ≈1.5 rad
# 这意味着龙头板凳跨越 ~0.24 圈
# 如果龙头继续向内（r更小），dθ更大，板凳跨越更多圈
# 当 r 小到一定程度，dθ > 2π，板凳"绕了一圈回到自己"→ 碰撞！

# 检查 dθ > 2π 的情况
print("\n=== dθ 接近或超过 2π 的板凳 ===")
for i in range(n):
    dtheta = theta_array[i+1] - theta_array[i]
    if dtheta > np.pi:  # 超过半圈
        r_i = B * theta_array[i] / (2 * np.pi)
        print(f"  i={i:3d}  dθ={dtheta:.4f} ({dtheta/(2*np.pi):.4f} 圈)  r={r_i:.4f}m  L={L_list[i]}")

# 如果没有 dθ > π 的，说明在 t=412.83s 时还没到那么极端
# 那碰撞判据到底是什么？
# 让我检查：是不是碰撞发生在"龙头板凳"和"相邻圈的板凳"之间
# 龙头板凳 H0->H1 跨越 dθ≈1.5 rad
# 相邻圈（差2π）的板凳在 theta_0 + 2π 附近
print("\n=== 龙头板凳与相邻圈板凳的距离 ===")
theta_0 = theta_array[0]
# 找到 theta ≈ theta_0 + 2π 的板凳
for i in range(1, n):
    if abs(theta_array[i] - (theta_0 + 2*np.pi)) < 1.0:
        dist = np.linalg.norm(np.array(positions[0]) - np.array(positions[i]))
        seg_d = None
        # 线段距离
        p1, p2 = np.array(positions[0]), np.array(positions[1])
        p3, p4 = np.array(positions[i]), np.array(positions[min(i+1,n)])
        d = p2 - p1
        e = p4 - p3
        denom = np.dot(d,d)*np.dot(e,e) - np.dot(d,e)**2
        if abs(denom) > 1e-18:
            diff = p3 - p1
            t_ = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
            s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
            t_ = max(0, min(1, t_))
            s = max(0, min(1, s))
            cx = p1 + t_*d
            dx = p3 + s*e
            seg_d = np.linalg.norm(cx - dx)
        print(f"  bench {i}: theta={theta_array[i]:.4f} (target={theta_0+2*np.pi:.4f})  "
              f"r={B*theta_array[i]/(2*np.pi):.4f}  seg_dist={seg_d:.6f}m  {'COLLIDE' if seg_d and seg_d < W else ''}")
        break
