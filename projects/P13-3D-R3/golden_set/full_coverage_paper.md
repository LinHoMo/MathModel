
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
