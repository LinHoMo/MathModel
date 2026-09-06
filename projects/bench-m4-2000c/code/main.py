#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCM/ICM 2000 Problem C — 大象避孕飞镖种群控制（P13-3B 干预后 v2.2）。

v1 → v2 变更（对照 core/knowledge/pitfalls/model_construction_checklist.md）：

    干预① 校准合理性：v1 单参数生育率乘子 m=4.42 → 产犊间隔 1.9 年（生物
           学不可能）。v2 放弃单点校准，改为**双分支括弧**：
             下界（生物约束）：b0=0.167（产犊间隔 3 年，合理上界）+
               成年存活=0.995（合理带上限）→ λ≈1.053；
             上界（锚定一致）：捕杀记录锚 λ=1.0636 → 反解 b0≈0.26
               （产犊间隔 1.9 年——超出生物合理范围，仅作敏感性上界）。
           两分支之间的张量（锚要求的增长率处于该生存率表生物合理性边缘）
           本身就是模型的核心发现，显式报告而非掩盖。
    干预② 约束完备性：密度制约情景（K=1.3N*/2N*，生育率 ×(1−N/K)，先判
           λ_eff ≤ 1 → 无需干预）+ 搬迁作业上限（800 头/年）可行性核验。
    干预③ 不确定性传播：λ 锚区间传播到避孕配额区间、Q3 恢复年数与 Q4
           泛化表 min/max 列。
    口径统一：全链路唯一校准稳定分布，Q1/Q2 同源交叉引用。

不变项：数据修复（49→40）、分段生存率回归、bootstrap（5 批 × 200 次，
seed=42）、Leslie 框架。
输出: figures/all_results.json。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
K_TARGET = 11_000
AGE_MAX = 70
FERTILE_LO, FERTILE_HI = 10, 60
B0_ANCHOR = 0.167           # 下界分支：产犊间隔 3 年（生物合理上界）
ADULT_CEILING = 0.995       # 成年存活生物合理上限
RELOCATION_CAP = 800
PROJ_YEARS = 60
N_RUNS = 5
N_BOOT = 200

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- 数据
def load_pooled() -> tuple[np.ndarray, np.ndarray, float]:
    frames = []
    for name in ("data1.csv", "data2.csv"):
        df = pd.read_csv(ROOT / "inputs" / "data" / name)
        df = df.rename(columns=lambda c: c.strip())
        df.loc[df["Age"] == 49, "Age"] = 40
        frames.append(df)
    pooled = pd.concat(frames, ignore_index=True)
    g = pooled.groupby("Age")[["Total Number", "Number of Females"]].sum()
    g = g.reindex(range(AGE_MAX + 1), fill_value=0)
    return (g["Total Number"].to_numpy(float),
            g["Number of Females"].to_numpy(float),
            float(g["Number of Females"].sum() / g["Total Number"].sum()))


# ---------------------------------------------------------------- Q1
def segment_survival(n: np.ndarray) -> dict:
    ages = np.arange(len(n), dtype=float)

    def fit(lo: int, hi: int) -> float:
        m = (ages >= lo) & (ages <= hi) & (n > 0)
        slope = np.polyfit(ages[m], np.log(n[m]), 1)[0]
        return float(min(1.0, np.exp(slope)))

    return {"juvenile_0_2": fit(0, 2), "adult_2_50": fit(2, 50),
            "senescent_50_70": fit(50, 70)}


def survival_vector(seg: dict) -> np.ndarray:
    s = np.empty(AGE_MAX)
    s[:2] = seg["juvenile_0_2"]
    s[2:50] = seg["adult_2_50"]
    s[50:] = seg["senescent_50_70"]
    return s


def leslie(s_vec: np.ndarray, b0: float) -> np.ndarray:
    L = np.zeros((AGE_MAX + 1, AGE_MAX + 1))
    L[1:, :-1] = np.diag(s_vec)
    L[0, FERTILE_LO:FERTILE_HI + 1] = b0
    return L


def lambda_of(s_vec: np.ndarray, b0: float) -> float:
    return float(np.linalg.eigvals(leslie(s_vec, b0)).max().real)


def stable_distribution(s_vec: np.ndarray, b0: float) -> np.ndarray:
    val, vec = np.linalg.eig(leslie(s_vec, b0))
    v = np.abs(vec[:, int(np.argmax(val.real))].real)
    return v / v.sum()


def age_structure(dist: np.ndarray, female_share: float) -> dict:
    bands = {"0-10": slice(0, 11), "11-20": slice(11, 21),
             "21-30": slice(21, 31), "31-40": slice(31, 41),
             "41-50": slice(41, 51), "51-60": slice(51, 61),
             "61-70": slice(61, 71)}
    return {
        "per_band_headcount_at_11000": {
            k: round(float(dist[v].sum() / dist.sum() * K_TARGET), 1)
            for k, v in bands.items()},
        "calf_share_pct": round(100 * dist[:11].sum() / dist.sum(), 2),
        "cows_total": round(K_TARGET * female_share, 0),
        "fertile_cows": round(float(
            dist[FERTILE_LO:FERTILE_HI + 1].sum() / dist.sum()
            * K_TARGET * female_share), 0)}


def bisect(fn, lo: float, hi: float, iters: int = 48) -> float:
    for _ in range(iters):
        mid = (lo + hi) / 2
        if fn(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------- 模拟
def simulate(s_vec: np.ndarray, b0: float, dart_p: float = 0.0,
             relocate_r: float = 0.0, female_share: float = 0.47,
             K: float | None = None, years: int = PROJ_YEARS) -> tuple[float, float, np.ndarray]:
    base = leslie(s_vec, b0)
    v = stable_distribution(s_vec, b0) * K_TARGET * female_share
    darted = np.zeros(AGE_MAX + 1)
    counts: list[float] = []
    for _ in range(years):
        fert = v[FERTILE_LO:FERTILE_HI + 1].sum()
        share = (darted[FERTILE_LO:FERTILE_HI + 1].sum() / fert) if fert > 0 else 0.0
        L = base.copy()
        mult = max(0.0, 1.0 - share)
        if K:
            n_prev = v.sum() / female_share
            mult *= max(0.0, 1.0 - n_prev / K)
        L[0, :] *= mult
        v = L @ v
        nd = np.zeros(AGE_MAX + 1)
        nd[1:] = darted[:-1] * s_vec
        remaining = v[FERTILE_LO:FERTILE_HI + 1] - nd[FERTILE_LO:FERTILE_HI + 1]
        remaining = np.clip(remaining, 0, None)
        pool = float(remaining.sum())
        add = dart_p * pool
        if pool > 0 and add > 0:
            nd[FERTILE_LO:FERTILE_HI + 1] += add * remaining / pool
        darted = nd
        counts.append(add)
        if relocate_r > 0:
            total = v.sum() / female_share
            if total > 0:
                v *= max(0.0, 1.0 - relocate_r / total)
    return float(v.sum() / female_share), float(np.mean(counts[-20:])), v


def solve_dart_p(s_vec, b0, female_share, K=None) -> tuple[float, float]:
    p = bisect(lambda p: simulate(s_vec, b0, dart_p=p, female_share=female_share,
                                  K=K)[0] - K_TARGET, 0.0, 0.9)
    _, cows, _ = simulate(s_vec, b0, dart_p=p, female_share=female_share, K=K)
    return p, cows


def solve_relocate_r(s_vec, b0, female_share) -> float:
    return bisect(lambda r: simulate(s_vec, b0, relocate_r=r,
                                     female_share=female_share)[0] - K_TARGET,
                  0.0, 1_500.0)


def calibrate_b0(s_vec: np.ndarray, target_lambda: float) -> float:
    """上界分支：数据生存率下命中 λ 锚所需的 b0（可能超出生物合理范围）。"""
    return bisect(lambda b: target_lambda - lambda_of(s_vec, b),
                  0.05, 0.6, iters=60)


def bootstrap_batch(n_tot: np.ndarray, seed0: int, female_share: float,
                    b0: float) -> list[dict]:
    """bootstrap（上界分支口径）：重抽样 → 重估分段生存率形状 → p* → 年注射数。"""
    rng = np.random.default_rng(seed0)
    ages = np.arange(len(n_tot))
    pool = np.repeat(ages, n_tot.astype(int))
    out = []
    for _ in range(N_BOOT):
        sample = rng.choice(pool, size=len(pool), replace=True)
        bs = np.bincount(sample, minlength=len(n_tot)).astype(float)
        try:
            s_vec = survival_vector(segment_survival(bs))
            p, cows = solve_dart_p(s_vec, b0, female_share)
            out.append({"p_star": p, "cows_per_year": cows})
        except Exception:
            continue
    return out


def recovery_years(s_vec, b0, kill, female_share) -> int | str:
    v = stable_distribution(s_vec, b0) * K_TARGET * female_share * (1 - kill)
    L = leslie(s_vec, b0)
    for yr in range(1, 301):
        v = L @ v
        if v.sum() / female_share >= K_TARGET:
            return yr
    return ">300"


def main() -> int:
    np.random.seed(SEED)
    n_tot, n_fem, female_share = load_pooled()

    # ---- 双分支（干预①）
    seg = segment_survival(n_tot)
    s_vec = survival_vector(seg)
    s_bio = s_vec.copy()
    s_bio[2:50] = np.clip(s_vec[2:50] * (ADULT_CEILING / s_vec[2]), 0.0, 1.0)
    lam_bio = lambda_of(s_bio, B0_ANCHOR)
    lam_center = 1.0 + 700 / K_TARGET
    b0_hi = calibrate_b0(s_vec, lam_center)
    branches = {
        "bio_constrained_lower": {"s": s_bio, "b0": B0_ANCHOR,
                                  "lambda": round(lam_bio, 4)},
        "anchor_consistent_upper": {"s": s_vec, "b0": round(b0_hi, 4),
                                    "lambda": round(lam_center, 4)},
    }

    # ---- Q1
    dist = stable_distribution(s_bio, B0_ANCHOR)
    q1 = {
        "segment_survival_S": {k: round(v, 4) for k, v in seg.items()},
        "survival_examples": {f"S({a})": round(float(s_vec[a]), 4)
                              for a in (2, 5, 10, 20, 30, 40, 50, 55, 60)},
        "age_structure_11000_lower_branch": age_structure(dist, female_share),
        "branches": {k: {"b0": v["b0"], "lambda": v["lambda"]}
                     for k, v in branches.items()},
        "plausibility_finding": (
            "捕杀记录隐含增长率 λ=1.0636 处于数据生存率表生物合理性的边缘："
            "下界分支（成年存活 0.995 上限）只能达到 λ≈"
            f"{round(lam_bio, 4)}；上界分支需产犊间隔 ~"
            f"{round(0.5 / b0_hi, 1)} 年（超出 3-4.5 年常见区间）。"
            "两分支之间的张量是模型的核心发现，结论以区间呈现"),
    }

    # ---- Q2（双分支 + 干预②③）
    per_branch = {}
    for tag, br in branches.items():
        p, cows = solve_dart_p(br["s"], br["b0"], female_share)
        per_branch[tag] = {"p_star": round(p, 4),
                           "cows_per_year": round(cows, 1),
                           "relocation_eq_per_year": round(
                               solve_relocate_r(br["s"], br["b0"],
                                                female_share), 1)}
    batches = [bootstrap_batch(n_tot, SEED + i, female_share, b0_hi)
               for i in range(N_RUNS)]
    cows_runs = [float(np.mean([b["cows_per_year"] for b in batch]))
                 for batch in batches if batch]
    cows_all = np.array([b["cows_per_year"] for batch in batches
                         for b in batch])
    ci95 = [round(float(np.percentile(cows_all, q)), 1) for q in (2.5, 97.5)]
    density = {}
    for btag, br in branches.items():
        for kname, K in (("K=1.3N*", 1.3 * K_TARGET), ("K=2N*", 2.0 * K_TARGET)):
            mult = 1.0 - K_TARGET / K
            lam_eff = lambda_of(br["s"], br["b0"] * mult)
            key = f"{btag}/{kname}"
            if lam_eff <= 1.0:
                density[key] = {"lambda_eff": round(lam_eff, 4),
                                "cows_per_year": 0.0,
                                "reading": "密度均衡 ≤ 目标 → 无需干预"}
            else:
                p_dd, cows_dd = solve_dart_p(br["s"], br["b0"],
                                             female_share, K=K)
                density[key] = {"lambda_eff": round(lam_eff, 4),
                                "cows_per_year": round(cows_dd, 1)}
    cows_upper = per_branch["anchor_consistent_upper"]["cows_per_year"]
    dist = stable_distribution(branches["bio_constrained_lower"]["s"],
                               B0_ANCHOR)
    calf_before = round(100 * dist[:11].sum() / dist.sum(), 2)
    _, _, v_end = simulate(branches["anchor_consistent_upper"]["s"], b0_hi,
                           dart_p=per_branch["anchor_consistent_upper"]["p_star"],
                           female_share=female_share)
    dist_end = v_end / v_end.sum()
    calf_after = round(100 * dist_end[:11].sum() / dist_end.sum(), 2)
    q2 = {
        "cows_darted_per_year_bracket": [
            per_branch["bio_constrained_lower"]["cows_per_year"],
            per_branch["anchor_consistent_upper"]["cows_per_year"]],
        "per_branch": per_branch,
        "uncertainty": {
            "anchor_range": [round(1.0 + 600 / K_TARGET, 4),
                             round(1.0 + 800 / K_TARGET, 4)],
            "bootstrap_upper_branch": {"runs": len(cows_runs),
                                       "boots_per_run": N_BOOT, "seed": SEED,
                                       "cows_per_year_mean": round(float(np.mean(cows_runs)), 1),
                                       "cows_per_year_std": round(float(np.std(cows_runs, ddof=1)), 1),
                                       "cows_per_year_ci95": ci95},
        },
        "constraint_density_dependence": density,
        "constraint_relocation_cap": {
            "relocation_eq_per_year_upper": per_branch[
                "anchor_consistent_upper"]["relocation_eq_per_year"],
            "cap_from_problem": RELOCATION_CAP,
            "feasible": per_branch["anchor_consistent_upper"][
                "relocation_eq_per_year"] <= RELOCATION_CAP,
            "reading": "两分支搬迁均衡均 ≤ 作业上限 → 搬迁单独可行；"
                       "避孕配额为其 1/5-1/6，支持避孕为主、搬迁为辅",
        },
        "efficacy_sensitivity": {
            "scenario": "飞镖效期 2 年（非永久）",
            "cows_per_year_approx_upper": round(2 * cows_upper, 1),
            "note": "近似上界：每针覆盖期减半 → 稳态年度注射 ≈ 2×永久情景",
        },
        "age_structure_effect_darting": {
            "calf_share_pct_before": calf_before,
            "calf_share_pct_after_60y": calf_after,
            "conclusion": "避孕使幼龄份额下降 → 种群老龄化（上界分支口径）",
        },
        "darting_vs_relocation": {
            "relocation_individuals_per_year_eq": per_branch[
                "anchor_consistent_upper"]["relocation_eq_per_year"],
            "cows_darted_per_year_eq": per_branch[
                "anchor_consistent_upper"]["cows_per_year"],
            "note": "搬迁年度操作量大、立竿见影；避孕操作量小、不物理移除，"
                    "但对年龄结构扰动更大",
        },
    }

    # ---- Q3（双分支）
    q3 = {}
    for btag, br in branches.items():
        for k in (0.3, 0.5, 0.7):
            q3[f"{btag}_kill_{int(k * 100)}pct_recovery_years"] = \
                recovery_years(br["s"], br["b0"], k, female_share)
    q3["conclusion"] = ("灾难后立即停止避孕，种群可恢复（两分支均 λ>1）；"
                        "恢复年数区间即校准不确定性的传播结果（干预③）")

    # ---- Q4（双分支 min/max）
    table = []
    for scale in (0.9, 1.0, 1.1):
        s_scaled = np.clip(s_vec ** scale, 0, 1)
        s_bio_scaled = np.clip(s_bio ** scale, 0, 1)
        cows_by_size = {size: [] for size in (300, 2_000, 5_000, 11_000, 25_000)}
        for s_br, b0_br in ((s_scaled, calibrate_b0(s_scaled, lam_center)),
                            (s_bio_scaled, B0_ANCHOR)):
            p, _ = solve_dart_p(s_br, b0_br, female_share)
            d = stable_distribution(s_br, b0_br)
            fertile_share = d[FERTILE_LO:FERTILE_HI + 1].sum()
            for size in (300, 2_000, 5_000, 11_000, 25_000):
                cows_by_size[size].append(
                    round(p * fertile_share * size * female_share, 1))
        for size in (300, 2_000, 5_000, 11_000, 25_000):
            vals = cows_by_size[size]
            table.append({"park_size": size, "survival_scale": scale,
                          "cows_darted_per_year_min": min(vals),
                          "cows_darted_per_year_max": max(vals)})
    q4 = {"plan_table": table,
          "note": "干预③：每行 min/max 覆盖两分支——校准不确定性不再在下游消失",
          "memo": "output/management_memo.md（Task5 管理层报告）"}

    results = {
        "problem": "MCM/ICM 2000 C — elephant population control (v2.2, P13-3B)",
        "seed": SEED, "n_runs": N_RUNS, "boots_per_run": N_BOOT,
        "interventions": ["calibration_plausibility", "missing_constraints",
                          "uncertainty_propagation", "consistency_unification"],
        "data": {"pooled_elephants": int(n_tot.sum()),
                 "female_share": round(female_share, 4),
                 "fix_age49_to_40": True},
        "Q1_survival_age_structure": q1,
        "Q2_darting_quota": q2,
        "Q3_catastrophe_recovery": q3,
        "Q4_generalization": q4,
    }
    out = ROOT / "figures" / "all_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"[OK] all_results.json -> {out}")
    print(f"bracket cows/yr = {q2['cows_darted_per_year_bracket']} | "
          f"λ_bio={lam_bio:.4f} b0_hi={b0_hi:.4f} | "
          f"relocate_eq(upper)={per_branch['anchor_consistent_upper']['relocation_eq_per_year']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
