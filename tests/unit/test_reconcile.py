"""Reconcile 对账器单元测试（System Hardening P2）。

口径：status.json 投影 ↔ registry/graph 内容真源，只读、永不静默。
运行: python -m pytest tests/unit/test_reconcile.py -q
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402
from runtime.state.model import ProjectState  # noqa: E402
from runtime.state.reconcile import detect_mode, reconcile  # noqa: E402


def _build(tmp_path):
    reg = ArtifactRegistry(tmp_path / "state" / "registry.json")
    graph = EvidenceGraph(reg, tmp_path / "state" / "evidence_graph.json")
    state = ProjectState(tmp_path / "state" / "status.json")
    p = reg.create("problem", title="赛题", activate=True)
    q1 = reg.create("question", title="问题1", activate=True)
    m = reg.create("model", title="模型", depends_on=[q1.artifact_id], activate=True)
    e = reg.create("experiment", title="实验", question=q1.artifact_id,
                   depends_on=[m.artifact_id], activate=True)
    r = reg.create("result", title="结果", depends_on=[e.artifact_id], activate=True)
    c = reg.create("claim", title="结论", question=q1.artifact_id,
                   depends_on=[r.artifact_id], activate=True)
    graph.add_relation(p.artifact_id, "motivates", q1.artifact_id)
    graph.add_relation(q1.artifact_id, "solved_by", m.artifact_id)
    graph.add_relation(m.artifact_id, "validated_by", e.artifact_id)
    graph.add_relation(e.artifact_id, "produces", r.artifact_id)
    graph.add_relation(r.artifact_id, "supports", c.artifact_id)
    # 生产口径落盘顺序（checkpoint(): registry → graph → 派生投影 → state）
    reg.save()
    graph.save()
    state.refresh_from(reg, graph)
    state.save()
    return tmp_path, reg, graph, state, q1, m


class TestDetectMode:
    def test_empty(self, tmp_path):
        assert detect_mode(tmp_path) == "empty"

    def test_v3(self, tmp_path):
        sdir = tmp_path / "state"
        sdir.mkdir(parents=True)
        (sdir / "status.json").write_text("{}", encoding="utf-8")
        assert detect_mode(tmp_path) == "v3"

    def test_legacy(self, tmp_path):
        wdir = tmp_path / "work"
        wdir.mkdir(parents=True)
        (wdir / "state.json").write_text("{}", encoding="utf-8")
        assert detect_mode(tmp_path) == "legacy"


class TestReconcile:
    def test_ok_when_projection_matches(self, tmp_path):
        tmp_path, *_ = _build(tmp_path)
        rep = reconcile(tmp_path)
        assert rep["ok"], rep["problems"]

    def test_detects_questions_set_drift(self, tmp_path):
        tmp_path, reg, graph, state, q1, m = _build(tmp_path)
        # 内容真源新登记一个 question artifact，但投影未重新派生（崩溃窗口）
        reg.create("question", title="问题2",
                   depends_on=[q1.artifact_id], activate=True)
        reg.save()
        rep = reconcile(tmp_path)
        assert not rep["ok"]
        assert any("questions" in p_ for p_ in rep["problems"])
        assert "questions_set" in rep["diff"]

    def test_detects_models_candidates_drift(self, tmp_path):
        tmp_path, reg, graph, state, q1, m = _build(tmp_path)
        reg.create("model", title="新模型", depends_on=[q1.artifact_id], activate=True)
        reg.save()
        rep = reconcile(tmp_path)
        assert not rep["ok"]
        assert any("models.candidates" in p_ for p_ in rep["problems"])

    def test_recovery_reprojection_clears_problems(self, tmp_path):
        tmp_path, reg, graph, state, q1, m = _build(tmp_path)
        # 崩溃窗口：内容真源多了一个 question，投影未重新派生（同 drift 测试）
        reg.create("question", title="问题2", activate=True)
        reg.save()
        assert not reconcile(tmp_path)["ok"]
        # 恢复口径：重新派生投影并落盘（session.checkpoint() 的等价物）
        state.refresh_from(reg, graph)
        state.save()
        rep = reconcile(tmp_path)
        assert rep["ok"], rep["problems"]

    def test_missing_registry_reported(self, tmp_path):
        sdir = tmp_path / "state"
        sdir.mkdir(parents=True)
        state = ProjectState(sdir / "status.json")
        state.set_problem_status("in_progress")
        state.save()
        rep = reconcile(tmp_path)
        assert not rep["ok"]
        assert any("registry" in p_ for p_ in rep["problems"])

    def test_legacy_mode_ok_no_projection(self, tmp_path):
        wdir = tmp_path / "work"
        wdir.mkdir(parents=True)
        (wdir / "state.json").write_text(
            json.dumps({"schema_version": "1.0", "steps": []}), encoding="utf-8")
        rep = reconcile(tmp_path)
        assert rep["ok"] and rep["mode"] == "legacy"