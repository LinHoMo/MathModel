"""JudgeCritic — 评委视角终审（V3 P4，V2 scorer-judge 的升级）。

关键升级: 输出**判定**（PASS / WEAK / FAIL / UNKNOWN）而非分数。
- UNKNOWN: 信息不足以判定（无 claim / 无章节投影 / 证据门禁无法评估）
- FAIL:    证据门禁或叙事批判 FAIL（硬伤，评委必扣）
- WEAK:    无硬伤但有 weak 项（覆盖率不足 / 缺灵敏度）
- PASS:    证据完整 + 叙事一致

判定聚合自 evidence_gate 与 narrative_critic（异构验证），另附评委
风险清单（按严重度排序），供 paper_review 反馈环消费。
"""

from __future__ import annotations

from dataclasses import dataclass, field

UNKNOWN = "UNKNOWN"
WEAK = "WEAK"
FAIL = "FAIL"
PASS = "PASS"


@dataclass
class Risk:
    source: str          # evidence-gate / narrative-critic
    code: str
    severity: str
    message: str


@dataclass
class JudgeReport:
    verdict: str
    risks: list[Risk] = field(default_factory=list)
    coverage: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.verdict == PASS

    def summary(self) -> str:
        out = f"[judge-critic] {self.verdict}"
        if self.coverage.get("claims_total"):
            out += (f"  claims {self.coverage.get('claims_supported')}/"
                    f"{self.coverage.get('claims_total')}")
        for r in self.risks:
            out += f"\n  [{r.source}/{r.code}/{r.severity}] {r.message}"
        return out


class JudgeCritic:
    def evaluate(self, narrative, outline,
                 evidence_report=None) -> JudgeReport:
        """
        narrative: ResearchDirector.build() 产物
        outline:   PaperProjection.project() 产物
        evidence_report: evidence_gate.evaluate() 产物（缺省则视为无法评估）
        """
        risks: list[Risk] = []

        # ---- 硬证据优先：证据门禁 FAIL 是确定性判定，不得被 UNKNOWN 掩盖
        #（全部 claim 失效时叙事为空，属"已判死"而非"信息不足"）
        if evidence_report is not None and evidence_report.verdict == FAIL:
            for f in evidence_report.findings:
                risks.append(Risk("evidence-gate", f.code, f.severity, f.message))
            from .narrative_critic import NarrativeCritic
            nar_report = NarrativeCritic().evaluate(narrative, outline)
            for f in nar_report.findings:
                risks.append(Risk("narrative-critic", f.code, f.severity, f.message))
            risks.sort(key=lambda r: (0 if r.severity == "fail" else 1,
                                      r.source, r.code))
            return JudgeReport(FAIL, risks, evidence_report.coverage)

        # ---- UNKNOWN 判定（信息不足，不得瞎判）
        if not narrative.arcs or not outline.get("sections"):
            return JudgeReport(UNKNOWN, risks, narrative.coverage)
        if evidence_report is None:
            return JudgeReport(UNKNOWN, risks, narrative.coverage)

        # ---- 聚合证据门禁发现
        for f in evidence_report.findings:
            risks.append(Risk("evidence-gate", f.code, f.severity, f.message))
        ev_fail = evidence_report.verdict == FAIL
        ev_weak = evidence_report.verdict == "WEAK"

        # ---- 聚合叙事批判发现（重跑轻量检查，不要求调用方先跑）
        from .narrative_critic import NarrativeCritic
        nar_report = NarrativeCritic().evaluate(narrative, outline)
        for f in nar_report.findings:
            risks.append(Risk("narrative-critic", f.code, f.severity, f.message))

        # ---- 判定
        if ev_fail or nar_report.verdict == FAIL:
            verdict = FAIL
        elif ev_weak or any(r.severity == "weak" for r in risks):
            verdict = WEAK
        else:
            verdict = PASS

        # 风险按严重度排序（fail 在前）
        risks.sort(key=lambda r: (0 if r.severity == "fail" else 1,
                                  r.source, r.code))
        return JudgeReport(verdict, risks, evidence_report.coverage)
