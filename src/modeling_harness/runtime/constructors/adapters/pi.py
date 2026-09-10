# -*- coding: utf-8 -*-
"""Pi 适配器（P3-3，Optional Backend/Worker/harness 参考，非核心）。

接入模式（如实标注）：
1. **产物目录加载（可用）**：Pi（推理模型）在外部输出目录
   （model_ir.json / code.py / output_mapping.json / specs.json），
   本 adapter 读取并包装——与 MathModelAgentAdapter 同一契约。
2. **API 密钥通道（未配置）**：需要 `PI_API_KEY`/`PI_API_ENDPOINT`
   环境变量；未配置时 construct() 抛 ConstructorNotConfigured。

LLM-free：本模块不调用 LLM；API 通道若启用由外部调用方注入传输层。
"""

from __future__ import annotations

import json
from pathlib import Path

from ..protocol import ConstructionBundle, ConstructorAdapter
from .mathmodel_agent import ConstructorNotConfigured


class PiAdapter(ConstructorAdapter):
    name = "pi"
    capability = "C4"

    def __init__(self, source_dir: str | Path | None = None) -> None:
        self.source_dir = Path(source_dir) if source_dir else None

    def describe(self) -> dict:
        return {
            "name": self.name, "capability": self.capability,
            "mode": ("directory-loading"
                     if self.source_dir and self.source_dir.exists() else
                     "unconfigured"),
            "note": "Pi 外部产物目录加载；API 密钥通道未配置",
        }

    def construct(self, problem: dict,
                  context: dict | None = None) -> ConstructionBundle:
        if self.source_dir is None or not self.source_dir.exists():
            raise ConstructorNotConfigured(
                "PiAdapter 未配置产物目录（source_dir）。"
                "请先在外部运行 Pi 并把产物目录传给本 adapter。")
        q = problem.get("question") or problem.get("question_id") or "Q001"
        src = self.source_dir
        mir_f, code_f, om_f, spec_f = (
            src / "model_ir.json", src / "code.py",
            src / "output_mapping.json", src / "specs.json")
        if not (mir_f.exists() and code_f.exists()):
            raise ConstructorNotConfigured(
                f"Pi 产物目录缺契约文件（model_ir.json + code.py）: {src}")
        return ConstructionBundle(
            question=q,
            model_ir=json.loads(mir_f.read_text(encoding="utf-8")),
            code=code_f.read_text(encoding="utf-8"),
            output_mapping=(json.loads(om_f.read_text(encoding="utf-8"))
                            if om_f.exists() else {}),
            validation_spec=(json.loads(spec_f.read_text(encoding="utf-8"))
                             if spec_f.exists() else {}),
            revision_of=((context or {}).get("revision_of")
                         or json.loads(mir_f.read_text(encoding="utf-8"))
                         .get("revision_of")),
            reasoning_metadata={"adapter": self.name,
                                "source_dir": str(src)},
            constructor=self.name)
