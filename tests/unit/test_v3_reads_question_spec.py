"""audit FIX-2.5：V3 读取 question_spec.json → ProblemRepresentation。

- 有 spec → problem_repr 含题面内容（background/problems/constraints/data/delivery）
- 格式错误 → 明确报错（非静默回退）
- 无 spec → None（回退 legacy 粗画像）
- orchestrator 运行时 Problem/Question artifact 含题面内容

运行: python -m pytest tests/unit/test_v3_reads_question_spec.py -q
"""

import sys
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.modeling.problem_repr import (
    ProblemRepresentationError,
    load_problem_representation,
)


def test_reads_question_spec(tmp_path):
    inp = tmp_path / "inputs"
    inp.mkdir(parents=True)
    (inp / "question_spec.json").write_text(json.dumps({
        "background": "某资源配置问题",
        "problems": [{"id": "Q001", "title": "资源配置",
                      "description": "在有限产能下最大化利润"}],
        "constraints": [{"id": "C1", "text": "产能上限"}],
        "data": [{"name": "demand", "description": "需求表"}],
        "delivery": [{"type": "paper", "requirement": "论文"}],
    }), encoding="utf-8")
    pr = load_problem_representation(tmp_path)
    assert pr is not None
    assert pr.source == "question_spec"
    assert pr.background == "某资源配置问题"
    assert pr.problems[0]["id"] == "Q001"
    assert pr.constraints[0]["id"] == "C1"
    assert pr.data[0]["name"] == "demand"
    assert pr.delivery[0]["type"] == "paper"


def test_legacy_sub_questions_compat(tmp_path):
    inp = tmp_path / "inputs"
    inp.mkdir(parents=True)
    (inp / "question_spec.json").write_text(json.dumps({
        "sub_questions": [{"id": "Q001", "content": "第一问"}],
        "domain_keywords": ["optimization"],
    }), encoding="utf-8")
    pr = load_problem_representation(tmp_path)
    assert pr.problems[0]["description"] == "第一问"


def test_malformed_spec_raises(tmp_path):
    inp = tmp_path / "inputs"
    inp.mkdir(parents=True)
    (inp / "question_spec.json").write_text("{bad json", encoding="utf-8")
    with pytest.raises(ProblemRepresentationError):
        load_problem_representation(tmp_path)


def test_missing_spec_returns_none(tmp_path):
    assert load_problem_representation(tmp_path) is None
