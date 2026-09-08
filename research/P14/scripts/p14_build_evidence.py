#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""p14_build_evidence.py — P14.4 前置：从 Results 生成 Evidence（21）与 Claim（9）实体.

设计：
  Evidence：每个 Result 一条，解释文本由本脚本作者定义的模板嵌入实测数值；
            position=supports（被 Claim 引用）或 characterizes（行为刻画）。
  Claim：   每题 3 条，text/model_origin 锚定 artifact 原文（G7）；
            status 由构建器内嵌谓词按实测数据机械判定（supported/refuted）。
只生成实体，不定义门禁语义；hash 由 p14_finalize_hashes.py 终化。
用法: python p14_build_evidence.py <run_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p14_integrity_gate import canonical_hash  # noqa: E402


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def now():
    from datetime import datetime
    return datetime.now().isoformat(timespec="seconds")


def main(run: Path):
    man = load(run / "manifest.json")
    specs = {load(p)["entity_id"]: load(p) for p in sorted((run / "specs").glob("*.json"))}
    exes = [load(p) for p in sorted((run / "executions").glob("*.json"))]
    results = [load(p) for p in sorted((run / "results").glob("*.json"))]
    res_by_exe = {r["execution_ref"]["entity_id"]: r for r in results}
    spec_by_id = specs
    m = {r["data"]["experiment_id"]: r["data"]["metrics"] for r in results}

    # ---- Evidence 实体（21 条，按 Execution 顺序）----
    TPL = {
        "EXP-2020B-C0-1": "p2∈[0.3,0.8] 扫描：p2=0.5/0.6 的 E[总时间]={e5:.2f}/{e6:.2f}，策略稳定度 {stab:.3f}，p2 弹性 {el:.3f}——天气恶化推高期望时间但最优策略高度稳定。",
        "EXP-2020B-C1-1": "p2∈[0.3,0.8] 扫描：p2=0.5/0.6 的 E[总时间]={e5:.2f}/{e6:.2f}，策略稳定度 {stab:.3f}，p2 弹性 {el:.3f}——天气恶化推高期望时间但最优策略高度稳定。",
        "EXP-2020B-C0-2": "三次独立种子蒙特卡洛 P(安全到达)={p0:.3f}/{p1:.3f}/{p2m:.3f}，C1 违反率≈{v:.4f}：基线场景下 M3 策略到达性充足。",
        "EXP-2020B-C1-2": "三次独立种子蒙特卡洛 P(安全到达)={p0:.3f}/{p1:.3f}/{p2m:.3f}，C1 违反率≈{v:.4f}：基线场景下 M3 策略到达性充足。",
        "EXP-2020B-C0-3": "极端压测（p2=0.99）：P(安全到达)={pw:.3f}，C1 违反率={vw:.4f}；最好天气（p2=0.01）P(安全到达)={pb:.3f}。",
        "EXP-2020B-C1-3": "极端压测（p2=0.99）：P(安全到达)={pw:.3f}，C1 违反率={vw:.4f}；最好天气（p2=0.01）P(安全到达)={pb:.3f}。",
        "EXP-2020B-C1-4": "双口径最优策略重合度={ov:.3f}；值迭代 P(安全到达)={dp:.3f}，较贪心基线增益={g:+.3f}。",
        "EXP-2024B-C0-1": "30 组 (p, c_def/c_ins) 网格的 n* 与 E[C] 已记录；p 弹性={el:.3f}；不检验区占比={z:.2f}。",
        "EXP-2024B-C1-1": "30 组 (p, c_def/c_ins) 网格的 n* 与 E[C] 已记录；p 弹性={el:.3f}；不检验区占比={z:.2f}。",
        "EXP-2024B-C0-2": "泊松近似消融：|Δn*| 最大 {mx:.1f} 件；成本相对误差<1% 的近似有效边界 n≤{b}。",
        "EXP-2024B-C1-2": "泊松近似消融：|Δn*| 最大 {mx:.1f} 件；成本相对误差<1% 的近似有效边界 n≤{b}。",
        "EXP-2024B-C0-3": "批次蒙特卡洛（2000 批/规模）：N=100/1000/10000 的经验-理论相对误差={e100:.3f}/{e1000:.3f}/{e10000:.3f}。",
        "EXP-2024B-C1-3": "批次蒙特卡洛（2000 批/规模）：N=100/1000/10000 的经验-理论相对误差={e100:.3f}/{e1000:.3f}/{e10000:.3f}。",
        "EXP-2024B-C1-4": "小批次超几何对照：N=50/100/200 的 n* 偏差={g50:.1f}/{g100:.1f}/{g200:.1f}；C1 binding 区域占比={bf:.2f}。",
        "EXP-2022C-C0-1": "CLR 消融：有 CLR 准确率={a1:.3f}，无 CLR={a2:.3f}；轮廓系数差={sg:.3f}。",
        "EXP-2022C-C1-1": "CLR 消融：有 CLR 准确率={a1:.3f}，无 CLR={a2:.3f}；轮廓系数差={sg:.3f}。",
        "EXP-2022C-C0-2": "K∈[2,8] 扫描最优 K={bk}（kmeans_acc={ba:.3f}）；LDA 最优保留贡献率={bc:.2f}（acc={bca:.3f}）。",
        "EXP-2022C-C1-2": "K∈[2,8] 扫描最优 K={bk}（kmeans_acc={ba:.3f}）；LDA 最优保留贡献率={bc:.2f}（acc={bca:.3f}）。",
        "EXP-2022C-C0-3": "测量噪声 1%→10%：准确率 {c0:.3f}→{c9:.3f}，衰减 {drop:.3f}。",
        "EXP-2022C-C1-3": "测量噪声 1%→10%：准确率 {c0:.3f}→{c9:.3f}，衰减 {drop:.3f}。",
        "EXP-2022C-C1-4": "5 折分层交叉验证：准确率 {m:.3f}±{s:.3f}；O1 的 85% 成功标准达成={mt}。",
    }
    CLAIMED_BY = {
        "EXP-2020B-C0-2": "CLM001", "EXP-2020B-C1-4": "CLM002", "EXP-2020B-C0-3": "CLM003",
        "EXP-2024B-C0-2": "CLM004", "EXP-2024B-C0-1": "CLM005", "EXP-2024B-C1-4": "CLM006",
        "EXP-2022C-C0-1": "CLM007", "EXP-2022C-C1-4": "CLM008", "EXP-2022C-C0-3": "CLM009",
    }

    def fmt(exp_id, mt):
        t = TPL[exp_id]
        kw = {}
        if "2020B-C0-1" in exp_id or "2020B-C1-1" in exp_id:
            cfg = {c["p2"]: c for c in mt["configs"]}
            kw = {"e5": cfg[0.5]["E_total_time"], "e6": cfg[0.6]["E_total_time"],
                  "stab": mt["policy_stability"], "el": mt["elasticity_p2"]}
        elif "2020B-C0-2" in exp_id or "2020B-C1-2" in exp_id:
            r = mt["runs"]
            kw = {"p0": r[0]["P_safe_mc"], "p1": r[1]["P_safe_mc"],
                  "p2m": r[2]["P_safe_mc"], "v": r[0]["c1_violation_rate"]}
        elif "2020B-C0-3" in exp_id or "2020B-C1-3" in exp_id:
            kw = {"pw": mt["P_safe_worst"], "vw": mt["c1_violation_worst"],
                  "pb": mt["P_safe_best"]}
        elif "2020B-C1-4" in exp_id:
            kw = {"ov": mt["policy_overlap_ratio"], "dp": mt["P_safe_dp"],
                  "g": mt["P_safe_gain_vs_greedy"]}
        elif "2024B-C0-1" in exp_id or "2024B-C1-1" in exp_id:
            kw = {"el": mt["elasticity_p"], "z": mt["zero_inspection_region"]}
        elif "2024B-C0-2" in exp_id or "2024B-C1-2" in exp_id:
            kw = {"mx": max(r["abs_dn_star"] for r in mt["rows"]),
                  "b": mt["approx_valid_boundary"]}
        elif "2024B-C0-3" in exp_id or "2024B-C1-3" in exp_id:
            kw = {"e100": mt["100"]["relative_error"], "e1000": mt["1000"]["relative_error"],
                  "e10000": mt["10000"]["relative_error"]}
        elif "2024B-C1-4" in exp_id:
            r = {int(x["N"]): x for x in mt["rows"]}
            kw = {"g50": r[50]["hypergeo_gap"], "g100": r[100]["hypergeo_gap"],
                  "g200": r[200]["hypergeo_gap"], "bf": mt["boundary_region_frac"]}
        elif "2022C-C0-1" in exp_id or "2022C-C1-1" in exp_id:
            kw = {"a1": mt["accuracy_with_clr"], "a2": mt["accuracy_without_clr"],
                  "sg": mt["silhouette_gap"]}
        elif "2022C-C0-2" in exp_id or "2022C-C1-2" in exp_id:
            kw = {"bk": mt["best_K"], "ba": mt["best_kmeans_acc"],
                  "bc": mt["best_components"], "bca": mt["best_lda_acc"]}
        elif "2022C-C0-3" in exp_id or "2022C-C1-3" in exp_id:
            c = mt["accuracy_noise_curve"]
            kw = {"c0": c[0]["acc"], "c9": c[-1]["acc"],
                  "drop": mt["accuracy_drop_at_10pct"]}
        elif "2022C-C1-4" in exp_id:
            kw = {"m": mt["cv_accuracy_mean"], "s": mt["cv_accuracy_std"],
                  "mt": mt["meets_85pct_target"]}
        return t.format(**kw)

    claims_def = {
        "CLM001": {"q": "2020_B",
                   "text": "在 P14-20260907-01 场景基线下，M3（Bellman 值迭代）最优策略的安全到达率 P(安全到达) ≥ 0.90",
                   "element_type": "objective", "anchor": "max P(安全到达)",
                   "evidence": "EXP-2020B-C0-2",
                   "rule": lambda mt: "supported" if sum(r["P_safe_mc"] for r in mt["runs"]) / 3 >= 0.90 else "refuted"},
        "CLM002": {"q": "2020_B",
                   "text": "在场景基线下，目标 O1 的两种口径（min E[总时间] 与 max P(安全到达)）产生高度一致的最优策略（重合度 ≥ 0.95）",
                   "element_type": "objective", "anchor": "min E[总时间] 或 max P(安全到达)",
                   "evidence": "EXP-2020B-C1-4",
                   "rule": lambda mt: "supported" if mt["policy_overlap_ratio"] >= 0.95 else "refuted"},
        "CLM003": {"q": "2020_B",
                   "text": "约束 C1（r(t) ≥ 0 ∀t）在极端坏天气序列下存在可测违反风险（违反率 > 0）",
                   "element_type": "constraint", "anchor": "r(t) ≥ 0 ∀t",
                   "evidence": "EXP-2020B-C0-3",
                   "rule": lambda mt: "supported" if mt["c1_violation_worst"] > 0 else "refuted"},
        "CLM004": {"q": "2024_B",
                   "text": "在基准场景（N=1000, p=0.05）下，M1 泊松近似 e^{-np} 在 n ≤ 100 范围内与精确式 (1-p)^n 的最优成本相对误差 < 1%",
                   "element_type": "mechanism", "anchor": "P(miss) = (1-p)^n ≈ e^{-np}（大批次）",
                   "evidence": "EXP-2024B-C0-2",
                   "rule": lambda mt: "supported" if mt["approx_valid_boundary"] >= 100 else "refuted"},
        "CLM005": {"q": "2024_B",
                   "text": "M3 一阶条件解 n* 对不合格品率 p 的弹性为正（p 上升导致 n* 上升）",
                   "element_type": "mechanism", "anchor": "n* = argmin E[C]，一阶条件: c_ins = c_def·(N-n)·(-∂P(miss)/∂n)",
                   "evidence": "EXP-2024B-C0-1",
                   "rule": lambda mt: "supported" if mt["elasticity_p"] > 0 else "refuted"},
        "CLM006": {"q": "2024_B",
                   "text": "超几何精确模型与二项抽样模型在小批次下的 n* 偏差随 N 增大而收敛（50→200 单调下降）",
                   "element_type": "mechanism", "anchor": "二项抽样模型",
                   "evidence": "EXP-2024B-C1-4",
                   "rule": lambda mt: "supported" if mt["rows"][0]["hypergeo_gap"] >= mt["rows"][1]["hypergeo_gap"] >= mt["rows"][2]["hypergeo_gap"] else "refuted"},
        "CLM007": {"q": "2022_C",
                   "text": "机制 M1（CLR 变换）对 M3/M4 下游判别性能有非负贡献（有 CLR 准确率 ≥ 无 CLR）",
                   "element_type": "mechanism", "anchor": "clr(x) = [ln(x_i/g(x))] 其中 g(x) 为几何均值",
                   "evidence": "EXP-2022C-C0-1",
                   "rule": lambda mt: "supported" if mt["accuracy_with_clr"] >= mt["accuracy_without_clr"] else "refuted"},
        "CLM008": {"q": "2022_C",
                   "text": "M1→M2→M3→M4 流水线在 pilot 数据集上的判别准确率满足 O1 成功标准（CV 均值 ≥ 85%）",
                   "element_type": "objective", "anchor": "判别模型准确率>85%",
                   "evidence": "EXP-2022C-C1-4",
                   "rule": lambda mt: "supported" if mt["meets_85pct_target"] else "refuted"},
        "CLM009": {"q": "2022_C",
                   "text": "在约束 C1（各成分 ≥ 0 且总和 = 100%）重闭合下，≤10% 测量噪声造成的判别准确率衰减 ≤ 10 个百分点",
                   "element_type": "constraint", "anchor": "各成分含量 ≥ 0 且总和 = 100%",
                   "evidence": "EXP-2022C-C0-3",
                   "rule": lambda mt: "supported" if mt["accuracy_drop_at_10pct"] <= 0.10 else "refuted"},
    }

    # 写 Evidence（21）
    ev_id_of = {}
    for i, r in enumerate(results, 1):
        eid = f"P14-EVI{i:03d}"
        exp_id = r["data"]["experiment_id"]
        ev_id_of[exp_id] = eid
        claimed = CLAIMED_BY.get(exp_id)
        ev = {
            "entity_type": "evidence", "entity_id": eid, "schema_version": "p14.v1",
            "run_id": r["run_id"], "created_at": now(),
            "result_ref": {"entity_type": "result", "entity_id": r["entity_id"],
                           "content_sha256": r["content_sha256"]},
            "interpretation": fmt(exp_id, r["data"]["metrics"]),
            "position": "supports" if claimed else "characterizes",
            "target_claim_desc": claims_def[claimed]["text"] if claimed
                                 else "pilot 场景基线下的模型行为刻画（未被 Claim 直接引用）",
            "status": r["status"],
            "parent_ref": {"entity_type": "result", "entity_id": r["entity_id"],
                           "content_sha256": r["content_sha256"]},
            "content_sha256": None,
        }
        (run / "evidences" / f"{eid}.json").write_text(
            json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  + {eid} <- {r['entity_id']} ({exp_id}) position={ev['position']}")

    # 写 Claim（9）
    for i, (cid, c) in enumerate(claims_def.items(), 1):
        mt = m[c["evidence"]]
        status = c["rule"](mt)
        art = next(s for s in specs.values()
                   if s["question_id"] == c["q"] and s["condition"] == "C0")
        claim = {
            "entity_type": "claim", "entity_id": f"P14-{cid}", "schema_version": "p14.v1",
            "run_id": man["run_id"], "created_at": now(),
            "text": c["text"],
            "model_origin": {"element_type": c["element_type"], "anchor": c["anchor"]},
            "supported_by": [ev_id_of[c["evidence"]]],
            "refuted_by": [],
            "status": status,
            "parent_ref": {"entity_type": "model_artifact",
                           "entity_id": Path(art["model_artifact_ref"]["path"]).name,
                           "content_sha256": art["model_artifact_ref"]["model_artifact_hash"]},
            "content_sha256": None,
        }
        (run / "claims" / f"P14-{cid}.json").write_text(
            json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  + {cid} [{status}] {c['text'][:44]}…")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
