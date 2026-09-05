"""Evidence Gate — 证据门禁（V3 P3，evidence_gate 节点绑定 validator: evidence-gate）。

语义: 没有真实证据不允许进入论文投影。判 FAIL 触发反馈环回 experiment_design。

检查项（分级 fail / weak）:
    E1  无任何 claim                          → fail（论文无主张可支撑）
    E2  claim 无 supports 边                   → fail（主张无证据）
    E3  证据链含 invalidated/superseded 终态   → fail（证据已死）
    E4  实验无 produces 结果                   → fail（实验没跑出真东西）
    E5  结果无实验来源（produces 反向缺失）    → weak（来源待补）
    E6  证据链含 draft 状态                    → weak（证据未过验证）
    E7  claim 覆盖率 < min_coverage            → weak
    E8  无灵敏度/基线对比证据（tags 检索）     → weak

verdict: 任一 fail → FAIL；否则任一 weak → WEAK；否则 PASS。
"""

from __future__ import annotations

from dataclasses import dataclass, field

FAIL = "fail"
WEAK = "weak"
PASS = "PASS"
WEAK_VERDICT = "WEAK"
FAIL_VERDICT = "FAIL"

DEFAULT_MIN_COVERAGE = 0.8
_TERMINAL_STATUSES = ("invalidated", "superseded", "deprecated")
EVIDENCE_TAGS = ("sensitivity", "baseline")


def _evidence_closure(graph, artifact_id: str) -> set[str]:
    """双向遍历（in+out 边）可达的证据节点闭包（不含自身）。"""
    seen: set[str] = set()
    frontier = [artifact_id]
    while frontier:
        cur = frontier.pop()
        for e in graph.relations_of(cur):
            other = e["to"] if e["from"] == cur else e["from"]
            if other not in seen:
                seen.add(other)
                frontier.append(other)
    return seen


@dataclass
class Finding:
    code: str            # E1..E8
    severity: str        # "fail" | "weak"
    message: str
    artifacts: list[str] = field(default_factory=list)


@dataclass
class GateReport:
    verdict: str                     # PASS / WEAK / FAIL
    coverage: dict
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.verdict == PASS

    def summary(self) -> str:
        head = f"[evidence-gate] {self.verdict}"
        cov = self.coverage
        if cov.get("claims_total"):
            head += (f"  claims {cov.get('claims_supported')}/{cov.get('claims_total')}"
                     f" (coverage={cov.get('coverage_ratio')})")
        for f in self.findings:
            head += f"\n  [{f.code}/{f.severity}] {f.message}"
            if f.artifacts:
                head += f" → {', '.join(f.artifacts)}"
        return head

    def as_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "coverage": self.coverage,
            "findings": [
                {"code": f.code, "severity": f.severity, "message": f.message,
                 "artifacts": f.artifacts} for f in self.findings],
        }


def evaluate(registry, graph, min_coverage: float = DEFAULT_MIN_COVERAGE) -> GateReport:
    """评估项目证据质量。registry: ArtifactRegistry; graph: EvidenceGraph。"""
    findings: list[Finding] = []
    coverage = graph.coverage()

    # 双口径：E1/E2 清点"活跃 claim"（终态不计入，失效由 E3 报告）；
    # E3 的证据闭包排查必须走全部 claim（死 claim 的死链正是要抓的）
    all_claims = [a.artifact_id for a in registry.list_by_type("claim")]
    claims = [c for c in all_claims
              if registry.artifacts[c].status
              not in ("invalidated", "superseded", "deprecated")]

    # E1: 无活跃 claim（不提前返回——死 claim 的死链仍需 E3 报告）
    if not claims:
        findings.append(Finding(
            "E1", FAIL, "无任何活跃 claim：论文无主张可支撑，禁止进入论文投影"))

    # E2: 活跃 claim 无 supports 边
    unsupported = [c for c in claims if not any(
        e["relation"] == "supports" and e["to"] == c for e in graph.relations)]
    if unsupported:
        findings.append(Finding(
            "E2", FAIL, "claim 无实验支撑（无 supports 边）", unsupported))

    # E3/E6: 逐 claim 检查证据闭包生命周期
    # 闭包 = 双向遍历（in+out 边）可达的全部证据节点——数据死了（如 uses 出边
    # 指向的 DATA），即便不在 in-edge 链上也必须判死下游主张
    draft_in_chain: set[str] = set()
    dead_in_chain: set[str] = set()
    reval_in_chain: set[str] = set()
    for c in all_claims:
        for aid in _evidence_closure(graph, c):
            if aid not in registry.artifacts:
                continue
            a = registry.artifacts[aid]
            if a.status in ("invalidated", "superseded", "deprecated"):
                dead_in_chain.add(f"{aid}({a.status})支撑 {c}")
            elif a.status == "draft":
                draft_in_chain.add(f"{aid} 支撑 {c}")
            elif a.invalidation.get("status") in ("requires_revalidation", "dirty"):
                reval_in_chain.add(f"{aid}({a.invalidation['status']})支撑 {c}")
    if dead_in_chain:
        findings.append(Finding(
            "E3", FAIL, "证据链含失效/被替代 artifact", sorted(dead_in_chain)))
    if draft_in_chain:
        findings.append(Finding(
            "E6", WEAK, "证据链含 draft 状态 artifact（未过验证）",
            sorted(draft_in_chain)))
    if reval_in_chain:
        findings.append(Finding(
            "E6", WEAK, "证据链含需复查 artifact（invalidation 传播命中）",
            sorted(reval_in_chain)))

    # E4: 实验无结果产物（终态实验不计入——其 produces 边已随失效剪除）
    experiments = [a.artifact_id for a in registry.list_by_type("experiment")
                   if a.status not in _TERMINAL_STATUSES]
    barren = [e for e in experiments if not any(
        rel["relation"] == "produces" and rel["from"] == e
        for rel in graph.relations)]
    if barren:
        findings.append(Finding(
            "E4", FAIL, "实验无 produces 结果产物（实验没有真东西）", barren))

    # E5: 结果无实验来源（终态结果不计入）
    results = [a.artifact_id for a in registry.list_by_type("result")
               if a.status not in _TERMINAL_STATUSES]
    orphan = [r for r in results if not any(
        rel["relation"] == "produces" and rel["to"] == r
        for rel in graph.relations)]
    if orphan:
        findings.append(Finding(
            "E5", WEAK, "结果无实验来源（produces 反向缺失）", orphan))

    # E7: 覆盖率
    ratio = coverage.get("coverage_ratio")
    if ratio is not None and ratio < min_coverage:
        findings.append(Finding(
            "E7", WEAK,
            f"claim 覆盖率 {ratio} 低于阈值 {min_coverage}"))

    # E8: 灵敏度/基线证据
    tagged = [a.artifact_id for a in registry.artifacts.values()
              if a.tags and any(t in EVIDENCE_TAGS for t in a.tags)]
    if not tagged:
        findings.append(Finding(
            "E8", WEAK,
            "无灵敏度/基线对比证据（artifact tags 中无 sensitivity/baseline）"))

    if any(f.severity == FAIL for f in findings):
        verdict = FAIL_VERDICT
    elif findings:
        verdict = WEAK_VERDICT
    else:
        verdict = PASS
    return GateReport(verdict, coverage, findings)
