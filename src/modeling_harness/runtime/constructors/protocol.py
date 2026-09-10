# -*- coding: utf-8 -*-
"""Constructor Adapter Protocol（P1-1，audit CORE/OPTIONAL/EXTERNAL 边界）。

LinHoMo Runtime 与外部 Model Constructor（MathModelAgent / Claude Code /
GPT / 人工 / 自研 Reference Constructor）之间的统一接入契约。

核心哲学（The Agent Is Not The State）：
- Constructor 只产出"建模提案"（ConstructionBundle）——MODEL_IR + Code +
  映射 + 验证义务声明；
- Runtime 负责登记 / 校验 / 执行 / fidelity / 数值验证 / 选型 / 修订谱系；
- Constructor 永远没有 execution_result / fidelity / PASS 写权限。

Capability Levels（Constructor 能力分级）：
  C0 text-only          只有自然语言模型描述
  C1 model-description  结构化模型描述（无 schema 契约）
  C2 model-ir           MODEL_IR 契约（三层）
  C3 +code              MODEL_IR + 可执行代码（def solve(inputs) ABI）
  C4 +mapping           + output_mapping（变量→输出 key 显式翻译表）
  C5 revision-capable   支持按诊断/草案产出 M2（revision_of 谱系）

LLM-free：本模块是纯数据契约，不包含任何 LLM 调用。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any

CAPABILITY_LEVELS = ("C0", "C1", "C2", "C3", "C4", "C5")


@dataclass
class ConstructionBundle:
    """外部 Constructor 的标准化产出（一次 construct 调用）。

    字段对齐 RuntimeSession 的注入契约（external_model_irs / external_code /
    output_mappings / validation_specs），handlers 消费同一格式。
    """

    question: str                              # 问题 id（Q001）
    model_ir: dict                             # MODEL_IR（三层：语义/数学/计算）
    code: str = ""                             # def solve(inputs) -> outputs
    output_mapping: dict = field(default_factory=dict)   # 变量→输出 key 翻译表
    validation_spec: dict = field(default_factory=dict)  # 验证义务（C8 消费）
    revision_of: str | None = None             # M2 的修订谱系（M1 的 model_id/artifact id）
    reasoning_metadata: dict = field(default_factory=dict)  # 推理元数据（可审计，非事实）
    constructor: str = "unknown"               # 产出者标识（MathModelAgent/...）

    # ------------------------------------------------ 序列化

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "ConstructionBundle":
        return cls(
            question=d.get("question", ""),
            model_ir=d.get("model_ir") or {},
            code=d.get("code") or "",
            output_mapping=dict(d.get("output_mapping") or {}),
            validation_spec=dict(d.get("validation_spec") or {}),
            revision_of=d.get("revision_of"),
            reasoning_metadata=dict(d.get("reasoning_metadata") or {}),
            constructor=d.get("constructor") or "unknown",
        )

    @classmethod
    def from_json(cls, s: str) -> "ConstructionBundle":
        return cls.from_dict(json.loads(s))

    @property
    def capability_level(self) -> str:
        """由字段推断 Constructor 能力级别（C0-C5，最弱满足）。"""
        if not self.model_ir:
            return "C0"
        if not self.code:
            return "C2"
        if not self.output_mapping:
            return "C3"
        if not self.validation_spec:
            return "C4"
        return "C5"


class ConstructorAdapter(ABC):
    """Constructor 适配器基类——把具体外部 Agent 包装成统一 construct 接口。

    子类只需实现 construct()；Runtime 侧只依赖 ConstructionBundle，
    不依赖具体 Constructor 的实现细节。
    """

    name: str = "base"
    capability: str = "C0"

    def describe(self) -> dict:
        """适配器元数据（注册表展示/实验记录用）。"""
        return {"name": self.name, "capability": self.capability}

    @abstractmethod
    def construct(self, problem: dict, context: dict | None = None) -> ConstructionBundle:
        """对一道题产出建模提案（MODEL_IR + Code + 映射 + 义务）。

        problem: {question, statement, ...}（Problem Representation）
        context: {diagnosis, revision_draft, prior_bundles, ...}（可选——
                 revision 场景传失败诊断与草案，让 Constructor 产出 M2）
        """
        raise NotImplementedError
