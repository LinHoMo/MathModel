"""gate.py 退出码契约回归测试。"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.tools import gate  # noqa: E402


def _run_main(monkeypatch, tmp_path, results, json_mode):
    project = tmp_path / "project"
    project.mkdir(parents=True)
    monkeypatch.setattr(gate.S, "load", lambda project: {})
    monkeypatch.setattr(gate, "run_gate", lambda project, hand, agent, state: results)
    argv = ["gate.py", str(project), "modeler", "problem-parser"]
    if json_mode:
        argv.append("--json")
    monkeypatch.setattr(sys, "argv", argv)
    return gate.main()


def test_json_and_text_return_soft_failure_code_consistently(monkeypatch, tmp_path):
    result = SimpleNamespace(ok=False, hard=False, name="warning", detail="可改进")

    text_rc = _run_main(monkeypatch, tmp_path / "text", [result], json_mode=False)
    json_rc = _run_main(monkeypatch, tmp_path / "json", [result], json_mode=True)

    assert text_rc == gate.EXIT_SOFT
    assert json_rc == gate.EXIT_SOFT


def test_json_and_text_return_hard_failure_code_consistently(monkeypatch, tmp_path):
    result = SimpleNamespace(ok=False, hard=True, name="blocking", detail="阻塞")

    text_rc = _run_main(monkeypatch, tmp_path / "text", [result], json_mode=False)
    json_rc = _run_main(monkeypatch, tmp_path / "json", [result], json_mode=True)

    assert text_rc == gate.EXIT_HARD
    assert json_rc == gate.EXIT_HARD
