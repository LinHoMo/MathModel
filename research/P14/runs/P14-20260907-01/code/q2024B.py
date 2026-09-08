#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""q2024B.py — P14 实验：生产抽检优化（artifact 2024_B/B1_F 冻结机制 M1/M2/M3）.

场景基线（executor-defined pilot scenario，随本文件 sha256 冻结溯源）：
  批次 N=1000；c_ins=1 元/件；c_def=50 元/件；基准 p=0.05；A4 独立同分布。
机制实现：M1 P(miss)=(1-p)^n（精确）与 ≈e^{-np}（近似）；M2 E[C]=c_ins·n+c_def·P(miss)·(N-n)；
M3 一阶条件以数值极小化实现。
输出：stdout 严格 JSON {"metrics": {...}}。
"""
import json
import sys

import numpy as np

N_BASE = 1000
C_INS = 1.0
C_DEF = 50.0


def e_cost(n, p, N, c_ins=C_INS, c_def=C_DEF, approx=False):
    pm = np.exp(-n * p) if approx else (1.0 - p) ** n
    return c_ins * n + c_def * pm * (N - n)


def n_star(p, N, c_ins=C_INS, c_def=C_DEF, approx=False):
    grid = np.arange(0, N + 1, dtype=float)
    vals = e_cost(grid, p, N, c_ins, c_def, approx)
    i = int(np.argmin(vals))
    if 0 < i < N:
        cand = np.linspace(grid[i - 1], grid[i + 1], 2001)
        vals2 = e_cost(cand, p, N, c_ins, c_def, approx)
        return float(cand[int(np.argmin(vals2))])
    return float(grid[i])


def run_sensitivity():
    configs = []
    for p in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2):
        for ratio in (10, 50, 100, 500, 1000):
            c_def = C_INS * ratio
            ne = n_star(p, N_BASE, c_def=c_def)
            configs.append({"p": p, "ratio": ratio, "n_star_exact": ne,
                            "n_star_approx": n_star(p, N_BASE, c_def=c_def, approx=True),
                            "min_E_C": float(e_cost(ne, p, N_BASE, c_def=c_def))})
    n1 = n_star(0.05, N_BASE)
    n2 = n_star(0.1, N_BASE)
    elasticity = ((n2 - n1) / max(n1, 1e-9)) / (0.05 / 0.05)
    zero_region = sum(1 for c in configs if c["n_star_exact"] <= 0.5) / len(configs)
    return {"configs": configs, "elasticity_p": elasticity,
            "zero_inspection_region": zero_region}


def run_ablation():
    rows = []
    for p in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2):
        ne = n_star(p, N_BASE)
        na = n_star(p, N_BASE, approx=True)
        rows.append({"p": p, "abs_dn_star": abs(ne - na),
                     "cost_gap": float(e_cost(na, p, N_BASE) - e_cost(ne, p, N_BASE))})
    ns = np.arange(0, N_BASE + 1)
    ea = e_cost(ns, 0.05, N_BASE, approx=True)
    ee = e_cost(ns, 0.05, N_BASE)
    ok = np.where(np.abs(ea - ee) / np.maximum(ee, 1e-9) < 0.01)[0]
    boundary = int(ok.max()) if len(ok) else -1
    return {"rows": rows, "approx_valid_boundary": boundary}


def run_mc():
    out = {}
    p = 0.05
    for N in (100, 1000, 10000):
        nstar = int(round(n_star(p, N)))
        rng = np.random.RandomState(42)
        costs = []
        for _ in range(2000):
            defective = rng.binomial(N, p)
            if nstar <= 0:
                missed = defective
            else:
                found = defective > 0 and rng.random() < 1.0 - (1.0 - p) ** nstar
                missed = 0 if found else max(0, defective - 1)
            costs.append(C_INS * nstar + C_DEF * missed)
        emp = float(np.mean(costs))
        theo = float(e_cost(nstar, p, N))
        out[str(N)] = {"n_star": nstar, "empirical_E_C": emp, "theoretical_E_C": theo,
                       "relative_error": abs(emp - theo) / max(theo, 1e-9)}
    return out


def run_hypergeo():
    from math import comb
    rows = []
    p = 0.05
    for N in (50, 100, 200):
        K = max(1, int(round(p * N)))
        nb = n_star(p, N)

        def pm_hyp(n, N=N, K=K):
            n = int(n)
            if n > N - K:
                return 0.0
            return comb(N - K, n) / comb(N, n)

        vals = [C_INS * n + C_DEF * pm_hyp(n) * (N - n) for n in range(N + 1)]
        nh = float(int(np.argmin(vals)))
        rows.append({"N": N, "n_star_binomial": nb, "n_star_hypergeometric": nh,
                     "hypergeo_gap": abs(nb - nh)})
    cnt = tot = 0
    for p2 in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2):
        for ratio in (10, 50, 100, 500, 1000):
            tot += 1
            ns = n_star(p2, N_BASE, c_def=C_INS * ratio)
            if ns <= 0.5 or ns >= N_BASE - 0.5:
                cnt += 1
    return {"rows": rows, "boundary_region_frac": cnt / tot}


EXPERIMENTS = {
    "EXP-2024B-C0-1": run_sensitivity,
    "EXP-2024B-C0-2": run_ablation,
    "EXP-2024B-C0-3": run_mc,
    "EXP-2024B-C1-1": run_sensitivity,
    "EXP-2024B-C1-2": run_ablation,
    "EXP-2024B-C1-3": run_mc,
    "EXP-2024B-C1-4": run_hypergeo,
}

if __name__ == "__main__":
    exp = sys.argv[1]
    res = EXPERIMENTS[exp]()
    print(json.dumps({"experiment_id": exp, "metrics": res},
                     ensure_ascii=False, sort_keys=True))
