"""MODEL_IR — Executable Model Specification（P1-VS-001 C1）。

定位（用户裁决 STRATEGY_P1_VS001 / MODEL_IR_SPEC v1.1）：
    MODEL_IR 是**可执行模型规范**（Executable Model Specification），不是
    model_family 标签。它把模型分成三层：

        L1 semantic      问题绑定 / 假设 / 变量 / 参数
        L2 mathematical  目标 / 约束 / 机理 / 方程 / 依赖
        L3 computational 求解器 / 实验 / 验证

本模块零依赖（不引 jsonschema，不引任何第三方库），提供：
    * ModelIR dataclass —— 三层字段视图（L1/L2/L3）
    * ModelIRBuilder.from_dict(data) —— 入口（缺 required 字段即抛错）
    * validate_model_ir(model_ir) -> list[str] —— 结构校验，返回问题清单
      （空列表 = 通过）

required 字段 = src/modeling_harness/schemas/v3/model/model_ir.schema.json 顶层 required
（18 字段，与 P15-K002 模板 18 字段承诺对齐）：
    ir_version / model_id / model_family / problem_binding / assumptions /
    variables / parameters / objectives / constraints / mechanisms /
    equations / dependencies / solvers / experiments / validations /
    claims / model_graph / modeling_trace

core 内 LLM-free：本模块只登记/校验，不生成模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# 与 src/modeling_harness/schemas/v3/model/model_ir.schema.json 顶层 required 一一对应
MODEL_IR_REQUIRED_FIELDS: tuple[str, ...] = (
    "ir_version",
    "model_id",
    "model_family",
    "problem_binding",
    "assumptions",
    "variables",
    "parameters",
    "objectives",
    "constraints",
    "mechanisms",
    "equations",
    "dependencies",
    "solvers",
    "experiments",
    "validations",
    "claims",
    "model_graph",
    "modeling_trace",
)

# 三层字段归属（STRATEGY §2：L1 semantic / L2 mathematical / L3 computational）
L1_SEMANTIC_FIELDS: tuple[str, ...] = (
    "problem_binding", "assumptions", "variables", "parameters",
)
L2_MATHEMATICAL_FIELDS: tuple[str, ...] = (
    "objectives", "constraints", "mechanisms", "equations", "dependencies",
)
L3_COMPUTATIONAL_FIELDS: tuple[str, ...] = (
    "solvers", "experiments", "validations",
)


class ModelIRError(ValueError):
    """MODEL_IR 构造/校验非法。"""


@dataclass
class ModelIR:
    """Executable Model Specification 的三层视图。"""

    data: dict[str, Any]
    ir_version: str = "1.0"
    model_id: str = ""
    model_family: dict[str, Any] = field(default_factory=dict)
    problem_binding: dict[str, Any] = field(default_factory=dict)

    # L1 semantic
    assumptions: list[dict[str, Any]] = field(default_factory=list)
    variables: list[dict[str, Any]] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=list)

    # L2 mathematical
    objectives: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    mechanisms: list[dict[str, Any]] = field(default_factory=list)
    equations: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, Any]] = field(default_factory=list)

    # L3 computational
    solvers: list[dict[str, Any]] = field(default_factory=list)
    experiments: list[dict[str, Any]] = field(default_factory=list)
    validations: list[dict[str, Any]] = field(default_factory=list)

    claims: list[dict[str, Any]] = field(default_factory=list)
    model_graph: Any = None
    modeling_trace: Any = None

    # audit FIX-2.3（P1-03）：code_mapping（equation_id → code section/symbol）。
    # 可选字段，不加入 REQUIRED（18 字段契约稳定）；codegen 登记代码时
    # 校验 implementation_ref 指向真实 CODE artifact。
    code_mapping: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------ 视图

    @property
    def l1(self) -> dict[str, Any]:
        """L1 semantic：问题语义层。"""
        return {k: getattr(self, k) for k in L1_SEMANTIC_FIELDS}

    @property
    def l2(self) -> dict[str, Any]:
        """L2 mathematical：数学形式层。"""
        return {k: getattr(self, k) for k in L2_MATHEMATICAL_FIELDS}

    @property
    def l3(self) -> dict[str, Any]:
        """L3 computational：可计算层。"""
        return {k: getattr(self, k) for k in L3_COMPUTATIONAL_FIELDS}

    def layers(self) -> dict[str, dict[str, Any]]:
        """三层整体视图（验收 2：M1 必须含 L1+L2+L3 三层）。"""
        return {"L1_semantic": self.l1,
                "L2_mathematical": self.l2,
                "L3_computational": self.l3}

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.data)
        if self.code_mapping:
            d["code_mapping"] = self.code_mapping
        return d

    def parameters_dict(self) -> dict[str, Any]:
        """参数 → {symbol: value}（执行 input.json 的派生源）。"""
        out: dict[str, Any] = {}
        for p in self.parameters or []:
            sym = p.get("symbol") or p.get("parameter_id")
            if sym and "value" in p:
                out[sym] = p["value"]
        return out


def migrate_legacy_format(legacy: dict) -> dict:
    """P1-4：旧格式 → 当前契约格式（幂等，不修改输入）。

    差异（src/modeling_harness/schemas/v3/model/model_ir.schema.json 为唯一真源）：
    - 历史 research 产物（K001/K002/K003 预检与正式 run、vs001 演示基线）
      无 code_mapping 字段 → 补默认 {}（该字段非 required）。
    其余 18 个 required 顶层字段在 core 与历史产物间一致，无需迁移。

    注意：词表/嵌套结构的差异属于内容级差异，无法机械迁移；冻结产物
    （K001/K002/K003）标记 legacy 不回溯（见 LEGACY_MODEL_IR.md）。
    新产物必须直接符合 core schema。
    """
    out = dict(legacy or {})
    out.setdefault("code_mapping", {})
    return out


class ModelIRBuilder:
    """从 dict 构造 ModelIR（校验 required 字段，缺则抛 ModelIRError）。"""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ModelIR:
        if not isinstance(data, dict):
            raise ModelIRError(f"MODEL_IR 必须是 dict，实际 {type(data).__name__}")
        missing = [k for k in MODEL_IR_REQUIRED_FIELDS if k not in data]
        if missing:
            raise ModelIRError(
                f"MODEL_IR 缺少 required 字段: {missing}（共 {len(MODEL_IR_REQUIRED_FIELDS)} 个 required）")
        problems = validate_model_ir(data)
        if problems:
            raise ModelIRError("MODEL_IR 结构校验失败: " + "; ".join(problems[:8]))
        return ModelIR(
            data=data,
            ir_version=str(data.get("ir_version", "")),
            model_id=str(data.get("model_id", "")),
            model_family=dict(data.get("model_family") or {}),
            problem_binding=dict(data.get("problem_binding") or {}),
            assumptions=list(data.get("assumptions") or []),
            variables=list(data.get("variables") or []),
            parameters=list(data.get("parameters") or []),
            objectives=list(data.get("objectives") or []),
            constraints=list(data.get("constraints") or []),
            mechanisms=list(data.get("mechanisms") or []),
            equations=list(data.get("equations") or []),
            dependencies=list(data.get("dependencies") or []),
            solvers=list(data.get("solvers") or []),
            experiments=list(data.get("experiments") or []),
            validations=list(data.get("validations") or []),
            code_mapping=dict(data.get("code_mapping") or {}),
            claims=list(data.get("claims") or []),
            model_graph=data.get("model_graph"),
            modeling_trace=data.get("modeling_trace"),
        )


# ---------------------------------------------------------------- 校验

def validate_model_ir(model_ir: dict[str, Any]) -> list[str]:
    """结构校验（零依赖）：返回问题清单，空列表 = 通过。

    检查（对齐 schema 顶层承诺，不做 jsonschema 全量语义——那是 schema 校验层）：
      1. 18 个 required 顶层字段存在
      2. 三层（L1/L2/L3）关键字段类型为 list 且非空（模板承诺的数组节）
      3. ir_version == "1.0"
      4. 数组元素关键承诺字段存在（assumptions/variables/parameters/
         objectives/constraints/mechanisms/equations/solvers/experiments/
         validations/claims 的 id 字段）
    """
    problems: list[str] = []

    missing = [k for k in MODEL_IR_REQUIRED_FIELDS if k not in model_ir]
    if missing:
        problems.append(f"缺少 required 字段: {missing}")

    if "ir_version" in model_ir and str(model_ir["ir_version"]) != "1.0":
        problems.append(f"ir_version 必须为 '1.0'，实际 {model_ir['ir_version']!r}")

    # 对象节：problem_binding（schema 要求 object，不得为空）
    pb = model_ir.get("problem_binding")
    if pb is not None and not isinstance(pb, dict):
        problems.append(f"problem_binding 必须是对象，实际 {type(pb).__name__}")
    elif pb is not None and not pb:
        problems.append("problem_binding 为空对象")

    # 数组节（模板承诺的数组节）：存在性 + list 类型 + 非空。
    # FIX-2.1（audit P0-05）契约分层：modeling_trace 显式标注
    # construction_status=pending_model_spec（骨架 MIR，不可执行）时允许
    # 空数组——骨架不编造 variables/equations（禁止伪变量/伪方程），
    # 由 construction_status 显式承担"不可执行"义务；其余结构校验不变。
    _ARRAY_FIELDS = (
        "assumptions", "variables", "parameters",
        "objectives", "constraints", "mechanisms", "equations", "dependencies",
        "solvers", "experiments", "validations", "claims",
    )
    skeleton = _is_skeleton(model_ir)
    for f in _ARRAY_FIELDS:
        v = model_ir.get(f)
        if v is None:
            continue    # required 缺失已在上面报
        if not isinstance(v, list):
            problems.append(f"{f} 必须是数组，实际 {type(v).__name__}")
            continue
        if not v and not skeleton:
            problems.append(f"{f} 为空数组（模板承诺非空）")

    # 数组元素 id 承诺字段
    _ID_FIELDS = {
        "assumptions": "assumption_id", "variables": "variable_id",
        "parameters": "parameter_id", "objectives": "objective_id",
        "constraints": "constraint_id", "mechanisms": "mechanism_id",
        "equations": "equation_id", "solvers": "solver_id",
        "experiments": "experiment_id", "validations": "validation_id",
        "claims": "claim_id",
    }
    for key, id_field in _ID_FIELDS.items():
        for i, item in enumerate(model_ir.get(key) or []):
            if not isinstance(item, dict):
                problems.append(f"{key}[{i}] 必须是对象")
                continue
            if not str(item.get(id_field) or "").strip():
                problems.append(f"{key}[{i}] 缺少 {id_field}")

    if not skeleton:
        problems.extend(_check_l2_mathematical(model_ir))

    return problems


def _check_l2_mathematical(model_ir: dict[str, Any]) -> list[str]:
    """L2 Mathematical 真实接线（audit FIX-5.3 / P2-02）。

    用 src/modeling_harness/validators/modules/formula_checker 对 MODEL_IR 全部数学表达式
    （objectives/constraints/equations 的 expression/equation 字段）做确定性
    结构检查：括号配对 + LaTeX 语法 + 常见错误（空分母/连续运算符等）。
    只做语法/结构正确性，不推断数学等价性——数值正确性由 execution +
    validation 承担。
    """
    from modeling_harness.validators.modules.formula_checker import check_formulas

    issues: list[str] = []
    expressions: list[tuple[str, str]] = []   # (来源标签, 表达式)
    for o in model_ir.get("objectives") or []:
        for f in ("expression", "target"):
            v = o.get(f)
            if isinstance(v, str) and v.strip():
                expressions.append((f"objective[{o.get('objective_id','?')}].{f}", v))
    for c in model_ir.get("constraints") or []:
        for f in ("expression", "inequality", "equality"):
            v = c.get(f)
            if isinstance(v, str) and v.strip():
                expressions.append((f"constraint[{c.get('constraint_id','?')}].{f}", v))
    for e in model_ir.get("equations") or []:
        for f in ("equation", "expression"):
            v = e.get(f)
            if isinstance(v, str) and v.strip():
                expressions.append((f"equation[{e.get('equation_id','?')}].{f}", v))
    for label, expr in expressions:
        res = check_formulas(expr)
        if not res.get("valid"):
            for issue in res.get("issues") or []:
                issues.append(f"{label}: {issue}")
    return issues


def _is_skeleton(model_ir: dict[str, Any]) -> bool:
    """骨架 MODEL_IR 判定：modeling_trace 显式标注 construction_status=
    pending_model_spec（不可执行，不编造 formulation）。"""
    trace = model_ir.get("modeling_trace")
    if not isinstance(trace, list):
        return False
    return any(
        isinstance(t, dict) and "pending_model_spec" in str(t.get("note", ""))
        for t in trace)
