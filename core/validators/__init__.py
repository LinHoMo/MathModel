"""Validators — V3 校验器集合（从 V2 agent 降级/升级而来）。

- evidence/evidence_gate.py: 证据门禁（PASS/WEAK/FAIL，E1-E8 检查项）
  DAG 节点 evidence_gate（validator: evidence-gate）绑定。
"""

from .evidence.evidence_gate import (  # noqa: F401
    DEFAULT_MIN_COVERAGE, GateReport, evaluate, Finding,
)
