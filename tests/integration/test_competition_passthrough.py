# -*- coding: utf-8 -*-
"""赛题类型（competition）从项目透传到 runtime 两个消费点的集成测试。

两个消费点（均使用真实依赖，不 mock）：
  1. ``WorkflowComposer.compose_executable(questions, competition)`` —— DAG 组合
  2. ``DefaultNodeExecutor(..., competition_type)`` —— candidate_arena 竞赛包选择

断言锚点：``candidate_arena.pack.pack_id``。理由：当前三个 competition profile
（cumcm/mcm/general）是刻意空壳，``dag.nodes`` 无差异；而 pack 语义可观测——
cp-cumcm 有 3 条 common_failure_modes，cp-mcm 为空。

契约：
  * competition_type / competition 显式给定 → 选用 ``cp-<competition>``；
  * 缺省（None）→ 行为与现状一致（默认 cp-cumcm）；
  * 未知赛事 → 回退默认 cp-cumcm（保持现状回退语义）；
  * Session 的 competition 透传到 compose_executable（未知赛事被 ComposeError 拒）。

运行: py -3.12 -m pytest tests/integration/test_competition_passthrough.py -q
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import pytest  # noqa: E402

from modeling_harness.runtime.execution.session import RuntimeSession  # noqa: E402
from modeling_harness.runtime.execution.handlers import DefaultNodeExecutor  # noqa: E402
from modeling_harness.runtime.execution.composer import ComposeError  # noqa: E402
from modeling_harness.runtime.artifacts.registry import ArtifactRegistry  # noqa: E402
from modeling_harness.runtime.graph.evidence_graph import EvidenceGraph  # noqa: E402


def _write_min_problem(project_dir) -> None:
    """最小题面（ADR-0008）：供问题理解层确定性派生 features。"""
    d = Path(project_dir) / "inputs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "problem.txt").write_text(
        "2026 年数学建模竞赛题目\n\n"
        "问题1　根据给定的数据，对候选方案作综合评价。\n",
        encoding="utf-8")


def _executor(tmp_path, **kw):
    reg = ArtifactRegistry(tmp_path / "registry.json")
    g = EvidenceGraph(reg, tmp_path / "evidence_graph.json")
    return DefaultNodeExecutor(reg, g, **kw)


# ---------------- 消费点 2：DefaultNodeExecutor → CandidateArena pack ----------------

def test_executor_competition_type_selects_matching_pack(tmp_path):
    """competition_type='mcm' → candidate_arena 选用 cp-mcm（而非默认 cp-cumcm）。"""
    ex = _executor(tmp_path, competition_type="mcm")
    assert ex.candidate_arena.pack is not None
    assert ex.candidate_arena.pack.pack_id == "cp-mcm"


def test_executor_cumcm_competition_type_selects_cumcm_pack(tmp_path):
    """competition_type='cumcm' → 选用 cp-cumcm。"""
    ex = _executor(tmp_path, competition_type="cumcm")
    assert ex.candidate_arena.pack.pack_id == "cp-cumcm"


def test_executor_none_preserves_default_cumcm(tmp_path):
    """无 competition_type → 行为与现状完全一致（默认 cp-cumcm）。"""
    ex = _executor(tmp_path)
    assert ex.candidate_arena.pack.pack_id == "cp-cumcm"


def test_executor_unknown_competition_falls_back_to_cumcm(tmp_path):
    """未知 competition_type → 回退默认 cp-cumcm（保持现状回退语义）。"""
    ex = _executor(tmp_path, competition_type="no-such")
    assert ex.candidate_arena.pack.pack_id == "cp-cumcm"


# ---------------- 消费点 1：RuntimeSession → compose_executable / executor ----------------

def test_session_competition_passthrough_to_executor(tmp_path):
    """RuntimeSession(competition='mcm') 透传到 executor 的候选竞技场。"""
    proj = tmp_path / "proj"
    _write_min_problem(proj)
    s = RuntimeSession(proj, ["Q001"], competition="mcm")
    assert s.executor_impl.candidate_arena.pack.pack_id == "cp-mcm"


def test_session_competition_passthrough_to_dag(tmp_path):
    """RuntimeSession(competition=...) 透传到 compose_executable。

    三个 competition profile 均为空壳（dag.nodes 无差异），故以「未知赛事被
    ComposeError 拒绝」作为透传的可观测证据——若 competition 未透传，
    compose_executable 只会用默认 profile，构造不会报错。
    """
    proj = tmp_path / "proj"
    _write_min_problem(proj)
    with pytest.raises(ComposeError):
        RuntimeSession(proj, ["Q001"], competition="no-such-competition")


def test_session_without_competition_preserves_behavior(tmp_path):
    """无 competition 入参 → 走既有路径（默认 cp-cumcm，构造成功）。"""
    proj = tmp_path / "proj"
    _write_min_problem(proj)
    s = RuntimeSession(proj, ["Q001"])
    assert s.executor_impl.candidate_arena.pack.pack_id == "cp-cumcm"
