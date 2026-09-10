# -*- coding: utf-8 -*-
"""audit FIX-4.2/4.3/4.4（K003 实验治理）：
- FIX-4.2 rebuild 可复现（execution_writer.rebuild_all 幂等）
- FIX-4.3 执行权限分离（execution_result 唯一写入路径在 execution_writer）
- FIX-4.4 submission ID 随机化（uuid4，不可逆/不可链接）

运行: python -m pytest tests/unit/test_k003_governance.py -q
"""

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
for p in (_REPO / "core", _REPO / "research" / "P15" / "experiments" / "P15-K003"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from scripts.execution_writer import (build_execution_result,  # noqa: E402
                                      rebuild_all, write_run_execution)


# ---------------------------------------------------------------- FIX-4.2
def _make_registry_with_exec(tmp_path, exec_id="EXEC001"):
    from runtime.artifacts.registry import ArtifactRegistry
    reg = ArtifactRegistry(tmp_path / "project" / "state" / "registry.json")
    reg.project = "k003"
    reg.create("question", title="Q1", activate=True)
    reg.create("execution_result", title="exec", question="Q001",
               activate=True,
               data={"status": "success", "returncode": 0,
                     "outputs": {"objective": 12.5},
                     "stdout": "ok\n", "stderr": "",
                     "duration_ms": 10, "code_hash": "c" * 64,
                     "environment_hash": "e" * 64,
                     "execution_id": exec_id,
                     "legacy_unverified": True})
    reg.save()
    return reg


def test_rebuild_reproducible_idempotent(tmp_path):
    """FIX-4.2：rebuild_all 幂等——同 registry 两次重建输出一致。"""
    reg = _make_registry_with_exec(tmp_path)
    runs = tmp_path / "runs" / "run001"
    runs.mkdir(parents=True)
    (runs / "manifest.json").write_text(
        json.dumps({"execution": {"exec_id": "EXEC001",
                                  "code_id": "CODE001"},
                    "model_id": "M-001"}), encoding="utf-8")

    r1 = rebuild_all(runs.parent, tmp_path / "project")
    assert r1["run001"]["ok"] and r1["run001"]["status"] == "success"
    out1 = (runs / "execution_result.json").read_text(encoding="utf-8")

    r2 = rebuild_all(runs.parent, tmp_path / "project")
    out2 = (runs / "execution_result.json").read_text(encoding="utf-8")
    assert out1 == out2, "rebuild 必须幂等（同 registry → 同产物）"
    data = json.loads(out1)
    assert data["status"] == "success"
    assert data["outputs"] == {"objective": 12.5}
    assert data["code_hash"] == "c" * 64
    assert data["exec_id"] == "EXEC001"


def test_rebuild_invalid_when_registry_missing(tmp_path):
    """FIX-4.2：registry 无 EXEC → invalid 壳（不写默认数值冒充真实）。"""
    runs = tmp_path / "runs" / "run001"
    runs.mkdir(parents=True)
    (runs / "manifest.json").write_text(
        json.dumps({"execution": {"exec_id": "EXEC-NOPE",
                                  "code_id": "CODE001"},
                    "model_id": "M-001"}), encoding="utf-8")
    (tmp_path / "project" / "state").mkdir(parents=True)
    r = rebuild_all(runs.parent, tmp_path / "project")
    assert r["run001"]["ok"]
    assert r["run001"]["status"] == "invalid"
    data = json.loads((runs / "execution_result.json").read_text(encoding="utf-8"))
    assert data["status"] == "invalid"
    assert "registry 无" in data["error"]


# ---------------------------------------------------------------- FIX-4.3
def test_writer_is_single_write_path(tmp_path):
    """FIX-4.3：runner 源码不得再直接写 execution_result.json（写入收敛到
    execution_writer）。结构断言：k003_formal_runner.py 中
    "execution_result.json" 仅作为 writer 调用参数出现，无 write_json 写入。
    """
    runner = (_REPO / "research" / "P15" / "experiments" / "P15-K003"
              / "k003_formal_runner.py")
    src = runner.read_text(encoding="utf-8")
    # 不允许 runner 里出现 write_json(run_dir / "execution_result.json", ...)
    assert "write_json(run_dir / \"execution_result.json\"" not in src, \
        "runner 不得直接写 execution_result.json（必须走 execution_writer）"
    # writer 存在且包含写入路径
    writer = (_REPO / "research" / "P15" / "experiments" / "P15-K003"
              / "scripts" / "execution_writer.py")
    ws = writer.read_text(encoding="utf-8")
    assert "execution_result.json" in ws


def test_build_execution_result_reads_registry_only(tmp_path):
    """FIX-4.3：execution_result 字段必须来自 registry（execution substrate），
    不允许默认值冒充。"""
    reg = _make_registry_with_exec(tmp_path)
    res = build_execution_result(tmp_path / "project", "EXEC001",
                                 "CODE001", "M-001")
    assert res["status"] == "success"
    assert res["returncode"] == 0
    assert res["outputs"] == {"objective": 12.5}
    assert res["code_hash"] == "c" * 64
    assert res["executed_at"]


# ---------------------------------------------------------------- FIX-4.4
def test_blind_id_unlinkable():
    """FIX-4.4：submission ID 为 uuid4——不可反推 problem/arm/seed。"""
    from k003_formal_runner import make_submission_id
    a = make_submission_id("2020_B", "A", 42)
    b = make_submission_id("2020_B", "A", 42)
    assert len(a) == 12
    assert a != b, "uuid4 必须唯一（同参数两次生成不同 ID）"
    assert all(c in "0123456789abcdef" for c in a)
    # 不可逆：ID 中不得包含可反推的明文片段
    for needle in ("2020_B", "A", "42", "seed"):
        assert needle not in a
