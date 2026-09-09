"""Run Provenance / Deterministic Replay 测试（System Hardening P3）。

覆盖：
  * session.run() 自动落盘 RunRecord（schema 字段齐全、产物哈希可复算）
  * replay.verify：同配置同输入 → 全匹配；修改 inputs → 检出 input_hash 漂移
  * replay.diff：两次运行逐字段差异归因
  * 波次并行（max_workers=2）：per-question 隔离 + 状态可对账
运行: python -m pytest tests/unit/test_run_provenance.py -q
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from conftest import injected_session  # noqa: E402

from runtime.execution.replay import diff as replay_diff  # noqa: E402
from runtime.execution.replay import verify  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402
from runtime.state.reconcile import reconcile  # noqa: E402
from runtime.state.runs import derive_run_id, list_run_records  # noqa: E402


class TestRunRecord:
    def test_run_emits_record_with_required_fields(self, tmp_path):
        proj = tmp_path / "proj"
        s = injected_session(tmp_path, ["Q001"], run_meta={
            "model_provider": "mock", "model_version": "mock-1",
            "decision": "测试决策"})
        s.run()
        recs = list_run_records(proj)
        assert len(recs) == 1
        r = recs[0]
        for k in ("schema_version", "run_id", "status", "workflow_version",
                  "tool_version", "input_hash", "prompt_hash",
                  "artifact_hash", "evidence_hash", "started_at"):
            assert r.get(k), f"缺字段 {k}"
        assert r["schema_version"] == 1
        assert r["status"] == "completed"
        assert r["model_provider"] == "mock"
        assert r["model_version"] == "mock-1"
        # 产物哈希指到真实落盘文件
        assert (proj / "state" / "registry.json").exists()

    def test_run_id_deterministic(self):
        a = derive_run_id("p", ["Q001", "Q002"], "wf", "in")
        b = derive_run_id("p", ["Q002", "Q001"], "wf", "in")
        c = derive_run_id("p", ["Q001", "Q002"], "wf2", "in")
        assert a == b          # question 顺序无关
        assert a != c          # 工作流版本变了 run_id 变


class TestReplayVerify:
    def test_verify_ok_on_fresh_run(self, tmp_path):
        proj = tmp_path / "proj"
        injected_session(tmp_path, ["Q001"]).run()
        rep = verify(proj)
        assert rep["ok"], rep["problems"]

    def test_verify_detects_input_drift(self, tmp_path):
        proj = tmp_path / "proj"
        injected_session(tmp_path, ["Q001"]).run()
        # 篡改输入（新增文件）→ 应检出 input_hash 漂移
        indir = proj / "inputs"
        indir.mkdir(parents=True, exist_ok=True)
        (indir / "篡改.txt").write_text("drift", encoding="utf-8")
        rep = verify(proj)
        assert not rep["ok"]
        assert any(d["field"] == "input_hash" for d in rep["drift"])

    def test_verify_detects_artifact_drift(self, tmp_path):
        proj = tmp_path / "proj"
        injected_session(tmp_path, ["Q001"]).run()
        reg = proj / "state" / "registry.json"
        reg.write_text(reg.read_text(encoding="utf-8") + "\n// tampered",
                       encoding="utf-8")
        rep = verify(proj)
        assert not rep["ok"]
        assert any(d["field"] == "artifact_hash" for d in rep["drift"])

    def test_diff_attributes_changes(self, tmp_path):
        proj = tmp_path / "proj"
        s1 = injected_session(tmp_path, ["Q001"])
        s1.run()
        r1 = list_run_records(proj)[-1]["run_id"]
        # 外部执行器换版本 + 输入变化 → 出现两条记录
        indir = proj / "inputs"
        indir.mkdir(parents=True, exist_ok=True)
        (indir / "C.txt").write_text("题面", encoding="utf-8")
        s2 = injected_session(tmp_path, ["Q001"])
        s2.run()
        r2 = list_run_records(proj)[-1]["run_id"]
        assert r1 != r2
        d = replay_diff(proj, r1, r2)
        fields = {x["field"] for x in d["changed_fields"]}
        assert "input_hash" in fields


class TestParallelIsolation:
    def test_two_questions_parallel_isolated_and_reconcilable(self, tmp_path):
        proj = tmp_path / "proj"
        s = injected_session(tmp_path, ["Q001", "Q002"], max_workers=2)
        rep = s.run()
        art_qs = [a.question for a in s.registry.all()
                  if a.question in ("Q001", "Q002")]
        # per-question 隔离：artifact 各归其位，无串扰
        assert set(art_qs) == {"Q001", "Q002"}
        assert rep["progress"]["blocked"] == {}
        assert rep["progress"]["failures"] == {}
        # 并行后状态可对账（单一真源不变）
        rc = reconcile(proj)
        assert rc["ok"], rc["problems"]
        # 并行运行同样落 RunRecord 且可重放验证
        assert verify(proj)["ok"]