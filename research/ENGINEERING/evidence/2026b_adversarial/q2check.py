"""Q2 策略对拍：同一先验下比较 harness 推荐点与答案稿推荐点的 E[D]。

设置（与 Q1Q2_最终答案稿 §2.3 一致）：
  S1 在原点，转动坐标使测得示向度 theta1 = 0；
  真源 G = R*(cos(-d1), sin(-d1))，R 面积均匀 [5,1500]；
  d1,d2 ~ U(-1,1) 度；r_G ~ U[max(1000,R), 1500]；
  S2 = d*(cos psi, sin psi)（psi 相对测得示向度）；
  |S2-G| > r_G 时第二次测量失败 -> 单站扇形，D_fan(r_G)。
  D 由精确半平面交给出。
"""
import math

EPS = 1.0
RMAX = 1500.0
RMIN = 5.0


def _dir(a):
    r = math.radians(a)
    return math.cos(r), math.sin(r)


def wedge_hp(sx, sy, th, eps):
    out = []
    for ang in (th - eps, th + eps):
        dx, dy = _dir(ang)
        a, b = -dy, dx
        c = a * sx + b * sy
        out.append((a, b, c))
    return [(out[0][0], out[0][1], out[0][2], "ge"),
            (out[1][0], out[1][1], out[1][2], "le")]


def clip(poly, a, b, c, sense):
    if not poly:
        return []
    tol = 1e-9

    def ins(p):
        v = a * p[0] + b * p[1]
        return v >= c - tol if sense == "ge" else v <= c + tol

    def inter(p, q):
        fp = a * p[0] + b * p[1] - c
        fq = a * q[0] + b * q[1] - c
        t = fp / (fp - fq) if (fp - fq) != 0 else 0.0
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))

    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        pi, qi = ins(p), ins(q)
        if pi:
            out.append(p)
        if pi != qi:
            out.append(inter(p, q))
    return out


def region(pts, bears, eps=EPS, bbox=9000.0):
    poly = [(-bbox, -bbox), (bbox, -bbox), (bbox, bbox), (-bbox, bbox)]
    for (sx, sy), th in zip(pts, bears):
        for (a, b, c, s) in wedge_hp(sx, sy, th, eps):
            poly = clip(poly, a, b, c, s)
            if len(poly) < 3:
                return poly
    return poly


def hull(pts):
    P = sorted(set((round(x, 9), round(y, 9)) for x, y in pts))
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
    if len(H) < 2:
        return 0.0
    best = 0.0
    for i in range(len(H)):
        for j in range(i + 1, len(H)):
            d = math.dist(H[i], H[j])
            if d > best:
                best = d
    return best


def D_fan(rg):
    return math.sqrt(rg * rg - 10.0 * rg * math.cos(math.radians(EPS)) + 25.0)


def D_of(psi_deg, d, R, d1, d2, rg):
    """定位区域直径（精确半平面交；失败时退化为单站扇形）。"""
    gx = R * math.cos(math.radians(-d1))
    gy = R * math.sin(math.radians(-d1))
    S2 = (d * math.cos(math.radians(psi_deg)), d * math.sin(math.radians(psi_deg)))
    if math.dist(S2, (gx, gy)) > rg:
        return D_fan(rg), True
    th2 = math.degrees(math.atan2(gy - S2[1], gx - S2[0])) + d2
    reg = region([(0.0, 0.0), S2], [0.0, th2])
    if len(reg) < 3:
        return D_fan(rg), True          # 无界/退化兜底
    return diam(reg), False


def gauss_legendre(n):
    # Newton on Legendre polynomials
    xs, ws = [], []
    for i in range(1, n + 1):
        x = math.cos(math.pi * (i - 0.25) / (n + 0.5))
        for _ in range(100):
            p0, p1 = 1.0, 0.0
            for k in range(1, n + 1):
                p2 = p1
                p1 = p0
                p0 = ((2 * k - 1) * x * p1 - (k - 1) * p2) / k
            dp = n * (x * p0 - p1) / (x * x - 1)
            dx = -p0 / dp
            x += dx
            if abs(dx) < 1e-14:
                break
        xs.append(x)
        ws.append(2.0 / ((1 - x * x) * dp * dp))
    return xs, ws


def evaluate(psi_deg, d, nR=48, nd=13, nrg=9):
    """返回 (E[D], 失效概率)。"""
    xr, wr = gauss_legendre(nR)
    xd, wd = gauss_legendre(nd)
    xg, wg = gauss_legendre(nrg)
    tot = 0.0
    wtot = 0.0
    fail_w = 0.0
    for i in range(nR):                                   # R: 面积均匀 -> p(R)=2R/(Rmax^2-Rmin^2)
        R = RMIN + (RMAX - RMIN) * 0.5 * (xr[i] + 1.0)
        wR = wr[i] * 0.5 * (RMAX - RMIN) * (2 * R) / (RMAX ** 2 - RMIN ** 2)
        lo = max(1000.0, R)
        hi = 1500.0
        for a in range(nd):
            d1 = EPS * xd[a]
            w1 = wd[a] * 0.5                              # U(-eps,eps): 密度 1/(2eps), dx=eps*dx'
            for b in range(nd):
                d2 = EPS * xd[b]
                w2 = wd[b] * 0.5
                acc = 0.0
                if hi > lo:
                    for g in range(nrg):
                        rg = lo + (hi - lo) * 0.5 * (xg[g] + 1.0)
                        wg2 = wg[g] * 0.5 * (hi - lo) / (hi - lo)
                        val, failed = D_of(psi_deg, d, R, d1, d2, rg)
                        acc += wg2 * val
                        fail_w += wR * w1 * w2 * wg2 * (1.0 if failed else 0.0)
                else:
                    val, failed = D_of(psi_deg, d, R, d1, d2, lo)
                    acc = val
                    fail_w += wR * w1 * w2 * (1.0 if failed else 0.0)
                tot += wR * w1 * w2 * acc
                wtot += wR * w1 * w2
    return tot / wtot, fail_w / wtot


if __name__ == "__main__":
    print("E[D] 对拍（精确半平面交 + Gauss-Legendre 求积）")
    print(f"{'策略':<34}{'E[D] (m)':>12}{'失效概率':>12}")
    cands = [
        ("答案稿推荐  psi=30.0, d=1150", 30.0, 1150.0),
        ("答案稿备选  psi=30.0, d=1000", 30.0, 1000.0),
        ("harness 推荐 psi=45.0, d=1697", 45.0, 1697.06),
        ("harness 同偏移 psi=45, d=1200", 45.0, 1200.0),
        ("Harness 垂线 offset=300 (psi~14)", 14.04, 1236.9),
    ]
    base = None
    for name, psi, d in cands:
        e, f = evaluate(psi, d)
        if base is None:
            base = e
        print(f"{name:<34}{e:>12.3f}{f*100:>11.4f}%")
    print()
    print("扫描 psi x d 网格（找 E[D] 最小）:")
    best = None
    for psi in (20.0, 25.0, 30.0, 35.0, 40.0, 45.0):
        row = []
        for d in (1000.0, 1150.0, 1300.0):
            e, _ = evaluate(psi, d, nR=32, nd=9, nrg=7)
            row.append(e)
            if best is None or e < best[0]:
                best = (e, psi, d)
        print(f"  psi={psi:5.1f}  " + "  ".join(f"d={d:.0f}:{v:8.3f}" for d, v in zip((1000.,1150.,1300.), row)))
    print(f"  网格最小: E[D]={best[0]:.3f} m  @ psi={best[1]}, d={best[2]}")
