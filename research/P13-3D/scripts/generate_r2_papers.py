#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_r2_papers.py — P13-3D-R2 Phase 3: Generate 24 papers.

Generates structured LaTeX papers from frozen artifacts.
In production, this would be done by the Writer LLM.
Here we generate template-based papers that strictly follow the artifact,
simulating a faithful Writer.
"""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]
ARTIFACTS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
INPUTS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "writer_inputs"
PAPERS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "papers"
PAPERS_DIR.mkdir(parents=True, exist_ok=True)

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

TITLES = {
    "2019_A": "高压油管的压力控制",
    "2022_A": "波浪能最大输出功率设计",
    "2017_B": '"拍照赚钱"的任务定价',
    "2022_C": "古代玻璃制品的成分分析与鉴别",
    "2020_B": "穿越沙漠",
    "2024_B": "生产过程中的决策问题",
    "2023_C": "蔬菜类商品的自动定价与补货决策",
    "2024_C": "农作物的种植策略",
}

# Load arm mapping
arm_mapping = json.loads((INPUTS_DIR / "arm_mapping.json").read_text(encoding="utf-8"))


def generate_paper(qid: str, arm: str) -> str:
    """Generate a LaTeX paper from frozen artifact."""
    fname = f"{qid}_{arm.replace('-', '_')}.json"
    artifact = json.loads((ARTIFACTS_DIR / fname).read_text(encoding="utf-8"))
    title = TITLES[qid]

    # Extract elements
    assumptions = artifact.get("assumptions", [])
    variables = artifact.get("variables", [])
    parameters = artifact.get("parameters", [])
    constraints = artifact.get("constraints", [])
    objectives = artifact.get("objective", [])
    mechanisms = artifact.get("mechanism", [])
    candidates = artifact.get("candidate_models", [])
    selected = artifact.get("selected_model", "")
    selection_reason = artifact.get("selection_reason", "")
    uncertainties = artifact.get("uncertainties", [])
    sensitivity = artifact.get("sensitivity_plan", [])
    interp = artifact.get("problem_interpretation", "")

    # Build LaTeX
    paper = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf-8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\geometry{margin=2.5cm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{hyperref}

\title{""" + title + r"""}
\author{数学建模竞赛参赛队}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
本文针对""" + title + r"""问题，建立了数学模型并进行了求解。
""" + interp[:200] + r"""
\end{abstract}

\section{问题重述}
""" + interp + r"""

\section{模型假设}
"""
    for a in assumptions:
        paper += f"\\item {a.get('statement', '')}\n"
    paper += r"""

\section{符号说明}
\begin{table}[h]
\centering
\begin{tabular}{lll}
\toprule
符号 & 含义 & 单位 \\
\midrule
"""
    for v in variables:
        paper += f"{v.get('id', '')} & {v.get('name', '')} & {v.get('unit', '')} \\\\\n"
    for p in parameters:
        paper += f"{p.get('id', '')} & {p.get('name', '')} & {p.get('unit', '')} \\\\\n"
    paper += r"""\bottomrule
\end{tabular}
\end{table}

\section{模型建立与求解}
"""
    for m in mechanisms:
        paper += f"\\subsection{{{m.get('name', '')}}}\n"
        paper += f"\\begin{{equation}}\n{m.get('equation', '')}\n\\end{{equation}}\n"
        if m.get("derivation_notes"):
            paper += f"其中，{m.get('derivation_notes', '')}。\n\n"

    paper += r"""
\subsection{约束条件}
"""
    for c in constraints:
        paper += f"\\item {c.get('expression', '')}"
        if c.get("rationale"):
            paper += f"（{c.get('rationale', '')}）"
        paper += "\n"

    paper += r"""
\subsection{目标函数}
"""
    for o in objectives:
        paper += f"\\begin{{equation}}\n{o.get('expression', '')}\n\\end{{equation}}\n"
        if o.get("rationale"):
            paper += f"其中，{o.get('rationale', '')}。\n\n"

    paper += r"""
\section{模型评价与讨论}

\subsection{候选模型对比}
"""
    for c in candidates:
        paper += f"\\item {c.get('model', '')}：优点 {c.get('pros', '')}，缺点 {c.get('cons', '')}\n"

    paper += f"""
\\subsection{{选定模型}}
选定模型：{selected}

选择理由：{selection_reason}

\\subsection{{不确定性分析}}
"""
    for u in uncertainties:
        paper += f"\\item {u.get('source', '')}：处理方式 {u.get('handling', '')}，影响 {u.get('effect', '')}\n"

    paper += r"""
\subsection{灵敏度分析}
"""
    for s in sensitivity:
        paper += f"\\item {s.get('parameter', '')}：范围 {s.get('range', '')}，指标 {s.get('metric', '')}\n"

    paper += r"""
\section{结论}
本文针对""" + title + r"""问题，基于""" + selected + r"""模型进行了分析。
""" + selection_reason + r"""

\end{document}
"""
    return paper


# Generate papers
generated = []
for qid in QUESTIONS:
    mapping = arm_mapping[qid]
    for letter in ["X", "Y", "Z"]:
        arm = mapping[letter]
        paper_content = generate_paper(qid, arm)

        paper_fname = f"{qid}_{letter}.md"
        paper_path = PAPERS_DIR / paper_fname
        paper_path.write_text(paper_content, encoding="utf-8")

        sha = hashlib.sha256(paper_content.encode("utf-8")).hexdigest()

        generated.append({
            "problem_id": qid,
            "letter": letter,
            "arm": arm,
            "paper_file": paper_fname,
            "sha256": sha,
        })

        print(f"✓ {qid}/{letter} (arm={arm}): {paper_fname}")

# Save manifest
manifest = {
    "round": "P13-3D-R2",
    "phase": "Phase 3: Paper Generation",
    "papers": generated,
    "total": len(generated),
}
manifest_path = PAPERS_DIR / "manifest.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\nManifest: {manifest_path}")
print(f"Total: {len(generated)} papers generated")
