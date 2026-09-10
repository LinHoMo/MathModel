# -*- coding: utf-8 -*-
"""内置最小 Reference Constructor（P2-2 边界：benchmark baseline /
regression / demo；非 LLM，非核心能力）。

从内置参数化模型模板构造 ConstructionBundle——K004 的 M/M/c 模板即
参考实现模式。用于：
- Constructor-independent benchmark 的"Reference Constructor"对照臂；
- 本地回归/demo（不依赖外部 Agent）；
- 受控实验（错误注入、revision 演示）。

模板 = 数学建模模板（可复用知识资产），不是 LLM 输出；产出必须满足
MODEL_IR 契约 + def solve(inputs) ABI。
"""

from __future__ import annotations

from typing import Any

from ..protocol import ConstructionBundle, ConstructorAdapter


class ReferenceConstructor(ConstructorAdapter):
    """从注册的模板字典构造 bundle（模板由调用方提供，adapter 只装配）。"""

    name = "reference"
    capability = "C5"   # 支持按 revision 请求产出 M2（模板参数替换）

    def __init__(self, templates: dict[str, Any] | None = None) -> None:
        # templates: {question: {"model_ir": dict, "code": str,
        #                        "output_mapping": dict, ...}}
        self.templates = templates or {}

    def describe(self) -> dict:
        return {"name": self.name, "capability": self.capability,
                "mode": "builtin-template",
                "template_questions": sorted(self.templates)}

    def construct(self, problem: dict,
                  context: dict | None = None) -> ConstructionBundle:
        q = problem.get("question") or problem.get("question_id") or "Q001"
        if q not in self.templates:
            raise KeyError(
                f"ReferenceConstructor 无 {q} 的模板（可选: "
                f"{sorted(self.templates)}）")
        t = self.templates[q]
        revision_of = ((context or {}).get("revision_of")
                       or t.get("revision_of"))
        return ConstructionBundle(
            question=q, model_ir=dict(t.get("model_ir") or {}),
            code=t.get("code") or "",
            output_mapping=dict(t.get("output_mapping") or {}),
            validation_spec=dict(t.get("validation_spec") or {}),
            revision_of=revision_of,
            reasoning_metadata={"adapter": self.name,
                                "template": True,
                                "revision": bool(revision_of)},
            constructor=self.name)
