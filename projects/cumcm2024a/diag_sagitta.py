"""验证 sagitta 碰撞判据：板凳弦线偏离螺线弧的垂度 > b - w 时碰撞。

物理推导：
- 板凳是矩形 w×L，中心线是螺线上两把手的弦
- 弦偏离弧的最大距离（垂度）= r*(1-cos(Δθ/2))
- 板凳内边缘偏离 = sagitta + w/2
- 相邻内圈板凳外边缘在 r-b+w/2 处
- 碰撞条件: r - sagitta - w/2 < r - b + w/2
  即 sagitta > b - w = 0.55 - 0.30 = 0.25m
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point, spiral_arc_length, inverse_arc_length
from chain import solve_chain_thetas
from solve import _build_L_list, B, W, THETA_0, V1

L_list = _build_L_list()

def max_sagitta(theta_array, L_list, b=0.55):
    """计算所有板凳的最大垂度。"""
    n = len(L_list)
    max_sag = 0.0
    max_i = -1
    for i in range(n):
        theta_a = theta_array[i]
        theta_b = theta_array[i + 1]
        r_a = b * theta_a / (2 * np.pi)
        r_b = b * theta_b / (2 * np.pi)
        r_mid = (r_a + r_b) / 2.0
        dtheta = abs(theta_b - theta_a)
        sag = r_mid * (1.0 - np.cos(dtheta / 2.0))
        if sag > max_sag:
            max_sag = sag
            max_i = i
    return max_sag, max_i

threshold = B - W  # 0.25m
print(f"碰撞阈值: sagitta > {threshold}m (b-w = {B}-{W})")
print()
print("t(s)    head_r(m)  max_sag(m)  bench_i  r_bench(m)  collides?")
print("-" * 75)

# 粗扫
t_collision = None
for t in range(0, 601, 10):
    s0 = spiral_arc_length(THETA_0, B)
    s_target = s0 - V1 * t
    if s_target < 0:
        s_target = 0.0
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    
    sag, idx = max_sagitta(theta_array, L_list, B)
    head_r = B * theta_array[0] / (2 * np.pi)
    bench_r = B * theta_array[idx] / (2 * np.pi)
    collides = sag > threshold
    flag = " <===" if collides else ""
    if collides and t_collision is None:
        t_collision = t
    print(f"{t:4d}    {head_r:8.4f}   {sag:10.6f}   {idx:3d}     {bench_r:8.4f}    {'YES' if collides else 'no'}{flag}")

# 二分细化
if t_collision:
    print(f"\n粗扫碰撞区间: [{t_collision-10}, {t_collision}]")
    t_lo, t_hi = t_collision - 10, t_collision
    for _ in range(50):
        t_mid = (t_lo + t_hi) / 2.0
        s0 = spiral_arc_length(THETA_0, B)
        s_target = max(0, s0 - V1 * t_mid)
        theta_head = inverse_arc_length(s_target, B)
        theta_array = solve_chain_thetas(theta_head, L_list, B)
        sag, idx = max_sagitta(theta_array, L_list, B)
        if sag > threshold:
            t_hi = t_mid
        else:
            t_lo = t_mid
    t_star = (t_lo + t_hi) / 2.0
    s0 = spiral_arc_length(THETA_0, B)
    s_target = max(0, s0 - V1 * t_star)
    theta_head = inverse_arc_length(s_target, B)
    theta_array = solve_chain_thetas(theta_head, L_list, B)
    head_r = B * theta_array[0] / (2 * np.pi)
    sag, idx = max_sagitta(theta_array, L_list, B)
    print(f"t* = {t_star:.2f}s")
    print(f"head_r = {head_r:.6f}m")
    print(f"d_min = 2*head_r = {2*head_r:.6f}m")
    print(f"max_sagitta = {sag:.6f}m (threshold={threshold})")
    print(f"collision at bench {idx}, r={B*theta_array[idx]/(2*np.pi):.4f}m")
else:
    print("\n未检测到碰撞！")
