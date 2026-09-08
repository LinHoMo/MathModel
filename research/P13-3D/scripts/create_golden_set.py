#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""create_golden_set.py — Create Golden Set for STC Evaluator Calibration.

Creates 3 test papers with known STC labels:
1. Full Coverage: Paper covers all artifact elements
2. Partial Coverage: Paper missing meta-model elements (simulates R2 omission)
3. Mutation: Paper adds unauthorized elements

Each paper has a golden label dict: {element: 0 or 1}
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]
R2_ARTIFACTS = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
R3_GOLDEN = ROOT / "research" / "P13-3D-R3" / "golden_set"
R3_GOLDEN.mkdir(parents=True, exist_ok=True)

# Load artifact
artifact = json.loads((R2_ARTIFACTS / "2019_A_MMA.json").read_text(encoding="utf-8"))

# ═══════════════════════════════════════════════════════════════
# Paper 1: Full Coverage (all artifact elements present)
# ═══════════════════════════════════════════════════════════════

paper_full = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf-8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\geometry{margin=2.5cm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{hyperref}

\title{高压油管的压力控制}
\author{数学建模竞赛参赛队}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
本文针对高压油管的压力控制问题，建立了数学模型并进行了求解。
高压油管内燃油喷射的压力控制问题。通过凸轮驱动进油阀控制喷射规律，需要建立压力-流量耦合模型，分析压力波动规律并优化凸轮运动使压力稳定。
\end{abstract}

\section{问题重述}
高压油管内燃油喷射的压力控制问题。通过凸轮驱动进油阀控制喷射规律，需要建立压力-流量耦合模型，分析压力波动规律并优化凸轮运动使压力稳定。

\section{模型假设}
\item 燃油不可压缩，流动为准稳态
\item 喷嘴流量与压力平方根成正比
\item 燃油温度恒定，密度均匀

\section{符号说明}
\begin{table}[h]
\centering
\begin{tabular}{lll}
\toprule
符号 & 含义 & 单位 \\
\midrule
P & 油管内压力 & MPa \\
Q & 喷油流量 & mm³/s \\
x & 进油阀位移 & mm \\
p1 & 流量系数 Cd & 1 \\
p2 & 管路容积 V & mm³ \\
\bottomrule
\end{tabular}
\end{table}

\section{模型建立与求解}
\subsection{压力动态}
\begin{equation}
dP/dt = (E/V)·(Q_in - Q_out)
\end{equation}
其中，体积弹性模量 E，管路容积 V。

\subsection{进油流量}
\begin{equation}
Q_in = Cd·A_in·√(2(P_in-P)/ρ)
\end{equation}
其中，进油阀流量，P_in 为供油压力。

\subsection{喷嘴流量}
\begin{equation}
Q_out = Cd·A_out·√(2P/ρ)
\end{equation}
其中，伯努利方程。

\subsection{约束条件}
\item 0 ≤ x ≤ x_max（阀门行程有限）

\subsection{目标函数}
\begin{equation}
最小化压力波动幅值
\end{equation}
其中，压力稳定是喷射质量的关键。

\section{候选模型对比}
\item ODE + 伯努利：优点 物理可解释，缺点 参数少
\item CFD 数值模拟：优点 精度高，缺点 计算成本高

\section{选定模型}
选定模型：ODE + 伯努利方程

选择理由：题目要求分析压力变化规律，ODE 模型足够且可解释

\section{灵敏度分析}
\item 流量系数 Cd：范围 ±20%，指标 压力波动幅值
\item 凸轮转速：范围 ±10%，指标 压力稳定性

\section{结论}
本文针对高压油管的压力控制问题，基于ODE + 伯努利方程模型进行了分析。
题目要求分析压力变化规律，ODE 模型足够且可解释

\end{document}
"""

# Golden labels for Full Coverage
golden_full = {
    "variables": 1,      # Paper mentions P, Q, x
    "parameters": 1,     # Paper mentions Cd, V
    "mechanism": 1,      # Paper mentions dP/dt, Q_in, Q_out equations
    "objective": 1,      # Paper mentions "最小化压力波动幅值"
    "constraints": 1,    # Paper mentions "0 ≤ x ≤ x_max"
    "assumptions": 1,    # Paper mentions 3 assumptions
    "candidate_model": 1, # Paper mentions ODE+伯努利 and CFD
    "selected_model": 1,  # Paper mentions "ODE + 伯努利方程"
    "sensitivity_plan": 1, # Paper mentions Cd ±20% and 凸轮转速 ±10%
}

# ═══════════════════════════════════════════════════════════════
# Paper 2: Partial Coverage (missing meta-model elements)
# ═══════════════════════════════════════════════════════════════

paper_partial = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf-8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\geometry{margin=2.5cm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{hyperref}

\title{高压油管的压力控制}
\author{数学建模竞赛参赛队}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
本文针对高压油管的压力控制问题，建立了数学模型并进行了求解。
高压油管内燃油喷射的压力控制问题。通过凸轮驱动进油阀控制喷射规律，需要建立压力-流量耦合模型，分析压力波动规律并优化凸轮运动使压力稳定。
\end{abstract}

\section{问题重述}
高压油管内燃油喷射的压力控制问题。通过凸轮驱动进油阀控制喷射规律，需要建立压力-流量耦合模型，分析压力波动规律并优化凸轮运动使压力稳定。

\section{模型假设}
\item 燃油不可压缩，流动为准稳态
\item 喷嘴流量与压力平方根成正比
\item 燃油温度恒定，密度均匀

\section{符号说明}
\begin{table}[h]
\centering
\begin{tabular}{lll}
\toprule
符号 & 含义 & 单位 \\
\midrule
P & 油管内压力 & MPa \\
Q & 喷油流量 & mm³/s \\
x & 进油阀位移 & mm \\
p1 & 流量系数 Cd & 1 \\
p2 & 管路容积 V & mm³ \\
\bottomrule
\end{tabular}
\end{table}

\section{模型建立与求解}
\subsection{压力动态}
\begin{equation}
dP/dt = (E/V)·(Q_in - Q_out)
\end{equation}
其中，体积弹性模量 E，管路容积 V。

\subsection{进油流量}
\begin{equation}
Q_in = Cd·A_in·√(2(P_in-P)/ρ)
\end{equation}
其中，进油阀流量，P_in 为供油压力。

\subsection{喷嘴流量}
\begin{equation}
Q_out = Cd·A_out·√(2P/ρ)
\end{equation}
其中，伯努利方程。

\subsection{约束条件}
\item 0 ≤ x ≤ x_max（阀门行程有限）

\subsection{目标函数}
\begin{equation}
最小化压力波动幅值
\end{equation}
其中，压力稳定是喷射质量的关键。

\section{结论}
本文针对高压油管的压力控制问题，基于ODE + 伯努利方程模型进行了分析。
题目要求分析压力变化规律，ODE 模型足够且可解释

\end{document}
"""

# Golden labels for Partial Coverage (missing candidate_model, selected_model, sensitivity_plan)
golden_partial = {
    "variables": 1,      # Paper mentions P, Q, x
    "parameters": 1,     # Paper mentions Cd, V
    "mechanism": 1,      # Paper mentions dP/dt, Q_in, Q_out equations
    "objective": 1,      # Paper mentions "最小化压力波动幅值"
    "constraints": 1,    # Paper mentions "0 ≤ x ≤ x_max"
    "assumptions": 1,    # Paper mentions 3 assumptions
    "candidate_model": 0, # Paper MISSING candidate models section
    "selected_model": 0,  # Paper MISSING selected model section
    "sensitivity_plan": 0, # Paper MISSING sensitivity analysis section
}

# ═══════════════════════════════════════════════════════════════
# Paper 3: Mutation (has unauthorized elements)
# ═══════════════════════════════════════════════════════════════

paper_mutation = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf-8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\geometry{margin=2.5cm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{hyperref}

\title{高压油管的压力控制}
\author{数学建模竞赛参赛队}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
本文针对高压油管的压力控制问题，建立了数学模型并进行了求解。
高压油管内燃油喷射的压力控制问题。通过凸轮驱动进油阀控制喷射规律，需要建立压力-流量耦合模型，分析压力波动规律并优化凸轮运动使压力稳定。
\end{abstract}

\section{问题重述}
高压油管内燃油喷射的压力控制问题。通过凸轮驱动进油阀控制喷射规律，需要建立压力-流量耦合模型，分析压力波动规律并优化凸轮运动使压力稳定。

\section{模型假设}
\item 燃油不可压缩，流动为准稳态
\item 喷嘴流量与压力平方根成正比
\item 燃油温度恒定，密度均匀
\item 管路长度恒定（UNAUTHORIZED: not in artifact）

\section{符号说明}
\begin{table}[h]
\centering
\begin{tabular}{lll}
\toprule
符号 & 含义 & 单位 \\
\midrule
P & 油管内压力 & MPa \\
Q & 喷油流量 & mm³/s \\
x & 进油阀位移 & mm \\
p1 & 流量系数 Cd & 1 \\
p2 & 管路容积 V & mm³ \\
L & 管路长度 & mm \\
\bottomrule
\end{tabular}
\end{table}

\section{模型建立与求解}
\subsection{压力动态}
\begin{equation}
dP/dt = (E/V)·(Q_in - Q_out)
\end{equation}
其中，体积弹性模量 E，管路容积 V。

\subsection{进油流量}
\begin{equation}
Q_in = Cd·A_in·√(2(P_in-P)/ρ)
\end{equation}
其中，进油阀流量，P_in 为供油压力。

\subsection{喷嘴流量}
\begin{equation}
Q_out = Cd·A_out·√(2P/ρ)
\end{equation}
其中，伯努利方程。

\subsection{约束条件}
\item 0 ≤ x ≤ x_max（阀门行程有限）

\subsection{目标函数}
\begin{equation}
最小化压力波动幅值
\end{equation}
其中，压力稳定是喷射质量的关键。

\section{候选模型对比}
\item ODE + 伯努利：优点 物理可解释，缺点 参数少
\item CFD 数值模拟：优点 精度高，缺点 计算成本高

\section{选定模型}
选定模型：ODE + 伯努利方程

选择理由：题目要求分析压力变化规律，ODE 模型足够且可解释

\section{灵敏度分析}
\item 流量系数 Cd：范围 ±20%，指标 压力波动幅值
\item 凸轮转速：范围 ±10%，指标 压力稳定性

\section{结论}
本文针对高压油管的压力控制问题，基于ODE + 伯努利方程模型进行了分析。
题目要求分析压力变化规律，ODE 模型足够且可解释

\end{document}
"""

# Golden labels for Mutation (has unauthorized L parameter and extra assumption)
golden_mutation = {
    "variables": 1,      # Paper mentions P, Q, x
    "parameters": 1,     # Paper mentions Cd, V (but also unauthorized L)
    "mechanism": 1,      # Paper mentions dP/dt, Q_in, Q_out equations
    "objective": 1,      # Paper mentions "最小化压力波动幅值"
    "constraints": 1,    # Paper mentions "0 ≤ x ≤ x_max"
    "assumptions": 0.5,  # Paper has 4 assumptions (3 correct + 1 unauthorized)
    "candidate_model": 1, # Paper mentions ODE+伯努利 and CFD
    "selected_model": 1,  # Paper mentions "ODE + 伯努利方程"
    "sensitivity_plan": 1, # Paper mentions Cd ±20% and 凸轮转速 ±10%
}

# Save Golden Set
papers = [
    {"name": "full_coverage", "paper": paper_full, "golden": golden_full, 
     "description": "Paper covers all artifact elements"},
    {"name": "partial_coverage", "paper": paper_partial, "golden": golden_partial,
     "description": "Paper missing meta-model elements (simulates R2 omission)"},
    {"name": "mutation", "paper": paper_mutation, "golden": golden_mutation,
     "description": "Paper has unauthorized elements"},
]

for p in papers:
    # Save paper
    paper_path = R3_GOLDEN / f"{p['name']}_paper.md"
    paper_path.write_text(p["paper"], encoding="utf-8")
    
    # Save golden labels
    golden_path = R3_GOLDEN / f"{p['name']}_golden.json"
    golden_path.write_text(json.dumps(p["golden"], ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"Created: {p['name']}")
    print(f"  Paper: {paper_path}")
    print(f"  Golden: {golden_path}")
    print(f"  Description: {p['description']}")
    print()

# Save artifact for reference
artifact_path = R3_GOLDEN / "artifact_2019_A_MMA.json"
artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Artifact: {artifact_path}")
