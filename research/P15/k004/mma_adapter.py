# -*- coding: utf-8 -*-
"""P2-1: MathModelAgent Adapter（外部 Agent 集成点，不 fork）。

通过 P1-1 ConstructorAdapter 协议接入 jihe520/MathModelAgent：
外部 Agent 产出 ConstructionBundle（MODEL_IR + code），Runtime 负责
执行/验证/谱系。本文件提供适配器契约与执行方案；实际调用由
MathModelAgent 的运行入口（CLI/HTTP）提供，运行时按需装配。

契约要点（The Agent Is Not The State）：
- Agent 只写 MODEL_IR/code/reasoning；execution_result/fidelity/PASS
  由 LinHoMo Runtime 机械产生。
- Agent 输出若无 MODEL_IR（仅自然语言/代码），按 capability 降级
  C1/C3 接入；Runtime 侧以 fidelity/验证裁决。
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from modeling_harness.runtime.constructors.protocol import ConstructorAdapter, ConstructionBundle


class MathModelAgentAdapter(ConstructorAdapter):
    """外部 MathModelAgent 适配器（经 P1-1 协议接入）。

    装配方式：提供 `mma_entry`（MathModelAgent 仓库入口，如
    `python -m agent.main`）与工作目录。construct() 调外部 Agent
    产出 JSON（ConstructionBundle 兼容格式），解析为 bundle。
    """

    name = "mma"
    capability = "C5"

    def __init__(self, entry: str | None = None,
                 workdir: str | Path | None = None) -> None:
        self.entry = entry or "python -m agent.main"
        self.workdir = Path(workdir) if workdir else None

    def construct(self, problem: dict,
                  context: dict | None = None) -> ConstructionBundle:
        """调用外部 MathModelAgent 产出 ConstructionBundle。

        外部 Agent 若未安装/不可用 → 抛 ConstructorError（由上层
        决策回退 ref/gen Constructor；K004 设计允许 Constructor 替换）。
        """
        if shutil.which(self.entry.split()[0]) is None and self.workdir is None:
            from modeling_harness.runtime.constructors.registry import ConstructorError
            raise ConstructorError(
                f"MathModelAgent 未装配（entry={self.entry!r}）——"
                "这是外部集成点，装配后自动生效")

        # 外部调用协议：把 problem 序列化给 Agent，Agent 返回
        # ConstructionBundle JSON（to_json 格式兼容）。
        payload = json.dumps({"problem": problem, "context": context or {}},
                             ensure_ascii=False)
        cmd = f"{self.entry} construct"
        proc = subprocess.run(
            cmd, shell=True, input=payload, capture_output=True,
            text=True, timeout=300, cwd=str(self.workdir) if self.workdir else None)
        if proc.returncode != 0:
            from modeling_harness.runtime.constructors.registry import ConstructorError
            raise ConstructorError(
                f"MathModelAgent 调用失败: {proc.stderr[:300]}")
        return ConstructionBundle.from_json(proc.stdout)


import json  # noqa: E402  (module-level import for clarity)
