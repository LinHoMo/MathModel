"""NarrativeCritic — 叙事一致性批判（V3 P4，V2 scorer-reader 的升级）。

检查叙事与投影的一致性（判定而非分数）:
    N1  无 claim                      → FAIL（没有故事可讲）
    N2  死主张出现在叙事中             → FAIL（失效传播后未清理叙事）
    N3  无支撑主张进入结果章节         → FAIL（弱证据强叙事）
    N4  claim 无章节归属（pending）    → FAIL（主张悬空）
    N5  结果章节无任何 claim           → FAIL（有结果无主张 = 论文空转）
    N6  灵敏度章节无证据               → WEAK
    N7  图未归属任何主张               → WEAK
"""

from __future__ import annotations

from dataclasses import dataclass, field

# severity 统一小写（与 evidence_gate 一致，供 judge_critic 聚合排序）
SEV_FAIL = "fail"
SEV_WEAK = "weak"


@dataclass
class NFinding:
    code: str
    severity: str
    message: str
    items: list[str] = field(default_factory=list)


@dataclass
class NarrativeReport:
    verdict: str          # PASS / FAIL
    findings: list[NFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"

    def summary(self) -> str:
        out = f"[narrative-critic] {self.verdict}"
        for f in self.findings:
            out += f"\n  [{f.code}/{f.severity}] {f.message}"
            if f.items:
                out += f" → {', '.join(f.items)}"
        return out


class NarrativeCritic:
    def evaluate(self, narrative, outline) -> NarrativeReport:
        findings: list[NFinding] = []

        # N1
        if not narrative.arcs:
            return NarrativeReport("FAIL", [NFinding(
                "N1", SEV_FAIL, "无任何 claim：没有故事可讲")])

        # N2: 死主张未从叙事剔除 —— 判定口径是"仍被投影"：
        # director 保留死弧供审计（dead_arcs 可见），但投影必须排除它；
        # 死主张出现在结果章节 = 剔除失败（弱证据强叙事）
        dead = [a.claim_id for a in narrative.dead_arcs]
        if dead:
            result_section = next(
                (s for s in outline.get("sections", [])
                 if s.get("section") == "结果与分析"), {})
            placed = {c.get("claim") for c in result_section.get("claims", [])}
            leaked = [c for c in dead if c in placed]
            if leaked:
                findings.append(NFinding(
                    "N2", SEV_FAIL, "死主张未从叙事剔除（仍在结果章节投影中）",
                    leaked))

        # N3: 无支撑主张出现在结果章节投影中
        result_section = next(
            (s for s in outline.get("sections", [])
             if s.get("section") == "结果与分析"), {})
        unsupported_in_results = [
            c["claim"] for c in result_section.get("claims", [])
            if not c.get("supported")]
        if unsupported_in_results:
            findings.append(NFinding(
                "N3", SEV_FAIL, "无支撑主张进入结果章节（弱证据强叙事）",
                unsupported_in_results))

        # N4
        pending = outline.get("pending_placement", [])
        if pending:
            findings.append(NFinding(
                "N4", SEV_FAIL, "claim 无章节归属（appears_in 未回写）", pending))

        # N5
        if not result_section.get("claims"):
            findings.append(NFinding(
                "N5", SEV_FAIL, "结果章节无任何 claim（有结果无主张）"))

        # N6
        sens = next(
            (s for s in outline.get("sections", [])
             if s.get("section") == "灵敏度与稳健性"), {})
        if not sens.get("evidence"):
            findings.append(NFinding(
                "N6", SEV_WEAK, "灵敏度章节无证据（tags 缺 sensitivity/baseline）"))

        # N7: 图未被任何主张闭包引用（孤儿图）
        claimed_figs = {f for c in result_section.get("claims", [])
                        for f in c.get("figures", [])}
        all_figs = set(result_section.get("figures", []))
        orphan_figs = sorted(all_figs - claimed_figs)
        if orphan_figs:
            findings.append(NFinding(
                "N7", SEV_WEAK, "图未归属任何主张", orphan_figs))

        verdict = "FAIL" if any(f.severity == SEV_FAIL for f in findings) else "PASS"
        return NarrativeReport(verdict, findings)
