"""
P15-K003 配对分析 — block 级配对差 + bootstrap CI。

主终点：
  MCQ_primary = (L2+L3+L4) / (15+9+9) × 100
  VAL_primary = L4 / 9 × 100

配对设计：同题同 rep（problem_id + seed）的 F/S/SV 三臂构成一个 block。
主检验 6 题 × 3 rep = 18 blocks；泛化 2 题 × 2 rep = 4 blocks。

对比：S−F, SV−F（主终点 + 敏感性：逐层 L1/L2/L3/L4）。
bootstrap: 10000 resamples of blocks, percentile 95% CI.
"""
import json
import random
from pathlib import Path
from collections import defaultdict

EXP = Path(__file__).resolve().parent.parent
SCORES_DIR = EXP / "scores"
KEY_DIR = EXP / "key"
ANALYSIS_DIR = EXP / "analysis"
ANALYSIS_DIR.mkdir(exist_ok=True)

EVALUATORS = ["A", "B", "C"]
BUNDLE_IDS = [f"BUNDLE_{i:03d}" for i in range(1, 67)]

MAIN_PROBLEMS = ["2020_B", "2018_A", "2019_C", "2018_B", "2017_B", "2011_B"]
GEN_PROBLEMS = ["2022_C", "2024_A"]
ALL_PROBLEMS = MAIN_PROBLEMS + GEN_PROBLEMS

LAYER_MAX = {"L1": 9, "L2": 15, "L3": 9, "L4": 9}
MCQ_MAX = 15 + 9 + 9  # 33
VAL_MAX = 9

random.seed(42)
N_BOOTSTRAP = 10000


def load_condition_map():
    with open(KEY_DIR / "condition_map.json", encoding="utf-8") as f:
        return json.load(f)


def load_bundle_scores():
    """返回 {bundle_id: {layer: score}} —— 3 evaluator 取均值。"""
    bundle_layer_scores = defaultdict(lambda: defaultdict(list))
    missing = []
    for ev in EVALUATORS:
        ev_dir = SCORES_DIR / f"evaluator_{ev}"
        for bid in BUNDLE_IDS:
            fpath = ev_dir / f"{bid}.json"
            if not fpath.exists():
                missing.append(f"{ev}/{bid}.json")
                continue
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                lt = data.get("layer_totals", {})
                for layer in ["L1", "L2", "L3", "L4"]:
                    if layer in lt:
                        bundle_layer_scores[bid][layer].append(lt[layer])
            except Exception as e:
                missing.append(f"{ev}/{bid}.json parse error: {e}")
    # 取均值
    result = {}
    for bid in BUNDLE_IDS:
        result[bid] = {}
        for layer in ["L1", "L2", "L3", "L4"]:
            vals = bundle_layer_scores[bid].get(layer, [])
            result[bid][layer] = sum(vals) / len(vals) if vals else 0.0
    return result, missing


def compute_endpoints(layer_scores):
    """MCQ = (L2+L3+L4)/33*100, VAL = L4/9*100。"""
    mcq = (layer_scores["L2"] + layer_scores["L3"] + layer_scores["L4"]) / MCQ_MAX * 100
    val = layer_scores["L4"] / VAL_MAX * 100
    return round(mcq, 2), round(val, 2)


def build_blocks(cond_map, bundle_scores):
    """按 (problem_id, seed) 分组，每 block 含 F/S/SV 三臂的 endpoint。"""
    blocks = defaultdict(dict)  # {(problem, seed): {arm: {mcq, val, layers}}}
    for bid, info in cond_map.items():
        if bid not in bundle_scores:
            continue
        key = (info["problem_id"], info["seed"])
        arm = info["arm"]
        ls = bundle_scores[bid]
        mcq, val = compute_endpoints(ls)
        blocks[key][arm] = {
            "mcq": mcq, "val": val,
            "L1": round(ls["L1"], 2), "L2": round(ls["L2"], 2),
            "L3": round(ls["L3"], 2), "L4": round(ls["L4"], 2),
            "bundle_id": bid,
        }
    return blocks


def paired_diffs(blocks, contrast, metric, problem_set):
    """计算指定问题集上某对比的 block 级差值列表。"""
    arm1, arm2 = contrast.split("−")
    diffs = []
    for (prob, seed), arms in blocks.items():
        if prob not in problem_set:
            continue
        if arm1 in arms and arm2 in arms:
            d = arms[arm1][metric] - arms[arm2][metric]
            diffs.append(round(d, 4))
    return diffs


def bootstrap_ci(diffs, n_boot=N_BOOTSTRAP, alpha=0.05):
    """percentile bootstrap CI for mean."""
    if not diffs:
        return None, None, None
    n = len(diffs)
    means = []
    for _ in range(n_boot):
        sample = [diffs[random.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(n_boot * alpha / 2)]
    hi = means[int(n_boot * (1 - alpha / 2))]
    mean = sum(diffs) / n
    return round(mean, 4), round(lo, 4), round(hi, 4)


def cohens_d(diffs):
    """配对差值的 Cohen's d (mean / sd of diffs)."""
    if len(diffs) < 2:
        return None
    mean = sum(diffs) / len(diffs)
    var = sum((d - mean) ** 2 for d in diffs) / (len(diffs) - 1)
    sd = var ** 0.5
    if sd == 0:
        return None
    return round(mean / sd, 4)


def main():
    cond_map = load_condition_map()
    bundle_scores, missing = load_bundle_scores()

    if missing:
        print(f"WARNING: {len(missing)} missing score files")

    blocks = build_blocks(cond_map, bundle_scores)

    # 验证 block 完整性
    main_blocks = {k: v for k, v in blocks.items() if k[0] in MAIN_PROBLEMS}
    gen_blocks = {k: v for k, v in blocks.items() if k[0] in GEN_PROBLEMS}
    print(f"主检验 blocks: {len(main_blocks)} (期望 18)")
    print(f"泛化 blocks: {len(gen_blocks)} (期望 4)")

    # 每 block 三臂完整性
    incomplete = []
    for key, arms in blocks.items():
        if not all(a in arms for a in ["F", "S", "SV"]):
            incomplete.append({"block": f"{key[0]}_seed{key[1]}", "arms_present": list(arms.keys())})
    if incomplete:
        print(f"不完整 block: {len(incomplete)}")
        for inc in incomplete:
            print(f"  {inc}")

    results = {
        "experiment": "P15-K003",
        "design": {
            "main_problems": MAIN_PROBLEMS,
            "generalization_problems": GEN_PROBLEMS,
            "n_main_blocks": len(main_blocks),
            "n_gen_blocks": len(gen_blocks),
            "contrasts": ["S−F", "SV−F"],
            "metrics": ["mcq", "val", "L1", "L2", "L3", "L4"],
            "bootstrap_n": N_BOOTSTRAP,
            "ci_method": "percentile",
            "seed": 42,
        },
        "incomplete_blocks": incomplete,
        "missing_score_files": missing,
        "primary_results": {},
        "sensitivity_results": {},
        "arm_means": {},
    }

    # 各臂均值
    for arm in ["F", "S", "SV"]:
        mcq_vals = []
        val_vals = []
        layer_vals = defaultdict(list)
        for key, arms in blocks.items():
            if arm in arms:
                mcq_vals.append(arms[arm]["mcq"])
                val_vals.append(arms[arm]["val"])
                for L in ["L1", "L2", "L3", "L4"]:
                    layer_vals[L].append(arms[arm][L])
        results["arm_means"][arm] = {
            "mcq_mean": round(sum(mcq_vals) / len(mcq_vals), 2) if mcq_vals else None,
            "val_mean": round(sum(val_vals) / len(val_vals), 2) if val_vals else None,
            "n": len(mcq_vals),
            "layer_means": {L: round(sum(v) / len(v), 2) if v else None for L, v in layer_vals.items()},
        }

    # 主终点配对分析
    for scope_name, problem_set in [("main", MAIN_PROBLEMS), ("generalization", GEN_PROBLEMS), ("all", ALL_PROBLEMS)]:
        results["primary_results"][scope_name] = {}
        for contrast in ["S−F", "SV−F"]:
            results["primary_results"][scope_name][contrast] = {}
            for metric in ["mcq", "val"]:
                diffs = paired_diffs(blocks, contrast, metric, problem_set)
                mean, lo, hi = bootstrap_ci(diffs)
                d = cohens_d(diffs)
                results["primary_results"][scope_name][contrast][metric] = {
                    "n_blocks": len(diffs),
                    "mean_diff": mean,
                    "ci_95": [lo, hi],
                    "cohens_d": d,
                    "significant": (lo is not None and hi is not None and (lo > 0 or hi < 0)),
                    "diffs": diffs,
                }

    # 敏感性：逐层
    for scope_name, problem_set in [("main", MAIN_PROBLEMS), ("generalization", GEN_PROBLEMS)]:
        results["sensitivity_results"][scope_name] = {}
        for contrast in ["S−F", "SV−F"]:
            results["sensitivity_results"][scope_name][contrast] = {}
            for layer in ["L1", "L2", "L3", "L4"]:
                diffs = paired_diffs(blocks, contrast, layer, problem_set)
                mean, lo, hi = bootstrap_ci(diffs)
                d = cohens_d(diffs)
                results["sensitivity_results"][scope_name][contrast][layer] = {
                    "n_blocks": len(diffs),
                    "mean_diff": mean,
                    "ci_95": [lo, hi],
                    "cohens_d": d,
                    "significant": (lo is not None and hi is not None and (lo > 0 or hi < 0)),
                }

    out_path = ANALYSIS_DIR / "paired_analysis.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 打印摘要
    print("\n=== K003 配对分析主终点（主检验 18 blocks）===")
    print(f"{'对比':<8} {'指标':<6} {'均值差':>8} {'95% CI':>16} {'Cohen d':>8} {'显著':>4}")
    print("-" * 55)
    for contrast in ["S−F", "SV−F"]:
        for metric in ["mcq", "val"]:
            r = results["primary_results"]["main"][contrast][metric]
            ci = f"[{r['ci_95'][0]}, {r['ci_95'][1]}]" if r['ci_95'][0] is not None else "N/A"
            sig = "★" if r["significant"] else ""
            print(f"{contrast:<8} {metric:<6} {str(r['mean_diff']):>8} {ci:>16} {str(r['cohens_d']):>8} {sig:>4}")

    print("\n=== 各臂均值 ===")
    for arm in ["F", "S", "SV"]:
        am = results["arm_means"][arm]
        print(f"  {arm}: MCQ={am['mcq_mean']}, VAL={am['val_mean']}, n={am['n']}")

    print(f"\n结果已保存: {out_path}")
    return results


if __name__ == "__main__":
    main()
