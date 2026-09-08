#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mock_llm_executor.py — Research-layer mock LLM executor (方案 D).

为 V3 DAG 的 16 个节点生成非空、结构有效的 artifact payload，使用确定性规则
（不是随机，不是真实 LLM 调用）。所有 artifact 明确标记 mock_execution=true。

用途：验证 measurement pipeline（execution_gate + e2e_metrics）在非空 artifact 上
能否正常工作，获得第一个 mock_baseline 能力测量。不证明 Agent 真实能力。

铁律：
- 不修改 core/ 架构
- 不伪造能力结论（明确标记 mock）
- 所有新文件放在 research/P15/measurement_recovery/ 或 projects/<项目>/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
GENERATOR = "mock_llm_executor_v1"
SCHEMA_VERSION = "3.1"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

# 16 个 DAG 节点 → artifact 映射
NODE_ARTIFACT_MAP = {
    "problem_analysis": "P001",
    "literature_search": "D001",
    "model_selection": "M001",
    "model_construction": "M001",  # 同一 artifact，construction 填充 payload
    "model_critique": "M001",
    "assumption_check": ["A001", "A002"],
    "experiment_design": "D002",
    "experiment@Q001": "E001",
    "experiment_critique@Q001": "E001",
    "evidence_build": "C001",
    "evidence_gate": "C001",
    "quality_evaluation": "R001",
    "research_direction": "D001",
    "paper_projection": "S001",
    "paper_sections@Q001": ["S001", "S002", "S003", "S004", "S005"],
    "paper_review": "S005",
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_provenance(node: str) -> dict:
    """生成 mock execution provenance。"""
    return {
        "mock_execution": True,
        "generator": GENERATOR,
        "node": node,
        "model_provider": "mock",
        "model_version": "mock-v1.0",
        "execution_mode": "mock",
        "generated_at": TIMESTAMP,
        "deterministic": True,
        "note": "此 artifact 由 mock_llm_executor 用确定性规则生成，不是真实 LLM 输出",
    }


def _make_validation(status: str = "mock_validated") -> dict:
    return {
        "status": status,
        "validated_by": GENERATOR,
        "validated_at": TIMESTAMP,
        "checks": ["layer1_non_empty", "layer2_structural"],
        "note": "mock 验证：仅确认结构非空，不验证语义正确性",
    }


def _make_lifecycle(node: str) -> list:
    return [
        {"from": None, "to": "draft", "at": TIMESTAMP, "by": node, "reason": "created"},
        {"from": "draft", "to": "active", "at": TIMESTAMP, "by": node,
         "reason": "registered with mock payload"},
    ]


def _base_artifact(artifact_id: str, atype: str, title: str, node: str,
                   question: str = "") -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "type": atype,
        "version": 1,
        "status": "active",
        "title": title,
        "question": question,
        "created_by": node,
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
        "payload": {},
        "parent": [],
        "depends_on": [],
        "relations": [],
        "provenance": _make_provenance(node),
        "validation": _make_validation(),
        "lifecycle_history": _make_lifecycle(node),
        "invalidation": {},
        "tags": [],
        "data": {},
    }


# ---------------------------------------------------------------------------
# 题面数据（来自 problem_statement.txt + card.yaml）
# ---------------------------------------------------------------------------
def load_problem_data(problem_statement_path: Path, card_path: Path) -> dict:
    """加载题面文本和 problem card。"""
    text = problem_statement_path.read_text(encoding="utf-8")
    # 极简 YAML 解析（零依赖）：只提取需要的字段
    card_raw = card_path.read_text(encoding="utf-8")
    return {
        "text": text,
        "text_sha256": _sha256(text),
        "card_raw": card_raw,
        "title": "板凳龙闹元宵",
        "problem_id": "2024_A",
    }


# ---------------------------------------------------------------------------
# 各 artifact payload 生成器
# ---------------------------------------------------------------------------
def gen_problem_payload(pdata: dict) -> dict:
    return {
        "text": pdata["text"],
        "source": "CUMCM 2024 A 题（板凳龙闹元宵）",
        "competition": "cumcm",
        "problem_id": pdata["problem_id"],
        "text_sha256": pdata["text_sha256"],
        "word_count": len(pdata["text"]),
    }


def gen_question_payload() -> dict:
    sub_questions = [
        {
            "id": "Q1",
            "text": ("舞龙队沿螺距为55cm的等距螺线顺时针盘入，龙头前把手速度1m/s，"
                     "初始位于第16圈A点。给出从初始时刻到300s为止，每秒整个舞龙队的"
                     "位置和速度，保存到result1.xlsx。"),
            "type": "forward_simulation",
            "depends_on": [],
        },
        {
            "id": "Q2",
            "text": ("沿Q1设定的螺线盘入，确定盘入终止时刻使得板凳之间不发生碰撞，"
                     "给出此时舞龙队的位置和速度，保存到result2.xlsx。"),
            "type": "collision_detection",
            "depends_on": ["Q1"],
        },
        {
            "id": "Q3",
            "text": ("调头空间为以螺线中心为圆心、直径9m的圆形区域。确定最小螺距，"
                     "使得龙头前把手能够沿着相应的螺线盘入到调头空间的边界。"),
            "type": "parameter_optimization",
            "depends_on": ["Q1"],
        },
        {
            "id": "Q4",
            "text": ("盘入螺距1.7m，盘出螺线与盘入关于中心对称，调头路径由两段圆弧"
                     "相切连接成S形（前弧半径=后弧2倍），与盘入盘出均相切。能否调整"
                     "圆弧使调头曲线变短？给出从-100s到100s每秒的位置和速度。"),
            "type": "trajectory_optimization",
            "depends_on": ["Q2", "Q3"],
        },
        {
            "id": "Q5",
            "text": ("沿Q4设定的路径行进，龙头速度保持不变，确定龙头的最大行进速度，"
                     "使得舞龙队各把手的速度均不超过2m/s。"),
            "type": "velocity_optimization",
            "depends_on": ["Q4"],
        },
    ]
    return {
        "sub_questions": sub_questions,
        "original_text": ("2024年高教社杯全国大学生数学建模竞赛A题：板凳龙闹元宵。"
                          "某板凳龙由223节板凳组成，建立数学模型解决5个子问题。"),
        "count": len(sub_questions),
    }


def gen_literature_decision_payload() -> dict:
    return {
        "decision": ("针对板凳龙运动学问题，文献检索确认该问题属于多体动力学+几何建模"
                    "+数值优化交叉领域。核心方法家族为多体刚体链递推、阿基米德螺线"
                    "参数化、碰撞检测和约束优化。"),
        "alternatives": [
            {"id": "mc-monte-carlo", "score": 82,
             "reason": "蒙特卡洛模拟适用于多体系统的不确定性传播和碰撞概率估计"},
            {"id": "mc-ga", "score": 75,
             "reason": "遗传算法适用于Q3最小螺距和Q4轨迹优化的非线性搜索"},
            {"id": "mc-pso", "score": 70,
             "reason": "粒子群优化可作为Q3/Q4的替代优化器，收敛较快"},
            {"id": "mc-ols", "score": 55,
             "reason": "最小二乘可用于螺线参数拟合，但不直接解决运动学递推"},
        ],
        "criteria": ["问题类型匹配（运动学/几何）", "方法适用性（时空坐标输出）",
                     "验证可行性（刚体约束可检验）", "竞赛历史表现"],
        "evidence_ids": ["P001"],
        "reasoning": ("题面核心是223节板凳龙沿螺线的运动学仿真（Q1）、碰撞检测（Q2）、"
                     "参数优化（Q3）、轨迹优化（Q4）和速度约束优化（Q5）。这是典型的"
                     "多体刚体链运动学问题，需要螺线几何参数化+刚体约束递推+数值优化。"
                     "评价类方法（TOPSIS/AHP）无法产生时空坐标，不适用。"),
    }


def gen_experiment_design_payload() -> dict:
    return {
        "decision": ("Q001实验设计：采用多体刚体链递推仿真，龙头沿阿基米德螺线运动，"
                    "后节位置由前节约束递推。包含基线对比、灵敏度分析和多次运行验证。"),
        "alternatives": [
            {"id": "E-Q001-01", "score": 90,
             "reason": "主实验：多体递推仿真+刚体约束验证"},
            {"id": "E-Q001-02", "score": 80,
             "reason": "基线对比：纯几何螺旋拟合（忽略刚体约束）"},
            {"id": "E-Q001-03", "score": 75,
             "reason": "灵敏度分析：螺距±10%扰动对碰撞时间的影响"},
        ],
        "criteria": ["方法可复现性", "刚体约束可验证性", "计算效率（O(N)递推）",
                     "结果可解释性"],
        "evidence_ids": ["M001"],
        "reasoning": ("实验必须验证刚体约束守恒（相邻节间距相对误差<1e-6）、"
                     "碰撞检测覆盖所有非相邻节对、时间步长收敛性。主方法为多体递推，"
                     "基线为纯几何拟合，灵敏度分析扰动螺距参数。"),
    }


def gen_model_payload() -> dict:
    variables = [
        {"name": "N", "domain": "integer", "description": "板凳龙总节数", "unit": "节",
         "value": 223},
        {"name": "L_head", "domain": "real", "description": "龙头板长", "unit": "m",
         "value": 3.41},
        {"name": "L_body", "domain": "real", "description": "龙身和龙尾板长", "unit": "m",
         "value": 2.20},
        {"name": "W", "domain": "real", "description": "板凳板宽", "unit": "m", "value": 0.30},
        {"name": "p_in", "domain": "real", "description": "盘入螺距（Q1/Q2）", "unit": "m",
         "value": 0.55},
        {"name": "v0", "domain": "real", "description": "龙头前把手行进速度", "unit": "m/s",
         "value": 1.0},
        {"name": "R_turn", "domain": "real", "description": "调头空间半径", "unit": "m",
         "value": 4.5},
        {"name": "v_max", "domain": "real", "description": "各把手速度上限（Q5）", "unit": "m/s",
         "value": 2.0},
        {"name": "x_i, y_i", "domain": "real", "description": "第i节把手坐标", "unit": "m"},
        {"name": "theta_i", "domain": "real", "description": "第i节方位角", "unit": "rad"},
        {"name": "R(theta)", "domain": "real", "description": "螺旋半径（角度函数）",
         "unit": "m"},
    ]
    constraints = [
        {"expression": "R(theta) = R0 + p_in * theta / (2*pi)",
         "description": "等距阿基米德螺线方程（龙头轨迹约束）"},
        {"expression": "sqrt((x_i - x_{i-1})^2 + (y_i - y_{i-1})^2) = L_i",
         "description": "相邻节把手间距守恒（刚体约束，L_i为第i节板长）"},
        {"expression": "v_head = 1.0 m/s (constant)",
         "description": "龙头前把手匀速约束"},
        {"expression": "min_{i<j, |i-j|>1} distance(section_i, section_j) >= W",
         "description": "非相邻节不碰撞约束（板宽W=0.30m为安全距离下界）"},
        {"expression": "R_final >= R_turn = 4.5 m (Q3)",
         "description": "调头空间边界约束（Q3最小螺距优化）"},
        {"expression": "v_i <= v_max = 2.0 m/s for all i (Q5)",
         "description": "各把手速度上限约束（Q5）"},
    ]
    equations = [
        {"latex": r"R(\theta) = R_0 + \frac{p_{in}}{2\pi}\theta",
         "description": "阿基米德等距螺线参数方程（龙头轨迹）"},
        {"latex": r"\mathbf{r}_i(t) = \mathbf{r}_{i-1}(t) + L_i \cdot \hat{\mathbf{u}}_i(t)",
         "description": "刚体链递推方程（后节位置=前节位置+板长×方向单位向量）"},
        {"latex": r"\|\mathbf{v}_i(t)\| = \left\|\frac{d\mathbf{r}_i}{dt}\right\| \leq v_{max}",
         "description": "各节速度约束（Q5优化目标约束）"},
    ]
    parameters = [
        {"name": "N", "value": 223, "unit": "节"},
        {"name": "L_head", "value": 3.41, "unit": "m"},
        {"name": "L_body", "value": 2.20, "unit": "m"},
        {"name": "W", "value": 0.30, "unit": "m"},
        {"name": "p_in", "value": 0.55, "unit": "m"},
        {"name": "v0", "value": 1.0, "unit": "m/s"},
        {"name": "R_turn", "value": 4.5, "unit": "m"},
        {"name": "v_max", "value": 2.0, "unit": "m/s"},
        {"name": "dt", "value": 1.0, "unit": "s"},
        {"name": "t_end", "value": 300.0, "unit": "s"},
    ]
    assumptions = [
        "每节板凳视为刚体，相邻节通过把手铰接，板长和间距守恒",
        "龙头前把手沿等距阿基米德螺线运动，速度恒定1m/s",
        "忽略板凳的弯曲变形和空气阻力，运动为平面运动",
        "碰撞检测中安全距离取板宽W=0.30m（保守估计）",
        "所有长度单位统一为米(m)，时间单位为秒(s)",
    ]
    return {
        "objective": ("最小化舞龙队盘入运动学仿真的位置预测误差；"
                     "Q1: 仿真223节板凳龙0-300s每秒位置速度；"
                     "Q2: 最小化首次碰撞时间的预测误差；"
                     "Q3: 最小化盘入螺距p使得龙头到达半径4.5m边界；"
                     "Q4: 最小化S形调头曲线长度；"
                     "Q5: 最大化龙头速度v0使得各把手速度≤2m/s"),
        "constraints": constraints,
        "variables": variables,
        "equations": equations,
        "parameters": parameters,
        "mechanism": ("多体刚体链递推 + 阿基米德螺线几何参数化。龙头沿螺线运动给定，"
                      "后节位置由前节约束递推（间距守恒），速度由位置对时间求导得到。"
                      "Q3/Q4/Q5转化为带约束的数值优化问题。"),
        "assumptions": assumptions,
        "model_family": "multibody_dynamics + numerical_optimization",
    }


def gen_assumption_payload(statement: str, justification: str,
                           relaxation: str, testable: bool = True) -> dict:
    return {
        "statement": statement,
        "justification": justification,
        "relaxation_impact": relaxation,
        "testable": testable,
    }


def gen_experiment_payload() -> dict:
    return {
        "method": ("多体刚体链递推仿真：龙头前把手沿阿基米德螺线以1m/s匀速运动，"
                  "后节位置由前节约束递推（相邻节间距守恒），速度由位置差分得到。"
                  "碰撞检测遍历所有|i-j|>1的节对，间距<板宽0.30m判定为碰撞。"),
        "parameters": {
            "N": 223,
            "L_head_m": 3.41,
            "L_body_m": 2.20,
            "W_m": 0.30,
            "p_in_m": 0.55,
            "v0_mps": 1.0,
            "dt_s": 1.0,
            "t_end_s": 300.0,
            "initial_turn": 16,
            "collision_safety_m": 0.30,
            "random_seed": 42,
            "multi_run_count": 5,
        },
        "results": {
            "collision_time_s": 187.5,
            "collision_radius_m": 2.34,
            "max_velocity_mps": 1.85,
            "max_velocity_section": 198,
            "min_clearance_m": 0.02,
            "min_clearance_time_s": 187.5,
            "total_distance_head_m": 300.0,
            "final_radius_m": 1.82,
            "rigid_constraint_max_error": 1.2e-7,
            "convergence_ratio_pct": 0.03,
        },
        "baseline": "纯几何螺旋拟合（忽略刚体约束，所有节直接投影到螺线上）",
        "repetitions": 5,
        "sensitivity": {
            "p_in_plus10pct_collision_time_s": 172.3,
            "p_in_minus10pct_collision_time_s": 204.1,
            "v0_plus20pct_collision_time_s": 156.2,
        },
    }


def gen_result_payload() -> dict:
    return {
        "values": {
            "collision_time_s": 187.5,
            "collision_radius_m": 2.34,
            "max_velocity_mps": 1.85,
            "min_clearance_m": 0.02,
            "total_distance_head_m": 300.0,
            "final_radius_m": 1.82,
            "rigid_constraint_max_error": 1.2e-7,
            "q3_min_pitch_m": 0.42,
            "q4_curve_length_m": 12.8,
            "q5_max_head_velocity_mps": 1.35,
        },
        "uncertainty": {
            "collision_time_s": 0.8,
            "collision_radius_m": 0.05,
            "max_velocity_mps": 0.03,
            "q3_min_pitch_m": 0.01,
            "q5_max_head_velocity_mps": 0.04,
        },
        "raw_data_path": "output/q001_simulation_results.json",
        "multi_run_stats": {
            "runs": 5,
            "collision_time_mean_s": 187.5,
            "collision_time_std_s": 0.8,
            "max_velocity_mean_mps": 1.85,
            "max_velocity_std_mps": 0.03,
        },
    }


def gen_figure_payload() -> dict:
    # 生成螺线轨迹的模拟数据点（阿基米德螺线，0到300秒）
    import math
    x_data, y_data = [], []
    p = 0.55  # 螺距 m
    v = 1.0   # 速度 m/s
    R0 = 16 * p / (2 * math.pi) + p * 16  # 第16圈起始半径（近似）
    for t in range(0, 301, 10):
        arc_length = v * t
        # 阿基米德螺线弧长近似积分
        theta = math.sqrt(2 * arc_length * 2 * math.pi / p)
        R = R0 + p * theta / (2 * math.pi)
        x_data.append(round(R * math.cos(theta), 4))
        y_data.append(round(R * math.sin(theta), 4))
    return {
        "data": {
            "x": x_data,
            "y": y_data,
            "time_s": list(range(0, 301, 10)),
            "labels": ["龙头前把手轨迹"],
        },
        "file_path": "figures/q001_trajectory.png",
        "caption": ("图1 板凳龙盘入螺线轨迹（0-300s，龙头前把手，螺距55cm，"
                   "初始第16圈，速度1m/s）"),
        "figure_type": "line",
        "x_label": "x (m)",
        "y_label": "y (m)",
    }


def gen_claim_payload() -> dict:
    return {
        "claim": ("在螺距55cm、龙头速度1m/s、初始第16圈条件下，板凳龙于187.5s发生"
                 "首次非相邻节碰撞，此时龙头位于半径2.34m处，最大把手速度1.85m/s"
                 "（出现在第198节），刚体约束最大误差1.2e-7m。"),
        "claim_type": "quantitative",
        "evidence_ref": ["R001", "E001"],
        "confidence": 0.85,
        "limitations": ("mock仿真结果，由确定性规则生成，未与金标准对比。"
                       "碰撞时间和速度数值为模拟值，不代表真实求解结果。"),
        "supporting_values": {
            "collision_time_s": 187.5,
            "collision_radius_m": 2.34,
            "max_velocity_mps": 1.85,
        },
    }


def gen_paper_section_payload(section_name: str, content: str) -> dict:
    return {
        "section_name": section_name,
        "content": content,
        "word_count": len(content),
        "citations": ["[1] 多体系统动力学", "[2] 阿基米德螺线几何"],
    }


# 论文各节内容（≥500字符，引用模型和结果）
PAPER_SECTIONS = {
    "问题重述与分析": (
        "板凳龙闹元宵是2024年全国大学生数学建模竞赛A题。某板凳龙由223节板凳组成，"
        "其中第1节为龙头（板长341cm），第2至222节为龙身（板长220cm），第223节为"
        "龙尾（板长220cm），所有板凳板宽30cm。相邻板凳通过把手连接，孔径5.5cm，"
        "孔中心距最近板头27.5cm。本题包含五个子问题：Q1要求舞龙队沿螺距55cm的等距"
        "螺线顺时针盘入，龙头速度1m/s，初始位于第16圈，给出0到300s每秒全节位置速度；"
        "Q2要求确定盘入终止时刻使得板凳不发生碰撞；Q3要求在直径9m调头空间约束下确定"
        "最小螺距；Q4要求在螺距1.7m条件下优化S形调头曲线；Q5要求确定龙头最大速度使得"
        "各把手速度不超过2m/s。本题核心是多体刚体链运动学仿真与约束优化问题。"
    ),
    "模型建立": (
        "本文建立多体刚体链递推模型求解板凳龙运动学问题。龙头前把手沿阿基米德等距螺线"
        "运动，螺线方程为R(θ)=R0+p·θ/(2π)，其中p为螺距。后节位置由刚体约束递推得到："
        "r_i(t)=r_{i-1}(t)+L_i·û_i(t)，其中L_i为第i节板长（龙头3.41m，龙身/龙尾2.20m），"
        "û_i为第i节方向单位向量。速度由位置对时间求导得到。模型假设：(1)每节板凳为刚体，"
        "相邻节间距守恒；(2)龙头沿螺线匀速运动，速度1m/s；(3)忽略弯曲变形和空气阻力，"
        "平面运动；(4)碰撞安全距离取板宽0.30m。Q3最小螺距转化为约束优化：min p subject to "
        "R_final≥4.5m。Q4 S形曲线优化：min curve_length subject to 相切约束。Q5速度优化："
        "max v0 subject to v_i≤2.0m/s for all i。模型变量包括N=223、L_head=3.41m、"
        "L_body=2.20m、W=0.30m、p_in=0.55m、v0=1.0m/s、R_turn=4.5m等。"
    ),
    "结果与分析": (
        "基于多体刚体链递推模型，对Q1进行0-300s仿真（时间步长1s，223节）。仿真结果表明："
        "龙头前把手在300s内行进300m，最终半径降至1.82m。首次非相邻节碰撞发生在187.5s，"
        "此时龙头位于半径2.34m处，碰撞涉及第45节与第120节（间距0.02m，小于安全距离0.30m）。"
        "最大把手速度出现在第198节，为1.85m/s（小于龙头速度1m/s的2倍，物理合理）。"
        "刚体约束验证：相邻节间距最大误差1.2e-7m，远小于阈值1e-6m，约束守恒良好。"
        "时间步长收敛性：dt=1s与dt=0.5s结果差异0.03%，满足收敛要求。Q3最小螺距优化结果为"
        "0.42m（小于题面给定的0.55m，说明在4.5m调头空间约束下可以使用更小螺距）。"
        "Q4优化后S形曲线长度12.8m。Q5龙头最大速度1.35m/s（受龙尾节速度约束限制）。"
    ),
    "灵敏度与稳健性": (
        "本文对关键参数进行灵敏度分析。螺距灵敏度：p_in增加10%（0.55→0.605m）时，"
        "首次碰撞时间从187.5s提前至172.3s（-8.1%）；p_in减少10%（0.55→0.495m）时，"
        "碰撞时间推迟至204.1s（+8.9%）。螺距对碰撞时间呈近似线性负相关，灵敏度约-1.6s/mm。"
        "龙头速度灵敏度：v0增加20%（1.0→1.2m/s）时，碰撞时间从187.5s提前至156.2s（-16.7%），"
        "速度与碰撞时间呈反比关系。多次运行验证（5次，随机种子42）：碰撞时间均值187.5s，"
        "标准差0.8s（变异系数0.43%）；最大速度均值1.85m/s，标准差0.03m/s（变异系数1.62%）。"
        "结果稳健性良好。基线对比：纯几何螺旋拟合（忽略刚体约束）在150s即出现间距违反，"
        "说明刚体约束递推对结果精度至关重要。模型局限性：mock仿真未考虑板凳柔性变形和"
        "三维运动，实际碰撞可能涉及板宽方向的接触而非仅中心点间距。"
    ),
    "结论": (
        "本文建立了多体刚体链递推模型求解2024年A题板凳龙闹元宵问题。主要结论如下："
        "(1) Q1：在螺距55cm、龙头速度1m/s、初始第16圈条件下，完成0-300s全节位置速度仿真，"
        "刚体约束最大误差1.2e-7m，收敛性良好。(2) Q2：首次非相邻节碰撞发生在187.5s，"
        "龙头半径2.34m，盘入应在此之前终止。(3) Q3：在直径9m调头空间约束下，最小螺距为0.42m。"
        "(4) Q4：优化后S形调头曲线长度12.8m，前弧半径为后弧2倍的约束下可进一步缩短。"
        "(5) Q5：龙头最大行进速度为1.35m/s，受龙尾节速度不超过2m/s约束限制。"
        "模型创新点：将多体刚体链递推与阿基米德螺线参数化结合，O(N)时间复杂度完成223节仿真；"
        "碰撞检测覆盖所有非相邻节对，避免了仅检查相邻节的常见错误。未来工作：引入有限元"
        "柔性体模型考虑板凳弯曲变形；扩展三维运动模型；用真实金标准数据验证仿真精度。"
        "注意：本报告数值为mock_executor生成的模拟结果，用于验证测量管线，不代表真实求解结果。"
    ),
}


# ---------------------------------------------------------------------------
# 主生成逻辑
# ---------------------------------------------------------------------------
def build_registry(pdata: dict, project_name: str) -> dict:
    """构建完整的 registry.json（16个非空 artifact）。"""
    artifacts = {}

    # P001: problem
    p = _base_artifact("P001", "problem", "赛题：板凳龙闹元宵", "problem_analysis")
    p["payload"] = gen_problem_payload(pdata)
    p["relations"] = [
        {"from": "P001", "relation": "motivates", "to": "Q001", "at": TIMESTAMP},
    ]
    artifacts["P001"] = p

    # Q001: question (question 字段不能指向自身，设为空字符串)
    q = _base_artifact("Q001", "question", "子问题分解（Q1-Q5）", "problem_analysis",
                       question="")
    q["payload"] = gen_question_payload()
    q["depends_on"] = ["P001"]
    q["relations"] = [
        {"from": "P001", "relation": "motivates", "to": "Q001", "at": TIMESTAMP},
        {"from": "Q001", "relation": "solved_by", "to": "M001", "at": TIMESTAMP},
    ]
    artifacts["Q001"] = q

    # D001: decision (literature_search + research_direction)
    d1 = _base_artifact("D001", "decision", "文献检索与方法选型决策", "literature_search")
    d1["payload"] = gen_literature_decision_payload()
    d1["depends_on"] = ["P001"]
    d1["relations"] = [
        {"from": "D001", "relation": "based_on", "to": "P001", "at": TIMESTAMP},
    ]
    d1["data"] = {
        "recommendations": [
            {"card_id": "mc-monte-carlo", "score": 82,
             "matched": ["问题类型命中: simulation", "多体系统不确定性传播"]},
            {"card_id": "mc-ga", "score": 75, "matched": ["问题类型命中: optimization"]},
            {"card_id": "mc-pso", "score": 70, "matched": ["问题类型命中: optimization"]},
        ],
    }
    artifacts["D001"] = d1

    # M001: model
    m = _base_artifact("M001", "model", "多体刚体链递推+螺线参数化模型", "model_construction",
                       question="Q001")
    model_payload = gen_model_payload()
    m["payload"] = model_payload
    m["depends_on"] = ["Q001", "D001"]
    m["relations"] = [
        {"from": "Q001", "relation": "solved_by", "to": "M001", "at": TIMESTAMP},
        {"from": "M001", "relation": "assumes", "to": "A001", "at": TIMESTAMP},
        {"from": "M001", "relation": "assumes", "to": "A002", "at": TIMESTAMP},
        {"from": "M001", "relation": "validated_by", "to": "E001", "at": TIMESTAMP},
        {"from": "D002", "relation": "based_on", "to": "M001", "at": TIMESTAMP},
        {"from": "E001", "relation": "tests", "to": "M001", "at": TIMESTAMP},
    ]
    # e2e_metrics structural check 读取 data 中的 objective/constraints/variables
    m["data"] = {
        "card_id": "mc-monte-carlo",
        "family": "uncertainty_propagation",
        "shortlist": ["mc-monte-carlo", "mc-ga", "mc-pso"],
        "objective": model_payload["objective"],
        "constraints": model_payload["constraints"],
        "variables": model_payload["variables"],
        "model_family": "multibody_dynamics + numerical_optimization",
    }
    artifacts["M001"] = m

    # A001: assumption
    a1 = _base_artifact("A001", "assumption", "假设1：刚体链约束", "assumption_check",
                        question="Q001")
    a1["payload"] = gen_assumption_payload(
        "每节板凳视为刚体，相邻节通过把手铰接，间距守恒（龙头3.41m，龙身/龙尾2.20m）",
        "题面描述板凳通过把手连接，木板弯曲变形在民俗运动速度下可忽略，刚体近似合理",
        "若考虑柔性变形，需引入有限元模型，计算量从O(N)增至O(N²)以上，且需材料参数",
    )
    a1["depends_on"] = ["M001"]
    a1["relations"] = [
        {"from": "M001", "relation": "assumes", "to": "A001", "at": TIMESTAMP},
    ]
    artifacts["A001"] = a1

    # A002: assumption
    a2 = _base_artifact("A002", "assumption", "假设2：龙头螺线匀速运动", "assumption_check",
                        question="Q001")
    a2["payload"] = gen_assumption_payload(
        "龙头前把手沿等距阿基米德螺线运动，速度恒定1m/s，顺时针盘入",
        "题面明确指定螺距55cm等距螺线和龙头速度1m/s，初始位置第16圈A点",
        "若速度变化，需引入速度控制律，轨迹时间参数化改变，碰撞时间预测需重新校准",
    )
    a2["depends_on"] = ["M001"]
    a2["relations"] = [
        {"from": "M001", "relation": "assumes", "to": "A002", "at": TIMESTAMP},
    ]
    artifacts["A002"] = a2

    # D002: decision (experiment_design)
    d2 = _base_artifact("D002", "decision", "Q001 实验计划决策", "experiment_design",
                        question="Q001")
    d2["payload"] = gen_experiment_design_payload()
    d2["depends_on"] = ["M001"]
    d2["relations"] = [
        {"from": "D002", "relation": "based_on", "to": "M001", "at": TIMESTAMP},
    ]
    d2["data"] = {
        "question": "Q001",
        "methods": ["mc-monte-carlo", "mc-ga"],
        "entries": [
            {"experiment_id": "E-Q001-01", "purpose": "多体递推仿真主实验",
             "method": "multibody_recursive_simulation", "priority": 1},
            {"experiment_id": "E-Q001-02", "purpose": "纯几何拟合基线对比",
             "method": "pure_geometric_spiral", "priority": 1},
            {"experiment_id": "E-Q001-03", "purpose": "螺距灵敏度分析",
             "method": "sensitivity_analysis", "priority": 2},
        ],
    }
    artifacts["D002"] = d2

    # E001: experiment
    e = _base_artifact("E001", "experiment", "Q001 多体递推仿真实验", "experiment@Q001",
                       question="Q001")
    e["payload"] = gen_experiment_payload()
    e["depends_on"] = ["M001", "D002"]
    e["relations"] = [
        {"from": "E001", "relation": "tests", "to": "M001", "at": TIMESTAMP},
        {"from": "E001", "relation": "produces", "to": "R001", "at": TIMESTAMP},
        {"from": "M001", "relation": "validated_by", "to": "E001", "at": TIMESTAMP},
    ]
    e["data"] = {
        "card_id": "mc-monte-carlo",
        "plan_ref": "D002",
        "plan_entry": "E-Q001-01",
        "hypothesis_ref": "多体递推仿真刚体约束误差<1e-6",
    }
    artifacts["E001"] = e

    # R001: result
    r = _base_artifact("R001", "result", "Q001 仿真结果", "quality_evaluation",
                       question="Q001")
    r["payload"] = gen_result_payload()
    r["depends_on"] = ["E001"]
    r["relations"] = [
        {"from": "E001", "relation": "produces", "to": "R001", "at": TIMESTAMP},
        {"from": "R001", "relation": "visualized_by", "to": "F001", "at": TIMESTAMP},
        {"from": "R001", "relation": "supports", "to": "C001", "at": TIMESTAMP},
    ]
    r["tags"] = ["sensitivity", "baseline", "multi_run"]
    r["data"] = {"card_id": "mc-monte-carlo", "runs": 5}
    artifacts["R001"] = r

    # F001: figure
    f = _base_artifact("F001", "figure", "Q001 盘入轨迹图", "experiment@Q001",
                       question="Q001")
    f["payload"] = gen_figure_payload()
    f["depends_on"] = ["R001"]
    f["relations"] = [
        {"from": "R001", "relation": "visualized_by", "to": "F001", "at": TIMESTAMP},
    ]
    artifacts["F001"] = f

    # C001: claim
    c = _base_artifact("C001", "claim", "Q001 研究结论", "evidence_build",
                       question="Q001")
    c["payload"] = gen_claim_payload()
    c["depends_on"] = ["R001"]
    c["relations"] = [
        {"from": "R001", "relation": "supports", "to": "C001", "at": TIMESTAMP},
        {"from": "C001", "relation": "appears_in", "to": "S003", "at": TIMESTAMP},
    ]
    c["data"] = {
        "statement": c["payload"]["claim"][:80] + "...",
        "claim_type": "quantitative",
        "experiment_refs": ["R001", "E001"],
        "literature_refs": [],
    }
    artifacts["C001"] = c

    # S001-S005: paper_sections
    section_ids = ["S001", "S002", "S003", "S004", "S005"]
    for i, (sname, scontent) in enumerate(PAPER_SECTIONS.items()):
        sid = section_ids[i]
        s = _base_artifact(sid, "paper_section", f"Q001 · {sname}", "paper_sections@Q001",
                           question="Q001")
        s["payload"] = gen_paper_section_payload(sname, scontent)
        if sid == "S003":
            s["relations"] = [
                {"from": "C001", "relation": "appears_in", "to": "S003", "at": TIMESTAMP},
            ]
        artifacts[sid] = s

    # 构建 counters
    counters = {}
    for art in artifacts.values():
        atype = art["type"]
        counters[atype] = counters.get(atype, 0) + 1

    registry = {
        "registry_version": 3,
        "project": project_name,
        "updated_at": TIMESTAMP,
        "counters": counters,
        "artifacts": artifacts,
        "history": {},  # 必须为空 dict，加载器期望 {artifact_id: {version: snapshot}}
        "mock_metadata": {
            "generator": GENERATOR,
            "executed_at": TIMESTAMP,
            "nodes_executed": list(NODE_ARTIFACT_MAP.keys()),
            "artifact_count": len(artifacts),
            "mock_execution": True,
        },
    }
    return registry


def build_status(project_name: str) -> dict:
    """构建 status.json。"""
    return {
        "schema_version": 3,
        "project": project_name,
        "state": {
            "problem": {"status": "validated"},
            "questions": {
                "Q001": {
                    "status": "validated",
                    "models": ["M001"],
                    "experiments": ["E001"],
                    "claims": ["C001"],
                    "dependencies": [],
                    "retry_count": 0,
                    "failure_reason": None,
                    "last_updated": TIMESTAMP,
                },
            },
            "models": {"status": "validated", "candidates": ["M001"], "selected": ["M001"]},
            "experiments": {"status": "completed", "by_question": {"Q001": ["E001"]}},
            "evidence": {
                "status": "validated",
                "graph_version": 1,
                "claims_supported": 1,
                "claims_total": 1,
                "coverage_ratio": 1.0,
            },
            "narrative": {"status": "completed"},
            "paper": {"status": "draft", "sections_written": 5, "sections_total": 5},
            "review": {"status": "pending", "rounds_completed": 0, "verdict": None},
        },
        "workflow": {
            "current_nodes": [],
            "completed_nodes": list(NODE_ARTIFACT_MAP.keys()),
            "blocked_nodes": [],
            "waiting_approval": [],
            "retries": {},
            "notes": ["mock_execution: 所有节点由 mock_llm_executor_v1 完成"],
        },
        "run": {
            "phase": "completed",
            "started_at": TIMESTAMP,
            "updated_at": TIMESTAMP,
        },
    }


def build_evidence_graph(project_name: str) -> dict:
    """构建 evidence_graph.json。"""
    relations = [
        {"from": "P001", "relation": "motivates", "to": "Q001", "at": TIMESTAMP},
        {"from": "D001", "relation": "based_on", "to": "P001", "at": TIMESTAMP},
        {"from": "Q001", "relation": "solved_by", "to": "M001", "at": TIMESTAMP},
        {"from": "M001", "relation": "assumes", "to": "A001", "at": TIMESTAMP},
        {"from": "M001", "relation": "assumes", "to": "A002", "at": TIMESTAMP},
        {"from": "D002", "relation": "based_on", "to": "M001", "at": TIMESTAMP},
        {"from": "M001", "relation": "validated_by", "to": "E001", "at": TIMESTAMP},
        {"from": "E001", "relation": "tests", "to": "M001", "at": TIMESTAMP},
        {"from": "E001", "relation": "produces", "to": "R001", "at": TIMESTAMP},
        {"from": "R001", "relation": "visualized_by", "to": "F001", "at": TIMESTAMP},
        {"from": "R001", "relation": "supports", "to": "C001", "at": TIMESTAMP},
        {"from": "C001", "relation": "appears_in", "to": "S003", "at": TIMESTAMP},
    ]
    return {
        "graph_schema_version": 3,
        "graph_version": 1,
        "project": project_name,
        "updated_at": TIMESTAMP,
        "relations": relations,
    }


def build_decision_log() -> dict:
    """构建 decision_log.json。"""
    return {
        "schema_version": 3,
        "updated_at": TIMESTAMP,
        "decisions": [
            {
                "decision_id": "D001",
                "question": "Q001 方法选型",
                "chosen": "mc-monte-carlo",
                "alternatives": [
                    "mc-ga（score=75，优化类方法适用于Q3/Q4/Q5）",
                    "mc-pso（score=70，粒子群优化替代方案）",
                ],
                "criteria": ["问题类型匹配", "方法适用性", "验证可行性", "竞赛历史表现"],
                "evidence_ids": ["P001"],
                "reasoning": ("板凳龙为多体刚体链运动学问题，核心是仿真+优化。"
                             "选择mc-monte-carlo作为主方法卡（仿真类），mc-ga/mc-pso作为"
                             "优化备选。评价类方法（TOPSIS/AHP）不适用。"),
                "confidence": 0.85,
                "reversible": True,
                "created_by": "literature_search",
                "created_at": TIMESTAMP,
                "status": "active",
                "question_type": "simulation_optimization",
                "knowledge_refs": [
                    {"id": "mc-monte-carlo", "version": 1},
                    {"id": "mc-ga", "version": 1},
                ],
                "failure_refs": ["fm-wrong-model-family"],
                "required_validation": ["baseline_comparison", "rigid_constraint_check"],
                "score_breakdown": {
                    "fit": 35, "data": 15, "interpretability": 10, "robustness": 8,
                    "complexity": 5, "innovation": 3, "competition": 8, "evidence_cost": 3,
                    "risk_penalty": -5,
                },
                "consequences": [],
                "invalidated_by": None,
                "invalidated_reason": None,
                "invalidated_at": None,
            },
            {
                "decision_id": "D002",
                "question": "Q001 实验设计",
                "chosen": "E-Q001-01",
                "alternatives": ["E-Q001-02（基线对比）", "E-Q001-03（灵敏度分析）"],
                "criteria": ["可复现性", "约束可验证性", "计算效率", "可解释性"],
                "evidence_ids": ["M001"],
                "reasoning": "主实验为多体递推仿真，辅以基线对比和灵敏度分析。",
                "confidence": 0.90,
                "reversible": True,
                "created_by": "experiment_design",
                "created_at": TIMESTAMP,
                "status": "active",
                "question_type": "experiment_design",
                "knowledge_refs": [],
                "failure_refs": [],
                "required_validation": ["rigid_constraint_check", "convergence_check"],
                "score_breakdown": {"fit": 40, "data": 10, "robustness": 10, "complexity": 5},
                "consequences": [],
                "invalidated_by": None,
                "invalidated_reason": None,
                "invalidated_at": None,
            },
        ],
    }


def build_quality_report() -> dict:
    return {
        "schema_version": 1,
        "project": "p151-2024a-r2",
        "generated_at": TIMESTAMP,
        "overall_score": 72.5,
        "dimensions": {
            "problem_analysis": 85.0,
            "model_quality": 78.0,
            "experiment_quality": 70.0,
            "evidence_quality": 75.0,
            "paper_quality": 65.0,
        },
        "mock_execution": True,
        "note": "mock 质量评分，由 mock_llm_executor_v1 生成",
    }


def build_engine_progress() -> dict:
    return {
        "schema_version": 1,
        "project": "p151-2024a-r2",
        "phase": "completed",
        "completed_nodes": 16,
        "total_nodes": 16,
        "failed_nodes": 0,
        "retries": 0,
        "mock_execution": True,
        "generator": GENERATOR,
    }


def build_run_record(project_path: Path, input_hash: str) -> dict:
    """构建 state/runs/ 下的 run record。"""
    return {
        "schema_version": 1,
        "run_id": "mock_b0r2_" + _sha256(TIMESTAMP)[:12],
        "parent_run_id": None,
        "project": str(project_path),
        "questions": ["Q001"],
        "status": "completed",
        "workflow_version": _sha256("mock_workflow_v1"),
        "skill_version": _sha256(GENERATOR),
        "tool_version": "mock-executor-v1",
        "model_provider": "mock",
        "model_version": "mock-v1.0",
        "prompt_hash": _sha256("mock_prompt"),
        "input_hash": input_hash,
        "artifact_hash": _sha256("mock_artifacts"),
        "evidence_hash": _sha256("mock_evidence"),
        "decision_log_hash": _sha256("mock_decisions"),
        "latency": {
            "started_at": TIMESTAMP,
            "finished_at": TIMESTAMP,
            "seconds": 0.01,
        },
        "started_at": TIMESTAMP,
        "token_cost": None,
        "execution_mode": "mock",
        "engine": {
            "completed_nodes": 16,
            "retries": 0,
            "failures": [],
        },
        "decision": None,
        "mock_execution": True,
        "generator": GENERATOR,
    }


def build_gt() -> dict:
    """构建金标准（GT）JSON，用于 e2e_metrics 的 decomposition 和 method_selection。"""
    return {
        "problem_id": "2024_A",
        "title": "板凳龙闹元宵",
        "sub_questions": ["Q1", "Q2", "Q3", "Q4", "Q5"],
        "methods": [
            "multibody_dynamics",
            "numerical_optimization",
            "differential_geometry",
            "catenary_approximation",
            "pure_geometric_spiral",
        ],
        "allowed_model_families": [
            "multibody_dynamics",
            "catenary_approximation",
            "differential_geometry",
            "numerical_optimization",
            "pure_geometric_spiral",
        ],
    }


# ---------------------------------------------------------------------------
# 项目目录创建
# ---------------------------------------------------------------------------
def create_project_structure(project_path: Path, problem_text: str) -> None:
    """创建项目目录结构。"""
    dirs = [
        "artifacts", "code", "deliverables", "figures", "inputs",
        "inputs/external", "output", "paper", "state", "state/runs",
        "work", "_scratch",
    ]
    for d in dirs:
        (project_path / d).mkdir(parents=True, exist_ok=True)

    # 写入题面
    (project_path / "inputs" / "cumcm2024A.txt").write_text(
        problem_text, encoding="utf-8")

    # 创建 minimal paper/main.tex（使 writing_completeness 可计算）
    tex_content = r"""% mock paper main.tex (generated by mock_llm_executor_v1)
\documentclass{article}
\begin{document}
\section{问题重述与分析}
板凳龙闹元宵问题包含5个子问题。
\section{模型建立}
多体刚体链递推模型。
\begin{equation}
R(\theta) = R_0 + \frac{p}{2\pi}\theta
\end{equation}
\begin{equation}
\mathbf{r}_i = \mathbf{r}_{i-1} + L_i \hat{\mathbf{u}}_i
\end{equation}
\section{结果与分析}
仿真结果表明碰撞时间187.5s。
\begin{table}
\caption{结果表}
\begin{tabular}{cc}
时间 & 半径 \\
187.5 & 2.34 \\
\end{tabular}
\end{table}
\section{结论}
mock结论。
\includegraphics{figures/q001_trajectory.png}
\end{document}
"""
    (project_path / "paper" / "main.tex").write_text(tex_content, encoding="utf-8")
    (project_path / "paper" / "references.bib").write_text(
        "@article{mock1,\n  title={Mock Reference},\n  year={2024}\n}\n",
        encoding="utf-8")


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="mock_llm_executor_v1 — 为 V3 DAG 16 节点生成非空 mock artifact")
    parser.add_argument("--project", required=True, help="项目目录路径")
    parser.add_argument("--problem-card", required=True, help="Problem Card YAML 路径")
    parser.add_argument("--problem-statement", default=None,
                        help="题面文本路径（默认从 problem-card 同目录读取）")
    args = parser.parse_args()

    project_path = Path(args.project).resolve()
    card_path = Path(args.problem_card).resolve()

    if args.problem_statement:
        statement_path = Path(args.problem_statement).resolve()
    else:
        statement_path = card_path.parent / "problem_statement.txt"

    if not statement_path.exists():
        print(f"ERROR: 题面文件不存在: {statement_path}", file=sys.stderr)
        sys.exit(1)
    if not card_path.exists():
        print(f"ERROR: Problem Card 不存在: {card_path}", file=sys.stderr)
        sys.exit(1)

    project_name = project_path.name
    print(f"[mock_llm_executor_v1] 项目: {project_name}")
    print(f"[mock_llm_executor_v1] 题面: {statement_path}")
    print(f"[mock_llm_executor_v1] Problem Card: {card_path}")

    # 1. 加载题面数据
    pdata = load_problem_data(statement_path, card_path)
    print(f"[mock_llm_executor_v1] 题面 SHA256: {pdata['text_sha256'][:16]}...")
    print(f"[mock_llm_executor_v1] 题面长度: {len(pdata['text'])} 字符")

    # 2. 创建项目目录结构
    create_project_structure(project_path, pdata["text"])
    print(f"[mock_llm_executor_v1] 项目目录结构已创建: {project_path}")

    # 3. 构建 registry（16 个非空 artifact）
    registry = build_registry(pdata, project_name)
    registry_path = project_path / "state" / "registry.json"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    artifact_count = len(registry["artifacts"])
    non_empty_count = sum(1 for a in registry["artifacts"].values()
                          if a["payload"] and a["payload"] not in ([], {}, ""))
    print(f"[mock_llm_executor_v1] registry.json 已写入: {registry_path}")
    print(f"[mock_llm_executor_v1] artifact 总数: {artifact_count}, 非空: {non_empty_count}")

    # 4. 构建其他状态文件
    status = build_status(project_name)
    (project_path / "state" / "status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    egraph = build_evidence_graph(project_name)
    (project_path / "state" / "evidence_graph.json").write_text(
        json.dumps(egraph, ensure_ascii=False, indent=2), encoding="utf-8")

    dlog = build_decision_log()
    (project_path / "state" / "decision_log.json").write_text(
        json.dumps(dlog, ensure_ascii=False, indent=2), encoding="utf-8")

    qreport = build_quality_report()
    (project_path / "state" / "quality_report.json").write_text(
        json.dumps(qreport, ensure_ascii=False, indent=2), encoding="utf-8")

    eprogress = build_engine_progress()
    (project_path / "state" / "engine_progress.json").write_text(
        json.dumps(eprogress, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. 构建 run record
    input_hash = _sha256(pdata["text"])
    run_record = build_run_record(project_path, input_hash)
    run_id = run_record["run_id"]
    (project_path / "state" / "runs" / f"{run_id}.json").write_text(
        json.dumps(run_record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[mock_llm_executor_v1] run record: {run_id}")

    # 6. 构建 GT 文件（用于 e2e_metrics）
    gt = build_gt()
    gt_path = project_path / "state" / "gt.json"
    gt_path.write_text(json.dumps(gt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[mock_llm_executor_v1] GT 文件: {gt_path}")

    # 7. 汇总报告
    print()
    print("=" * 60)
    print("mock_llm_executor_v1 执行完成")
    print("=" * 60)
    print(f"  项目: {project_name}")
    print(f"  题面 SHA256: {pdata['text_sha256']}")
    print(f"  artifact 总数: {artifact_count}")
    print(f"  非空 artifact: {non_empty_count}/{artifact_count} "
          f"({100*non_empty_count/artifact_count:.1f}%)")
    print(f"  provenance.mock_execution: true (全部 artifact)")
    print(f"  generator: {GENERATOR}")
    print()
    print("  artifact 类型分布:")
    for atype, count in sorted(registry["counters"].items()):
        print(f"    {atype}: {count}")
    print()
    print("  产出文件:")
    print(f"    {registry_path}")
    print(f"    {project_path / 'state' / 'status.json'}")
    print(f"    {project_path / 'state' / 'evidence_graph.json'}")
    print(f"    {project_path / 'state' / 'decision_log.json'}")
    print(f"    {project_path / 'state' / 'quality_report.json'}")
    print(f"    {project_path / 'state' / 'engine_progress.json'}")
    print(f"    {project_path / 'state' / 'runs' / f'{run_id}.json'}")
    print(f"    {gt_path}")
    print(f"    {project_path / 'inputs' / 'cumcm2024A.txt'}")
    print(f"    {project_path / 'paper' / 'main.tex'}")
    print()
    print("  注意: 所有 artifact 均为 mock_execution，不代表真实 LLM 输出。")
    print("  用途: 验证 measurement pipeline 在非空 artifact 上的工作状态。")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
