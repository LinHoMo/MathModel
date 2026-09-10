# -*- coding: utf-8 -*-
"""P1-M3 候选竞技场共享 driver：多候选注入 → 独立执行/验证 → evidence-based 选型。

与 VS-001 driver 同构：e2e 测试（tests/integration/test_p1_m3_competition.py）
与演示脚本（run_m3_demo.py）共用本模块，保证候选竞技场逻辑单一真源。

设计要点（LLM-free）：
- 候选 MODEL_IR/Code 由 m3_fixtures 手写注入（shared["external_candidates"]）；
- 每个候选独立 artifact 链 MIR-i→CODE-i→EXEC-i→R-i→VR-i（互不覆盖）；
- do_model_selection 只登记容器 model（不假装选型，消除 recs[0] 硬编码）；
- do_model_selection_decision 基于 VR 机械指标选型并写 decision -selects-> model 边。
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from m3_fixtures import CANDIDATES, VALIDATION_SPEC  # noqa: E402
from vs001_fixtures import OUTPUT_MAPPING  # noqa: E402

from modeling_harness.runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402

# DAG 闭环节点序列（modeling 尾链含 P1-M3 新增的 model_selection_decision）
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
    "model_selection_decision",
]


def make_session(project_dir, questions=("Q001",)):
    """构建 RuntimeSession：真实 LocalPythonAdapter + 单 worker（确定性）。"""
    return RuntimeSession(
        Path(project_dir), list(questions), max_workers=1,
        execution_adapter=LocalPythonAdapter())


def inject_candidates(session, candidates=None, workdir=None):
    """注入外部候选列表到 shared（core 只登记/校验/执行/验证/选型）。"""
    shared = session.executor_impl.shared
    shared["external_candidates"] = {"Q001": candidates or CANDIDATES}
    shared["validation_specs"] = {"Q001": VALIDATION_SPEC}
    # P0-1 契约：候选 MODEL_IR 声明的向量变量（x_i/y_i→positions）在代码
    # 输出中为嵌套结构，外部 Constructor 显式声明翻译表（同 vs001_driver）
    shared["output_mappings"] = {"Q001": OUTPUT_MAPPING}
    if workdir is not None:
        shared["_workdir"] = str(workdir)
    return shared


def step_all(session, nodes=LOOP_NODES):
    """按序步进 DAG 节点，返回 {node_id: result}（由调用方按阶段断言）。"""
    results = {}
    for nid in nodes:
        results[nid] = session.engine.step(nid)
    return results


def run_competition(session, workdir, candidates=None):
    """候选竞技场闭环：注入候选 → 步进全链（含选型节点）。

    断言：非选型节点全 PASS；model_validation 因任一候选 FAIL 但仍存活
    （n_pass>=1）而 PASS；model_selection_decision PASS。
    返回 (session, results)。
    """
    inject_candidates(session, candidates=candidates, workdir=workdir)
    results = step_all(session)
    for nid, r in results.items():
        if nid in ("model_selection", "model_construction", "model_critique",
                   "assumption_check", "code_generation", "model_execution",
                   "model_validation", "model_selection_decision"):
            assert r.status == "pass", f"节点 {nid} 未通过: {r.status}"
        else:
            assert r.status == "pass", f"节点 {nid} 未通过: {r.status}"
    session.checkpoint()
    return session, results


def artifact_ids(session, atype: str, question: str = "Q001") -> list[str]:
    return [a.artifact_id for a in session.registry.list_by_type(atype)
            if a.question == question]


def relation_pairs(session) -> set[tuple[str, str, str]]:
    return {(r["from"], r["relation"], r["to"])
            for r in session.graph.relations}


def decisions_of(session, question: str = "Q001") -> list[dict]:
    """该问题的候选竞技场选型 decision artifacts（data 视图）。"""
    out = []
    for a in session.registry.list_by_type("decision"):
        if a.question == question and "候选竞技场选型" in (a.title or ""):
            out.append({"artifact_id": a.artifact_id,
                        "data": dict(a.data or {}),
                        "payload": a.payload})
    return out


def replay_report(project_dir, exec_id: str) -> dict:
    """用 src/modeling_harness/runtime/execution/replay.py 重放一次执行并报告偏差。"""
    from modeling_harness.runtime.execution.replay import replay_execution
    return replay_execution(project_dir, exec_id)
