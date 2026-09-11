#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_value.py —— 候选池的边际价值：「先验锁死一个候选」要付多少代价（M-SELECT-003）。

承 M-SELECT-002（RING / SPIRAL / AIFIX 在真实 Mock 上的三候选配对对照）之上，
回答 Harness 自身答不了的那个问题：

    如果候选池被先验收敛到单一候选，与「全池都跑过、按期望选」相比差多少？

这正是 ADR-0016 记录的机制（`handlers.py:1876-1879` 只取 `cands[0]`）的**代价量化**。

口径（ADR-0012：跨实现比较前必须归一口径）
------------------------------------------
- **固定候选策略**：真实场景必须在**看到 seed 之前**选定候选，故可比量是候选的
  **期望 T_total**（mean over seeds）。per-seed 最优是信息泄漏下的下界，不是成绩。
  （M-SELECT-002 数据里 Q4 seed42 最快的候选是 AIFIX，而按期望最优的是 SPIRAL，
  这正是该口径不可省略的实证。）
- **差距的显著性**：与配对 95% CI 比；落在 CI 内 ⇒ 标 `significant=False`，
  不得把噪声报成「损失」。

诚实边界
--------
本分析只测**选择层**的边际价值（候选已生成、只是没被选）。它**不测生成层**：
候选是人给定的，Harness 能否自己生成非常规候选是另一个问题，不在本模块结论范围。

运行：``py -3.12 -X utf8 -m pool_value``
输出：``artifacts/results/pool_value.json`` + 并入 ``all_results.json`` 台账
（供模型描述文档的数值追溯——同 solve_b_http / candidate_select 的既有惯例）。
"""
from __future__ import annotations

import itertools
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _paired_ci(paired: dict, a: str, b: str):
    """取 a、b 两候选的配对 95% CI 半宽（键顺序无关）；无记录 → None。"""
    for key in (f"{a}|{b}", f"{b}|{a}"):
        rec = paired.get(key)
        if isinstance(rec, dict):
            v = rec.get("delta_ci95_halfwidth_s")
            if v is not None:
                return float(v)
    return None


def pool_value(questions: dict) -> dict:
    """从 M-SELECT-002 风格的逐候选聚合数据算池价值。

    ``questions[label] = {"candidates": {name: {"T_total_s": ...}},
                          "paired": {"A|B": {"delta_ci95_halfwidth_s": ...}}}``
    """
    out: dict = {}
    for label, q in (questions or {}).items():
        cands = (q or {}).get("candidates") or {}
        means = {n: float(c["T_total_s"]) for n, c in cands.items()
                 if isinstance(c, dict) and c.get("T_total_s") is not None}
        if not means:
            continue
        paired = (q or {}).get("paired") or {}
        ranked = sorted(means, key=lambda n: (means[n], n))
        best, best_t = ranked[0], means[ranked[0]]

        # 全部子集枚举（候选数很少，穷举可行且客观——不引入「加入顺序」假设）
        subsets = []
        for r in range(1, len(ranked) + 1):
            for combo in itertools.combinations(ranked, r):
                pool = list(combo)
                b = min(pool, key=lambda n: (means[n], n))
                gap = means[b] - best_t
                ci = _paired_ci(paired, b, best) if b != best else 0.0
                subsets.append({
                    "pool": pool,
                    "best": b,
                    "best_mean_T": means[b],
                    "abs_gap_vs_full_s": gap,
                    "paired_ci95_halfwidth_s": ci,
                    "significant": bool(b != best and ci is not None and gap > ci),
                })

        worst_name = max(means, key=lambda n: (means[n], n))
        w_gap = means[worst_name] - best_t
        w_ci = _paired_ci(paired, worst_name, best) if worst_name != best else 0.0
        out[label] = {
            "candidate_mean_T": means,
            "ranked_by_mean": ranked,
            "best_candidate": best,
            "best_mean_T": best_t,
            "worst_single_pool": {
                "candidate": worst_name,
                "mean_T": means[worst_name],
                "abs_loss_s": w_gap,
                # 两个口径都给（避免「相对谁」含糊——ADR-0012 的同类教训）
                "rel_loss_vs_best": (w_gap / best_t) if best_t else None,
                "rel_loss_vs_self": (w_gap / means[worst_name]
                                     if means[worst_name] else None),
                "paired_ci95_halfwidth_s": w_ci,
                "significant": bool(worst_name != best and w_ci is not None
                                    and w_gap > w_ci),
            },
            "subsets": subsets,
        }
    return out


def _merge_into_all_results(report: dict) -> None:
    """并入项目根结果台账（供数值追溯：模型描述文档引用的数字可溯源）。"""
    allres = HERE.parent.parent / "all_results.json"
    data: dict = {}
    if allres.exists():
        try:
            data = json.loads(allres.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    seg: dict = {"milestone": "M-SELECT-003",
                 "scope": "selection-layer only（候选由人给定；不测生成层）"}
    for label, v in report.items():
        seg[f"{label}_best_candidate"] = v["best_candidate"]
        seg[f"{label}_best_mean_total_time_s"] = v["best_mean_T"]
        w = v["worst_single_pool"]
        seg[f"{label}_worst_single_pool_candidate"] = w["candidate"]
        seg[f"{label}_worst_single_pool_abs_loss_s"] = w["abs_loss_s"]
        seg[f"{label}_worst_single_pool_rel_loss_vs_best"] = w["rel_loss_vs_best"]
        # 百分比形态也落账：模型描述文档按「23.6%」书写，L4 数值追溯按字面取数，
        # 只落小数形态（0.2361）会对不上（容差为相对 0.5%）。
        if w["rel_loss_vs_best"] is not None:
            seg[f"{label}_worst_single_pool_rel_loss_vs_best_pct"] = round(
                w["rel_loss_vs_best"] * 100.0, 2)
        if w["rel_loss_vs_self"] is not None:
            seg[f"{label}_worst_single_pool_rel_loss_vs_self_pct"] = round(
                w["rel_loss_vs_self"] * 100.0, 2)
        seg[f"{label}_worst_single_pool_ci95_halfwidth_s"] = (
            w["paired_ci95_halfwidth_s"])
        seg[f"{label}_worst_single_pool_significant"] = w["significant"]
    data["candidate_pool_value"] = seg
    allres.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"[OK] 已并入 {allres} 的 candidate_pool_value 段")


def main() -> int:
    # 优先读最新一轮（M-SELECT-003 四候选）；没有则回退 M-SELECT-002 的三候选产物
    for name in ("candidate_selection_m3.json", "candidate_selection_m2.json"):
        src = HERE.parent / "results" / name
        if src.exists():
            break
    if not src.exists():
        print(f"[FAIL] 缺少输入 {src}；先跑 candidate_select --trials 5")
        return 1
    out = json.loads(src.read_text(encoding="utf-8"))
    print(f"[输入] {src.name}（milestone={out.get('milestone')}，"
          f"候选={out.get('candidates')}）")
    report = pool_value(out.get("questions") or {})

    for label, v in report.items():
        w = v["worst_single_pool"]
        verdict = "显著" if w["significant"] else "不显著（落在 95% CI 内）"
        print(f"[{label}] 期望最优 = {v['best_candidate']} ({v['best_mean_T']:.1f} s)")
        print(f"    先验锁死为最差候选 {w['candidate']} → 代价 {w['abs_loss_s']:.1f} s "
              f"(相对最优 {w['rel_loss_vs_best']:.1%}, "
              f"相对自身 {w['rel_loss_vs_self']:.1%})；"
              f"CI±{w['paired_ci95_halfwidth_s']:.1f} → {verdict}")

    p = HERE.parent / "results" / "pool_value.json"
    os.makedirs(p.parent, exist_ok=True)
    p.write_text(json.dumps({"milestone": "M-SELECT-003",
                             "source": "candidate_selection_m2.json",
                             "questions": report}, ensure_ascii=False, indent=2),
                 encoding="utf-8")
    print(f"[OK] {p}")
    _merge_into_all_results(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
