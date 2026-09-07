#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic Replay / Recovery（System Hardening P3）。

回答「为什么这个 Artifact 是这样产生的」：
  verify —— 用当前磁盘状态重算全部确定性口径（输入哈希 / 工作流版本 / 技能版本
            / 工具版本 / 产物哈希 / 状态对账），与 RunRecord 逐字段比对。
            同输入同配置 → 全部一致（可重放）；有漂移 → 逐字段列出（可归因）。
  diff   —— 两次运行的字段级差异 + 归因提示（哪一层变了：题目/指令/工作流/
            执行器/产物）。
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO / "core") not in sys.path:
    sys.path.insert(0, str(REPO / "core"))

from runtime.state.reconcile import detect_mode, reconcile  # noqa: E402
from runtime.state.runs import (  # noqa: E402
    compute_input_hash, list_run_records, load_run_record,
    skill_version, tool_version, workflow_version,
)

# 归因表：字段 → 人类可读解释（供 replay diff 输出）
ATTRIBUTION = {
    "input_hash": "题目输入（inputs/）变化",
    "workflow_version": "工作流定义（roles/workflows YAML）变化",
    "prompt_hash": "角色/工作流指令文件变化",
    "skill_version": "技能指令包（core/skills）变化",
    "tool_version": "工具链版本（catalog/git）变化",
    "artifact_hash": "Registry 产物内容不同（结果/模型变化）",
    "evidence_hash": "证据图内容不同",
    "decision_log_hash": "决策记录不同",
    "model_provider": "外部执行器提供方不同",
    "model_version": "外部执行器模型版本不同",
}

HASH_FIELDS = ("input_hash", "workflow_version", "prompt_hash", "skill_version",
               "tool_version", "artifact_hash", "evidence_hash", "decision_log_hash")


def verify(project_dir, run_id: str | None = None) -> dict:
    """确定性重放校验：现磁盘重算 vs RunRecord。"""
    mode = detect_mode(project_dir)
    if mode != "v3":
        return {"ok": False, "mode": mode,
                "problems": ["非 v3 项目，无 RunRecord 可验证"]}
    rec = load_run_record(project_dir, run_id)
    pdir = Path(project_dir)
    sdir = pdir / "state"

    current = {
        "input_hash": compute_input_hash(pdir),
        "workflow_version": workflow_version(),
        "skill_version": skill_version(),
        "tool_version": tool_version(),
    }
    # 产物哈希（现磁盘）
    for name, fname in (("artifact_hash", "registry.json"),
                        ("evidence_hash", "evidence_graph.json"),
                        ("decision_log_hash", "decision_log.json")):
        p = sdir / fname
        from runtime.state.runs import _hash_path
        current[name] = _hash_path(p)

    matches, drift = {}, []
    for field, cur in current.items():
        recorded = rec.get(field)
        ok_field = (recorded == cur)
        matches[field] = ok_field
        if not ok_field:
            drift.append({
                "field": field,
                "recorded": (recorded or "")[:16],
                "current": (cur or "")[:16],
                "why": ATTRIBUTION.get(field, field),
            })

    # 状态对账（投影 vs 内容）一并收起；内容文件不可解析时如实报告
    state_ok, rep = False, {"ok": False, "problems": []}
    try:
        rep = reconcile(pdir)
        state_ok = rep.get("ok", False)
    except Exception as e:  # noqa: BLE001 —— 对账器自身异常要显式暴露
        rep["problems"].append(f"对账异常（内容文件不可解析?）: {e}")

    problems = []
    if drift:
        problems.append(f"{len(drift)} 个确定性字段与记录不符")
    if not state_ok:
        problems.append(f"状态对账不一致: {rep.get('problems')}")
    return {
        "ok": (not drift) and state_ok,
        "run_id": rec["run_id"],
        "status": rec.get("status"),
        "field_matches": matches,
        "drift": drift,
        "reconcile": {"ok": state_ok, "problems": rep.get("problems", [])},
        "problems": problems,
    }


def diff(project_dir, run_a: str, run_b: str) -> dict:
    """两次运行的字段级差异 + 归因。"""
    a = load_run_record(project_dir, run_a)
    b = load_run_record(project_dir, run_b)
    fields = ["questions", "status", "workflow_version", "skill_version",
              "tool_version", "input_hash", "prompt_hash", "artifact_hash",
              "evidence_hash", "model_provider", "model_version",
              "parent_run_id", "decision"] + \
             [f"engine.{k}" for k in ("completed_nodes", "retries", "failures")]
    diffs = []
    for f in fields:
        if f.startswith("engine."):
            sub = f.split(".", 1)[1]
            va, vb = a["engine"].get(sub), b["engine"].get(sub)
        else:
            va, vb = a.get(f), b.get(f)
        if va != vb:
            diffs.append({"field": f, "run_a": va, "run_b": vb,
                          "why": ATTRIBUTION.get(f, "")})
    return {"run_a": run_a, "run_b": run_b, "changed_fields": diffs,
            "summary": [d["field"] for d in diffs]}


def list_runs(project_dir) -> list[dict]:
    out = []
    for r in list_run_records(project_dir):
        out.append({
            "run_id": r.get("run_id"),
            "status": r.get("status"),
            "started_at": r.get("started_at"),
            "parent_run_id": r.get("parent_run_id"),
        })
    return out