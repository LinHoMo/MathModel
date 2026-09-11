# -*- coding: utf-8 -*-
"""Model Comparison（audit FIX-6.4 / P2-08）：M1/M2 基于机械证据比较。

从两模型的活跃 VR artifact 提取指标（mathematical_valid / 通过检查数 /
constraint_violation_max / robustness），输出结构化比较结果与 accept/reject
建议。全部确定性，零 LLM。
"""

from __future__ import annotations

from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _vr_metrics(registry, mir_id: str) -> dict | None:
    """取模型最新活跃 VR 指标；无 VR 返回 None（证据缺失不比较）。"""
    # P0-4：删除无效循环（for 内仅 continue，无任何逻辑）——
    # VR 由 execution_id 关联，需按模型反查（_resolve_vr_for_model）
    # 反向关联：VR.data 不含 model_id 时，通过 verified_by 无法反查；
    # 用 execution → implemented_by → model 谱系解析模型绑定。
    return _resolve_vr_for_model(registry, mir_id)


def _resolve_vr_for_model(registry, mir_id: str) -> dict | None:
    """model_ir → implemented_by → code → executed_by → execution → verified_by → VR。"""
    for code in registry.list_by_type("code"):
        cdata = code.data or {}
        if cdata.get("model_id") == mir_id or mir_id in str(
                cdata.get("implementation_of", "")):
            for ex in registry.list_by_type("execution_result"):
                xdata = ex.data or {}
                if xdata.get("code_hash") == cdata.get("code_hash") \
                        or (xdata.get("model_id") == mir_id):
                    for vr in registry.list_by_type("verification_result"):
                        vdata = vr.data or {}
                        if vdata.get("execution_id") == ex.artifact_id \
                                or vdata.get("evidence_refs", []) == [
                                    ex.artifact_id]:
                            return _metrics(vdata)
                    # 兼容：execution 无 VR 时返回执行证据
                    if xdata.get("status") != "success":
                        return {"valid": False, "reason": "execution_failed"}
    return None


def _metrics(vdata: dict) -> dict:
    checks = vdata.get("checks") or []
    passed = sum(1 for c in checks if c.get("passed"))
    return {
        "valid": vdata.get("status") == "passed",
        "checks_passed": passed,
        "checks_total": len(checks),
        "constraint_violation_max": vdata.get("constraint_violation_max"),
        "robustness": vdata.get("robustness"),
        "execution_valid": vdata.get("execution_valid"),
        # ADR-0013：模型选择必须以目标函数值为首要依据，验证检查数只是回退项。
        "objective_value": vdata.get("objective_value"),
        "objective_direction": vdata.get("objective_direction") or "minimize",
    }


def compare_models(registry, mir1_id: str, mir2_id: str) -> dict:
    """比较 M1/M2（活跃 VR 机械证据），输出 accept/reject 建议。"""
    m1 = _resolve_vr_for_model(registry, mir1_id)
    m2 = _resolve_vr_for_model(registry, mir2_id)
    if m1 is None or m2 is None:
        return {
            "comparison_id": f"CMP-{mir1_id}-{mir2_id}",
            "better_model": "INCONCLUSIVE",
            "reasoning": "证据缺失：M1/M2 至少一方无活跃 VR 可比较",
            "deltas": {}, "evidence_refs": [],
            "recommendation": "pending",
            "created_at": _now(),
        }
    deltas = {
        "valid": m2.get("valid") - m1.get("valid"),
        "checks_passed": (m2.get("checks_passed") or 0)
                         - (m1.get("checks_passed") or 0),
        "robustness": ((m2.get("robustness") or 0.0)
                       - (m1.get("robustness") or 0.0)),
    }
    cv1 = m1.get("constraint_violation_max") or 0.0
    cv2 = m2.get("constraint_violation_max") or 0.0
    deltas["constraint_violation_max"] = cv2 - cv1
    if m2.get("valid") and not m1.get("valid"):
        better, rec = mir2_id, "accept"
        reason = f"{mir2_id} 通过验证（M1 failed）"
    elif m1.get("valid") and not m2.get("valid"):
        better, rec = mir1_id, "reject"
        reason = f"{mir2_id} 验证失败（M1 保持有效）"
    elif m1.get("valid") and m2.get("valid"):
        # ADR-0013：两者均通过验证时，**先比目标函数值**，不得用验证检查数代偿
        # （那会把「验证做得更细的模型」误判为更优，而不管其目标值是否更好）。
        o1, o2 = m1.get("objective_value"), m2.get("objective_value")
        if o1 is None or o2 is None:
            if (m2.get("checks_passed") or 0) > (m1.get("checks_passed") or 0):
                better, rec = mir2_id, "accept"
                reason = (f"{mir2_id} 通过检查数更高"
                          f"（{m2.get('checks_passed')} vs "
                          f"{m1.get('checks_passed')}）；"
                          f"目标值不可得，退化为按验证质量比较（ADR-0013 回退）")
            else:
                better, rec = mir1_id, "keep"
                reason = "两者均通过；目标值不可得，验证质量亦无优势"
            deltas["objective_fallback"] = True
        else:
            o1, o2 = float(o1), float(o2)
            direction = m1.get("objective_direction") or "minimize"
            deltas["objective_value"] = o2 - o1
            if abs(o2 - o1) <= 1e-12 * max(abs(o1), abs(o2), 1.0):
                better, rec = mir1_id, "keep"
                reason = f"两者目标值无实质差异（{o1:g} vs {o2:g}）；M1 保持"
            elif (o2 < o1) if direction == "minimize" else (o2 > o1):
                better, rec = mir2_id, "accept"
                reason = f"{mir2_id} 目标值更优（{o2:g} vs {o1:g}，{direction}）"
            else:
                better, rec = mir1_id, "keep"
                reason = f"{mir1_id} 目标值更优（{o1:g} vs {o2:g}，{direction}）"
    else:
        better, rec = "NONE", "reject"
        reason = "两者均未通过验证"
    return {
        "comparison_id": f"CMP-{mir1_id}-{mir2_id}",
        "better_model": better,
        "recommendation": rec,
        "reasoning": reason,
        "deltas": deltas,
        "evidence_refs": [],
        "created_at": _now(),
    }
