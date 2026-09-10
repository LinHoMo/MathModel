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
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from modeling_harness.runtime.execution.replay import replay_execution  # noqa: E402
from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402


def _make_exec(tmp_path, code=None, qid="Q001"):
    """经真实 DAG（外部 code 注入 → subprocess 执行）产出 EXEC artifact。"""
    from _real_session import make_real_session
    if code is None:
        code = ("def solve(inputs):\n"
                "    return {'v': 42}\n\n"
                "if __name__ == '__main__':\n"
                "    import json\n"
                "    print(json.dumps(solve({}), ensure_ascii=False))\n")
    s = make_real_session(tmp_path, questions=(qid,), run=False)
    s.executor_impl.shared["external_code"][qid] = code
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
        override = ("def solve(inputs):\n"
                    "    return {'v': 99}\n\n"
                    "if __name__ == '__main__':\n"
                    "    import json\n"
                    "    print(json.dumps(solve({}), ensure_ascii=False))\n")
        rep = replay_execution(s.project_dir, x.artifact_id,
                               code_override=override)
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
        rep2 = replay_execution(
            s.project_dir, x.artifact_id,
            code_override=("def solve(inputs):\n"
                           "    return {'v': 42}\n\n"
                           "if __name__ == '__main__':\n"
                           "    import json\n"
                           "    print(json.dumps(solve({}), ensure_ascii=False))\n"))
        assert rep2["ok"] is True

    def test_replay_failed_original(self, tmp_path):
        boom = ("def solve(inputs):\n"
                "    raise ValueError('boom')\n\n"
                "if __name__ == '__main__':\n"
                "    import json\n"
                "    print(json.dumps(solve({}), ensure_ascii=False))\n")
        s, x = _make_exec(tmp_path, code=boom)
        assert x.data["status"] == "failed"
        rep = replay_execution(s.project_dir, x.artifact_id)
        assert rep["ok"] is True   # 失败也是可重放状态（复现失败=一致）
        assert rep["replayed_status"] == "failed"
        assert rep["outputs_match"] is False  # 非 success 无输出可比
        assert rep["deviation"] == []
