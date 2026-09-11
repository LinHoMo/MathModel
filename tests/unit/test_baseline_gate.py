#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADR-0013 门禁守卫：`baseline` 标签必须伴随真实对照结果，否则 validate 判失败。

这是「静默失效」的门禁侧收口：planner 声明 → handlers 打标签 → 却从未比较。
标签成了声明的同义词。本测试锁死门禁能抓住这个形态。
"""
from __future__ import annotations

import json

from modeling_harness.cli.validate import check_baseline_closure


def _write_registry(root, proj: str, artifacts: list) -> None:
    d = root / "projects" / proj / "state"
    d.mkdir(parents=True, exist_ok=True)
    (d / "registry.json").write_text(
        json.dumps({"artifacts": artifacts}, ensure_ascii=False), encoding="utf-8")


def test_no_projects_dir_passes(tmp_path):
    ok, msg = check_baseline_closure(tmp_path)
    assert ok and "跳过" in msg


def test_artifact_without_baseline_tag_passes(tmp_path):
    _write_registry(tmp_path, "p1", [{"artifact_id": "R1", "tags": ["sensitivity"],
                                      "data": {}}])
    ok, _ = check_baseline_closure(tmp_path)
    assert ok


def test_tagged_but_no_comparison_fails(tmp_path):
    """核心回归：打了 baseline 标签却没有对照结果 ⇒ 判失败。"""
    _write_registry(tmp_path, "p1", [{"artifact_id": "R1", "tags": ["baseline"],
                                      "data": {"outputs": {"t": 1.0}}}])
    ok, msg = check_baseline_closure(tmp_path)
    assert not ok
    assert "R1@p1" in msg
    assert "标签是回执" in msg


def test_tagged_with_missing_status_fails(tmp_path):
    _write_registry(tmp_path, "p1", [{"artifact_id": "R2", "tags": ["baseline"],
                                      "data": {"baseline_comparison":
                                               {"status": "missing"}}}])
    ok, _ = check_baseline_closure(tmp_path)
    assert not ok


def test_tagged_with_real_comparison_passes(tmp_path):
    _write_registry(tmp_path, "p1", [{"artifact_id": "R3", "tags": ["baseline"],
                                      "data": {"baseline_comparison":
                                               {"better": "a", "compared_keys": 1}}}])
    ok, msg = check_baseline_closure(tmp_path)
    assert ok and "闭合" in msg


def test_scans_all_projects(tmp_path):
    _write_registry(tmp_path, "ok_proj", [{"artifact_id": "A", "tags": ["baseline"],
                                           "data": {"baseline_comparison":
                                                    {"better": "tie"}}}])
    _write_registry(tmp_path, "bad_proj", [{"artifact_id": "B", "tags": ["baseline"],
                                            "data": {}}])
    ok, msg = check_baseline_closure(tmp_path)
    assert not ok and "B@bad_proj" in msg
