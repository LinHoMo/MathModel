# -*- coding: utf-8 -*-
"""Evaluator C: write BUNDLE_023..033 score JSONs (batch 3)."""
import json, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))
KEY_DIMS = {
    "L1": ["L1.1", "L1.3", "L1.5"],
    "L2": ["L2.1", "L2.2", "L2.4", "L2.5", "L2.6"],
    "L3": ["L3.1", "L3.2", "L3.4"],
    "L4": ["L4.1", "L4.2", "L4.4", "L4.5"],
}
MAXES = {"L1": 9, "L2": 15, "L3": 9, "L4": 9}

# (score, max, evidence) per dimension; template ids reference by index
DIMS = ["L1.1", "L1.2", "L1.3", "L1.4", "L1.5",
        "L2.1", "L2.2", "L2.3", "L2.4", "L2.5", "L2.6", "L2.7",
        "L3.1", "L3.2", "L3.3", "L3.4", "L3.5",
        "L4.1", "L4.2", "L4.3", "L4.4", "L4.5"]
MAXS = [2, 2, 2, 1, 2,
        2, 2, 2, 2, 2, 3, 2,
        2, 2, 2, 2, 1,
        2, 2, 1, 2, 2]

def build(bundle, scores, notes):
    s = {}
    for d, mx in zip(DIMS, MAXS):
        s[d] = {"score": scores[d], "max": mx, "evidence": scores.get("_ev", {}).get(d, "")}
    totals = {}
    passes = {}
    for layer in ["L1", "L2", "L3", "L4"]:
        tot = sum(s[d]["score"] for d in s if d.startswith(layer + "."))
        totals[layer] = tot
        key_ok = any(s[d]["score"] > 0 for d in KEY_DIMS[layer])
        passes[layer] = (tot >= MAXES[layer] * 0.7) and key_ok
    # 统一口径：L4.1 对照基线为 L4 关键维度，缺失则 L4 层强制 FAIL
    if scores["L4.1"] == 0:
        passes["L4"] = False
    overall = all(passes.values())
    out = {
        "bundle_id": bundle,
        "evaluator_id": "C",
        "rubric_version": "v1.1",
        "scores": s,
        "layer_totals": totals,
        "layer_max": dict(MAXES),
        "layer_pass": passes,
        "overall_pass": overall,
        "notes": notes,
    }
    with open(os.path.join(OUT, bundle + ".json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(bundle, "L1:%d/%d %s L2:%d/%d %s L3:%d/%d %s L4:%d/%d %s OVERALL:%s" % (
        totals["L1"], 9, passes["L1"], totals["L2"], 15, passes["L2"],
        totals["L3"], 9, passes["L3"], totals["L4"], 9, passes["L4"], overall))

# ---------------- BUNDLE_023 : 2019C M/M/1 IR + validation_plan (=017) ----------------
b = "BUNDLE_023"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_ir.json problem_binding 覆盖 Q1-Q4，assumptions 捕获 Poisson/指数服务等显式参数；Q2 数据收集未落实"
ev["L1.2"] = "model_ir.json assumptions A1/A2/A3 明确 M/M/1 假设、放空确定性、先到先服务等机制/简化条件"
ev["L1.3"] = "problem_binding 列出 Q1-Q4 并 focus Q1；Q2-Q4 未交付方案"
ev["L1.4"] = "execution_result.json status=success, returncode=0，默认无异常路径分析"
ev["L1.5"] = "model_family primary=queuing_theory，M1 M/M/1 + 收益比较决策"
ev["L2.1"] = "model_ir.json variables 6 项含符号/单位/取值范围（lambda, mu, W_q, profit_q/c, decision）"
ev["L2.2"] = "model_ir.json parameters 声明 λ=30/μ=40/车费/成本等 6 参数；EQ2 的 c_f（fuel_idle=0.5）与 t_c（time_city=20）仅出现于代码未在 IR 参数声明 → 部分缺失"
ev["L2.3"] = "objectives OBJ1 max(profit_q,profit_c) 与 constraints C1(rho<1)/C2(W_q>=0) 齐备"
ev["L2.4"] = "focus 仅 Q1；Q2 依赖真实机场数据未建模，Q3/Q4 未覆盖"
ev["L2.5"] = "claims CL1 引 E1/E2/V1；experiments E1/E2 与 validations V1/V2 支撑"
ev["L2.6"] = "E1 机理正确（M/M/1 等待时间）+ E2 方程与机理一致 + OBJ/C 支撑决策；无候选模型对比节 → 基础 2 分"
ev["L2.7"] = "equations EQ1/EQ2 完整且 derivation_trace 给出推导来源，符号与 variables 基本对应"
ev["L3.1"] = "run_model.py 自包含可运行；execution_result.json status=success returncode=0"
ev["L3.2"] = "execution_result.json outputs 含 optimal_decision/profit/decision_scan 全字段，fidelity 14/14=1.0"
ev["L3.3"] = "outputs 收敛：expected_wait_min=0.1, rho=0.75, lambda_critical=39.98 均有限且单调；decision_scan 9 点完整"
ev["L3.4"] = "code_hash=0e57dd35... 存在；代码确定性（无随机），可复现"
ev["L3.5"] = "λ=30<μ=40 稳定，W_q=0.1min 合理，排队收益 79.8 vs 放空 -5.0 与决策 queue 自洽"
ev["L4.1"] = "execution_result.json/fidelity_report.json 无对照基线（无 baseline 模型或原方案对比）"
ev["L4.2"] = "execution_result.json outputs.decision_scan 已执行 λ=10..38 敏感性扫描，输出 9 点决策/等待时间/收益"
ev["L4.3"] = "validation_plan.json limit_tests 含零到达率与高到达率 2 类边界检验（未实际执行，按计划存在计 1）"
ev["L4.4"] = "claims CL1 evidence_refs E1/E2/V1 均可在 model_ir 与 execution outputs 中解析"
ev["L4.5"] = "CL1 声明可追溯至已执行 E1/E2 输出；code_hash 完整，复现路径明确"
s.update({d: v for d, v in zip(DIMS, [1,2,1,1,2, 2,1,2,1,2,2,1, 2,2,2,2,1, 0,2,1,2,2])})
s["_ev"] = ev
build(b, s, "2019C M/M/1 排队+收益比较，IR+validation_plan；执行成功且输出完整，L4.1 无基线致 L4 层失败")

# ---------------- BUNDLE_024 : 2020B 沙漠 DP IR + validation_plan (=004+plan) ----------------
b = "BUNDLE_024"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_ir.json problem_binding Q1-Q3，assumptions 提取六关/天气/负重/资金等题面参数"
ev["L1.2"] = "assumptions A1 地图简化为 5 节点线性图、A2 天气已知、A3 资源离散整数箱"
ev["L1.3"] = "problem_binding 覆盖 Q1-Q3，focus Q1；附件 Result.xlsx 未产出"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "model_family primary=dynamic_programming + MDP/优化"
ev["L2.1"] = "variables profit/water/food/day/path 含单位与取值范围"
ev["L2.2"] = "parameters 声明 cap=20/money=10000/days=10/mine=1000；题面基准价格/村庄倍率/退回半价未入 parameters → 缺失率>30%"
ev["L2.3"] = "objectives OBJ1 max 总资金 + constraints C1/C2/C3（负重/非耗尽/沙暴停留）"
ev["L2.4"] = "focus 仅 Q1，Q2/Q3 未建模"
ev["L2.5"] = "claims CL1 引 E1/V1；experiments E1 + validations V1/V2"
ev["L2.6"] = "E1 Bellman 机理正确 + EQ1 递推与机理一致 + OBJ/C 支撑；无候选对比 → 基础 2 分"
ev["L2.7"] = "EQ1 完整，符号与 variables 对应；消耗倍率 c_w/c_f 仅在 derivation_trace 描述 → 部分"
ev["L3.1"] = "run_model.py 可运行，execution_result.json status=success"
ev["L3.2"] = "success 但执行退化：optimal_profit=0/arrival_day=-1/n_states_explored=1，fidelity 13/14"
ev["L3.3"] = "无收敛数值：optimal_profit=0、path 为空，DP 未到达终点，fidelity arrival_day=-1 超范围 → 0"
ev["L3.4"] = "code_hash=a37f4bf4... 存在；random.seed(42) 固定 → 确定性"
ev["L3.5"] = "arrival_day=-1 与路径空说明求解失败，非物理合理结果 → 0"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "validation_plan.json sensitivity 声明初始资金/负重上限 2 类但未执行 → 1"
ev["L4.3"] = "validation_plan.json limit_tests 含零资源/全沙暴 2 类（计划存在，未执行）"
ev["L4.4"] = "validation_targets OBJ1 与 CL1 匹配，但执行退化使证据弱"
ev["L4.5"] = "CL1 可追溯至 E1 声明；执行退化，复现路径仅代码层面"
s.update({d: v for d, v in zip(DIMS, [1,2,1,1,2, 2,0,2,1,1,2,1, 2,1,0,2,0, 0,1,1,1,1])})
s["_ev"] = ev
build(b, s, "2020B 沙漠 DP，IR+validation_plan；DP 执行退化（n_states=1 未到达），L3.3/L3.5=0，L4 因 L4.1 失败")

# ---------------- BUNDLE_025 : 2020B 沙漠 DP model_doc (seed42) ----------------
b = "BUNDLE_025"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_doc.md 问题理解覆盖六关/天气/负重/资金等题面参数"
ev["L1.2"] = "model_doc.md 假设节含 5 节点线性图简化、天气已知、资源离散"
ev["L1.3"] = "model_doc.md 目标覆盖 Q1-Q3；Result.xlsx 附件未交付"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "model_doc.md 机理节 Bellman DP + 前向递推求解"
ev["L2.1"] = "model_doc.md 变量节 profit/water/food/day/path 含定义"
ev["L2.2"] = "model_doc.md 参数节完整：负重 20/资金 10000/天数 10/消耗倍率/水 5 食物 10/挖矿 1000/村庄 2 倍/退回半价"
ev["L2.3"] = "model_doc.md 目标节最大化总资金 + 约束节 3 条约束"
ev["L2.4"] = "focus Q1；Q2/Q3 未讨论"
ev["L2.5"] = "model_doc.md 验证节 3 项验证声明（可行性/约束/收敛）"
ev["L2.6"] = "E1 Bellman 机理+EQ1 递推+OBJ/C 支撑；无候选对比 → 基础 2 分"
ev["L2.7"] = "EQ1 完整，消耗倍率在参数节覆盖；符号基本对应"
ev["L3.1"] = "run_model.py 可运行，status=success"
ev["L3.2"] = "success 但执行退化（profit=0/arrival_day=-1/n_states=1），fidelity unverifiable"
ev["L3.3"] = "无收敛数值，DP 未到达终点 → 0"
ev["L3.4"] = "code_hash 存在；random.seed(42) → 确定性"
ev["L3.5"] = "arrival_day=-1 非合理结果 → 0"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "无敏感性分析证据"
ev["L4.3"] = "无极限检验执行证据"
ev["L4.4"] = "验证声明为叙述式，无结构化 claim 映射"
ev["L4.5"] = "model_doc 叙述式验证，无 claim_evidence_map → 1"
s.update({d: v for d, v in zip(DIMS, [1,2,1,1,2, 2,2,2,1,1,2,2, 2,1,0,2,0, 0,0,0,1,1])})
s["_ev"] = ev
build(b, s, "2020B 沙漠 DP 叙述式文档；执行退化，L3.3/L3.5=0；L4 证据缺位从严")

# ---------------- BUNDLE_026 : 2018A 热防护服 model_doc ----------------
b = "BUNDLE_026"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_doc.md 问题理解含 Q1 显式条件（75°C/II 6mm/IV 5mm/90min）；Q2/Q3 参数未纳入"
ev["L1.2"] = "model_doc.md 假设节 4 条：一维热传导/对流边界/物性恒定/左边界 Dirichlet"
ev["L1.3"] = "目标节计算温度场；problem1.xlsx 交付未提及"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "问题类型明确：一维瞬态热传导（Fourier+有限差分）"
ev["L2.1"] = "变量节 T(x,t)/T_skin/t/x 含定义"
ev["L2.2"] = "参数节四层 k/ρc/d 全声明 + 环境 75/对流 8/5400s + 体核 37°C → 符号全覆盖"
ev["L2.3"] = "目标节与约束节（47°C 上限/44°C 累计 5min）齐备"
ev["L2.4"] = "Q1 实现；Q2/Q3 最优厚度未求解"
ev["L2.5"] = "约束节 C1/C2 与问题对应"
ev["L2.6"] = "E1 热传导方程正确 + 边界条件完整 + 目标支撑；无候选对比 → 基础 2 分"
ev["L2.7"] = "方程节 PDE+双边界条件完整，符号与参数对应"
ev["L3.1"] = "run_model.py 可运行，status=success returncode=0"
ev["L3.2"] = "success 输出完整（skin_temp_final 42.525/温度曲线 21 点），但 problem1.xlsx 未产出 → 1"
ev["L3.3"] = "单次执行无网格收敛对比；CFL 声明未在输出验证 → 1"
ev["L3.4"] = "code_hash 存在；完全确定性（无随机）"
ev["L3.5"] = "42.5°C 处于 37-47 合理区间，曲线单调上升趋于稳态，物理合理"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "无敏感性分析"
ev["L4.3"] = "无极限检验执行"
ev["L4.4"] = "验证为叙述式（稳定性/边界/物理合理性），无结构化 claims"
ev["L4.5"] = "叙述式文档无 claim_evidence_map → 1"
s.update({d: v for d, v in zip(DIMS, [1,2,1,1,2, 2,2,2,1,2,2,2, 2,1,1,2,1, 0,0,0,1,1])})
s["_ev"] = ev
build(b, s, "2018A 热防护服叙述式文档；执行成功数值合理，L4 证据缺位从严")

# ---------------- BUNDLE_027 : 2018B RGV IR + validation_plan (=020) ----------------
b = "BUNDLE_027"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_ir.json problem_binding Q1-Q3；parameters 仅第 1 组参数"
ev["L1.2"] = "assumptions A1/A2/A3 明确一道工序/贪心策略/忽略故障"
ev["L1.3"] = "focus 任务1 一道工序；任务2 需 3 组数据+附件2 EXCEL 未完整交付"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "model_family primary=simulation 离散事件仿真"
ev["L2.1"] = "variables N/throughput/cycle/util/cnc_util 含单位与范围"
ev["L2.2"] = "parameters 声明第 1 组加工/移动/上下料/清洗/班次；EQ1 的 n_i 未单列 → 部分缺失"
ev["L2.3"] = "objectives OBJ1 max N + constraints C1/C2"
ev["L2.4"] = "focus Q1（一道工序第 1 组）；Q2 两道工序/Q3 故障未建模"
ev["L2.5"] = "claims CL1 引 E1/V1"
ev["L2.6"] = "E1 离散事件仿真正确 + EQ1 核算一致 + OBJ/C 支撑；无候选调度策略对比 → 基础 2 分"
ev["L2.7"] = "EQ1 完整，符号与 variables 对应"
ev["L3.1"] = "run_model.py 可运行，status=success returncode=0"
ev["L3.2"] = "success 输出完整（total_parts=248 等），但附件2 EXCEL 未产出、仅第 1 组 → 1"
ev["L3.3"] = "输出收敛：total_parts=248, 吞吐 31/h, CNC 利用率 0.6028 一致"
ev["L3.4"] = "code_hash 存在；完全确定性"
ev["L3.5"] = "248 件/8h、rgv 利用率 0.996、CNC 0.603 合理自洽"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "validation_plan.json sensitivity 声明加工时间/CNC 数量但未执行 → 1"
ev["L4.3"] = "validation_plan.json limit_tests 含单 CNC/零移动 2 类（计划存在）"
ev["L4.4"] = "validation_targets OBJ1 与 CL1 匹配，E1 已执行"
ev["L4.5"] = "CL1 evidence_refs E1/V1 可解析，code_hash 完整"
s.update({d: v for d, v in zip(DIMS, [1,2,1,1,2, 2,1,2,1,1,2,1, 2,1,2,2,1, 0,1,1,1,2])})
s["_ev"] = ev
build(b, s, "2018B RGV IR+validation_plan；执行成功输出合理，EXCEL 交付缺位，L4.1=0 致 L4 失败")

# ---------------- BUNDLE_028 : 2019C M/M/1 IR + validation_plan (=017/023) ----------------
b = "BUNDLE_028"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_ir.json problem_binding Q1-Q4，assumptions 捕获 Poisson/指数服务等显式参数"
ev["L1.2"] = "assumptions A1/A2/A3 明确 M/M/1 假设与放空确定性"
ev["L1.3"] = "problem_binding 列出 Q1-Q4 并 focus Q1；Q2-Q4 未交付方案"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "model_family primary=queuing_theory"
ev["L2.1"] = "variables 6 项含符号/单位/取值范围"
ev["L2.2"] = "parameters 6 参数声明；EQ2 的 c_f/t_c 仅代码级 → 部分缺失"
ev["L2.3"] = "OBJ1 + C1/C2 齐备"
ev["L2.4"] = "focus 仅 Q1"
ev["L2.5"] = "claims CL1 引 E1/E2/V1"
ev["L2.6"] = "E1 机理正确+E2 一致+OBJ/C 支撑 → 基础 2 分"
ev["L2.7"] = "EQ1/EQ2 完整且有 derivation_trace"
ev["L3.1"] = "run_model.py 可运行，status=success"
ev["L3.2"] = "outputs 全字段，fidelity 14/14=1.0"
ev["L3.3"] = "输出收敛：rho=0.75/W_q=0.1/lambda_critical=39.98，decision_scan 9 点"
ev["L3.4"] = "code_hash=0e57dd35... 存在；确定性"
ev["L3.5"] = "结果物理合理且与决策自洽"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "outputs.decision_scan 已执行 λ 敏感性扫描"
ev["L4.3"] = "validation_plan.json limit_tests 2 类"
ev["L4.4"] = "CL1 证据可解析"
ev["L4.5"] = "CL1 可追溯 + code_hash 完整"
s.update({d: v for d, v in zip(DIMS, [1,2,1,1,2, 2,1,2,1,2,2,1, 2,2,2,2,1, 0,2,1,2,2])})
s["_ev"] = ev
build(b, s, "2019C M/M/1 IR+validation_plan；执行成功输出完整，仅 L4.1=0 致 L4 失败")

# ---------------- BUNDLE_029 : 2024A 板凳龙 model_doc (=021 变体, seed42) ----------------
b = "BUNDLE_029"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_doc.md 显式条件齐全（223 节/板长/板宽/螺距 55cm/1m/s/第16圈/Q3-Q5 参数）"
ev["L1.2"] = "model_doc.md 隐式条件与歧义点节：刚体链/碰撞判定/后节速度递推"
ev["L1.3"] = "问题理解覆盖 Q1-Q5；result1/2/4.xlsx 附件未交付"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "问题类型：运动学仿真（阿基米德螺线+刚体链）"
ev["L2.1"] = "变量节 theta/r/(x_i,y_i)/v_i/d_min 含定义"
ev["L2.2"] = "参数节 N/L_head/L_body/W/pitch/v0/R_turn；r0=0.5 与 0.85 节长系数未声明 → 部分"
ev["L2.3"] = "目标节 Q1/Q2/Q3/Q5 目标齐备"
ev["L2.4"] = "Q1 实现；Q2 碰撞/Q3/Q4/Q5 仅估算未完整求解"
ev["L2.5"] = "约束节 刚体/无碰撞/速度 3 条"
ev["L2.6"] = "E1-E3 机理正确 + 候选对比节明确排除 PDE 与纯优化 → 3 分"
ev["L2.7"] = "E1-E4 方程完整，符号与变量对应；0.85 系数未声明 → 部分"
ev["L3.1"] = "run_model.py 可运行，status=success"
ev["L3.2"] = "success 输出关键帧，但 result1.xlsx 未产出、Q2 碰撞检测仅粗判定 → 1"
ev["L3.3"] = "单次执行无收敛对比；min_segment_gap 恒 3.74（抽样步长 10 粗） → 1"
ev["L3.4"] = "random.seed(42) 固定；几何确定性 → 2"
ev["L3.5"] = "tail_final_position x=276.5/y=-313.3 与螺线半径~56m 严重不符，collision=false 亦不合理 → 0"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "model_doc 验证节声明螺距 ±10% 灵敏度但未执行 → 1"
ev["L4.3"] = "model_doc 验证节声明 pitch→0 极限检验但未执行 → 1"
ev["L4.4"] = "验证方案叙述式，无结构化 claim 映射"
ev["L4.5"] = "叙述式文档无 claim_evidence_map → 1"
s.update({d: v for d, v in zip(DIMS, [2,2,1,1,2, 2,1,2,1,1,3,1, 2,1,1,2,0, 0,1,1,1,1])})
s["_ev"] = ev
build(b, s, "2024A 板凳龙叙述式文档；机理与候选对比完整，但尾坐标物理错误致 L3.5=0、L3 层 6/9 失败")

# ---------------- BUNDLE_030 : 2011B 交巡警 IR (无 plan, =003) ----------------
b = "BUNDLE_030"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_ir.json problem_binding Q1/Q2；附件2 真实路网数据未使用"
ev["L1.2"] = "assumptions A1 简化 20 节点网络替代附件路网 → 隐式条件未充分挖掘"
ev["L1.3"] = "focus Q1 管辖+封锁；Q1 第三问（增平台）与 Q2 未交付"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "model_family primary=graph_algorithm"
ev["L2.1"] = "variables coverage/t_max/CV/allocation/blockade 含定义与范围"
ev["L2.2"] = "parameters 仅 speed/resp/nplat/nexit 4 项；附件2 边权数据未入参 → 部分"
ev["L2.3"] = "objectives OBJ1/OBJ2 双目标 + constraints C1/C2"
ev["L2.4"] = "focus Q1；Q2 全市六区未建模"
ev["L2.5"] = "claims CL1/CL2 引 E1/V1 与 E2/V2"
ev["L2.6"] = "E1/E2 机理正确（Dijkstra+最近邻）+ OBJ/C 支撑；无候选对比 → 基础 2 分"
ev["L2.7"] = "EQ1/EQ2 完整，但边权 w(e) 未在参数声明 → 符号部分缺失"
ev["L3.1"] = "run_model.py 可运行，status=success"
ev["L3.2"] = "success 且 outputs 覆盖管辖与封锁全部字段，fidelity 12/12=1.0"
ev["L3.3"] = "输出收敛但退化：coverage=1.0 且 max_response=0.0（每节点自分配）→ 上限 1"
ev["L3.4"] = "code_hash 存在；确定性（random_seed 变量未用随机）"
ev["L3.5"] = "max_response_time_min=0.0 因 20 平台=20 节点自分配所致，非真实解 → 0"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "E2 封锁实验已执行（贪心调度 13 路口）→ 1"
ev["L4.3"] = "V1/V2 为范围与可行性校验，非极限检验 → 1"
ev["L4.4"] = "CL1/CL2 证据可解析至 E1/E2 输出"
ev["L4.5"] = "claims 结构化可追溯 + code_hash 完整"
s.update({d: v for d, v in zip(DIMS, [1,1,1,1,2, 2,1,1,1,1,2,1, 2,2,1,2,0, 0,1,1,1,2])})
s["_ev"] = ev
build(b, s, "2011B 交巡警 IR；Dijkstra+最近邻可运行但输出退化（响应全 0），L1.1/L2.2 扣分，L4.1=0")

# ---------------- BUNDLE_031 : 2017B 定价 IR seed44 + validation_plan (=022+plan) ----------------
b = "BUNDLE_031"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_ir.json problem_binding Q1-Q4；附件一/二/三真实数据未使用"
ev["L1.2"] = "assumptions A2 明确合成数据替代附件一 → 隐式条件（会员信誉/预订限额）归入密度"
ev["L1.3"] = "focus Q1/Q2；Q3 打包/Q4 新项目未交付"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "model_family primary=statistical_modeling（Logistic）"
ev["L2.1"] = "variables price/distance/density/P_complete/price_opt/profit 含范围"
ev["L2.2"] = "parameters 仅样本量/学习率/轮数；EQ1 的 β0-β3 未入参数声明 → 缺失率>30%"
ev["L2.3"] = "objectives OBJ1 估计+OBJ2 最大化期望利润 + constraints C1/C2"
ev["L2.4"] = "focus Q1/Q2；Q3/Q4 未覆盖"
ev["L2.5"] = "claims CL1/CL2 引 E1/V1/V2 与 E2"
ev["L2.6"] = "E1/E2 机理正确（Logistic+网格搜索）+ OBJ/C 支撑；无候选对比 → 基础 2 分"
ev["L2.7"] = "EQ1/EQ2 完整，符号部分未入参数 → 部分缺失"
ev["L3.1"] = "run_model.py 可运行，status=success returncode=0"
ev["L3.2"] = "success 输出完整（系数/利润曲线/最优价），fidelity 14/17=0.82（会员密度缺输出键）→ 1"
ev["L3.3"] = "单次执行无收敛对比；loss_final=0.681 有限 → 1"
ev["L3.4"] = "code_hash 存在；random.seed(44)≠42 → 1"
ev["L3.5"] = "系数符号与解释一致（price +0.1192/distance -0.2269/density +0.1647），最优价 40 为网格端点 → 1"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "validation_plan.json sensitivity 声明定价/距离 2 类但未执行 → 1"
ev["L4.3"] = "validation_plan.json limit_tests 零价格/极远任务 2 类（计划存在）"
ev["L4.4"] = "validation_targets OBJ1/OBJ2 与 CL1/CL2 匹配，E1/E2 已执行"
ev["L4.5"] = "CL1/CL2 结构化可追溯 + code_hash 完整"
s.update({d: v for d, v in zip(DIMS, [1,1,1,1,2, 2,0,1,1,1,2,1, 2,1,1,1,1, 0,1,1,1,2])})
s["_ev"] = ev
build(b, s, "2017B 定价 IR seed44+validation_plan；合成数据替代附件致 L1/L2 扣分，L3.4=1（seed≠42），L4.1=0")

# ---------------- BUNDLE_032 : 2018A 热防护服 model_doc (=026) ----------------
b = "BUNDLE_032"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_doc.md 问题理解含 Q1 显式条件；Q2/Q3 参数未纳入"
ev["L1.2"] = "假设节 4 条完整（一维/对流/物性恒定/Dirichlet）"
ev["L1.3"] = "目标节计算温度场；problem1.xlsx 未提及"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "一维瞬态热传导（Fourier+有限差分）"
ev["L2.1"] = "变量节 T/T_skin/t/x 含定义"
ev["L2.2"] = "参数节四层 k/ρc/d + 环境/对流/时长全覆盖"
ev["L2.3"] = "目标节+约束节（47°C/44°C-5min）齐备"
ev["L2.4"] = "Q1 实现；Q2/Q3 最优厚度未求解"
ev["L2.5"] = "约束节与问题对应"
ev["L2.6"] = "E1 正确+边界完整+目标支撑；无候选对比 → 基础 2 分"
ev["L2.7"] = "PDE+双边界完整，符号对应"
ev["L3.1"] = "run_model.py 可运行，status=success"
ev["L3.2"] = "success 输出完整，但 problem1.xlsx 未产出 → 1"
ev["L3.3"] = "单次执行无网格收敛对比 → 1"
ev["L3.4"] = "code_hash 存在；确定性"
ev["L3.5"] = "42.5°C 合理，曲线单调上升趋于稳态"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "无敏感性分析"
ev["L4.3"] = "无极限检验执行"
ev["L4.4"] = "验证叙述式，无结构化 claims"
ev["L4.5"] = "叙述式文档无 claim_evidence_map → 1"
s.update({d: v for d, v in zip(DIMS, [1,2,1,1,2, 2,2,2,1,2,2,2, 2,1,1,2,1, 0,0,0,1,1])})
s["_ev"] = ev
build(b, s, "2018A 热防护服叙述式文档；执行成功数值合理，L4 证据缺位从严")

# ---------------- BUNDLE_033 : 2011B 交巡警 IR + validation_plan (=003) ----------------
b = "BUNDLE_033"
s = {d: 0 for d in DIMS}
ev = {}
ev["L1.1"] = "model_ir.json problem_binding Q1/Q2；附件2 真实路网未使用"
ev["L1.2"] = "A1 简化 20 节点网络替代附件路网"
ev["L1.3"] = "focus Q1；Q1 增平台/Q2 未交付"
ev["L1.4"] = "execution_result.json status=success returncode=0"
ev["L1.5"] = "graph_algorithm（Dijkstra+贪心）"
ev["L2.1"] = "variables 5 项含定义与范围"
ev["L2.2"] = "parameters 4 项，附件边权未入参 → 部分"
ev["L2.3"] = "OBJ1/OBJ2 + C1/C2"
ev["L2.4"] = "focus Q1"
ev["L2.5"] = "CL1/CL2 引 E1/V1 与 E2/V2"
ev["L2.6"] = "E1/E2 机理正确+OBJ/C 支撑；无候选对比 → 基础 2 分"
ev["L2.7"] = "EQ1/EQ2 完整，w(e) 未声明 → 部分缺失"
ev["L3.1"] = "run_model.py 可运行，status=success"
ev["L3.2"] = "success 输出覆盖管辖/封锁全字段，fidelity 12/12=1.0"
ev["L3.3"] = "输出退化（coverage=1.0 且响应=0.0）→ 上限 1"
ev["L3.4"] = "code_hash 存在；确定性"
ev["L3.5"] = "max_response=0.0 为自分配退化，非真实解 → 0"
ev["L4.1"] = "无对照基线"
ev["L4.2"] = "validation_plan.json sensitivity 声明响应要求/平台数量但未执行 → 1"
ev["L4.3"] = "validation_plan.json limit_tests 单平台/全连接 2 类"
ev["L4.4"] = "CL1/CL2 证据可解析至 E1/E2"
ev["L4.5"] = "claims 结构化可追溯 + code_hash 完整"
s.update({d: v for d, v in zip(DIMS, [1,1,1,1,2, 2,1,1,1,1,2,1, 2,2,1,2,0, 0,1,1,1,2])})
s["_ev"] = ev
build(b, s, "2011B 交巡警 IR+validation_plan；输出退化（响应全 0），L4.1=0 致 L4 失败")
