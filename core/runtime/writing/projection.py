"""PaperProjection — 叙事 + 证据图 → 论文大纲投影（V3 P4）。

大纲是结构化的（机器可读），不是散文：
    sections: 每章的 claims / figures / tables 归属
    claim → section 通过 appears_in 边回写 Evidence Graph（未回写的 claim
    在大纲中标记 pending_placement，由 narrative-critic 拦截）
"""

from __future__ import annotations

SECTION_ORDER = ("问题重述与分析", "模型建立", "结果与分析", "灵敏度与稳健性", "结论")


class PaperProjection:
    def __init__(self, registry, graph):
        self.registry = registry
        self.graph = graph

    def project(self, narrative) -> dict:
        """从 Narrative 投影论文大纲。"""
        sections: list[dict] = []

        # 1) 问题重述与分析：全部 Question
        sections.append({
            "section": "问题重述与分析",
            "questions": [q["id"] for q in narrative.questions],
            "claims": [],
            "figures": [],
        })

        # 2) 模型建立：按 Question 的 models（含假设）
        model_claims = []
        for q in narrative.questions:
            for mid in q["models"]:
                assumptions = sorted(
                    e["to"] for e in self.graph.out_edges(mid)
                    if e["relation"] == "assumes")
                model_claims.append({"model": mid, "question": q["id"],
                                     "assumptions": assumptions})
        sections.append({"section": "模型建立", "models": model_claims,
                         "claims": [], "figures": []})

        # 3) 结果与分析：每个 supported claim 一节内容 + 支撑图表
        result_claims = []
        for arc in narrative.arcs:
            if arc.status == "dead":
                continue          # 死主张不得投影
            placement = sorted(
                e["to"] for e in self.graph.out_edges(arc.claim_id)
                if e["relation"] == "appears_in")
            figures = self._figures_for(arc)
            result_claims.append({
                "claim": arc.claim_id,
                "statement": arc.statement,
                "placement": placement,
                "figures": figures,
                "supported": arc.status == "supported",
            })
        sections.append({"section": "结果与分析", "claims": result_claims,
                         "figures": sorted({f for c in result_claims
                                            for f in c["figures"]})})

        # 4) 灵敏度与稳健性：tags 检索
        tagged = [a.artifact_id for a in self.registry.artifacts.values()
                  if a.tags and any(t in ("sensitivity", "baseline")
                                    for t in a.tags)]
        sections.append({"section": "灵敏度与稳健性", "evidence": tagged,
                         "claims": [], "figures": []})

        # 5) 结论：全部 supported 主张的汇总
        sections.append({
            "section": "结论",
            "claims": [a.claim_id for a in narrative.supported_arcs],
            "figures": [],
        })

        outline = {
            "problem": narrative.problem,
            "sections": sections,
            "coverage": narrative.coverage,
            "pending_placement": [
                a.claim_id for a in narrative.arcs
                if not any(e["relation"] == "appears_in"
                           and e["from"] == a.claim_id
                           for e in self.graph.relations)],
            "dead_claims_excluded": [a.claim_id for a in narrative.dead_arcs],
        }
        return outline

    def _figures_for(self, arc) -> list[str]:
        """主张证据闭包中的 figure artifacts。"""
        out = []
        for aid in arc.evidence_ids:
            a = self.registry.artifacts.get(aid)
            if a is not None and a.type == "figure":
                out.append(aid)
        return sorted(out)
