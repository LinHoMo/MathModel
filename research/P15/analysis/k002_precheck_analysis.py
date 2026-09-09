#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k002_precheck_analysis.py — P15-K002 预检分析工具集

功能：
1. neutralize: 将 12 份产物中性化到 blind/ 目录（model_id 替换为 m-<hash8>，去除臂标签）
2. aggregate: 汇总 12 份评分，计算每题 F/S 的 L1-L4 各维均值、MCQ_primary、差值、区分度判定
3. kappa: 计算 G2 三评估者的维度级 Cohen's κ（两两 3 对）

用法:
  py -3.12 research/P15/analysis/k002_precheck_analysis.py neutralize
  py -3.12 research/P15/analysis/k002_precheck_analysis.py aggregate
  py -3.12 research/P15/analysis/k002_precheck_analysis.py kappa
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
P15 = SCRIPTS_DIR.parent
ROOT = P15.parent.parent
PRECHECK = P15 / "experiments" / "P15-K002-precheck"
RUNS = PRECHECK / "runs"
SCORES = PRECHECK / "scores"
BLIND = PRECHECK / "blind"
G2 = PRECHECK / "g2"
CONDITION_MAP = PRECHECK / "key" / "condition_map.json"

# Rubric v1.0 维度定义
L1_DIMS = ["L1.1", "L1.2", "L1.3", "L1.4", "L1.5"]
L2_DIMS = ["L2.1", "L2.2", "L2.3", "L2.4", "L2.5", "L2.6", "L2.7"]
L2_KEY_DIMS = ["L2.1", "L2.2", "L2.4", "L2.5", "L2.6", "L2.7"]  # 排除 L2.3（非关键），与 K001 一致
L3_DIMS = ["L3.1", "L3.2", "L3.3", "L3.4", "L3.5"]
L4_DIMS = ["L4.1", "L4.2", "L4.3", "L4.4", "L4.5"]
ALL_DIMS = L1_DIMS + L2_DIMS + L3_DIMS + L4_DIMS  # 22 维

# 各维度满分
DIM_MAX = {
    "L1.1": 2, "L1.2": 2, "L1.3": 2, "L1.4": 1, "L1.5": 2,  # L1 total 9
    "L2.1": 2, "L2.2": 2, "L2.3": 2, "L2.4": 2, "L2.5": 2, "L2.6": 3, "L2.7": 2,  # L2 total 15
    "L3.1": 2, "L3.2": 2, "L3.3": 2, "L3.4": 2, "L3.5": 1,  # L3 total 9
    "L4.1": 2, "L4.2": 2, "L4.3": 1, "L4.4": 2, "L4.5": 2,  # L4 total 9
}
L2_KEY_MAX = sum(DIM_MAX[d] for d in L2_KEY_DIMS)  # 13
L3_MAX = sum(DIM_MAX[d] for d in L3_DIMS)  # 9
L4_MAX = sum(DIM_MAX[d] for d in L4_DIMS)  # 9
MCQ_PRIMARY_MAX = L2_KEY_MAX + L3_MAX + L4_MAX  # 31


def load_condition_map() -> dict:
    return json.loads(CONDITION_MAP.read_text(encoding="utf-8"))["map"]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# 1. Neutralize (盲评中性化)
# ---------------------------------------------------------------------------

def neutralize() -> None:
    """将 runs/<sid>/ 中的产物复制到 blind/<sid>/，中性化 model_id 和臂标签。"""
    if BLIND.exists():
        shutil.rmtree(BLIND)
    BLIND.mkdir(parents=True)

    cmap = load_condition_map()
    for sid, info in cmap.items():
        run_dir = RUNS / sid
        blind_dir = BLIND / sid
        blind_dir.mkdir()
        arm = info["arm"]
        neutral_id = "m-" + sha256_text(sid)[:8]

        if arm == "S":
            src = run_dir / "model_ir.json"
            if not src.exists():
                print(f"[WARN] {sid[:8]} S 臂缺少 model_ir.json，跳过中性化")
                continue
            ir = json.loads(src.read_text(encoding="utf-8"))
            ir["model_id"] = neutral_id
            # 移除可能暴露臂的字段
            ir.pop("arm", None)
            if "problem_binding" in ir and isinstance(ir["problem_binding"], dict):
                ir["problem_binding"].pop("arm", None)
            (blind_dir / "model_ir.json").write_text(
                json.dumps(ir, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:  # F
            src = run_dir / "model_doc.md"
            if not src.exists():
                print(f"[WARN] {sid[:8]} F 臂缺少 model_doc.md，跳过中性化")
                continue
            text = src.read_text(encoding="utf-8")
            # 替换 submission_id 引用为 neutral_id
            text = text.replace(sid, neutral_id)
            text = text.replace(sid[:8], neutral_id)
            # 移除可能的臂标签行
            lines = text.split("\n")
            cleaned = []
            for line in lines:
                low = line.lower()
                if any(k in low for k in ["arm:", "arm =", "臂:", "臂=", "free text", "自由文本臂", "结构化臂"]):
                    continue
                cleaned.append(line)
            (blind_dir / "model_doc.md").write_text("\n".join(cleaned), encoding="utf-8")

    print(f"[OK] 中性化完成，输出目录: {BLIND}")


# ---------------------------------------------------------------------------
# 2. Aggregate (分数汇总 + 区分度判定)
# ---------------------------------------------------------------------------

def load_score(sid: str) -> dict:
    path = SCORES / f"{sid}.json"
    if not path.exists():
        raise FileNotFoundError(f"评分文件不存在: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_dim_score(score: dict, dim: str) -> int:
    """从评分 JSON 中提取某维度分数，兼容多种格式。"""
    # 格式 1: dimensions.{dim}.score
    dims = score.get("dimensions", {})
    if dim in dims and isinstance(dims[dim], dict):
        return dims[dim].get("score", 0)
    if dim in dims and isinstance(dims[dim], (int, float)):
        return int(dims[dim])
    # 格式 2: 顶层 {dim: score}
    if dim in score and isinstance(score[dim], (int, float)):
        return int(score[dim])
    return 0


def compute_layer_totals(score: dict) -> dict:
    """计算 L1-L4 各层总分及 MCQ_primary。"""
    l1 = sum(get_dim_score(score, d) for d in L1_DIMS)
    l2 = sum(get_dim_score(score, d) for d in L2_DIMS)
    l2_key = sum(get_dim_score(score, d) for d in L2_KEY_DIMS)
    l3 = sum(get_dim_score(score, d) for d in L3_DIMS)
    l4 = sum(get_dim_score(score, d) for d in L4_DIMS)
    mcq_primary = (l2_key + l3 + l4) / MCQ_PRIMARY_MAX * 100
    l2_100 = l2 / 15 * 100  # L2 全 7 维折算百分制
    return {
        "L1_total": l1, "L1_max": 9,
        "L2_total": l2, "L2_max": 15, "L2_100": round(l2_100, 2),
        "L2_key": l2_key, "L2_key_max": 13,
        "L3_total": l3, "L3_max": 9,
        "L4_total": l4, "L4_max": 9,
        "MCQ_primary": round(mcq_primary, 2),
    }


def aggregate() -> dict:
    """汇总 12 份评分，按题目分组计算 F/S 对比。"""
    cmap = load_condition_map()
    results = {}

    # 收集每题的 F/S 评分
    by_problem: dict[str, dict[str, list]] = {}
    for sid, info in cmap.items():
        pid = info["problem_id"]
        arm = info["arm"]
        score = load_score(sid)
        totals = compute_layer_totals(score)
        by_problem.setdefault(pid, {"F": [], "S": []})
        by_problem[pid][arm].append({"sid": sid, "score": score, "totals": totals})

    report = {"problems": {}, "overall": {}}

    for pid in sorted(by_problem.keys()):
        arms = by_problem[pid]
        f_scores = arms["F"]
        s_scores = arms["S"]

        # 22 维均值
        f_dim_means = {}
        s_dim_means = {}
        for d in ALL_DIMS:
            f_vals = [get_dim_score(s["score"], d) for s in f_scores]
            s_vals = [get_dim_score(s["score"], d) for s in s_scores]
            f_dim_means[d] = round(sum(f_vals) / len(f_vals), 2) if f_vals else 0
            s_dim_means[d] = round(sum(s_vals) / len(s_vals), 2) if s_vals else 0

        # 层级均值
        f_mcq = round(sum(s["totals"]["MCQ_primary"] for s in f_scores) / len(f_scores), 2) if f_scores else 0
        s_mcq = round(sum(s["totals"]["MCQ_primary"] for s in s_scores) / len(s_scores), 2) if s_scores else 0
        f_l2 = round(sum(s["totals"]["L2_100"] for s in f_scores) / len(f_scores), 2) if f_scores else 0
        s_l2 = round(sum(s["totals"]["L2_100"] for s in s_scores) / len(s_scores), 2) if s_scores else 0

        mcq_diff = round(s_mcq - f_mcq, 2)
        l2_diff = round(s_l2 - f_l2, 2)

        # 区分度判定：MCQ_primary 差 = 0 → 无区分度
        has_discrimination = mcq_diff != 0
        # 由于 n=1 per arm in precheck, 差值就是两个个体分数之差
        # 判定规则：差=0 → 无区分度

        report["problems"][pid] = {
            "n_F": len(f_scores), "n_S": len(s_scores),
            "F_dim_means": f_dim_means,
            "S_dim_means": s_dim_means,
            "F_MCQ_primary": f_mcq,
            "S_MCQ_primary": s_mcq,
            "MCQ_diff_S_minus_F": mcq_diff,
            "F_L2_100": f_l2,
            "S_L2_100": s_l2,
            "L2_diff_S_minus_F": l2_diff,
            "has_discrimination": has_discrimination,
            "F_sids": [s["sid"] for s in f_scores],
            "S_sids": [s["sid"] for s in s_scores],
        }

    # 全局统计
    no_disc = [pid for pid, p in report["problems"].items() if not p["has_discrimination"]]
    report["overall"]["no_discrimination_problems"] = no_disc
    report["overall"]["no_discrimination_count"] = len(no_disc)
    report["overall"]["STOP_triggered"] = len(no_disc) >= 2
    report["overall"]["MCQ_primary_max"] = MCQ_PRIMARY_MAX

    # 写汇总 JSON
    out = PRECHECK / "analysis_summary.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] 汇总完成: {out}")
    print(f"  无区分度题目: {no_disc} ({len(no_disc)} 题)")
    print(f"  STOP 触发: {report['overall']['STOP_triggered']}")
    return report


# ---------------------------------------------------------------------------
# 3. Cohen's kappa (G2 评估者间一致性)
# ---------------------------------------------------------------------------

def cohens_kappa(labels_a: list, labels_b: list) -> float:
    """计算两个评估者在一组样本上的 Cohen's κ。

    labels_a / labels_b: 相同长度的离散标签列表（整数分数）。
    对于有序评分，将分数视为名义类别计算 κ（标准做法）。
    """
    n = len(labels_a)
    if n == 0:
        return 0.0
    # 观测一致率
    po = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    # 期望一致率（边际分布乘积）
    all_labels = sorted(set(labels_a) | set(labels_b))
    pa = {l: labels_a.count(l) / n for l in all_labels}
    pb = {l: labels_b.count(l) / n for l in all_labels}
    pe = sum(pa[l] * pb[l] for l in all_labels)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def kappa() -> dict:
    """计算 G2 三评估者的维度级 Cohen's κ（两两 3 对），并取均值。"""
    if not G2.exists():
        print("[WARN] G2 目录不存在，跳过 κ 计算")
        return {}

    evaluators = sorted([d.name for d in G2.iterdir() if d.is_dir()])
    if len(evaluators) < 2:
        print(f"[WARN] 评估者数量不足 ({len(evaluators)})，跳过 κ 计算")
        return {}

    # 收集每个评估者的评分
    eval_scores: dict[str, dict[str, dict]] = {}
    all_sids: set[str] = set()
    for ev in evaluators:
        eval_scores[ev] = {}
        ev_dir = G2 / ev
        for f in ev_dir.glob("*.json"):
            sid = f.stem
            eval_scores[ev][sid] = json.loads(f.read_text(encoding="utf-8"))
            all_sids.add(sid)

    common_sids = sorted(all_sids)
    # 只取所有评估者都评分了的样本
    common_sids = [sid for sid in common_sids if all(sid in eval_scores[ev] for ev in evaluators)]

    if not common_sids:
        print("[WARN] 没有共同评分的样本，跳过 κ 计算")
        return {}

    # 维度级 κ
    kappa_results: dict[str, dict] = {}
    for dim in ALL_DIMS:
        pair_kappas = {}
        for ev_a, ev_b in combinations(evaluators, 2):
            labels_a = [get_dim_score(eval_scores[ev_a][sid], dim) for sid in common_sids]
            labels_b = [get_dim_score(eval_scores[ev_b][sid], dim) for sid in common_sids]
            k = cohens_kappa(labels_a, labels_b)
            pair_kappas[f"{ev_a}_vs_{ev_b}"] = round(k, 4)
        mean_k = round(sum(pair_kappas.values()) / len(pair_kappas), 4)
        kappa_results[dim] = {
            "pairs": pair_kappas,
            "mean_kappa": mean_k,
            "pass": mean_k >= 0.6,
        }

    # 总分 κ
    total_pair_kappas = {}
    for ev_a, ev_b in combinations(evaluators, 2):
        totals_a = [sum(get_dim_score(eval_scores[ev_a][sid], d) for d in ALL_DIMS) for sid in common_sids]
        totals_b = [sum(get_dim_score(eval_scores[ev_b][sid], d) for d in ALL_DIMS) for sid in common_sids]
        total_pair_kappas[f"{ev_a}_vs_{ev_b}"] = round(cohens_kappa(totals_a, totals_b), 4)
    kappa_results["TOTAL"] = {
        "pairs": total_pair_kappas,
        "mean_kappa": round(sum(total_pair_kappas.values()) / len(total_pair_kappas), 4),
        "pass": round(sum(total_pair_kappas.values()) / len(total_pair_kappas), 4) >= 0.6,
    }

    # MCQ_primary κ
    mcq_pair_kappas = {}
    for ev_a, ev_b in combinations(evaluators, 2):
        mcq_a = [compute_layer_totals(eval_scores[ev_a][sid])["MCQ_primary"] for sid in common_sids]
        mcq_b = [compute_layer_totals(eval_scores[ev_b][sid])["MCQ_primary"] for sid in common_sids]
        # MCQ 是连续值，四舍五入到整数作为类别
        mcq_pair_kappas[f"{ev_a}_vs_{ev_b}"] = round(cohens_kappa(
            [round(v) for v in mcq_a], [round(v) for v in mcq_b]), 4)
    kappa_results["MCQ_primary"] = {
        "pairs": mcq_pair_kappas,
        "mean_kappa": round(sum(mcq_pair_kappas.values()) / len(mcq_pair_kappas), 4),
        "pass": round(sum(mcq_pair_kappas.values()) / len(mcq_pair_kappas), 4) >= 0.6,
    }

    out = PRECHECK / "g2_kappa.json"
    out.write_text(json.dumps(kappa_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 汇总判定
    dim_means = [v["mean_kappa"] for k, v in kappa_results.items() if k in ALL_DIMS]
    overall_mean = round(sum(dim_means) / len(dim_means), 4)
    fail_dims = [k for k, v in kappa_results.items() if k in ALL_DIMS and not v["pass"]]

    print(f"[OK] G2 κ 计算完成: {out}")
    print(f"  评估者: {evaluators}")
    print(f"  共同样本: {common_sids} ({len(common_sids)} 个)")
    print(f"  维度级平均 κ: {overall_mean}")
    print(f"  未通过维度 (κ<0.6): {fail_dims}")
    print(f"  G2 PASS: {len(fail_dims) == 0 or overall_mean >= 0.6}")

    return {
        "evaluators": evaluators,
        "common_sids": common_sids,
        "dimension_kappas": kappa_results,
        "overall_mean_kappa": overall_mean,
        "fail_dimensions": fail_dims,
        "G2_pass": len(fail_dims) == 0 or overall_mean >= 0.6,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "neutralize":
        neutralize()
    elif cmd == "aggregate":
        aggregate()
    elif cmd == "kappa":
        kappa()
    else:
        print(f"未知命令: {cmd}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
