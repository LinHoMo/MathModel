"""对抗性交叉检验：不采信任何一方，独立验证三个命题。

命题 A  两站失效窗 = (90°, 90°+2ε)，且窗宽与站距无关
命题 B  若源距 R 已知，GDOP 准则「χ=90° 最优」是否成立
命题 C  若源距 R 未知，最优角是否随先验漂移（即「30°」是先验相关的，不是物理常数）
"""
import math

EPS_DEF = 1.0


# ---------------- 几何内核（与 harness 同构，独立重写） ----------------
def _dir(a):
    r = math.radians(a)
    return math.cos(r), math.sin(r)


def wedge_hp(sx, sy, th, eps):
    out = []
    for ang in (th - eps, th + eps):
        dx, dy = _dir(ang)
        a, b = -dy, dx
        out.append((a, b, a * sx + b * sy))
    return [(out[0][0], out[0][1], out[0][2], "ge"),
            (out[1][0], out[1][1], out[1][2], "le")]


def clip(poly, a, b, c, sense, tol=1e-9):
    if not poly:
        return []
    def ins(p):
        v = a * p[0] + b * p[1]
        return v >= c - tol if sense == "ge" else v <= c + tol
    def inter(p, q):
        fp = a * p[0] + b * p[1] - c
        fq = a * q[0] + b * q[1] - c
        t = fp / (fp - fq) if (fp - fq) != 0 else 0.0
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
    out, n = [], len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        pi, qi = ins(p), ins(q)
        if pi:
            out.append(p)
        if pi != qi:
            out.append(inter(p, q))
    return out


def region(pts, bears, eps, bbox=9000.0):
    poly = [(-bbox, -bbox), (bbox, -bbox), (bbox, bbox), (-bbox, bbox)]
    for (sx, sy), th in zip(pts, bears):
        for (a, b, c, s) in wedge_hp(sx, sy, th, eps):
            poly = clip(poly, a, b, c, s)
            if len(poly) < 3:
                return poly
    return poly


def hull(P):
    P = sorted(set((round(x, 9), round(y, 9)) for x, y in P))
    if len(P) <= 2:
        return P
    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    up = []
    for p in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def diam(V):
    H = hull(V)
    best = 0.0
    for i in range(len(H)):
        for j in range(i + 1, len(H)):
            d = math.dist(H[i], H[j])
            if d > best:
                best = d
    return best, H


def covers(V):
    """(V-A)·(V-B) ≤ 0 判据，阈值按 D^2 定标。"""
    if len(V) < 3:
        return None
    H = hull(V)
    D, pair = 0.0, None
    for i in range(len(H)):
        for j in range(i + 1, len(H)):
            d = math.dist(H[i], H[j])
            if d > D:
                D, pair = d, (H[i], H[j])
    A, B = pair
    thr = 1e-12 * D * D
    return all((v[0] - A[0]) * (v[0] - B[0]) + (v[1] - A[1]) * (v[1] - B[1]) <= thr
               for v in H)


def bear(x1, y1, x2, y2):
    return math.degrees(math.atan2(y2 - y1, x2 - x1)) % 360.0


def bdiff(b1, b2):
    return abs(((b1 - b2 + 180.0) % 360.0) - 180.0)


def two_station_chi_config(chi, t1, t2, eps):
    """交点在原点、两站位于各自示向度直线反向延长线；交点处夹角恒 = chi。"""
    S1 = (-t1, 0.0)
    a = math.radians(chi)
    S2 = (-t2 * math.cos(a), t2 * math.sin(a))
    b1 = bear(S1[0], S1[1], 0.0, 0.0)
    b2 = bear(S2[0], S2[1], 0.0, 0.0)
    return S1, S2, b1, b2


# ---------------- 命题 A ----------------
def test_A():
    print("=" * 74)
    print("命题 A：两站失效窗 = (90°, 90°+2ε)，且与站距无关")
    ts = [3.0, 40.0, 1000.0]
    for eps in (0.25, 0.5, 1.0, 2.0):
        lo = hi = None
        chi = 88.0
        step = 0.01
        flag_rows = []
        while chi <= 90.0 + 2 * eps + 1.0 + 1e-9:
            res = set()
            for t1 in ts:
                for t2 in ts:
                    S1, S2, b1, b2 = two_station_chi_config(chi, t1, t2, eps)
                    reg = region([S1, S2], [b1, b2], eps)
                    if len(reg) < 3:
                        res.add(None)
                        continue
                    res.add(covers(reg))
            flag_rows.append((chi, res))
            chi += step
        bad = [c for c, r in flag_rows if len(r - {None}) > 1]
        fail = sorted(c for c, r in flag_rows if False in r)
        if fail:
            lo, hi = fail[0], fail[-1]
        width = (hi - lo) if (lo is not None) else float("nan")
        print(f"  ε={eps:>4}°  失效窗=({lo}, {hi})  窗宽={width:.2f}°  "
              f"2ε={2*eps}°  站距矛盾行={len(bad)}")
    # 站距无关性
    print("  站距无关性复核（ε=1°，χ=91°，t1,t2 ∈ {1,3,10,40,200,1000} 共 36 组）：")
    res = set()
    for t1 in (1, 3, 10, 40, 200, 1000):
        for t2 in (1, 3, 10, 40, 200, 1000):
            S1, S2, b1, b2 = two_station_chi_config(91.0, t1, t2, 1.0)
            reg = region([S1, S2], [b1, b2], 1.0)
            if len(reg) >= 3:
                res.add(covers(reg))
    print(f"    36 组覆盖结论集合 = {res}  ->  {'与站距无关' if len(res)==1 else '与站距有关'}")
    res2 = set()
    for t1 in (1, 3, 10, 40, 200, 1000):
        for t2 in (1, 3, 10, 40, 200, 1000):
            S1, S2, b1, b2 = two_station_chi_config(95.0, t1, t2, 1.0)
            reg = region([S1, S2], [b1, b2], 1.0)
            if len(reg) >= 3:
                res2.add(covers(reg))
    print(f"    χ=95°（窗外）36 组覆盖结论集合 = {res2}")


# ---------------- 命题 B / C 公共积分 ----------------
def gl(n):
    xs, ws = [], []
    for i in range(1, n + 1):
        x = math.cos(math.pi * (i - 0.25) / (n + 0.5))
        dp = 1.0
        for _ in range(100):
            p0, p1 = 1.0, 0.0
            for k in range(1, n + 1):
                p2, p1 = p1, p0
                p0 = ((2 * k - 1) * x * p1 - (k - 1) * p2) / k
            dp = n * (x * p0 - p1) / (x * x - 1)
            dx = -p0 / dp
            x += dx
            if abs(dx) < 1e-14:
                break
        xs.append(x)
        ws.append(2.0 / ((1 - x * x) * dp * dp))
    return xs, ws


def D_of(psi, d, R, d1, d2, rg, eps=EPS_DEF):
    gx = R * math.cos(math.radians(-d1))
    gy = R * math.sin(math.radians(-d1))
    S2 = (d * math.cos(math.radians(psi)), d * math.sin(math.radians(psi)))
    if math.dist(S2, (gx, gy)) > rg:
        return math.sqrt(rg * rg - 10 * rg * math.cos(math.radians(eps)) + 25), True
    th2 = math.degrees(math.atan2(gy - S2[1], gx - S2[0])) + d2
    reg = region([(0.0, 0.0), S2], [0.0, th2], eps)
    if len(reg) < 3:
        return math.sqrt(rg * rg - 10 * rg * math.cos(math.radians(eps)) + 25), True
    return diam(reg)[0], False


def ED(psi, d, prior, nR=24, nd=9, nrg=5, eps=EPS_DEF):
    """prior: ('fixed', R) 或 ('area', lo, hi) 或 ('unif', lo, hi)"""
    xr, wr = gl(nR)
    xd, wd = gl(nd)
    xg, wg = gl(nrg)
    tot = wt = fw = 0.0
    if prior[0] == "fixed":
        Rs = [(prior[1], 1.0)]
    else:
        _, lo, hi = prior
        Rs = []
        for i in range(nR):
            R = lo + (hi - lo) * 0.5 * (xr[i] + 1.0)
            w = wr[i] * 0.5 * (hi - lo)
            if prior[0] == "area":
                w *= 2 * R / (hi ** 2 - lo ** 2)
            else:
                w *= 1.0 / (hi - lo)
            Rs.append((R, w))
    for R, wR in Rs:
        rlo, rhi = max(1000.0, R), 1500.0
        for a in range(nd):
            d1 = eps * xd[a]
            w1 = wd[a] * 0.5
            for b in range(nd):
                d2 = eps * xd[b]
                w2 = wd[b] * 0.5
                acc = 0.0
                if rhi > rlo:
                    for g in range(nrg):
                        rg = rlo + (rhi - rlo) * 0.5 * (xg[g] + 1.0)
                        acc += wg[g] * 0.5 * D_of(psi, d, R, d1, d2, rg, eps)[0]
                        fw += wR * w1 * w2 * wg[g] * 0.5 * (
                            1.0 if D_of(psi, d, R, d1, d2, rg, eps)[1] else 0.0)
                else:
                    v, f = D_of(psi, d, R, d1, d2, rlo, eps)
                    acc = v
                    fw += wR * w1 * w2 * (1.0 if f else 0.0)
                tot += wR * w1 * w2 * acc
                wt += wR * w1 * w2
    return tot / wt, fw / wt


def chi_at_est(psi, d, R):
    """以估计源 G' = 两测得射线交点（δ=0 时即真源）计算的源端交会角。"""
    gx, gy = R, 0.0
    S2 = (d * math.cos(math.radians(psi)), d * math.sin(math.radians(psi)))
    A = math.atan2(0 - gy, 0 - gx)
    B = math.atan2(S2[1] - gy, S2[0] - gx)
    return bdiff(math.degrees(A) % 360, math.degrees(B) % 360)


def test_B():
    print()
    print("=" * 74)
    print("命题 B：源距 R 已知时，GDOP 准则「χ=90° 最优」是否成立？")
    print("  （R=1200 固定，δ1,δ2~U(-1°,1°)，r_G~U[1200,1500]，精确半平面交）")
    rows = []
    for psi in (20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0):
        row = []
        for d in (900.0, 1200.0, 1500.0, 1697.0):
            e, f = ED(psi, d, ("fixed", 1200.0), nR=1, nd=9, nrg=5)
            row.append((d, e, f))
        rows.append((psi, row))
        print("  ψ=%5.1f  " % psi + "  ".join(
            f"d={d:6.0f}:{e:8.2f}({f*100:5.2f}%)" for d, e, f in row))
    best = min(((e, psi, d, f) for psi, row in rows for d, e, f in row))
    print(f"  网格最小 E[D]={best[0]:.3f} m @ ψ={best[1]}°, d={best[2]:.0f} m")
    print(f"    该点源端交会角 χ(R=1200) = {chi_at_est(best[1], best[2], 1200.0):.2f}°")
    print(f"  对照：ψ=45°,d=1697（harness 垂线偏移=1200）χ = "
          f"{chi_at_est(45.0, 1697.06, 1200.0):.2f}°  "
          f"E[D]={ED(45.0,1697.06,('fixed',1200.0),nR=1,nd=9,nrg=5)[0]:.3f} m")


def test_C():
    print()
    print("=" * 74)
    print("命题 C：源距 R 未知时，最优角是否随先验漂移？")
    priors = [("面积均匀", ("area", 5.0, 1500.0)),
              ("r 均匀", ("unif", 5.0, 1500.0)),
              ("远距 r 均匀", ("unif", 1000.0, 1500.0))]
    for pname, pr in priors:
        best = None
        for psi in (20.0, 25.0, 30.0, 35.0, 40.0, 45.0):
            for d in (1000.0, 1150.0, 1300.0):
                e, f = ED(psi, d, pr, nR=20, nd=7, nrg=3)
                if best is None or e < best[0]:
                    best = (e, psi, d, f)
        print(f"  {pname:<12} -> 最优 ψ*={best[1]:5.1f}°  d*={best[2]:6.0f} m  "
              f"E[D]={best[0]:7.3f} m  失效={best[3]*100:.3f}%")
    print("  -> 若 ψ* 随先验明显漂移，则任何单一「最优角」都不是物理常数，"
          "必须报候选区 + 先验灵敏度")


if __name__ == "__main__":
    test_A()
    test_B()
    test_C()
