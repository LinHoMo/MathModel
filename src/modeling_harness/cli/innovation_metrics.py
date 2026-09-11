#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""innovation_metrics.py —— 结构距离与创新度量（R3 Rank 工具，只读，不阻塞交付）。

判据：docs/architecture/MODEL_QUALITY_CRITERIA.md §3（R3，v1.1）。

口径
----
* 实例声明 `innovation.structure_distance` → 直接采用声明值（declared=True）；
* 未声明 → 一阶二值距离：model_family.primary ∈ 题面 allowed_modeling_structures
  → 0，否则 1（v1 二值；结构本体图与相似度深化后升级为连续距离）；
* 同时报告创新维度声明（仅非零维度）与 difference_arguments 数量。

创新是 Rank 线（排序参考），不是合格线；本工具只读报告，退出码恒 0。
零第三方运行时依赖（pyyaml 不在本模块使用）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def binary_structure_distance(family, allowed) -> float:
    """一阶二值结构距离：family ∈ allowed → 0，否则 → 1（v1 口径）。"""
    if not allowed:
        return 1.0
    return 0.0 if str(family) in [str(a) for a in allowed] else 1.0


def _family_primary(mf):
    if isinstance(mf, dict):
        return mf.get("primary") or mf.get("id")
    return mf


def _allowed_structures(data):
    pb = data.get("problem_binding") or {}
    allowed = pb.get("allowed_modeling_structures") or []
    return list(allowed)


def innovation_report(project_path) -> dict:
    """对活跃实例计算结构距离与创新声明度量（Rank 数据）。"""
    from modeling_harness.cli.validate import _live_project_dirs

    per_project: dict[str, dict] = {}
    for pdir in _live_project_dirs(Path(project_path)):
        mir = pdir / "model_ir.json"
        if not mir.exists():
            continue
        try:
            data = json.loads(mir.read_text(encoding="utf-8"))
        except Exception:
            continue
        innov = data.get("innovation") or {}
        declared = bool(innov)
        sd = innov.get("structure_distance")
        if sd is None:
            family = _family_primary(data.get("model_family"))
            allowed = _allowed_structures(data)
            sd = binary_structure_distance(family, allowed)
        dims = innov.get("dimensions") or {}
        args = innov.get("difference_arguments") or []
        per_project[pdir.name] = {
            "structure_distance": float(sd),
            "declared": declared,
            "dimensions": {k: v for k, v in dims.items()
                           if isinstance(v, (int, float)) and v > 0},
            "arguments": len(args) if isinstance(args, list) else 0,
        }
    return {"total": len(per_project), "per_project": per_project}


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    rep = innovation_report(root)
    print("=" * 60)
    print("R3 结构距离与创新声明度量（Rank，不阻塞）")
    print("=" * 60)
    if not rep["total"]:
        print("  无活跃实例（projects/ 为空或缺少 model_ir.json）")
        return 0
    for name, d in sorted(rep["per_project"].items()):
        dims = ", ".join(f"{k}={v}" for k, v in d["dimensions"].items()) or "-"
        src = "声明" if d["declared"] else "二值计算"
        print(f"  {name:16s} d_structure={d['structure_distance']:.2f} "
              f"({src})  创新维度[{dims}]  arguments={d['arguments']}")
    print("-" * 60)
    print("口径：声明值优先；未声明用一阶二值（family∈allowed→0 否则 1）。")
    print("v1 二值距离待结构本体图深化为连续相似度（见审查文档 D2/R3 遗留项）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
