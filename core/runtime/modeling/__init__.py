"""Modeling 层运行时（V3 P3）。

- selection.py: MethodArena — 方法选型竞技场（KnowledgeRetriever 候选 +
  Decision Log 历史决策 → shortlist + 决策登记）
- planner.py: ExperimentPlanner — 实验规划器（方法卡 validation + 失败记忆
  avoidance → 必做检查清单 + preflight 守卫 + 基线对比 + 灵敏度方案）
"""

from .planner import ExperimentPlan, ExperimentPlanner
from .selection import MethodArena, SelectionError, SelectionOutcome

__all__ = [
    "ExperimentPlan", "ExperimentPlanner",
    "MethodArena", "SelectionError", "SelectionOutcome",
]
