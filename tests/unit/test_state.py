"""state.py 状态机回归测试。

覆盖两个历史 bug：
1. sync 间隙定位 —— 产物反推时因重复/目录产物导致的误判，无法正确定位缺口；
2. advance 乱序跳步 —— 允许跳过串行前置步骤、以及排序时对陈旧条目抛 StopIteration。
"""
import argparse
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.tools.state import (  # noqa: E402
    PIPELINE,
    _artifact_exists,
    _empty_state,
    _first_incomplete,
    _pipeline_index,
    cmd_advance,
    load,
    save,
    sync_from_artifacts,
)


def _project(tmp_path, *artifacts):
    """创建临时项目，写入指定相对路径的产物文件，返回项目路径。"""
    proj = tmp_path / "p"
    (proj / "work").mkdir(parents=True)
    for rel in artifacts:
        f = proj / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x", encoding="utf-8")
    return proj


def _sync(proj):
    st = _empty_state(str(proj))
    sync_from_artifacts(str(proj), st)
    return st


def _advance(proj, hand, agent, no_gate=True):
    return cmd_advance(
        str(proj),
        argparse.Namespace(hand=hand, agent=agent, output="", no_gate=no_gate),
    )


def _done_set(st):
    return {(c["hand"], c["agent"]) for c in st.get("completed", [])}


# ---------------------------------------------------------------------------
# Bug 1: sync 间隙定位
# ---------------------------------------------------------------------------
def test_sync_locate_middle_gap(tmp_path):
    """缺中间步骤时，sync 应把 current 定位到那条缺口而非按 len 跳位。"""
    proj = _project(
        tmp_path,
        "work/question_spec.json",
        "work/type_classification.json",
        # 缺 literature-searcher
        "work/method_candidates.json",
    )
    st = _sync(proj)
    assert st["current"] == {
        "hand": "modeler", "agent": "literature-searcher", "stage": 1.5,
    }
    assert ("modeler", "literature-searcher") not in _done_set(st)


def test_sync_duplicate_artifact_not_double_counted(tmp_path):
    """main.tex 只应反推 section-writer，不应误推 writer/guardrails-checker。"""
    proj = _project(tmp_path, "paper/main.tex")
    st = _sync(proj)
    agents = _done_set(st)
    assert ("writer", "section-writer") in agents
    assert ("writer", "guardrails-checker") not in agents


def test_sync_empty_directory_not_counted(tmp_path):
    """空目录产物（paper/figures）不应反推 figure-generator 已完成。"""
    proj = _project(tmp_path)
    (proj / "paper" / "figures").mkdir(parents=True)
    st = _sync(proj)
    assert ("writer", "figure-generator") not in _done_set(st)


def test_artifact_exists_directory_requires_content(tmp_path):
    empty_dir = tmp_path / "figures"
    empty_dir.mkdir()
    assert _artifact_exists(empty_dir) is False
    (empty_dir / "f.png").write_text("x")
    assert _artifact_exists(empty_dir) is True


def test_first_incomplete_none_when_all_done():
    completed = [{"hand": h, "agent": a, "stage": s} for h, a, s in PIPELINE]
    assert _first_incomplete(completed) is None


# ---------------------------------------------------------------------------
# Bug 2: advance 乱序跳步
# ---------------------------------------------------------------------------
def test_advance_rejects_out_of_order_skip(tmp_path):
    """当前是 problem-parser 时，advance method-matcher 应被拒绝。"""
    proj = _project(tmp_path)
    save(str(proj), _empty_state(str(proj)))
    assert _advance(proj, "modeler", "method-matcher") == 1
    assert ("modeler", "method-matcher") not in _done_set(load(str(proj)))


def test_advance_allows_parallel_band(tmp_path):
    """评审团 5 个 scorer 同 stage=1，可并行推进（任意顺序）。"""
    proj = _project(tmp_path)
    st = _empty_state(str(proj))
    # 模拟 reviewer 之前的所有步骤已完成
    st["completed"] = [
        {"hand": h, "agent": a, "stage": s}
        for h, a, s in PIPELINE
        if h != "reviewer"
    ]
    save(str(proj), st)
    assert _first_incomplete(st["completed"])["agent"] == "scorer-academic"
    # 同 stage 的 scorer-judge 允许推进
    assert _advance(proj, "reviewer", "scorer-judge") == 0
    # 串行后续 weakness-hunter（stage 2）在 scorer 未齐时被拒绝
    assert _advance(proj, "reviewer", "weakness-hunter") == 1


def test_advance_does_not_crash_on_stale_entry(tmp_path):
    """completed 含陈旧（不在 PIPELINE）条目时，advance 不应抛 StopIteration。"""
    proj = _project(tmp_path)
    st = _empty_state(str(proj))
    st["completed"].append({
        "hand": "modeler", "agent": "old-removed-agent", "stage": 0,
        "timestamp": "", "output": "", "output_hash": "",
    })
    save(str(proj), st)
    assert _advance(proj, "modeler", "problem-parser") == 0


def test_save_recomputes_stale_current(tmp_path):
    """current 与 completed 不一致（如历史 null）时，save 应重新定位缺口。"""
    proj = _project(tmp_path)
    st = _empty_state(str(proj))
    st["current"] = None
    st["completed"] = [{"hand": "modeler", "agent": "problem-parser", "stage": 1}]
    save(str(proj), st)
    assert load(str(proj))["current"] == {
        "hand": "modeler", "agent": "type-classifier", "stage": 2,
    }




# ---------------------------------------------------------------------------
# Bug 3: advance 与 gate 的可信度闭环
# ---------------------------------------------------------------------------
def test_advance_rejects_gate_error_without_registering_completion(tmp_path, monkeypatch):
    """门禁异常时必须 fail-closed，不能把 agent 登记为已完成。"""
    proj = _project(tmp_path)
    save(str(proj), _empty_state(str(proj)))
    monkeypatch.setattr(
        "core.tools.state._run_advance_gate",
        lambda project, hand, agent: (3, {}),
    )

    assert _advance(proj, "modeler", "problem-parser", no_gate=False) == 3
    assert ("modeler", "problem-parser") not in _done_set(load(str(proj)))


def test_advance_allows_soft_gate_and_records_gate_result(tmp_path, monkeypatch):
    """仅软失败允许推进，但完成记录必须保留门禁结果以便审计。"""
    proj = _project(tmp_path)
    save(str(proj), _empty_state(str(proj)))
    summary = {
        "hard_fail_count": 0,
        "soft_fail_count": 1,
        "hard_fail": [],
        "soft_fail": [{"name": "warning", "detail": "可改进"}],
    }
    monkeypatch.setattr(
        "core.tools.state._run_advance_gate",
        lambda project, hand, agent: (1, summary),
    )

    assert _advance(proj, "modeler", "problem-parser", no_gate=False) == 0
    rec = next(c for c in load(str(proj))["completed"]
               if c["agent"] == "problem-parser")
    assert rec["gate"]["exit_code"] == 1
    assert rec["gate"]["soft_fail_count"] == 1
