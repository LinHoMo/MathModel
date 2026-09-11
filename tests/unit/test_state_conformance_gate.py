# -*- coding: utf-8 -*-
"""实例状态契约门禁测试（validate.check_project_state_conformance）。

背景：三个交付实例原先写的是**扁平** status.json（problem/questions 挂顶层）、
用了非法维度值（problem.status="parsed"）并注册退役类型 narrative，导致
e2e_metrics 抛 KeyError、交付物被静默丢弃。本测试把这两类缺陷固化为回归用例：
门禁必须能抓到它们，也必须放行合规实例。

运行: py -3.12 -m pytest tests/unit/test_state_conformance_gate.py -q
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.cli.validate import check_project_state_conformance  # noqa: E402


def _mk_project(root: Path, name: str = "p1") -> Path:
    pdir = root / "projects" / name
    (pdir / "state").mkdir(parents=True, exist_ok=True)
    return pdir


def _registry(types, extra_payload=None):
    arts = {}
    for i, t in enumerate(types, start=1):
        aid = {"question": f"Q{i}", "result": f"MH-RESULT-{i:04d}"}.get(
            t, f"MH-{t.upper()}-{i:04d}")
        payload = {}
        if extra_payload:
            payload.update(extra_payload)
        arts[aid] = {"schema_version": "3.1", "artifact_id": aid, "type": t,
                     "version": 1, "status": "active", "title": t,
                     "created_by": "test", "created_at": "2026-09-10T00:00:00Z",
                     "updated_at": "2026-09-10T00:00:00Z", "payload": payload}
    return {"registry_version": 3, "project": "p1", "updated_at": "x",
            "counters": {}, "artifacts": arts}


class TestStateConformanceGate:
    def test_no_projects_dir_passes(self, tmp_path):
        ok, msg = check_project_state_conformance(tmp_path)
        assert ok and "无活跃项目实例" in msg

    def test_flat_legacy_status_is_rejected(self, tmp_path):
        """扁平投影（缺 state 键）→ 必须失败（原先会让 e2e_metrics 崩）。"""
        pdir = _mk_project(tmp_path)
        (pdir / "state" / "status.json").write_text(json.dumps({
            "schema_version": 3, "project": "p1", "updated_at": "x",
            "problem": {"status": "parsed", "artifact": "MH-PROBLEM-0001"},
            "questions": {}, "evidence": {"claims_total": 0},
        }, ensure_ascii=False), encoding="utf-8")
        (pdir / "state" / "registry.json").write_text(
            json.dumps(_registry(["problem"]), ensure_ascii=False),
            encoding="utf-8")
        ok, msg = check_project_state_conformance(tmp_path)
        assert not ok
        assert "非多维投影" in msg

    def test_retired_artifact_type_is_rejected(self, tmp_path):
        """退役类型 narrative → 必须失败（原先被静默跳过）。"""
        pdir = _mk_project(tmp_path)
        (pdir / "state" / "registry.json").write_text(
            json.dumps(_registry(["problem", "narrative"]), ensure_ascii=False),
            encoding="utf-8")
        _write_conformant_status(pdir)
        ok, msg = check_project_state_conformance(tmp_path)
        assert not ok
        assert "narrative" in msg

    def test_dangling_payload_path_is_rejected(self, tmp_path):
        """payload 指向不存在的文件 → 必须失败。"""
        pdir = _mk_project(tmp_path)
        (pdir / "state" / "registry.json").write_text(
            json.dumps(_registry(["problem"], extra_payload={"path": "missing/x.md"}),
                       ensure_ascii=False), encoding="utf-8")
        _write_conformant_status(pdir)
        ok, msg = check_project_state_conformance(tmp_path)
        assert not ok
        assert "悬空" in msg

    def test_illegal_dimension_value_is_rejected(self, tmp_path):
        pdir = _mk_project(tmp_path)
        (pdir / "state" / "registry.json").write_text(
            json.dumps(_registry(["problem"]), ensure_ascii=False),
            encoding="utf-8")
        _write_conformant_status(pdir, problem_status="parsed")
        ok, msg = check_project_state_conformance(tmp_path)
        assert not ok
        assert "非法值" in msg

    def test_conformant_project_passes(self, tmp_path):
        pdir = _mk_project(tmp_path)
        (pdir / "state" / "registry.json").write_text(
            json.dumps(_registry(["problem", "question", "model", "experiment",
                                  "result", "claim"]), ensure_ascii=False),
            encoding="utf-8")
        _write_conformant_status(pdir)
        ok, msg = check_project_state_conformance(tmp_path)
        assert ok, msg
        assert "契约一致" in msg


def _write_conformant_status(pdir: Path, problem_status: str = "complete"):
    """用 Runtime 的 ProjectState 写一份合规投影（与生产路径同口径）。"""
    from modeling_harness.runtime.state.model import ProjectState

    st = ProjectState(pdir / "state" / "status.json")
    st.data = ProjectState._empty()
    st.data["project"] = "p1"
    st.data["state"]["problem"]["status"] = problem_status
    st.data["state"]["questions"]["Q1"] = {
        "status": "validated", "models": [], "experiments": [], "claims": [],
        "dependencies": [], "retry_count": 0, "failure_reason": None,
        "last_updated": "2026-09-10T00:00:00Z",
    }
    st.save()
