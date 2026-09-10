"""P13-0 Measurement Integrity（provenance-based realization v1）测试。

运行: python -m pytest tests/integration/test_e2e_metrics.py -q
验证: 真实性拆分的分子/分母保留、不进能力均值、判据为 created_by。
"""

import importlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "core" / "tools"))

from runtime.execution.session import RuntimeSession  # noqa: E402


def _project(tmp_path, name="p-mi"):
    """2 问题管线 + 一组 agent 登记的实验/结果/声明。

    FIX-1.5：注入真实外部 Model Constructor 产物（MODEL_IR + code +
    validation_spec）走真实执行闭环——Measurement Integrity 统计的
    是真实产物结构，不是空跑结构。
    """
    from conftest import mir, CODE, validation_spec
    from runtime.execution.adapters import LocalPythonAdapter
    s = RuntimeSession(tmp_path / name, ["Q001", "Q002"],
                       execution_adapter=LocalPythonAdapter())
    for i, q in enumerate(["Q001", "Q002"]):
        qid = f"Q{i + 1:03d}"
        s.executor_impl.shared["external_model_irs"] = {
            **s.executor_impl.shared.get("external_model_irs", {}),
            qid: mir(qid, f"M-{qid}"),
        }
        s.executor_impl.shared["external_code"] = {
            **s.executor_impl.shared.get("external_code", {}),
            qid: CODE,
        }
        s.executor_impl.shared["validation_specs"] = {
            **s.executor_impl.shared.get("validation_specs", {}),
            qid: validation_spec(),
        }
    s.run()
    exp = s.registry.create("experiment", title="agent 实验", question="Q001",
                            data={"runs": 5}, created_by="agent-test",
                            activate=True)
    res = s.registry.create("result", title="agent 结果", question="Q001",
                            depends_on=[exp.artifact_id],
                            tags=["baseline", "sensitivity"],
                            data={"runs": 5}, created_by="agent-test",
                            activate=True)
    claim = s.registry.create("claim", title="agent 声明", question="Q001",
                              depends_on=[res.artifact_id],
                              created_by="agent-test", activate=True)
    s.graph.add_relation(exp.artifact_id, "produces", res.artifact_id)
    s.graph.add_relation(res.artifact_id, "supports", claim.artifact_id)
    s.checkpoint()
    return tmp_path / name


def test_integrity_keeps_numerator_denominator(tmp_path):
    em = importlib.import_module("e2e_metrics")
    report = em.compute_e2e_metrics(_project(tmp_path))
    mi = report["measurement_integrity"]
    # 数值 = 真实 DAG 产物计数（audit FIX-1.5 后 DAG 注入真实外部
    # 产物执行，实验/声明由执行链真实产生）：
    #   experiment: 2（DAG 每问题 1 实验节点）+ 1（agent）= 3
    #   claim: 2（DAG 合成 claim）+ 1（agent）= 3
    #   paper_section: 10（论文投影节点产生）+ 0（agent）= 10
    # 机制不变量：numerator = created_by 为 agent 的产物数。
    assert mi["experiment_realization"]["numerator"] == 1
    assert mi["experiment_realization"]["denominator"] == 3   # 2×DAG + agent
    assert mi["experiment_realization"]["value"] == 33.3
    assert mi["validation_realization"]["numerator"] == 1
    assert mi["validation_realization"]["denominator"] == 3
    assert mi["validation_realization"]["value"] == 33.3
    assert mi["writing_realization"]["numerator"] == 0
    assert mi["writing_realization"]["denominator"] == 12  # DAG writing 节点计数
    assert mi["writing_realization"]["value"] == 0.0
    assert "criterion" in mi and "v1" in mi["criterion"]


def test_integrity_not_part_of_capability_mean(tmp_path):
    em = importlib.import_module("e2e_metrics")
    report = em.compute_e2e_metrics(_project(tmp_path, name="p-mi2"))
    assert "measurement_integrity" not in report["metrics"]
    assert not any(k.endswith("mean") for k in report["measurement_integrity"])
    # summary 只由 8 项能力指标构成
    assert report["summary"]["computed"] + report["summary"]["absent"] == 8


def test_overall_real_artifact(tmp_path):
    em = importlib.import_module("e2e_metrics")
    report = em.compute_e2e_metrics(_project(tmp_path, name="p-mi3"))
    mi = report["measurement_integrity"]["overall_real_artifact"]
    assert mi["numerator"] == 3 and mi["denominator"] > mi["numerator"]
    assert mi["value"] == round(100.0 * mi["numerator"] / mi["denominator"], 1)


def test_structure_hit_compact_canonicalization():
    """P13-2 统一规则（非单题特判）：allowed_modeling_structures 与卡族名的
    紧凑匹配归一化（v1.2 起结构为唯一评分依据，字符串方法匹配已移除）。"""
    em = importlib.import_module("e2e_metrics")
    fam = {"mc-arima": "classical_timeseries"}
    assert em._structure_hit("mc-arima", fam, ["time series"])[0] is True
    assert em._structure_hit("mc-topsis", {"mc-topsis": "decision_analysis"},
                             ["time series"])[0] is False
    assert em._structure_hit("mc-arima", fam,
                             ["classical_timeseries"])[0] is True


def test_model_structural_check_modelir_contract():
    """P1 统一后：structural check 以 MODEL_IR 契约为准（objectives 复数）；
    旧式指针 artifact（card_id/family/shortlist）标记 legacy_pointer 不判 FAIL。"""
    import types

    em = importlib.import_module("e2e_metrics")

    def art(aid, data, payload=None):
        return types.SimpleNamespace(artifact_id=aid, data=data, payload=payload or [])

    mir = art("MIR001", {
        "ir_version": "1.0",
        "model_family": {"primary": "multibody_dynamics", "description": "x"},
        "objectives": [{"objective_id": "O001", "type": "simulate"}],
        "constraints": [{"constraint_id": "C001", "type": "equality"}],
        "variables": [{"variable_id": "V001", "type": "state"}],
    })
    legacy = art("M001", {"card_id": "mc-x", "family": "dp", "shortlist": ["dp"]})
    broken = art("MIR002", {
        "ir_version": "1.0",
        "objectives": [],
        "constraints": [{"constraint_id": "C001"}],
        "variables": [{"variable_id": "V001"}],
    })

    r1 = em._model_structural_check([mir, legacy])
    assert r1["structural_pass"] is True
    assert r1["models_checked"] == 1
    assert r1["legacy_pointer_skipped"] == 1
    assert r1["per_model"]["M001"]["legacy_pointer"] is True
    assert all(r1["per_model"]["MIR001"][f] is True
               for f in ("objectives", "constraints", "variables"))

    r2 = em._model_structural_check([broken])
    assert r2["structural_pass"] is False
    assert r2["per_model"]["MIR002"]["objectives"] is False

    # 全为 legacy pointer → 无可查契约模型，不判 FAIL（None）
    r3 = em._model_structural_check([legacy])
    assert r3["structural_pass"] is None
    assert r3["legacy_pointer_skipped"] == 1
