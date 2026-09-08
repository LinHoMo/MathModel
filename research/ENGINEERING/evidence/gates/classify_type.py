#!/usr/bin/env python3
import json, os
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')

status_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'state.json'
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

registry_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'registry.json'
if os.path.exists(registry_path):
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # Write results to a file
    results = []
    
    current = status.get('current', {})
    results.append(f'Current step: {current.get("hand")}/{current.get("agent")}')
    results.append(f'Completed: {len(status.get("completed", []))}/29 (V2 pipeline)')
    results.append(f'Run phase: {status.get("run", {}).get("phase", "N/A")}')
    
    artifact_count = len(registry.get('artifacts', {}))
    results.append(f'Registry artifacts: {artifact_count}')
    
    providers = set()
    for art_id, art in registry.get('artifacts', {}).items():
        p = art.get('provider', '')
        if p:
            providers.add(p)
    results.append(f'Artifacts with provider: {len(providers)} distinct')
    if providers:
        results.append(f'Provider IDs: {providers}')
    
    for art_id in ['Q001', 'M001', 'E001', 'C001', 'A001', 'D001', 'R001']:
        art = registry.get('artifacts', {}).get(art_id, {})
        art_type = art.get('type', 'N/A')
        prov = art.get('provider', '-')
        stat = art.get('status', '-')
        results.append(f'  {art_id}: type={art_type}, provider={prov!r}, status={stat!r}')
        if art.get('data'):
            results.append(f'    data keys: {list(art["data"].keys())[:3]}')
    
    if artifact_count > 0 and any(art.get('provider') for art in registry.get('artifacts', {}).values()):
        results.append('RUN TYPE: real_execution')
    else:
        results.append('RUN TYPE: scaffold')
    
    with open(mathmodel / 'projects' / 'v3-real-2024a' / 'run_type_result.txt', 'w', encoding='utf-8') as out:
        out.write('\n'.join(results) + '\n')

print('Results written to run_type_result.txt')