# -*- coding: utf-8 -*-
"""V3 问题表示层（audit FIX-2.5）：把项目 inputs 的题面/规格解析为
结构化 ProblemRepresentation，供 features 与建模节点使用。

来源单一真源：inputs/question_spec.json（结构化）或 inputs/problem.txt
（纯文本）。两者皆缺 → 返回 None（节点如实处理，禁止回退掩盖）。
格式错误明确报错（禁止静默回退掩盖损坏）。
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
from typing import Any


class ProblemRepresentationError(ValueError):
    """题面规格解析失败。"""


@dataclass
class ProblemRepresentation:
    background: str = ""
    problems: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    data: list[dict[str, Any]] = field(default_factory=list)
    delivery: list[dict[str, Any]] = field(default_factory=list)
    source: str = "question_spec"          # question_spec | problem_txt
    raw_text: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_problem_representation(project_dir: str | Path) -> "ProblemRepresentation | None":
    """读取项目题面规格；缺失返回 None；格式错误抛 ProblemRepresentationError。"""
    base = Path(project_dir) / "inputs"
    spec = base / "question_spec.json"
    text = base / "problem.txt"
    if spec.exists():
        try:
            raw = json.loads(spec.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise ProblemRepresentationError(
                f"question_spec.json 无法解析: {e}") from e
        if not isinstance(raw, dict):
            raise ProblemRepresentationError(
                "question_spec.json 顶层必须是 object")
        problems = raw.get("problems") or [
            {"id": q.get("id", f"Q{i + 1}"), "title": q.get("title", ""),
             "description": q.get("description", q.get("content", ""))}
            for i, q in enumerate(raw.get("sub_questions") or [])
        ]
        if isinstance(raw.get("sub_questions"), list) and not problems:
            problems = [{"id": f"Q{i + 1}", "title": "", "description": ""}
                        for i in range(len(raw["sub_questions"]))]
        return ProblemRepresentation(
            background=str(raw.get("background") or ""),
            problems=problems,
            constraints=list(raw.get("constraints") or []),
            data=list(raw.get("data") or []),
            delivery=list(raw.get("delivery") or []),
            source="question_spec",
            raw_text=str(raw.get("raw_text") or ""),
        )
    if text.exists():
        body = text.read_text(encoding="utf-8")
        return ProblemRepresentation(background=body, source="problem_txt",
                                     raw_text=body)
    return None
