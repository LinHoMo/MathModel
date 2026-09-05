#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Research Quality Evaluators（P9-2~P9-8）—— 七维确定性检查器。

设计分工（防重复计算，P9-0 审计 §2）:
* Evidence Gate 判"链是否可用"（终局 fail-closed）；本模块判"为什么够/不够、
  怎么补"。传入 gate_report 时自动跳过 Gate 已覆盖的检查（E1/E2/E3/E4），
  未传入时自行兜底——同一语义只算一次。
* Capability Matching 的 applicability 规则被 M1 复用（经 model.data.card_id
  → 卡片字段），不重写第二套兼容性规则。
* 所有 finding 携带 subject + refs + recommended_action（映射 P7 已冻结语义）。
"""

from __future__ import annotations

from ..evidence.evidence_gate import evaluate as gate_evaluate
from .contract import (FAIL, PASS, UNKNOWN, WEAK, QualityDimensionReport,
                       QualityFinding, QualityReport)


def _finding(dim, severity, subject_type, subject_id, reason, *,
             check_id="", status=None, **refs) -> QualityFinding:
    st = status or (FAIL if severity == "fail" else
                    UNKNOWN if severity == "unknown" else
                    WEAK if severity == "weak" else PASS)
    return QualityFinding(dimension=dim, severity=severity,
                          status=st, subject_type=subject_type,
                          subject_id=subject_id, reason=reason,
                          check_id=check_id, **refs)


def _edges(graph):
    return [(e["from"], e["relation"], e["to"]) for e in graph.relations]


def _active(registry, typ):
    return [a for a in registry.list_by_type(typ)
            if a.status not in ("invalidated", "superseded", "deprecated")]


# ============================================================
# Q1 Problem Validity
# ============================================================

def problem_quality(registry, graph) -> list[QualityFinding]:
    out = []
    problems = _active(registry, "problem")
    questions = _active(registry, "question")
    if not questions:
        out.append(_finding("problem", "unknown", "question", "",
                            "无活跃 Question，无法评估问题质量", check_id="P-Q0"))
        return out
    edges = _edges(graph)
    for q in questions:
        motivated = any(r == "motivates" and t == q.artifact_id
                        for _, r, t in edges)
        if not problems:
            out.append(_finding("problem", "fail", "question", q.artifact_id,
                                "问题缺少来源 Problem（motivates 缺失）",
                                artifact_refs=[q.artifact_id], check_id="P-Q1",
                                recommended_action="recompute"))
        elif not motivated:
            out.append(_finding("problem", "weak", "question", q.artifact_id,
                                "问题未挂接来源 Problem 的 motivates 边",
                                artifact_refs=[q.artifact_id], check_id="P-Q1",
                                recommended_action="recompute"))
        st = registry.get(q.artifact_id).status
        state_q = None
        if st == "draft":
            out.append(_finding("problem", "weak", "question", q.artifact_id,
                                "问题仍处 draft，未被研究流程激活",
                                artifact_refs=[q.artifact_id], check_id="P-Q2"))
    return out


# ============================================================
# Q2 Model Validity（M1–M4）
# ============================================================

def model_quality(registry, graph, knowledge=None, decisions=None) -> list[QualityFinding]:
    out = []
    models = _active(registry, "model")
    if not models:
        out.append(_finding("model", "unknown", "model", "",
                            "无活跃模型，无法评估模型质量", check_id="M-0"))
        return out
    edges = _edges(graph)
    for m in models:
        mid = m.artifact_id
        card_id = str(m.data.get("card_id", ""))
        # M1: 选型的卡片存在且可追溯（复用 P8 applicability 数据，不重算）
        if not card_id:
            out.append(_finding("model", "fail", "model", mid,
                                "模型未登记 card_id，无法追溯选型依据",
                                artifact_refs=[mid], check_id="M1",
                                recommended_action="rerun_model_selection"))
        elif knowledge is not None and card_id not in knowledge.cards:
            out.append(_finding("model", "fail", "model", mid,
                                f"选型引用的 MethodCard 不存在: {card_id}",
                                artifact_refs=[mid], check_id="M1",
                                knowledge_refs=[{"id": card_id}],
                                recommended_action="rerun_model_selection"))
        # M2: 假设声明存在
        has_assumption = any(f == mid and r == "assumes" for f, r, _ in edges)
        if not has_assumption:
            out.append(_finding("model", "fail", "model", mid,
                                "模型无假设声明（assumes 边缺失）",
                                artifact_refs=[mid], check_id="M2",
                                recommended_action="recompute"))
        # M3: 对比证据——计划存在且带 baseline 与 metrics
        plan = _plan_for(registry, mid)
        if plan is None:
            out.append(_finding("model", "weak", "model", mid,
                                "模型无实验计划（无法证明对比存在）",
                                artifact_refs=[mid], check_id="M3",
                                recommended_action="refine_experiment_plan"))
        else:
            if not plan.get("baseline_comparison"):
                out.append(_finding("model", "fail", "model", mid,
                                    "实验计划无基线对照（不得宣称最优）",
                                    artifact_refs=[mid], check_id="M3",
                                    recommended_action="refine_experiment_plan"))
            first = (plan.get("entries") or [{}])[0]
            if not first.get("metrics"):
                out.append(_finding("model", "weak", "model", mid,
                                    "对比指标缺失（comparison metric 未定义）",
                                    artifact_refs=[mid], check_id="M3",
                                    recommended_action="refine_experiment_plan"))
        # M4: 选择 trace——决策已登记且覆盖该卡
        dec = _selection_decision(decisions, card_id) if decisions else None
        if dec is None:
            out.append(_finding("model", "weak", "model", mid,
                                f"选型决策未登记（为什么选 {card_id} 无法追溯）",
                                artifact_refs=[mid], check_id="M4",
                                knowledge_refs=[{"id": card_id}],
                                recommended_action="review_decision"))
    return out


def _plan_for(registry, model_id) -> dict | None:
    """找该模型的实验计划 decision artifact（data=plan dict）。"""
    for a in registry.list_by_type("decision"):
        if "实验计划" in (a.title or "") and a.status == "active" \
                and model_id in (a.depends_on or []):
            return a.data or {}
    return None


def _selection_decision(decisions, card_id):
    if decisions is None:
        return None
    for d in decisions.decisions.values():
        if d.status == "active" and d.chosen == card_id:
            return d
    return None


# ============================================================
# Q3 Experiment Validity（E1–E8）
# ============================================================

def experiment_quality(registry, graph) -> list[QualityFinding]:
    out = []
    plans = [a for a in registry.list_by_type("decision")
             if "实验计划" in (a.title or "") and a.status == "active"]
    if not plans:
        out.append(_finding("experiment", "unknown", "experiment_plan", "",
                            "无实验计划，无法评估实验质量", check_id="E-0"))
        return out
    edges = _edges(graph)
    for pa in plans:
        plan = pa.data or {}
        entries = plan.get("entries") or []
        if not entries:
            out.append(_finding("experiment", "fail", "experiment_plan",
                                pa.artifact_id, "实验计划无结构化条目",
                                artifact_refs=[pa.artifact_id], check_id="E-0",
                                recommended_action="refine_experiment_plan"))
            continue
        for e in entries:
            eid = e.get("experiment_id", "?")
            # E1 purpose
            if not (e.get("purpose") or "").strip():
                out.append(_finding("experiment", "fail", "experiment_plan",
                                    pa.artifact_id,
                                    f"{eid}: purpose 缺失（为什么做不能为空）",
                                    artifact_refs=[pa.artifact_id],
                                    check_id="E1",
                                    recommended_action="refine_experiment_plan"))
            # E2 hypothesis testable
            if not (e.get("hypothesis") or "").strip():
                out.append(_finding("experiment", "fail", "experiment_plan",
                                    pa.artifact_id,
                                    f"{eid}: hypothesis 缺失（不可检验）",
                                    artifact_refs=[pa.artifact_id],
                                    check_id="E2",
                                    recommended_action="refine_experiment_plan"))
            # E3 decision rule executable
            rule = e.get("decision_rule")
            if not rule or not (rule.get("accept_if") or "").strip() \
                    or not (rule.get("reject_if") or "").strip():
                out.append(_finding("experiment", "fail", "experiment_plan",
                                    pa.artifact_id,
                                    f"{eid}: decision rule 不可执行"
                                    "（缺 accept/reject 条件）",
                                    artifact_refs=[pa.artifact_id],
                                    check_id="E3",
                                    recommended_action="refine_experiment_plan"))
            # E4 information gain justified
            gain = e.get("expected_information_gain")
            if gain is None or not 0 <= float(gain) <= 1:
                out.append(_finding("experiment", "weak", "experiment_plan",
                                    pa.artifact_id,
                                    f"{eid}: 信息增益未定义或越界（{gain}）",
                                    artifact_refs=[pa.artifact_id],
                                    check_id="E4",
                                    recommended_action="refine_experiment_plan"))
            elif e.get("priority") == 1 and float(gain) < 0.5:
                out.append(_finding("experiment", "weak", "experiment_plan",
                                    pa.artifact_id,
                                    f"{eid}: 必做实验的信息增益偏低（{gain}），"
                                    "与优先级不匹配",
                                    artifact_refs=[pa.artifact_id],
                                    check_id="E4"))
            # E5 baseline exists
            if not (e.get("baseline") or "").strip():
                out.append(_finding("experiment", "fail", "experiment_plan",
                                    pa.artifact_id,
                                    f"{eid}: baseline 缺失（无对照不得下结论）",
                                    artifact_refs=[pa.artifact_id],
                                    check_id="E5",
                                    recommended_action="refine_experiment_plan"))
        # E7/E8: 执行侧——结果解析假设 + 失败产生新决策
        experiments = [a for a in registry.list_by_type("experiment")
                       if a.status == "active"]
        for exp in experiments:
            if exp.question and exp.question != pa.data.get("question") \
                    and pa.data.get("question") not in (None, ""):
                continue
            has_result = any(f == exp.artifact_id and r == "produces"
                             and registry.get(t).status == "active"
                             for f, r, t in edges)
            if not has_result:
                out.append(_finding("experiment", "weak", "experiment",
                                    exp.artifact_id,
                                    "实验无活跃 result（假设未被结果解析）",
                                    artifact_refs=[exp.artifact_id],
                                    check_id="E7",
                                    recommended_action="rerun_experiment"))
        # E8: 死链结果必须有后续决策（重建或判死记录）
        dead_results = [a for a in registry.list_by_type("result")
                        if a.status in ("invalidated", "superseded")]
        for dr in dead_results:
            qid = dr.question
            still_active = [a for a in registry.list_by_type("result")
                            if a.question == qid and a.status == "active"]
            if not still_active:
                out.append(_finding("experiment", "fail", "experiment", dr.artifact_id,
                                    f"{dr.artifact_id} 失效后问题 {qid} 无重建结果，"
                                    "且无重跑决策记录（失败必须产生决策）",
                                    artifact_refs=[dr.artifact_id], check_id="E8",
                                    recommended_action="rerun_experiment"))
    return out


# ============================================================
# Q4 Evidence Sufficiency（与 Gate 分工：gate_report 提供时跳过其覆盖项）
# ============================================================

def evidence_quality(registry, graph, gate_report=None,
                     min_coverage: float = 0.8) -> list[QualityFinding]:
    out = []
    claims = _active(registry, "claim")
    if not claims:
        out.append(_finding("evidence", "unknown", "claim", "",
                            "无活跃 claim，证据充分性无法评估", check_id="Q-0"))
        return out
    edges = _edges(graph)
    # ① independence：同一实验产出链支撑的多个 claim 不得计为独立证据
    producer_of = {}
    for f, r, t in edges:
        if r == "produces":
            producer_of[t] = f
    support_sources: dict[str, set[str]] = {}
    for c in claims:
        sources = {producer_of.get(f, f) for f, r, t in edges
                   if r == "supports" and t == c.artifact_id}
        support_sources[c.artifact_id] = sources
    for i, c1 in enumerate(claims):
        for c2 in claims[i + 1:]:
            if c1.question and c1.question == c2.question:
                s1, s2 = support_sources[c1.artifact_id], support_sources[c2.artifact_id]
                if s1 and s2 and s1 == s2:
                    out.append(_finding(
                        "evidence", "weak", "claim", c2.artifact_id,
                        f"{c1.artifact_id} 与 {c2.artifact_id} 由同一实验产出链支撑，"
                        "不得计为独立证据",
                        artifact_refs=[c1.artifact_id, c2.artifact_id],
                        check_id="EQ-independence"))
    # ② coverage（复用图派生，不重算 gate 内部规则）
    cov = graph.coverage()
    ratio = cov.get("coverage_ratio")
    if ratio is not None and ratio < min_coverage:
        out.append(_finding("evidence", "weak", "claim", "",
                            f"claim 覆盖率 {ratio} 低于阈值 {min_coverage}",
                            check_id="EQ-coverage",
                            recommended_action="rebuild_evidence"))
    # ③ gate 委托：有 GateReport 时记录其 fail 项为证据维 blocker（引用不重算）
    if gate_report is not None:
        for f in gate_report.findings:
            if f.severity == "fail":
                out.append(_finding(
                    "evidence", "fail", "claim", "",
                    f"[evidence-gate {f.code}] {f.message}",
                    artifact_refs=list(f.artifacts), check_id=f"EQ-gate-{f.code}",
                    recommended_action="rebuild_evidence"))
    return out


# ============================================================
# Q5 Claim Quality（六问的确定性子集）
# ============================================================

def claim_quality(registry, graph, gate_report=None) -> list[QualityFinding]:
    out = []
    claims = _active(registry, "claim")
    edges = _edges(graph)
    for c in claims:
        cid = c.artifact_id
        # What: statement 存在
        if not (c.data.get("statement") or c.title or "").strip():
            out.append(_finding("evidence", "fail", "claim", cid,
                                "claim 无主张内容（What 缺失）",
                                artifact_refs=[cid], check_id="CQ-what"))
        # Based on: 支撑存在（gate E2 提供时跳过）
        if gate_report is None:
            if not any(r == "supports" and t == cid for _, r, t in edges):
                out.append(_finding("evidence", "fail", "claim", cid,
                                    "claim 无 supports 证据（Based on 缺失）",
                                    artifact_refs=[cid], check_id="CQ-based",
                                    recommended_action="rebuild_evidence"))
        # Reproducible: 支撑链可回放（result → experiment）
        for f, r, t in edges:
            if r == "supports" and t == cid:
                producer = next((ff for ff, r2, tt in edges
                                 if r2 == "produces" and tt == f), None)
                if producer is None:
                    out.append(_finding("evidence", "weak", "claim", cid,
                                        f"支撑 {f} 无产出实验（不可复现）",
                                        artifact_refs=[cid, f], check_id="CQ-repro",
                                        recommended_action="rebuild_evidence"))
        # Compared against: claim.data 里应有对照说明
        if not (c.data.get("compared_against") or c.data.get("baseline") or ""):
            out.append(_finding("evidence", "weak", "claim", cid,
                                "claim 未记录对照物（Compared against 缺失）",
                                artifact_refs=[cid], check_id="CQ-baseline"))
    return out


# ============================================================
# Q6 Innovation Validity（I1–I7 → 四态映射）
# ============================================================

def innovation_quality(registry, graph, plans=None) -> list[QualityFinding]:
    out = []
    plans = plans if plans is not None else [
        a for a in registry.list_by_type("decision")
        if "实验计划" in (a.title or "") and a.status == "active"]
    inno_entries = []
    for pa in plans:
        for e in (pa.data or {}).get("entries") or []:
            if str(e.get("purpose", "")).startswith("创新验证") \
                    or "innovation" in str(e.get("method", "")):
                inno_entries.append((pa, e))
    if not inno_entries:
        return out
    for pa, e in inno_entries:
        eid = e.get("experiment_id", "?")
        # I2 修改显式（hypothesis 说明了改动）
        if not (e.get("hypothesis") or "").strip():
            out.append(_finding("innovation", "fail", "innovation", eid,
                                f"{eid}: 创新修改未显式声明（I2）",
                                artifact_refs=[pa.artifact_id], check_id="I2",
                                recommended_action="refine_experiment_plan"))
        # I4 baseline
        if not (e.get("baseline") or "").strip():
            out.append(_finding("innovation", "fail", "innovation", eid,
                                f"{eid}: 创新无对照基线（I4）",
                                artifact_refs=[pa.artifact_id], check_id="I4",
                                recommended_action="refine_experiment_plan"))
        # I6 风险已评估
        if not (e.get("failure_detection") or "").strip():
            out.append(_finding("innovation", "weak", "innovation", eid,
                                f"{eid}: 创新失败风险未登记检测信号（I6）",
                                artifact_refs=[pa.artifact_id], check_id="I6"))
        # I3/I5: 改进测量——确定性运行无测量值 → UNKNOWN（hypothesis 语义）
        out.append(_finding(
            "innovation", "unknown", "innovation", eid,
            f"{eid}: 创新改进尚未测量（I3/I5）——证据落地前保持 hypothesis，"
            "不得进入 Research State 结论",
            artifact_refs=[pa.artifact_id], check_id="I3", status=UNKNOWN,
            recommended_action="rerun_experiment"))
    return out


# ============================================================
# Q7 Decision Validity（D1–D6；P9-8 核心不变量）
# ============================================================

def decision_quality(registry, graph, knowledge=None,
                     decisions=None) -> list[QualityFinding]:
    out = []
    if decisions is None:
        return out
    terminal = ("invalidated", "superseded", "deprecated")
    for d in decisions.decisions.values():
        did = d.decision_id
        if d.status != "active":
            continue
        # D1: 知识引用存在
        for ref in d.knowledge_refs:
            kid = ref.get("id", "")
            if knowledge is not None and kid not in knowledge.cards:
                out.append(_finding("decision", "fail", "decision", did,
                                    f"决策引用的 MethodCard 不存在: {kid}",
                                    decision_refs=[did], check_id="D1",
                                    knowledge_refs=[ref],
                                    recommended_action="review_decision"))
        # D2: 失败记忆引用存在
        for fid in d.failure_refs:
            if knowledge is not None and fid not in knowledge.failures:
                out.append(_finding("decision", "weak", "decision", did,
                                    f"决策引用的失败记忆不存在: {fid}",
                                    decision_refs=[did], check_id="D2"))
        # D3: required_validation 非空
        if not d.required_validation:
            out.append(_finding("decision", "weak", "decision", did,
                                "决策无 required_validation（验证要求未声明）",
                                decision_refs=[did], check_id="D3"))
        # D5: 分数拆解存在（防黑箱总分）
        if not d.score_breakdown:
            out.append(_finding("decision", "weak", "decision", did,
                                "决策无 score_breakdown（依据不可拆解）",
                                decision_refs=[did], check_id="D5"))
        # D4（核心不变量）：决策不得引用已失效事实作为当前依据
        dead_in_refs = [ref["id"] for ref in d.knowledge_refs
                        if knowledge is not None
                        and ref.get("id") in knowledge.cards
                        and knowledge.cards[ref["id"]].status == "deprecated"]
        if dead_in_refs:
            out.append(_finding("decision", "fail", "decision", did,
                                f"决策引用已废弃知识: {dead_in_refs}",
                                decision_refs=[did], check_id="D4",
                                recommended_action="review_decision"))
        # 决策所选方法链上的结果全部失效且无重建 → 决策依据已死
        qid = (d.question or "").split(" ")[0]
        results = [a for a in registry.list_by_type("result")
                   if a.question == qid]
        if results and all(a.status in terminal for a in results) \
                and d.status == "active":
            out.append(_finding("decision", "fail", "decision", did,
                                f"决策 {did} 的结果证据已全部失效"
                                "（不得作为当前依据，需 recompute）",
                                decision_refs=[did], check_id="D4",
                                artifact_refs=[a.artifact_id for a in results],
                                recommended_action="recompute"))
    return out


# ============================================================
# Q8 Reproducibility
# ============================================================

def reproducibility_quality(registry, graph) -> list[QualityFinding]:
    out = []
    for a in registry.all():
        if a.status in ("invalidated", "superseded", "deprecated"):
            continue
        if not (a.created_by or "").strip():
            out.append(_finding("reproducibility", "weak", "evidence",
                                a.artifact_id,
                                f"{a.artifact_id} 无 created_by 溯源"
                                "（不可复现）",
                                artifact_refs=[a.artifact_id],
                                check_id="R1"))
    # 图表归属
    edges = _edges(graph)
    for fig in _active(registry, "figure"):
        if not any(r == "visualized_by" and t == fig.artifact_id
                   for _, r, t in edges):
            out.append(_finding("reproducibility", "weak", "evidence",
                                fig.artifact_id,
                                f"{fig.artifact_id} 未被任何结果引用"
                                "（图表无来源归属）",
                                artifact_refs=[fig.artifact_id], check_id="R2"))
    return out
