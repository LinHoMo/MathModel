#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""q2020B.py — P14 实验：沙漠穿越 MDP（artifact 2020_B/MMA 冻结机制 M1/M2/M3）.

场景基线（executor-defined pilot scenario，随本文件 sha256 冻结溯源）：
  L=100 km，步长 10 km；天气 ∈ {good, bad}；P(bad→bad)=p2，P(bad|good)=0.2；
  速度决策 a ∈ {10, 20} km/period；每 period 消耗 = (a/10)·(good:1.0 / bad:1.5)；
  初始资源 r0=40；时限 T=30 periods；约束 C1: r(t) ≥ 0 ∀t。
机制实现：M1 状态转移（确定性位移+随机天气）；M2 奖励/代价；M3 Bellman 值迭代。
输出：stdout 严格 JSON {"metrics": {...}}。
"""
import json
import sys

import numpy as np

L = 100.0
STEP = 10.0
NPOS = 11          # 0..10（0..100 km）
NR = 61            # r ∈ {0..60}
T_MAX = 30
ACTIONS = (10.0, 20.0)
R0 = 40.0
P_GIVEN_BAD = 0.2  # P(bad | good)，固定；p2 = P(bad | bad) 为扫描参数
R_SCALE = NR / (R0 + 1.0)  # 资源离散化比例


def consumption(a, weather):
    return (a / 10.0) * (1.0 if weather == 0 else 1.5)


def solve_dp(p2, objective):
    """有限水平 DP。objective: "time"（min E[总时间]）或 "safe"（max P 安全到达）。"""
    V = np.zeros((NPOS, NR, 2))
    policy = np.zeros((NPOS, NR, 2), dtype=int)
    for _ in range(T_MAX):
        Vn = V.copy()
        for pi in range(NPOS - 1):
            for ri in range(NR):
                for w in (0, 1):
                    best_val = None
                    best_a = 0
                    for ai, a in enumerate(ACTIONS):
                        npi = min(NPOS - 1, pi + int(round(a / STEP)))
                        nri_f = ri - consumption(a, w) * R_SCALE
                        c1_violated = nri_f < 0
                        nri = max(0, int(round(nri_f)))
                        pw_bad = p2 if w == 1 else P_GIVEN_BAD
                        pw_good = 1.0 - pw_bad
                        if c1_violated:
                            val = (1e6 if objective == "time" else 0.0)
                        elif npi == NPOS - 1:
                            val = (0.0 if objective == "time" else 1.0)
                        else:
                            nxt = pw_bad * V[npi, nri, 1] + pw_good * V[npi, nri, 0]
                            val = (1.0 + nxt) if objective == "time" else nxt
                        better = (best_val is None
                                  or (objective == "time" and val < best_val)
                                  or (objective == "safe" and val > best_val))
                        if better:
                            best_val, best_a = val, ai
                    Vn[pi, ri, w] = best_val
                    policy[pi, ri, w] = best_a
        V = Vn
    return V, policy


def policy_array(p2, objective):
    return solve_dp(p2, objective)[1]


def run_sensitivity():
    rows = []
    for p2 in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        Vt = solve_dp(p2, "time")[0]
        Vs = solve_dp(p2, "safe")[0]
        rows.append({"p2": p2, "E_total_time": float(Vt[0, int(R0), 0]),
                     "P_safe": float(Vs[0, int(R0), 0])})
    pol_base = policy_array(0.5, "time")
    pol_adj = policy_array(0.6, "time")
    stability = float((pol_base == pol_adj).mean())
    e1, e2 = rows[2]["E_total_time"], rows[3]["E_total_time"]
    elasticity = ((e2 - e1) / e1) / (0.1 / 0.5)
    return {"configs": rows, "policy_stability": stability, "elasticity_p2": elasticity}


def simulate(p2, policy, n_seq, rng):
    safe = 0
    viol = 0
    times = []
    for _ in range(n_seq):
        pi, ri, w, t = 0, int(R0), 0, 0
        ok = False
        violated = False
        while t < T_MAX:
            a = ACTIONS[policy[pi, ri, w]]
            ri_f = ri - consumption(a, w) * R_SCALE
            if ri_f < 0:
                viol += 1
                violated = True
                break
            ri = int(round(ri_f))
            pi = min(NPOS - 1, pi + int(round(a / STEP)))
            t += 1
            if pi == NPOS - 1:
                ok = True
                break
            w = 1 if rng.random() < (p2 if w == 1 else P_GIVEN_BAD) else 0
        if ok and not violated:
            safe += 1
            times.append(t)
    n = max(1, n_seq)
    return {"P_safe_mc": safe / n, "c1_violation_rate": viol / n,
            "arrival_time_p90": float(np.percentile(times, 90)) if times else None}


def run_mc():
    pol = policy_array(0.5, "time")
    runs = []
    for i in range(3):
        rng = np.random.RandomState(42 + i)
        runs.append(simulate(0.5, pol, 1000, rng))
    return {"runs": runs}


def run_extreme():
    pol = policy_array(0.5, "time")
    worst = simulate(0.99, pol, 1000, np.random.RandomState(42))
    best = simulate(0.01, pol, 1000, np.random.RandomState(42))
    return {"P_safe_worst": worst["P_safe_mc"], "P_safe_best": best["P_safe_mc"],
            "c1_violation_worst": worst["c1_violation_rate"]}


def run_dual():
    pol_t = policy_array(0.5, "time")
    pol_s = policy_array(0.5, "safe")
    overlap = float((pol_t == pol_s).mean())

    def greedy_episode(rng, p2):
        pi, ri, w, t = 0, int(R0), 0, 0
        while t < T_MAX:
            best_a, best_key = None, None
            for a in ACTIONS:
                cons = consumption(a, w)
                if ri - cons * R_SCALE < 0:
                    continue
                key = (L - pi * STEP) / a
                if best_key is None or key < best_key:
                    best_key, best_a = key, a
            if best_a is None:
                return False, t
            ri = int(round(ri - consumption(best_a, w) * R_SCALE))
            pi = min(NPOS - 1, pi + int(round(best_a / STEP)))
            t += 1
            if pi == NPOS - 1:
                return True, t
            w = 1 if rng.random() < (p2 if w == 1 else P_GIVEN_BAD) else 0
        return False, t

    pol = policy_array(0.5, "time")
    rng = np.random.RandomState(42)
    safe_dp = 0
    safe_g = 0
    for _ in range(1000):
        r = simulate(0.5, pol, 1, np.random.RandomState(rng.randint(0, 2 ** 31)))
        safe_dp += r["P_safe_mc"]
        ok, _t = greedy_episode(rng, 0.5)
        safe_g += 1.0 if ok else 0.0
    return {"policy_overlap_ratio": overlap,
            "P_safe_dp": safe_dp / 1000.0,
            "P_safe_gain_vs_greedy": safe_dp / 1000.0 - safe_g / 1000.0}


EXPERIMENTS = {
    "EXP-2020B-C0-1": run_sensitivity,
    "EXP-2020B-C0-2": run_mc,
    "EXP-2020B-C0-3": run_extreme,
    "EXP-2020B-C1-1": run_sensitivity,
    "EXP-2020B-C1-2": run_mc,
    "EXP-2020B-C1-3": run_extreme,
    "EXP-2020B-C1-4": run_dual,
}

if __name__ == "__main__":
    exp = sys.argv[1]
    res = EXPERIMENTS[exp]()
    print(json.dumps({"experiment_id": exp, "metrics": res},
                     ensure_ascii=False, sort_keys=True))
