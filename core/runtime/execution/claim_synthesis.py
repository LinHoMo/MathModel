"""Claim Synthesis — 由执行事实确定性合成结论（audit FIX-1.4 / P0-06）。

核心原则（LLM-free）：Claim 是 evidence 的投影，不是 Agent 的自我陈述。
`"{qid} 结论"` 占位符不得获得 supports 边；只有基于真实 EXEC outputs /
VR 数值的确定性合成 statement 才可支撑 claim。

本模块不调用任何 LLM；输入均为机械事实（EXEC data / VR data / Result data）。
"""

from __future__ import annotations

from typing import Any


def _fmt_value(v: Any) -> str:
    """把任意数值格式化为可读的短字符串（保留 4 位有效数字）。"""
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, (int, float)):
        if isinstance(v, int):
            return str(v)
        return f"{v:.4g}"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}={_fmt_value(x)}" for k, x in list(v.items())[:3]) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_fmt_value(x) for x in list(v)[:3]) + "]"
    return str(v)[:80]


def synthesize_claim(qid: str, result_art, exec_art=None,
                     vr_art=None) -> str:
    """从真实执行产物确定性合成 claim statement。

    参数:
      qid: Question ID（如 "Q001"）
      result_art: result Artifact（data.outputs 为真实数值快照）
      exec_art:   execution_result Artifact（可为 None）
      vr_art:     verification_result Artifact（可为 None，数值验证证据）

    返回:
      确定性模板生成的 statement 字符串；若没有任何可引用的数值事实，
      返回 ""（调用方应保持 placeholder 并禁止 supports 边）。
    """
    rdata = (result_art.data or {}) if result_art is not None else {}
    outputs = rdata.get("outputs") or rdata.get("value") or {}
    if not isinstance(outputs, dict) or not outputs:
        return ""

    parts: list[str] = [f"{qid} 模型执行产出"]
    # 1) 核心数值：取 outputs 前 3 个键值
    kv = []
    for k, v in list(outputs.items())[:3]:
        kv.append(f"{k}={_fmt_value(v)}")
    if kv:
        parts.append("，".join(kv))

    # 2) 执行事实（EXEC）
    if exec_art is not None:
        xdata = exec_art.data or {}
        status = xdata.get("status")
        if status == "success":
            parts.append("执行成功")
        elif status in ("failed", "timeout", "invalid"):
            parts.append(f"执行失败（{status}）")

    # 3) 数值验证事实（VR）
    if vr_art is not None:
        vdata = vr_art.data or {}
        vstatus = vdata.get("status")
        if vstatus == "passed":
            cvm = vdata.get("constraint_violation_max")
            if cvm is not None:
                parts.append(f"约束违反度={_fmt_value(cvm)}")
            parts.append("数值验证通过")
        elif vstatus in ("failed", "blocked"):
            cvm = vdata.get("constraint_violation_max")
            if cvm is not None:
                parts.append(f"约束违反度={_fmt_value(cvm)}")
            parts.append(f"数值验证未通过（{vstatus}）")

    return "；".join(parts) + "。"
