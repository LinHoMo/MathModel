"""P0-E5 Validation Primitive 测试：三状态铁律机械落地。

铁律：execution_status=success 绝不推出 model_status=correct。
VR.status：
  - passed  ⟺  execution success 且全部检查通过
  - failed  ⟺  execution success 但至少一项检查失败（可归因到具体 check）
  - invalid ⟺  execution 非 success（无输出可验证，不得 passed）
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402
from modeling_harness.runtime.execution.validation import (  # noqa: E402
    run_checks, validate_execution,
)
from modeling_harness.runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402


def _make_exec(tmp_path, code, qid="Q001"):
    """经真实 DAG（外部 code 注入 → subprocess 执行）产出 EXEC artifact。"""
    from _real_session import make_real_session
    s = make_real_session(tmp_path, questions=(qid,), run=False)
    s.executor_impl.shared["external_code"][qid] = code
    s.run()
    execs = s.registry.list_by_type("execution_result")
    assert len(execs) == 1
    return s, execs[0]


def _abicode(payload_lines: list[str]) -> str:
    """构造满足 L0 ABI（def solve(inputs) -> dict）的可执行代码。"""
    body = "\n".join("    " + ln for ln in payload_lines)
    return (f"def solve(inputs):\n{body}\n\n"
            "if __name__ == '__main__':\n"
            "    import json\n"
            "    print(json.dumps(solve({}), ensure_ascii=False))\n")


OK_CODE = _abicode(["return {'total_cost': 42.0, 'n': 5}"])
NEG_CODE = _abicode(["return {'total_cost': -1}"])
BOOM_CODE = _abicode(["raise ValueError('boom')"])


class TestRunChecks:
    def test_success_all_pass(self):
        status, checks = run_checks(
            {"status": "success", "outputs": {"total_cost": 42.0, "n": 5}},
            [{"name": "有结果", "kind": "output_field_exists", "path": "total_cost"},
             {"name": "数值", "kind": "output_numeric", "path": "total_cost"},
             {"name": "范围", "kind": "output_range", "path": "total_cost",
              "min": 0, "max": 100}])
        assert status == "passed"
        assert all(c["passed"] for c in checks)

    def test_range_failure_attributable(self):
        status, checks = run_checks(
            {"status": "success", "outputs": {"total_cost": -5.0}},
            [{"name": "成本非负", "kind": "output_range", "path": "total_cost",
              "min": 0}])
        assert status == "failed"
        assert checks[0]["passed"] is False
        assert "超出" in checks[0]["detail"]

    def test_failed_execution_invalid_not_passed(self):
        # 铁律：execution 非 success → invalid，即使检查看起来会通过
        status, checks = run_checks(
            {"status": "failed", "outputs": {"total_cost": 42.0}},
            [{"name": "有结果", "kind": "output_field_exists", "path": "total_cost"}])
        assert status == "invalid"
        assert checks[0]["passed"] is False
        assert "__execution_status__" == checks[0]["name"]

    def test_missing_field_detected(self):
        status, checks = run_checks(
            {"status": "success", "outputs": {}},
            [{"name": "有结果", "kind": "output_field_exists", "path": "total_cost"}])
        assert status == "failed"
        assert "缺失字段" in checks[0]["detail"]


class TestValidateExecution:
    def test_passed_vr_registered_with_edge(self, tmp_path):
        s, x = _make_exec(tmp_path, OK_CODE)
        vr = validate_execution(
            s.project_dir, x.artifact_id,
            [{"name": "成本范围", "kind": "output_range", "path": "total_cost",
              "min": 0, "max": 100}])
        assert vr.status == "passed"
        assert vr.verification_id.startswith("VR")
        assert vr.evidence_refs == [x.artifact_id]
        # registry 有 VR（重载磁盘真源，session 内存态不感知外部写入）
        # 注意：DAG model_validation 节点已按注入 validation_spec 真实产 VR001，
        # 手动 validate_execution 产 VR002——双重验证均为真实产物，都需落盘。
        from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
        reg2 = ArtifactRegistry(s.project_dir / "state" / "registry.json")
        reg2.load()
        vrs = reg2.list_by_type("verification_result")
        assert any(v.artifact_id == vr.verification_id for v in vrs)
        # graph 有 verified_by 边
        g = EvidenceGraph(s.registry, s.project_dir / "state" / "evidence_graph.json")
        g.load()
        edges = [(e["from"], e["relation"], e["to"]) for e in g.relations]
        assert (x.artifact_id, "verified_by", vr.verification_id) in edges

    def test_failed_vr_with_specific_check(self, tmp_path):
        s, x = _make_exec(tmp_path, NEG_CODE)
        assert x.data["status"] == "success"
        vr = validate_execution(
            s.project_dir, x.artifact_id,
            [{"name": "成本非负", "kind": "output_range", "path": "total_cost",
              "min": 0}])
        assert vr.status == "failed"
        assert vr.checks[0]["passed"] is False

    def test_failed_execution_yields_invalid_vr(self, tmp_path):
        s, x = _make_exec(tmp_path, BOOM_CODE)
        assert x.data["status"] == "failed"
        vr = validate_execution(
            s.project_dir, x.artifact_id,
            [{"name": "有结果", "kind": "output_field_exists", "path": "x"}])
        assert vr.status == "invalid"
        assert vr.checks[0]["name"] == "__execution_status__"

    def test_unknown_exec_id_raises(self, tmp_path):
        s, _ = _make_exec(tmp_path, OK_CODE)
        with pytest.raises(ValueError):
            validate_execution(s.project_dir, "EXEC999", [])
