# -*- coding: utf-8 -*-
"""P3-2 确定性指标：用机械检查替代盲评维度（The Agent Is Not The State）。

替代目标（ROADMAP P3-2）：
- L4.5 Claim-Evidence map → Evidence Graph 机械遍历（本模块）
  `claim_evidence_coverage()`：每个 claim 是否被真实证据链支撑
  （supports 边 + 证据终端的 provenance/数值），覆盖率与缺口列表。
- L4.1 Baseline comparison → execution_result 数值确定性比较（本模块）
  `baseline_comparison()`：两个执行结果（模型 vs 基线）的数值相对
  差异/改进，全部由数值决定，无 LLM 参与。

设计原则：
- 只读 Evidence Graph + Artifact Registry（不写、不推断）。
- 证据"真实"判定是机械的：execution_result 必须有 execution_token
  或 legacy_unverified 显式声明；verification_result 必须有数值字段；
  supports 边优先带 exec_ref（边级 provenance）。
- 任何缺失 → 记为 unsupported / missing，绝不默认通过。
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------- L4.5

def claim_evidence_coverage(graph) -> dict[str, Any]:
    """遍历 Evidence Graph，机械报告 claim 的证据支撑覆盖率。

    Args:
        graph: EvidenceGraph 实例（已连接 registry）。

    Returns:
        {
          total_claims, supported_claims, coverage_ratio,
          unsupported: [claim_id, ...],
          evidence_types: {result: n, verification_result: n,
                           execution_result: n},
          with_exec_ref: n,   # supports 边携带 exec_ref（边级 provenance）
        }
    """
    claims = [a for a in graph.registry.all()
              if getattr(a, "type", None) == "claim"]
    total = len(claims)
    supported: list[str] = []
    unsupported: list[str] = []
    evidence_types: dict[str, int] = {}
    with_exec_ref = 0

    for claim in claims:
        in_edges = [e for e in graph.in_edges(claim.artifact_id)
                    if e["relation"] == "supports"]
        if not in_edges:
            unsupported.append(claim.artifact_id)
            continue
        # 至少一条 supports 边指向"真实"证据终端才算 supported
        ok = False
        for e in in_edges:
            src = e["from"]
            if e.get("exec_ref"):
                with_exec_ref += 1
            art = graph.registry.get(src)
            if not art:
                continue
            dtype = art.type
            evidence_types[dtype] = evidence_types.get(dtype, 0) + 1
            if _evidence_is_real(art):
                ok = True
                break
        if ok:
            supported.append(claim.artifact_id)
        else:
            unsupported.append(claim.artifact_id)

    return {
        "total_claims": total,
        "supported_claims": len(supported),
        "coverage_ratio": (len(supported) / total) if total else 1.0,
        "unsupported": unsupported,
        "evidence_types": evidence_types,
        "with_exec_ref": with_exec_ref,
    }


def _evidence_is_real(art) -> bool:
    """证据终端是否真实（机械判定，LLM-free）。

    - execution_result: 必须带 execution_token 或 legacy_unverified=True
      （P0-3 execution_auth 语义；无 token 的 success EXEC 不可信）。
    - verification_result: 必须带 status 且（mathematical_valid /
      constraint_violation_max / variable_domain_violation 等数值字段）。
    - result: 必须带数值 outputs 且由 EXEC produces（经 registry 无法
      直接看边——由调用方保证；此处只查 data 结构）。
    """
    data = art.data or {}
    t = art.type
    if t == "execution_result":
        if data.get("execution_token"):
            return True
        return bool(data.get("legacy_unverified"))
    if t == "verification_result":
        status = data.get("status")
        numeric = any(k in data for k in (
            "mathematical_valid", "constraint_violation_max",
            "variable_domain_violation", "residual", "passed"))
        return status in ("passed", "failed") and numeric
    if t == "result":
        outputs = data.get("outputs")
        return isinstance(outputs, dict) and len(outputs) > 0
    # 其他类型（model/decision 等）不作为 evidence 终端
    return False


# ---------------------------------------------------------------- L4.1

def baseline_comparison(outputs_a: dict, outputs_b: dict,
                        keys: list[str] | None = None,
                        tolerance: float = 1e-9) -> dict[str, Any]:
    """两个执行结果（模型 vs 基线）的确定性数值比较。

    - 只在两端都存在的数值 key 上比较（缺失 key 不进比较并列出）。
    - 相对差异 = |a-b| / max(|a|,|b|,eps)；两 key 相对差异 ≤ tolerance
      视为"无实质差异"。
    - 输出 better: "a" / "b" / "tie" / "incomparable"（按目标方向：
      objective_less_is_better 可翻转）。

    Args:
        outputs_a: 模型 A 的 execution outputs（dict of 数值/可数值化）。
        outputs_b: 模型 B（基线）的 execution outputs。
        keys: 要比较的数值 key；缺省取两端共有数值 key 全比。
        tolerance: 相对差异阈值。
    """
    eps = 1e-12
    a = {k: v for k, v in (outputs_a or {}).items() if _is_num(v)}
    b = {k: v for k, v in (outputs_b or {}).items() if _is_num(v)}
    if keys is None:
        keys = sorted(set(a) & set(b))
    else:
        keys = [k for k in keys if k in a and k in b]

    compared = []
    for k in keys:
        va, vb = float(a[k]), float(b[k])
        denom = max(abs(va), abs(vb), eps)
        rel = abs(va - vb) / denom
        compared.append({"key": k, "a": va, "b": vb,
                         "rel_diff": round(rel, 8),
                         "same_within_tolerance": rel <= tolerance})
    if not compared:
        return {"compared_keys": 0, "better": "incomparable",
                "note": "两端无共有数值 key", "missing_in_a": list(set(keys) - set(a)),
                "missing_in_b": list(set(keys) - set(b))}

    max_rel = max(c["rel_diff"] for c in compared)
    mean_rel = sum(c["rel_diff"] for c in compared) / len(compared)
    return {
        "compared_keys": len(compared),
        "max_rel_diff": round(max_rel, 8),
        "mean_rel_diff": round(mean_rel, 8),
        "better": "tie" if max_rel <= tolerance else "different",
        "detail": compared,
    }


def _is_num(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False
