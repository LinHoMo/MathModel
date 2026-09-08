#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e2e_metrics.py — 端到端指标计算

从验证产物计算端到端指标：精度、覆盖率、一致性等。

用法:
    python core/tools/e2e_metrics.py <project>
    python core/tools/e2e_metrics.py <project> --output metrics.json

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


def compute_metrics(project_dir: Path) -> dict:
    """计算端到端指标。"""
    work_dir = project_dir / "work"
    metrics = {
        "project": project_dir.name,
        "artifacts": {},
        "coverage": 0.0,
        "consistency": 0.0,
    }

    registry_path = work_dir / "artifact_registry.json"
    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
        artifacts = registry.get("artifacts", {})
        total = len(artifacts)
        validated = sum(1 for a in artifacts.values()
                       if isinstance(a, dict) and a.get("status") == "validated")
        metrics["artifacts"]["total"] = total
        metrics["artifacts"]["validated"] = validated
        metrics["coverage"] = validated / total if total > 0 else 0.0

    state_path = work_dir / "state.json"
    if state_path.exists():
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
        completed = state.get("completed", [])
        failed = state.get("failed", [])
        total_steps = len(completed) + len(failed)
        metrics["consistency"] = len(completed) / total_steps if total_steps > 0 else 0.0

    return metrics


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="端到端指标计算")
    parser.add_argument("project", help="项目名")
    parser.add_argument("-o", "--output", help="输出路径")
    args = parser.parse_args(argv)

    project_dir = ROOT / "projects" / args.project
    if not project_dir.exists():
        print(f"[FAIL] 项目不存在: {project_dir}", file=sys.stderr)
        return 1

    metrics = compute_metrics(project_dir)

    if args.output:
        Path(args.output).write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[OK] 指标已保存: {args.output}")
    else:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
