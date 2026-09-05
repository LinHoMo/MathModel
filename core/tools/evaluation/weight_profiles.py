#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""weight_profiles.py — 题型差异化评审权重

根据赛题类型（A/B/C/D/E/MCM/ICM）调整 5 个评分员的权重。
基础权重 × 题型乘子 → clamp [0.7, 1.5] → 归一化。

用法:
    from weight_profiles import get_weights
    weights = get_weights("C")  # C 题权重

    python core/tools/weight_profiles.py [题型]  # CLI 查看权重

零第三方依赖。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core" / "env"))

from loader import get  # noqa: E402

DEFAULT_BASE = {
    "scorer-academic": 0.25,
    "scorer-engineering": 0.20,
    "scorer-judge": 0.25,
    "scorer-reader": 0.15,
    "scorer-adversarial": 0.15,
}

DEFAULT_MULTIPLIERS = {
    "A": {"scorer-engineering": 1.3, "scorer-judge": 1.2, "scorer-academic": 0.9, "scorer-reader": 0.8, "scorer-adversarial": 0.9},
    "B": {"scorer-engineering": 1.2, "scorer-judge": 1.2, "scorer-academic": 0.9, "scorer-reader": 0.8, "scorer-adversarial": 1.0},
    "C": {"scorer-academic": 1.3, "scorer-adversarial": 1.2, "scorer-judge": 1.0, "scorer-engineering": 0.8, "scorer-reader": 0.8},
    "D": {"scorer-reader": 1.3, "scorer-academic": 1.2, "scorer-judge": 1.0, "scorer-engineering": 0.8, "scorer-adversarial": 0.8},
    "E": {"scorer-engineering": 1.2, "scorer-judge": 1.1, "scorer-academic": 1.0, "scorer-reader": 0.9, "scorer-adversarial": 0.9},
    "MCM": {"scorer-reader": 1.4, "scorer-academic": 1.1, "scorer-judge": 1.0, "scorer-engineering": 0.8, "scorer-adversarial": 0.8},
    "ICM": {"scorer-reader": 1.3, "scorer-adversarial": 1.2, "scorer-academic": 1.0, "scorer-judge": 0.9, "scorer-engineering": 0.7},
}


def get_weights(problem_type: str) -> dict[str, float]:
    """根据题型返回归一化后的评审权重。

    Args:
        problem_type: 题型标识（A/B/C/D/E/MCM/ICM），不区分大小写。

    Returns:
        {scorer_name: weight}，权重之和为 1.0。
    """
    base = get("review.weight_profiles.base", default=DEFAULT_BASE)
    multipliers_all = get("review.weight_profiles.multipliers", default=DEFAULT_MULTIPLIERS)
    clamp_range = get("review.weight_profiles.clamp", default=[0.7, 1.5])

    key = problem_type.upper()
    multipliers = multipliers_all.get(key, {})

    lo, hi = clamp_range[0], clamp_range[1]
    adjusted = {}
    for scorer, w in base.items():
        m = multipliers.get(scorer, 1.0)
        m = max(lo, min(hi, m))
        adjusted[scorer] = w * m

    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: round(v / total, 4) for k, v in adjusted.items()}

    return adjusted


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="题型差异化评审权重")
    parser.add_argument("problem_type", nargs="?", default=None,
                        help="题型（A/B/C/D/E/MCM/ICM），不指定则显示全部")
    args = parser.parse_args(argv)

    if args.problem_type:
        weights = get_weights(args.problem_type)
        print(f"题型 {args.problem_type.upper()} 评审权重:")
        for scorer, w in sorted(weights.items(), key=lambda x: -x[1]):
            bar = "█" * int(w * 40)
            print(f"  {scorer:25s} {w:.4f}  {bar}")
        print(f"  {'合计':25s} {sum(weights.values()):.4f}")
    else:
        for pt in ["A", "B", "C", "D", "E", "MCM", "ICM"]:
            weights = get_weights(pt)
            top = max(weights, key=weights.get)
            print(f"  {pt:4s}: top={top}({weights[top]:.3f})  "
                  + "  ".join(f"{k.split('-')[1][0]}={v:.3f}" for k, v in sorted(weights.items())))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
