# -*- coding: utf-8 -*-
"""Engine Validator Hook（P0-3 启用）。

engine._post_execute 在节点 PASS 后先过 validator（返回非空字符串 = 判 FAIL）。
本模块提供通用一致性 validator：handler 声称已登记的产物/证据必须真实存在
于 registry——节点不能"自己说完成就算完成"（The Agent Is Not The State）。

LLM-free：纯机械复核，不判断内容优劣。
"""

from __future__ import annotations


def evidence_consistency_validator(registry, graph=None):
    """返回 validator(node_id, result) -> str | None。

    检查：
    - outputs.artifacts 中每个 id 必须能 registry.get 到（防 handler 谎报产物）；
    - outputs.evidence 中每条 {from, relation, to} 的 from/to 必须真实存在
      （防伪造 evidence 边端点）。
    任何一项不满足 → 返回失败原因（engine 将其转 FAIL，走统一失败语义）。
    """

    def _has(aid: str) -> bool:
        """registry.get 对缺失 id 抛 ArtifactNotFound——安全判定存在性。"""
        try:
            return registry.get(aid) is not None
        except Exception:
            return False

    def validate(node_id: str, result) -> str:
        if getattr(result, "status", None) != "pass":
            return ""
        out = result.outputs or {}
        for aid in out.get("artifacts") or []:
            if not aid:
                continue
            if not _has(aid):
                return f"节点 {node_id} 声称的 artifact 不存在: {aid}"
        for ev in out.get("evidence") or []:
            if not isinstance(ev, dict):
                return f"节点 {node_id} evidence 条目非对象: {ev!r}"
            for k in ("from", "to"):
                v = ev.get(k)
                if v and not _has(v):
                    return f"节点 {node_id} evidence 端点不存在: {k}={v}"
        return ""

    return validate


def build_engine_validators(registry, graph=None, node_types=None):
    """按 node.type 注册统一 validator（engine 按 node_id / node.type 两级查表）。

    node_types：NODE_TYPES 迭代；None 时调用方需保证全类型覆盖。
    """
    fn = evidence_consistency_validator(registry, graph)
    return {t: fn for t in (node_types or ())}
