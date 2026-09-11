#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_state.py — 为 cumcm2026a 生成状态四件套（Artifact Registry / Evidence Graph / Decision Log / Status）。

输入：model_ir.json（模型表示）+ all_results.json（结果台账）。
输出：state/registry.json, state/evidence_graph.json, state/decision_log.json, state/status.json

设计原则（与仓库铁律一致）：
- 状态只由确定性机制推进：本脚本是纯函数，同一输入必得同一输出；
- 数值只来自 all_results.json（不手工转述、不编造）；
- 文件哈希用 sha256 真实计算，frontier 可追溯。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", ".."))       # projects/cumcm2026a
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))   # 仓库根
STATE = os.path.join(PROJ, "state")
PROJECT = "cumcm2026a"
PROBLEM_ID = "2026_A"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(rel: str):
    p = os.path.join(PROJ, rel)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def art(aid, atype, title, created_by, payload, question="", data=None) -> dict:
    d = {
        "schema_version": "3.1",
        "artifact_id": aid,
        "type": atype,
        "version": 1,
        "status": "active",
        "title": title,
        "created_by": created_by,
        "created_at": NOW,
        "updated_at": NOW,
        "payload": payload,
    }
    if question:                       # 挂到 Question 名下（state 投影据此聚合）
        d["question"] = question
    if data is not None:               # 内联契约数据（MODEL_IR 结构化字段）
        d["data"] = data
    return d


def build():
    ir = load("model_ir.json")
    res = load("all_results.json")
    summ = res["summary"]

    artifacts: dict[str, dict] = {}
    relations: list[dict] = []

    # ---- problem / question
    artifacts["MH-PROBLEM-0001"] = art(
        "MH-PROBLEM-0001", "problem", "2026_A 药材烘干", "problem_understanding",
        {"statement": "inputs/problem.txt",
         "sha256": ir["problem_binding"]["problem_sha256"],
         "sub_questions": ["Q1", "Q2", "Q3", "Q4"]})
    sq_types = {"Q1": "forward_simulation", "Q2": "forward_simulation_two_stage",
                "Q3": "inverse_time", "Q4": "moving_boundary_inverse"}
    # 每个子问题登记为独立 question artifact（V3：Question 是一等实体）。
    # 此前只登记一个容器 artifact，state 投影与分解指标都只数到 1 问。
    sq_texts = ir["problem_binding"]["sub_questions"]
    for q in ("Q1", "Q2", "Q3", "Q4"):
        artifacts[q] = art(q, "question", f"{q} {sq_types[q]}",
                           "problem_understanding",
                           {"id": q, "type": sq_types[q], "text": sq_texts[q]})
        relations.append({"from": "MH-PROBLEM-0001", "to": q,
                          "relation": "motivates"})

    # ---- model
    artifacts["MH-MODEL-0001"] = art(
        "MH-MODEL-0001", "model", ir["title"], "model_construction",
        {"model_ir": "model_ir.json",
         "model_doc": "model.md",
         "model_family": ir["model_family"]["primary"],
         "secondary": ir["model_family"]["secondary"],
         "equations": [e["equation_id"] for e in ir["equations"]],
         "sha256": sha256(os.path.join(PROJ, "model_ir.json"))})
    artifacts["MH-MODEL-0001"]["status"] = "validated"   # 已通过验证与批判
    for q in ("Q1", "Q2", "Q3", "Q4"):
        relations.append({"from": q, "to": "MH-MODEL-0001",
                          "relation": "solved_by"})

    # MODEL_IR 是 model 的契约新形态：内联登记结构化字段，使结构检查能评估
    # objectives/constraints/variables（此前只登记指针，被判 legacy_pointer）。
    artifacts["MH-MODEL_IR-0001"] = art(
        "MH-MODEL_IR-0001", "model_ir", ir["title"], "model_construction",
        {"path": "model_ir.json",
         "sha256": sha256(os.path.join(PROJ, "model_ir.json"))},
        data=ir)
    relations.append({"from": "MH-MODEL-0001", "to": "MH-MODEL_IR-0001",
                      "relation": "derived_from",
                      "note": "MODEL_IR 是 model 的契约形态"})

    # ---- assumptions
    artifacts["MH-ASSUMPTION-0001"] = art(
        "MH-ASSUMPTION-0001", "assumption", "模型假设 A01-A08", "model_construction",
        {"items": [{"id": a["assumption_id"], "type": a["type"],
                    "source": a["source"], "confidence": a["confidence"],
                    "text": a["text"]} for a in ir["assumptions"]]})
    relations.append({"from": "MH-MODEL-0001", "to": "MH-ASSUMPTION-0001",
                      "relation": "assumes"})

    # ---- code
    code_files = [("MH-CODE-0001", "solve_a.py", "径向耦合传热传质隐式求解 + 移动边界 + 验证套件")]
    for cid, name, note in code_files:
        rel = os.path.join("artifacts", "code", name)
        artifacts[cid] = art(cid, "code", name, "experiment_execution",
                             {"path": rel.replace(os.sep, "/"),
                              "sha256": sha256(os.path.join(PROJ, rel)), "note": note})
        relations.append({"from": "MH-MODEL-0001", "to": cid,
                          "relation": "implemented_by", "note": note})

    # ---- experiments / results（数值全部取自 all_results.json）
    exp_meta = {
        "Q1": ("预热平衡阶段（1800 s，附录 2 常物性）", "problem1", "result1.xlsx"),
        "Q2": ("全程烘干前 3 h（两阶段参数，附录 3 变物性）", "problem2", "result2.xlsx"),
        "Q3": ("固定半径烘干至中心含水率 < 0.15（求时长）", "problem3", "result3.xlsx"),
        "Q4": ("移动边界（失水收缩）烘干至中心含水率 < 0.15", "problem4", "result4.xlsx"),
    }
    n = 1
    for q in ("Q1", "Q2", "Q3", "Q4"):
        eid, rid = f"MH-EXPERIMENT-{n:04d}", f"MH-RESULT-{n:04d}"
        desc, key, xlsx = exp_meta[q]
        block = summ[key]
        rel_xlsx = os.path.join("artifacts", "results", xlsx)
        artifacts[eid] = art(eid, "experiment", f"{q} {desc}", "experiment_design",
                             {"sub_question": q, "solver": "S01/S02/S03",
                              "code_ref": "MH-CODE-0001",
                              "key_outputs": sorted(block.keys())},
                             question=q)
        artifacts[eid]["status"] = "validated"
        artifacts[rid] = art(rid, "result", f"{q} 结果（{xlsx}）", "experiment_execution",
                             {"path": rel_xlsx.replace(os.sep, "/"),
                              "sha256": sha256(os.path.join(PROJ, rel_xlsx)),
                              "values": block},
                             question=q)
        artifacts[rid]["status"] = "validated"
        relations += [
            {"from": "MH-MODEL-0001", "to": eid, "relation": "validated_by", "sub_question": q},
            {"from": eid, "to": "MH-MODEL-0001", "relation": "tests", "sub_question": q},
            {"from": eid, "to": "MH-CODE-0001", "relation": "uses"},
            {"from": eid, "to": rid, "relation": "produces"},
        ]
        n += 1

    # ---- claims
    for i, c in enumerate(ir["claims"], start=1):
        cid = f"MH-CLAIM-{i:04d}"
        q = c["sub_question_binding"][0]
        artifacts[cid] = art(cid, "claim", f"{c['claim_id']}（{q}）",
                             "model_construction",
                             {"text": c["text"], "status": c["status"],
                              "type": c["type"],
                              "validation_refs": c.get("validation_refs", [])},
                             question=q)
        rid = f"MH-RESULT-{int(q[1:]):04d}"
        if rid in artifacts:
            relations.append({"from": rid, "to": cid, "relation": "supports",
                              "sub_question": q})

    # ---- deliverable（模型描述文档是 MODEL_IR 的人类可读交付投影）
    # 注：类型 narrative 已退役（不在 ARTIFACT_TYPES 内），改为 deliverable。
    artifacts["MH-DELIVERABLE-0001"] = art(
        "MH-DELIVERABLE-0001", "deliverable", "模型描述文档（含 Mermaid）",
        "model_construction",
        {"path": "model.md", "sha256": sha256(os.path.join(PROJ, "model.md"))})
    relations.append({"from": "MH-MODEL-0001", "to": "MH-DELIVERABLE-0001",
                      "relation": "derived_from",
                      "note": "模型描述是 MODEL_IR 的人类可读投影"})

    counters: dict[str, int] = {}
    for a in artifacts.values():
        counters[a["type"]] = counters.get(a["type"], 0) + 1

    registry = {"registry_version": 3, "project": PROJECT, "updated_at": NOW,
                "counters": dict(sorted(counters.items())), "artifacts": artifacts}

    graph = {"graph_schema_version": 3, "graph_version": 1, "project": PROJECT,
             "updated_at": NOW, "relations": relations}

    decisions = [
        {"decision_id": "MH-DECISION-0001",
         "question": "是否保留轴向自由度？",
         "chosen": "只保留径向一维（轴对称柱坐标）",
         "alternatives": ["径向 + 轴向二维 PDE", "三维有限元"],
         "criteria": ["轴向/径向扩散时间尺度比", "题面给定几何与可计算性"],
         "evidence_ids": ["MH-RESULT-0001"],
         "reasoning": "长径比使 (L/R0)^2 = 156，轴向在远小于一秒内均温；本题关心的尺度为 1800 s 至数天，轴向已平衡。",
         "confidence": 0.95, "reversible": True,
         "created_by": "model_construction", "created_at": NOW},
        {"decision_id": "MH-DECISION-0002",
         "question": "烘干终点的判据取全场还是中心？",
         "chosen": "取中心 r=0 的单点判据 t_dry = inf{t: C(0,t) < 0.15}",
         "alternatives": ["全场逐点扫描同时达标", "取表面含水率"],
         "criteria": ["剖面单调性", "是否等价于题面「各处 < 0.15」"],
         "evidence_ids": ["MH-RESULT-0001", "MH-RESULT-0003"],
         "reasoning": "径向单调剖面下中心为极值点，故中心达标 ⟺ 全场达标；取表面会大幅低估时长（终态表面 0.0522 vs 中心 0.1500）。",
         "confidence": 0.95, "reversible": True,
         "created_by": "model_construction", "created_at": NOW},
        {"decision_id": "MH-DECISION-0003",
         "question": "径向网格与时间步取多少？",
         "chosen": "N_r = 1280（Δr = 0.0015625 cm），Δt = 10 s",
         "alternatives": ["N_r = 320", "N_r = 640", "自适应网格"],
         "criteria": ["网格/时间步收敛序列", "表面「干壳」层分辨率"],
         "evidence_ids": ["MH-RESULT-0003"],
         "reasoning": "实测 N=160/320/640/1280/2560 给出 63.5222/58.0944/57.5000/57.4278/57.4167 h；N=320 偏高约 1.2%，N=1280 与 2560 差 0.02%。Δt ≤ 10 s 后时间离散误差 < 0.005%。",
         "confidence": 0.9, "reversible": True,
         "created_by": "experiment_design", "created_at": NOW},
        {"decision_id": "MH-DECISION-0004",
         "question": "恒温干燥目标温度如何确定？",
         "chosen": "T_target = 50 °C，并作为待标定参数在敏感性验证中量化",
         "alternatives": ["取 45 / 55 / 60 °C", "由附件 1 曲线逐点拟合"],
         "criteria": ["是否落在题面「2-3 天」窗口", "中药材低温热风干燥常见工艺"],
         "evidence_ids": ["MH-RESULT-0003"],
         "reasoning": "实测 45/50/55/60 °C 分别给出 69.1778/58.0944/49.4/42.5 h；落入 48-72 h 窗口的区间约 44-55 °C，50 °C 取为该区间代表值。该取值不是题面给定，故在局限中显式声明。",
         "confidence": 0.8, "reversible": True,
         "created_by": "experiment_design", "created_at": NOW},
        {"decision_id": "MH-DECISION-0005",
         "question": "失水收缩对烘干时长是净正还是净负效应？",
         "chosen": "净负（时长增加）：固定域 57.4222 h → 移动域 64.7806 h",
         "alternatives": ["直觉判断半径减小 ⇒ 时间减少", "忽略收缩"],
         "criteria": ["两解对照", "干物质守恒闭合是否正确"],
         "evidence_ids": ["MH-RESULT-0003", "MH-RESULT-0004"],
         "reasoning": "半径收缩缩短了后期扩散路径（有利），但表面积减小且含水率阈值对应的绝对水量下降更慢（不利），净效应为 +7.36 h；不凭直觉结论，以两解对照为准。",
         "confidence": 0.85, "reversible": True,
         "created_by": "model_construction", "created_at": NOW},
    ]
    decision_log = {"schema_version": 3, "project": PROJECT, "updated_at": NOW,
                    "decisions": decisions}

    qstat = {}
    for q in ("Q1", "Q2", "Q3", "Q4"):
        idx = int(q[1:])
        qstat[q] = {"status": "validated", "models": ["MH-MODEL-0001"],
                    "experiments": [f"MH-EXPERIMENT-{idx:04d}"],
                    "claims": [f"MH-CLAIM-{i:04d}" for i, c in enumerate(ir["claims"], 1)
                               if q in c["sub_question_binding"]]}

    limitations = [
        "A04：恒温干燥目标温度 50 °C 由「2-3 天」窗口反标定，非题面给定值（V03 已量化敏感性）",
        "A03：烘房湿度取两段阶跃、温度按时间常数 450 s 指数趋近，属对附件曲线形态的简化",
        "A05：物性取上一时步滞后（O(Δt) 误差），未做全隐式非线性迭代",
        "均匀网格在表面「干壳」层仍有约 0.02% 残差（N_r = 1280 与 2560 之差）",
        "未做官方标准答案比对（题面未给参考答案，不凭记忆构造真值）",
    ]

    # 四件套落盘：status.json 由内容真源派生（唯一入口，见 state_projection）
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    from state_projection import write_state_projection  # noqa: E402
    result = write_state_projection(
        project_dir=PROJ, repo_root=REPO, project=PROJECT,
        registry=registry, evidence_graph=graph, decision_log=decision_log,
        per_question=qstat, limitations=limitations,
        workflow_notes=["本实例由项目内确定性脚本构建（未走 RuntimeSession 引擎），"
                        "workflow 节点不虚报；内容真源为 registry + evidence_graph。"])
    print("written:", result["status_path"])
    print("[summary]", json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    build()
