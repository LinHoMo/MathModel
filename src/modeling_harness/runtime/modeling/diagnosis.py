# -*- coding: utf-8 -*-
"""Failure Diagnosis（audit FIX-6.1 / P2-04）：从验证结果机械归因失败。

LLM-free 确定性诊断：输入 registry + VR artifact，输出结构化失败诊断
（failed_components / root_cause / suggested_fixes / evidence_refs）。
不推断数值正确性——只从机械证据（checks 失败项 / execution status /
constraint_violation_max）归因失败环节，建议动作可执行、不编造新数值。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class FailureDiagnosis:
    diagnosis_id: str
    model_id: str
    verification_id: str
    execution_id: str
    failed_components: list[str]
    root_cause: str
    suggested_fixes: list[str]
    evidence_refs: list[str]
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def _classify_failure(data: dict) -> tuple[list[str], list[str]]:
    """(failed_components, suggested_fixes)——按检查类型确定性归因。"""
    components: list[str] = []
    fixes: list[str] = []
    status = data.get("status")
    if data.get("execution_valid") is False or status == "invalid":
        components.append("execution")
        tail = str(data.get("stderr", ""))[-200:]
        fixes.append(
            "修正可执行代码（执行失败，stderr 尾部: "
            + (tail or "无") + "）；确认 solve(inputs) ABI 与依赖")
        return components, fixes
    for c in data.get("checks") or []:
        if c.get("passed"):
            continue
        kind = c.get("kind", "")
        name = c.get("name", "?")
        detail = c.get("detail", "")
        if kind == "output_field_exists" or kind == "output_key_exists":
            components.append(f"output_field:{name}")
            fixes.append(f"检查输出字段 {name!r}（{detail}）："
                         "代码必须输出 MODEL_IR 声明的变量/目标")
        elif kind in ("output_range", "output_equals", "output_numeric"):
            components.append(f"numeric:{name}")
            fixes.append(f"数值不符 {name!r}（{detail}）："
                         "检查参数取值/方程系数/求解逻辑")
        else:
            components.append(f"check:{name}")
            fixes.append(f"验证项 {name!r} 未通过（{detail}）")
    cvm = data.get("constraint_violation_max")
    if isinstance(cvm, (int, float)) and cvm > 1e-9:
        components.append("constraint_violation")
        fixes.append(
            f"约束违反最大值 {cvm:.6g}：校对约束参考值/系数"
            "（若违反的是间距守恒，检查 ell_body/ell_head 等参数）")
    return components, fixes


def diagnose_failure(registry, mir_id: str, vr_id: str,
                     exec_id: str | None = None) -> FailureDiagnosis:
    """从 VR artifact 生成结构化失败诊断（不修改任何状态）。"""
    vr = registry.get(vr_id)
    vdata = dict(vr.data or {})
    status = vdata.get("status")
    if status != "failed":
        raise ValueError(
            f"VR {vr_id} status={status}，不可诊断（只有 failed 可诊断）")
    components, fixes = _classify_failure(vdata)
    exec_ref = exec_id or vdata.get("execution_id") or ""
    cause_parts = []
    if not vdata.get("execution_valid", True):
        cause_parts.append("执行层失败")
    if vdata.get("constraint_violation_max"):
        cause_parts.append(f"约束违反（max={vdata['constraint_violation_max']:.6g}）")
    if not vdata.get("mathematical_valid", True):
        cause_parts.append("数值验证未通过")
    root_cause = ("；".join(cause_parts) or "验证未通过") + \
        f"（VR {vr_id}，{len(components)} 个失败组件）"
    return FailureDiagnosis(
        diagnosis_id=f"DIAG-{vr_id}",
        model_id=mir_id,
        verification_id=vr_id,
        execution_id=exec_ref,
        failed_components=components,
        root_cause=root_cause,
        suggested_fixes=fixes,
        evidence_refs=[vr_id] + ([exec_ref] if exec_ref else []),
    )
