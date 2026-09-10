# -*- coding: utf-8 -*-
"""治理扫描：核对具体失效引用的目标"""
from pathlib import Path

ROOT = Path(".").resolve()
checks = [
    "src/modeling_harness/validators/quality/paper_integrity.py",
    "src/modeling_harness/runtime/writing/renderer.py",
    "src/modeling_harness/knowledge/competition/cumcm.yaml",
    "src/modeling_harness/knowledge/bench/cumcm/rubric_20xx.json",
    "src/modeling_harness/cli/validation/citation_check.py",
    "src/modeling_harness/knowledge/bench/imported",
    "src/modeling_harness/knowledge/_negative/reflection_bank.json",
    "core/Modeler/knowledge/paper-bridge.md",
    "core/env/dim_weights.yaml",
    "src/modeling_harness/knowledge/methods/cards/",
    "src/modeling_harness/knowledge/failures/",
    "src/modeling_harness/knowledge/patterns/",
    "examples/cards",
    "core/agents/critic/experiment-critic/SKILL.md",
    "core/agents/critic/model-critic/SKILL.md",
    "core/agents/critic/narrative-critic/SKILL.md",
    "core/cognition/evidence/claim_builder.py",
    "core/cognition/evidence/evidence_graph.py",
    "core/cognition/experiment/experiment_planner.py",
    "core/cognition/modeling/model_selection_arena.py",
    "src/modeling_harness/knowledge/methods/registry.py",
    "src/modeling_harness/workflows/engine.py",
    "src/modeling_harness/workflows/modeling/standard.yaml",
    "src/modeling_harness/runtime/heuristics/modeling.yaml",
    "src/modeling_harness/runtime/rules/cumcm.yaml",
    "src/modeling_harness/schemas/evidence_graph.schema.json",
    "src/modeling_harness/cli/replay.py",
    "src/modeling_harness/cli/e2e_metrics.py",
    "src/modeling_harness/cli/citation_check.py",
    "src/modeling_harness/cli/validation/",
    "docs/decisions/2026-09-04-refactor-plan-v2.md",
]
for c in checks:
    p = ROOT / c
    print(f"{'OK ' if p.exists() else 'MISS'}  {c}")
