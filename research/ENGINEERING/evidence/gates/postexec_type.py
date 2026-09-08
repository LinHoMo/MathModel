#!/usr/bin/env python3
"""Check run type after V3 execution."""
import json, os
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')

# Check status
status_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'state.json'
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

# Check registry
registry_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'registry.json'
if registry_path.exists():
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    print('=== RUN TYPE CLASSIFICATION (POST-EXECUTION) ===')
    current = status.get('current', {})
    print(f'  Current step: {current.get("hand")}/{current.get("agent")}')
    print(f'  Completed: {len(status.get("completed", []))}/29 (V2 pipeline)')
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
    if providers:
        print(f'  Provider IDs: {providers}')
    
    # Check for model_provider and skill_version
    for art_id, art in registry.get('artifacts', {}).items():
        mp = art.get('model_provider', '')
        sv = art.get('skill_version', '')
        if mp or sv:
            print(f'  {art_id}: model_provider={mp!r}, skill_version={sv!r}')
    
    # Check key artifact types
    print()
    print('  Key artifact types:')
    for art_id in ['Q001', 'M001', 'E001', 'C001', 'A001', 'D001', 'R001']:
        art = registry.get('artifacts', {}).get(art_id, {})
        art_type = art.get('type', 'N/A')
        print(f'    {art_id}: type={art_type}, provider={art.get("provider", "-")!r}, status={art.get("status", "-")!r}')
        if art.get('data'):
            print(f'      data keys: {list(art["data"].keys())[:5]}')
    
    # Run type determination
    print()
    if artifact_count > 0 and any(art.get('provider') for art in registry.get('artifacts', {}).values()):
        print('  RUN TYPE: real_execution')
    else:
        print('  RUN TYPE: scaffold')