#!/usr/bin/env python3
"""Try V3 DAG composition."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT / "core" / "tools"))
sys.path.insert(0, str(ROOT / "core" / "tools" / "runtime"))

# Now try the imports
try:
    from runtime.execution.composer import WorkflowComposer
    from runtime.roles import load_roles, validate_dag_roles
    print("Import SUCCESS")
    
    # Try to compose with Q001
    reg_path = Path("projects/v3-real-2024a/work/registry.json")
    questions = ["Q001"]  # Default since registry may not have Q ids in expected format
    
    print(f"Questions: {questions}")
    dag = composer.compose_executable(questions, "cumcm")
    print(f"DAG composed: {dag.name}, nodes: {len(dag.nodes)}")
    
    roles = load_roles(ROOT / "core" / "roles")
    print(f"Roles loaded: {len(roles)} roles")
    
    role_problems = validate_dag_roles(dag, roles)
    if role_problems:
        print(f"Role problems: {role_problems}")
    else:
        print("Role validation: PASS")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:500]}")
    import traceback
    traceback.print_exc()