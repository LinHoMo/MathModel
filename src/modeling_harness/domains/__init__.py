#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical Domain Model —— 概念唯一真源（System Hardening P1）。

12 个规范实体，每个绑定唯一 canonical schema 归属与合法投影名称。
规则：任何新增 schema / 字段 / 文件不得发明本模块之外的近义词；
已有 V2 schema 全部视为 legacy 投影（见 docs/architecture/CANONICAL_DOMAIN.md）。

纯定义层：零行为、零第三方依赖。runtime / validators / 文档均可安全 import。
状态（T-CONF-006 裁定，2026-09-10）：契约层冻结，v1.0 不接入消费者；
接入条件见 domains/README.md（需要 canonical entity 校验时再从此 import）。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 实体注册表：canonical 名 -> (schema 归属, v3 subtype, legacy 投影)
#   schema 归属: "v3/<相对 src/modeling_harness/schemas/v3 的路径>" 或 None（由 subtype 承载）
#   v3 subtype: 与 src/modeling_harness/schemas/v3/artifact/artifact.schema.json 的 type enum 一致
#   legacy 投影: V2 时代的文件/schema/字段名（同义词被禁止再造）
# ---------------------------------------------------------------------------

CANONICAL_ENTITIES: dict[str, dict] = {
    "Problem": {
        "schema": None,  # 题面以 inputs/ 原始文件为准，无独立 schema
        "v3_subtype": "problem",
        "legacy_projections": ["question_spec.schema.json（解析投影）", "inputs/*.txt|pdf|docx（原始题面）"],
    },
    "Question": {
        "schema": None,  # 由 workflow DAG per_question 展开 + Research State questions 维度承载
        "v3_subtype": "question",
        "legacy_projections": ["question_spec.schema.json", "work/state.json 的 q_states（V2 雏形）"],
    },
    "Model": {
        "schema": None,  # 以 M artifact 承载；模型规格内容在 payload 文件
        "v3_subtype": "model",
        "legacy_projections": ["MODEL_SPEC.md（legacy 契约文件）", "model_spec.schema.json",
                               "model_artifact.schema.json（V2 冻结实验用）", "model_dag.schema.json（M payload）"],
    },
    "Artifact": {
        "schema": "artifact/artifact.schema.json",
        "v3_subtype": None,  # 统一契约本体（含 15 个子类型）
        "legacy_projections": ["（V2 无对等物；V2 各契约文件均为其投影）"],
    },
    "Experiment": {
        "schema": None,
        "v3_subtype": "experiment",
        "legacy_projections": ["（V2 CODE_DELIVERABLES 契约已随论文链删除）"],
    },
    "Result": {
        "schema": None,
        "v3_subtype": "result",
        "legacy_projections": ["figures/all_results.json（legacy 数值真源导出）", "R artifact 的 legacy 视图"],
    },
    "Evidence": {
        "schema": "evidence/graph.schema.json",
        "v3_subtype": None,  # graph 为主体；单条 evidence 是边 + 被引 artifact
        "legacy_projections": ["（V2 文献证据 schema 已随论文链删除）"],
    },
    "Claim": {
        "schema": None,
        "v3_subtype": "claim",
        "legacy_projections": ["（V2 无对等物；P10 Finding Graph 是其前身研究）"],
    },
    "Decision": {
        "schema": "decision/decision.schema.json",
        "v3_subtype": "decision",
        "legacy_projections": ["decision_log.schema.json（V2，已升级有 reversible/invalidated_by 等）"],
    },
    "Failure": {
        "schema": "knowledge/failure.schema.json",
        "v3_subtype": None,  # 知识层实体，非 artifact
        "legacy_projections": ["src/modeling_harness/knowledge/pitfalls/ + _negative/（markdown 前置形态）"],
    },
    "Run": {
        "schema": "run/run_record.schema.json",  # System Hardening P3 创建（预注册）
        "v3_subtype": None,  # 运行记录层，非 artifact
        "legacy_projections": ["reproducibility.schema.json（V2 复现表单）", "state/runs/（P3 落盘）"],
    },
}

# 同义词回收表：出现的旧称呼必须映射回 canonical 名，禁止新文档/新代码再造
ENTIT_ALIASES: dict[str, str] = {
    "model_spec": "Model", "MODEL_SPEC": "Model", "model_artifact": "Model",
    "model_output": "Model", "formal_model": "Model", "model_card": "Model",
    "experiment_result": "Result", "all_results": "Result",
    "validator_report": "Evidence", "evidence_graph": "Evidence",
    "experiment_evidence": "Evidence",
    "run_record": "Run", "run_log": "Run", "checkpoint": "Run",
    "status_json": "Run",  # status.json 是流程状态投影，见 STATE_TRUTH.md
}


def canonical_name(alias: str) -> str:
    """同义词 → canonical 实体名（未登记则原样返回，供审计定位）。"""
    return ENTIT_ALIASES.get(alias, alias)


def entity_schema(entity: str) -> str | None:
    """canonical 实体的唯一 schema 归属（v3 相对路径）。"""
    info = CANONICAL_ENTITIES.get(entity)
    return info["schema"] if info else None
