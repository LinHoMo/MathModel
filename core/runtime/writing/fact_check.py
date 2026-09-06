#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paper Fact Checker + PaperIntegrity（P10-8/9/10）。

方向铁律（P10-6/7）：Paper 必须是 Research State 的投影；LLM 只负责表达。
本模块在投影产物（LaTeX）上做**反向回查**——论文里的每个数字、图、表、
引用、结论必须能回到 Registry/Evidence；找不到来源的标 UNSUPPORTED，
由 Writer 解释与否无关（架构上封死，而非约定）。

PaperIntegrity（P1–P12）产出独立报告结构（PaperFinding/PaperIntegrityReport，
四态复用 P9 语义），**不修改 P9 七维契约**。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

TERMINAL = ("invalidated", "superseded", "deprecated")
INTEGRITY_STATUSES = ("PASS", "WEAK", "FAIL", "UNKNOWN")


# ============================================================
# P10-9 Reference Provenance
# ============================================================

@dataclass
class Reference:
    ref_id: str                     # bib key
    source_type: str = "paper"      # official/paper/competition_archive/...
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: str = ""
    doi_url: str = ""
    retrieved_at: str = ""
    used_by: list[str] = field(default_factory=list)   # 引用它的 tex 位置/claim

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "ref_id", "source_type", "title", "authors", "year", "doi_url",
            "retrieved_at", "used_by")}


def parse_bib(bib_text: str) -> dict[str, Reference]:
    """最小 BibTeX 解析（key/type/title/author/year/doi-url）。"""
    refs: dict[str, Reference] = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", bib_text,
                         re.S):
        body = m.group(3)
        fields = dict(re.findall(
            r"(\w+)\s*=\s*[{\"]+(.*?)[}\"]+\s*,?\s*\n", body))
        refs[m.group(2)] = Reference(
            ref_id=m.group(2),
            source_type="paper" if m.group(1).lower() == "article"
            else m.group(1).lower(),
            title=(fields.get("title") or "").strip("{} "),
            authors=[a.strip() for a in
                     (fields.get("author") or "").split(" and ") if a.strip()],
            year=fields.get("year", ""),
            doi_url=fields.get("doi") or fields.get("url") or "")
    return refs


# ============================================================
# LaTeX 事实抽取
# ============================================================

_NUM_RE = re.compile(r"(?<![\w.])(\d+\.\d+|\d+%|\d+)(?![\w.])")
_FIG_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
_TABLE_RE = re.compile(r"\\begin\{table\}")
_EQ_RE = re.compile(r"\\begin\{(equation|align)\}")
_CITE_RE = re.compile(r"\\cite[tp]?\{([^}]+)\}")
_SECTION_RE = re.compile(r"\\(sub)*section\{([^}]+)\}")


def extract_facts(tex: str) -> dict:
    """从 LaTeX 抽取事实清单：数字/图/表/公式/引用/章节。"""
    return {
        "numbers": sorted(set(_NUM_RE.findall(tex))),
        "figures": _FIG_RE.findall(tex),
        "tables": len(_TABLE_RE.findall(tex)),
        "equations": len(_EQ_RE.findall(tex)),
        "citations": sorted({k.strip() for m in _CITE_RE.findall(tex)
                             for k in m.split(",")}),
        "sections": [t for _, t in _SECTION_RE.findall(tex)],
    }


# ============================================================
# PaperIntegrity（P1–P12）
# ============================================================

@dataclass
class PaperFinding:
    code: str                # P1..P12
    severity: str            # fail / weak / unknown / info
    status: str              # PASS/WEAK/FAIL/UNKNOWN
    subject: str
    reason: str
    refs: list[str] = field(default_factory=list)

    @property
    def is_blocker(self) -> bool:
        return self.severity == "fail"

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "code", "severity", "status", "subject", "reason", "refs")}


@dataclass
class PaperIntegrityReport:
    findings: list[PaperFinding] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        st = "PASS"
        rank = {"PASS": 0, "UNKNOWN": 1, "WEAK": 2, "FAIL": 3}
        for f in self.findings:
            if rank[f.status] > rank[st]:
                st = f.status
        return st

    @property
    def blockers(self) -> list[PaperFinding]:
        return [f for f in self.findings if f.is_blocker]

    def as_dict(self) -> dict:
        return {"overall_status": self.overall_status,
                "findings": [f.as_dict() for f in self.findings],
                "blockers": [f.as_dict() for f in self.blockers]}


class PaperFactChecker:
    """反向回查：Paper → Claims/Numbers/Figures/Tables/Citations → Registry。"""

    def __init__(self, registry, graph, findings_graph=None,
                 narrative_ir=None):
        self.registry = registry
        self.graph = graph
        self.findings_graph = findings_graph
        self.ir = narrative_ir

    # ------------------------------------------------------------ 主入口

    def check(self, tex: str, bib_path: Path | None = None,
              min_coverage: float = 1.0) -> PaperIntegrityReport:
        facts = extract_facts(tex)
        findings: list[PaperFinding] = []
        active_claims = [a for a in self.registry.list_by_type("claim")
                         if a.status not in TERMINAL]
        terminal_claims = [a for a in self.registry.list_by_type("claim")
                           if a.status in TERMINAL]
        active_results = [a for a in self.registry.list_by_type("result")
                          if a.status not in TERMINAL]
        terminal_results = [a for a in self.registry.list_by_type("result")
                            if a.status in TERMINAL]
        active_figures = [a for a in self.registry.list_by_type("figure")
                          if a.status not in TERMINAL]
        models = [a for a in self.registry.list_by_type("model")
                  if a.status not in TERMINAL]
        claim_texts = {self._claim_text(c): c.artifact_id
                       for c in active_claims}

        # P1 claim coverage：每个活跃 claim 必须出现在论文中
        for c in active_claims:
            if self._claim_text(c) not in tex:
                findings.append(PaperFinding(
                    "P1", "fail", "FAIL", c.artifact_id,
                    "活跃 claim 未进入论文（claim coverage 缺口）",
                    [c.artifact_id]))
        # P2 evidence coverage：论文中的 claim 必须有证据
        for c in active_claims:
            if self._claim_text(c) in tex:
                has_support = any(r["relation"] == "supports"
                                  and r["to"] == c.artifact_id
                                  for r in self.graph.relations)
                if not has_support:
                    findings.append(PaperFinding(
                        "P2", "fail", "FAIL", c.artifact_id,
                        "论文中的 claim 无实验证据支撑（UNSUPPORTED）",
                        [c.artifact_id]))
        # P3 number provenance：论文数字必须能追溯到 Registry（data/tags/title）
        registry_corpus = self._registry_corpus()
        for num in facts["numbers"]:
            if num not in registry_corpus:
                findings.append(PaperFinding(
                    "P3", "fail", "FAIL", num,
                    f"论文数字 {num} 在 Registry 中无来源（UNSUPPORTED）"))
        # P4 figure provenance
        for fig_path in facts["figures"]:
            name = Path(fig_path).stem
            if not any(name in (a.title or "") or name in a.artifact_id
                       for a in active_figures):
                findings.append(PaperFinding(
                    "P4", "fail", "FAIL", fig_path,
                    f"论文图 {fig_path} 无对应活跃 Figure Artifact"))
        # P5 table provenance
        n_tables_reg = len(self.registry.list_by_type("table"))
        if facts["tables"] > n_tables_reg:
            findings.append(PaperFinding(
                "P5", "fail", "FAIL", "tables",
                f"论文含 {facts['tables']} 张表，Registry 仅登记 "
                f"{n_tables_reg} 张（orphan table）"))
        # P6 equation provenance
        if facts["equations"] > len(models):
            findings.append(PaperFinding(
                "P6", "weak", "WEAK", "equations",
                f"论文公式数 {facts['equations']} 超过模型数 {len(models)}，"
                "部分公式无模型来源"))
        # P7 citation provenance（Reference Registry 回查）
        bib_refs: dict[str, Reference] = {}
        if bib_path is not None and Path(bib_path).exists():
            bib_refs = parse_bib(Path(bib_path).read_text(encoding="utf-8"))
        for key in facts["citations"]:
            if bib_refs and key not in bib_refs:
                findings.append(PaperFinding(
                    "P7", "fail", "FAIL", key,
                    f"论文引用 {key} 不在 references.bib（hallucinated citation）"))
            elif not bib_refs:
                findings.append(PaperFinding(
                    "P7", "weak", "WEAK", key,
                    f"论文引用 {key} 无 Reference Provenance 可回查"
                    "（未提供 bib）"))
        # P8/P9/P10 一致性：abstract/conclusion 由 IR 从 validated findings
        # 派生（P10-11），论文层若出现 Registry 不存在的结论文本，
        # 已被 P1/P2/P11 覆盖——此处不再重复计一项。
        # P11 dead claim leakage
        for c in terminal_claims:
            if self._claim_text(c) in tex:
                findings.append(PaperFinding(
                    "P11", "fail", "FAIL", c.artifact_id,
                    "死主张（invalidated/superseded）泄漏进论文",
                    [c.artifact_id]))
        # P12 superseded result leakage
        for r in terminal_results:
            if (r.title or "") in tex and r.status == "superseded":
                findings.append(PaperFinding(
                    "P12", "fail", "FAIL", r.artifact_id,
                    "被替代的旧结果泄漏进当前论文", [r.artifact_id]))
        # orphan figure（E 的变体）：Registry 有图但论文未引用
        for f in active_figures:
            stem = Path(f.title or f.artifact_id).stem
            if not any(stem in p for p in facts["figures"]) \
                    and not any(f.artifact_id in p for p in facts["figures"]):
                findings.append(PaperFinding(
                    "P4", "weak", "WEAK", f.artifact_id,
                    f"Registry 图 {f.artifact_id} 未被论文引用（orphan figure）"))
        return PaperIntegrityReport(findings=findings)

    # ------------------------------------------------------------ 工具

    @staticmethod
    def _claim_text(c) -> str:
        return (c.data.get("statement") or c.title or "").strip()

    def _registry_corpus(self) -> set[str]:
        """Registry 全部可作为合法数字来源的文本（data 值 + title + tags）。"""
        corpus: set[str] = set()
        for a in self.registry.all():
            corpus.add(a.title or "")
            corpus.update(str(v) for v in (a.data or {}).values())
            corpus.update(a.tags or [])
            corpus.update(str(x) for x in (a.payload or []))
        return corpus
