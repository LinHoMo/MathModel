#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""innovation_metrics.py —— 结构距离与创新度量（R3 Rank 工具，只读，不阻塞交付）。

判据：docs/architecture/MODEL_QUALITY_CRITERIA.md §3（R3，v1.1 → §9.3 深化）。

口径（§9.3 深化后）
--------------------
* 优先采用声明值 `innovation.structure_distance`（declared=True）；
* 未声明 → 计算**连续结构距离**（`continuous_structure_distance`）：
  从 model_families.yaml 派生结构本体图 O（节点=建模结构族，边=共享机制），
  d_structure = 1 − max_{s∈model, s'∈allowed} sim(s, s')，sim 随图最短路径指数衰减；
  本体图/词表缺失时回退一阶二值距离（family∈allowed→0 否则 1）；
* 声明审计（audit）：比较声明值与机械计算值，偏差>阈值 → WARN
  （防虚报创新 / 虚报从众），R3 为 Rank 线不阻塞，audit 仅提示；
* 同时报告创新维度声明（仅非零维度）与 difference_arguments 数量。

创新是 Rank 线（排序参考），不是合格线；本工具只读报告，退出码恒 0。
零第三方**导入期**依赖：pyyaml 仅在使用真实词表时按需懒加载；无词表则回退二值。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


# ======================================================================
# 一阶二值距离（v1 口径，作为本体图缺失时的回退）
# ======================================================================
def binary_structure_distance(family, allowed) -> float:
    """一阶二值结构距离：family ∈ allowed → 0，否则 → 1（v1 口径）。"""
    if not allowed:
        return 1.0
    return 0.0 if str(family) in [str(a) for a in allowed] else 1.0


# ======================================================================
# 结构本体图 O（§9.3）：节点=建模结构族，边=共享机制
# ======================================================================
def build_ontology(families):
    """从受控词表构造结构本体图与解析器。

    返回 (graph, resolve)：
      graph:  dict[node] -> dict[neighbor] -> 共享机制数（边权重）；
      resolve(token): 把任意结构名（id/alias/mechanism/method/solver）解析到
                      canonical family id；解析不到返回 None。
    """
    edges: dict = {}
    token_to_id: dict = {}
    mech_to_fams: dict = {}
    for fam in families:
        fid = fam.get("id")
        if not fid:
            continue
        edges.setdefault(fid, {})
        token_to_id.setdefault(str(fid).lower(), fid)
        for key in ("aliases", "mechanism", "methods", "solvers"):
            for tok in (fam.get(key) or []):
                token_to_id.setdefault(str(tok).lower(), fid)
        for m in (fam.get("mechanism") or []):
            mech_to_fams.setdefault(m, []).append(fid)
    # 共享机制 ⇒ 连边（权重=共享机制数）
    for fams in mech_to_fams.values():
        for i in range(len(fams)):
            for j in range(i + 1, len(fams)):
                a, b = fams[i], fams[j]
                w = edges[a].get(b, 0) + 1
                edges[a][b] = w
                edges[b][a] = edges[b].get(a, 0) + 1

    def resolve(token):
        if token is None:
            return None
        return token_to_id.get(str(token).lower())

    return edges, resolve


def family_similarity(fam_a, fam_b, graph=None) -> float:
    """两结构族在 O 上的相似度：同族=1；经共享机制相连按路径指数衰减（0.5^L）；不连通=0。

    要求 fam_a/fam_b 为 canonical id；graph 缺失或节点不在图中 → 0。
    相似度定义为最短路径上的 0.5**L（L 为跳数），使「近邻结构」distance 显著小于
    「远缘/未知结构」，把 R3 从一阶二值升级为连续量。
    """
    if graph is None:
        graph = _get_ontology()[0]
        if graph is None:
            return 0.0
    if fam_a == fam_b:
        return 1.0
    if fam_a not in graph or fam_b not in graph:
        return 0.0
    from collections import deque
    visited = {fam_a}
    q = deque([(fam_a, 0)])
    while q:
        node, d = q.popleft()
        for nb in graph[node]:
            if nb == fam_b:
                return 0.5 ** (d + 1)
            if nb not in visited:
                visited.add(nb)
                q.append((nb, d + 1))
    return 0.0


def canonicalize_token(token, resolver=None):
    """把结构名解析到 canonical family id（解析不到返回原 token）。"""
    if resolver is None:
        resolver = _get_ontology()[1]
    if resolver is None:
        return token
    cid = resolver(token)
    return cid if cid is not None else token


def continuous_structure_distance(model_family, allowed, resolver=None,
                                 graph=None) -> float:
    """连续结构距离（§9.3 深化）。

    model_family: dict（含 primary / 可选 secondary 列表）；
    allowed: 题面允许结构名列表。
    d = 1 − max_{s∈model, s'∈allowed} sim(s, s')；
    model 任一结构贴近已知结构 ⇒ d→0（与「结构距离=0」语义一致）。
    解析不到模型结构或无图 ⇒ 回退一阶二值（primary∈allowed?）。
    """
    if resolver is None or graph is None:
        graph, resolver = _get_ontology()
    if resolver is None or graph is None:
        primary = (model_family or {}).get("primary")
        return binary_structure_distance(primary, allowed)
    primary = (model_family or {}).get("primary")
    secondary = (model_family or {}).get("secondary") or []
    model_structs = []
    for s in [primary, *secondary]:
        if s is None:
            continue
        cid = resolver(s)
        if cid and cid not in model_structs:
            model_structs.append(cid)
    if not model_structs:
        return 1.0  # 无法定位到任何已知结构族 ⇒ 视为最远（新颖）
    known = set()
    for a in (allowed or []):
        cid = resolver(a)
        if cid:
            known.add(cid)
    if not known:
        return 1.0
    best = 0.0
    for ms in model_structs:
        for k in known:
            sim = family_similarity(ms, k, graph)
            if sim > best:
                best = sim
    return 1.0 - best


# ----------------------------------------------------------------------
# 本体图懒加载（保持模块导入期零第三方依赖）
# ----------------------------------------------------------------------
_ONTOLOGY = None


def _load_default_ontology():
    """懒加载 model_families.yaml → (graph, resolve)；失败返回 (None, None)。"""
    try:
        import yaml  # 仅此处按需引入，保持模块导入期零依赖
    except Exception:
        return None, None
    catalog = (Path(__file__).resolve().parent.parent
               / "catalog" / "model_families.yaml")
    if not catalog.exists():
        return None, None
    try:
        with open(catalog, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return None, None
    families = (data or {}).get("canonical_families") or []
    if not families:
        return None, None
    return build_ontology(families)


def _get_ontology():
    global _ONTOLOGY
    if _ONTOLOGY is None:
        _ONTOLOGY = _load_default_ontology()
    return _ONTOLOGY  # (graph, resolve) 或 (None, None)


# ======================================================================
# 报告（Rank 数据，只读）
# ======================================================================
AUDIT_TOLERANCE = 0.15  # 声明值与机械值偏差阈值：超此即 WARN（防虚报）


def _compute_audit(declared_sd, computed_sd):
    """声明审计：无声明 / 偏差≤阈值 / 偏差超限 / 非法值。"""
    if declared_sd is None:
        return "no_declaration"
    try:
        d = abs(float(declared_sd) - float(computed_sd))
    except (TypeError, ValueError):
        return "invalid_declared"
    if d <= AUDIT_TOLERANCE:
        return "ok"
    return "WARN_mismatch"


def _family_primary(mf):
    if isinstance(mf, dict):
        return mf.get("primary") or mf.get("id")
    return mf


def _allowed_structures(data):
    pb = data.get("problem_binding") or {}
    allowed = pb.get("allowed_modeling_structures") or []
    return list(allowed)


def innovation_report(project_path) -> dict:
    """对活跃实例计算结构距离、声明审计与创新声明度量（Rank 数据）。"""
    from modeling_harness.cli.validate import _live_project_dirs

    graph, resolver = _get_ontology()
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
        computed_sd = continuous_structure_distance(
            data.get("model_family") or {},
            _allowed_structures(data), resolver, graph)
        declared_sd = innov.get("structure_distance")
        if declared_sd is None:
            sd = computed_sd
            declared = False
        else:
            sd = float(declared_sd)
            declared = True
        dims = innov.get("dimensions") or {}
        args = innov.get("difference_arguments") or []
        per_project[pdir.name] = {
            "structure_distance": float(sd),
            "declared": declared,
            "computed_structure_distance": float(computed_sd),
            "distance_delta": (abs(float(declared_sd) - computed_sd)
                               if declared_sd is not None else None),
            "audit": _compute_audit(declared_sd, computed_sd),
            "dimensions": {k: v for k, v in dims.items()
                           if isinstance(v, (int, float)) and v > 0},
            "arguments": len(args) if isinstance(args, list) else 0,
        }
    return {"total": len(per_project), "per_project": per_project}


def main() -> int:
    args = sys.argv[1:]
    root = Path(args[0]).resolve() if args and not args[0].startswith("-") \
        else Path.cwd()
    rep = innovation_report(root)
    if "--json" in args:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0
    print("=" * 64)
    print("R3 结构距离与创新声明度量（Rank，不阻塞）")
    print("=" * 64)
    if not rep["total"]:
        print("  无活跃实例（projects/ 为空或缺少 model_ir.json）")
        return 0
    for name, d in sorted(rep["per_project"].items()):
        dims = ", ".join(f"{k}={v}" for k, v in d["dimensions"].items()) or "-"
        src = "声明" if d["declared"] else "计算"
        comp = d["computed_structure_distance"]
        delta = d["distance_delta"]
        delta_s = f"Δ={delta:.2f}" if delta is not None else "Δ=n/a"
        print(f"  {name:16s} d={d['structure_distance']:.2f} ({src})  "
              f"comp={comp:.2f} {delta_s} audit={d['audit']}  "
              f"维度[{dims}] args={d['arguments']}")
    print("-" * 64)
    print("口径：声明值优先；未声明用连续结构距离（本体图相似度，§9.3）；")
    print("声明审计偏差>0.15 → WARN（防虚报创新/虚报从众）；Rank 不阻塞。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
