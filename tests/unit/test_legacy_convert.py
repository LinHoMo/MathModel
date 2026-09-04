"""P1 Legacy Compatibility 测试：V2 ⇄ V3 双向转换。

运行: python -m pytest tests/unit/test_legacy_convert.py -q
覆盖任务书 §36 Migration Tests: V2 Project → V3 conversion → V3 executable。
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.artifacts.registry import ArtifactRegistry
from runtime.graph.evidence_graph import EvidenceGraph
from runtime.legacy.convert import (
    LegacyError, convert_project, export_results, import_results, import_state,
)
from runtime.state.model import ProjectState


@pytest.fixture
def v2_project(tmp_path):
    """模拟一个有产物与进度的 V2 项目。"""
    p = tmp_path / "v2proj"
    (p / "work").mkdir(parents=True)
    (p / "figures").mkdir()
    (p / "code").mkdir()
    (p / "code" / "main.py").write_text("print('v2')", encoding="utf-8")
    (p / "figures" / "all_results.json").write_text(json.dumps({
        "q1_total_cost": 12345.6,
        "q2_efficiency": 0.87,
        "_meta": "skip me",
    }), encoding="utf-8")
    (p / "work" / "state.json").write_text(json.dumps({
        "state_version": "1.0",
        "project": "v2proj",
        "completed": [
            {"hand": "modeler", "agent": "problem-parser", "stage": 1},
            {"hand": "modeler", "agent": "type-classifier", "stage": 2},
            {"hand": "programmer", "agent": "template-selector", "stage": 1},
        ],
        "current": {"hand": "programmer", "agent": "code-implementer", "stage": 2},
    }), encoding="utf-8")
    return p


class TestImportResults:
    def test_import_creates_artifacts(self, v2_project):
        reg = ArtifactRegistry(v2_project / "state" / "registry.json")
        g = EvidenceGraph(reg, path=v2_project / "state" / "evidence_graph.json")
        report = import_results(v2_project, reg, g)
        # 两个有效键（_meta 跳过）→ R artifacts
        assert len(report["results"]) == 2
        rs = reg.list_by_type("result")
        assert {a.data["key"] for a in rs} == {"q1_total_cost", "q2_efficiency"}
        # code + experiment 载体
        assert report["code"] == "CODE001"
        assert report["experiment"] == "E001"
        # 关系: E001 produces R001/R002; E001 uses CODE001
        rels = {(e["from"], e["relation"], e["to"]) for e in g.relations}
        assert ("E001", "produces", "R001") in rels
        assert ("E001", "produces", "R002") in rels
        assert ("E001", "uses", "CODE001") in rels

    def test_import_idempotent(self, v2_project):
        reg = ArtifactRegistry(v2_project / "state" / "registry.json")
        g = EvidenceGraph(reg, path=v2_project / "state" / "evidence_graph.json")
        r1 = import_results(v2_project, reg, g)
        r2 = import_results(v2_project, reg, g)
        assert r2["results"] == []
        assert r2["skipped"] == ["q1_total_cost", "q2_efficiency"]
        assert len(reg.list_by_type("result")) == 2

    def test_missing_results_file_rejected(self, tmp_path):
        reg = ArtifactRegistry(tmp_path / "r.json")
        g = EvidenceGraph(reg, path=tmp_path / "g.json")
        with pytest.raises(LegacyError):
            import_results(tmp_path, reg, g)


class TestExportResults:
    def test_roundtrip(self, v2_project):
        reg = ArtifactRegistry(v2_project / "state" / "registry.json")
        g = EvidenceGraph(reg, path=v2_project / "state" / "evidence_graph.json")
        import_results(v2_project, reg, g)
        out = v2_project / "state" / "all_results_exported.json"
        exported = export_results(reg, out)
        assert exported == {"q1_total_cost": 12345.6, "q2_efficiency": 0.87}
        # V2 工具链可继续消费（标准 JSON 对象）
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["q1_total_cost"] == 12345.6


class TestImportState:
    def test_partial_progress_mapping(self, v2_project):
        state = ProjectState(v2_project / "state" / "status.json")
        state.data["project"] = "v2proj"
        mapping = import_state(v2_project, state)
        # modeler 部分完成 → problem/models in_progress
        assert mapping["problem"] == "in_progress"
        assert mapping["models"] == "in_progress"
        # programmer 部分完成 → experiments/evidence in_progress
        assert mapping["experiments"] == "in_progress"
        # writer/reviewer 未动 → pending
        assert mapping["review"] == "pending"
        assert state.data["run"]["phase"] == "legacy-imported"
        assert state.data["legacy"]["v2_state"]["completed_steps"] == 3

    def test_full_completion_mapping(self, tmp_path):
        p = tmp_path / "full"
        (p / "work").mkdir(parents=True)
        (p / "work" / "state.json").write_text(json.dumps({
            "completed": (
                [{"hand": "modeler", "agent": a} for a in (
                    "problem-parser", "type-classifier", "literature-searcher",
                    "method-matcher", "model-builder", "dag-builder",
                    "assumption-validator", "spec-auditor")]
                + [{"hand": "programmer", "agent": a} for a in (
                    "template-selector", "code-implementer", "test-runner",
                    "result-verifier", "guardrails-checker", "hash-auditor")]),
        }), encoding="utf-8")
        state = ProjectState(p / "state" / "status.json")
        mapping = import_state(p, state)
        assert mapping["problem"] == "complete"
        assert mapping["models"] == "complete"
        assert mapping["experiments"] == "complete"
        assert mapping["evidence"] == "complete"
        assert mapping["paper"] == "pending"

    def test_legacy_file_untouched(self, v2_project):
        before = (v2_project / "work" / "state.json").read_bytes()
        state = ProjectState(v2_project / "state" / "status.json")
        import_state(v2_project, state)
        assert (v2_project / "work" / "state.json").read_bytes() == before


class TestConvertProject:
    def test_end_to_end_conversion(self, v2_project):
        report = convert_project(v2_project)
        # state/ 三件套落盘
        state_dir = v2_project / "state"
        assert (state_dir / "registry.json").exists()
        assert (state_dir / "evidence_graph.json").exists()
        assert (state_dir / "status.json").exists()
        # 转换报告: CODE + E + R×2 = 4 个 artifacts
        assert report["registry"]["total"] == 4
        # 校验 Registry 完整性
        reg = ArtifactRegistry(state_dir / "registry.json")
        assert reg.integrity_check() == []
        g = EvidenceGraph(reg, path=state_dir / "evidence_graph.json")
        assert g.integrity_check() == []
        # V2 文件未被移动/删除
        assert (v2_project / "figures" / "all_results.json").exists()
        assert (v2_project / "work" / "state.json").exists()

    def test_convert_idempotent(self, v2_project):
        convert_project(v2_project)
        report2 = convert_project(v2_project)
        reg = ArtifactRegistry(v2_project / "state" / "registry.json")
        assert len(reg.list_by_type("result")) == 2
        assert len(reg.list_by_type("experiment")) == 1

    def test_v3_project_executable_after_conversion(self, v2_project):
        """任务书 §36 Migration Tests: 转换后的 V3 项目可被引擎消费。"""
        from runtime.execution.composer import WorkflowComposer
        from runtime.execution.engine import NodeResult, WorkflowEngine

        convert_project(v2_project)
        comp = WorkflowComposer(REPO / "core" / "workflows")
        exp = comp.compose_executable(["Q001", "Q002"])
        eng = WorkflowEngine(exp, lambda nid, ctx: NodeResult("pass"))
        result = eng.run()
        assert not result["blocked"]
        assert len(result["completed"]) == len(exp.nodes)
