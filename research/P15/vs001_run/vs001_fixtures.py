# -*- coding: utf-8 -*-
"""P1-VS-001 演示/测试 fixture：外部 Model Constructor 手写产出。

核心铁律（LLM-free）：core runtime 内不调用任何 LLM。MODEL_IR（M1/M2）与
Code（C1/C2）由外部 Model Constructor 在此手写产出（JSON + Python 代码字符串），
core runtime 只负责登记/校验/执行/保真/验证/谱系/replay。

选题：2024_A（板凳龙闹元宵）Q1 正向运动学仿真（research/P15/benchmark/problem_cards/2024_A/）。

故意失败设计（M1）：
    C002 相邻把手间距约束的系数写错——孔心距只减了一次 d_offset：
        ell_{i>1} = L_body − d_offset = 2.20 − 0.275 = 1.925（错误）
    正确值应为 ell_{i>1} = L_body − 2·d_offset = 2.20 − 0.55 = 1.65。
    M1 执行后输出真实数值（相邻把手实测间距 ≈1.925），Validation 基于真实数值
    判 mathematical_valid=False（constraint_violation_max ≈ 0.275 > 0）。
M2 修正 C002 系数与参数（ell_body=1.65）→ RUN2 全部数值检查通过 → PASS。
M1 的错误是数学/数值层面的（约束系数+参数值），不是语法错误。

固定 ABI：code 必须包含 `def solve(inputs) -> outputs`；
执行约定：input.json → run_model.py → output.json（stdout 末块 JSON = outputs）。
"""

from __future__ import annotations

# ---------------------------------------------------------------- 基础节（M1/M2 共用）

_BASE = {
    "ir_version": "1.0",
    "model_family": {
        "primary": "multibody_dynamics",
        "secondary": ["differential_geometry", "kinematic"],
        "description": "多体刚体链递推 + 阿基米德螺线参数化（2024_A Q1 正向运动学）",
    },
    "problem_binding": {
        "problem_id": "2024_A",
        "sub_question_id": "Q1",
        "problem_card_ref": "research/P15/benchmark/problem_cards/2024_A/card.yaml",
        "competition_format": "cumcm",
        "problem_sha256": "c" * 64,
    },
    "assumptions": [
        {"assumption_id": "A001", "text": "每节板凳视为刚体，不发生弯曲变形",
         "source": "reasonable_simplification", "confidence": 0.95,
         "sub_question_binding": ["Q1"]},
        {"assumption_id": "A002", "text": "相邻板凳通过把手铰接，相邻把手间距守恒",
         "source": "problem_explicit", "confidence": 0.99,
         "sub_question_binding": ["Q1"]},
        {"assumption_id": "A003", "text": "龙头前把手沿螺线匀速运动，速度恒为 1 m/s",
         "source": "problem_explicit", "confidence": 0.99,
         "sub_question_binding": ["Q1"]},
    ],
    "variables": [
        {"variable_id": "V001", "name": "x_i", "symbol": "x_i(t)",
         "definition": "第 i 个把手中心 x 坐标（i=1..224，1=龙头前把手，224=龙尾后把手）",
         "unit": "m", "type": "state",
         "value_range": {"min": -15.0, "max": 15.0}, "sub_question_binding": ["Q1"]},
        {"variable_id": "V002", "name": "y_i", "symbol": "y_i(t)",
         "definition": "第 i 个把手中心 y 坐标", "unit": "m", "type": "state",
         "value_range": {"min": -15.0, "max": 15.0}, "sub_question_binding": ["Q1"]},
        {"variable_id": "V003", "name": "theta", "symbol": "theta(t)",
         "definition": "龙头前把手在螺线上的极角（从 A 点起算，顺时针为正）",
         "unit": "rad", "type": "state",
         "value_range": {"min": 0.0, "max": 200.0}, "sub_question_binding": ["Q1"]},
        {"variable_id": "V004", "name": "R_spiral", "symbol": "R(theta)",
         "definition": "螺线半径作为极角的函数", "unit": "m", "type": "derived",
         "value_range": {"min": 0.0, "max": 15.0}, "sub_question_binding": ["Q1"]},
        {"variable_id": "V005", "name": "v_i", "symbol": "v_i(t)",
         "definition": "第 i 个把手的速率", "unit": "m/s", "type": "derived",
         "value_range": {"min": 0.0, "max": 5.0}, "sub_question_binding": ["Q1"]},
    ],
    "parameters": [
        {"parameter_id": "PARM001", "name": "R_A", "symbol": "R_A",
         "definition": "初始龙头前把手（第16圈 A 点）螺线半径", "unit": "m",
         "value": 8.8, "source": "derived", "sub_question_binding": ["Q1"]},
        {"parameter_id": "PARM002", "name": "p", "symbol": "p",
         "definition": "盘入螺距", "unit": "m",
         "value": 0.55, "source": "problem_given", "sub_question_binding": ["Q1"]},
        {"parameter_id": "PARM003", "name": "v0", "symbol": "v0",
         "definition": "龙头前把手行进速度", "unit": "m/s",
         "value": 1.0, "source": "problem_given", "sub_question_binding": ["Q1"]},
        {"parameter_id": "PARM004", "name": "N", "symbol": "N",
         "definition": "把手总数（龙头前把手 + 各节连接点 + 龙尾后把手）", "unit": "个",
         "value": 224, "source": "derived", "sub_question_binding": ["Q1"]},
        {"parameter_id": "PARM005", "name": "ell_head", "symbol": "ell_head",
         "definition": "龙头前后把手间距 L_head − 2·d_offset = 3.41 − 0.55", "unit": "m",
         "value": 2.86, "source": "derived", "sub_question_binding": ["Q1"]},
    ],
    "objectives": [
        {"objective_id": "O001", "type": "simulate",
         "expression": "求解 {x_i(t), y_i(t), v_i(t)}_{i=1}^{224}, t in {0,60,120,180,240,300}s",
         "variables_refs": ["V001", "V002", "V005"],
         "sub_question_binding": ["Q1"],
         "description": "Q1: 正向仿真板凳龙各把手位置和速度"},
    ],
    "mechanisms": [
        {"mechanism_id": "MECH001", "name": "阿基米德螺线参数化",
         "description": "龙头前把手沿等距螺线运动，半径随极角线性变化",
         "type": "geometric", "governing_principle": "R(theta) = R_A − b·theta",
         "variables_refs": ["V003", "V004"], "assumptions_refs": ["A003"],
         "sub_question_binding": ["Q1"]},
        {"mechanism_id": "MECH002", "name": "全把手螺线弦距递推",
         "description": "所有把手中心均位于螺线上，相邻把手弦距守恒（刚体铰接）",
         "type": "physical",
         "governing_principle": "r_{i+1} 为螺线上与 r_i 弦距恰为 ell_i 的点（体侧外扩）",
         "variables_refs": ["V001", "V002"], "assumptions_refs": ["A001", "A002"],
         "sub_question_binding": ["Q1"]},
    ],
    "equations": [
        {"equation_id": "E001", "latex": "R(\\theta) = R_A - b\\theta, b = p/(2\\pi)",
         "type": "constitutive", "variables_refs": ["V003", "V004"],
         "parameters_refs": ["PARM001", "PARM002"],
         "mechanism_ref": "MECH001", "sub_question_binding": ["Q1"]},
        {"equation_id": "E002", "latex": "d\\theta/dt = v0 / \\sqrt{R(\\theta)^2 + b^2}",
         "type": "derived", "variables_refs": ["V003"],
         "parameters_refs": ["PARM003", "PARM002"],
         "mechanism_ref": "MECH001", "sub_question_binding": ["Q1"]},
        {"equation_id": "E003",
         "latex": "r_{i+1} \\in \\{r : |r - r_i| = ell_i\\} \\cap spiral,\\ "
                  "r_{i+1} = r(\\theta_i - \\Delta_i),\\ "
                  "|r(\\theta_i) - r(\\theta_i - \\Delta_i)| = ell_i",
         "type": "balance", "variables_refs": ["V001", "V002"],
         "parameters_refs": ["PARM004"],
         "mechanism_ref": "MECH002", "sub_question_binding": ["Q1"]},
    ],
    "dependencies": [
        {"dependency_id": "DEP001", "from_type": "parameter", "from_id": "PARM002",
         "to_type": "equation", "to_id": "E001", "relation": "uses",
         "sub_question_binding": ["Q1"]},
        {"dependency_id": "DEP002", "from_type": "equation", "from_id": "E001",
         "to_type": "equation", "to_id": "E002", "relation": "feeds",
         "sub_question_binding": ["Q1"]},
    ],
    "solvers": [
        {"solver_id": "S001", "name": "刚体链递推数值仿真器", "type": "simulation",
         "method": "Euler 积分（dt=0.01）求解 theta(t) + 刚体链几何递推",
         "parameters": {"dt": 0.01, "output_interval": 1.0},
         "implementation_ref": "CODE001",
         "equations_refs": ["E001", "E002", "E003"],
         "sub_question_binding": ["Q1"]},
    ],
    "experiments": [
        {"experiment_id": "EXP001", "method": "Q1 正向运动学仿真：0/60/120/180/240/300s 输出 224 个把手位置与速度",
         "parameters": {"times": [0, 60, 120, 180, 240, 300],
                        "sections_to_report": [1, 2, 52, 102, 152, 202, 224]},
         "inputs_refs": ["V001", "V002", "V003"],
         "run_metadata": {"seed": 42, "repetitions": 1, "exit_code": 0},
         "solver_ref": "S001", "sub_question_binding": ["Q1"]},
    ],
    "validations": [
        {"validation_id": "VAL001", "type": "constraint",
         "method": "相邻把手实测间距 vs C002 声明间距的绝对偏差最大值",
         "results": {"max_relative_error": 1e-7, "threshold": 1e-6},
         "pass_fail": "pending", "evidence_refs": ["EXP001"],
         "targets_refs": ["C002", "E003"], "sub_question_binding": ["Q1"]},
    ],
    "claims": [
        {"claim_id": "CL001",
         "text": "各把手位置由龙头前把手螺线位置和各节板长经刚体链递推唯一确定",
         "type": "interpretation", "evidence_refs": ["EXP001"],
         "model_refs": ["E003", "MECH002"], "sub_question_binding": ["Q1"],
         "status": "pending"},
    ],
    "model_graph": {
        "graph_version": "1.0",
        "nodes": [
            {"node_id": "P001", "node_type": "problem", "label": "2024_A 板凳龙闹元宵"},
            {"node_id": "E001", "node_type": "equation", "label": "螺线参数方程"},
            {"node_id": "C002", "node_type": "constraint", "label": "间距守恒约束"},
        ],
        "edges": [],
    },
    "modeling_trace": {
        "trace_version": "1.0",
        "generated_at": "2026-09-09T00:00:00Z",
        "agent_identity": "external_model_constructor",
        "model_version": "N/A",
        "generation_order": [],
        "version_history": [],
    },
}


def _constraints_m1():
    """M1：C002 系数写错——孔心距只减一次 d_offset（ell=2.20−0.275=1.925）。"""
    return [
        {"constraint_id": "C001", "type": "equality",
         "expression": "R(theta) = R_A − b·theta（顺时针盘入，半径递减）",
         "variables_refs": ["V003", "V004"],
         "parameters_refs": ["PARM001", "PARM002"],
         "source": "geometric", "sub_question_binding": ["Q1"]},
        {"constraint_id": "C002", "type": "equality",
         "expression": "|r_{i+1} − r_i| = ell_i；ell_1 = L_head − 2d_offset；"
                       "ell_{i>1} = L_body − d_offset（错误：只减一次）",
         "variables_refs": ["V001", "V002"],
         "parameters_refs": ["PARM005"],
         "source": "physical_law", "sub_question_binding": ["Q1"],
         "note": "M1 故意错误：体板孔心距应为 L_body − 2d_offset = 1.65，此处误为 1.925"},
        {"constraint_id": "C003", "type": "equality",
         "expression": "|dot r_1(t)| = v0 = 1.0 m/s",
         "variables_refs": ["V005"], "parameters_refs": ["PARM003"],
         "source": "problem", "sub_question_binding": ["Q1"]},
    ]


def _constraints_m2():
    """M2：修正 C002 系数（ell_{i>1} = L_body − 2d_offset = 1.65）。"""
    return [
        {"constraint_id": "C001", "type": "equality",
         "expression": "R(theta) = R_A − b·theta（顺时针盘入，半径递减）",
         "variables_refs": ["V003", "V004"],
         "parameters_refs": ["PARM001", "PARM002"],
         "source": "geometric", "sub_question_binding": ["Q1"]},
        {"constraint_id": "C002", "type": "equality",
         "expression": "|r_{i+1} − r_i| = ell_i；ell_1 = L_head − 2d_offset = 2.86；"
                       "ell_{i>1} = L_body − 2d_offset = 1.65",
         "variables_refs": ["V001", "V002"],
         "parameters_refs": ["PARM005"],
         "source": "physical_law", "sub_question_binding": ["Q1"],
         "note": "M2 修正：体板孔心距 = L_body − 2·d_offset = 2.20 − 0.55 = 1.65"},
        {"constraint_id": "C003", "type": "equality",
         "expression": "|dot r_1(t)| = v0 = 1.0 m/s",
         "variables_refs": ["V005"], "parameters_refs": ["PARM003"],
         "source": "problem", "sub_question_binding": ["Q1"]},
    ]


def _m1_dict() -> dict:
    d = dict(_BASE)
    d["model_id"] = "M2024A-Q1-v1"
    d["constraints"] = _constraints_m1()
    d["parameters"] = list(_BASE["parameters"]) + [
        {"parameter_id": "PARM006", "name": "ell_body", "symbol": "ell_body",
         "definition": "龙身/龙尾相邻把手间距（M1 错误值：L_body − d_offset）",
         "unit": "m", "value": 1.925, "source": "derived",
         "sub_question_binding": ["Q1"]}]
    return d


def _m2_dict() -> dict:
    d = dict(_BASE)
    d["model_id"] = "M2024A-Q1-v2"
    d["constraints"] = _constraints_m2()
    d["parameters"] = list(_BASE["parameters"]) + [
        {"parameter_id": "PARM006", "name": "ell_body", "symbol": "ell_body",
         "definition": "龙身/龙尾相邻把手间距（M2 正确值：L_body − 2·d_offset）",
         "unit": "m", "value": 1.65, "source": "derived",
         "sub_question_binding": ["Q1"]}]
    # FIX-3.1（audit P1-03/P1-09）：M2 是 revision 后的新模型，其 solver 的
    # implementation_ref 必须指向 M2 自己的实现（C2_CODE → CODE002），
    # 而不是继承 M1 的 CODE001——MIR→Code 映射必须随 revision 更新。
    d["solvers"] = [dict(s, implementation_ref="CODE002")
                    for s in d.get("solvers") or []]
    return d


M1_DICT = _m1_dict()
M2_DICT = _m2_dict()

# MODEL_IR 契约 v1.0（2026-09-10）：全部 fixture 产物迁移到
# src/modeling_harness/schemas/v3/model/model_ir.schema.json（唯一真源）规范。
# 迁移是数据适配（词表/minItems/model_graph 结构化），语义不变；
# 迁移后必须通过 jsonschema 全量校验（tests 断言）。
from mir_compat import migrate_model_ir  # noqa: E402

M1_DICT = migrate_model_ir(M1_DICT)
M2_DICT = migrate_model_ir(M2_DICT)
M1_DICT["model_id"] = "M2024A-Q1-v1"
M2_DICT["model_id"] = "M2024A-Q1-v2"


# ---------------------------------------------------------------- 可执行代码（固定 ABI）

def _code(version: str) -> str:
    return f'''# -*- coding: utf-8 -*-
"""2024_A Q1 可执行模型：阿基米德螺线龙头 + 全把手螺线弦距递推（固定 ABI）。

{version}
几何（题面）：所有把手中心均位于等距螺线上（E001 R(theta)=R_A−b·theta）；
相邻把手弦距守恒（C002：ell_1=2.86，ell_{{i>1}}=ell_body）。
输入（input.json）：R_A / p / v0 / N / ell_head / ell_body / times
输出：positions / head_speeds / head_theta / pair_distances / diagnostics
"""
import json
import math


def _solve_theta(R_A, p, v0, T, dt):
    """Euler 积分 E002：dθ/dt = v0 / sqrt(R(theta)^2 + b^2)，theta(0)=0。"""
    b = p / (2.0 * math.pi)
    theta = 0.0
    steps = int(round(T / dt))
    for _ in range(steps):
        R = R_A - b * theta
        if R <= 0:
            break
        theta += v0 / math.sqrt(R * R + b * b) * dt
    return theta


def _spiral_point(R_A, b, theta):
    R = R_A - b * theta
    return (R * math.cos(theta), R * math.sin(theta))


def _place_next(R_A, b, th_cur, ell, iters=80):
    """螺线上与 th_cur 弦距恰为 ell 的下一个把手（沿 θ 递减方向 = 体侧外扩）。

    二分求解 |r(theta_cur) − r(theta_cur − Δ)| = ell（f(Δ)=chord−ell，f 单调）。
    """
    R = R_A - b * th_cur
    hi = min(4.0 * ell / max(R, 1e-6), math.pi)
    lo = 0.0
    cx = R * math.cos(th_cur)
    cy = R * math.sin(th_cur)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        Rm = R_A - b * (th_cur - mid)
        d = math.hypot(cx - Rm * math.cos(th_cur - mid),
                       cy - Rm * math.sin(th_cur - mid))
        if d < ell:
            lo = mid
        else:
            hi = mid
    th_next = th_cur - 0.5 * (lo + hi)
    return th_next, _spiral_point(R_A, b, th_next)


def solve(inputs):
    R_A = float(inputs["R_A"])
    p = float(inputs["p"])
    v0 = float(inputs["v0"])
    N = int(inputs["N"])
    ell_head = float(inputs["ell_head"])
    ell_body = float(inputs["ell_body"])
    times = [float(t) for t in inputs.get("times", [0, 60, 120, 180, 240, 300])]
    b = p / (2.0 * math.pi)

    theta_at = {{T: _solve_theta(R_A, p, v0, T, 0.01) for T in times}}
    positions = []
    head_speeds = {{}}
    pair_distances = {{}}
    for T in times:
        th = theta_at[T]
        pts = [_spiral_point(R_A, b, th)]
        # 全把手均在螺线上：逐节弦距二分（体侧外扩，θ 递减）
        for i in range(1, N):
            ell = ell_head if i == 1 else ell_body
            th, pt = _place_next(R_A, b, th, ell)
            pts.append(pt)
        positions.append({{"time": T, "points": pts}})
        ds = []
        for i in range(N - 1):
            dx = pts[i + 1][0] - pts[i][0]
            dy = pts[i + 1][1] - pts[i][1]
            ds.append(math.hypot(dx, dy))
        pair_distances[str(int(T))] = ds
        if T >= 1.0:
            c = _spiral_point(R_A, b, _solve_theta(R_A, p, v0, T - 1.0, 0.01))
            head_speeds[str(int(T))] = math.hypot(pts[0][0] - c[0], pts[0][1] - c[1])
        else:
            c = _spiral_point(R_A, b, _solve_theta(R_A, p, v0, T + 1.0, 0.01))
            head_speeds[str(int(T))] = math.hypot(pts[0][0] - c[0], pts[0][1] - c[1])

    return {{
        "positions": positions,
        "head_speeds": head_speeds,
        "head_theta": {{str(int(T)): theta_at[T] for T in times}},
        "pair_distances": pair_distances,
        "R_spiral": {{str(int(T)): R_A - b * theta_at[T] for T in times}},
        "diagnostics": {{"solver": "euler+spiral_chord_bisection",
                        "euler_dt": 0.01, "handles": N,
                        "ell_head": ell_head, "ell_body": ell_body}},
    }}


if __name__ == "__main__":
    with open("input.json", encoding="utf-8") as f:
        _inputs = json.load(f)
    _out = solve(_inputs)
    print(json.dumps(_out, ensure_ascii=False))
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(_out, f, ensure_ascii=False, indent=2)
'''


# C1/C2：求解器本体完全一致（修正发生在 MODEL_IR 层——ell_body 1.925→1.65），
# 仅 provenance 注释不同 → 不同 code_hash → 各自独立 CODE artifact。
C1_CODE = _code("# MODEL_IR v1: ell_body = 1.925（M1 约束系数错误，数值验证将 FAIL）")
C2_CODE = _code("# MODEL_IR v2: ell_body = 1.65（M2 修正约束系数，数值验证应 PASS）")

# ---------------------------------------------------------------- 数值验证规格（外部注入）



# ---------------------------------------------------------------- 契约对齐（audit FIX-5.4）

def _enrich_schema_required(d: dict) -> dict:
    """补齐 model_ir.schema.json 各节 required 字段（真实字段值，非占位）。

    机制/方程/实验/假设的 schema 承诺字段在 M1/M2 中以真实语义补全：
    related_equations 引用本模型方程 id；derivation_trace 引用机制/假设；
    experiments 声明 inputs/expected_outputs（来自 parameters/variables）；
    assumptions 显式 type + rationale。
    """
    for m in d.get("mechanisms") or []:
        m.setdefault("related_equations",
                     [e["equation_id"] for e in d.get("equations") or []
                      if e.get("mechanism_ref") == m.get("mechanism_id")])
        if not m.get("related_equations") and d.get("equations"):
            m["related_equations"] = [d["equations"][0]["equation_id"]]
    for e in d.get("equations") or []:
        e.setdefault("derivation_trace", [])
        if not e.get("derivation_trace"):
            mech = e.get("mechanism_ref")
            if mech:
                e["derivation_trace"] = ["mechanism " + mech]
    for x in d.get("experiments") or []:
        x.setdefault("type", "simulation")
        x.setdefault("inputs",
                     [i for i in (x.get("inputs_refs") or [])])
        if not x.get("inputs") and d.get("parameters"):
            x["inputs"] = [p_["parameter_id"] for p_ in d["parameters"][:2]]
        x.setdefault("expected_outputs",
                     [v["symbol"] for v in d.get("variables") or []
                      if v.get("type") in ("state", "output", "decision")])
    for a in d.get("assumptions") or []:
        a.setdefault("type", "simplification")
        a.setdefault("rationale", a.get("text", ""))
    return d


M1_DICT = _enrich_schema_required(M1_DICT)
M2_DICT = _enrich_schema_required(M2_DICT)

# P0-1 契约：MODEL_IR 声明变量 → 代码输出 key 的显式翻译表（可审计）。
# x_i/y_i 为向量输出（positions[].points 数组），theta→head_theta、
# R_spiral→R_spiral、v_i→head_speeds（dict 按时间索引）。fidelity 据此做
# 结构映射校验；容器输出（positions）只做 key 存在性判定，范围校验跳过。
OUTPUT_MAPPING = {
    "x_i": "positions",
    "y_i": "positions",
    "theta": "head_theta",
    "R_spiral": "R_spiral",
    "v_i": "head_speeds",
}

VALIDATION_SPEC = {
    "constraint_tolerance": 1e-6,
    "constraints": [
        {"name": "C002_head_spacing", "pair_index": 0,
         "reference": 2.86, "tolerance": 1e-6},
        {"name": "C002_body_spacing", "pair_index": "1+",
         "reference": 1.65, "tolerance": 1e-6},
    ],
    "objective": {"name": "head_speed", "expected": 1.0, "tolerance": 0.02},
    "domain": {"min": -15.0, "max": 15.0},
}
