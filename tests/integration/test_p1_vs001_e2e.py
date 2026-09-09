# -*- coding: utf-8 -*-
"""P1-VS-001 e2e：Executable Model Construction Loop（2024_A vertical slice）。

真实闭环（全部经 Artifact Registry / Evidence Graph / Replay 复原）：

    M1 → RUN1 → VALIDATION FAIL → REVISION → M2 → RUN2 → VALIDATION PASS

7 条硬验收逐条断言：
  1. Problem 有稳定 Artifact ID（registry 中可查）
  2. M1 是真实 MODEL_IR（L1 semantic + L2 mathematical + L3 computational 三层）
  3. Code 由 M1 生成并实际执行（subprocess 真跑，固定 ABI def solve(inputs)）
  4. ExecutionResult 含真实数值输出（status 来自真实退出码）
  5. Validation 基于真实数值判 FAIL（M1 约束违反 > 0，非伪造）
  6. M2 与 M1 存在 revision lineage（revision_of/supersedes 边；M2 不覆盖 M1）
  7. Replay 能从 M1 重现 RUN1/RUN2（输出数值一致）

LLM-free：M1/M2 MODEL_IR 与 C1/C2 代码由外部 Model Constructor 手写注入
（research/P15/vs001_run/vs001_fixtures.py），core runtime 只登记/校验/执行/
保真/验证/谱系/replay。
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "research" / "P15" / "vs001_run"))

from vs001_driver import (  # noqa: E402
    LOOP_NODES, artifact_ids, make_session, relation_pairs, replay_report,
    run_m1, run_m2,
)
from vs001_fixtures import C1_CODE, VALIDATION_SPEC  # noqa: E402

from runtime.modeling.model_ir import ModelIRBuilder  # noqa: E402


@pytest.fixture()
def session(tmp_path):
    s = make_session(tmp_path / "proj")
    yield s
    # 清理：无


def _pair_distances(session, exec_id: str) -> dict:
    x = session.registry.get(exec_id)
    return (x.data or {}).get("outputs", {}).get("pair_distances", {})


class TestP1VS001E2E:
    """7 条验收，逐条断言（真实 subprocess 数值）。"""

    def test_01_problem_stable_artifact_id(self, session, tmp_path):
        run_m1(session, tmp_path / "exec")
        # problem 为全局 artifact（无 question 归属），直接按类型查
        ps = [a.artifact_id for a in session.registry.list_by_type("problem")]
        assert len(ps) == 1
        pid = ps[0]
        assert pid == "P001", f"问题应有稳定 Artifact ID（P001），实际 {pid}"
        assert session.registry.get(pid).type == "problem"
        assert session.registry.get(pid).status == "active"

    def test_02_m1_is_real_model_ir_three_layers(self, session, tmp_path):
        run_m1(session, tmp_path / "exec")
        mirs = artifact_ids(session, "model_ir")
        assert len(mirs) == 1
        mir1 = session.registry.get(mirs[0])
        data = mir1.data
        assert data["model_id"] == "M2024A-Q1-v1"
        assert data["ir_version"] == "1.0"
        # 三层：L1 semantic / L2 mathematical / L3 computational
        m = ModelIRBuilder.from_dict(data)
        layers = m.layers()
        assert set(layers) == {"L1_semantic", "L2_mathematical",
                               "L3_computational"}
        assert len(layers["L1_semantic"]) == 4
        assert len(layers["L2_mathematical"]) == 5
        assert len(layers["L3_computational"]) == 3
        assert any(e.get("type") == "constitutive"
                   for e in m.l2["equations"])                     # E001
        assert any(s.get("type") == "simulation"
                   for s in m.l3["solvers"])                        # S001

    def test_03_code_generated_and_subprocess_executed(self, session, tmp_path):
        run_m1(session, tmp_path / "exec")
        codes = artifact_ids(session, "code")
        assert len(codes) == 1
        code_art = session.registry.get(codes[0])
        assert "def solve(inputs)" in code_art.data["code"]          # 固定 ABI
        assert code_art.data["code_hash"]
        execs = artifact_ids(session, "execution_result")
        assert len(execs) == 1
        ex = session.registry.get(execs[0])
        assert ex.data["status"] == "success"                        # 真实退出码 0
        assert ex.data["returncode"] == 0
        assert "local_python" in ex.data["provenance"].get("adapter", "")
        # 边：model_ir -implemented_by-> code -executed_by-> EXEC
        rels = relation_pairs(session)
        mir1 = artifact_ids(session, "model_ir")[0]
        assert (mir1, "implemented_by", codes[0]) in rels
        assert (codes[0], "executed_by", execs[0]) in rels

    def test_04_execution_result_has_real_numeric_outputs(self, session, tmp_path):
        run_m1(session, tmp_path / "exec")
        execs = artifact_ids(session, "execution_result")
        ex = session.registry.get(execs[0])
        outputs = ex.data["outputs"]
        assert isinstance(outputs, dict) and outputs
        # 真实数值（M1：体板间距 ≈1.925，龙头速度 ≈1.0）
        assert abs(outputs["pair_distances"]["0"][0] - 2.86) < 1e-6
        assert abs(outputs["pair_distances"]["0"][1] - 1.925) < 1e-6
        assert abs(outputs["head_speeds"]["60"] - 1.0) < 0.01
        assert len(outputs["positions"]) == 6
        assert len(outputs["positions"][0]["points"]) == 224
        # 结果 R artifact 有真实数值（非占位）
        results = artifact_ids(session, "result")
        assert len(results) == 1
        rv = session.registry.get(results[0]).data
        assert rv["status"] == "computed"
        assert rv["value"]["pair_distances"]["0"][1] == pytest.approx(1.925)

    def test_05_validation_fails_on_real_numbers(self, session, tmp_path):
        run_m1(session, tmp_path / "exec")
        vrs = artifact_ids(session, "verification_result")
        assert len(vrs) == 1
        vr = session.registry.get(vrs[0])
        d = vr.data
        assert d["status"] == "failed"                              # 整体 FAIL
        assert d["execution_valid"] is True                         # 执行本身成功
        assert d["mathematical_valid"] is False                     # 数值判 FAIL
        assert d["constraint_violation_max"] == pytest.approx(0.275, abs=1e-6)
        # FAIL 独立于 evidence_gate：数值检查如实给出失败原因
        assert any(c["name"] == "C002_body_spacing" and not c["passed"]
                   for c in d["checks"])
        # 边：EXEC -verified_by-> VR
        execs = artifact_ids(session, "execution_result")
        rels = relation_pairs(session)
        assert (execs[0], "verified_by", vrs[0]) in rels

    def test_06_m2_revision_lineage_no_overwrite(self, session, tmp_path):
        run_m1(session, tmp_path / "exec")
        mir1 = artifact_ids(session, "model_ir")[0]
        # M1 快照（防覆盖）
        m1_snapshot = session.registry.get(mir1).data
        run_m2(session, mir1, tmp_path / "exec")
        mirs = artifact_ids(session, "model_ir")
        assert len(mirs) == 2
        mir2 = [m for m in mirs if m != mir1][0]
        m2_data = session.registry.get(mir2).data
        assert m2_data["model_id"] == "M2024A-Q1-v2"
        # M1 未被覆盖：原 artifact 仍在、数据不变；状态 → superseded（FIX-6.3）
        assert session.registry.get(mir1) is not None
        assert session.registry.get(mir1).data == m1_snapshot
        assert session.registry.get(mir1).status == "superseded"
        assert session.registry.get(mir1).invalidation["invalidated_by"] == mir2
        # 谱系边：MIR2 -revision_of-> MIR1、MIR2 -supersedes-> MIR1（新取代旧）
        rels = relation_pairs(session)
        assert (mir2, "revision_of", mir1) in rels
        assert (mir2, "supersedes", mir1) in rels
        # FIX-6.1/6.4：失败诊断 + 修订接受决策（机械证据）已登记
        diags = artifact_ids(session, "diagnosis")
        assert len(diags) == 1
        assert (mir1, "diagnosed_by", diags[0]) in rels
        decs = [a for a in session.registry.list_by_type("decision")
                if (a.data or {}).get("kind") == "revision_acceptance"]
        assert len(decs) == 1
        assert decs[0].data["recommendation"] in ("accept", "keep")
        assert decs[0].data["chosen"] == mir2
        assert (decs[0].artifact_id, "selects", mir2) in rels
        # M2 有自己的执行链（CODE2 → EXEC2 → R2）
        assert len(artifact_ids(session, "code")) == 2
        assert len(artifact_ids(session, "execution_result")) == 2
        assert len(artifact_ids(session, "verification_result")) == 2

    def test_07_replay_reproduces_runs(self, session, tmp_path):
        run_m1(session, tmp_path / "exec")
        exec1 = artifact_ids(session, "execution_result")[0]
        r1 = replay_report(session.project_dir, exec1)
        assert r1["ok"] is True, f"RUN1 重放失败: {r1.get('problems')}"
        assert r1["outputs_match"] is True
        assert r1["recorded_status"] == r1["replayed_status"] == "success"

        mir1 = artifact_ids(session, "model_ir")[0]
        run_m2(session, mir1, tmp_path / "exec")
        execs = artifact_ids(session, "execution_result")
        exec2 = [e for e in execs if e != exec1][0]
        r2 = replay_report(session.project_dir, exec2)
        assert r2["ok"] is True, f"RUN2 重放失败: {r2.get('problems')}"
        assert r2["outputs_match"] is True
        # RUN2 输出为修正后的真实数值（1.65），且与 RUN1 不同（数值级）
        x2 = session.registry.get(exec2)
        d2 = x2.data["outputs"]["pair_distances"]["0"][1]
        assert abs(d2 - 1.65) < 1e-6
        x1 = session.registry.get(exec1)
        assert abs(x1.data["outputs"]["pair_distances"]["0"][1] - 1.925) < 1e-6
        # 闭环终态：M2 验证 PASS
        vrs = artifact_ids(session, "verification_result")
        assert len(vrs) == 2
        vr2 = session.registry.get(vrs[1])
        assert vr2.data["status"] == "passed"
        assert vr2.data["mathematical_valid"] is True
        assert vr2.data["empirical_valid"] is True

    # ------------------------------------------------------------ 闭环结构完整性

    def test_full_loop_persisted_and_reconstructable(self, session, tmp_path):
        run_m1(session, tmp_path / "exec")
        mir1 = artifact_ids(session, "model_ir")[0]
        run_m2(session, mir1, tmp_path / "exec")
        # 落盘复原：从磁盘 registry/graph 重建并核对闭环
        proj = session.project_dir
        reg_path = proj / "state" / "registry.json"
        graph_path = proj / "state" / "evidence_graph.json"
        assert reg_path.exists() and graph_path.exists()
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        ids = reg["artifacts"]  # {aid: {...}}
        # 闭环 artifact 全部在场：P/MIR1/C1/EXEC1/VR1/MIR2/C2/EXEC2/VR2
        for prefix in ("P001", "MIR001", "CODE001", "EXEC001", "VR001",
                       "MIR002", "CODE002", "EXEC002", "VR002"):
            assert prefix in ids, f"缺 {prefix}"
        rels = {(r["from"], r["relation"], r["to"])
                for r in graph["relations"]}
        # 关键边
        assert ("MIR001", "instantiates", "M001") in rels
        assert ("MIR001", "implemented_by", "CODE001") in rels
        assert ("CODE001", "executed_by", "EXEC001") in rels
        assert ("EXEC001", "produces", "R001") in rels
        assert ("EXEC001", "verified_by", "VR001") in rels
        assert ("MIR002", "revision_of", "MIR001") in rels
        assert ("MIR001", "supersedes", "MIR002") in rels
        assert ("MIR002", "implemented_by", "CODE002") in rels
        assert ("CODE002", "executed_by", "EXEC002") in rels
        assert ("EXEC002", "produces", "R002") in rels
        assert ("EXEC002", "verified_by", "VR002") in rels
        # 状态文件
        assert (proj / "state" / "status.json").exists()
