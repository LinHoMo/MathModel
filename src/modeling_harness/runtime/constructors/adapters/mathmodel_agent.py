# -*- coding: utf-8 -*-
"""MathModelAgent 适配器（P2-2，CORE/EXTERNAL 边界：Worker/External Solver/
Reference Baseline/Demo，非 Runtime 信任核心）。

接入模式（如实标注）：
1. **目录加载（可用）**：MMA 在外部运行后把建模产物写入目录
   （model_ir.json / code.py / output_mapping.json / specs.json），
   本 adapter 读取并包装为 ConstructionBundle——目录由用户/调度提供。
2. **CLI/API 通道（未配置）**：若检测到 `mathmodel-agent` 可执行或
   `MATHMODEL_AGENT_API` 环境变量，可扩展；未配置时 construct()
   抛 ConstructorNotConfigured（禁止 fallback/伪造）。

LLM-free：本模块不调用 LLM，只做产物契约读取。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..protocol import ConstructionBundle, ConstructorAdapter


class ConstructorNotConfigured(RuntimeError):
    """外部 Constructor 通道未配置（如实报错，不伪装可用）。"""


class MathModelAgentAdapter(ConstructorAdapter):
    name = "mathmodel-agent"
    capability = "C4"   # MODEL_IR + code + mapping 可加载；C5 取决于是否带 revision

    def __init__(self, source_dir: str | Path | None = None) -> None:
        self.source_dir = Path(source_dir) if source_dir else None

    def describe(self) -> dict:
        return {
            "name": self.name, "capability": self.capability,
            "mode": ("directory-loading"
                     if self.source_dir and self.source_dir.exists() else
                     "unconfigured"),
            "source_dir": str(self.source_dir) if self.source_dir else None,
            "note": "MMA 外部运行产物目录加载；CLI/API 通道未配置",
        }

    def construct(self, problem: dict,
                  context: dict | None = None) -> ConstructionBundle:
        if self.source_dir is None or not self.source_dir.exists():
            raise ConstructorNotConfigured(
                "MathModelAgentAdapter 未配置产物目录（source_dir）。"
                "请先在外部运行 MMA 并把产物目录传给本 adapter；"
                "禁止伪造 bundle。")
        q = problem.get("question") or problem.get("question_id") or "Q001"
        src = self.source_dir
        mir_f, code_f, om_f, spec_f = (
            src / "model_ir.json", src / "code.py",
            src / "output_mapping.json", src / "specs.json")
        if not (mir_f.exists() and code_f.exists()):
            raise ConstructorNotConfigured(
                f"MMA 产物目录缺契约文件（需要 model_ir.json + code.py）: {src}")
        model_ir = json.loads(mir_f.read_text(encoding="utf-8"))
        code = code_f.read_text(encoding="utf-8")
        output_mapping = (json.loads(om_f.read_text(encoding="utf-8"))
                          if om_f.exists() else {})
        validation_spec = (json.loads(spec_f.read_text(encoding="utf-8"))
                           if spec_f.exists() else {})
        revision_of = (model_ir.get("revision_of")
                       or (context or {}).get("revision_of"))
        return ConstructionBundle(
            question=q, model_ir=model_ir, code=code,
            output_mapping=output_mapping, validation_spec=validation_spec,
            revision_of=revision_of,
            reasoning_metadata={
                "adapter": self.name, "source_dir": str(src),
                "mode": "directory-loading"},
            constructor=self.name)
