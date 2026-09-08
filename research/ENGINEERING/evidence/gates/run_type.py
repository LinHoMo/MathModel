#!/usr/bin/env python3
"""Check run type classification and gate status."""
import json, os, sys
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')
sys.path.insert(0, str(mathmodel))

# Check current status
status_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'state.json'
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

# Check registry for provider/skill info
registry_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'registry.json'
if registry_path.exists():
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    print('Current run type classification:')
    current = status.get('current', {})
    print(f'  Current step: {current.get("hand")}/{current.get("agent")}')
    print(f'  Completed: {len(status.get("completed", []))}/29')
    print(f'  Run phase: {status.get("run", {}).get("phase", "N/A")}')
    
    artifact_count = len(registry.get('artifacts', {}))
    print(f'  Registry artifacts: {artifact_count}')
    
    # Check for provider in artifacts
    providers = set()
    for art_id, art in registry.get('artifacts', {}).items():
        p = art.get('provider', '')
        if p:
            providers.add(p)
    print(f'  Artifacts with provider: {len(providers)} distinct')
    
    # Check question specs
    q001 = registry.get('artifacts', {}).get('Q001', {})
    print(f'  Q001 type: {q001.get("type", "N/A")}')
    if q001.get('data'):
        print(f'  Q001 data keys: {list(q001["data"].keys())}')
    else:
        print(f'  Q001 data: empty/none')
    
    # Check for model_provider and skill_version
    for art_id, art in registry.get('artifacts', {}).items():
        mp = art.get('model_provider', '')
        sv = art.get('skill_version', '')
        if mp or sv:
            print(f'  {art_id}: model_provider={mp!r}, skill_version={sv!r}')
    
    # Run type determination
    print()
    if artifact_count == 0 and len(status.get('completed', [])) == 0:
        print('  RUN TYPE: scaffold (no real execution yet)')
    elif artifact_count > 0 and any(art.get('provider') for art in registry.get('artifacts', {}).values()):
        print('  RUN TYPE: real_execution (has provider references)')
    else:
        print('  RUN TYPE: indeterminate (need execution data)')

print()

# Also check the gate status
print('Gate check:')
gate_script = mathmodel / 'core' / 'tools' / 'gate.py'
import subprocess
result = subprocess.run(
    [sys.executable, str(gate_script), 'v3-real-2024a', 'modeler', 'problem-parser', '--json'],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print(f'  gate returncode: {result.returncode}')
output = (result.stdout or '')[:300] + ((result.stderr or '')[:300] if result.stderr else '')
print(f'  gate output: {output}')