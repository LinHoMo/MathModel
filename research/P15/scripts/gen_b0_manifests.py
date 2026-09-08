#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate 5 B0 baseline manifests for 2024_A 板凳龙闹元宵."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT_DIR = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\b0_manifests\2024_A")
OUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_SHA = "9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e"

def ts(base, offset_sec):
    return (base + timedelta(seconds=offset_sec)).strftime("%Y-%m-%dT%H:%M:%SZ")

base = datetime(2026, 9, 8, 14, 0, 0, tzinfo=timezone.utc)

def common(node_id, dag_pos, started_off, finished_off, latency):
    return {
        "executor_type": "external_agent",
        "agent_identity": "doubao",
        "model_version": "doubao-pro-32k",
        "input_sha256": INPUT_SHA,
        "prompt_or_skill_version": "b0-baseline-v1",
        "artifact_schema_version": "model-ir-1.0",
        "started_at": ts(base, started_off),
        "finished_at": ts(base, finished_off),
        "latency_seconds": latency,
        "submitted_at": ts(base, finished_off + 1),
        "node_id": node_id,
        "dag_position": dag_pos,
    }

# ============================================================
# Node 0: problem_understanding
# ============================================================
m0 = common("problem_understanding", 0, 0, 45, 45.0)
m0["payload"] = {
    "title": "2024_A 板凳龙闹元宵 — 问题理解与分解",
    "problem_type": "运动学仿真与几何优化",
    "sub_questions": [
        {"id": "Q1", "text": "沿螺距55cm等距螺线顺时针盘入，龙头前把手速度1m/s，初始在第16圈A点，求0-300s每秒各把手位置和速度", "type": "forward_simulation"},
        {"id": "Q2", "text": "确定盘入终止时刻使得板凳间不发生碰撞，给出此时位置和速度", "type": "collision_detection"},
        {"id": "Q3", "text": "调头空间为直径9m圆形区域，确定最小螺距使龙头能盘入到调头空间边界", "type": "geometric_optimization"},
        {"id": "Q4", "text": "盘入螺距1.7m，盘出螺线中心对称，S形调头曲线由两段相切圆弧组成（前半径=后半径2倍），能否调整圆弧使调头曲线变短；给出-100s到100s每秒位置速度", "type": "curve_optimization_and_simulation"},
        {"id": "Q5", "text": "沿Q4路径行进，确定龙头最大行进速度使各把手速度均不超过2m/s", "type": "velocity_constrained_optimization"},
    ],
    "key_variables": [
        {"name": "N", "meaning": "板凳总节数", "value": 223, "unit": "节"},
        {"name": "L_head", "meaning": "龙头板长", "value": 3.41, "unit": "m"},
        {"name": "L_body", "meaning": "龙身/龙尾板长", "value": 2.20, "unit": "m"},
        {"name": "W", "meaning": "板宽", "value": 0.30, "unit": "m"},
        {"name": "d_offset", "meaning": "孔中心距最近板头距离", "value": 0.275, "unit": "m"},
        {"name": "p_in", "meaning": "盘入螺距(Q1/Q2)", "value": 0.55, "unit": "m"},
        {"name": "v0", "meaning": "龙头前把手行进速度", "value": 1.0, "unit": "m/s"},
        {"name": "R_turn", "meaning": "调头空间半径(直径9m)", "value": 4.5, "unit": "m"},
        {"name": "n_handles", "meaning": "把手中心总数(223前把手+1龙尾后把手)", "value": 224, "unit": "个"},
    ],
    "model_family_hint": "multibody_dynamics + differential_geometry + numerical_optimization",
    "difficulty_assessment": {
        "overall": "high",
        "reason": "多体刚体链运动学+阿基米德螺线参数化+碰撞检测+几何优化，5个子问题耦合度高，需要精确数值仿真",
        "sub_question_difficulty": {"Q1": "medium", "Q2": "high", "Q3": "medium", "Q4": "high", "Q5": "medium"},
    },
}

# ============================================================
# Node 1: model_construction (most important)
# ============================================================
m1 = common("model_construction", 1, 46, 180, 134.0)
m1["payload"] = {
    "title": "板凳龙多体刚体链运动学模型",
    "model_type": "rigid_body_chain_kinematics",
    "model_family": "multibody_dynamics",
    "assumptions": [
        "每节板凳视为刚体，不发生弯曲变形",
        "把手与板固连，把手中心位于孔中心，相邻板凳通过把手铰接",
        "忽略空气阻力和板凳质量，仅考虑运动学不涉及动力学受力分析",
        "各把手中心均位于等距螺线上（题面明确要求）",
        "龙头前把手沿螺线匀速运动，速度大小恒为1m/s",
        "板凳宽度方向不发生重叠时视为不碰撞（碰撞判据为非相邻把手间距小于板宽）",
    ],
    "variables": [
        {"name": "x_i", "symbol": "x_i(t)", "definition": "第i个把手中心的x坐标(i=1..224)", "unit": "m"},
        {"name": "y_i", "symbol": "y_i(t)", "definition": "第i个把手中心的y坐标", "unit": "m"},
        {"name": "v_i", "symbol": "v_i(t)", "definition": "第i个把手的速率", "unit": "m/s"},
        {"name": "theta", "symbol": "\\theta(t)", "definition": "龙头前把手在螺线上的极角（顺时针为正）", "unit": "rad"},
        {"name": "R_spiral", "symbol": "R(\\theta)", "definition": "螺线半径作为极角的函数", "unit": "m"},
        {"name": "phi_i", "symbol": "\\phi_i(t)", "definition": "第i节板凳的方位角", "unit": "rad"},
        {"name": "s_i", "symbol": "s_i(t)", "definition": "第i个把手沿螺线的弧长坐标", "unit": "m"},
        {"name": "d_ij", "symbol": "d_{ij}(t)", "definition": "第i与第j个把手间距离（碰撞检测用）", "unit": "m"},
        {"name": "p_opt", "symbol": "p_{opt}", "definition": "Q3优化的最小螺距", "unit": "m"},
        {"name": "v_head_max", "symbol": "v_{head,max}", "definition": "Q5优化的龙头最大行进速度", "unit": "m/s"},
        {"name": "omega", "symbol": "\\omega(t)", "definition": "龙头前把手的角速度", "unit": "rad/s"},
        {"name": "t_collision", "symbol": "t_{collision}", "definition": "Q2首次碰撞时刻", "unit": "s"},
    ],
    "parameters": [
        {"name": "N", "symbol": "N", "definition": "板凳龙总节数", "unit": "节", "value": 223},
        {"name": "L_head", "symbol": "L_{head}", "definition": "龙头板长", "unit": "m", "value": 3.41},
        {"name": "L_body", "symbol": "L_{body}", "definition": "龙身和龙尾板长", "unit": "m", "value": 2.20},
        {"name": "d_offset", "symbol": "d_{offset}", "definition": "孔中心距最近板头距离", "unit": "m", "value": 0.275},
        {"name": "W", "symbol": "W", "definition": "板凳板宽", "unit": "m", "value": 0.30},
        {"name": "p_in", "symbol": "p_{in}", "definition": "盘入螺距(Q1/Q2)", "unit": "m", "value": 0.55},
        {"name": "v0", "symbol": "v_0", "definition": "龙头前把手行进速度", "unit": "m/s", "value": 1.0},
        {"name": "R_A", "symbol": "R_A", "definition": "初始时刻龙头(第16圈A点)螺线半径", "unit": "m", "value": 8.8},
        {"name": "b_spiral", "symbol": "b", "definition": "阿基米德螺线参数 b=p/(2π)", "unit": "m/rad", "value": 0.08754},
        {"name": "R_turn", "symbol": "R_{turn}", "definition": "调头空间半径", "unit": "m", "value": 4.5},
    ],
    "objectives": [
        "Q1: 正向仿真223节板凳龙0-300s每秒224个把手的位置和速度",
        "Q2: 确定首次碰撞时刻 t_collision = min{t: ∃_{i<j,|i-j|>1} d_ij(t) < W}",
        "Q3: 最小化螺距 p 使龙头能盘入到半径4.5m的调头空间边界",
        "Q4: 优化S形调头曲线使总弧长最短，同时保持与盘入/盘出螺线相切",
        "Q5: 最大化龙头速度 v_head 使所有把手速度 v_i ≤ 2 m/s",
    ],
    "constraints": [
        "阿基米德等距螺线: R(θ) = R_A - b·θ (顺时针盘入半径递减)",
        "相邻把手间距守恒: sqrt((x_i-x_{i-1})²+(y_i-y_{i-1})²) = ℓ_i, ℓ_1=L_head-2d_offset, ℓ_{i>1}=L_body-2d_offset",
        "龙头前把手匀速: ||ṙ_1(t)|| = v_0 = 1.0 m/s",
        "非相邻节不碰撞: d_ij(t) ≥ W, ∀_{i<j,|i-j|>1}",
        "初始条件: θ(0)=0, R(0)=R_A=8.8m",
        "Q3调头空间边界: R(θ_final) ≥ R_turn = 4.5m",
        "Q5速度约束: v_i(t) ≤ 2.0 m/s, ∀i,t",
    ],
    "mechanisms": [
        "阿基米德螺线参数化: 龙头前把手沿等距螺线运动，半径随极角线性变化 R(θ)=R0+bθ",
        "刚体链运动学递推: 板凳龙视为多节刚体铰接链，后节位置由前节约束递推；各把手均在螺线上",
        "碰撞检测机制: 非相邻把手间欧氏距离小于板宽时判定为碰撞",
        "S形曲线几何: 两段相切圆弧连接盘入与盘出螺线，半径比2:1，切点处曲率连续",
    ],
    "equations": [
        {"latex": "R(\\theta) = R_A - b\\theta, \\quad b = \\frac{p_{in}}{2\\pi}", "description": "阿基米德等距螺线参数方程"},
        {"latex": "\\mathbf{r}_i(t) = \\mathbf{r}_{i-1}(t) + \\ell_i \\cdot \\hat{\\mathbf{u}}_i(t), \\quad \\hat{\\mathbf{u}}_i = \\frac{\\mathbf{r}_{i-1} - \\mathbf{r}_{i-2}}{\\|\\mathbf{r}_{i-1} - \\mathbf{r}_{i-2}\\|}", "description": "刚体链递推方程"},
        {"latex": "\\mathbf{v}_i(t) = \\frac{d\\mathbf{r}_i}{dt}, \\quad v_i = \\|\\mathbf{v}_i\\|", "description": "速度定义方程"},
        {"latex": "\\frac{d\\theta}{dt} = \\frac{v_0}{\\sqrt{R(\\theta)^2 + b^2}}, \\quad \\omega = \\frac{d\\theta}{dt}", "description": "龙头角速度方程（由匀速约束和螺线几何推导）"},
        {"latex": "d_{ij}(t) = \\sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}", "description": "把手间距离定义（碰撞检测用）"},
        {"latex": "\\min_{p} \\; p \\quad \\text{s.t.} \\quad R_A - \\frac{p}{2\\pi}\\theta_{final} \\geq R_{turn}", "description": "Q3最小螺距优化问题"},
        {"latex": "\\max_{v_{head}} \\; v_{head} \\quad \\text{s.t.} \\quad v_i(t) \\leq 2.0, \\; \\forall i,t", "description": "Q5最大龙头速度优化问题"},
    ],
    "data": {
        "objective": "建立多体刚体链运动学模型，仿真板凳龙沿阿基米德螺线盘入/盘出的位置速度，检测碰撞，优化螺距与调头曲线，求解速度约束下的最大龙头速度",
        "constraints": [
            "相邻把手间距守恒(刚体约束)",
            "龙头前把手匀速1m/s",
            "非相邻节不碰撞(间距≥板宽0.3m)",
            "各把手中心位于螺线上",
            "Q3调头空间半径4.5m边界约束",
            "Q5所有把手速度≤2m/s",
        ],
        "variables": [
            "x_i(t), y_i(t): 224个把手中心坐标",
            "v_i(t): 各把手速率",
            "θ(t): 龙头极角",
            "R(θ): 螺线半径",
            "d_ij(t): 把手间距(碰撞检测)",
            "p_opt: 最小螺距(Q3)",
            "v_head_max: 最大龙头速度(Q5)",
        ],
        "card_id": "mc-monte-carlo",
        "shortlist": ["mc-monte-carlo", "mc-ga", "mc-pso"],
    },
}

# ============================================================
# Node 2: method_selection
# ============================================================
m2 = common("method_selection", 2, 181, 240, 59.0)
m2["payload"] = {
    "decision": "采用多体刚体链运动学递推 + 阿基米德螺线参数化作为核心方法；Q3/Q4/Q5的优化子问题使用数值优化（黄金分割/网格搜索）；碰撞检测使用逐帧欧氏距离扫描。可用方法卡中无运动学/几何类，最接近的是mc-monte-carlo（用于碰撞时刻的随机采样验证）和mc-ga（用于Q3/Q4/Q5优化），这本身是方法卡覆盖度不足的观测。",
    "alternatives": [
        "纯几何螺线法(pure_geometric_spiral): 直接假设所有把手在同一螺线上，忽略板长约束，计算简单但精度不足",
        "悬链线近似(catenary_approximation): 将板凳龙视为柔性链，不适用于刚体板凳铰接结构",
        "微分几何法(differential_geometry): 用Frenet标架描述曲线运动，数学优美但实现复杂",
        "蒙特卡洛采样(mc-monte-carlo): 随机采样初始条件和参数估计碰撞概率，可作为验证手段但不适合确定性仿真",
        "遗传算法(mc-ga): 用于Q3/Q4/Q5的优化问题，可作为全局优化备选",
    ],
    "reasoning": "1) 题面明确要求各把手中心位于螺线上，且板凳为刚体铰接，刚体链运动学递推是最直接的物理建模方式；2) 阿基米德螺线有解析参数方程，可精确计算龙头位置和角速度；3) Q1/Q2为确定性正向仿真，无需随机方法；4) Q3/Q4/Q5为单变量或低维优化，数值方法足够，mc-ga可作为全局优化验证；5) 现有方法卡库缺乏运动学/几何类卡片，mc-monte-carlo仅能用于碰撞检测的鲁棒性验证，不能替代核心运动学模型。",
    "criteria": [
        "物理一致性: 模型必须反映刚体铰接和板长约束",
        "可解性: 必须能在合理时间内完成300s×224把手的数值仿真",
        "精度: 位置速度需保留6位小数，碰撞时刻需精确到秒级",
        "可扩展性: 模型需能覆盖Q1-Q5全部子问题",
        "方法卡匹配度: 尽量从可用方法卡中选择最接近的",
    ],
    "confidence": 0.82,
}

# ============================================================
# Node 3: solving_strategy
# ============================================================
m3 = common("solving_strategy", 3, 241, 310, 69.0)
m3["payload"] = {
    "decision": "分阶段求解策略：(1) 螺线参数化与龙头轨迹解析求解；(2) 刚体链几何递推计算各把手位置；(3) 中心差分数值微分求速度；(4) 逐帧碰撞扫描确定Q2终止时刻；(5) 一维搜索求解Q3最小螺距和Q5最大速度；(6) Q4S形曲线几何构造+仿真。时间步长dt=0.01s，输出间隔1s。",
    "alternatives": [
        "全ODE积分法: 将224个把手的运动方程写成DAE系统用数值积分器求解，精度高但计算量大",
        "纯解析法: 假设所有把手严格在螺线上，通过弧长差直接映射，忽略板长方向偏差",
        "模型预测控制: 逐步优化每节板凳姿态，过于复杂且不必要",
    ],
    "reasoning": "1) 龙头轨迹有解析解（阿基米德螺线+匀速约束→角速度ODE可分离变量积分），无需数值积分；2) 各把手位置由龙头位置和板长约束通过几何递推唯一确定，递推复杂度O(N) per frame；3) 速度通过位置的中心差分获得，精度满足6位小数要求；4) 碰撞检测只需扫描非相邻把手对，可用空间哈希加速；5) Q3和Q5本质是一维约束优化，黄金分割法高效可靠；6) Q4S形曲线可通过几何相切条件解析构造。",
    "algorithm": """
算法: 板凳龙运动学仿真
输入: 螺距p, 龙头速度v0, 初始半径R_A, 时间范围[t_start, t_end]
输出: 各时刻224个把手的位置(x_i,y_i)和速度v_i

1. 螺线参数化: b = p/(2π), R(θ) = R_A - bθ
2. 龙头角速度: dθ/dt = v0 / sqrt(R(θ)² + b²)
   数值积分θ(t) using RK4 or analytical approximation
3. 龙头位置: x_1 = R(θ)cos(θ), y_1 = R(θ)sin(θ)
   (顺时针盘入时θ取负值或调整坐标方向)
4. 刚体链递推 for i = 2..224:
   ℓ_i = (L_head - 2d_offset) if i==2 else (L_body - 2d_offset)
   direction = (r_{i-1} - r_{i-2}) / ||r_{i-1} - r_{i-2}||
   r_i = r_{i-1} + ℓ_i * direction
   (注意: 各把手需投影回螺线上)
5. 速度计算: v_i = (r_i(t+dt) - r_i(t-dt)) / (2dt)
6. 碰撞检测: for all i<j with |i-j|>1:
   if ||r_i - r_j|| < W: 记录碰撞时刻
7. Q3: 一维搜索最小p使R(θ_final) ≥ R_turn
8. Q4: 构造S形曲线(两段相切圆弧), 仿真-100s到100s
9. Q5: 一维搜索最大v_head使max_i,t v_i ≤ 2.0
""",
    "feasibility": {
        "computational_complexity": "O(T/dt × N²) for collision detection, O(T/dt × N) for simulation; N=224, T=300s, dt=0.01s → ~6.7M frame-sections, feasible in Python with vectorization",
        "numerical_stability": "刚体递推无累积误差（每帧独立从龙头重算），中心差分二阶精度",
        "implementation_effort": "中等，核心递推约100行代码，优化部分约50行",
        "risk_points": [
            "把手投影回螺线的数值精度",
            "碰撞检测的时间分辨率（可能需要子步长）",
            "Q4 S形曲线的相切条件求解",
        ],
    },
}

# ============================================================
# Node 4: validation_plan
# ============================================================
m4 = common("validation_plan", 4, 311, 370, 59.0)
m4["payload"] = {
    "decision": "多层验证策略：(1) 刚体约束守恒验证（相邻把手间距误差<1e-6）；(2) 螺线约束验证（各把手到螺线距离<1e-4）；(3) 龙头速度验证（||v_1||-1.0 < 1e-6）；(4) 碰撞检测敏感性分析（板宽±10%对碰撞时刻的影响）；(5) 时间步长收敛性验证（dt=0.01 vs dt=0.005）；(6) Q3/Q5优化结果的边界验证。",
    "alternatives": [
        "仅做结果合理性检查: 人工审查数值范围，不够严格",
        "蒙特卡洛验证: 随机扰动参数验证结果鲁棒性，计算量大",
        "与解析极限对比: 在特殊参数下（如螺距→0）验证模型退化为已知解",
    ],
    "reasoning": "1) 刚体约束守恒是运动学模型的核心物理约束，必须逐帧验证；2) 螺线约束是题面硬性要求，把手偏离螺线会导致结果无效；3) 龙头速度是边界条件，验证其守恒可确认积分器正确性；4) 碰撞时刻对板宽敏感，敏感性分析可评估结果稳健性；5) 时间步长收敛性验证确保数值解逼近真实解；6) 优化问题的边界验证确保最优解在可行域边界上。",
    "sensitivity_analysis": {
        "parameters_to_vary": [
            {"name": "板宽W", "range": "±10%", "impact_on": "Q2碰撞时刻t_collision"},
            {"name": "板长L_body", "range": "±5%", "impact_on": "Q1位置精度, Q2碰撞时刻"},
            {"name": "螺距p_in", "range": "±10%", "impact_on": "Q2碰撞时刻, Q3最小螺距"},
            {"name": "龙头速度v0", "range": "±10%", "impact_on": "Q1速度分布, Q5最大速度"},
            {"name": "时间步长dt", "range": "0.01s vs 0.005s vs 0.001s", "impact_on": "数值收敛性"},
        ],
        "method": "单因素敏感性分析，每次变动一个参数，记录关键输出变化量，计算弹性系数",
        "expected_outcome": "碰撞时刻对板宽最敏感（弹性系数~0.3-0.5），对螺距中等敏感，对板长低敏感",
    },
    "validation_methods": [
        "刚体约束守恒: 逐帧检查||r_i - r_{i-1}|| - ℓ_i < 1e-6 (相对误差)",
        "螺线约束验证: 各把手到最近螺线点的距离 < 1e-4 m",
        "龙头速度守恒: ||v_1(t)|| - 1.0 < 1e-6 m/s",
        "能量/动量类比: 虽无动力学，但可验证总弧长守恒",
        "碰撞检测交叉验证: 用不同时间步长(0.01s, 0.005s)计算碰撞时刻，差异<0.5s",
        "优化结果验证: Q3最小螺距代入仿真验证龙头确实到达调头空间边界；Q5最大速度代入验证所有把手速度≤2m/s",
        "极端情况测试: 螺距→0时板凳龙应紧密盘绕，碰撞时刻应提前；龙头速度→0时所有把手速度应→0",
    ],
}

# Write all manifests
manifests = [
    ("00_problem_understanding.json", m0),
    ("01_model_construction.json", m1),
    ("02_method_selection.json", m2),
    ("03_solving_strategy.json", m3),
    ("04_validation_plan.json", m4),
]

for fname, data in manifests:
    path = OUT_DIR / fname
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {fname} ({len(json.dumps(data))} bytes)")

print("\nAll 5 manifests generated.")
