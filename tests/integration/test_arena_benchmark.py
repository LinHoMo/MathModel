# -*- coding: utf-8 -*-
"""Candidate Arena benchmark 机制固化测试（轻量池，不重跑全池）。

验证：候选加载（F 臂跳过原因）/ 真实执行 / 通用数值验证 / 机械选型 /
报告 schema。选型必须基于机械证据（exec_status/valid/cvm/fidelity），
无候选满足 → UNSELECTED（不硬选）。
"""

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_ARENA = _REPO / "research" / "P15" / "benchmark" / "arena"
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_ARENA) not in sys.path:
    sys.path.insert(0, str(_ARENA))

from arena_runner import (  # noqa: E402
    build_spec,
    load_pool,
    render_markdown,
    run_arena,
    select_by_evidence,
)

POOL = _REPO / "research" / "P15" / "experiments" / "P15-K003" / "runs"


@pytest.fixture(scope="module")
def pool():
    return load_pool(POOL)


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    workdir = tmp_path_factory.mktemp("arena")
    return run_arena(POOL, workdir, problems=["2011_B", "2019_C"])


def test_load_pool_skips_f_arm_with_reason(pool):
    """F 臂（自由文本，无 MODEL_IR）按设计跳过并记录原因。"""
    real, skipped = pool
    assert real, "候选池不应为空"
    reasons = {x["reason"] for x in skipped}
    assert "F 臂无 model_ir" in reasons
    # 池内候选不含 F 臂
    assert all(c["arm"] != "F" for cands in real.values() for c in cands)


def test_build_spec_resolves_output_mapping():
    """通用验证规格：声明名经 output_mapping 解析到代码输出键。"""
    cand = {
        "model_ir": {"variables": [{"symbol": "coverage"}],
                     "objectives": [{"target": "t_max"}]},
        "output_mapping": {"coverage": "coverage_rate_3min",
                           "t_max": "max_response_time_min"},
    }
    spec = build_spec(cand)
    paths = {c["path"] for c in spec["checks"]}
    assert "coverage_rate_3min" in paths
    assert "max_response_time_min" in paths
    assert "coverage" not in paths


def test_select_by_evidence_prefers_valid():
    """机械选型：valid=True 优先；无 success 不选型。"""
    rows = [
        {"model_id": "A", "exec_status": "success", "valid": False,
         "constraint_violation_max": 0.5, "fidelity_score": 1.0},
        {"model_id": "B", "exec_status": "success", "valid": True,
         "constraint_violation_max": 0.0, "fidelity_score": 0.9},
    ]
    d = select_by_evidence(rows)
    assert d["selected"] is True and d["chosen"] == "B"
    # 无 success → 如实不选型
    d2 = select_by_evidence([{"model_id": "X", "exec_status": "failed",
                              "valid": False}])
    assert d2["selected"] is False and d2["chosen"] is None


def test_run_arena_report_schema(report):
    """报告 schema：汇总 + 逐题决策（selected/chosen/basis）+ 验证语义说明。"""
    assert report["summary"]["problems"] == 2
    assert report["summary"]["candidates"] >= 4
    for p in report["problems"]:
        assert p["decision"]["selected"] in (True, False)
        assert p["decision"]["basis"]
        for c in p["candidates"]:
            assert c["exec_status"] in (
                "success", "failed", "timeout", "invalid", "not_executed")
    md = render_markdown(report)
    assert "## 验证语义说明" in md
    assert "机械选型" in md


def test_arena_reproducible(report, tmp_path_factory):
    """可复现：同池同题重跑，决策一致（真实 subprocess 重跑）。"""
    workdir2 = tmp_path_factory.mktemp("arena2")
    report2 = run_arena(POOL, workdir2, problems=["2011_B"])
    assert report2["problems"][0]["decision"]["chosen"] \
        == report["problems"][0]["decision"]["chosen"]


def test_arena_evidence_is_mechanical(report):
    """选型依据只来自机械字段（exec_status/valid/cvm/fidelity），无 recs[0]。"""
    for p in report["problems"]:
        for b in p["decision"]["basis"]:
            assert any(k in b for k in (
                "exec_status", "valid", "cvm", "fidelity", "l6", "无候选"))
