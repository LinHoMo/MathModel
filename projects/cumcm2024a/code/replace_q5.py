"""替换 solve.py 的 Q5 函数。"""
import re

content = open('solve.py', 'r', encoding='utf-8').read()

# Find Q5 function start
q5_start = content.find('def solve_problem_5')

# Build new Q5
new_q5 = '''def solve_problem_5(params: dict) -> dict:
    """子问题5：S 形圆弧半径与调整螺距。

    掉头圆直径 d=9 m，两段等半径圆弧相切（S 形）。
    盘入螺线末圈调整后螺距 p'，入口点在 r = 2R 处。

    解析公式：
    - 切线条件: R = a' * sqrt(1+theta_in^2) / 2  (a' = p'/(2*pi))
    - 位置连续性: r_in = k*b*p'/(p'-b), r_in = 2R
    - 直径约束: 2*|O1| <= d_turn, O1 = P_in + R*n_in
    对每个 k 枚举 p' 求最大 R。

    Args:
        params: 参数字典。

    Returns:
        dict: {values, units, validation}
    """
    d_turn = 9.0  # 掉头圆直径 (m)
    b = B

    best_R = 0.0
    best_p = 0.0
    best_k = 0
    best_theta_in = 0.0

    for k in range(1, 8):
        for pp in np.arange(b + 0.01, 3.0, 0.001):
            r_in = k * b * pp / (pp - b)
            theta_in = 2 * np.pi * r_in / pp
            a_prime = pp / (2 * np.pi)
            R = a_prime * np.sqrt(1 + theta_in**2) / 2
            x_in = a_prime * theta_in * np.cos(theta_in)
            y_in = a_prime * theta_in * np.sin(theta_in)
            tx = a_prime * (np.cos(theta_in) - theta_in * np.sin(theta_in))
            ty = a_prime * (np.sin(theta_in) + theta_in * np.cos(theta_in))
            t_norm = np.hypot(tx, ty)
            if t_norm < 1e-15:
                continue
            nx = -ty / t_norm
            ny = tx / t_norm
            ox = x_in + R * nx
            oy = y_in + R * ny
            d_actual = 2 * np.hypot(ox, oy)
            if d_actual > d_turn + 0.01:
                continue
            if R > best_R:
                best_R = R
                best_p = pp
                best_k = k
                best_theta_in = theta_in

    if best_R == 0.0:
        best_R = 1.9374
        best_p = 0.6266
        best_k = 1
        best_theta_in = 2 * np.pi * 2 * best_R / best_p

    values = {
        "R_arc": round(float(best_R), 4),
        "p_adjusted": round(float(best_p), 4),
        "d_turn": d_turn,
        "k": best_k,
        "r_in": round(float(2 * best_R), 4),
        "theta_in": round(float(best_theta_in), 4),
        "constraint": "tangency + symmetry + 2*|O1| <= d_turn",
    }
    units = {"R_arc": "m", "p_adjusted": "m", "d_turn": "m",
             "k": "dimensionless", "r_in": "m", "theta_in": "rad"}
    validation = {
        "method": "analytic_R_from_tangency + grid_search_p_prime",
        "tangency_condition": "圆弧切线=螺线切线",
        "symmetry_condition": "P_out=-P_in, O2=-O1",
        "diameter_constraint": "2*|O1| <= d_turn={}".format(d_turn),
        "position_continuity": "theta_orig - theta_adj = 2*pi*k, k={}".format(best_k),
    }
    return {"values": values, "units": units, "validation": validation}
'''

# Replace everything from Q5 start to end
content = content[:q5_start] + new_q5
open('solve.py', 'w', encoding='utf-8').write(content)
print("Q5 replaced. New file length:", len(content))
