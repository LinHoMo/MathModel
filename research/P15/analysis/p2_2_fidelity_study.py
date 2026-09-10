# -*- coding: utf-8 -*-
"""P2-2: Fidelity Measurement Study — 测量 L2 Fidelity 在 K003 66 runs 的分布，
分析 fidelity 与盲评 L2 结构维度的相关性，识别 misaligned 案例。

数据源（已存在，FROZEN 后不再生成）：
  research/P15/experiments/P15-K003/key/condition_map.json（fidelity_score/arm/problem）
  research/P15/experiments/P15-K003/scores/evaluator_{A,B,C}/BUNDLE_*.json（22 维盲评）
  research/P15/experiments/P15-K003/runs/<sid>/fidelity_report.json（check 明细）

LLM-free：纯确定性统计，无 LLM。
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
K003 = REPO / "research" / "P15" / "experiments" / "P15-K003"

# ---------------------------------------------------------------- 加载

cond = json.loads((K003 / "key" / "condition_map.json").read_text(encoding="utf-8"))
scores: dict[str, dict[str, dict]] = {}
for ev in ("A", "B", "C"):
    d = {}
    for f in (K003 / "scores" / f"evaluator_{ev}").glob("BUNDLE_*.json"):
        j = json.loads(f.read_text(encoding="utf-8"))
        d[j["bundle_id"]] = j["scores"]
    scores[ev] = d

# L2 结构维度（MODEL_IR 契约质量）——K003 盲评 rubric
L2_DIMS = [d for d in [
    "L2.1", "L2.2", "L2.3", "L2.4", "L2.5", "L2.6",
    "L2.7", "L2.8", "L2.9", "L2.10", "L2.11", "L2.12",
] if d in (next(iter(scores["A"].values())) if scores["A"] else {})]

# 先探测实际维度集合
_sample = next(iter(scores["A"].values()), {})
ALL_DIMS = list(_sample.keys())
print(f"dimensions: {len(ALL_DIMS)} -> {ALL_DIMS[:6]} ...")

# ---------------------------------------------------------------- 汇总


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = sum((a - mx) ** 2 for a in xs)
    vy = sum((b - my) ** 2 for b in ys)
    if vx == 0 or vy == 0:
        return float("nan")
    return cov / math.sqrt(vx * vy)


def spearman(xs: list[float], ys: list[float]) -> float:
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(xs), rank(ys)
    return pearson(rx, ry)


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else float("nan")


rows: list[dict] = []
for bid, info in cond.items():
    if not isinstance(info, dict):
        continue
    fid = info.get("fidelity_score")
    if fid is None:
        continue
    l2_scores = []
    for ev in ("A", "B", "C"):
        s = scores.get(ev, {}).get(bid)
        if not s:
            continue
        for d in ALL_DIMS:
            if d.startswith("L2."):
                item = s.get(d) or {}
                sc = item.get("score")
                mx = item.get("max") or 0
                if sc is not None and mx:
                    l2_scores.append(sc / mx)
    rows.append({
        "bundle_id": bid,
        "submission_id": info.get("submission_id"),
        "problem_id": info.get("problem_id"),
        "arm": info.get("arm"),
        "fidelity_score": float(fid),
        "fidelity_status": "aligned" if float(fid) >= 0.6 else "misaligned",
        "exec_status": info.get("exec_status"),
        "l2_norm": _mean(l2_scores) if l2_scores else float("nan"),
    })

rows.sort(key=lambda r: r["fidelity_score"])
n = len(rows)

# ---------------------------------------------------------------- 分布

fids = [r["fidelity_score"] for r in rows]
bins = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
for f in fids:
    if f < 0.2:
        bins["0.0-0.2"] += 1
    elif f < 0.4:
        bins["0.2-0.4"] += 1
    elif f < 0.6:
        bins["0.4-0.6"] += 1
    elif f < 0.8:
        bins["0.6-0.8"] += 1
    else:
        bins["0.8-1.0"] += 1

by_arm: dict[str, list[float]] = {}
by_problem: dict[str, list[float]] = {}
for r in rows:
    by_arm.setdefault(r["arm"], []).append(r["fidelity_score"])
    by_problem.setdefault(r["problem_id"], []).append(r["fidelity_score"])

# ---------------------------------------------------------------- 相关

l2s = [r["l2_norm"] for r in rows if not math.isnan(r["l2_norm"])]
fids_l2 = [r["fidelity_score"] for r in rows if not math.isnan(r["l2_norm"])]
corr_pearson = pearson(fids_l2, l2s)
corr_spearman = spearman(fids_l2, l2s)

# 维度级相关：fidelity vs 每个 L2 维度
dim_corr = {}
for d in ALL_DIMS:
    if not d.startswith("L2."):
        continue
    xs, ys = [], []
    for r in rows:
        vals = []
        for ev in ("A", "B", "C"):
            s = scores.get(ev, {}).get(r["bundle_id"]) or {}
            item = s.get(d) or {}
            sc, mx = item.get("score"), item.get("max") or 0
            if sc is not None and mx:
                vals.append(sc / mx)
        if vals:
            xs.append(r["fidelity_score"])
            ys.append(_mean(vals))
    if len(xs) >= 8:
        dim_corr[d] = round(pearson(xs, ys), 3)

# ---------------------------------------------------------------- misaligned 案例

mis = [r for r in rows if r["fidelity_status"] == "misaligned"]
mis_sorted = sorted(mis, key=lambda r: r["fidelity_score"])[:6]
mis_details = []
for r in mis_sorted:
    sid = r["submission_id"]
    frep = K003 / "runs" / sid / "fidelity_report.json"
    checks = []
    if frep.exists():
        j = json.loads(frep.read_text(encoding="utf-8"))
        checks = [{"name": c.get("name"), "kind": c.get("kind"),
                   "passed": c.get("passed"),
                   "detail": (c.get("detail") or "")[:80]}
                  for c in (j.get("checks") or [])[:4]]
    mis_details.append({**r, "checks": checks})

# ---------------------------------------------------------------- 输出

out = {
    "n_runs": n,
    "fidelity_distribution": bins,
    "fidelity_mean": round(_mean(fids), 4),
    "fidelity_median": sorted(fids)[n // 2] if n else None,
    "fidelity_misaligned_count": len(mis),
    "by_arm": {k: {"n": len(v), "mean": round(_mean(v), 4),
                   "min": round(min(v), 4), "max": round(max(v), 4)}
               for k, v in sorted(by_arm.items())},
    "by_problem": {k: {"n": len(v), "mean": round(_mean(v), 4)}
                   for k, v in sorted(by_problem.items())},
    "fidelity_vs_L2_pearson": round(corr_pearson, 3),
    "fidelity_vs_L2_spearman": round(corr_spearman, 3),
    "dimension_corr": dict(sorted(dim_corr.items(), key=lambda kv: kv[1])),
    "misaligned_examples": mis_details,
}

(K003 / "analysis" / "p2_2_fidelity_study.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items()
                  if k not in ("misaligned_examples",)}, ensure_ascii=False, indent=2))
