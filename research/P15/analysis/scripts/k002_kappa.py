#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k002_kappa.py — P15-K002 盲评一致性（G2 Instrument validity）

对每个 evaluator 对，按维度计算 Cohen's κ（未加权）与二次加权 κ，
再对维度取平均。校准样本为全部 evaluator 共享的 5 份 submission。

用法:
    py -3.12 research/P15/analysis/scripts/k002_kappa.py
    py -3.12 research/P15/analysis/scripts/k002_kappa.py --out <json 路径>

零第三方依赖（标准库）。
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

P15 = Path(__file__).resolve().parents[2]
RAW = P15 / "analysis" / "raw_k002"
CAL = RAW / "scores" / "_calibration"

L1 = [f"L1.{i}" for i in range(1, 6)]
L2 = [f"L2.{i}" for i in range(1, 8)]
L3 = [f"L3.{i}" for i in range(1, 6)]
L4 = [f"L4.{i}" for i in range(1, 6)]
DIMS = L1 + L2 + L3 + L4


def load_eval(name: str) -> dict:
    out = {}
    d = CAL / name
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.json")):
        s = json.loads(p.read_text(encoding="utf-8"))
        vals = {k: (v or {}).get("score") for k, v in (s.get("dimensions") or {}).items()}
        if all(v is None for v in vals.values()):
            continue
        out[s["submission_id"]] = vals
    return out


def cohen_kappa(pairs: list) -> tuple:
    """pairs: list of (a, b) 整数对。返回 (kappa, n, agreement, pe)。"""
    n = len(pairs)
    if n == 0:
        return (float("nan"), 0, float("nan"), float("nan"))
    cats = sorted({x for p in pairs for x in p})
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    obs = [[0] * k for _ in range(k)]
    for a, b in pairs:
        obs[idx[a]][idx[b]] += 1
    po = sum(obs[i][i] for i in range(k)) / n
    ra = [sum(row) / n for row in obs]
    rb = [sum(obs[i][j] for i in range(k)) / n for j in range(k)]
    pe = sum(ra[i] * rb[i] for i in range(k))
    if pe >= 1.0:
        # 完全一致或退化（Kappa 悖论）：约定 κ=1.0
        return (1.0, n, po, pe)
    return ((po - pe) / (1 - pe), n, po, pe)


def quadratic_weight(a, b, k: int) -> float:
    return ((a - b) ** 2) / ((k - 1) ** 2) if k > 1 else 0.0


def weighted_kappa(pairs: list) -> float:
    n = len(pairs)
    if n == 0:
        return float("nan")
    cats = sorted({x for p in pairs for x in p})
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    obs = [[0] * k for _ in range(k)]
    for a, b in pairs:
        obs[idx[a]][idx[b]] += 1
    ra = [sum(row) / n for row in obs]
    rb = [sum(obs[i][j] for i in range(k)) / n for j in range(k)]
    num = sum(quadratic_weight(i, j, k) * obs[i][j] for i in range(k) for j in range(k))
    den = sum(quadratic_weight(i, j, k) * ra[i] * rb[j] * n for i in range(k) for j in range(k))
    if den == 0:
        return 1.0
    return 1 - num / den


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(RAW / "g2_kappa_formal.json"))
    ap.add_argument("--threshold", type=float, default=0.6)
    args = ap.parse_args()

    evals = {}
    for d in sorted(CAL.iterdir()):
        if d.is_dir():
            ev = load_eval(d.name)
            if ev:
                evals[d.name] = ev
    if len(evals) < 2:
        print(f"[FAIL] 有效 evaluator 不足 2（当前 {len(evals)}）")
        return 1

    report = {"evaluators": {k: sorted(v) for k, v in evals.items()}, "pairs": {}, "per_dim": {}}
    all_dims = []
    for a, b in itertools.combinations(sorted(evals), 2):
        sa, sb = evals[a], evals[b]
        common = sorted(set(sa) & set(sb))
        per = {}
        for dim in DIMS:
            pairs = [(sa[s][dim], sb[s][dim]) for s in common
                     if sa[s].get(dim) is not None and sb[s].get(dim) is not None]
            if not pairs:
                continue
            kap, n, po, pe = cohen_kappa(pairs)
            wk = weighted_kappa(pairs)
            per[dim] = {"kappa": round(kap, 3), "qwk": round(wk, 3), "n": n,
                        "agree": round(po, 3), "pe": round(pe, 3)}
            all_dims.append((f"{a}|{b}", dim, kap))
        ks = [v["kappa"] for v in per.values()]
        ws = [v["qwk"] for v in per.values()]
        report["pairs"][f"{a}|{b}"] = {
            "n_samples": len(common),
            "n_dims": len(ks),
            "mean_kappa": round(sum(ks) / len(ks), 3) if ks else None,
            "mean_qwk": round(sum(ws) / len(ws), 3) if ws else None,
            "dims_k_lt_threshold": sorted([d for d, v in per.items()
                                           if v["kappa"] < args.threshold]),
        }
        report["per_dim"][f"{a}|{b}"] = per

    vals = [k for _, _, k in all_dims]
    report["overall"] = {
        "n_pairs": len(report["pairs"]),
        "n_dim_pair_cells": len(vals),
        "mean_kappa_dim_level": round(sum(vals) / len(vals), 3) if vals else None,
        "perfect_dims": sum(1 for v in vals if v >= 0.999),
        "dims_lt_threshold": sum(1 for v in vals if v < args.threshold),
        "threshold": args.threshold,
        "gate": "PASS" if vals and (sum(vals) / len(vals)) >= args.threshold else "FAIL",
    }

    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    o = report["overall"]
    print(f"[kappa] evaluators={list(evals)}")
    for k, v in report["pairs"].items():
        print(f"  {k}: n={v['n_samples']} mean_kappa={v['mean_kappa']} mean_qwk={v['mean_qwk']} "
              f"低κ维度={v['dims_k_lt_threshold']}")
    print(f"  总体维度级 mean_kappa={o['mean_kappa_dim_level']} "
          f"完美一致={o['perfect_dims']}/{o['n_dim_pair_cells']} "
          f"<{o['threshold']}={o['dims_lt_threshold']} → G2 {o['gate']}")
    print(f"  证据: {args.out}")
    return 0 if o["gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
