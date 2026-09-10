"""Crash Consistency 故障注入测试（System Hardening P2）。

模拟 checkpoint 中途崩溃（registry/graph 已落盘、status.json 投影未落盘），
验证：①各文件原子写（无半截损坏）②reconcile 诚实报出漂移③resume 恢复口径
（重派生投影）后对账全绿。

运行: python -m pytest tests/unit/test_crash_consistency.py -q
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402
from modeling_harness.runtime.state.model import ProjectState  # noqa: E402
from modeling_harness.runtime.state.reconcile import reconcile  # noqa: E402


class TestCrashConsistency:
    def test_checkpoint_crash_leaves_readable_files_and_reconcile_flags(self, tmp_path):
        proj = tmp_path / "proj"
        s = RuntimeSession(proj, ["Q001"], max_workers=1)
        s.run()

        # 注入崩溃：registry/graph 落盘成功后，status.json 投影落盘前抛错
        def _crash():
            raise RuntimeError("simulated crash mid-checkpoint")

        s.state.save = _crash
        s.registry.create("model", title="崩溃窗口新增模型",
                          depends_on=["Q001"], activate=True)
        with pytest.raises(RuntimeError, match="simulated crash"):
            s.checkpoint()

        # 所有已落盘文件必须仍可解析（原子写保证）
        state2 = ProjectState(proj / "state" / "status.json")
        assert state2.data["schema_version"] == 3
        # 投影是旧的（无新模型），内容真源是新的（有新模型）→ reconcile 必须报漂移
        rep = reconcile(proj)
        assert not rep["ok"]
        assert any("models.candidates" in p_ for p_ in rep["problems"])

        # 恢复：重建会话 → resume（会自动 checkpoint 重派生投影）→ 对账全绿
        s2 = RuntimeSession(proj, ["Q001"], max_workers=1)
        s2.resume()
        rep2 = reconcile(proj)
        assert rep2["ok"], rep2["problems"]

    def test_engine_progress_atomic_write(self, tmp_path):
        proj = tmp_path / "proj"
        s = RuntimeSession(proj, ["Q001"], max_workers=1)
        s.run()
        p = proj / "state" / "engine_progress.json"
        assert p.exists()
        # 无残留 .tmp 半截文件
        leftovers = [f for f in p.parent.iterdir() if f.suffix == ".tmp"]
        assert leftovers == []
        import json
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data["engine_schema"] == 1
        assert isinstance(data["completed"], list) and data["completed"]