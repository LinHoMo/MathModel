# -*- coding: utf-8 -*-
"""治理扫描：核对具体失效引用的目标"""
from pathlib import Path

ROOT = Path(".").resolve()
checks = [
    "core/validators/quality/paper_integrity.py",
    "core/runtime/writing/renderer.py",
    "core/knowledge/competition/cumcm.yaml",
    "core/knowledge/bench/cumcm/rubric_20xx.json",
    "core/tools/validation/citation_check.py",
    "core/knowledge/bench/imported",
    "core/knowledge/_negative/reflection_bank.json",
    "core/Modeler/knowledge/paper-bridge.md",
    "core/env/dim_weights.yaml",
    "core/knowledge/methods/cards/",
    "core/knowledge/failures/",
    "core/knowledge/patterns/",
    "examples/cards",
    "core/agents/critic/experiment-critic/SKILL.md",
    "core/agents/critic/model-critic/SKILL.md",
    "core/agents/critic/narrative-critic/SKILL.md",
    "core/cognition/evidence/claim_builder.py",
    "core/cognition/evidence/evidence_graph.py",
    "core/cognition/experiment/experiment_planner.py",
    "core/cognition/modeling/model_selection_arena.py",
    "core/knowledge/methods/registry.py",
    "core/workflows/engine.py",
    "core/workflows/modeling/standard.yaml",
    "core/runtime/heuristics/modeling.yaml",
    "core/runtime/rules/cumcm.yaml",
    "core/schemas/evidence_graph.schema.json",
    "core/tools/replay.py",
    "core/tools/e2e_metrics.py",
    "core/tools/citation_check.py",
    "core/tools/validation/",
    "docs/decisions/2026-09-04-refactor-plan-v2.md",
]
for c in checks:
    p = ROOT / c
    print(f"{'OK ' if p.exists() else 'MISS'}  {c}")
