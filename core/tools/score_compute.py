#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_compute.py — 评分计算器

整合评分流程：调用 score_artifact 计算原始分，再用 weight_profiles 加权聚合。

用法:
    python core/tools/score_compute.py <project>
    python core/tools/score_compute.py <project> --profile default
    python core/tools/score_compute.py <project> --output report.json

零第三方依赖。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "tools"))
for _cat in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
    sys.path.insert(0, str(ROOT / "core" / "tools" / _cat))

import score_artifact as SA  # noqa: E402
import weight_profiles as WP  # noqa: E402


def compute_score(project_dir: Path, profile_name: str = "default") -> dict:
    """计算项目评分。"""
    raw_scores = SA.score_project(project_dir)
    weights = WP.get_weights(profile_name)

    weighted_total = 0.0
    breakdown = {}
    for dim, raw in raw_scores.items():
        w = weights.get(dim, 0.0)
        weighted = raw * w
        weighted_total += weighted
        breakdown[dim] = {
            "raw": raw,
            "weight": w,
            "weighted": round(weighted, 4),
        }

    return {
        "project": project_dir.name,
        "profile": profile_name,
        "weighted_total": round(weighted_total, 4),
        "raw_scores": raw_scores,
        "breakdown": breakdown,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="评分计算器")
    parser.add_argument("project", help="项目名")
    parser.add_argument("--profile", default="default", help="权重配置")
    parser.add_argument("-o", "--output", help="输出路径")
    args = parser.parse_args(argv)

    project_dir = ROOT / "projects" / args.project
    if not project_dir.exists():
        print(f"[FAIL] 项目不存在: {project_dir}", file=sys.stderr)
        return 1

    result = compute_score(project_dir, args.profile)

    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[OK] 评分报告已保存: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    print(f"\n加权总分: {result['weighted_total']}")
    for dim, info in result["breakdown"].items():
        print(f"  {dim:20s}: {info['raw']:.4f} × {info['weight']:.2f} = {info['weighted']:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
