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
if str(REPO / "core") not in sys.path:
    sys.path.insert(0, str(REPO / "core"))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from vs001_fixtures import C1_CODE, C2_CODE, M1_DICT, M2_DICT, VALIDATION_SPEC  # noqa: E402

from runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402

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
    下游 → 步进修订环 → 返回 (session, results)。M1 不被覆盖。

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
    return session, results


def artifact_ids(session, atype: str, question: str = "Q001") -> list[str]:
    return [a.artifact_id for a in session.registry.list_by_type(atype)
            if a.question == question]


def relation_pairs(session) -> set[tuple[str, str, str]]:
    return {(r["from"], r["relation"], r["to"])
            for r in session.graph.relations}


def replay_report(project_dir, exec_id: str) -> dict:
    """用 core/runtime/execution/replay.py 重放一次执行并报告偏差。"""
    from runtime.execution.replay import replay_execution
    return replay_execution(project_dir, exec_id)
