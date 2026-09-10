#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-Question Context（P12-3-lite）—— 给 Agent 的统一跨问题上下文。

最小语义闭包（冻结，见 docs/architecture/CROSS_QUESTION_SYNTHESIS_CONTRACT.md）:

    Input:   Registry / EvidenceGraph / State / P12-1 dependencies / P12-2 relations
    Output:  CrossQuestionContext（派生对象）
    Properties:
        derived-only（每次从 State 重算）      deterministic（零 LLM、零随机）
        no persistence（不落盘、不写 State）    no artifact registration
        no invalidation propagation            no new ontology
        no LLM

它只是 Agent 的上下文压缩/汇总结果，不是新的科研实体体系：不新增 artifact
类型、不新增关系类型、不落盘、不参与失效传播。上游失效后的陈旧性通过
state_version 展示，重派生即更新（P12-7 不实现）。

准入门（P12-0 §3，三条件全部满足才得 supported/qualified，否则 hypothesis）:
    1. 显式依赖声明：P12-1 records 中存在连接两问题的依赖，且类型参与
       synthesis（P12-1 参与矩阵冻结：evidential/comparative/extension）;
    2. 组件 finding status ∈ {PASS, WEAK}（FAIL/UNKNOWN 不得进入组合）;
    3. 证据独立：两侧组合成员的支撑 result 集合不相交
       （P9 EQ-independence 跨问题扩展：同源不得因数量升级）。

定级（离散瓶颈规则，不实现连续加权）:
    全部成员 PASS           → supported
    存在 WEAK（瓶颈=最弱）   → qualified
    任一门未过               → hypothesis
    无任何准入组合           → 上下文块标注 synthesis: absent
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from modeling_harness.runtime.state.dependencies import DEPENDENCY_TYPES, PARTICIPATION
from modeling_harness.runtime.state.dependencies import dependency_records
from modeling_harness.runtime.state.relations import cross_relations


@dataclass
class Finding:
    """最小 Finding 表示（跨问题 synthesis 用）。"""
    finding_id: str
    type: str            # e.g. "conclusion", "extension", "comparison"
    status: str          # "PASS" | "WEAK" | "FAIL" | "UNKNOWN"
    statement: str
    supported_by: list[str] = field(default_factory=list)
    question: str = ""
    provenance: dict = field(default_factory=dict)


class FindingGraph:
    """从 Registry + EvidenceGraph 构建 finding 图（简化版）。"""

    def __init__(self, registry, graph):
        self.findings: list[Finding] = []
        for a in registry.list_by_type("finding"):
            self.findings.append(Finding(
                finding_id=a.artifact_id,
                type=a.payload[0] if a.payload else "unknown",
                status=a.status,
                statement=a.title,
                supported_by=[r.to_id for r in graph.in_edges(a.artifact_id)
                              if r.relation == "supported_by"],
                question=a.question or "",
                provenance=a.provenance or {},
            ))

    def by_question(self, qid: str) -> list[Finding]:
        return [f for f in self.findings if f.question == qid]

    def validated(self) -> list[Finding]:
        return [f for f in self.findings if f.status in ("PASS", "WEAK")]

    def as_dict(self) -> dict:
        return {"findings": [f.finding_id for f in self.findings]}

# 参与 synthesis 的依赖类型（由 P12-1 冻结参与矩阵派生，不在本层另立名单）
SYNTHESIS_DEPENDENCY_TYPES = tuple(
    t for t in DEPENDENCY_TYPES if PARTICIPATION[t]["synthesis"])

_ADMISSIBLE = ("PASS", "WEAK")
_LEVELS = ("supported", "qualified", "hypothesis")

_STATEMENT_BY_TYPE = {
    "evidential": "{tgt} 的结论建立在 {src} 的证据之上",
    "extension": "{tgt} 在 {src} 的发现基础上扩展",
    "comparative": "{src} 与 {tgt} 构成跨问题对照",
}


class ContextError(ValueError):
    """跨问题上下文构建非法（未知 question 等）。"""


@dataclass
class CrossQuestionContext:
    """一次重算得到的跨问题上下文（纯派生对象，不落盘）。"""

    question_ids: list[str]
    state_version: dict                  # {graph_version, dependency_records, cross_question_relations}
    per_question: dict[str, dict]        # {qid: {status, claims, findings}}
    dependencies: list[dict]             # 两端均在问题集内的 P12-1 records
    cross_relations: list[dict]          # 两端均在问题集内的 P12-2 records
    conclusions: list[dict] = field(default_factory=list)   # 准入（supported/qualified）
    hypotheses: list[dict] = field(default_factory=list)    # 未准入组合

    # ------------------------------------------------------------ 导出

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "question_ids", "state_version", "per_question", "dependencies",
            "cross_relations", "conclusions", "hypotheses")}

    def to_context_block(self) -> str:
        """渲染 markdown 上下文块（V3 执行会话直接消费）。"""
        sv = self.state_version
        lines = [
            "## 跨问题综合上下文（P12-3-lite · 派生式）",
            "",
            f"state_version: graph={sv['graph_version']} · "
            f"deps={sv['dependency_records']} · "
            f"relations={sv['cross_question_relations']}",
            "> 本块每次从 Registry/Graph/State 重算：不落盘、不注册 artifact、"
            "不参与失效传播；引用前请核对 state_version 是否新鲜。",
            "",
        ]
        for qid, q in self.per_question.items():
            lines.append(f"### {qid} · status={q['status']}")
            for f in q["findings"]:
                exp = f" ← {f['experiment']}" if f["experiment"] else ""
                lines.append(
                    f"- [{f['status']}][{f['type']}] {f['statement']}"
                    f"〔results: {', '.join(f['results']) or '—'}{exp}〕")
            if not q["findings"]:
                lines.append("- （无 finding）")
            lines.append("")

        lines.append("### 跨问题链路")
        if not self.dependencies and not self.cross_relations:
            lines.append("- （无显式跨问题依赖/关系）")
        for d in self.dependencies:
            lines.append(f"- 依赖: {d['source_question']} "
                         f"--{d['dependency_type']}--> {d['target_question']}"
                         f" — {d['reason']}")
        for r in self.cross_relations:
            lines.append(f"- 关系: {r['relation_id']} {r['relation_type']}"
                         f"（{r['source']} → {r['target']}）"
                         f" status={r['status']}")
        lines.append("")

        if self.conclusions:
            lines.append("### 结论（准入）")
            for c in self.conclusions:
                lim = "；".join(c["limitations"]) or "无"
                refs = ", ".join(f["key"] for f in c["finding_refs"])
                lines.append(
                    f"- [{c['level']}] {c['source_question']} → "
                    f"{c['target_question']}（{c['dependency_type']}）: "
                    f"{c['statement']}")
                lines.append(f"  依据 finding: {refs}；决策规则: "
                             f"discrete-bottleneck（瓶颈="
                             f"{c['decision_rule']['bottleneck']}）；局限: {lim}")
            lines.append("")
        else:
            lines.append("> synthesis: absent（无准入的跨问题组合；"
                         "以下仅为链路/假设，不得作为综合结论引用）")
            lines.append("")

        if self.hypotheses:
            lines.append("### 假设（未准入，引用须显式标注假设态）")
            for h in self.hypotheses:
                lines.append(f"- [hypothesis] {' × '.join(h['question_refs'])}"
                             f" — {h['reason']}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"


# ============================================================
# 构建（纯函数式：读 Registry/Graph/State，不写任何一处）
# ============================================================

def build_cross_question_context(registry, graph, state,
                                 question_ids=None) -> CrossQuestionContext:
    """从三件套重算跨问题上下文。question_ids 缺省 = Registry 全部 question。"""
    known = [a.artifact_id for a in registry.list_by_type("question")]
    qids = list(question_ids) if question_ids is not None else list(known)
    for q in qids:
        if q not in known:
            raise ContextError(f"question 不存在: {q!r}")

    fg = FindingGraph(registry, graph)
    qs = state.data["state"]["questions"]
    per_question = {
        qid: {
            "status": state.question_status(qid),
            "claims": list(qs.get(qid, {}).get("claims", [])),
            "findings": [_finding_ref(f) for f in fg.by_question(qid)],
        }
        for qid in qids
    }

    all_deps = dependency_records(state)
    all_rels = cross_relations(state)
    deps = [d for d in all_deps
            if d["source_question"] in qids and d["target_question"] in qids]
    rels = [r for r in all_rels
            if r["source_question"] in qids and r["target_question"] in qids]
    state_version = {
        "graph_version": int(getattr(graph, "graph_version", 0)),
        "dependency_records": len(all_deps),
        "cross_question_relations": len(all_rels),
    }

    conclusions: list[dict] = []
    hypotheses: list[dict] = []
    declared_pairs: set[frozenset] = set()
    for d in deps:
        src, tgt = d["source_question"], d["target_question"]
        declared_pairs.add(frozenset((src, tgt)))
        if d["dependency_type"] not in SYNTHESIS_DEPENDENCY_TYPES:
            hypotheses.append(_hypothesis(
                (src, tgt), state_version,
                f"依赖类型 {d['dependency_type']} 不参与 synthesis"
                "（P12-1 参与矩阵冻结）"))
            continue
        src_f = _candidates(fg, src)
        tgt_f = _candidates(fg, tgt)
        if not src_f or not tgt_f:
            hypotheses.append(_hypothesis(
                (src, tgt), state_version,
                "组合组件缺失：至少一侧无非 FAIL/UNKNOWN 的 finding 可组合"))
            continue
        if not _evidence_independent(src_f, tgt_f):
            hypotheses.append(_hypothesis(
                (src, tgt), state_version,
                "证据同源（共享支撑 result），不得因数量升级"
                "（P9 EQ-independence 跨问题扩展）"))
            continue
        conclusions.append(_conclusion(d, src_f, tgt_f, rels, state_version,
                                       qs))

    # 无依赖声明但结构上可比的 pair → hypothesis（P12-0 Q10）
    for a, b in combinations(qids, 2):
        if frozenset((a, b)) in declared_pairs:
            continue
        common = ({f.type for f in _candidates(fg, a)}
                  & {f.type for f in _candidates(fg, b)})
        if common:
            hypotheses.append(_hypothesis(
                (a, b), state_version,
                f"无显式依赖声明（结构上可比: 双方均有 "
                f"{'/'.join(sorted(common))} finding）"))

    return CrossQuestionContext(
        question_ids=qids, state_version=state_version,
        per_question=per_question, dependencies=deps,
        cross_relations=rels, conclusions=conclusions,
        hypotheses=hypotheses)


# ============================================================
# 内部：稳定引用 / 准入门 / 定级
# ============================================================

def _finding_key(f: Finding) -> str:
    """跨重建稳定键（finding_id 含 batch 序号，不跨重建稳定，不作引用）。"""
    return f"{f.type}:{'+'.join(f.supported_by)}"


def _finding_ref(f: Finding) -> dict:
    return {"finding_id": f.finding_id, "key": _finding_key(f),
            "type": f.type, "status": f.status, "statement": f.statement,
            "results": list(f.supported_by),
            "experiment": (f.provenance or {}).get("experiment", "")}


def _candidates(fg: FindingGraph, qid: str) -> list[Finding]:
    """门 2：状态可入组的 finding（FAIL/UNKNOWN 永不入组合）。"""
    return [f for f in fg.by_question(qid) if f.status in _ADMISSIBLE]


def _evidence_independent(src_f: list[Finding], tgt_f: list[Finding]) -> bool:
    """门 3：两侧支撑 result 集合不相交（同源不得因数量升级）。"""
    src_r = {r for f in src_f for r in f.supported_by}
    tgt_r = {r for f in tgt_f for r in f.supported_by}
    return not (src_r & tgt_r)


def _conclusion(dep: dict, src_f: list[Finding], tgt_f: list[Finding],
                rels: list[dict], state_version: dict, qs: dict) -> dict:
    src, tgt = dep["source_question"], dep["target_question"]
    members = src_f + tgt_f
    statuses = {f.status for f in members}
    bottleneck = "WEAK" if "WEAK" in statuses else "PASS"
    level = "supported" if bottleneck == "PASS" else "qualified"
    tmpl = _STATEMENT_BY_TYPE.get(
        dep["dependency_type"], "{src} 与 {tgt} 跨问题组合")
    stmt = (tmpl.format(src=src, tgt=tgt)
            + f"（{len(src_f)}+{len(tgt_f)} 条 finding 组合）")
    pair_rels = [r for r in rels
                 if {r["source_question"], r["target_question"]}
                 == {src, tgt}]
    limitations = [f"瓶颈 finding 状态 WEAK: {_finding_key(f)}"
                   for f in members if f.status == "WEAK"]
    return {
        "level": level,
        "source_question": src,
        "target_question": tgt,
        "dependency_type": dep["dependency_type"],
        "statement": stmt,
        "question_refs": [src, tgt],
        "finding_refs": [_finding_ref(f) for f in members],
        "claim_refs": sorted({c for q in (src, tgt)
                              for c in qs.get(q, {}).get("claims", [])}),
        "dependency_refs": [dict(dep)],
        "relations": [dict(r) for r in pair_rels],
        "decision_rule": {
            "rule": "discrete-bottleneck",
            "bottleneck": bottleneck,
            "admission": ["declared-dependency", "status-admissible",
                          "evidence-independent"],
        },
        "limitations": limitations,
        "state_version": dict(state_version),
    }


def _hypothesis(pair: tuple[str, str], state_version: dict,
                reason: str) -> dict:
    return {"level": "hypothesis", "question_refs": list(pair),
            "reason": reason, "state_version": dict(state_version)}
