"""
P15-K003 预检 — 6题主检验题目的模型定义与自包含求解代码。

每个题目返回 dict:
  code           : str, run_model.py 源码（纯标准库，def solve(inputs)->dict，stdout末行JSON）
  model_ir       : dict, MODEL_IR 18字段契约（S/SV臂用）
  model_doc      : str, 自由文本九部分（F臂用）
  validation_plan: dict, SV臂强制验证计划
  output_mapping : dict, {声明名/符号 -> 输出key}
  family_primary : str, canonical model_family id

铁律：代码 self-contained，禁 scipy/numpy/网络，固定 ABI def solve(inputs: dict) -> dict。
"""
from __future__ import annotations

import json
import textwrap


# ============================================================
# 2020_B — 穿越沙漠（动态规划，确定性天气已知）
# ============================================================
def problem_2020_B() -> dict:
    code = textwrap.dedent('''\
        """2020_B 穿越沙漠 — 确定性天气下的资源约束动态规划（自包含，纯标准库）。"""
        import json
        import random

        def solve(inputs: dict) -> dict:
            random.seed(42)
            # ---- 简化地图：5节点线性图 Start-Village-Mine-Waypoint-End ----
            nodes = ["Start", "Village", "Mine", "Waypoint", "End"]
            adj = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2, 4], 4: [3]}
            n_days = 10
            # 天气：0=晴朗, 1=高温, 2=沙暴（沙暴日必须停留）
            weather = [0, 0, 1, 0, 2, 0, 1, 0, 0, 0]
            # 资源参数
            base_water, base_food = 1, 1
            price_water, price_food = 5, 10
            capacity = 20
            start_money = 10000
            mine_income = 1000
            village_mult = 2
            refund_mult = 0.5

            # DP: state=(day, pos, water, food) -> max money; -inf = unreachable
            NEG = float("-inf")
            # water, food discretized 0..capacity
            dp = {}
            parent = {}
            # day 0: at Start, buy initial resources
            for w in range(capacity + 1):
                for f in range(capacity + 1 - w):
                    cost = w * price_water + f * price_food
                    if cost <= start_money:
                        dp[(0, 0, w, f)] = start_money - cost

            def consume(day, action, w, f):
                """返回 (water_after, food_after) 或 None if 耗尽."""
                mult = {"stay": 1, "move": 2, "mine": 3}[action]
                w2 = w - base_water * mult
                f2 = f - base_food * mult
                if w2 < 0 or f2 < 0:
                    return None
                return w2, f2

            for day in range(n_days):
                next_dp = {}
                for (d, pos, w, f), money in dp.items():
                    if d != day:
                        continue
                    wstate = weather[day]
                    # 沙暴日只能停留
                    if wstate == 2:
                        actions = [("stay", pos)]
                    else:
                        actions = [("stay", pos)]
                        for nb in adj[pos]:
                            actions.append(("move", nb))
                        if pos == 2:  # Mine
                            actions.append(("mine", pos))
                    for act, new_pos in actions:
                        c = consume(day, act, w, f)
                        if c is None:
                            continue
                        nw, nf = c
                        nmoney = money
                        if act == "mine":
                            nmoney += mine_income
                        # 村庄购买（随时可买，价格2倍）
                        if new_pos == 1:
                            # 简化：不主动购买（初始购买已够）
                            pass
                        key = (day + 1, new_pos, nw, nf)
                        if nmoney > next_dp.get(key, NEG):
                            next_dp[key] = nmoney
                            parent[key] = (day, pos, w, f, act)
                dp = next_dp

            # 终点：到达 End(pos=4) 的最优
            best = None
            best_key = None
            for (d, pos, w, f), money in dp.items():
                if pos == 4:
                    # 退回剩余资源
                    refund = (w * price_water + f * price_food) * refund_mult
                    total = money + refund
                    if best is None or total > best:
                        best = total
                        best_key = (d, pos, w, f)

            # 回溯路径
            path = []
            if best_key:
                cur = best_key
                while cur in parent:
                    p = parent[cur]
                    path.append({"day": p[0], "from": nodes[p[1]], "action": p[4], "to": nodes[cur[1]]})
                    cur = (p[0], p[1], p[2], p[3])
                path.reverse()

            return {
                "optimal_profit": round(best, 2) if best is not None else 0.0,
                "remaining_water": best_key[2] if best_key else 0,
                "remaining_food": best_key[3] if best_key else 0,
                "arrival_day": best_key[0] if best_key else -1,
                "path_length": len(path),
                "optimal_path": path[:5],
                "n_states_explored": len(dp),
                "weather_known": True,
            }

        if __name__ == "__main__":
            print(json.dumps(solve({}), ensure_ascii=False))
    ''')

    model_ir = {
        "ir_version": "1.0",
        "model_id": "M-2020B-DP",
        "model_family": {
            "primary": "dynamic_programming",
            "secondary": ["markov_decision_process", "optimization", "graph_algorithm"]
        },
        "problem_binding": {
            "problem_id": "2020_B",
            "sub_questions": ["Q1", "Q2", "Q3"],
            "focus": "Q1 确定性天气最优策略"
        },
        "assumptions": [
            {"assumption_id": "A1", "type": "projection",
             "statement": "地图简化为5节点线性图（Start-Village-Mine-Waypoint-End），保留核心资源约束机制",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A2", "type": "mechanism_assumption",
             "statement": "天气全部已知（Q1设定），沙暴日必须停留，消耗倍率按题目规则",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A3", "type": "simplification",
             "statement": "水/食物离散为整数箱，负重上限20箱，初始资金10000",
             "sub_question_binding": ["Q1"]}
        ],
        "variables": [
            {"variable_id": "v_profit", "name": "最优收益", "symbol": "profit",
             "definition": "到达终点后剩余资金+退回资源的总金额", "unit": "元",
             "type": "output", "value_range": {"min": 0, "max": 50000},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_water", "name": "剩余水量", "symbol": "water",
             "definition": "到达终点时剩余水量（箱）", "unit": "箱",
             "type": "output", "value_range": {"min": 0, "max": 20},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_food", "name": "剩余食物", "symbol": "food",
             "definition": "到达终点时剩余食物量（箱）", "unit": "箱",
             "type": "output", "value_range": {"min": 0, "max": 20},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_day", "name": "到达天数", "symbol": "day",
             "definition": "到达终点的天数", "unit": "天",
             "type": "output", "value_range": {"min": 0, "max": 10},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_path", "name": "最优路径", "symbol": "path",
             "definition": "从起点到终点的最优行动序列", "unit": "无",
             "type": "output", "sub_question_binding": ["Q1"]}
        ],
        "parameters": [
            {"parameter_id": "p_cap", "name": "负重上限", "value": 20, "unit": "箱", "source": "题目"},
            {"parameter_id": "p_money", "name": "初始资金", "value": 10000, "unit": "元", "source": "假设"},
            {"parameter_id": "p_days", "name": "游戏天数", "value": 10, "unit": "天", "source": "简化"},
            {"parameter_id": "p_mine", "name": "挖矿基础收益", "value": 1000, "unit": "元/天", "source": "假设"}
        ],
        "objectives": [
            {"objective_id": "OBJ1", "type": "max",
             "expression": "maximize 到达终点时的总资金（含剩余资源退回）",
             "variables_refs": ["v_profit", "v_water", "v_food"],
             "sub_question_binding": ["Q1"]}
        ],
        "constraints": [
            {"constraint_id": "C1", "type": "resource_capacity",
             "expression": "water + food <= 20（负重上限）",
             "variables_refs": ["v_water", "v_food"], "source": "题目",
             "sub_question_binding": ["Q1"]},
            {"constraint_id": "C2", "type": "non_depletion",
             "expression": "每日消耗后 water>=0 且 food>=0，否则游戏失败",
             "variables_refs": ["v_water", "v_food"], "source": "题目",
             "sub_question_binding": ["Q1"]},
            {"constraint_id": "C3", "type": "weather_constraint",
             "expression": "沙暴日必须在原地停留",
             "variables_refs": ["v_day"], "source": "题目",
             "sub_question_binding": ["Q1"]}
        ],
        "mechanisms": [
            {"mechanism_id": "M1", "name": "Bellman最优性原理",
             "description": "状态=(day,position,water,food)，值函数V(s)=max_a [reward(a)+V(s')]，无后效性满足",
             "equations_refs": ["EQ1"], "sub_question_binding": ["Q1"]}
        ],
        "equations": [
            {"equation_id": "EQ1", "latex": "V(d,p,w,f)=\\max_{a\\in A(d,p)}[r(a)+V(d+1,p',w-c_w(a),f-c_f(a))]",
             "type": "dp_recurrence", "variables_refs": ["v_profit", "v_water", "v_food", "v_day"],
             "derivation_trace": "由Bellman最优性原理，消耗c_w/c_f依行动类型(stay/move/mine)取1/2/3倍基础消耗",
             "sub_question_binding": ["Q1"]}
        ],
        "dependencies": [],
        "solvers": [
            {"solver_id": "S1", "name": "后向动态规划",
             "description": "从day=0前向推进DP表，状态空间=days×positions×water×food，回溯最优路径",
             "sub_question_binding": ["Q1"]}
        ],
        "experiments": [
            {"experiment_id": "E1", "name": "10天5节点确定性天气",
             "description": "固定天气序列，初始资金10000，负重20，验证DP收敛与路径可行性",
             "sub_question_binding": ["Q1"]}
        ],
        "validations": [
            {"validation_id": "V1", "type": "feasibility",
             "description": "最优路径中每日资源消耗后water>=0且food>=0",
             "sub_question_binding": ["Q1"]},
            {"validation_id": "V2", "type": "constraint_check",
             "description": "负重约束water+food<=20在所有状态满足",
             "sub_question_binding": ["Q1"]}
        ],
        "claims": [
            {"claim_id": "CL1", "statement": "确定性天气下存在资源约束最优策略，DP可在多项式状态空间内求解",
             "evidence_refs": ["E1", "V1"], "sub_question_binding": ["Q1"]}
        ],
        "model_graph": {"nodes": 5, "edges": 4, "type": "linear_chain"},
        "modeling_trace": [
            {"step": 1, "action": "problem_decomposition", "detail": "Q1确定性天气→确定性DP"},
            {"step": 2, "action": "state_design", "detail": "(day,pos,water,food)四元组"},
            {"step": 3, "action": "solver_selection", "detail": "前向DP表+回溯"}
        ]
    }

    model_doc = textwrap.dedent('''\
        # 2020_B 穿越沙漠 — 模型文档（自由文本）

        ## 1. 问题理解
        玩家在沙漠中从起点出发，携带水和食物，经历不同天气，可在矿山挖矿、村庄购买，目标是在规定时间内到达终点并保留尽可能多的资金。Q1假设天气全部已知，求最优策略。

        ## 2. 假设
        - 地图简化为5节点线性图（起点-村庄-矿山-路点-终点），保留资源约束核心机制
        - 天气全部已知，沙暴日必须停留
        - 水/食物离散为整数箱，负重上限20箱，初始资金10000元
        - 挖矿收益1000元/天，村庄价格为基准2倍，终点退回价格为基准一半

        ## 3. 变量
        - profit：到达终点后的最优总收益（元）
        - water：剩余水量（箱）
        - food：剩余食物量（箱）
        - day：到达终点的天数
        - path：最优行动序列

        ## 4. 参数
        - 负重上限20箱，初始资金10000元，游戏天数10天
        - 基础消耗：停留1倍、行走2倍、挖矿3倍
        - 基准价格：水5元/箱，食物10元/箱

        ## 5. 目标
        最大化到达终点时的总资金（含剩余资源按半价退回）。

        ## 6. 约束
        - 负重约束：water + food <= 20
        - 资源非耗尽：每日消耗后 water>=0 且 food>=0
        - 天气约束：沙暴日必须原地停留

        ## 7. 机理与方程
        采用Bellman最优性原理的动态规划。状态为(day, position, water, food)，值函数递推：
        V(d,p,w,f) = max_{a∈A(d,p)} [r(a) + V(d+1,p',w-c_w(a),f-c_f(a))]
        其中消耗倍率依行动类型取1/2/3倍基础消耗。

        ## 8. 求解方法与实验
        前向动态规划：从day=0逐步推进DP表，记录父指针用于回溯。状态空间约为10×5×21×21。实验设定为10天5节点确定性天气序列。

        ## 9. 验证
        - 可行性检验：最优路径中每日资源消耗后均非负
        - 约束检验：所有状态满足负重约束water+food<=20
        - 收敛性：DP表在有限步内收敛，最优路径可回溯
    ''')

    validation_plan = {
        "plan_id": "VP-2020B",
        "limit_tests": [
            {"name": "零资源边界", "description": "初始water=0,food=0时应无法出发",
             "expected": "游戏失败或profit=0"},
            {"name": "全沙暴天气", "description": "10天全沙暴时只能停留，应无法到达终点",
             "expected": "arrival_day=-1"}
        ],
        "sensitivity": [
            {"parameter": "初始资金", "range": [5000, 10000, 20000],
             "expected_effect": "资金增加→可购买更多资源→profit单调不减"},
            {"parameter": "负重上限", "range": [10, 20, 30],
             "expected_effect": "负重增加→策略空间扩大→profit不减"}
        ],
        "validation_targets": ["OBJ1"],
        "constraint_violation_check": True,
        "residual_check": False
    }

    output_mapping = {
        "最优收益": "optimal_profit", "profit": "optimal_profit",
        "剩余水量": "remaining_water", "water": "remaining_water",
        "剩余食物": "remaining_food", "food": "remaining_food",
        "到达天数": "arrival_day", "day": "arrival_day",
        "最优路径": "optimal_path", "path": "optimal_path",
    }

    return {
        "problem_id": "2020_B", "title": "穿越沙漠",
        "code": code, "model_ir": model_ir, "model_doc": model_doc,
        "validation_plan": validation_plan, "output_mapping": output_mapping,
        "family_primary": "dynamic_programming",
        "sub_questions": ["Q1", "Q2", "Q3"],
    }


# ============================================================
# 2018_A — 高温作业专用服装设计（一维瞬态热传导PDE，显式FDM）
# ============================================================
def problem_2018_A() -> dict:
    code = textwrap.dedent('''\
        """2018_A 高温作业专用服装 — 一维四层瞬态热传导显式有限差分（自包含，纯标准库）。"""
        import json
        import math

        def solve(inputs: dict) -> dict:
            # 四层材料参数 (k W/mK, rho*c J/m3K, thickness m)
            layers = [
                {"name": "I",   "k": 0.045, "rhoc": 1.2e6, "d": 0.006},
                {"name": "II",  "k": 0.055, "rhoc": 1.0e6, "d": 0.006},
                {"name": "III", "k": 0.065, "rhoc": 0.8e6, "d": 0.004},
                {"name": "IV",  "k": 0.028, "rhoc": 1.2e3, "d": 0.005},
            ]
            T_ambient = 75.0   # 环境温度 °C
            T_skin_init = 37.0  # 初始皮肤侧温度
            T_body = 37.0       # 体核温度
            h_conv = 8.0        # 皮肤侧对流系数 W/m2K
            total_time = 5400.0  # 90分钟 = 5400秒
            dx = 0.0005          # 空间步长 0.5mm

            # 构建网格
            xs = []
            layer_idx = []
            x = 0.0
            for li, layer in enumerate(layers):
                n_pts = int(round(layer["d"] / dx))
                for i in range(n_pts):
                    xs.append(x)
                    layer_idx.append(li)
                    x += dx
            N = len(xs)
            L = x

            # 时间步长（稳定性：dt <= dx^2 / (2*alpha_max)）
            alpha_max = max(l["k"] / l["rhoc"] for l in layers)
            dt = 0.25 * dx * dx / alpha_max
            n_steps = int(math.ceil(total_time / dt))

            # 初始化温度场
            T = [T_skin_init] * N
            T[0] = T_ambient  # 左边界Dirichlet

            skin_temps = []  # 记录皮肤侧温度随时间
            sample_interval = max(1, n_steps // 100)

            for step in range(n_steps):
                T_new = T[:]
                T_new[0] = T_ambient  # 左边界固定环境温度
                # 内部节点显式更新（层间界面用调和平均热扩散率）
                for i in range(1, N - 1):
                    li = layer_idx[i]
                    k = layers[li]["k"]
                    rhoc = layers[li]["rhoc"]
                    alpha = k / rhoc
                    # 层间界面处理：用相邻层k的调和平均
                    if layer_idx[i - 1] != li:
                        k_left = layers[layer_idx[i - 1]]["k"]
                        k_eff = 2 * k * k_left / (k + k_left)
                        alpha = k_eff / rhoc
                    elif layer_idx[i + 1] != li:
                        k_right = layers[layer_idx[i + 1]]["k"]
                        k_eff = 2 * k * k_right / (k + k_right)
                        alpha = k_eff / rhoc
                    T_new[i] = T[i] + alpha * dt / (dx * dx) * (T[i + 1] - 2 * T[i] + T[i - 1])
                # 右边界：对流边界（皮肤侧与体核换热）
                i = N - 1
                li = layer_idx[i]
                k = layers[li]["k"]
                rhoc = layers[li]["rhoc"]
                # Neumann型对流：-k dT/dx = h(T - T_body)
                # 用ghost node方法
                T_ghost = T[i - 1] + 2 * dx * h_conv / k * (T_body - T[i])
                alpha = k / rhoc
                T_new[i] = T[i] + alpha * dt / (dx * dx) * (T_ghost - 2 * T[i] + T[i - 1])
                T = T_new
                if step % sample_interval == 0 or step == n_steps - 1:
                    t = (step + 1) * dt
                    skin_temps.append({"time_s": round(t, 1), "temp_C": round(T[N - 1], 3)})

            T_skin_final = T[N - 1]
            T_skin_max = max(s["temp_C"] for s in skin_temps)
            # 超过44°C的时间
            time_above_44 = 0.0
            for j in range(1, len(skin_temps)):
                if skin_temps[j]["temp_C"] > 44.0:
                    dt_sample = skin_temps[j]["time_s"] - skin_temps[j - 1]["time_s"]
                    time_above_44 += dt_sample

            return {
                "skin_temp_final": round(T_skin_final, 3),
                "skin_temp_max": round(T_skin_max, 3),
                "time_above_44C_s": round(time_above_44, 1),
                "time_above_44C_min": round(time_above_44 / 60.0, 2),
                "total_thickness_m": round(L, 5),
                "n_grid_points": N,
                "n_time_steps": n_steps,
                "dt_s": round(dt, 4),
                "temperature_curve": skin_temps[::max(1, len(skin_temps) // 20)],
                "ambient_temp": T_ambient,
                "duration_s": total_time,
            }

        if __name__ == "__main__":
            print(json.dumps(solve({}), ensure_ascii=False))
    ''')

    model_ir = {
        "ir_version": "1.0",
        "model_id": "M-2018A-PDE",
        "model_family": {
            "primary": "numerical_pde",
            "secondary": ["optimization", "inverse_problem", "ode_models"]
        },
        "problem_binding": {
            "problem_id": "2018_A",
            "sub_questions": ["Q1", "Q2", "Q3"],
            "focus": "Q1 温度分布计算"
        },
        "assumptions": [
            {"assumption_id": "A1", "type": "projection",
             "statement": "一维热传导，忽略横向温度梯度，四层材料均匀各向同性",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A2", "type": "mechanism_assumption",
             "statement": "皮肤侧为对流边界（h=8 W/m²K），体核温度恒定37°C",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A3", "type": "simplification",
             "statement": "物性参数不随温度变化，忽略相变和辐射",
             "sub_question_binding": ["Q1"]}
        ],
        "variables": [
            {"variable_id": "v_T", "name": "温度场", "symbol": "T",
             "definition": "四层织物内的温度分布 T(x,t)", "unit": "°C",
             "type": "field", "sub_question_binding": ["Q1"]},
            {"variable_id": "v_Ts", "name": "皮肤侧温度", "symbol": "T_skin",
             "definition": "假人皮肤外侧（IV层右边界）的温度随时间变化", "unit": "°C",
             "type": "output", "value_range": {"min": 37, "max": 80},
             "sub_question_binding": ["Q1", "Q2", "Q3"]},
            {"variable_id": "v_t", "name": "时间", "symbol": "t",
             "definition": "工作时间", "unit": "s",
             "type": "independent", "value_range": {"min": 0, "max": 5400},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_x", "name": "空间坐标", "symbol": "x",
             "definition": "沿厚度方向坐标，x=0为I层外表面", "unit": "m",
             "type": "independent", "sub_question_binding": ["Q1"]}
        ],
        "parameters": [
            {"parameter_id": "p_k1", "name": "I层导热系数", "value": 0.045, "unit": "W/mK", "source": "假设"},
            {"parameter_id": "p_k2", "name": "II层导热系数", "value": 0.055, "unit": "W/mK", "source": "假设"},
            {"parameter_id": "p_d2", "name": "II层厚度", "value": 0.006, "unit": "m", "source": "题目Q1"},
            {"parameter_id": "p_d4", "name": "IV层厚度", "value": 0.005, "unit": "m", "source": "题目Q1"},
            {"parameter_id": "p_Tamb", "name": "环境温度", "value": 75, "unit": "°C", "source": "题目Q1"},
            {"parameter_id": "p_h", "name": "对流系数", "value": 8.0, "unit": "W/m²K", "source": "假设"}
        ],
        "objectives": [
            {"objective_id": "OBJ1", "type": "estimate",
             "expression": "计算温度场T(x,t)和皮肤侧温度T_skin(t)",
             "variables_refs": ["v_T", "v_Ts", "v_t", "v_x"],
             "sub_question_binding": ["Q1"]}
        ],
        "constraints": [
            {"constraint_id": "C1", "type": "temperature_limit",
             "expression": "T_skin(t) <= 47°C（工作结束时）",
             "variables_refs": ["v_Ts"], "source": "题目Q2/Q3",
             "sub_question_binding": ["Q2", "Q3"]},
            {"constraint_id": "C2", "type": "time_limit",
             "expression": "T_skin超过44°C的累计时间 <= 5分钟",
             "variables_refs": ["v_Ts", "v_t"], "source": "题目Q2/Q3",
             "sub_question_binding": ["Q2", "Q3"]}
        ],
        "mechanisms": [
            {"mechanism_id": "M1", "name": "Fourier热传导定律",
             "description": "一维瞬态热传导方程ρc∂T/∂t = k∂²T/∂x²，层间界面用调和平均热导率",
             "equations_refs": ["EQ1"], "sub_question_binding": ["Q1"]}
        ],
        "equations": [
            {"equation_id": "EQ1", "latex": "\\rho_i c_i \\frac{\\partial T}{\\partial t} = k_i \\frac{\\partial^2 T}{\\partial x^2}, \\quad x\\in\\Omega_i,\\; i=1,2,3,4",
             "type": "pde", "variables_refs": ["v_T", "v_x", "v_t"],
             "derivation_trace": "由Fourier定律与能量守恒导出，i遍历I-IV层",
             "sub_question_binding": ["Q1"]},
            {"equation_id": "EQ2", "latex": "-k\\frac{\\partial T}{\\partial x}\\bigg|_{x=L} = h(T(L,t)-T_{body})",
             "type": "boundary_condition", "variables_refs": ["v_Ts", "v_x"],
             "derivation_trace": "皮肤侧对流边界（Newton冷却定律）",
             "sub_question_binding": ["Q1"]}
        ],
        "dependencies": [],
        "solvers": [
            {"solver_id": "S1", "name": "显式有限差分法",
             "description": "时间前向+空间中心差分，dt满足CFL稳定性条件，层间界面调和平均",
             "sub_question_binding": ["Q1"]}
        ],
        "experiments": [
            {"experiment_id": "E1", "name": "75°C环境90分钟温度场",
             "description": "II层6mm/IV层5mm，环境75°C，工作90分钟，计算皮肤侧温度曲线",
             "sub_question_binding": ["Q1"]}
        ],
        "validations": [
            {"validation_id": "V1", "type": "stability",
             "description": "显式FDM满足CFL条件 dt <= dx²/(2α_max)",
             "sub_question_binding": ["Q1"]},
            {"validation_id": "V2", "type": "boundary_check",
             "description": "左边界温度恒等于环境温度，右边界满足对流条件",
             "sub_question_binding": ["Q1"]}
        ],
        "claims": [
            {"claim_id": "CL1", "statement": "一维四层瞬态热传导FDM可稳定计算皮肤侧温度变化",
             "evidence_refs": ["E1", "V1"], "sub_question_binding": ["Q1"]}
        ],
        "model_graph": {"nodes": 4, "edges": 3, "type": "layered_1d"},
        "modeling_trace": [
            {"step": 1, "action": "physics_modeling", "detail": "一维瞬态热传导PDE"},
            {"step": 2, "action": "discretization", "detail": "显式FDM，CFL稳定时间步"},
            {"step": 3, "action": "boundary_handling", "detail": "左Dirichlet+右对流Neumann"}
        ]
    }

    model_doc = textwrap.dedent('''\
        # 2018_A 高温作业专用服装设计 — 模型文档（自由文本）

        ## 1. 问题理解
        专用服装由四层织物（I-II-III-IV）构成，需在高温环境下保护假人皮肤。Q1要求给定环境温度75°C、II层厚度6mm、IV层厚度5mm、工作90分钟，建立数学模型计算温度分布。

        ## 2. 假设
        - 一维热传导，忽略横向温度梯度，四层材料均匀各向同性
        - 皮肤侧为对流边界（h=8 W/m²K），体核温度恒定37°C
        - 物性参数不随温度变化，忽略相变和辐射
        - 左边界（I层外表面）温度恒等于环境温度75°C

        ## 3. 变量
        - T(x,t)：四层织物内的温度场（°C）
        - T_skin(t)：皮肤侧温度（IV层右边界）随时间变化
        - t：工作时间（s）
        - x：沿厚度方向空间坐标（m）

        ## 4. 参数
        - I层：k=0.045 W/mK, ρc=1.2e6 J/m³K, d=6mm
        - II层：k=0.055, ρc=1.0e6, d=6mm
        - III层：k=0.065, ρc=0.8e6, d=4mm
        - IV层：k=0.028, ρc=1.2e3, d=5mm
        - 环境温度75°C，对流系数8 W/m²K，工作时间5400s

        ## 5. 目标
        计算温度场T(x,t)和皮肤侧温度T_skin(t)，生成温度分布。

        ## 6. 约束
        - 皮肤侧温度不超过47°C（Q2/Q3设计约束）
        - 超过44°C的累计时间不超过5分钟

        ## 7. 机理与方程
        由Fourier热传导定律与能量守恒导出一维瞬态热传导方程：
        ρ_i c_i ∂T/∂t = k_i ∂²T/∂x², x∈Ω_i, i=1,2,3,4
        左边界T(0,t)=T_ambient（Dirichlet），右边界-k∂T/∂x|_L = h(T(L,t)-T_body)（对流Neumann）。

        ## 8. 求解方法与实验
        显式有限差分法：时间前向差分+空间中心差分，时间步长满足CFL稳定性条件dt≤dx²/(2α_max)。层间界面用调和平均热导率。空间步长0.5mm，约42个网格点。实验：75°C环境90分钟，II层6mm/IV层5mm。

        ## 9. 验证
        - 稳定性检验：CFL条件满足
        - 边界检验：左边界恒为环境温度，右边界满足对流条件
        - 物理合理性：皮肤侧温度应在37°C基础上升，最终趋于稳态
    ''')

    validation_plan = {
        "plan_id": "VP-2018A",
        "limit_tests": [
            {"name": "零厚度II层", "description": "d2=0时II层消失，热阻减小，皮肤温度应更高",
             "expected": "T_skin_max > 基准值"},
            {"name": "环境温度=体温", "description": "T_ambient=37°C时无温差，皮肤温度应恒为37°C",
             "expected": "T_skin_final≈37.0"}
        ],
        "sensitivity": [
            {"parameter": "II层厚度", "range": [0.003, 0.006, 0.012],
             "expected_effect": "厚度增加→热阻增大→皮肤温度降低"},
            {"parameter": "环境温度", "range": [65, 75, 85],
             "expected_effect": "环境温度升高→皮肤温度单调升高"}
        ],
        "validation_targets": ["OBJ1"],
        "constraint_violation_check": True,
        "residual_check": True
    }

    output_mapping = {
        "皮肤侧温度": "skin_temp_final", "T_skin": "skin_temp_final",
        "最高皮肤温度": "skin_temp_max",
        "超温时间": "time_above_44C_s",
        "温度场": "temperature_curve", "T": "temperature_curve",
        "时间": "duration_s", "t": "duration_s",
    }

    return {
        "problem_id": "2018_A", "title": "高温作业专用服装设计",
        "code": code, "model_ir": model_ir, "model_doc": model_doc,
        "validation_plan": validation_plan, "output_mapping": output_mapping,
        "family_primary": "numerical_pde",
        "sub_questions": ["Q1", "Q2", "Q3"],
    }


# ============================================================
# 2019_C — 机场出租车决策（排队论 M/M/1 + 收益比较）
# ============================================================
def problem_2019_C() -> dict:
    code = textwrap.dedent('''\
        """2019_C 机场出租车决策 — M/M/1排队模型+收益比较（自包含，纯标准库）。"""
        import json
        import math

        def solve(inputs: dict) -> dict:
            # 系统参数
            lambda_pass = 30.0    # 乘客到达率（人/分钟）
            mu_taxi = 40.0        # 出租车服务率（辆/分钟，含上车时间）
            avg_fare_queue = 80.0  # 排队载客平均车费（元）
            avg_fare_city = 50.0   # 放空回市区拉客平均车费（元）
            waiting_cost = 1.5     # 等待时间成本（元/分钟，含燃油+机会成本）
            empty_cost = 25.0      # 放空回市区成本（元，含燃油+时间）
            fuel_idle = 0.5        # 怠速燃油成本（元/分钟）
            n_taxis_pool = 50      # 蓄车池已有出租车数

            # M/M/1 排队分析
            rho = lambda_pass / mu_taxi
            if rho >= 1.0:
                W_q = float("inf")
                L_q = float("inf")
                queue_stable = False
            else:
                W_q = 1.0 / (mu_taxi - lambda_pass)  # 平均等待时间（分钟）
                L_q = lambda_pass / (mu_taxi - lambda_pass)  # 平均排队长度
                queue_stable = True

            # 排队策略期望收益
            profit_queue = avg_fare_queue - (waiting_cost + fuel_idle) * W_q

            # 放空回市区策略期望收益
            time_city = 20.0  # 回市区+拉客平均时间（分钟）
            profit_city = avg_fare_city - empty_cost - waiting_cost * time_city

            # 决策
            if profit_queue > profit_city:
                decision = "queue"
                decision_cn = "前往到达区排队等待载客"
            else:
                decision = "return"
                decision_cn = "直接放空返回市区拉客"

            # 临界到达率（排队收益=放空收益时的lambda）
            # profit_queue = fare_q - (wc+fi)/(mu-lambda) = profit_city
            # => 1/(mu-lambda) = (fare_q - profit_city)/(wc+fi)
            diff = avg_fare_queue - profit_city
            if diff > 0 and (waiting_cost + fuel_idle) > 0:
                lambda_crit = mu_taxi - (waiting_cost + fuel_idle) / diff
            else:
                lambda_crit = 0.0

            # 不同到达率下的决策扫描
            scan = []
            for lam in [10, 15, 20, 25, 28, 30, 32, 35, 38]:
                if lam < mu_taxi:
                    w = 1.0 / (mu_taxi - lam)
                    pq = avg_fare_queue - (waiting_cost + fuel_idle) * w
                else:
                    w = float("inf")
                    pq = float("-inf")
                scan.append({
                    "lambda": lam,
                    "wait_min": round(w, 2) if w != float("inf") else None,
                    "profit_queue": round(pq, 2) if pq != float("-inf") else None,
                    "profit_city": round(profit_city, 2),
                    "optimal": "queue" if pq > profit_city else "return"
                })

            return {
                "optimal_decision": decision,
                "optimal_decision_cn": decision_cn,
                "profit_queue": round(profit_queue, 2),
                "profit_city": round(profit_city, 2),
                "profit_diff": round(profit_queue - profit_city, 2),
                "expected_wait_min": round(W_q, 2) if queue_stable else None,
                "queue_length_avg": round(L_q, 2) if queue_stable else None,
                "rho_utilization": round(rho, 4),
                "queue_stable": queue_stable,
                "lambda_critical": round(lambda_crit, 2),
                "n_taxis_in_pool": n_taxis_pool,
                "decision_scan": scan,
            }

        if __name__ == "__main__":
            print(json.dumps(solve({}), ensure_ascii=False))
    ''')

    model_ir = {
        "ir_version": "1.0",
        "model_id": "M-2019C-QUEUE",
        "model_family": {
            "primary": "queuing_theory",
            "secondary": ["decision_analysis", "optimization", "game_theory"]
        },
        "problem_binding": {
            "problem_id": "2019_C",
            "sub_questions": ["Q1", "Q2", "Q3", "Q4"],
            "focus": "Q1 出租车司机选择决策模型"
        },
        "assumptions": [
            {"assumption_id": "A1", "type": "mechanism_assumption",
             "statement": "乘客到达服从Poisson过程（λ=30/分钟），出租车服务时间服从指数分布（μ=40/分钟）",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A2", "type": "simplification",
             "statement": "蓄车池为单服务台M/M/1模型，先到先服务",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A3", "type": "projection",
             "statement": "放空回市区的时间和成本为确定值，忽略交通波动",
             "sub_question_binding": ["Q1"]}
        ],
        "variables": [
            {"variable_id": "v_lambda", "name": "乘客到达率", "symbol": "lambda",
             "definition": "单位时间到达乘车区的乘客数", "unit": "人/分钟",
             "type": "input", "value_range": {"min": 0, "max": 60},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_mu", "name": "服务率", "symbol": "mu",
             "definition": "单位时间一辆出租车可完成的载客服务数", "unit": "辆/分钟",
             "type": "input", "value_range": {"min": 0, "max": 100},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_Wq", "name": "平均等待时间", "symbol": "W_q",
             "definition": "出租车在蓄车池的平均等待时间", "unit": "分钟",
             "type": "output", "value_range": {"min": 0, "max": 120},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_pq", "name": "排队收益", "symbol": "profit_q",
             "definition": "排队等待载客策略的期望净收益", "unit": "元",
             "type": "output", "sub_question_binding": ["Q1"]},
            {"variable_id": "v_pc", "name": "放空收益", "symbol": "profit_c",
             "definition": "放空回市区拉客策略的期望净收益", "unit": "元",
             "type": "output", "sub_question_binding": ["Q1"]},
            {"variable_id": "v_dec", "name": "最优决策", "symbol": "decision",
             "definition": "司机应选择的策略（queue/return）", "unit": "无",
             "type": "output", "sub_question_binding": ["Q1"]}
        ],
        "parameters": [
            {"parameter_id": "p_lam", "name": "乘客到达率", "value": 30, "unit": "人/分钟", "source": "假设"},
            {"parameter_id": "p_mu", "name": "服务率", "value": 40, "unit": "辆/分钟", "source": "假设"},
            {"parameter_id": "p_fare_q", "name": "排队平均车费", "value": 80, "unit": "元", "source": "假设"},
            {"parameter_id": "p_fare_c", "name": "市区平均车费", "value": 50, "unit": "元", "source": "假设"},
            {"parameter_id": "p_wc", "name": "等待成本", "value": 1.5, "unit": "元/分钟", "source": "假设"},
            {"parameter_id": "p_ec", "name": "放空成本", "value": 25, "unit": "元", "source": "假设"}
        ],
        "objectives": [
            {"objective_id": "OBJ1", "type": "max",
             "expression": "maximize 司机期望净收益 max(profit_q, profit_c)",
             "variables_refs": ["v_pq", "v_pc", "v_dec"],
             "sub_question_binding": ["Q1"]}
        ],
        "constraints": [
            {"constraint_id": "C1", "type": "stability",
             "expression": "系统稳定要求 rho=lambda/mu < 1",
             "variables_refs": ["v_lambda", "v_mu"], "source": "排队论",
             "sub_question_binding": ["Q1"]},
            {"constraint_id": "C2", "type": "nonnegative",
             "expression": "等待时间 W_q >= 0",
             "variables_refs": ["v_Wq"], "source": "物理约束",
             "sub_question_binding": ["Q1"]}
        ],
        "mechanisms": [
            {"mechanism_id": "M1", "name": "M/M/1排队系统",
             "description": "Poisson到达+指数服务+单服务台+先到先服务，由Little定律和生灭过程推导稳态指标",
             "equations_refs": ["EQ1", "EQ2"], "sub_question_binding": ["Q1"]}
        ],
        "equations": [
            {"equation_id": "EQ1", "latex": "W_q = \\frac{1}{\\mu - \\lambda}, \\quad \\rho = \\frac{\\lambda}{\\mu} < 1",
             "type": "queueing_formula", "variables_refs": ["v_Wq", "v_lambda", "v_mu"],
             "derivation_trace": "M/M/1稳态平均等待时间，由生灭过程平衡方程推导",
             "sub_question_binding": ["Q1"]},
            {"equation_id": "EQ2", "latex": "\\pi_q = F_q - (c_w+c_f)W_q, \\quad \\pi_c = F_c - C_e - c_w t_c",
             "type": "profit_formula", "variables_refs": ["v_pq", "v_pc", "v_Wq"],
             "derivation_trace": "排队收益=车费-等待成本×等待时间；放空收益=市区车费-放空成本-时间成本",
             "sub_question_binding": ["Q1"]}
        ],
        "dependencies": [],
        "solvers": [
            {"solver_id": "S1", "name": "M/M/1解析求解+收益比较",
             "description": "解析计算排队指标，比较两策略期望收益，求临界到达率",
             "sub_question_binding": ["Q1"]}
        ],
        "experiments": [
            {"experiment_id": "E1", "name": "基准场景决策",
             "description": "λ=30/分钟, μ=40/分钟, 排队车费80元, 市区车费50元，比较最优决策",
             "sub_question_binding": ["Q1"]},
            {"experiment_id": "E2", "name": "到达率敏感性扫描",
             "description": "λ从10到38扫描，观测决策切换点和临界到达率",
             "sub_question_binding": ["Q1"]}
        ],
        "validations": [
            {"validation_id": "V1", "type": "stability",
             "description": "rho<1时系统稳定，W_q有限；rho>=1时队列无限增长",
             "sub_question_binding": ["Q1"]},
            {"validation_id": "V2", "type": "monotonicity",
             "description": "等待时间W_q随λ增大而单调增大，排队收益随λ增大而单调减小",
             "sub_question_binding": ["Q1"]}
        ],
        "claims": [
            {"claim_id": "CL1", "statement": "M/M/1排队模型可量化出租车等待时间，收益比较给出最优决策",
             "evidence_refs": ["E1", "E2", "V1"], "sub_question_binding": ["Q1"]}
        ],
        "model_graph": {"nodes": 3, "edges": 2, "type": "decision_tree"},
        "modeling_trace": [
            {"step": 1, "action": "queue_modeling", "detail": "蓄车池建模为M/M/1"},
            {"step": 2, "action": "profit_modeling", "detail": "两策略期望收益公式"},
            {"step": 3, "action": "decision_rule", "detail": "收益比较+临界到达率"}
        ]
    }

    model_doc = textwrap.dedent('''\
        # 2019_C 机场出租车问题 — 模型文档（自由文本）

        ## 1. 问题理解
        送客到机场的出租车司机面临两个选择：(A)前往到达区排队等待载客返回市区，需付出等待时间成本；(B)直接放空返回市区拉客，需付出空载费用和潜在收益损失。Q1要求建立司机选择决策模型并给出策略。

        ## 2. 假设
        - 乘客到达服从Poisson过程（λ=30人/分钟），出租车服务时间服从指数分布（μ=40辆/分钟）
        - 蓄车池为单服务台M/M/1模型，先到先服务
        - 放空回市区的时间和成本为确定值，忽略交通波动
        - 排队载客平均车费80元，市区拉客平均车费50元

        ## 3. 变量
        - λ：乘客到达率（人/分钟）
        - μ：出租车服务率（辆/分钟）
        - W_q：平均等待时间（分钟）
        - profit_q：排队策略期望净收益（元）
        - profit_c：放空策略期望净收益（元）
        - decision：最优决策（queue/return）

        ## 4. 参数
        - 等待成本1.5元/分钟，怠速燃油0.5元/分钟
        - 放空成本25元，回市区时间20分钟
        - 蓄车池已有50辆出租车

        ## 5. 目标
        最大化司机期望净收益 max(profit_q, profit_c)。

        ## 6. 约束
        - 系统稳定要求 ρ=λ/μ < 1
        - 等待时间 W_q >= 0

        ## 7. 机理与方程
        M/M/1排队系统：Poisson到达+指数服务+单服务台+FCFS。
        平均等待时间 W_q = 1/(μ-λ)，ρ=λ/μ<1。
        排队收益 π_q = F_q - (c_w+c_f)W_q；放空收益 π_c = F_c - C_e - c_w t_c。

        ## 8. 求解方法与实验
        解析计算M/M/1稳态指标，比较两策略期望收益，求临界到达率λ*（排队收益=放空收益）。
        实验1：基准场景（λ=30, μ=40）决策。
        实验2：λ从10到38扫描，观测决策切换点。

        ## 9. 验证
        - 稳定性：ρ<1时W_q有限，ρ>=1时队列无限增长
        - 单调性：W_q随λ增大而增大，排队收益随λ增大而减小
        - 决策一致性：扫描结果中决策切换点与解析临界值一致
    ''')

    validation_plan = {
        "plan_id": "VP-2019C",
        "limit_tests": [
            {"name": "零到达率", "description": "λ=0时无乘客，排队收益应为负无穷（永远等不到）",
             "expected": "decision=return"},
            {"name": "高到达率接近服务率", "description": "λ→μ⁻时W_q→∞，排队收益→-∞",
             "expected": "decision=return"}
        ],
        "sensitivity": [
            {"parameter": "乘客到达率λ", "range": [10, 20, 30, 38],
             "expected_effect": "λ增大→等待时间增大→排队收益减小→可能切换为return"},
            {"parameter": "排队车费F_q", "range": [50, 80, 120],
             "expected_effect": "车费增加→排队收益增大→更倾向queue"}
        ],
        "validation_targets": ["OBJ1"],
        "constraint_violation_check": True,
        "residual_check": False
    }

    output_mapping = {
        "最优决策": "optimal_decision", "decision": "optimal_decision",
        "排队收益": "profit_queue", "profit_q": "profit_queue",
        "放空收益": "profit_city", "profit_c": "profit_city",
        "平均等待时间": "expected_wait_min", "W_q": "expected_wait_min",
        "乘客到达率": "lambda_critical", "lambda": "lambda_critical",
        "服务率": "rho_utilization", "mu": "rho_utilization",
    }

    return {
        "problem_id": "2019_C", "title": "机场的出租车问题",
        "code": code, "model_ir": model_ir, "model_doc": model_doc,
        "validation_plan": validation_plan, "output_mapping": output_mapping,
        "family_primary": "queuing_theory",
        "sub_questions": ["Q1", "Q2", "Q3", "Q4"],
    }


# ============================================================
# 2018_B — 智能RGV动态调度（离散事件仿真 + 贪心调度）
# ============================================================
def problem_2018_B() -> dict:
    code = textwrap.dedent('''\
        """2018_B 智能RGV动态调度 — 离散事件仿真+贪心调度（自包含，纯标准库）。"""
        import json
        import heapq

        def solve(inputs: dict) -> dict:
            # 系统参数（第1组数据）
            move_times = {1: 20, 2: 33, 3: 46}  # RGV移动1/2/3个单位时间（秒）
            process_time = 560  # 一道工序加工时间（秒）
            load_odd = 28   # RGV为1#,3#,5#,7#上下料时间
            load_even = 31  # RGV为2#,4#,6#,8#上下料时间
            clean_time = 25  # 清洗时间
            n_cnc = 8
            shift_time = 8 * 3600  # 8小时 = 28800秒

            def move_time(from_pos, to_pos):
                dist = abs(from_pos - to_pos)
                if dist == 0:
                    return 0
                # 线性插值：已知1/2/3单位时间
                if dist <= 3:
                    return move_times[dist]
                # 超过3单位：用3单位时间 + 每额外单位约13秒
                return move_times[3] + (dist - 3) * 13

            # 离散事件仿真
            # 事件: (time, type, cnc_id)
            # type: "cnc_done" (CNC加工完成), "rgv_arrive" (RGV到达某CNC)
            events = []
            # CNC状态: "idle" / "processing" / "done_waiting"
            cnc_state = ["idle"] * n_cnc
            cnc_done_time = [0.0] * n_cnc
            cnc_parts = [0] * n_cnc  # 每台CNC完成的物料数

            rgv_pos = 0  # RGV初始位置（在1#CNC旁，位置索引0）
            rgv_busy_until = 0.0
            total_parts = 0
            rgv_move_total = 0.0
            rgv_idle_total = 0.0
            last_event_time = 0.0

            # 初始化：所有CNC idle，RGV依次上料
            # 贪心策略：RGV总是去最近的需要上下料的CNC
            def find_nearest_idle(pos):
                best = None
                best_dist = float("inf")
                for i in range(n_cnc):
                    if cnc_state[i] == "idle":
                        d = abs(pos - i)
                        if d < best_dist:
                            best_dist = d
                            best = i
                return best

            def find_nearest_done(pos):
                best = None
                best_time = float("inf")
                for i in range(n_cnc):
                    if cnc_state[i] == "done_waiting":
                        if cnc_done_time[i] < best_time:
                            best_time = cnc_done_time[i]
                            best = i
                    elif cnc_state[i] == "processing":
                        if cnc_done_time[i] < best_time:
                            best_time = cnc_done_time[i]
                            best = i
                return best

            current_time = 0.0
            # 初始：给所有CNC上料（RGV依次移动）
            init_order = list(range(n_cnc))
            for cnc_id in init_order:
                mt = move_time(rgv_pos, cnc_id)
                current_time += mt
                rgv_move_total += mt
                lt = load_odd if cnc_id % 2 == 0 else load_even
                current_time += lt
                cnc_state[cnc_id] = "processing"
                cnc_done_time[cnc_id] = current_time + process_time
                rgv_pos = cnc_id

            # 主仿真循环
            while current_time < shift_time:
                # 找最近的已完成或即将完成的CNC
                target = find_nearest_done(rgv_pos)
                if target is None:
                    break

                # 移动到目标
                mt = move_time(rgv_pos, target)
                arrival_time = current_time + mt
                rgv_move_total += mt

                # 等待CNC加工完成（如果还没完成）
                if arrival_time < cnc_done_time[target]:
                    wait = cnc_done_time[target] - arrival_time
                    rgv_idle_total += wait
                    arrival_time = cnc_done_time[target]

                if arrival_time > shift_time:
                    break

                # 下料+上料+清洗
                lt = load_odd if target % 2 == 0 else load_even
                service_time = lt * 2 + clean_time  # 下料+上料+清洗
                finish_time = arrival_time + service_time

                if finish_time > shift_time:
                    break

                # 完成一个物料
                total_parts += 1
                cnc_parts[target] += 1
                cnc_state[target] = "processing"
                cnc_done_time[target] = finish_time + process_time
                current_time = finish_time
                rgv_pos = target

            # 统计
            utilization = []
            for i in range(n_cnc):
                busy = cnc_parts[i] * process_time
                utilization.append(round(min(1.0, busy / shift_time), 4))

            avg_cycle = shift_time / total_parts if total_parts > 0 else 0
            rgv_util = round(1.0 - rgv_idle_total / shift_time, 4) if shift_time > 0 else 0

            return {
                "total_parts": total_parts,
                "throughput_per_hour": round(total_parts / 8.0, 2),
                "avg_cycle_time_s": round(avg_cycle, 2),
                "rgv_utilization": rgv_util,
                "rgv_move_total_s": round(rgv_move_total, 1),
                "rgv_idle_total_s": round(rgv_idle_total, 1),
                "cnc_utilization": utilization,
                "cnc_parts_per_machine": cnc_parts,
                "shift_duration_s": shift_time,
                "n_cnc": n_cnc,
                "process_time_s": process_time,
                "scheduling_strategy": "greedy_nearest",
            }

        if __name__ == "__main__":
            print(json.dumps(solve({}), ensure_ascii=False))
    ''')

    model_ir = {
        "ir_version": "1.0",
        "model_id": "M-2018B-DES",
        "model_family": {
            "primary": "simulation",
            "secondary": ["optimization", "graph_algorithm", "metaheuristics"]
        },
        "problem_binding": {
            "problem_id": "2018_B",
            "sub_questions": ["Q1", "Q2", "Q3"],
            "focus": "任务1 一道工序RGV动态调度模型"
        },
        "assumptions": [
            {"assumption_id": "A1", "type": "projection",
             "statement": "一道工序情形，8台CNC安装相同刀具，物料可在任一台加工完成",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A2", "type": "mechanism_assumption",
             "statement": "RGV采用贪心最近策略：总是前往最近的已完成或即将完成的CNC进行上下料",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A3", "type": "simplification",
             "statement": "忽略CNC故障（Q3单独考虑），物料充足，清洗后直接上料",
             "sub_question_binding": ["Q1"]}
        ],
        "variables": [
            {"variable_id": "v_N", "name": "完成物料数", "symbol": "N",
             "definition": "一个班次内系统完成的物料总数", "unit": "件",
             "type": "output", "value_range": {"min": 0, "max": 500},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_thr", "name": "吞吐量", "symbol": "throughput",
             "definition": "每小时完成的物料数", "unit": "件/小时",
             "type": "output", "sub_question_binding": ["Q1"]},
            {"variable_id": "v_cyc", "name": "平均周期", "symbol": "cycle",
             "definition": "完成一件物料的平均时间", "unit": "秒",
             "type": "output", "sub_question_binding": ["Q1"]},
            {"variable_id": "v_util", "name": "RGV利用率", "symbol": "util",
             "definition": "RGV非空闲时间占比", "unit": "比例",
             "type": "output", "value_range": {"min": 0, "max": 1},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_cnc", "name": "CNC利用率", "symbol": "cnc_util",
             "definition": "每台CNC的加工时间占比", "unit": "比例",
             "type": "output", "sub_question_binding": ["Q1"]}
        ],
        "parameters": [
            {"parameter_id": "p_pt", "name": "加工时间", "value": 560, "unit": "秒", "source": "表1第1组"},
            {"parameter_id": "p_m1", "name": "移动1单位时间", "value": 20, "unit": "秒", "source": "表1第1组"},
            {"parameter_id": "p_lo", "name": "奇数CNC上下料", "value": 28, "unit": "秒", "source": "表1第1组"},
            {"parameter_id": "p_le", "name": "偶数CNC上下料", "value": 31, "unit": "秒", "source": "表1第1组"},
            {"parameter_id": "p_ct", "name": "清洗时间", "value": 25, "unit": "秒", "source": "表1第1组"},
            {"parameter_id": "p_shift", "name": "班次时长", "value": 28800, "unit": "秒", "source": "题目"}
        ],
        "objectives": [
            {"objective_id": "OBJ1", "type": "max",
             "expression": "maximize 班次内完成物料数 N（即系统吞吐量）",
             "variables_refs": ["v_N", "v_thr"],
             "sub_question_binding": ["Q1"]}
        ],
        "constraints": [
            {"constraint_id": "C1", "type": "resource",
             "expression": "RGV同一时刻只能为一台CNC服务",
             "variables_refs": ["v_util"], "source": "物理约束",
             "sub_question_binding": ["Q1"]},
            {"constraint_id": "C2", "type": "sequence",
             "expression": "CNC必须完成当前物料加工后才能上下料",
             "variables_refs": ["v_cnc"], "source": "工艺约束",
             "sub_question_binding": ["Q1"]}
        ],
        "mechanisms": [
            {"mechanism_id": "M1", "name": "离散事件仿真",
             "description": "以事件驱动模拟RGV移动、CNC加工、上下料清洗等操作，时间推进到下一事件",
             "equations_refs": ["EQ1"], "sub_question_binding": ["Q1"]}
        ],
        "equations": [
            {"equation_id": "EQ1", "latex": "N = \\sum_{i=1}^{8} n_i, \\quad \\text{throughput} = N / T_{shift}",
             "type": "accounting", "variables_refs": ["v_N", "v_thr", "v_cnc"],
             "derivation_trace": "总产出为各CNC产出之和，吞吐量为总产出除以班次时长",
             "sub_question_binding": ["Q1"]}
        ],
        "dependencies": [],
        "solvers": [
            {"solver_id": "S1", "name": "贪心最近调度+离散事件仿真",
             "description": "RGV总是前往最近的已完成/即将完成CNC，事件驱动仿真8小时班次",
             "sub_question_binding": ["Q1"]}
        ],
        "experiments": [
            {"experiment_id": "E1", "name": "第1组参数一道工序",
             "description": "使用表1第1组数据（移动20/33/46s, 加工560s, 上下料28/31s, 清洗25s），仿真8小时",
             "sub_question_binding": ["Q1"]}
        ],
        "validations": [
            {"validation_id": "V1", "type": "conservation",
             "description": "总物料数=各CNC物料数之和",
             "sub_question_binding": ["Q1"]},
            {"validation_id": "V2", "type": "utilization_bound",
             "description": "CNC利用率和RGV利用率均在[0,1]范围内",
             "sub_question_binding": ["Q1"]}
        ],
        "claims": [
            {"claim_id": "CL1", "statement": "贪心最近调度策略在一道工序下可实现较高系统吞吐量",
             "evidence_refs": ["E1", "V1"], "sub_question_binding": ["Q1"]}
        ],
        "model_graph": {"nodes": 9, "edges": 8, "type": "linear_track"},
        "modeling_trace": [
            {"step": 1, "action": "system_modeling", "detail": "8CNC+1RGV线性轨道系统"},
            {"step": 2, "action": "scheduling_design", "detail": "贪心最近调度策略"},
            {"step": 3, "action": "des_implementation", "detail": "事件驱动离散事件仿真"}
        ]
    }

    model_doc = textwrap.dedent('''\
        # 2018_B 智能RGV动态调度 — 模型文档（自由文本）

        ## 1. 问题理解
        智能加工系统由8台CNC、1辆RGV、直线轨道、上下料传送带组成。RGV可在轨道上移动，为CNC上下料并清洗物料。任务1要求对一道工序情形给出RGV动态调度模型和求解算法，并用表1第1组数据检验。

        ## 2. 假设
        - 一道工序：每台CNC安装相同刀具，物料可在任一台加工完成
        - RGV采用贪心最近策略：总是前往最近的已完成或即将完成的CNC
        - 忽略CNC故障（Q3单独考虑），物料充足
        - 班次连续作业8小时（28800秒）

        ## 3. 变量
        - N：班次内完成物料总数（件）
        - throughput：每小时完成物料数（件/小时）
        - cycle：完成一件物料的平均周期（秒）
        - util：RGV利用率（非空闲时间占比）
        - cnc_util：每台CNC的利用率

        ## 4. 参数（表1第1组）
        - RGV移动1/2/3单位：20/33/46秒
        - 一道工序加工时间：560秒
        - 奇数CNC上下料：28秒，偶数CNC上下料：31秒
        - 清洗时间：25秒
        - 班次时长：28800秒

        ## 5. 目标
        最大化班次内完成物料数N（即系统吞吐量）。

        ## 6. 约束
        - RGV同一时刻只能为一台CNC服务
        - CNC必须完成当前物料加工后才能上下料
        - 物料加工完成后必须经RGV清洗下料

        ## 7. 机理与方程
        离散事件仿真：以事件驱动模拟系统运行。事件类型包括CNC加工完成、RGV到达某CNC。
        总产出 N = Σ n_i（i=1..8），吞吐量 = N / T_shift。

        ## 8. 求解方法与实验
        贪心最近调度+离散事件仿真：RGV总是前往最近的已完成或即将完成的CNC，执行下料+清洗+上料，然后移动到下一个目标。初始阶段依次为所有CNC上料。
        实验：表1第1组数据，一道工序，仿真8小时。

        ## 9. 验证
        - 守恒检验：总物料数=各CNC物料数之和
        - 利用率边界：CNC和RGV利用率均在[0,1]
        - 物理合理性：吞吐量受加工时间560s/8台≈理论上限51件/小时约束
    ''')

    validation_plan = {
        "plan_id": "VP-2018B",
        "limit_tests": [
            {"name": "单CNC系统", "description": "n_cnc=1时RGV无需移动，吞吐量受加工时间+上下料限制",
             "expected": "throughput ≈ 3600/(560+28*2+25)"},
            {"name": "零移动时间", "description": "move_time=0时RGV可瞬间到达，吞吐量应提高",
             "expected": "total_parts > 基准值"}
        ],
        "sensitivity": [
            {"parameter": "加工时间", "range": [400, 560, 700],
             "expected_effect": "加工时间减少→CNC利用率降低→RGV成为瓶颈→吞吐量可能不增"},
            {"parameter": "CNC数量", "range": [4, 8, 12],
             "expected_effect": "CNC增加→并行度提高→吞吐量增加但边际递减"}
        ],
        "validation_targets": ["OBJ1"],
        "constraint_violation_check": True,
        "residual_check": False
    }

    output_mapping = {
        "完成物料数": "total_parts", "N": "total_parts",
        "吞吐量": "throughput_per_hour", "throughput": "throughput_per_hour",
        "平均周期": "avg_cycle_time_s", "cycle": "avg_cycle_time_s",
        "RGV利用率": "rgv_utilization", "util": "rgv_utilization",
        "CNC利用率": "cnc_utilization", "cnc_util": "cnc_utilization",
    }

    return {
        "problem_id": "2018_B", "title": "智能RGV的动态调度策略",
        "code": code, "model_ir": model_ir, "model_doc": model_doc,
        "validation_plan": validation_plan, "output_mapping": output_mapping,
        "family_primary": "simulation",
        "sub_questions": ["Q1", "Q2", "Q3"],
    }


# ============================================================
# 2017_B — 拍照赚钱任务定价（Logistic回归 + 定价优化）
# ============================================================
def problem_2017_B() -> dict:
    code = textwrap.dedent('''\
        """2017_B 拍照赚钱任务定价 — Logistic回归+定价优化（自包含，纯标准库）。"""
        import json
        import math
        import random

        def solve(inputs: dict) -> dict:
            random.seed(42)
            # 生成合成数据（模拟附件一：任务位置、定价、完成情况）
            n_tasks = 200
            data = []
            for i in range(n_tasks):
                # 任务到最近会员的距离（km）
                distance = random.expovariate(1.0 / 2.0)  # 均值2km
                distance = min(distance, 15.0)
                # 会员密度（附近会员数）
                member_density = max(1, int(random.gauss(10, 4)))
                # 原定价（元）
                price = round(15 + distance * 2 + random.gauss(0, 3), 1)
                price = max(5, price)
                # 完成概率（真实模型：价格越高、距离越近、会员越多→越可能完成）
                p_complete = 1.0 / (1.0 + math.exp(-(
                    -2.0 + 0.08 * price - 0.15 * distance + 0.05 * member_density
                )))
                completed = 1 if random.random() < p_complete else 0
                data.append({
                    "task_id": i, "distance_km": round(distance, 2),
                    "member_density": member_density, "price": price,
                    "completed": completed
                })

            # Logistic回归（梯度下降，纯Python）
            # 特征: [1, price, distance, member_density]
            def sigmoid(z):
                if z >= 0:
                    return 1.0 / (1.0 + math.exp(-z))
                else:
                    ez = math.exp(z)
                    return ez / (1.0 + ez)

            def predict(x, beta):
                z = sum(b * xi for b, xi in zip(beta, x))
                return sigmoid(z)

            # 标准化特征
            prices = [d["price"] for d in data]
            distances = [d["distance_km"] for d in data]
            densities = [d["member_density"] for d in data]
            p_mean, p_std = sum(prices) / len(prices), (sum((p - sum(prices)/len(prices))**2 for p in prices) / len(prices))**0.5 or 1
            d_mean, d_std = sum(distances) / len(distances), (sum((d - sum(distances)/len(distances))**2 for d in distances) / len(distances))**0.5 or 1
            m_mean, m_std = sum(densities) / len(densities), (sum((m - sum(densities)/len(densities))**2 for m in densities) / len(densities))**0.5 or 1

            X = []
            y = []
            for d in data:
                X.append([
                    1.0,
                    (d["price"] - p_mean) / p_std,
                    (d["distance_km"] - d_mean) / d_std,
                    (d["member_density"] - m_mean) / m_std,
                ])
                y.append(d["completed"])

            # 梯度下降
            beta = [0.0, 0.0, 0.0, 0.0]
            lr = 0.1
            n_epochs = 500
            losses = []
            for epoch in range(n_epochs):
                grad = [0.0, 0.0, 0.0, 0.0]
                loss = 0.0
                for xi, yi in zip(X, y):
                    pred = predict(xi, beta)
                    error = pred - yi
                    loss -= yi * math.log(max(pred, 1e-15)) + (1 - yi) * math.log(max(1 - pred, 1e-15))
                    for j in range(4):
                        grad[j] += error * xi[j]
                for j in range(4):
                    beta[j] -= lr * grad[j] / len(X)
                losses.append(round(loss / len(X), 6))

            # 模型评估
            correct = 0
            for xi, yi in zip(X, y):
                pred = predict(xi, beta)
                if (pred >= 0.5 and yi == 1) or (pred < 0.5 and yi == 0):
                    correct += 1
            accuracy = correct / len(X)

            # 实际完成率
            actual_completion = sum(d["completed"] for d in data) / len(data)

            # 定价优化：最大化期望利润 = price * P(完成|price, distance=均值, density=均值)
            best_price = 0
            best_profit = -1
            profit_curve = []
            for price_test in [5, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40]:
                x_test = [
                    1.0,
                    (price_test - p_mean) / p_std,
                    0.0,  # 距离均值
                    0.0,  # 密度均值
                ]
                p = predict(x_test, beta)
                profit = price_test * p
                profit_curve.append({"price": price_test, "completion_prob": round(p, 4),
                                     "expected_profit": round(profit, 2)})
                if profit > best_profit:
                    best_profit = profit
                    best_price = price_test

            return {
                "n_tasks": n_tasks,
                "actual_completion_rate": round(actual_completion, 4),
                "model_accuracy": round(accuracy, 4),
                "logistic_coefficients": {
                    "intercept": round(beta[0], 4),
                    "price": round(beta[1], 4),
                    "distance": round(beta[2], 4),
                    "member_density": round(beta[3], 4),
                },
                "coefficient_interpretation": {
                    "price": "正系数→价格越高完成概率越高（在合理范围内）",
                    "distance": "负系数→距离越远完成概率越低",
                    "member_density": "正系数→会员越多完成概率越高",
                },
                "optimal_price": best_price,
                "optimal_expected_profit": round(best_profit, 2),
                "profit_curve": profit_curve,
                "loss_final": losses[-1] if losses else None,
                "feature_standardization": {
                    "price_mean": round(p_mean, 2), "price_std": round(p_std, 2),
                    "distance_mean": round(d_mean, 2), "distance_std": round(d_std, 2),
                },
            }

        if __name__ == "__main__":
            print(json.dumps(solve({}), ensure_ascii=False))
    ''')

    model_ir = {
        "ir_version": "1.0",
        "model_id": "M-2017B-LOGIT",
        "model_family": {
            "primary": "statistical_modeling",
            "secondary": ["optimization", "clustering", "decision_analysis"]
        },
        "problem_binding": {
            "problem_id": "2017_B",
            "sub_questions": ["Q1", "Q2", "Q3", "Q4"],
            "focus": "Q1 任务定价规律分析 + Q2 新定价方案"
        },
        "assumptions": [
            {"assumption_id": "A1", "type": "mechanism_assumption",
             "statement": "任务完成概率服从Logistic分布，受价格、距离、会员密度影响",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A2", "type": "simplification",
             "statement": "使用合成数据模拟附件一（200个任务），特征关系已知",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A3", "type": "projection",
             "statement": "会员信誉和预订限额的影响暂归入member_density特征",
             "sub_question_binding": ["Q1"]}
        ],
        "variables": [
            {"variable_id": "v_p", "name": "定价", "symbol": "price",
             "definition": "任务的标定酬金", "unit": "元",
             "type": "input", "value_range": {"min": 5, "max": 50},
             "sub_question_binding": ["Q1", "Q2"]},
            {"variable_id": "v_d", "name": "距离", "symbol": "distance",
             "definition": "任务到最近会员的距离", "unit": "km",
             "type": "input", "value_range": {"min": 0, "max": 15},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_m", "name": "会员密度", "symbol": "density",
             "definition": "任务附近的会员数量", "unit": "人",
             "type": "input", "value_range": {"min": 1, "max": 30},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_c", "name": "完成概率", "symbol": "P_complete",
             "definition": "任务被完成的概率（Logistic模型输出）", "unit": "概率",
             "type": "output", "value_range": {"min": 0, "max": 1},
             "sub_question_binding": ["Q1", "Q2"]},
            {"variable_id": "v_popt", "name": "最优定价", "symbol": "price_opt",
             "definition": "最大化期望利润的定价", "unit": "元",
             "type": "output", "value_range": {"min": 5, "max": 50},
             "sub_question_binding": ["Q2"]},
            {"variable_id": "v_prof", "name": "期望利润", "symbol": "profit",
             "definition": "定价×完成概率的期望收益", "unit": "元",
             "type": "output", "sub_question_binding": ["Q2"]}
        ],
        "parameters": [
            {"parameter_id": "p_n", "name": "样本量", "value": 200, "unit": "个", "source": "合成数据"},
            {"parameter_id": "p_lr", "name": "学习率", "value": 0.1, "unit": "无", "source": "超参数"},
            {"parameter_id": "p_epoch", "name": "训练轮数", "value": 500, "unit": "轮", "source": "超参数"}
        ],
        "objectives": [
            {"objective_id": "OBJ1", "type": "estimate",
             "expression": "估计任务完成概率 P(complete=1|price,distance,density)",
             "variables_refs": ["v_c", "v_p", "v_d", "v_m"],
             "sub_question_binding": ["Q1"]},
            {"objective_id": "OBJ2", "type": "max",
             "expression": "maximize 期望利润 price * P_complete(price)",
             "variables_refs": ["v_popt", "v_prof", "v_c"],
             "sub_question_binding": ["Q2"]}
        ],
        "constraints": [
            {"constraint_id": "C1", "type": "range",
             "expression": "定价在[5, 50]元范围内",
             "variables_refs": ["v_p"], "source": "业务约束",
             "sub_question_binding": ["Q2"]},
            {"constraint_id": "C2", "type": "probability",
             "expression": "完成概率 P_complete ∈ [0, 1]",
             "variables_refs": ["v_c"], "source": "概率公理",
             "sub_question_binding": ["Q1"]}
        ],
        "mechanisms": [
            {"mechanism_id": "M1", "name": "Logistic回归",
             "description": "任务完成概率由Logistic函数建模：P=1/(1+exp(-(β0+β1*price+β2*distance+β3*density)))",
             "equations_refs": ["EQ1"], "sub_question_binding": ["Q1"]}
        ],
        "equations": [
            {"equation_id": "EQ1", "latex": "P(y=1|x) = \\frac{1}{1+\\exp(-(\\beta_0+\\beta_1 x_{price}+\\beta_2 x_{dist}+\\beta_3 x_{dens}))}",
             "type": "logistic", "variables_refs": ["v_c", "v_p", "v_d", "v_m"],
             "derivation_trace": "广义线性模型，连接函数为logit，假设误差服从二项分布",
             "sub_question_binding": ["Q1"]},
            {"equation_id": "EQ2", "latex": "\\pi(p) = p \\cdot P_{complete}(p), \\quad p^* = \\arg\\max_{p} \\pi(p)",
             "type": "optimization", "variables_refs": ["v_prof", "v_popt", "v_c"],
             "derivation_trace": "期望利润=定价×完成概率，在价格网格上搜索最优",
             "sub_question_binding": ["Q2"]}
        ],
        "dependencies": [],
        "solvers": [
            {"solver_id": "S1", "name": "梯度下降Logistic回归+网格搜索",
             "description": "标准化特征后梯度下降训练Logistic回归，在价格网格上搜索最优定价",
             "sub_question_binding": ["Q1", "Q2"]}
        ],
        "experiments": [
            {"experiment_id": "E1", "name": "200任务合成数据回归",
             "description": "生成200个合成任务（距离指数分布、价格线性+噪声、完成概率Logistic），训练回归模型",
             "sub_question_binding": ["Q1"]},
            {"experiment_id": "E2", "name": "定价网格搜索",
             "description": "在[5,40]元网格上计算期望利润，搜索最优定价",
             "sub_question_binding": ["Q2"]}
        ],
        "validations": [
            {"validation_id": "V1", "type": "accuracy",
             "description": "模型在训练集上的预测准确率",
             "sub_question_binding": ["Q1"]},
            {"validation_id": "V2", "type": "monotonicity",
             "description": "距离系数应为负，会员密度系数应为正",
             "sub_question_binding": ["Q1"]}
        ],
        "claims": [
            {"claim_id": "CL1", "statement": "Logistic回归可量化定价/距离/密度对任务完成率的影响",
             "evidence_refs": ["E1", "V1", "V2"], "sub_question_binding": ["Q1"]},
            {"claim_id": "CL2", "statement": "存在最优定价使期望利润最大化",
             "evidence_refs": ["E2"], "sub_question_binding": ["Q2"]}
        ],
        "model_graph": {"nodes": 4, "edges": 3, "type": "regression_chain"},
        "modeling_trace": [
            {"step": 1, "action": "data_generation", "detail": "合成200任务数据"},
            {"step": 2, "action": "model_training", "detail": "Logistic回归梯度下降"},
            {"step": 3, "action": "price_optimization", "detail": "网格搜索最优定价"}
        ]
    }

    model_doc = textwrap.dedent('''\
        # 2017_B 拍照赚钱任务定价 — 模型文档（自由文本）

        ## 1. 问题理解
        "拍照赚钱"是移动互联网下的自助式服务模式，用户领取拍照任务赚取酬金。Q1要求研究已结束项目的任务定价规律，分析未完成原因。Q2要求设计新的任务定价方案并与原方案比较。

        ## 2. 假设
        - 任务完成概率服从Logistic分布，受价格、距离、会员密度影响
        - 使用合成数据模拟附件一（200个任务），特征关系已知
        - 会员信誉和预订限额的影响暂归入member_density特征
        - 期望利润 = 定价 × 完成概率

        ## 3. 变量
        - price：任务定价（元）
        - distance：任务到最近会员的距离（km）
        - density：任务附近会员数量（人）
        - P_complete：任务被完成的概率
        - price_opt：最优定价（元）
        - profit：期望利润（元）

        ## 4. 参数
        - 样本量200，学习率0.1，训练500轮
        - 价格搜索范围[5, 40]元

        ## 5. 目标
        Q1：估计任务完成概率 P(complete=1|price,distance,density)。
        Q2：最大化期望利润 price × P_complete(price)。

        ## 6. 约束
        - 定价在[5, 50]元范围内
        - 完成概率 P_complete ∈ [0, 1]

        ## 7. 机理与方程
        Logistic回归：P(y=1|x) = 1/(1+exp(-(β0+β1*price+β2*distance+β3*density)))。
        期望利润 π(p) = p · P_complete(p)，最优定价 p* = argmax π(p)。

        ## 8. 求解方法与实验
        标准化特征后梯度下降训练Logistic回归（500轮，学习率0.1）。在价格网格[5,40]上搜索最优定价。
        实验1：200合成任务回归训练，评估准确率。
        实验2：定价网格搜索，绘制期望利润曲线。

        ## 9. 验证
        - 准确率：模型在训练集上的预测准确率
        - 单调性：距离系数应为负（越远越难完成），会员密度系数应为正
        - 收敛性：损失函数随训练轮数下降并收敛
    ''')

    validation_plan = {
        "plan_id": "VP-2017B",
        "limit_tests": [
            {"name": "零价格", "description": "price=0时完成概率应极低（无激励）",
             "expected": "P_complete < 0.1"},
            {"name": "极远任务", "description": "distance=15km时完成概率应显著降低",
             "expected": "P_complete < 距离均值时的概率"}
        ],
        "sensitivity": [
            {"parameter": "定价", "range": [5, 15, 30],
             "expected_effect": "定价增加→完成概率增加→期望利润先增后减（存在最优）"},
            {"parameter": "距离", "range": [1, 5, 10],
             "expected_effect": "距离增加→完成概率降低→最优定价可能提高"}
        ],
        "validation_targets": ["OBJ1", "OBJ2"],
        "constraint_violation_check": True,
        "residual_check": True
    }

    output_mapping = {
        "完成概率": "actual_completion_rate", "P_complete": "actual_completion_rate",
        "最优定价": "optimal_price", "price_opt": "optimal_price",
        "期望利润": "optimal_expected_profit", "profit": "optimal_expected_profit",
        "定价": "optimal_price", "price": "optimal_price",
        "距离": "feature_standardization", "distance": "feature_standardization",
        "模型准确率": "model_accuracy",
    }

    return {
        "problem_id": "2017_B", "title": "拍照赚钱的任务定价",
        "code": code, "model_ir": model_ir, "model_doc": model_doc,
        "validation_plan": validation_plan, "output_mapping": output_mapping,
        "family_primary": "statistical_modeling",
        "sub_questions": ["Q1", "Q2", "Q3", "Q4"],
    }


# ============================================================
# 2011_B — 交巡警服务平台设置与调度（图论 + Dijkstra + 分配）
# ============================================================
def problem_2011_B() -> dict:
    code = textwrap.dedent('''\
        """2011_B 交巡警服务平台 — 图论Dijkstra+最近邻分配（自包含，纯标准库）。"""
        import json
        import heapq
        import math

        def solve(inputs: dict) -> dict:
            # 构建A区简化交通网络：20个节点，模拟城区道路
            # 节点坐标（km），用于计算距离
            random_seed = 42
            # 固定的20个节点坐标（模拟A区交通网络）
            coords = [
                (0.5, 0.5), (1.5, 0.3), (2.5, 0.6), (3.5, 0.4), (4.5, 0.7),
                (0.8, 1.5), (1.8, 1.8), (2.8, 1.5), (3.8, 1.9), (4.8, 1.6),
                (0.3, 2.8), (1.3, 3.0), (2.3, 2.7), (3.3, 3.1), (4.3, 2.8),
                (1.0, 4.0), (2.0, 4.2), (3.0, 3.9), (4.0, 4.1), (4.8, 3.8),
            ]
            n_nodes = len(coords)

            # 构建邻接表：相邻节点（距离<1.5km）之间有道路
            adj = {i: [] for i in range(n_nodes)}
            edges = []
            for i in range(n_nodes):
                for j in range(i + 1, n_nodes):
                    dist = math.sqrt((coords[i][0] - coords[j][0])**2 +
                                     (coords[i][1] - coords[j][1])**2)
                    if dist < 1.5:
                        adj[i].append((j, dist))
                        adj[j].append((i, dist))
                        edges.append((i, j, round(dist, 3)))

            # 20个交巡警服务平台（设在节点0,2,4,6,8,10,12,14,16,18,1,3,5,7,9,11,13,15,17）
            platforms = list(range(20))  # 每个节点都有平台（简化）

            # Dijkstra最短路径
            def dijkstra(source):
                dist = {i: float("inf") for i in range(n_nodes)}
                dist[source] = 0
                pq = [(0, source)]
                while pq:
                    d, u = heapq.heappop(pq)
                    if d > dist[u]:
                        continue
                    for v, w in adj[u]:
                        if dist[u] + w < dist[v]:
                            dist[v] = dist[u] + w
                            heapq.heappush(pq, (dist[v], v))
                return dist

            # 从每个平台到所有节点的最短距离
            platform_distances = {}
            for p in platforms:
                platform_distances[p] = dijkstra(p)

            # 管辖范围分配：每个节点分配给最近的平台
            speed = 60.0  # km/h
            response_limit = 3.0  # 分钟
            distance_limit = speed * response_limit / 60.0  # 3km

            allocation = {}
            max_response = 0.0
            covered_count = 0
            platform_workload = {p: 0 for p in platforms}

            for node in range(n_nodes):
                best_platform = None
                best_dist = float("inf")
                for p in platforms:
                    d = platform_distances[p][node]
                    if d < best_dist:
                        best_dist = d
                        best_platform = p
                allocation[node] = {
                    "platform": best_platform,
                    "distance_km": round(best_dist, 3),
                    "response_time_min": round(best_dist / speed * 60, 2),
                    "within_3min": best_dist <= distance_limit,
                }
                platform_workload[best_platform] += 1
                if best_dist <= distance_limit:
                    covered_count += 1
                max_response = max(max_response, best_dist / speed * 60)

            coverage_rate = covered_count / n_nodes

            # 工作量不均衡度（变异系数）
            workloads = list(platform_workload.values())
            mean_wl = sum(workloads) / len(workloads)
            std_wl = (sum((w - mean_wl)**2 for w in workloads) / len(workloads))**0.5
            cv_workload = std_wl / mean_wl if mean_wl > 0 else 0

            # 13条交通要道封锁调度（Q1第二问）
            # 模拟13个出入城区路口节点
            exit_nodes = [0, 4, 9, 14, 19, 1, 6, 11, 16, 3, 8, 13, 18]
            # 贪心分配：每个平台封锁一个路口，最小化总调度距离
            available_platforms = set(platforms)
            blockade_schedule = []
            total_blockade_dist = 0.0
            for exit_node in exit_nodes:
                best_p = None
                best_d = float("inf")
                for p in available_platforms:
                    d = platform_distances[p][exit_node]
                    if d < best_d:
                        best_d = d
                        best_p = p
                if best_p is not None:
                    available_platforms.discard(best_p)
                    blockade_schedule.append({
                        "exit_node": exit_node,
                        "platform": best_p,
                        "distance_km": round(best_d, 3),
                        "arrival_min": round(best_d / speed * 60, 2),
                    })
                    total_blockade_dist += best_d

            return {
                "n_nodes": n_nodes,
                "n_edges": len(edges),
                "n_platforms": len(platforms),
                "coverage_rate_3min": round(coverage_rate, 4),
                "max_response_time_min": round(max_response, 2),
                "avg_response_time_min": round(
                    sum(a["response_time_min"] for a in allocation.values()) / n_nodes, 2),
                "workload_cv": round(cv_workload, 4),
                "platform_workload": platform_workload,
                "allocation": {str(k): v for k, v in allocation.items()},
                "blockade_n_exits": len(exit_nodes),
                "blockade_total_dist_km": round(total_blockade_dist, 3),
                "blockade_avg_arrival_min": round(
                    sum(b["arrival_min"] for b in blockade_schedule) / len(blockade_schedule), 2),
                "blockade_schedule": blockade_schedule,
                "speed_kmh": speed,
                "response_limit_min": response_limit,
                "distance_limit_km": distance_limit,
            }

        if __name__ == "__main__":
            print(json.dumps(solve({}), ensure_ascii=False))
    ''')

    model_ir = {
        "ir_version": "1.0",
        "model_id": "M-2011B-GRAPH",
        "model_family": {
            "primary": "graph_algorithm",
            "secondary": ["optimization", "decision_analysis", "simulation"]
        },
        "problem_binding": {
            "problem_id": "2011_B",
            "sub_questions": ["Q1", "Q2"],
            "focus": "Q1 管辖范围分配 + 交通要道封锁调度"
        },
        "assumptions": [
            {"assumption_id": "A1", "type": "projection",
             "statement": "A区简化为20节点交通网络，相邻节点（距离<1.5km）间有道路",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A2", "type": "mechanism_assumption",
             "statement": "警车时速60km/h，3分钟响应要求对应3km覆盖半径",
             "sub_question_binding": ["Q1"]},
            {"assumption_id": "A3", "type": "simplification",
             "statement": "每个节点均设有交巡警服务平台（20个平台），管辖分配采用最近邻原则",
             "sub_question_binding": ["Q1"]}
        ],
        "variables": [
            {"variable_id": "v_cov", "name": "3分钟覆盖率", "symbol": "coverage",
             "definition": "能在3分钟内到达的节点比例", "unit": "比例",
             "type": "output", "value_range": {"min": 0, "max": 1},
             "sub_question_binding": ["Q1"]},
            {"variable_id": "v_resp", "name": "最大响应时间", "symbol": "t_max",
             "definition": "所有节点中最远的出警时间", "unit": "分钟",
             "type": "output", "sub_question_binding": ["Q1"]},
            {"variable_id": "v_cv", "name": "工作量变异系数", "symbol": "CV",
             "definition": "各平台管辖节点数的变异系数（衡量均衡性）", "unit": "无",
             "type": "output", "sub_question_binding": ["Q1"]},
            {"variable_id": "v_alloc", "name": "管辖分配", "symbol": "allocation",
             "definition": "每个节点分配到的最近平台及距离", "unit": "无",
             "type": "output", "sub_question_binding": ["Q1"]},
            {"variable_id": "v_block", "name": "封锁调度", "symbol": "blockade",
             "definition": "13条交通要道的封锁平台分配方案", "unit": "无",
             "type": "output", "sub_question_binding": ["Q1"]}
        ],
        "parameters": [
            {"parameter_id": "p_speed", "name": "警车时速", "value": 60, "unit": "km/h", "source": "题目"},
            {"parameter_id": "p_resp", "name": "响应时间要求", "value": 3, "unit": "分钟", "source": "题目"},
            {"parameter_id": "p_nplat", "name": "平台数量", "value": 20, "unit": "个", "source": "题目"},
            {"parameter_id": "p_nexit", "name": "出入城区路口数", "value": 13, "unit": "个", "source": "题目"}
        ],
        "objectives": [
            {"objective_id": "OBJ1", "type": "min",
             "expression": "minimize 最大响应时间 t_max（管辖分配优化）",
             "variables_refs": ["v_resp", "v_alloc"],
             "sub_question_binding": ["Q1"]},
            {"objective_id": "OBJ2", "type": "min",
             "expression": "minimize 封锁调度总距离（13路口分配）",
             "variables_refs": ["v_block"],
             "sub_question_binding": ["Q1"]}
        ],
        "constraints": [
            {"constraint_id": "C1", "type": "response_time",
             "expression": "尽量3分钟内到达事发地（coverage最大化）",
             "variables_refs": ["v_cov", "v_resp"], "source": "题目",
             "sub_question_binding": ["Q1"]},
            {"constraint_id": "C2", "type": "resource",
             "expression": "一个平台最多封锁一个路口",
             "variables_refs": ["v_block"], "source": "题目",
             "sub_question_binding": ["Q1"]}
        ],
        "mechanisms": [
            {"mechanism_id": "M1", "name": "Dijkstra最短路径",
             "description": "从每个平台出发计算到所有节点的最短路径距离，用于管辖分配和封锁调度",
             "equations_refs": ["EQ1"], "sub_question_binding": ["Q1"]},
            {"mechanism_id": "M2", "name": "贪心分配",
             "description": "管辖分配用最近邻原则；封锁调度用贪心最小总距离分配",
             "equations_refs": ["EQ2"], "sub_question_binding": ["Q1"]}
        ],
        "equations": [
            {"equation_id": "EQ1", "latex": "d(p,v) = \\min_{path\\;p\\to v} \\sum_{e\\in path} w(e)",
             "type": "shortest_path", "variables_refs": ["v_alloc", "v_resp"],
             "derivation_trace": "Dijkstra算法求解单源最短路径，边权为道路距离",
             "sub_question_binding": ["Q1"]},
            {"equation_id": "EQ2", "latex": "p^*(v) = \\arg\\min_{p\\in P} d(p,v), \\quad \\forall v\\in V",
             "type": "assignment", "variables_refs": ["v_alloc", "v_cov"],
             "derivation_trace": "最近邻管辖分配：每个节点分配给距离最近的平台",
             "sub_question_binding": ["Q1"]}
        ],
        "dependencies": [],
        "solvers": [
            {"solver_id": "S1", "name": "Dijkstra+最近邻分配+贪心封锁",
             "description": "Dijkstra计算全对最短路径，最近邻分配管辖范围，贪心分配封锁路口",
             "sub_question_binding": ["Q1"]}
        ],
        "experiments": [
            {"experiment_id": "E1", "name": "A区20节点管辖分配",
             "description": "20节点交通网络，20平台，计算3分钟覆盖率和最大响应时间",
             "sub_question_binding": ["Q1"]},
            {"experiment_id": "E2", "name": "13路口封锁调度",
             "description": "贪心分配20平台到13个出入城区路口，最小化总调度距离",
             "sub_question_binding": ["Q1"]}
        ],
        "validations": [
            {"validation_id": "V1", "type": "coverage_check",
             "description": "3分钟覆盖率在[0,1]范围内，每节点有且仅有一个分配平台",
             "sub_question_binding": ["Q1"]},
            {"validation_id": "V2", "type": "blockade_feasibility",
             "description": "13个路口各分配一个不同平台，无重复分配",
             "sub_question_binding": ["Q1"]}
        ],
        "claims": [
            {"claim_id": "CL1", "statement": "Dijkstra+最近邻分配可有效划分交巡警管辖范围",
             "evidence_refs": ["E1", "V1"], "sub_question_binding": ["Q1"]},
            {"claim_id": "CL2", "statement": "贪心调度可实现13路口快速全封锁",
             "evidence_refs": ["E2", "V2"], "sub_question_binding": ["Q1"]}
        ],
        "model_graph": {"nodes": 20, "edges": 0, "type": "road_network"},
        "modeling_trace": [
            {"step": 1, "action": "graph_construction", "detail": "20节点交通网络邻接表"},
            {"step": 2, "action": "shortest_path", "detail": "Dijkstra全对最短路径"},
            {"step": 3, "action": "allocation", "detail": "最近邻管辖分配+贪心封锁"}
        ]
    }

    model_doc = textwrap.dedent('''\
        # 2011_B 交巡警服务平台设置与调度 — 模型文档（自由文本）

        ## 1. 问题理解
        某市A区设有20个交巡警服务平台，需为各平台分配管辖范围，使突发事件尽量在3分钟内有交巡警到达（警车时速60km/h）。同时需调度全区警力对13条交通要道实现快速全封锁，一个平台最多封锁一个路口。

        ## 2. 假设
        - A区简化为20节点交通网络，相邻节点（距离<1.5km）间有道路连接
        - 警车时速60km/h，3分钟响应要求对应3km覆盖半径
        - 每个节点均设有交巡警服务平台（20个平台）
        - 管辖分配采用最近邻原则，封锁调度采用贪心最小总距离

        ## 3. 变量
        - coverage：3分钟覆盖率（能在3分钟内到达的节点比例）
        - t_max：最大响应时间（分钟）
        - CV：各平台工作量变异系数
        - allocation：每个节点的管辖分配（平台+距离+响应时间）
        - blockade：13条交通要道的封锁调度方案

        ## 4. 参数
        - 警车时速60km/h，响应时间要求3分钟
        - 平台数量20个，出入城区路口13个
        - 覆盖半径3km

        ## 5. 目标
        Q1管辖分配：最小化最大响应时间，最大化3分钟覆盖率。
        Q1封锁调度：最小化13路口封锁的总调度距离。

        ## 6. 约束
        - 尽量3分钟内到达事发地
        - 一个平台最多封锁一个路口
        - 每个节点有且仅有一个管辖平台

        ## 7. 机理与方程
        Dijkstra最短路径：d(p,v) = min Σ w(e)，从每个平台到所有节点。
        最近邻分配：p*(v) = argmin_p d(p,v)。
        贪心封锁：依次为每个路口分配最近的可用平台。

        ## 8. 求解方法与实验
        Dijkstra计算全对最短路径，最近邻分配管辖范围，贪心分配封锁路口。
        实验1：A区20节点管辖分配，计算覆盖率和最大响应时间。
        实验2：13路口封锁调度，计算总距离和平均到达时间。

        ## 9. 验证
        - 覆盖检验：3分钟覆盖率在[0,1]，每节点有唯一分配平台
        - 封锁可行性：13路口各分配不同平台，无重复
        - 物理合理性：响应时间=距离/速度×60
    ''')

    validation_plan = {
        "plan_id": "VP-2011B",
        "limit_tests": [
            {"name": "单平台系统", "description": "仅1个平台时，所有节点分配给该平台，最大响应时间应较大",
             "expected": "t_max > 多平台时的t_max"},
            {"name": "全连接图", "description": "所有节点间距离相等时，所有平台到所有节点距离相同",
             "expected": "coverage=1.0, workload完全均衡"}
        ],
        "sensitivity": [
            {"parameter": "响应时间要求", "range": [2, 3, 5],
             "expected_effect": "要求放宽→覆盖率提高"},
            {"parameter": "平台数量", "range": [5, 10, 20],
             "expected_effect": "平台增加→覆盖率提高→最大响应时间降低"}
        ],
        "validation_targets": ["OBJ1", "OBJ2"],
        "constraint_violation_check": True,
        "residual_check": False
    }

    output_mapping = {
        "3分钟覆盖率": "coverage_rate_3min", "coverage": "coverage_rate_3min",
        "最大响应时间": "max_response_time_min", "t_max": "max_response_time_min",
        "工作量变异系数": "workload_cv", "CV": "workload_cv",
        "管辖分配": "allocation", "allocation": "allocation",
        "封锁调度": "blockade_schedule", "blockade": "blockade_schedule",
    }

    return {
        "problem_id": "2011_B", "title": "交巡警服务平台的设置与调度",
        "code": code, "model_ir": model_ir, "model_doc": model_doc,
        "validation_plan": validation_plan, "output_mapping": output_mapping,
        "family_primary": "graph_algorithm",
        "sub_questions": ["Q1", "Q2"],
    }


# ============================================================
# 题目注册表
# ============================================================
PROBLEMS = {
    "2020_B": problem_2020_B,
    "2018_A": problem_2018_A,
    "2019_C": problem_2019_C,
    "2018_B": problem_2018_B,
    "2017_B": problem_2017_B,
    "2011_B": problem_2011_B,
}

MAIN_PROBLEMS = ["2020_B", "2018_A", "2019_C", "2018_B", "2017_B", "2011_B"]


if __name__ == "__main__":
    for pid in MAIN_PROBLEMS:
        p = PROBLEMS[pid]()
        print(f"{pid}: {p['title']} | family={p['family_primary']} | "
              f"code_len={len(p['code'])} | ir_fields={len(p['model_ir'])} | "
              f"mapping={len(p['output_mapping'])}")
