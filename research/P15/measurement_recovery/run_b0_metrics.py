#!/usr/bin/env python3
"""Run e2e metrics for a B0 project and print summary."""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "core" / "tools"))
from e2e_metrics import compute_e2e_metrics

project = sys.argv[1]
gt_path = sys.argv[2] if len(sys.argv) > 2 else None

gt = json.load(open(gt_path, encoding="utf-8")) if gt_path else None
r = compute_e2e_metrics(project, gt=gt)

print(f"=== {r['project']} ===")
print(f"Computed: {r['summary']['computed']}/8, Mean: {r['summary']['mean_of_available']}")
for name, m in r["metrics"].items():
    v = "n/a" if m["value"] is None else m["value"]
    print(f"  {name}: {v}")
print(f"Empty artifacts excluded: {r['empty_artifact_filter'].get('total_excluded', 0)}")
mi = r.get("measurement_integrity", {})
if mi:
    print(f"  overall_real_artifact: {mi.get('overall_real_artifact', {}).get('value', 'n/a')}%")

# Save full report
out = Path(project) / "state" / "e2e_metrics_report.json"
out.parent.mkdir(parents=True, exist_ok=True)
json.dump(r, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Full report: {out}")
