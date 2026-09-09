"""Compute summary statistics for K003 blind eval scores."""
import json
import statistics
from pathlib import Path

base = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\analysis\raw_k003\scores")
dims = ["L1.1","L1.2","L1.3","L1.4","L1.5","L2.1","L2.2","L2.3","L2.4","L2.5","L2.6","L2.7",
        "L3.1","L3.2","L3.3","L3.4","L3.5","L4.1","L4.2","L4.3","L4.4","L4.5"]
layer_max = {"L1": 9, "L2": 15, "L3": 9, "L4": 9}

for ev in ["A", "B", "C"]:
    mcqs = []
    vals = []
    layer_means = {"L1": [], "L2": [], "L3": [], "L4": []}
    for f in sorted((base / f"evaluator_{ev}").glob("BUNDLE_*.json")):
        j = json.load(open(f, encoding="utf-8"))
        mcqs.append(j["MCQ_primary"])
        vals.append(j["VAL_primary"])
        for k in ["L1", "L2", "L3", "L4"]:
            layer_means[k].append(j["layer_totals"][k])
    print(f"=== Evaluator {ev} ===")
    print(f"  MCQ: mean={statistics.mean(mcqs):.2f}, median={statistics.median(mcqs):.2f}, "
          f"sd={statistics.stdev(mcqs):.2f}, min={min(mcqs):.2f}, max={max(mcqs):.2f}")
    print(f"  VAL: mean={statistics.mean(vals):.2f}, median={statistics.median(vals):.2f}, "
          f"sd={statistics.stdev(vals):.2f}")
    for k in ["L1", "L2", "L3", "L4"]:
        m = statistics.mean(layer_means[k])
        print(f"  {k}: mean={m:.2f}/{layer_max[k]} ({m/layer_max[k]*100:.1f}%)")

# Per-bundle 3-evaluator mean
bundle_mcq = {}
bundle_val = {}
for i in range(1, 67):
    bid = f"BUNDLE_{i:03d}"
    mvals = []
    vvals = []
    for ev in ["A", "B", "C"]:
        j = json.load(open(base / f"evaluator_{ev}" / (bid + ".json"), encoding="utf-8"))
        mvals.append(j["MCQ_primary"])
        vvals.append(j["VAL_primary"])
    bundle_mcq[bid] = statistics.mean(mvals)
    bundle_val[bid] = statistics.mean(vvals)

mcq_vals = list(bundle_mcq.values())
val_vals = list(bundle_val.values())
print(f"\n=== 3-Evaluator Mean (per bundle, n=66) ===")
print(f"  MCQ: mean={statistics.mean(mcq_vals):.2f}, median={statistics.median(mcq_vals):.2f}, "
      f"sd={statistics.stdev(mcq_vals):.2f}")
print(f"  MCQ min={min(mcq_vals):.2f} ({min(bundle_mcq, key=bundle_mcq.get)}), "
      f"max={max(mcq_vals):.2f} ({max(bundle_mcq, key=bundle_mcq.get)})")
print(f"  VAL: mean={statistics.mean(val_vals):.2f}, median={statistics.median(val_vals):.2f}")

# MCQ spread
spreads = []
for i in range(1, 67):
    bid = f"BUNDLE_{i:03d}"
    vals = []
    for ev in ["A", "B", "C"]:
        j = json.load(open(base / f"evaluator_{ev}" / (bid + ".json"), encoding="utf-8"))
        vals.append(j["MCQ_primary"])
    spreads.append(max(vals) - min(vals))
print(f"\n=== MCQ Inter-Evaluator Spread ===")
print(f"  mean={statistics.mean(spreads):.2f}, median={statistics.median(spreads):.2f}, max={max(spreads):.2f}")
print(f"  spread>10: {sum(1 for s in spreads if s > 10)}, >15: {sum(1 for s in spreads if s > 15)}, >20: {sum(1 for s in spreads if s > 20)}")

# Dimension means across all evaluators and bundles
print(f"\n=== Dimension Mean Scores (all 3 evals × 66 bundles) ===")
for d in dims:
    all_s = []
    for ev in ["A", "B", "C"]:
        for f in sorted((base / f"evaluator_{ev}").glob("BUNDLE_*.json")):
            j = json.load(open(f, encoding="utf-8"))
            all_s.append(j["scores"][d])
    print(f"  {d}: mean={statistics.mean(all_s):.2f}")
