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
    """2 问题管线 + 一组 agent 登记的实验/结果/声明。"""
    s = RuntimeSession(tmp_path / name, ["Q001", "Q002"])
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
    assert mi["experiment_realization"]["numerator"] == 1
    assert mi["experiment_realization"]["denominator"] == 3   # E001/E002 + agent
    assert mi["experiment_realization"]["value"] == 33.3
    assert mi["validation_realization"]["numerator"] == 1
    assert mi["validation_realization"]["denominator"] == 3
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
