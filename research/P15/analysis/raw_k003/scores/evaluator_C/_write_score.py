"""Evaluator C helper: write a bundle score JSON with computed totals.
Usage: python _write_score.py BUNDLE_001 '{"L1.1":2,...}' "notes text"
Scores are my (evaluator C) cognitive judgment; this script only computes sums and writes JSON.
"""
import json, sys, os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    bundle_id = sys.argv[1]
    scores = json.loads(sys.argv[2])
    notes = sys.argv[3] if len(sys.argv) > 3 else ""
    order = ["L1.1","L1.2","L1.3","L1.4","L1.5","L2.1","L2.2","L2.3","L2.4","L2.5","L2.6","L2.7",
             "L3.1","L3.2","L3.3","L3.4","L3.5","L4.1","L4.2","L4.3","L4.4","L4.5"]
    assert set(scores.keys()) == set(order), f"dimension mismatch: {set(order)-set(scores)} / {set(scores)-set(order)}"
    L1 = sum(scores[k] for k in ["L1.1","L1.2","L1.3","L1.4","L1.5"])
    L2 = sum(scores[k] for k in ["L2.1","L2.2","L2.3","L2.4","L2.5","L2.6","L2.7"])
    L3 = sum(scores[k] for k in ["L3.1","L3.2","L3.3","L3.4","L3.5"])
    L4 = sum(scores[k] for k in ["L4.1","L4.2","L4.3","L4.4","L4.5"])
    mcq = round((L2 + L3 + L4) / 33 * 100, 2)
    val = round(L4 / 9 * 100, 2)
    doc = {
        "bundle_id": bundle_id,
        "evaluator": "C",
        "rubric_version": "MODEL_CONSTRUCTION_RUBRIC-v1.1",
        "anchored_protocol": "v1.2a",
        "scores": {k: scores[k] for k in order},
        "layer_totals": {"L1": L1, "L2": L2, "L3": L3, "L4": L4},
        "MCQ_primary": mcq,
        "VAL_primary": val,
        "notes": notes,
    }
    out = os.path.join(OUT_DIR, bundle_id + ".json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"written {out} | L1={L1} L2={L2} L3={L3} L4={L4} MCQ={mcq} VAL={val}")

if __name__ == "__main__":
    main()
