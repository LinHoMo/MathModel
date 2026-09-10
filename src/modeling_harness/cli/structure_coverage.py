#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""structure_coverage.py —— 模型结构解析与覆盖率度量（能力层：结构可识别性）。

用途
----
把 `src/modeling_harness/catalog/model_families.yaml`（受控词表）当唯一真源，
把任意来源（实例 model_ir、基准 gt、生成侧）给出的**模型结构名**解析到 canonical
family；未命中的记为 `out_of_catalog`。据此度量「方法结构对齐」能力的缺口——
把 `docs/PROJECTS_FEEDBACK_AUDIT.md §4`「词表无交集」从散文变成可测数字。

解析口径（对齐词表头部治理声明）
--------------------------------
族命中 = id OR alias OR mechanism OR method OR solver 任一落在本表；
未命中 → "out_of_catalog"（不自动判错，由评审语义判断）。

本模块**只读**词表，不改动 frozen 的词表本身。

零第三方运行时依赖（yaml 用于解析词表，属工具链既有依赖）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

_CATALOG = Path(__file__).resolve().parent.parent / "catalog" / "model_families.yaml"


def _load_families() -> list:
    if yaml is None:  # pragma: no cover
        raise RuntimeError("解析 model_families.yaml 需要 pyyaml")
    with open(_CATALOG, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("canonical_families") or []


def build_index(families=None) -> dict:
    """构建 名字(小写) → family_id 索引；families=None 时加载真实词表。"""
    fams = _load_families() if families is None else families
    idx: dict[str, str] = {}
    for fam in fams:
        fid = fam.get("id")
        if not fid:
            continue
        names = [fid]
        for key in ("aliases", "mechanism", "methods", "solvers"):
            names += list(fam.get(key) or [])
        for n in names:
            idx.setdefault(str(n).lower(), fid)
    return idx


def resolve_structure(name: str, index: dict) -> str:
    """把结构名解析到 canonical family_id；未命中返回 "out_of_catalog"。"""
    return index.get(str(name).lower(), "out_of_catalog")


def _structures_of(mir_data: dict) -> list:
    """从实例 model_ir 取结构名列表（顶层或 problem_binding 内）。"""
    s = mir_data.get("allowed_modeling_structures")
    if not s:
        s = (mir_data.get("problem_binding") or {}).get("allowed_modeling_structures")
    return list(s or [])


def coverage_report(project_path, families=None) -> dict:
    """对活跃实例的 allowed_modeling_structures 计算解析覆盖率。"""
    from modeling_harness.cli.validate import _live_project_dirs

    index = build_index(families)
    total = resolved = 0
    ooc: list[tuple[str, str]] = []
    per_project: dict[str, dict] = {}
    for pdir in _live_project_dirs(Path(project_path)):
        mir = pdir / "model_ir.json"
        if not mir.exists():
            continue
        try:
            data = json.loads(mir.read_text(encoding="utf-8"))
        except Exception:
            continue
        names = _structures_of(data)
        if not names:
            continue
        p_res = 0
        for s in names:
            total += 1
            if resolve_structure(s, index) == "out_of_catalog":
                ooc.append((pdir.name, s))
            else:
                resolved += 1
                p_res += 1
        per_project[pdir.name] = {"total": len(names), "resolved": p_res}
    return {"total": total, "resolved": resolved,
            "ratio": (resolved / total if total else 1.0),
            "out_of_catalog": ooc, "per_project": per_project}


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    rep = coverage_report(root)
    print("=" * 60)
    print("模型结构解析覆盖率（model_families 受控词表）")
    print("=" * 60)
    for name, d in sorted(rep["per_project"].items()):
        print(f"  {name:16s} {d['resolved']}/{d['total']}")
    print(f"  合计: {rep['resolved']}/{rep['total']} = {rep['ratio']:.1%}")
    if rep["out_of_catalog"]:
        print("  out_of_catalog（词表无交集 → 需 Architecture Gate 评审）:")
        for proj, s in rep["out_of_catalog"]:
            print(f"    {proj}: {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
