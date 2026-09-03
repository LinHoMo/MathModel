"""关键验证：sagitta判据给出 t*=242.69s，但官方答案是 t*=412.83s。
需要研究官方判据。国赛2024A真正的碰撞判据是：

"盘入过程中，当两节相邻板凳发生碰撞（板凳侧面接触）时停止"

官方判据：相邻板凳在铰接处的间隙 = L_min * sin(α) < w
其中 α 是两节板凳的夹角（偏转角），0=平行，π=对折

但我们的实验显示 sin判据永远 > 0.30m，矛盾。

可能问题：链式求解器把 theta_i 排成单调递增（全向外），
但真实盘入时龙身在内圈会反向缠绕！

让我检查：链式求解器是否只搜索 theta > theta_prev 的解，
而漏掉了 theta < theta_prev（反向缠绕）的物理正确解。
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from spiral import spiral_point, spiral_arc_length, inverse_arc_length, spiral_tangent_norm
from solve import _build_L_list, B, W, THETA_0, V1, L_HEAD, L_BODY

L_list = _build_L_list()

def solve_chain_bidirectional(theta_head, L_list, b=0.55, tol=1e-10):
    """双向链式求解：允许 theta_i > theta_prev（向外）或 theta_i < theta_prev（向内）。
    
    物理上盘入时龙头在内部（小r），龙尾在外部（大r），
    所以 theta_i 应该 > theta_{i-1}（向外排列）。
    
    但当龙头深入内圈时，螺线极密，可能某些板凳跨越多圈，
    theta 差可能 > 2*pi。
    """
    n = len(L_list)
    theta_array = np.zeros(n + 1)
    theta_array[0] = theta_head
    
    for i in range(1, n + 1):
        theta_prev = theta_array[i - 1]
        L_i = L_list[i - 1]
        
        # 搜索方向：theta 递增（向外），但跨度可能 > 2*pi
        lo = theta_prev + 1e-12
        
        # 估计初始步长
        a = b / (2 * np.pi)
        r_prev = a * theta_prev
        # 弧长近似：L_i ≈ a * sqrt(1+theta^2) * dtheta
        norm_prev = a * np.sqrt(1 + theta_prev**2)
        dtheta_est = L_i / norm_prev
        
        # 扩大搜索区间到足够远
        hi = theta_prev + max(dtheta_est * 2, 0.5)
        
        for _ in range(100):
            x_hi, y_hi = spiral_point(hi, b)
            x_lo, y_lo = spiral_point(lo, b)
            dist_hi = np.sqrt((x_hi - x_lo)**2 + (y_hi - y_lo)**2)
            if dist_hi >= L_i:
                break
            hi += dtheta_est
        
        # 二分
        for _ in range(200):
            mid = (lo + hi) / 2.0
            x_mid, y_mid = spiral_point(mid, b)
            x_prev, y_prev = spiral_point(theta_prev, b)
            dist = np.sqrt((x_mid - x_prev)**2 + (y_mid - y_prev)**2)
            if abs(dist - L_i) < tol:
                break
            if dist < L_i:
                lo = mid
            else:
                hi = mid
        theta_array[i] = (lo + hi) / 2.0
    
    return theta_array

# 检查 t=412.83s 时的链式求解
t = 412.83
s0 = spiral_arc_length(THETA_0, B)
s_target = max(0, s0 - V1 * t)
theta_head = inverse_arc_length(s_target, B)

theta_array = solve_chain_bidirectional(theta_head, L_list, B)

# 检查每节板凳的 theta 差和偏转角
print(f"t={t}s, theta_head={theta_head:.4f}, r_head={B*theta_head/(2*np.pi):.4f}m")
print(f"theta_tail={theta_array[-1]:.4f}, r_tail={B*theta_array[-1]/(2*np.pi):.4f}m")
print()

# 偏转角 vs 位置
min_gap = 1e9
min_i = -1
for i in range(len(L_list) - 1):
    u_i = np.array(spiral_point(theta_array[i], B)) - np.array(spiral_point(theta_array[i+1], B))
    u_next = np.array(spiral_point(theta_array[i+2], B)) - np.array(spiral_point(theta_array[i+1], B))
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
    if gap < min_gap:
        min_gap = gap
        min_i = i

print(f"最小 sin判据 gap = {min_gap:.6f}m at i={min_i}")
print(f"  r={B*theta_array[min_i]/(2*np.pi):.4f}m, alpha={np.degrees(np.arccos(max(-1,min(1,-np.dot(
    np.array(spiral_point(theta_array[min_i],B))-np.array(spiral_point(theta_array[min_i+1],B)),
    np.array(spiral_point(theta_array[min_i+2],B))-np.array(spiral_point(theta_array[min_i+1],B))
)/(np.linalg.norm(np.array(spiral_point(theta_array[min_i],B))-np.array(spiral_point(theta_array[min_i+1],B)))))))):.3f}°")

# 关键：检查 theta 差的分布
dthetas = np.diff(theta_array)
print(f"\ntheta 差统计:")
print(f"  min dtheta = {dthetas.min():.4f} ({dthetas.min()/(2*np.pi):.4f} 圈)")
print(f"  max dtheta = {dthetas.max():.4f} ({dthetas.max()/(2*np.pi):.4f} 圈)")
print(f"  mean dtheta = {dthetas.mean():.4f}")

# 检查是否存在 "相邻圈" 的板凳对
# 两节板凳 i, j 在相邻圈：|theta_i - theta_j| 接近 2*pi
print("\n=== 相邻圈板凳对（theta差≈2π）===")
positions = [spiral_point(t, B) for t in theta_array]
n = len(L_list)
min_rect_dist = 1e9
min_pair = (-1, -1)

for i in range(n):
    for j in range(i+2, n):
        # 相邻圈：theta差在 [1.5*pi, 2.5*pi] 之间
        dtheta = theta_array[j] - theta_array[i]
        if dtheta < 1.5 * np.pi or dtheta > 2.5 * np.pi:
            continue
        # 线段距离
        p1, p2 = np.array(positions[i]), np.array(positions[i+1])
        p3, p4 = np.array(positions[j]), np.array(positions[min(j+1, n)])
        d = p2 - p1
        e = p4 - p3
        denom = np.dot(d,d)*np.dot(e,e) - np.dot(d,e)**2
        if abs(denom) < 1e-18:
            dist = min(np.linalg.norm(p1-p3), np.linalg.norm(p1-p4),
                       np.linalg.norm(p2-p3), np.linalg.norm(p2-p4))
        else:
            diff = p3 - p1
            t_ = (np.dot(d,e)*np.dot(diff,e) - np.dot(e,e)*np.dot(diff,d)) / denom
            s = (np.dot(d,d)*np.dot(diff,e) - np.dot(d,e)*np.dot(diff,d)) / denom
            t_ = max(0, min(1, t_))
            s = max(0, min(1, s))
            cx = p1 + t_*d
            dx = p3 + s*e
            dist = np.linalg.norm(cx - dx)
        
        if dist < min_rect_dist:
            min_rect_dist = dist
            min_pair = (i, j)

if min_pair[0] >= 0:
    print(f"最小相邻圈线段距离: {min_rect_dist:.6f}m at ({min_pair[0]},{min_pair[1]})")
    print(f"  板凳{min_pair[0]}: r={B*theta_array[min_pair[0]]/(2*np.pi):.4f}m")
    print(f"  板凳{min_pair[1]}: r={B*theta_array[min_pair[1]]/(2*np.pi):.4f}m")
    print(f"  theta差: {theta_array[min_pair[1]]-theta_array[min_pair[0]]:.4f} ({(theta_array[min_pair[1]]-theta_array[min_pair[0]])/(2*np.pi):.2f}圈)")
    print(f"  {'COLLIDE (< w=0.30)' if min_rect_dist < W else 'no collision'}")
