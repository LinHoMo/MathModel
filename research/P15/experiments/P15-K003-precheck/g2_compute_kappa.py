"""
P15-K003 G2 — Cohen's κ 计算 + 分歧归因。

输入：g2/evaluator_{A,B,C}/CALIB_0X.json（3 evaluator × 8 packages × 22 dimensions）
输出：g2/g2_kappa.json（维度级 κ + mean_kappa + mean_qwk + 分歧归因 + Kappa悖论标注）

通过标准：维度级 Cohen's κ ≥ 0.6，或分歧可归因（逐条记录）。
"""
import json
from pathlib import Path
from itertools import combinations

PRECHECK = Path(__file__).resolve().parent
G2_DIR = PRECHECK / "g2"
EVALUATORS = ["A", "B", "C"]
CALIB_IDS = [f"CALIB_{i:02d}" for i in range(1, 9)]

# 22 维度定义（层级.维度号 -> 满分）
DIMENSIONS = {
    # L1 (5 dims, max 9)
    "L1.1": 2, "L1.2": 2, "L1.3": 2, "L1.4": 1, "L1.5": 2,
    # L2 (7 dims, max 15)
    "L2.1": 2, "L2.2": 2, "L2.3": 2, "L2.4": 2, "L2.5": 2, "L2.6": 3, "L2.7": 2,
    # L3 (5 dims, max 9)
    "L3.1": 2, "L3.2": 2, "L3.3": 2, "L3.4": 2, "L3.5": 1,
    # L4 (5 dims, max 9)
    "L4.1": 2, "L4.2": 2, "L4.3": 1, "L4.4": 2, "L4.5": 2,
}

DIM_LIST = list(DIMENSIONS.keys())


def load_scores():
    """加载 3 evaluator × 8 packages 的评分。"""
    scores = {}  # {evaluator: {calib_id: {dim: score}}}
    missing = []
    for ev in EVALUATORS:
        scores[ev] = {}
        ev_dir = G2_DIR / f"evaluator_{ev}"
        if not ev_dir.exists():
            missing.append(f"evaluator_{ev} directory missing")
            continue
        for cid in CALIB_IDS:
            fpath = ev_dir / f"{cid}.json"
            if not fpath.exists():
                missing.append(f"{ev}/{cid}.json missing")
                continue
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                dim_scores = {}
                for layer in ["L1", "L2", "L3", "L4"]:
                    layer_data = data.get(layer, {})
                    dims = layer_data.get("dimensions", {})
                    for dim_key, dim_val in dims.items():
                        # dim_key may be "L1.1" or "L1.1_explicit_conditions"
                        short_key = dim_key.split("_")[0] if "_" in dim_key else dim_key
                        if short_key in DIMENSIONS:
                            dim_scores[short_key] = dim_val.get("score", 0)
                scores[ev][cid] = dim_scores
            except Exception as e:
                missing.append(f"{ev}/{cid}.json parse error: {e}")
    return scores, missing


def cohen_kappa(scores1, scores2):
    """计算两个 evaluator 在一组 package 上某维度的 Cohen's κ。

    scores1, scores2: list of scores (same length, one per package)
    返回 (kappa, po, pe)
    """
    n = len(scores1)
    if n == 0:
        return None, None, None

    # 观测一致率 po
    agree = sum(1 for a, b in zip(scores1, scores2) if a == b)
    po = agree / n

    # 期望一致率 pe（基于边际分布）
    all_scores = list(set(scores1 + scores2))
    pe = 0.0
    for s in all_scores:
        p1 = scores1.count(s) / n
        p2 = scores2.count(s) / n
        pe += p1 * p2

    if pe == 1.0:
        # 完全一致的边际分布（所有评分相同）
        return 1.0 if po == 1.0 else 0.0, po, pe

    kappa = (po - pe) / (1 - pe)
    return round(kappa, 4), round(po, 4), round(pe, 4)


def quadratic_weighted_kappa(scores1, scores2, max_score):
    """计算二次加权 κ（QWK），用于有序评分尺度。"""
    n = len(scores1)
    if n == 0:
        return None

    # 构建混淆矩阵
    categories = list(range(max_score + 1))
    O = [[0] * len(categories) for _ in categories]
    for a, b in zip(scores1, scores2):
        O[a][b] += 1

    # 边际分布
    row_totals = [sum(row) for row in O]
    col_totals = [sum(O[r][c] for r in range(len(categories))) for c in range(len(categories))]

    # 期望矩阵 E
    E = [[(row_totals[r] * col_totals[c]) / n for c in range(len(categories))]
         for r in range(len(categories))]

    # 权重矩阵（二次加权）
    W = [[((r - c) ** 2) / (max_score ** 2) for c in range(len(categories))]
         for r in range(len(categories))]

    # 加权 κ
    num = sum(W[r][c] * O[r][c] for r in range(len(categories)) for c in range(len(categories)))
    den = sum(W[r][c] * E[r][c] for r in range(len(categories)) for c in range(len(categories)))

    if den == 0:
        return 1.0 if num == 0 else 0.0

    qwk = 1 - num / den
    return round(qwk, 4)


def compute_kappa():
    scores, missing = load_scores()

    if missing:
        print("WARNING: Missing files:")
        for m in missing:
            print(f"  {m}")

    # 维度级 κ（每对 evaluator）
    dim_kappa = {}
    for dim in DIM_LIST:
        dim_kappa[dim] = {}
        max_score = DIMENSIONS[dim]
        for ev1, ev2 in combinations(EVALUATORS, 2):
            s1 = []
            s2 = []
            for cid in CALIB_IDS:
                if cid in scores.get(ev1, {}) and cid in scores.get(ev2, {}):
                    s1.append(scores[ev1][cid].get(dim, 0))
                    s2.append(scores[ev2][cid].get(dim, 0))
            kappa, po, pe = cohen_kappa(s1, s2)
            qwk = quadratic_weighted_kappa(s1, s2, max_score)
            pair_key = f"{ev1}-{ev2}"
            dim_kappa[dim][pair_key] = {
                "kappa": kappa, "po": po, "pe": pe, "qwk": qwk,
                "n_packages": len(s1),
            }
        # 该维度的 mean κ（3 对平均）
        kappas = [dim_kappa[dim][f"{e1}-{e2}"]["kappa"]
                  for e1, e2 in combinations(EVALUATORS, 2)
                  if dim_kappa[dim][f"{e1}-{e2}"]["kappa"] is not None]
        qwks = [dim_kappa[dim][f"{e1}-{e2}"]["qwk"]
                for e1, e2 in combinations(EVALUATORS, 2)
                if dim_kappa[dim][f"{e1}-{e2}"]["qwk"] is not None]
        dim_kappa[dim]["mean_kappa"] = round(sum(kappas) / len(kappas), 4) if kappas else None
        dim_kappa[dim]["mean_qwk"] = round(sum(qwks) / len(qwks), 4) if qwks else None
        dim_kappa[dim]["max_score"] = max_score

        # Kappa 悖论检测：κ≈0 但 po>0.80
        mk = dim_kappa[dim]["mean_kappa"]
        pos = [dim_kappa[dim][f"{e1}-{e2}"]["po"]
               for e1, e2 in combinations(EVALUATORS, 2)
               if dim_kappa[dim][f"{e1}-{e2}"]["po"] is not None]
        mean_po = round(sum(pos) / len(pos), 4) if pos else None
        dim_kappa[dim]["mean_po"] = mean_po
        if mk is not None and abs(mk) < 0.05 and mean_po and mean_po > 0.80:
            dim_kappa[dim]["kappa_paradox"] = True
            dim_kappa[dim]["paradox_note"] = f"κ={mk}≈0 但 po={mean_po}>0.80，Kappa悖论伪影（边际分布极端偏斜）"
        else:
            dim_kappa[dim]["kappa_paradox"] = False

    # 总体指标
    all_mean_kappas = [dim_kappa[d]["mean_kappa"] for d in DIM_LIST
                        if dim_kappa[d]["mean_kappa"] is not None]
    all_mean_qwks = [dim_kappa[d]["mean_qwk"] for d in DIM_LIST
                      if dim_kappa[d]["mean_qwk"] is not None]
    overall_mean_kappa = round(sum(all_mean_kappas) / len(all_mean_kappas), 4) if all_mean_kappas else None
    overall_mean_qwk = round(sum(all_mean_qwks) / len(all_mean_qwks), 4) if all_mean_qwks else None

    # κ≥0.6 的维度数
    n_ge_06 = sum(1 for k in all_mean_kappas if k >= 0.6)
    n_lt_06 = len(all_mean_kappas) - n_ge_06

    # 分歧归因（κ<0.6 的维度）
    disagreements = []
    for dim in DIM_LIST:
        mk = dim_kappa[dim]["mean_kappa"]
        if mk is not None and mk < 0.6 and not dim_kappa[dim].get("kappa_paradox"):
            # 找出分歧最大的 package
            max_disagree = 0
            disagree_pkgs = []
            for cid in CALIB_IDS:
                pkg_scores = []
                for ev in EVALUATORS:
                    if cid in scores.get(ev, {}):
                        pkg_scores.append(scores[ev][cid].get(dim, 0))
                if len(pkg_scores) >= 2:
                    spread = max(pkg_scores) - min(pkg_scores)
                    if spread > max_disagree:
                        max_disagree = spread
                        disagree_pkgs = [(cid, pkg_scores)]
                    elif spread == max_disagree and spread > 0:
                        disagree_pkgs.append((cid, pkg_scores))
            disagreements.append({
                "dimension": dim,
                "mean_kappa": mk,
                "max_disagreement_spread": max_disagree,
                "disagreement_examples": [
                    {"calib_id": cid, "scores": s} for cid, s in disagree_pkgs[:3]
                ],
                "attribution": "待人工审查判据歧义（见 G2_REPORT 归因分析）",
            })

    result = {
        "n_evaluators": len(EVALUATORS),
        "n_calibration_packages": len(CALIB_IDS),
        "n_dimensions": len(DIM_LIST),
        "dimension_kappa": dim_kappa,
        "overall": {
            "mean_kappa": overall_mean_kappa,
            "mean_qwk": overall_mean_qwk,
            "n_dimensions_ge_0.6": n_ge_06,
            "n_dimensions_lt_0.6": n_lt_06,
            "pass_rate": round(n_ge_06 / len(all_mean_kappas), 4) if all_mean_kappas else None,
        },
        "disagreements": disagreements,
        "missing_files": missing,
        "kappa_threshold": 0.6,
        "pass_criterion": "维度级 mean κ ≥ 0.6，或分歧可归因（含 Kappa 悖论伪影标注）",
    }

    # 保存
    out_path = G2_DIR / "g2_kappa.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 打印摘要
    print(f"=== G2 κ 计算结果 ===")
    print(f"评估者数: {len(EVALUATORS)}, 校准包数: {len(CALIB_IDS)}, 维度数: {len(DIM_LIST)}")
    print(f"总体 mean κ: {overall_mean_kappa}")
    print(f"总体 mean QWK: {overall_mean_qwk}")
    print(f"κ≥0.6 维度: {n_ge_06}/{len(all_mean_kappas)} ({result['overall']['pass_rate']*100:.1f}%)")
    print()
    print(f"{'维度':<8} {'满分':>4} {'mean_κ':>8} {'mean_po':>8} {'mean_qwk':>8} {'悖论':>4}")
    print("-" * 50)
    for dim in DIM_LIST:
        d = dim_kappa[dim]
        paradox = "★" if d.get("kappa_paradox") else ""
        print(f"{dim:<8} {d['max_score']:>4} {str(d['mean_kappa']):>8} "
              f"{str(d.get('mean_po')):>8} {str(d['mean_qwk']):>8} {paradox:>4}")
    print()
    if disagreements:
        print(f"κ<0.6 分歧维度（非悖论）: {len(disagreements)}")
        for d in disagreements:
            print(f"  {d['dimension']}: κ={d['mean_kappa']}, max_spread={d['max_disagreement_spread']}")
    print(f"\n结果已保存: {out_path}")
    return result


if __name__ == "__main__":
    compute_kappa()
