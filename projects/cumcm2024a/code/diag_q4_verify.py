"""验证盘出 'increasing'（龙身在外圈）方向的速度放大是否正确。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spiral import (spiral_arc_length, inverse_arc_length, spiral_tangent_norm,
                    spiral_point, spiral_r)
from chain import chain_velocities
from solve import B, V1, THETA_0, N_BENCH, _build_L_list, solve_problem_3


def solve_chain_increasing(theta_head, L_list, b=B, delta=0.5, tol=1e-10):
    n = len(L_list)
    ta = np.zeros(n + 1)
    ta[0] = theta_head
    for i in range(1, n + 1):
        tp = ta[i - 1]
        L = L_list[i - 1]
        lo = tp + 1e-12
        hi = tp + delta
        for _ in range(50):
            xhi, yhi = spiral_point(hi, b)
            xlo, ylo = spiral_point(lo, b)
            if np.hypot(xhi - xlo, yhi - ylo) >= L:
                break
            hi += delta
        for _ in range(200):
            mid = (lo + hi) / 2.0
            xm, ym = spiral_point(mid, b)
            xp, yp = spiral_point(tp, b)
            d = np.hypot(xm - xp, ym - yp)
            if abs(d - L) < tol:
                break
            if d < L:
                lo = mid
            else:
                hi = mid
        ta[i] = (lo + hi) / 2.0
    return ta


a = B / (2.0 * np.pi)
q3 = solve_problem_3({})
r_start = q3["values"]["r_collision"]
th_start = r_start / a
L_list = _build_L_list()
s0 = spiral_arc_length(th_start, B)

print("r_start={:.6f} th_start={:.6f} a={:.8f}".format(r_start, th_start, a))

for t in [0, 100, 200, 300, 400, 407, 412, 500, 600]:
    st = s0 + V1 * t
    thh = inverse_arc_length(st, B)
    ta = solve_chain_increasing(thh, L_list, B)
    dth = V1 / spiral_tangent_norm(thh, B)
    sp = chain_velocities(ta, dth, B)
    i = int(np.argmax(sp))
    print("t={:4d} head_r={:6.3f}(th={:6.2f}) tail_r={:6.3f}(th={:6.2f}) "
          "head_v={:.4f} tail_v={:.4f} max_v={:.4f}@h{}".format(
        t, spiral_r(thh, B), thh, spiral_r(ta[-1], B), ta[-1],
        sp[0], sp[-1], sp.max(), i))