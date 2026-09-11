#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""协议 Mock 演练强度扩容 + 误差分析（verifier 产出，不改被测代码）。

背景 / 为什么需要
-----------------
对比组 b_win 的验证强度自述为「5500 局蒙特卡洛」；本实例的协议 Mock 演练此前只有
5 局（solve_b_http.run_trials_mock 的默认与 main() 都取 n_trials=5），且只报点估计
（均值/最小值），没有标准差、分位数或置信区间——不足以支撑「清除比例稳定 = 1.0」
这类结论（5 局的 1.0 与 100 局的 1.0 是不同强度的证据）。

本脚本在**已提交的 297ba6d 代码之上**（只 import run_trials_mock，不修改任何被测
实现）把协议 Mock 演练从 5 局提到 N 局（默认 100，种子自 42 起连续），对每问报告：
  * 清除比例（cleared_fraction）：均值 ± 标准差、最小、分位数、95% 置信区间
  * 摊薄口径 avg_locate_clear_time_s（= 虚拟总时间 / 已清除源数，ADR-0012）：同上
  * 辅助量：n_measure、move_dist_m、virtual_time_s

统计口径
--------
  * 标准差取**样本标准差**（n−1 分母），与「多种子重复实验」的语义一致。
  * 95% 置信区间用 t 分布（df=n−1）的均值 CI：mean ± t_{0.975,df}·s/√n；
    正态近似在 n=100 下几乎相同，但小 n 时 t 更稳妥。
  * 分位数用线性插值（numpy 默认 'linear'，与 statistics.quantiles 口径一致）。

运行：py -3.12 -X utf8 -m verify_protocol_mock_scale --trials 100
输出：projects/cumcm2026b/artifacts/protocol_mock_scale.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import solve_b_http as H  # noqa: E402  被测实现（只调用 run_trials_mock）

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.abspath(os.path.join(HERE, "..", "protocol_mock_scale.json"))

SEED = 42

# t_{0.975, df} 的双侧 95% 区间系数（df = n−1）。n=100 → df=99。
_T95 = {
    4: 2.776445, 5: 2.570582, 9: 2.262157, 14: 2.144787,
    19: 2.093024, 29: 2.045230, 49: 2.009575, 99: 1.984217,
    199: 1.971896, 499: 1.964729,
}


def _t95(df: int) -> float:
    """双侧 95% t 系数；不在表中则取最接近的上界，缺省用正态 1.96。"""
    if df in _T95:
        return _T95[df]
    keys = sorted(_T95)
    for k in keys:
        if df <= k:
            return _T95[k]
    return 1.959964


def _quantile(sorted_v, q):
    """线性插值分位数（与 numpy.quantile 默认口径一致）。"""
    if not sorted_v:
        return float("nan")
    if len(sorted_v) == 1:
        return float(sorted_v[0])
    pos = (len(sorted_v) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_v[lo])
    frac = pos - lo
    return float(sorted_v[lo] * (1 - frac) + sorted_v[hi] * frac)


def _stats(values):
    """均值 ± 样本标准差 + 分位数 + t 95% CI。"""
    n = len(values)
    if n == 0:
        return {"n": 0}
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if n >= 2 else 0.0
    sv = sorted(values)
    half = _t95(n - 1) * sd / math.sqrt(n) if n >= 2 else 0.0
    return {
        "n": n,
        "mean": mean,
        "std_sample": sd,
        "min": float(min(values)),
        "max": float(max(values)),
        "median": _quantile(sv, 0.5),
        "q2_5": _quantile(sv, 0.025),
        "q25": _quantile(sv, 0.25),
        "q75": _quantile(sv, 0.75),
        "q97_5": _quantile(sv, 0.975),
        "ci95_halfwidth": half,
        "ci95_low": mean - half,
        "ci95_high": mean + half,
    }


def _augment(rec, cleared_frac):
    """从单局记录抽取本脚本所需字段。"""
    n_cleared = rec["n_cleared"]
    return {
        "seed": rec["seed"],
        "cleared_fraction": cleared_frac,
        "n_cleared": n_cleared,
        "total_sources": rec["total_sources"],
        "virtual_time_s": rec["virtual_time_s"],
        "avg_locate_clear_time_s": (
            rec["virtual_time_s"] / n_cleared if n_cleared else float("inf")),
        "mean_locate_clear_time_s": rec["mean_locate_clear_time_s"],
        "n_measure": rec["n_measure"],
        "move_dist_m": rec["move_dist_m"],
    }


def run_question(kind_mix, n_trials, base_port, label):
    """对一问跑 N 局，返回逐局 + 汇总统计。"""
    summary, recs = H.run_trials_mock(n_trials=n_trials, kind_mix=kind_mix,
                                      seed=SEED, base_port=base_port)
    per = [_augment(r, r["cleared_fraction"]) for r in recs]

    def col(key):
        return [r[key] for r in per if math.isfinite(r[key])]

    block = {
        "label": label,
        "kind_mix": kind_mix,
        "n_trials": n_trials,
        "seed_start": SEED,
        "seed_end": SEED + n_trials - 1,
        "cleared_fraction": _stats(col("cleared_fraction")),
        "avg_locate_clear_time_s": _stats(col("avg_locate_clear_time_s")),
        "mean_locate_clear_time_s": _stats(col("mean_locate_clear_time_s")),
        "virtual_time_s": _stats(col("virtual_time_s")),
        "n_measure": _stats(col("n_measure")),
        "move_dist_m": _stats(col("move_dist_m")),
        "n_cleared_total": sum(r["n_cleared"] for r in per),
        "n_sources_total": sum(r["total_sources"] for r in per),
        "run_trials_mock_summary": summary,
        "per_trial": per,
    }
    return block


def main(trials=100):
    out = {
        "script": "verify_protocol_mock_scale.py",
        "protocol": "CUMCM2026B 附件2 HTTP+JSON（本地 Mock）",
        "seed_policy": f"固定 42，{trials} 局取 seed 42..{SEED + trials - 1} 连续",
        "std_convention": "样本标准差（n−1）",
        "ci_convention": "均值 t 分布双侧 95% CI（df=n−1）",
        "n_trials": trials,
    }
    out["q3_omni"] = run_question(False, trials, 2300, "Q3 全向")
    out["q4_mix"] = run_question(True, trials, 2350, "Q4 混合")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    for key in ("q3_omni", "q4_mix"):
        b = out[key]
        cf = b["cleared_fraction"]
        ac = b["avg_locate_clear_time_s"]
        print(f"[{b['label']}] N={b['n_trials']} seeds {b['seed_start']}..{b['seed_end']}")
        print(f"  清除比例  mean±sd = {cf['mean']:.6f} ± {cf['std_sample']:.6f}  "
              f"min={cf['min']:.6f}  95%CI=[{cf['ci95_low']:.6f},{cf['ci95_high']:.6f}]")
        print(f"  摊薄 avg_locate_clear  mean±sd = {ac['mean']:.3f} ± {ac['std_sample']:.3f} s  "
              f"[{ac['q2_5']:.1f},{ac['q97_5']:.1f}] (2.5–97.5%)")
        print(f"  已清除源/总源 = {b['n_cleared_total']}/{b['n_sources_total']}")
    print(f"[OK] {OUT_PATH}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=100)
    a = ap.parse_args()
    raise SystemExit(main(trials=a.trials))
