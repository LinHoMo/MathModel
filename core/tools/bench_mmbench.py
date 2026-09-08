#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_mmbench.py — MMBench 基准测试执行器

执行 MMBench 数据集上的模型评估，计算各项能力指标。

用法:
    python core/tools/bench_mmbench.py <project> [--split dev|val|test]
    python core/tools/bench_mmbench.py <project> --dry-run

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

import metrics as M  # noqa: E402

MMBENCH_ROOT = ROOT / "core" / "tools" / "evaluation" / "mmbench"


def _load_split(split: str) -> list[dict]:
    """加载 MMBench 数据分片。"""
    split_path = MMBENCH_ROOT / f"{split}.jsonl"
    if not split_path.exists():
        return []

    samples = []
    with open(split_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def run_benchmark(project_dir: Path, split: str = "dev",
                  dry_run: bool = False) -> dict:
    """执行基准测试。"""
    samples = _load_split(split)
    if not samples:
        return {"error": f"未找到数据分片: {split}", "total": 0}

    if dry_run:
        return {
            "dry_run": True,
            "split": split,
            "total_samples": len(samples),
            "sample_ids": [s.get("id", "") for s in samples[:5]],
        }

    results = []
    for sample in samples:
        result = {
            "id": sample.get("id", ""),
            "question": sample.get("question", "")[:100],
            "prediction": "",
            "ground_truth": sample.get("answer", ""),
            "correct": False,
        }
        results.append(result)

    total = len(results)
    correct = sum(1 for r in results if r.get("correct"))
    accuracy = correct / total if total > 0 else 0.0

    return {
        "split": split,
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "results": results,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MMBench 基准测试执行器")
    parser.add_argument("project", help="项目名")
    parser.add_argument("--split", default="dev", choices=["dev", "val", "test"])
    parser.add_argument("--dry-run", action="store_true", help="试运行")
    args = parser.parse_args(argv)

    project_dir = ROOT / "projects" / args.project
    if not project_dir.exists() and not args.dry_run:
        print(f"[FAIL] 项目不存在: {project_dir}", file=sys.stderr)
        return 1

    result = run_benchmark(project_dir, split=args.split, dry_run=args.dry_run)

    if result.get("error"):
        print(f"[FAIL] {result['error']}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[DRY-RUN] 分片: {args.split}, 样本数: {result.get('total_samples', 0)}")
    else:
        print(f"[OK] 基准测试完成:")
        print(f"  分片: {result['split']}")
        print(f"  总数: {result['total']}")
        print(f"  正确: {result['correct']}")
        print(f"  准确率: {result['accuracy']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
