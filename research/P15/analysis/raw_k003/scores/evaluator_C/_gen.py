"""Evaluator C batch generator: reads _batch_input.json -> writes per-bundle JSON.
Input format: {"bundles": [{"bundle_id": "BUNDLE_001", "scores": {...22 dims...}, "notes": "..."}]}
Scores are evaluator C's cognitive judgment; this script only computes sums and writes JSON.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["L1.1","L1.2","L1.3","L1.4","L1.5","L2.1","L2.2","L2.3","L2.4","L2.5","L2.6","L2.7",
         "L3.1","L3.2","L3.3","L3.4","L3.5","L4.1","L4.2","L4.3","L4.4","L4.5"]

def main():
    with open(os.path.join(HERE, "_batch_input.json"), encoding="utf-8-sig") as f:
        data = json.load(f)
    for item in data["bundles"]:
        bundle_id = item["bundle_id"]
        scores = item["scores"]
        notes = item.get("notes", "")
        assert set(scores.keys()) == set(ORDER), f"{bundle_id} dim mismatch"
        L1 = sum(scores[k] for k in ORDER[0:5])
        L2 = sum(scores[k] for k in ORDER[5:12])
        L3 = sum(scores[k] for k in ORDER[12:17])
        L4 = sum(scores[k] for k in ORDER[17:22])
        mcq = round((L2 + L3 + L4) / 33 * 100, 2)
        val = round(L4 / 9 * 100, 2)
        doc = {
            "bundle_id": bundle_id,
            "evaluator": "C",
            "rubric_version": "MODEL_CONSTRUCTION_RUBRIC-v1.1",
            "anchored_protocol": "v1.2a",
            "scores": {k: scores[k] for k in ORDER},
            "layer_totals": {"L1": L1, "L2": L2, "L3": L3, "L4": L4},
            "MCQ_primary": mcq,
            "VAL_primary": val,
            "notes": notes,
        }
        out = os.path.join(HERE, bundle_id + ".json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print(f"written {out} | L1={L1} L2={L2} L3={L3} L4={L4} MCQ={mcq} VAL={val}")

if __name__ == "__main__":
    main()
