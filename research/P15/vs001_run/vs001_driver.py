# -*- coding: utf-8 -*-
"""P1-VS-001 演示/测试共享 driver：M1 → RUN1 → VALIDATION FAIL → REVISION →
M2 → RUN2 → VALIDATION PASS 闭环（2024_A 垂直切片）。

e2e 测试（tests/integration/test_p1_vs001_e2e.py）与演示脚本
（run_vs001_demo.py）共用本模块，保证闭环逻辑单一真源。

设计要点（外部 Model Constructor / LLM-free）：
- M1/M2 MODEL_IR 与 C1/C2 代码由 vs001_fixtures 手写注入（shared 字典）；
- core runtime 只登记/校验/执行/保真/验证/谱系/replay；
- 执行状态只来自真实 subprocess 退出码（LocalPythonAdapter）；
- M2 经 revision_of 边关联 M1（M1 不被覆盖）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from vs001_fixtures import (  # noqa: E402
    C1_CODE, C2_CODE, M1_DICT, M2_DICT, OUTPUT_MAPPING, VALIDATION_SPEC,
)

from modeling_harness.runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402

# DAG 闭环节点序列（与 catalog/v3.yaml + stages 一致）
LOOP_NODES = [
    "problem_analysis",
    "literature_search",
    "model_selection",
    "model_construction",
    "model_critique",
    "assumption_check",
    "code_generation",
    "model_execution",
    "model_validation",
]

# M2 修订环：只重跑 model_construction 下游（上游已 completed）
REVISION_NODES = [
    "model_construction",
    "model_critique",
    "assumption_check",
    "code_generation",
    "model_execution",
    "model_validation",
]


def make_session(project_dir, questions=("Q001",)):
    """构建 RuntimeSession：真实 LocalPythonAdapter + 单 worker（确定性）。"""
    return RuntimeSession(
        Path(project_dir), list(questions), max_workers=1,
        execution_adapter=LocalPythonAdapter())


def inject(session, mir_dict, code, workdir):
    """注入外部 Model Constructor 产物到 shared（每阶段一次性）。"""
    shared = session.executor_impl.shared
    shared["external_model_irs"] = {"Q001": mir_dict}
    shared["external_code"] = {"Q001": code}
    shared["validation_specs"] = {"Q001": VALIDATION_SPEC}
    shared["output_mappings"] = {"Q001": OUTPUT_MAPPING}
    shared["_workdir"] = str(workdir)


def step_all(session, nodes=LOOP_NODES):
    """按序步进 DAG 节点，返回 {node_id: result}（由调用方按阶段断言）。"""
    results = {}
    for nid in nodes:
        results[nid] = session.engine.step(nid)
    return results


def run_m1(session, workdir):
    """M1 闭环：注入 M1+C1 → 步进全链 → 返回 (session, results)。

    断言：除 model_validation 必须 FAIL（数值判 FAIL，验收 5）外，其余全 PASS。
    """
    inject(session, M1_DICT, C1_CODE, workdir)
    results = step_all(session)
    for nid, r in results.items():
        if nid == "model_validation":
            assert r.status == "fail", (
                f"M1 的 model_validation 必须 FAIL（真实数值判 FAIL），实际 {r.status}")
        else:
            assert r.status == "pass", f"节点 {nid} 未通过: {r.status}"
    session.checkpoint()
    return session, results


def run_m2(session, mir1_id: str, workdir):
    """M2 闭环（修订）：注入 M2（revision_of=MIR1）+C2 → 重置 model_construction
    下游 → 步进修订环 → 修订收口（diagnosis/supersede/comparison）→
    返回 (session, results)。M1 数据不被覆盖，状态 → superseded。

    断言：修订环全部 PASS（含 model_validation）。
    """
    m2 = dict(M2_DICT)
    m2["revision_of"] = mir1_id
    inject(session, m2, C2_CODE, workdir)
    session.engine.reset_to("model_construction")
    results = step_all(session, nodes=REVISION_NODES)
    for nid, r in results.items():
        assert r.status == "pass", f"M2 修订环 {nid} 未通过: {r.status}"
    session.checkpoint()
    finalize_revision(session, mir1_id, m2["model_id"])
    session.checkpoint()
    return session, results


def finalize_revision(session, mir1_id: str, mir2_model_id: str):
    """修订收口（audit Batch 6，LLM-free 确定性）：

    FIX-6.1  failure diagnosis：从 M1 的 VR 机械归因 → diagnosis artifact
             + (M1, diagnosed_by, DIAG) 边
    FIX-6.3  supersede 方向统一：registry.supersede(M1, replacement=M2)
             （M1 状态 → superseded，数据不覆盖）+ (M2, supersedes, M1) 边
    FIX-6.4  M1/M2 比较：compare_models（VR 机械证据）→ revision_acceptance
             decision（accept/reject + reasoning + selects 边）
    不编造新数值；diagnosis/comparison 全部来自机械证据。
    """
    from modeling_harness.runtime.modeling.diagnosis import diagnose_failure
    from modeling_harness.runtime.modeling.comparison import compare_models, _resolve_vr_for_model

    reg, graph = session.registry, session.graph
    mir2 = None
    for m in reg.list_by_type("model_ir"):
        if (m.data or {}).get("model_id") == mir2_model_id:
            mir2 = m.artifact_id
    if mir2 is None:
        return
    # FIX-6.1：M1 失败诊断（VR 机械证据）——P0-2 起诊断已在 DAG 内
    # （model_validation FAIL 时）生成；此处仅当尚无 diagnosed_by 边时
    # 才补建（防重复 DIAG）。诊断内容同一（diagnose_failure 确定性）。
    vr1 = _resolve_vr_for_model(reg, mir1_id)
    if vr1 is not None and not vr1.get("valid"):
        existing = [g for g in graph.relations
                    if g["from"] == mir1_id
                    and g["relation"] == "diagnosed_by"]
        if not existing:
            vrs = [a for a in reg.list_by_type("verification_result")
                   if (a.data or {}).get("status") == "failed"
                   and a.question == "Q001"]
            if vrs:
                diag = diagnose_failure(reg, mir1_id, vrs[-1].artifact_id)
                d = reg.create(
                    "diagnosis", title=f"失败诊断 {mir1_id}",
                    question="Q001", depends_on=[mir1_id],
                    data=diag.to_dict(), activate=True,
                    created_by="runtime.modeling.diagnosis")
                graph.add_relation(mir1_id, "diagnosed_by", d.artifact_id)
    # FIX-6.3：supersede（新取代旧；M1 数据保留，状态 → superseded）
    reg.supersede(mir1_id, reason="M2 修订通过验证，取代 M1",
                  replacement=mir2, by="runtime.revision")
    graph.add_relation(mir2, "supersedes", mir1_id)
    # FIX-6.4：M1/M2 比较 → accept/reject 决策
    cmp = compare_models(reg, mir1_id, mir2)
    ddata = {
        "kind": "revision_acceptance",
        "chosen": cmp["better_model"] or "NONE",
        "alternatives": [mir1_id, mir2],
        "criteria": ["mathematical_valid", "checks_passed",
                     "constraint_violation_max", "robustness"],
        "evidence_ids": cmp.get("evidence_refs") or [],
        "confidence": 1.0 if cmp["recommendation"] != "pending" else 0.0,
        "reasoning": cmp["reasoning"],
        "recommendation": cmp["recommendation"],
        "deltas": cmp["deltas"],
    }
    dec = reg.create(
        "decision", title=f"修订接受决策 {mir1_id} → {mir2_model_id}",
        question="Q001", payload=[cmp["better_model"]] if cmp[
            "better_model"] else [],
        data=ddata, depends_on=[mir1_id, mir2],
        activate=True, created_by="runtime.revision")
    if cmp["better_model"] and cmp["better_model"] != "NONE":
        graph.add_relation(dec.artifact_id, "selects", cmp["better_model"])
    return cmp


def artifact_ids(session, atype: str, question: str = "Q001") -> list[str]:
    return [a.artifact_id for a in session.registry.list_by_type(atype)
            if a.question == question]


def relation_pairs(session) -> set[tuple[str, str, str]]:
    return {(r["from"], r["relation"], r["to"])
            for r in session.graph.relations}


def replay_report(project_dir, exec_id: str) -> dict:
    """用 src/modeling_harness/runtime/execution/replay.py 重放一次执行并报告偏差。"""
    from modeling_harness.runtime.execution.replay import replay_execution
    return replay_execution(project_dir, exec_id)
