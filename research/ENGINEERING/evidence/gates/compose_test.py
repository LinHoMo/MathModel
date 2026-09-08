#!/usr/bin/env python3
"""Test V3 DAG composition and execution."""
import sys
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')
sys.path.insert(0, str(mathmodel))

from core.runtime.roles import load_roles, validate_dag_roles
from core.runtime.execution.composer import WorkflowComposer

print("=" * 60)
print("V3 DAG Composition Test")
print("=" * 60)

# 1. Load roles
roles = load_roles(mathmodel / "core" / "roles")
print(f"\n1. Roles loaded: {len(roles)} roles")
for name, role in roles.items():
    print(f"   - {name}: capability={getattr(role, 'capabilities', 'N/A')}")

# 2. Compose DAG with Q001
questions = ["Q001"]
composer = WorkflowComposer(mathmodel / "core" / "workflows")

print(f"\n2. Composing DAG with questions: {questions}")
try:
    dag = composer.compose_executable(questions, "cumcm")
    print(f"   DAG composed: {dag.name}")
    print(f"   Nodes: {len(dag.nodes)}")
    print(f"   Edges: {len(dag.edges)}")
    
    # 3. Validate DAG roles
    role_problems = validate_dag_roles(dag, roles)
    print(f"\n3. Role validation:")
    if role_problems:
        print(f"   FAIL: {role_problems}")
    else:
        print(f"   PASS: All roles valid")
    
    # 4. Show node details
    print(f"\n4. DAG nodes:")
    for nid in sorted(dag.nodes.keys()):
        n = dag.nodes[nid]
        bits = [f"type={n.type}"]
        if n.role:
            bits.append(f"role={n.role}")
        if n.validator:
            bits.append(f"validator={n.validator}")
        if n.per_question:
            bits.append("per_question")
        if n.on_fail:
            bits.append(f"on_fail->{n.on_fail}")
        print(f"   {nid:32s} {'  '.join(bits)}")
        
except Exception as e:
    print(f"\nError: {type(e).__name__}: {str(e)[:500]}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)