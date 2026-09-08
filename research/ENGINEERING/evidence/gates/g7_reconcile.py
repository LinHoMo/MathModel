#!/usr/bin/env python3
"""G7: Reconcile verification."""
import json, os, sys
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')
proj_dir = mathmodel / 'projects' / 'v3-real-2024a'

# Current state
status_path = proj_dir / 'work' / 'state.json'
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

# Registry
registry_path = proj_dir / 'work' / 'registry.json'
reg_exists = os.path.exists(registry_path)
if reg_exists:
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # Evidence graph
    eg_path = proj_dir / 'state' / 'evidence_graph.json'
    eg_exists = os.path.exists(eg_path)
    
    print('=== RECONCILE STATUS ===')
    print(f'Status current: {status.get("current", {}).get("hand")}/{status.get("current", {}).get("agent")}')
    print(f'Status completed: {len(status.get("completed", []))}')
    print(f'Registry exists: {reg_exists}, artifacts: {len(registry.get("artifacts", {}))}')
    print(f'Evidence graph exists: {eg_exists}')
    
    # Run reconcile command
    print()
    print('Running reconcile...')
    import subprocess
    result = subprocess.run(
        ['python', 'core/tools/state.py', 'v3-real-2024a', 'reconcile'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    print(f'Return code: {result.returncode}')
    print(f'Stdout: {result.stdout[:800]}')
    print(f'Stderr: {result.stderr[:800]}')
else:
    print('Registry not found')