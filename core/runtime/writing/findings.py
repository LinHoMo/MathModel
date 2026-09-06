#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Finding Graph（P10-4/5）—— 把"结果"升级成"科学发现"。

Result:  模型 A 的 MAE = 0.123，模型 B 的 MAE = 0.151
Finding: 在对照基线下，模型 A 以 X% 的相对改进优于模型 B（依据 E001/E002，
         稳健性 Y，局限 Z）——凭什么，可回答。

设计裁决（P10-0）：Finding 是**派生层**（从 Registry+Graph 计算），不新增
artifact type（不触 P7 契约）；失效传播经由其引用的 result ids 自动生效——
引用死了，finding 状态即降级。状态复用 P9 四态（PASS/WEAK/FAIL/UNKNOWN），
不造第五种。
"""

from __future__ import annotations

from dataclasses import dataclass, field

FINDING_STATUSES = ("PASS", "WEAK", "FAIL", "UNKNOWN")
FINDING_TYPES = ("descriptive", "comparative", "robustness", "causal")

_SEQ = {"n": 0}


@dataclass
class Finding:
    """P10-5 Scientific Finding Contract。"""
    finding_id: str
    type: str                                  # FINDING_TYPES 之一
    statement: str                             # 结论性陈述（凭什么可答）
    supported_by: list[str] = field(default_factory=list)   # result ids
    comparison: dict = field(default_factory=dict)          # {baseline, candidate}
    robustness: str = ""                       # 稳健性证据描述
    limitations: list[str] = field(default_factory=list)
    confidence: float = 0.0                    # 0-1（派生自证据强度）
    status: str = "UNKNOWN"                    # PASS/WEAK/FAIL/UNKNOWN
    question: str = ""
    provenance: dict = field(default_factory=dict)          # {plan_ref, ...}

    def __post_init__(self):
        if self.type not in FINDING_TYPES:
            raise ValueError(f"finding.type 非法: {self.type!r}")
        if self.status not in FINDING_STATUSES:
            raise ValueError(f"finding.status 非法: {self.status!r}")

    def compares_with(self, other: "Finding") -> bool:
        return (self.type == "comparative" and other.type == "comparative"
                and self.question == other.question)

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "finding_id", "type", "statement", "supported_by", "comparison",
            "robustness", "limitations", "confidence", "status", "question",
            "provenance")}


class FindingGraph:
    """从 Registry+Graph 派生发现（每次构建都是最新的，随失效自动降级）。"""

    def __init__(self, registry, graph):
        self.registry = registry
        self.graph = graph
        self.findings: list[Finding] = self._derive()

    # ------------------------------------------------------------ 派生

    def _derive(self) -> list[Finding]:
        out: list[Finding] = []
        _SEQ["n"] += 1
        batch = _SEQ["n"]
        edges = [(e["from"], e["relation"], e["to"]) for e in self.graph.relations]
        active_results = [a for a in self.registry.list_by_type("result")
                          if a.status not in TERMINAL_]

        # 按问题聚合结果 → descriptive / comparative findings
        by_q: dict[str, list] = {}
        for r in active_results:
            by_q.setdefault(r.question, []).append(r)

        for qid, results in by_q.items():
            # descriptive：每个活跃结果是一条描述性发现
            for r in results:
                producer = next((f for f, rel, t in edges
                                 if rel == "produces" and t == r.artifact_id), None)
                robust = bool(r.tags)   # sensitivity/baseline 标签即稳健性证据
                out.append(Finding(
                    finding_id=f"FD{batch:03d}-D{r.artifact_id}",
                    type="descriptive",
                    statement=f"{qid} 的实验结果已获得（{r.title}）",
                    supported_by=[r.artifact_id],
                    robustness="含灵敏度/基线证据" if robust else "",
                    confidence=0.8 if robust else 0.5,
                    status="PASS" if (producer and robust) else
                           ("WEAK" if producer else "FAIL"),
                    question=qid,
                    provenance={"result": r.artifact_id,
                                "experiment": producer or ""}))
            # comparative：同问题多结果可比较时才产生；单结果 → UNKNOWN 占位
            if len(results) >= 2:
                a, b = results[0], results[1]
                out.append(Finding(
                    finding_id=f"FD{batch:03d}-C{qid}",
                    type="comparative",
                    statement=f"{qid}: {a.title} 与 {b.title} 的对比已具备测量前提",
                    supported_by=[a.artifact_id, b.artifact_id],
                    comparison={"candidate": a.artifact_id,
                                "baseline": b.artifact_id},
                    confidence=0.6, status="WEAK", question=qid))
            elif results:
                out.append(Finding(
                    finding_id=f"FD{batch:03d}-C{qid}",
                    type="comparative",
                    statement=f"{qid}: 尚无对照结果，比较型发现处于假设阶段",
                    supported_by=[results[0].artifact_id],
                    comparison={"candidate": results[0].artifact_id,
                                "baseline": ""},
                    confidence=0.2, status="UNKNOWN", question=qid))

        # 死引用 → FAIL（失效传播经由 supported_by 自动生效）
        for f in out:
            if f.status == "FAIL":
                continue
            dead = [rid for rid in f.supported_by
                    if self.registry.get(rid).status in TERMINAL_]
            if dead:
                f.status = "FAIL"
                f.limitations.append(f"支撑证据已失效: {dead}")
        return out

    # ------------------------------------------------------------ 查询

    def validated(self) -> list[Finding]:
        return [f for f in self.findings if f.status == "PASS"]

    def by_question(self, qid: str) -> list[Finding]:
        return [f for f in self.findings if f.question == qid]

    def as_dict(self) -> dict:
        return {"findings": [f.as_dict() for f in self.findings],
                "validated": [f.finding_id for f in self.validated()]}


TERMINAL_ = ("invalidated", "superseded", "deprecated")
