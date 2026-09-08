"""P0-E4 Execution-level Replay 测试：重建执行 + 偏差报告。

Replay ≠ rerun：在相同声明环境下重建一次 execution，并报告偏差。
场景：
1. 同 code 同 env → outputs 一致（可重放）
2. code 不同 → code_hash 偏差
3. 环境差异 → environment_hash 偏差
4. 无 code 本体（P0-E4 前产物）→ 明确报错 + code_override 可用
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from runtime.execution.replay import replay_execution  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402


def _make_exec(tmp_path, code="import json; print(json.dumps({'v': 42}))"):
    """通过真实 runtime 产出一个 execution_result artifact。"""
    s = RuntimeSession(tmp_path / "proj", ["Q001"], max_workers=1,
                       execution_adapter=LocalPythonAdapter())
    for qid in s.questions:
        s.executor_impl.shared.setdefault(qid, {})["plan"] = {"code": code}
    s.run()
    execs = s.registry.list_by_type("execution_result")
    assert len(execs) == 1
    return s, execs[0]


class TestReplayExecution:
    def test_replay_identical_outputs(self, tmp_path):
        s, x = _make_exec(tmp_path)
        rep = replay_execution(s.project_dir, x.artifact_id)
        assert rep["ok"] is True, rep
        assert rep["outputs_match"] is True
        assert rep["replayed_status"] == "success"
        assert rep["deviation"] == []

    def test_replay_code_change_detected(self, tmp_path):
        s, x = _make_exec(tmp_path)
        rep = replay_execution(s.project_dir, x.artifact_id,
                               code_override="import json; print(json.dumps({'v': 99}))")
        assert rep["ok"] is False
        dims = {d["dim"] for d in rep["deviation"]}
        assert "code_hash" in dims
        assert "outputs" in dims   # 输出也不同

    def test_replay_missing_code_reports_clearly(self, tmp_path):
        s, x = _make_exec(tmp_path)
        # 模拟 P0-E4 前产物：从磁盘 registry 去掉 code 本体
        reg_path = s.project_dir / "state" / "registry.json"
        raw = reg_path.read_text(encoding="utf-8")
        import json
        obj = json.loads(raw)
        art = obj["artifacts"][x.artifact_id]
        art["data"].pop("code", None)
        reg_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        rep = replay_execution(s.project_dir, x.artifact_id)
        assert rep["ok"] is False
        assert "未存 code 本体" in rep["problems"][0]
        # 提供 code_override 后可用
        rep2 = replay_execution(s.project_dir, x.artifact_id,
                                code_override="import json; print(json.dumps({'v': 42}))")
        assert rep2["ok"] is True

    def test_replay_failed_original(self, tmp_path):
        s, x = _make_exec(tmp_path, code="raise ValueError('boom')")
        assert x.data["status"] == "failed"
        rep = replay_execution(s.project_dir, x.artifact_id)
        assert rep["ok"] is True   # 失败也是可重放状态（复现失败=一致）
        assert rep["replayed_status"] == "failed"
        assert rep["outputs_match"] is False  # 非 success 无输出可比
        assert rep["deviation"] == []
