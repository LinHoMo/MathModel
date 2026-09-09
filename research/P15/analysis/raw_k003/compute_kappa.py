"""
P15-K003 正式盲评 — 评估者间一致性计算
维度级 Cohen's κ + Quadratic Weighted Kappa (QWK)
3 evaluators (A/B/C) × 66 bundles × 22 dimensions
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\analysis\raw_k003")
SCORES_DIR = BASE / "scores"
OUTPUT = BASE / "kappa_formal.json"

DIMENSIONS = [
    "L1.1", "L1.2", "L1.3", "L1.4", "L1.5",
    "L2.1", "L2.2", "L2.3", "L2.4", "L2.5", "L2.6", "L2.7",
    "L3.1", "L3.2", "L3.3", "L3.4", "L3.5",
    "L4.1", "L4.2", "L4.3", "L4.4", "L4.5",
]

MAX_SCORES = {
    "L1.1": 2, "L1.2": 2, "L1.3": 2, "L1.4": 1, "L1.5": 2,
    "L2.1": 2, "L2.2": 2, "L2.3": 2, "L2.4": 2, "L2.5": 2, "L2.6": 3, "L2.7": 2,
    "L3.1": 2, "L3.2": 2, "L3.3": 2, "L3.4": 2, "L3.5": 1,
    "L4.1": 2, "L4.2": 2, "L4.3": 1, "L4.4": 2, "L4.5": 2,
}

EVALUATORS = ["A", "B", "C"]
PAIRS = [("A", "B"), ("A", "C"), ("B", "C")]
KAPPA_THRESHOLD = 0.6


def load_scores():
    """Load all scores: {bundle_id: {evaluator: {dim: score}}}"""
    data = defaultdict(dict)
    missing = []
    for ev in EVALUATORS:
        ev_dir = SCORES_DIR / f"evaluator_{ev}"
        if not ev_dir.exists():
            missing.append(f"evaluator_{ev} dir missing")
            continue
        for f in sorted(ev_dir.glob("BUNDLE_*.json")):
            bundle_id = f.stem
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    j = json.load(fh)
                data[bundle_id][ev] = j["scores"]
            except Exception as e:
                missing.append(f"{ev}/{bundle_id}: {e}")
    return data, missing


def cohen_kappa(scores1, scores2):
    """Cohen's kappa for two raters on ordinal/categorical data."""
    n = len(scores1)
    if n == 0:
        return 0.0, 0.0
    # Observed agreement
    po = sum(1 for a, b in zip(scores1, scores2) if a == b) / n
    # Expected agreement by chance
    categories = sorted(set(list(scores1) + list(scores2)))
    freq1 = defaultdict(int)
    freq2 = defaultdict(int)
    for a in scores1:
        freq1[a] += 1
    for b in scores2:
        freq2[b] += 1
    pe = sum((freq1[c] / n) * (freq2[c] / n) for c in categories)
    if pe == 1.0:
        # All same category, perfect agreement but kappa undefined → 1.0
        return 1.0, po
    kappa = (po - pe) / (1 - pe) if (1 - pe) > 0 else 1.0
    return kappa, po


def quadratic_weighted_kappa(scores1, scores2, max_score):
    """Quadratic Weighted Kappa for ordinal ratings."""
    n = len(scores1)
    if n == 0:
        return 0.0
    categories = list(range(max_score + 1))
    k = len(categories)
    # Confusion matrix
    O = [[0] * k for _ in range(k)]
    for a, b in zip(scores1, scores2):
        O[a][b] += 1
    # Row and column sums
    row_sum = [sum(O[i]) for i in range(k)]
    col_sum = [sum(O[i][j] for i in range(k)) for j in range(k)]
    total = sum(row_sum)
    if total == 0:
        return 0.0
    # Expected matrix
    E = [[(row_sum[i] * col_sum[j]) / total for j in range(k)] for i in range(k)]
    # Weights (quadratic)
    max_w = (k - 1) ** 2
    # Numerator and denominator
    num = 0.0
    den = 0.0
    for i in range(k):
        for j in range(k):
            w = ((i - j) ** 2) / max_w if max_w > 0 else 0.0
            num += w * O[i][j]
            den += w * E[i][j]
    if den == 0:
        return 1.0  # Perfect agreement
    qwk = 1.0 - num / den
    return qwk


def detect_kappa_paradox(dim, pair_results, all_scores):
    """Detect kappa paradox: high po but low kappa due to skewed marginal."""
    # If po >= 0.85 and kappa < 0.4, likely paradox
    for pair, res in pair_results.items():
        if res["po"] >= 0.85 and res["kappa"] < 0.4:
            return True
    return False


def main():
    data, missing = load_scores()

    # Check completeness
    bundles = sorted(data.keys())
    n_bundles = len(bundles)
    completeness = {}
    for ev in EVALUATORS:
        completeness[ev] = sum(1 for b in bundles if ev in data[b])

    print(f"Loaded {n_bundles} bundles")
    for ev in EVALUATORS:
        print(f"  Evaluator {ev}: {completeness[ev]}/{n_bundles} files")
    if missing:
        print(f"  Missing/errors: {missing}")

    if n_bundles == 0:
        print("ERROR: No score files found!")
        sys.exit(1)

    # Compute per-dimension kappa
    dimension_kappa = {}
    all_mean_kappas = []
    all_mean_qwks = []
    n_dims_ge_threshold = 0
    n_dims_lt_threshold = 0
    low_kappa_dims = []

    for dim in DIMENSIONS:
        max_s = MAX_SCORES[dim]
        pair_results = {}
        kappas = []
        qwks = []
        pos = []

        for ev1, ev2 in PAIRS:
            s1 = []
            s2 = []
            for b in bundles:
                if ev1 in data[b] and ev2 in data[b] and dim in data[b][ev1] and dim in data[b][ev2]:
                    s1.append(data[b][ev1][dim])
                    s2.append(data[b][ev2][dim])
            n_pair = len(s1)
            k, po = cohen_kappa(s1, s2)
            q = quadratic_weighted_kappa(s1, s2, max_s)
            pair_results[f"{ev1}-{ev2}"] = {
                "kappa": round(k, 4),
                "po": round(po, 4),
                "qwk": round(q, 4),
                "n_packages": n_pair,
            }
            kappas.append(k)
            qwks.append(q)
            pos.append(po)

        mean_k = sum(kappas) / len(kappas)
        mean_q = sum(qwks) / len(qwks)
        mean_po = sum(pos) / len(pos)

        # Kappa paradox detection
        is_paradox = detect_kappa_paradox(dim, pair_results, None)

        dimension_kappa[dim] = {
            **{f"{ev1}-{ev2}": pair_results[f"{ev1}-{ev2}"] for ev1, ev2 in PAIRS},
            "mean_kappa": round(mean_k, 4),
            "mean_qwk": round(mean_q, 4),
            "max_score": max_s,
            "mean_po": round(mean_po, 4),
            "kappa_paradox": is_paradox,
        }

        all_mean_kappas.append(mean_k)
        all_mean_qwks.append(mean_q)

        if mean_k >= KAPPA_THRESHOLD or is_paradox:
            n_dims_ge_threshold += 1
        else:
            n_dims_lt_threshold += 1
            low_kappa_dims.append(dim)

    overall_mean_kappa = sum(all_mean_kappas) / len(all_mean_kappas)
    overall_mean_qwk = sum(all_mean_qwks) / len(all_mean_qwks)

    # Disagreement analysis for low-kappa dimensions
    disagreements = []
    for dim in low_kappa_dims:
        # Find bundles with max spread
        spread_examples = []
        for b in bundles:
            scores = []
            for ev in EVALUATORS:
                if ev in data[b] and dim in data[b][ev]:
                    scores.append(data[b][ev][dim])
            if len(scores) == 3:
                spread = max(scores) - min(scores)
                if spread >= 1:
                    spread_examples.append({"bundle_id": b, "scores": scores, "spread": spread})
        spread_examples.sort(key=lambda x: -x["spread"])
        top_examples = [
            {"bundle_id": e["bundle_id"], "scores": e["scores"]}
            for e in spread_examples[:5]
        ]
        max_spread = max((e["spread"] for e in spread_examples), default=0)
        disagreements.append({
            "dimension": dim,
            "mean_kappa": dimension_kappa[dim]["mean_kappa"],
            "max_disagreement_spread": max_spread,
            "n_bundles_with_disagreement": len(spread_examples),
            "disagreement_examples": top_examples,
            "attribution": "正式盲评残余分歧，待人工审查" if not dimension_kappa[dim]["kappa_paradox"] else "Kappa 悖论伪影（边际分布极端偏斜）",
        })

    result = {
        "experiment": "P15-K003 formal blind evaluation",
        "n_evaluators": 3,
        "n_bundles": n_bundles,
        "n_dimensions": 22,
        "evaluator_completeness": completeness,
        "missing_files": missing,
        "dimension_kappa": dimension_kappa,
        "overall": {
            "mean_kappa": round(overall_mean_kappa, 4),
            "mean_qwk": round(overall_mean_qwk, 4),
            "n_dimensions_ge_0.6": n_dims_ge_threshold,
            "n_dimensions_lt_0.6": n_dims_lt_threshold,
            "pass_rate": round(n_dims_ge_threshold / 22, 4),
        },
        "disagreements": disagreements,
        "kappa_threshold": KAPPA_THRESHOLD,
        "pass_criterion": "维度级 mean κ ≥ 0.6，或 Kappa 悖论伪影标注",
        "g2_calibration_reference": {
            "mean_kappa": 0.712,
            "mean_qwk": 0.7322,
            "n_dimensions_ge_0.6": 13,
            "n_calibration_packages": 8,
        },
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n=== Kappa Results ===")
    print(f"Overall mean κ: {overall_mean_kappa:.4f}")
    print(f"Overall mean QWK: {overall_mean_qwk:.4f}")
    print(f"Dims ≥ 0.6: {n_dims_ge_threshold}/22")
    print(f"Dims < 0.6: {n_dims_lt_threshold}/22")
    print(f"Pass rate: {n_dims_ge_threshold/22:.1%}")
    print(f"\nLow-kappa dimensions: {low_kappa_dims}")
    print(f"\nOutput written to: {OUTPUT}")

    # Print per-dimension table
    print(f"\n{'Dim':<6} {'max':>3} {'mean_κ':>8} {'mean_QWK':>9} {'po':>7} {'paradox':>8}")
    print("-" * 50)
    for dim in DIMENSIONS:
        d = dimension_kappa[dim]
        print(f"{dim:<6} {d['max_score']:>3} {d['mean_kappa']:>8.4f} {d['mean_qwk']:>9.4f} {d['mean_po']:>7.4f} {str(d['kappa_paradox']):>8}")


if __name__ == "__main__":
    main()
