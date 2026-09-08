#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_metrics_runner.py — e2e_metrics 调用器（由 run_evaluation.ps1 通过环境变量驱动）。

环境变量:
  EVAL_PROJECT  — 项目目录路径
  EVAL_REPO     — 仓库根路径
  EVAL_GT       — GT JSON 文件路径（可选）
  EVAL_RESPONSE — response JSON 文件路径（可选）
  EVAL_OUTPUT   — 输出 JSON 报告路径
"""
import json
import os
import sys
from pathlib import Path

REPO = Path(os.environ.get("EVAL_REPO", ""))
if not REPO:
    # 回退：从脚本位置推断
    REPO = Path(__file__).resolve().parents[3]

sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "core" / "tools" / "evaluation"))

import e2e_metrics as em  # noqa: E402

project = Path(os.environ["EVAL_PROJECT"])
gt = None
response = None

gt_path = os.environ.get("EVAL_GT", "")
if gt_path and Path(gt_path).exists():
    gt = json.loads(Path(gt_path).read_text(encoding="utf-8"))

resp_path = os.environ.get("EVAL_RESPONSE", "")
if resp_path and Path(resp_path).exists():
    response = json.loads(Path(resp_path).read_text(encoding="utf-8"))

report = em.compute_e2e_metrics(project, gt=gt, response=response)

out = Path(os.environ["EVAL_OUTPUT"])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

# 渲染 markdown
md = em.render_report(report)
md_path = out.with_suffix(".md")
md_path.write_text(md, encoding="utf-8")

print(f"Metrics report: {out}")
print(f"Markdown report: {md_path}")
print()
s = report["summary"]
print(f"Computed: {s['computed']}/8, Absent: {s['absent']}, Mean: {s['mean_of_available']}")
eaf = report.get("empty_artifact_filter", {})
if eaf.get("total_excluded", 0) > 0:
    print(f"Empty artifacts excluded: {eaf['total_excluded']} "
          f"(registry total: {eaf.get('registry_empty_total', '?')})")
