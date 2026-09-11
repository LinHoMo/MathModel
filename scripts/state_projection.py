"""state_projection.py — 把内容真源派生为一致的 status.json 投影（项目脚本共用）。

来源（projects 反馈闭环）：仓库内三个交付实例（cumcm2024a / cumcm2026a /
cumcm2026b）由手工脚本直接拼装 status.json，产出的是**扁平结构**
（`problem` / `questions` 直接挂在顶层），并使用了非法维度值
（`problem.status = "parsed"` 不在 `DIMENSION_STATES` 内），且注册了退役
artifact 类型 `narrative`。后果：harness 的端到端指标工具读不动这些实例
（`e2e_metrics` 在 `loaded["state"].data["state"]` 处抛 KeyError: 'state'），
反馈环因此断开。

本模块把「写投影」收敛为唯一入口，纠正上述三处偏差的根因——**项目脚本不再
手写 status.json**，而是先落盘内容真源（registry + graph + decisions），再由
`ProjectState.refresh_from` 派生流程投影。这与 `runtime/state/reconcile.py`
声明的口径一致（「status.json 只能由 registry/graph 重新派生」）。

硬约束：
- status.json 是**派生视图**；唯一派生入口是 `ProjectState.refresh_from`。
  本模块不反向手写内容字段（questions 的挂载由 registry 派生）。
- 不迁移冻结数据：退役类型由项目脚本在写入前自行修正，本模块不做静默替换。
- 只依赖 stdlib + harness 公开 API，无第三方依赖。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# DAG 全节点（src/modeling_harness/catalog/v3.yaml nodes 真源）。
DAG_NODES: tuple[str, ...] = (
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
    "experiment_design",
    "experiment",
    "experiment_critique",
    "evidence_build",
    "evidence_gate",
    "quality_evaluation",
)


def _ensure_harness_on_path(repo_root: Path) -> None:
    src = str(Path(repo_root) / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def write_state_projection(
    *,
    project_dir: Path | str,
    repo_root: Path | str,
    project: str,
    registry: dict,
    evidence_graph: dict,
    decision_log: dict,
    per_question: dict,
    limitations: list[str],
    completed_nodes: tuple[str, ...] | list[str] | None = None,
    workflow_notes: list[str] | None = None,
    review_verdict: str | None = "pass",
    evidence_extra: dict | None = None,
) -> dict:
    """落盘状态四件套；status.json 由 ProjectState 派生。

    参数
        per_question: {qid: {"status": <QUESTION_STATES>, "models": [...],
                             "experiments": [...], "claims": [...],
                             "dependencies": [...]}}
        limitations: 交付局限（如实声明，非占位符）
        completed_nodes: 已完成的 DAG 节点（默认全 16 节点）
    返回
        {"summary": ProjectState.summary(), "artifacts": <计数>}
    """
    _ensure_harness_on_path(Path(repo_root))
    from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
    from modeling_harness.runtime.graph.evidence_graph import EvidenceGraph
    from modeling_harness.runtime.state.model import (
        ProjectState,
        can_question_transition,
    )

    state_dir = Path(project_dir) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    # 1) 内容真源先落盘（投影必须建立在已落盘的真源之上）
    for name, obj in (("registry.json", registry),
                      ("evidence_graph.json", evidence_graph),
                      ("decision_log.json", decision_log)):
        (state_dir / name).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    reg = ArtifactRegistry(state_dir / "registry.json")
    graph = EvidenceGraph(reg, state_dir / "evidence_graph.json")

    # 2) 流程投影：refresh_from 是唯一派生入口。
    #    无论磁盘上遗留什么旧投影（扁平结构 / 上一轮投影），一律重置为空白后
    #    再由真源派生——投影是派生物，绝不以旧投影为输入（否则不再可重放）。
    st = ProjectState(state_dir / "status.json")
    st.data = ProjectState._empty()
    st.data["project"] = project
    st.refresh_from(reg, graph)

    # 3) 问题级状态：沿合法状态链推进（pending→analyzing→modeled→
    #    experimenting→validated），非法目标会被 can_question_transition 拦下。
    chain = ("analyzing", "modeled", "experimenting", "validated", "complete")
    for qid, info in per_question.items():
        st.ensure_question(qid)
        target = info.get("status", "validated")
        for step in chain:
            cur = st.question_status(qid)
            if cur == target:
                break
            if step == target or can_question_transition(cur, step):
                st.set_question_status(qid, step)
            if st.question_status(qid) == target:
                break
        q = st.data["state"]["questions"][qid]
        q["dependencies"] = list(info.get("dependencies", []))
        q["retry_count"] = 0
        q["failure_reason"] = None
        # 注：不写 q["models"] —— 模型的 Question 归属由 evidence graph 的
        # solved_by 边表达；state 的 question.models 只反映 registry 的
        # artifact.question 直连（单模型服务多问时为 []，由 refresh_from 派生）。

    # 4) 维度状态 + workflow + run（会话自有字段，非内容派生）
    st.set_problem_status("complete")
    st.set_dimension(
        "experiments", "complete",
        by_question={q: list(info.get("experiments", []))
                     for q, info in per_question.items()})
    if evidence_extra:
        for k, v in evidence_extra.items():
            st.dimension("evidence")[k] = v
    st.set_dimension("review", "complete", rounds_completed=1,
                     verdict=review_verdict)
    # workflow 是引擎会话自有字段（非内容派生）。手工脚本构建的实例没有引擎
    # 进度文件，故不虚报 completed_nodes（reconcile 会因缺 engine_progress.json
    # 判为不可精确 resume）；如调方确有引擎进度，可显式传入 completed_nodes。
    for node in (completed_nodes or ()):
        st.workflow_complete(node)
    for note in (workflow_notes or ()):
        st.data["workflow"].setdefault("notes", []).append(
            {"node": "", "note": note, "at": st.data["run"]["updated_at"]})
    st.data["run"]["phase"] = "delivered"
    st.data["limitations"] = list(limitations)
    st.save()

    return {
        "summary": st.summary(),
        "artifacts": len(registry.get("artifacts", {})),
        "status_path": str(state_dir / "status.json"),
    }
