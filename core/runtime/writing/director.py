"""ResearchDirector — 从 Evidence Graph 提炼研究叙事（V3 P4）。

V3 倒置原则的落地点：论文不是流水线终点，而是 Research State 的投影。
本模块先把研究状态蒸馏成叙事（Story Arcs）：
    问题 → 子问题 → 主张（claim）→ 证据闭包 → 结论

每个 StoryArc = 一条可写进论文的主张 + 支撑它的全部证据 artifact 及其健康度。
下游 PaperProjection 消费 Narrative 生成大纲；narrative/judge critic 消费其
完整性指标。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StoryArc:
    claim_id: str
    statement: str                       # 主张文本（title 或 data.statement）
    question: str = ""                   # 所属 Q
    evidence_ids: list[str] = field(default_factory=list)   # 证据闭包
    dead_evidence: list[str] = field(default_factory=list)  # 已死证据
    status: str = "unsupported"          # supported / unsupported / dead


@dataclass
class Narrative:
    problem: str = ""
    questions: list[dict] = field(default_factory=list)   # [{id, models, claims}]
    arcs: list[StoryArc] = field(default_factory=list)
    coverage: dict = field(default_factory=dict)

    @property
    def supported_arcs(self) -> list[StoryArc]:
        return [a for a in self.arcs if a.status == "supported"]

    @property
    def unsupported(self) -> list[str]:
        return [a.claim_id for a in self.arcs if a.status == "unsupported"]

    @property
    def dead_arcs(self) -> list[StoryArc]:
        return [a for a in self.arcs if a.status == "dead"]


class ResearchDirector:
    def __init__(self, registry, graph):
        self.registry = registry
        self.graph = graph

    def build(self) -> Narrative:
        nar = Narrative(coverage=self.graph.coverage())

        # 问题与子问题
        problems = self.registry.list_by_type("problem")
        if problems:
            nar.problem = problems[0].title
        for q in self.registry.list_by_type("question"):
            models = sorted(
                e["to"] for e in self.graph.out_edges(q.artifact_id)
                if e["relation"] == "solved_by")
            claims = sorted(
                a.artifact_id for a in self.registry.list_by_type("claim")
                if a.question == q.artifact_id)
            nar.questions.append({"id": q.artifact_id, "models": models,
                                  "claims": claims})

        # 主张 → 证据闭包
        for claim in self.registry.list_by_type("claim"):
            arc = StoryArc(
                claim_id=claim.artifact_id,
                statement=claim.data.get("statement") or claim.title,
                question=claim.question,
                evidence_ids=sorted(self._closure(claim.artifact_id)),
            )
            supported = any(
                e["relation"] == "supports" and e["to"] == claim.artifact_id
                for e in self.graph.relations)
            dead = [aid for aid in arc.evidence_ids
                    if aid in self.registry.artifacts
                    and self.registry.artifacts[aid].status in
                    ("invalidated", "superseded", "deprecated")]
            arc.dead_evidence = dead
            if dead:
                arc.status = "dead"
            elif supported:
                arc.status = "supported"
            nar.arcs.append(arc)
        return nar

    def _closure(self, artifact_id: str) -> set[str]:
        seen: set[str] = set()
        frontier = [artifact_id]
        while frontier:
            cur = frontier.pop()
            for e in self.graph.relations_of(cur):
                other = e["to"] if e["from"] == cur else e["from"]
                if other not in seen:
                    seen.add(other)
                    frontier.append(other)
        return seen
