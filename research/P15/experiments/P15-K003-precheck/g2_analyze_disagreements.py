"""
P15-K003 G2 — 详细分歧归因分析。
对每个 κ<0.6 的维度，输出 3 evaluator × 8 package 的评分矩阵，定位分歧点。
"""
import json
from pathlib import Path
from itertools import combinations

PRECHECK = Path(__file__).resolve().parent
G2_DIR = PRECHECK / "g2"
EVALUATORS = ["A", "B", "C"]
CALIB_IDS = [f"CALIB_{i:02d}" for i in range(1, 9)]

DIMENSIONS = {
    "L1.1": 2, "L1.2": 2, "L1.3": 2, "L1.4": 1, "L1.5": 2,
    "L2.1": 2, "L2.2": 2, "L2.3": 2, "L2.4": 2, "L2.5": 2, "L2.6": 3, "L2.7": 2,
    "L3.1": 2, "L3.2": 2, "L3.3": 2, "L3.4": 2, "L3.5": 1,
    "L4.1": 2, "L4.2": 2, "L4.3": 1, "L4.4": 2, "L4.5": 2,
}

def load_all_scores():
    scores = {}
    for ev in EVALUATORS:
        scores[ev] = {}
        for cid in CALIB_IDS:
            fpath = G2_DIR / f"evaluator_{ev}" / f"{cid}.json"
            data = json.loads(fpath.read_text(encoding="utf-8"))
            dim_scores = {}
            for layer in ["L1", "L2", "L3", "L4"]:
                dims = data.get(layer, {}).get("dimensions", {})
                for dk, dv in dims.items():
                    if dk in DIMENSIONS:
                        dim_scores[dk] = dv.get("score", 0)
            scores[ev][cid] = dim_scores
    return scores

def main():
    scores = load_all_scores()
    kappa_data = json.loads((G2_DIR / "g2_kappa.json").read_text(encoding="utf-8"))

    print("=" * 80)
    print("G2 分歧归因详细分析（κ<0.6 的维度）")
    print("=" * 80)

    for dim in DIMENSIONS:
        mk = kappa_data["dimension_kappa"][dim]["mean_kappa"]
        if mk >= 0.6:
            continue

        print(f"\n{'─' * 80}")
        print(f"维度 {dim} (满分{DIMENSIONS[dim]})  mean_κ={mk}  "
              f"mean_po={kappa_data['dimension_kappa'][dim]['mean_po']}")
        print(f"{'─' * 80}")

        # 评分矩阵
        header = f"{'Package':<12}" + "".join(f"{'Ev'+e:>6}" for e in EVALUATORS) + f"{'spread':>8}"
        print(header)
        print("-" * len(header))

        disagreements = []
        for cid in CALIB_IDS:
            vals = [scores[ev][cid].get(dim, 0) for ev in EVALUATORS]
            spread = max(vals) - min(vals)
            row = f"{cid:<12}" + "".join(f"{v:>6}" for v in vals) + f"{spread:>8}"
            print(row)
            if spread > 0:
                disagreements.append((cid, vals, spread))

        # 边际分布
        all_vals = [scores[ev][cid].get(dim, 0) for ev in EVALUATORS for cid in CALIB_IDS]
        from collections import Counter
        dist = Counter(all_vals)
        print(f"\n  评分分布: {dict(sorted(dist.items()))}")
        print(f"  分歧包数: {len(disagreements)}/8")

        if disagreements:
            print(f"  分歧详情:")
            for cid, vals, spread in sorted(disagreements, key=lambda x: -x[2]):
                print(f"    {cid}: A={vals[0]} B={vals[1]} C={vals[2]} (spread={spread})")

    # 总结：按归因类型分类
    print(f"\n\n{'=' * 80}")
    print("归因总结")
    print("=" * 80)

    # 读取 condition_map 用于分析（仅归因用，不对外）
    cond = json.loads((G2_DIR / "_condition_map.json").read_text(encoding="utf-8"))

    # L3.3 特殊分析：F臂 fidelity=null 的评分分歧
    print("\n【L3.3 结果收敛性】F臂 fidelity=null 评分分歧:")
    for cid in CALIB_IDS:
        arm = cond[cid]["arm"]
        if arm == "F":
            vals = [scores[ev][cid].get("L3.3", 0) for ev in EVALUATORS]
            print(f"  {cid} ({arm}): A={vals[0]} B={vals[1]} C={vals[2]}")

    # L1.4 特殊分析：假设是否算歧义标注
    print("\n【L1.4 歧义点标注】评分分歧:")
    for cid in CALIB_IDS:
        vals = [scores[ev][cid].get("L1.4", 0) for ev in EVALUATORS]
        if max(vals) - min(vals) > 0:
            print(f"  {cid}: A={vals[0]} B={vals[1]} C={vals[2]}")

if __name__ == "__main__":
    main()
