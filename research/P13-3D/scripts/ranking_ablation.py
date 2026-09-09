#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ranking_ablation.py — P13-2 Retriever 排序权重消融（守卫式影子评分器）。

回答的问题（P13_1_REPORT §5）：当前 ranking 为什么系统性地把语义匹配更强
的方法压下去？哪一组权重原则能让人语义正确的方法稳定进入 top-1？

方法：
  1. 影子评分器完整复刻 runtime/knowledge/retriever.py 的 recommend()
     + _capability_match 打分路径；**守卫**：基线权重下排序必须与真实
     retriever 逐卡一致，否则拒绝运行（防影子漂移）。
  2. 变体（P13-2 落地后：V0 = runtime 现状 w_sem=6，守卫基准；
     V1 = 落地前 w_sem=3 留作 A/B 对照；其余为先验变体）：
       V0 落地基线                   w_sem=6,  app=(20,4,cap40), qscale=1.0
       V1 落地前对照                 w_sem=3
       V2 适配基线压平               w_sem=6, app=(10,2,cap20)
       V3 质量维度减半               w_sem=6, qscale=0.5
  3. 评价：case 文件（features + 预注册 GT）× 变体 → top-1/top-3 GT 命中；
     反向检查（评价类 case）确保 AHP/TOPSIS 在语义再平衡后仍然 top-1。

决策规则（预注册）：按 V1→V2→V3→V4→V5 取**最简单**的、同时满足
  (a) 2000C top-1 GT 命中  (b) 2023C top-1 GT 命中  (c) 反向检查通过
的变体；都不满足 → 如实报告并停止（不加权重、不造新层）。

用法: python core/tools/ranking_ablation.py [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT / "core" / "tools" / "evaluation"))

from runtime.knowledge.retriever import (  # noqa: E402
    KnowledgeRetriever, _cond_key, _cond_satisfied, SAMPLE_ORDER)
from e2e_metrics import _load_card_names, _method_hit  # noqa: E402

E2E_DIR = ROOT / "core" / "knowledge" / "bench" / "e2e"
CASES = ["case_2000C_global.json", "case_2023C_global.json",
         "case_reverse_evaluation.json"]

SEV = {"low": -1, "medium": -3, "high": -6}

VARIANTS = [
    # V0 = 已落地权重（P13-2 消融后的 runtime 现状，守卫基准）
    ("V0_landed_w6",    {"w_sem": 6, "app0": 20, "app1": 4, "cap": 40, "qscale": 1.0}),
    ("V1_legacy_w3",    {"w_sem": 3, "app0": 20, "app1": 4, "cap": 40, "qscale": 1.0}),
    ("V2_floor_w6",     {"w_sem": 6, "app0": 10, "app1": 2, "cap": 20, "qscale": 1.0}),
    ("V3_quality_w6",   {"w_sem": 6, "app0": 20, "app1": 4, "cap": 40, "qscale": 0.5}),
]


def shadow_rank(retriever: KnowledgeRetriever, features: dict,
                w: dict) -> list[str]:
    """影子评分器：复刻 recommend() + _capability_match，权重可变。"""
    pts = set(features.get("problem_types") or [])
    has_data = features.get("has_data")
    sample_size = features.get("sample_size")
    time_series = features.get("time_series")
    objectives = features.get("objectives")
    uncertainty = features.get("uncertainty")

    scored: list[tuple[int, str]] = []
    for card in retriever.cards.values():
        gate = w["w_sem"] * len(pts & set(card.problem_types))
        if time_series is not None and card.time_series is not None:
            gate += 1 if card.time_series == time_series else -4
        if isinstance(objectives, int) and objectives >= 2:
            gate += 2 if card.multi_objective else -1
        if uncertainty and card.handles_uncertainty:
            gate += 2
        if card.requires_data and has_data is False:
            continue
        if sample_size in SAMPLE_ORDER and card.sample_size \
                and sample_size not in card.sample_size:
            continue
        if gate <= 0:
            continue

        fit = min(w["cap"], w["app0"] + w["app1"]
                  * len(card.applicability_positive))
        for cond in card.applicability_positive:
            key = _cond_key(cond)
            if key and _cond_satisfied(key, features):
                fit = min(w["cap"], fit + 4)
        for cond in card.applicability_negative:
            key = _cond_key(cond)
            if key and _cond_satisfied(key, features):
                fit = max(0, fit - 10)
        for cond in card.required_conditions:
            key = _cond_key(cond)
            if key and not _cond_satisfied(key, features):
                fit = max(0, fit - 15)
        fit += gate

        data = {"low": 15, "medium": 10, "high": 5}.get(
            card.costs.get("data", "medium"), 10)
        if has_data is False and card.requires_data:
            data = 0
        if sample_size in SAMPLE_ORDER and card.sample_size \
                and sample_size not in card.sample_size:
            data = max(0, data - 8)

        q = w["qscale"]
        interp = round({"high": 10, "medium": 6, "low": 2}.get(
            card.interpretability, 5) * q)
        robust = round({"high": 10, "medium": 6, "low": 2}.get(
            card.robustness, 5) * q)
        complexity = {"low": 5, "medium": 3, "high": 1}.get(
            card.costs.get("compute", "medium"), 3)
        innovation = {"high": 10, "medium": 6, "low": 2}.get(
            card.innovation_potential, 4)
        competition = round({"high": 10, "medium": 6, "low": 2}.get(
            card.competition_suitability, 5) * q)
        evidence_cost = {"low": 5, "medium": 3, "high": 1}.get(
            "high" if len(card.evidence_minimum) >= 2
            else "medium" if card.evidence_minimum else "low", 3)

        risk = sum(SEV.get(level, -3) for level in card.risk.values())
        for fm in retriever.failures_for(card.card_id):
            risk += SEV.get(fm.severity if fm.severity in SEV else "medium", -3)

        total = (fit + data + interp + robust + complexity + innovation
                 + competition + evidence_cost + risk)
        scored.append((total, card.card_id))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [cid for _, cid in scored]


def real_rank(retriever: KnowledgeRetriever, features: dict) -> list[str]:
    return [r.card.card_id
            for r in retriever.recommend(dict(features), top_k=len(retriever.cards))]


def gt_hit(ranking: list[str], gt: list[str], card_names: dict,
           k: int) -> bool:
    return _method_hit(ranking[:k], card_names, gt)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Retriever 排序权重消融（P13-2）")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    retriever = KnowledgeRetriever(ROOT / "core" / "knowledge")
    card_names = _load_card_names()
    cases = []
    for name in CASES:
        cases.append(json.loads((E2E_DIR / name).read_text(encoding="utf-8")))

    # ---- 守卫：影子 V0 必须与真实 retriever 一致
    for case in cases:
        real = real_rank(retriever, case["features"])
        shadow = shadow_rank(retriever, case["features"], VARIANTS[0][1])
        if real != shadow:
            print(f"[GUARD FAIL] {case['case']}: 影子评分器与真实 retriever 不一致\n"
                  f"  real={real}\n  shadow={shadow}")
            return 2
    print("[GUARD PASS] 影子 V0 与真实 retriever 全 case 一致\n")

    rows = []
    for case in cases:
        for vname, w in VARIANTS:
            ranking = shadow_rank(retriever, case["features"], w)
            rows.append({
                "case": case["case"], "variant": vname,
                "top1": ranking[0] if ranking else "",
                "top1_gt": gt_hit(ranking, case["gt"], card_names, 1),
                "top3_gt": gt_hit(ranking, case["gt"], card_names, 3),
                "ranking": ranking[:5],
            })

    hdr = f"{'case':22s} {'variant':16s} {'top1':18s} {'t1hit':5s} {'t3hit':5s}"
    print(hdr)
    for r in rows:
        print(f"{r['case']:22s} {r['variant']:16s} {r['top1']:18s} "
              f"{str(r['top1_gt']):5s} {str(r['top3_gt']):5s}")

    # ---- 决策规则（预注册）：满足 (a)(b)(c) 的最靠前变体
    by = {(r["case"], r["variant"]): r for r in rows}
    chosen = None
    for vname, _ in VARIANTS:
        ok = (by[("2000C_global", vname)]["top1_gt"]
              and by[("2023C_global", vname)]["top1_gt"]
              and by[("reverse_evaluation", vname)]["top1_gt"])
        if ok:
            chosen = vname
            break
    print()
    if chosen:
        print(f"[DECISION] 最简单可行变体 = {chosen}（两题 top-1 GT 命中 + 反向检查通过）")
    else:
        print("[DECISION] 无变体满足决策规则 → 按纪律停止：不加权重、不造新层，"
              "转入 matcher/ranking 根因分析")
    if args.as_json:
        print(json.dumps({"rows": rows, "chosen": chosen},
                         ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
