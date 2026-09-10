# -*- coding: utf-8 -*-
"""Revision Proposal（audit FIX-6.2 / P2-05）：基于诊断生成 M2 草案框架。

LLM-free 确定性：不编造新数值——真正的 M2 由外部 Model Constructor 提供
（LLM-free 边界）。本模块输出**修订草案框架**：指明需改动的组件、失败
原因、建议动作，并把 M2 草案（外部修订后）标记 changed_components 与
revision lineage（revision_of / modeling_trace 追加修订步骤）。
"""

from __future__ import annotations

from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_revision_draft(mir_data: dict, diagnosis: dict,
                         new_model_id: str) -> dict:
    """从 M1 结构 + 诊断生成 M2 修订草案（结构继承 + 变更标注）。

    - 继承 M1 全部字段（外部注入者在此基础上修订）
    - changed_components：从诊断 failed_components 映射到 M1 结构组件
      （parameter / constraint / equation / variable / solver / code）
    - modeling_trace 按 MODEL_IR 契约（object：trace_version /
      generation_order / version_history）追加修订记录——generation_order 增加
      revision_draft 步骤，version_history 增加 M2 版本条目（来源 = 诊断，
      可审计）
    - 不修改任何数值——无伪造 new value
    """
    draft = dict(mir_data)
    draft["model_id"] = new_model_id
    changed = _map_changes(mir_data, diagnosis)
    trace = draft.get("modeling_trace")
    if isinstance(trace, dict):
        # MODEL_IR 契约形态（schema modeling_trace object）：按子结构追加
        trace = dict(trace)
        gen_order = [dict(e) for e in (trace.get("generation_order") or [])]
        gen_order.append({
            "node_id": "revision_draft",
            "order_index": len(gen_order),
            "timestamp": _now(),
        })
        trace["generation_order"] = gen_order
        hist = [dict(e) for e in (trace.get("version_history") or [])]
        hist.append({
            "version_number": len(hist) + 1,
            "commit_hash": new_model_id,
            "changed_nodes": [c.get("component") for c in changed
                              if c.get("component")],
            "change_summary": f"revision_draft from "
                              f"{mir_data.get('model_id')} "
                              f"(diagnosis={diagnosis.get('diagnosis_id')})",
            "timestamp": _now(),
        })
        trace["version_history"] = hist
    else:
        # 历史字符串列表形态（外部 Constructor 旧产物）：保持兼容可读，
        # 追加 revision 步骤条目（以 dict 记录，不破坏旧元素）
        trace = list(trace or [])
        trace.append({
            "step": "revision_draft",
            "note": f"从 {mir_data.get('model_id')} 修订（diagnosis="
                    f"{diagnosis.get('diagnosis_id')}）",
            "changed_components": changed,
            "at": _now(),
        })
    draft["modeling_trace"] = trace
    draft["changed_components"] = changed
    return draft


def _map_changes(mir_data: dict, diagnosis: dict) -> list[dict]:
    """failed_components → M1 结构组件映射（确定性，尽力而为）。"""
    changes: list[dict] = []
    params = {p.get("symbol") or p.get("parameter_id"): p
              for p in mir_data.get("parameters") or []}
    for comp in diagnosis.get("failed_components") or []:
        if comp.startswith("constraint_violation"):
            changes.append({
                "component": "constraints",
                "issue": "约束数值违反",
                "action": "校对约束参考值/系数（外部 Model Constructor 修订）",
            })
            continue
        if comp.startswith("numeric:"):
            name = comp[len("numeric:"):]
            hit = params.get(name)
            if hit:
                changes.append({
                    "component": f"parameter.{hit.get('parameter_id')}",
                    "issue": f"数值不符（{name}）",
                    "action": "校对参数取值与来源（外部 Model Constructor 修订）",
                })
            else:
                changes.append({
                    "component": "equations/objective",
                    "issue": f"数值不符（{name}）",
                    "action": "校对方程/目标表达式（外部 Model Constructor 修订）",
                })
            continue
        if comp.startswith("output_field:"):
            changes.append({
                "component": "code/output",
                "issue": f"输出字段缺失（{comp}）",
                "action": "修正代码输出以匹配 MODEL_IR 声明（外部修订）",
            })
            continue
        changes.append({
            "component": comp,
            "issue": "验证未通过",
            "action": "定位并修订（外部 Model Constructor）",
        })
    return changes
