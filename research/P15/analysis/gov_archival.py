# -*- coding: utf-8 -*-
"""治理修复：历史规划/报告文档加 archival 横幅（正文不动，保持历史快照诚实性）。

适用：引用路径已迁移/失效、内容已被新架构取代的历史文档。
"""
from pathlib import Path

ROOT = Path(".").resolve()
BANNER = (
    "<!-- ARCHIVAL-NOTE\n"
    "本文件为历史规划/报告快照（撰写时的真实状态），部分内部路径与术语已被后续"
    "架构演进取代（如 src/modeling_harness/cli/evaluation/ 已迁至 src/modeling_harness/cli/、V2 agent 目录已"
    "重组为 V3 roles）。当前权威口径以 AGENTS.md 与 docs/architecture/"
    "HARDENING_PROGRAM.md 为准；历史文档仅作溯源，不作为实现依据。\n"
    "ARCHIVAL-NOTE -->\n"
)

TARGETS = [
    "docs/architecture/V3_ARCHITECTURE_PLAN.md",
    "docs/architecture/V3_MIGRATION_MAP.md",
    "docs/architecture/V3_BASELINE_AUDIT.md",
    "docs/architecture/V3_IMPLEMENTATION_REPORT.md",
    "docs/architecture/V3_RED_TEAM_REPORT.md",
    "docs/architecture/V3_FINAL_AUDIT.md",
    "docs/architecture/IMPROVEMENT_PLAN.md",
    "docs/architecture/P13_3D_REPORT.md",
    "docs/architecture/P13_3_REPORT.md",
    "docs/architecture/P13_3C_REPORT.md",
    "docs/architecture/P13_3D_R2_PREREG.md",
    "docs/architecture/P13_3D_R3_PREREG.md",
    "docs/architecture/R3_1_CALIBRATION_REPORT.md",
    "docs/architecture/R3_2_REAL_WRITER_PREREG.md",
    "docs/architecture/R3_WRITER_PROTOCOL.md",
    "docs/architecture/R3_W0_PROMPT_TEMPLATE.md",
    "docs/architecture/R3_W1_PROMPT_TEMPLATE.md",
    "docs/decisions/2026-09-04-refactor-plan-v2.md",
    "docs/architecture/COMPETITION_INTELLIGENCE_AUDIT.md",
    "docs/architecture/PAPER_INTELLIGENCE_AUDIT.md",
    "docs/architecture/SCIENTIFIC_WRITING_AUDIT.md",
    "docs/architecture/RESEARCH_QUALITY_AUDIT.md",
    "docs/architecture/BASELINE_REPORT.md",
]

n = 0
for rel in TARGETS:
    p = ROOT / rel
    if not p.exists():
        print(f"  [SKIP] {rel} (not found)")
        continue
    t = p.read_text(encoding="utf-8")
    if "ARCHIVAL-NOTE" in t:
        print(f"  [SKIP] {rel} (already annotated)")
        continue
    # 在第一个标题/正文前插入；若以 YAML front-matter 开头则插在其后
    if t.startswith("---"):
        parts = t.split("---", 2)
        if len(parts) == 3:
            t = parts[0] + "---" + parts[1] + "---\n" + BANNER + parts[2].lstrip("\n")
        else:
            t = BANNER + t
    else:
        t = BANNER + t
    p.write_text(t, encoding="utf-8")
    n += 1
    print(f"  [OK] {rel}")
print(f"\ntotal annotated: {n}")
