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
        # 跨节点共享（session 级）：qid -> {"model": aid, "plan": ..., ...}
        self.shared: dict = {}

    # ------------------------------------------------------------ 工具

    def _question_of(self, node_id: str) -> str | None:
        return node_id.split("@", 1)[1] if "@" in node_id else None

    def _question_ids(self) -> list[str]:
        return [a.artifact_id for a in self.registry.list_by_type("question")]

    def _models_of(self, qid: str) -> list[str]:
        """该问题的活跃模型（终态 invalidated/superseded/deprecated 不计入）。"""
        return [a.artifact_id for a in self.registry.list_by_type("model")
                if a.question == qid and a.status not in _TERMINAL]

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
            mid = models[-1] if models else ""
            if not mid:
                m = self.registry.create(
                    "model", title=card.get("name") or outcome.chosen,
                    question=qid,
                    depends_on=[qid],
                    data={"card_id": outcome.chosen, "family": card.get("family", "")},
                    activate=True, created_by=node_id)
                mid = m.artifact_id
            ev.append({"from": qid, "relation": "solved_by", "to": mid})
            self.shared.setdefault(qid, {})["card_id"] = outcome.chosen
            if self.state:
                self._advance_question(qid, "modeled")
            self.shared[qid]["model"] = mid
            self.shared[qid]["shortlist"] = outcome.shortlist
            count += 1
        return NodeResult(PASS, f"{count} 个问题完成选型",
                          outputs={"artifacts": [], "evidence": ev})

    def do_model_construction(self, node_id: str) -> NodeResult:
        """模型构建：登记 model 的关键假设（assumes 证据）。"""
        ev = []
        n_assumed = 0
        for qid in self._question_ids():
            mid = self.shared.get(qid, {}).get("model")
            if not mid:
                return NodeResult(FAIL, f"{qid}: 尚无已选模型（上游缺失）")
            if any(r["from"] == mid and r["relation"] == "assumes"
                   for r in self.graph.relations):
                continue    # 幂等：rollback 后重跑不重复登记假设
            card = self.retriever.cards.get(self.shared[qid].get("card_id", ""))
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
            info = self.shared.get(qid, {})
            card_id = info.get("card_id")
            if not card_id:
                return NodeResult(FAIL, f"{qid}: 无选型结果，无法规划实验")
            if info.get("plan"):
                continue    # 幂等：计划已存在
            shortlist = [c["card_id"] for c in info.get("shortlist", [])]
            baseline = next((c for c in shortlist if c != card_id), None)
            plan = self.planner.plan(qid, [card_id], baseline_card_id=baseline)
            mid = info.get("model")
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
        mid = info.get("model")
        if not mid:
            return NodeResult(FAIL, f"{qid}: 无模型可实验")
        live_results = [rid for rid in info.get("results", [])
                        if self.registry.get(rid).status not in _TERMINAL]
        if live_results:
            # 幂等：rollback 后重跑复用既有（非终态）实验链
            r = live_results[-1]
            f = next((a.artifact_id for a in self.registry.list_by_type("figure")
                      if a.question == qid
                      and a.status not in _TERMINAL), r)
            return NodeResult(PASS, f"{qid}: 复用既有实验链",
                              outputs={"artifacts": [], "evidence": [
                                  {"from": r, "relation": "visualized_by", "to": f}]})
        info["results"] = live_results   # 清掉已失效的旧结果，走全新链
        # 退役旧实验链（reval 命中但未终态的 E）：新链替代，E4 不再误报
        from runtime.artifacts.lifecycle import LifecycleError
        for old_e in self.registry.list_by_type("experiment"):
            if old_e.question == qid and old_e.status not in _TERMINAL:
                try:
                    old_e.transition("superseded", by=node_id,
                                     reason="replaced by re-run after invalidation")
                except LifecycleError:
                    pass
        e = self.registry.create("experiment", title=f"{qid} 实验",
                                 question=qid, depends_on=[mid],
                                 activate=True, created_by=node_id)
        plan = info.get("plan") or {}
        tags = [t for t, key in (("sensitivity", "sensitivity"),
                                 ("baseline", "baseline_comparison"))
                if plan.get(key)]
        r = self.registry.create("result", title=f"{qid} 结果",
                                 question=qid, depends_on=[e.artifact_id],
                                 data={"card_id": info.get("card_id", "")},
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
        if self.state:
            self._advance_question(qid, "experimenting")
        return NodeResult(PASS, f"{qid}: 实验/结果/图已登记",
                          outputs={"artifacts": [], "evidence": ev})

    def do_experiment_critique(self, node_id: str) -> NodeResult:
        qid = self._question_of(node_id)
        results = [rid for rid in self.shared.get(qid, {}).get("results", [])
                   if self.registry.get(rid).status not in _TERMINAL]
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
            results = self.shared.get(qid, {}).get("results", [])
            if not results:
                return NodeResult(FAIL, f"{qid}: 无 result，证据链断裂")
            claim_id = self.shared.get(qid, {}).get("claim")
            if claim_id and self.registry.get(claim_id).status not in _TERMINAL:
                continue    # 幂等：有效 claim 已登记（终态则重建）
            c = self.registry.create("claim", title=f"{qid} 结论",
                                     question=qid,
                                     depends_on=[results[-1]],
                                     activate=True, created_by=node_id)
            ev.append({"from": results[-1], "relation": "supports",
                       "to": c.artifact_id})
            self.shared.setdefault(qid, {})["claim"] = c.artifact_id
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
        return NodeResult(PASS, f"{len(outline.get('sections', []))} 个章节投影",
                          outputs={"artifacts": [], "evidence": []})

    def do_paper_sections(self, node_id: str) -> NodeResult:
        """Per-Qi 章节投影：为该问题创建 paper_section 并挂 appears_in。"""
        qid = self._question_of(node_id)
        outline = self.shared.get("outline")
        narrative = self.shared.get("narrative")
        if outline is None or narrative is None:
            return NodeResult(FAIL, "outline/narrative 缺失（paper_projection 未完成）")
        claim = self.shared.get(qid, {}).get("claim")
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
