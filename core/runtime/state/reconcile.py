#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconcile —— 状态对账器（System Hardening P2）。

回答「系统当前到底是什么状态」只能有一个答案：

  内容真源（研究内容）:  state/registry.json + state/evidence_graph.json
                        （+ decision_log.json，决策记录）
  流程状态投影（派生）:  state/status.json —— 只能由 registry/graph 重新派生，
                        禁止反向手写（ProjectState.refresh_from 是唯一派生入口）
  会话进度（断点续跑）:  state/engine_progress.json

对账口径（只读，永不静默）：
  * 用当前磁盘上的 registry + graph 重新派生一份「理想投影」，与落盘的
    status.json 逐项比较，任何不同都列为 problem，并给出字段级 diff。
  * workflow / run / review 等会话自有字段不参与比较
    （它们不由内容派生，属引擎职责），在 STATE_TRUTH.md 有决策表登记。

模式：v3（state/status.json）/ legacy（仅 work/state.json）/ empty。
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO / "core") not in sys.path:
    sys.path.insert(0, str(REPO / "core"))

from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402
from runtime.state.model import ProjectState  # noqa: E402

# ---------------------------------------------------------------- 模式探测

def detect_mode(project_dir) -> str:
    pdir = Path(project_dir)
    if (pdir / "state" / "status.json").exists():
        return "v3"
    if (pdir / "work" / "state.json").exists():
        return "legacy"
    return "empty"


# ---------------------------------------------------------------- 对账

def reconcile(project_dir) -> dict:
    """只读对账。返回 {ok, mode, problems, diff, advice}。"""
    pdir = Path(project_dir)
    mode = detect_mode(pdir)
    if mode == "empty":
        return {"ok": True, "mode": mode, "problems": [],
                "note": "无任何状态文件（未初始化或空项目）"}
    if mode == "legacy":
        return {"ok": True, "mode": mode, "problems": [],
                "note": "legacy 模式：work/state.json 是唯一状态文件，"
                        "无多维投影可对账（可用 state.py sync 检查单文件一致性）"}

    problems: list[str] = []
    sdir = pdir / "state"
    status_path = sdir / "status.json"
    reg_path = sdir / "registry.json"
    graph_path = sdir / "evidence_graph.json"

    if not reg_path.exists():
        problems.append("registry.json 不存在：status.json 投影失去内容真源")
        return {"ok": False, "mode": mode, "problems": problems}
    if not graph_path.exists():
        problems.append("evidence_graph.json 不存在：status.json 投影失去关系真源")

    disk = ProjectState(status_path)
    reg = ArtifactRegistry(reg_path)
    graph = EvidenceGraph(reg, graph_path)

    # 理想投影：从当前内容重新派生（在临时目录进行，绝不触碰落盘投影）
    with tempfile.TemporaryDirectory() as td:
        ideal = ProjectState(Path(td) / "status.json")
        ideal.data["project"] = disk.data.get("project", "")
        ideal.refresh_from(reg, graph)
    ideal_st = ideal.data["state"]
    disk_st = disk.data["state"]

    diff: dict = {}
    dq = dict(disk_st["questions"])
    iq = dict(ideal_st["questions"])

    # 1) questions 集合（内容真源：registry 的 question artifacts）
    if set(dq) != set(iq):
        problems.append(
            f"questions 集合不一致: 投影多出 {sorted(set(dq) - set(iq))}, "
            f"缺失 {sorted(set(iq) - set(dq))}")
        diff["questions_set"] = {"disk": sorted(dq), "ideal": sorted(iq)}

    # 2) models 候选/选中（内容真源：registry 的 model artifacts）
    for k in ("candidates", "selected"):
        if disk_st["models"].get(k) != ideal_st["models"].get(k):
            problems.append(f"models.{k} 与内容真源不一致")
            diff[f"models.{k}"] = {
                "disk": disk_st["models"].get(k), "ideal": ideal_st["models"].get(k)}

    # 3) 每个 Question 的挂载（experiments/claims 等，内容真源：registry）
    for qid, q in iq.items():
        d = dq.get(qid, {})
        for k in ("models", "experiments", "claims"):
            if set(d.get(k, [])) != set(q.get(k, [])):
                problems.append(
                    f"{qid}.{k} 与内容真源不一致: 投影 {sorted(d.get(k, []))} "
                    f"vs 理想 {sorted(q.get(k, []))}")
                diff[f"{qid}.{k}"] = {
                    "disk": sorted(d.get(k, [])), "ideal": sorted(q.get(k, []))}

    # 4) evidence 聚合计数（内容真源：graph 的 coverage）
    for k in ("graph_version", "claims_supported", "claims_total"):
        if disk_st["evidence"].get(k) != ideal_st["evidence"].get(k):
            problems.append(
                f"evidence.{k} 不一致: 投影 {disk_st['evidence'].get(k)} "
                f"vs 理想 {ideal_st['evidence'].get(k)}")
            diff[f"evidence.{k}"] = {
                "disk": disk_st["evidence"].get(k),
                "ideal": ideal_st["evidence"].get(k)}

    # 5) 会话进度文件（引擎断点续跑真源）
    if not (sdir / "engine_progress.json").exists() \
            and disk.data["workflow"]["completed_nodes"]:
        problems.append("engine_progress.json 不存在但 workflow 有已完成节点："
                        "崩溃后无法精确 resume")

    # 6) D1 依赖双写完整性（复用 P12 既有口径）
    try:
        from runtime.state.dependencies import dependency_integrity_problems
        d1 = dependency_integrity_problems(reg, disk)
        if d1:
            problems.append(f"依赖双写不一致（D1）: {d1}")
    except Exception as e:  # noqa: BLE001 —— 防御：检查器自身异常要显式暴露
        problems.append(f"依赖完整性检查异常: {e}")

    advice = ""
    if problems:
        advice = ("恢复口径：投影可由内容重建——重新派生投影并落盘即可"
                  "（RuntimeSession.resume()/checkpoint() 会自动执行等价操作）；"
                  "禁止手工编辑 status.json 掩盖差异。")
    return {"ok": not problems, "mode": mode, "problems": problems,
            "diff": diff, "advice": advice}