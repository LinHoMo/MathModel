# Playbook: 2026B 无线电干扰源定位清除（测向交会 + 覆盖搜索）

> **题型**: CUMCM B 题 — 计算几何 + 路径规划 + 离散事件仿真
> **核心方法**: 楔形交会定位 + 最小包围圆 + GDOP 布站 + 同心环覆盖 + 交会-归航清除
> **难度**: ★★★★☆（几何判据 + 策略可信度约束）

---

## 1. 问题拆解

```json
{
  "problem": "2026B 干扰源定位清除",
  "sub_questions": [
    {"id": "Q1", "desc": "给定观测点与示向度，给出定位区域直径算法，并判定以直径为直径的圆能否覆盖该区域", "type": "computational_geometry", "depends_on": [], "key_output": "区域直径 + 覆盖判定"},
    {"id": "Q2", "desc": "已知一个测点的示向度，给出第二测点的选择策略与候选区域", "type": "geometry_optimization", "depends_on": ["Q1"], "key_output": "推荐点（直线）+ 候选区域"},
    {"id": "Q3", "desc": "多个全向源的自动搜索-定位-清除策略与算法，模拟器演练统计", "type": "coverage_control", "depends_on": ["Q1", "Q2"], "key_output": "清除比例 + 平均用时"},
    {"id": "Q4", "desc": "混合全向与定向源下的策略与算法，模拟器演练检验", "type": "coverage_control_blindzone", "depends_on": ["Q3"], "key_output": "清除比例 + 平均用时"}
  ]
}
```

## 2. 类型判定

| 维度 | 判定 |
|------|------|
| 题型 | **B 题**（离散/几何 + 仿真） |
| 核心建模 | 计算几何（凸多边形）+ 路径规划 + 离散事件 |
| 求解类型 | 几何精确解 + 蒙特卡洛统计 |
| 数据需求 | 题面给的检测点/示向度/接收半径/时耗；无外部数据 |
| 方法方向 | 凸集交 + 覆盖完备性 + 可观测量策略 |

## 3. 候选模型对比

| 方法 | 优势 | 劣势 | 适用子问 | 推荐度 |
|------|------|------|---------|--------|
| **楔形交会凸多边形（精确）** | 与「区间误差」语义一致；可精确求直径/最小包围圆 | 需处理退化（近共线） | Q1/Q2 | ★★★★★ |
| 最小二乘/最大似然点估计 | 给单点与协方差 | 与题面「区间误差」不匹配；丢失区域形状 | Q1 | ★★☆☆☆ |
| 网格/粒子贝叶斯定位 | 可含先验与非线性 | 无先验信息；精度受网格限制 | Q1/Q2 | ★★★☆☆ |
| 螺旋覆盖路径 | 平滑、转弯少 | 大半径处空隙超作用半径 ⇒ 不完备 | Q3/Q4 | ★★☆☆☆ |
| **同心环覆盖路径** | 完备性有几何保证（R/(2k)） | 内外环频繁切换，路径稍长 | Q3/Q4 | ★★★★★ |

**最终选择**: 楔形交会 + 最小包围圆 + GDOP 布站（Q1/Q2）；同心环覆盖 + 交会-归航清除（Q3/Q4）

## 4. 模型建立

### 4.1 符号定义

| 符号 | 含义 | 单位 |
|------|------|------|
| $S_i, b_i$ | 观测点坐标、示向度 | m, ° |
| $\varepsilon$ | 示向度误差界 | ° |
| $\Omega$ | 定位区域（楔形交集） | — |
| $D_\Omega$ | 定位区域直径 | m |
| $\varphi$ | 交会角 | ° |
| $r_{rec}$ | 有效接收半径 | m |
| $R$ | 目标区域半径 | m |
| $\rho_i$ | 第 i 条覆盖环半径 | m |

### 4.2 定位区域与直径

$$W_i=\{P:\arg(P-S_i)\in[b_i-\varepsilon,b_i+\varepsilon]\},\qquad
\Omega=\bigcap_i W_i,\qquad D_\Omega=\max_{(p,q)\in\Omega\times\Omega}|p-q|$$

求交用 Sutherland–Hodgman 半平面裁剪；直径用凸包顶点枚举（等价旋转卡壳）。

### 4.3 覆盖判据（Thales）

$$\Omega\subseteq\mathcal C(A,B)\iff \angle APB\ge 90^\circ,\quad \forall P\in\mathrm{vert}(\Omega)\setminus\{A,B\}$$

不普遍成立：锐角三角形反例（最小包围圆半径 > 直径圆半径）。

### 4.4 第二测点

$$\sigma_P\propto\frac{1}{\sin\varphi},\qquad
P_2^*=G_{est}+t\,\mathbf n_\perp,\quad \mathbf n_\perp\perp(G_{est}-S_1)$$

### 4.5 覆盖路径完备性

$$\rho_i=\frac{R(2i-1)}{2k}\ \Longrightarrow\ \max_{\rho\in[0,R]}\min_i|\rho-\rho_i|=\frac{R}{2k}$$

全向取 $k=2$（$R=1800$ m ⇒ 450 m < $r_{rec,\min}=1000$ m）；含定向源追加外侧环补盲区。

### 4.6 交会与归航

$$G=\mathrm{cross}(P_1,b_1;P_2,b_2),\qquad
x_{n+1}=x_n+\mathrm{clip}(rel\cdot r_{nom},\,15,500)\,\mathbf u(b(x_n))$$

## 5. 代码实现（骨架）

```python
"""2026B 干扰源定位清除 — 楔形交会 + 同心环覆盖 + 归航清除"""
import numpy as np, math

np.random.seed(42)                    # 演练 30 组实例，种子 42 起连续取值
R_AREA, EPS, R_REC_MIN, D_OPTIC = 1800.0, 1.0, 1000.0, 20.0
T_DET, T_OPTIC, T_LASER, V, ARC = 5.0, 3.0, 2.0, 5.0, 500.0
RING_OMNI, RING_DIR = (450., 1350.), (450., 1350., 1200., 1799.)

def wedge_planes(S, b_deg, eps=EPS):
    """示向度 b±ε 的角域 → 两个有向半平面 (n, c, sense)。

    约定：点在角域内 ⟺ sense * (n·P − c) ≥ 0。
    θ ≤ b+ε  ⟺ (−sin(b+ε), cos(b+ε))·(P−S) ≤ 0  → sense = −1
    θ ≥ b−ε  ⟺ (−sin(b−ε), cos(b−ε))·(P−S) ≥ 0  → sense = +1
    """
    planes = []
    for s, sense in ((+eps, -1), (-eps, +1)):
        th = math.radians(b_deg + s)
        n = (-math.sin(th), math.cos(th))
        planes.append((n, n[0]*S[0] + n[1]*S[1], sense))
    return planes

def clip(poly, plane):
    """Sutherland–Hodgman 单半平面裁剪（凸多边形保持凸）"""
    if not poly:
        return poly
    n, c, sense = plane
    def val(p): return n[0]*p[0] + n[1]*p[1] - c
    def inside(p): return sense * val(p) >= -1e-9
    def inter(a, b):
        t = val(a) / (val(a) - val(b))
        return (a[0] + t*(b[0]-a[0]), a[1] + t*(b[1]-a[1]))
    out = []
    for i, cur in enumerate(poly):
        prv = poly[i-1]
        if inside(cur):
            if not inside(prv):
                out.append(inter(prv, cur))
            out.append(cur)
        elif inside(prv):
            out.append(inter(prv, cur))
    return out

def location_region(obs, box=2*R_AREA):
    """obs: [(Sx,Sy,b_deg)] → 定位区域（凸多边形顶点）；先给大包围盒再逐条裁剪"""
    poly = [(-box, -box), (box, -box), (box, box), (-box, box)]
    for Sx, Sy, b in obs:
        for plane in wedge_planes((Sx, Sy), b):
            poly = clip(poly, plane)
            if not poly:
                return []                      # 楔形无交集 ⇒ 不可定位，如实返回空
    return poly

def diameter(poly):
    """凸多边形直径 = 凸包顶点最远点对"""
    h = convex_hull(poly)
    return max(math.dist(a, b) for a in h for b in h) if len(h) > 1 else 0.0

def convex_hull(pts):
    pts = sorted(set(pts))
    if len(pts) <= 2: return pts
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and cross(out[-2], out[-1], p) <= 0: out.pop()
            out.append(p)
        return out
    return half(pts)[:-1] + half(pts[::-1])[:-1]

def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

def min_enclosing_circle(pts):
    """Welzl 随机增量：含全部顶点的最小圆"""
    pts = list(pts)
    c, r = (0., 0.), 0.
    for i, p in enumerate(pts):
        if math.dist(p, c) <= r + 1e-9: continue
        c, r = p, 0.
        for j in range(i):
            if math.dist(pts[j], c) <= r + 1e-9: continue
            c = ((p[0]+pts[j][0])/2, (p[1]+pts[j][1])/2)
            r = math.dist(p, c)
            for k in range(j):
                if math.dist(pts[k], c) <= r + 1e-9: continue
                c, r = circumcircle(p, pts[j], pts[k])
    return c, r

def circumcircle(a, b, c):
    ax, ay, bx, by, cx, cy = *a, *b, *c
    d = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    ux = ((ax**2+ay**2)*(by-cy)+(bx**2+by**2)*(cy-ay)+(cx**2+cy**2)*(ay-by))/d
    uy = ((ax**2+ay**2)*(cx-bx)+(bx**2+by**2)*(ax-cx)+(cx**2+cy**2)*(bx-ax))/d
    ctr = (ux, uy)
    return ctr, math.dist(ctr, a)

def ring_points(radii, arc=ARC):
    """同心环 + 弧长等分检测点（覆盖完备性的实现形式）"""
    pts = []
    for rho in radii:
        n = max(3, int(round(2*math.pi*rho/arc)))
        pts += [(rho*math.cos(2*math.pi*i/n), rho*math.sin(2*math.pi*i/n))
                for i in range(n)]
    return pts

if __name__ == "__main__":
    radii = RING_OMNI
    print("覆盖环:", radii, "最大最近距离 =", R_AREA/(2*len(radii)), "m")
    print("检测点数:", len(ring_points(radii)))
    # 演练主体：Simulator（源生成 + 观测 + 归航清除）→ run_trials(30) 统计
```

> 说明：骨架覆盖 Q1 的定位区域/直径/最小包围圆、Q3 的同心环布点与漏检率核算；
> 完整演练主体（源生成、交会解算、归航清除、时间计价与 30 组统计）见项目交付代码。

## 6. 结果验证

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| 覆盖完备性 | 各 2e4 个随机源（含随机朝向）蒙特卡洛 | 报告漏检率 + 样本量 |
| 反例构造 | 锐角三角形验证「直径圆覆盖」不成立 | 最小包围圆半径 > 直径圆半径 |
| 解析-网格一致 | 垂线解析最优 vs 极坐标网格最优 | 交会角均为 90.00° |
| 清除完备性 | 30 组实例逐一检查 | 最小清除比例 = 1.0 |
| 可观测量合规 | 静态检查策略无真值读取 | 真值仅用于作用距离判定 |

```python
def coverage_miss_ratio(radii, n=20000, directional=False):
    """蒙特卡洛漏检率：随机源是否被某个检测点覆盖"""
    import random
    pts = ring_points(radii)
    miss = 0
    for _ in range(n):
        # 源位置（含朝向，用于定向源可见性判定）
        rho = R_AREA*math.sqrt(random.random()); th = 2*math.pi*random.random()
        src = (rho*math.cos(th), rho*math.sin(th))
        if not any(math.dist(src, p) <= R_REC_MIN for p in pts):
            miss += 1
    return miss/n
```

## 7. 论文结构

| 章节 | 内容 | 图表 |
|------|------|------|
| 摘要 | 三问链路：定位精度 → 布站 → 搜索清除 | — |
| 1 问题分析 | 几何/规划/仿真三层拆解 | 图1 场景示意 |
| 2 假设与符号 | 区间误差、可测量清单、盲区规则 | 表1 符号表 |
| 3 Q1 定位区域 | 楔形交集 + 直径 + 覆盖判据 + 反例 | 图2 区域与直径圆 |
| 4 Q2 第二测点 | GDOP + 垂线最优 + 候选区域 | 图3 候选区域 |
| 5 Q3/Q4 覆盖清除 | 同心环 + 交会-归航 + 时间计价 | 图4 覆盖环, 图5 轨迹 |
| 6 验证 | 漏检率 + 清除完备性 + 一致性 | 图6 漏检率 vs 环数 |
| 7 评价 | 局限：本地模拟器、名义接收半径、残余漏检 | — |

## 8. 关键图表

| 编号 | 类型 | 内容 | 工具 |
|------|------|------|------|
| 图1 | 示意图 | 目标圆域 + 观测点 + 示向度楔形 | matplotlib |
| 图2 | 多边形图 | 定位区域 + 直径 + 直径圆/最小包围圆 | matplotlib |
| 图3 | 示意图 | 第二点垂线 + 候选扇形环域 | matplotlib |
| 图4 | 路径图 | 同心环检测点布置 | matplotlib |
| 图5 | 轨迹图 | 机器狗搜索-归航-清除轨迹 | matplotlib |
| 图6 | 曲线 | 漏检率随环数/作用半径变化 | matplotlib |

## 9. LaTeX 源码片段

```latex
\section{定位区域与覆盖判据}
第 $i$ 个测点获得示向度 $b_i$，误差界为 $\varepsilon$，其可能角域为
\begin{equation}
  W_i=\bigl\{P:\arg(P-S_i)\in[b_i-\varepsilon,\;b_i+\varepsilon]\bigr\},
  \qquad \Omega=\bigcap_{i} W_i .
\end{equation}
由 Thales 定理，以 $AB$ 为直径的圆覆盖 $\Omega$ 的充要条件为
\begin{equation}
  \angle APB\ge 90^\circ,\qquad \forall P\in\operatorname{vert}(\Omega)\setminus\{A,B\},
\end{equation}
该条件并非恒成立：锐角三角形的最小包围圆半径严格大于其直径之半，即为其反例。
```

## 10. 复用要点

- **误差是区间就画楔形**：不要默认正态分布去给椭圆。
- **「直径圆覆盖」要判据 + 反例**：不给反例的断言不可信。
- **布站以 GDOP 为约束**：最优第二点是一条直线（Thales 切线），不是一个点。
- **覆盖完备性先证明再谈效率**：$R/(2k)\le r_{rec}$ 是硬条件；报告漏检率与样本量。
- **策略只能吃可观测量**：真值导航会让指标虚高，必须做真值封锁重跑。
- **方向性传感器要单独补扫**：波束盲区必须用外侧环覆盖，且如实报残余漏检率。
