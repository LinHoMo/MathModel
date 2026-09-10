"""Modeling 层运行时（V3 P3 + P1-VS-001 C1）。

- selection.py: MethodArena — 方法选型竞技场（KnowledgeRetriever 候选 +
  Decision Log 历史决策 → shortlist + 决策登记）
- planner.py: ExperimentPlanner — 实验规划器（方法卡 validation + 失败记忆
  avoidance → 必做检查清单 + preflight 守卫 + 基线对比 + 灵敏度方案）
- model_ir.py: MODEL_IR — Executable Model Specification（三层：
  L1 semantic / L2 mathematical / L3 computational；零依赖校验）
"""

from .model_ir import (
    L1_SEMANTIC_FIELDS,
    L2_MATHEMATICAL_FIELDS,
    L3_COMPUTATIONAL_FIELDS,
    MODEL_IR_REQUIRED_FIELDS,
    ModelIR,
    ModelIRBuilder,
    ModelIRError,
    validate_model_ir,
)
from .planner import ExperimentPlan, ExperimentPlanner
from .selection import MethodArena, SelectionError, SelectionOutcome
from .candidates import (
    Candidate, CandidateArena, InnovationCandidate,
    map_card_obligations, _merge_obligations,
)

__all__ = [
    "ExperimentPlan", "ExperimentPlanner",
    "MethodArena", "SelectionError", "SelectionOutcome",
    # P1-VS-001 C1: MODEL_IR
    "MODEL_IR_REQUIRED_FIELDS",
    "L1_SEMANTIC_FIELDS", "L2_MATHEMATICAL_FIELDS", "L3_COMPUTATIONAL_FIELDS",
    "ModelIR", "ModelIRBuilder", "ModelIRError", "validate_model_ir",
    # P1-M4: 候选 + 知识义务映射
    "Candidate", "CandidateArena", "InnovationCandidate",
    "map_card_obligations", "_merge_obligations",
]
