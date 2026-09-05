#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime Contracts（P7 Contract Freeze）—— 语义不变量的单一代码真源。

本模块是 V3 Runtime 的**契约冻结层**：生命周期语义、可复用性、可入证性、
NodeResult 结构全部在此定义，handlers / gate / critic / tools 一律 import
这里的谓词，禁止各自内联元组（P6 修的 E1/E2/E3/E4/N2 口径分裂即由此而来）。

配套文档: docs/architecture/RUNTIME_CONTRACTS.md（验收标准 A–K 映射）
"""

from __future__ import annotations

# ============================================================
# 1. Artifact Lifecycle Contract
# ============================================================
# 正向: draft → active → validated → published
# 终态: invalidated（错误/失效）/ superseded（被新谱系替代）/ deprecated（人工废弃）
# 权威实现: core/runtime/artifacts/lifecycle.py（状态机，fail-closed）

TERMINAL_STATUSES = frozenset({"invalidated", "superseded", "deprecated"})
ACTIVE_STATUSES = frozenset({"draft", "active", "validated", "published"})

# 生命周期语义表（P7 冻结，变更须改此处 + lifecycle.py + RUNTIME_CONTRACTS.md）:
#
#   状态         | 可复用 | 可进证据图 | 可支撑 Claim | 可进论文投影 | 审计保留
#   draft        |  否    |    边可挂   |      否      |     否       |    是
#   active       |  是    |    是      |      是      |     是       |    是
#   validated    |  是    |    是      |      是      |     是       |    是
#   published    |  是    |    是      |      是      |     是       |    是
#   blocked      |  否    |    是      |      否      |     否       |    是
#   superseded   |  否    |  否(剪边)  |      否      |     否       |    是
#   invalidated  |  否    |  否(剪边)  |      否      |     否       |    是
#   deprecated   |  否    |  否(剪边)  |      否      |     否       |    是


def is_reusable(status: str) -> bool:
    """终态产物不可复用（P6 不变量：Terminal artifacts are immutable and
    non-reusable）。handler 复用判断一律用本谓词，禁止手写 status 元组。"""
    return status in {"active", "validated", "published"}


def is_terminal(status: str) -> bool:
    return status in TERMINAL_STATUSES


def can_support_claim(status: str) -> bool:
    """该状态的产物能否作为 claim 的支撑证据。"""
    return status in {"active", "validated", "published"}


def can_enter_paper(status: str) -> bool:
    """该状态的产物能否进入论文投影（narrative / outline / section）。"""
    return status in {"active", "validated", "published"}


def requires_reuse_check(fn):
    """装饰器：标注该 handler/函数已按契约做终态复用检查（文档用，无行为）。"""
    return fn


# ============================================================
# 2. NodeResult Contract（节点执行器输出契约）
# ============================================================
# executor(node_id, ctx) -> NodeResult（core/runtime/execution/engine.py）
# NodeResult.outputs 允许的键与类型（多余键 = 契约违约）:

NODE_RESULT_OUTPUT_KEYS = {
    "artifacts": list,    # 产出说明（默认 handlers 直接写 Registry，此键留作 LLM 节点）
    "evidence": list,     # [{from, relation, to}] —— ID 必须已注册，relation 合法
    "metrics": dict,      # 节点指标（latency_ms 等，审计用）
    "context": dict,      # 跨节点接力上下文（shared 状态镜像，只读约定）
}

EVIDENCE_RELATION_KEYS = {"from", "relation", "to"}


def validate_node_result_outputs(outputs: dict) -> list[str]:
    """校验 NodeResult.outputs 契约，返回问题列表（空 = 合法）。"""
    problems = []
    if outputs is None:
        return problems
    if not isinstance(outputs, dict):
        return [f"outputs 必须是 dict，实际 {type(outputs).__name__}"]
    for key, value in outputs.items():
        if key not in NODE_RESULT_OUTPUT_KEYS:
            problems.append(f"outputs 含未定义键: {key!r}"
                            f"（合法: {sorted(NODE_RESULT_OUTPUT_KEYS)}）")
            continue
        expected = NODE_RESULT_OUTPUT_KEYS[key]
        if not isinstance(value, expected):
            problems.append(f"outputs.{key} 应为 {expected.__name__}，"
                            f"实际 {type(value).__name__}")
    for rel in outputs.get("evidence", []) or []:
        if not isinstance(rel, dict):
            problems.append(f"evidence 项应为 dict，实际 {type(rel).__name__}")
            continue
        missing = EVIDENCE_RELATION_KEYS - set(rel)
        if missing:
            problems.append(f"evidence 项缺字段: {sorted(missing)}")
    return problems


# ============================================================
# 3. 执行语义区分（Resume / Retry / Rerun / Recompute）—— P7 冻结
# ============================================================
#
# Resume     继续未完成的执行：恢复 completed/blocked/waiting/retries，
#            已完成节点绝不重复执行（engine.save_progress / WorkflowEngine.load）。
# Retry      同一节点失败后的引擎内自动重试（max_retries 轮，耗尽走 on_fail/阻塞）。
# Rerun      研究者主动要求重新执行：session.rerun(node_id) —— 重置节点及下游，
#            旧谱系显式 superseded（审计保留），新谱系全新 Artifact。
# Recompute  上游证据变化（invalidation）触发的下游重算：session.invalidate() →
#            图传播 → 剪死边 → 按产物类型映射局部重置。与 Rerun 的区别是触发源
#            为证据失效而非人工意志，旧谱系为 invalidated 而非 superseded。


class ContractViolation(RuntimeError):
    """Runtime 契约违约（fail-closed，调用方必须处理而非吞掉）。"""
