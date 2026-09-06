#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Research Quality Aggregator（P9-9）+ Runtime 反馈映射（P9-10/11/13）。

ResearchQuality.evaluate(...) 返回 QualityReport（不是 0.82）：
    overall_status / dimensions{7} / blockers / warnings / unknowns /
    recommended_actions / priorities

P9-13：Competition Pack 的 judging_preferences 只改变**检查优先级的排序**，
绝不改变任何 finding 的 severity/status（FAIL 永远是 FAIL）。

P9-12 Quality Memory：blockers 落盘 state/quality_report.json，并可显式
登记为 DecisionLog 的 quality 类决策（写回既有记忆体系，不建平行 memory）。
"""

from __future__ import annotations

import json
from pathlib import Path

from .contract import (FAIL, PASS, QUALITY_STATUSES, UNKNOWN, WEAK,
                       QualityDimensionReport, QualityFinding, QualityReport)
from .evaluators import (claim_quality, decision_quality, evidence_quality,
                         experiment_quality, innovation_quality,
                         model_quality, problem_quality,
                         reproducibility_quality)

DIMENSION_ORDER = ("problem", "model", "experiment", "evidence",
                   "decision", "innovation", "reproducibility")


class ResearchQuality:
    """统一评估入口。确定性、只读（除显式 persist/record）。

    用法:
        rq = ResearchQuality(knowledge=retriever, decisions=dlog, pack=pack)
        report = rq.evaluate(registry, graph)
        report.overall_status      # PASS/WEAK/FAIL/UNKNOWN
        report.blockers            # [QualityFinding]
        report.recommended_actions # [{action, subject_type, subject_id, ...}]
    """

    def __init__(self, knowledge=None, decisions=None, pack=None,
                 min_coverage: float = 0.8):
        self.knowledge = knowledge
        self.decisions = decisions
        self.pack = pack
        self.min_coverage = min_coverage

    # ------------------------------------------------------------ 评估

    def evaluate(self, registry, graph, gate_report=None,
                 state=None) -> QualityReport:
        gate = gate_report
        if gate is None and self.pack is None:
            # 评估器需要 gate 事实时兜底自算（gate 语义不重算：只调用一次）
            try:
                from ..evidence.evidence_gate import evaluate as _eval
                gate = _eval(registry, graph,
                             min_coverage=self.min_coverage)
            except Exception:
                gate = None

        dims: dict[str, list[QualityFinding]] = {d: [] for d in DIMENSION_ORDER}
        dims["problem"] += problem_quality(registry, graph)
        dims["model"] += model_quality(registry, graph, self.knowledge,
                                       self.decisions)
        dims["experiment"] += experiment_quality(registry, graph)
        dims["evidence"] += evidence_quality(registry, graph, gate,
                                             self.min_coverage)
        dims["evidence"] += claim_quality(registry, graph, gate)
        dims["decision"] += decision_quality(registry, graph, self.knowledge,
                                             self.decisions)
        dims["innovation"] += innovation_quality(registry, graph)
        dims["reproducibility"] += reproducibility_quality(registry, graph)

        report = QualityReport(subject=getattr(registry, "project", ""))
        for name in DIMENSION_ORDER:
            report.dimensions[name] = QualityDimensionReport(
                dimension=name, findings=dims[name])

        # P9-13：Pack → 检查优先级（只排序 recommended_actions，不改判定）
        if self.pack is not None:
            report.priorities = self._pack_priorities()
            report.recommended_actions.sort(
                key=lambda a: report.priorities.get(
                    _action_dimension(a), 99))
        return report

    # ------------------------------------------------------------ P9-13

    def _pack_priorities(self) -> dict[str, int]:
        """judging_preferences/evaluation_dimensions → 维度优先级（小者先）。"""
        prefs = [p.lower() for p in (self.pack.judging_preferences or [])]
        dims = [d.lower() for d in (self.pack.evaluation_dimensions or [])]
        prio: dict[str, int] = {}
        rank = 0
        for dim in DIMENSION_ORDER:
            if any(dim in p or p in dim for p in prefs + dims):
                prio[dim] = rank
                rank += 1
        # 未命中的维度保持默认后位（不影响判定，只影响处置顺序）
        for dim in DIMENSION_ORDER:
            prio.setdefault(dim, 50 + DIMENSION_ORDER.index(dim))
        return prio

    # ------------------------------------------------------------ P9-10 动作映射

    @staticmethod
    def workflow_feedback(report: QualityReport) -> dict:
        """Quality → Workflow 动作（P9-10/11）：映射到 P7 已冻结语义。

        FAIL  → 找到 blocker 的 recommended_action（rerun/recompute/…）
        WEAK  → refine（advisory，不阻断）
        UNKNOWN → request_evidence
        """
        actions = {"rerun": [], "recompute": [], "refine": [],
                   "request_evidence": [], "advisory": []}
        for f in report.blockers:
            act = f.recommended_action
            if act in ("rerun_model_selection", "rerun_experiment"):
                actions["rerun"].append(f.as_dict())
            elif act in ("recompute", "rebuild_evidence", "reset_question"):
                actions["recompute"].append(f.as_dict())
            elif act == "refine_experiment_plan":
                actions["refine"].append(f.as_dict())
            elif act == "request_evidence":
                actions["request_evidence"].append(f.as_dict())
            else:
                actions["advisory"].append(f.as_dict())
        for f in report.warnings:
            actions["advisory"].append(f.as_dict())
        for f in report.unknowns:
            actions.setdefault("request_evidence", []).append(f.as_dict())
        return actions

    # ------------------------------------------------------------ P9-12 Quality Memory

    @staticmethod
    def persist(report: QualityReport, project_dir: Path) -> Path:
        """报告落盘 state/quality_report.json（state 资产，非知识文件）。"""
        out = Path(project_dir) / "state" / "quality_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report.as_dict(), ensure_ascii=False,
                                  indent=2), encoding="utf-8")
        return out

    def record_blockers(self, report: QualityReport, created_by="research-quality"):
        """把 FAIL blockers 显式登记进 DecisionLog（quality 类决策，
        写回既有记忆体系 → 未来 Capability Matching 经 failure/knowledge
        交叉引用形成 Research Learning Loop）。"""
        if self.decisions is None:
            return []
        recorded = []
        for b in report.blockers:
            question = (f"[quality] {b.subject_type}:{b.subject_id} "
                        f"{b.check_id or b.dimension}")
            # 去重：同一 blocker 不重复登记（审计保留首次）
            if any(d.question == question and d.status == "active"
                   for d in self.decisions.decisions.values()):
                continue
            dec = self.decisions.add(
                question=question,
                chosen=f"{b.status}:{b.reason[:80]}",
                alternatives=["ignore", "fix", "defer"],
                criteria=["quality_contract"],
                reasoning=b.reason,
                confidence=1.0,
                reversible=True,
                created_by=created_by,
                evidence_ids=list(b.artifact_refs)[:5],
                question_type="quality",
                knowledge_refs=list(b.knowledge_refs),
                required_validation=[b.recommended_action],
                score_breakdown={"dimension": b.dimension,
                                 "severity": b.severity},
            )
            recorded.append(dec)
        return recorded


def _action_dimension(action: dict) -> str:
    """行动 → 归属维度（用于 Pack 优先级排序）。"""
    a = action.get("action", "")
    if "model" in a:
        return "model"
    if "experiment" in a or "rerun" in a:
        return "experiment"
    if "evidence" in a or "recompute" in a:
        return "evidence"
    if "decision" in a or "review" in a:
        return "decision"
    return action.get("subject_type", "problem")
