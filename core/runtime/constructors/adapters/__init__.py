# -*- coding: utf-8 -*-
"""外部 Constructor 适配器包（P2-2 / P3-3）。

- MathModelAgentAdapter：从 MMA 产物目录加载（真实可用）；CLI/API 通道
  标注未配置（不假装可调）。
- PiAdapter：从推理产物 JSON/目录加载；API 密钥通道标注未配置。
- ReferenceConstructor：内置最小参考 Constructor（模板化模型，
  benchmark baseline / regression / demo 用；非 LLM）。

核心纪律（The Agent Is Not The State + infra 不冒充 capability）：
- 任何 adapter 只产出 ConstructionBundle（建模提案），永无
  execution_result / fidelity / PASS 写权限；
- 外部通道未配置时 construct() 抛 ConstructorNotConfigured（明确错误，
  禁止 fallback 到伪造产物）。
"""
