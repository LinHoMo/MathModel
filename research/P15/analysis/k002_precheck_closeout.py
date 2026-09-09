# -*- coding: utf-8 -*-
"""K002 预检收口：G2 一致性（Fleiss κ on dimensions + 总分一致性）+ 区分度分析 + PRECHECK_REPORT。

数据源（只读）：
- scores/<sid>.json：主盲评 12 份（评估者 s_0001KcfKHMO）
- g2/evaluator_{A,B,C}/<sid>.json：G2 三评估者 × 5 样例
- key/condition_map.json：预检分组（phase=PRECHECK，解封用于预检判定）
"""
import json
from pathlib import Path
import math

BASE = Path("research/P15/experiments/P15-K002-precheck")
DIMS = [f"L{a}.{b}" for a in range(1, 5) for b in range(1, 6)]
DIMS = [d for d in DIMS if d in {
    "L1.1","L1.2","L1.3","L1.4","L1.5","L2.1","L2.2","L2.3","L2.4","L2.5","L2.6","L2.7",
    "L3.1","L3.2","L3.3","L3.4","L3.5","L4.1","L4.2","L4.3","L4.4","L4.5"}]
L2 = ["L2.1","L2.2","L2.3","L2.4","L2.5","L2.6","L2.7"]

def load_scores(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def total_of(scores, dims=DIMS):
    return sum(scores["dimensions"][d]["score"] for d in dims)

def l2_of(scores):
    return sum(scores["dimensions"][d]["score"] for d in L2)

# ---------- 1. 主盲评 12 runs：分组 + 总分 + L2 ----------
cond = json.loads((BASE / "key" / "condition_map.json").read_text(encoding="utf-8"))["map"]
rows = []
for sid, meta in cond.items():
    f = BASE / "scores" / f"{sid}.json"
    if not f.exists():
        print(f"  [MISS] {sid[:8]} scores")
        continue
    s = load_scores(f)
    rows.append({
        "sid": sid[:8], "problem": meta["problem_id"], "arm": meta["arm"],
        "total": total_of(s), "l2": l2_of(s),
    })
rows.sort(key=lambda r: (r["problem"], r["arm"], r["sid"]))

print("=== 主盲评 12 runs（总分/42, L2/15）===")
for r in rows:
    print(f"  {r['problem']}  {r['arm']}  {r['sid']}  total={r['total']}  L2={r['l2']}")

# ---------- 2. 区分度：每题的 F vs S ----------
print("\n=== 区分度（F vs S）===")
by_problem = {}
for r in rows:
    by_problem.setdefault(r["problem"], []).append(r)
disc_fail = 0
for prob in sorted(by_problem):
    grp = by_problem[prob]
    f = [g for g in grp if g["arm"] == "F"]
    s = [g for g in grp if g["arm"] == "S"]
    f_mean = sum(g["total"] for g in f) / len(f) if f else float("nan")
    s_mean = sum(g["total"] for g in s) / len(s) if s else float("nan")
    d = s_mean - f_mean
    zero = (d == 0) or (f_mean == s_mean)
    if zero:
        disc_fail += 1
    print(f"  {prob}: F={f_mean:.2f}(n={len(f)})  S={s_mean:.2f}(n={len(s)})  Δ(S-F)={d:+.2f}  {'零区分度!' if zero else 'ok'}")
print(f"  零区分度题数: {disc_fail}/6")

# ---------- 3. G2 一致性：3 评估者 × 5 样例 ----------
print("\n=== G2 一致性（3 evaluators × 5 samples）===")
sample_ids = ["1a3d1fa7-bc89-40a9-a3b8-c1e9392456de", "07a0ca6e-0822-48f3-ac03-1199972a8469",
              "386ecbe0-6b65-46a4-8b81-48f6b38a088c", "28df6ec4-ce4a-4bbd-8241-330b01a9e71f",
              "371ecd7b-27cd-4130-8722-9389571aa876"]
evals = {}
for ev in ("A", "B", "C"):
    evals[ev] = {}
    for sid in sample_ids:
        f = g2_dir = BASE / "g2" / f"evaluator_{ev}" / f"{sid}.json"
        if f.exists():
            evals[ev][sid] = load_scores(f)
        else:
            print(f"  [MISS] evaluator_{ev} {sid[:8]}")

# Fleiss' kappa（维度分数 0-3 离散类）线性加权版本
def fleiss_kappa_weighted(ratings, k=4):
    """ratings: list of n 样例, each = list of m 评估者分数（0..k-1）"""
    n = len(ratings)
    m = len(ratings[0])
    if n == 0 or m < 2:
        return float("nan")
    # 每样例的分数分布
    counts = [[0] * k for _ in range(n)]
    for i, r in enumerate(ratings):
        for v in r:
            counts[i][v] += 1
    # Fleiss: 用平方权重做加权 kappa
    def weight(a, b):
        return 1.0 - (a - b) ** 2 / (k - 1) ** 2
    # 观察一致
    total_pairs = n * m * (m - 1)
    obs_num = 0.0
    for i in range(n):
        for a in range(k):
            for b in range(k):
                obs_num += counts[i][a] * (counts[i][b] - (1 if a == b else 0)) * weight(a, b)
    if total_pairs == 0:
        return float("nan")
    obs = obs_num / total_pairs
    # 期望一致
    pj = [0.0] * k
    for i in range(n):
        for v in range(k):
            pj[v] += counts[i][v]
    for v in range(k):
        pj[v] /= (n * m)
    exp_num = 0.0
    for a in range(k):
        for b in range(k):
            exp_num += pj[a] * pj[b] * weight(a, b) * n * m * (m - 1)
    exp = exp_num / total_pairs
    if 1 - exp == 0:
        return float("nan")
    return (obs - exp) / (1 - exp)

# 维度级 Fleiss κ（跨 22 维 × 5 样例 = 110 个评分单元）
all_cells = []
total_by_eval = {e: [] for e in evals}
for sid in sample_ids:
    per = {e: evals[e].get(sid) for e in evals}
    if any(v is None for v in per.values()):
        continue
    for d in DIMS:
        vals = [per[e]["dimensions"][d]["score"] for e in evals]
        all_cells.append(vals)
    for e in evals:
        total_by_eval[e].append(total_of(per[e]))

kw = fleiss_kappa_weighted(all_cells)
print(f"  维度级加权 Fleiss κ: {kw:.3f}  (n={len(all_cells)} cells × 3 evaluators)")
print("  评估者总分（/42）:")
for e in evals:
    print(f"    {e}: {total_by_eval[e]}")
# 总分一致性（平均绝对差）
pairs = [("A", "B"), ("A", "C"), ("B", "C")]
mads = []
for a, b in pairs:
    diff = [abs(x - y) for x, y in zip(total_by_eval[a], total_by_eval[b])]
    mad = sum(diff) / len(diff) if diff else float("nan")
    mads.append((f"{a}-{b}", round(mad, 2), diff))
    print(f"    总分 MAD {a}-{b}: {mads[-1][1]}  diffs={mads[-1][2]}")

# ---------- 4. 结论判定 ----------
print("\n=== 判定 ===")
g2_pass = kw >= 0.6 if kw == kw else False
print(f"  G2 一致性: κ={kw:.3f} >= 0.6 ? {g2_pass}")
print(f"  区分度: 零区分度 {disc_fail}/6（≥2 → STOP；0 → 全保留）")

# 输出 JSON 供报告引用
out = {
    "phase": "PRECHECK_CLOSEOUT",
    "runs": rows,
    "discrimination": {
        prob: {"F": [g for g in by_problem[prob] if g["arm"] == "F"],
               "S": [g for g in by_problem[prob] if g["arm"] == "S"]}
        for prob in by_problem
    },
    "g2": {
        "fleiss_kappa_weighted": round(kw, 3) if kw == kw else None,
        "total_by_eval": {e: total_by_eval[e] for e in evals},
        "mad_pairs": [{"pair": p, "mad": m} for p, m, _ in mads],
        "pass": g2_pass,
    },
    "verdict": {
        "g2_pass": g2_pass,
        "zero_discrimination_count": disc_fail,
    },
}
(BASE / "precheck_closeout.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n[OK] precheck_closeout.json written")
