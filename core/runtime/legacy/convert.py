"""Legacy Compatibility Layer — V2 产物 ⇄ V3 Registry/Graph/State 双向转换。

职责（V3.1 §1.18 / Migration Map §6）:
    1. import_results:  V2 figures/all_results.json → R artifacts（数值快照）
        + CODE/E artifacts + produces 边（不搬文件，payload 指回原路径）
    2. export_results:  Registry R artifacts → all_results.json 兼容文件
        （V2 工具链 zero-change 继续消费，直到 P5）
    3. import_state:    V2 work/state.json（29 步）→ V3 state/status.json
        （legacy 文件原样保留，只读不写）

铁律: 转换不删除、不移动、不覆盖任何 V2 文件。
"""

from __future__ import annotations

import json
from pathlib import Path

from ..artifacts.registry import ArtifactRegistry
from ..graph.evidence_graph import EvidenceGraph
from ..state.model import ProjectState


class LegacyError(ValueError):
    """Legacy 转换非法。"""


# V2 29-step → V3 状态维度映射（hand → 维度 / 推进阶段）
_HAND_TO_DIMENSION = {
    "modeler": ("problem", "models"),
    "programmer": ("experiments", "evidence"),
    "writer": ("narrative", "paper"),
    "reviewer": ("review",),
}


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise LegacyError(f"文件不存在: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------- results

def import_results(project_dir: str | Path, registry: ArtifactRegistry,
                   graph: EvidenceGraph | None = None) -> dict:
    """V2 all_results.json → R artifacts + 关系边。

    * 每个（非下划线）顶层键 → 一个 result artifact（data 存数值快照）
    * code/main.py 存在 → CODE001 + E001（experiment produces 各 R）
    * graph 提供时登记 produces / implemented_by 边
    幂等: 已导入的键（按 title 匹配）不重复导入。
    """
    base = Path(project_dir)
    results = _read_json(base / "figures" / "all_results.json")
    if not isinstance(results, dict):
        raise LegacyError("all_results.json 顶层必须是对象")

    imported = {"results": [], "skipped": [], "code": None, "experiment": None}

    # 代码与实验载体
    main_py = base / "code" / "main.py"
    if main_py.exists():
        if not any(a.type == "code" and "code/main.py" in a.payload
                   for a in registry.list_by_type("code")):
            code_art = registry.create(
                "code", title="legacy:code/main.py", payload=["code/main.py"],
                created_by="legacy.import", activate=True)
            exp_art = registry.create(
                "experiment", title="legacy:main-experiment",
                payload=["figures/all_results.json"], created_by="legacy.import",
                activate=True)
            if graph is not None:
                # 实验使用代码（uses: experiment→code；implemented_by 是 model→code）
                graph.add_relation(exp_art.artifact_id, "uses", code_art.artifact_id)
            imported["code"] = code_art.artifact_id
            imported["experiment"] = exp_art.artifact_id
        else:
            code_arts = [a for a in registry.list_by_type("code")
                         if "code/main.py" in a.payload]
            exp_arts = registry.list_by_type("experiment")
            imported["code"] = code_arts[0].artifact_id if code_arts else None
            imported["experiment"] = exp_arts[0].artifact_id if exp_arts else None

    existing_titles = {a.title for a in registry.list_by_type("result")}
    for key, value in sorted(results.items()):
        if key.startswith("_"):
            continue
        legacy_title = f"legacy:{key}"
        if legacy_title in existing_titles:
            imported["skipped"].append(key)
            continue
        art = registry.create(
            "result", title=legacy_title, created_by="legacy.import",
            data={"key": key, "value": value, "source": "figures/all_results.json"},
            activate=True)
        if graph is not None and imported.get("experiment"):
            graph.add_relation(imported["experiment"], "produces", art.artifact_id)
        imported["results"].append(art.artifact_id)
    return imported


def export_results(registry: ArtifactRegistry, out_path: str | Path) -> dict:
    """Registry R artifacts → all_results.json 兼容文件（V2 工具链可继续消费）。

    仅导出 data.key 存在的 result（即经 import 或按同契约登记的）。
    """
    exported = {}
    for art in registry.list_by_type("result"):
        key = (art.data or {}).get("key")
        if not key:
            continue
        exported[key] = (art.data or {}).get("value")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(exported, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    return exported


# --------------------------------------------------------------- state

def import_state(project_dir: str | Path, state: ProjectState) -> dict:
    """V2 work/state.json（29 步线性）→ V3 status.json 多维状态。

    映射规则（按 hand 的完成度聚合，粗粒度但保守——只前进不冒进）:
        modeler 全完成   → problem=complete, models=complete
        programmer 全完成→ experiments=complete, evidence=complete
        writer 全完成    → narrative/paper=complete
        reviewer 全完成  → review=complete
        部分完成         → in_progress
    legacy state.json 原样保留（只读）。
    """
    base = Path(project_dir)
    legacy = _read_json(base / "work" / "state.json")
    completed = legacy.get("completed", [])
    # completed 条目形态: [{"hand","agent","stage","timestamp"},...]
    by_hand: dict[str, set[str]] = {}
    for entry in completed:
        hand = entry.get("hand") if isinstance(entry, dict) else None
        if hand:
            by_hand.setdefault(hand, set()).add(entry.get("agent", ""))

    # V2 每个 hand 的 agent 全集（与 state.py PIPELINE 一致）
    V2_HANDS = {
        "modeler": {"problem-parser", "type-classifier", "literature-searcher",
                    "method-matcher", "model-builder", "dag-builder",
                    "assumption-validator", "spec-auditor"},
        "programmer": {"template-selector", "code-implementer", "test-runner",
                       "result-verifier", "guardrails-checker", "hash-auditor"},
        "writer": {"structure-planner", "section-writer", "figure-generator",
                   "reference-curator", "consistency-checker",
                   "guardrails-checker", "final-validator"},
        "reviewer": {"scorer-academic", "scorer-engineering", "scorer-judge",
                     "scorer-reader", "scorer-adversarial", "weakness-hunter",
                     "revision-planner", "revision-executor"},
    }

    def hand_status(hand: str) -> str:
        done = by_hand.get(hand, set())
        total = V2_HANDS[hand]
        if not done:
            return "pending"
        if done >= total:
            return "complete"
        return "in_progress"

    st = state.data["state"]
    mapping: dict[str, str] = {}
    for hand, dims in _HAND_TO_DIMENSION.items():
        hs = hand_status(hand)
        for dim in dims:
            mapping[dim] = hs
            if dim in st and isinstance(st[dim], dict):
                st[dim]["status"] = hs
                st[dim].setdefault("legacy_source", f"v2:{hand}")
    state.data["run"]["phase"] = "legacy-imported"
    state.data.setdefault("legacy", {})["v2_state"] = {
        "completed_steps": len(completed),
        "current": legacy.get("current"),
    }
    return mapping


# --------------------------------------------------------------- 组合入口

def convert_project(project_dir: str | Path, *, save: bool = True) -> dict:
    """一键转换: V2 项目 → V3 state/（registry + graph + status）。

    幂等安全: 重复调用不重复导入（import_results / registry 均幂等）。
    """
    base = Path(project_dir)
    state_dir = base / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    registry = ArtifactRegistry(state_dir / "registry.json")
    graph = EvidenceGraph(registry, path=state_dir / "evidence_graph.json")
    pstate = ProjectState(state_dir / "status.json")
    if not pstate.data.get("project"):
        pstate.data["project"] = base.name

    report: dict = {"graph_relations": len(graph.relations)}
    if (base / "figures" / "all_results.json").exists():
        report["results"] = import_results(base, registry, graph)
    if (base / "work" / "state.json").exists():
        report["state_mapping"] = import_state(base, pstate)
    report["state_summary"] = pstate.refresh_from(registry, graph)
    report["registry"] = registry.summary()

    if save:
        graph.sync_all_views()
        registry.save()
        graph.save()
        pstate.save()
    return report
