#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RuntimeSession（P6）—— Registry + Evidence Graph + State + WorkflowEngine 的胶水层。

一次会话 = 一个可执行研究运行：

    questions → compose_executable DAG → WaveExecutor
        ↙ 节点处理器产出 Artifact / Evidence
    Registry / Graph 落盘 → State.refresh_from 派生聚合 → resume 可用

核心联动（评审 P6 验收项）:
    ④ Evidence Registration   处理器直接写 Registry/Graph，run() 结束统一落盘
    ⑤ Validator Hook          engine validators 挂钩（PASS 先过 validator）
    ⑥ Failure Recovery        引擎 retry / on_fail / unblock（局部重跑）
    ⑦ Invalidation            session.invalidate(artifact_id) → 图传播 → 引擎局部重置
    ⑧ Resume                  进度落盘 save_progress / WorkflowEngine.load 断点续跑
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO / "core") not in sys.path:
    sys.path.insert(0, str(REPO / "core"))

from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from runtime.decisions.log import DecisionLog  # noqa: E402
from runtime.execution.composer import WorkflowComposer  # noqa: E402
from runtime.execution.engine import WorkflowEngine  # noqa: E402
from runtime.execution.wave_executor import WaveExecutor  # noqa: E402
from runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402
from runtime.state.model import ProjectState  # noqa: E402

from .handlers import DefaultNodeExecutor  # noqa: E402


class SessionError(RuntimeError):
    """会话操作非法。"""


class RuntimeSession:
    """一个项目的 V3 研究运行会话。"""

    def __init__(self, project_dir: str | Path, questions: list[str],
                 features: dict | None = None, knowledge_root=None,
                 max_workers: int = 1, min_coverage: float = 0.6):
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        if not questions:
            raise SessionError("questions 不能为空")
        self.questions = list(questions)

        sdir = self.project_dir / "state"
        self.state = ProjectState(sdir / "status.json")
        self.registry = ArtifactRegistry(sdir / "registry.json")
        self.graph = EvidenceGraph(self.registry, sdir / "evidence_graph.json")
        self.decisions = DecisionLog(sdir / "decision_log.json")

        dag = WorkflowComposer(REPO / "core" / "workflows").compose_executable(
            self.questions)
        self.executor_impl = DefaultNodeExecutor(
            self.registry, self.graph, state=self.state,
            decisions=self.decisions, knowledge_root=knowledge_root,
            features=features, min_coverage=min_coverage)
        # 预登记 Question Artifact（分配的 ID Q001… 依序即 questions 标签）
        existing = [a.artifact_id for a in self.registry.list_by_type("question")]
        for q in self.questions:
            if q not in existing:
                self.registry.create("question", title=q,
                                     activate=True, created_by="session")
            self.state.ensure_question(q)
        self.engine = WorkflowEngine(dag, self.executor_impl, state=self.state,
                                     on_success=self._register_evidence)
        self.waves = WaveExecutor(dag, self.executor_impl, max_workers=max_workers)
        self.engine = self.waves.engine          # 波次执行器内嵌引擎（共享状态）
        self.waves.engine.on_success = self._register_evidence

    def _register_evidence(self, node_id: str, result) -> None:
        """P6-④ Evidence Registration：节点最终 PASS 后把 outputs.evidence 写入图。"""
        from runtime.graph.evidence_graph import GraphError
        for rel in (result.outputs or {}).get("evidence", []):
            try:
                self.graph.add_relation(rel["from"], rel["relation"], rel["to"])
            except GraphError as e:
                # 重复登记 / 引用缺失：可见但不阻断（幂等重跑常见）
                self.engine._record(node_id, "evidence-skip", str(e))

    # ------------------------------------------------------------ 执行

    def run(self, save: bool = True) -> dict:
        """跑完整个 DAG（含反馈环/重试），落盘并派生聚合状态。"""
        report = self.waves.run()
        self.engine.save_progress(self.project_dir / "state" / "engine_progress.json")
        if save:
            self.checkpoint()
        return report

    def resume(self) -> dict:
        """从断点继续（进度文件存在时恢复引擎，否则等价于 run）。"""
        p = self.project_dir / "state" / "engine_progress.json"
        if p.exists():
            self.engine.restore(json.loads(p.read_text(encoding="utf-8")))
        return self.run()

    def checkpoint(self) -> None:
        """Registry / Graph / State 三件套落盘 + State 从 Registry/Graph 派生。"""
        self.registry.save()
        self.graph.save()
        self.state.refresh_from(self.registry, self.graph)
        self.state.save()

    # ------------------------------------------------------------ Invalidation（P6-⑦）

    def invalidate(self, artifact_id: str, reason: str = "") -> dict:
        """失效一个 Artifact：图传播 → 按语义映射到引擎局部重置。

        映射规则（保守、可预期）:
            question          → 全部重置（问题的证据链整体重建）
            model/assumption  → reset_to("model_selection")（重选型并重跑下游）
            experiment/result/figure/question 级实验产物 → reset_question(qid)
            claim             → reset_to("evidence_build")
            paper_section     → reset_to("paper_projection")
        """
        report = self.graph.invalidate(artifact_id, reason=reason)
        # 传播完成后剪除触及终态产物的死边（否则 E3 永远 FAIL，健康链无法重建）
        self.graph.retract_invalidated()
        art = self.registry.get(artifact_id)
        t = art.type
        if t == "question":
            # 问题的证据链整体重建：全图重置
            affected = self._reset_all()
        elif t in ("model", "assumption"):
            affected = self.engine.reset_to("model_selection")
        elif t == "claim":
            affected = self.engine.reset_to("evidence_build")
        elif t == "paper_section":
            affected = self.engine.reset_to("paper_projection")
        else:
            # dataset / experiment / result / figure 等 → 按所属 Question 局部重跑
            qid = art.question or next(
                (a.question for a in self.registry.all()
                 if a.artifact_id == artifact_id), None)
            if qid and any(nid.endswith(f"@{qid}")
                           for nid in self.engine.dag.nodes):
                affected = self.engine.reset_question(qid)
            else:
                affected = set()
        self.checkpoint()
        return {"invalidation": report, "reset_nodes": sorted(affected),
                "resume_ready": self.engine.ready()}

    def _reset_all(self) -> set[str]:
        affected: set[str] = set()
        for nid in list(self.engine.dag.nodes):
            if nid in self.engine.completed or nid in self.engine.blocked \
                    or nid in self.engine.waiting:
                affected |= self.engine.reset_to(nid)
        return affected
