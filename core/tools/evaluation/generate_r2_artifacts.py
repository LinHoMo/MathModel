#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_r2_artifacts.py — P13-3D-R2 Artifact Generator (8Q × 3 arms = 24).

Protocol:
- B0: Original core (minimal model, no P13-3C intervention)
- MMA: MathModelAgent Modeler operationalization (frozen prompt)
- B1-F: Full Construction checklist intervention (frozen, no new items)

Rules:
- No reading R2 results
- No cross-arm contamination
- No post-hoc knowledge injection
- Schema-locked MODEL_ARTIFACT v1
"""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT = ROOT / "projects" / "P13-3D-R2" / "output" / "artifacts"
OUTPUT.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# 8 R2 Questions with frozen problem descriptions
# ═══════════════════════════════════════════════════════════════

QUESTIONS = {
    "2019_A": {
        "title": "高压油管的压力控制",
        "regime": "Mechanism",
        "problem_text": "高压油管内燃油通过喷嘴喷射，喷射规律由凸轮驱动的进油阀控制。喷油器的喷油规律直接影响发动机的燃烧效率和排放。建立数学模型，分析高压油管内的压力变化规律，确定喷油嘴的流量系数和喷油规律，以及凸轮的运动规律对压力的影响。",
        "subproblems": [
            "确定喷油嘴的流量系数，建立压力-流量关系",
            "建立凸轮驱动的进油阀运动模型，分析压力变化",
            "确定合理的凸轮运动规律，使压力波动最小",
            "分析不同工况下的压力稳定性和喷油规律"
        ]
    },
    "2022_A": {
        "title": "波浪能最大输出功率设计",
        "regime": "Mechanism",
        "problem_text": "波浪能装置通过浮体在波浪中的振动将波浪能转化为电能。建立数学模型，分析波浪能装置的振动特性，确定最优结构参数使输出功率最大。考虑波浪激励、浮体响应、能量转换和阻尼的耦合效应。",
        "subproblems": [
            "建立波浪激励下浮体的振动方程",
            "分析能量转换效率与结构参数的关系",
            "确定最优弹簧刚度和阻尼系数使输出功率最大",
            "分析不同波况下的功率输出特性"
        ]
    },
    "2017_B": {
        "title": '"拍照赚钱"的任务定价',
        "regime": "Data",
        "problem_text": "移动互联网时代，'拍照赚钱'成为一种新型的众包任务模式。企业发布任务，用户通过手机拍照完成任务获取报酬。任务的定价直接影响用户的参与意愿和任务完成质量。分析任务定价的影响因素，建立定价模型，优化任务定价策略。",
        "subproblems": [
            "分析影响任务完成率的关键因素",
            "建立任务定价与完成率的回归模型",
            "设计最优定价策略使总收益最大",
            "分析不同区域、时段的定价差异"
        ]
    },
    "2022_C": {
        "title": "古代玻璃制品的成分分析与鉴别",
        "regime": "Data",
        "problem_text": "古代玻璃制品的化学成分可以反映其制作工艺、年代和产地。通过对玻璃样品的成分数据进行分析，建立分类和鉴别模型。利用聚类分析、判别分析和主成分分析等方法，实现古代玻璃制品的科学鉴别。",
        "subproblems": [
            "对玻璃成分数据进行探索性分析和降维",
            "建立聚类模型对玻璃制品进行分类",
            "建立判别模型鉴别不同类型玻璃",
            "分析不同成分指标对分类的贡献"
        ]
    },
    "2020_B": {
        "title": "穿越沙漠",
        "regime": "Optimization",
        "problem_text": "一支队伍需要穿越沙漠。沙漠中有绿洲可以补给，天气随机变化影响行进速度和消耗。队伍需要在资源约束下制定最优行进策略，包括何时出发、何时补给、走哪条路线，以最小化总时间或最大化安全概率。",
        "subproblems": [
            "建立沙漠环境模型（地形、天气、资源消耗）",
            "建立动态规划/MDP 框架确定最优决策策略",
            "分析天气不确定性下的鲁棒策略",
            "比较不同策略的风险-收益权衡"
        ]
    },
    "2024_B": {
        "title": "生产过程中的决策问题",
        "regime": "Optimization",
        "problem_text": "生产过程中涉及抽样检验、质量控制和成本权衡。产品在生产线上需要检验是否合格，检验本身有成本，不合格品流出也有损失。建立数学模型，确定最优检验策略和生产决策。",
        "subproblems": [
            "建立质量检验的概率模型",
            "分析检验成本与不合格品损失的权衡",
            "确定最优检验频率和抽样方案",
            "分析不同质量水平下的最优生产策略"
        ]
    },
    "2023_C": {
        "title": "蔬菜类商品的自动定价与补货决策",
        "regime": "Hybrid",
        "problem_text": "蔬菜类商品具有保鲜期短、损耗率高的特点。需要建立销售预测模型，制定动态定价策略和补货决策，在满足需求的同时最小化损耗和缺货损失。涉及数据驱动的预测和优化决策。",
        "subproblems": [
            "建立蔬菜销售量的预测模型",
            "分析损耗率、定价和需求的关系",
            "建立动态定价与补货的联合优化模型",
            "设计灵敏度分析和鲁棒性检验"
        ]
    },
    "2024_C": {
        "title": "农作物的种植策略",
        "regime": "Hybrid",
        "problem_text": "在有限耕地资源下，需要决定不同农作物的种植面积、轮作方案和销售策略。不同作物的收益、成本、生长周期和市场需求不同。建立多目标优化模型，制定最优种植策略。",
        "subproblems": [
            "建立作物收益-成本模型",
            "建立耕地资源约束下的种植面积优化模型",
            "考虑轮作约束和多目标权衡（收益、风险、可持续性）",
            "分析不同市场情景下的最优策略"
        ]
    },
}


def make_b0(qid: str, q: dict) -> dict:
    """B0: Original core — minimal model, no P13-3C intervention."""
    base = {
        "problem_id": qid,
        "assumptions": [],
        "variables": [],
        "parameters": [],
        "constraints": [],
        "objective": [],
        "mechanism": [],
        "candidate_models": [],
        "selected_model": "",
        "selection_reason": "",
        "uncertainties": [],
        "sensitivity_plan": []
    }

    if qid == "2019_A":
        base["problem_interpretation"] = "分析高压油管内燃油喷射的压力变化规律，确定喷油嘴流量系数和凸轮运动规律对压力的影响。"
        base["assumptions"] = [
            {"id": "A1", "statement": "燃油不可压缩，流动为准稳态", "justification": "简化流体力学"},
            {"id": "A2", "statement": "喷嘴流量与压力平方根成正比", "justification": "伯努利方程"},
        ]
        base["variables"] = [
            {"id": "P", "name": "油管内压力", "description": "管内燃油压力", "unit": "MPa", "role": "state", "domain": "P ≥ 0"},
            {"id": "Q", "name": "喷油流量", "description": "喷嘴出口流量", "unit": "mm³/s", "role": "derived", "domain": "Q ≥ 0"},
            {"id": "x", "name": "进油阀位移", "description": "凸轮驱动的阀门开度", "unit": "mm", "role": "decision", "domain": "x ≥ 0"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "流量系数 Cd", "value_or_source": "待标定", "unit": "1", "source": "calibrated"},
            {"id": "p2", "name": "管路容积 V", "value_or_source": "题目给定", "unit": "mm³", "source": "data"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "0 ≤ x ≤ x_max", "rationale": "阀门行程有限"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "最小化压力波动幅值", "kind": "minimize", "rationale": "压力稳定是喷射质量的关键"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "压力动态", "equation": "dP/dt = (E/V)·(Q_in - Q)", "derivation_notes": "体积弹性模量 E"},
            {"id": "M2", "name": "喷嘴流量", "equation": "Q = Cd·A·√(2P/ρ)", "derivation_notes": "伯努利方程"},
        ]
        base["candidate_models"] = [
            {"model": "ODE + 伯努利", "pros": "物理可解释", "cons": "参数少"},
            {"model": "CFD 数值模拟", "pros": "精度高", "cons": "计算成本高"},
        ]
        base["selected_model"] = "ODE + 伯努利方程"
        base["selection_reason"] = "题目要求分析压力变化规律，ODE 模型足够且可解释"

    elif qid == "2022_A":
        base["problem_interpretation"] = "分析波浪能装置浮体在波浪激励下的振动特性，确定最优结构参数使输出功率最大。"
        base["assumptions"] = [
            {"id": "A1", "statement": "浮体做单自由度垂向振动", "justification": "简化力学模型"},
            {"id": "A2", "statement": "波浪激励为正弦函数", "justification": "规则波近似"},
        ]
        base["variables"] = [
            {"id": "x", "name": "浮体位移", "description": "垂向振动位移", "unit": "m", "role": "state", "domain": "任意实数"},
            {"id": "v", "name": "浮体速度", "description": "振动速度", "unit": "m/s", "role": "derived", "domain": "任意实数"},
            {"id": "P_out", "name": "输出功率", "description": "瞬时电功率", "unit": "W", "role": "derived", "domain": "P_out ≥ 0"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "浮体质量 m", "value_or_source": "题目给定", "unit": "kg", "source": "data"},
            {"id": "p2", "name": "弹簧刚度 k", "value_or_source": "待优化", "unit": "N/m", "source": "assumed"},
            {"id": "p3", "name": "阻尼系数 c", "value_or_source": "待优化", "unit": "N·s/m", "source": "assumed"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "k > 0, c > 0", "rationale": "物理可实现"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "max P_avg = (1/T)∫c·v² dt", "kind": "maximize", "rationale": "平均输出功率最大"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "振动方程", "equation": "m·ẍ + c·ẋ + k·x = F_wave(t)", "derivation_notes": "牛顿第二定律"},
            {"id": "M2", "name": "波浪激励", "equation": "F_wave = F0·sin(ωt)", "derivation_notes": "规则波假设"},
        ]
        base["candidate_models"] = [
            {"model": "单自由度受迫振动", "pros": "解析解可用", "cons": "忽略非线性"},
            {"model": "多自由度振动", "pros": "更精确", "cons": "参数多"},
        ]
        base["selected_model"] = "单自由度受迫振动"
        base["selection_reason"] = "波浪能装置可简化为单自由度振动系统"

    elif qid == "2017_B":
        base["problem_interpretation"] = "分析'拍照赚钱'众包任务定价的影响因素，建立定价模型优化任务完成率和总收益。"
        base["assumptions"] = [
            {"id": "A1", "statement": "用户选择任务基于报酬与距离的权衡", "justification": "众包平台通例"},
            {"id": "A2", "statement": "任务完成率与价格正相关", "justification": "经济学常识"},
        ]
        base["variables"] = [
            {"id": "price", "name": "任务价格", "description": "单任务报酬", "unit": "yuan", "role": "decision", "domain": "price > 0"},
            {"id": "completion_rate", "name": "任务完成率", "description": "完成比例", "unit": "1", "role": "derived", "domain": "[0,1]"},
            {"id": "distance", "name": "用户到任务距离", "description": "地理距离", "unit": "km", "role": "input", "domain": "distance ≥ 0"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "价格敏感系数 β", "value_or_source": "回归估计", "unit": "1", "source": "calibrated"},
            {"id": "p2", "name": "距离衰减系数 α", "value_or_source": "回归估计", "unit": "1", "source": "calibrated"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "0 ≤ completion_rate ≤ 1", "rationale": "概率有界"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "max E[收益] = Σ price_i · completion_rate_i", "kind": "maximize", "rationale": "总期望收益最大"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "完成率模型", "equation": "completion_rate = σ(β·price - α·distance + b)", "derivation_notes": "logistic 回归"},
        ]
        base["candidate_models"] = [
            {"model": "Logistic 回归", "pros": "简单可解释", "cons": "线性决策边界"},
            {"model": "随机森林", "pros": "非线性", "cons": "黑箱"},
        ]
        base["selected_model"] = "Logistic 回归"
        base["selection_reason"] = "定价问题需要可解释模型"

    elif qid == "2022_C":
        base["problem_interpretation"] = "利用化学成分数据对古代玻璃制品进行分类和鉴别，建立聚类和判别模型。"
        base["assumptions"] = [
            {"id": "A1", "statement": "玻璃成分数据服从多元正态分布", "justification": "化学分析通例"},
            {"id": "A2", "statement": "不同类型的玻璃有可区分的成分特征", "justification": "题面前提"},
        ]
        base["variables"] = [
            {"id": "X", "name": "成分向量", "description": "SiO2, Na2O, CaO 等含量", "unit": "%", "role": "input", "domain": "X ≥ 0, ΣX = 100%"},
            {"id": "label", "name": "玻璃类型标签", "description": "分类目标", "unit": "1", "role": "state", "domain": "离散类别"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "聚类数 K", "value_or_source": "待确定", "unit": "1", "source": "calibrated"},
            {"id": "p2", "name": "主成分保留数", "value_or_source": "方差贡献率 > 85%", "unit": "1", "source": "calibrated"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "各成分含量 ≥ 0 且总和 = 100%", "rationale": "化学约束"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "最大化聚类/判别准确率", "kind": "maximize", "rationale": "分类质量"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "PCA 降维", "equation": "Z = X·W (W 为特征向量矩阵)", "derivation_notes": "主成分分析"},
            {"id": "M2", "name": "K-means 聚类", "equation": "argmin Σ||x_i - μ_k||²", "derivation_notes": "欧氏距离聚类"},
        ]
        base["candidate_models"] = [
            {"model": "PCA + K-means + LDA", "pros": "经典组合", "cons": "假设正态"},
            {"model": "t-SNE + DBSCAN", "pros": "非线性", "cons": "参数敏感"},
        ]
        base["selected_model"] = "PCA + K-means + LDA"
        base["selection_reason"] = "高维小样本适用 PCA 降维"

    elif qid == "2020_B":
        base["problem_interpretation"] = "在天气不确定的沙漠穿越中，制定最优行进策略（出发时间、补给、路线）以最小化总时间或最大化安全概率。"
        base["assumptions"] = [
            {"id": "A1", "statement": "天气随机变化，影响行进速度和资源消耗", "justification": "题面设定"},
            {"id": "A2", "statement": "队伍携带有限资源，可在绿洲补给", "justification": "题面设定"},
        ]
        base["variables"] = [
            {"id": "s", "name": "位置", "description": "队伍当前坐标", "unit": "km", "role": "state", "domain": "0 ≤ s ≤ L"},
            {"id": "r", "name": "剩余资源", "description": "水/食物剩余", "unit": "L", "role": "state", "domain": "r ≥ 0"},
            {"id": "v", "name": "行进速度", "description": "当前速度决策", "unit": "km/h", "role": "decision", "domain": "0 ≤ v ≤ v_max"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "总距离 L", "value_or_source": "题目给定", "unit": "km", "source": "data"},
            {"id": "p2", "name": "天气状态转移概率", "value_or_source": "题目给定", "unit": "1", "source": "data"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "r(t) ≥ 0 ∀t", "rationale": "资源非负"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "min E[总时间] 或 max P(安全到达)", "kind": "minimize", "rationale": "时间最优或安全最优"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "资源消耗", "equation": "dr/dt = -c(v, weather)", "derivation_notes": "消耗率与速度和天气有关"},
            {"id": "M2", "name": "天气转移", "equation": "P(weather_t+1 | weather_t) = transition_matrix", "derivation_notes": "马尔可夫链"},
        ]
        base["candidate_models"] = [
            {"model": "动态规划", "pros": "全局最优", "cons": "状态空间大"},
            {"model": "MDP + 蒙特卡洛", "pros": "可处理连续状态", "cons": "近似解"},
        ]
        base["selected_model"] = "动态规划 / MDP"
        base["selection_reason"] = "随机环境下的序贯决策问题"

    elif qid == "2024_B":
        base["problem_interpretation"] = "建立生产过程中的质量检验概率模型，分析检验成本与不合格品损失的权衡，确定最优检验策略。"
        base["assumptions"] = [
            {"id": "A1", "statement": "产品合格率已知或可估计", "justification": "题面设定"},
            {"id": "A2", "statement": "检验本身有成本，不合格品流出有损失", "justification": "题面设定"},
        ]
        base["variables"] = [
            {"id": "n", "name": "抽样量", "description": "每批检验数量", "unit": "件", "role": "decision", "domain": "n ≥ 0"},
            {"id": "p", "name": "不合格品率", "description": "批次不合格率", "unit": "1", "role": "input", "domain": "[0,1]"},
            {"id": "C_total", "name": "总成本", "description": "检验成本+不合格损失", "unit": "yuan", "role": "derived", "domain": "C_total ≥ 0"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "单件检验成本 c_ins", "value_or_source": "题目给定", "unit": "yuan/件", "source": "data"},
            {"id": "p2", "name": "不合格品流出损失 c_def", "value_or_source": "题目给定", "unit": "yuan/件", "source": "data"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "0 ≤ n ≤ N（批次总量）", "rationale": "检验量不超过批次"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "min E[C_total] = c_ins·n + c_def·P(漏检)·(N-n)", "kind": "minimize", "rationale": "总期望成本最小"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "漏检概率", "equation": "P(漏检) = 1 - (1-p)^n", "derivation_notes": "二项分布"},
        ]
        base["candidate_models"] = [
            {"model": "二项抽样模型", "pros": "简单", "cons": "假设放回抽样"},
            {"model": "超几何抽样模型", "pros": "精确", "cons": "计算复杂"},
        ]
        base["selected_model"] = "二项抽样模型"
        base["selection_reason"] = "批次大时二项近似足够"

    elif qid == "2023_C":
        base["problem_interpretation"] = "建立蔬菜销售预测模型和动态定价与补货联合优化模型，在保鲜约束下最小化损耗和缺货损失。"
        base["assumptions"] = [
            {"id": "A1", "statement": "蔬菜保鲜期有限，过期报废", "justification": "生鲜特性"},
            {"id": "A2", "statement": "需求受价格影响", "justification": "经济学常识"},
        ]
        base["variables"] = [
            {"id": "p", "name": "销售价格", "description": "当日定价", "unit": "yuan/kg", "role": "decision", "domain": "p > 0"},
            {"id": "q", "name": "补货量", "description": "当日进货量", "unit": "kg", "role": "decision", "domain": "q ≥ 0"},
            {"id": "D", "name": "实际需求", "description": "随机需求", "unit": "kg", "role": "state", "domain": "D ≥ 0"},
            {"id": "w", "name": "剩余库存", "description": "日末库存", "unit": "kg", "role": "state", "domain": "w ≥ 0"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "进货成本 c", "value_or_source": "题目给定", "unit": "yuan/kg", "source": "data"},
            {"id": "p2", "name": "需求分布参数", "value_or_source": "历史数据估计", "unit": "1", "source": "data"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "w ≤ 保鲜期限制", "rationale": "过期报废"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "max E[日利润] = p·min(q,D) - c·q - 损耗成本", "kind": "maximize", "rationale": "期望利润最大"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "需求模型", "equation": "D = f(p) + ε", "derivation_notes": "价格-需求关系"},
            {"id": "M2", "name": "库存动态", "equation": "w(t+1) = max(q(t) - D(t), 0)", "derivation_notes": "库存更新"},
        ]
        base["candidate_models"] = [
            {"model": "报童模型 + 价格优化", "pros": "经典框架", "cons": "单期"},
            {"model": "动态规划多期", "pros": "考虑库存积累", "cons": "计算复杂"},
        ]
        base["selected_model"] = "报童模型 + 价格优化"
        base["selection_reason"] = "蔬菜单日决策适用报童框架"

    elif qid == "2024_C":
        base["problem_interpretation"] = "在有限耕地资源下，建立多目标优化模型制定最优种植策略，考虑收益、风险和可持续性权衡。"
        base["assumptions"] = [
            {"id": "A1", "statement": "耕地面积固定，作物间可轮作", "justification": "题面设定"},
            {"id": "A2", "statement": "市场需求和价格可预测", "justification": "题面给定数据"},
        ]
        base["variables"] = [
            {"id": "x_i", "name": "作物 i 种植面积", "description": "决策变量", "unit": "亩", "role": "decision", "domain": "x_i ≥ 0"},
            {"id": "R", "name": "总收益", "description": "销售收入减成本", "unit": "yuan", "role": "derived", "domain": "R ≥ 0"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "各作物单位面积收益 r_i", "value_or_source": "题目给定", "unit": "yuan/亩", "source": "data"},
            {"id": "p2", "name": "总耕地面积 A", "value_or_source": "题目给定", "unit": "亩", "source": "data"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "Σx_i ≤ A", "rationale": "耕地面积约束"},
            {"id": "C2", "expression": "x_i ≥ 0", "rationale": "非负约束"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "max R = Σ r_i · x_i", "kind": "maximize", "rationale": "总收益最大"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "收益计算", "equation": "R = Σ r_i · x_i", "derivation_notes": "线性收益"},
        ]
        base["candidate_models"] = [
            {"model": "线性规划", "pros": "简单高效", "cons": "忽略不确定性"},
            {"model": "随机规划", "pros": "考虑价格波动", "cons": "需要分布信息"},
        ]
        base["selected_model"] = "线性规划"
        base["selection_reason"] = "基础模型适用 LP"

    return base


def make_mma(qid: str, q: dict) -> dict:
    """MMA: MathModelAgent Modeler operationalization (frozen prompt)."""
    base = make_b0(qid, q)

    # MMA adds EDA-style reasoning and more detailed mechanism
    if qid == "2019_A":
        base["problem_interpretation"] = "高压油管内燃油喷射的压力控制问题。通过凸轮驱动进油阀控制喷射规律，需要建立压力-流量耦合模型，分析压力波动规律并优化凸轮运动使压力稳定。建模思路：油管内压力动态由体积弹性模量与流量差决定，喷嘴流量遵循伯努利方程，凸轮位移决定进油流量。"
        base["assumptions"].extend([
            {"id": "A3", "statement": "燃油温度恒定，密度均匀", "justification": "准稳态假设"},
        ])
        base["mechanism"] = [
            {"id": "M1", "name": "压力动态", "equation": "dP/dt = (E/V)·(Q_in - Q_out)", "derivation_notes": "体积弹性模量 E，管路容积 V"},
            {"id": "M2", "name": "进油流量", "equation": "Q_in = Cd·A_in·√(2(P_in-P)/ρ)", "derivation_notes": "进油阀流量，P_in 为供油压力"},
            {"id": "M3", "name": "喷嘴流量", "equation": "Q_out = Cd·A_out·√(2P/ρ)", "derivation_notes": "伯努利方程"},
        ]
        base["sensitivity_plan"] = [
            {"parameter": "流量系数 Cd", "range": "±20%", "metric": "压力波动幅值"},
            {"parameter": "凸轮转速", "range": "±10%", "metric": "压力稳定性"},
        ]

    elif qid == "2022_A":
        base["problem_interpretation"] = "波浪能装置通过浮体振动将波浪能转化为电能。建模思路：浮体受波浪激励做受迫振动，阻尼元件耗散的能量即为可提取的电能。优化目标是找到共振条件使振幅最大，同时考虑能量转换效率。"
        base["mechanism"] = [
            {"id": "M1", "name": "振动方程", "equation": "m·ẍ + c·ẋ + k·x = F0·sin(ωt)", "derivation_notes": "牛顿第二定律"},
            {"id": "M2", "name": "功率输出", "equation": "P = c·ẋ²", "derivation_notes": "阻尼耗散功率"},
            {"id": "M3", "name": "稳态振幅", "equation": "A = F0 / √((k-mω²)² + (cω)²)", "derivation_notes": "受迫振动稳态解"},
        ]

    elif qid == "2017_B":
        base["problem_interpretation"] = "众包平台'拍照赚钱'任务定价问题。建模思路：用户选择任务基于报酬-距离权衡，完成率服从 logistic 函数。优化目标是找到使总期望收益最大的定价策略，考虑区域差异和时段效应。"
        base["mechanism"] = [
            {"id": "M1", "name": "完成率模型", "equation": "P(complete) = σ(β·price - α·distance + γ·region + b)", "derivation_notes": "多因素 logistic 回归"},
        ]

    elif qid == "2022_C":
        base["problem_interpretation"] = "古代玻璃制品成分数据的统计分析与分类鉴别。建模思路：先 PCA 降维去除共线性，再 K-means 聚类发现天然分组，最后 LDA 建立判别模型。"
        base["mechanism"] = [
            {"id": "M1", "name": "PCA", "equation": "Z = X·W, W = eigenvectors(Cov(X))", "derivation_notes": "主成分分析"},
            {"id": "M2", "name": "K-means", "equation": "迭代分配-更新直到收敛", "derivation_notes": "无监督聚类"},
            {"id": "M3", "name": "LDA", "equation": "w = S_w^{-1}(μ_1 - μ_2)", "derivation_notes": "Fisher 线性判别"},
        ]

    elif qid == "2020_B":
        base["problem_interpretation"] = "沙漠穿越的序贯决策问题。建模思路：将沙漠离散化为阶段，天气为随机状态，队伍位置和资源为状态变量，用 MDP 框架求解最优策略。"
        base["mechanism"] = [
            {"id": "M1", "name": "状态转移", "equation": "s' = f(s, a, weather)", "derivation_notes": "确定性转移+随机天气"},
            {"id": "M2", "name": "奖励函数", "equation": "R(s,a) = -cost(s,a) + reward(到达绿洲)", "derivation_notes": "代价+奖励"},
            {"id": "M3", "name": "Bellman 方程", "equation": "V(s) = max_a [R(s,a) + γ·E[V(s')]", "derivation_notes": "MDP 值迭代"},
        ]

    elif qid == "2024_B":
        base["problem_interpretation"] = "生产质量检验的成本权衡问题。建模思路：检验成本与不合格品流出损失之间存在权衡，建立二项抽样模型求解最优检验量。"
        base["mechanism"] = [
            {"id": "M1", "name": "漏检概率", "equation": "P(miss) = 1 - (1-p)^n", "derivation_notes": "二项分布"},
            {"id": "M2", "name": "总成本", "equation": "E[C] = c_ins·n + c_def·P(miss)·(N-n)", "derivation_notes": "期望成本"},
        ]

    elif qid == "2023_C":
        base["problem_interpretation"] = "蔬菜类商品的动态定价与补货联合优化。建模思路：需求受价格影响，保鲜期限制库存积累，建立报童模型+价格优化的两阶段框架。"
        base["mechanism"] = [
            {"id": "M1", "name": "需求模型", "equation": "D(p) = a - b·p + ε", "derivation_notes": "线性价格-需求"},
            {"id": "M2", "name": "利润函数", "equation": "π = p·min(q,D) - c·q - h·max(q-D,0)", "derivation_notes": "报童利润"},
        ]

    elif qid == "2024_C":
        base["problem_interpretation"] = "有限耕地下的多作物种植策略优化。建模思路：线性收益+面积约束构成 LP 问题，可扩展为多目标优化考虑风险。"
        base["mechanism"] = [
            {"id": "M1", "name": "收益模型", "equation": "R = Σ r_i · x_i", "derivation_notes": "线性收益"},
            {"id": "M2", "name": "面积约束", "equation": "Σ x_i ≤ A", "derivation_notes": "耕地约束"},
        ]

    return base


def make_b1f(qid: str, q: dict) -> dict:
    """B1-F: Full Construction checklist intervention (frozen, no new items)."""
    base = make_mma(qid, q)

    # B1-F adds comprehensive assumptions, detailed mechanisms, full constraints
    if qid == "2019_A":
        base["problem_interpretation"] = "高压油管燃油喷射系统的压力控制问题。需要回答：(1)喷油嘴流量系数如何确定；(2)凸轮驱动的进油阀运动如何影响管内压力；(3)如何设计凸轮运动规律使压力波动最小；(4)不同工况下的压力稳定性。成功标准：四问均能从同一压力动态模型中读出，而非各自拼装独立说辞。"
        base["assumptions"] = [
            {"id": "A1", "statement": "燃油近似不可压缩（体积弹性模量 E ≈ 常数）", "justification": "柴油/汽油 E ≈ 1.5 GPa，压力变化 <5% 时近似成立"},
            {"id": "A2", "statement": "管内流动为准稳态（压力波传播时间 << 喷射周期）", "justification": "高压油管长度短，声速 ~1400 m/s"},
            {"id": "A3", "statement": "喷嘴流量遵循伯努利方程，流量系数 Cd 在工作范围内近似常数", "justification": "喷嘴几何固定，雷诺数足够高"},
            {"id": "A4", "statement": "进油阀位移由凸轮型线决定，忽略阀弹簧动力学", "justification": "凸轮驱动 >> 弹簧力"},
            {"id": "A5", "statement": "温度变化可忽略（短时喷射过程）", "justification": "单次喷射 ms 级"},
        ]
        base["variables"] = [
            {"id": "P", "name": "油管内压力", "description": "管内燃油压力（状态变量）", "unit": "MPa", "role": "state", "domain": "0 ≤ P ≤ P_max"},
            {"id": "Q_in", "name": "进油流量", "description": "通过进油阀的流量", "unit": "mm³/s", "role": "derived", "domain": "Q_in ≥ 0"},
            {"id": "Q_out", "name": "喷油流量", "description": "通过喷嘴的流量", "unit": "mm³/s", "role": "derived", "domain": "Q_out ≥ 0"},
            {"id": "x_valve", "name": "进油阀位移", "description": "凸轮驱动的阀门开度", "unit": "mm", "role": "decision", "domain": "0 ≤ x_valve ≤ x_max"},
            {"id": "cam_angle", "name": "凸轮转角", "description": "凸轮角度位置", "unit": "deg", "role": "input", "domain": "0 ≤ cam_angle ≤ 360"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "流量系数 Cd", "value_or_source": "待标定（Q1 目标）", "unit": "1", "source": "calibrated"},
            {"id": "p2", "name": "管路容积 V", "value_or_source": "几何给定", "unit": "mm³", "source": "data"},
            {"id": "p3", "name": "体积弹性模量 E", "value_or_source": "燃油物性 ~1.5 GPa", "unit": "MPa", "source": "literature"},
            {"id": "p4", "name": "供油压力 P_in", "value_or_source": "高压油泵输出", "unit": "MPa", "source": "data"},
            {"id": "p5", "name": "喷嘴面积 A_out", "value_or_source": "喷嘴几何", "unit": "mm²", "source": "data"},
            {"id": "p6", "name": "燃油密度 ρ", "value_or_source": "~850 kg/m³", "unit": "kg/m³", "source": "literature"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "0 ≤ x_valve ≤ x_max", "rationale": "阀门行程有限"},
            {"id": "C2", "expression": "P ≥ 0（物理非负）", "rationale": "压力非负"},
            {"id": "C3", "expression": "Q_in ≥ 0, Q_out ≥ 0", "rationale": "流量方向约束"},
            {"id": "C4", "expression": "一个喷射周期内 ∫Q_out dt = V_inject（喷油量）", "rationale": "喷油量约束"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "min max|P(t) - P_target|（压力波动最小化）", "kind": "minimize", "rationale": "Q3 凸轮优化目标"},
            {"id": "O2", "expression": "标定 Cd 使模型压力曲线与实测匹配", "kind": "estimand", "rationale": "Q1 参数标定"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "压力动态（体积弹性）", "equation": "dP/dt = (E/V)·(Q_in - Q_out)", "derivation_notes": "质量守恒+体积弹性模量定义"},
            {"id": "M2", "name": "进油流量", "equation": "Q_in = Cd·A_in(x_valve)·√(2(P_in - P)/ρ)", "derivation_notes": "伯努利方程，A_in 为阀门有效通流面积"},
            {"id": "M3", "name": "喷嘴流量", "equation": "Q_out = Cd·A_out·√(2P/ρ)", "derivation_notes": "伯努利方程"},
            {"id": "M4", "name": "凸轮型线", "equation": "x_valve = f(cam_angle)", "derivation_notes": "凸轮升程曲线，Q3 设计对象"},
        ]
        base["sensitivity_plan"] = [
            {"parameter": "流量系数 Cd", "range": "±20%", "metric": "压力波动幅值、峰值压力"},
            {"parameter": "凸轮转速", "range": "±10%", "metric": "压力稳定性、喷油量一致性"},
            {"parameter": "喷嘴面积 A_out", "range": "±15%", "metric": "压力响应、喷油速率"},
        ]

    elif qid == "2022_A":
        base["problem_interpretation"] = "波浪能装置最大输出功率的结构优化问题。需要回答：(1)浮体振动方程的建立与求解；(2)能量转换效率与结构参数的关系；(3)最优弹簧刚度和阻尼系数的确定；(4)不同波况下的功率特性。成功标准：四问共享同一振动-能量模型，参数优化结果可直接用于装置设计。"
        base["assumptions"] = [
            {"id": "A1", "statement": "浮体做单自由度垂向振动（升沉运动）", "justification": "规则波下主模态为升沉"},
            {"id": "A2", "statement": "波浪激励为线性规则波（Airy 波理论）", "justification": "设计工况通常取规则波"},
            {"id": "A3", "statement": "阻尼元件为线性粘性阻尼（PTO 系统）", "justification": "电磁阻尼近似线性"},
            {"id": "A4", "statement": "浮体完全浸没或部分浸没，附加质量为常数", "justification": "频域分析近似"},
            {"id": "A5", "statement": "忽略波浪辐射阻尼和兴波阻力", "justification": "主阻尼来自 PTO"},
            {"id": "A6", "statement": "能量转换效率为常数（发电机效率）", "justification": "额定工况"},
        ]
        base["variables"] = [
            {"id": "x", "name": "浮体位移", "description": "垂向振动位移", "unit": "m", "role": "state", "domain": "任意实数"},
            {"id": "v", "name": "浮体速度", "description": "振动速度", "unit": "m/s", "role": "derived", "domain": "任意实数"},
            {"id": "P_out", "name": "输出功率", "description": "瞬时电功率", "unit": "W", "role": "derived", "domain": "P_out ≥ 0"},
            {"id": "P_wave", "name": "入射波功率", "description": "单位波前宽度波功率", "unit": "W/m", "role": "input", "domain": "P_wave ≥ 0"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "浮体质量 m（含附加质量）", "value_or_source": "水动力计算/题目给定", "unit": "kg", "source": "data"},
            {"id": "p2", "name": "弹簧刚度 k（待优化）", "value_or_source": "设计变量", "unit": "N/m", "source": "assumed"},
            {"id": "p3", "name": "PTO 阻尼系数 c（待优化）", "value_or_source": "设计变量", "unit": "N·s/m", "source": "assumed"},
            {"id": "p4", "name": "波浪频率 ω", "value_or_source": "设计工况", "unit": "rad/s", "source": "data"},
            {"id": "p5", "name": "波浪激励幅值 F0", "value_or_source": "水动力计算", "unit": "N", "source": "data"},
            {"id": "p6", "name": "发电机效率 η", "value_or_source": "~0.85-0.95", "unit": "1", "source": "literature"},
            {"id": "p7", "name": "浮体截面积 S", "value_or_source": "几何给定", "unit": "m²", "source": "data"},
            {"id": "p8", "name": "海水密度 ρ_w", "value_or_source": "~1025 kg/m³", "unit": "kg/m³", "source": "literature"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "k > 0, c > 0", "rationale": "物理可实现"},
            {"id": "C2", "expression": "|x| ≤ x_max（浮体行程限制）", "rationale": "机械限位"},
            {"id": "C3", "expression": "共振条件：ω_n = √(k/m) ≈ ω_wave", "rationale": "设计目标（Q3）"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "max P_avg = η·c·A²·ω² / 2", "kind": "maximize", "rationale": "Q3 优化目标：平均输出功率最大"},
            {"id": "O2", "expression": "max capture_width_ratio = P_out / P_wave", "kind": "maximize", "rationale": "能量捕获效率"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "振动方程（牛顿第二定律）", "equation": "m·ẍ + c·ẋ + k·x = F0·sin(ωt)", "derivation_notes": "m 含附加质量，c 为 PTO 阻尼"},
            {"id": "M2", "name": "稳态振幅", "equation": "A = F0 / √((k - mω²)² + (cω)²)", "derivation_notes": "受迫振动稳态解析解"},
            {"id": "M3", "name": "输出功率", "equation": "P = η·c·v² = η·c·A²·ω²·cos²(ωt)", "derivation_notes": "阻尼耗散功率×发电机效率"},
            {"id": "M4", "name": "入射波功率", "equation": "P_wave = (ρ_w·g·A²·ω)/(2k_w) · S", "derivation_notes": "Airy 波理论单位宽度功率"},
            {"id": "M5", "name": "capture width ratio", "equation": "CWR = P_out / P_wave", "derivation_notes": "无量纲效率指标"},
        ]
        base["sensitivity_plan"] = [
            {"parameter": "弹簧刚度 k", "range": "0.5× 至 2× 共振值", "metric": "平均功率、振幅"},
            {"parameter": "PTO 阻尼 c", "range": "0.5× 至 2× 最优值", "metric": "平均功率、CWR"},
            {"parameter": "波浪频率 ω", "range": "±30% 设计频率", "metric": "功率频率响应曲线"},
            {"parameter": "波浪幅值 F0", "range": "0.5× 至 2×", "metric": "线性响应验证"},
        ]

    elif qid == "2017_B":
        base["problem_interpretation"] = "众包任务定价的多因素优化问题。需要回答：(1)影响任务完成率的关键因素；(2)定价与完成率的定量关系；(3)最优定价策略；(4)区域和时段差异。成功标准：定价模型能解释现有数据并给出可执行的优化策略。"
        base["assumptions"] = [
            {"id": "A1", "statement": "用户选择任务基于报酬-距离-难度的效用最大化", "justification": "离散选择理论"},
            {"id": "A2", "statement": "任务完成率服从 logistic 函数（S 形曲线）", "justification": "价格响应的饱和效应"},
            {"id": "A3", "statement": "区域固定效应可通过虚拟变量捕获", "justification": "区域异质性"},
            {"id": "A4", "statement": "时段效应（工作日/周末、白天/晚间）影响用户可用性", "justification": "时间经济学"},
            {"id": "A5", "statement": "任务难度与所需时间成正比", "justification": "题面隐含"},
        ]
        base["variables"] = [
            {"id": "price", "name": "任务价格", "description": "单任务报酬", "unit": "yuan", "role": "decision", "domain": "price > 0"},
            {"id": "completion_rate", "name": "任务完成率", "description": "完成比例", "unit": "1", "role": "derived", "domain": "[0,1]"},
            {"id": "distance", "name": "用户到任务距离", "description": "地理距离", "unit": "km", "role": "input", "domain": "distance ≥ 0"},
            {"id": "difficulty", "name": "任务难度", "description": "所需时间/技能", "unit": "1", "role": "input", "domain": "[0,1]"},
            {"id": "region", "name": "区域虚拟变量", "description": "区域固定效应", "unit": "1", "role": "input", "domain": "离散"},
            {"id": "time_slot", "name": "时段虚拟变量", "description": "时段效应", "unit": "1", "role": "input", "domain": "离散"},
        ]
        base["parameters"] = [
            {"id": "p1", "name": "价格敏感系数 β_price", "value_or_source": "回归估计", "unit": "1/yuan", "source": "calibrated"},
            {"id": "p2", "name": "距离衰减系数 β_dist", "value_or_source": "回归估计", "unit": "1/km", "source": "calibrated"},
            {"id": "p3", "name": "难度系数 β_diff", "value_or_source": "回归估计", "unit": "1", "source": "calibrated"},
            {"id": "p4", "name": "截距 b", "value_or_source": "回归估计", "unit": "1", "source": "calibrated"},
            {"id": "p5", "name": "区域效应 γ_r", "value_or_source": "回归估计", "unit": "1", "source": "calibrated"},
            {"id": "p6", "name": "时段效应 δ_t", "value_or_source": "回归估计", "unit": "1", "source": "calibrated"},
        ]
        base["constraints"] = [
            {"id": "C1", "expression": "0 ≤ completion_rate ≤ 1", "rationale": "概率有界"},
            {"id": "C2", "expression": "price ≥ 0", "rationale": "价格非负"},
            {"id": "C3", "expression": "总预算约束：Σ price_i ≤ B", "rationale": "平台预算"},
        ]
        base["objective"] = [
            {"id": "O1", "expression": "max E[收益] = Σ price_i · completion_rate_i", "kind": "maximize", "rationale": "总期望收益最大"},
            {"id": "O2", "expression": "max 任务完成数 = Σ completion_rate_i", "kind": "maximize", "rationale": "平台任务完成量"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "完成率模型（多因素 logistic）", "equation": "P(complete) = σ(β_p·price - β_d·distance - β_diff·difficulty + γ_r + δ_t + b)", "derivation_notes": "σ 为 logistic 函数"},
            {"id": "M2", "name": "收益函数", "equation": "Revenue = price · P(complete)", "derivation_notes": "期望收益"},
            {"id": "M3", "name": "价格-完成率弹性", "equation": "ε = β_p · price · (1 - P(complete))", "derivation_notes": "弹性分析"},
        ]
        base["sensitivity_plan"] = [
            {"parameter": "价格 price", "range": "5-50 yuan", "metric": "完成率曲线、收益曲线"},
            {"parameter": "距离 distance", "range": "0.5-10 km", "metric": "完成率衰减"},
            {"parameter": "区域效应 γ_r", "range": "±1", "metric": "区域差异"},
        ]

    elif qid == "2022_C":
        base["problem_interpretation"] = "古代玻璃制品成分数据的多方法统计分析与鉴别体系。需要回答：(1)成分数据的探索性分析与降维；(2)基于成分的聚类分类；(3)判别模型的建立与验证；(4)各成分指标的分类贡献。成功标准：聚类结果有物理意义，判别模型准确率>85%。"
        base["assumptions"] = [
            {"id": "A1", "statement": "成分数据经对数比变换后近似多元正态", "justification": "成分数据统计通例（clr 变换）"},
            {"id": "A2", "statement": "不同年代/产地的玻璃有可区分的成分指纹", "justification": "题面前提"},
            {"id": "A3", "statement": "样本量较小（n<100），适用小样本方法", "justification": "古代样品稀缺"},
            {"id": "A4", "statement": "成分含量总和 = 100%（闭合约束）", "justification": "化学分析约束"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "CLR 变换", "equation": "clr(x) = [ln(x_i/g(x))] 其中 g(x) 为几何均值", "derivation_notes": "消除闭合约束"},
            {"id": "M2", "name": "PCA", "equation": "Z = X·W, W = eigenvectors(Σ)", "derivation_notes": "主成分分析"},
            {"id": "M3", "name": "K-means", "equation": "迭代: 分配 x_i → nearest μ_k; 更新 μ_k = mean(cluster_k)", "derivation_notes": "无监督聚类"},
            {"id": "M4", "name": "LDA 判别", "equation": "w = S_w^{-1}(μ_1 - μ_2), score = w^T x", "derivation_notes": "Fisher 线性判别"},
        ]

    elif qid == "2020_B":
        base["problem_interpretation"] = "沙漠穿越的随机序贯决策优化问题。需要回答：(1)环境模型的建立（地形、天气、资源消耗）；(2)最优决策策略的求解（MDP/DP）；(3)不确定性下的鲁棒策略；(4)不同策略的风险-收益权衡。成功标准：策略在随机天气下显著优于贪心策略。"
        base["assumptions"] = [
            {"id": "A1", "statement": "天气状态服从马尔可夫链（晴/阴/雨），转移概率已知", "justification": "题面设定"},
            {"id": "A2", "statement": "资源消耗率与速度和天气相关", "justification": "物理合理性"},
            {"id": "A3", "statement": "绿洲位置和补给量已知", "justification": "题面给定"},
            {"id": "A4", "statement": "队伍速度可连续调节", "justification": "简化控制"},
            {"id": "A5", "statement": "目标为最小化期望到达时间或最大化安全概率", "justification": "两种目标可比较"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "位置动态", "equation": "s(t+1) = s(t) + v(t)·Δt", "derivation_notes": "确定性前进"},
            {"id": "M2", "name": "资源消耗", "equation": "r(t+1) = r(t) - c(v, weather)·Δt", "derivation_notes": "消耗率依赖速度和天气"},
            {"id": "M3", "name": "天气转移", "equation": "P(w'=j | w=i) = T_ij", "derivation_notes": "马尔可夫转移矩阵"},
            {"id": "M4", "name": "Bellman 方程", "equation": "V(s,w) = min_a [cost(s,w,a) + γ·Σ_w' T(w,w')·V(s',w')]", "derivation_notes": "MDP 值迭代"},
        ]

    elif qid == "2024_B":
        base["problem_interpretation"] = "生产质量检验的成本-风险权衡优化问题。需要回答：(1)质量检验的概率模型；(2)检验成本与不合格品损失的权衡；(3)最优检验频率和抽样方案；(4)不同质量水平下的最优策略。成功标准：最优策略显著降低总期望成本。"
        base["assumptions"] = [
            {"id": "A1", "statement": "产品不合格率 p 已知或可通过历史数据估计", "justification": "题面设定"},
            {"id": "A2", "statement": "检验为破坏性或非破坏性均可，但有单位成本", "justification": "题面设定"},
            {"id": "A3", "statement": "不合格品流出造成客户损失 c_def >> c_ins", "justification": "质量惩罚"},
            {"id": "A4", "statement": "批次内产品独立同分布", "justification": "随机抽样假设"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "漏检概率", "equation": "P(miss) = (1-p)^n ≈ e^{-np}（大批次）", "derivation_notes": "二项分布/泊松近似"},
            {"id": "M2", "name": "总期望成本", "equation": "E[C] = c_ins·n + c_def·P(miss)·(N-n)", "derivation_notes": "检验成本+期望损失"},
            {"id": "M3", "name": "最优检验量", "equation": "n* = argmin E[C]，一阶条件: c_ins = c_def·(N-n)·(-∂P(miss)/∂n)", "derivation_notes": "边际成本=边际收益"},
        ]

    elif qid == "2023_C":
        base["problem_interpretation"] = "蔬菜类商品的动态定价与补货联合优化问题。需要回答：(1)销售量预测模型；(2)损耗率、定价和需求的关系；(3)动态定价与补货的联合优化；(4)灵敏度分析。成功标准：优化策略相比固定定价显著降低损耗率并提高利润。"
        base["assumptions"] = [
            {"id": "A1", "statement": "蔬菜保鲜期为 T_max 天，超过则完全损耗", "justification": "生鲜特性"},
            {"id": "A2", "statement": "需求受价格影响，线性近似 D = a - b·p", "justification": "短期价格弹性稳定"},
            {"id": "A3", "statement": "每日补货一次，日末处理剩余库存", "justification": "实际操作"},
            {"id": "A4", "statement": "历史销售数据可用于需求分布估计", "justification": "数据驱动"},
            {"id": "A5", "statement": "缺货损失 = 毛利率 × 期望缺货量", "justification": "机会成本"},
        ]
        base["variables"] = [
            {"id": "p_t", "name": "第 t 日定价", "description": "销售价格", "unit": "yuan/kg", "role": "decision", "domain": "p_t > 0"},
            {"id": "q_t", "name": "第 t 日补货量", "description": "进货量", "unit": "kg", "role": "decision", "domain": "q_t ≥ 0"},
            {"id": "D_t", "name": "第 t 日需求", "description": "随机需求", "unit": "kg", "role": "state", "domain": "D_t ≥ 0"},
            {"id": "w_t", "name": "第 t 日末库存", "description": "剩余量", "unit": "kg", "role": "state", "domain": "w_t ≥ 0"},
            {"id": "L_t", "name": "第 t 日损耗", "description": "过期报废量", "unit": "kg", "role": "derived", "domain": "L_t ≥ 0"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "需求模型", "equation": "D_t = max(0, a - b·p_t + ε_t), ε_t ~ N(0, σ²)", "derivation_notes": "带噪声的线性需求"},
            {"id": "M2", "name": "库存动态", "equation": "w_t = max(w_{t-1} + q_t - D_t, 0)", "derivation_notes": "库存更新"},
            {"id": "M3", "name": "损耗", "equation": "L_t = max(w_{t-1} + q_t - D_t - W_max, 0)", "derivation_notes": "超过保鲜容量的部分"},
            {"id": "M4", "name": "利润函数", "equation": "π_t = p_t·min(q_t + w_{t-1}, D_t) - c·q_t - h·L_t", "derivation_notes": "销售收益-进货成本-损耗成本"},
        ]

    elif qid == "2024_C":
        base["problem_interpretation"] = "有限耕地资源下的多作物种植策略多目标优化问题。需要回答：(1)各作物收益-成本模型；(2)耕地面积约束下的种植优化；(3)轮作约束和多目标权衡（收益、风险、可持续性）；(4)不同市场情景下的策略。成功标准：帕累托前沿清晰，策略可执行。"
        base["assumptions"] = [
            {"id": "A1", "statement": "总耕地面积 A 固定，可分配给多种作物", "justification": "题面设定"},
            {"id": "A2", "statement": "各作物单位面积收益 r_i 已知或可估计", "justification": "题面给定数据"},
            {"id": "A3", "statement": "作物间存在轮作约束（同一种作物不能连续种植）", "justification": "农业常识"},
            {"id": "A4", "statement": "市场需求在计划期内稳定", "justification": "简化假设"},
            {"id": "A5", "statement": "考虑收益最大化和风险最小化两个目标", "justification": "多目标权衡"},
        ]
        base["variables"] = [
            {"id": "x_i", "name": "作物 i 种植面积", "description": "决策变量", "unit": "亩", "role": "decision", "domain": "x_i ≥ 0"},
            {"id": "R_total", "name": "总收益", "description": "销售收入减成本", "unit": "yuan", "role": "derived", "domain": "R_total ≥ 0"},
            {"id": "risk", "name": "收益风险", "description": "收益方差", "unit": "yuan²", "role": "derived", "domain": "risk ≥ 0"},
        ]
        base["mechanism"] = [
            {"id": "M1", "name": "收益模型", "equation": "R = Σ r_i · x_i", "derivation_notes": "线性收益"},
            {"id": "M2", "name": "面积约束", "equation": "Σ x_i ≤ A", "derivation_notes": "耕地约束"},
            {"id": "M3", "name": "轮作约束", "equation": "x_i(t) + x_i(t+1) ≤ A（简化）", "derivation_notes": "轮作约束"},
            {"id": "M4", "name": "风险模型", "equation": "Var(R) = Σ σ_i²·x_i² + 2·Σ_{i<j} ρ_ij·σ_i·σ_j·x_i·x_j", "derivation_notes": "方差-协方差"},
        ]

    return base


# ═══════════════════════════════════════════════════════════════
# Generate all 24 artifacts
# ═══════════════════════════════════════════════════════════════
generated = []
for qid, q in QUESTIONS.items():
    for arm, maker in [("B0", make_b0), ("MMA", make_mma), ("B1-F", make_b1f)]:
        artifact = maker(qid, q)
        fname = f"{qid}_{arm.replace('-', '_')}.json"
        fpath = OUTPUT / fname
        content = json.dumps(artifact, ensure_ascii=False, indent=2)
        fpath.write_text(content, encoding="utf-8")

        # SHA256 hash
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        generated.append({
            "problem_id": qid,
            "arm": arm,
            "file": fname,
            "sha256": sha,
            "element_count": (
                len(artifact.get("variables", []))
                + len(artifact.get("parameters", []))
                + len(artifact.get("constraints", []))
                + len(artifact.get("objective", []))
                + len(artifact.get("mechanism", []))
                + len(artifact.get("assumptions", []))
            )
        })
        print(f"✓ {qid}/{arm}: {fname} (sha256={sha[:12]}..., elements={generated[-1]['element_count']})")

# Save manifest
manifest = {
    "round": "P13-3D-R2",
    "phase": "Phase 2: Artifact Construction",
    "protocol": {
        "B0": "Original core (minimal, no P13-3C intervention)",
        "MMA": "MathModelAgent Modeler operationalization (frozen prompt)",
        "B1-F": "Full Construction checklist intervention (frozen, no new items)"
    },
    "artifacts": generated,
    "total": len(generated)
}
manifest_path = ROOT / "projects" / "P13-3D-R2" / "output" / "artifacts" / "manifest.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nManifest: {manifest_path}")
print(f"Total: {len(generated)} artifacts generated")
