#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""默认节点执行器（P6）—— 把 15 个 Workflow 节点接到真实认知实现上。

执行器协议（P6-② Node Executor）:
    executor(node_id, engine_ctx) -> NodeResult
    NodeResult.outputs 可选键:
        artifacts: list[dict]  产出 Artifact（registry.create 参数：type/title/
                               question/depends_on/data/payload/activate）
        evidence:  list[dict]  证据关系（{from, relation, to}，ID 必须已注册）
        metrics:   dict        节点指标（latency_ms 等，审计用）

本实现是**确定性认知管线**（零 LLM）：文献检索/方法竞技场/实验规划器/研究叙事/
论文投影/批判器全部复用 core/runtime 下的真实模块，产出可追溯到
Artifact Registry + Evidence Graph 的研究状态。LLM 节点后续按同一协议接入。

失败即 FAIL（fail-closed）：缺模型 / 缺假设 / 证据门禁不过 / 判审不 PASS，
都走引擎统一 retry → on_fail 反馈环，而不是"节点自己说完成"。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from .engine import FAIL, PASS, NodeResult

_TERMINAL = ("invalidated", "superseded", "deprecated")

REPO = Path(__file__).resolve().parents[3]
if str(REPO / "core") not in sys.path:
    sys.path.insert(0, str(REPO / "core"))

from runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402
from runtime.modeling.planner import ExperimentPlanner, PlannerError  # noqa: E402
from runtime.modeling.selection import MethodArena, SelectionError  # noqa: E402
from runtime.writing.director import ResearchDirector  # noqa: E402
from runtime.writing.judge_critic import JudgeCritic  # noqa: E402
from runtime.writing.projection import PaperProjection  # noqa: E402
from validators.evidence.evidence_gate import evaluate as evidence_gate_evaluate  # noqa: E402


class HandlerError(RuntimeError):
    """节点处理器配置错误。"""


def _base(node_id: str) -> str:
    return node_id.split("@", 1)[0]


class DefaultNodeExecutor:
    """按节点基名分发的默认执行器。共享上下文经 ctx 传递（跨节点接力）。"""

    def __init__(self, registry, graph, state=None, decisions=None,
                 knowledge_root: str | Path | None = None,
                 features: dict | None = None, min_coverage: float = 0.6):
        self.registry = registry
        self.graph = graph
        self.state = state
        self.decisions = decisions
        self.features = dict(features or {
            "problem_types": ["evaluation"],
            "has_data": True,
            "sample_size": "medium",
        })
        self.min_coverage = min_coverage
        self.retriever = KnowledgeRetriever(knowledge_root or REPO / "core" / "knowledge")
        self.arena = MethodArena(self.retriever, decisions)
        self.planner = ExperimentPlanner(self.retriever)
        # P8：Competition Intelligence 接入 Runtime（候选竞技场 + 竞赛包只读修饰）
        from runtime.knowledge.packs import load_competition_packs
        from runtime.modeling.candidates import CandidateArena
        _packs = load_competition_packs(knowledge_root or REPO / "core" / "knowledge")
        _pack = _packs.get("cp-cumcm") or next(iter(_packs.values()), None)
        self.candidate_arena = CandidateArena(self.retriever, _pack)
        # 跨节点共享（session 级）：qid -> {"model": aid, "plan": ..., ...}
        self.shared: dict = {}
        # P7 Rerun 语义：显式重跑的节点强制新建谱系（旧产物 superseded 审计保留）
        self.force_new_lineage: set[str] = set()

    # ------------------------------------------------------------ 工具

    def _question_of(self, node_id: str) -> str | None:
        return node_id.split("@", 1)[1] if "@" in node_id else None

    def _question_ids(self) -> list[str]:
        return [a.artifact_id for a in self.registry.list_by_type("question")]

    def _models_of(self, qid: str) -> list[str]:
        """该问题的活跃模型（终态 invalidated/superseded/deprecated 不计入）。"""
        return [a.artifact_id for a in self.registry.list_by_type("model")
                if a.question == qid and a.status not in _TERMINAL]

    def _results_of(self, qid: str) -> list[str]:
        """该问题的活跃 result（P7：Registry 派生，崩溃/resume 后仍可重建）。"""
        return [a.artifact_id for a in self.registry.list_by_type("result")
                if a.question == qid and a.status not in _TERMINAL]

    def _claim_of(self, qid: str) -> str:
        """该问题的活跃 claim（无则空串）。"""
        for a in self.registry.list_by_type("claim"):
            if a.question == qid and a.status not in _TERMINAL:
                return a.artifact_id
        return ""

    def _plan_artifact_for(self, qid: str, mid: str):
        """该问题的活跃实验计划（P9.5 红队修复：Registry 派生，不依赖内存 shared）。"""
        for a in self.registry.list_by_type("decision"):
            if "实验计划" in (a.title or "") and a.status == "active":
                if not a.depends_on or mid in a.depends_on:
                    return a
        return None

    def _card_id_of(self, qid: str, mid: str) -> str:
        """问题的选型 card_id：shared 缓存优先，回退 model.data（Registry 真源）。"""
        info = self.shared.get(qid, {})
        if info.get("card_id"):
            return info["card_id"]
        if mid:
            return str(self.registry.get(mid).data.get("card_id", ""))
        return ""

    def _advance_question(self, qid: str, target: str) -> None:
        """沿问题状态机推进（非法转换静默跳过，由 state fail-closed 兜底）。"""
        from runtime.state.model import StateError
        try:
            cur = self.state.question_status(qid)
            path = {"modeled": ["analyzing", "modeled"],
                    "experimenting": ["analyzing", "modeled", "experimenting"]}
            for st in path.get(target, [target]):
                if cur != st:
                    self.state.set_question_status(qid, st)
                    cur = st
        except StateError:
            pass

    def _mk(self, node_id: str, **kw) -> dict:
        kw.setdefault("created_by", node_id)
        return kw

    # ------------------------------------------------------------ 分发

    def __call__(self, node_id: str, ctx: dict) -> NodeResult:
        t0 = time.perf_counter()
        fn = getattr(self, "do_" + _base(node_id), None)
        if fn is None:
            return NodeResult(FAIL, f"没有节点处理器: {_base(node_id)}")
        try:
            result = fn(node_id)
        except (SelectionError, PlannerError) as e:
            return NodeResult(FAIL, str(e))
        result.outputs.setdefault("metrics", {})
        result.outputs["metrics"]["latency_ms"] = round(
            (time.perf_counter() - t0) * 1000, 1)
        return result

    # ------------------------------------------------------------ 节点实现

    def do_problem_analysis(self, node_id: str) -> NodeResult:
        """登记 Problem Artifact + motivates 证据（Question 已由 session 预登记）。"""
        if not self.registry.list_by_type("problem"):
            self.registry.create("problem", title=self.features.get(
                "problem_title", "赛题"), activate=True, created_by=node_id)
        problem_id = self.registry.list_by_type("problem")[0].artifact_id
        qids = self._question_ids()
        ev = [{"from": problem_id, "relation": "motivates", "to": qid}
              for qid in qids]
        return NodeResult(PASS, f"{len(qids)} 个问题已登记",
                          outputs={"artifacts": [], "evidence": ev})

    def do_literature_search(self, node_id: str) -> NodeResult:
        """知识库检索 → 文献证据 decision artifact（记录 top 建议与失败记忆）。"""
        recs = self.retriever.recommend(self.features, top_k=3)
        payload = [{"card_id": r.card.card_id, "score": r.score,
                    "matched": r.matched} for r in recs]
        pids = self.registry.list_by_type("problem")
        d = self.registry.create(
            "decision", title="文献检索与证据提取",
            payload=[r["card_id"] for r in payload],
            data={"recommendations": payload},
            depends_on=[pids[0].artifact_id] if pids else [],
            activate=True, created_by=node_id)
        ev = [{"from": d.artifact_id, "relation": "based_on",
               "to": pids[0].artifact_id}] if pids else []
        return NodeResult(PASS, f"检索到 {len(recs)} 张方法卡",
                          outputs={"artifacts": [], "evidence": ev,
                                   "context": {"literature": payload}})

    def do_model_selection(self, node_id: str) -> NodeResult:
        """方法竞技场：每问题选型 → model artifact + solved_by 证据。"""
        ev = []
        count = 0
        for qid in self._question_ids():
            outcome = self.arena.select(qid, self.features, created_by=node_id)
            card = outcome.chosen_card
            models = self._models_of(qid)
            if node_id in self.force_new_lineage:
                from runtime.artifacts.lifecycle import LifecycleError
                self.shared.pop(qid, None)   # 清缓存：旧 shared 指向将死谱系
                for old_m in models:
                    try:
                        self.registry.get(old_m).transition(
                            "superseded", by=node_id,
                            reason="superseded by explicit rerun")
                    except LifecycleError:
                        pass
                self.force_new_lineage.discard(node_id)
                models = []
            mid = models[-1] if models else ""
            if not mid:
                m = self.registry.create(
                    "model", title=card.get("name") or outcome.chosen,
                    question=qid,
                    depends_on=[qid],
                    data={"card_id": outcome.chosen,
                          "family": card.get("family", ""),
                          "shortlist": [c["card_id"] for c in outcome.shortlist]},
                    activate=True, created_by=node_id)
                mid = m.artifact_id
            ev.append({"from": qid, "relation": "solved_by", "to": mid})
            self.shared.setdefault(qid, {})["card_id"] = outcome.chosen
            # P8-4：生成候选方案（baseline/improved/hybrid/innovation）供规划消费
            try:
                cands = self.candidate_arena.generate_candidates(
                    qid, self.features)
                self.shared[qid]["candidates"] = [
                    c.as_dict() for c in self.candidate_arena.rank(cands)]
            except Exception as e:      # 候选生成失败不阻断选型（降级记录）
                self.shared[qid]["candidates_error"] = str(e)
            if self.state:
                self._advance_question(qid, "modeled")
            self.shared[qid]["model"] = mid
            self.shared[qid]["shortlist"] = [c["card_id"] for c in outcome.shortlist]
            count += 1
        return NodeResult(PASS, f"{count} 个问题完成选型",
                          outputs={"artifacts": [], "evidence": ev})

    def do_model_construction(self, node_id: str) -> NodeResult:
        """模型构建：登记 model 的关键假设（assumes 证据）。"""
        ev = []
        n_assumed = 0
        for qid in self._question_ids():
            models = self._models_of(qid)
            if not models:
                return NodeResult(FAIL, f"{qid}: 尚无已选模型（上游缺失）")
            mid = models[-1]
            if any(r["from"] == mid and r["relation"] == "assumes"
                   for r in self.graph.relations):
                continue    # 幂等：rollback 后重跑不重复登记假设
            card = self.retriever.cards.get(self._card_id_of(qid, mid))
            risks = list(card.risks)[:2] if card else []
            if not risks:
                risks = ["所选方法的前提条件成立（数据规模/类型/独立性）"]
            for i, risk in enumerate(risks, 1):
                a = self.registry.create(
                    "assumption", title=f"{mid} 假设{i}: {risk[:40]}",
                    depends_on=[mid], activate=True, created_by=node_id)
                ev.append({"from": mid, "relation": "assumes", "to": a.artifact_id})
                n_assumed += 1
        return NodeResult(PASS, f"登记 {n_assumed} 条假设",
                          outputs={"artifacts": [], "evidence": ev})

    def do_model_critique(self, node_id: str) -> NodeResult:
        """模型批判门禁：每个问题必须有 model 且至少一条假设。"""
        for qid in self._question_ids():
            models = self._models_of(qid)
            if not models:
                return NodeResult(FAIL, f"{qid}: 无模型可选")
            for mid in models:
                if not any(r["from"] == mid and r["relation"] == "assumes"
                           for r in self.graph.relations):
                    return NodeResult(FAIL, f"{mid}: 无假设支撑，批判不通过")
        return NodeResult(PASS, "模型-假设链完整")

    def do_assumption_check(self, node_id: str) -> NodeResult:
        """假设必要性：每模型 ≥1 条 assumes（与批判互补的 L4 检查）。"""
        for qid in self._question_ids():
            if not self._models_of(qid):
                return NodeResult(FAIL, f"{qid}: 模型缺失，无法核查假设")
        return NodeResult(PASS, "假设核查通过")

    def do_experiment_design(self, node_id: str) -> NodeResult:
        """实验规划器：主方法 + 对照基线 + 灵敏度 → decision artifact。"""
        ev = []
        for qid in self._question_ids():
            info = self.shared.setdefault(qid, {})
            mid = info.get("model") or (self._models_of(qid) or [None])[-1]
            card_id = self._card_id_of(qid, mid)
            if not card_id:
                return NodeResult(FAIL, f"{qid}: 无选型结果，无法规划实验")
            if info.get("plan"):
                continue    # 幂等：计划已存在
            # P8-4→P8-7 通道：最优候选直接生成结构化计划（含创新验证条目）
            cands = info.get("candidates")
            if cands:
                from runtime.modeling.candidates import Candidate
                top = cands[0]
                cand = Candidate(
                    candidate_id=top["candidate_id"], kind=top["kind"],
                    composition=list(top["composition"]),
                    base_card=top["base_card"], rationale=top["rationale"],
                    score=top["score"], required_experiments=list(
                        top["required_experiments"]),
                    knowledge_refs=list(top["knowledge_refs"]))
                plan = self.planner.plan_from_candidate(cand, qid)
                # P9.5 红队修复：新计划建立前退役旧计划（R3 谱系语义，
                # 旧计划 superseded 审计保留，不得双 active）
                from runtime.artifacts.lifecycle import LifecycleError
                for old_pa in self.registry.list_by_type("decision"):
                    if "实验计划" in (old_pa.title or "")                             and old_pa.status == "active"                             and mid in (old_pa.depends_on or []):
                        try:
                            old_pa.transition(
                                "superseded", by=node_id,
                                reason="superseded by re-planned lineage")
                        except LifecycleError:
                            pass
                d = self.registry.create(
                    "decision", title=f"{qid} 实验计划",
                    payload=plan.methods, data=plan.as_dict(),
                    depends_on=[mid] if mid else [],
                    activate=True, created_by=node_id)
                info["plan"] = plan.as_dict()
                ev.append({"from": d.artifact_id, "relation": "based_on", "to": mid})
                continue
            shortlist = [c["card_id"] if isinstance(c, dict) else c
                         for c in (info.get("shortlist") or [])]
            if not shortlist and mid:
                # P7：shortlist 持久化于 model.data（Registry 真源），崩溃后可重建
                shortlist = list(self.registry.get(mid).data.get("shortlist", []))
            baseline = next((c for c in shortlist if c != card_id), None)
            plan = self.planner.plan(qid, [card_id], baseline_card_id=baseline)
            d = self.registry.create(
                "decision", title=f"{qid} 实验计划",
                payload=plan.methods,
                data=plan.as_dict(), depends_on=[mid] if mid else [],
                activate=True, created_by=node_id)
            if mid:
                ev.append({"from": d.artifact_id, "relation": "based_on", "to": mid})
            info["plan"] = plan.as_dict()
        return NodeResult(PASS, "实验计划完成",
                          outputs={"artifacts": [], "evidence": ev})

    def do_experiment(self, node_id: str) -> NodeResult:
        """实验执行（确定性仿真）：E → R → F 证据链。"""
        qid = self._question_of(node_id)
        if not qid:
            return NodeResult(FAIL, "experiment 节点必须 per_question")
        info = self.shared.setdefault(qid, {})
        mid = info.get("model") or (self._models_of(qid) or [None])[-1]
        if not mid:
            return NodeResult(FAIL, f"{qid}: 无模型可实验")
        info["model"] = mid
        if node_id in self.force_new_lineage:
            self.force_new_lineage.discard(node_id)
            # Rerun 语义：旧链（E/R/F/C）整链 superseded，强制全新谱系
            self._supersede_question_chain(qid, node_id)
        live_results = self._results_of(qid)
        if live_results:
            # 幂等：rollback 后重跑复用既有（非终态）实验链；
            # 并回填缺失的 tags/provenance（resume 后 shared 丢失的场景）
            r = live_results[-1]
            r_art = self.registry.get(r)
            plan_art = self._plan_artifact_for(qid, mid)
            plan = (plan_art.data if plan_art else {}) or info.get("plan") or {}
            tags = [t for t, key in (("sensitivity", "sensitivity"),
                                     ("baseline", "baseline_comparison"))
                    if plan.get(key)]
            if tags and not r_art.tags:
                r_art.tags = tags
            e_art = self.registry.get(
                next(f for f, r2, t2 in
                     [(x["from"], x["relation"], x["to"])
                      for x in self.graph.relations]
                     if r2 == "produces" and t2 == r))
            if plan_art and not e_art.data.get("plan_ref"):
                entries = plan.get("entries") or [{}]
                e_art.data.update({
                    "plan_ref": plan_art.artifact_id,
                    "plan_entry": entries[0].get("experiment_id", ""),
                    "hypothesis_ref": entries[0].get("hypothesis", "")})
            f = next((a.artifact_id for a in self.registry.list_by_type("figure")
                      if a.question == qid
                      and a.status not in _TERMINAL), r)
            self._clear_revalidation_marks(qid, node_id)   # 复验存活链
            return NodeResult(PASS, f"{qid}: 复用既有实验链",
                              outputs={"artifacts": [], "evidence": [
                                  {"from": r, "relation": "visualized_by", "to": f}]})
        info["results"] = live_results   # 清掉已失效的旧结果，走全新链
        # 退役旧实验链（fresh 分支触发，如 recompute 后重建）
        self._supersede_question_chain(qid, node_id)
        # P9.5：计划 provenance 从 Registry 派生（resume 后 shared 不可信），
        # 挂在 experiment（计划的执行者）上
        plan_art = self._plan_artifact_for(qid, mid)
        plan = (plan_art.data if plan_art else None) or info.get("plan") or {}
        entries = plan.get("entries") or [{}]
        tags = [t for t, key in (("sensitivity", "sensitivity"),
                                 ("baseline", "baseline_comparison"))
                if plan.get(key)]
        e = self.registry.create("experiment", title=f"{qid} 实验",
                                 question=qid, depends_on=[mid],
                                 data={"card_id": self._card_id_of(qid, mid),
                                       "plan_ref": plan_art.artifact_id
                                       if plan_art else "",
                                       "plan_entry": (entries[0] or {})
                                       .get("experiment_id", ""),
                                       "hypothesis_ref": (entries[0] or {})
                                       .get("hypothesis", "")},
                                 activate=True, created_by=node_id)
        r = self.registry.create("result", title=f"{qid} 结果",
                                 question=qid, depends_on=[e.artifact_id],
                                 data={"card_id": self._card_id_of(qid, mid)},
                                 tags=tags,
                                 activate=True, created_by=node_id)
        f = self.registry.create("figure", title=f"{qid} 结果图",
                                 question=qid, depends_on=[r.artifact_id],
                                 activate=True, created_by=node_id)
        ev = [
            {"from": mid, "relation": "validated_by", "to": e.artifact_id},
            {"from": e.artifact_id, "relation": "tests", "to": mid},
            {"from": e.artifact_id, "relation": "produces", "to": r.artifact_id},
            {"from": r.artifact_id, "relation": "visualized_by", "to": f.artifact_id},
        ]
        info.setdefault("results", []).append(r.artifact_id)
        info["results"] = self._results_of(qid)   # 以 Registry 为准
        self._clear_revalidation_marks(qid, node_id)   # 重建即复验通过
        if self.state:
            self._advance_question(qid, "experimenting")
        return NodeResult(PASS, f"{qid}: 实验/结果/图已登记",
                          outputs={"artifacts": [], "evidence": ev})

    def _clear_revalidation_marks(self, qid: str, by_node: str) -> None:
        """P9.5 红队修复（E6 死循环）：链重建/复验即复验通过——

        清除该问题活跃产物上的 requires_revalidation/dirty 传播标记。
        只清标记（bookkeeping），不改 lifecycle 状态；终态产物不可清除
        （lifecycle fail-closed）。若无此清除，Evidence Gate E6 将永久 WEAK。
        """
        from runtime.artifacts.lifecycle import LifecycleError
        for a in self.registry.all():
            if a.question == qid and a.status not in _TERMINAL                     and a.invalidation:
                try:
                    a.clear_invalidation()
                except LifecycleError:
                    pass

    def _supersede_question_chain(self, qid: str, by_node: str) -> None:
        """退役该问题的整条实验链（E/R/F/C → superseded，审计保留）。

        Rerun 与 Recompute 重建共用：旧 claim 失去支撑后由 evidence_build
        重建新 claim；E4 不再误报旧实验。
        """
        from runtime.artifacts.lifecycle import LifecycleError
        for art in self.registry.all():
            if art.question == qid and art.type in (
                    "experiment", "result", "figure", "claim")                     and art.status not in _TERMINAL:
                try:
                    art.transition("superseded", by=by_node,
                                   reason="replaced by re-run")
                except LifecycleError:
                    pass
        self.shared.pop(qid, None)

    def do_experiment_critique(self, node_id: str) -> NodeResult:
        qid = self._question_of(node_id)
        results = self._results_of(qid)
        if not results:
            return NodeResult(FAIL, f"{qid}: 实验无有效结果产出，批判不通过")
        for rid in results:
            art = self.registry.get(rid)
            if art.status in ("invalidated", "superseded", "deprecated"):
                return NodeResult(FAIL, f"{rid}: 结果已被失效，需重跑实验")
        return NodeResult(PASS, f"{qid}: 实验批判通过")

    def do_evidence_build(self, node_id: str) -> NodeResult:
        """证据构建：每问题 result → claim（supports）。"""
        ev = []
        n = 0
        for qid in self._question_ids():
            results = self._results_of(qid)
            if not results:
                return NodeResult(FAIL, f"{qid}: 无 result，证据链断裂")
            claim_id = self.shared.get(qid, {}).get("claim") or self._claim_of(qid)
            if node_id in self.force_new_lineage and claim_id                     and self.registry.get(claim_id).status not in _TERMINAL:
                self.shared.pop(qid, None)
                from runtime.artifacts.lifecycle import LifecycleError
                try:
                    self.registry.get(claim_id).transition(
                        "superseded", by=node_id,
                        reason="superseded by explicit rerun")
                except LifecycleError:
                    pass
            if claim_id and self.registry.get(claim_id).status not in _TERMINAL:
                continue    # 幂等：有效 claim 已登记（终态则重建）
            c = self.registry.create("claim", title=f"{qid} 结论",
                                     question=qid,
                                     depends_on=[results[-1]],
                                     data={"statement": f"{qid} 结论",
                                           "claim_type": "comparative",
                                           "experiment_refs": [results[-1]],
                                           "literature_refs": []},
                                     activate=True, created_by=node_id)
            ev.append({"from": results[-1], "relation": "supports",
                       "to": c.artifact_id})
            self.shared.setdefault(qid, {})["claim"] = c.artifact_id
            self.shared[qid]["results"] = results
            n += 1
        return NodeResult(PASS, f"{n} 条结论已登记",
                          outputs={"artifacts": [], "evidence": ev})

    def do_evidence_gate(self, node_id: str) -> NodeResult:
        """证据门禁（L4）：coverage ≥ 阈值，否则 FAIL 走反馈环。"""
        # 评估前幂等剪除触及终态产物的死边（旧链退役晚于失效剪边时序）
        self.graph.retract_invalidated()
        report = evidence_gate_evaluate(self.registry, self.graph,
                                        min_coverage=self.min_coverage)
        self.shared["gate_report"] = report
        if report.passed:
            return NodeResult(PASS, report.summary(),
                              outputs={"metrics": {"coverage": report.coverage}})
        return NodeResult(FAIL, f"证据门禁未通过: {report.summary()}")

    def do_quality_evaluation(self, node_id: str) -> NodeResult:
        """P9-10/11：研究质量评估节点（七维 → 四态 → 反馈）。

        FAIL  → 反馈重建（on_fail→evidence_build，复用 P7 语义）
        WEAK/UNKNOWN → PASS + advisory（refine / request_evidence 记录在案，
                       不阻断确定性流程，避免同输入死循环）
        """
        import sys as _sys
        if str(REPO) not in _sys.path:
            _sys.path.insert(0, str(REPO))
        from validators.quality import ResearchQuality

        rq = ResearchQuality(knowledge=self.retriever, decisions=self.decisions)
        report = rq.evaluate(self.registry, self.graph)
        self.shared["quality_report"] = report.as_dict()
        # P9-12：报告落盘 state/（Registry 路径 parents[1] = 项目根）
        try:
            rq.persist(report, self.registry.path.parents[1])
        except Exception:
            pass
        if report.blockers:
            try:
                rq.record_blockers(report)      # P9-12 Quality Memory
            except Exception:
                pass
            actions = ResearchQuality.workflow_feedback(report)
            return NodeResult(
                FAIL,
                f"quality FAIL: {len(report.blockers)} 项阻塞"
                f"（{', '.join(b['check_id'] or b['dimension'] for b in report.blockers[:4])}）",
                outputs={"metrics": {"blockers": len(report.blockers),
                                     "actions": len(actions["rerun"] or []) +
                                     len(actions["recompute"] or [])}})
        detail = (f"quality {report.overall_status}: "
                  f"{len(report.warnings)} warnings / "
                  f"{len(report.unknowns)} unknowns")
        return NodeResult(PASS, detail,
                          outputs={"metrics": {
                              "overall": report.overall_status,
                              "warnings": len(report.warnings),
                              "unknowns": len(report.unknowns)}})

    def do_research_direction(self, node_id: str) -> NodeResult:
        """研究叙事：从 claims 闭包构建 story arcs。"""
        narrative = ResearchDirector(self.registry, self.graph).build()
        self.shared["narrative"] = narrative
        if not narrative.arcs:
            return NodeResult(FAIL, "无任何 claim，无法构建研究叙事")
        return NodeResult(PASS, f"{len(narrative.arcs)} 条故事线",
                          outputs={"metrics": {
                              "supported": len(narrative.supported_arcs)}})

    def do_paper_projection(self, node_id: str) -> NodeResult:
        """论文投影：narrative → 大纲（纯函数，每次重算以收敛 pending_placement）。"""
        narrative = self.shared.get("narrative")
        if narrative is None:
            return NodeResult(FAIL, "narrative 缺失（上游未完成）")
        outline = PaperProjection(self.registry, self.graph).project(narrative)
        self.shared["outline"] = outline
        # P10：Research State → Claim Graph → Finding Graph → Narrative IR
        from runtime.writing.findings import FindingGraph
        from runtime.writing.narrative_ir import build_narrative_ir
        fg = FindingGraph(self.registry, self.graph)
        ir = build_narrative_ir(self.registry, self.graph,
                                findings_graph=fg)
        self.shared["narrative_ir"] = ir.as_dict()
        self.shared["findings"] = fg.as_dict()
        return NodeResult(
            PASS, f"{len(outline.get('sections', []))} 个章节投影 · "
                  f"{len(fg.findings)} findings（validated "
                  f"{len(fg.validated())}）",
            outputs={"artifacts": [], "evidence": [],
                     "metrics": {"findings": len(fg.findings),
                                 "validated": len(fg.validated())}})

    def do_paper_sections(self, node_id: str) -> NodeResult:
        """Per-Qi 章节投影：为该问题创建 paper_section 并挂 appears_in。"""
        qid = self._question_of(node_id)
        outline = self.shared.get("outline")
        narrative = self.shared.get("narrative")
        if outline is None or narrative is None:
            return NodeResult(FAIL, "outline/narrative 缺失（paper_projection 未完成）")
        claim = self.shared.get(qid, {}).get("claim") or self._claim_of(qid)
        claim = claim if claim and self.registry.get(claim).status not in _TERMINAL             else None
        sections = {a.title: a.artifact_id
                    for a in self.registry.list_by_type("paper_section")
                    if a.question == qid}
        ev, n = [], 0
        for sec in outline.get("sections", []):
            title = f"{qid} · {sec.get('section', '章节')}"
            if sec.get("section") == "结果与分析" and not claim:
                continue
            if title in sections:
                # 幂等：章节已存在，但新 claim 仍需补挂归属边
                if sec.get("section") == "结果与分析" and claim:
                    ev.append({"from": claim, "relation": "appears_in",
                               "to": sections[title]})
                continue
            s_art = self.registry.create(
                "paper_section", title=title,
                question=qid, payload=[sec.get("section", "")],
                activate=True, created_by=node_id)
            if sec.get("section") == "结果与分析" and claim:
                ev.append({"from": claim, "relation": "appears_in",
                           "to": s_art.artifact_id})
            n += 1
        if ev:
            # claim 归属已落地 → 立即刷新 outline（pending_placement 收敛）
            self.shared["outline"] = PaperProjection(
                self.registry, self.graph).project(narrative)
        return NodeResult(PASS, f"{qid}: 新建 {n} 个章节",
                          outputs={"artifacts": [], "evidence": ev})

    def do_paper_review(self, node_id: str) -> NodeResult:
        """判审（judge-critic）：PASS 才放行；WEAK/FAIL/UNKNOWN 走反馈环。"""
        narrative = self.shared.get("narrative")
        outline = self.shared.get("outline")
        report = self.shared.get("gate_report")
        judge = JudgeCritic().evaluate(narrative, outline,
                                       evidence_report=report)
        self.shared["judge_report"] = judge
        if judge.verdict == "PASS":
            return NodeResult(PASS, judge.summary())
        risks = [f"{r.source}/{r.code}" for r in judge.risks]
        return NodeResult(FAIL, f"judge {judge.verdict}: {', '.join(risks) or 'insufficient'}")
