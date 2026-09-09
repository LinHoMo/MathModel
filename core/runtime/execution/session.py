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
                 max_workers: int = 1, min_coverage: float = 0.6,
                 run_meta: dict | None = None,
                 execution_adapter=None,
                 external_model_irs: dict | None = None,
                 external_code: dict | None = None,
                 validation_specs: dict | None = None,
                 external_candidates: dict | None = None):
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        if not questions:
            raise SessionError("questions 不能为空")
        self.questions = list(questions)
        # Hardening P3：外部 executor 溯源（model_provider/model_version/
        # token_cost/decision）；additive，None 时记录为 null
        self.run_meta = run_meta or {}
        # P0-E：真实执行后端（ExecutionAdapter；None = 不执行，result 保持
        # not_executed，由外部 executor 回填）
        self.execution_adapter = execution_adapter

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
            features=features, min_coverage=min_coverage,
            execution_adapter=execution_adapter,
            external_model_irs=external_model_irs,
            external_code=external_code,
            validation_specs=validation_specs,
            external_candidates=external_candidates)
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
        import time as _time
        _t0 = _time.time()
        report = self.waves.run()
        self.engine.save_progress(self.project_dir / "state" / "engine_progress.json")
        if save:
            self.checkpoint()
        self._emit_run_record(_t0, report)
        return report

    def _emit_run_record(self, t0: float, report: dict) -> None:
        """Hardening P3：checkpoint 后落盘 RunRecord（best-effort，不阻断主流程）。"""
        try:
            from runtime.state.runs import emit_run_record, list_run_records
            if self.run_meta.get("_parent_run_id"):
                parent = self.run_meta["_parent_run_id"]
            else:
                prev = list_run_records(self.project_dir)
                parent = prev[-1]["run_id"] if prev else None
            failures = report.get("progress", {}).get("failures", {})
            status = "completed" if not failures else "failed"
            emit_run_record(
                self.project_dir, self.questions, status=status, started_at=t0,
                run_meta=self.run_meta, parent_run_id=parent,
                engine_summary={
                    "completed": len(getattr(self.engine, "completed", [])),
                    "retries": len(getattr(self.engine, "retries", {})),
                    "failures": list(failures.keys()),
                })
        except Exception as e:  # noqa: BLE001 —— 记录失败不得阻断研究主流程
            import sys
            print(f"[runs] RunRecord 记录失败（不阻断）: {e}", file=sys.stderr)

    def resume(self) -> dict:
        """从断点继续（进度文件存在时恢复引擎，否则等价于 run）。"""
        p = self.project_dir / "state" / "engine_progress.json"
        if p.exists():
            self.engine.restore(json.loads(p.read_text(encoding="utf-8")))
        return self.run()

    def checkpoint(self) -> None:
        """Registry / Graph / State / DecisionLog 落盘 + State 派生。"""
        self.registry.save()
        self.graph.save()
        if getattr(self.decisions, "_dirty", False) or                 not self.decisions.path.exists():
            self.decisions.save()
        self.state.refresh_from(self.registry, self.graph)
        self.state.save()

    # ------------------------------------------------------------ P12-1 Question Dependency

    def declare_dependency(self, source_question: str, target_question: str,
                           dependency_type: str, reason: str,
                           created_by: str = "session") -> dict:
        """显式声明科学依赖（P12-1）：State records + 调度镜像 + Registry
        depends_on 镜像三处双写。D2：依赖只能由此显式产生。"""
        from runtime.state.dependencies import declare_dependency
        rec = declare_dependency(self.state, self.registry, source_question,
                                 target_question, dependency_type, reason,
                                 created_by=created_by)
        self.checkpoint()
        return rec

    def dependency_integrity(self) -> list[str]:
        """D1：双写一致性检查（问题清单，空 = 一致）。"""
        from runtime.state.dependencies import dependency_integrity_problems
        return dependency_integrity_problems(self.registry, self.state)

    def declare_cross_relation(self, source: str, target: str,
                               relation_type: str,
                               dependency_refs: list[dict],
                               created_by: str = "session") -> dict:
        """P12-2：显式声明跨问题科学关系（compares/extends/derived_from）。"""
        from runtime.state.relations import declare_cross_relation
        rec = declare_cross_relation(self.state, self.registry, source, target,
                                     relation_type, dependency_refs,
                                     created_by=created_by)
        self.checkpoint()
        return rec

    def cross_relations(self) -> list[dict]:
        from runtime.state.relations import cross_relations
        return cross_relations(self.state)

    def cross_question_context(self, question_ids=None):
        """P12-3-lite：统一跨问题上下文（只读派生——每次从 Registry/Graph/
        State 重算，不落盘、不注册 artifact、不参与失效传播）。"""
        from runtime.synthesis.context import build_cross_question_context
        return build_cross_question_context(
            self.registry, self.graph, self.state, question_ids)

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
        # P12-1 D3/D4：跨问题失效传播——只沿 evidential/extension 依赖打
        # requires_revalidation 标记（execution 依赖永不传播，D3 钉死）
        art0 = self.registry.get(artifact_id)
        src_q = art0.question or (art0.artifact_id
                                  if art0.type == "question" else "")
        if src_q:
            from runtime.state.dependencies import propagate_to_dependents
            self._cross_question_propagation = propagate_to_dependents(
                self.registry, self.state, src_q, reason)
            # P12-2: 上游失效 → 参与的跨问题关系进入 requires_revalidation
            from runtime.state.relations import mark_relations_for_revalidation
            self._relation_revalidation = mark_relations_for_revalidation(
                self.state, src_q, reason)
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
        elif t in ("result", "execution_result", "verification_result"):
            # 执行/验证产物失效 → 从 model_execution 开始重跑
            # （R 由 execute_code 真实执行产生；reset_question 只重置
            #   @qid 节点，model_execution 是全局节点，必须显式 reset）
            qid = art.question or ""
            # FIX-1.5：旧实验链随执行产物失效退役（E/R/C/F superseded，
            # 审计保留）——否则旧 experiment 仍 active 指向死 result，
            # evidence_gate E4 误报"实验无 produces 结果"（audit P0-08）
            if qid and hasattr(self.executor_impl, "_supersede_question_chain"):
                try:
                    self.executor_impl._supersede_question_chain(
                        qid, "invalidate:" + reason[:40])
                except Exception:
                    pass
            if "model_execution" in self.engine.dag.nodes:
                affected = self.engine.reset_to("model_execution")
            else:
                affected = self.engine.reset_question(qid)
        else:
            # dataset / experiment / figure 等 → 按所属 Question 局部重跑
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

    def rerun(self, node_id: str, reason: str = "manual rerun") -> dict:
        """P7 Rerun：研究者主动重跑（区别于 Recompute）。

        重置 node 及其下游；该节点强制新建谱系，旧产物显式 superseded
        （审计保留，不可再成为活跃证据）。返回受影响节点与恢复入口。
        """
        if node_id not in self.engine.dag.nodes:
            raise SessionError(f"未知节点: {node_id}")
        affected = self.engine.reset_to(node_id)
        self.executor_impl.force_new_lineage.add(node_id)
        self.engine._record(node_id, "rerun", reason)
        self.checkpoint()
        return {"reset_nodes": sorted(affected), "reason": reason,
                "resume_ready": self.engine.ready()}

    def _reset_all(self) -> set[str]:
        affected: set[str] = set()
        for nid in list(self.engine.dag.nodes):
            if nid in self.engine.completed or nid in self.engine.blocked \
                    or nid in self.engine.waiting:
                affected |= self.engine.reset_to(nid)
        return affected
