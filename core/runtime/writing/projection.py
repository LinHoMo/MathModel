# -*- coding: utf-8 -*-
"""PaperProjection — 叙事 + 证据图 → 论文大纲投影（V3 P4 / P3-3）。

大纲是结构化的（机器可读），不是散文：
    sections: 每章的 claims / figures / tables / evidence / models 归属
    claim → section 通过 appears_in 边回写 Evidence Graph（未回写的 claim
    在大纲中标记 pending_placement，由 narrative-critic 拦截）

P3-3（2026-09-10）：统一到 ScientificNarrative IR（.sections/.coverage/
.reasoning_edges）。本版完全机械派生：
- models 输出 {model, question, assumptions}（graph assumes 边 + registry）
- dead claim（registry 终态或死证据支撑）从投影排除并记入 dead_claims_excluded
- 灵敏度与稳健性章节 evidence = tags 含 sensitivity/baseline 的 active result
- 章节表 6 节（问题重述 / 模型建立 / 实验设计 / 结果 / 灵敏度 / 结论，
  discussion 并入结论）
"""

from __future__ import annotations

SECTION_ORDER = ("问题重述与分析", "模型建立", "实验设计", "结果与分析",
                 "灵敏度与稳健性", "结论")

_PURPOSE_TITLE = {
    "problem_definition": "问题重述与分析",
    "methodology": "模型建立",
    "experiment": "实验设计",
    "results": "结果与分析",
    "discussion": "结论",
    "conclusion": "结论",
}

_TERMINAL = {"dead", "invalidated", "superseded", "archived"}


class PaperProjection:
    def __init__(self, registry, graph):
        self.registry = registry
        self.graph = graph

    def _is_dead(self, artifact_id: str) -> bool:
        art = self.registry.get(artifact_id)
        if art is None:
            return True
        if art.status in _TERMINAL:
            return True
        for e in self.graph.in_edges(artifact_id):
            if e["relation"] == "supports" and self._is_dead(e["from"]):
                return True
        return False

    def _claim_entry(self, claim_id) -> dict:
        if isinstance(claim_id, dict):
            return claim_id
        art = self.registry.get(claim_id)
        data = art.data if art is not None else {}
        supported = any(e["relation"] == "supports" and e["to"] == claim_id
                        for e in self.graph.relations)
        ev_ids = [e["from"] for e in self.graph.in_edges(claim_id)
                  if e["relation"] == "supports"]
        figures = sorted(
            a.artifact_id for a in self.registry.all()
            if getattr(a, "type", None) == "figure"
            and any(e["relation"] == "visualized_by"
                    and e["from"] in ev_ids and e["to"] == a.artifact_id
                    for e in self.graph.relations))
        return {
            "claim": claim_id,
            "statement": (data.get("statement") or data.get("text") or ""),
            "supported": supported,
            "placement": [],
            "figures": figures,
        }

    def _model_entry(self, model_id: str) -> dict:
        art = self.registry.get(model_id)
        assumptions = sorted(
            e["to"] for e in self.graph.out_edges(model_id)
            if e["relation"] == "assumes")
        return {
            "model": model_id,
            "question": art.question if art is not None else "",
            "assumptions": assumptions,
        }

    def _sensitivity_evidence(self) -> list:
        return sorted(
            a.artifact_id for a in self.registry.list_by_type("result")
            if a.status not in _TERMINAL
            and any(t in ("sensitivity", "baseline")
                    for t in (a.tags or [])))

    def project(self, narrative) -> dict:
        sections: list[dict] = []
        seen: dict[str, dict] = {}

        for sec in narrative.sections:
            title = _PURPOSE_TITLE.get(sec.purpose, sec.title or sec.purpose)
            bucket = seen.setdefault(title, {
                "section": title, "claims": [], "figures": [],
                "tables": [], "equations": [], "evidence": [],
                "models": [], "purpose": sec.purpose,
            })
            bucket["claims"] += list(sec.claims)
            bucket["figures"] += list(sec.figures)
            bucket["tables"] += list(sec.tables)
            bucket["equations"] += list(sec.equations)
            bucket["evidence"] += list(sec.evidence)
            bucket["models"] += list(sec.models)

        for title in SECTION_ORDER:
            sections.append(seen.pop(title, {
                "section": title, "claims": [], "figures": [],
                "tables": [], "equations": [], "evidence": [],
                "models": [], "purpose": "empty",
            }))
        sections += list(seen.values())

        for b in sections:
            for k in ("figures", "tables", "equations", "evidence", "models"):
                b[k] = sorted(set(b[k]))
            b["claims"] = [self._claim_entry(c) for c in
                           sorted(set(b["claims"]))]

        claim_entries = [c for b in sections for c in b["claims"]]
        placed_ids = {c["claim"] for c in claim_entries
                      if any(e["relation"] == "appears_in"
                             and e["from"] == c["claim"]
                             for e in self.graph.relations)}
        for c in claim_entries:
            c["placement"] = sorted(
                e["to"] for e in self.graph.out_edges(c["claim"])
                if e["relation"] == "appears_in")

        sens = next((s for s in sections
                     if s["section"] == "灵敏度与稳健性"), None)
        if sens is not None:
            sens["evidence"] = self._sensitivity_evidence()

        for b in sections:
            if b["section"] == "模型建立":
                b["models"] = [self._model_entry(m)
                               for m in sorted(set(b["models"]))]

        dead_ids = sorted({c["claim"] for c in claim_entries
                          if self._is_dead(c["claim"])})
        alive = [c for c in claim_entries if c["claim"] not in dead_ids]
        for b in sections:
            b["claims"] = [c for c in b["claims"]
                           if c["claim"] not in dead_ids]

        outline = {
            "problem": getattr(narrative, "title", "") or "",
            "sections": sections,
            "coverage": getattr(narrative, "coverage", {}),
            "pending_placement": sorted(
                {c["claim"] for c in alive} - placed_ids),
            "dead_claims_excluded": sorted(dead_ids),
        }
        return outline
