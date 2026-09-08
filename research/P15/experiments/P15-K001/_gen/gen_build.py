# -*- coding: utf-8 -*-
"""P15-K001 2020_B 外部建模 Agent 的 model_ir 生成器（共享构建逻辑）。

每个 run 由 gen_cfg_a.py / gen_cfg_b.py 中的配置驱动，
本模块负责把配置组装成 MODEL IR v1.0 的 JSON。
仅用于生成实验产物，不修改 core/、frozen_specs/、bundle 与已登记 run。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # research/P15/experiments/P15-K001
EXP = ROOT

PROBLEM_SHA256 = "a2d0867169b94c592caafb438f608dfa12fc91c7e5df0aab5acaa5a9408ed4f2"

# ---------------------------------------------------------------- equations
def build_equations(sym: dict) -> list:
    W, F, M, P, A, D = sym["W"], sym["F"], sym["M"], sym["P"], sym["A"], sym["D"]
    Wth, V, gw, gf = sym["Wth"], sym["V"], sym["gw"], sym["gf"]
    mult, bw, bf, cw, cf = sym["mult"], sym["bw"], sym["bf"], sym["cw"], sym["cf"]
    Rev, kap, rho, Tr, k = sym["Rev"], sym["kap"], sym["rho"], sym["Tr"], sym["k"]
    M0 = sym["M0"]

    def st(p, w, f, m, t, wth):
        """状态元组串，t 为已含下标的第 t 天（如 't'）或 't+1'。"""
        return f"({p}, {w}, {f}, {m}, {t}, {wth})"

    st_t = st(f"{P}_{D}", f"{W}_{D}", f"{F}_{D}", f"{M}_{D}", D, f"{Wth}_{D}")
    st_t1 = st(f"{P}_{{{D}+1}}", f"{W}_{{{D}+1}}", f"{F}_{{{D}+1}}", f"{M}_{{{D}+1}}", f"{D}+1", f"{Wth}_{{{D}+1}}")

    return [
        {
            "equation_id": "E1",
            "latex": f"{W}_{{{D}+1}} = {W}_{D} - {mult}({A}_{D}) {bw} + {gw}",
            "type": "state_transition",
            "variables_refs": ["V3", "V7"],
            "parameters_refs": ["P3", "P9"],
            "mechanism_ref": "M1",
            "derivation_trace": f"由资源消耗倍率机理直接写出；{gw} 为当日购买并入存量的水量，非补给点当日为 0。",
            "sub_question_binding": "Q1",
        },
        {
            "equation_id": "E2",
            "latex": f"{F}_{{{D}+1}} = {F}_{D} - {mult}({A}_{D}) {bf} + {gf}",
            "type": "state_transition",
            "variables_refs": ["V4", "V7"],
            "parameters_refs": ["P4", "P9"],
            "mechanism_ref": "M1",
            "derivation_trace": f"同 E1，对食物分量写出；消耗倍率与购买项均与水量平行。",
            "sub_question_binding": "Q1",
        },
        {
            "equation_id": "E3",
            "latex": f"{M}_{{{D}+1}} = {M}_{D} - {kap}({cw} {gw} + {cf} {gf}) + {Rev} \\cdot \\mathbf{{1}}[{A}_{D} = \\mathrm{{mine}}]",
            "type": "state_transition",
            "variables_refs": ["V5", "V7"],
            "parameters_refs": ["P5", "P6", "P7", "P11"],
            "mechanism_ref": "M3",
            "derivation_trace": "支出按村庄加价系数 kap（起点购买时视为 1），挖矿当日按基础收益入账；资金为累积型状态量。",
            "sub_question_binding": "Q1",
        },
        {
            "equation_id": "E4",
            "latex": f"{V}_{D}{st_t} = \\max_{{{A}}} \\left\\{{ r({st_t}, {A}) + {V}_{{{D}+1}}{st_t1} \\right\\}}",
            "type": "recurrence",
            "variables_refs": ["V1", "V2", "V3", "V4", "V5", "V6", "V9", "V12"],
            "mechanism_ref": "M2",
            "derivation_trace": "Bellman 方程：由最优子结构与无后效性导出；状态必须完整包含位置/两类资源/资金/天数/天气，否则无后效性不成立；r 为当日即时收益。",
            "sub_question_binding": "Q1",
        },
        {
            "equation_id": "E5",
            "latex": f"{V}_{D}{st_t} = {M}_{D} + {rho}({cw} {W}_{D} + {cf} {F}_{D}) \\; \\mathrm{{if}}\\; {P}_{D} = {P}_{{end}}; \\quad {V}_{D}{st_t} = -\\infty \\; \\mathrm{{otherwise}}",
            "type": "terminal_condition",
            "variables_refs": ["V2", "V3", "V4", "V5"],
            "parameters_refs": ["P12"],
            "mechanism_ref": "M2",
            "derivation_trace": "终端条件：到达终点按半价退回剩余资源；未到达记为不可行（-∞），把『到达终点』作为硬约束放在终端而非目标中。",
            "sub_question_binding": "Q1",
        },
        {
            "equation_id": "E6",
            "latex": f"{V}_{D}({P}_{{start}}, {W}_0, {F}_0, {M0} - {cw} {W}_0 - {cf} {F}_0, 0, {Wth}_0) = \\mathrm{{opt}}",
            "type": "initial_condition",
            "variables_refs": ["V1", "V2", "V3", "V4", "V5"],
            "parameters_refs": ["P5", "P6", "P8"],
            "mechanism_ref": "M2",
            "derivation_trace": "初始条件：第 0 天在起点以基准价格完成首次采购，采购量 (W_0, F_0) 本身也是决策变量，在最外层枚举。",
            "sub_question_binding": "Q1",
        },
        {
            "equation_id": "E7",
            "latex": f"{V}_{D}{st_t} = \\max_{{{A}}} \\sum_{{\\omega'}} {Tr}(\\omega'|{Wth}_{D}) \\left\\{{ r({st_t}, {A}) + {V}_{{{D}+1}}{st_t1} \\right\\}}",
            "type": "recurrence",
            "variables_refs": ["V6", "V9", "V12"],
            "parameters_refs": ["P10"],
            "mechanism_ref": "M4",
            "derivation_trace": "Q2 的随机动态规划形式：对明日天气取期望；天气取晴朗/高温/沙暴三种取值，转移由一阶马尔可夫链给出。",
            "sub_question_binding": "Q2",
        },
        {
            "equation_id": "E8",
            "latex": f"{mult}_{{\\mathrm{{multi}}}}(k) = 2k, \\quad {Rev}_{{\\mathrm{{multi}}}}(k) = {Rev}/k, \\quad {kap}_{{\\mathrm{{multi}}}}(k) = 4",
            "type": "coupling",
            "variables_refs": ["V8"],
            "parameters_refs": ["P7", "P11"],
            "mechanism_ref": "M5",
            "derivation_trace": "Q3 的同行耦合规则：把单人参数替换为同行人数 k 的函数，再对每个玩家求最优反应并迭代至不动点。",
            "sub_question_binding": "Q3",
        },
    ]


# ---------------------------------------------------------------- variables
def build_variables(sym: dict) -> list:
    L, W, F, D = sym["L"], sym["W"], sym["F"], sym["D"]
    return [
        {"variable_id": "V1", "name": "天数", "symbol": sym["D"],
         "definition": "阶段计数，第 0 天位于起点", "unit": "天", "type": "index",
         "value_range": f"[0, {sym['T']}]", "sub_question_binding": "Q1"},
        {"variable_id": "V2", "name": "所在区域", "symbol": sym["P"],
         "definition": "玩家当日所处地图区域编号", "unit": "区域编号", "type": "state",
         "value_range": f"地图节点集 {sym['P']}", "sub_question_binding": "Q1"},
        {"variable_id": "V3", "name": "剩余水量", "symbol": W,
         "definition": "当日全部消耗与购买完成后的剩余水", "unit": "箱", "type": "state",
         "value_range": f"[0, {L}]", "sub_question_binding": "Q1"},
        {"variable_id": "V4", "name": "剩余食物量", "symbol": F,
         "definition": "当日全部消耗与购买完成后的剩余食物", "unit": "箱", "type": "state",
         "value_range": f"[0, {L}]", "sub_question_binding": "Q1"},
        {"variable_id": "V5", "name": "剩余资金", "symbol": sym["M"],
         "definition": "当日全部收支完成后的剩余资金", "unit": "元", "type": "state",
         "sub_question_binding": "Q1"},
        {"variable_id": "V6", "name": "天气状态", "symbol": sym["Wth"],
         "definition": "当日天气，取晴朗/高温/沙暴", "unit": "枚举", "type": "state",
         "value_range": "{clear, hot, sandstorm}", "sub_question_binding": "Q1"},
        {"variable_id": "V7", "name": "当日行动", "symbol": sym["A"],
         "definition": "决策变量：停留/移动至某相邻区域/挖矿/购买", "unit": "枚举", "type": "decision",
         "sub_question_binding": "Q1"},
        {"variable_id": "V8", "name": "当日同行人数", "symbol": sym["k"],
         "definition": "Q3 中执行同一行动的玩家数", "unit": "人", "type": "state",
         "value_range": "[1, n]", "sub_question_binding": "Q3"},
        {"variable_id": "V9", "name": "价值函数", "symbol": sym["V"],
         "definition": f"从第 {D} 天状态 s 出发到终点可获得的资金上界", "unit": "元", "type": "derived",
         "sub_question_binding": "Q1"},
        {"variable_id": "V10", "name": "当日购水量", "symbol": sym["gw"],
         "definition": "当日购买并计入存量的水量，起点/村庄按不同价格", "unit": "箱", "type": "decision",
         "value_range": f"[0, {L} - {W}_{D} - {F}_{D}]", "sub_question_binding": "Q1"},
        {"variable_id": "V11", "name": "当日购食物量", "symbol": sym["gf"],
         "definition": "当日购买并计入存量的食物量，起点/村庄按不同价格", "unit": "箱", "type": "decision",
         "value_range": f"[0, {L} - {W}_{D} - {F}_{D}]", "sub_question_binding": "Q1"},
        {"variable_id": "V12", "name": "当日即时收益", "symbol": "r",
         "definition": "第 D 天采取行动 a 后当期的净资金变化（含购买支出与挖矿收益）", "unit": "元", "type": "derived",
         "sub_question_binding": "Q1"},
    ]


# ---------------------------------------------------------------- parameters
def build_parameters(sym: dict) -> list:
    return [
        {"parameter_id": "P1", "name": "截止天数", "symbol": sym["T"],
         "definition": "必须到达终点的最后期限", "unit": "天", "value": "关卡附件给定",
         "source": "题面附件", "sub_question_binding": "Q1"},
        {"parameter_id": "P2", "name": "负重上限", "symbol": sym["L"],
         "definition": "水与食物箱数之和的上限", "unit": "箱", "value": "关卡附件给定",
         "source": "题面规则(2)", "sub_question_binding": "Q1"},
        {"parameter_id": "P3", "name": "水的基础消耗量", "symbol": sym["bw"],
         "definition": "原地停留一天消耗的水", "unit": "箱/天", "value": "关卡附件给定",
         "source": "题面规则(5)", "sub_question_binding": "Q1"},
        {"parameter_id": "P4", "name": "食物的基础消耗量", "symbol": sym["bf"],
         "definition": "原地停留一天消耗的食物", "unit": "箱/天", "value": "关卡附件给定",
         "source": "题面规则(5)", "sub_question_binding": "Q1"},
        {"parameter_id": "P5", "name": "水的基准价格", "symbol": sym["cw"],
         "definition": "起点购买水的单价", "unit": "元/箱", "value": "关卡附件给定",
         "source": "题面规则(6)", "sub_question_binding": "Q1"},
        {"parameter_id": "P6", "name": "食物的基准价格", "symbol": sym["cf"],
         "definition": "起点购买食物的单价", "unit": "元/箱", "value": "关卡附件给定",
         "source": "题面规则(6)", "sub_question_binding": "Q1"},
        {"parameter_id": "P7", "name": "基础收益", "symbol": sym["Rev"],
         "definition": "单人挖矿一天获得的资金", "unit": "元/天", "value": "关卡附件给定",
         "source": "题面规则(7)", "sub_question_binding": "Q1"},
        {"parameter_id": "P8", "name": "初始资金", "symbol": sym["M0"],
         "definition": "第 0 天可用资金", "unit": "元", "value": "关卡附件给定",
         "source": "题面规则(6)", "sub_question_binding": "Q1"},
        {"parameter_id": "P9", "name": "消耗倍率", "symbol": sym["mult"],
         "definition": "停留=1，行走=2，挖矿=3", "unit": "无量纲", "value": "{1,2,3}",
         "source": "题面规则(5)(7)", "sub_question_binding": "Q1"},
        {"parameter_id": "P10", "name": "天气转移概率", "symbol": sym["Tr"],
         "definition": "Q2 中天气的一阶转移矩阵", "unit": "概率", "value": "待由附件/假设标定",
         "source": "假设 A3", "sub_question_binding": "Q2"},
        {"parameter_id": "P11", "name": "村庄加价系数", "symbol": sym["kap"],
         "definition": "村庄购买价格相对基准价格的倍数", "unit": "无量纲", "value": "2",
         "source": "题面规则(8)", "sub_question_binding": "Q1"},
        {"parameter_id": "P12", "name": "终点退回系数", "symbol": sym["rho"],
         "definition": "终点退回价格相对基准价格的比例", "unit": "无量纲", "value": "0.5",
         "source": "题面规则(6)", "sub_question_binding": "Q1"},
    ]


# ---------------------------------------------------------------- constraints
def build_constraints(sym: dict) -> list:
    W, F, P, A, Wth, D = sym["W"], sym["F"], sym["P"], sym["A"], sym["Wth"], sym["D"]
    return [
        {"constraint_id": "C1", "type": "inequality",
         "expression": f"{W}_{D} + {F}_{D} <= {sym['L']}",
         "variables_refs": ["V3", "V4"], "source": "题面规则(2) 负重上限",
         "description": "每日水与食物箱数之和不超过负重上限（上界约束，方向为 ≤）",
         "sub_question_binding": "Q1"},
        {"constraint_id": "C2", "type": "inequality",
         "expression": f"{W}_{D} >= 0,  {F}_{D} >= 0",
         "variables_refs": ["V3", "V4"], "source": "题面规则(2) 资源耗尽即失败",
         "description": "生存约束：资源非负是硬约束，不进入目标函数做权衡（下界约束，方向为 ≥）",
         "sub_question_binding": "Q1"},
        {"constraint_id": "C3", "type": "inequality",
         "expression": f"tau <= {sym['T']}",
         "variables_refs": ["V1"], "source": "题面规则(1) 截止日期",
         "description": "到达终点的时刻不超过截止天数",
         "sub_question_binding": "Q1"},
        {"constraint_id": "C4", "type": "equality",
         "expression": f"{A}_{D} = stay  if {Wth}_{D} = sandstorm",
         "variables_refs": ["V6", "V7"], "source": "题面规则(4) 沙暴日必须停留",
         "description": "沙暴日行动被强制为原地停留（挖矿仍可进行，见规则(7)）",
         "sub_question_binding": "Q1"},
        {"constraint_id": "C5", "type": "inequality",
         "expression": f"{P}_{{{D}+1}} in Adj({P}_{D}) union {{ {P}_{D} }}",
         "variables_refs": ["V2"], "source": "题面规则(4) 与注1（公共边界才算相邻）",
         "description": "每日仅可移动到有公共边界的相邻区域或原地停留",
         "sub_question_binding": "Q1"},
        {"constraint_id": "C6", "type": "inequality",
         "expression": "purchase_at_start_allowed only when D = 0",
         "variables_refs": ["V1", "V2"], "source": "题面规则(6) 起点不可重复购买",
         "description": "基准价格购买仅限第 0 天在起点；村庄价格购买不受此限",
         "sub_question_binding": "Q1"},
        {"constraint_id": "C7", "type": "inequality",
         "expression": f"mine_allowed on day {D} only if {P}_{{{D}-1}} = mine and {P}_{D} = mine",
         "variables_refs": ["V2", "V7"], "source": "题面规则(7) 到达矿山当天不能挖矿",
         "description": "到达矿山当日不可挖矿，须在矿山停留满一天后才可挖矿",
         "sub_question_binding": "Q1"},
    ]


def build_objectives(sym: dict) -> list:
    M, W, F = sym["M"], sym["W"], sym["F"]
    return [
        {"objective_id": "O1", "type": "maximize",
         "expression": f"J = {M}_T + {sym['rho']} * ({sym['cw']} * {W}_T + {sym['cf']} * {F}_T)",
         "variables_refs": ["V3", "V4", "V5"],
         "description": "最大化到达终点时的剩余资金（含按半价退回的剩余资源折算）",
         "sub_question_binding": "Q1", "clarity_score": 3},
        {"objective_id": "O2", "type": "maximize",
         "expression": f"J = E[ {M}_tau + {sym['rho']} * ({sym['cw']} * {W}_tau + {sym['cf']} * {F}_tau) ]",
         "variables_refs": ["V3", "V4", "V5", "V6"],
         "description": "Q2 天气随机时最大化期望终局资金；tau 为到达终点的停时",
         "sub_question_binding": "Q2", "clarity_score": 3},
    ]


def build_graph(all_ids: dict) -> dict:
    nodes = [
        {"id": "problem", "type": "problem", "label": "2020_B Q1-Q3"},
        {"id": "assumptions", "type": "group", "label": all_ids["assumptions"]},
        {"id": "variables", "type": "group", "label": all_ids["variables"]},
        {"id": "parameters", "type": "group", "label": all_ids["parameters"]},
    ]
    for mid, label in all_ids["mechanisms"].items():
        nodes.append({"id": mid, "type": "mechanism", "label": label})
    for eid, label in all_ids["equations"].items():
        nodes.append({"id": eid, "type": "equation", "label": label})
    for cid, label in all_ids["constraints"].items():
        nodes.append({"id": cid, "type": "constraint", "label": label})
    for oid, label in all_ids["objectives"].items():
        nodes.append({"id": oid, "type": "objective", "label": label})
    for sid, label in all_ids["solvers"].items():
        nodes.append({"id": sid, "type": "solver", "label": label})

    edges = [
        {"from": "problem", "to": "assumptions", "relation": "yields"},
        {"from": "assumptions", "to": "variables", "relation": "defines"},
        {"from": "assumptions", "to": "parameters", "relation": "defines"},
    ]
    mech_eq = [("M1", "E1"), ("M1", "E2"), ("M3", "E3"), ("M2", "E4"),
               ("M2", "E5"), ("M2", "E6"), ("M4", "E7"), ("M5", "E8")]
    for m, e in mech_eq:
        if m in all_ids["mechanisms"] and e in all_ids["equations"]:
            edges.append({"from": m, "to": e, "relation": "derives"})
    for c, e in [("C1", "E1"), ("C2", "E1"), ("C4", "E4")]:
        if c in all_ids["constraints"] and e in all_ids["equations"]:
            edges.append({"from": c, "to": e, "relation": "restricts"})
    if "E4" in all_ids["equations"] and "O1" in all_ids["objectives"]:
        edges.append({"from": "E4", "to": "O1", "relation": "supports"})
    if "E7" in all_ids["equations"] and "O2" in all_ids["objectives"]:
        edges.append({"from": "E7", "to": "O2", "relation": "supports"})
    for e, s in [("E4", "S1"), ("E7", "S2"), ("E8", "S3")]:
        if e in all_ids["equations"] and s in all_ids["solvers"]:
            edges.append({"from": e, "to": s, "relation": "solved_by"})
    return {"graph_version": "1.0", "nodes": nodes, "edges": edges}


def build_ir(cfg: dict) -> dict:
    sym = cfg["sym"]
    assumptions = cfg["assumptions"]
    variables = build_variables(sym) + cfg.get("extra_variables", [])
    parameters = build_parameters(sym) + cfg.get("extra_parameters", [])
    objectives = build_objectives(sym)
    constraints = build_constraints(sym)
    mechanisms = cfg["mechanisms"]
    equations = build_equations(sym) + cfg.get("extra_equations", [])
    dependencies = cfg["dependencies"]
    solvers = cfg["solvers"]
    experiments = cfg["experiments"]
    validations = cfg["validations"]
    claims = cfg["claims"]

    mech_labels = {m["mechanism_id"]: m["name"] for m in mechanisms}
    eq_labels = {e["equation_id"]: e["type"] for e in equations}
    c_labels = {c["constraint_id"]: c["description"][:6] for c in constraints}
    o_labels = {o["objective_id"]: ("最大化终局资金" if "O1" in o["objective_id"] else "最大化期望终局资金") for o in objectives}
    s_labels = {s["solver_id"]: s["name"] for s in solvers}
    all_ids = {
        "assumptions": ",".join(a["assumption_id"] for a in assumptions),
        "variables": ",".join(v["variable_id"] for v in variables),
        "parameters": ",".join(p["parameter_id"] for p in parameters),
        "mechanisms": mech_labels, "equations": eq_labels,
        "constraints": c_labels, "objectives": o_labels, "solvers": s_labels,
    }

    ir = {
        "ir_version": "1.0",
        "model_id": cfg["model_id"],
        "model_family": {
            "primary": cfg["primary"],
            "secondary": cfg["secondary"],
            "description": cfg["desc"],
        },
        "problem_binding": {
            "problem_id": "2020_B",
            "sub_question_id": "Q1",
            "problem_sha256": PROBLEM_SHA256,
            "problem_card_ref": "research/P15/benchmark/problem_cards/2020_B/card.yaml",
            "competition_format": "CUMCM",
        },
        "assumptions": assumptions,
        "variables": variables,
        "parameters": parameters,
        "objectives": objectives,
        "constraints": constraints,
        "mechanisms": mechanisms,
        "equations": equations,
        "dependencies": dependencies,
        "solvers": solvers,
        "experiments": experiments,
        "validations": validations,
        "claims": claims,
        "model_graph": build_graph(all_ids),
        "modeling_trace": {
            "trace_version": "1.0",
            "generated_at": cfg["generated_at"],
            "agent_identity": "doubao",
            "input_sha256": PROBLEM_SHA256,
            "node_events": cfg["trace_events"],
            "generation_order": [
                "assumptions", "variables", "parameters", "constraints",
                "mechanisms", "equations", "objectives", "solvers",
                "validations", "claims",
            ],
        },
    }
    return ir


def write_run(cfg: dict) -> None:
    ir = build_ir(cfg)
    run_dir = EXP / "runs" / cfg["sid"]
    out = run_dir / "model_ir.json"
    out.write_text(json.dumps(ir, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[GEN] {cfg['sid']} -> {out}  ({len(json.dumps(ir, ensure_ascii=False))} bytes)")


def main() -> None:
    from gen_cfg_a import RUNS_A
    from gen_cfg_b import RUNS_B
    for cfg in RUNS_A + RUNS_B:
        write_run(cfg)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
