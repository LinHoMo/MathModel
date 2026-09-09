"""FIX-2.1（audit P0-05）：默认路径必须产 MODEL_IR 或如实 FAIL。

审查发现：do_model_construction 无外部注入时只登记假设，不产 MIR，
节点仍 PASS——"只登记假设就 PASS" 的假闭环。

修复：无外部 Model Constructor 注入时，基于选中方法卡构造骨架 MODEL_IR
（18 字段契约合规，modeling_trace 显式标注 construction_status=
pending_model_spec——不可执行，不编造 variables/equations）；
无方法卡 → 返回 None → 节点如实 FAIL（no_model_ir）。

运行: python -m pytest tests/integration/test_model_ir_skeleton.py -q
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.modeling.model_ir import (  # noqa: E402
    MODEL_IR_REQUIRED_FIELDS,
    ModelIRBuilder,
)


def _default_session(tmp_path):
    """无注入、无 adapter 的默认路径 session（认知由默认确定性执行器完成）。"""
    return RuntimeSession(tmp_path / "proj", ["Q001"])


def test_default_path_no_injection_fails_honestly(tmp_path):
    """无外部构造者 + 无选中方法卡 → model_construction 如实 FAIL（no_model_ir）。

    禁止"只登记假设就 PASS"：节点必须 FAIL/blocked，且不产生假 claim。
    """
    s = _default_session(tmp_path)
    rep = s.run()
    prog = rep["progress"]
    assert "model_construction" in prog.get("blocked", {}), \
        "无方法卡时不得 PASS（audit P0-05 假闭环）"
    assert "no_model_ir" in prog["failures"]["model_construction"], \
        prog["failures"]["model_construction"]
    # 执行/声明环节不得出现假 PASS 产物（无真实数值执行 → evidence 如实 FAIL）
    claims = s.registry.list_by_type("claim")
    assert not any(c.status == "active" and c.data.get("statement")
                   for c in claims), "无执行事实不得产活跃 claim"


def test_skeleton_mir_contract_compliant(tmp_path):
    """有选中方法卡时构造骨架 MODEL_IR：18 字段契约合规 + 显式 pending。

    - 18 顶层 required 字段齐全（ModelIRBuilder 结构校验通过）
    - modeling_trace 标注 construction_status=pending_model_spec（不可执行）
    - variables/objectives/equations 不编造（保持空，禁止伪变量/伪方程）
    """
    s = _default_session(tmp_path)
    s.run()  # 系统创建 Q001 节点与 registry 结构（model_construction 如实 FAIL 无妨）
    # 显式注入选型：Q001 选中方法卡 mc-ols（替代无证据 UNSELECTED 场景）
    s.executor_impl.shared["Q001"] = {"card_id": "mc-ols"}
    mid = s.registry.create(
        "model", title="OLS 模型", question="Q001",
        data={"card_id": "mc-ols", "model_family": "ols"}, activate=True)
    mir_id = s.executor_impl._skeleton_mir("Q001", mid.artifact_id)
    assert mir_id, "有方法卡时必须产出骨架 MODEL_IR"
    art = s.registry.get(mir_id)
    data = art.data
    # 18 字段契约
    assert all(k in data for k in MODEL_IR_REQUIRED_FIELDS), \
        sorted(MODEL_IR_REQUIRED_FIELDS - set(data))
    # 可构造性（结构校验通过）
    ModelIRBuilder.from_dict(data)
    # 显式不可执行标注（诚实：不编造 formulation）
    trace = data["modeling_trace"]
    assert any("pending_model_spec" in t.get("note", "")
               for t in trace), "骨架 MIR 必须标注不可执行"
    assert data["variables"] == [] and data["equations"] == [], \
        "骨架不得编造伪变量/伪方程"
    # instantiates 边
    assert any(r["relation"] == "instantiates"
               and r["from"] == mir_id and r["to"] == mid.artifact_id
               for r in s.graph.relations)


def test_skeleton_mir_passes_jsonschema(tmp_path):
    """骨架 MODEL_IR 通过 core/schemas/v3/model/model_ir.schema.json 校验。"""
    import json

    import jsonschema

    s = _default_session(tmp_path)
    s.run()
    s.executor_impl.shared["Q001"] = {"card_id": "mc-ols"}
    mid = s.registry.create(
        "model", title="OLS 模型", question="Q001",
        data={"card_id": "mc-ols", "model_family": "ols"}, activate=True)
    mir_id = s.executor_impl._skeleton_mir("Q001", mid.artifact_id)
    schema = json.loads(
        Path(REPO / "core/schemas/v3/model/model_ir.schema.json")
        .read_text(encoding="utf-8"))
    jsonschema.validate(s.registry.get(mir_id).data, schema)
