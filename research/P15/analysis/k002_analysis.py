# -*- coding: utf-8 -*-
"""P15-K002 正式分析：配对差 + bootstrap 95% CI（预注册规格 §4.1/§5）。
主终点 MCQ_primary=(L2+L3+L4)/33*100；次主 VAL_primary=L4/9*100。
block 级配对差（主检验 6 题），决策门=CI 下界>0 → positive（与 K001 相同）。
无 scipy：bootstrap 纯 random 实现。
"""
import collections
import glob
import json
import math
import os
import random

ROOT = "research/P15/experiments/P15-K002/runs"
SCORE_DIR = "research/P15/analysis/raw_k002/scores"
MAIN_PROBLEMS = ["2020_B", "2018_A", "2019_C", "2018_B", "2017_B", "2011_B"]
GEN_PROBLEMS = ["2022_C", "2024_A"]
ARMS = ["F", "S", "SV"]

# 盲评低 κ 维度（κ<0.6，来自 K002_BLIND_EVAL_REPORT）：敏感性分析剔除用
LOW_KAPPA_DIMS = ["L1.2", "L1.4", "L2.1", "L2.4", "L2.5", "L3.2", "L3.5", "L4.3", "L4.5"]
# L2 维度全集（rubric v1.1，L2 满分 15）：用于低 κ 剔除后重算 L2
L2_DIMS_ALL = ["L2.1", "L2.2", "L2.4", "L2.5", "L2.6", "L2.7"]
L3_DIMS_ALL = ["L3.1", "L3.2", "L3.3", "L3.4", "L3.5"]
L4_DIMS_ALL = ["L4.1", "L4.2", "L4.3", "L4.4", "L4.5"]
L2_MAX, L3_MAX, L4_MAX = 15.0, 9.0, 9.0


def load_all():
    rows = []
    for mf in glob.glob(f"{ROOT}/*/manifest.json"):
        sid = os.path.basename(os.path.dirname(mf))
        m = json.load(open(mf, encoding="utf-8"))
        sf = f"{SCORE_DIR}/{sid}.json"
        try:
            s = json.load(open(sf, encoding="utf-8"))
        except FileNotFoundError:
            print(f"[WARN] 缺评分: {sid}")
            continue
        vec = s["vector"]
        rows.append({
            "sid": sid, "arm": m["arm"], "problem": m["problem_id"],
            "rep": m.get("rep"), "block_role": m.get("block_role"),
            "coverage_complete": (m.get("coverage") or {}).get("complete", False),
            "L1": vec["L1_total"], "L2": vec["L2_total"],
            "L3": vec["L3_total"], "L4": vec["L4_total"],
            "dims": s["dimensions"], "evaluator": s.get("evaluator", {}).get("model"),
        })
    return rows


def mcq(r): return (r["L2"] + r["L3"] + r["L4"]) / (L2_MAX + L3_MAX + L4_MAX) * 100.0
def val(r): return r["L4"] / L4_MAX * 100.0


def dims_score(rows, keep_dims):
    """按保留维度重算 L2/L3/L4（用于低 κ 敏感性）。keep_dims: {'L2':[..],'L3':[..],'L4':[..]}"""
    out = []
    for r in rows:
        d = r["dims"]
        def total(prefix, full_max):
            keep = [k for k in keep_dims.get(prefix, [])]
            if not keep:
                return None
            s = sum(d[k]["score"] for k in keep if k in d)
            # 满分 = 按保留维度的原满分和（L2.6 权重 3，其余 2；L1.4 两档 1）
            mx = 0.0
            for k in keep:
                if k not in d:
                    continue
                if k == "L2.6":
                    mx += 3.0
                elif k == "L1.4":
                    mx += 1.0
                else:
                    mx += 2.0
            return s / mx * full_max
        L2r = total("L2", L2_MAX)
        L3r = total("L3", L3_MAX)
        L4r = total("L4", L4_MAX)
        out.append({**r, "L2": L2r, "L3": L3r, "L4": L4r})
    return out


def block_means(rows, problems):
    """每题×臂均值 → {problem: {arm: mean_mcq/mean_val/mean_L3}}"""
    tbl = {}
    for p in problems:
        tbl[p] = {}
        for a in ARMS:
            sub = [r for r in rows if r["problem"] == p and r["arm"] == a]
            if sub:
                tbl[p][a] = {
                    "mcq": sum(mcq(r) for r in sub) / len(sub),
                    "val": sum(val(r) for r in sub) / len(sub),
                    "L3": sum(r["L3"] for r in sub) / len(sub),
                    "n": len(sub),
                }
    return tbl


def paired_diffs(tbl, problems, metric, arm_a, arm_b):
    diffs = []
    valid = 0
    for p in problems:
        if arm_a in tbl[p] and arm_b in tbl[p]:
            diffs.append(tbl[p][arm_a][metric] - tbl[p][arm_b][metric])
            valid += 1
    return diffs, valid


def bootstrap_ci(diffs, n_iter=100000, alpha=0.05, seed=42):
    if len(diffs) < 2:
        return None, None, None, None
    rng = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(n_iter):
        s = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(s) / n)
    means.sort()
    lo = means[int(n_iter * alpha / 2)]
    hi = means[int(n_iter * (1 - alpha / 2))]
    return sum(diffs) / n, lo, hi, n


def report_rows(rows, problems, label):
    tbl = block_means(rows, problems)
    print(f"\n===== {label}（{len(problems)} 题）=====")
    for p in problems:
        cells = []
        for a in ARMS:
            if a in tbl[p]:
                e = tbl[p][a]
                cells.append(f"{a}: MCQ={e['mcq']:.1f} VAL={e['val']:.1f} L3={e['L3']:.1f}")
        print(f"  {p}: " + " | ".join(cells))
    for (a1, a2, metric, name) in [
        ("S", "F", "mcq", "RQ1 S−F(MCQ)"),
        ("SV", "S", "val", "RQ2 SV−S(VAL)"),
        ("SV", "F", "mcq", "补充 SV−F(MCQ)"),
        ("SV", "F", "val", "补充 SV−F(VAL)"),
        ("S", "F", "val", "补充 S−F(VAL)"),
    ]:
        diffs, valid = paired_diffs(tbl, problems, metric, a1, a2)
        if valid == 0:
            print(f"  {name}: 无配对")
            continue
        mu, lo, hi, n = bootstrap_ci(diffs)
        verdict = "POSITIVE" if (lo is not None and lo > 0) else ("NEGATIVE" if hi is not None and hi < 0 else "inclusive")
        print(f"  {name}: Δ={mu:+.2f} 95%CI=[{lo:+.2f},{hi:+.2f}] (block n={n}) → {verdict}")
    return tbl


def main():
    rows = load_all()
    print(f"载入 {len(rows)} 份评分")
    # coverage gate：预注册定义针对 MODEL_IR 的 problem_binding.sub_question_id（S/SV 臂）；
    # F 臂为自由文本（无 MODEL_IR），gate 不适用（N/A），纳入主终点（测量局限，如实报告）
    fail = [r for r in rows if r["arm"] != "F" and not r["coverage_complete"]]
    print(f"COVERAGE_FAIL: {len(fail)} 份（S/SV 臂，不进入主终点）；F 臂 gate N/A（无 MODEL_IR）")
    main_rows = [r for r in rows if r["problem"] in MAIN_PROBLEMS
                 and (r["arm"] == "F" or r["coverage_complete"])]
    gen_rows = [r for r in rows if r["problem"] in GEN_PROBLEMS
                and (r["arm"] == "F" or r["coverage_complete"])]

    # 主分析
    report_rows(main_rows, MAIN_PROBLEMS, "主检验 6 题（F 纳入 + S/SV coverage 通过）")
    report_rows(gen_rows, GEN_PROBLEMS, "泛化 2 题（观察）")

    # 敏感性 A：仅 S/SV（F 臂 N/A 敏感性——剔除 F 后 S/SV 配对）——即 SV−S 在 coverage 通过子集
    print("\n===== 敏感性 A：仅 coverage 通过的 S/SV（F 剔除）=====")
    sv_rows = [r for r in main_rows if r["arm"] != "F"]
    tbl_sv = block_means(sv_rows, MAIN_PROBLEMS)
    for p in MAIN_PROBLEMS:
        cells = []
        for a in ("S", "SV"):
            if a in tbl_sv[p]:
                e = tbl_sv[p][a]
                cells.append(f"{a}: MCQ={e['mcq']:.1f} VAL={e['val']:.1f} L3={e['L3']:.1f}")
        print(f"  {p}: " + " | ".join(cells))
    diffs, valid = paired_diffs(tbl_sv, MAIN_PROBLEMS, "val", "SV", "S")
    mu, lo, hi, n = bootstrap_ci(diffs)
    verdict = "POSITIVE" if (lo is not None and lo > 0) else ("NEGATIVE" if hi is not None and hi < 0 else "inclusive")
    print(f"  RQ2 SV−S(VAL): Δ={mu:+.2f} 95%CI=[{lo:+.2f},{hi:+.2f}] (block n={n}) → {verdict}")
    diffs, valid = paired_diffs(tbl_sv, MAIN_PROBLEMS, "mcq", "SV", "S")
    mu, lo, hi, n = bootstrap_ci(diffs)
    verdict = "POSITIVE" if (lo is not None and lo > 0) else ("NEGATIVE" if hi is not None and hi < 0 else "inclusive")
    print(f"  补充 SV−S(MCQ): Δ={mu:+.2f} 95%CI=[{lo:+.2f},{hi:+.2f}] (block n={n}) → {verdict}")

    # 敏感性 b：剔除低 κ 维度重算 MCQ
    keep = {"L2": [k for k in L2_DIMS_ALL if k not in LOW_KAPPA_DIMS],
            "L3": [k for k in L3_DIMS_ALL if k not in LOW_KAPPA_DIMS],
            "L4": [k for k in L4_DIMS_ALL if k not in LOW_KAPPA_DIMS]}
    print(f"\n===== 敏感性 B：剔除低 κ 维度（保留 {keep}）=====")
    sens_rows = dims_score(main_rows, keep)
    report_rows(sens_rows, MAIN_PROBLEMS, "主检验 6 题（低κ剔除）")

    # 敏感性 c：L3 地板（生成产物不含真实执行，L3 系统性低分）——仅 L2+L4 重算
    print("\n===== 敏感性 C：仅 L2+L4（去除 L3 执行层地板）=====")
    keep2 = {"L2": L2_DIMS_ALL, "L3": [], "L4": L4_DIMS_ALL}
    sens2_rows = dims_score(main_rows, keep2)
    # MCQ 公式改为 (L2+L4)/(15+9)*100
    for r in sens2_rows:
        r["_mcq24"] = (r["L2"] + r["L4"]) / (L2_MAX + L4_MAX) * 100.0
    tbl = {}
    for p in MAIN_PROBLEMS:
        tbl[p] = {}
        for a in ARMS:
            sub = [r for r in sens2_rows if r["problem"] == p and r["arm"] == a]
            if sub:
                tbl[p][a] = sum(r["_mcq24"] for r in sub) / len(sub)
    for p in MAIN_PROBLEMS:
        cells = []
        for a in ARMS:
            if a in tbl[p]:
                cells.append(f"{a}: {tbl[p][a]:.1f}")
        print(f"  {p}: " + " | ".join(cells))
    # 配对（手工，L2+L4）
    diffs, valid = [], 0
    for p in MAIN_PROBLEMS:
        sub = lambda a: [r for r in sens2_rows if r["problem"] == p and r["arm"] == a]
        sf = sub("S"); ff = sub("F")
        if sf and ff:
            diffs.append(sum(r["_mcq24"] for r in sf)/len(sf) - sum(r["_mcq24"] for r in ff)/len(ff))
            valid += 1
    mu, lo, hi, n = bootstrap_ci(diffs)
    verdict = "POSITIVE" if lo is not None and lo > 0 else ("NEGATIVE" if hi is not None and hi < 0 else "inclusive")
    print(f"  RQ1 S−F(L2+L4): Δ={mu:+.2f} 95%CI=[{lo:+.2f},{hi:+.2f}] (n={n}) → {verdict}")
    diffs, valid = [], 0
    for p in MAIN_PROBLEMS:
        sub = lambda a: [r for r in sens2_rows if r["problem"] == p and r["arm"] == a]
        svf = sub("SV"); ff = sub("F")
        if svf and ff:
            diffs.append(sum(r["_mcq24"] for r in svf)/len(svf) - sum(r["_mcq24"] for r in ff)/len(ff))
            valid += 1
    mu, lo, hi, n = bootstrap_ci(diffs)
    verdict = "POSITIVE" if lo is not None and lo > 0 else ("NEGATIVE" if hi is not None and hi < 0 else "inclusive")
    print(f"  补充 SV−F(L2+L4): Δ={mu:+.2f} 95%CI=[{lo:+.2f},{hi:+.2f}] (n={n}) → {verdict}")


if __name__ == "__main__":
    main()
